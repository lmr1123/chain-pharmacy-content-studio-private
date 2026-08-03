#!/usr/bin/env python3
"""商品培训视频全量换主题：文案屏显 + 包装图 + 克隆旁白 + 分段重渲 + 拼接。

由 generate_business_video.py --mode full 调用。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import wave
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "poc/gold-sample"

SEGMENTS: list[dict[str, str]] = [
    {
        "id": "opening",
        "json": "product-training-opening.json",
        "label": "开场",
    },
    {
        "id": "brand",
        "json": "product-training-brand-overview.json",
        "label": "品牌品类",
    },
    {
        "id": "faithful",
        "json": "product-training-faithful.json",
        "label": "核心讲解",
    },
    {
        "id": "efficacy",
        "json": "product-training-efficacy.json",
        "label": "核心功效",
    },
    {
        "id": "features",
        "json": "product-training-features.json",
        "label": "产品特点",
    },
    {
        "id": "audience",
        "json": "product-training-audience.json",
        "label": "适宜人群",
    },
    {
        "id": "combination",
        "json": "product-training-combination.json",
        "label": "联合用药",
    },
    {
        "id": "summary",
        "json": "product-training-summary.json",
        "label": "总结",
    },
]

DEFAULT_TEMPO = 1.16
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
LEAD_IN = 0.06
LEAD_OUT = 0.10


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip())
    return re.sub(r"-+", "-", s).strip("-")[:80] or "theme"


def prepare_workspace(run_dir: Path) -> Path:
    ws = run_dir / "render-workspace"
    if ws.exists():
        shutil.rmtree(ws)
    ignore = shutil.ignore_patterns(
        "node_modules",
        "dist",
        ".render-work",
        ".git",
        "*.mp4",
        ".DS_Store",
    )
    shutil.copytree(GOLD, ws, ignore=ignore, symlinks=True)
    nm = GOLD / "node_modules"
    if nm.exists() and not (ws / "node_modules").exists():
        os.symlink(nm, ws / "node_modules")
    return ws


def map_sections_to_segments(
    sections: list[dict[str, Any]], product: str
) -> dict[str, dict[str, Any]]:
    """Map business sections onto the 8 gold segment slots by keyword + order."""
    by_label: dict[str, dict[str, Any]] = {}
    remaining = list(sections)

    def take(keywords: list[str]) -> dict[str, Any] | None:
        for i, sec in enumerate(remaining):
            title = str(sec.get("title") or "")
            if any(k in title for k in keywords):
                return remaining.pop(i)
        return None

    order_keywords = [
        ("opening", ["开场", "为什么", "了解", "引入", "背景"]),
        ("brand", ["品牌", "品类", "介绍", "基础信息", "商品信息"]),
        ("faithful", ["核心讲解", "关系", "缺乏", "机制"]),
        ("efficacy", ["功效", "核心功效", "利益"]),
        ("features", ["特点", "工艺", "原料", "背书"]),
        ("audience", ["人群", "适宜"]),
        ("combination", ["联合", "搭配", "组合"]),
        ("summary", ["总结", "小结", "回顾"]),
    ]
    for sid, kws in order_keywords:
        hit = take(kws)
        if hit:
            by_label[sid] = hit

    # Fill remaining slots in order with leftover sections / pad with last
    leftovers = remaining
    li = 0
    for seg in SEGMENTS:
        sid = seg["id"]
        if sid in by_label:
            continue
        if li < len(leftovers):
            by_label[sid] = leftovers[li]
            li += 1
        elif sections:
            # pad: reuse nearest content so every segment has narration
            by_label[sid] = sections[min(len(sections) - 1, len(by_label))]
        else:
            by_label[sid] = {
                "title": seg["label"],
                "narration": f"本段介绍{product}相关培训要点。",
            }
    return by_label


def extract_screen_fields(
    product: str, mapped: dict[str, dict[str, Any]], sections: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build screen payload for data-driven TSX fields."""

    def bullets(sid: str, n: int, defaults: list[str]) -> list[str]:
        sec = mapped.get(sid) or {}
        text = str(sec.get("narration") or "")
        # split by common list markers
        parts = re.split(r"[\n；;]|[0-9]+[、.．]", text)
        parts = [p.strip(" ，,。.") for p in parts if len(p.strip()) >= 2]
        out = []
        for i in range(n):
            if i < len(parts) and parts[i]:
                # keep short for on-screen
                t = parts[i]
                if len(t) > 28:
                    t = t[:28]
                out.append(f"{i+1}、{t}" if not re.match(r"^\d", t) else t)
            else:
                out.append(defaults[i] if i < len(defaults) else f"{i+1}、要点")
        return out

    # labels from brand section first lines
    brand_nar = str((mapped.get("brand") or {}).get("narration") or "")
    labels = [
        p.strip()[:12]
        for p in re.split(r"[\n，,；;]", brand_nar)
        if 2 <= len(p.strip()) <= 16
    ][:3]
    if len(labels) < 3:
        labels = (labels + ["核心卖点", "适用场景", "沟通要点"])[:3]

    efficacy = bullets(
        "efficacy",
        2,
        ["1.促进能量生成", "2.抗氧化，减少组织细胞损伤"],
    )
    # normalize numbering style for efficacy (dot style in gold)
    efficacy = [
        re.sub(r"^(\d+)[、.]", r"\1.", e) if i == 0 else e
        for i, e in enumerate(efficacy)
    ]

    features = bullets(
        "features",
        3,
        ["1、原研工艺，锁住活性", "2、海外原料，提升品质", "3、医疗背书"],
    )
    combo = bullets(
        "combination",
        2,
        [f"1、联合方案甲＋{product}", f"2、联合方案乙＋{product}"],
    )

    # summary cells: try pull short phrases from sections
    def short_lines(sid: str, n: int, fallback: list[str]) -> list[str]:
        sec = mapped.get(sid) or {}
        text = str(sec.get("narration") or "")
        parts = re.split(r"[\n；;。！]", text)
        parts = [p.strip() for p in parts if 2 <= len(p.strip()) <= 36]
        out = []
        for i in range(n):
            if i < len(parts):
                out.append(parts[i][:36])
            else:
                out.append(fallback[i] if i < len(fallback) else "待补充")
        return out

    cells = (
        short_lines("efficacy", 2, ["核心功效一", "核心功效二"])
        + short_lines("features", 3, ["特点一", "特点二", "特点三"])
        + short_lines("audience", 3, ["人群一", "人群二", "人群三"])
        + short_lines("combination", 2, [f"方案甲＋{product}", f"方案乙＋{product}"])
    )

    return {
        "product_name": product,
        "labels": labels,
        "efficacy_title": "两大核心功效",
        "efficacy_sections": efficacy,
        "feature_sections": features,
        "combo_sections": combo,
        "audience_title": "适宜人群",
        "pack_badge": "授权包装" if False else "包装图槽位",
        "meter_label": product,
        "summary": {
            "headers": ["核心功效", "产品特点", "适宜人群", "联合用药"],
            "cells": cells,
            "brand": "大参林",
            "slogan": f"内部培训 · {product} 商品知识",
        },
    }


