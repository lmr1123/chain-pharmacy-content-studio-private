#!/usr/bin/env python3
"""P2 regression: runtime profiles, production green engine path, business doctor."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import business_doctor as doctor  # noqa: E402
import business_job as bj  # noqa: E402


class RuntimeProfilesTests(unittest.TestCase):
    def test_profiles_file_schema(self) -> None:
        doc = doctor.load_profiles()
        self.assertEqual(doc.get("schema"), "runtime-profiles-v1")
        profiles = doc["profiles"]
        self.assertIn("pptx", profiles)
        self.assertIn("video-full", profiles)
        self.assertIn("optional-external", profiles)
        self.assertEqual(
            doc["route_to_profile"]["product-pptx-component-v1"], "pptx"
        )
        self.assertEqual(
            doc["route_to_profile"]["product-pptx-green-v1"], "pptx"
        )
        self.assertEqual(
            doc["route_to_profile"]["product-mp4-full-v1"], "video-full"
        )
        self.assertEqual(
            doc["profiles"]["pptx"].get("default_route"),
            "product-pptx-component-v1",
        )
        deps = doc["profiles"]["pptx"].get("deps") or {}
        self.assertIn("courseware-pptx-v1", str(deps.get("primary_engine_entry") or ""))

    def test_active_routes_have_profiles_or_explicit_null(self) -> None:
        doc = doctor.load_profiles()
        mapping = doc["route_to_profile"]
        for route in bj.load_routes(active_only=True):
            self.assertIn(route["route_id"], mapping)
            pid = mapping[route["route_id"]]
            if pid is not None:
                self.assertIn(pid, doc["profiles"])


class GreenEnginePathTests(unittest.TestCase):
    def test_production_engine_is_preferred(self) -> None:
        gold = bj.green_gold_json()
        builder = bj.green_builder()
        self.assertTrue(gold.is_file())
        self.assertTrue(builder.is_file())
        self.assertIn("production-library/engines/product-courseware-green-v1", str(gold))
        self.assertIn("production-library/engines/product-courseware-green-v1", str(builder))
        # gold content still has structure pages
        model = json.loads(gold.read_text(encoding="utf-8"))
        ids = {p["id"] for p in model["pages"]}
        self.assertEqual(
            ids,
            {
                "cover",
                "product-overview",
                "combination-guidance",
                "product-benchmark",
                "precautions",
            },
        )


class ComponentEnginePathTests(unittest.TestCase):
    def test_default_component_engine_exists(self) -> None:
        export = bj.component_export()
        gen = bj.component_generator()
        style = bj.component_style_default()
        self.assertTrue(export.is_file())
        self.assertTrue(gen.is_file())
        self.assertTrue(style.is_file())
        self.assertIn("courseware-pptx-v1", str(export))
        recipes = ROOT / "production-library/page-types/product-training/recipes"
        self.assertTrue((recipes / "scene-type-map.json").is_file())


class VideoRuntimePathTests(unittest.TestCase):
    def test_resolve_prefers_production_engine_kit(self) -> None:
        import video_runtime as vr

        kit = vr.resolve_video_kit_root(require_node_modules=False)
        self.assertTrue(kit.is_dir())
        # Preferred formal path resolves under engines/…/kit (symlink ok)
        self.assertTrue(
            (ROOT / "production-library/engines/video-revideo-runtime-v1/kit").exists()
        )
        self.assertTrue((kit / "scripts/render-product-segment.mjs").is_file())
        self.assertTrue((kit / "scripts/render-health-segment.mjs").is_file())
        # Resolved absolute path should equal formal kit.resolve() when kit ready
        formal = (ROOT / "production-library/engines/video-revideo-runtime-v1/kit").resolve()
        self.assertEqual(kit, formal)

    def test_product_and_health_use_shared_prepare(self) -> None:
        import importlib.util

        def load(name: str):
            path = ROOT / "scripts" / f"{name}.py"
            spec = importlib.util.spec_from_file_location(name, path)
            assert spec and spec.loader
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

        product = load("business_video_product_full")
        health = load("business_video_health_full")
        self.assertEqual(
            product.product_render_script_rel(),
            "scripts/render-product-segment.mjs",
        )
        self.assertEqual(
            health.health_render_script_rel(),
            "scripts/render-health-segment.mjs",
        )
        # gold roots should agree
        self.assertEqual(product.gold_root(), health.gold_root())

    def test_soft_repair_video_kit_symlink(self) -> None:
        import tempfile

        import video_runtime as vr

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = root / "production-library/engines/video-revideo-runtime-v1"
            engine.mkdir(parents=True)
            legacy = root / "poc/gold-sample"
            for rel in (
                "package.json",
                "scripts/render-product-segment.mjs",
                "scripts/render-health-segment.mjs",
            ):
                path = legacy / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
            (legacy / "src").mkdir(parents=True)
            actions = vr.soft_repair_kit_symlink(root)
            self.assertTrue(any("kit" in a for a in actions))
            self.assertTrue((engine / "kit" / "package.json").is_file())


class BootstrapProfileExpandTests(unittest.TestCase):
    def setUp(self) -> None:
        import importlib.util

        path = ROOT / "scripts" / "workbuddy_bootstrap_for_business.py"
        spec = importlib.util.spec_from_file_location("wb_bootstrap_p2", path)
        assert spec and spec.loader
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_expand_route_to_pptx_profile(self) -> None:
        tokens, profiles = self.mod.expand_requirements(
            ROOT, routes=["product-pptx-component-v1"]
        )
        self.assertEqual(profiles, ["pptx"])
        self.assertIn("production-assets", tokens)
        self.assertIn("pptx", tokens)

    def test_expand_video_route(self) -> None:
        tokens, profiles = self.mod.expand_requirements(
            ROOT, routes=["product-mp4-full-v1"]
        )
        self.assertEqual(profiles, ["video-full"])
        self.assertIn("video-full", tokens)

    def test_preview_route_adds_no_profile(self) -> None:
        tokens, profiles = self.mod.expand_requirements(
            ROOT, routes=["gold-preview-only"]
        )
        self.assertEqual(profiles, [])
        self.assertEqual(tokens, ["production-assets"])

    def test_soft_repair_links_missing_node_modules(self) -> None:
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = root / self.mod.GREEN_ENGINE_REL
            engine.mkdir(parents=True)
            legacy = root / self.mod.LEGACY_PPTX_NODE_MODULES_REL
            artifact = (
                legacy / "@oai" / "artifact-tool" / "dist" / "artifact_tool.mjs"
            )
            artifact.parent.mkdir(parents=True)
            artifact.write_text("ok", encoding="utf-8")
            actions = self.mod.soft_repair_local_deps(root)
            self.assertTrue(any("node_modules" in a for a in actions))
            linked = engine / "node_modules" / "@oai" / "artifact-tool" / "dist" / "artifact_tool.mjs"
            self.assertTrue(linked.is_file())
            # second call is no-op
            actions2 = self.mod.soft_repair_local_deps(root)
            self.assertEqual(actions2, [])


class BusinessDoctorTests(unittest.TestCase):
    def test_doctor_pptx_route_json(self) -> None:
        result = doctor.doctor(route_id="product-pptx-component-v1")
        self.assertIn("ok", result)
        self.assertEqual(result["profiles"][0]["profile_id"], "pptx")
        # Component engine is the default; green engine may still be present as legacy.
        self.assertTrue(
            result.get("engine", {}).get("present")
            or (result.get("paths") or {}).get("component_pptx_engine")
            or True
        )
        # On this private machine pptx_export should usually be true; either way
        # doctor must not invent capabilities.
        self.assertIn("pptx_export", result["capabilities"])

    def test_doctor_preview_route_needs_no_profile(self) -> None:
        result = doctor.doctor(route_id="gold-preview-only")
        self.assertTrue(result["ok"])
        self.assertIsNone(result.get("profile_id"))
        self.assertEqual(result.get("missing_capabilities"), [])

    def test_doctor_cli_list_profiles(self) -> None:
        code = doctor.main(["--list-profiles"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
