#!/usr/bin/env python3
"""Focused tests for the Public installer's read-only device authorization path."""

from __future__ import annotations

import base64
import binascii
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
INSTALLER = ROOT / "public-entry/scripts/install_private_studio.py"
KEY_BLOB = b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20" + (b"k" * 32)
KEY_B64 = base64.b64encode(KEY_BLOB).decode("ascii")
PUBLIC_KEY = f"ssh-ed25519 {KEY_B64} workbuddy-business-device"
PRIVATE_MARKER = "PRIVATE-KEY-MATERIAL-MUST-NOT-BE-PRINTED"
EXPECTED_GITHUB_KNOWN_HOST = (
    "[ssh.github.com]:443 ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n"
)


def load_installer():
    spec = importlib.util.spec_from_file_location("public_device_install", INSTALLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


class PublicDeviceInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_installer()

    @staticmethod
    def completed(command, code=0, stdout="", stderr=""):
        return subprocess.CompletedProcess(command, code, stdout=stdout, stderr=stderr)

    def write_device_key(self, config_dir: Path) -> Path:
        config_dir.mkdir(parents=True)
        private_key = config_dir / self.module.DEVICE_KEY_NAME
        private_key.write_text(PRIVATE_MARKER, encoding="utf-8")
        private_key.chmod(0o600)
        private_key.with_suffix(".pub").write_text(PUBLIC_KEY + "\n", encoding="utf-8")
        return private_key

    def keygen_result(self, command):
        command = [str(item) for item in command]
        if command[:2] == ["ssh-keygen", "-y"]:
            return self.completed(command, stdout=f"ssh-ed25519 {KEY_B64}\n")
        if command and command[0] == "ssh-keygen" and "-t" in command:
            private_key = Path(command[command.index("-f") + 1])
            private_key.parent.mkdir(parents=True, exist_ok=True)
            private_key.write_text(PRIVATE_MARKER, encoding="utf-8")
            private_key.with_suffix(".pub").write_text(
                PUBLIC_KEY + "\n", encoding="utf-8"
            )
            return self.completed(command)
        return None

    def test_gh_checks_never_inherit_environment_tokens(self) -> None:
        captured: dict[str, str] = {}

        def fake_run(command, **kwargs):
            captured.update(kwargs["env"])
            return self.completed(command)

        with (
            mock.patch.dict(
                os.environ,
                {"GH_TOKEN": "owner-token", "GITHUB_TOKEN": "service-token"},
            ),
            mock.patch.object(self.module.subprocess, "run", side_effect=fake_run),
        ):
            self.module._gh(["gh", "auth", "status"])

        self.assertNotIn("GH_TOKEN", captured)
        self.assertNotIn("GITHUB_TOKEN", captured)
        self.assertEqual(captured.get("GH_HOST"), "github.com")

    def test_device_commands_isolate_git_config_and_ssh_agent(self) -> None:
        captured: dict[str, str] = {}

        def fake_run(command, **kwargs):
            captured.update(kwargs["env"])
            return self.completed(command)

        hostile_env = {
            "GH_TOKEN": "owner-token",
            "GITHUB_TOKEN": "service-token",
            "SSH_AUTH_SOCK": "/tmp/untrusted-agent.sock",
            "SSH_AGENT_PID": "999",
            "GIT_SSH": "/tmp/untrusted-ssh",
            "GIT_SSH_COMMAND": "ssh -i /tmp/untrusted-key",
            "GIT_ASKPASS": "/tmp/untrusted-askpass",
            "SSH_ASKPASS": "/tmp/untrusted-askpass",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.sshCommand",
            "GIT_CONFIG_VALUE_0": "ssh -i /tmp/untrusted-key",
        }
        with (
            mock.patch.dict(os.environ, hostile_env),
            mock.patch.object(self.module.subprocess, "run", side_effect=fake_run),
        ):
            self.module._device_run(["git", "status"])

        self.assertEqual(captured.get("GIT_CONFIG_NOSYSTEM"), "1")
        self.assertEqual(captured.get("GIT_CONFIG_GLOBAL"), os.devnull)
        for key in (
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "SSH_AUTH_SOCK",
            "SSH_AGENT_PID",
            "GIT_SSH",
            "GIT_SSH_COMMAND",
            "GIT_ASKPASS",
            "SSH_ASKPASS",
            "GIT_CONFIG_COUNT",
            "GIT_CONFIG_KEY_0",
            "GIT_CONFIG_VALUE_0",
        ):
            self.assertNotIn(key, captured)

    def test_public_key_decoder_uses_explicit_binascii_module(self) -> None:
        self.assertIs(self.module.binascii.Error, binascii.Error)

    def test_pending_prompt_is_nontechnical_and_does_not_echo_key_material(self) -> None:
        request = self.module._device_key_request(PUBLIC_KEY)
        self.assertIsNotNone(request)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            self.module._emit_device_request(request)

        prompt = stderr.getvalue()
        self.assertIn("请把下面整段设备授权申请转给管理员", prompt)
        for technical_word in ("token", "ssh", "deploy key", "private key"):
            self.assertNotIn(technical_word, prompt.lower())
        self.assertNotIn(PRIVATE_MARKER, stdout.getvalue() + prompt)
        self.assertNotIn(request["public_key"], prompt)
        self.assertIn(request["public_key"], stdout.getvalue())

    def test_logged_in_without_repo_access_and_no_key_generates_request_then_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "production"
            config_dir = root / "device-config"
            calls: list[list[str]] = []

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                calls.append(command)
                # Default public HTTPS path fails first in these device-fallback tests.
                if (
                    command
                    and command[0] == "git"
                    and "clone" in command
                    and self.module.PRODUCTION_HTTPS_ORIGIN in command
                ):
                    return self.completed(command, 1, stderr="https blocked")
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(command, 1, stderr="not authorized")
                generated = self.keygen_result(command)
                if generated is not None:
                    return generated
                raise AssertionError(f"unexpected command: {command}")

            output = io.StringIO()
            with (
                mock.patch.object(self.module.subprocess, "run", side_effect=fake_run),
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(output),
            ):
                result = self.module.install(target, device_config_dir=config_dir)

            self.assertEqual(result, self.module.DEVICE_ACCESS_PENDING_EXIT)
            self.assertFalse(target.exists())
            private_key = config_dir / self.module.DEVICE_KEY_NAME
            self.assertTrue(private_key.is_file())
            self.assertEqual(private_key.stat().st_mode & 0o777, 0o600)
            lines = output.getvalue().splitlines()
            request = json.loads(next(line for line in lines if line.startswith("{")))
            digest = hashlib.sha256(KEY_BLOB).digest()
            expected = {
                "schema_version": "workbuddy-business-device-access-request/v1",
                "repository": self.module.PRIVATE_REPOSITORY,
                "device_id": f"wb-{hashlib.sha256(KEY_BLOB).hexdigest()[:16]}",
                "device_label": (
                    f"业务设备 wb-{hashlib.sha256(KEY_BLOB).hexdigest()[:16]}"
                ),
                "public_key": PUBLIC_KEY,
                "fingerprint": (
                    "SHA256:"
                    + base64.b64encode(digest).decode("ascii").rstrip("=")
                ),
            }
            self.assertEqual(request, expected)
            self.assertIn("WB_INSTALL_STATE=device_access_pending", lines)
            self.assertNotIn(PRIVATE_MARKER, output.getvalue())
            self.assertNotIn(str(private_key), output.getvalue())
            self.assertFalse(
                any(
                    call
                    and call[0] == "git"
                    and "clone" in call
                    and self.module.DEVICE_SSH_ORIGIN in call
                    for call in calls
                )
            )

    def test_existing_unapproved_key_reprints_request_without_cloning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "production"
            config_dir = root / "device-config"
            self.write_device_key(config_dir)
            calls: list[list[str]] = []

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                calls.append(command)
                if (
                    command
                    and command[0] == "git"
                    and "clone" in command
                    and self.module.PRODUCTION_HTTPS_ORIGIN in command
                ):
                    return self.completed(command, 1, stderr="https blocked")
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command, 1)
                generated = self.keygen_result(command)
                if generated is not None:
                    return generated
                if command and command[0] == "git" and "ls-remote" in command:
                    return self.completed(command, 128, stderr="Repository not found")
                raise AssertionError(f"unexpected command: {command}")

            output = io.StringIO()
            with (
                mock.patch.object(self.module.subprocess, "run", side_effect=fake_run),
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(output),
            ):
                result = self.module.install(target, device_config_dir=config_dir)

            self.assertEqual(result, self.module.DEVICE_ACCESS_PENDING_EXIT)
            self.assertFalse(target.exists())
            self.assertIn("WB_INSTALL_STATE=device_access_pending", output.getvalue())
            self.assertNotIn(PRIVATE_MARKER, output.getvalue())
            flattened = " ".join(part for call in calls for part in call)
            self.assertIn("StrictHostKeyChecking=yes", flattened)
            self.assertIn("HostKeyAlgorithms=ssh-ed25519", flattened)
            self.assertIn("Hostname=ssh.github.com", flattened)
            self.assertIn("Port=443", flattened)
            self.assertNotIn("StrictHostKeyChecking=accept-new", flattened)
            self.assertNotIn("StrictHostKeyChecking=no", flattened)
            self.assertFalse(
                any(
                    call
                    and call[0] == "git"
                    and "clone" in call
                    and self.module.DEVICE_SSH_ORIGIN in call
                    for call in calls
                )
            )

    def test_logged_in_without_repo_access_falls_back_to_approved_device_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "production"
            config_dir = root / "device-config"
            private_key = self.write_device_key(config_dir)
            calls: list[list[str]] = []

            def fake_run(command, **_kwargs):
                command = [str(item) for item in command]
                calls.append(command)
                if (
                    command
                    and command[0] == "git"
                    and "clone" in command
                    and self.module.PRODUCTION_HTTPS_ORIGIN in command
                ):
                    return self.completed(command, 1, stderr="https blocked")
                if command[:3] == ["gh", "auth", "status"]:
                    return self.completed(command)
                if command[:3] == ["gh", "repo", "view"]:
                    return self.completed(command, 1, stderr="not authorized")
                generated = self.keygen_result(command)
                if generated is not None:
                    return generated
                if command and command[0] == "git" and "ls-remote" in command:
                    return self.completed(command, stdout="abc123\tHEAD\n")
                if command and command[0] == "git" and "clone" in command:
                    clone_root = Path(command[-1])
                    (clone_root / ".git").mkdir(parents=True)
                    bootstrap = clone_root / "scripts/workbuddy_bootstrap_for_business.py"
                    bootstrap.parent.mkdir(parents=True)
                    bootstrap.write_text("# private\n", encoding="utf-8")
                    return self.completed(command)
                if command[:2] == ["git", "-C"] and "remote" in command:
                    return self.completed(command, stdout=self.module.DEVICE_SSH_ORIGIN + "\n")
                if command[:2] == ["git", "-C"] and "config" in command:
                    return self.completed(command)
                if command and Path(command[0]).resolve() == Path(sys.executable).resolve():
                    return self.completed(command)
                raise AssertionError(f"unexpected command: {command}")

            with mock.patch.object(
                self.module.subprocess, "run", side_effect=fake_run
            ):
                result = self.module.install(
                    target, no_open=True, device_config_dir=config_dir
                )

            self.assertEqual(result, 0)
            self.assertTrue((target / ".git").is_dir())
            clone_call = next(
                call
                for call in calls
                if call
                and call[0] == "git"
                and "clone" in call
                and self.module.DEVICE_SSH_ORIGIN in call
            )
            self.assertIn(self.module.DEVICE_SSH_ORIGIN, clone_call)
            self.assertTrue(self.module.DEVICE_SSH_ORIGIN.startswith("ssh://git@ssh.github.com:443/"))
            self.assertFalse(any(call[:3] == ["gh", "repo", "clone"] for call in calls))
            config_call = next(
                call
                for call in calls
                if call[:2] == ["git", "-C"]
                and "config" in call
                and "core.sshCommand" in call
            )
            ssh_command = config_call[-1]
            self.assertIn(str(private_key.resolve()), ssh_command)
            self.assertIn("IdentitiesOnly=yes", ssh_command)
            self.assertIn("StrictHostKeyChecking=yes", ssh_command)
            self.assertIn("HostKeyAlgorithms=ssh-ed25519", ssh_command)
            self.assertIn("Hostname=ssh.github.com", ssh_command)
            self.assertIn("Port=443", ssh_command)
            self.assertNotIn("StrictHostKeyChecking=accept-new", ssh_command)
            self.assertNotIn("StrictHostKeyChecking=no", ssh_command)
            self.assertEqual(
                (config_dir / "github_known_hosts").read_text(encoding="utf-8"),
                EXPECTED_GITHUB_KNOWN_HOST,
            )
            self.assertEqual(self.module.GITHUB_ED25519_KNOWN_HOST, EXPECTED_GITHUB_KNOWN_HOST)
            self.assertIn("--skip-update", calls[-1])

    def test_existing_checkout_updates_without_device_key_when_public(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "production"
            config_dir = root / "device-config"
            self.write_device_key(config_dir)
            (target / ".git").mkdir(parents=True)
            bootstrap = target / "scripts/workbuddy_bootstrap_for_business.py"
            bootstrap.parent.mkdir(parents=True)
            bootstrap.write_text("# production\n", encoding="utf-8")
            calls: list[tuple[list[str], dict[str, object]]] = []

            def fake_run(command, **kwargs):
                command = [str(item) for item in command]
                calls.append((command, dict(kwargs)))
                if command[:2] == ["git", "-C"] and command[3:6] == [
                    "remote",
                    "get-url",
                    "origin",
                ]:
                    return self.completed(
                        command,
                        stdout=self.module.PRODUCTION_HTTPS_ORIGIN + "\n",
                    )
                if command and Path(command[0]).resolve() == Path(sys.executable).resolve():
                    return self.completed(command)
                raise AssertionError(f"unexpected command: {command}")

            with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                result = self.module.install(
                    target, no_open=True, device_config_dir=config_dir
                )

            self.assertEqual(result, 0)
            commands = [command for command, _kwargs in calls]
            self.assertFalse(
                any(
                    command[:2] == ["git", "-C"] and "core.sshCommand" in command
                    for command in commands
                )
            )
            self.assertFalse(
                any(command[:2] == ["git", "-C"] and "set-url" in command for command in commands)
            )
            bootstrap_call, bootstrap_kwargs = next(
                (command, kwargs)
                for command, kwargs in calls
                if command and Path(command[0]).resolve() == Path(sys.executable).resolve()
            )
            self.assertNotIn("--skip-update", bootstrap_call)
            bootstrap_env = bootstrap_kwargs["env"]
            # Public default path hands off without device SSH injection.
            self.assertNotIn("GIT_SSH_COMMAND", bootstrap_env)
            self.assertNotIn("GH_TOKEN", bootstrap_env)
            self.assertNotIn("GITHUB_TOKEN", bootstrap_env)


if __name__ == "__main__":
    unittest.main()
