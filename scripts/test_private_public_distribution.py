#!/usr/bin/env python3
"""Tests for the sanitized Public installer distribution boundary."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


class PublicExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_path(
            "export_public_installer", ROOT / "scripts/export_public_installer.py"
        )

    @staticmethod
    def write_policy(path: Path, allowed: list[str], *, max_file_bytes: int = 4096) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "default_action": "deny",
                    "source_root": "public-entry",
                    "public_repository": "lmr1123/chain-pharmacy-content-studio",
                    "private_repository": (
                        "lmr1123/chain-pharmacy-content-studio-private"
                    ),
                    "history_policy": "new-repository-only",
                    "allowed_source_paths": allowed,
                    "generated_paths": ["SHA256SUMS.json"],
                    "max_file_bytes": max_file_bytes,
                    "max_total_bytes": max_file_bytes * max(1, len(allowed)),
                }
            ),
            encoding="utf-8",
        )

    def test_export_is_default_deny_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "README.md").write_text("public\n", encoding="utf-8")
            (source / "install.py").write_text("print('ok')\n", encoding="utf-8")
            policy = root / "policy.json"
            self.write_policy(policy, ["README.md", "install.py"])
            out_a = root / "out-a"
            out_b = root / "out-b"

            self.module.export_public_installer(source, out_a, policy)
            self.module.export_public_installer(source, out_b, policy)

            files_a = {
                path.relative_to(out_a).as_posix(): path.read_bytes()
                for path in out_a.rglob("*")
                if path.is_file()
            }
            files_b = {
                path.relative_to(out_b).as_posix(): path.read_bytes()
                for path in out_b.rglob("*")
                if path.is_file()
            }
            self.assertEqual(files_a, files_b)
            manifest = json.loads(files_a["SHA256SUMS.json"])
            self.assertEqual(
                [item["path"] for item in manifest["files"]],
                ["README.md", "install.py"],
            )
            for item in manifest["files"]:
                self.assertEqual(
                    item["sha256"], hashlib.sha256(files_a[item["path"]]).hexdigest()
                )

            cache = source / "__pycache__"
            cache.mkdir()
            (cache / "ignored.pyc").write_bytes(b"local bytecode cache")
            self.module.export_public_installer(source, root / "out-cache", policy)

            (source / "not-allowlisted.txt").write_text("no\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "not allowlisted"):
                self.module.export_public_installer(source, root / "rejected", policy)

    def test_export_rejects_dangerous_content(self) -> None:
        cases = {
            "media.mp4": b"video",
            "office.docx": b"office",
            "archive.zip": b"archive",
            "image.png": b"image",
            "font.woff2": b"font",
            "disguised.md": b"PK\x03\x04archive",
            ".env": b"SAFE_NAME=value",
            "secret.txt": b"github_pat_1234567890abcdefghijklmnop",
        }
        for name, payload in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = root / "source"
                source.mkdir()
                (source / name).write_bytes(payload)
                policy = root / "policy.json"
                self.write_policy(policy, [name])
                with self.assertRaises(SystemExit):
                    self.module.export_public_installer(source, root / "out", policy)

    def test_export_rejects_symlink_and_oversized_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            (source / "link.txt").symlink_to(outside)
            policy = root / "policy.json"
            self.write_policy(policy, ["link.txt"])
            with self.assertRaisesRegex(SystemExit, "symlink"):
                self.module.export_public_installer(source, root / "out-link", policy)

            (source / "link.txt").unlink()
            (source / "large.md").write_bytes(b"x" * 65)
            self.write_policy(policy, ["large.md"], max_file_bytes=64)
            with self.assertRaisesRegex(SystemExit, "too large"):
                self.module.export_public_installer(source, root / "out-large", policy)


class PublicInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_path(
            "public_install",
            ROOT / "public-entry/scripts/install_private_studio.py",
        )

    @staticmethod
    def completed(cmd: list[str], code: int = 0, stdout: str = "", stderr: str = ""):
        return subprocess.CompletedProcess(cmd, code, stdout=stdout, stderr=stderr)

    def test_authorized_clone_is_atomic_official_and_hands_off_without_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "production"
            calls: list[list[str]] = []
            gh_environments: list[dict[str, str]] = []

            def fake_run(command, **kwargs):
                command = [str(item) for item in command]
                calls.append(command)
                if command and command[0] == "gh":
                    gh_environments.append(kwargs["env"])
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(
                        command,
                        stdout=json.dumps(
                            {
                                "nameWithOwner": self.module.PRIVATE_REPOSITORY,
                                "visibility": "PRIVATE",
                            }
                        ),
                    )
                if command[:3] == ["gh", "repo", "clone"]:
                    clone_root = Path(command[4])
                    (clone_root / ".git").mkdir(parents=True)
                    bootstrap = clone_root / "scripts/workbuddy_bootstrap_for_business.py"
                    bootstrap.parent.mkdir(parents=True)
                    bootstrap.write_text("# private\n", encoding="utf-8")
                    return self.completed(command)
                if command[:2] == ["git", "-C"]:
                    return self.completed(
                        command,
                        stdout=(
                            "git@github.com:lmr1123/"
                            "chain-pharmacy-content-studio-private.git\n"
                        ),
                    )
                return self.completed(command)

            with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                result = self.module.install(target)

            self.assertEqual(result, 0)
            self.assertTrue((target / ".git").is_dir())
            clone_call = next(call for call in calls if call[:3] == ["gh", "repo", "clone"])
            self.assertEqual(clone_call[3], self.module.PRIVATE_REPOSITORY)
            self.assertEqual(
                Path(clone_call[4]).parent.parent.resolve(), target.parent.resolve()
            )
            self.assertFalse(any("proxy" in part.lower() for part in clone_call))
            self.assertIn("http.version=HTTP/1.1", clone_call)
            self.assertIn("--single-branch", clone_call)
            self.assertIn("--no-tags", clone_call)
            self.assertTrue(any(call[:2] == ["git", "-C"] for call in calls))
            self.assertTrue(gh_environments)
            self.assertTrue(
                all(environment.get("GH_HOST") == "github.com" for environment in gh_environments)
            )
            handoff = calls[-1]
            self.assertIn("--skip-update", handoff)
            self.assertEqual(
                Path(handoff[1]).resolve(),
                (target / "scripts/workbuddy_bootstrap_for_business.py").resolve(),
            )
            target_index = handoff.index("--target") + 1
            self.assertEqual(Path(handoff[target_index]).resolve(), target.resolve())
            leftovers = list(target.parent.glob(f".{target.name}.install-*"))
            self.assertEqual(leftovers, [])

    def test_interrupted_clone_retries_once_from_clean_official_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "production"
            clone_calls: list[list[str]] = []

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(
                        command,
                        stdout=json.dumps(
                            {
                                "nameWithOwner": self.module.PRIVATE_REPOSITORY,
                                "visibility": "PRIVATE",
                            }
                        ),
                    )
                if command[:3] == ["gh", "repo", "clone"]:
                    clone_calls.append(command)
                    clone_root = Path(command[4])
                    if len(clone_calls) == 1:
                        clone_root.mkdir(parents=True)
                        (clone_root / "partial").write_text(
                            "interrupted", encoding="utf-8"
                        )
                        return self.completed(command, 1, stderr="early EOF")
                    self.assertFalse((clone_root / "partial").exists())
                    (clone_root / ".git").mkdir(parents=True)
                    bootstrap = clone_root / "scripts/workbuddy_bootstrap_for_business.py"
                    bootstrap.parent.mkdir(parents=True)
                    bootstrap.write_text("# private\n", encoding="utf-8")
                    return self.completed(command)
                if command[:2] == ["git", "-C"]:
                    return self.completed(
                        command,
                        stdout=(
                            "https://github.com/lmr1123/"
                            "chain-pharmacy-content-studio-private.git\n"
                        ),
                    )
                return self.completed(command)

            with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                result = self.module.install(target, no_open=True)

            self.assertEqual(result, 0)
            self.assertEqual(len(clone_calls), 2)
            self.assertTrue((target / ".git").is_dir())
            self.assertEqual(list(target.parent.glob(f".{target.name}.install-*")), [])

    def test_auth_or_access_failure_leaves_no_partial_target_and_redacts_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "production"
            secret = "ghp_1234567890abcdefghijklmnopqrstuv"
            failed = self.completed(["gh"], 1, stderr=f"token={secret}")
            output = io.StringIO()
            with (
                mock.patch.object(self.module.subprocess, "run", return_value=failed),
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(output),
            ):
                result = self.module.install(target)
            self.assertNotEqual(result, 0)
            self.assertFalse(target.exists())
            self.assertEqual(list(target.parent.glob(f".{target.name}.install-*")), [])
            self.assertNotIn(secret, output.getvalue())

    def test_authenticated_account_without_private_access_honestly_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "production"
            calls: list[list[str]] = []

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                calls.append(command)
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(command, 1, stderr="not found")
                raise AssertionError("clone must not run without repository access")

            output = io.StringIO()
            with (
                mock.patch.object(self.module.subprocess, "run", side_effect=fake_run),
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(output),
            ):
                result = self.module.install(target)
            self.assertEqual(result, 3)
            self.assertFalse(target.exists())
            self.assertFalse(any(call[:3] == ["gh", "repo", "clone"] for call in calls))
            self.assertIn("没有私有生产仓库权限", output.getvalue())

    def test_failed_clone_removes_atomic_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "production"

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(
                        command,
                        stdout=json.dumps(
                            {
                                "nameWithOwner": self.module.PRIVATE_REPOSITORY,
                                "visibility": "PRIVATE",
                            }
                        ),
                    )
                if command[:3] == ["gh", "repo", "clone"]:
                    clone_root = Path(str(command[4]))
                    clone_root.mkdir(parents=True)
                    (clone_root / "partial").write_text("partial", encoding="utf-8")
                    return self.completed(command, 1, stderr="clone failed")
                raise AssertionError(command)

            with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                result = self.module.install(target)
            self.assertNotEqual(result, 0)
            self.assertFalse(target.exists())
            self.assertEqual(list(target.parent.glob(f".{target.name}.install-*")), [])

    def test_proxy_origin_is_rejected_even_after_successful_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "production"

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(
                        command,
                        stdout=json.dumps(
                            {
                                "nameWithOwner": self.module.PRIVATE_REPOSITORY,
                                "visibility": "PRIVATE",
                            }
                        ),
                    )
                if command[:3] == ["gh", "repo", "clone"]:
                    clone_root = Path(command[4])
                    (clone_root / ".git").mkdir(parents=True)
                    bootstrap = clone_root / "scripts/workbuddy_bootstrap_for_business.py"
                    bootstrap.parent.mkdir(parents=True)
                    bootstrap.write_text("# private\n", encoding="utf-8")
                    return self.completed(command)
                if command[:2] == ["git", "-C"]:
                    return self.completed(
                        command,
                        stdout=(
                            "https://ghproxy.example/https://github.com/lmr1123/"
                            "chain-pharmacy-content-studio-private.git\n"
                        ),
                    )
                raise AssertionError(command)

            with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                result = self.module.install(target)
            self.assertEqual(result, 4)
            self.assertFalse(target.exists())
            self.assertEqual(list(target.parent.glob(f".{target.name}.install-*")), [])

    def test_existing_official_checkout_is_handed_to_bootstrap_for_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "production"
            (target / ".git").mkdir(parents=True)
            bootstrap = target / "scripts/workbuddy_bootstrap_for_business.py"
            bootstrap.parent.mkdir(parents=True)
            bootstrap.write_text("# private\n", encoding="utf-8")
            calls: list[list[str]] = []

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                calls.append(command)
                if command[:2] == ["git", "-C"]:
                    return self.completed(
                        command,
                        stdout=(
                            "https://github.com/lmr1123/"
                            "chain-pharmacy-content-studio-private.git\n"
                        ),
                    )
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(
                        command,
                        stdout=json.dumps(
                            {
                                "nameWithOwner": self.module.PRIVATE_REPOSITORY,
                                "visibility": "PRIVATE",
                            }
                        ),
                    )
                return self.completed(command)

            with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                result = self.module.install(target, no_open=True)

            self.assertEqual(result, 0)
            self.assertFalse(any(call[:3] == ["gh", "repo", "clone"] for call in calls))
            handoff = calls[-1]
            self.assertNotIn("--skip-update", handoff)
            self.assertIn("--no-open", handoff)
            self.assertEqual(Path(handoff[1]).resolve(), bootstrap.resolve())


class PublicSelfAuditTests(unittest.TestCase):
    def test_exported_tree_self_audits_and_detects_tampering(self) -> None:
        exporter = load_path(
            "export_public_installer_for_audit",
            ROOT / "scripts/export_public_installer.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "public"
            exporter.export_public_installer(
                ROOT / "public-entry",
                out,
                ROOT / "distribution/public-installer-policy.json",
            )
            audit = load_path("public_audit", out / "scripts/audit_public_tree.py")
            self.assertEqual(audit.audit_tree(out), [])
            (out / "README.md").write_text("tampered\n", encoding="utf-8")
            self.assertTrue(audit.audit_tree(out))
            (out / "extra.txt").write_text("not declared\n", encoding="utf-8")
            self.assertTrue(any("unexpected" in item for item in audit.audit_tree(out)))

            payload = (out / "extra.txt").read_bytes()
            manifest_path = out / "SHA256SUMS.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"].append(
                {
                    "path": "extra.txt",
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
            manifest["total_bytes"] += len(payload)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertTrue(
                any("allowlist" in item for item in audit.audit_tree(out)),
                "editing the manifest must not expand the exact Public allowlist",
            )

    def test_public_audit_rejects_forbidden_path_in_git_history(self) -> None:
        exporter = load_path(
            "export_public_installer_for_history",
            ROOT / "scripts/export_public_installer.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "public"
            exporter.export_public_installer(
                ROOT / "public-entry",
                out,
                ROOT / "distribution/public-installer-policy.json",
            )
            def git(*args: str) -> None:
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(out),
                        "-c",
                        "user.name=Public Audit Test",
                        "-c",
                        "user.email=public-audit@example.invalid",
                        *args,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            git("init", "-b", "main")
            git("add", ".")
            git("commit", "-m", "sanitized root")
            clean_audit = load_path(
                "public_audit_clean_history",
                out / "scripts/audit_public_tree.py",
            )
            self.assertEqual(clean_audit.audit_tree(out), [])
            leak = out / "old-assets.zip"
            leak.write_bytes(b"historical leak")
            git("add", "old-assets.zip")
            git("commit", "-m", "bad history")
            leak.unlink()
            git("add", "-u")
            git("commit", "-m", "remove bad path")

            audit = load_path("public_audit_history", out / "scripts/audit_public_tree.py")
            self.assertIn(
                "forbidden historical path: old-assets.zip",
                audit.audit_tree(out),
            )


if __name__ == "__main__":
    unittest.main()