def split_cues(text: str, duration: float) -> list[dict[str, Any]]:
    """Character-proportional subtitle cues over [LEAD_IN, duration-LEAD_OUT]."""
    # sentence-ish chunks
    raw = re.split(r"(?<=[。！？；;，,])", text)
    chunks = [c.strip() for c in raw if c.strip()]
    if not chunks:
        chunks = [text.strip() or "……"]
    total_chars = sum(max(1, len(re.sub(r"\s+", "", c))) for c in chunks)
    start = LEAD_IN
    end_limit = max(start + 0.5, duration - LEAD_OUT)
    usable = end_limit - start
    cues = []
    cursor = start
    for i, c in enumerate(chunks):
        ch = max(1, len(re.sub(r"\s+", "", c)))
        if i == len(chunks) - 1:
            seg_end = end_limit
        else:
            seg_end = cursor + usable * (ch / total_chars)
        cues.append(
            {
                "start": round(cursor, 3),
                "end": round(seg_end, 3),
                "text": c[:48],
            }
        )
        cursor = seg_end
    return cues


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def detect_tts_python() -> Path | None:
    candidates = [
        ROOT / ".venv-qwen-tts/bin/python",
        ROOT
        / "production-library/validation/courseware/product-courseware-4-faithful-replica-v1/.venv-tts/bin/python",
        Path(sys.executable),
    ]
    for py in candidates:
        if not py.exists():
            continue
        r = subprocess.run(
            [str(py), "-c", "from mlx_audio.tts.utils import load_model"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            return py
    return None


def generate_tts(
    *,
    text: str,
    out_wav: Path,
    prompt_audio: Path,
    ref_text: str,
    py: Path,
) -> float:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    worker = out_wav.with_suffix(".worker.py")
    worker.write_text(
        f"""
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model
import subprocess

text = {text!r}
ref_audio = {str(prompt_audio)!r}
ref_text = {ref_text!r}
out = {str(out_wav)!r}
tempo = {DEFAULT_TEMPO}
model = load_model({MODEL_ID!r})
sr = model.sample_rate
results = list(model.generate(text=text, voice="", speed=1.0, lang_code="Chinese", ref_audio=ref_audio, ref_text=ref_text))
chunks = []
for r in results:
    arr = np.array(r.audio, copy=True)
    if arr.ndim > 1:
        arr = arr.reshape(-1)
    chunks.append(arr)
audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
raw = Path(out).with_suffix('.raw.wav')
sf.write(raw, audio, sr)
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(raw),'-af',f'atempo={{tempo:.6f}},aresample={{sr}}',str(out)], check=True)
raw.unlink(missing_ok=True)
print(json.dumps({{'ok': True}}))
""",
        encoding="utf-8",
    )
    try:
        r = subprocess.run(
            [str(py), str(worker)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-1000:] or r.stdout[-1000:])
    finally:
        worker.unlink(missing_ok=True)
    # pad lead
    padded = out_wav.with_suffix(".pad.wav")
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(out_wav),
            "-af",
            f"adelay={int(LEAD_IN*1000)}|{int(LEAD_IN*1000)},apad=pad_dur={LEAD_OUT}",
            str(padded),
        ],
        check=True,
    )
    padded.replace(out_wav)
    return wav_duration(out_wav)


