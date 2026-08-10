#!/usr/bin/env python3
"""Tests for on-demand gold asset materialization."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import ensure_gold_assets as ega

ROOT = Path(__file__).resolve().parents[1]


class EnsureGoldAssetsTests(unittest.TestCase):
    def test_manifest_lists_large_settled_media(self) -> None:
        assets = ega.list_assets(ROOT)
        self.assertGreaterEqual(len(assets), 8)
        paths = {str(a["path"]) for a in assets}
        self.assertTrue(any(p.endswith(".mp4") for p in paths))
        self.assertTrue(any(p.endswith(".pptx") for p in paths))
        # green compact pptx is small and must NOT be on-demand-only inventory
        self.assertFalse(
            any("product-courseware-green-v1" in p and p.endswith(".pptx") for p in paths)
        )

    def test_sparse_negations_use_repo_relative_paths(self) -> None:
        patterns = ega.sparse_negation_patterns(ROOT)
        self.assertTrue(all(p.startswith("!/") for p in patterns))
        self.assertTrue(any("辅酶Q10" in p or "product-video" in p for p in patterns))

    def test_match_by_route_and_slug(self) -> None:
        by_route = ega._match_assets(root=ROOT, route_id="courseware3-pptx-v1")
        self.assertTrue(
            any("速福达" in str(a["path"]) and a["path"].endswith(".pptx") for a in by_route)
        )
        by_slug = ega._match_assets(
            root=ROOT, template_slug="kangaisen-lycopene-health-edu-v1"
        )
        self.assertTrue(any(a["path"].endswith(".pptx") for a in by_slug))
        portal = ega._match_assets(root=ROOT, portal=True)
        self.assertGreaterEqual(len(portal), 2)

    def test_materialize_noop_when_present(self) -> None:
        # Developer tree already has golds — ensure is no-op.
        assets = ega._match_assets(root=ROOT, portal=True)
        paths = ega.ensure_paths([str(a["path"]) for a in assets[:1]], root=ROOT, quiet=True)
        self.assertTrue(paths[0].is_file())
        self.assertGreater(paths[0].stat().st_size, 1000)

    def test_materialize_from_git_blob_roundtrip(self) -> None:
        # Write a tiny tracked-like blob via git in a temp repo.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            rel = "production-library/templates/settled/demo/gold.mp4"
            path = repo / rel
            path.parent.mkdir(parents=True)
            payload = b"FAKEGOLD" * 200
            path.write_bytes(payload)
            subprocess.run(["git", "add", rel], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "add gold"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            path.unlink()
            self.assertFalse(path.exists())
            out = ega.materialize_git_blob(repo, rel, quiet=True)
            self.assertEqual(out.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
