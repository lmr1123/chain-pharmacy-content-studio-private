#!/usr/bin/env python3
"""Build video + native editable PPTX deliverables (single content-model).

  python3 scripts/build_deliverables.py
  python3 scripts/build_deliverables.py --patches editable-patches.json
  python3 scripts/build_deliverables.py --skip-video
  python3 scripts/build_deliverables.py --skip-pptx
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUT = ROOT / "out"
PPTX_NAME = "福尔番茄红素_商品培训课件4_可编辑课件_v1.pptx"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patches", default="")
    ap.add_argument("--skip-video", action="store_true")
    ap.add_argument("--skip-pptx", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    run([sys.executable, str(SCRIPTS / "build_layer_manifest.py")])

    patches = args.patches
    if not patches and (ROOT / "editable-patches.json").exists():
        patches = str(ROOT / "editable-patches.json")

    if not args.skip_video:
        video_cmd = [sys.executable, str(SCRIPTS / "export-full-film-video.py")]
        if patches:
            video_cmd += ["--patches", patches]
        run(video_cmd)

    pptx_path = OUT / PPTX_NAME
    if not args.skip_pptx:
        pptx_cmd = ["node", str(SCRIPTS / "export-cw4-pptx.mjs")]
        if patches:
            pptx_cmd.append(patches)
        run(pptx_cmd)

    # web media links for editor
    media = ROOT / "web" / "media"
    media.mkdir(parents=True, exist_ok=True)
    stills = media / "stills"
    if not stills.exists():
        try:
            stills.symlink_to(OUT / "scene-stills")
        except OSError:
            pass
    film = media / "film.mp4"
    mp4 = OUT / "商品培训课件4_保真复刻_全片_v1.mp4"
    if mp4.exists():
        if film.is_symlink() or film.exists():
            try:
                film.unlink()
            except OSError:
                pass
        try:
            film.symlink_to(mp4.resolve())
        except OSError:
            pass
    courseware = media / "courseware.pptx"
    if pptx_path.exists():
        if courseware.is_symlink() or courseware.exists():
            try:
                courseware.unlink()
            except OSError:
                pass
        try:
            courseware.symlink_to(pptx_path.resolve())
        except OSError:
            pass

    index = {
        "project_id": "product-courseware-4-faithful-replica-v1",
        "status": "editable-delivery-v1",
        "channels": ["video_still_mp4", "pptx_native_editable"],
        "single_content_model": "content-model.json",
        "layer_manifest": "layer-manifest.json",
        "outputs": {
            "video_mp4": "out/商品培训课件4_保真复刻_全片_v1.mp4" if mp4.exists() else None,
            "video_stills_dir": "out/scene-stills",
            "pptx_editable": f"out/{PPTX_NAME}" if pptx_path.exists() else None,
            "contact_sheet": "out/full-film-contact-sheet.png",
            "pptx_qa_contact": "out/pptx-qa/contact-sheet.png",
        },
        "how_to_edit": {
            "text_image": "改 content-model.json 字段，或写 editable-patches.json 后重新 build_deliverables",
            "pack_slots": "替换 assets/generated/slot-pack-*.png 等槽位文件",
            "rebuild_all": "python3 scripts/build_deliverables.py",
            "rebuild_pptx_only": "npm run export:pptx",
            "rebuild_video_only": "python3 scripts/export-full-film-video.py",
            "revideo_editor": "npm run start:editor → http://127.0.0.1:9012/",
        },
        "experience_doc": "docs/video-pptx-grammar-and-experience-v1.md",
        "pptx_pattern": "sufuda export-sufuda-pptx.mjs (Artifact Tool native editable)",
    }
    (OUT / "DELIVERY_INDEX.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(index["outputs"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
