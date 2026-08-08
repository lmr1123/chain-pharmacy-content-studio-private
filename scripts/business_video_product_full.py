#!/usr/bin/env python3
"""商品培训视频全量换主题：文案屏显 + 包装图 + 克隆旁白 + 分段重渲 + 拼接。

由 generate_business_video.py --mode full 调用。
"""

from __future__ import annotations

import hashlib
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
sys.path.insert(0, str(ROOT / "scripts"))
from content_driven_rules import (  # noqa: E402
    extract_list_items,
    number_list_items,
    plan_list_block,
    segment_has_content,
)

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


def media_tool(name: str) -> str | None:
    for prefix in (Path("/opt/homebrew/bin"), Path("/usr/local/bin")):
        candidate = prefix / name
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def product_content_sha256(content: dict[str, Any]) -> str:
    payload = {
        "theme": str(content.get("theme") or ""),
        "sections": [
            {
                "title": str(section.get("title") or ""),
                "narration": str(section.get("narration") or ""),
            }
            for section in content.get("sections") or []
        ],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_product_approval_request(
    content: dict[str, Any], product_image: Path | None
) -> dict[str, Any]:
    return {
        "schema": "product-video-approval-v1",
        "approved": False,
        "approved_by": "",
        "approved_at": "",
        "authorization_reference": "",
        "approved_content_sha256": product_content_sha256(content),
        "approved_product_image_sha256": (
            sha256_file(product_image)
            if product_image and product_image.is_file()
            else None
        ),
        "notes": "确认 8 段审核稿与包装图可用于本次内部培训视频后再批准",
    }


def require_product_approval(
    content: dict[str, Any], product_image: Path, approval_path: Path | None
) -> dict[str, Any]:
    if not approval_path or not approval_path.is_file():
        return {
            "ok": False,
            "error": "缺少 --product-approval；请先审核 product-approval.request.json",
        }
    try:
        approval = load_json(approval_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": f"商品审批文件不可读: {exc}"}
    expected_content = product_content_sha256(content)
    expected_image = sha256_file(product_image)
    required_text = ("approved_by", "approved_at", "authorization_reference")
    if approval.get("schema") != "product-video-approval-v1":
        return {"ok": False, "error": "商品审批 schema 不匹配"}
    if approval.get("approved") is not True:
        return {"ok": False, "error": "商品内容与包装尚未批准（approved != true）"}
    missing = [key for key in required_text if not str(approval.get(key) or "").strip()]
    if missing:
        return {"ok": False, "error": f"商品审批缺少字段: {', '.join(missing)}"}
    if approval.get("approved_content_sha256") != expected_content:
        return {"ok": False, "error": "商品审核稿在审批后发生变化，请重新审核"}
    if approval.get("approved_product_image_sha256") != expected_image:
        return {"ok": False, "error": "商品包装图在审批后发生变化，请重新审核"}
    return {
        "ok": True,
        "approved": True,
        "approved_by": approval["approved_by"],
        "approved_at": approval["approved_at"],
        "authorization_reference": approval["authorization_reference"],
        "approved_content_sha256": expected_content,
        "approved_product_image_sha256": expected_image,
    }


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
    """Map business sections onto gold slots. Missing slots stay absent (omit)."""
    del product  # theme only used by callers; keep signature stable
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
        if hit and segment_has_content(hit):
            by_label[sid] = hit

    # leftover real sections fill empty slots in order — never invent shells
    leftovers = [s for s in remaining if segment_has_content(s)]
    for seg in SEGMENTS:
        sid = seg["id"]
        if sid in by_label:
            continue
        if leftovers:
            by_label[sid] = leftovers.pop(0)
    return by_label


def extract_screen_fields(
    product: str, mapped: dict[str, dict[str, Any]], sections: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build screen payload; lists are N-item, never padded to gold counts."""
    del sections

    def items_for(sid: str, max_items: int = 6, max_len: int = 28) -> list[str]:
        sec = mapped.get(sid) or {}
        return extract_list_items(
            str(sec.get("narration") or ""), max_items=max_items, max_len=max_len
        )

    brand_nar = str((mapped.get("brand") or {}).get("narration") or "")
    labels = extract_list_items(brand_nar, max_items=4, max_len=12)

    efficacy_raw = items_for("efficacy", max_items=4, max_len=28)
    efficacy = number_list_items(efficacy_raw, style="点")
    # gold efficacy uses "1." style
    efficacy = [re.sub(r"^(\d+)[、．]", r"\1.", e) for e in efficacy]

    features = number_list_items(items_for("features", max_items=5, max_len=28))
    combo = number_list_items(items_for("combination", max_items=4, max_len=32))

    n_eff = len(efficacy)
    _cn = {1: "一", 2: "两", 3: "三", 4: "四", 5: "五"}
    efficacy_title = (
        f"{_cn.get(n_eff, str(n_eff))}大核心功效" if n_eff else "核心功效"
    )
    # summary cells: only from included modules, no pad shells
    def short_lines(sid: str, max_n: int) -> list[str]:
        return items_for(sid, max_items=max_n, max_len=36)

    headers: list[str] = []
    cells: list[str] = []
    if "efficacy" in mapped and efficacy:
        headers.append("核心功效")
        cells.extend(short_lines("efficacy", 4) or efficacy_raw)
    if "features" in mapped and features:
        headers.append("产品特点")
        cells.extend(short_lines("features", 5))
    if "audience" in mapped:
        aud = short_lines("audience", 4)
        if aud:
            headers.append("适宜人群")
            cells.extend(aud)
    if "combination" in mapped and combo:
        headers.append("联合用药")
        cells.extend(short_lines("combination", 4))
    if not headers:
        headers = ["培训要点"]
        cells = [product]

    list_plans = {
        "efficacy": plan_list_block(
            module_id="efficacy",
            title="核心功效",
            items=efficacy,
            gold_example_count=2,
        ),
        "features": plan_list_block(
            module_id="features",
            title="产品特点",
            items=features,
            gold_example_count=3,
        ),
        "combination": plan_list_block(
            module_id="combination",
            title="联合用药",
            items=combo,
            gold_example_count=2,
        ),
    }

    return {
        "product_name": product,
        "labels": labels,
        "efficacy_title": efficacy_title,
        "efficacy_sections": efficacy,
        "feature_sections": features,
        "combo_sections": combo,
        "audience_title": "适宜人群",
        "pack_badge": "包装图槽位",
        "meter_label": product,
        "list_plans": list_plans,
        "summary": {
            "headers": headers,
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
    ffmpeg = media_tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("缺少 ffmpeg，无法生成正式旁白")
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
ffmpeg = {ffmpeg!r}
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
subprocess.run([ffmpeg,'-loglevel','error','-y','-i',str(raw),'-af',f'atempo={{tempo:.6f}},aresample={{sr}}',str(out)], check=True)
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
            ffmpeg,
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
    else:
        # Gold JSON may contain the Q10 demonstration packshot. A new product may
        # never inherit it: missing authorization is a gap, not a substitution.
        assets = data.get("assets")
        if isinstance(assets, dict):
            assets.pop("product", None)
    return data


def render_segment(ws: Path, segment_id: str, out_mp4: Path) -> None:
    """Render into workspace/out first so public/ audio resolves correctly."""
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    ws_out = ws / "out" / f"{segment_id}.mp4"
    ws_out.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    ffmpeg = media_tool("ffmpeg")
    ffprobe = media_tool("ffprobe")
    if ffmpeg:
        env["FFMPEG_PATH"] = env.get("FFMPEG_PATH") or ffmpeg
    if ffprobe:
        env["FFPROBE_PATH"] = env.get("FFPROBE_PATH") or ffprobe
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
    ffmpeg = media_tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("缺少 ffmpeg，无法拼接正式视频")
    lst = out.with_suffix(".concat.txt")
    lst.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in paths) + "\n", encoding="utf-8"
    )
    subprocess.run(
        [
            ffmpeg,
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
    product_approval: Path | None = None,
) -> dict[str, Any]:
    product = content["theme"]
    sections = content["sections"]
    real_sections = [section for section in sections if segment_has_content(section)]
    if with_render and len(real_sections) > len(SEGMENTS):
        extra = real_sections[len(SEGMENTS) :]
        return {
            "ok": False,
            "error": (
                f"商品正式成片固定为 8 段，检测到 {len(real_sections)} 段审核内容；"
                "额外内容不得静默丢弃，请合并或重新确认 8 段结构。"
            ),
            "extra_sections": [str(item.get("title") or "") for item in extra],
        }
    mapped = map_sections_to_segments(sections, product)
    if not mapped:
        return {"ok": False, "error": "未映射到任何有效段落（请提供带旁白的 sections）"}
    authorized_product_image = bool(product_image and product_image.is_file())
    if with_render and not authorized_product_image:
        return {
            "ok": False,
            "error": (
                "正式 render 缺少业务声明的授权包装图。"
                "请通过 --product-image 提供授权原图；通用示意包装仅可用于显式预览/规划。"
            ),
            "gate": "authorized_product_packshot",
            "product": product,
        }
    missing_segments = [seg["id"] for seg in SEGMENTS if seg["id"] not in mapped]
    if with_render and missing_segments:
        return {
            "ok": False,
            "error": f"商品正式成片需要完整 8 段，当前缺少: {', '.join(missing_segments)}",
            "missing_segments": missing_segments,
        }
    approval_gate: dict[str, Any] | None = None
    if with_render:
        assert product_image is not None
        approval_gate = require_product_approval(content, product_image, product_approval)
        if not approval_gate.get("ok"):
            return {
                "ok": False,
                "error": approval_gate.get("error"),
                "approval": approval_gate,
            }
    screen = extract_screen_fields(product, mapped, sections)
    if authorized_product_image:
        screen["pack_badge"] = "授权包装"
        screen["content_gaps"] = []
    else:
        screen["pack_badge"] = "待补授权包装（仅规划，不可正式渲染）"
        screen["content_gaps"] = [
            {
                "field": "authorized_product_packshot",
                "reason": "未提供业务声明授权的商品包装原图",
            }
        ]

    segment_plan = {
        seg["id"]: {
            "label": seg["label"],
            "status": "included" if seg["id"] in mapped else "omitted",
            "title": (mapped.get(seg["id"]) or {}).get("title"),
            "note": None
            if seg["id"] in mapped
            else "业务未提供该段内容，跳过渲染",
        }
        for seg in SEGMENTS
    }
    write_json(
        out_dir / "segment-map.json",
        {
            "included": {k: v.get("title") for k, v in mapped.items()},
            "plan": segment_plan,
        },
    )
    write_json(out_dir / "screen.json", screen)

    status: dict[str, Any] = {
        "mode": "full-content-visual-audio",
        "product": product,
        "content_driven": True,
        "authorized_product_packshot": authorized_product_image,
        "approval": approval_gate,
        "content_gaps": screen["content_gaps"],
        "segment_plan": segment_plan,
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
    if authorized_product_image:
        assert product_image is not None
        dest_img = ws / "public" / "product-training-assets" / f"business-{slugify(product)}.png"
        dest_img.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(product_image, dest_img)
        product_asset_url = f"/product-training-assets/{dest_img.name}"
        screen["pack_badge"] = "授权包装"

    segment_mp4s: list[Path] = []
    audio_dir = out_dir / "audio" / "sections"
    audio_dir.mkdir(parents=True, exist_ok=True)

    for seg in SEGMENTS:
        sid = seg["id"]
        if sid not in mapped:
            status["segments"][sid] = {
                "status": "omitted",
                "reason": "业务未提供该段",
            }
            print(f"[skip] {sid} {seg['label']} （空段跳过）")
            continue

        sec = mapped[sid]
        narration = str(sec.get("narration") or "").strip()
        if not segment_has_content(sec):
            status["segments"][sid] = {
                "status": "omitted",
                "reason": "旁白为空",
            }
            print(f"[skip] {sid} {seg['label']} （无旁白）")
            continue

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
            "status": "included",
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
        status["mp4"] = {
            "ok": True,
            "path": str(final),
            "segments": len(segment_mp4s),
            "omitted": [
                s["id"]
                for s in SEGMENTS
                if status["segments"].get(s["id"], {}).get("status") == "omitted"
            ],
        }
        status["ok"] = True
    elif with_render and not segment_mp4s:
        status["ok"] = False
        status["mp4"] = {"ok": False, "error": "全部段被跳过，无成片"}
    else:
        status["ok"] = True
        status["mp4"] = {"ok": False, "error": "未请求渲染"}

    write_json(out_dir / "full-render-status.json", status)
    return status
