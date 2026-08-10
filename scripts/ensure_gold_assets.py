#!/usr/bin/env python3
"""Materialize large settled gold media on demand (full quality).

Business sparse installs exclude these files so the first clone stays small.
When a route/template needs a gold MP4/PPTX, this module fetches the exact
blob from the current git commit via ``git cat-file`` (works with
``--filter=blob:none`` promisor remotes). Full developer checkouts already
have the files on disk — no-op.

  python3 scripts/ensure_gold_assets.py --slug product-courseware-green-v1
  python3 scripts/ensure_gold_assets.py --route courseware3-pptx-v1
  python3 scripts/ensure_gold_assets.py --portal
  python3 scripts/ensure_gold_assets.py --path production-library/templates/settled/.../x.mp4
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = Path("production-library/on-demand-gold-assets.json")


def load_manifest(root: Path = ROOT) -> dict[str, Any]:
    path = root / MANIFEST_REL
    if not path.is_file():
        return {"assets": []}
    return json.loads(path.read_text(encoding="utf-8"))


def list_assets(root: Path = ROOT) -> list[dict[str, Any]]:
    return list(load_manifest(root).get("assets") or [])


def sparse_negation_patterns(root: Path = ROOT) -> list[str]:
    """Patterns for business-sparse-checkout (git non-cone / gitignore style)."""
    out: list[str] = []
    for asset in list_assets(root):
        rel = str(asset.get("path") or "").strip().lstrip("/")
        if rel:
            out.append(f"!/{rel}")
    return out


def _git_ok(root: Path) -> bool:
    return (root / ".git").exists() or (root / ".git").is_file()


def _present(path: Path, *, min_bytes: int = 1) -> bool:
    try:
        return path.is_file() and path.stat().st_size >= min_bytes
    except OSError:
        return False


def materialize_git_blob(root: Path, rel: str, *, quiet: bool = False) -> Path:
    """Write HEAD:rel into the working tree (fetches promisor blob if needed)."""
    rel = rel.lstrip("/")
    dest = root / rel
    if _present(dest, min_bytes=1024):
        return dest

    if not _git_ok(root):
        raise FileNotFoundError(
            f"缺少金样资产且非 git 工作区，无法按需拉取: {rel}"
        )

    # Resolve object id first (also triggers negotiation on some git versions).
    rev = subprocess.run(
        ["git", "-C", str(root), "rev-parse", f"HEAD:{rel}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if rev.returncode != 0:
        raise FileNotFoundError(
            f"当前提交不含金样路径（无法按需拉取）: {rel}\n"
            f"{(rev.stderr or rev.stdout or '').strip()}"
        )

    if not quiet:
        print(f"按需下载全质量金样: {rel}")

    # cat-file blob downloads from promisor remote when using partial clone.
    blob = subprocess.run(
        ["git", "-C", str(root), "cat-file", "blob", f"HEAD:{rel}"],
        capture_output=True,
        check=False,
    )
    if blob.returncode != 0 or not blob.stdout:
        err = (blob.stderr or b"").decode("utf-8", "replace").strip()
        raise RuntimeError(f"git cat-file 拉取失败: {rel}\n{err}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    part.write_bytes(blob.stdout)
    part.replace(dest)
    if not quiet:
        mb = dest.stat().st_size / (1024 * 1024)
        print(f"  → 已就绪 ({mb:.1f} MB)")
    return dest


def ensure_paths(
    rel_paths: list[str],
    *,
    root: Path = ROOT,
    quiet: bool = False,
) -> list[Path]:
    done: list[Path] = []
    for rel in rel_paths:
        rel = str(rel).strip().lstrip("/")
        if not rel:
            continue
        done.append(materialize_git_blob(root, rel, quiet=quiet))
    return done


def _match_assets(
    *,
    root: Path = ROOT,
    template_slug: str | None = None,
    route_id: str | None = None,
    portal: bool = False,
    kinds: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for asset in list_assets(root):
        if kinds and str(asset.get("kind") or "") not in kinds:
            continue
        if portal and asset.get("portal"):
            selected.append(asset)
            continue
        if template_slug and template_slug in (asset.get("template_slugs") or []):
            selected.append(asset)
            continue
        if route_id and route_id in (asset.get("route_ids") or []):
            selected.append(asset)
            continue
    # de-dupe by path
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for asset in selected:
        p = str(asset.get("path") or "")
        if p and p not in seen:
            seen.add(p)
            out.append(asset)
    return out


def ensure_for_template(
    template_slug: str,
    *,
    root: Path = ROOT,
    quiet: bool = False,
) -> list[Path]:
    assets = _match_assets(root=root, template_slug=template_slug)
    return ensure_paths([str(a["path"]) for a in assets], root=root, quiet=quiet)


def ensure_for_route(
    route_id: str,
    *,
    root: Path = ROOT,
    quiet: bool = False,
) -> list[Path]:
    assets = _match_assets(root=root, route_id=route_id)
    return ensure_paths([str(a["path"]) for a in assets], root=root, quiet=quiet)


def ensure_portal_golds(*, root: Path = ROOT, quiet: bool = False) -> list[Path]:
    assets = _match_assets(root=root, portal=True)
    return ensure_paths([str(a["path"]) for a in assets], root=root, quiet=quiet)


def ensure_path(rel: str, *, root: Path = ROOT, quiet: bool = False) -> Path:
    return materialize_git_blob(root, rel, quiet=quiet)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--slug", help="settled template slug")
    parser.add_argument("--route", help="business route_id")
    parser.add_argument("--portal", action="store_true", help="portal gold mp4 sources")
    parser.add_argument("--path", action="append", default=[], help="explicit repo-relative path")
    parser.add_argument("--list", action="store_true", help="print on-demand inventory")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.list:
        for asset in list_assets(root):
            p = root / str(asset["path"])
            flag = "ok" if _present(p) else "missing"
            print(f"{flag:7}  {asset.get('kind')}  {asset['path']}")
        return 0

    paths: list[str] = list(args.path or [])
    if args.portal:
        paths.extend(str(a["path"]) for a in _match_assets(root=root, portal=True))
    if args.slug:
        paths.extend(
            str(a["path"]) for a in _match_assets(root=root, template_slug=args.slug)
        )
    if args.route:
        paths.extend(
            str(a["path"]) for a in _match_assets(root=root, route_id=args.route)
        )
    if not paths:
        parser.error("provide --slug / --route / --portal / --path")

    try:
        ensure_paths(paths, root=root, quiet=args.quiet)
    except (FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
