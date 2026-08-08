#!/usr/bin/env python3
"""rembg 抠像叠 PPT 第3页（v6.2：保留原片曝光 + 固定缩放防抖）。

相对 v6.1：
  - 去掉 crush_exposure / 二次压高光，数字人 RGB 保持 HeyGen 原片
  - 缩放与锚点只在首帧标定一次，整段视频共用，消除「一大一小」抖动
  - 仍用 rembg 干净抠像 + 硬 alpha，避免白边叠浅蓝 PPT 发白

用法（在 POC 目录）：
  .venv-rembg/bin/python scripts/composite_with_rembg.py --all
  .venv-rembg/bin/python scripts/composite_with_rembg.py --key A B C --fps 20
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rembg import new_session, remove

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SLIDE = OUT / "enterprise-page03-presenter-slide-only.png"
STATE = ROOT / "work" / "job-state.json"
CANVAS_W, CANVAS_H = 1920, 1080
PERSON_LEFT = 1280
MARGIN_R, MARGIN_B = 12, 0

VARIANTS = {
    "A": {
        "label_zh": "A · 药师站姿",
        "video": OUT / "sample-15s.mp4",
        "out": OUT / "ppt-presenter-15s-A-pharmacist-standing.mp4",
        "target_h": 1040,
        "max_w": 620,
        "y_lift": 0,
    },
    "B": {
        "label_zh": "B · 商务托腮",
        "video": OUT / "sample-15s-business-chin-v1.mp4",
        "out": OUT / "ppt-presenter-15s-B-business-chin.mp4",
        "target_h": 1040,
        "max_w": 620,
        "y_lift": 0,
    },
    "C": {
        "label_zh": "C · 商务站姿",
        "video": OUT / "sample-15s-business-standing-v1.mp4",
        "out": OUT / "ppt-presenter-15s-C-business-standing.mp4",
        "target_h": 1000,
        "max_w": 680,
        "y_lift": 40,
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


def make_label(text: str) -> Image.Image:
    font = load_font(34)
    pad_x, pad_y = 18, 12
    tmp = Image.new("RGBA", (8, 8))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    im = Image.new("RGBA", (tw + pad_x * 2, th + pad_y * 2), (26, 95, 180, 225))
    d = ImageDraw.Draw(im)
    d.text((pad_x - bb[0], pad_y - bb[1]), text, font=font, fill=(255, 255, 255, 255))
    return im


def content_bbox(rgba: Image.Image, thr: int = 16) -> tuple[int, int, int, int]:
    a = np.array(rgba.split()[-1])
    ys, xs = np.where(a > thr)
    if len(xs) == 0:
        return 0, 0, rgba.width, rgba.height
    x0, x1 = max(0, int(xs.min()) - 2), min(rgba.width, int(xs.max()) + 3)
    y0, y1 = max(0, int(ys.min()) - 2), min(rgba.height, int(ys.max()) + 3)
    return x0, y0, x1, y1


def process_frame(rgb: Image.Image, session) -> Image.Image:
    """只抠像，不改曝光。硬 alpha 去掉半透明白边。"""
    buf = io.BytesIO()
    rgb.convert("RGB").save(buf, format="PNG")
    cut = remove(buf.getvalue(), session=session)
    person = Image.open(io.BytesIO(cut)).convert("RGBA")
    arr = np.array(person)
    a = arr[:, :, 3]
    # 硬 alpha：半透明边 → 全透或全不透，避免叠浅蓝 PPT 二次发白
    a = np.where(a < 50, 0, np.where(a > 180, 255, a)).astype(np.uint8)
    arr[:, :, 3] = a
    return Image.fromarray(arr, "RGBA")


def calibrate_layout(
    person: Image.Image, target_h: int, max_w: int, y_lift: int
) -> tuple[float, int, int]:
    """首帧标定：固定 scale + 固定整帧粘贴原点。

    关键帧对「整段 rembg 输出帧」用同一 scale 缩放、同一 (paste_x, paste_y) 粘贴。
    不再按每帧 content bbox 重算缩放，避免举手/掩膜抖动导致一大一小。
    位置按首帧 content 底部贴底、content 水平中心落在人物槽中线。
    """
    x0, y0, x1, y1 = content_bbox(person)
    cw, ch = max(1, x1 - x0), max(1, y1 - y0)
    scale = target_h / ch
    if cw * scale > max_w:
        scale = max_w / cw
    scale = float(scale)

    # 首帧 content 几何（源像素）→ 缩放后应对齐的画布位置
    content_cx = (x0 + x1) / 2.0
    content_bottom = float(y1)
    slot_left = PERSON_LEFT
    slot_w = CANVAS_W - PERSON_LEFT - MARGIN_R
    slot_cx = slot_left + slot_w / 2.0
    # paste_x + content_cx*scale = slot_cx
    paste_x = int(round(slot_cx - content_cx * scale))
    # paste_y + content_bottom*scale = CANVAS_H - y_lift
    paste_y = int(round(CANVAS_H - y_lift - MARGIN_B - content_bottom * scale))
    return scale, paste_x, paste_y


def place_person_stable(
    slide: Image.Image,
    person: Image.Image,
    scale: float,
    paste_x: int,
    paste_y: int,
) -> Image.Image:
    """整帧固定 scale + 固定原点粘贴（不按 content 逐帧裁切重定位）。"""
    nw = max(1, int(round(person.width * scale)))
    nh = max(1, int(round(person.height * scale)))
    person = person.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = slide.copy().convert("RGBA")
    px, py = paste_x, paste_y
    sx0 = sy0 = 0
    sx1, sy1 = nw, nh
    if px < 0:
        sx0 = -px
        px = 0
    if py < 0:
        sy0 = -py
        py = 0
    if px + (sx1 - sx0) > CANVAS_W:
        sx1 = sx0 + (CANVAS_W - px)
    if py + (sy1 - sy0) > CANVAS_H:
        sy1 = sy0 + (CANVAS_H - py)
    if sx1 > sx0 and sy1 > sy0:
        canvas.alpha_composite(person.crop((sx0, sy0, sx1, sy1)), (px, py))
    return canvas


def extract_frames(video: Path, frame_dir: Path, fps: int) -> list[Path]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(frame_dir / "f_%05d.png")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vf", f"fps={fps}", pattern],
        check=True,
        capture_output=True,
    )
    return sorted(frame_dir.glob("f_*.png"))


def encode_video(frame_dir: Path, audio_src: Path, out: Path, fps: int):
    pattern = str(frame_dir / "c_%05d.png")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        pattern,
        "-i",
        str(audio_src),
        "-map",
        "0:v",
        "-map",
        "1:a?",
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
        "-shortest",
        "-movflags",
        "+faststart",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise RuntimeError("encode failed")


def run_one(key: str, session, fps: int):
    cfg = VARIANTS[key]
    video: Path = cfg["video"]
    out: Path = cfg["out"]
    if not video.exists():
        raise FileNotFoundError(video)
    slide = Image.open(SLIDE).convert("RGBA").resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    label = make_label(cfg["label_zh"])

    with tempfile.TemporaryDirectory(prefix=f"rembg-{key}-") as td:
        td = Path(td)
        raw_dir, comp_dir = td / "raw", td / "comp"
        comp_dir.mkdir()
        frames = extract_frames(video, raw_dir, fps=fps)
        n = len(frames)
        print(f"[{key}] {cfg['label_zh']} frames={n} fps={fps}")
        t0 = time.time()

        # 首帧标定固定 scale + 固定粘贴原点（整段共用，防大小/位置抖）
        first = process_frame(Image.open(frames[0]).convert("RGB"), session)
        scale, paste_x, paste_y = calibrate_layout(
            first, cfg["target_h"], cfg["max_w"], cfg["y_lift"]
        )
        print(
            f"  fixed_scale={scale:.4f} paste=({paste_x},{paste_y}) "
            f"(full-frame lock from frame 1)"
        )

        for i, fp in enumerate(frames, 1):
            if i == 1:
                person = first
            else:
                person = process_frame(Image.open(fp).convert("RGB"), session)
            canvas = place_person_stable(slide, person, scale, paste_x, paste_y)
            canvas.alpha_composite(label, (36, CANVAS_H - label.height - 28))
            canvas.convert("RGB").save(comp_dir / f"c_{i:05d}.png")
            if i == 1 or i % 20 == 0 or i == n:
                elapsed = time.time() - t0
                eta = elapsed / i * (n - i)
                print(f"  frame {i}/{n}  elapsed={elapsed:.0f}s  eta={eta:.0f}s")

        encode_video(comp_dir, video, out, fps=fps)
        # 预览静帧
        preview = out.with_name(out.stem + "-frame.jpg")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "2", "-i", str(out), "-frames:v", "1", str(preview)],
            capture_output=True,
        )
        print(f"  OK → {out} ({out.stat().st_size // 1024} KB)  preview={preview.name}")


def update_state(keys: list[str]):
    state = {}
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    outs = state.setdefault("outputs", {})
    outs["ppt_presenter_samples"] = {
        k: str(VARIANTS[k]["out"].relative_to(ROOT)) for k in VARIANTS
    }
    outs["ppt_presenter_layout"] = {
        "version": "v6.2-rembg-original-exposure-fixed-scale",
        "note_zh": "rembg抠像；保留原片曝光；首帧标定固定缩放防抖；硬alpha去白边",
    }
    state["status"] = "ppt_presenter_abc_v6_2_ready_for_business_review"
    state["progress_summary_zh"] = (
        "PPT侧讲 A/B/C v6.2：保留原数字人曝光 + 固定缩放防大小抖动。待业务复核。"
    )
    done = state.setdefault("done", [])
    tag = "ppt_presenter_abc_v6_2_original_exposure_fixed_scale"
    if tag not in done:
        done.append(tag)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", choices=list(VARIANTS), action="append")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--fps", type=int, default=20)
    args = ap.parse_args()
    keys = list(VARIANTS) if args.all or not args.key else args.key
    print("loading rembg u2net…")
    session = new_session("u2net")
    for k in keys:
        run_one(k, session, fps=args.fps)
    update_state(keys)
    print("done", keys)


if __name__ == "__main__":
    main()
