#!/usr/bin/env python3
"""白底位图 → RGBA 抠图：贴边连通近白背景置透明 + 边缘去白晕 + 适配烘焙尺寸。

Usage:
  python3 scripts/whitekey-cutout.py in.png out.png [--size 900x874] [--tol 26]

流程：近白连通域（贴边）→ 背景；alpha 高斯微羽化；半透明像素按白底合成公式
反解前景色（去白边）；--size 时按宽高比 contain 进目标画布并居中。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def cutout(im: Image.Image, tol: int) -> Image.Image:
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    rgb, alpha = a[:, :, :3], a[:, :, 3]

    nearwhite = (rgb.min(axis=2) > 255 - tol) & (alpha > 200)
    lab, n = ndimage.label(nearwhite, structure=np.ones((3, 3)))
    border = np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))
    bg_ids = border[border > 0]
    background = np.isin(lab, bg_ids) if bg_ids.size else np.zeros_like(nearwhite)

    out_a = np.where(background, 0.0, 255.0)
    out_a = ndimage.gaussian_filter(out_a, sigma=0.8)

    # 去白晕：c = α·f + (1-α)·255  →  f = (c - (1-α)·255) / α
    semi = (out_a > 8) & (out_a < 250)
    af = (out_a[semi] / 255.0)[:, None]
    a[:, :, :3][semi] = np.clip((rgb[semi] - (1 - af) * 255.0) / af, 0, 255)
    a[:, :, 3] = out_a
    return Image.fromarray(a.astype(np.uint8))


def fit_canvas(im: Image.Image, w: int, h: int) -> Image.Image:
    a = np.asarray(im)[:, :, 3]
    ys, xs = np.where(a > 8)
    if not ys.size:
        raise SystemExit("no subject after cutout")
    sub = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    scale = min(w / sub.width, h / sub.height)
    sub = sub.resize((max(1, round(sub.width * scale)), max(1, round(sub.height * scale))),
                     Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(sub, ((w - sub.width) // 2, (h - sub.height) // 2), sub)
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--size", default=None, help="WxH，contain 适配；缺省=裁切后原样输出")
    ap.add_argument("--tol", type=int, default=26)
    args = ap.parse_args()

    out = cutout(Image.open(args.src), args.tol)
    if args.size:
        w, h = (int(x) for x in args.size.lower().split("x"))
        out = fit_canvas(out, w, h)
    args.dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.dst)
    print(f"{args.src} -> {args.dst} {out.size}")


if __name__ == "__main__":
    main()
