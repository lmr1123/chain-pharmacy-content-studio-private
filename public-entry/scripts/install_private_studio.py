#!/usr/bin/env python3
"""Install the authorized private production repository via GitHub CLI."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PRIVATE_REPOSITORY = "lmr1123/chain-pharmacy-content-studio-private"
DEFAULT_TARGET_NAME = "chain-pharmacy-content-studio-private"
OFFICIAL_ORIGINS = {
    "https://github.com/lmr1123/chain-pharmacy-content-studio-private",
    "https://github.com/lmr1123/chain-pharmacy-content-studio-private.git",
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private",
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private.git",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private.git",
}


def _gh(
    command: list[str], *, timeout: float = 120
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
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


def _handoff(
    target: Path,
    *,
    skip_update: bool,
    no_open: bool,
    requirements: list[str],
) -> int:
    bootstrap = target / "scripts/workbuddy_bootstrap_for_business.py"
    command = [sys.executable, str(bootstrap), "--target", str(target)]
    if skip_update:
        command.append("--skip-update")
    if no_open:
        command.append("--no-open")
    for requirement in requirements:
        command.extend(["--require", requirement])
    handoff_env = os.environ.copy()
    handoff_env.pop("GH_TOKEN", None)
    handoff_env.pop("GITHUB_TOKEN", None)
    try:
        return subprocess.run(
            command,
            cwd=str(target),
            check=False,
            env=handoff_env,
        ).returncode
    except OSError:
        print("私有 bootstrap 启动失败；仓库已完整保留，可稍后重试。", file=sys.stderr)
        return 6


def install(
    target: Path,
    *,
    no_open: bool = False,
    requirements: list[str] | None = None,
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
        print(f"目标目录已存在但不是官方 Private 生产仓，未作改动：{target}", file=sys.stderr)
        return 5

    target.parent.mkdir(parents=True, exist_ok=True)

    auth = _gh(["gh", "auth", "status", "--hostname", "github.com"])
    if auth.returncode != 0:
        print(
            "Public 安装入口可用，但当前 GitHub 身份尚未认证。\n"
            "模板、声音和生产资产均未安装，当前不能生成正式 PPTX/MP4。\n"
            "请运行：gh auth login --hostname github.com --web",
            file=sys.stderr,
        )
        print("WB_INSTALL_STATE=auth_required")
        return 2

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
    if access.returncode != 0:
        print(
            "GitHub 已登录，但当前账号没有私有生产仓库权限。\n"
            "模板、声音和生产资产均未安装，当前不能生成正式 PPTX/MP4。\n"
            "请联系内部管理员为当前 GitHub 账号开通权限。",
            file=sys.stderr,
        )
        print("WB_INSTALL_STATE=private_access_required")
        return 3
    try:
        repository = json.loads(access.stdout or "{}")
    except json.JSONDecodeError:
        repository = {}
    if (
        repository.get("nameWithOwner") != PRIVATE_REPOSITORY
        or str(repository.get("visibility", "")).upper() != "PRIVATE"
    ):
        print("私有仓库身份校验失败，已停止安装。", file=sys.stderr)
        print("WB_INSTALL_STATE=private_identity_invalid")
        return 3

    if existing:
        print(f"已找到官方 Private 生产仓，交由 bootstrap 安全更新：{target}")
        return _handoff(
            target,
            skip_update=False,
            no_open=no_open,
            requirements=requirements,
        )

    staging = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.install-", dir=str(target.parent))
    )
    try:
        cloned = _gh(
            [
                "gh",
                "repo",
                "clone",
                PRIVATE_REPOSITORY,
                str(staging),
                "--",
                "--depth",
                "1",
            ],
            timeout=1800,
        )
        bootstrap = staging / "scripts/workbuddy_bootstrap_for_business.py"
        if (
            cloned.returncode != 0
            or not (staging / ".git").is_dir()
            or not bootstrap.is_file()
            or not _official_origin(staging)
        ):
            print(
                "私有生产仓库下载或完整性检查失败，未留下半成品。",
                file=sys.stderr,
            )
            return 4
        if target.exists() or target.is_symlink():
            print("安装期间目标目录被占用，未覆盖现有内容。", file=sys.stderr)
            return 5
        os.replace(staging, target)
    finally:
        _remove_staging(staging)

    print(f"私有生产仓库已安全安装：{target}")
    return _handoff(
        target,
        skip_update=True,
        no_open=no_open,
        requirements=requirements,
    )


def main() -> int:
    public_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=public_root.parent / DEFAULT_TARGET_NAME,
        help="Authorized private production repository destination",
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