def apply_content_to_json(
    *,
    base: dict,
    product: str,
    narration: str,
    audio_public_path: str,
    duration: float,
    screen: dict,
    product_asset: str | None,
    segment_id: str,
) -> dict:
    data = deepcopy(base)
    data["product_name"] = product
    data["title"] = product if segment_id == "opening" else data.get("title", product)
    data["screen"] = screen
    data["playback_duration"] = round(duration, 3)
    if "range" in data and isinstance(data["range"], dict):
        data["range"]["duration"] = round(duration, 3)
    if "referenceRange" in data and isinstance(data["referenceRange"], dict):
        data["referenceRange"]["duration"] = round(duration, 3)

    if segment_id != "summary":
        data["cues"] = split_cues(narration, duration)
        data["audio"] = {
            "source": "voice.reference-pharmacist-qwen-v1",
            "file": audio_public_path,
            "disclosure": "业务主题克隆药师旁白；v5-smooth",
            "pace_policy": {
                "default_tempo": DEFAULT_TEMPO,
                "mode": "full-segment-continuous",
                "version": "v5-smooth-business",
            },
        }
    else:
        # summary has short music-less voice optional; keep tagline
        data["tagline"] = screen.get("summary", {}).get(
            "slogan", f"内部培训 · {product} 商品知识"
        )
        data["audio"] = data.get("audio") or {
            "source": "voice.reference-pharmacist-qwen-v1",
            "file": audio_public_path,
        }
        data["audio"]["file"] = audio_public_path
        data["cues"] = split_cues(narration, max(duration, 6.0))

    if product_asset:
        assets = data.setdefault("assets", {})
        if isinstance(assets, dict):
            assets["product"] = product_asset
    return data


def render_segment(ws: Path, segment_id: str, out_mp4: Path) -> None:
    """Render into workspace/out first so public/ audio resolves correctly."""
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    ws_out = ws / "out" / f"{segment_id}.mp4"
    ws_out.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["FFMPEG_PATH"] = env.get("FFMPEG_PATH") or "/opt/homebrew/bin/ffmpeg"
    env["FFPROBE_PATH"] = env.get("FFPROBE_PATH") or "/opt/homebrew/bin/ffprobe"
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"
    cmd = [
        "node",
        "scripts/render-product-segment.mjs",
        segment_id,
        str(ws_out),
    ]
    print(f"[render] {segment_id} → {out_mp4.name}")
    r = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(
            f"render {segment_id} failed:\n{r.stderr[-2000:]}\n{r.stdout[-1000:]}"
        )
    # copy to delivery segments folder
    if ws_out.exists():
        shutil.copy2(ws_out, out_mp4)
    elif Path(str(ws_out).replace(".mp4", "-0.mp4")).exists():
        shutil.copy2(Path(str(ws_out).replace(".mp4", "-0.mp4")), out_mp4)
    else:
        # find any new mp4 in ws/out
        cands = sorted((ws / "out").glob(f"*{segment_id}*.mp4"))
        if not cands:
            raise RuntimeError(f"render produced no mp4 for {segment_id}")
        shutil.copy2(cands[-1], out_mp4)


