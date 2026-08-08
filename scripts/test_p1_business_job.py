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
    def test_routes_file_has_core_active_routes(self) -> None:
        doc = bj.load_routes_doc()
        self.assertEqual(doc.get("schema"), "business-routes-v1")
        self.assertEqual(doc.get("default_pptx_route"), "product-pptx-component-v1")
        active = [r for r in doc["routes"] if r.get("active")]
        ids = {r["route_id"] for r in active}
        self.assertIn("product-pptx-component-v1", ids)
        self.assertIn("product-pptx-green-v1", ids)
        self.assertIn("product-mp4-full-v1", ids)
        # Health remains inactive until theme-package self-serve is proven.
        health = next(r for r in doc["routes"] if r["route_id"] == "health-mp4-full-v1")
        self.assertFalse(health["active"])
        # Default component route outranks legacy green.
        comp = next(r for r in active if r["route_id"] == "product-pptx-component-v1")
        green = next(r for r in active if r["route_id"] == "product-pptx-green-v1")
        self.assertLess(int(comp["priority"]), int(green["priority"]))

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

    def test_portal_commands_include_job_cli_for_wired_templates(self) -> None:
        catalog = bj.catalog_by_slug()
        component = catalog["product-courseware-component-v1"]
        green = catalog["product-courseware-green-v1"]
        video = catalog["product-video-faithful-v1"]
        self.assertIn(
            "business_job.py new --route product-pptx-component-v1",
            build_business_command(component),
        )
        self.assertIn("business_job.py new --route product-pptx-green-v1", build_business_command(green))
        self.assertIn("business_job.py new --route product-mp4-full-v1", build_business_command(video))
        self.assertIn("--gate content", build_job_command(component) or "")
        self.assertIn("product_image", build_job_command(video) or "")


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

    def test_pptx_draft_approve_blocks_render_without_content_gate(self) -> None:
        rc = bj.main(
            [
                "new",
                "--route",
                "product-pptx-green-v1",
                "--theme",
                "测试绿茶",
                "--notes",
                "卖点A\n卖点B",
                "--job-id",
                "test-green-1",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-green-1")
        self.assertEqual(job["state"], "intake")

        rc = bj.main(["draft", "--job", "test-green-1", "--json"])
        self.assertEqual(rc, 0)
        job = bj.load_job("test-green-1")
        self.assertEqual(job["state"], "draft_ready")
        self.assertTrue(Path(job["draft"]["content_model"]).is_file())
        self.assertEqual(len(job["draft"]["content_sha256"]), 64)

        with self.assertRaises(SystemExit) as ctx:
            bj.main(["render", "--job", "test-green-1", "--json"])
        self.assertIn("审批未齐", str(ctx.exception))

        rc = bj.main(
            [
                "approve",
                "--job",
                "test-green-1",
                "--gate",
                "content",
                "--by",
                "测试员",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        job = bj.load_job("test-green-1")
        self.assertEqual(job["state"], "content_approved")
        self.assertTrue(job["approvals"]["content"]["approved"])

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
                "product-pptx-green-v1",
                "--theme",
                "环境阻断样例",
                "--job-id",
                "test-env-1",
                "--auto-draft",
            ]
        )
        self.assertEqual(rc, 0)
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
        with mock.patch.object(bj, "probe_capabilities", return_value={"pptx_export": False}):
            code = bj.main(["render", "--job", "test-env-1", "--json"])
        self.assertEqual(code, 2)
        job = bj.load_job("test-env-1")
        self.assertEqual(job["state"], "env_blocked")
        self.assertFalse((job.get("delivery") or {}).get("published"))
        # nothing published under delivery root
        self.assertEqual(list(self.delivery.iterdir()), [])

    def test_whitelist_publish_only_after_success(self) -> None:
        route = bj.get_route("product-pptx-green-v1")
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

    def test_pptx_draft_strips_green_gold_residue(self) -> None:
        """New theme must not inherit 金银花露 medical/price/combo copy from gold JSON."""
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
        self.assertEqual(len(prec["items"]), 3)


class PortalStillHasApprovalLanguageTests(unittest.TestCase):
    def test_preview_only_template_still_blocks_formal_generation_language(self) -> None:
        catalog = bj.catalog_by_slug()
        preview = catalog["fuler-fanqiehongsu-product-courseware-4-v1"]
        cmd = build_business_command(preview)
        self.assertIn("仅查看金样", cmd)
        self.assertIn("不要生成正式成品", cmd)
        self.assertIsNone(build_job_command(preview))


if __name__ == "__main__":
    unittest.main()
