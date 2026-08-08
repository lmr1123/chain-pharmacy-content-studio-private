#!/usr/bin/env python3
"""Tests for video_full_env package / restore / check helpers."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import video_full_env as vfe  # noqa: E402
import video_runtime as vr  # noqa: E402


def _make_minimal_kit(path: Path, *, with_nm: bool = True) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "package.json").write_text('{"name":"kit-test"}\n', encoding="utf-8")
    (path / "scripts").mkdir(exist_ok=True)
    (path / "scripts" / "render-product-segment.mjs").write_text("// product\n", encoding="utf-8")
    (path / "scripts" / "render-health-segment.mjs").write_text("// health\n", encoding="utf-8")
    (path / "src").mkdir(exist_ok=True)
    (path / "src" / "index.ts").write_text("export {}\n", encoding="utf-8")
    if with_nm:
        (path / "node_modules").mkdir(exist_ok=True)
        (path / "node_modules" / "x").write_text("1", encoding="utf-8")
    # noise that must be excluded from package
    (path / "dist").mkdir(exist_ok=True)
    (path / "dist" / "out.mp4").write_bytes(b"fake")


class VideoFullEnvPackageTests(unittest.TestCase):
    def test_package_and_restore_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vfe-") as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "src-kit"
            _make_minimal_kit(src)
            self.assertTrue(vr.kit_ready(src, require_node_modules=True))

            archive = tmp_path / "kit.tgz"
            result = vfe.package_kit(
                source=src, out_path=archive, include_node_modules=True
            )
            self.assertTrue(result["ok"])
            self.assertTrue(archive.is_file())
            self.assertGreater(result["file_count"], 3)

            # Restore into a fake ROOT by monkeypatching KIT_DIR / ENGINE
            fake_root = tmp_path / "repo"
            engine = fake_root / "production-library" / "engines" / "video-revideo-runtime-v1"
            engine.mkdir(parents=True)
            # point module paths
            old_root, old_engine, old_kit = vfe.ROOT, vfe.ENGINE, vfe.KIT_DIR
            try:
                vfe.ROOT = fake_root
                vfe.ENGINE = engine
                vfe.KIT_DIR = engine / "kit"
                restored = vfe.restore_kit_from_archive(archive, force=True)
                self.assertTrue(restored["ok"])
                self.assertTrue(
                    vr.kit_ready(vfe.KIT_DIR, require_node_modules=True)
                )
                # dist/mp4 excluded
                self.assertFalse((vfe.KIT_DIR / "dist" / "out.mp4").exists())
            finally:
                vfe.ROOT, vfe.ENGINE, vfe.KIT_DIR = old_root, old_engine, old_kit

    def test_package_without_node_modules(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vfe2-") as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "src-kit"
            _make_minimal_kit(src, with_nm=True)
            archive = tmp_path / "kit-src.tgz"
            result = vfe.package_kit(
                source=src, out_path=archive, include_node_modules=False
            )
            self.assertTrue(result["ok"])
            # extract and ensure no node_modules
            import tarfile

            with tarfile.open(archive, "r:gz") as tar:
                names = tar.getnames()
            self.assertTrue(any(n.startswith("kit/") for n in names))
            self.assertFalse(any("node_modules" in n for n in names))

    def test_check_report_has_business_route(self) -> None:
        report = vfe.build_check_report()
        self.assertEqual(report["business_route"], "product-mp4-full-v1")
        self.assertIn("capabilities", report)
        self.assertIn("kit", report)
        self.assertIn("tts", report)


if __name__ == "__main__":
    unittest.main()
