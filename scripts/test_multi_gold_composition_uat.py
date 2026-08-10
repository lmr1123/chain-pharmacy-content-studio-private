#!/usr/bin/env python3
"""Data-contract tests for the three multi-gold component PPT UAT fixtures."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_courseware as courseware  # noqa: E402
import product_pptx_asset_plan as asset_plan  # noqa: E402


FIXTURE_ROOT = (
    ROOT
    / "production-library"
    / "validation"
    / "courseware"
    / "multi-gold-composition-uat-v1"
)
REGISTRY_PATH = (
    ROOT / "production-library/page-types/product-training/registry.json"
)
MATRIX_PATH = FIXTURE_ROOT / "source-capability-matrix.json"
AUTHORIZATION_PATH = FIXTURE_ROOT / "packshot-authorization.json"
CASE_DIRS = (
    FIXTURE_ROOT / "case-a-three-gold-new-tab",
    FIXTURE_ROOT / "case-b-evidence-overview",
    FIXTURE_ROOT / "case-c-handoff-path",
)

FORBIDDEN_SCRIPT_TOKENS = (
    "功效",
    "用法",
    "用量",
    "剂量",
    "联合",
    "联推",
    "搭配",
    "治疗",
    "预防",
    "缓解",
    "疾病",
    "病名",
    "患者",
    "金银花露",
    "穿心莲",
    "速福达",
    "玛巴洛沙韦",
    "番茄红素",
    "辅酶Q10",
    "福尔",
    "麦金利",
)
PENDING_TOKENS = ("待确认", "待业务", "待补充", "待审核", "TODO", "TBD")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MultiGoldCompositionUATTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(REGISTRY_PATH)
        cls.registered = {
            item["id"]: item for item in cls.registry.get("page_types") or []
        }
        cls.matrix = load_json(MATRIX_PATH)
        cls.sources = cls.matrix["sources"]
        cls.authorization = load_json(AUTHORIZATION_PATH)
        cls.cases = [
            (
                load_json(case_dir / "case-contract.json"),
                load_json(case_dir / "script.structured.json"),
                load_json(case_dir / "asset-bindings.json"),
            )
            for case_dir in CASE_DIRS
        ]

    def test_source_matrix_points_to_real_manifests_artifacts_and_contracts(self) -> None:
        self.assertEqual(
            self.matrix["visual_target"]["style_pack_id"],
            "style-pack.reference-product-blue-v1",
        )
        self.assertTrue((ROOT / self.matrix["visual_target"]["tokens_path"]).is_file())
        self.assertTrue(
            (ROOT / self.matrix["visual_target"]["lineage_artifact"]).is_file()
        )

        for source_ref, source in self.sources.items():
            manifest_path = source.get("manifest_path")
            if manifest_path:
                manifest = load_json(ROOT / manifest_path)
                self.assertEqual(
                    manifest["template_id"],
                    source["template_id"],
                    source_ref,
                )
            artifact_path = source.get("canonical_artifact")
            if artifact_path:
                self.assertTrue((ROOT / artifact_path).is_file(), source_ref)
            contract_path = source.get("contract_path")
            if contract_path:
                contract = load_json(ROOT / contract_path)
                self.assertEqual(
                    contract["page_type"], source["target_page_type"], source_ref
                )

    def test_packshot_is_a_real_uat_only_authorized_file(self) -> None:
        packshot = ROOT / self.authorization["asset_path"]
        self.assertTrue(packshot.is_file())
        self.assertEqual(sha256_file(packshot), self.authorization["sha256"])
        self.assertEqual(self.authorization["scope"], "uat-only")
        self.assertIn("正式业务交付", self.authorization["prohibited_use"])

    def test_case_source_combinations_and_new_tab_contract(self) -> None:
        source_sets: dict[str, frozenset[str]] = {}
        expected_counts = {"A": 7, "B": 6, "C": 5}
        expected_source_counts = {"A": 3, "B": 2, "C": 2}
        all_sequences: set[tuple[str, ...]] = set()
        all_page_sets: set[frozenset[str]] = set()
        new_tabs = []

        for contract, _script, _bindings in self.cases:
            case_id = contract["case_id"]
            sequence = contract["expected"]["page_sequence"]
            self.assertEqual(contract["expected"]["page_count"], expected_counts[case_id])
            self.assertEqual(len(sequence), expected_counts[case_id])
            self.assertEqual(len(contract["source_tabs"]), expected_source_counts[case_id])
            self.assertEqual(contract["style_pack_id"], "style-pack.reference-product-blue-v1")
            self.assertEqual(contract["route_id"], "product-pptx-component-v1")
            self.assertEqual(contract["scope"], "uat")
            all_sequences.add(tuple(sequence))
            all_page_sets.add(frozenset(sequence))

            refs = frozenset(tab["source_ref"] for tab in contract["source_tabs"])
            source_sets[case_id] = refs
            for tab in contract["source_tabs"]:
                source = self.sources[tab["source_ref"]]
                self.assertEqual(tab["target_page_type"], source["target_page_type"])
                self.assertEqual(
                    sequence[tab["page"] - 1], tab["target_page_type"], tab["tab_id"]
                )
            for tab in contract["new_tabs"]:
                new_tabs.append(tab)
                self.assertFalse(tab["requires_new_renderer"])
                self.assertEqual(tab["source_ref"], "new.objection_handling")
                self.assertEqual(
                    sequence[tab["page"] - 1], tab["target_page_type"], tab["tab_id"]
                )

        self.assertEqual(
            source_sets["A"],
            {
                "green.product_overview",
                "disease.consultation_framework",
                "sufuda.evidence_ladder",
            },
        )
        self.assertNotEqual(source_sets["B"], source_sets["C"])
        self.assertEqual(len(all_sequences), 3)
        self.assertEqual(len(all_page_sets), 3)
        self.assertTrue(new_tabs)

    def test_scripts_expand_to_exact_distinct_page_sequences(self) -> None:
        for contract, script, _bindings in self.cases:
            expected = contract["expected"]
            self.assertEqual(script["meta"]["page_sequence"], expected["page_sequence"])
            plan = courseware.expand_scene_plan(script, self.registry)
            observed = [page["page_type"] for page in plan["pages"]]
            self.assertEqual(observed, expected["page_sequence"], contract["case_id"])
            self.assertEqual(plan["page_count"], expected["page_count"])
            model = courseware.scene_plan_to_content_model(
                plan, script, "style-pack.reference-product-blue-v1"
            )
            self.assertEqual(
                model["style_pack_id"], "style-pack.reference-product-blue-v1"
            )
            self.assertEqual(
                [scene["page_type"] for scene in model["scenes"]], observed
            )
            for page_type in observed:
                self.assertIn(page_type, self.registered)

    def test_scripts_are_safe_non_medical_uat_copy(self) -> None:
        for contract, script, _bindings in self.cases:
            blob = json.dumps(script, ensure_ascii=False)
            for token in FORBIDDEN_SCRIPT_TOKENS + PENDING_TOKENS:
                self.assertNotIn(token, blob, f"{contract['case_id']}: {token}")
            self.assertEqual(script.get("gaps"), [])
            self.assertTrue(script["meta"]["brand_boast_disabled"])
            self.assertEqual(script["meta"]["content_lock"], "uat-safe-non-medical-v1")
            self.assertNotIn("combination", script)
            self.assertNotIn("benefits", script)

    def test_each_script_declares_three_safe_cover_points_and_uat_stage(self) -> None:
        for contract, script, _bindings in self.cases:
            meta = script["meta"]
            points = meta.get("cover_points")
            self.assertEqual(meta.get("cover_stage_tag"), "内部 UAT")
            self.assertIsInstance(points, list)
            self.assertEqual(len(points), 3, contract["case_id"])
            self.assertTrue(all(isinstance(point, str) and point.strip() for point in points))
            blob = json.dumps(script, ensure_ascii=False)
            for point in points:
                self.assertIn(point, blob)

    def test_asset_contracts_are_complete_and_visual_gate_is_honestly_empty(self) -> None:
        for contract, script, bindings in self.cases:
            asset_contract = contract["assets"]
            self.assertEqual(
                asset_contract["required_slots"]["business_authorized"],
                ["meta.product_packshot"],
            )
            self.assertEqual(
                asset_contract["required_slots"]["system_generated_or_approved_library"],
                [],
            )
            self.assertEqual(bindings["bindings"], {})
            self.assertEqual(
                asset_contract["authorization_reference"],
                self.authorization["authorization_reference"],
            )
            self.assertTrue((ROOT / asset_contract["product_image_path"]).is_file())
            self.assertTrue((ROOT / asset_contract["authorization_path"]).is_file())
            self.assertTrue((ROOT / asset_contract["asset_bindings_path"]).is_file())

            plan = asset_plan.build_product_pptx_asset_plan(
                script, template_slug="product-courseware-component-v1"
            )
            [packshot] = [
                item
                for item in plan["business_provides"]
                if item.get("slot_contract") == "cover.product_packshot"
            ]
            self.assertEqual(packshot["status"], "ready", contract["case_id"])
            self.assertEqual(plan["system_generates"], [], contract["case_id"])


if __name__ == "__main__":
    unittest.main()
