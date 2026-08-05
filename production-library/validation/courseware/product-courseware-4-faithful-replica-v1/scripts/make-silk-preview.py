#!/usr/bin/env python3
"""丝绸底横排预览：复刻 layout.ts SILK_BG，把 RGBA 图合成上去并排输出。

Usage:
  python3 scripts/make-silk-preview.py out.png img1.png img2.png [...] [--labels a,b,c]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

BASE = (206, 203, 196, 255)  # #cecbc4
LIGHT = (255, 255, 255)
DARK = (170, 165, 158)
CELL_W, CELL_H = 480, 560
PAD = 24


def silk(w: int, h: int) -> Image.Image:
    im = Image.new("RGBA", (w, h), BASE)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i, a in enumerate([18, 14, 10, 8]):
        x0 = -200 + i * 180
        while x0 < w:
            d.polygon([(x0, 0), (x0 + 420, 0), (x0 + 820, h), (x0 + 200, h)],
                      fill=LIGHT + (a,))
            x0 += 720
    for i, a in enumerate([12, 9, 6]):
        x0 = 400 + i * 220
        while x0 < w:
            d.polygon([(x0, 0), (x0 + 280, 0), (x0 + 100, h), (x0 - 180, h)],
                      fill=DARK + (a,))
            x0 += 660
    return Image.alpha_composite(im, ov)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("imgs", nargs="+", type=Path)
    ap.add_argument("--labels", default=None)
    args = ap.parse_args()

    n = len(args.imgs)
    bg = silk(n * CELL_W, CELL_H)
    d = ImageDraw.Draw(bg)
    for i, p in enumerate(args.imgs):
        im = Image.open(p).convert("RGBA")
        s = min((CELL_W - 2 * PAD) / im.width, (CELL_H - 2 * PAD - 30) / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        x = i * CELL_W + (CELL_W - im.width) // 2
        y = (CELL_H - 30 - im.height) // 2
        bg.paste(im, (x, y), im)
        label = (args.labels.split(",")[i] if args.labels else p.stem)
        d.text((i * CELL_W + PAD, CELL_H - 26), label, fill=(60, 50, 45, 255))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(args.out)
    print(f"-> {args.out} {bg.size}")


if __name__ == "__main__":
    main()
