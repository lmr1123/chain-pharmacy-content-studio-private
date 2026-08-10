#!/usr/bin/env python3
"""P0 truth-contract tests for the business template shelf and registries."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from business_guided_portal import (
    _component_page_type_label_zh,
    build_business_command,
    build_guided_portal_html,
    build_route_selector_prompt,
    deliverable_badges,
    green_gold_portal_example_paragraphs,
    load_business_modes,
    load_business_route_selector,
    paragraphs_to_html_blocks,
    portal_example_paragraphs_for_slug,
    shelf_group_for_template,
)
from query_production_library import APPROVED_STATUSES, load_entries
from sync_settled_template_previews import (
    CATALOG,
    COMPONENT_PREVIEW_MAX_COURSEWARE4_BACKGROUND_RATIO,
    COMPONENT_PREVIEW_MAX_CROSS_CASE_KEY_LAYOUT_SIMILARITY,
    COMPONENT_PREVIEW_MAX_GOLD_LAYOUT_SIMILARITY,
    COMPONENT_PREVIEW_MAX_TOP_YELLOW_RED_RATIO,
    COMPONENT_PREVIEW_QA_DIR,
    COMPONENT_PREVIEW_QA_SCHEMA,
    COURSEWARE4_GOLD_PREVIEW_DIR,
    COURSEWARE4_STYLE_PACK_ID,
    _top_yellow_red_ratio,
    component_preview_qa_failures,
    component_preview_suite_evidence,
    component_preview_visual_metrics,
    derive_catalog_entry,
    pick_keys,
    qualified_component_preview_sources,
)
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


def source_catalog_for_portal() -> list[dict]:
    """Use current source inventory without requiring generated package refresh."""
    source_only_keys = {"cover_src", "keys", "fallback_keys"}
    return [
        {key: value for key, value in entry.items() if key not in source_only_keys}
        for entry in CATALOG
    ]


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
        self.assertEqual(
            {
                "seedance-health-edu-v1",
                "jiugongge-health-edu-v1",
                "jiugongge-health-edu-compliance-v1",
                "digital-human-presenter-scheme-C",
                "domestic-flat-cartoon-health-mg-v1",
            },
            {
                item.get("id")
                for item in entries
                if item.get("_registry_type") == "business-mode"
            },
        )
        self.assertTrue(
            any(
                item.get("_registry_path")
                == "assets/component-library/product-training-precautions/registry.json"
                and item.get("id") == "pre-consult"
                for item in entries
            )
        )

    def test_kangaisen_ingredient_health_template_has_one_registry_entry(self) -> None:
        entries = load_entries()
        matches = [
            item
            for item in entries
            if item.get("id") == "template.kangaisen-lycopene-health-edu-v1"
        ]
        self.assertEqual(1, len(matches))
        entry = matches[0]
        settled_dir = (
            "production-library/templates/settled/"
            "kangaisen-lycopene-health-edu-v1"
        )
        self.assertEqual(
            1,
            sum(item.get("settled_template_dir") == settled_dir for item in entries),
        )
        self.assertEqual(
            "production-library/registries/templates.json",
            entry["_registry_path"],
        )
        self.assertEqual(settled_dir, entry["settled_template_dir"])
        self.assertEqual(
            "production-library/templates/settled/kangaisen-lycopene-health-edu-v1/manifest.json",
            entry["manifest"],
        )
        self.assertEqual(
            "style-pack.lycopene-health-edu-cream-red-v1",
            entry["style_pack_id"],
        )
        self.assertIn(
            "production-library/engines/ingredient-health-edu-pptx-v1/export.mjs",
            entry["source_projects"],
        )
        for relative_path in (
            entry["manifest"],
            entry["canonical_artifact"]["path"],
            *entry["source_projects"],
        ):
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)
        self.assertTrue(
            any(
                item.get("id") == entry["style_pack_id"]
                and item.get("_registry_type") == "style"
                for item in entries
            )
        )


class PortalContractTests(unittest.TestCase):
    def test_preview_sync_prefers_catalog_gold_keys_over_stale_settled(self) -> None:
        """Catalog gold thumbs must win so bootstrap fallbacks can be replaced."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "settled-template"
            preview = root / "preview"
            preview.mkdir(parents=True)
            stale_labels = [f"旧回退关键页 {index}" for index in range(1, 6)]
            for index in range(1, 6):
                Image.new("RGB", (16, 9), (index, index, index)).save(
                    preview / f"key-{index:02d}.png"
                )
            (root / "manifest.json").write_text(
                json.dumps(
                    {"preview": {"key_frame_labels_zh": stale_labels}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            gold_dir = Path(tmp) / "gold-thumbs"
            gold_dir.mkdir()
            gold_sources = []
            gold_labels = [f"金样关键页 {index}" for index in range(1, 6)]
            for index, label in enumerate(gold_labels, 1):
                path = gold_dir / f"key-{index:02d}.png"
                Image.new("RGB", (16, 9), (200 + index, 0, 0)).save(path)
                gold_sources.append((path, label))
            missing = Path(tmp) / "missing.png"
            entry = {
                "preview_key_limit": 6,
                "keys": gold_sources,
                "fallback_keys": [(missing, "缺失回退")],
            }

            chosen = pick_keys(entry, root)

            self.assertEqual(5, len(chosen))
            self.assertEqual(gold_labels, [label for _, label in chosen])
            self.assertTrue(all(path.parent == gold_dir for path, _ in chosen))

    def test_preview_sync_uses_settled_when_catalog_keys_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "settled-template"
            preview = root / "preview"
            preview.mkdir(parents=True)
            labels = [f"已签样关键页 {index}" for index in range(1, 6)]
            for index in range(1, 6):
                Image.new("RGB", (16, 9), (index, index, index)).save(
                    preview / f"key-{index:02d}.png"
                )
            (root / "manifest.json").write_text(
                json.dumps(
                    {"preview": {"key_frame_labels_zh": labels}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            missing = Path(tmp) / "missing.png"
            entry = {
                "preview_key_limit": 6,
                "keys": [(missing, "缺失金样 1"), (missing, "缺失金样 2")],
                "fallback_keys": [(missing, "缺失回退")],
            }

            chosen = pick_keys(entry, root)

            self.assertEqual(5, len(chosen))
            self.assertEqual(labels, [label for _, label in chosen])
            self.assertTrue(all(path.parent == preview for path, _ in chosen))

    def test_component_preview_requires_a_qualified_three_case_uat_suite(self) -> None:
        self.assertEqual(
            ROOT
            / "production-library/validation/courseware/"
            "product-courseware-component-flexible-uat-v1/portal-preview",
            COMPONENT_PREVIEW_QA_DIR,
        )
        with tempfile.TemporaryDirectory() as tmp:
            qa_dir = Path(tmp) / "portal-preview"
            qa_dir.mkdir()
            names = ("cover.png", *(f"key-{i:02d}.png" for i in range(1, 6)))
            sequences = {
                "A": [
                    "cover", "hook", "pain-map", "ingredient-proof",
                    "benefit-chain", "audience", "summary",
                ],
                "B": [
                    "cover", "disease-bridge", "scenario", "recommendation",
                    "precautions", "summary",
                ],
                "C": [
                    "cover", "composition-map", "new-comparison-matrix",
                    "action-checklist", "summary",
                ],
            }
            capability_by_slot = {
                "A": ["product-courseware-green-v1"],
                "B": ["disease-product-scenario-v1"],
                "C": ["sufuda-mabaloshawei-product-courseware-3-v1"],
            }
            cases: list[dict] = []
            for case_number, slot in enumerate(("A", "B", "C"), 1):
                case_id = f"case-{slot.lower()}"
                case_dir = qa_dir / "cases" / case_id
                pages_dir = case_dir / "pages"
                pages_dir.mkdir(parents=True)
                for frame_index, name in enumerate(names):
                    image = Image.new("RGB", (1280, 720), (0, 0, 0))
                    draw = ImageDraw.Draw(image)
                    if slot == "A":
                        x = 35 + frame_index * 120
                        draw.rectangle((x, 85, x + 8, 635), fill=(0, 90, 190))
                    elif slot == "B":
                        y = 45 + frame_index * 95
                        draw.rectangle((90, y, 1190, y + 8), fill=(0, 145, 175))
                    else:
                        offset = frame_index * 45
                        draw.line(
                            (85 + offset, 620, 930 + offset, 95),
                            fill=(25, 105, 210),
                            width=9,
                        )
                    image.save(case_dir / name)

                page_qa: list[dict] = []
                for page_number, page_type in enumerate(sequences[slot], 1):
                    page = Image.new("RGB", (640, 360), (4, 12, 24))
                    draw = ImageDraw.Draw(page)
                    draw.rectangle(
                        (
                            20 * case_number,
                            18 * page_number,
                            20 * case_number + 12,
                            18 * page_number + 160,
                        ),
                        fill=(20, 80 + case_number * 20, 170),
                    )
                    page_path = pages_dir / f"page-{page_number:03d}.png"
                    page.save(page_path)
                    page_qa.append(
                        {
                            "page_number": page_number,
                            "page_type": page_type,
                            "passed": True,
                            "render_sha256": hashlib.sha256(
                                page_path.read_bytes()
                            ).hexdigest(),
                        }
                    )

                deck_path = case_dir / "deck.pptx"
                with zipfile.ZipFile(deck_path, "w") as deck:
                    deck.writestr("[Content_Types].xml", "<Types/>")
                    deck.writestr(
                        "ppt/presentation.xml", f"<presentation slot='{slot}'/>"
                    )
                cases.append(
                    {
                        "case_id": case_id,
                        "suite_slot": slot,
                        "name_zh": f"正式构件案例{slot}",
                        "source_job_id": f"uat-component-suite-{slot.lower()}",
                        "is_gold_sample": False,
                        "visual_qa_passed": True,
                        "visual_difference_review_passed": True,
                        "provenance_ok": True,
                        "qa_backend": "artifact-tool",
                        "slides_test_passed": True,
                        "placeholder_hits": 0,
                        "gold_residual_hits": 0,
                        "gold_source_media_hash_hits": 0,
                        "overflow_hits": 0,
                        "style_pack_id": "style-pack.component-flexible-distinct-v1",
                        "deck_sha256": hashlib.sha256(deck_path.read_bytes()).hexdigest(),
                        "page_count": len(sequences[slot]),
                        "settled_capability_slugs": capability_by_slot[slot],
                        "page_type_sequence": sequences[slot],
                        "new_page_types": (
                            ["new-comparison-matrix"] if slot == "C" else []
                        ),
                        "page_qa": page_qa,
                        "portal_key_index": case_number,
                        "preview_source_page_numbers": {
                            name: min(frame_index + 1, len(sequences[slot]))
                            for frame_index, name in enumerate(names)
                        },
                        "preview_sha256": {
                            name: hashlib.sha256((case_dir / name).read_bytes()).hexdigest()
                            for name in names
                        },
                    }
                )

            summary = {
                "schema": COMPONENT_PREVIEW_QA_SCHEMA,
                "ok": True,
                "template_slug": "product-courseware-component-v1",
                "source_scope": "uat-suite",
                "style_pack_id": "style-pack.component-flexible-distinct-v1",
                "style_label_zh": "统一浅蓝商品培训视觉",
                "cases": cases,
            }

            visual_review = {
                "schema": "component-portal-preview-visual-review-v1",
                "reviewed": True,
                "reviewer": "Codex逐页视觉复核",
                "cases": [
                    {
                        "case_id": case["case_id"],
                        "deck_sha256": case["deck_sha256"],
                        "reviewed": True,
                        "pages": [
                            {
                                **record,
                                "reviewed": True,
                                "collision_hits": 0,
                                "clipping_hits": 0,
                                "duplicate_page_number_hits": 0,
                                "body_overflow_hits": 0,
                            }
                            for record in case["page_qa"]
                        ],
                    }
                    for case in cases
                ],
            }
            review_path = qa_dir / "visual-review.json"
            review_path.write_text(
                json.dumps(visual_review, ensure_ascii=False), encoding="utf-8"
            )
            summary["visual_review_sha256"] = hashlib.sha256(
                review_path.read_bytes()
            ).hexdigest()

            def write_summary(value: dict) -> None:
                (qa_dir / "qa-summary.json").write_text(
                    json.dumps(value, ensure_ascii=False), encoding="utf-8"
                )

            summary["cases"][0]["placeholder_hits"] = 1
            write_summary(summary)
            self.assertIn(
                "case:case-a:placeholder_hits",
                component_preview_qa_failures(qa_dir),
            )
            self.assertIsNone(qualified_component_preview_sources(qa_dir))

            summary["cases"][0]["placeholder_hits"] = 0
            write_summary(summary)
            failures = component_preview_qa_failures(qa_dir)
            self.assertEqual([], failures, failures)
            qualified = qualified_component_preview_sources(qa_dir)
            self.assertIsNotNone(qualified)
            cover, keys = qualified
            self.assertEqual(qa_dir / "cases/case-a/cover.png", cover)
            self.assertEqual(3, len(keys))
            evidence = component_preview_suite_evidence(qa_dir)
            self.assertIsNotNone(evidence)
            self.assertEqual(3, evidence["case_count"])
            self.assertEqual(
                ["A", "B", "C"],
                [item["suite_slot"] for item in evidence["cases"]],
            )

            missing_overflow_proof = copy.deepcopy(summary)
            missing_overflow_proof["cases"][0]["slides_test_passed"] = False
            write_summary(missing_overflow_proof)
            self.assertIn(
                "case:case-a:slides_test_not_passed",
                component_preview_qa_failures(qa_dir),
            )

            tampered_review = review_path.read_bytes()
            review_path.write_bytes(tampered_review + b" ")
            write_summary(summary)
            self.assertIn(
                "visual_review_hash_binding_mismatch",
                component_preview_qa_failures(qa_dir),
            )
            review_path.write_bytes(tampered_review)

            two_cases = copy.deepcopy(summary)
            two_cases["cases"] = two_cases["cases"][:2]
            write_summary(two_cases)
            self.assertIn(
                "suite_case_count_too_small",
                component_preview_qa_failures(qa_dir),
            )

            mixed_style = copy.deepcopy(summary)
            mixed_style["cases"][1]["style_pack_id"] = "style-pack.other-v1"
            write_summary(mixed_style)
            self.assertIn(
                "case:case-b:mixed_style_pack",
                component_preview_qa_failures(qa_dir),
            )

            gold_style = copy.deepcopy(summary)
            gold_style["style_pack_id"] = COURSEWARE4_STYLE_PACK_ID
            for case in gold_style["cases"]:
                case["style_pack_id"] = COURSEWARE4_STYLE_PACK_ID
            write_summary(gold_style)
            self.assertIn(
                "courseware4_style_pack_forbidden",
                component_preview_qa_failures(qa_dir),
            )

            short_formal = copy.deepcopy(summary)
            short_formal["cases"][0]["page_type_sequence"] = [
                "cover",
                "hook",
                "pain-map",
            ]
            short_formal["cases"][0]["page_count"] = 3
            short_formal["cases"][0]["page_qa"] = short_formal["cases"][0][
                "page_qa"
            ][:3]
            write_summary(short_formal)
            self.assertIn(
                "case:case-a:formal_deck_page_count_too_small",
                component_preview_qa_failures(qa_dir),
            )

            duplicate_sequence = copy.deepcopy(summary)
            duplicate_sequence["cases"][1]["page_type_sequence"] = list(
                duplicate_sequence["cases"][0]["page_type_sequence"]
            )
            duplicate_sequence["cases"][1]["page_count"] = 7
            write_summary(duplicate_sequence)
            self.assertIn(
                "page_type_sequences_not_unique",
                component_preview_qa_failures(qa_dir),
            )

            one_source = copy.deepcopy(summary)
            for case in one_source["cases"]:
                case["settled_capability_slugs"] = ["product-courseware-green-v1"]
            write_summary(one_source)
            self.assertIn(
                "suite_settled_capability_count_invalid",
                component_preview_qa_failures(qa_dir),
            )

            no_new_page_type = copy.deepcopy(summary)
            no_new_page_type["cases"][2]["new_page_types"] = []
            write_summary(no_new_page_type)
            self.assertIn(
                "suite_new_page_type_missing",
                component_preview_qa_failures(qa_dir),
            )

            missing_preview_provenance = copy.deepcopy(summary)
            missing_preview_provenance["cases"][0].pop(
                "preview_source_page_numbers"
            )
            write_summary(missing_preview_provenance)
            self.assertIn(
                "case:case-a:preview_source_pages_invalid",
                component_preview_qa_failures(qa_dir),
            )

            write_summary(summary)
            page_path = qa_dir / "cases/case-b/pages/page-001.png"
            original_page = page_path.read_bytes()
            page_path.write_bytes(original_page + b"changed")
            self.assertIn(
                "case:case-b:page_render_hash_binding_mismatch",
                component_preview_qa_failures(qa_dir),
            )
            page_path.write_bytes(original_page)

            targets = (
                (qa_dir / "cases/case-b/key-02.png", (0, 135, 185), 1),
                (qa_dir / "cases/case-c/key-03.png", (20, 95, 220), 2),
            )
            originals = [(path, path.read_bytes()) for path, _, _ in targets]
            for path, color, case_index in targets:
                recolor = Image.new("RGB", (1280, 720), (0, 0, 0))
                ImageDraw.Draw(recolor).rectangle((35, 85, 43, 635), fill=color)
                recolor.save(path)
                summary["cases"][case_index]["preview_sha256"][path.name] = (
                    hashlib.sha256(path.read_bytes()).hexdigest()
                )
            write_summary(summary)
            self.assertGreater(
                COMPONENT_PREVIEW_MAX_CROSS_CASE_KEY_LAYOUT_SIMILARITY,
                0,
            )
            self.assertIn(
                "cross_case_key_layout_similarity_too_high",
                component_preview_qa_failures(qa_dir),
            )
            for (path, original), (_, _, case_index) in zip(originals, targets):
                path.write_bytes(original)
                summary["cases"][case_index]["preview_sha256"][path.name] = (
                    hashlib.sha256(original).hexdigest()
                )

            background = qa_dir / "cases/case-a/key-01.png"
            Image.new("RGB", (1280, 720), (207, 204, 197)).save(background)
            summary["cases"][0]["preview_sha256"]["key-01.png"] = hashlib.sha256(
                background.read_bytes()
            ).hexdigest()
            write_summary(summary)
            self.assertIn(
                "case:case-a:courseware4_background_ratio_too_high",
                component_preview_qa_failures(qa_dir),
            )

            accent = Image.new("RGB", (1280, 720), (10, 30, 50))
            ImageDraw.Draw(accent).rectangle((0, 0, 1279, 239), fill=(255, 190, 20))
            accent.save(background)
            summary["cases"][0]["preview_sha256"]["key-01.png"] = hashlib.sha256(
                background.read_bytes()
            ).hexdigest()
            write_summary(summary)
            self.assertIn(
                "case:case-a:courseware4_yellow_red_ratio_too_high",
                component_preview_qa_failures(qa_dir),
            )

            background.write_bytes(
                (COURSEWARE4_GOLD_PREVIEW_DIR / "slide-01.png").read_bytes()
            )
            summary["cases"][0]["preview_sha256"]["key-01.png"] = hashlib.sha256(
                background.read_bytes()
            ).hexdigest()
            write_summary(summary)
            failures = component_preview_qa_failures(qa_dir)
            self.assertIn("case:case-a:courseware4_preview_hash_hit", failures)
            self.assertIn("case:case-a:courseware4_layout_similarity_too_high", failures)

    def test_courseware4_color_detector_distinguishes_coral_from_brick_red(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            coral_path = Path(tmp) / "coral.png"
            brick_path = Path(tmp) / "brick.png"
            for path, color in (
                (coral_path, (248, 120, 80)),
                (brick_path, (176, 40, 40)),
            ):
                image = Image.new("RGB", (1280, 720), (64, 168, 224))
                ImageDraw.Draw(image).rectangle((0, 0, 1279, 239), fill=color)
                image.save(path)
            self.assertEqual(0, _top_yellow_red_ratio(coral_path))
            self.assertGreater(
                _top_yellow_red_ratio(brick_path),
                COMPONENT_PREVIEW_MAX_TOP_YELLOW_RED_RATIO,
            )

    def test_current_component_preview_is_a_qualified_three_case_suite(self) -> None:
        failures = component_preview_qa_failures(COMPONENT_PREVIEW_QA_DIR)
        self.assertEqual([], failures, failures)
        self.assertIsNotNone(
            qualified_component_preview_sources(COMPONENT_PREVIEW_QA_DIR)
        )
        summary = json.loads(
            (COMPONENT_PREVIEW_QA_DIR / "qa-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(["A", "B", "C"], [case["suite_slot"] for case in summary["cases"]])
        for case in summary["cases"]:
            metrics = case["visual_metrics"]
            self.assertEqual(0, metrics["courseware4_preview_exact_hash_hits"])
            self.assertLessEqual(
                metrics["max_courseware4_background_ratio"],
                COMPONENT_PREVIEW_MAX_COURSEWARE4_BACKGROUND_RATIO,
            )
            self.assertLessEqual(
                metrics["max_top_yellow_red_ratio"],
                COMPONENT_PREVIEW_MAX_TOP_YELLOW_RED_RATIO,
            )
            self.assertLessEqual(
                metrics["max_gold_layout_similarity"],
                COMPONENT_PREVIEW_MAX_GOLD_LAYOUT_SIMILARITY,
            )

    def test_route_selector_prompt_recommends_before_any_task_creation(self) -> None:
        prompt = build_route_selector_prompt(
            "可编辑 PPTX",
            "疾病 + 商品 + 场景演练",
            "固定 18 页",
            "给新员工培训，已有包装图和审核要点",
        )
        self.assertIn("可编辑 PPTX", prompt)
        self.assertIn("疾病 + 商品 + 场景演练", prompt)
        self.assertIn("固定 18 页", prompt)
        self.assertIn("已有包装图和审核要点", prompt)
        self.assertIn("business_job recommend", prompt)
        self.assertIn("不要原样回显内部路线标识、脚本命令或建草稿命令", prompt)
        self.assertIn("推荐的已签样金样模板", prompt)
        self.assertIn("推荐理由", prompt)
        self.assertIn("确认模板【模板名】", prompt)
        self.assertIn("不得创建任务", prompt)
        self.assertIn("不得生成正式成品", prompt)
        self.assertNotIn("python3", prompt)
        self.assertNotIn("route_id", prompt)
        self.assertNotRegex(prompt, r"business_job(?:\.py)?\s+new")
        self.assertNotIn("--route", prompt)

    def test_route_selector_loads_only_portal_safe_intent_labels_and_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            fallback = load_business_route_selector(missing)
            self.assertEqual("我不懂模板，帮我选", fallback["title_zh"])
            labels = [item["label_zh"] for item in fallback["structures"]]
            self.assertIn("固定 5 页 · 绿色紧凑课", labels)
            self.assertNotIn("动态页数 · 灵活构件兜底 PPT", labels)
            self.assertNotIn("灵活构件", " ".join(labels))

            configured_path = Path(tmp) / "selector.json"
            configured_path.write_text(
                json.dumps(
                    {
                        "profiles": [
                            {
                                "route_id": "internal-route-must-not-leak",
                                "family": "internal-family",
                            }
                        ],
                        "portal": {
                            "title_zh": "不会选课型？先问 WorkBuddy",
                        },
                        "intent_options": {
                            "deliverables": [
                                {
                                    "value": "pptx",
                                    "label_zh": "可编辑演示文稿（PPTX）",
                                }
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            configured = load_business_route_selector(configured_path)
            self.assertEqual("不会选课型？先问 WorkBuddy", configured["title_zh"])
            self.assertIn(
                "可编辑演示文稿（PPTX）",
                [item["label_zh"] for item in configured["deliverables"]],
            )
            self.assertNotIn("profiles", configured)
            self.assertNotIn("route_id", json.dumps(configured, ensure_ascii=False))

            configured_path.write_text("{broken", encoding="utf-8")
            recovered = load_business_route_selector(configured_path)
            self.assertEqual("我不懂模板，帮我选", recovered["title_zh"])

    def test_route_selector_form_is_not_on_business_portal(self) -> None:
        """Business picks gold cards; dropdown form options are unreadable and removed."""
        html = build_guided_portal_html(load_catalog(), examples={})
        self.assertIn('id="template-grid"', html)
        self.assertNotIn('id="route-selector"', html)
        self.assertNotIn("不会选也能开始", html)
        self.assertNotIn("我不懂模板，帮我选", html)
        self.assertNotIn("生成选课口令", html)
        self.assertNotIn('id="selector-copy"', html)
        self.assertNotIn("function buildRouteSelectorPrompt()", html)
        self.assertNotIn("ROUTE_SELECTOR_PROMPT", html)
        self.assertNotIn("selector-layout", html)
        self.assertNotIn("route_id", html)
        self.assertNotRegex(html, r"business_job(?:\.py)?\s+new")
        # Keep gold-card shelf as the only portal selection UI.
        self.assertIn("选金样", html)
        self.assertIn("确认选用 · 复制给 WorkBuddy", html)
        self.assertNotIn("internal-route-must-not-leak", html)

    def test_green_portal_example_uses_gold_composition_not_blank_fill(self) -> None:
        paras = green_gold_portal_example_paragraphs()
        self.assertGreaterEqual(len(paras), 20)
        text = "\n".join(paras)
        self.assertIn("金样内容组成", text)
        self.assertIn("金银花露", text)
        self.assertIn("【封面", text)
        self.assertIn("商品介绍、核心卖点、适宜人群", text)
        self.assertIn("联合用药话术", text)
        self.assertIn("品种对标", text)
        self.assertIn("注意事项", text)
        self.assertIn("小儿咽扁颗粒", text)
        self.assertIn("宝宝去火，温和安全，甘甜又好喝", text)
        # Blank fill-in placeholders must not replace gold composition.
        self.assertNotIn("【待替换为审核原文】", text)
        self.assertNotIn("示例商品A", text)
        self.assertNotIn("asset://", text)

        via_slug = portal_example_paragraphs_for_slug("product-courseware-green-v1")
        self.assertEqual(via_slug, paras)

        html = build_guided_portal_html(
            load_catalog(),
            examples={"product-courseware-green-v1": paras},
        )
        self.assertIn("金样内容组成", html)
        self.assertIn("金银花露（可可康）", html)
        self.assertIn("已签样真实结构示范", html)
        self.assertIn("小儿咽扁颗粒", html)
        self.assertNotIn("【待替换为审核原文】", html)
        # Body lines stay body (not false headings).
        rendered = paragraphs_to_html_blocks(paras)
        self.assertIn("<h4>【封面 · 金银花露】</h4>", rendered)
        self.assertIn("<p>· 主要成分：金银花</p>", rendered)

    def test_commands_match_the_requested_deliverable_and_keep_approval_gate(self) -> None:
        templates = {item["slug"]: item for item in load_catalog()}

        ppt_cmd = build_business_command(templates["product-courseware-component-v1"])
        self.assertIn("内部补缺", ppt_cmd)
        self.assertIn("已签样金样模板", ppt_cmd)
        self.assertIn("需要补漏的页签", ppt_cmd)
        self.assertIn("禁止整课自由组合", ppt_cmd)
        self.assertIn("达不到交付标准", ppt_cmd)
        self.assertIn("不得创建任务", ppt_cmd)
        self.assertNotIn("完整 MP4", ppt_cmd)
        self.assertNotIn("自然语言交付目标", ppt_cmd)
        self.assertNotIn("python3", ppt_cmd)
        self.assertNotIn("route", ppt_cmd.lower())
        # Signed green courseware is a real fixed route after full content/image gates.
        green_cmd = build_business_command(templates["product-courseware-green-v1"])
        self.assertIn("内容初稿", green_cmd)
        self.assertIn("确认后", green_cmd)
        self.assertIn("PPTX", green_cmd)
        self.assertIn("确认先锁定模板", green_cmd)
        self.assertNotIn("不要承诺或生成正式成品", green_cmd)

        disease_cmd = build_business_command(templates["disease-product-scenario-v1"])
        self.assertIn("内容初稿", disease_cmd)
        self.assertIn("PPTX", disease_cmd)

        courseware3_cmd = build_business_command(
            templates["sufuda-mabaloshawei-product-courseware-3-v1"]
        )
        self.assertIn("PPTX", courseware3_cmd)
        self.assertNotIn("完整 MP4", courseware3_cmd)

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

    def test_component_suite_page_types_have_safe_business_labels(self) -> None:
        expected = {
            "courseware_cover": "封面",
            "hook_intro": "培训导语",
            "hook_pain_data": "痛点与数据",
            "summary_matrix": "总结回顾",
        }
        self.assertEqual(
            expected,
            {
                page_type: _component_page_type_label_zh(page_type)
                for page_type in expected
            },
        )
        self.assertEqual("自定义页签", _component_page_type_label_zh("unknown-internal-id"))

    def test_component_capability_compatibility_note_survives_sync_outputs(self) -> None:
        catalog_component = next(
            item
            for item in load_catalog()
            if item["slug"] == "product-courseware-component-v1"
        )
        note = catalog_component.get("capabilities_note_zh") or ""
        self.assertIn("门户不展示", note)
        self.assertIn("达不到交付标准", note)
        settled = ROOT / "production-library/templates/settled/product-courseware-component-v1"
        manifest = json.loads((settled / "manifest.json").read_text(encoding="utf-8"))
        catalog_entry = json.loads(
            (settled / "preview/catalog-entry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(note, manifest["preview"]["capabilities_note_zh"])
        self.assertEqual(note, catalog_entry["capabilities_note_zh"])
        self.assertNotIn("active route", catalog_component["status_note"])
        self.assertIn("内部补漏", catalog_component["status_note"])

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
        self.assertIn("已签样标准课型", html)
        self.assertIn("其他课型", html)
        self.assertIn("先选金样模板", html)
        self.assertIn("自由构件化不在货架展示", html)
        # Gold-first: no separate「金样课型与制作模式」step or A/B entry; content opens with the card.
        self.assertNotIn("金样课型与制作模式", html)
        self.assertNotIn("选择开始方式", html)
        self.assertNotIn("填报示例与模式说明", html)
        self.assertNotIn("A · 先选金样模板（推荐）", html)
        self.assertNotIn("B · 先交内容", html)
        self.assertIn("选金样", html)
        self.assertIn("inline-ex-panel", html)
        self.assertIn("确认选用 · 复制给 WorkBuddy", html)
        self.assertIn("业务提供真图", html)
        self.assertIn("系统自动生成", html)
        self.assertIn("业务不需要自己写生图提示词", html)
        # Free-form component shelf is internal-only: not on the business portal.
        self.assertNotIn("灵活构件商品培训 PPT（兜底）", html)
        self.assertNotIn("已复制灵活构件口令", html)
        self.assertNotIn("未命中 5/18/13/20 页固定课型时使用", html)
        self.assertNotIn("构件化商品培训 PPT（默认主路径）", html)
        # Dead internal JS may still mention the slug; the shelf must not list the card.
        self.assertNotRegex(html, r'"slug": "product-courseware-component-v1"')
        self.assertNotIn('"job_command"', html)
        self.assertNotIn('"route_id"', html)
        self.assertNotIn("business_job.py", html)
        self.assertNotIn("--route", html)

        template_match = re.search(r"const TEMPLATES = (.*);\n", html)
        self.assertIsNotNone(template_match)
        embedded_templates = json.loads(template_match.group(1))
        self.assertFalse(
            any(
                item["slug"] == "product-courseware-component-v1"
                for item in embedded_templates
            )
        )
        self.assertTrue(
            any(item["slug"] == "product-courseware-green-v1" for item in embedded_templates)
        )

    def test_qualified_component_suite_is_hidden_from_business_portal(self) -> None:
        """Component UAT suite remains internal; portal never surfaces free-compose cards."""
        templates = source_catalog_for_portal()
        self.assertTrue(
            any(item["slug"] == "product-courseware-component-v1" for item in templates)
        )
        html = build_guided_portal_html(templates, examples={})
        self.assertNotRegex(html, r'"slug": "product-courseware-component-v1"')
        self.assertNotIn("正式非金样 UAT", html)
        self.assertIn("product-courseware-green-v1", html)
        # Internal page-type labels remain available for WorkBuddy, not the portal.
        self.assertEqual("商品信息总览", _component_page_type_label_zh("product_overview"))
        self.assertEqual("异议应答", _component_page_type_label_zh("objection_handling"))

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
        self.assertIn("MP4 · 本机缺 video_full", blocked)
        # Default PPT (component) is self-serve when local pptx is ready.
        self.assertIn("PPTX · 可生成 · 仍需内容/素材确认", blocked)

    def test_route_truth_overrides_catalog_booleans_and_supports_multiple_outputs(self) -> None:
        template = {
            "slug": "test-multi-route",
            "name_zh": "多交付物测试",
            "category": "商品培训",
            "capabilities": {
                "new_theme_pptx": False,
                "new_theme_mp4": False,
                "business_selfserve": False,
            },
        }
        routes = {
            "test-multi-route": [
                {
                    "active": True,
                    "deliverable": "pptx",
                    "env_require": ["pptx_export"],
                },
                {
                    "active": True,
                    "deliverable": "mp4",
                    "env_require": ["video_full"],
                },
            ]
        }
        badges = deliverable_badges(
            template,
            {"pptx_export": True, "video_full": False},
            routes_by_template=routes,
        )
        self.assertEqual(["ready", "conditional"], [item["kind"] for item in badges])
        self.assertIn("PPTX · 可生成", badges[0]["label"])
        self.assertIn("MP4 · 本机缺 video_full", badges[1]["label"])
        command = build_business_command(template, routes_by_template=routes)
        self.assertIn("可编辑 PPTX / 完整 MP4", command)

    def test_active_pptx_and_inactive_mp4_are_shown_separately(self) -> None:
        template = {
            "slug": "test-split-readiness",
            "name_zh": "拆分状态测试",
            "category": "商品培训",
        }
        routes = {
            "test-split-readiness": [
                {
                    "active": True,
                    "deliverable": "pptx",
                    "env_require": ["pptx_export"],
                },
                {
                    "active": False,
                    "deliverable": "mp4",
                    "env_require": ["video_full"],
                },
            ]
        }
        badges = deliverable_badges(
            template,
            {"pptx_export": True, "video_full": False},
            routes_by_template=routes,
        )
        self.assertEqual(["ready", "building"], [item["kind"] for item in badges])
        self.assertEqual("PPTX · 可生成 · 仍需内容/素材确认", badges[0]["label"])
        self.assertEqual("MP4 · 尚未开放（不可生成）", badges[1]["label"])
        command = build_business_command(template, routes_by_template=routes)
        self.assertIn("生成可编辑 PPTX", command)
        self.assertNotIn("完整 MP4", command)

    def test_catalog_generator_derives_fixed_courseware_state_from_routes(self) -> None:
        by_slug = {entry["slug"]: entry for entry in CATALOG}
        self.assertIn("product-courseware-component-v1", by_slug)
        self.assertEqual(
            "default-general",
            shelf_group_for_template(by_slug["product-courseware-component-v1"]),
        )
        component = derive_catalog_entry(
            by_slug["product-courseware-component-v1"],
            {
                "product-courseware-component-v1": [
                    {"active": True, "deliverable": "pptx"}
                ]
            },
        )
        self.assertEqual(
            "内部补缺页签 · PPTX 可生成", component["status_label"]
        )
        self.assertIn("不作为业务货架课型", component["one_liner"])
        self.assertIn("内部补漏", component["status_note"])
        for fixed_slug in (
            "product-courseware-green-v1",
            "disease-product-scenario-v1",
            "sufuda-mabaloshawei-product-courseware-3-v1",
            "kangaisen-lycopene-health-edu-v1",
        ):
            self.assertEqual(
                "signed-standard",
                shelf_group_for_template(by_slug[fixed_slug]),
            )

        slug = "sufuda-mabaloshawei-product-courseware-3-v1"
        inactive = derive_catalog_entry(
            by_slug[slug],
            {
                slug: [
                    {
                        "active": False,
                        "deliverable": "pptx_and_mp4",
                    }
                ]
            },
        )
        self.assertEqual("signed-standard", inactive["shelf_group"])
        self.assertEqual(
            "尚未开放 · 当前不可生成 · 金样可查看",
            inactive["status_label"],
        )
        self.assertFalse(inactive["capabilities"]["new_theme_pptx"])
        self.assertFalse(inactive["capabilities"]["new_theme_mp4"])
        self.assertFalse(inactive["capabilities"]["business_selfserve"])

        active = derive_catalog_entry(
            by_slug[slug],
            {
                slug: [
                    {"active": True, "deliverable": "pptx"},
                    {"active": True, "deliverable": "mp4"},
                ]
            },
        )
        self.assertTrue(active["capabilities"]["new_theme_pptx"])
        self.assertTrue(active["capabilities"]["new_theme_mp4"])
        self.assertTrue(active["capabilities"]["business_selfserve"])

    def test_ingredient_health_courseware_follows_route_truth(self) -> None:
        slug = "kangaisen-lycopene-health-edu-v1"
        source = next(entry for entry in CATALOG if entry["slug"] == slug)
        self.assertEqual(
            "template.kangaisen-lycopene-health-edu-v1",
            source["template_id"],
        )
        self.assertEqual(
            "番茄红素成分健康科普 PPT（米白番茄红）",
            source["name_zh"],
        )
        self.assertEqual("成分健康科普", source["category"])
        self.assertIn("20 页", source["one_liner"])
        self.assertIn("不是福尔课件4", source["one_liner"])
        self.assertIn("不是福尔商品培训课件4", source["status_note"])
        self.assertEqual("signed-standard", shelf_group_for_template(source))

        inactive_route = {
            "route_id": "ingredient-health-edu-pptx-v1",
            "template_slug": slug,
            "active": False,
            "deliverable": "pptx",
            "env_require": ["pptx_export"],
        }
        routes = {slug: [inactive_route]}
        inactive = derive_catalog_entry(source, routes)
        self.assertEqual(
            "尚未开放 · 当前不可生成 · 金样可查看",
            inactive["status_label"],
        )
        self.assertFalse(inactive["capabilities"]["new_theme_pptx"])
        self.assertFalse(inactive["capabilities"]["business_selfserve"])
        self.assertEqual(
            "PPTX · 尚未开放（不可生成）",
            deliverable_badges(
                source,
                {"pptx_export": True},
                routes_by_template=routes,
            )[0]["label"],
        )
        inactive_command = build_business_command(source, routes_by_template=routes)
        self.assertIn("尚未开放", inactive_command)
        self.assertIn("成分或健康主题", inactive_command)
        self.assertNotIn("生成可编辑 PPTX", inactive_command)

        active_route = {**inactive_route, "active": True}
        active_routes = {slug: [active_route]}
        active = derive_catalog_entry(source, active_routes)
        self.assertEqual(
            "已签样标准课型 · PPTX 可生成",
            active["status_label"],
        )
        self.assertTrue(active["capabilities"]["new_theme_pptx"])
        self.assertTrue(active["capabilities"]["business_selfserve"])
        self.assertIn(
            "PPTX · 可生成",
            deliverable_badges(
                source,
                {"pptx_export": True},
                routes_by_template=active_routes,
            )[0]["label"],
        )
        active_command = build_business_command(source, routes_by_template=active_routes)
        self.assertIn("生成可编辑 PPTX", active_command)
        self.assertIn("成分或健康主题", active_command)


class ProductionModePortalTests(unittest.TestCase):
    EXPECTED_MODE_IDS = {
        "seedance-health-edu-v1",
        "jiugongge-health-edu-v1",
        "jiugongge-health-edu-compliance-v1",
        "digital-human-presenter-scheme-C",
        "domestic-flat-cartoon-health-mg-v1",
    }

    def test_machine_catalog_exposes_gated_production_modes(self) -> None:
        modes = load_business_modes()
        self.assertEqual(
            self.EXPECTED_MODE_IDS,
            {mode["mode_id"] for mode in modes},
        )
        for mode in modes:
            with self.subTest(mode=mode["mode_id"]):
                self.assertTrue(mode["workbuddy_outputs"])
                self.assertTrue(
                    any(item["stage"] == "review" for item in mode["workbuddy_outputs"])
                )
                self.assertTrue(mode["approval_gate"]["required"])
                self.assertTrue(mode["approval_gate"]["confirmation_phrase"])
                self.assertIn("external_render", mode)
                boundary = mode["external_render"]["boundary_zh"]
                if mode["external_render"]["required"]:
                    self.assertIn("账号", boundary)
                else:
                    self.assertTrue(
                        "本机" in boundary or "ReVideo" in boundary or "费用" in boundary
                    )

        prompt_modes = [mode for mode in modes if mode["prompt_only"]]
        self.assertTrue(
            all(
                mode["approval_gate"]["enforcement"] == "hash_bound_release"
                for mode in prompt_modes
            )
        )
        digital_human = next(
            mode
            for mode in modes
            if mode["mode_id"] == "digital-human-presenter-scheme-C"
        )
        self.assertFalse(digital_human["workbuddy_direct_generation"])
        self.assertEqual(
            "human_process_only",
            digital_human["approval_gate"]["enforcement"],
        )
        self.assertEqual("conditional", digital_human["badges"][0]["kind"])
        self.assertIn("复核包模板", digital_human["badges"][0]["label"])
        self.assertIn(".venv-rembg", digital_human["production_requirements"])
        self.assertIn("ffmpeg", digital_human["production_requirements"])
        mg = next(
            mode
            for mode in modes
            if mode["mode_id"] == "domestic-flat-cartoon-health-mg-v1"
        )
        self.assertFalse(mg["prompt_only"])
        self.assertFalse(mg["external_render"]["required"])
        self.assertIn("mp4", mg["local_artifact_types"])
        self.assertGreaterEqual(len(mg.get("portal_key_frames") or []), 5)
        self.assertTrue((ROOT / mg["portal_video_example"]["source"]).is_file())
        self.assertTrue((ROOT / mg["portal_cover"]["source"]).is_file())

    def test_prompt_only_modes_never_claim_a_local_video_delivery(self) -> None:
        modes = load_business_modes()
        prompt_only = [mode for mode in modes if mode["prompt_only"]]
        self.assertEqual(3, len(prompt_only))
        for mode in prompt_only:
            with self.subTest(mode=mode["mode_id"]):
                self.assertFalse(
                    {"mp4", "video_file", "image_file", "rendered_media"}.intersection(
                        mode["local_artifact_types"]
                    )
                )
                for badge in mode["badges"]:
                    if "成片" in badge["label"]:
                        self.assertEqual("external", badge["kind"])
                self.assertIn("本机成片", mode["selection_command"])

        original = next(
            mode for mode in modes if mode["mode_id"] == "jiugongge-health-edu-v1"
        )
        three_view_phrases = [
            item["label"]
            for item in original["workbuddy_outputs"]
            if "三视图" in item["label"]
        ]
        self.assertTrue(three_view_phrases)
        self.assertTrue(all("提示词" in phrase for phrase in three_view_phrases))

    def test_mode_copy_commands_enforce_review_before_release(self) -> None:
        modes = {mode["mode_id"]: mode for mode in load_business_modes()}
        for mode in modes.values():
            with self.subTest(mode=mode["mode_id"]):
                command = mode["selection_command"]
                self.assertIn("请先", command)
                self.assertIn("确认", command)
                self.assertIn("前", command)
                if mode["external_render"]["required"]:
                    self.assertIn("账号", command)
                    self.assertIn("费用", command)
                else:
                    self.assertTrue("费用" in command or "确认" in command)

        digital_human = modes["digital-human-presenter-scheme-C"]["selection_command"]
        self.assertIn("最终脚本通过", digital_human)
        self.assertIn("关键页清单通过", digital_human)
        self.assertIn("不得调用 HeyGen", digital_human)
        self.assertIn("可以生成", digital_human)
        self.assertIn("不是 hash 校验器", modes["digital-human-presenter-scheme-C"]["approval_gate"]["before_approval_zh"])
        seedance = modes["seedance-health-edu-v1"]
        self.assertTrue(seedance["input_expansion_required"])
        self.assertIn("meta-prompt", seedance["selection_command"])
        self.assertIn("逐项列为待补", seedance["selection_command"])
        self.assertIn("不得生成正式提示词包", seedance["selection_command"])
        mg_cmd = modes["domestic-flat-cartoon-health-mg-v1"]["selection_command"]
        self.assertIn("scene_recipe", mg_cmd)
        self.assertIn("不得登记 settled", mg_cmd)
        for mode_id in (
            "seedance-health-edu-v1",
            "digital-human-presenter-scheme-C",
            "domestic-flat-cartoon-health-mg-v1",
        ):
            example = modes[mode_id]["portal_video_example"]
            self.assertTrue((ROOT / example["source"]).is_file())
            self.assertEqual(Path(example["filename"]).name, example["filename"])

    def test_modes_use_a_separate_shelf_without_changing_template_inventory(self) -> None:
        templates = source_catalog_for_portal()
        html = build_guided_portal_html(templates, examples={})
        self.assertIn("动画与数字人制作模式", html)
        self.assertIn("const PRODUCTION_MODES = ", html)
        self.assertIn('t.portal_item_kind === "production_mode"', html)
        self.assertIn("mode-cover", html)
        self.assertLess(
            html.index('"title": "已签样标准课型"'),
            html.index('"title": "动画与数字人制作模式"'),
        )
        self.assertLess(
            html.index('"title": "动画与数字人制作模式"'),
            html.index('"title": "其他课型"'),
        )
        self.assertIn("已复制制作模式口令", html)
        self.assertIn("模式说明已复制到剪贴板", html)
        self.assertIn("PORTAL_ITEMS.find", html)
        self.assertIn('id="case-video" controls playsinline', html)
        self.assertIn("selectionClusterHome.appendChild(selectionCluster)", html)
        self.assertIn("selectedGroup.appendChild(selectionCluster)", html)
        self.assertNotIn("selectedGroup.appendChild(pane)", html)
        self.assertIn('class="keys" id="sel-keys"', html)
        self.assertLess(html.index('id="selection-cluster"'), html.index('id="cmdbox"'))
        self.assertLess(html.index('id="cmdbox"'), html.index('id="preview-pane"'))
        self.assertLess(html.index('id="preview-pane"'), html.index('id="sel-keys"'))
        self.assertIn("复制提示词示例", html)
        self.assertIn("提示词示例已复制到剪贴板", html)

        template_match = re.search(r"const TEMPLATES = (.*);\n", html)
        mode_match = re.search(r"const PRODUCTION_MODES = (.*);\n", html)
        self.assertIsNotNone(template_match)
        self.assertIsNotNone(mode_match)
        embedded_templates = json.loads(template_match.group(1))
        embedded_modes = json.loads(mode_match.group(1))
        # Component free-compose is cataloged but filtered out of the business portal.
        visible_templates = [
            item
            for item in templates
            if item["slug"] != "product-courseware-component-v1"
        ]
        self.assertEqual(len(visible_templates), len(embedded_templates))
        self.assertEqual(8, len(embedded_templates))
        self.assertFalse(
            any(
                item["slug"] == "product-courseware-component-v1"
                for item in embedded_templates
            )
        )
        self.assertEqual(5, len(embedded_modes))
        self.assertFalse(
            self.EXPECTED_MODE_IDS.intersection(
                item["slug"] for item in embedded_templates
            )
        )
        self.assertTrue(
            all(item["shelf_group"] == "production-modes" for item in embedded_modes)
        )
        digital_human = next(
            item
            for item in embedded_modes
            if item["slug"] == "digital-human-presenter-scheme-C"
        )
        self.assertFalse(digital_human["self_serve"])
        self.assertEqual("conditional", digital_human["portal_status_kind"])
        self.assertEqual("真人数字人讲解模式", digital_human["name_zh"])
        self.assertEqual(
            "digital-human-presenter-example.mp4",
            digital_human["portal_video_example"]["filename"],
        )
        seedance = next(
            item for item in embedded_modes if item["slug"] == "seedance-health-edu-v1"
        )
        self.assertEqual(
            "seedance-meta-prompt-example.mp4",
            seedance["portal_video_example"]["filename"],
        )
        self.assertIn("冷调暴雨 vs 暖调台灯", seedance["generated_prompt_example"])
        self.assertIn("52-60s | [温暖收尾与转发]", seedance["generated_prompt_example"])
        self.assertIn("function mediaCaseVideo(t)", html)
        self.assertIn("function mediaModeAsset(filename)", html)
        mg = next(
            item
            for item in embedded_modes
            if item["slug"] == "domestic-flat-cartoon-health-mg-v1"
        )
        self.assertEqual("国内扁平卡通健康 MG 动画", mg["name_zh"])
        self.assertEqual(
            "domestic-flat-cartoon-mg-example.mp4",
            mg["portal_video_example"]["filename"],
        )
        self.assertTrue(mg["portal_cover_filename"])
        self.assertGreaterEqual(len(mg["portal_key_frames"]), 5)
        self.assertIn("政策城市分层", " ".join(mg["key_frame_labels_zh"]))
        health = next(
            item
            for item in embedded_templates
            if item["slug"] == "health-video-reference-tech-v1"
        )
        product = next(
            item
            for item in embedded_templates
            if item["slug"] == "product-video-faithful-v1"
        )
        self.assertEqual("gold.mp4", health["portal_video_example"]["filename"])
        self.assertEqual("gold.mp4", product["portal_video_example"]["filename"])
        self.assertIn("风热证", health["portal_video_example"]["label"])
        self.assertIn("辅酶", product["portal_video_example"]["label"])
        self.assertTrue(
            (ROOT / health["portal_video_example"]["source"]).is_file()
        )
        self.assertTrue(
            (ROOT / product["portal_video_example"]["source"]).is_file()
        )
        # Labels live on the generated shelf catalog after preview sync.
        catalog_by_slug = {item["slug"]: item for item in load_catalog()}
        self.assertEqual(
            ["开场", "典型症状", "病因机理", "治疗思路", "用药建议", "总结"],
            catalog_by_slug["health-video-reference-tech-v1"]["key_frame_labels_zh"],
        )
        self.assertEqual(
            ["开场", "品牌/品类", "核心功效", "产品特点", "适宜人群", "联合用药"],
            catalog_by_slug["product-video-faithful-v1"]["key_frame_labels_zh"],
        )
        self.assertNotIn("production-library/validation/", mode_match.group(1))
        for item in embedded_modes:
            if item["prompt_only"]:
                self.assertFalse(
                    any(
                        "MP4 · 可生成" in badge["label"]
                        for badge in item["deliverable_badges"]
                    )
                )


if __name__ == "__main__":
    unittest.main()
