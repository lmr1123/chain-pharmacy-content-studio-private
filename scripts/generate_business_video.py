#!/usr/bin/env python3
"""业务视频绿线：内容 → 交付包 → 换文案/屏显/包装 → 克隆旁白 → 分段重渲 MP4。

用法示例：

  # 仅规划包（无 TTS）
  python3 scripts/generate_business_video.py \\
    --template product --sections-json path/to/sections.json

  # 商品培训视频全量（文案+画面槽位+包装图+旁白+分段重渲）
  .venv-qwen-tts/bin/python scripts/generate_business_video.py \\
    --template product --sections-json path/to/sections.json \\
    --with-tts --with-mp4 \\
    --product-image path/to/pack.png

  # 疾病科普视频全量（风热金样工程数据驱动 · 7 段重渲）
  .venv-qwen-tts/bin/python scripts/generate_business_video.py \\
    --template health --sections-json path/to/sections.json \\
    --with-tts --with-mp4

  # 旧：仅叠旁白到金样壳（不推荐，仅兼容）
  ... --mode audio-shell --with-tts --with-mp4

sections.json：
  {
    "theme": "商品名",
    "sections": [
      {"title": "开场", "narration": "审核旁白……"},
      {"title": "核心功效", "narration": "……"}
    ]
  }
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _import_parse_video_docx():
    """Lazy import so --sections-json works in TTS-only venvs without python-docx."""
    sys.path.insert(0, str(ROOT / "poc" / "video-training-natural-import"))
    sys.path.insert(0, str(ROOT / "poc" / "courseware-export" / "text-word-import"))
    from import_universal_video_content import parse_video_docx

    return parse_video_docx


TEMPLATES: dict[str, dict[str, Any]] = {
    "product-video-faithful-v1": {
        "aliases": ["product", "q10", "商品培训视频"],
        "video_type": "product",
        "template_id": "template.product-training-faithful-v1",
        "style_pack_id": "style-pack.reference-product-blue-v1",
        "name_zh": "商品培训视频（如辅酶 Q10）",
        "settled": ROOT
        / "production-library/templates/settled/product-video-faithful-v1",
        "gold_mp4": ROOT
        / "production-library/templates/settled/product-video-faithful-v1"
        / "辅酶Q10_商品培训视频_金样_v1.mp4",
        "voice_pack": ROOT
        / "production-library/voices/reference-pharmacist-qwen-v1",
        "segment_labels": [
            "开场",
            "核心讲解",
            "品牌品类",
            "核心功效",
            "产品特点",
            "适宜人群",
            "联合用药",
            "总结",
        ],
    },
    "health-video-reference-tech-v1": {
        "aliases": ["health", "wind-heat", "风热", "疾病科普视频"],
        "video_type": "health",
        "template_id": "template.health-reference-tech-v1",
        "style_pack_id": "style-pack.reference-medical-tech-v1",
        "name_zh": "疾病科普视频（如风热证）",
        "settled": ROOT
        / "production-library/templates/settled/health-video-reference-tech-v1",
        "gold_mp4": ROOT
        / "production-library/templates/settled/health-video-reference-tech-v1"
        / "风热证_疾病科普视频_金样_v1.mp4",
        "voice_pack": ROOT
        / "production-library/voices/reference-pharmacist-qwen-v1",
        "segment_labels": [
            "开场",
            "人物情境",
            "病因机理",
            "典型症状",
            "治疗思路",
            "用药建议",
            "总结",
        ],
    },
}

DEFAULT_TEMPO = 1.16
MAX_TEMPO = 1.18
LEAD_IN = 0.06
LEAD_OUT = 0.10
CROSSFADE = 0.035
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"


def resolve_template(key: str) -> tuple[str, dict[str, Any]]:
    k = key.strip()
    if k in TEMPLATES:
        return k, TEMPLATES[k]
    low = k.lower()
    for slug, meta in TEMPLATES.items():
        if low == slug or low in {a.lower() for a in meta["aliases"]}:
            return slug, meta
        if k in meta["aliases"] or k == meta["name_zh"]:
            return slug, meta
    raise SystemExit(
        f"未知模板: {key}；可选: {', '.join(TEMPLATES)} / product / health"
    )


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80] or "video-run"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_voice_pack(pack_dir: Path) -> dict[str, Any]:
    pack_json = pack_dir / "voice-pack.json"
    if not pack_json.exists():
        raise SystemExit(f"缺少 voice pack: {pack_json}")
    pack = json.loads(pack_json.read_text(encoding="utf-8"))
    prompt = pack_dir / (pack.get("prompt", {}) or {}).get("audio", "prompt.wav")
    ref_text = (pack.get("prompt", {}) or {}).get("ref_text")
    if not ref_text:
        ref_path = pack_dir / "ref_text.txt"
        ref_text = ref_path.read_text(encoding="utf-8").strip() if ref_path.exists() else ""
    if not prompt.exists() or not ref_text:
        raise SystemExit(f"voice pack 不完整: {pack_dir}")
    return {
        "id": pack.get("id", "voice.reference-pharmacist-qwen-v1"),
        "prompt_audio": prompt,
        "ref_text": ref_text,
        "pack_dir": pack_dir,
        "raw": pack,
    }


def sections_from_docx(docx: Path, video_type: str, asset_root: Path) -> dict[str, Any]:
    parse_video_docx = _import_parse_video_docx()
    manifest = parse_video_docx(docx, asset_root, video_type)
    sections = []
    for sec in manifest.get("sections") or []:
        paras = sec.get("approved_narration") or []
        text = "\n".join(p for p in paras if str(p).strip())
        if not text.strip():
            continue
        sections.append(
            {
                "title": sec.get("title") or f"板块{len(sections)+1}",
                "narration": text.strip(),
                "images": sec.get("images") or [],
            }
        )
    theme = (manifest.get("video") or {}).get("theme") or docx.stem
    return {
        "theme": theme,
        "sections": sections,
        "source": {"kind": "docx", "path": str(docx)},
        "routing": manifest.get("routing"),
        "raw_manifest": manifest,
    }


def sections_from_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"theme": path.stem, "sections": data}
    sections = []
    for i, sec in enumerate(data.get("sections") or []):
        nar = sec.get("narration") or sec.get("approved_narration") or sec.get("text") or ""
        if isinstance(nar, list):
            nar = "\n".join(str(x).strip() for x in nar if str(x).strip())
        nar = str(nar).strip()
        if not nar:
            continue
        sections.append(
            {
                "title": sec.get("title") or sec.get("heading") or f"板块{i+1}",
                "narration": nar,
                "images": sec.get("images") or [],
            }
        )
    return {
        "theme": data.get("theme") or path.stem,
        "sections": sections,
        "source": {"kind": "json", "path": str(path)},
    }


def build_gap_report(content: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    gaps = []
    for i, sec in enumerate(content["sections"]):
        imgs = sec.get("images") or []
        if not imgs:
            gaps.append(
                {
                    "id": f"gap-section-{i+1}-image",
                    "section": sec["title"],
                    "kind": "optional_image",
                    "message": "本板块未附授权图；无图可继续，有包装/Logo 请业务补传",
                    "business_provides": True,
                }
            )
    gaps.append(
        {
            "id": "gap-visual-shell",
            "kind": "visual_shell",
            "message": (
                "本绿线默认复用金样画面时间轴；完整换包装/插画重渲需后续分段渲染。"
                "旁白以业务审核原文为准。"
            ),
            "business_provides": False,
        }
    )
    return {
        "schema": "business-gap-list-v1",
        "template_id": meta["template_id"],
        "style_pack_id": meta["style_pack_id"],
        "gap_count": len(gaps),
        "gaps": gaps,
    }


def build_storyboard_html(content: dict[str, Any], meta: dict[str, Any], out: Path) -> None:
    cards = []
    for i, sec in enumerate(content["sections"], 1):
        nar = (
            str(sec["narration"])
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )
        title = (
            str(sec["title"])
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        cards.append(
            f"""
