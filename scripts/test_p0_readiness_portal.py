#!/usr/bin/env python3
"""P0 truth-contract tests for the business template shelf and registries."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from business_guided_portal import build_business_command, build_guided_portal_html
from query_production_library import APPROVED_STATUSES, load_entries
from validate_production_readiness import validate_repository


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "production-library/templates/settled/business-catalog.json"

CAPABILITY_KEYS = {
    "gold_viewable",
    "content_draft",
    "new_theme_preview",
    "new_theme_pptx",
    "new_theme_mp4",
    "business_selfserve",
}


def load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["templates"]


class CapabilityTruthTests(unittest.TestCase):
    def test_every_template_exposes_explicit_boolean_capability_matrix(self) -> None:
        for template in load_catalog():
            with self.subTest(template=template["slug"]):
                capabilities = template.get("capabilities") or {}
                self.assertTrue(CAPABILITY_KEYS.issubset(capabilities))
                for key in CAPABILITY_KEYS:
                    self.assertIs(type(capabilities[key]), bool)
                self.assertEqual(
                    template.get("production_ready"),
                    capabilities["business_selfserve"],
                    "legacy production_ready must be a derived compatibility alias",
                )
                self.assertIsInstance(template.get("requirements"), list)
                self.assertIsInstance(template.get("blockers"), list)

    def test_courseware4_does_not_claim_theme_generation(self) -> None:
        template = next(
            item
            for item in load_catalog()
            if item["slug"] == "fuler-fanqiehongsu-product-courseware-4-v1"
        )
        capabilities = template["capabilities"]
        self.assertTrue(capabilities["gold_viewable"])
        self.assertFalse(capabilities["new_theme_pptx"])
        self.assertFalse(capabilities["new_theme_mp4"])
        self.assertFalse(capabilities["business_selfserve"])
        self.assertTrue(any("未接线" in item for item in template["blockers"]))

    def test_repository_readiness_contract_has_no_errors(self) -> None:
        report = validate_repository(ROOT)
        self.assertEqual([], report["errors"], json.dumps(report, ensure_ascii=False, indent=2))

    def test_signed_gold_and_asset_component_members_are_queryable(self) -> None:
        self.assertIn("user-approved-gold", APPROVED_STATUSES)
        entries = load_entries()
        self.assertTrue(any(item.get("status") == "user-approved-gold" for item in entries))
        self.assertTrue(
            any(
                item.get("_registry_path")
                == "assets/component-library/product-training-precautions/registry.json"
                and item.get("id") == "pre-consult"
                for item in entries
            )
        )


class PortalContractTests(unittest.TestCase):
    def test_commands_match_the_requested_deliverable_and_keep_approval_gate(self) -> None:
        templates = {item["slug"]: item for item in load_catalog()}

        ppt_cmd = build_business_command(templates["product-courseware-component-v1"])
        self.assertIn("内容初稿", ppt_cmd)
        self.assertIn("确认后", ppt_cmd)
        self.assertIn("PPTX", ppt_cmd)
        self.assertNotIn("完整 MP4", ppt_cmd)
        # Green five-page shell retired from self-serve.
        green_cmd = build_business_command(templates["product-courseware-green-v1"])
        self.assertIn("仅查看金样", green_cmd)

        video_cmd = build_business_command(templates["product-video-faithful-v1"])
        self.assertIn("脚本和分镜", video_cmd)
        self.assertIn("确认后", video_cmd)
        self.assertIn("完整 MP4", video_cmd)
        self.assertIn("业务授权", video_cmd)
        self.assertNotIn("生成ppt", video_cmd.lower())

        health_cmd = build_business_command(templates["health-video-reference-tech-v1"])
        self.assertIn("7 段", health_cmd)
        self.assertIn("全部画面确认后", health_cmd)
        self.assertIn("只列缺口", health_cmd)

        for template in templates.values():
            self.assertNotIn("商品名或病名", build_business_command(template))

        preview_cmd = build_business_command(
            templates["fuler-fanqiehongsu-product-courseware-4-v1"]
        )
        self.assertIn("仅查看金样", preview_cmd)
        self.assertIn("不要生成正式成品", preview_cmd)

    def test_portal_cards_are_keyboard_buttons_and_mobile_grid_is_single_column(self) -> None:
        templates = load_catalog()
        html = build_guided_portal_html(templates, examples={})
        self.assertIn('const card = document.createElement("button")', html)
        self.assertIn('card.type = "button"', html)
        self.assertNotIn('document.createElement("article")', html)
        self.assertIn(".tcard:focus-visible", html)
        self.assertRegex(
            html,
            re.compile(
                r"@media \(max-width: 480px\).*?\.grid\s*\{\s*grid-template-columns:\s*1fr",
                re.S,
            ),
        )
        self.assertNotIn("本页一行四个卡片", html)
        self.assertIn("readiness-badge", html)

    def test_catalog_json_remains_serializable_for_portal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "portal.html"
            out.write_text(build_guided_portal_html(load_catalog()), encoding="utf-8")
            self.assertGreater(out.stat().st_size, 1000)

    def test_portal_intersects_template_requirements_with_local_runtime(self) -> None:
        templates = load_catalog()
        blocked = build_guided_portal_html(
            templates,
            runtime_capabilities={"pptx_export": True, "video_full": False},
        )
        self.assertIn("本机缺 video_full · 可先做草稿", blocked)
        # Default PPT (component) is self-serve when local pptx is ready.
        self.assertIn("可自助生成", blocked)


if __name__ == "__main__":
    unittest.main()
