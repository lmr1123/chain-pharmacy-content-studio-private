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

DEFAULT_REPO = "https://github.com/lmr1123/chain-pharmacy-content-studio.git"
DEFAULT_DIR_NAME = "chain-pharmacy-content-studio"
# Mainland CN: github.com often intermittent; try mirrors after official URL fails.
# Format: ghproxy prefixes the full https://github.com/...git URL.
CN_CLONE_MIRRORS = (
    "https://ghproxy.com/https://github.com/lmr1123/chain-pharmacy-content-studio.git",
    "https://mirror.ghproxy.com/https://github.com/lmr1123/chain-pharmacy-content-studio.git",
    "https://gitclone.com/github.com/lmr1123/chain-pharmacy-content-studio",
)
PKG_REL = Path("outputs") / "业务使用资料包" / "药店培训内容工厂-业务包"
PORTAL_NAME = "index.html"
CATALOG_REL = (
    Path("production-library") / "templates" / "settled" / "business-catalog.json"
)


def clone_url_candidates(primary: str) -> list[str]:
    urls = [primary]
    if "github.com" in primary and "lmr1123/chain-pharmacy-content-studio" in primary:
        for m in CN_CLONE_MIRRORS:
            if m not in urls:
                urls.append(m)
    # env override: CHAIN_PHARMACY_CLONE_MIRRORS=url1,url2
    extra = os.environ.get("CHAIN_PHARMACY_CLONE_MIRRORS", "").strip()
    if extra:
        for part in extra.split(","):
            part = part.strip()
            if part and part not in urls:
                urls.append(part)
    return urls


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


def is_repo(path: Path) -> bool:
    return (path / ".git").is_dir() and (path / "production-library" / "templates" / "settled").is_dir()


def resolve_repo_root(explicit: Path | None) -> Path | None:
    if explicit and is_repo(explicit):
        return explicit.resolve()
    # running from inside repo
    here = Path(__file__).resolve().parents[1]
    if is_repo(here):
        return here
    # cwd
    cwd = Path.cwd()
    if is_repo(cwd):
        return cwd.resolve()
    return None


def clone_or_update(repo_url: str, target: Path) -> Path:
    if target.exists() and is_repo(target):
        print(f"已安装，更新: {target}")
        # Prefer pull; if remote is slow, still ok to proceed with existing tree
        run(["git", "pull", "--ff-only"], cwd=target, check=False)
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
        if result.returncode == 0 and is_repo(target):
            # normalize origin to official github for later pull when network allows
            run(
                ["git", "remote", "set-url", "origin", DEFAULT_REPO],
                cwd=target,
                check=False,
            )
            print(f"克隆成功（来源: {url}）")
            return target.resolve()
        last_err = result.returncode
        print(f"失败 (exit={last_err})，换下一个源…")
    raise SystemExit(
        "git clone 全部源失败。说明：\n"
        "· 仓库已 Public，一般不需要 GitHub 登录\n"
        "· 国内直连 github.com 常不稳定（TLS/空响应），已自动试过 ghproxy 等镜像\n"
        "· 仍失败：换网络/手机热点、公司代理，或由制作发业务包 zip 备用\n"
        f"官方地址: {DEFAULT_REPO}\n"
        "请把报错原文发给 IT/制作，或稍后回复「继续安装」。"
    )


def ensure_package(root: Path) -> Path:
    portal = root / PKG_REL / PORTAL_NAME
    if portal.is_file():
        return portal
    # try light rebuild if scripts present
    build = root / "scripts" / "build_business_tier_a_package.py"
    if build.is_file():
        print("业务引导页缺失，尝试重建业务包…")
        run([sys.executable, str(build)], cwd=root, check=False)
    if portal.is_file():
        return portal
    raise SystemExit(
        f"未找到业务引导页: {portal}\n"
        "请制作侧执行: python3 scripts/refresh_business_delivery.py 后推送仓库。"
    )


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
        help="Install directory (default: ~/Documents/chain-pharmacy-content-studio)",
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
    args = parser.parse_args()

    existing = resolve_repo_root(None)
    if existing and args.target is None:
        root = existing
        print(f"检测到已在仓库内: {root}")
        run(["git", "pull", "--ff-only"], cwd=root, check=False)
    else:
        target = args.target or (default_parent() / DEFAULT_DIR_NAME)
        if args.update_only and not is_repo(target):
            raise SystemExit(f"--update-only 但未找到仓库: {target}")
        root = clone_or_update(args.repo_url, target)

    portal = ensure_package(root)
    print_guide(root, portal)
    if not args.no_open:
        open_path(portal)
    # machine-readable last line for agents
    print(f"WB_ROOT={root}")
    print(f"WB_PORTAL={portal}")


if __name__ == "__main__":
    main()
