#!/usr/bin/env python3
"""Gold-sample media fail-closed guard for every settled courseware template.

New themes must not reuse pixels from settled gold samples (text-only swaps).
Checks:

1. SHA-256 of bound image files against gold PPTX media / gold source assets
2. Path markers that still point at settled / validation gold trees

Authorized gold regeneration (explicit gold_sample / known gold theme name) is
allowed to keep using that template's own media.
"""

from __future__ import annotations

import hashlib
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

# Directories whose loose images are QA screenshots / previews, not production slots.
_SKIP_DIR_NAMES = {
    "preview",
    "node_modules",
    "qa",
    "qa-editable",
    "qa-reference",
    "qa-batch-workbook",
    "qa-brand-upgrade",
    "comparison",
    "__pycache__",
    ".git",
}

_SKIP_NAME_PREFIXES = (
    "slide-",
    "montage",
    "compare-",
    "comparison",
    "deck-montage",
    "cover.png",  # catalog preview only; real covers come from ppt/media
)

# Path fragments that must never appear on non-gold bound assets (pre-snapshot).
FORBIDDEN_PATH_MARKERS = (
    "/production-library/templates/settled/",
    "/production-library/validation/courseware/",
    "/poc/gold-sample/",
    "/poc/courseware-export/",
)

# template_slug → extra roots that hold gold source media beyond settled/
# (validation gold packages, engine gold content, etc.)
_EXTRA_GOLD_ROOTS: dict[str, tuple[Path, ...]] = {
    "disease-product-scenario-v1": (
        ROOT / "production-library" / "validation" / "courseware" / "disease-product-scenario-v1",
    ),
    "product-courseware-green-v1": (
        ROOT / "production-library" / "validation" / "courseware" / "product-courseware-green-v1",
        ROOT / "production-library" / "engines" / "product-courseware-green-v1",
    ),
    "sufuda-mabaloshawei-product-courseware-3-v1": (
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "sufuda-product-courseware-3-gold-v1",
    ),
    "kangaisen-lycopene-health-edu-v1": (
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "kangaisen-lycopene-health-edu-v1",
    ),
    "fuler-fanqiehongsu-product-courseware-4-v1": (
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "product-courseware-4-faithful-replica-v1",
    ),
    "product-courseware-component-v1": (
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "product-courseware-component-v1",
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "product-courseware-4-faithful-replica-v1",
    ),
    "product-video-faithful-v1": (
        ROOT / "production-library" / "validation" / "video" / "tomato-lycopene-faithful-v1",
    ),
    "health-video-reference-tech-v1": (
        ROOT / "production-library" / "validation" / "video",
    ),
    "disease-health-shenke-blue-v1": (
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "disease-uri-acute-upper-respiratory-v1",
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "gold-samples"
        / "uri-shenke-health-pptx-gold-v1",
    ),
}

