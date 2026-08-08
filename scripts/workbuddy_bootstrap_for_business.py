#!/usr/bin/env python3
"""WorkBuddy: install or update the factory repo, then print the business guide path.

Business only says in WorkBuddy:
  请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用

WorkBuddy runs this script (or follows docs/workbuddy-install-and-guide.md).
No zip/unzip for business.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO = "https://github.com/lmr1123/chain-pharmacy-content-studio-private.git"
DEFAULT_DIR_NAME = "chain-pharmacy-content-studio-private"
OFFICIAL_PRIVATE_ORIGINS = {
    DEFAULT_REPO,
    DEFAULT_REPO.removesuffix(".git"),
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private.git",
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private.git",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private",
}
PRIVATE_MARKER_REL = Path("distribution") / "private-production.json"
PRIVATE_MARKER_KIND = "chain-pharmacy-private-production"
PKG_REL = Path("outputs") / "业务使用资料包" / "药店培训内容工厂-业务包"
PORTAL_NAME = "index.html"
RUNTIME_PORTAL_NAME = "index.local.html"
CATALOG_REL = (
    Path("production-library") / "templates" / "settled" / "business-catalog.json"
)
PROBE_REQUIRE_CHOICES = (
    "pptx",
    "courseware",
    "video-plan",
    "video-tts",
    "video-full",
    "production-assets",
)


def clone_url_candidates(primary: str) -> list[str]:
    if primary != DEFAULT_REPO:
        raise SystemExit(
            "只允许从官方 Private 生产仓安装，已拒绝非官方地址或镜像："
            f"{primary}"
        )
    return [DEFAULT_REPO]


def default_parent() -> Path:
    home = Path.home()
    for candidate in (
        home / "Documents",
        home / "WorkBuddy",
        home / "Projects",
        home,
    ):
        if candidate.is_dir():
            return candidate
    return home


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=check)


def update_repo(root: Path) -> None:
    """Update an existing checkout, stopping rather than using a stale tree."""
    if not is_private_repo(root):
        raise SystemExit(
            f"当前目录不是官方 Private 生产仓，已拒绝 git pull: {root}"
        )
    result = run(["git", "pull", "--ff-only"], cwd=root, check=False)
    if result.returncode != 0:
        raise SystemExit(
            f"git pull --ff-only 失败（exit={result.returncode}），已停止启动。\n"
            "本地仓库保持原状；请修复网络或本地分支冲突后重试。"
        )


def is_repo(path: Path) -> bool:
    return (path / ".git").exists() and (
        path / "production-library" / "templates" / "settled"
    ).is_dir()


def private_origin_url(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(path),
            capture_output=True,
            text=True,
            check=False,
            timeout=8.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def private_origin_official(path: Path) -> bool:
    return private_origin_url(path) in OFFICIAL_PRIVATE_ORIGINS


def private_marker_valid(path: Path) -> bool:
    marker_path = path / PRIVATE_MARKER_REL
    if not marker_path.is_file():
        return False
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return marker == {
        "kind": PRIVATE_MARKER_KIND,
        "version": 1,
        "repository_url": DEFAULT_REPO,
        "production_assets": True,
    }


def is_private_repo(path: Path) -> bool:
    return (
        is_repo(path)
        and private_marker_valid(path)
        and private_origin_official(path)
    )


def resolve_repo_root(explicit: Path | None) -> Path | None:
    if explicit and is_private_repo(explicit):
        return explicit.resolve()
    # running from inside repo
    here = Path(__file__).resolve().parents[1]
    if is_private_repo(here):
        return here
    # cwd
    cwd = Path.cwd()
    if is_private_repo(cwd):
        return cwd.resolve()
    return None


def clone_or_update(repo_url: str, target: Path, *, skip_update: bool = False) -> Path:
    if skip_update:
        if target.exists() and is_private_repo(target):
            print(f"已由 Public 安装器同步，跳过更新: {target}")
            return target.resolve()
        raise SystemExit(
            f"--skip-update 只允许用于已同步且校验通过的 Private 生产仓: {target}"
        )
    if target.exists() and is_repo(target):
        if not is_private_repo(target):
            raise SystemExit(
                f"现有目录不是官方 Private 生产仓，已拒绝更新: {target}"
            )
        print(f"已安装，更新: {target}")
        update_repo(target)
        return target.resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit(
            f"目标目录已存在且不是本仓库: {target}\n"
            "请换路径，或删空后重试。"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"首次安装，克隆到: {target}")
    last_err = None
    for url in clone_url_candidates(repo_url):
        print(f"尝试: {url}")
        # clean partial failed clone
        if target.exists():
            import shutil

            shutil.rmtree(target, ignore_errors=True)
        result = run(["git", "clone", "--depth", "1", url, str(target)], check=False)
        if result.returncode == 0 and is_private_repo(target):
            print(f"克隆成功（来源: {url}）")
            return target.resolve()
        if result.returncode == 0:
            raise SystemExit(
                "克隆完成但 Private 标记或 origin 校验失败，已停止启动。"
            )
        last_err = result.returncode
        print(f"失败 (exit={last_err})，换下一个源…")
    raise SystemExit(
        "Private 生产仓克隆失败。说明：\n"
        "· 请先确认 GitHub 账号已获 Private 仓读取权限\n"
        "· 为保护授权资产，本脚本禁止 ghproxy 和第三方镜像\n"
        "· 请修复官方 GitHub 网络或账号权限后重试\n"
        f"官方地址: {DEFAULT_REPO}\n"
        "请把报错原文发给 IT/制作，或稍后回复「继续安装」。"
    )


def ensure_package(
    root: Path,
    runtime_capabilities: dict[str, bool] | None = None,
) -> Path:
    portal = root / PKG_REL / PORTAL_NAME
    build = root / "scripts" / "build_business_tier_a_package.py"
    if not portal.is_file():
        if not build.is_file():
            raise SystemExit(f"缺少业务包生成器，无法重建引导页: {build}")
        print("业务引导页缺失，尝试重建业务包…")
        result = run([sys.executable, str(build)], cwd=root, check=False)
        if result.returncode != 0:
            raise SystemExit(
                f"业务包重建失败（exit={result.returncode}），已停止启动。\n"
                f"请检查上方错误并重试: {build}"
            )
        if not portal.is_file():
            raise SystemExit(
                f"业务包重建完成但未找到引导页，已停止启动: {portal}"
            )

    if runtime_capabilities is None:
        return portal

    if not build.is_file():
        print(f"警告：缺少业务门户生成器，回退固定引导页: {build}")
        return portal
    runtime_portal = portal.with_name(RUNTIME_PORTAL_NAME)
    command = [
        sys.executable,
        str(build),
        "--runtime-capabilities-json",
        json.dumps(
            runtime_capabilities,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "--portal-only",
    ]
    print("刷新业务引导页的本机能力状态…")
    result = run(command, cwd=root, check=False)
    if result.returncode != 0:
        print(
            f"警告：业务门户能力刷新失败（exit={result.returncode}），"
            "回退固定引导页；生成前仍须重新探测任务能力。"
        )
        return portal
    if not runtime_portal.is_file():
        print(
            f"警告：未找到本机能力引导页，回退固定引导页: {runtime_portal}"
        )
        return portal
    return runtime_portal


def probe_environment(root: Path, requirements: list[str]) -> dict:
    """Probe the installed tree for the exact capabilities requested by the task."""
    probe = root / "scripts" / "probe_production_env.py"
    if not probe.is_file():
        raise SystemExit(f"缺少环境探测脚本，已停止启动: {probe}")

    command = [sys.executable, str(probe), "--json"]
    for requirement in requirements:
        command.extend(["--require", requirement])
    print("+", " ".join(command))
    result = subprocess.run(
        command,
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 2):
        detail = (result.stderr or result.stdout).strip()
        suffix = f"\n{detail}" if detail else ""
        raise SystemExit(
            f"生产环境探测执行失败（exit={result.returncode}），已停止启动。{suffix}"
        )
    try:
        report = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise SystemExit(f"生产环境探测未返回有效 JSON，已停止启动: {exc}") from exc

    capabilities = report.get("capabilities") or {}
    ready = sorted(name for name, available in capabilities.items() if available)
    unavailable = sorted(name for name, available in capabilities.items() if not available)
    print(f"环境能力可用: {', '.join(ready) if ready else '无'}")
    if unavailable:
        print(f"环境能力不可用: {', '.join(unavailable)}")

    missing = report.get("missing_capabilities") or []
    if result.returncode == 2 or not report.get("ok", False):
        missing_text = ", ".join(str(item) for item in missing) or ", ".join(requirements)
        messages = report.get("messages_zh") or []
        detail = "\n".join(f"· {message}" for message in messages)
        raise SystemExit(
            "当前机器缺少本任务要求的生产能力，已诚实停止；不会用降级产物冒充正式交付。\n"
            f"缺少能力: {missing_text}"
            + (f"\n{detail}" if detail else "")
        )
    return report


def load_catalog_names(root: Path) -> list[str]:
    path = root / CATALOG_REL
    if not path.is_file():
        # package catalog
        alt = root / PKG_REL / "01_模板货架" / "catalog.json"
        path = alt if alt.is_file() else path
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = data if isinstance(data, list) else data.get("templates") or data.get("items") or []
    names = []
    for t in items:
        if isinstance(t, dict):
            n = t.get("name_zh") or t.get("name") or t.get("slug")
            if n:
                names.append(str(n))
    return names


def open_path(path: Path) -> None:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        elif system == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        print(f"（未能自动打开浏览器: {exc}）")


def print_guide(root: Path, portal: Path) -> None:
    names = load_catalog_names(root)
    name_lines = "\n".join(f"  - {n}" for n in names) if names else "  （见引导页货架）"
    print(
        f"""
