#!/usr/bin/env python3
"""P2.9 clean-clone / production-path readiness harness.

Does not re-clone the repo (that needs network + auth). Instead it asserts the
current tree can support the formal business path the way a clean Private clone
should after bootstrap soft-repair:

1. On-demand package inventory honesty
2. Critical production files for default PPT route
3. Probe + doctor for pptx profile
4. Component route draft → content/visual/product-image approvals → render E2E
   (when pptx_export true)
5. Honest skip when pptx_export false (no fake delivery)
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import business_doctor as doctor  # noqa: E402
import business_job as bj  # noqa: E402
import probe_production_env as probe  # noqa: E402


ON_DEMAND = ROOT / "production-library" / "on-demand-packages.json"

# Files that must exist in Private production for default PPT (ship_in_git=true).
CRITICAL_PPTX_PATHS = [
    "production-library/business-routes.json",
    "production-library/runtime-profiles.json",
    "production-library/engines/courseware-pptx-v1/export.mjs",
    "production-library/engines/courseware-pptx-v1/components/index.mjs",
    "production-library/engines/product-courseware-green-v1/build-product-courseware.mjs",
    "production-library/engines/disease-product-scenario-pptx-v1/export.mjs",
    "production-library/engines/courseware3-pptx-v1/export.mjs",
    "production-library/page-types/product-training/registry.json",
    "production-library/page-types/product-training/recipes/scene-type-map.json",
    "production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json",
    "production-library/templates/settled/product-courseware-component-v1/manifest.json",
    "scripts/generate_courseware.py",
    "scripts/business_job.py",
    "scripts/business_doctor.py",
    "scripts/probe_production_env.py",
    "scripts/replicate_courseware_theme.py",
]


class OnDemandPackagesTests(unittest.TestCase):
    def test_manifest_schema_and_core_packages(self) -> None:
        self.assertTrue(ON_DEMAND.is_file(), "missing on-demand-packages.json")
        doc = json.loads(ON_DEMAND.read_text(encoding="utf-8"))
        self.assertEqual(doc.get("schema"), "on-demand-packages-v1")
        ids = {p["id"] for p in doc.get("packages") or []}
        self.assertIn("artifact-tool-node-modules", ids)
        self.assertIn("courseware-pptx-component-engine", ids)
        self.assertIn("video-revideo-runtime-kit", ids)
        self.assertFalse(doc["policy"]["no_silent_network_install"] is False)

    def test_ship_in_git_packages_exist(self) -> None:
        doc = json.loads(ON_DEMAND.read_text(encoding="utf-8"))
        for pkg in doc.get("packages") or []:
            if pkg.get("ship_in_git") is not True:
                continue
            for rel in pkg.get("paths") or []:
                path = ROOT / rel
                self.assertTrue(
                    path.exists(),
                    msg=f"ship_in_git package {pkg['id']} missing {rel}",
                )


class CriticalPathInventoryTests(unittest.TestCase):
    def test_default_pptx_critical_files(self) -> None:
        missing = [p for p in CRITICAL_PPTX_PATHS if not (ROOT / p).exists()]
        self.assertEqual(missing, [], msg=f"clean-clone blockers: {missing}")

    def test_default_route_and_fixed_standard_routes(self) -> None:
        routes = bj.load_routes_doc()
        self.assertEqual(routes.get("default_pptx_route"), "product-pptx-component-v1")
        active = {r["route_id"] for r in bj.load_routes(active_only=True)}
        for route_id in (
            "product-pptx-component-v1",
            "product-pptx-green-v1",
            "product-pptx-disease-scenario-v1",
            "courseware3-pptx-v1",
        ):
            self.assertIn(route_id, active)
        component = bj.get_route("product-pptx-component-v1")
        self.assertEqual(component.get("adapter"), "product_pptx_component")
        green = bj.get_route("product-pptx-green-v1")
        self.assertTrue(green.get("active"))
        self.assertFalse(green.get("retired"))
        self.assertFalse(bj.get_route("courseware3-mp4-v1").get("active"))


class ProbeDoctorHonestyTests(unittest.TestCase):
    def test_probe_reports_component_engine_path(self) -> None:
        report = probe.probe()
        paths = report.get("paths") or {}
        # When engine file exists, probe must surface it
        engine = ROOT / "production-library/engines/courseware-pptx-v1/export.mjs"
        if engine.is_file():
            self.assertEqual(paths.get("component_pptx_engine"), str(engine))

    def test_doctor_pptx_profile(self) -> None:
        code = doctor.main(["--profile", "pptx", "--json"])
        # 0 = ready, 2 = missing env (honest). Either is acceptable; crash is not.
        self.assertIn(code, (0, 2))


class ComponentRouteE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="p29-clone-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.jobs = self.tmp / "jobs"
        self.delivery = self.tmp / "delivery"
        self.jobs.mkdir()
        self.delivery.mkdir()
        self._jobs_root = bj.jobs_root
        self._delivery_root = bj.delivery_root
        bj.jobs_root = lambda: self.jobs  # type: ignore[assignment]
        bj.delivery_root = lambda: self.delivery  # type: ignore[assignment]
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        bj.jobs_root = self._jobs_root  # type: ignore[assignment]
        bj.delivery_root = self._delivery_root  # type: ignore[assignment]

    def _new_and_approve_complete_job(self, job_id: str, theme: str) -> None:
        image = self.tmp / f"{job_id}.png"
        image.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0c"
            b"IDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        script = {
            "schema": "product-training-script/v1",
            "meta": {
                "display_name": theme,
                "organization": "清洁克隆核验",
                "page_sequence": [
                    "courseware_cover",
                    "hook_intro",
                    "benefit_cards",
                    "feature_cards",
                    "audience_list",
                    "combination_guidance",
                    "summary_matrix",
                    "precautions",
                ],
            },
            "hook": {"title": "培训导语", "paragraphs": ["以下内容已完成审核。"]},
            "benefits": {"title": "核心知识", "items": [{"title": "知识点", "body": "已审核说明。"}]},
            "features": {"title": "产品特点", "items": [{"title": "特点", "body": "已审核特点。"}]},
            "audience": {"title": "适宜人群", "items": ["已审核人群"]},
            "combination": {"title": "咨询场景", "rows": [{"problem": "场景一", "partner": "搭档一", "talk_track": "已审核话术。"}]},
            "summary": {"title": "总结", "rows": [{"label": "要点", "value": "已审核。"}]},
            "precautions": {"title": "注意事项", "items": ["核对本品正式标签。"]},
        }
        script_path = self.tmp / f"{job_id}.json"
        script_path.write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(
            bj.main(
                [
                    "new",
                    "--route",
                    "product-pptx-component-v1",
                    "--theme",
                    theme,
                    "--script-json",
                    str(script_path),
                    "--job-id",
                    job_id,
                    "--auto-draft",
                    "--json",
                ]
            ),
            0,
        )
        job = bj.load_job(job_id)
        plan = json.loads(Path(job["draft"]["asset_plan_json"]).read_text(encoding="utf-8"))
        bindings = {item["script_path"]: str(image) for item in plan["system_generates"]}
        bindings_path = self.tmp / f"{job_id}-bindings.json"
        bindings_path.write_text(json.dumps(bindings, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(
            bj.main(
                [
                    "approve",
                    "--job",
                    job_id,
                    "--gate",
                    "content",
                    "--by",
                    "测试员",
                    "--json",
                ]
            ),
            0,
        )
        self.assertEqual(
            bj.main(
                [
                    "approve",
                    "--job",
                    job_id,
                    "--gate",
                    "visual",
                    "--by",
                    "测试员",
                    "--asset-bindings",
                    str(bindings_path),
                    "--json",
                ]
            ),
            0,
        )
        self.assertEqual(
            bj.main(
                [
                    "approve",
                    "--job",
                    job_id,
                    "--gate",
                    "product_image",
                    "--by",
                    "测试员",
                    "--product-image",
                    str(image),
                    "--authorization-reference",
                    "TEST-AUTH-CLEAN-CLONE",
                    "--json",
                ]
            ),
            0,
        )

    def test_draft_blocks_gold_residue(self) -> None:
        # Inject forbidden token via notes that would only appear if builder copied gold — 
        # build script uses theme only; force-check assert helper.
        with self.assertRaises(SystemExit):
            script = {
                "meta": {"display_name": "清白商品"},
                "benefits": {
                    "items": [{"title": "知识点", "body": "含福尔麦金利金样残留"}]
                },
            }
            bj._assert_no_component_gold_residue(script, "清白商品")

    def test_component_draft_approve_env_block_no_delivery(self) -> None:
        self._new_and_approve_complete_job("p29-comp-1", "清洁克隆样例片")
        job = bj.load_job("p29-comp-1")
        self.assertEqual(job["state"], "visual_approved")
        self.assertEqual(job["draft"]["kind"], "product_pptx_component")
        self.assertTrue(Path(job["draft"]["script"]).is_file())
        self.assertTrue(Path(job["draft"]["content_model"]).is_file())
        self.assertGreaterEqual(int(job["draft"].get("page_count") or 0), 8)
        with mock.patch.object(bj, "probe_capabilities", return_value={"pptx_export": False}):
            code = bj.main(["render", "--job", "p29-comp-1", "--json"])
        self.assertEqual(code, 2)
        job = bj.load_job("p29-comp-1")
        self.assertEqual(job["state"], "env_blocked")
        self.assertEqual(list(self.delivery.iterdir()), [])

    def test_component_render_publishes_when_export_ok(self) -> None:
        caps = probe.probe().get("capabilities") or {}
        if not caps.get("pptx_export"):
            self.skipTest("pptx_export false on this machine — honest skip")

        self._new_and_approve_complete_job("p29-comp-e2e", "E2E构件样例")
        code = bj.main(["render", "--job", "p29-comp-e2e", "--json"])
        self.assertEqual(code, 0, msg="component render should deliver when pptx_export true")
        job = bj.load_job("p29-comp-e2e")
        self.assertEqual(job["state"], "delivered")
        delivery = Path(job["delivery"]["path"])
        self.assertTrue((delivery / "终稿.pptx").is_file())
        self.assertTrue((delivery / "run-manifest.json").is_file())
        # whitelist only
        names = {p.name for p in delivery.iterdir()}
        self.assertNotIn("generate.log", names)
        self.assertIn("终稿.pptx", names)


class GoldRegressionGeneratorTests(unittest.TestCase):
    def test_maikenli_script_plans_gold_page_types(self) -> None:
        script = (
            ROOT
            / "production-library/validation/courseware/fuler-maikenli-lycopene-v1/script.structured.json"
        )
        if not script.is_file():
            self.skipTest("gold script missing")
        out = Path(tempfile.mkdtemp(prefix="p28-gold-"))
        self.addCleanup(shutil.rmtree, out, True)
        # This historical fixture predates the explicit non-empty hook card slots.
        # Normalize only the temporary test copy with values already present in
        # its source paragraph text; do not mutate the validation gold source.
        script_data = json.loads(script.read_text(encoding="utf-8"))
        hook = script_data["hook"]
        hook.setdefault(
            "symptoms",
            ["尿频", "尿急", "会阴坠胀", "排尿灼痛"],
        )
        hook.setdefault(
            "stats",
            [
                {"number": "32.9%", "unit": "", "note": "32.9%"},
                {"number": "40%", "unit": "", "note": "40%"},
            ],
        )
        normalized_script = out / "script.structured.json"
        normalized_script.write_text(
            json.dumps(script_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        report = bj._run_courseware_generator(
            script_path=normalized_script,
            out_dir=out,
            skip_export=True,
            skip_qa=True,
            skip_provenance=True,
            name_suffix="金样回归",
        )
        self.assertGreaterEqual(int(report.get("page_count") or 0), 10)
        types = set(report.get("page_types") or [])
        for needed in (
            "courseware_cover",
            "benefit_cards",
            "audience_list",
            "combination_guidance",
            "precautions",
        ):
            self.assertIn(needed, types)


if __name__ == "__main__":
    unittest.main()
