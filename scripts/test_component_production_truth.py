#!/usr/bin/env python3
"""Production-truth contract for the flexible component PPT fallback."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "production-library"
PAGE_TYPES = (
    "product_overview",
    "consultation_framework",
    "evidence_ladder",
    "objection_handling",
)
QA_SUMMARY = (
    LIBRARY
    / "validation/courseware/product-courseware-component-flexible-uat-v1"
    / "portal-preview/qa-summary.json"
)
VISUAL_REVIEW = QA_SUMMARY.with_name("visual-review.json")
QA_SHA256 = "7ff6fbca1fe00f7968a1ddf998a1fd4f7821bcc3f7aad731cc7cccc36ec752f6"
REVIEW_SHA256 = "c6b54744e6521ab8b78882f1125be552c2a646ce03995622a850f76519c48272"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ComponentProductionTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(
            LIBRARY / "page-types/product-training/registry.json"
        )
        cls.qa = load_json(QA_SUMMARY)
        cls.review = load_json(VISUAL_REVIEW)
        cls.template_registry = load_json(LIBRARY / "registries/templates.json")
        cls.style_registry = load_json(LIBRARY / "registries/styles.json")
        cls.manifest_path = (
            LIBRARY / "templates/settled/product-courseware-component-v1/manifest.json"
        )
        cls.manifest = load_json(cls.manifest_path)

    def test_suite_evidence_is_hash_bound_and_page_reviewed(self) -> None:
        self.assertEqual(sha256(QA_SUMMARY), QA_SHA256)
        self.assertEqual(sha256(VISUAL_REVIEW), REVIEW_SHA256)
        self.assertTrue(self.qa["ok"])
        self.assertTrue(self.review["reviewed"])
        self.assertEqual([case["page_count"] for case in self.qa["cases"]], [7, 6, 5])
        self.assertEqual(sum(len(case["pages"]) for case in self.review["cases"]), 18)

        qa_cases = {case["case_id"]: case for case in self.qa["cases"]}
        review_cases = {case["case_id"]: case for case in self.review["cases"]}
        for page_type, refs in self.registry["production_validation"][
            "page_type_cases"
        ].items():
            self.assertIn(page_type, PAGE_TYPES)
            for ref in refs:
                page = qa_cases[ref["case_id"]]["page_qa"][ref["page"] - 1]
                reviewed = review_cases[ref["case_id"]]["pages"][ref["page"] - 1]
                self.assertEqual(page["page_type"], page_type)
                self.assertTrue(page["passed"])
                self.assertEqual(reviewed["render_sha256"], page["render_sha256"])
                self.assertTrue(reviewed["reviewed"])

    def test_four_page_types_and_recipes_are_production_validated(self) -> None:
        entries = {item["id"]: item for item in self.registry["page_types"]}
        validation = self.registry["production_validation"]
        self.assertEqual(validation["status"], "production-validated")
        self.assertEqual(validation["qa_summary_sha256"], QA_SHA256)
        self.assertEqual(validation["visual_review_sha256"], REVIEW_SHA256)
        for page_type in PAGE_TYPES:
            self.assertEqual(entries[page_type]["status"], "production-validated")
            self.assertEqual(
                entries[page_type]["production_validation_ref"],
                f"#/production_validation/page_type_cases/{page_type}",
            )
            recipe = load_json(
                LIBRARY / f"page-types/product-training/recipes/{page_type}.json"
            )
            self.assertEqual(recipe["page_type"], page_type)
            self.assertEqual(recipe["status"], "production-validated")
            self.assertEqual(
                recipe["production_validation_ref"],
                f"../registry.json#/production_validation/page_type_cases/{page_type}",
            )

    def test_blue_ppt_adapter_uses_the_same_production_evidence(self) -> None:
        style = next(
            item
            for item in self.style_registry["items"]
            if item["id"] == "style-pack.reference-product-blue-v1"
        )
        tokens = load_json(LIBRARY / "styles/reference-product-blue-v1/tokens.json")
        self.assertEqual(style["status"], "production-validated")
        self.assertEqual(style["ppt_adapter"]["status"], "production-validated")
        self.assertEqual(style["production_validation"]["qa_summary_sha256"], QA_SHA256)
        self.assertEqual(tokens["status"], "production-validated")
        self.assertEqual(tokens["production_validation"]["qa_summary_sha256"], QA_SHA256)
        self.assertEqual(
            tokens["production_validation"]["visual_review_sha256"], REVIEW_SHA256
        )

    def test_template_is_named_as_fallback_without_promoting_smoke_to_gold(self) -> None:
        registered = next(
            item
            for item in self.template_registry["items"]
            if item["id"] == "template.product-courseware-component-v1"
        )
        expected_name = "灵活构件商品培训 PPT（兜底）"
        self.assertEqual(registered["name_zh"], expected_name)
        self.assertEqual(registered["status"], "production-default")
        self.assertTrue(set(PAGE_TYPES).issubset(registered["supported_scene_types"]))
        self.assertEqual(registered["production_validated_page_types"], list(PAGE_TYPES))
        self.assertFalse(registered["canonical_artifact"]["is_gold_sample"])
        self.assertEqual(
            registered["canonical_artifact"]["role"],
            "legacy-12-page-structure-smoke-only",
        )
        self.assertEqual(
            registered["production_validation"]["qa_summary_sha256"], QA_SHA256
        )

        manifest = self.manifest
        self.assertEqual(manifest["business_catalog"]["name_zh"], expected_name)
        self.assertEqual(manifest["preview"]["name_zh"], expected_name)
        self.assertFalse(manifest["canonical_is_gold_sample"])
        self.assertEqual(manifest["canonical_role"], "legacy-12-page-structure-smoke-only")
        self.assertEqual(manifest["production_validated_page_types"], list(PAGE_TYPES))
        self.assertEqual(manifest["production_validation"]["qa_summary_sha256"], QA_SHA256)
        self.assertIn("旧兼容键", manifest["preview"]["capabilities_note_zh"])
        self.assertIn("结构冒烟", manifest["preview"]["status_note"])

        canonical = self.manifest_path.parent / manifest["canonical_artifact"]
        with zipfile.ZipFile(canonical) as archive:
            slides = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
        self.assertEqual(len(slides), 12)
        self.assertNotIn(sha256(canonical), {case["deck_sha256"] for case in self.qa["cases"]})


if __name__ == "__main__":
    unittest.main()
