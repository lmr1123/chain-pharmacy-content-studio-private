#!/usr/bin/env python3
"""Focused contract tests for the business route recommender."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recommend_business_route as selector  # noqa: E402


class BusinessRouteSelectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector_doc = selector.load_json(selector.SELECTOR_PATH)
        cls.routes_doc = selector.load_json(selector.ROUTES_PATH)

    def recommend(
        self,
        text: str,
        *,
        routes_doc: dict | None = None,
        capabilities: dict[str, bool] | None = None,
    ) -> dict:
        return selector.recommend(
            text,
            selector_doc=self.selector_doc,
            routes_doc=routes_doc or self.routes_doc,
            capabilities=capabilities,
        )

    def test_selector_profiles_are_capability_map_not_route_truth_copy(self) -> None:
        profiles = self.selector_doc["profiles"]
        self.assertEqual(len(profiles), 6)
        forbidden = {
            "active",
            "gates",
            "env_require",
            "adapter",
            "qa_profile",
            "delivery_whitelist",
            "name_zh",
            "deliverable",
        }
        for profile in profiles:
            self.assertFalse(forbidden.intersection(profile))
            for field in (
                "family",
                "structure_mode",
                "page_count",
                "gold_lineage",
                "reusable_capabilities",
                "signals",
                "explanation_zh",
            ):
                self.assertIn(field, profile)
            self.assertIn(profile["page_count"]["mode"], {"dynamic", "fixed"})
            for capability_type in ("page_types", "evidence", "scenes"):
                self.assertIn(
                    capability_type, profile["reusable_capabilities"]
                )

    def test_six_supported_business_intents(self) -> None:
        cases = {
            "舒心维C咀嚼片普通商品培训PPT，版式和页数要灵活": "product-pptx-component-v1",
            "按金银花绿色五页标准课型做商品培训PPT": "product-pptx-green-v1",
            "按穿心莲18页疾病、商品、销售场景课型做PPT": "product-pptx-disease-scenario-v1",
            "按速福达课件3做13页专项讲解PPT": "courseware3-pptx-v1",
            "做20页番茄红素成分健康科普PPT，米白番茄红": "ingredient-health-edu-pptx-v1",
            "为这个商品做完整MP4培训视频": "product-mp4-full-v1",
        }
        for text, route_id in cases.items():
            with self.subTest(text=text):
                result = self.recommend(text)
                self.assertEqual(result["decision"], "recommended")
                self.assertEqual(result["recommendation"]["route_id"], route_id)

    def test_multi_courseware_tab_composition_maps_to_component_route(self) -> None:
        for text in (
            "我要组合2到3个课件页签，再新增一个页签，保持同一套视觉风格",
            "多课型组合课件：商品信息总览、门店咨询框架、证据阶梯、异议应答",
        ):
            with self.subTest(text=text):
                result = self.recommend(text)
                self.assertEqual(result["decision"], "recommended")
                self.assertEqual(
                    result["recommendation"]["route_id"],
                    "product-pptx-component-v1",
                )

        capabilities = self.recommend(
            "多课型组合课件：商品信息总览、门店咨询框架、证据阶梯、异议应答"
        )["recommendation"]
        page_types = capabilities["reusable_capabilities"]["page_types"]
        for label in ("商品信息总览", "门店咨询框架", "商品证据阶梯", "门店异议应答"):
            self.assertIn(label, page_types)
        self.assertNotIn("课件4", capabilities["gold_lineage"]["source_zh"])

    def test_component_start_command_requires_workbuddy_confirmed_script(self) -> None:
        result = self.recommend("普通新商品培训PPT，页数需要灵活编排")
        command = result["recommendation"]["start_draft_command"]
        self.assertIn("--script-json", command)
        self.assertIn("业务确认", command)
        self.assertNotIn("--notes", command)

    def test_green_business_wording_does_not_fall_through_to_component(self) -> None:
        result = self.recommend("用绿色商品培训 PPT，商品是某商品")
        self.assertEqual(result["decision"], "recommended")
        self.assertEqual(
            result["recommendation"]["route_id"], "product-pptx-green-v1"
        )

    def test_product_training_without_format_returns_two_choices_and_one_question(self) -> None:
        result = self.recommend("我要做一个新的商品培训")
        self.assertEqual(result["decision"], "needs_clarification")
        self.assertEqual(
            [candidate["route_id"] for candidate in result["candidates"]],
            ["product-pptx-component-v1", "product-mp4-full-v1"],
        )
        self.assertIsInstance(result["question_zh"], str)
        self.assertTrue(result["question_zh"].strip())
        self.assertNotIn("questions_zh", result)

    def test_active_state_is_read_live_from_business_routes(self) -> None:
        routes_doc = copy.deepcopy(self.routes_doc)
        target = next(
            route
            for route in routes_doc["routes"]
            if route["route_id"] == "product-pptx-green-v1"
        )
        target["active"] = False
        result = self.recommend(
            "按绿色五页标准课型做商品培训PPT", routes_doc=routes_doc
        )
        self.assertEqual(result["decision"], "route_inactive")
        self.assertFalse(result["recommendation"]["active"])
        self.assertIsNone(result["recommendation"]["start_draft_command"])

    def test_environment_is_explicitly_unchecked_or_blocked(self) -> None:
        unchecked = self.recommend("做商品培训完整MP4视频")
        candidate = unchecked["recommendation"]
        self.assertEqual(candidate["render_readiness"], "not_checked")
        self.assertEqual(candidate["env_require"], ["video_full"])
        self.assertIn("business_doctor.py", candidate["doctor_command"])

        blocked = self.recommend(
            "做商品培训完整MP4视频", capabilities={"video_full": False}
        )
        self.assertEqual(blocked["decision"], "env_blocked")
        self.assertEqual(
            blocked["recommendation"]["missing_capabilities"], ["video_full"]
        )
        self.assertTrue(blocked["recommendation"]["can_start_draft"])
        self.assertFalse(blocked["recommendation"]["can_render"])

        ready = self.recommend(
            "做商品培训完整MP4视频", capabilities={"video_full": True}
        )
        self.assertEqual(ready["decision"], "recommended")
        self.assertEqual(ready["recommendation"]["render_readiness"], "ready")
        self.assertTrue(ready["recommendation"]["can_render"])

    def test_cli_json_output(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = selector.main(
                ["--text", "按速福达13页课件3做PPT", "--json"]
            )
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["recommendation"]["route_id"], "courseware3-pptx-v1")


if __name__ == "__main__":
    unittest.main()
