#!/usr/bin/env python3
"""P0 regressions for approved content, packshots, and prompt release gates."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_health_theme_package import (  # noqa: E402
    LANG_PATH as HEALTH_LANGUAGE_PATH,
    build_screen_and_plan as build_health_theme_screen,
    map_sections as map_health_theme_sections,
)
from business_video_health_full import (  # noqa: E402
    extract_screen_fields as health_screen,
    require_theme_package_approval,
    run_health_full,
    theme_package_payload_sha256,
)
from business_video_product_full import (  # noqa: E402
    build_product_approval_request,
    require_product_approval,
    run_product_full,
)
from scaffold_jiugongge_health_edu_compliance import (  # noqa: E402
    build_segments as build_compliance_segments,
    scan_release_banned_terms,
)


class P0ContentSafetyTest(unittest.TestCase):
    def test_health_plan_does_not_infer_medical_claims_from_disease_name(self) -> None:
        sections = [
            {"title": "典型症状", "narration": "鼻塞、流涕、乏力。"},
        ]
        mapped = {"symptoms": sections[0]}

        screen = health_screen("风寒感冒", mapped, sections)
        payload = json.dumps(screen, ensure_ascii=False)

        for leaked_claim in (
            "风邪",
            "寒邪",
            "辛温解表",
            "疏风清热",
            "辨证调理",
            "桑叶",
            "银翘解毒颗粒",
        ):
            self.assertNotIn(leaked_claim, payload)

        gap_fields = {gap["field"] for gap in screen["content_gaps"]}
        self.assertIn("mechanism_equation", gap_fields)
        self.assertIn("treatment_principle", gap_fields)

    def test_health_screen_uses_only_submitted_treatment_wording(self) -> None:
        treatment = {
            "title": "调理建议",
            "narration": "审核原文：核心是充分休息。每日少量多次饮水。",
        }
        screen = health_screen("示例主题", {"treatment": treatment}, [treatment])

        self.assertEqual(screen["core_treatment"], "充分休息")
        self.assertIn("充分休息", screen["treatment_line_1"])
        self.assertNotIn("辨证调理", json.dumps(screen, ensure_ascii=False))

    def test_health_theme_package_does_not_add_unsubmitted_medical_content(self) -> None:
        sections = [
            {"title": "典型表现", "narration": "业务审核原文：打喷嚏。"},
        ]
        mapped = map_health_theme_sections(sections, "风寒感冒")

        self.assertNotIn("intro", mapped)
        with tempfile.TemporaryDirectory() as temp_dir:
            language = json.loads(HEALTH_LANGUAGE_PATH.read_text(encoding="utf-8"))
            screen, _ = build_health_theme_screen(
                "风寒感冒", mapped, language, Path(temp_dir)
            )

        payload = json.dumps(screen, ensure_ascii=False)
        for leaked_claim in (
            "风邪",
            "寒邪",
            "辛温解表",
            "解表祛邪",
            "桑叶",
            "菊花",
            "银翘解毒颗粒",
            "多喝温水",
        ):
            self.assertNotIn(leaked_claim, payload)
        self.assertNotIn("character", mapped)
        self.assertIn("symptoms", mapped)
        self.assertEqual(screen["character_cards"], [])
        self.assertEqual(
            screen["symptom_groups"][0]["items"][0]["label"],
            "业务审核原文：打喷嚏",
        )
        self.assertTrue(screen["content_gaps"])

    def test_health_visual_approval_is_bound_to_current_package_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir)
            for name, payload in {
                "screen.json": {"disease_name": "审核主题"},
                "sections.json": {"sections": []},
                "visual-plan.json": {"slots": []},
                "visual-coverage.json": {"total": 0},
            }.items():
                (package / name).write_text(
                    json.dumps(payload, ensure_ascii=False), encoding="utf-8"
                )
            current_hash = theme_package_payload_sha256(package)
            approval_path = package / "approval.json"
            approval_path.write_text(
                json.dumps(
                    {
                        "visuals_approved": True,
                        "approved_by": "测试审核人",
                        "approved_at": "2026-08-08T10:00:00+08:00",
                        "approved_payload_sha256": current_hash,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.assertTrue(require_theme_package_approval(package)["ok"])

            (package / "screen.json").write_text(
                json.dumps({"disease_name": "审批后被修改"}, ensure_ascii=False),
                encoding="utf-8",
            )
            rejected = require_theme_package_approval(package)
            self.assertFalse(rejected["ok"])
            self.assertIn("SHA-256", rejected["error"])

    def test_formal_health_render_cannot_skip_visual_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sections_path = Path(temp_dir) / "sections.json"
            sections_path.write_text(
                json.dumps(
                    {
                        "theme": "审核主题",
                        "sections": [{"title": "开场", "narration": "审核开场"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "generate_business_video.py"),
                    "--template",
                    "health",
                    "--sections-json",
                    str(sections_path),
                    "--mode",
                    "full",
                    "--with-mp4",
                    "--skip-visual-approval",
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("旁白、渲染和交付均禁止", result.stderr + result.stdout)

    def test_health_theme_package_cannot_be_overridden_by_external_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = temp / "theme-package"
            package.mkdir()
            (package / "sections.json").write_text(
                json.dumps({"theme": "已审批主题", "sections": []}, ensure_ascii=False),
                encoding="utf-8",
            )
            external = temp / "external.json"
            external.write_text(
                json.dumps(
                    {
                        "theme": "审批外主题",
                        "sections": [{"title": "开场", "narration": "审批外旁白"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "generate_business_video.py"),
                    "--template",
                    "health",
                    "--theme-package",
                    str(package),
                    "--sections-json",
                    str(external),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("禁止再叠加外部", result.stderr + result.stdout)

    def test_product_formal_render_requires_authorized_packshot_before_tts(self) -> None:
        content = {
            "theme": "示例商品",
            "sections": [{"title": "开场", "narration": "这是审核通过的开场。"}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            status = run_product_full(
                content=content,
                out_dir=temp / "run",
                voice_pack_dir=temp / "missing-voice-pack",
                with_tts=True,
                with_render=True,
                product_image=None,
            )

            self.assertFalse(status["ok"])
            self.assertIn("授权包装", status["error"])
            self.assertFalse((temp / "run" / "render-workspace").exists())
            self.assertNotIn(
                "generic-coq10-packshot-v1.png",
                json.dumps(status, ensure_ascii=False),
            )

    def test_formal_video_rejects_extra_unmapped_approved_sections(self) -> None:
        product_sections = [
            {"title": f"商品段落{index + 1}", "narration": f"审核旁白{index + 1}"}
            for index in range(9)
        ]
        health_sections = [
            {"title": f"健康段落{index + 1}", "narration": f"审核旁白{index + 1}"}
            for index in range(8)
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            product = run_product_full(
                content={"theme": "示例商品", "sections": product_sections},
                out_dir=temp / "product",
                voice_pack_dir=temp / "missing-voice",
                with_tts=False,
                with_render=True,
                product_image=None,
            )
            health = run_health_full(
                content={"theme": "示例主题", "sections": health_sections},
                out_dir=temp / "health",
                voice_pack_dir=temp / "missing-voice",
                with_tts=False,
                with_render=True,
            )

        self.assertFalse(product["ok"])
        self.assertIn("8 段", product["error"])
        self.assertIn("额外", product["error"])
        self.assertFalse(health["ok"])
        self.assertIn("7 段", health["error"])
        self.assertIn("额外", health["error"])

    def test_product_approval_binds_content_packshot_and_authorization_reference(self) -> None:
        content = {
            "theme": "示例商品",
            "sections": [{"title": "开场", "narration": "已审核开场"}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            image = temp / "pack.png"
            image.write_bytes(b"authorized-packshot")
            approval = build_product_approval_request(content, image)
            approval.update(
                {
                    "approved": True,
                    "approved_by": "业务审核人",
                    "approved_at": "2026-08-08T12:00:00+08:00",
                    "authorization_reference": "品牌方授权单-2026-001",
                }
            )
            approval_path = temp / "approval.json"
            approval_path.write_text(
                json.dumps(approval, ensure_ascii=False), encoding="utf-8"
            )
            self.assertTrue(require_product_approval(content, image, approval_path)["ok"])

            image.write_bytes(b"changed-after-approval")
            rejected = require_product_approval(content, image, approval_path)
            self.assertFalse(rejected["ok"])
            self.assertIn("包装图", rejected["error"])

    def test_same_path_product_approval_is_not_overwritten_on_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            out_dir = temp / "run"
            out_dir.mkdir()
            sections = temp / "sections.json"
            sections.write_text(
                json.dumps(
                    {
                        "theme": "示例商品",
                        "sections": [
                            {"title": "开场", "narration": "审核通过的开场旁白"}
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            approval = out_dir / "product-approval.request.json"
            original = {
                "schema": "product-video-approval-v1",
                "approved": True,
                "sentinel": "must-not-be-overwritten",
            }
            approval.write_text(
                json.dumps(original, ensure_ascii=False), encoding="utf-8"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "generate_business_video.py"),
                    "--template",
                    "product",
                    "--sections-json",
                    str(sections),
                    "--out-dir",
                    str(out_dir),
                    "--mode",
                    "plan",
                    "--product-approval",
                    str(approval),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(
                json.loads(approval.read_text(encoding="utf-8")),
                original,
            )

    def test_prompt_scaffolds_default_to_review_and_release_after_approval(self) -> None:
        cases = [
            (
                "scaffold_seedance_health_edu.py",
                {
                    "theme": "暴雨天居家安全",
                    "target_audience": "家人",
                },
                "01-科普脚本复核包.md",
                ["02-Seedance提示词-分段.md", "03-视频号发布全家桶.md"],
            ),
            (
                "scaffold_jiugongge_health_edu.py",
                {"theme": "生活状态提醒", "knowledge_points": ["留意日常变化"]},
                "01-科普脚本复核包.md",
                [
                    "02-角色三视图提示词.md",
                    "03-九宫格与视频提示词-六段.md",
                    "04-社媒合规发布包.md",
                ],
            ),
            (
                "scaffold_jiugongge_health_edu_compliance.py",
                {"theme": "办公久坐小习惯", "habit_points": ["每小时起身走一走"]},
                "01-合规脚本复核包.md",
                [
                    "02-视觉资产提示词.md",
                    "03-九宫格与视频提示词-六段.md",
                    "04-视频号发布全家桶.md",
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            for index, (script, variables, review_name, release_names) in enumerate(cases):
                with self.subTest(script=script):
                    vars_path = temp / f"vars-{index}.json"
                    vars_path.write_text(
                        json.dumps(variables, ensure_ascii=False), encoding="utf-8"
                    )
                    out_root = temp / f"out-{index}"
                    slug = f"case-{index}"
                    review = self._run_scaffold(
                        script,
                        vars_path,
                        out_root,
                        slug,
                    )
                    self.assertEqual(review.returncode, 0, review.stderr)

                    out = out_root / slug
                    self.assertTrue((out / review_name).is_file())
                    approval_path = out / "approval.json"
                    self.assertTrue(approval_path.is_file())
                    for name in release_names:
                        self.assertFalse((out / name).exists())
                    self.assertFalse((out / "release-manifest.json").exists())

                    approval = json.loads(approval_path.read_text(encoding="utf-8"))
                    approval["approved"] = True
                    approval["approved_by"] = "测试审核人"
                    approval_path.write_text(
                        json.dumps(approval, ensure_ascii=False), encoding="utf-8"
                    )
                    release = self._run_scaffold(
                        script,
                        vars_path,
                        out_root,
                        slug,
                        "--release",
                        "--approval",
                        str(approval_path),
                    )
                    self.assertEqual(release.returncode, 0, release.stderr)
                    for name in release_names:
                        self.assertTrue((out / name).is_file(), name)
                    self.assertTrue((out / "release-manifest.json").is_file())

    def test_prompt_release_rejects_stale_input_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vars_path = temp / "vars.json"
            vars_path.write_text(
                json.dumps({"theme": "暴雨天居家安全"}, ensure_ascii=False),
                encoding="utf-8",
            )
            out_root = temp / "out"
            slug = "seedance"
            first = self._run_scaffold(
                "scaffold_seedance_health_edu.py", vars_path, out_root, slug
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            approval_path = out_root / slug / "approval.json"
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
            approval.update({"approved": True, "approved_by": "测试审核人"})
            approval_path.write_text(json.dumps(approval), encoding="utf-8")

            vars_path.write_text(
                json.dumps({"theme": "已经改过的主题"}, ensure_ascii=False),
                encoding="utf-8",
            )
            result = self._run_scaffold(
                "scaffold_seedance_health_edu.py",
                vars_path,
                out_root,
                slug,
                "--release",
                "--approval",
                str(approval_path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hash", (result.stderr + result.stdout).lower())

    def test_prompt_release_binds_review_hash_and_removes_stale_release_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vars_path = temp / "vars.json"
            vars_path.write_text(
                json.dumps(
                    {"theme": "暴雨天居家安全", "target_audience": "家人"},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            out_root = temp / "out"
            slug = "seedance-review-hash"
            review = self._run_scaffold(
                "scaffold_seedance_health_edu.py", vars_path, out_root, slug
            )
            self.assertEqual(review.returncode, 0, review.stderr)
            out = out_root / slug
            approval_path = out / "approval.json"
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
            approval.update({"approved": True, "approved_by": "测试审核人"})
            approval_path.write_text(
                json.dumps(approval, ensure_ascii=False), encoding="utf-8"
            )
            released = self._run_scaffold(
                "scaffold_seedance_health_edu.py",
                vars_path,
                out_root,
                slug,
                "--release",
                "--approval",
                str(approval_path),
            )
            self.assertEqual(released.returncode, 0, released.stderr)
            release_file = out / "02-Seedance提示词-分段.md"
            self.assertTrue(release_file.is_file())

            approval["review_sha256"] = "stale-review-hash"
            approval_path.write_text(
                json.dumps(approval, ensure_ascii=False), encoding="utf-8"
            )
            rejected = self._run_scaffold(
                "scaffold_seedance_health_edu.py",
                vars_path,
                out_root,
                slug,
                "--release",
                "--approval",
                str(approval_path),
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("review hash", (rejected.stderr + rejected.stdout).lower())
            self.assertFalse(release_file.exists())

    def test_compliance_release_hard_fails_on_banned_terms(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vars_path = temp / "vars.json"
            vars_path.write_text(
                json.dumps(
                    {"theme": "感冒预防", "habit_points": ["治疗感冒的小动作"]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            out_root = temp / "out"
            slug = "unsafe"
            review = self._run_scaffold(
                "scaffold_jiugongge_health_edu_compliance.py",
                vars_path,
                out_root,
                slug,
            )
            self.assertEqual(review.returncode, 0, review.stderr)
            approval_path = out_root / slug / "approval.json"
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
            approval.update({"approved": True, "approved_by": "测试审核人"})
            approval_path.write_text(json.dumps(approval), encoding="utf-8")

            release = self._run_scaffold(
                "scaffold_jiugongge_health_edu_compliance.py",
                vars_path,
                out_root,
                slug,
                "--release",
                "--approval",
                str(approval_path),
            )
            self.assertNotEqual(release.returncode, 0)
            self.assertIn("禁词", release.stderr + release.stdout)
            self.assertFalse((out_root / slug / "03-九宫格与视频提示词-六段.md").exists())

    def test_compliance_scan_allows_explicit_negative_guards(self) -> None:
        example = ROOT / (
            "production-library/templates/prompt-modes/"
            "jiugongge-health-edu-compliance-v1/example-告别办公久坐僵硬.json"
        )
        variables = json.loads(example.read_text(encoding="utf-8"))
        hits = scan_release_banned_terms(
            variables, build_compliance_segments(variables)
        )
        self.assertEqual(hits, [])

    def test_compliance_disclaimer_does_not_hide_same_sentence_claims(self) -> None:
        variables = {
            "theme": "居家习惯",
            "habit_points": ["不能替代医生诊断，但这里给出治疗方案。"],
        }
        hits = scan_release_banned_terms(
            variables, build_compliance_segments(variables)
        )
        terms = {item["term"] for item in hits}
        self.assertTrue({"医生", "诊断", "治疗"} & terms)

    def _run_scaffold(
        self,
        script: str,
        vars_path: Path,
        out_root: Path,
        slug: str,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / script),
                "--vars",
                str(vars_path),
                "--out-root",
                str(out_root),
                "--slug",
                slug,
                *extra,
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )


if __name__ == "__main__":
    unittest.main()
