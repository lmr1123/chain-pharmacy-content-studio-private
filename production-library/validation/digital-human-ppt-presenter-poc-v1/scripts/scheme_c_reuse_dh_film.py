#!/usr/bin/env python3
"""方案 C 业务审片：复用已有单段数字人，不新生成 HeyGen。

产品规则（2026-08-08 锁定，见 PRODUCT-MODE-presenter-scheme-C.md）：
  - 关键页：讲解安全版收窄布局 + 动态数字人（复用 v6.2 样片）
  - 非关键页：全宽金样布局放大课件内容，**不叠静帧人**（禁止「假站人」）
  - 布局从 PPT 比例资产选用，禁止后期强行拉升画面
  - 零新增 HeyGen

用法（POC 根目录）：
  python3 scripts/scheme_c_reuse_dh_film.py
  python3 scripts/scheme_c_reuse_dh_film.py --variant A --static-sec 2.2
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
# 关键页用讲解安全版静帧（仅作对照；动态段已含合成）
QA_PRESENTER = OUT / "qa-presenter-v1"
# 非关键页：全宽金样比例（内容铺满，含右侧图），禁止塞静帧人
QA_FULL = (
    ROOT.parents[0]  # …/validation
    / "courseware"
    / "gold-samples"
    / "uri-shenke-health-pptx-gold-v1"
    / "web"
    / "media"
    / "slides"
)
STATE = ROOT / "work" / "job-state.json"
CANVAS_W, CANVAS_H = 1920, 1080

# 默认关键页 = 疾病概览（与现有 15s 旁白 / 动态样片对应）
DEFAULT_KEY_PAGES = {3}

VARIANTS = {
    "A": {
        "label": "药师站姿",
        "dynamic": OUT / "ppt-presenter-15s-A-pharmacist-standing.mp4",
        "note": "与静帧 cutout 同 IP，整片人物一致",
    },
    "B": {
        "label": "商务托腮",
        "dynamic": OUT / "ppt-presenter-15s-B-business-chin.mp4",
        "note": "动态为商务像；静帧仍为药师 cutout（仅演示节奏）",
    },
    "C": {
        "label": "商务站姿",
        "dynamic": OUT / "ppt-presenter-15s-C-business-standing.mp4",
        "note": "动态为商务像；静帧仍为药师 cutout（仅演示节奏）",
    },
}


def load_font(size: int) -> ImageFont.ImageFont:
    for p in (
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size, index=0)
            except OSError:
                pass
    return ImageFont.load_default()


def make_badge(text: str) -> Image.Image:
    font = load_font(28)
    pad_x, pad_y = 16, 10
    tmp = Image.new("RGBA", (8, 8))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    im = Image.new("RGBA", (tw + pad_x * 2, th + pad_y * 2), (26, 95, 180, 220))
    d = ImageDraw.Draw(im)
    d.text((pad_x - bb[0], pad_y - bb[1]), text, font=font, fill=(255, 255, 255, 255))
    return im


def load_slide_full(page: int) -> Image.Image:
    """非关键页：全宽金样静帧。只用 resize 到 16:9 画布，不改变构图比例（无 crop/强拉）。"""
    src = QA_FULL / f"slide-{page:02d}.png"
    if not src.exists():
        raise FileNotFoundError(src)
    im = Image.open(src).convert("RGB")
    if im.size != (CANVAS_W, CANVAS_H):
        # 等比适配到 1920×1080（金样多为 16:9 同源，仅分辨率不同）
        im = im.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    return im

def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def encode_still_clip(png: Path, sec: float, out_mp4: Path, fps: int = 25):
    """静帧 + 静音，固定时长。"""
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(png),
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t",
        f"{sec:.3f}",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        raise RuntimeError(f"encode still failed: {out_mp4.name}")


def prepare_dynamic_clip(src: Path, out_mp4: Path):
    """复用动态数字人片段：统一 25fps/AAC，并遮掉左下角 A/B/C 选型标签。"""
    # 标签约在左下；用浅色矩形盖住（业务整片不需要选型角标）
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        "fps=25,drawbox=x=20:y=1000:w=360:h=70:color=0xE8F2FA@1:t=fill",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        raise RuntimeError("prepare dynamic failed")


def concat_clips(clips: list[Path], out: Path):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        list_path = Path(f.name)
        for c in clips:
            # concat demuxer 需要 escaped path
            p = str(c.resolve()).replace("'", "'\\''")
            f.write(f"file '{p}'\n")
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-2500:], file=sys.stderr)
            raise RuntimeError("concat failed")
    finally:
        list_path.unlink(missing_ok=True)


def write_endcard(path: Path, variant: str, key_pages: set[int], static_sec: float):
    im = Image.new("RGB", (CANVAS_W, CANVAS_H), (245, 249, 252))
    d = ImageDraw.Draw(im)
    title = load_font(42)
    body = load_font(28)
    small = load_font(22)
    d.text((80, 120), "方案 C · 业务审片（复用数字人 · 未新生成）", font=title, fill=(26, 95, 180))
    lines = [
        f"动态关键页：第 {', '.join(str(p) for p in sorted(key_pages))} 页（讲解安全版 + 数字人侧讲）",
        f"非关键页：全宽金样布局放大课件 · 每页约 {static_sec:.1f}s · 不叠静帧人",
        "布局从 PPT 双比例导出选用，禁止后期强行拉升画面",
        "合成规范：v6.2；HeyGen 零新增调用",
        "产品可复用：其他课件同样「关键页收窄+人 / 其余全宽无人」",
    ]
    y = 240
    for line in lines:
        d.text((80, y), "·  " + line, font=body, fill=(40, 55, 70))
        y += 56
    d.text((80, 980), "仅限内部学习 · POC 非整课终稿", font=small, fill=(120, 130, 140))
    im.save(path, quality=92)


def run(variant: str, static_sec: float, key_pages: set[int], pages: list[int]):
    cfg = VARIANTS[variant]
    dyn_src = cfg["dynamic"]
    if not dyn_src.exists():
        raise FileNotFoundError(f"缺少动态样片: {dyn_src}")
    if not QA_FULL.is_dir():
        raise FileNotFoundError(f"缺少全宽金样静帧目录: {QA_FULL}")

    out_film = OUT / f"scheme-c-reuse-{variant}-film.mp4"
    work = OUT / f"_scheme_c_work_{variant}"
    work.mkdir(parents=True, exist_ok=True)

    clips: list[Path] = []
    plan_rows = []

    # 1) 动态关键页准备（已是讲解安全版 + 数字人）
    dyn_clip = work / "key-dynamic.mp4"
    print(f"prepare dynamic from {dyn_src.name} …")
    prepare_dynamic_clip(dyn_src, dyn_clip)
    dyn_dur = ffprobe_duration(dyn_clip)

    # 2) 逐页：关键页=动态侧讲；非关键页=全宽课件无人
    for page in pages:
        if page in key_pages:
            clips.append(dyn_clip)
            plan_rows.append(
                {
                    "page": page,
                    "mode": "dynamic_presenter",
                    "layout": "presenter_narrow",
                    "person": "dynamic_dh_reuse",
                    "duration_s": round(dyn_dur, 2),
                    "source": str(dyn_src.relative_to(ROOT)),
                }
            )
            print(f"  page {page:02d}  DYNAMIC presenter  {dyn_dur:.1f}s")
            continue

        slide = load_slide_full(page)
        png = work / f"page-{page:02d}.png"
        slide.save(png)
        mp4 = work / f"page-{page:02d}.mp4"
        encode_still_clip(png, static_sec, mp4)
        clips.append(mp4)
        plan_rows.append(
            {
                "page": page,
                "mode": "still_full_width",
                "layout": "full_width_gold",
                "person": "none",
                "duration_s": static_sec,
                "source": str((QA_FULL / f"slide-{page:02d}.png")),
            }
        )
        print(f"  page {page:02d}  FULL-WIDTH no-person  {static_sec:.1f}s")

    # 3) 片尾说明卡
    end_png = work / "endcard.png"
    end_mp4 = work / "endcard.mp4"
    write_endcard(end_png, variant, key_pages, static_sec)
    encode_still_clip(end_png, 4.0, end_mp4)
    clips.append(end_mp4)
    plan_rows.append({"page": "endcard", "mode": "info", "duration_s": 4.0})

    print(f"concat {len(clips)} clips → {out_film.name}")
    concat_clips(clips, out_film)
    total = ffprobe_duration(out_film)

    preview = out_film.with_name(out_film.stem + "-frame.jpg")
    subprocess.run(
        ["ffmpeg", "-y", "-ss", "8", "-i", str(out_film), "-frames:v", "1", str(preview)],
        capture_output=True,
    )

    plan = {
        "scheme": "C",
        "mode": "reuse_single_dh_no_heygen",
        "product_rules": "PRODUCT-MODE-presenter-scheme-C.md",
        "variant": variant,
        "variant_label": cfg["label"],
        "note_zh": cfg["note"],
        "key_pages": sorted(key_pages),
        "static_sec": static_sec,
        "total_duration_s": round(total, 2),
        "output": str(out_film.relative_to(ROOT)),
        "layout_policy_zh": (
            "关键页=讲解安全版收窄+动态数字人；"
            "非关键页=全宽金样内容放大、无人；"
            "禁止静帧站人；禁止后期强行拉升构图"
        ),
        "pages": plan_rows,
        "business_message_zh": (
            "方案 C 节奏样片（零新增 HeyGen）："
            "仅关键页侧讲数字人；其余页全宽课件无人。"
            "后续其他课件同模式：先改 PPT 双布局，再叠人。"
        ),
    }
    plan_path = OUT / f"scheme-c-reuse-{variant}-plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    # job-state
    state = {}
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    outs = state.setdefault("outputs", {})
    outs["scheme_c_reuse_film"] = str(out_film.relative_to(ROOT))
    outs["scheme_c_reuse_plan"] = str(plan_path.relative_to(ROOT))
    state["status"] = "scheme_c_reuse_film_ready_for_business"
    state["progress_summary_zh"] = (
        f"方案C整片（复用{variant}动态，无新HeyGen）已出，待业务看整体节奏。"
    )
    done = state.setdefault("done", [])
    tag = "scheme_c_reuse_single_dh_film"
    if tag not in done:
        done.append(tag)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK {out_film}  ({out_film.stat().st_size // 1024} KB, {total:.1f}s)")
    print(f"plan {plan_path}")
    return out_film


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--variant",
        choices=list(VARIANTS),
        default="A",
        help="复用哪条已合成动态样片（默认 A 药师，与静帧 cutout 一致）",
    )
    ap.add_argument("--static-sec", type=float, default=2.2, help="非关键页静帧时长")
    ap.add_argument(
        "--key-pages",
        type=int,
        nargs="*",
        default=sorted(DEFAULT_KEY_PAGES),
        help="动态关键页号（默认仅 3）",
    )
    ap.add_argument(
        "--pages",
        type=int,
        nargs="*",
        default=list(range(1, 19)),
        help="参与成片的页（默认 1–18 全页）",
    )
    args = ap.parse_args()
    run(args.variant, args.static_sec, set(args.key_pages), list(args.pages))


if __name__ == "__main__":
    main()
