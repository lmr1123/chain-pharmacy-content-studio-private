#!/usr/bin/env python3
"""Protection tests for WorkBuddy runtime isolation and reproducible delivery."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GitIgnoreIsolationTests(unittest.TestCase):
    def check_ignored(self, relative_path: str) -> bool:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", relative_path],
            cwd=ROOT,
            check=False,
        )
        return result.returncode == 0

    def test_runtime_and_business_payloads_are_ignored_but_markers_are_not(self) -> None:
        package = "outputs/业务使用资料包/药店培训内容工厂-业务包"
        ignored = (
            "outputs/business-video-runs/demo/render-workspace/render.js",
            "outputs/business-courseware-runs/demo/final.pptx",
            "outputs/workbuddy-workspaces/demo/private.docx",
            f"{package}/index.local.html",
            f"{package}/05_交付物放这里/job/final.mp4",
            f"{package}/07_业务填报上传/误放在根目录的资料.docx",
            f"{package}/07_业务填报上传/待处理/业务资料.docx",
            f"{package}/07_业务填报上传/已提交/业务资料.docx",
        )
        for path in ignored:
            with self.subTest(path=path):
                self.assertTrue(self.check_ignored(path), path)

        retained = (
            f"{package}/05_交付物放这里/.gitkeep",
            f"{package}/05_交付物放这里/README.md",
            f"{package}/07_业务填报上传/README.md",
            f"{package}/07_业务填报上传/待处理/.gitkeep",
            f"{package}/07_业务填报上传/已提交/.gitkeep",
        )
        for path in retained:
            with self.subTest(path=path):
                self.assertFalse(self.check_ignored(path), path)


class BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("workbuddy_bootstrap_for_business")

    def make_private_root(self, parent: Path, origin: str | None = None) -> Path:
        root = parent / "repo"
        (root / ".git").mkdir(parents=True)
        (root / "production-library/templates/settled").mkdir(parents=True)
        marker = root / self.module.PRIVATE_MARKER_REL
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            json.dumps(
                {
                    "kind": self.module.PRIVATE_MARKER_KIND,
                    "version": 1,
                    "repository_url": self.module.DEFAULT_REPO,
                    "production_assets": True,
                }
            ),
            encoding="utf-8",
        )
        self.module.private_origin_url = mock.Mock(
            return_value=origin or self.module.DEFAULT_REPO
        )
        return root

    def test_existing_repo_pull_failure_stops_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self.make_private_root(Path(tmp))
            failed = subprocess.CompletedProcess(["git", "pull"], 1)
            with mock.patch.object(self.module, "run", return_value=failed):
                with self.assertRaisesRegex(SystemExit, "git pull"):
                    self.module.clone_or_update("https://example.invalid/repo.git", target)

    def test_private_bootstrap_uses_only_official_private_repo(self) -> None:
        self.assertEqual(
            self.module.clone_url_candidates(self.module.DEFAULT_REPO),
            ["https://github.com/lmr1123/chain-pharmacy-content-studio-private.git"],
        )
        self.assertNotIn("ghproxy", self.module.DEFAULT_REPO)

    def test_wrong_origin_is_not_a_private_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self.make_private_root(
                Path(tmp),
                origin="https://github.com/lmr1123/chain-pharmacy-content-studio.git",
            )
            self.assertFalse(self.module.is_private_repo(target))

    def test_official_ssh_origin_is_a_private_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self.make_private_root(
                Path(tmp),
                origin=(
                    "git@github.com:lmr1123/"
                    "chain-pharmacy-content-studio-private.git"
                ),
            )
            self.assertTrue(self.module.is_private_repo(target))

    def test_skip_update_only_accepts_valid_private_root_and_never_pulls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self.make_private_root(Path(tmp))
            with mock.patch.object(self.module, "run") as run:
                self.assertEqual(
                    self.module.clone_or_update(
                        self.module.DEFAULT_REPO,
                        target,
                        skip_update=True,
                    ),
                    target.resolve(),
                )
            run.assert_not_called()

    def test_skip_update_rejects_public_shell_without_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "repo"
            (target / ".git").mkdir(parents=True)
            (target / "production-library/templates/settled").mkdir(parents=True)
            with self.assertRaisesRegex(SystemExit, "Private"):
                self.module.clone_or_update(
                    self.module.DEFAULT_REPO,
                    target,
                    skip_update=True,
                )

    def test_bootstrap_always_requires_private_production_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self.make_private_root(Path(tmp))
            portal = target / "portal.html"
            with (
                mock.patch.object(
                    self.module.sys,
                    "argv",
                    [
                        "workbuddy_bootstrap_for_business.py",
                        "--target",
                        str(target),
                        "--skip-update",
                        "--no-open",
                        "--skip-soft-repair",
                    ],
                ),
                mock.patch.object(
                    self.module,
                    "probe_environment",
                    return_value={"capabilities": {"private_production_assets": True}},
                ) as probe,
                mock.patch.object(self.module, "ensure_package", return_value=portal),
                mock.patch.object(self.module, "print_guide"),
            ):
                self.module.main()
            probe.assert_called_once()
            args, kwargs = probe.call_args
            self.assertEqual(args[0], target.resolve())
            self.assertEqual(args[1], ["production-assets"])
            self.assertEqual(kwargs.get("profile_ids"), [])

    def test_bootstrap_profile_pptx_expands_require(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self.make_private_root(Path(tmp))
            # minimal runtime profiles for expand_requirements
            profiles = target / self.module.RUNTIME_PROFILES_REL
            profiles.parent.mkdir(parents=True, exist_ok=True)
            profiles.write_text(
                json.dumps(
                    {
                        "profiles": {
                            "pptx": {
                                "probe_require": ["pptx"],
                                "install_hints_zh": ["安装 node"],
                            }
                        },
                        "route_to_profile": {
                            "product-pptx-green-v1": "pptx",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            portal = target / "portal.html"
            with (
                mock.patch.object(
                    self.module.sys,
                    "argv",
                    [
                        "workbuddy_bootstrap_for_business.py",
                        "--target",
                        str(target),
                        "--skip-update",
                        "--no-open",
                        "--skip-soft-repair",
                        "--route",
                        "product-pptx-green-v1",
                    ],
                ),
                mock.patch.object(
                    self.module,
                    "probe_environment",
                    return_value={"capabilities": {"private_production_assets": True, "pptx_export": True}},
                ) as probe,
                mock.patch.object(self.module, "ensure_package", return_value=portal),
                mock.patch.object(self.module, "print_guide"),
                mock.patch.object(self.module, "run_doctor_summary"),
            ):
                self.module.main()
            args, kwargs = probe.call_args
            self.assertEqual(args[1], ["production-assets", "pptx"])
            self.assertEqual(kwargs.get("profile_ids"), ["pptx"])

    def test_failed_business_package_rebuild_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "scripts/build_business_tier_a_package.py"
            build.parent.mkdir(parents=True)
            build.write_text("# test\n", encoding="utf-8")
            failed = subprocess.CompletedProcess(["python", str(build)], 1)
            with mock.patch.object(self.module, "run", return_value=failed):
                with self.assertRaisesRegex(SystemExit, "业务包重建失败"):
                    self.module.ensure_package(root)

    def test_existing_portal_is_refreshed_with_runtime_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portal = root / self.module.PKG_REL / self.module.PORTAL_NAME
            portal.parent.mkdir(parents=True)
            portal.write_text("old", encoding="utf-8")
            build = root / "scripts/build_business_tier_a_package.py"
            build.parent.mkdir(parents=True)
            build.write_text("# test\n", encoding="utf-8")
            capabilities = {"pptx_export": True, "video_full": False}
            runtime_portal = portal.with_name(self.module.RUNTIME_PORTAL_NAME)

            def successful_refresh(command, **_kwargs):
                runtime_portal.write_text("local", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            with mock.patch.object(
                self.module, "run", side_effect=successful_refresh
            ) as run:
                self.assertEqual(
                    self.module.ensure_package(root, capabilities), runtime_portal
                )
            command = run.call_args.args[0]
            self.assertIn("--portal-only", command)
            raw = command[command.index("--runtime-capabilities-json") + 1]
            self.assertEqual(json.loads(raw), capabilities)

    def test_runtime_portal_refresh_failure_falls_back_to_fixed_portal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portal = root / self.module.PKG_REL / self.module.PORTAL_NAME
            portal.parent.mkdir(parents=True)
            portal.write_text("fixed", encoding="utf-8")
            build = root / "scripts/build_business_tier_a_package.py"
            build.parent.mkdir(parents=True)
            build.write_text("# test\n", encoding="utf-8")
            failed = subprocess.CompletedProcess(["python", str(build)], 1)
            with mock.patch.object(self.module, "run", return_value=failed):
                self.assertEqual(
                    self.module.ensure_package(root, {"video_full": False}),
                    portal,
                )

    def test_required_capability_failure_stops_with_missing_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            probe = root / "scripts/probe_production_env.py"
            probe.parent.mkdir(parents=True)
            probe.write_text("# test\n", encoding="utf-8")
            report = {
                "ok": False,
                "capabilities": {"video_full": False},
                "missing_capabilities": ["video_full"],
                "messages_zh": ["缺少正式旁白环境。"],
            }
            failed = subprocess.CompletedProcess(
                ["python", str(probe)],
                2,
                stdout=json.dumps(report, ensure_ascii=False),
                stderr="",
            )
            with mock.patch.object(self.module.subprocess, "run", return_value=failed) as run:
                with self.assertRaisesRegex(SystemExit, "video_full"):
                    self.module.probe_environment(root, ["video-full"])
            command = run.call_args.args[0]
            self.assertEqual(command[-2:], ["--require", "video-full"])


class ProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_script("probe_production_env")

    def test_explicit_requirement_controls_top_level_status(self) -> None:
        report = {
            "ok": True,
            "capabilities": {"video_full": False, "video_plan": True},
        }
        result = self.module.apply_requirements(report, ["video-full"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["missing_capabilities"], ["video_full"])

    def test_production_assets_requirement_maps_to_private_capability(self) -> None:
        report = {
            "ok": True,
            "capabilities": {"private_production_assets": False},
        }
        result = self.module.apply_requirements(report, ["production-assets"])
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["missing_capabilities"], ["private_production_assets"]
        )

    def test_missing_private_marker_disables_every_production_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            with mock.patch.object(self.module, "ROOT", root):
                report = self.module.probe()
        self.assertFalse(report["capabilities"]["private_production_assets"])
        self.assertTrue(report["capabilities"])
        self.assertTrue(all(not value for value in report["capabilities"].values()))

    def test_wrong_origin_disables_private_production_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / self.module.PRIVATE_MARKER_REL
            marker.parent.mkdir(parents=True)
            marker.write_text(
                json.dumps(
                    {
                        "kind": self.module.PRIVATE_MARKER_KIND,
                        "version": 1,
                        "repository_url": self.module.PRIVATE_REPO_URL,
                        "production_assets": True,
                    }
                ),
                encoding="utf-8",
            )
            with (
                mock.patch.object(self.module, "ROOT", root),
                mock.patch.object(
                    self.module,
                    "git_origin_url",
                    return_value="https://github.com/lmr1123/chain-pharmacy-content-studio.git",
                ),
            ):
                report = self.module.probe()
        self.assertFalse(report["capabilities"]["private_production_assets"])
        self.assertTrue(
            any("origin" in message for message in report["messages_zh"])
        )

    def test_official_ssh_origin_enables_private_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / self.module.PRIVATE_MARKER_REL
            marker.parent.mkdir(parents=True)
            marker.write_text(
                json.dumps(
                    {
                        "kind": self.module.PRIVATE_MARKER_KIND,
                        "version": 1,
                        "repository_url": self.module.PRIVATE_REPO_URL,
                        "production_assets": True,
                    }
                ),
                encoding="utf-8",
            )
            for relative in self.module.PRIVATE_ASSET_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("asset fact\n", encoding="utf-8")
            with mock.patch.object(
                self.module,
                "git_origin_url",
                return_value=(
                    "ssh://git@github.com/lmr1123/"
                    "chain-pharmacy-content-studio-private.git"
                ),
            ):
                status = self.module.private_production_status(root)
        self.assertTrue(status["ready"])

    def test_private_assets_require_marker_origin_and_fixed_asset_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / self.module.PRIVATE_MARKER_REL
            marker.parent.mkdir(parents=True)
            marker.write_text(
                json.dumps(
                    {
                        "kind": self.module.PRIVATE_MARKER_KIND,
                        "version": 1,
                        "repository_url": self.module.PRIVATE_REPO_URL,
                        "production_assets": True,
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                self.module,
                "git_origin_url",
                return_value=self.module.PRIVATE_REPO_URL,
            ):
                incomplete = self.module.private_production_status(root)
                self.assertFalse(incomplete["ready"])
                self.assertEqual(incomplete["reason"], "missing_assets")

                for relative in self.module.PRIVATE_ASSET_PATHS:
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("asset fact\n", encoding="utf-8")
                complete = self.module.private_production_status(root)
        self.assertTrue(complete["ready"])
        self.assertEqual(complete["missing_paths"], [])

    def test_probe_records_key_tool_versions(self) -> None:
        report = self.module.probe()
        self.assertIn("versions", report)
        self.assertTrue(report["versions"]["python"])
        for key in ("git", "node", "npm", "ffmpeg", "ffprobe", "tts_python"):
            self.assertIn(key, report["versions"])

    def test_full_renderers_use_the_same_resolved_media_tools_as_probe(self) -> None:
        report = self.module.probe()
        product = load_script("business_video_product_full")
        health = load_script("business_video_health_full")
        for name in ("ffmpeg", "ffprobe"):
            expected = report["tools"][name]
            self.assertEqual(product.media_tool(name), expected)
            self.assertEqual(health.media_tool(name), expected)
        for script_name in (
            "render-product-segment.mjs",
            "render-health-segment.mjs",
        ):
            # Formal production engine entry first; legacy kit remains content source.
            candidates = [
                ROOT
                / "production-library"
                / "engines"
                / "video-revideo-runtime-v1"
                / "scripts"
                / script_name,
                ROOT / "poc" / "gold-sample" / "scripts" / script_name,
            ]
            path = next(p for p in candidates if p.is_file())
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("/opt/homebrew/bin/ffmpeg", source)
            self.assertNotIn("/opt/homebrew/bin/ffprobe", source)

    def test_voice_pack_requires_manifest_audio_and_reference_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "voice-pack.json").write_text(
                json.dumps(
                    {
                        "id": "voice.test",
                        "prompt": {"audio": "prompt.wav", "ref_text": "审核参考文本"},
                    }
                ),
                encoding="utf-8",
            )
            self.assertFalse(self.module.voice_pack_ready(pack))
            (pack / "prompt.wav").write_bytes(b"wave")
            self.assertTrue(self.module.voice_pack_ready(pack))


class BusinessPackageRebuildTests(unittest.TestCase):
    MODE_FILES = {
        "08_数字人侧讲模式": (
            "README.md",
            "业务复核包-模板.md",
            "代理执行清单.md",
            "口令卡.md",
        ),
        "09_健康科普Seedance模式": (
            "README.md",
            "业务复核包-模板.md",
            "代理执行清单.md",
            "口令卡.md",
        ),
        "10_健康科普九宫格模式": (
            "README.md",
            "业务复核包-模板.md",
            "代理执行清单.md",
            "口令卡.md",
        ),
        "11_健康科普九宫格合规版": (
            "README.md",
            "代理执行清单.md",
            "口令卡.md",
        ),
    }

    def test_incomplete_mode_stops_before_generated_files_are_removed(self) -> None:
        module = load_script("build_business_tier_a_package")
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / module.PKG_NAME
            static_package = Path(tmp) / "business-package-static"
            for mode, filenames in self.MODE_FILES.items():
                for filename in filenames:
                    if mode == "08_数字人侧讲模式" and filename == "口令卡.md":
                        continue
                    path = static_package / mode / filename
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("fixed\n", encoding="utf-8")
            generated = package / "README.md"
            generated.parent.mkdir(parents=True, exist_ok=True)
            generated.write_text("must remain on validation failure\n", encoding="utf-8")
            with (
                mock.patch.object(module, "PKG", package),
                mock.patch.object(module, "STATIC_PACKAGE", static_package),
            ):
                with self.assertRaisesRegex(SystemExit, "08_数字人侧讲模式/口令卡.md"):
                    module.prepare_package_directory()
            self.assertTrue(generated.is_file())

    def test_rebuild_is_repeatable_preserves_modes_and_excludes_private_payloads(self) -> None:
        module = load_script("build_business_tier_a_package")
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            settled = repo / "production-library/templates/settled"
            static_package = repo / "production-library/business-package-static"
            out_root = repo / "outputs/业务使用资料包"
            package = out_root / module.PKG_NAME
            settled.mkdir(parents=True)
            package.mkdir(parents=True)
            (settled / "business-catalog.json").write_text(
                json.dumps({"templates": []}, ensure_ascii=False), encoding="utf-8"
            )

            for mode, filenames in self.MODE_FILES.items():
                for filename in filenames:
                    path = static_package / mode / filename
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(f"{mode}/{filename}\n", encoding="utf-8")

            minimal_mp4 = (
                b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2"
                b"\x00\x00\x00\x08moov\x00\x00\x00\x08mdat"
            )
            for filename in (
                "seedance-meta-prompt-example.mp4",
                "digital-human-presenter-example.mp4",
            ):
                portal_example = static_package / "media/production-modes" / filename
                portal_example.parent.mkdir(parents=True, exist_ok=True)
                portal_example.write_bytes(minimal_mp4)

            private_files = (
                package / "05_交付物放这里/job/final.mp4",
                package / "07_业务填报上传/待处理/业务资料.docx",
                package / "07_业务填报上传/已提交/业务资料.docx",
            )
            for path in private_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"private")
            runtime_portal = package / module.RUNTIME_PORTAL_NAME
            runtime_portal.write_text("stale machine state", encoding="utf-8")

            with (
                mock.patch.object(module, "REPO", repo),
                mock.patch.object(module, "SETTLED", settled),
                mock.patch.object(module, "STATIC_PACKAGE", static_package),
                mock.patch.object(module, "OUT_ROOT", out_root),
                mock.patch.object(module, "PKG", package),
                mock.patch.object(
                    module,
                    "build_guided_portal_html",
                    wraps=module.build_guided_portal_html,
                ) as portal_builder,
            ):
                capabilities = {"pptx_export": True, "video_full": False}
                module.main(runtime_capabilities=capabilities)
                zip_path = out_root / f"{module.PKG_NAME}.zip"
                first_zip_bytes = zip_path.read_bytes()
                static_readme = static_package / "08_数字人侧讲模式/README.md"
                static_readme.chmod(0o600)
                os.utime(static_readme, (1_000_000_000, 1_000_000_000))
                module.main(runtime_capabilities=capabilities)

            runtime_calls = [
                call.kwargs.get("runtime_capabilities")
                for call in portal_builder.call_args_list
            ]
            self.assertIn(None, runtime_calls)
            self.assertIn(capabilities, runtime_calls)
            self.assertTrue(runtime_portal.is_file())

            for mode, filenames in self.MODE_FILES.items():
                for filename in filenames:
                    self.assertTrue((package / mode / filename).is_file(), f"{mode}/{filename}")
            for path in private_files:
                self.assertTrue(path.is_file(), str(path))

            with ZipFile(zip_path) as zf:
                entries = zf.infolist()
                ordered_names = [entry.filename for entry in entries]
                names = set(ordered_names)
            self.assertEqual(first_zip_bytes, zip_path.read_bytes())
            self.assertEqual(ordered_names, sorted(ordered_names))
            self.assertTrue(entries)
            for entry in entries:
                self.assertEqual(entry.date_time, module.REPRODUCIBLE_ZIP_TIMESTAMP)
                self.assertEqual(entry.create_system, 3)
                self.assertEqual((entry.external_attr >> 16) & 0o777, 0o644)
                self.assertFalse(entry.is_dir())
            for mode, filenames in self.MODE_FILES.items():
                for filename in filenames:
                    expected = f"{module.PKG_NAME}/{mode}/{filename}"
                    self.assertIn(expected, names)
            for path in private_files:
                self.assertNotIn(str(path.relative_to(out_root)), names)
            self.assertNotIn(str(runtime_portal.relative_to(out_root)), names)
            self.assertIn(
                f"{module.PKG_NAME}/05_交付物放这里/README.md", names
            )


if __name__ == "__main__":
    unittest.main()
