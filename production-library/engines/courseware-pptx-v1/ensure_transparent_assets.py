#!/usr/bin/env python3
"""Ensure illustration PNGs have transparent background (blend with silk/cream PPT).

Gate (aligned with check-alpha.py):
  - corner 8×8 max alpha ≤ 8
  - optional: whitekey-cutout when FAIL

Pack-slot UI cards (slot-pack-*.png) are exempt — they are designed product cards.

Usage:
  python3 ensure_transparent_assets.py --dir PATH/assets/generated [--apply] [--json report.json]

Default is dry-run (report only). --apply runs whitekey-cutout in place (keeps .bak).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ENGINE = Path(__file__).resolve().parent
WHITEKEY = ENGINE / "whitekey-cutout.py"
CORNER = 8
CORNER_GATE = 8
# intentional full-bleed / UI — do not whitekey
EXEMPT_PREFIXES = (
    "slot-pack-",  # product placeholder cards (white UI by design)
    "slot-photo-",  # real photos / b-roll plates (sit on white_stage)
    "slot-time-",  # magazine cover full-bleed
    "badge-",  # sun badge design fill; corners usually transparent
)
EXEMPT_NAMES = set()


def analyze(path: Path) -> dict:
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im)
    alpha = a[:, :, 3]
    rgb = a[:, :, :3].astype(np.int16)
    corners = np.concatenate(
        [
            alpha[:CORNER, :CORNER].ravel(),
            alpha[:CORNER, -CORNER:].ravel(),
            alpha[-CORNER:, :CORNER].ravel(),
            alpha[-CORNER:, -CORNER:].ravel(),
        ]
    )
    corner_max = int(corners.max())
    whiteish = float(((rgb.min(axis=2) > 245) & (alpha > 200)).mean())
    return {
        "path": str(path),
        "name": path.name,
        "corner_max_alpha": corner_max,
        "whiteish_opaque_pct": round(whiteish * 100, 2),
        "ok": corner_max <= CORNER_GATE,
        "exempt": path.name.startswith(EXEMPT_PREFIXES) or path.name in EXEMPT_NAMES,
    }


def whitekey_in_place(path: Path, tol: int = 26) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
    tmp = path.with_suffix(".whitekey-tmp.png")
    cmd = [sys.executable, str(WHITEKEY), str(path), str(tmp), f"--tol={tol}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"whitekey failed {path.name}: {r.stderr or r.stdout}")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True, help="assets/generated or any PNG dir")
    ap.add_argument("--apply", action="store_true", help="run whitekey on FAIL (non-exempt)")
    ap.add_argument("--tol", type=int, default=26)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    root = args.dir.resolve()
    if not root.is_dir():
        print(f"ERROR: not a dir: {root}", file=sys.stderr)
        return 2

    pngs = sorted(root.glob("*.png"))
    # skip bak / tmp
    pngs = [p for p in pngs if not p.name.endswith(".bak") and ".whitekey" not in p.name]
    rows = [analyze(p) for p in pngs]

    fail = [r for r in rows if not r["ok"] and not r["exempt"]]
    exempt_fail = [r for r in rows if not r["ok"] and r["exempt"]]
    applied = []

    if args.apply:
        for r in fail:
            p = Path(r["path"])
            try:
                whitekey_in_place(p, tol=args.tol)
                after = analyze(p)
                applied.append({"name": p.name, "before": r, "after": after})
                r.update(after)
            except Exception as e:
                r["apply_error"] = str(e)

    report = {
        "dir": str(root),
        "total": len(rows),
        "ok": sum(1 for r in rows if r["ok"] or r["exempt"]),
        "fail_need_whitekey": [r["name"] for r in fail],
        "exempt_opaque_ok": [r["name"] for r in exempt_fail],
        "applied": applied,
        "items": rows,
        "policy": {
            "corner_alpha_max": CORNER_GATE,
            "illustration_must_be_transparent": True,
            "exempt": list(EXEMPT_PREFIXES),
        },
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")
    print(text)

    # exit 1 if still failing after apply (or dry-run has fails)
    still = [r for r in rows if not r["ok"] and not r["exempt"]]
    return 1 if still else 0


if __name__ == "__main__":
    raise SystemExit(main())
