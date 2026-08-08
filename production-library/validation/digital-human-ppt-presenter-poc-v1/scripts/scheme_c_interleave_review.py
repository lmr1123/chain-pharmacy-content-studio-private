#!/usr/bin/env python3
"""方案 C 业务审片：关键页穿插 + 非关键页旁白（1–2 页验收）。

读取 work/key_pages.json：
  - 关键页 3 个锚点（头-腰-尾）：3 / 9 / 15
  - 真动态：仅复用已有 v6.2 药师侧讲（p03 口型对齐；p09/15 节奏示意）
  - 非关键+旁白验收：p04、p10 全宽 + edge-tts 旁白
  - 壳页短 hold：1、2、18

不新调 HeyGen。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
STATE = ROOT / "work" / "job-state.json"
KEY_CFG = ROOT / "work" / "key_pages.json"
QA_FULL = (
    ROOT.parents[0]
    / "courseware"
    / "gold-samples"
    / "uri-shenke-health-pptx-gold-v1"
    / "web"
    / "media"
    / "slides"
)
# 关键页动态：p03 真对齐；p09/p15 同段数字人叠到对应讲解安全版页（口型示意）
DH = {
    3: OUT / "ppt-presenter-15s-A-pharmacist-standing.mp4",
    9: OUT / "ppt-presenter-key-p09-reuse-dh.mp4",
    15: OUT / "ppt-presenter-key-p15-reuse-dh.mp4",
}
NARR = {
    4: ROOT / "inputs" / "narration-review" / "page-04-clinical.mp3",
    10: ROOT / "inputs" / "narration-review" / "page-10-precautions.mp3",
}
CANVAS_W, CANVAS_H = 1920, 1080
FPS = 25


def load_font(size: int) -> ImageFont.ImageFont:
    for p in (
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size, index=0)
            except OSError:
                pass
    return ImageFont.load_default()


def badge(text: str, bg=(26, 95, 180, 230)) -> Image.Image:
    font = load_font(26)
    pad_x, pad_y = 14, 9
    tmp = Image.new("RGBA", (8, 8))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    im = Image.new("RGBA", (tw + pad_x * 2, th + pad_y * 2), bg)
    d = ImageDraw.Draw(im)
    d.text((pad_x - bb[0], pad_y - bb[1]), text, font=font, fill=(255, 255, 255, 255))
    return im


def ffprobe_dur(path: Path) -> float:
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


def load_full(page: int) -> Image.Image:
    src = QA_FULL / f"slide-{page:02d}.png"
    im = Image.open(src).convert("RGB")
    if im.size != (CANVAS_W, CANVAS_H):
        im = im.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    return im


def encode_still_audio(png: Path, audio: Path | None, sec: float, out: Path):
    if audio and audio.exists():
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-preset",
            "veryfast",
            "-crf",
            "20",
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
            "-shortest",
            "-r",
            str(FPS),
            "-movflags",
            "+faststart",
            str(out),
        ]
    else:
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
            "-r",
            str(FPS),
            "-movflags",
            "+faststart",
            str(out),
        ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        raise RuntimeError(f"encode failed {out.name}")


def prepare_dh(src: Path, out: Path, label: str | None):
    """复用动态片段；遮掉旧 A 标签；可选加穿插角标。"""
    # 先标准化
    tmp = out.with_suffix(".raw.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        "fps=25,drawbox=x=20:y=1000:w=380:h=70:color=0xE8F2FA@1:t=fill",
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
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise RuntimeError("prepare_dh failed")

    if not label:
        tmp.rename(out)
        return

    # 烧角标：生成透明 PNG overlay
    b = badge(label, bg=(180, 90, 30, 235))
    overlay = out.with_suffix(".badge.png")
    # full frame transparent with badge at top-left of person slot-ish
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    canvas.alpha_composite(b, (36, 36))
    canvas.save(overlay)
    cmd2 = [
        "ffmpeg",
        "-y",
        "-i",
        str(tmp),
        "-i",
        str(overlay),
        "-filter_complex",
        "[0:v][1:v]overlay=0:0",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        str(out),
    ]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    overlay.unlink(missing_ok=True)
    if r2.returncode != 0:
        print(r2.stderr[-1500:], file=sys.stderr)
        raise RuntimeError("badge overlay failed")


def concat(clips: list[Path], out: Path):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        list_path = Path(f.name)
        for c in clips:
            p = str(c.resolve()).replace("'", "'\\''")
            f.write(f"file '{p}'\n")
    try:
        r = subprocess.run(
            [
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
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print(r.stderr[-2500:], file=sys.stderr)
            raise RuntimeError("concat failed")
    finally:
        list_path.unlink(missing_ok=True)


def endcard(path: Path, keys: list[int]):
    im = Image.new("RGB", (CANVAS_W, CANVAS_H), (245, 249, 252))
    d = ImageDraw.Draw(im)
    t, b, s = load_font(40), load_font(26), load_font(22)
    d.text((80, 100), "方案 C · 关键页穿插 + 旁白验收", font=t, fill=(26, 95, 180))
    lines = [
        f"关键页（头-腰-尾）：第 {', '.join(map(str, keys))} 页 → 动态数字人侧讲",
        "非关键页：全宽课件放大 + 旁白（本片验收第 4、10 页）",
        "禁止：非关键页静帧站人；禁止后期强行拉升构图",
        "本片 p09/p15 为节奏示意（复用同段数字人），量产按各页旁白重渲",
        "规则文档：KEY-PAGE-INTERLEAVE-RULES.md · key_pages.json",
    ]
    y = 220
    for line in lines:
        d.text((80, y), "· " + line, font=b, fill=(40, 55, 70))
        y += 52
    d.text((80, 980), "仅限内部学习 · POC", font=s, fill=(120, 130, 140))
    im.save(path)


def main():
    cfg = json.loads(KEY_CFG.read_text(encoding="utf-8"))
    keys = [k["page"] for k in cfg["key_pages"]]
    review = cfg["business_review_pages"]
    for p, path in DH.items():
        if not path.exists():
            raise SystemExit(f"missing DH clip for page {p}: {path}")
    for p, a in NARR.items():
        if not a.exists():
            raise SystemExit(f"missing narration {a}")

    work = OUT / "_scheme_c_interleave_work"
    work.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    plan = []

    # shell 1-2
    for page in review["shell_hold"]:
        if page not in (1, 2):
            continue
        png = work / f"p{page:02d}.png"
        load_full(page).save(png)
        mp4 = work / f"p{page:02d}.mp4"
        encode_still_audio(png, None, 2.0, mp4)
        clips.append(mp4)
        plan.append({"page": page, "mode": "shell_hold", "dur": 2.0})
        print(f"  p{page:02d} shell 2.0s")

    # key1 real (p03 口型对齐)
    dh_real = work / "key1-real.mp4"
    prepare_dh(DH[3], dh_real, "关键① 开场知识 · 动态数字人")
    clips.append(dh_real)
    plan.append({"page": 3, "mode": "key_dh_real", "dur": round(ffprobe_dur(dh_real), 2)})
    print(f"  p03 KEY1 real DH {plan[-1]['dur']}s")

    # non-key narr 4
    png = work / "p04.png"
    load_full(4).save(png)
    frame = Image.open(png).convert("RGBA")
    frame.alpha_composite(badge("非关键页 · 全宽 + 旁白验收"), (36, CANVAS_H - 70))
    frame.convert("RGB").save(png)
    mp4 = work / "p04.mp4"
    encode_still_audio(png, NARR[4], 0, mp4)
    clips.append(mp4)
    plan.append({"page": 4, "mode": "full_narration", "dur": round(ffprobe_dur(mp4), 2)})
    print(f"  p04 FULL+narr {plan[-1]['dur']}s")

    # key2：本页讲解安全版 + 同段数字人（课件正确；口型示意）
    dh2 = work / "key2.mp4"
    prepare_dh(DH[9], dh2, None)  # 片内已有关键②角标
    clips.append(dh2)
    plan.append({"page": 9, "mode": "key_dh_on_correct_slide", "dur": round(ffprobe_dur(dh2), 2)})
    print(f"  p09 KEY2 on-slide {plan[-1]['dur']}s")

    # non-key narr 10
    png = work / "p10.png"
    load_full(10).save(png)
    frame = Image.open(png).convert("RGBA")
    frame.alpha_composite(badge("非关键页 · 全宽 + 旁白验收"), (36, CANVAS_H - 70))
    frame.convert("RGB").save(png)
    mp4 = work / "p10.mp4"
    encode_still_audio(png, NARR[10], 0, mp4)
    clips.append(mp4)
    plan.append({"page": 10, "mode": "full_narration", "dur": round(ffprobe_dur(mp4), 2)})
    print(f"  p10 FULL+narr {plan[-1]['dur']}s")

    # key3
    dh3 = work / "key3.mp4"
    prepare_dh(DH[15], dh3, None)
    clips.append(dh3)
    plan.append({"page": 15, "mode": "key_dh_on_correct_slide", "dur": round(ffprobe_dur(dh3), 2)})
    print(f"  p15 KEY3 on-slide {plan[-1]['dur']}s")
    # shell 18
    png = work / "p18.png"
    load_full(18).save(png)
    mp4 = work / "p18.mp4"
    encode_still_audio(png, None, 2.2, mp4)
    clips.append(mp4)
    plan.append({"page": 18, "mode": "shell_hold", "dur": 2.2})
    print("  p18 shell 2.2s")

    # endcard
    ep = work / "end.png"
    endcard(ep, keys)
    em = work / "end.mp4"
    encode_still_audio(ep, None, 5.0, em)
    clips.append(em)
    plan.append({"page": "endcard", "mode": "info", "dur": 5.0})

    out = OUT / "scheme-c-interleave-review.mp4"
    print(f"concat {len(clips)} → {out.name}")
    concat(clips, out)
    total = ffprobe_dur(out)

    plan_path = OUT / "scheme-c-interleave-review-plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "output": str(out.relative_to(ROOT)),
                "total_s": round(total, 2),
                "key_pages": keys,
                "rules": "KEY-PAGE-INTERLEAVE-RULES.md",
                "segments": plan,
                "note_zh": (
                    "头-腰-尾 3 关键页穿插；p04/p10 全宽旁白验收；"
                    "p09/p15 复用同段数字人仅示节奏，量产需各页旁白+HeyGen"
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if STATE.exists():
        st = json.loads(STATE.read_text(encoding="utf-8"))
        st["status"] = "scheme_c_interleave_review_ready"
        st["progress_summary_zh"] = (
            "关键页穿插规则已定（3/9/15）；审片含多关键出镜+2页全宽旁白。"
        )
        outs = st.setdefault("outputs", {})
        outs["scheme_c_interleave_review"] = str(out.relative_to(ROOT))
        outs["key_pages"] = "work/key_pages.json"
        done = st.setdefault("done", [])
        for t in ("key_page_interleave_rules", "scheme_c_interleave_review_film", "non_dh_narration_p04_p10"):
            if t not in done:
                done.append(t)
        STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK {out} ({out.stat().st_size // 1024} KB, {total:.1f}s)")
    print(f"plan {plan_path}")


if __name__ == "__main__":
    main()
