#!/usr/bin/env python3
"""疾病科普视频全量换主题：文案屏显 + 克隆旁白 + 风热金样分段重渲 + 拼接。

由 generate_business_video.py --template health --mode full 调用。
架构对齐 business_video_product_full.py。
"""

from __future__ import annotations

import json
import hashlib
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
sys.path.insert(0, str(ROOT / "scripts"))
from content_driven_rules import (  # noqa: E402
    extract_list_items,
    plan_list_block,
    segment_has_content,
)
from video_runtime import (  # noqa: E402
    health_render_script_rel,
    prepare_workspace as _prepare_workspace_from_kit,
    resolve_video_kit_root,
)


def gold_root() -> Path:
    """Formal kit root (production engine kit preferred over poc/gold-sample)."""
    return resolve_video_kit_root(require_node_modules=False)

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
THEME_PAYLOAD_FILES = (
    "screen.json",
    "sections.json",
    "visual-plan.json",
    "visual-coverage.json",
)


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


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip())
    return re.sub(r"-+", "-", s).strip("-")[:80] or "theme"


def prepare_workspace(run_dir: Path) -> Path:
    """Stage a disposable render workspace from the formal video runtime kit."""
    return _prepare_workspace_from_kit(run_dir, kit_root=gold_root())


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
    """Build a safe planning payload from submitted sections only.

    Gold-sample defaults contain wind-heat medical claims. They are layout examples,
    not approved content, so a new disease/theme must never inherit them. A complete
    formal screen payload comes from an approved theme package; this fallback keeps
    exact submitted wording and records every missing content field as a gap.
    """
    del sections

    gaps: list[dict[str, str]] = []

    def add_gap(field: str, reason: str) -> None:
        if not any(item["field"] == field for item in gaps):
            gaps.append({"field": field, "reason": reason})

    def narration(sid: str) -> str:
        return str((mapped.get(sid) or {}).get("narration") or "").strip()

    def exact_parts(text: str, *, max_items: int, max_len: int) -> list[str]:
        parts = [
            p.strip(" ，,。.")
            for p in re.split(r"[。！？；;\n]", text)
            if p.strip(" ，,。.")
        ]
        return [part[:max_len] for part in parts[:max_items]]

    screen: dict[str, Any] = {
        "disease_name": disease,
        "eyebrow": "中医基础知识",
        "tagline": "营运培训 · 专业赋能",
        "chapter_intro": "基础认知",
        "chapter_character": "基础认知",
        "chapter_mechanism": "病因机理",
        "chapter_symptoms": "典型症状",
        "chapter_treatment": "调理建议",
        "chapter_medication": "调理建议",
        "chapter_summary": "重点总结",
        "mechanism_title": f"{disease}相关机理",
        "symptoms_title": f"{disease}相关表现",
        "summary_title": f"{disease}总结",
        "slogan": f"内部培训 · {disease}健康知识",
        "core_heading": "审核稿要点",
        "advice_title": "生活禁忌与建议",
        "source_policy": "business-sections-only",
    }

    mechanism_nar = narration("mechanism")
    mechanism_parts = exact_parts(mechanism_nar, max_items=3, max_len=40)
    screen["mechanism_text"] = mechanism_parts
    # Do not transform a disease name into cause/mechanism claims. The equation
    # stays empty until an approved theme package supplies its exact wording.
    screen["equation_left"] = ""
    screen["equation_right"] = ""
    screen["equation_result"] = ""
    if not mechanism_parts:
        add_gap("mechanism_equation", "业务 sections 未提供已审核病因/机理表述")
    else:
        add_gap(
            "mechanism_equation",
            "已保留机理审核原文，但未提供可直接上屏的三段等式文案",
        )

    # character symptom chips — N items, never pad to gold 6
    char_nar = narration("character")
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

    treat_nar = narration("treatment")
    sym_nar = narration("symptoms")
    core = ""
    principle = re.search(
        r"(?:核心(?:原则|思路)?|调理原则)(?:是|为)?[：:]?\s*"
        r"([^，,。！？；;\n]{2,16})",
        treat_nar,
    )
    if principle:
        core = principle.group(1).strip()
    if not core:
        add_gap("treatment_principle", "业务 sections 未提供明确的已审核调理原则")
    screen["core_treatment"] = core
    screen["treatment_principle"] = core

    body_parts = exact_parts(sym_nar, max_items=3, max_len=22)
    for index in range(3):
        screen[f"core_body_{index + 1}"] = (
            body_parts[index] if index < len(body_parts) else ""
        )
    if not body_parts:
        add_gap("symptom_summary", "业务 sections 未提供已审核表现/症状原文")

    treat_parts = exact_parts(treat_nar, max_items=2, max_len=32)
    screen["treatment_line_1"] = treat_parts[0] if treat_parts else ""
    screen["treatment_line_2"] = treat_parts[1] if len(treat_parts) > 1 else ""
    if not treat_parts:
        add_gap("treatment_details", "业务 sections 未提供已审核调理建议原文")

    # advice rows — N only
    med_nar = narration("medication")
    advice_lines = extract_list_items(med_nar, max_items=6, max_len=28)
    new_advice = []
    for i, line in enumerate(advice_lines):
        new_advice.append(
            {
                "title": f"{i+1}. 要点",
                "body": line,
                "image": None,
                "transparent": True,
            }
        )
    screen["advice_items"] = new_advice
    if not advice_lines:
        add_gap("advice_items", "业务 sections 未提供已审核生活/用药建议")
    elif advice_lines:
        add_gap("advice_visuals", "建议文案已有，仍缺已批准主题包中的对应画面")
    screen["list_plans"]["advice_items"] = plan_list_block(
        module_id="advice_items",
        title="生活建议",
        items=advice_lines,
        gold_example_count=4,
    )

    def short_block(sid: str) -> str:
        parts = exact_parts(narration(sid), max_items=1, max_len=40)
        return parts[0] if parts else ""

    # summary matrix only for included content modules
    summary_items: list[dict[str, str]] = []
    if "mechanism" in mapped:
        body = short_block("mechanism")
        if body:
            summary_items.append({"title": "病因", "body": body})
    if "symptoms" in mapped:
        body = short_block("symptoms")
        if body:
            summary_items.append({"title": "症状", "body": body})
    if "treatment" in mapped:
        body = short_block("treatment")
        if body:
            summary_items.append({"title": "调理", "body": body})
    if "medication" in mapped:
        body = short_block("medication")
        if body:
            summary_items.append({"title": "建议", "body": body})
    if not summary_items:
        add_gap("summary_items", "业务 sections 未提供可用于总结的审核原文")
    screen["summary_items"] = summary_items

    sym_bits = extract_list_items(sym_nar, max_items=3, max_len=14)
    groups = [
        {
            "number": str(index + 1),
            "title": "审核稿表现",
            "summaryLines": [bit],
            "items": [{"image": None, "label": bit[:8]}],
        }
        for index, bit in enumerate(sym_bits)
    ]
    screen["symptom_groups"] = groups
    if groups:
        add_gap("symptom_visuals", "表现文案已有，仍缺已批准主题包中的对应画面")

    known_herbs = re.findall(
        r"(桑叶|菊花|薄荷|生姜|葱白|金银花|连翘|板蓝根|甘草|陈皮|半夏|黄芪|党参|枸杞|红枣|大枣|柠檬|蜂蜜)",
        treat_nar,
    )
    screen["recipe_text"] = ""
    screen["recipe_effect"] = ""
    screen["herbs"] = [
        {"name": name, "image": None, "lines": []}
        for name in dict.fromkeys(known_herbs)
    ]
    if known_herbs:
        add_gap("herb_details", "仅识别到审核原文中的名称，未提供剂量/作用或批准画面")
    else:
        add_gap("herbs", "业务 sections 未提供已审核草本/食疗内容")

    med_names = [
        n
        for n in extract_list_items(med_nar, max_items=4, max_len=12)
        if 2 <= len(n) <= 12 and not re.search(r"[，。、是的了]", n)
    ]
    screen["medication_names"] = med_names
    if not med_names:
        add_gap("medication_names", "业务 sections 未提供可直接上屏的已审核药品名称")

    screen["content_gaps"] = gaps

    return screen


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
    ffmpeg = media_tool("ffmpeg")
    ffprobe = media_tool("ffprobe")
    if ffmpeg:
        env["FFMPEG_PATH"] = env.get("FFMPEG_PATH") or ffmpeg
    if ffprobe:
        env["FFPROBE_PATH"] = env.get("FFPROBE_PATH") or ffprobe
    # Relative out path keeps Revideo public/ audio resolution inside workspace
    cmd = [
        "node",
        health_render_script_rel(),
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


def theme_package_payload_sha256(theme_package: Path) -> str:
    """Hash the exact content and visual assets covered by a theme approval."""
    pkg = theme_package.resolve()
    files: list[Path] = []
    for name in THEME_PAYLOAD_FILES:
        path = pkg / name
        if not path.is_file():
            raise FileNotFoundError(f"主题包缺少审批载荷文件: {path}")
        files.append(path)
    assets = pkg / "assets"
    if assets.is_dir():
        files.extend(sorted(path for path in assets.rglob("*") if path.is_file()))

    digest = hashlib.sha256()
    for path in files:
        rel = path.relative_to(pkg).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def require_theme_package_approval(theme_package: Path) -> dict[str, Any]:
    """Require a complete visual review bound to the current package payload."""
    pkg = theme_package.resolve()
    if not pkg.is_dir():
        return {"ok": False, "error": f"主题包不存在: {pkg}"}
    approval_path = pkg / "approval.json"
    if not approval_path.is_file():
        return {
            "ok": False,
            "error": (
                f"缺少 approval.json。请先打开 {pkg / 'review.html'} 全部过目后写入批准。"
            ),
        }
    try:
        payload_sha256 = theme_package_payload_sha256(pkg)
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}

    approval = load_json(approval_path)
    if not approval.get("visuals_approved"):
        return {
            "ok": False,
            "error": (
                "画面尚未全部过目批准（approval.visuals_approved != true）。"
                f"请审阅 {pkg / 'review.html'} 后更新 approval.json。"
            ),
            "approval": approval,
        }
    if not approval.get("approved_by"):
        return {
            "ok": False,
            "error": "approval.json 须填写 approved_by（过目人）",
            "approval": approval,
        }
    if not approval.get("approved_at"):
        return {
            "ok": False,
            "error": "approval.json 须填写 approved_at（过目时间）",
            "approval": approval,
        }
    approved_hash = approval.get("approved_payload_sha256")
    if approved_hash != payload_sha256:
        return {
            "ok": False,
            "error": (
                "主题包审批 SHA-256 与当前内容不一致；内容或画面在审批后发生了变化，"
                "请重新打开 review.html 全部过目并更新 approved_payload_sha256。"
            ),
            "approval": approval,
            "payload_sha256": payload_sha256,
        }

    screen = load_json(pkg / "screen.json")
    content_gaps = screen.get("content_gaps") or []
    if content_gaps:
        return {
            "ok": False,
            "error": "主题包仍有内容缺口，禁止进入正式渲染",
            "approval": approval,
            "content_gaps": content_gaps,
            "payload_sha256": payload_sha256,
        }
    visual_plan = load_json(pkg / "visual-plan.json")
    unresolved = [
        slot
        for slot in visual_plan.get("slots") or []
        if slot.get("status") not in {"library_matched", "theme_local"}
    ]
    if unresolved:
        return {
            "ok": False,
            "error": "主题包仍有未完成画面槽位，禁止进入正式渲染",
            "approval": approval,
            "unresolved_visuals": unresolved,
            "payload_sha256": payload_sha256,
        }
    return {
        "ok": True,
        "approval": approval,
        "package": str(pkg),
        "payload_sha256": payload_sha256,
    }


