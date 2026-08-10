#!/usr/bin/env python3
"""WorkBuddy: install or update the factory repo, then print the business guide path.

Business only says in WorkBuddy:
  请安装 https://github.com/lmr1123/chain-pharmacy-content-studio-private.git，然后指引我使用

WorkBuddy clones that single production repository (or follows
docs/workbuddy-install-and-guide.md). No zip/unzip for business.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from collections.abc import Mapping
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
BUSINESS_SPARSE_REL = Path("distribution") / "business-sparse-checkout.txt"
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
PROFILE_CHOICES = (
    "pptx",
    "video-full",
    "optional-external",
)
RUNTIME_PROFILES_REL = Path("production-library") / "runtime-profiles.json"
GREEN_ENGINE_REL = (
    Path("production-library") / "engines" / "product-courseware-green-v1"
)
COMPONENT_ENGINE_REL = (
    Path("production-library") / "engines" / "courseware-pptx-v1"
)
LEGACY_PPTX_NODE_MODULES_REL = (
    Path("poc") / "courseware-export" / "work" / "node_modules"
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


def load_business_sparse_paths(root: Path) -> list[str]:
    """Paths for cone sparse-checkout (quality-critical production only)."""
    path = root / BUSINESS_SPARSE_REL
    if not path.is_file():
        return []
    paths: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        paths.append(text)
    return paths


def is_sparse_checkout(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "sparse-checkout", "list"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            timeout=8.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def apply_business_sparse_checkout(root: Path, *, force: bool = False) -> bool:
    """Apply business sparse paths. Returns True if sparse mode is active.

    Never force-sparse a full developer tree (has excluded research dirs)
    unless force=True (fresh business clone only).
    """
    paths = load_business_sparse_paths(root)
    if not paths:
        print("警告：缺少 business-sparse-checkout.txt，跳过 sparse 安装。")
        return False
    if not force and not is_sparse_checkout(root):
        # Full developer checkout: do not strip local research trees.
        if (root / "poc" / "reference-replica").exists() or (
            root / "assets" / "business-input-guides"
        ).exists():
            print(
                "检测到完整开发检出（含 research/素材目录），保持全量树；"
                "业务精简安装仅用于新 clone。"
            )
            return False
    # non-cone: allow keeping production-library while excluding validation/
    result = run(
        ["git", "sparse-checkout", "init", "--no-cone"],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        print("警告：sparse-checkout init 失败，继续全量树。")
        return False
    result = run(
        ["git", "sparse-checkout", "set", *paths],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        print("警告：sparse-checkout set 失败，继续当前检出。")
        return False
    print(
        "已启用业务 sparse 检出："
        "保留 settled 金样 / 构件库 / 视频 kit（成片质量不变），"
        "去掉 validation/research 冗余。"
    )
    return True


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
    # Refresh sparse patterns only when already in sparse business mode.
    if is_sparse_checkout(root):
        apply_business_sparse_checkout(root, force=True)


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
    print(f"首次安装，克隆到: {target}（业务 sparse + depth 1，成片质量资产完整保留）")
    last_err = None
    for url in clone_url_candidates(repo_url):
        print(f"尝试: {url}")
        # clean partial failed clone
        if target.exists():
            import shutil

            shutil.rmtree(target, ignore_errors=True)
        # Partial clone + sparse: skip research trees; keep settled golds &
        # component-library (illustration quality) and poc/gold-sample (video kit).
        result = run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                url,
                str(target),
            ],
            check=False,
        )
        if result.returncode != 0:
            # Fallback for older git without sparse/filter support.
            print("sparse/filter 克隆失败，回退普通 depth-1 克隆…")
            if target.exists():
                import shutil

                shutil.rmtree(target, ignore_errors=True)
            result = run(
                ["git", "clone", "--depth", "1", url, str(target)],
                check=False,
            )
        if result.returncode == 0 and is_private_repo(target):
            apply_business_sparse_checkout(target, force=True)
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


def _package_media_incomplete(root: Path, package_root: Path) -> bool:
    """True when portal gold videos should exist but are missing locally.

    Gold mp4s are not tracked (deduped); production installs rebuild them from
    settled sources. Fixture/min repos without settled golds are not incomplete.
    """
    media = package_root / "01_模板货架" / "media"
    pairs = (
        (
            media / "health-video-reference-tech-v1" / "gold.mp4",
            root
            / "production-library/templates/settled/health-video-reference-tech-v1",
        ),
        (
            media / "product-video-faithful-v1" / "gold.mp4",
            root
            / "production-library/templates/settled/product-video-faithful-v1",
        ),
    )
    for dest, settled in pairs:
        if dest.is_file():
            continue
        if settled.is_dir() and any(settled.glob("*.mp4")):
            return True
    return False


def ensure_package(
    root: Path,
    runtime_capabilities: dict[str, bool] | None = None,
) -> Path:
    portal = root / PKG_REL / PORTAL_NAME
    package_root = root / PKG_REL
    build = root / "scripts" / "build_business_tier_a_package.py"
    portal_missing = not portal.is_file()
    media_missing = _package_media_incomplete(root, package_root)
    needs_full_rebuild = portal_missing or media_missing
    if needs_full_rebuild:
        if not build.is_file():
            raise SystemExit(f"缺少业务包生成器，无法重建引导页: {build}")
        reason = (
            "业务引导页缺失"
            if portal_missing
            else "业务包金样视频未生成（仓库不跟踪重复 gold.mp4）"
        )
        print(f"{reason}，尝试重建业务包…")
        result = run([sys.executable, str(build)], cwd=root, check=False)
        if result.returncode != 0:
            # Hard-fail only when we have no portal at all.
            if portal_missing and not portal.is_file():
                raise SystemExit(
                    f"业务包重建失败（exit={result.returncode}），已停止启动。\n"
                    f"请检查上方错误并重试: {build}"
                )
            print(
                f"警告：业务包重建失败（exit={result.returncode}），"
                "继续使用现有引导页；视频预览金样可能稍后补齐。"
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


def load_runtime_profiles(root: Path) -> dict:
    path = root / RUNTIME_PROFILES_REL
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def expand_requirements(
    root: Path,
    *,
    require: list[str] | None = None,
    profiles: list[str] | None = None,
    routes: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Map --require / --profile / --route into probe tokens + profile ids used.

    Always starts from production-assets. Returns (probe_tokens, profile_ids).
    """
    doc = load_runtime_profiles(root)
    profile_map = doc.get("profiles") or {}
    route_map = doc.get("route_to_profile") or {}

    tokens: list[str] = ["production-assets"]
    used_profiles: list[str] = []

    for token in require or []:
        if token not in tokens:
            tokens.append(token)

    for route_id in routes or []:
        pid = route_map.get(route_id)
        if pid is None and route_id in route_map:
            # explicit null: preview-only
            continue
        if pid and pid not in used_profiles:
            used_profiles.append(pid)

    for pid in profiles or []:
        if pid not in used_profiles:
            used_profiles.append(pid)

    for pid in used_profiles:
        prof = profile_map.get(pid) or {}
        for token in prof.get("probe_require") or []:
            if token not in tokens:
                tokens.append(token)

    return tokens, used_profiles


