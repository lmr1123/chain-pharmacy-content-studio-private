#!/usr/bin/env python3
"""RGBA 抠图质检：四角透明度门禁 + 白晕环带 + 主体占比。

Usage:
  python3 scripts/check-alpha.py assets/generated/foo.png [more.png ...]
  python3 scripts/check-alpha.py assets/generated/*.png --json qa/asset-alpha-report.json

硬门禁：四角 8×8 块 max alpha ≤ 8（烤死背景判 FAIL）。
警示：白晕环带 near-white 占比 >15%；主体占比 <25% 或 >98%。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

CORNER = 8
CORNER_GATE = 8
HALO_WARN = 0.15
OCC_LO, OCC_HI = 0.25, 0.98


def analyze(path: Path) -> dict:
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.uint8)
    h, w = a.shape[:2]
    alpha = a[:, :, 3]
    rgb = a[:, :, :3].astype(np.int16)

    corners = np.concatenate([
        alpha[:CORNER, :CORNER].ravel(), alpha[:CORNER, -CORNER:].ravel(),
        alpha[-CORNER:, :CORNER].ravel(), alpha[-CORNER:, -CORNER:].ravel(),
    ])
    corner_alpha = int(corners.max())

    opaque = alpha > 250
    subject = alpha > 8
    transp_ratio = float((alpha <= 8).mean())

    # 白晕环带：贴住不透明主体外侧 12px 内的半透明像素里，近白像素占比
    band = ndimage.binary_dilation(opaque, iterations=12) & ~opaque & subject
    if band.any():
        px = rgb[band]
        nearwhite = (px.min(axis=1) > 220) & ((px.max(axis=1) - px.min(axis=1)) < 28)
        halo_ratio = float(nearwhite.mean())
        band_px = int(band.sum())
    else:
        halo_ratio, band_px = 0.0, 0

    if subject.any():
        ys, xs = np.where(subject)
        occ_w = (xs.max() - xs.min() + 1) / w
        occ_h = (ys.max() - ys.min() + 1) / h
    else:
        occ_w = occ_h = 0.0

    issues = []
    if corner_alpha > CORNER_GATE:
        issues.append(f"corner_alpha={corner_alpha}>8(背景烤死)")
    if halo_ratio > HALO_WARN:
        issues.append(f"halo={halo_ratio:.0%}>15%(白晕)")
    if not (OCC_LO <= min(occ_w, occ_h) and max(occ_w, occ_h) <= OCC_HI):
        issues.append(f"occupancy={occ_w:.0%}x{occ_h:.0%} 异常")

    return {
        "file": path.name,
        "size": [w, h],
        "corner_alpha": corner_alpha,
        "transparent_ratio": round(transp_ratio, 3),
        "halo_ratio": round(halo_ratio, 3),
        "halo_band_px": band_px,
        "occupancy_wh": [round(occ_w, 3), round(occ_h, 3)],
        "verdict": "FAIL" if corner_alpha > CORNER_GATE else ("WARN" if issues else "PASS"),
        "issues": issues,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    rows = [analyze(p) for p in args.images]
    print(f"{'file':<28} {'size':<10} {'corner':>6} {'transp':>6} {'halo':>6} {'occupancy':<11} verdict")
    for r in rows:
        print(f"{r['file']:<28} {r['size'][0]}x{r['size'][1]:<5} {r['corner_alpha']:>6} "
              f"{r['transparent_ratio']:>6.1%} {r['halo_ratio']:>6.1%} "
              f"{r['occupancy_wh'][0]:.0%}x{r['occupancy_wh'][1]:<4.0%} {r['verdict']}"
              + (f"  <- {'; '.join(r['issues'])}" if r["issues"] else ""))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
        print(f"\nreport -> {args.json}")
    return 1 if any(r["verdict"] == "FAIL" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
