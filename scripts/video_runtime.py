#!/usr/bin/env python3
"""Shared video Revideo runtime resolution (P2 formal path).

Prefer production-library/engines/video-revideo-runtime-v1/kit over poc/gold-sample.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "production-library" / "engines" / "video-revideo-runtime-v1"
MANIFEST_PATH = ENGINE_DIR / "runtime-manifest.json"
LEGACY_KIT = ROOT / "poc" / "gold-sample"


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {
            "required_kit_markers": [
                "package.json",
                "scripts/render-product-segment.mjs",
                "scripts/render-health-segment.mjs",
                "src",
                "node_modules",
            ],
            "entry_scripts": {
                "product_segment": "scripts/render-product-segment.mjs",
                "health_segment": "scripts/render-health-segment.mjs",
            },
            "legacy_kit_rel": "poc/gold-sample",
        }
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def kit_candidates() -> list[Path]:
    return [
        ENGINE_DIR / "kit",
        LEGACY_KIT,
    ]


def kit_ready(path: Path, *, require_node_modules: bool = True) -> bool:
    if not path.is_dir():
        return False
    markers = list(load_manifest().get("required_kit_markers") or [])
    if not require_node_modules:
        markers = [m for m in markers if m != "node_modules"]
    for rel in markers:
        target = path / rel
        if not target.exists():
            return False
    return True


def resolve_video_kit_root(*, require_node_modules: bool = True) -> Path:
    """Return absolute kit root or raise RuntimeError."""
    for candidate in kit_candidates():
        if kit_ready(candidate, require_node_modules=require_node_modules):
            return candidate.resolve()
    raise RuntimeError(
        "缺少视频 runtime kit：预期 production-library/engines/"
        "video-revideo-runtime-v1/kit（或历史 poc/gold-sample）含 render 脚本、src 与 node_modules"
    )


def resolve_video_kit_root_or_none(*, require_node_modules: bool = True) -> Path | None:
    try:
        return resolve_video_kit_root(require_node_modules=require_node_modules)
    except RuntimeError:
        return None


def video_runtime_ready() -> bool:
    return resolve_video_kit_root_or_none(require_node_modules=True) is not None


def product_render_script_rel() -> str:
    return str(
        (load_manifest().get("entry_scripts") or {}).get(
            "product_segment", "scripts/render-product-segment.mjs"
        )
    )


def health_render_script_rel() -> str:
    return str(
        (load_manifest().get("entry_scripts") or {}).get(
            "health_segment", "scripts/render-health-segment.mjs"
        )
    )


def prepare_workspace(run_dir: Path, *, kit_root: Path | None = None) -> Path:
    """Copy kit into run_dir/render-workspace; symlink node_modules from kit."""
    gold = kit_root or resolve_video_kit_root()
    ws = run_dir / "render-workspace"
    if ws.exists():
        shutil.rmtree(ws)
    ignore = shutil.ignore_patterns(
        "node_modules",
        "dist",
        ".render-work",
        ".git",
        "*.mp4",
        ".DS_Store",
    )
    shutil.copytree(gold, ws, ignore=ignore, symlinks=True)
    nm = gold / "node_modules"
    if nm.exists() and not (ws / "node_modules").exists():
        os.symlink(nm, ws / "node_modules")
    return ws


def soft_repair_kit_symlink(root: Path | None = None) -> list[str]:
    """If formal kit is missing but legacy exists, link kit → legacy."""
    root = root or ROOT
    engine = root / "production-library" / "engines" / "video-revideo-runtime-v1"
    kit = engine / "kit"
    legacy = root / "poc" / "gold-sample"
    actions: list[str] = []
    if not engine.is_dir():
        return actions
    if kit_ready(kit, require_node_modules=False):
        return actions
    if not kit_ready(legacy, require_node_modules=False):
        return actions
    if kit.is_symlink() or kit.exists():
        if kit.is_symlink() and not kit.exists():
            try:
                kit.unlink()
            except OSError:
                return actions
        elif kit.exists():
            return actions
    try:
        rel = Path(os.path.relpath(legacy, start=engine))
        kit.symlink_to(rel, target_is_directory=True)
        actions.append(f"已链接视频 runtime kit → {rel.as_posix()}（过渡期，本地复用）")
    except OSError as exc:
        actions.append(f"未能链接视频 kit: {exc}")
    return actions