def concat_mp4s(paths: list[Path], out: Path) -> None:
    lst = out.with_suffix(".concat.txt")
    lst.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in paths) + "\n", encoding="utf-8"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c",
            "copy",
            str(out),
        ],
        check=True,
    )
    lst.unlink(missing_ok=True)


def run_product_full(
    *,
    content: dict[str, Any],
    out_dir: Path,
    voice_pack_dir: Path,
    with_tts: bool,
    with_render: bool,
    product_image: Path | None = None,
) -> dict[str, Any]:
    product = content["theme"]
    sections = content["sections"]
    mapped = map_sections_to_segments(sections, product)
    screen = extract_screen_fields(product, mapped, sections)
    if product_image and product_image.exists():
        screen["pack_badge"] = "授权包装"

    write_json(out_dir / "segment-map.json", {k: v.get("title") for k, v in mapped.items()})
    write_json(out_dir / "screen.json", screen)

    status: dict[str, Any] = {
        "mode": "full-content-visual-audio",
        "product": product,
        "segments": {},
    }

    if not with_tts and not with_render:
        status["ok"] = True
        status["note"] = "仅写入 segment-map/screen；加 --with-tts --with-mp4 才重渲"
        return status

    py = detect_tts_python() if with_tts else None
    if with_tts and not py:
        return {"ok": False, "error": "缺少 .venv-qwen-tts（Qwen3 克隆环境）"}

    pack = load_json(voice_pack_dir / "voice-pack.json")
    prompt_audio = voice_pack_dir / pack["prompt"]["audio"]
    ref_text = pack["prompt"]["ref_text"]

    ws = prepare_workspace(out_dir)
    public_audio = ws / "public" / "product-training-audio" / "business-theme"
    public_audio.mkdir(parents=True, exist_ok=True)

    product_asset_url = None
    if product_image and product_image.exists():
        dest_img = ws / "public" / "product-training-assets" / f"business-{slugify(product)}.png"
        dest_img.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(product_image, dest_img)
        product_asset_url = f"/product-training-assets/{dest_img.name}"
        screen["pack_badge"] = "授权包装"
    else:
        # keep gold generic packshot
        product_asset_url = "/product-training-assets/generic-coq10-packshot-v1.png"

    segment_mp4s: list[Path] = []
    audio_dir = out_dir / "audio" / "sections"
    audio_dir.mkdir(parents=True, exist_ok=True)

    for seg in SEGMENTS:
        sid = seg["id"]
        sec = mapped[sid]
        narration = str(sec.get("narration") or "").strip()
        if not narration:
            narration = f"{product} · {seg['label']} 培训要点。"

        wav_name = f"business-{sid}.wav"
        wav_ws = public_audio / wav_name
        wav_out = audio_dir / f"{sid}.wav"

        if with_tts:
            print(f"[tts] {sid} {seg['label']} …")
            dur = generate_tts(
                text=narration,
                out_wav=wav_ws,
                prompt_audio=prompt_audio,
                ref_text=ref_text,
                py=py,  # type: ignore[arg-type]
            )
            shutil.copy2(wav_ws, wav_out)
        else:
            # without tts cannot full render meaningfully
            return {
                "ok": False,
                "error": "full 模式需要 --with-tts 以生成与画面同步的旁白",
            }

        base = load_json(GOLD / seg["json"])
        patched = apply_content_to_json(
            base=base,
            product=product,
            narration=narration,
            audio_public_path=f"/product-training-audio/business-theme/{wav_name}",
            duration=dur,
            screen=screen,
            product_asset=product_asset_url,
            segment_id=sid,
        )
        write_json(ws / seg["json"], patched)
        write_json(out_dir / "segment-json" / seg["json"], patched)

        status["segments"][sid] = {
            "title": sec.get("title"),
            "duration_s": round(dur, 3),
            "narration_chars": len(re.sub(r"\s+", "", narration)),
        }

        if with_render:
            mp4 = out_dir / "segments" / f"{sid}.mp4"
            render_segment(ws, sid, mp4)
            segment_mp4s.append(mp4)
            status["segments"][sid]["mp4"] = str(mp4)

    if with_render and segment_mp4s:
        final = out_dir / f"{slugify(product)}_商品培训视频_v1.mp4"
        concat_mp4s(segment_mp4s, final)
        status["mp4"] = {"ok": True, "path": str(final), "segments": len(segment_mp4s)}
        status["ok"] = True
    else:
        status["ok"] = True
        status["mp4"] = {"ok": False, "error": "未请求渲染"}

    write_json(out_dir / "full-render-status.json", status)
    return status
