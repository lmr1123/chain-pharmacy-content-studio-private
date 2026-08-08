#!/usr/bin/env python3
"""把 HeyGen 数字人样片叠到讲解安全版 PPT 第 3 页，输出侧讲效果视频。

布局 v4：
  - A/B：比例位置保持（业务已认可）
  - C：半身收紧裁切 + 放大，左缘对齐
  - 曝光修复：去掉错误的 colorlevels rimax（会拉爆高光）；
    用 curves 压亮部 + 温和 eq，减轻脸部白光

用法：
  python3 scripts/composite_ppt_presenter_video.py
  python3 scripts/composite_ppt_presenter_video.py --only A B
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
SLIDE = OUT / "enterprise-page03-presenter-slide-only.png"
STATE = ROOT / "work" / "job-state.json"

CANVAS_W, CANVAS_H = 1920, 1080

# —— 布局（A/B 业务认可；C 单独加大对齐）——
PERSON_LEFT = 1280
PORTRAIT_H = 1040
PORTRAIT_MAX_W = 620
LANDSCAPE_H = 1000
LANDSCAPE_MAX_W = 680

# 压曝光 v5（业务反馈仍发白 → 大幅压亮部+中亮肤色）
# - 禁止 colorlevels rimax<1
# - curves：肤色中亮区与高光一起压，纯白 1.0→0.62
# - eq：再降亮/gamma，略提饱和避免发灰
GRADE = (
    "curves=all='0/0 0.25/0.22 0.4/0.34 0.55/0.44 0.7/0.52 0.85/0.58 1/0.62',"
    "eq=brightness=-0.12:contrast=1.08:saturation=1.08:gamma=0.85"
)
COLORKEY_BC = "colorkey=0xF2F2F2:0.22:0.10"
COLORKEY_A = "colorkey=0xEDEDED:0.18:0.12"

VARIANTS = {
    "A": {
        "tag": "pharmacist_standing_v1",
        "label_zh": "A · 药师站姿",
        "video": OUT / "sample-15s.mp4",
        "out": OUT / "ppt-presenter-15s-A-pharmacist-standing.mp4",
        "layout": "portrait",
        "key": "color_a",
    },
    "B": {
        "tag": "business_chin_v1",
        "label_zh": "B · 商务托腮",
        "video": OUT / "sample-15s-business-chin-v1.mp4",
        "out": OUT / "ppt-presenter-15s-B-business-chin.mp4",
        "layout": "portrait",
        "key": "color",
    },
    "C": {
        "tag": "business_standing_v1",
        "label_zh": "C · 商务站姿",
        "video": OUT / "sample-15s-business-standing-v1.mp4",
        "out": OUT / "ppt-presenter-15s-C-business-standing.mp4",
        "layout": "landscape",
        "key": "color",
    },
}


def ffprobe_wh(path: Path) -> tuple[int, int]:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    w, h = r.stdout.strip().split(",")
    return int(w), int(h)


def load_font(size: int) -> ImageFont.ImageFont:
    for p in (
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


def make_label_png(text: str, dest: Path) -> Path:
    font = load_font(34)
    pad_x, pad_y = 18, 12
    tmp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    im = Image.new("RGBA", (tw + pad_x * 2, th + pad_y * 2), (26, 95, 180, 225))
    d = ImageDraw.Draw(im)
    d.text((pad_x - bbox[0], pad_y - bbox[1]), text, font=font, fill=(255, 255, 255, 255))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest)
    return dest


def build_filter(layout: str, key_mode: str) -> str:
    """输入: 0=slide 1=person 2=label → [vout]"""
    if layout == "landscape":
        th, mw = LANDSCAPE_H, LANDSCAPE_MAX_W
        # C：半身横图——紧裁主体（去左右大白边），略裁顶空，视觉接近 A/B 半身站位
        pre_crop = "crop=iw*0.62:ih*0.96:iw*0.19:ih*0.02,"
        # 垂直：略上抬，不要缩在右下角
        y_expr = f"H-h-40"
    else:
        th, mw = PORTRAIT_H, PORTRAIT_MAX_W
        pre_crop = "crop=iw*0.88:ih:iw*0.06:0,"
        y_expr = "H-h"

    if key_mode == "color_a":
        key = COLORKEY_A
        pre_crop = "crop=iw*0.90:ih*0.98:iw*0.05:ih*0.01,"
    else:
        key = COLORKEY_BC

    # 裁边 → 抠底 → 压曝光 → 缩放
    person = (
        f"[1:v]format=rgba,"
        f"{pre_crop}"
        f"{key},"
        f"{GRADE},"
        f"scale=-1:{th}:flags=lanczos,"
        f"scale='min({mw},iw)':-1:flags=lanczos[p]"
    )
    bg = f"[0:v]scale={CANVAS_W}:{CANVAS_H}:flags=lanczos,setsar=1[bg]"
    overlay_p = (
        f"[bg][p]overlay="
        f"x='min({PERSON_LEFT}\\,W-w-12)':"
        f"y='{y_expr}':"
        f"format=auto[v0]"
    )
    overlay_l = "[v0][2:v]overlay=36:H-h-28:format=auto[vout]"
    return ";".join([bg, person, overlay_p, overlay_l])


def composite_one(key: str, cfg: dict, work: Path) -> Path:
    video: Path = cfg["video"]
    out: Path = cfg["out"]
    if not video.exists():
        raise FileNotFoundError(f"missing sample: {video}")
    if not SLIDE.exists():
        raise FileNotFoundError(f"missing slide: {SLIDE}")

    src_w, src_h = ffprobe_wh(video)
    label_path = make_label_png(cfg["label_zh"], work / f"label-{key}.png")
    fc = build_filter(cfg["layout"], cfg["key"])
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(SLIDE),
        "-i",
        str(video),
        "-loop",
        "1",
        "-i",
        str(label_path),
        "-filter_complex",
        fc,
        "-map",
        "[vout]",
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
    print(f"[{key}] {cfg['label_zh']}  layout={cfg['layout']} key={cfg['key']}")
    print(f"  person_left≈{PERSON_LEFT}  portrait_h={PORTRAIT_H}  max_w={PORTRAIT_MAX_W}")
    print(f"  in  {video.name} ({src_w}x{src_h})")
    print(f"  out {out.name}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed for {key}")
    return out


def update_state(results: dict[str, str]):
    state = {}
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    outs = state.setdefault("outputs", {})
    outs["ppt_presenter_samples"] = results
    outs["ppt_presenter_layout"] = {
        "version": "v5",
        "person_left": PERSON_LEFT,
        "portrait_h": PORTRAIT_H,
        "portrait_max_w": PORTRAIT_MAX_W,
        "landscape_h": LANDSCAPE_H,
        "landscape_max_w": LANDSCAPE_MAX_W,
        "grade": GRADE,
        "note_zh": "v5强压曝光：curves 1→0.62 + eq 降亮；A/B/C全部重渲",
    }
    state["status"] = "ppt_presenter_abc_v5_ready_for_business_review"
    state["progress_summary_zh"] = (
        "PPT侧讲 A/B/C v5：三版强压曝光（脸部/高光）。待业务复核。"
    )
    done = state.setdefault("done", [])
    if "ppt_presenter_abc_v5_strong_underexpose" not in done:
        done.append("ppt_presenter_abc_v5_strong_underexpose")
    state["next_agent_instructions_zh"] = [
        "等业务在 A/B/C PPT侧讲视频（v5强压曝光）中选型",
        "选定后再推进方案C关键页",
    ]
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(VARIANTS), nargs="*", help="只生成指定版本")
    args = ap.parse_args()
    keys = args.only or list(VARIANTS.keys())
    results = {}
    with tempfile.TemporaryDirectory(prefix="ppt-dh-") as td:
        work = Path(td)
        for k in keys:
            out = composite_one(k, VARIANTS[k], work)
            results[k] = str(out.relative_to(ROOT))
            print(f"  OK {out} ({out.stat().st_size // 1024} KB)")
    if STATE.exists():
        prev = json.loads(STATE.read_text(encoding="utf-8"))
        prev_map = (prev.get("outputs") or {}).get("ppt_presenter_samples") or {}
        prev_map.update(results)
        results = prev_map
    update_state(results)
    print("done →", results)


if __name__ == "__main__":
    main()