def inject_theme_assets(ws: Path, theme_package: Path) -> dict[str, int]:
    """把主题包 assets 拷入渲染 workspace 的 public 槽位目录。"""
    assets = theme_package / "assets"
    mapping = [
        ("symptoms", ws / "public" / "production-symptoms"),
        ("herbs", ws / "public" / "treatment-assets"),
        ("advice", ws / "public" / "advice-assets"),
        ("mechanism", ws / "public" / "mechanism-assets"),
    ]
    counts: dict[str, int] = {}
    for src_name, dest in mapping:
        src = assets / src_name
        if not src.is_dir():
            counts[src_name] = 0
            continue
        dest.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in src.iterdir():
            if f.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"} and f.is_file():
                shutil.copy2(f, dest / f.name)
                n += 1
        counts[src_name] = n
    return counts


def run_health_full(
    *,
    content: dict[str, Any],
    out_dir: Path,
    voice_pack_dir: Path,
    with_tts: bool,
    with_render: bool,
    theme_package: Path | None = None,
    require_visual_approval: bool = True,
) -> dict[str, Any]:
    disease = content["theme"]
    sections = content["sections"]
    real_sections = [section for section in sections if segment_has_content(section)]
    if with_render and len(real_sections) > len(SEGMENTS):
        extra = real_sections[len(SEGMENTS) :]
        return {
            "ok": False,
            "error": (
                f"健康正式成片固定为 7 段，检测到 {len(real_sections)} 段审核内容；"
                "额外内容不得静默丢弃，请合并或重新确认 7 段结构。"
            ),
            "extra_sections": [str(item.get("title") or "") for item in extra],
        }
    mapped = map_sections_to_segments(sections, disease)
    if not mapped:
        return {"ok": False, "error": "未映射到任何有效段落（请提供带旁白的 sections）"}
    missing_segments = [seg["id"] for seg in SEGMENTS if seg["id"] not in mapped]
    if with_render and missing_segments:
        return {
            "ok": False,
            "error": f"健康正式成片需要完整 7 段，当前缺少: {', '.join(missing_segments)}",
            "missing_segments": missing_segments,
        }
    theme_meta: dict[str, Any] = {}
    screen: dict[str, Any]
    if theme_package is not None:
        gate = require_theme_package_approval(theme_package)
        if require_visual_approval and not gate.get("ok"):
            return {
                "ok": False,
                "error": gate.get("error"),
                "theme_package": str(theme_package),
                "gate": gate,
            }
        # Prefer frozen screen from theme package (visual planner output)
        screen_path = theme_package / "screen.json"
        if screen_path.is_file():
            screen = load_json(screen_path)
        else:
            screen = extract_screen_fields(disease, mapped, sections)
        language_id = None
        if (theme_package / "package.json").is_file():
            language_id = load_json(theme_package / "package.json").get("language_id")
        theme_meta = {
            "path": str(theme_package.resolve()),
            "approval": gate.get("approval"),
            "payload_sha256": gate.get("payload_sha256"),
            "language_id": language_id,
        }
        if (theme_package / "visual-coverage.json").is_file():
            theme_meta["visual_coverage"] = load_json(
                theme_package / "visual-coverage.json"
            )
    else:
        # 兼容旧路径：无主题包时仍可规划，但正式渲染应使用主题包
        screen = extract_screen_fields(disease, mapped, sections)
        if with_render and require_visual_approval:
            return {
                "ok": False,
                "error": (
                    "高质量换主题出片须提供 --theme-package（含 review 过目与 approval）。"
                    "请先：python3 scripts/build_health_theme_package.py ..."
                ),
            }

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
        "content_gaps": screen.get("content_gaps") or [],
        "segment_plan": segment_plan,
        "theme_package": theme_meta or None,
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
    if theme_package is not None:
        status["injected_assets"] = inject_theme_assets(ws, theme_package)
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
        if not segment_has_content(sec):
            status["segments"][sid] = {
                "status": "omitted",
                "reason": "旁白为空",
            }
            print(f"[skip] health/{sid} {seg['label']} （无旁白）")
            continue

        wav_name = f"business-{sid}.wav"
        wav_ws = public_audio / wav_name
        wav_out = audio_dir / f"{sid}.wav"

        if with_tts:
            print(f"[tts] health/{sid} {seg['label']} …")
            tts_text = narration
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

        base = load_json(gold_root() / seg["json"])
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
