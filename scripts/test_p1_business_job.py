#!/usr/bin/env python3
"""P1 regression: business-routes + business_job state machine gates."""

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

import business_job as bj  # noqa: E402
from business_guided_portal import build_business_command, build_job_command  # noqa: E402


class BusinessRoutesTests(unittest.TestCase):
    def test_business_status_labels_are_unambiguous(self) -> None:
        route = bj.get_route("product-pptx-component-v1")
        self.assertEqual(bj.business_label("content_approved", {"approvals": {}}, route), "等待视觉确认")
        self.assertEqual(bj.business_label("visual_approved", {}, route), "等待业务资料")
        ready_job = {
            "approvals": {
                "visual": {"approved": True},
                "product_image": {"approved": True},
            }
        }
        self.assertEqual(bj.business_label("visual_approved", ready_job, route), "可开始生成")
        self.assertEqual(bj.business_label("env_blocked", {}, route), "环境不足")
        self.assertEqual(bj.business_label("qa_failed", {}, route), "质检失败")
        self.assertEqual(bj.business_label("delivered", {}, route), "已交付")

    def test_routes_file_has_core_active_routes(self) -> None:
        doc = bj.load_routes_doc()
        self.assertEqual(doc.get("schema"), "business-routes-v1")
        self.assertEqual(doc.get("default_pptx_route"), "product-pptx-component-v1")
        active = [r for r in doc["routes"] if r.get("active")]
        ids = {r["route_id"] for r in active}
        self.assertIn("product-pptx-component-v1", ids)
        self.assertIn("product-pptx-green-v1", ids)
        self.assertIn("product-pptx-disease-scenario-v1", ids)
        self.assertIn("courseware3-pptx-v1", ids)
        self.assertIn("product-mp4-full-v1", ids)
        # Health remains inactive until theme-package self-serve is proven.
        health = next(r for r in doc["routes"] if r["route_id"] == "health-mp4-full-v1")
        self.assertFalse(health["active"])
        green = next(r for r in doc["routes"] if r["route_id"] == "product-pptx-green-v1")
        self.assertTrue(green["active"])
        self.assertFalse(green.get("retired"))

    def test_active_routes_point_at_catalog_templates(self) -> None:
        catalog = bj.catalog_by_slug()
        for route in bj.load_routes(active_only=True):
            slug = route.get("template_slug")
            self.assertIn(slug, catalog, msg=route["route_id"])
            caps = catalog[slug].get("capabilities") or {}
            if route["deliverable"] == "pptx":
                self.assertTrue(caps.get("new_theme_pptx") or caps.get("gold_viewable"))
            if route["deliverable"] == "mp4":
                self.assertTrue(caps.get("new_theme_mp4") or caps.get("gold_viewable"))

    def test_portal_prompts_hide_job_cli_from_business(self) -> None:
        catalog = bj.catalog_by_slug()
        component = catalog["product-courseware-component-v1"]
        green = catalog["product-courseware-green-v1"]
        video = catalog["product-video-faithful-v1"]
        component_prompt = build_business_command(component)
        self.assertIn("全中文页签大纲", component_prompt)
        self.assertIn("每页能力来源解释", component_prompt)
        self.assertIn("只使用一种主视觉", component_prompt)
        self.assertIn("先不要创建正式任务", component_prompt)
        self.assertIn("不需要填写 JSON", component_prompt)
        self.assertNotIn("确认先锁定模板", component_prompt)
        self.assertNotIn("business_job.py", component_prompt)
        self.assertNotIn("route", component_prompt.lower())
        # Green five-page courseware is a signed fixed route with real gates.
        green_cmd = build_business_command(green)
        self.assertIn("内容初稿", green_cmd)
        self.assertIn("确认后", green_cmd)
        self.assertIn("--gate content", build_job_command(green) or "")
        self.assertIn("--gate product_image", build_job_command(green) or "")
        self.assertIn("--gate visual", build_job_command(green) or "")
        self.assertNotIn("business_job.py", build_business_command(video))
        self.assertIn("--gate content", build_job_command(component) or "")
        self.assertIn("--gate visual", build_job_command(component) or "")
        self.assertIn("--gate product_image", build_job_command(component) or "")
        self.assertIn("product_image", build_job_command(video) or "")

    def test_business_job_recommend_does_not_create_a_job(self) -> None:
        with mock.patch.object(
            bj, "probe_capabilities", return_value={"pptx_export": True}
        ), mock.patch.object(bj, "cmd_new") as create_job:
            code = bj.main(
                [
                    "recommend",
                    "按穿心莲18页疾病商品场景课型做PPT",
                    "--check-env",
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        create_job.assert_not_called()


class BusinessJobScopeIsolationTests(unittest.TestCase):
    def tearDown(self) -> None:
        bj.set_active_scope("production")

    def test_uat_roots_are_separate_from_production_and_official_pickup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="biz-scope-") as temp:
            fake_root = Path(temp)
            with mock.patch.object(bj, "ROOT", fake_root):
                bj.set_active_scope("production")
                production_jobs = bj.jobs_root()
                production_delivery = bj.delivery_root()

                bj.set_active_scope("uat")
                uat_jobs = bj.jobs_root()
                uat_delivery = bj.delivery_root()

            self.assertNotEqual(uat_jobs, production_jobs)
            self.assertNotEqual(uat_delivery, production_delivery)
            self.assertEqual(uat_jobs, fake_root / "outputs/workbuddy-workspaces/uat/jobs")
            self.assertEqual(uat_delivery, fake_root / "outputs/workbuddy-workspaces/uat/delivery")
            self.assertNotIn("05_交付物放这里", str(uat_delivery))


class BusinessJobStateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="biz-job-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.jobs = self.tmp / "jobs"
        self.delivery = self.tmp / "delivery"
        self.jobs.mkdir()
        self.delivery.mkdir()
        self._jobs_root = bj.jobs_root
        self._delivery_root = bj.delivery_root
        bj.jobs_root = lambda: self.jobs  # type: ignore[assignment]
        bj.delivery_root = lambda: self.delivery  # type: ignore[assignment]
        self.addCleanup(self._restore_roots)

    def _restore_roots(self) -> None:
        bj.jobs_root = self._jobs_root  # type: ignore[assignment]
        bj.delivery_root = self._delivery_root  # type: ignore[assignment]

    def test_component_theme_only_draft_has_no_invented_medical_copy(self) -> None:
        script = bj._build_component_script("仅商品名测试", "")
        blob = json.dumps(script, ensure_ascii=False)
        for forbidden in (
            "用药前请仔细阅读说明书",
            "药师指导下使用",
            "过敏者禁用",
            "过敏体质者慎用",
            "关注健康信号",
            "生活质量下降",
        ):
            self.assertNotIn(forbidden, blob)

        self.assertEqual(script["meta"]["page_sequence"], ["courseware_cover"])
        self.assertIn("中文页签大纲待确认", script["gaps"])
        for fixed_section in (
            "hook",
            "benefits",
            "features",
            "audience",
            "combination",
            "summary",
            "precautions",
        ):
            self.assertNotIn(fixed_section, script)

    def test_component_notes_choose_a_minimal_dynamic_outline(self) -> None:
        import generate_courseware as gc

        script = bj._build_component_script(
            "动态组合测试",
            "\n".join(
                (
                    "商品信息总览：核对商品名称与规格",
                    "门店咨询框架：先核对需求",
                    "商品证据阶梯：记录证据来源",
                    "异议应答：资料外问题需升级",
                )
            ),
        )
        expected = [
            "courseware_cover",
            "product_overview",
            "consultation_framework",
            "evidence_ladder",
            "objection_handling",
        ]
        self.assertEqual(script["meta"]["page_sequence"], expected)
        for fixed_section in ("benefits", "features", "audience", "combination", "precautions"):
            self.assertNotIn(fixed_section, script)
        plan = gc.expand_scene_plan(script, gc.load_json(gc.DEFAULT_REGISTRY))
        self.assertEqual([page["page_type"] for page in plan["pages"]], expected)

        generic = bj._build_component_script("动态组合测试", "这是业务已提供的一条中性说明")
        self.assertEqual(
            generic["meta"]["page_sequence"],
            ["courseware_cover", "hook_intro"],
        )
        self.assertEqual(
            generic["hook"]["paragraphs"],
            ["这是业务已提供的一条中性说明（待业务确认）"],
        )

    def test_pending_component_copy_uses_neutral_visual_slots(self) -> None:
        import generate_courseware as gc

        self.assertEqual(
            gc.benefit_chain_assets("核心卖点 1（待确认）", 0),
            ["benefit_source_pending", "arrow", "benefit_result_pending"],
        )
        self.assertEqual(gc.guess_audience_icon("适宜人群 1（待确认）"), "audience_pending")
        self.assertEqual(
            gc.combo_icon_file(
                {"problem": "联合场景（待确认）", "partner": "搭档商品（待确认）"}
            ),
            "__missing__/combination-pending.png",
        )
        script = bj._build_component_script("仅商品名测试", "")
        plan = gc.expand_scene_plan(script, gc.load_json(gc.DEFAULT_REGISTRY))
        self.assertEqual([page["page_type"] for page in plan["pages"]], ["courseware_cover"])
        plan_blob = json.dumps(plan, ensure_ascii=False)
        for forbidden in (
            "tomato",
            "prostate",
            "不代替药物",
            "禁忌人群",
            "随餐服用",
            "就医咨询",
        ):
            self.assertNotIn(forbidden, plan_blob)

    def test_pptx_draft_approve_blocks_render_without_content_gate(self) -> None:
        rc = bj.main(
            [
                "new",
                "--route",
                "product-pptx-component-v1",
                "--theme",
                "测试构件片",
                "--notes",
                "卖点A\n卖点B\n卖点C",
                "--job-id",
                "test-comp-1",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-comp-1")
        self.assertEqual(job["state"], "intake")
        self.assertEqual(job["template_id"], "template.product-courseware-component-v1")
        self.assertEqual(job["style_pack_id"], "style-pack.reference-product-blue-v1")

        rc = bj.main(["draft", "--job", "test-comp-1", "--json"])
        self.assertEqual(rc, 0)
        job = bj.load_job("test-comp-1")
        self.assertEqual(job["state"], "draft_ready")
        self.assertEqual(job["draft"]["kind"], "product_pptx_component")
        self.assertTrue(Path(job["draft"]["content_model"]).is_file())
        self.assertTrue(Path(job["draft"]["asset_plan_json"]).is_file())
        self.assertTrue(Path(job["draft"]["asset_plan_md"]).is_file())
        review = Path(job["draft"]["review_md"]).read_text(encoding="utf-8")
        self.assertIn("中文页签大纲（待确认）", review)
        self.assertIn("P2：产品特点卡", review)
        self.assertNotIn("feature_cards /", review)
        asset_plan = json.loads(
            Path(job["draft"]["asset_plan_json"]).read_text(encoding="utf-8")
        )
        self.assertEqual(asset_plan["schema"], "product-pptx-asset-plan/v1")
        self.assertEqual(asset_plan["business_provides"][0]["asset"], "商品正式包装图")
        self.assertTrue(asset_plan["business_provides"][0]["required"])
        self.assertTrue(asset_plan["system_generates"])
        self.assertTrue(asset_plan["template_reuses"])
        self.assertTrue(asset_plan["policy"]["generate_only_after_content_approval"])
        self.assertTrue(asset_plan["policy"]["first_representative_slot_qa"])
        self.assertTrue(
            all(item["fit"] in {"cover", "contain"} for item in asset_plan["system_generates"])
        )
        self.assertTrue(all(item.get("binding") for item in asset_plan["system_generates"]))
        self.assertTrue(
            any(
                item["status"] == "blocked_pending_content"
                for item in asset_plan["system_generates"]
            )
        )
        self.assertEqual(len(job["draft"]["content_sha256"]), 64)

        with self.assertRaises(SystemExit) as ctx:
            bj.main(["render", "--job", "test-comp-1", "--json"])
        self.assertIn("审批未齐", str(ctx.exception))

        with self.assertRaises(SystemExit) as ctx:
            bj.main(
                [
                    "approve",
                    "--job",
                    "test-comp-1",
                    "--gate",
                    "content",
                    "--by",
                    "测试员",
                    "--json",
                ]
            )
        self.assertIn("内容仍含待补字段", str(ctx.exception))
        job = bj.load_job("test-comp-1")
        self.assertEqual(job["state"], "draft_ready")
        self.assertNotIn("content", job["approvals"])

    def test_component_approval_binds_all_planned_assets(self) -> None:
        image = self.tmp / "asset.png"
        image.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0c"
            b"IDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        script = {
            "schema": "product-training-script/v1",
            "meta": {
                "display_name": "完整素材测试",
                "organization": "测试组织",
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
            "hook": {"title": "培训导语", "paragraphs": ["以下内容已完成业务审核。"]},
            "benefits": {"title": "核心知识", "items": [{"title": "知识点", "body": "已审核说明。"}]},
            "features": {"title": "产品特点", "items": [{"title": "使用体验", "body": "已审核特点。"}]},
            "audience": {"title": "适宜人群", "items": ["已审核人群"]},
            "combination": {"title": "咨询场景", "rows": [{"problem": "场景一", "partner": "搭档一", "talk_track": "已审核话术。"}]},
            "summary": {"title": "总结", "rows": [{"label": "要点", "value": "已审核。"}]},
            "precautions": {"title": "注意事项", "items": ["核对本品正式标签。"]},
        }
        script_path = self.tmp / "script.json"
        script_path.write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
        rc = bj.main(
            [
                "new",
                "--route",
                "product-pptx-component-v1",
                "--theme",
                "完整素材测试",
                "--script-json",
                str(script_path),
                "--job-id",
                "test-assets-complete",
                "--auto-draft",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-assets-complete")
        plan = json.loads(Path(job["draft"]["asset_plan_json"]).read_text(encoding="utf-8"))
        bindings = {item["script_path"]: str(image) for item in plan["system_generates"]}
        bindings_path = self.tmp / "bindings.json"
        bindings_path.write_text(json.dumps(bindings, ensure_ascii=False), encoding="utf-8")

        rc = bj.main(
            [
                "approve",
                "--job",
                "test-assets-complete",
                "--gate",
                "content",
                "--by",
                "测试员",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        rc = bj.main(
            [
                "approve",
                "--job",
                "test-assets-complete",
                "--gate",
                "visual",
                "--by",
                "测试员",
                "--asset-bindings",
                str(bindings_path),
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-assets-complete")
        self.assertEqual(job["state"], "visual_approved")
        self.assertEqual(len(job["approvals"]["visual"]["visual_assets_sha256"]), 64)
        rc = bj.main(
            [
                "approve",
                "--job",
                "test-assets-complete",
                "--gate",
                "product_image",
                "--by",
                "测试员",
                "--product-image",
                str(image),
                "--authorization-reference",
                "TEST-AUTH-COMPONENT",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-assets-complete")
        final_script = json.loads(Path(job["draft"]["script"]).read_text(encoding="utf-8"))
        self.assertTrue(Path(final_script["meta"]["product_packshot"]).is_file())
        self.assertEqual(final_script["benefits"]["items"][0]["chain"][0]["w"], 1200)
        self.assertTrue(final_script["precautions"]["illustrations"][0]["wide"])
        final_plan = json.loads(Path(job["draft"]["asset_plan_json"]).read_text(encoding="utf-8"))
        self.assertFalse(bj.formal_render_blockers(final_plan))
        ready, missing = bj._approvals_ready(
            job, bj.get_route("product-pptx-component-v1")
        )
        self.assertTrue(ready, missing)

    def test_uat_job_is_hidden_from_default_production_scope(self) -> None:
        uat_jobs = self.tmp / "uat-jobs"
        uat_delivery = self.tmp / "uat-delivery"
        uat_jobs.mkdir()
        uat_delivery.mkdir()
        production_jobs = self.jobs
        production_delivery = self.delivery

        bj.jobs_root = lambda: (  # type: ignore[assignment]
            uat_jobs if bj._ACTIVE_SCOPE == "uat" else production_jobs
        )
        bj.delivery_root = lambda: (  # type: ignore[assignment]
            uat_delivery if bj._ACTIVE_SCOPE == "uat" else production_delivery
        )

        rc = bj.main(
            [
                "new",
                "--scope",
                "uat",
                "--route",
                "product-pptx-component-v1",
                "--theme",
                "模拟验收商品",
                "--job-id",
                "uat-scope-1",
                "--auto-draft",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue((uat_jobs / "uat-scope-1/job.json").is_file())
        self.assertFalse((production_jobs / "uat-scope-1").exists())

        with self.assertRaises(SystemExit):
            bj.main(["status", "--job", "uat-scope-1", "--json"])

        rc = bj.main(
            ["status", "--scope", "uat", "--job", "uat-scope-1", "--json"]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("uat-scope-1")
        self.assertEqual(job["scope"], "uat")

    def test_video_requires_product_image_gate_before_render(self) -> None:
        # tiny fake packshot
        pack = self.tmp / "pack.png"
        pack.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0c"
            b"IDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        rc = bj.main(
            [
                "new",
                "--route",
                "product-mp4-full-v1",
                "--theme",
                "测试舒心片",
                "--notes",
                "支持日常精力",
                "--product-image",
                str(pack),
                "--job-id",
                "test-video-1",
                "--auto-draft",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-video-1")
        self.assertEqual(job["state"], "draft_ready")
        self.assertEqual(job["draft"]["kind"], "product_video_full")

        bj.main(
            [
                "approve",
                "--job",
                "test-video-1",
                "--gate",
                "content",
                "--by",
                "测试员",
            ]
        )
        with self.assertRaises(SystemExit) as ctx:
            bj.main(["render", "--job", "test-video-1"])
        self.assertIn("product_image", str(ctx.exception))

        rc = bj.main(
            [
                "approve",
                "--job",
                "test-video-1",
                "--gate",
                "product_image",
                "--by",
                "测试员",
                "--authorization-reference",
                "TEST-AUTH-1",
            ]
        )
        self.assertEqual(rc, 0)
        ready, missing = bj._approvals_ready(
            bj.load_job("test-video-1"), bj.get_route("product-mp4-full-v1")
        )
        self.assertTrue(ready, missing)

    def test_render_env_blocked_does_not_publish(self) -> None:
        rc = bj.main(
            [
                "new",
                "--route",
                "product-pptx-component-v1",
                "--theme",
                "环境阻断样例",
                "--notes",
                "要点一\n要点二\n要点三",
                "--job-id",
                "test-env-1",
                "--auto-draft",
            ]
        )
        self.assertEqual(rc, 0)
        with mock.patch.object(bj, "_prepare_component_content_for_approval"):
            bj.main(
                [
                    "approve",
                    "--job",
                    "test-env-1",
                    "--gate",
                    "content",
                    "--by",
                    "测试员",
                ]
            )
        with mock.patch.object(bj, "_approvals_ready", return_value=(True, [])), mock.patch.object(
            bj, "probe_capabilities", return_value={"pptx_export": False}
        ):
            code = bj.main(["render", "--job", "test-env-1", "--json"])
        self.assertEqual(code, 2)
        job = bj.load_job("test-env-1")
        self.assertEqual(job["state"], "env_blocked")
        self.assertFalse((job.get("delivery") or {}).get("published"))
        # nothing published under delivery root
        self.assertEqual(list(self.delivery.iterdir()), [])

    def test_component_render_rechecks_asset_plan(self) -> None:
        path = self.jobs / "test-render-plan" / "draft"
        path.mkdir(parents=True)
        script_path = path / "script.structured.json"
        script = {"meta": {"page_sequence": ["courseware_cover"]}}
        script_path.write_text(json.dumps(script), encoding="utf-8")
        digest = bj._component_content_sha256(script)
        job = {
            "job_id": "test-render-plan",
            "theme": "素材门闸",
            "draft": {"script": str(script_path), "content_sha256": digest},
            "approvals": {"content": {"approved": True, "content_sha256": digest}},
        }
        route = bj.get_route("product-pptx-component-v1")
        with mock.patch.object(bj, "build_product_pptx_asset_plan", return_value={}), mock.patch.object(
            bj, "formal_render_blockers", return_value=["缺少业务授权真图：商品正式包装图"]
        ):
            with self.assertRaises(RuntimeError) as ctx:
                bj._render_product_pptx_component(job, route)
        self.assertIn("正式素材未齐", str(ctx.exception))

    def test_component_formal_flow_requires_explicit_page_sequence(self) -> None:
        path = self.jobs / "test-render-sequence" / "draft"
        path.mkdir(parents=True)
        script_path = path / "script.structured.json"
        script = {
            "schema": "product-training-script/v1",
            "meta": {"display_name": "页签闸门测试"},
            "hook": {"title": "导语", "paragraphs": ["内容已审核。"]},
        }
        script_path.write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
        digest = bj._component_content_sha256(script)
        job = {
            "job_id": "test-render-sequence",
            "theme": "页签闸门测试",
            "draft": {"script": str(script_path), "content_sha256": digest},
            "approvals": {"content": {"approved": True, "content_sha256": digest}},
        }
        route = bj.get_route("product-pptx-component-v1")
        with self.assertRaises(RuntimeError) as ctx:
            bj._render_product_pptx_component(job, route)
        self.assertIn("meta.page_sequence", str(ctx.exception))

    def test_candidate_page_types_are_uat_only_until_promoted(self) -> None:
        registry = self.tmp / "candidate-registry.json"
        registry.write_text(
            json.dumps(
                {
                    "page_types": [
                        {"id": "courseware_cover", "status": "settled"},
                        {"id": "future_candidate", "status": "candidate"},
                        {"id": "validated_page", "status": "production-validated"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        script = {
            "meta": {
                "display_name": "候选页型测试",
                "page_sequence": [
                    "courseware_cover",
                    "future_candidate",
                    "validated_page",
                ],
            }
        }
        with mock.patch.object(bj, "_COMPONENT_REGISTRY", registry):
            bj.set_active_scope("production")
            blockers = bj._component_page_sequence_blockers(script)
            self.assertTrue(any("future_candidate" in item for item in blockers))
            self.assertFalse(any("validated_page" in item for item in blockers))
            self.assertTrue(
                any(
                    "future_candidate" in item
                    for item in bj._component_content_blockers(script)
                )
            )

            bj.set_active_scope("uat")
            self.assertEqual(bj._component_page_sequence_blockers(script), [])
        bj.set_active_scope("production")

    def test_component_render_does_not_publish_without_complete_page_qa(self) -> None:
        path = self.jobs / "test-render-qa" / "draft"
        path.mkdir(parents=True)
        script_path = path / "script.structured.json"
        script = {"meta": {"page_sequence": ["courseware_cover"]}}
        script_path.write_text(json.dumps(script), encoding="utf-8")
        digest = bj._component_content_sha256(script)
        job = {
            "job_id": "test-render-qa",
            "theme": "逐页质检门闸",
            "draft": {"script": str(script_path), "content_sha256": digest},
            "approvals": {"content": {"approved": True, "content_sha256": digest}},
        }
        route = bj.get_route("product-pptx-component-v1")

        def fake_generator(**kwargs: object) -> dict[str, object]:
            out_dir = Path(kwargs["out_dir"])
            (out_dir / "fake.pptx").write_bytes(b"pptx")
            return {"ok": True, "page_count": 1, "qa": []}

        with mock.patch.object(bj, "build_product_pptx_asset_plan", return_value={}), mock.patch.object(
            bj, "formal_render_blockers", return_value=[]
        ), mock.patch.object(bj, "_verify_component_asset_approvals"), mock.patch.object(
            bj, "_run_courseware_generator", side_effect=fake_generator
        ):
            result = bj._render_product_pptx_component(job, route)
        self.assertFalse(result["ok"])
        self.assertFalse(result["qa_passed"])
        self.assertIn("逐页视觉 QA", str(result["error"]))
        self.assertEqual(list(self.delivery.iterdir()), [])

    def test_whitelist_publish_only_after_success(self) -> None:
        route = bj.get_route("product-pptx-component-v1")
        job = {
            "job_id": "pub-1",
            "theme": "发布样例",
            "draft": {"content_sha256": "a" * 64},
            "approvals": {
                "content": {
                    "approved": True,
                    "approved_by": "t",
                    "approved_at": "now",
                    "content_sha256": "a" * 64,
                }
            },
        }
        src = self.tmp / "src"
        src.mkdir()
        pptx = src / "a.pptx"
        pptx.write_bytes(b"PK fake")
        note = src / "note.md"
        note.write_text("ok", encoding="utf-8")
        rec = src / "rec.json"
        rec.write_text("{}", encoding="utf-8")
        result = bj._publish_whitelist(
            job,
            route,
            {
                "终稿.pptx": pptx,
                "交付说明.md": note,
                "内容确认记录.json": rec,
            },
        )
        self.assertTrue(result["ok"])
        dest = Path(result["path"])
        self.assertTrue((dest / "终稿.pptx").is_file())
        self.assertTrue((dest / "run-manifest.json").is_file())
        # no workspace pollution
        self.assertFalse((dest / "workspace").exists())
        self.assertFalse((dest / "node_modules").exists())

    def test_inactive_route_requires_force(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            bj.main(
                [
                    "new",
                    "--route",
                    "health-mp4-full-v1",
                    "--theme",
                    "感冒",
                    "--job-id",
                    "test-health-off",
                ]
            )
        self.assertIn("未激活", str(ctx.exception))

    def test_inactive_courseware3_mp4_route_requires_force(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            bj.main(
                [
                    "new",
                    "--route",
                    "courseware3-mp4-v1",
                    "--theme",
                    "暂不出视频",
                    "--job-id",
                    "test-courseware3-mp4-off",
                ]
            )
        self.assertIn("未激活", str(ctx.exception))

    def test_pptx_draft_strips_green_gold_residue(self) -> None:
        """Active green fixed route must not leak 金银花露 gold copy."""
        rc = bj.main(
            [
                "new",
                "--route",
                "product-pptx-green-v1",
                "--theme",
                "P1清洁冒烟商品",
                "--notes",
                "温和去火\n店员话术清晰",
                "--job-id",
                "test-green-clean",
                "--auto-draft",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-green-clean")
        model = json.loads(Path(job["draft"]["content_model"]).read_text(encoding="utf-8"))
        blob = json.dumps(model, ensure_ascii=False)
        for token in (
            "金银花露",
            "可可康",
            "小葵花",
            "小儿咽扁",
            "2429715",
            "265ml",
            "9.9元",
        ):
            self.assertNotIn(token, blob, msg=f"gold residue: {token}")

        overview = next(p for p in model["pages"] if p["id"] == "product-overview")
        self.assertEqual(overview["product"]["display_name"], "P1清洁冒烟商品")
        self.assertEqual(overview["product"]["code"], "待确认")
        self.assertEqual(overview["product"]["retail_price"], "待确认")

        combo = next(p for p in model["pages"] if p["id"] == "combination-guidance")
        self.assertEqual(len(combo["rows"]), 1)
        self.assertIn("待确认", combo["rows"][0]["scenario"])
        self.assertIn("P1清洁冒烟商品", combo["rows"][0]["combination"])

        bench = next(p for p in model["pages"] if p["id"] == "product-benchmark")
        self.assertEqual(bench["columns"][1], "P1清洁冒烟商品")
        self.assertIn("待确认", bench["columns"][2])

        prec = next(p for p in model["pages"] if p["id"] == "precautions")
        self.assertTrue(any("待确认" in str(i) for i in prec["items"]))
        self.assertEqual(len(prec["items"]), 4)

    def test_fixed_routes_accept_partial_materials_without_gold_copy(self) -> None:
        cases = (
            (
                "product-pptx-disease-scenario-v1",
                "资料未齐商品乙",
                "partial-disease",
                ("穿心莲", "安宫", "97%", "95%"),
            ),
            (
                "courseware3-pptx-v1",
                "资料未齐商品丙",
                "partial-courseware3",
                ("速福达", "玛巴洛沙韦"),
            ),
        )
        for route_id, theme, job_id, forbidden in cases:
            self.assertEqual(
                bj.main(
                    [
                        "new",
                        "--route",
                        route_id,
                        "--theme",
                        theme,
                        "--job-id",
                        job_id,
                        "--auto-draft",
                        "--json",
                    ]
                ),
                0,
            )
            job = bj.load_job(job_id)
            self.assertEqual(job["state"], "draft_ready")
            self.assertTrue(job["draft"]["gaps"])
            model = Path(job["draft"]["content_model"]).read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, model)
            with self.assertRaises(SystemExit):
                bj.main(
                    [
                        "approve",
                        "--job",
                        job_id,
                        "--gate",
                        "content",
                        "--by",
                        "测试员",
                    ]
                )


class PortalStillHasApprovalLanguageTests(unittest.TestCase):
    def test_preview_only_template_still_blocks_formal_generation_language(self) -> None:
        catalog = bj.catalog_by_slug()
        preview = catalog["fuler-fanqiehongsu-product-courseware-4-v1"]
        cmd = build_business_command(preview)
        self.assertIn("仅查看金样", cmd)
        self.assertIn("不要生成正式成品", cmd)
        self.assertIsNone(build_job_command(preview))


class WpsOpenContractTests(unittest.TestCase):
    def test_presentation_open_uses_wps_explicitly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wps-open-") as tmp:
            deck = Path(tmp) / "终稿.pptx"
            deck.write_bytes(b"pptx-test")
            wps = Path("/Applications/wpsoffice.app")
            completed = mock.Mock(returncode=0)
            with mock.patch.object(bj, "_find_macos_wps_app", return_value=wps), mock.patch.object(
                bj.subprocess, "run", return_value=completed
            ) as run:
                bj._open_business_path(deck)
            run.assert_called_once_with(
                ["open", "-a", str(wps), str(deck)],
                check=False,
            )
            argv = run.call_args.args[0]
            self.assertNotIn("LibreOffice", argv)
            self.assertNotIn("soffice", argv)

    def test_presentation_open_fails_closed_without_wps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="wps-missing-") as tmp:
            deck = Path(tmp) / "终稿.pptx"
            deck.write_bytes(b"pptx-test")
            with mock.patch.object(bj, "_find_macos_wps_app", return_value=None), mock.patch.object(
                bj.subprocess, "run"
            ) as run:
                with self.assertRaisesRegex(SystemExit, "未找到 WPS Office"):
                    bj._open_business_path(deck)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
