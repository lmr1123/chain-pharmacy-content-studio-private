#!/usr/bin/env python3
"""Regression contract for the reviewed r4 component portal-preview suite."""

from __future__ import annotations

import hashlib
import json
import unittest

from build_component_portal_preview_suite import CASES, VISUAL_REVIEW_SCHEMA
from sync_settled_template_previews import (
    COMPONENT_PREVIEW_MAX_COURSEWARE4_BACKGROUND_RATIO,
    COMPONENT_PREVIEW_MAX_GOLD_LAYOUT_SIMILARITY,
    COMPONENT_PREVIEW_MAX_TOP_YELLOW_RED_RATIO,
    COMPONENT_PREVIEW_QA_DIR,
    COMPONENT_PREVIEW_QA_SCHEMA,
    component_preview_qa_failures,
)


class ComponentPortalPreviewSuiteTests(unittest.TestCase):
    def test_formal_suite_is_bound_to_the_reviewed_r4_sources(self) -> None:
        failures = component_preview_qa_failures(COMPONENT_PREVIEW_QA_DIR)
        self.assertEqual([], failures, failures)
        summary_path = COMPONENT_PREVIEW_QA_DIR / "qa-summary.json"
        review_path = COMPONENT_PREVIEW_QA_DIR / "visual-review.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        review = json.loads(review_path.read_text(encoding="utf-8"))
        self.assertEqual(COMPONENT_PREVIEW_QA_SCHEMA, summary["schema"])
        self.assertEqual(VISUAL_REVIEW_SCHEMA, review["schema"])
        self.assertEqual("Codex逐页视觉复核", review["reviewer"])
        self.assertTrue(review["reviewed"])
        self.assertEqual(
            hashlib.sha256(review_path.read_bytes()).hexdigest(),
            summary["visual_review_sha256"],
        )

        cases_by_slot = {case["suite_slot"]: case for case in summary["cases"]}
        review_by_id = {case["case_id"]: case for case in review["cases"]}
        self.assertEqual({"A", "B", "C"}, set(cases_by_slot))
        self.assertEqual(18, sum(case["page_count"] for case in summary["cases"]))
        for spec in CASES:
            case = cases_by_slot[spec.slot]
            self.assertEqual(spec.job_id, case["source_job_id"])
            self.assertTrue(spec.job_id.endswith("-r4"))
            self.assertEqual(spec.expected_deck_sha256, case["deck_sha256"])
            self.assertEqual(list(spec.reviewed_page_sha256), [page["render_sha256"] for page in case["page_qa"]])
            self.assertTrue(case["slides_test_passed"])
            self.assertEqual(0, case["placeholder_hits"])
            self.assertEqual(0, case["gold_residual_hits"])
            self.assertEqual(0, case["gold_source_media_hash_hits"])
            self.assertEqual(0, case["overflow_hits"])

            metrics = case["visual_metrics"]
            self.assertEqual(0, metrics["courseware4_preview_exact_hash_hits"])
            self.assertLessEqual(metrics["max_courseware4_background_ratio"], COMPONENT_PREVIEW_MAX_COURSEWARE4_BACKGROUND_RATIO)
            self.assertLessEqual(metrics["max_top_yellow_red_ratio"], COMPONENT_PREVIEW_MAX_TOP_YELLOW_RED_RATIO)
            self.assertLessEqual(metrics["max_gold_layout_similarity"], COMPONENT_PREVIEW_MAX_GOLD_LAYOUT_SIMILARITY)
            self.assertEqual(6, len(case["visual_metrics_by_preview"]))

            review_case = review_by_id[spec.case_id]
            self.assertEqual(case["deck_sha256"], review_case["deck_sha256"])
            self.assertEqual(case["page_count"], len(review_case["pages"]))
            for page in review_case["pages"]:
                self.assertTrue(page["reviewed"])
                for field in (
                    "collision_hits",
                    "clipping_hits",
                    "duplicate_page_number_hits",
                    "body_overflow_hits",
                ):
                    self.assertEqual(0, page[field])

    def test_case_c_detail_frame_has_an_explicit_crop_provenance(self) -> None:
        summary = json.loads(
            (COMPONENT_PREVIEW_QA_DIR / "qa-summary.json").read_text(
                encoding="utf-8"
            )
        )
        case_c = next(case for case in summary["cases"] if case["suite_slot"] == "C")
        detail = case_c["preview_derivations"]["key-05.png"]
        self.assertEqual("crop-resize", detail["operation"])
        self.assertEqual(5, detail["source_page"])
        self.assertEqual([96, 54, 1184, 666], detail["crop_box_px"])
        self.assertEqual(
            case_c["page_qa"][4]["render_sha256"],
            detail["source_render_sha256"],
        )
        self.assertEqual(
            case_c["preview_sha256"]["key-05.png"],
            detail["output_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
