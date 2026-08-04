#!/usr/bin/env python3
"""疾病科普视频全量换主题：文案屏显 + 克隆旁白 + 风热金样分段重渲 + 拼接。

由 generate_business_video.py --template health --mode full 调用。
架构对齐 business_video_product_full.py。
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
sys.path.insert(0, str(ROOT / "scripts"))
from content_driven_rules import (  # noqa: E402
    extract_list_items,
    plan_list_block,
    segment_has_content,
)

SEGMENTS: list[dict[str, str]] = [
    {"id": "intro", "json": "health-training-intro.json", "label": "开场"},
    {"id": "character", "json": "health-training-character.json", "label": "基础认知"},
    {"id": "mechanism", "json": "health-training-mechanism.json", "label": "病因机理"},
    {"id": "symptoms", "json": "health-training-symptoms.json", "label": "典型症状"},
    {"id": "treatment", "json": "health-training-treatment.json", "label": "调理建议"},
    {"id": "medication", "json": "health-training-medication.json", "label": "用药建议"},
    {"id": "summary", "json": "health-training-summary.json", "label": "总结"},
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
    sections: list[dict[str, Any]], disease: str
) -> dict[str, dict[str, Any]]:
    """Map business sections onto health slots. Missing slots stay absent (omit)."""
    del disease
    by_label: dict[str, dict[str, Any]] = {}
    remaining = list(sections)

    def take(keywords: list[str]) -> dict[str, Any] | None:
        for i, sec in enumerate(remaining):
            title = str(sec.get("title") or "")
            if any(k in title for k in keywords):
                return remaining.pop(i)
        return None

    order_keywords = [
        ("intro", ["开场", "片头", "引入", "标题"]),
        ("character", ["基础", "认知", "人物", "情境", "为什么", "了解", "是什么"]),
        ("mechanism", ["机理", "病因", "病机", "机制", "怎么来", "入侵"]),
        ("symptoms", ["症状", "表现", "信号", "典型"]),
        ("treatment", ["治疗", "调理", "思路", "方药", "食疗", "中药", "茶饮"]),
        ("medication", ["用药", "药品", "建议", "注意", "禁忌", "生活"]),
        ("summary", ["总结", "小结", "回顾", "重点"]),
    ]
    for sid, kws in order_keywords:
        hit = take(kws)
        if hit and segment_has_content(hit):
            by_label[sid] = hit

    leftovers = [s for s in remaining if segment_has_content(s)]
    for seg in SEGMENTS:
        sid = seg["id"]
        if sid in by_label:
            continue
        if leftovers:
            by_label[sid] = leftovers.pop(0)
    return by_label




def extract_screen_fields(
    disease: str, mapped: dict[str, dict[str, Any]], sections: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build screen payload for health-training JSON fields."""
    defaults_path = GOLD / "health-training-screen-defaults.json"
    base = load_json(defaults_path) if defaults_path.exists() else {}
    screen = deepcopy(base)

    screen["disease_name"] = disease
    screen["eyebrow"] = screen.get("eyebrow") or "中医基础知识"
    screen["tagline"] = screen.get("tagline") or "营运培训 · 专业赋能"
    screen["mechanism_title"] = f"{disease}怎么找上门？"
    screen["symptoms_title"] = f"{disease}的典型症状"
    screen["summary_title"] = f"{disease}总结"
    screen["slogan"] = f"内部培训 · {disease}健康知识"

    # equation labels by disease family (screen text, not only audio)
    eq_left, eq_right, eq_result = _equation_for_disease(disease)
    screen["equation_left"] = eq_left
    screen["equation_right"] = eq_right
    screen["equation_result"] = eq_result

    # character symptom chips — N items, never pad to gold 6
    char_nar = str((mapped.get("character") or {}).get("narration") or "")
    chips = extract_list_items(char_nar, max_items=6, max_len=8)
    screen["character_cards"] = chips
    screen["list_plans"] = {
        "character_cards": plan_list_block(
            module_id="character_cards",
            title="典型表现",
            items=chips,
            gold_example_count=6,
        )
    }

    treat_nar = str((mapped.get("treatment") or {}).get("narration") or "")
    sym_nar = str((mapped.get("symptoms") or {}).get("narration") or "")
    core = screen.get("core_treatment") or "辨证调理"
    known = re.search(
        r"(疏风清热|清热解毒|辛温解表|散寒解表|解表清热|健脾祛湿|清热利湿|温阳利水|对症支持)",
        treat_nar + " " + sym_nar,
    )
    if known:
        core = known.group(1)
    else:
        m = re.search(r"(?:核心是|记住|就是)([^，,。！？\s]{2,8})", treat_nar)
        if m and not re.search(r"[是的了在]", m.group(1)):
            core = m.group(1)
        else:
            core = _default_core_for_disease(disease)
    screen["core_treatment"] = core
    screen["treatment_principle"] = core

    body_src = sym_nar or treat_nar
    body_parts = [
        p.strip(" ，,。.")
        for p in re.split(r"[。！？；;\n]", body_src)
        if 4 <= len(p.strip()) <= 28
    ]
    if body_parts:
        screen["core_body_1"] = body_parts[0][:22]
        if len(body_parts) > 1:
            screen["core_body_2"] = body_parts[1][:22]
        if len(body_parts) > 2:
            screen["core_body_3"] = body_parts[2][:22]
    elif "symptoms" in mapped or "treatment" in mapped:
        screen["core_body_1"] = f"围绕{disease}进行辨证讲解"
        screen["core_body_2"] = "识别典型表现与调理思路"
        screen["core_body_3"] = "注意禁忌，及时就医"

    treat_parts = [
        p.strip(" ，,。.")
        for p in re.split(r"[。！？；;\n]", treat_nar)
        if 4 <= len(p.strip()) <= 36
    ]
    if treat_parts:
        screen["treatment_line_1"] = treat_parts[0][:32]
        if len(treat_parts) > 1:
            screen["treatment_line_2"] = treat_parts[1][:32]

    # advice rows — N only
    med_nar = str((mapped.get("medication") or {}).get("narration") or "")
    advice_lines = extract_list_items(med_nar, max_items=6, max_len=28)
    base_advice = screen.get("advice_items") or []
    new_advice = []
    for i, line in enumerate(advice_lines):
        item = (
            deepcopy(base_advice[i])
            if i < len(base_advice)
            else {
                "title": f"{i+1}. 要点",
                "body": line,
                "image": "ventilation-v1.png",
                "transparent": True,
            }
        )
        item["body"] = line
        if not item.get("title"):
            item["title"] = f"{i+1}. 要点"
        new_advice.append(item)
    screen["advice_items"] = new_advice
    screen["list_plans"]["advice_items"] = plan_list_block(
        module_id="advice_items",
        title="生活建议",
        items=advice_lines,
        gold_example_count=4,
    )

    def short_block(sid: str, fallback: str) -> str:
        sec = mapped.get(sid) or {}
        text = str(sec.get("narration") or "")
        parts = re.split(r"[。！？；;\n]", text)
        parts = [p.strip() for p in parts if 2 <= len(p.strip()) <= 40]
        return (parts[0] if parts else fallback)[:40]

    # summary matrix only for included content modules
    summary_items: list[dict[str, str]] = []
    if "mechanism" in mapped:
        summary_items.append(
            {"title": "病因", "body": short_block("mechanism", f"{disease}相关病因")}
        )
    if "symptoms" in mapped:
        summary_items.append(
            {"title": "症状", "body": short_block("symptoms", "注意典型表现")}
        )
    if "treatment" in mapped:
        summary_items.append({"title": "调理", "body": short_block("treatment", core)})
    if "medication" in mapped:
        summary_items.append(
            {"title": "禁忌", "body": short_block("medication", "遵医嘱，忌擅自用药")}
        )
    if not summary_items:
        summary_items = [{"title": "要点", "body": f"{disease}培训小结"}]
    screen["summary_items"] = summary_items

    sym_bits = extract_list_items(sym_nar, max_items=3, max_len=14)
    groups = screen.get("symptom_groups") or []
    for i, g in enumerate(groups):
        if i < len(sym_bits) and isinstance(g, dict):
            lines = list(g.get("summaryLines") or ["", ""])
            lines[0] = sym_bits[i]
            if len(lines) < 2:
                lines.append("")
            g["summaryLines"] = lines[:2]
            if g.get("items") and len(g["items"]) > 0:
                g["items"][0]["label"] = sym_bits[i][:8]
    # if fewer symptom labels than gold groups, keep group shells but labels only updated
    screen["symptom_groups"] = groups

    known_herbs = re.findall(
        r"(桑叶|菊花|薄荷|生姜|葱白|金银花|连翘|板蓝根|甘草|陈皮|半夏|黄芪|党参|枸杞|红枣|大枣|柠檬|蜂蜜)",
        treat_nar,
    )
    herbs = screen.get("herbs") or []
    if known_herbs:
        for i, h in enumerate(herbs):
            if i < len(known_herbs) and isinstance(h, dict):
                h["name"] = known_herbs[i]
        names = " · ".join(known_herbs[:3])
        screen["recipe_text"] = f"{names}  适量"
    screen["herbs"] = herbs

    med_names = [
        n
        for n in extract_list_items(med_nar, max_items=4, max_len=12)
        if 2 <= len(n) <= 12 and not re.search(r"[，。、是的了]", n)
    ]
    screen["medication_names"] = med_names

    return screen