========================================
安装完成 · 请把下面整段对业务说
========================================
仓库: {root}
引导页: {portal}

你好！培训内容工厂已装好。你在本对话就能出课件和视频，三步做完：

第 1 步 · 看模板
  引导页：{portal}
  点卡片可看预览，再点「选用此模板」；也可直接说课型名。
  可选课型：
{name_lines}

第 2 步 · 输入培训内容（PPT 或视频都行）
  · PPT：「整理可可康灵芝胶囊…你先整理再生成 ppt」
  · 疾病科普视频：「我要用疾病科普视频，主题是感冒。症状…病因…调理…请生成培训视频」
  · 商品培训视频：「我要用商品培训视频，商品是××。功效/特点/人群…请生成培训视频」

第 3 步 · 下载与修改
  我把成片路径发给你；要改就说「…改成…再出一版」。

现在可以从第 1 步选模板，或直接发第 2 步内容给我。
========================================
【代理内部 · 勿对业务念】
- 系统提示全文：docs/workbuddy-system-prompt.md（须保持最新，含视频 full）
- 视频首次自检：docs/workbuddy-video-first-check.md（你执行）
- 疾病/商品视频：scripts/generate_business_video.py --mode full（禁止默认 audio-shell）
- 业务自助：正常 settled 单由你在本机出片，禁止推回制作
========================================
"""
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Install/update factory repo and start business guide")
    parser.add_argument(
        "--repo-url",
        default=os.environ.get("CHAIN_PHARMACY_REPO_URL", DEFAULT_REPO),
        help="Git clone URL",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Install directory (default: ~/Documents/chain-pharmacy-content-studio-private)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the portal in browser",
    )
    parser.add_argument(
        "--update-only",
        action="store_true",
        help="Only update existing repo (fail if missing)",
    )
    parser.add_argument(
        "--skip-update",
        action="store_true",
        help="Public installer already synced Private; validate root and skip pull",
    )
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        choices=PROBE_REQUIRE_CHOICES,
        help="Probe a task capability after update (repeatable)",
    )
    args = parser.parse_args()
    if args.skip_update and args.update_only:
        raise SystemExit("--skip-update 与 --update-only 不能同时使用")

    existing = resolve_repo_root(None)
    if args.skip_update:
        target = args.target or existing
        if target is None:
            raise SystemExit("--skip-update 但未找到已同步的 Private 生产仓")
        root = clone_or_update(args.repo_url, target, skip_update=True)
    elif existing and args.target is None:
        root = existing
        print(f"检测到已在仓库内: {root}")
        update_repo(root)
    else:
        target = args.target or (default_parent() / DEFAULT_DIR_NAME)
        if args.update_only and not is_private_repo(target):
            raise SystemExit(f"--update-only 但未找到仓库: {target}")
        root = clone_or_update(args.repo_url, target)

    requirements = list(dict.fromkeys(["production-assets", *args.require]))
    environment = probe_environment(root, requirements)
    portal = ensure_package(root, environment.get("capabilities") or {})
    print_guide(root, portal)
    if not args.no_open:
        open_path(portal)
    # machine-readable last line for agents
    print(f"WB_ROOT={root}")
    print(f"WB_PORTAL={portal}")


if __name__ == "__main__":
    main()
