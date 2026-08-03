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
PKG_REL = Path("outputs") / "业务使用资料包" / "药店培训内容工厂-业务包"
PORTAL_NAME = "index.html"
CATALOG_REL = (
    Path("production-library") / "templates" / "settled" / "business-catalog.json"
)


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
        run(["git", "pull", "--ff-only"], cwd=target, check=False)
        return target.resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit(
            f"目标目录已存在且不是本仓库: {target}\n"
            "请换路径，或删空后重试。"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"首次安装，克隆到: {target}")
    result = run(["git", "clone", repo_url, str(target)], check=False)
    if result.returncode != 0:
        raise SystemExit(
            "git clone 失败。常见原因：\n"
            "1) 私有仓库需先登录 GitHub（gh auth login / 配置 HTTPS token / SSH key）\n"
            "2) 无 git 或网络不可用\n"
            f"仓库: {repo_url}\n"
            "请业务把报错截图给 IT/制作，或先完成 GitHub 访问后再说「继续安装」。"
        )
    return target.resolve()


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
安装完成 · 开始指引业务
========================================
仓库路径: {root}
引导页:   {portal}

【请对业务说，并逐步陪做】

你好！培训内容工厂已装好。我们按开源项目四步走，你不需要解压任何 zip：

第 1 步 · 预览选模板
  我已打开引导页（若未打开请双击下面路径）。
  请点「下一步：预览选模板」，浏览封面和关键页，点「选用此模板」。
  可选课型：
{name_lines}

第 2 步 · 按 Word 填报
  选用后下载「空白 Word」，按「本课型怎么填」写公司审核内容。
  整节可删；联合用药/列表有几条写几条（2 组就 2 行）。
  包装/Logo 用授权图；没有就空着，我会记缺口，绝不仿包装。

第 3 步 · 上传提交
  把已填 Word + 授权图：
  · 拖到引导页上传区并复制口令发我；或
  · 放到 07_业务填报上传/待处理/
  也可直接把 Word 附件发到本对话。

第 4 步 · 审初稿 → 收成片
  我先出「内容初稿/分镜预览 + 缺口清单」；
  你确认后，我再出可编辑 PPTX / 培训视频。

现在请告诉我：更想做「商品 PPT」还是「健康/商品视频」？
也可以直接说主题名（如金银花露、风热证）。
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