def _equation_for_disease(disease: str) -> tuple[str, str, str]:
    d = disease or ""
    if "风寒" in d:
        return "💨  风邪", "❄️  寒邪", "入侵体表"
    if "风热" in d:
        return "💨  风邪", "🔥  热邪", "入侵身体"
    if "湿热" in d or "湿" in d:
        return "💧  湿邪", "🔥  热邪", "困阻中焦"
    if "感冒" in d or "外感" in d:
        return "💨  外邪", "🧍  卫气", "侵袭体表"
    if "咳嗽" in d:
        return "💨  外邪", "🫁  肺气", "宣降失常"
    return "💨  外因", "🧍  内因", f"诱发{d[:4] or '不适'}"


def _default_core_for_disease(disease: str) -> str:
    d = disease or ""
    if "风寒" in d:
        return "辛温解表"
    if "风热" in d:
        return "疏风清热"
    if "湿热" in d:
        return "清热利湿"
    if "感冒" in d or "外感" in d:
        return "解表祛邪"
    return "辨证调理"


def split_cues(text: str, duration: float) -> list[dict[str, Any]]:
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
    disease: str,
    narration: str,
    audio_public_path: str,
    duration: float,
    screen: dict,
    segment_id: str,
) -> dict:
    data = deepcopy(base)
    data["disease_name"] = disease
    data["theme"] = disease
    data["title"] = disease if segment_id == "intro" else data.get("title", disease)
    data["screen"] = screen
    data["playback_duration"] = round(duration, 3)
    if "range" in data and isinstance(data["range"], dict):
        data["range"]["duration"] = round(duration, 3)
    data["cues"] = split_cues(narration, duration) if narration else []
    data["audio"] = {
        "source": "voice.reference-pharmacist-qwen-v1",
        "file": audio_public_path,
        "disclosure": "业务主题克隆药师旁白；v5-smooth",
        "pace_policy": {
            "default_tempo": DEFAULT_TEMPO,
            "mode": "full-segment-continuous",
            "version": "v5-smooth-business-health",
        },
    }
    if segment_id == "summary":
        data["outro_start_ratio"] = float(data.get("outro_start_ratio") or (25.0 / 28.0))
    return data


