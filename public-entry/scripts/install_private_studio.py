#!/usr/bin/env python3
"""Compatibility forwarder: install the single production studio repository.

This script lives in the deprecated installer entry repository. Prefer cloning
the production repository directly:

  https://github.com/lmr1123/chain-pharmacy-content-studio-private.git

Default path is anonymous HTTPS clone. No GitHub account is required while
production is public. Device-key / gh paths remain only as fallbacks.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PRIVATE_REPOSITORY = "lmr1123/chain-pharmacy-content-studio-private"
PRODUCTION_HTTPS_ORIGIN = (
    "https://github.com/lmr1123/chain-pharmacy-content-studio-private.git"
)
DEVICE_SSH_ORIGIN = (
    "ssh://git@ssh.github.com:443/lmr1123/chain-pharmacy-content-studio-private.git"
)
DEFAULT_TARGET_NAME = "chain-pharmacy-content-studio-private"
CLONE_ATTEMPTS = 2
DEVICE_KEY_NAME = "workbuddy-business-device"
DEVICE_KEY_COMMENT = "workbuddy-business-device"
DEVICE_REQUEST_SCHEMA = "workbuddy-business-device-access-request/v1"
DEVICE_ACCESS_PENDING_EXIT = 7
DEVICE_KEY_ERROR_EXIT = 8
ALLOWED_VISIBILITIES = frozenset({"PUBLIC", "PRIVATE"})
GITHUB_ED25519_KNOWN_HOST = (
    "[ssh.github.com]:443 ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n"
)
OFFICIAL_ORIGINS = {
    "https://github.com/lmr1123/chain-pharmacy-content-studio-private",
    "https://github.com/lmr1123/chain-pharmacy-content-studio-private.git",
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private",
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private.git",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private.git",
    DEVICE_SSH_ORIGIN,
}


def _gh(
    command: list[str], *, timeout: float = 120
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("GH_TOKEN", None)
    env.pop("GITHUB_TOKEN", None)
    env["GH_HOST"] = "github.com"
    env["GH_PROMPT_DISABLED"] = "1"
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(command, 127, stdout="", stderr="")


def _device_run(
    command: list[str], *, timeout: float = 120
) -> subprocess.CompletedProcess[str]:
    env = _device_environment()
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(command, 127, stdout="", stderr="")


def _device_environment() -> dict[str, str]:
    env = os.environ.copy()
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
    ):
        env.pop(key, None)
    for key in list(env):
        if key.startswith("GIT_CONFIG_KEY_") or key.startswith("GIT_CONFIG_VALUE_"):
            env.pop(key, None)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _default_device_config_dir() -> Path:
    configured = os.environ.get("XDG_CONFIG_HOME")
    if configured:
        base = Path(configured).expanduser()
    elif os.name == "nt" and os.environ.get("APPDATA"):
        base = Path(os.environ["APPDATA"]).expanduser()
    else:
        base = Path.home() / ".config"
    return base / "chain-pharmacy-content-studio" / "device-access"


def _device_key_request(public_text: str) -> dict[str, str] | None:
    lines = public_text.strip().splitlines()
    if len(lines) != 1:
        return None
    parts = lines[0].split()
    if len(parts) < 2 or parts[0] != "ssh-ed25519":
        return None
    try:
        blob = base64.b64decode(parts[1], validate=True)
    except (ValueError, binascii.Error):
        return None
    prefix = b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20"
    if len(blob) != len(prefix) + 32 or not blob.startswith(prefix):
        return None
    digest = hashlib.sha256(blob).digest()
    device_id = f"wb-{hashlib.sha256(blob).hexdigest()[:16]}"
    return {
        "schema_version": DEVICE_REQUEST_SCHEMA,
        "repository": PRIVATE_REPOSITORY,
        "device_id": device_id,
        "device_label": f"业务设备 {device_id}",
        "public_key": f"ssh-ed25519 {parts[1]} {DEVICE_KEY_COMMENT}",
        "fingerprint": "SHA256:"
        + base64.b64encode(digest).decode("ascii").rstrip("="),
    }


def _load_device_key(config_dir: Path) -> tuple[Path, dict[str, str]] | None:
    private_key = config_dir / DEVICE_KEY_NAME
    public_key = private_key.with_suffix(".pub")
    if not private_key.exists() and not public_key.exists():
        return None
    if (
        private_key.is_symlink()
        or public_key.is_symlink()
        or not private_key.is_file()
        or not public_key.is_file()
    ):
        raise ValueError("invalid device key pair")
    private_key.chmod(0o600)
    public_key.chmod(0o644)
    request = _device_key_request(public_key.read_text(encoding="utf-8"))
    if request is None:
        raise ValueError("invalid device public key")
    derived = _device_run(["ssh-keygen", "-y", "-f", str(private_key)])
    derived_request = _device_key_request(
        (derived.stdout.strip() + f" {DEVICE_KEY_COMMENT}") if derived.returncode == 0 else ""
    )
    if derived_request is None or derived_request["public_key"] != request["public_key"]:
        raise ValueError("device key pair mismatch")
    return private_key.resolve(), request


def _exclusive_write(path: Path, payload: bytes, mode: int) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)


def _generate_device_key(config_dir: Path) -> tuple[Path, dict[str, str]] | None:
    with tempfile.TemporaryDirectory(prefix=".workbuddy-device-key-") as tmp:
        generated_key = Path(tmp) / DEVICE_KEY_NAME
        result = _device_run(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                DEVICE_KEY_COMMENT,
                "-f",
                str(generated_key),
            ]
        )
        if result.returncode != 0:
            return None
        generated = _load_device_key(Path(tmp))
        if generated is None:
            return None
        private_payload = generated_key.read_bytes()
        public_payload = generated_key.with_suffix(".pub").read_bytes()

    if config_dir.is_symlink() or (config_dir.exists() and not config_dir.is_dir()):
        raise ValueError("invalid device config directory")
    config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    config_dir.chmod(0o700)
    existing = _load_device_key(config_dir)
    if existing is not None:
        return existing
    private_key = config_dir / DEVICE_KEY_NAME
    public_key = private_key.with_suffix(".pub")
    private_created = False
    try:
        _exclusive_write(private_key, private_payload, 0o600)
        private_created = True
        _exclusive_write(public_key, public_payload, 0o644)
    except FileExistsError:
        if private_created and private_key.exists() and not public_key.exists():
            private_key.unlink()
        return _load_device_key(config_dir)
    except Exception:
        if private_created and private_key.exists() and not public_key.exists():
            private_key.unlink()
        raise
    return _load_device_key(config_dir)


def _emit_device_request(request: dict[str, str]) -> None:
    print(
        "请把下面整段设备授权申请转给管理员；"
        "设备私钥只保留在本机，任何人都不应索取。",
        file=sys.stderr,
    )
    print(json.dumps(request, ensure_ascii=False, sort_keys=True))
    print("WB_INSTALL_STATE=device_access_pending")


def _ensure_pinned_known_hosts(config_dir: Path) -> Path | None:
    known_hosts = config_dir / "github_known_hosts"
    if known_hosts.is_symlink():
        return None
    if known_hosts.exists():
        try:
            if known_hosts.read_text(encoding="utf-8") == GITHUB_ED25519_KNOWN_HOST:
                return known_hosts
            return None
        except OSError:
            return None
    try:
        _exclusive_write(known_hosts, GITHUB_ED25519_KNOWN_HOST.encode("utf-8"), 0o644)
    except FileExistsError:
        return _ensure_pinned_known_hosts(config_dir)
    except OSError:
        return None
    return known_hosts


def _device_ssh_command(private_key: Path, config_dir: Path) -> str | None:
    known_hosts = _ensure_pinned_known_hosts(config_dir)
    if known_hosts is None:
        return None
    parts = [
        "ssh",
        "-i",
        str(private_key),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "Hostname=ssh.github.com",
        "-o",
        "Port=443",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "HostKeyAlgorithms=ssh-ed25519",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
    ]
    return " ".join(shlex.quote(part) for part in parts)


def _device_access_approved(private_key: Path, config_dir: Path) -> bool:
    ssh_command = _device_ssh_command(private_key, config_dir)
    if ssh_command is None:
        return False
    result = _device_run(
        [
            "git",
            "-c",
            f"core.sshCommand={ssh_command}",
            "ls-remote",
            DEVICE_SSH_ORIGIN,
            "HEAD",
        ]
    )
    return result.returncode == 0


def _remove_staging(path: Path) -> None:
    if path.exists() and path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)


def _official_origin(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout.strip() in OFFICIAL_ORIGINS


def _clone_production_https(staging: Path) -> bool:
    """Anonymous official HTTPS clone — default simple path for business."""
    command = [
        "git",
        "-c",
        "http.version=HTTP/1.1",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--no-tags",
        PRODUCTION_HTTPS_ORIGIN,
        str(staging),
    ]
    for attempt in range(CLONE_ATTEMPTS):
        _remove_staging(staging)
        cloned = _device_run(command, timeout=1800)
        bootstrap = staging / "scripts/workbuddy_bootstrap_for_business.py"
        if (
            cloned.returncode == 0
            and (staging / ".git").is_dir()
            and bootstrap.is_file()
            and _official_origin(staging)
        ):
            return True
        if attempt + 1 < CLONE_ATTEMPTS:
            print(
                "生产仓下载未完成，正在通过 GitHub 官方地址清理后重试…",
                file=sys.stderr,
            )
    return False


def _clone_private(staging: Path) -> bool:
    command = [
        "gh",
        "repo",
        "clone",
        PRIVATE_REPOSITORY,
        str(staging),
        "--",
        "-c",
        "http.version=HTTP/1.1",
        "--depth",
        "1",
        "--single-branch",
        "--no-tags",
    ]
    for attempt in range(CLONE_ATTEMPTS):
        _remove_staging(staging)
        cloned = _gh(command, timeout=1800)
        bootstrap = staging / "scripts/workbuddy_bootstrap_for_business.py"
        if (
            cloned.returncode == 0
            and (staging / ".git").is_dir()
            and bootstrap.is_file()
            and _official_origin(staging)
        ):
            return True
        if attempt + 1 < CLONE_ATTEMPTS:
            print(
                "生产仓下载未完成，正在通过 GitHub 官方地址清理后重试…",
                file=sys.stderr,
            )
    return False


def _atomic_clone_to_target(target: Path, cloner) -> int:
    """Clone into staging then rename onto target.

    Returns 0 on success, 4 on clone/integrity failure, 5 if target became busy.
    """
    staging_parent = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.install-", dir=str(target.parent))
    )
    staging = staging_parent / "checkout"
    try:
        if not cloner(staging):
            return 4
        if target.exists() or target.is_symlink():
            return 5
        os.replace(staging, target)
        return 0
    finally:
        _remove_staging(staging_parent)


def _configure_device_checkout(
    root: Path, private_key: Path, config_dir: Path, *, set_ssh_origin: bool
) -> bool:
    ssh_command = _device_ssh_command(private_key, config_dir)
    if ssh_command is None:
        return False
    configured = _device_run(
        ["git", "-C", str(root), "config", "--local", "core.sshCommand", ssh_command]
    )
    if configured.returncode != 0:
        return False
    if set_ssh_origin:
        origin = _device_run(
            ["git", "-C", str(root), "remote", "set-url", "origin", DEVICE_SSH_ORIGIN]
        )
        if origin.returncode != 0:
            return False
    return True


def _clone_private_device(
    staging: Path, private_key: Path, config_dir: Path
) -> bool:
    ssh_command = _device_ssh_command(private_key, config_dir)
    if ssh_command is None:
        return False
    command = [
        "git",
        "-c",
        f"core.sshCommand={ssh_command}",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--no-tags",
        DEVICE_SSH_ORIGIN,
        str(staging),
    ]
    for attempt in range(CLONE_ATTEMPTS):
        _remove_staging(staging)
        cloned = _device_run(command, timeout=1800)
        bootstrap = staging / "scripts/workbuddy_bootstrap_for_business.py"
        if (
            cloned.returncode == 0
            and (staging / ".git").is_dir()
            and bootstrap.is_file()
            and _official_origin(staging)
            and _configure_device_checkout(
                staging, private_key, config_dir, set_ssh_origin=False
            )
        ):
            return True
        if attempt + 1 < CLONE_ATTEMPTS:
            print(
                "Private 下载未完成，正在通过官方安全地址清理后重试…",
                file=sys.stderr,
            )
    return False


def _device_authorization(
    config_dir: Path,
) -> tuple[Path, dict[str, str]] | int:
    try:
        device = _load_device_key(config_dir)
        if device is None:
            device = _generate_device_key(config_dir)
            if device is None:
                raise ValueError("device key generation failed")
            _emit_device_request(device[1])
            return DEVICE_ACCESS_PENDING_EXIT
        if not _device_access_approved(device[0], config_dir):
            _emit_device_request(device[1])
            return DEVICE_ACCESS_PENDING_EXIT
        return device
    except (OSError, ValueError):
        print(
            "业务设备密钥无法安全创建或校验；未安装任何生产资产。",
            file=sys.stderr,
        )
        print("WB_INSTALL_STATE=device_key_error")
        return DEVICE_KEY_ERROR_EXIT


def _handoff(
    target: Path,
    *,
    skip_update: bool,
    no_open: bool,
    requirements: list[str],
    device_ssh_command: str | None = None,
) -> int:
    bootstrap = target / "scripts/workbuddy_bootstrap_for_business.py"
    command = [sys.executable, str(bootstrap), "--target", str(target)]
    if skip_update:
        command.append("--skip-update")
    if no_open:
        command.append("--no-open")
    for requirement in requirements:
        command.extend(["--require", requirement])
    if device_ssh_command is None:
        handoff_env = os.environ.copy()
        handoff_env.pop("GH_TOKEN", None)
        handoff_env.pop("GITHUB_TOKEN", None)
    else:
        handoff_env = _device_environment()
        handoff_env["GIT_SSH_COMMAND"] = device_ssh_command
    try:
        return subprocess.run(
            command,
            cwd=str(target),
            check=False,
            env=handoff_env,
        ).returncode
    except OSError:
        print(
            "私有 bootstrap 启动失败；仓库已完整保留，可稍后重试。",
            file=sys.stderr,
        )
        return 6


def _install_with_device_access(
    target: Path,
    *,
    existing: bool,
    no_open: bool,
    requirements: list[str],
    device_config_dir: Path | None,
) -> int:
    config_dir = (device_config_dir or _default_device_config_dir()).expanduser()
    if config_dir.is_symlink():
        print(
            "业务设备授权目录不能是符号链接，已停止安装。",
            file=sys.stderr,
        )
        print("WB_INSTALL_STATE=device_key_error")
        return DEVICE_KEY_ERROR_EXIT
    config_dir = config_dir.resolve(strict=False)
    device_auth = _device_authorization(config_dir)
    if isinstance(device_auth, int):
        return device_auth
    private_key, _request = device_auth
    ssh_command = _device_ssh_command(private_key, config_dir)
    if ssh_command is None:
        print("业务设备授权配置无法安全读取，已停止安装。", file=sys.stderr)
        return 4
    if existing:
        if not _configure_device_checkout(
            target, private_key, config_dir, set_ssh_origin=True
        ):
            print("业务设备授权更新配置失败，已停止安装。", file=sys.stderr)
            return 4
        print(
            f"已找到官方 Private 生产仓，"
            f"使用已批准业务设备安全更新：{target}"
        )
        return _handoff(
            target,
            skip_update=False,
            no_open=no_open,
            requirements=requirements,
            device_ssh_command=ssh_command,
        )

    staging_parent = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.install-", dir=str(target.parent))
    )
    staging = staging_parent / "checkout"
    try:
        if not _clone_private_device(staging, private_key, config_dir):
            print(
                "私有生产仓库安全下载或完整性检查失败，未留下半成品。",
                file=sys.stderr,
            )
            return 4
        if target.exists() or target.is_symlink():
            print("安装期间目标目录被占用，未覆盖现有内容。", file=sys.stderr)
            return 5
        os.replace(staging, target)
    finally:
        _remove_staging(staging_parent)
    print(f"私有生产仓库已通过批准的业务设备安全安装：{target}")
    return _handoff(
        target,
        skip_update=True,
        no_open=no_open,
        requirements=requirements,
        device_ssh_command=ssh_command,
    )


def install(
    target: Path,
    *,
    no_open: bool = False,
    requirements: list[str] | None = None,
    device_config_dir: Path | None = None,
) -> int:
    requirements = list(requirements or [])
    requested_target = target.expanduser()
    if requested_target.is_symlink():
        print("目标目录不能是符号链接，未作改动。", file=sys.stderr)
        return 5
    target = requested_target.resolve(strict=False)
    existing = target.exists()
    if existing and (
        not target.is_dir()
        or not (target / ".git").exists()
        or not (target / "scripts/workbuddy_bootstrap_for_business.py").is_file()
        or not _official_origin(target)
    ):
        print(
            f"目标目录已存在但不是官方生产仓，未作改动：{target}",
            file=sys.stderr,
        )
        return 5

    target.parent.mkdir(parents=True, exist_ok=True)

    if existing:
        print(f"已找到官方生产仓，交由 bootstrap 安全更新：{target}")
        return _handoff(
            target,
            skip_update=False,
            no_open=no_open,
            requirements=requirements,
        )

    print(
        "提示：本安装入口已废弃。今后请直接安装 "
        "https://github.com/lmr1123/chain-pharmacy-content-studio-private.git",
        file=sys.stderr,
    )

    # 1) Default simple path: anonymous official HTTPS (no account / no device key).
    https_status = _atomic_clone_to_target(target, _clone_production_https)
    if https_status == 0:
        print(f"生产仓库已安装：{target}")
        return _handoff(
            target,
            skip_update=True,
            no_open=no_open,
            requirements=requirements,
        )
    if https_status == 5:
        print("安装期间目标目录被占用，未覆盖现有内容。", file=sys.stderr)
        return 5

    # 2) Fallback: authenticated gh clone when the machine already has login.
    auth = _gh(["gh", "auth", "status", "--hostname", "github.com"])
    if auth.returncode == 0:
        access = _gh(
            [
                "gh",
                "repo",
                "view",
                PRIVATE_REPOSITORY,
                "--json",
                "nameWithOwner,visibility",
            ]
        )
        if access.returncode == 0:
            try:
                repository = json.loads(access.stdout or "{}")
            except json.JSONDecodeError:
                repository = {}
            visibility = str(repository.get("visibility", "")).upper()
            if (
                repository.get("nameWithOwner") == PRIVATE_REPOSITORY
                and visibility in ALLOWED_VISIBILITIES
            ):
                gh_status = _atomic_clone_to_target(target, _clone_private)
                if gh_status == 0:
                    print(f"生产仓库已安装：{target}")
                    return _handoff(
                        target,
                        skip_update=True,
                        no_open=no_open,
                        requirements=requirements,
                    )
                if gh_status == 5:
                    print(
                        "安装期间目标目录被占用，未覆盖现有内容。",
                        file=sys.stderr,
                    )
                    return 5
            else:
                print(
                    "生产仓库身份校验失败，继续尝试其他安装方式…",
                    file=sys.stderr,
                )

    # 3) Last resort: device Deploy-key path (only when production is private again
    #    or anonymous HTTPS is blocked).
    return _install_with_device_access(
        target,
        existing=False,
        no_open=no_open,
        requirements=requirements,
        device_config_dir=device_config_dir,
    )


def main() -> int:
    public_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=public_root.parent / DEFAULT_TARGET_NAME,
        help="Production repository destination",
    )
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        choices=("pptx", "courseware", "video-plan", "video-tts", "video-full"),
    )
    args = parser.parse_args()
    return install(args.target, no_open=args.no_open, requirements=args.require)


if __name__ == "__main__":
    raise SystemExit(main())