# theme / model signals that authorize reusing that gold's own media
_GOLD_THEME_HINTS: dict[str, tuple[str, ...]] = {
    "disease-product-scenario-v1": ("穿心莲", "andrographolide-drop-pills"),
    "product-courseware-green-v1": ("金银花露",),
    "sufuda-mabaloshawei-product-courseware-3-v1": ("速福达", "玛巴洛沙韦", "mabaloshawei"),
    "kangaisen-lycopene-health-edu-v1": ("康爱森", "番茄红素_健康科普"),
    "fuler-fanqiehongsu-product-courseware-4-v1": ("福尔", "番茄红素软胶囊", "麦金利"),
    "product-courseware-component-v1": (),  # never authorize component gold inheritance by name
    "product-video-faithful-v1": ("辅酶Q10",),
    "health-video-reference-tech-v1": ("风热证",),
    "disease-health-shenke-blue-v1": ("急性上呼吸道感染",),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _should_skip_loose_image(path: Path) -> bool:
    name = path.name.lower()
    if any(name.startswith(prefix) for prefix in _SKIP_NAME_PREFIXES):
        return True
    parts = {part.lower() for part in path.parts}
    if parts & _SKIP_DIR_NAMES:
        return True
    # QA contact sheets and montages
    if "montage" in name or name.startswith("key-0"):
        return True
    return False


def _collect_from_pptx(path: Path, hashes: set[str]) -> int:
    count = 0
    try:
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if not member.startswith("ppt/media/") or member.endswith("/"):
                    continue
                lower = member.lower()
                if not any(lower.endswith(ext) for ext in IMAGE_SUFFIXES):
                    # some media lack extensions; still hash binary payload
                    pass
                try:
                    hashes.add(sha256_bytes(archive.read(member)))
                    count += 1
                except (KeyError, OSError):
                    continue
    except (OSError, zipfile.BadZipFile):
        return 0
    return count


def _collect_from_tree(root: Path, hashes: set[str]) -> int:
    if not root.exists():
        return 0
    count = 0
    if root.is_file():
        if root.suffix.lower() == ".pptx":
            return _collect_from_pptx(root, hashes)
        if root.suffix.lower() in IMAGE_SUFFIXES and not _should_skip_loose_image(root):
            try:
                hashes.add(sha256_file(root))
                return 1
            except OSError:
                return 0
        return 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".pptx":
            count += _collect_from_pptx(path, hashes)
            continue
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if _should_skip_loose_image(path):
            continue
        try:
            hashes.add(sha256_file(path))
            count += 1
        except OSError:
            continue
    return count


def settled_template_slugs() -> list[str]:
    settled = ROOT / "production-library" / "templates" / "settled"
    if not settled.is_dir():
        return []
    return sorted(
        path.name
        for path in settled.iterdir()
        if path.is_dir() and (path / "manifest.json").is_file()
    )


def gold_roots_for_slug(template_slug: str) -> list[Path]:
    roots: list[Path] = []
    settled = ROOT / "production-library" / "templates" / "settled" / template_slug
    if settled.is_dir():
        roots.append(settled)
    for extra in _EXTRA_GOLD_ROOTS.get(template_slug, ()):
        if extra.exists():
            roots.append(extra)
    return roots


@lru_cache(maxsize=32)
def gold_media_hashes_for_slug(template_slug: str) -> frozenset[str]:
    hashes: set[str] = set()
    for root in gold_roots_for_slug(template_slug):
        _collect_from_tree(root, hashes)
    return frozenset(hashes)


@lru_cache(maxsize=1)
def all_settled_gold_media_hashes() -> frozenset[str]:
    hashes: set[str] = set()
    for slug in settled_template_slugs():
        hashes |= set(gold_media_hashes_for_slug(slug))
    # Always include CW4 validation generated media even if slug scan skipped
    cw4_media = (
        ROOT
        / "production-library"
        / "validation"
        / "courseware"
        / "product-courseware-4-faithful-replica-v1"
        / "assets"
        / "generated"
    )
    _collect_from_tree(cw4_media, hashes)
    return frozenset(hashes)


def is_authorized_gold_theme(
    *,
    template_slug: str | None,
    theme: str,
    model: dict[str, Any] | None = None,
) -> bool:
    """Return True only when this job is explicitly regenerating that gold sample."""
    model = model or {}
    meta = model.get("meta") if isinstance(model.get("meta"), dict) else {}
    if model.get("gold_sample") is True or meta.get("gold_sample") is True:
        # gold_sample flag alone is not enough without identity match
        pass
    theme_text = f"{theme}\n{json_blob_for_identity(model)}"
    if not template_slug:
        return False
    hints = _GOLD_THEME_HINTS.get(template_slug, ())
    if not hints:
        # no name-based gold authorization for this slug
        if model.get("gold_sample") is True or meta.get("gold_sample") is True:
            # still require at least one known identity token in theme if configured empty
            return False
        return False
    if not any(hint in theme_text for hint in hints):
        return False
    # Prefer explicit flag when present; name match is the minimum bar for legacy jobs
    if "gold_sample" in model or "gold_sample" in meta:
        return bool(model.get("gold_sample") or meta.get("gold_sample"))
    return True


def json_blob_for_identity(model: dict[str, Any]) -> str:
    parts: list[str] = []
    meta = model.get("meta") if isinstance(model.get("meta"), dict) else {}
    for key in ("theme_id", "project_id", "slug"):
        value = model.get(key) or meta.get(key)
        if value:
            parts.append(str(value))
    product = model.get("product") if isinstance(model.get("product"), dict) else {}
    for key in ("name", "display_name", "brand_name", "generic_name"):
        value = product.get(key)
        if value:
            parts.append(str(value))
    return "\n".join(parts)


def path_forbidden_markers(path: Path | str) -> list[str]:
    try:
        text = str(Path(path).expanduser().resolve())
    except OSError:
        text = str(path)
    # normalize for marker match
    normalized = text.replace("\\", "/")
    hits = [marker for marker in FORBIDDEN_PATH_MARKERS if marker in normalized]
    return hits


def check_image_file(
    path: Path | str,
    *,
    binding: str = "image",
    template_slug: str | None = None,
    allow_gold: bool = False,
) -> list[str]:
    """Return blockers for one bound image path."""
    if allow_gold:
        return []
    blockers: list[str] = []
    raw = Path(str(path)).expanduser()
    if not raw.is_file():
        return blockers  # missing handled by route-specific formal blockers

    for marker in path_forbidden_markers(raw):
        blockers.append(
            f"{binding} 仍指向金样目录（{marker.strip('/')}），禁止用于新主题；"
            "请按本主题重新生成或绑定授权图"
        )

    try:
        digest = sha256_file(raw.resolve())
    except OSError:
        return blockers

    # Prefer route-specific blocklist; always also apply global settled union
    route_hashes = (
        gold_media_hashes_for_slug(template_slug) if template_slug else frozenset()
    )
    global_hashes = all_settled_gold_media_hashes()
    if digest in route_hashes:
        blockers.append(
            f"{binding} 像素与金样「{template_slug}」源图 SHA 相同，禁止继承；"
            "须按新主题重新生成/授权替换"
        )
    elif digest in global_hashes:
        blockers.append(
            f"{binding} 像素命中其他签样金样源图 SHA，禁止跨课型复用金样画面"
        )
    return list(dict.fromkeys(blockers))


def check_image_files(
    files: Iterable[tuple[str, Path | str]],
    *,
    template_slug: str | None = None,
    allow_gold: bool = False,
) -> list[str]:
    blockers: list[str] = []
    for binding, path in files:
        blockers.extend(
            check_image_file(
                path,
                binding=binding,
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )
    return list(dict.fromkeys(blockers))


def check_asset_manifest(
    manifest: dict[str, Any],
    *,
    template_slug: str | None = None,
    allow_gold: bool = False,
) -> list[str]:
    """manifest values may be {file, sha256} or bare path strings."""
    if allow_gold:
        return []
    blockers: list[str] = []
    pairs: list[tuple[str, Path | str]] = []
    route_hashes = (
        gold_media_hashes_for_slug(template_slug) if template_slug else frozenset()
    )
    global_hashes = all_settled_gold_media_hashes()
    for key, value in (manifest or {}).items():
        if isinstance(value, dict):
            raw = value.get("file") or value.get("path") or value.get("src")
            digest = str(value.get("sha256") or "")
            if raw:
                pairs.append((str(key), str(raw)))
            elif digest:
                if digest in route_hashes:
                    blockers.append(
                        f"{key} 的 SHA 仍是金样「{template_slug}」源图，禁止继承"
                    )
                elif digest in global_hashes:
                    blockers.append(f"{key} 的 SHA 命中签样金样源图，禁止继承")
        elif isinstance(value, str) and value.strip():
            pairs.append((str(key), value))
    blockers.extend(
        check_image_files(
            pairs, template_slug=template_slug, allow_gold=False
        )
    )
    return list(dict.fromkeys(blockers))


def guard_summary() -> dict[str, Any]:
    """Diagnostics for tests / readiness portal."""
    per_slug = {
        slug: len(gold_media_hashes_for_slug(slug)) for slug in settled_template_slugs()
    }
    return {
        "schema": "gold-asset-guard/v1",
        "template_slugs": sorted(per_slug),
        "hashes_per_slug": per_slug,
        "global_hash_count": len(all_settled_gold_media_hashes()),
        "forbidden_path_markers": list(FORBIDDEN_PATH_MARKERS),
    }


if __name__ == "__main__":
    import json as _json

    print(_json.dumps(guard_summary(), ensure_ascii=False, indent=2))