def render_segment(ws: Path, segment_id: str, out_mp4: Path) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    ws_out = ws / "out" / f"{segment_id}.mp4"
    ws_out.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["FFMPEG_PATH"] = env.get("FFMPEG_PATH") or "/opt/homebrew/bin/ffmpeg"
    env["FFPROBE_PATH"] = env.get("FFPROBE_PATH") or "/opt/homebrew/bin/ffprobe"
    env["PATH"] = f"/opt/homebrew/bin:{env.get('PATH', '')}"
    # Relative out path keeps Revideo public/ audio resolution inside workspace
    cmd = [
        "node",
        "scripts/render-health-segment.mjs",
        segment_id,
        f"out/{segment_id}.mp4",
    ]
    print(f"[render] health/{segment_id} → {out_mp4.name}")
    r = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(
            f"render {segment_id} failed:\n{r.stderr[-2000:]}\n{r.stdout[-1000:]}"
        )
    if ws_out.exists():
        shutil.copy2(ws_out, out_mp4)
    elif Path(str(ws_out).replace(".mp4", "-0.mp4")).exists():
        shutil.copy2(Path(str(ws_out).replace(".mp4", "-0.mp4")), out_mp4)
    else:
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


def run_health_full(
    *,
    content: dict[str, Any],
    out_dir: Path,
    voice_pack_dir: Path,
    with_tts: bool,
    with_render: bool,
) -> dict[str, Any]:
    disease = content["theme"]
    sections = content["sections"]
    mapped = map_sections_to_segments(sections, disease)
    if not mapped:
        return {"ok": False, "error": "未映射到任何有效段落（请提供带旁白的 sections）"}
    # intro with only disease name is valid if theme present and no intro section —
    # optional: auto-include short intro when any other segment exists
    if "intro" not in mapped and mapped:
        mapped = {
            "intro": {"title": "开场", "narration": disease},
            **mapped,
        }
    screen = extract_screen_fields(disease, mapped, sections)

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
        "template": "health-video-reference-tech-v1",
        "disease": disease,
        "content_driven": True,
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
    public_audio = ws / "public" / "health-training-audio" / "business-theme"
    public_audio.mkdir(parents=True, exist_ok=True)

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
            print(f"[skip] health/{sid} {seg['label']} （空段跳过）")
            continue

        sec = mapped[sid]
        narration = str(sec.get("narration") or "").strip()
        if sid != "intro" and not segment_has_content(sec):
            status["segments"][sid] = {
                "status": "omitted",
                "reason": "旁白为空",
            }
            print(f"[skip] health/{sid} {seg['label']} （无旁白）")
            continue
        if sid == "intro" and not narration:
            narration = disease

        wav_name = f"business-{sid}.wav"
        wav_ws = public_audio / wav_name
        wav_out = audio_dir / f"{sid}.wav"

        if with_tts:
            print(f"[tts] health/{sid} {seg['label']} …")
            tts_text = (
                narration
                if sid != "intro"
                else (narration if len(narration) > 4 else f"中医基础知识，{disease}")
            )
            dur = generate_tts(
                text=tts_text,
                out_wav=wav_ws,
                prompt_audio=prompt_audio,
                ref_text=ref_text,
                py=py,  # type: ignore[arg-type]
            )
            if sid == "intro":
                dur = max(dur, 4.0)
            shutil.copy2(wav_ws, wav_out)
        else:
            return {
                "ok": False,
                "error": "full 模式需要 --with-tts 以生成与画面同步的旁白",
            }

        base = load_json(GOLD / seg["json"])
        patched = apply_content_to_json(
            base=base,
            disease=disease,
            narration=narration if sid != "intro" else tts_text,
            audio_public_path=f"/health-training-audio/business-theme/{wav_name}",
            duration=dur,
            screen=screen,
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
        final = out_dir / f"{slugify(disease)}_疾病科普视频_v1.mp4"
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