<article style="border:1px solid #ddd;border-radius:12px;padding:14px 16px;margin:0 0 12px;background:#fff">
  <header style="display:flex;gap:10px;align-items:baseline">
    <span style="font-weight:800;color:#2b6cb0">{i:02d}</span>
    <h2 style="margin:0;font-size:16px">{title}</h2>
  </header>
  <p style="margin:10px 0 0;line-height:1.65;color:#222">{nar}</p>
</article>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<title>{content['theme']} · 分镜预览</title>
<style>
body{{font-family:PingFang SC,Microsoft YaHei,sans-serif;background:#f6f7f9;margin:0;padding:24px}}
.wrap{{max-width:880px;margin:0 auto}}
h1{{font-size:22px;margin:0 0 6px}}
.meta{{color:#666;font-size:13px;margin-bottom:18px}}
</style></head><body><div class="wrap">
<h1>{content['theme']}</h1>
<p class="meta">模板：{meta['name_zh']} · style_pack：{meta['style_pack_id']} · 板块 {len(content['sections'])} 个</p>
{''.join(cards)}
</div></body></html>
"""
    out.write_text(html, encoding="utf-8")


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
        try:
            r = subprocess.run(
                [str(py), "-c", "from mlx_audio.tts.utils import load_model"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return None


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def generate_section_tts(
    *,
    text: str,
    out_wav: Path,
    voice: dict[str, Any],
    py: Path,
) -> dict[str, Any]:
    """Generate one semantic-block wav via Qwen3 clone in the TTS venv."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    worker = out_wav.parent / f"_tts_worker_{out_wav.stem}.py"
    worker.write_text(
        f"""
import json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
import mlx.core as mx
from mlx_audio.tts.utils import load_model

text = {text!r}
ref_audio = {str(voice['prompt_audio'])!r}
ref_text = {voice['ref_text']!r}
out = {str(out_wav)!r}
model_id = {MODEL_ID!r}
tempo = {DEFAULT_TEMPO}

model = load_model(model_id)
sr = model.sample_rate
results = list(model.generate(
    text=text,
    voice="",
    speed=1.0,
    lang_code="Chinese",
    ref_audio=ref_audio,
    ref_text=ref_text,
))
if not results:
    raise SystemExit("TTS empty")
chunks = []
for r in results:
    arr = np.array(r.audio, copy=True)
    if arr.ndim > 1:
        arr = arr.reshape(-1)
    chunks.append(arr)
audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
raw_path = Path(out).with_suffix(".raw.wav")
sf.write(raw_path, audio, sr)
# mild tempo
import subprocess
subprocess.run([
    "ffmpeg","-loglevel","error","-y","-i",str(raw_path),
    "-af",f"atempo={{tempo:.6f}},aresample={{sr}}",
    str(out),
], check=True)
raw_path.unlink(missing_ok=True)
print(json.dumps({{"ok": True, "sample_rate": sr}}))
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
            raise RuntimeError(
                f"TTS failed for {out_wav.name}: {r.stderr[-800:] or r.stdout[-800:]}"
            )
    finally:
        worker.unlink(missing_ok=True)

    # lead in/out pad via ffmpeg
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
    dur = wav_duration(out_wav)
    return {
        "file": str(out_wav.relative_to(out_wav.parents[1]) if False else out_wav.name),
        "path": str(out_wav),
        "duration_s": round(dur, 3),
        "tempo": DEFAULT_TEMPO,
        "chars": len(re.sub(r"\s+", "", text)),
    }


def concat_wavs(paths: list[Path], out: Path, gap_s: float = 0.12) -> float:
    """Concatenate mono wavs with short gaps using ffmpeg."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if not paths:
        raise ValueError("no wavs")
    if len(paths) == 1:
        shutil.copy2(paths[0], out)
        return wav_duration(out)
    list_file = out.with_suffix(".concat.txt")
    silence = out.parent / "_gap.wav"
    # create silence matching first file format
    with wave.open(str(paths[0]), "rb") as w0:
        sr = w0.getframerate()
        ch = w0.getnchannels()
        sw = w0.getsampwidth()
    n = int(sr * gap_s)
    with wave.open(str(silence), "wb") as ws:
        ws.setnchannels(ch)
        ws.setsampwidth(sw)
        ws.setframerate(sr)
        ws.writeframes(b"\x00" * n * ch * sw)
    lines = []
    for i, p in enumerate(paths):
        lines.append(f"file '{p.resolve()}'")
        if i < len(paths) - 1:
            lines.append(f"file '{silence.resolve()}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
            str(list_file),
            "-c",
            "copy",
            str(out),
        ],
        check=True,
    )
    silence.unlink(missing_ok=True)
    list_file.unlink(missing_ok=True)
    return wav_duration(out)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def mux_audio_on_gold(
    *,
    gold_mp4: Path,
    narration_wav: Path,
    out_mp4: Path,
) -> dict[str, Any]:
    """Overlay new narration on gold video; stretch/pad to match audio."""
    if not gold_mp4.exists():
        raise FileNotFoundError(gold_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    v_dur = probe_duration(gold_mp4)
    a_dur = probe_duration(narration_wav)
    # match video length to audio (prefer extend/slow slightly rather than cut speech)
    if a_dur <= 0.1:
        raise RuntimeError("narration too short")
    ratio = a_dur / v_dur if v_dur > 0 else 1.0
    # setpts: >1 slows video
    vf = f"setpts=PTS*{ratio:.6f}" if abs(ratio - 1.0) > 0.02 else "null"
    cmd = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(gold_mp4),
        "-i",
        str(narration_wav),
        "-filter_complex",
        f"[0:v]{vf}[v];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-16:LRA=7:TP=-1.5[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return {
        "path": str(out_mp4),
        "gold_duration_s": round(v_dur, 3),
        "audio_duration_s": round(a_dur, 3),
        "video_time_stretch": round(ratio, 4),
        "method": "gold-visual-shell + cloned-narration-mux",
    }


def write_delivery_md(
    path: Path,
    *,
    content: dict[str, Any],
    meta: dict[str, Any],
    slug: str,
    status: dict[str, Any],
) -> None:
    mp4 = status.get("mp4")
    tts = status.get("tts")
    lines = [
        f"# 交付说明 · {content['theme']}",
        "",
        f"- 模板：{meta['name_zh']}（`{meta['template_id']}`）",
        f"- style_pack：`{meta['style_pack_id']}`",
        f"- voice：`{status.get('voice_id')}`",
        f"- 运行目录：`{slug}`",
        f"- 生成时间：{status.get('created_at')}",
        "",
        "## 产物",
        "",
        "| 文件 | 说明 |",
        "|------|------|",
        "| `content.json` | 解析后的板块与旁白 |",
        "| `storyboard.html` | 分镜预览（可浏览器打开） |",
        "| `gap-report.json` | 缺口清单 |",
    ]
    if tts and tts.get("ok"):
        lines.append("| `audio/full-narration.wav` | 克隆药师旁白母带 |")
        lines.append("| `audio/sections/*.wav` | 分板块旁白 |")
    if mp4 and mp4.get("ok"):
        method = (mp4 or {}).get("method") or ""
        if "segment" in method or "full" in method or "health" in method:
            desc = "培训视频（分段重渲：文案/屏显/旁白）"
        else:
            desc = "培训视频（兼容：金样画面壳 + 新旁白）"
        lines.append(f"| `{Path(mp4['path']).name}` | {desc} |")
    lines.extend(
        [
            "",
            "## 状态",
            "",
            f"- 规划包：{'✅' if status.get('package_ok') else '❌'}",
            f"- 克隆旁白：{('✅' if tts and tts.get('ok') else ('⏭ 跳过' if not status.get('want_tts') else '❌ ' + str((tts or {}).get('error'))))}",
            f"- MP4：{('✅' if mp4 and mp4.get('ok') else ('⏭ 跳过' if not status.get('want_mp4') else '❌ ' + str((mp4 or {}).get('error'))))}",
            "",
            "## 使用说明",
            "",
            "1. 打开 `storyboard.html` 核对旁白与板块。",
            "2. 有 MP4 则可直接内训试看；需改文案后重新运行本命令。",
            "3. 商品/疾病科普 full 模式会按主题分段重渲；audio-shell 仅为兼容旧路径。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="业务视频绿线：内容→交付包→可选 TTS/MP4")
    ap.add_argument(
        "--template",
        required=True,
        help="product-video-faithful-v1 | health-video-reference-tech-v1 | product | health",
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--docx", type=Path, help="记事本式业务 Word")
    src.add_argument("--sections-json", type=Path, help="板块 JSON")
    ap.add_argument("--out-dir", type=Path, default=None, help="输出目录（默认自动）")
    ap.add_argument("--slug", type=str, default=None, help="输出目录名")
    ap.add_argument("--with-tts", action="store_true", help="生成克隆旁白")
    ap.add_argument(
        "--with-mp4",
        action="store_true",
        help="导出 MP4：product/health 默认分段重渲；audio-shell 模式为叠金样壳",
    )
    ap.add_argument(
        "--mode",
        choices=["full", "plan", "audio-shell"],
        default="full",
        help="full=换文案/画面槽位+重渲(商品/疾病科普)；plan=仅规划；audio-shell=旧叠声壳",
    )
    ap.add_argument(
        "--product-image",
        type=Path,
        default=None,
        help="授权包装图（png/jpg），写入画面 product 槽位",
    )
    ap.add_argument(
        "--copy-to-business-delivery",
        action="store_true",
        help="复制到业务包 05_交付物放这里/",
    )
    args = ap.parse_args()

    slug_key, meta = resolve_template(args.template)
    if args.with_mp4 and not args.with_tts:
        args.with_tts = True
    if args.mode == "plan":
        args.with_tts = False
        args.with_mp4 = False

    if args.docx:
        asset_root = ROOT / "tmp" / "business-video-assets" / slugify(args.docx.stem)
        content = sections_from_docx(
            args.docx.resolve(), meta["video_type"], asset_root
        )
    else:
        content = sections_from_json(args.sections_json.resolve())

    if not content["sections"]:
        raise SystemExit("未解析到任何有效板块旁白")

    theme = content["theme"]
    run_slug = args.slug or f"{slugify(theme)}-{slug_key}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out_dir = (
        args.out_dir.resolve()
        if args.out_dir
        else (ROOT / "outputs" / "business-video-runs" / run_slug)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # package
    content_out = {
        "theme": theme,
        "template_slug": slug_key,
        "template_id": meta["template_id"],
        "style_pack_id": meta["style_pack_id"],
        "name_zh": meta["name_zh"],
        "sections": content["sections"],
        "source": content.get("source"),
        "segment_labels_hint": meta["segment_labels"],
    }
    write_json(out_dir / "content.json", content_out)
    gaps = build_gap_report(content, meta)
    write_json(out_dir / "gap-report.json", gaps)
    build_storyboard_html(content, meta, out_dir / "storyboard.html")

    status: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_ok": True,
        "want_tts": bool(args.with_tts),
        "want_mp4": bool(args.with_mp4),
        "voice_id": None,
        "out_dir": str(out_dir),
    }

    voice_meta = load_voice_pack(meta["voice_pack"])
    status["voice_id"] = voice_meta["id"]
    write_json(
        out_dir / "voice-plan.json",
        {
            "voice_id": voice_meta["id"],
            "pack_dir": str(voice_meta["pack_dir"].relative_to(ROOT)),
            "pace": {"default_tempo": DEFAULT_TEMPO, "max_tempo": MAX_TEMPO},
            "forbid_system_tts": True,
            "sections": [
                {"title": s["title"], "chars": len(re.sub(r"\s+", "", s["narration"]))}
                for s in content["sections"]
            ],
        },
    )

    tts_status: dict[str, Any] = {"ok": False}
    mp4_status: dict[str, Any] = {"ok": False}
    full_status: dict[str, Any] | None = None

    # --- product / health full content+visual+audio re-render ---
    use_product_full = (
        args.mode == "full"
        and slug_key == "product-video-faithful-v1"
        and (args.with_tts or args.with_mp4)
    )
    use_health_full = (
        args.mode == "full"
        and slug_key == "health-video-reference-tech-v1"
        and (args.with_tts or args.with_mp4)
    )
    if use_product_full:
        sys.path.insert(0, str(ROOT / "scripts"))
        from business_video_product_full import run_product_full  # type: ignore

        try:
            full_status = run_product_full(
                content=content,
                out_dir=out_dir,
                voice_pack_dir=meta["voice_pack"],
                with_tts=bool(args.with_tts),
                with_render=bool(args.with_mp4),
                product_image=args.product_image.resolve()
                if args.product_image
                else None,
            )
            tts_status = {
                "ok": bool(full_status.get("ok")) and bool(args.with_tts),
                "mode": "full-segment-clone",
                "segments": (full_status or {}).get("segments"),
                "error": full_status.get("error") if full_status else None,
            }
            mp4 = (full_status or {}).get("mp4") or {}
            mp4_status = {
                "ok": bool(mp4.get("ok")),
                "path": mp4.get("path"),
                "method": "segment-rerender-content-visual-audio",
                "error": mp4.get("error") or full_status.get("error"),
            }
        except Exception as e:
            tts_status = {"ok": False, "error": str(e)}
            mp4_status = {"ok": False, "error": str(e)}
            full_status = {"ok": False, "error": str(e)}
    elif use_health_full:
        sys.path.insert(0, str(ROOT / "scripts"))
        from business_video_health_full import run_health_full  # type: ignore

        try:
            full_status = run_health_full(
                content=content,
                out_dir=out_dir,
                voice_pack_dir=meta["voice_pack"],
                with_tts=bool(args.with_tts),
                with_render=bool(args.with_mp4),
            )
            tts_status = {
                "ok": bool(full_status.get("ok")) and bool(args.with_tts),
                "mode": "full-segment-clone-health",
                "segments": (full_status or {}).get("segments"),
                "error": full_status.get("error") if full_status else None,
            }
            mp4 = (full_status or {}).get("mp4") or {}
            mp4_status = {
                "ok": bool(mp4.get("ok")),
                "path": mp4.get("path"),
                "method": "health-segment-rerender-content-visual-audio",
                "error": mp4.get("error") or full_status.get("error"),
            }
        except Exception as e:
            tts_status = {"ok": False, "error": str(e)}
            mp4_status = {"ok": False, "error": str(e)}
            full_status = {"ok": False, "error": str(e)}

    # --- legacy audio-shell path (explicit only) ---
    if args.mode == "audio-shell":
        if args.with_tts:
            py = detect_tts_python()
            if not py:
                tts_status = {
                    "ok": False,
                    "error": "未找到可用 Qwen3-TTS 环境（期望 .venv-qwen-tts）",
                }
            else:
                try:
                    audio_dir = out_dir / "audio" / "sections"
                    audio_dir.mkdir(parents=True, exist_ok=True)
                    section_reports = []
                    wavs: list[Path] = []
                    for i, sec in enumerate(content["sections"], 1):
                        wav = audio_dir / f"{i:02d}-{slugify(sec['title'])[:40]}.wav"
                        print(f"[tts] {i}/{len(content['sections'])} {sec['title']} …")
                        rep = generate_section_tts(
                            text=sec["narration"],
                            out_wav=wav,
                            voice=voice_meta,
                            py=py,
                        )
                        rep["title"] = sec["title"]
                        section_reports.append(rep)
                        wavs.append(wav)
                    full = out_dir / "audio" / "full-narration.wav"
                    full_dur = concat_wavs(wavs, full)
                    tts_status = {
                        "ok": True,
                        "python": str(py),
                        "full_narration": str(full),
                        "full_duration_s": round(full_dur, 3),
                        "sections": section_reports,
                        "mode": "audio-shell",
                    }
                    write_json(out_dir / "audio" / "tts-report.json", tts_status)
                except Exception as e:
                    tts_status = {"ok": False, "error": str(e)}
        if args.with_mp4:
            if not tts_status.get("ok"):
                mp4_status = {
                    "ok": False,
                    "error": "需要成功的 --with-tts 才能叠轨 MP4",
                }
            else:
                try:
                    gold = meta["gold_mp4"]
                    if not gold.exists():
                        alts = list(meta["settled"].glob("*.mp4"))
                        gold = next(
                            (p for p in alts if "可编辑" not in p.name),
                            alts[0] if alts else gold,
                        )
                    out_mp4 = out_dir / f"{slugify(theme)}_培训视频_v1.mp4"
                    mux = mux_audio_on_gold(
                        gold_mp4=gold,
                        narration_wav=Path(tts_status["full_narration"]),
                        out_mp4=out_mp4,
                    )
                    mp4_status = {"ok": True, **mux, "method": "audio-shell"}
                except Exception as e:
                    mp4_status = {"ok": False, "error": str(e)}

    status["tts"] = tts_status
    status["mp4"] = mp4_status
    if full_status is not None:
        status["full"] = full_status

    write_json(out_dir / "run-status.json", status)
    write_delivery_md(
        out_dir / "DELIVERY.md",
        content=content,
        meta=meta,
        slug=run_slug,
        status=status,
    )

    if args.copy_to_business_delivery:
        dest_root = (
            ROOT
            / "outputs/业务使用资料包/药店培训内容工厂-业务包/05_交付物放这里"
            / run_slug
        )
        if dest_root.exists():
            shutil.rmtree(dest_root)
        shutil.copytree(out_dir, dest_root)
        status["business_delivery_copy"] = str(dest_root)
        write_json(out_dir / "run-status.json", status)

    # summary to stdout
    summary = {
        "ok": status["package_ok"]
        and (not args.with_tts or tts_status.get("ok"))
        and (not args.with_mp4 or mp4_status.get("ok")),
        "out_dir": str(out_dir),
        "theme": theme,
        "template": slug_key,
        "mode": args.mode,
        "method": mp4_status.get("method") or tts_status.get("mode"),
        "sections": len(content["sections"]),
        "tts": tts_status.get("ok"),
        "mp4": mp4_status.get("ok"),
        "mp4_path": mp4_status.get("path"),
        "storyboard": str(out_dir / "storyboard.html"),
        "error": tts_status.get("error") or mp4_status.get("error"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