def install_hints_for_profiles(root: Path, profile_ids: list[str]) -> list[str]:
    doc = load_runtime_profiles(root)
    profiles = doc.get("profiles") or {}
    hints: list[str] = []
    for pid in profile_ids:
        for hint in (profiles.get(pid) or {}).get("install_hints_zh") or []:
            if hint not in hints:
                hints.append(hint)
    return hints


def _artifact_node_modules_candidates(
    legacy: Path,
    *,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[Path]:
    """Return bounded local node_modules candidates in deterministic order."""
    env = os.environ if environ is None else environ
    home_dir = Path.home() if home is None else home
    candidates = [legacy]
    explicit = env.get("WORKBUDDY_NODE_MODULES")
    if explicit:
        candidates.append(Path(explicit).expanduser())
    for raw in (env.get("NODE_PATH") or "").split(os.pathsep):
        if raw:
            candidates.append(Path(raw).expanduser())
    for cache_name in ("codex-runtimes", "workbuddy-runtimes"):
        cache_root = home_dir / ".cache" / cache_name
        candidates.extend(
            sorted(cache_root.glob("*/dependencies/node/node_modules"))
        )

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _soft_repair_pptx_node_modules(
    engine: Path, candidates: list[Path], label: str
) -> list[str]:
    """Symlink engine/node_modules to a verified local artifact-tool runtime."""
    actions: list[str] = []
    if not engine.is_dir():
        return actions
    nm = engine / "node_modules"
    artifact = nm / "@oai" / "artifact-tool" / "dist" / "artifact_tool.mjs"
    if artifact.is_file():
        return actions
    if nm.is_symlink() and not nm.exists():
        try:
            nm.unlink()
        except OSError:
            pass
    source = next(
        (
            candidate
            for candidate in candidates
            if (
                candidate
                / "@oai"
                / "artifact-tool"
                / "dist"
                / "artifact_tool.mjs"
            ).is_file()
        ),
        None,
    )
    if (not nm.exists()) and source is not None:
        try:
            rel = Path(os.path.relpath(source, start=engine))
            nm.symlink_to(rel, target_is_directory=True)
            actions.append(
                f"已为{label}链接 node_modules 到本机已验证的 artifact-tool runtime（非网络安装）"
            )
        except OSError as exc:
            actions.append(f"未能为{label}自动链接 node_modules: {exc}")
    return actions


def soft_repair_local_deps(
    root: Path,
    *,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    """Local-only repairs that do not install paid services or network packages.

    - PPT engines: link a verified repository or WorkBuddy/Codex local artifact-tool runtime
    - Video runtime: link kit → poc/gold-sample when formal kit is missing
    """
    actions: list[str] = []
    legacy = root / LEGACY_PPTX_NODE_MODULES_REL
    pptx_candidates = _artifact_node_modules_candidates(
        legacy, home=home, environ=environ
    )
    actions.extend(
        _soft_repair_pptx_node_modules(
            root / COMPONENT_ENGINE_REL,
            pptx_candidates,
            "构件 PPT 引擎 courseware-pptx-v1",
        )
    )
    actions.extend(
        _soft_repair_pptx_node_modules(
            root / GREEN_ENGINE_REL, pptx_candidates, "绿色 PPT 兼容引擎"
        )
    )

    # Video runtime kit soft-repair (shared helper; no network)
    try:
        if str(root / "scripts") not in sys.path:
            sys.path.insert(0, str(root / "scripts"))
        from video_runtime import soft_repair_kit_symlink  # type: ignore

        actions.extend(soft_repair_kit_symlink(root))
    except Exception as exc:
        actions.append(f"视频 kit soft-repair 跳过: {exc}")
    return actions


def platform_summary() -> str:
    return f"{platform.system()} {platform.machine()} · python {platform.python_version()}"


def run_doctor_summary(root: Path, *, route: str | None, profile: str | None) -> None:
    """Best-effort doctor print; never overrides probe hard-fail."""
    doctor = root / "scripts" / "business_doctor.py"
    if not doctor.is_file():
        return
    command = [sys.executable, str(doctor)]
    if route:
        command.extend(["--route", route])
    elif profile:
        command.extend(["--profile", profile])
    print("+", " ".join(command))
    result = subprocess.run(
        command,
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    text = (result.stdout or "").strip()
    if text:
        print(text)
    if result.returncode not in (0, 2) and result.stderr:
        print(f"（doctor 辅助输出异常 exit={result.returncode}，可忽略）")


def probe_environment(root: Path, requirements: list[str], *, profile_ids: list[str] | None = None) -> dict:
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
        hints = install_hints_for_profiles(root, profile_ids or [])
        # If only production-assets was required, still try pptx hints when pptx missing
        if not hints and "pptx_export" in missing:
            hints = install_hints_for_profiles(root, ["pptx"])
        if not hints and "video_full" in missing:
            hints = install_hints_for_profiles(root, ["video-full"])
        hint_block = ""
        if hints:
            hint_block = "\n安装/修复提示:\n" + "\n".join(f"· {h}" for h in hints)
        doctor_hint = (
            "\n也可运行: python3 scripts/business_doctor.py"
            + (
                f" --profile {profile_ids[0]}"
                if profile_ids
                else " --route product-pptx-green-v1"
            )
        )
        raise SystemExit(
            "当前机器缺少本任务要求的生产能力，已诚实停止；不会用降级产物冒充正式交付。\n"
            f"缺少能力: {missing_text}"
            + (f"\n{detail}" if detail else "")
            + hint_block
            + doctor_hint
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

你好！培训内容工厂已装好。你在本对话就能出课件和视频，按五步做完：

第 1 步 · 锁定模板
  引导页：{portal}
  A（推荐）：点卡片看预览与真实能力，再点「确认选用」。
  B：先把商品名、要做 PPT/视频和已有内容告诉我，我推荐最多 3 个模板。
  两种方式都会先由你确认模板，再创建内容草稿。
  可选课型：
{name_lines}

第 2 步 · 交已有内容
  · 商品 PPT：「用绿色单品 PPT，主题是××，卖点…你先出内容初稿」
  · 商品视频：「用商品培训视频，商品是××。功效/特点/人群…先出脚本初稿」
  · 疾病视频（未全面自助开放时会诚实说明缺口）

第 3 步 · 审初稿
  我会同时给内容初稿、缺口和素材计划：包装/Logo/证据由你给真图，知识与场景插图由我自动生成。
  你确认内容后，我先用真实图槽验 1 张代表图，再补齐插图并生成正式成品；标「待确认」的医学/价格字段不能生图或进入正式成品。
  正式包装图或计划插图没齐、逐页视觉质检没完成时，系统会阻止发布，不会交一套占位稿。

第 4–5 步 · 生成与取件
  成片只在交付目录；失败不会伪装成已交付。

现在请选择：A 看模板，或 B 先发内容让我推荐模板。
========================================
【代理内部 · 勿对业务念】
- 平台: {platform_summary()}
- 系统提示全文：docs/workbuddy-system-prompt.md
- 统一任务：python3 scripts/business_job.py list-routes | new | draft | approve | render
- 环境自检：python3 scripts/business_doctor.py --route product-pptx-green-v1
- 能力真值：python3 scripts/probe_production_env.py --require pptx|video-full
- 绿色 PPT 正式引擎：production-library/engines/product-courseware-green-v1/
- 视频 full：scripts/generate_business_video.py --mode full（禁止默认 audio-shell）
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
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        choices=PROFILE_CHOICES,
        help="Runtime profile from production-library/runtime-profiles.json (repeatable)",
    )
    parser.add_argument(
        "--route",
        action="append",
        default=[],
        help="Business route_id; expands to its runtime profile (repeatable)",
    )
    parser.add_argument(
        "--skip-soft-repair",
        action="store_true",
        help="Do not auto-link a verified local artifact-tool runtime for PPT engines",
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

    print(f"平台: {platform_summary()}")
    if not args.skip_soft_repair:
        for action in soft_repair_local_deps(root):
            print(f"本地修复: {action}")

    requirements, profile_ids = expand_requirements(
        root,
        require=list(args.require or []),
        profiles=list(args.profile or []),
        routes=list(args.route or []),
    )
    if profile_ids:
        print(f"runtime profiles: {', '.join(profile_ids)}")
    print(f"probe require: {', '.join(requirements)}")

    environment = probe_environment(
        root, requirements, profile_ids=profile_ids
    )

    # Optional human-readable doctor summary for the first route/profile.
    first_route = (args.route or [None])[0]
    first_profile = (args.profile or profile_ids or [None])[0]
    if first_route or first_profile:
        run_doctor_summary(root, route=first_route, profile=first_profile)

    portal = ensure_package(root, environment.get("capabilities") or {})
    print_guide(root, portal)
    if not args.no_open:
        open_path(portal)
    # machine-readable last line for agents
    print(f"WB_ROOT={root}")
    print(f"WB_PORTAL={portal}")
    print(f"WB_PROFILES={','.join(profile_ids)}")
    print(f"WB_REQUIRE={','.join(requirements)}")


if __name__ == "__main__":
    main()
