#!/usr/bin/env python3
"""从速福达金样框架复刻其他商品主题课件。

输入 theme 包（theme.json + 可选 assets/）→ 复制框架 → 合并 content-model →
可选克隆旁白 → 导出 PPTX → 写出 gap-report。

示例：
  python3 scripts/replicate_courseware_theme.py \\
    --theme production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/theme-packages/demo-product-b \\
    --out-slug demo-product-b-courseware-v1 \\
    --skip-tts
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLD = (
    ROOT
    / "production-library/validation/courseware/sufuda-product-courseware-3-gold-v1"
)
DEFAULT_OUT_PARENT = ROOT / "production-library/validation/courseware"

REQUIRED_PRODUCT_FIELDS = ("brand_name", "generic_name", "display_name")
GOLD_PACKAGING_EXTRA_KEYS = {"pack40", "pack20", "packSusp"}
PLACEHOLDER_MARKERS = (
    "TODO",
    "awaiting-business",
    "待确认",
    "待业务",
    "请填写",
    "占位",
)
SAFE_PAGE_TITLES = {
    "cover": "封面",
    "flu": "课程背景",
    "summary": "课程总结",
}
RUNTIME_TEXT_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".html"}


class ThemeContractError(ValueError):
    """Theme data is incomplete or would leak source-gold content."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(f"- {item}" for item in errors))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _text_override(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict) and isinstance(value.get("text"), str):
        return str(value["text"]).strip()
    return None


def _is_complete_text(value: object) -> bool:
    text = _text_override(value)
    if not text:
        return False
    lowered = text.lower()
    if any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS):
        return False
    # The blank theme uses full-width parenthesized prompts such as （品牌名）.
    if text.startswith("（") and text.endswith("）"):
        return False
    return True


def _business_asset_keys(base: dict) -> set[str]:
    keys: set[str] = set()
    for page in base.get("pages") or []:
        for element in (page.get("elements") or {}).values():
            if element.get("kind") != "image":
                continue
            if element.get("replace") != "business_authorized":
                continue
            key = element.get("asset")
            if isinstance(key, str) and key:
                keys.add(key)
    return keys


def _illustration_asset_keys(base: dict) -> set[str]:
    keys: set[str] = set()
    for page in base.get("pages") or []:
        for element in (page.get("elements") or {}).values():
            if element.get("kind") != "image":
                continue
            if element.get("replace") != "theme_illustration":
                continue
            key = element.get("asset")
            if isinstance(key, str) and key:
                keys.add(key)
    return keys


def _replaceable_asset_keys(base: dict) -> set[str]:
    return _business_asset_keys(base) | _illustration_asset_keys(base)


def _gold_sample_theme_id(base: dict, gold: Path) -> str:
    """Return the canonical gold identity registered by both source records."""

    model_id = str(base.get("project_id") or "").strip()
    storyboard_path = gold / "storyboard.json"
    storyboard_id = ""
    if storyboard_path.is_file():
        storyboard_id = str(load_json(storyboard_path).get("project_id") or "").strip()
    if not model_id or model_id != storyboard_id:
        raise ThemeContractError(
            [
                "速福达金样身份登记不一致："
                f"content-model={model_id or '空'}, storyboard={storyboard_id or '空'}"
            ]
        )
    return model_id


def _is_gold_sample_update(base: dict, theme: dict, gold: Path) -> bool:
    return (
        theme.get("gold_sample") is True
        and str(theme.get("theme_id") or "").strip() == _gold_sample_theme_id(base, gold)
    )


def _asset_key_override(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict) and isinstance(value.get("asset"), str):
        return str(value["asset"]).strip() or None
    return None


def _resolve_theme_asset(theme_dir: Path, raw: object) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip()
    if any(marker.lower() in value.lower() for marker in PLACEHOLDER_MARKERS):
        return None
    path = Path(value).expanduser()
    candidates = [path] if path.is_absolute() else [theme_dir / path, theme_dir / "assets" / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _gold_replaceable_hashes(base: dict, gold: Path) -> set[str]:
    hashes: set[str] = set()
    assets = base.get("assets") or {}
    for key in _replaceable_asset_keys(base) | GOLD_PACKAGING_EXTRA_KEYS:
        raw = assets.get(key)
        if not isinstance(raw, str) or not raw:
            continue
        rel = raw.removeprefix("/")
        path = gold / "public" / rel
        if path.is_file():
            hashes.add(_sha256(path))
    return hashes


def _gold_replaceable_paths(base: dict, gold: Path) -> set[str]:
    """Include registered paths plus duplicate gold files with identical pixels."""

    hashes = _gold_replaceable_hashes(base, gold)
    public = gold / "public"
    return {
        f"/{path.relative_to(public).as_posix()}"
        for path in public.rglob("*")
        if path.is_file()
        and path.suffix.lower() == ".png"
        and _sha256(path) in hashes
    }


def _gold_copy_values(base: dict) -> set[str]:
    values = {
        str((base.get("product") or {}).get(field) or "").strip()
        for field in REQUIRED_PRODUCT_FIELDS
    }
    values.add(str(base.get("title") or "").strip())
    for page in base.get("pages") or []:
        for element in (page.get("elements") or {}).values():
            if element.get("kind") == "text" and element.get("replace") == "theme_copy":
                values.add(str(element.get("text") or "").strip())
    return {value for value in values if len(value) >= 4}


def _submitted_text_values(theme: dict) -> list[str]:
    values: list[str] = []
    product = theme.get("product") or {}
    for field in REQUIRED_PRODUCT_FIELDS:
        text = _text_override(product.get(field))
        if text:
            values.append(text)
    title = _text_override(theme.get("title"))
    if title:
        values.append(title)
    for page in theme.get("pages") or []:
        if not isinstance(page, dict):
            continue
        page_title = _text_override(page.get("title"))
        if page_title:
            values.append(page_title)
        for value in (page.get("elements") or {}).values():
            text = _text_override(value)
            if text:
                values.append(text)
    for caption in theme.get("captions") or []:
        text = _text_override(caption)
        if text:
            values.append(text)
    return values


def validate_theme_contract(
    base: dict,
    theme: dict,
    *,
    theme_dir: Path,
    gold: Path,
    require_captions: bool = False,
) -> dict[str, Path]:
    """Validate a complete theme before any gold framework is copied.

    Every source element marked ``theme_copy`` must be explicitly supplied by the
    new theme. Every image marked ``business_authorized`` must resolve to a real,
    non-gold PNG. This makes incomplete themes fail before they can inherit source
    copy or packaging.
    """

    errors: list[str] = []
    canonical_gold_id = _gold_sample_theme_id(base, gold)
    gold_sample_update = _is_gold_sample_update(base, theme, gold)
    if "gold_sample" in theme and not isinstance(theme.get("gold_sample"), bool):
        errors.append("gold_sample 必须是布尔值 true/false")
    if theme.get("gold_sample") is True and not gold_sample_update:
        errors.append(
            "gold_sample:true 仅允许登记金样 theme_id="
            f"{canonical_gold_id}；商品名相似不能进入原商品更新模式"
        )

    product = theme.get("product") or {}
    for field in REQUIRED_PRODUCT_FIELDS:
        if not _is_complete_text(product.get(field)):
            errors.append(f"product.{field} 缺少正式内容")
    if "title" in theme and not _is_complete_text(theme.get("title")):
        errors.append("title 仍为空或占位")

    expected_style = str(base.get("style_pack_id") or "")
    supplied_style = str(theme.get("style_pack_id") or expected_style)
    if supplied_style != expected_style:
        errors.append(
            f"style_pack_id 必须锁定 {expected_style}，收到 {supplied_style or '空'}"
        )
    expected_voice = str(base.get("voice_pack_id") or "")
    supplied_voice = str(theme.get("voice_pack_id") or expected_voice)
    if supplied_voice != expected_voice:
        errors.append(
            f"voice_pack_id 必须锁定 {expected_voice}，收到 {supplied_voice or '空'}"
        )

    raw_pages = theme.get("pages") or []
    page_overrides: dict[str, dict] = {}
    for page in raw_pages:
        if not isinstance(page, dict) or not page.get("id"):
            errors.append("pages 中存在缺少 id 的页面")
            continue
        page_id = str(page["id"])
        if page_id in page_overrides:
            errors.append(f"pages.{page_id} 重复")
            continue
        page_overrides[page_id] = page

    base_page_ids = {str(page.get("id")) for page in base.get("pages") or []}
    for unknown in sorted(set(page_overrides) - base_page_ids):
        errors.append(f"pages.{unknown} 不是课件3已登记页面")

    illustration_bindings: dict[str, str] = {}
    for page in base.get("pages") or []:
        page_id = str(page.get("id"))
        override = page_overrides.get(page_id)
        if override is None:
            errors.append(f"pages.{page_id} 整页未覆盖，禁止继承金样")
            continue
        if "title" in override and not _is_complete_text(override.get("title")):
            errors.append(f"pages.{page_id}.title 仍为空或占位")
        element_overrides = override.get("elements") or {}
        if not isinstance(element_overrides, dict):
            errors.append(f"pages.{page_id}.elements 必须是对象")
            continue
        known_roles = set((page.get("elements") or {}).keys())
        for unknown_role in sorted(set(element_overrides) - known_roles):
            errors.append(f"pages.{page_id}.elements.{unknown_role} 不是已登记槽位")
        for role, element in (page.get("elements") or {}).items():
            if (
                element.get("kind") == "image"
                and element.get("replace") == "business_authorized"
                and role in element_overrides
            ):
                errors.append(
                    f"pages.{page_id}.elements.{role} 不接受直接图片路径；"
                    f"请通过 assets.{element.get('asset')} 提交授权 PNG"
                )
            if (
                element.get("kind") == "image"
                and element.get("replace") == "theme_illustration"
            ):
                asset_key = _asset_key_override(element_overrides.get(role))
                if asset_key is None:
                    errors.append(
                        f"pages.{page_id}.elements.{role} 缺少插图资产绑定，"
                        "禁止继承金样插图"
                    )
                else:
                    illustration_bindings[f"{page_id}.{role}"] = asset_key
            if element.get("kind") != "text" or element.get("replace") != "theme_copy":
                continue
            if not _is_complete_text(element_overrides.get(role)):
                errors.append(
                    f"pages.{page_id}.elements.{role} 缺少正式文案，禁止继承金样"
                )

    captions = theme.get("captions") or []
    if require_captions and not captions:
        errors.append("生成旁白时 captions 必填")
    for index, item in enumerate(captions):
        text = item if isinstance(item, str) else item.get("text") if isinstance(item, dict) else None
        if not _is_complete_text(text):
            errors.append(f"captions[{index}] 缺少正式口播")

    raw_assets = theme.get("assets") or {}
    if not isinstance(raw_assets, dict):
        errors.append("assets 必须是对象")
        raw_assets = {}
    resolved_assets: dict[str, Path] = {}
    required_assets = _business_asset_keys(base) | set(illustration_bindings.values())
    gold_hashes = _gold_replaceable_hashes(base, gold)
    for key, raw in raw_assets.items():
        path = _resolve_theme_asset(theme_dir, raw)
        if path is None:
            errors.append(f"assets.{key} 路径无效或仍为占位：{raw!r}")
            continue
        with path.open("rb") as handle:
            signature = handle.read(8)
        if path.suffix.lower() != ".png" or signature != b"\x89PNG\r\n\x1a\n":
            errors.append(f"assets.{key} 必须是可读取的 PNG：{path}")
            continue
        resolved_assets[str(key)] = path

    if not gold_sample_update:
        for key, path in sorted(resolved_assets.items()):
            if _sha256(path) in gold_hashes:
                errors.append(f"assets.{key} 仍是速福达金样可替换图片，禁止用于新主题")

    for key in sorted(required_assets):
        path = resolved_assets.get(key)
        if path is None:
            errors.append(f"assets.{key} 为页面显式绑定的必填 PNG，缺失则禁止生成")

    if not gold_sample_update:
        submitted_text = "\n".join(_submitted_text_values(theme))
        leaked_copy = sorted(value for value in _gold_copy_values(base) if value in submitted_text)
        errors.extend(f"新主题显式内容仍含速福达金样文案：{value!r}" for value in leaked_copy)

    if errors:
        raise ThemeContractError(errors)
    return resolved_assets


def _normalized_asset_map(resolved: dict[str, Path], dest: Path) -> dict[str, str]:
    target = dest / "public" / "assets" / "theme"
    target.mkdir(parents=True, exist_ok=True)
    normalized: dict[str, str] = {}
    for key, source in sorted(resolved.items()):
        safe_key = re.sub(r"[^A-Za-z0-9._-]+", "-", key).strip("-") or "asset"
        out = target / f"{safe_key}.png"
        shutil.copy2(source, out)
        normalized[key] = f"/assets/theme/{out.name}"
    return normalized


def _override_blob(theme: dict) -> str:
    return json.dumps(theme, ensure_ascii=False, sort_keys=True)


def _assert_no_uncovered_gold_copy(
    base: dict,
    model: dict,
    theme: dict,
    *,
    allow_gold_copy: bool = False,
) -> None:
    """Prove every source theme-copy value still present was explicitly supplied."""

    supplied = _override_blob(theme)
    compiled = json.dumps(model, ensure_ascii=False, sort_keys=True)
    source_values: set[str] = set()
    source_values.update(
        str((base.get("product") or {}).get(field) or "")
        for field in REQUIRED_PRODUCT_FIELDS
    )
    for page in base.get("pages") or []:
        for element in (page.get("elements") or {}).values():
            if element.get("kind") == "text" and element.get("replace") == "theme_copy":
                value = str(element.get("text") or "").strip()
                if len(value) >= 4:
                    source_values.add(value)
    leaked = sorted(
        value
        for value in source_values
        if value and value in compiled and (not allow_gold_copy or value not in supplied)
    )
    if leaked:
        raise ThemeContractError(
            [f"编译结果仍继承金样文案：{value!r}" for value in leaked]
        )

    base_assets = base.get("assets") or {}
    compiled_blob = json.dumps(model, ensure_ascii=False, sort_keys=True)
    leaked_asset_refs = sorted(
        {
            str(base_assets.get(key))
            for key in _replaceable_asset_keys(base) | GOLD_PACKAGING_EXTRA_KEYS
            if base_assets.get(key) and str(base_assets.get(key)) in compiled_blob
        }
    )
    if leaked_asset_refs:
        raise ThemeContractError(
            [f"编译结果仍引用金样可替换图片：{value}" for value in leaked_asset_refs]
        )


def merge_content(
    base: dict,
    theme: dict,
    *,
    normalized_assets: dict[str, str],
) -> tuple[dict, list[dict]]:
    """Compile a fully validated theme into the fixed courseware-3 framework."""
    model = deepcopy(base)
    product = theme["product"]
    stable_product_refs = {
        key: value
        for key, value in (base.get("product") or {}).items()
        if key.endswith("_asset")
    }
    model["product"] = stable_product_refs | {
        field: str(product[field]).strip() for field in REQUIRED_PRODUCT_FIELDS
    }
    model["project_id"] = str(
        theme.get("project_id") or f"courseware.theme.{theme.get('theme_id') or theme.get('slug') or 'custom'}"
    )
    model["title"] = str(
        theme.get("title") or f"{model['product']['display_name']} · 商品培训课件"
    ).strip()

    model_assets = model.setdefault("assets", {})
    for key in _replaceable_asset_keys(base) | GOLD_PACKAGING_EXTRA_KEYS:
        model_assets.pop(key, None)
    model_assets.update(normalized_assets)

    page_overrides = {p["id"]: p for p in theme.get("pages") or [] if "id" in p}
    for page in model.get("pages") or []:
        ov = page_overrides[page["id"]]
        elements_ov = ov.get("elements") or {}
        for role, target in (page.get("elements") or {}).items():
            if target.get("kind") == "text" and target.get("replace") == "theme_copy":
                target["text"] = _text_override(elements_ov[role])
                continue
            if (
                target.get("kind") == "image"
                and target.get("replace") == "theme_illustration"
            ):
                target["asset"] = _asset_key_override(elements_ov[role])

        chapter = (page.get("elements") or {}).get("chapter") or {}
        if chapter.get("kind") == "text":
            page["chapter"] = chapter.get("text")
        nav_roles = [
            (role, element)
            for role, element in (page.get("elements") or {}).items()
            if re.fullmatch(r"nav\d+", role) and element.get("kind") == "text"
        ]
        if nav_roles:
            page["nav"] = [
                str(element.get("text") or "")
                for role, element in sorted(nav_roles, key=lambda item: int(item[0][3:]))
            ]
        page["title"] = str(
            ov.get("title")
            or page.get("chapter")
            or SAFE_PAGE_TITLES.get(str(page.get("id")), str(page.get("id")))
        )

    model["_theme_captions"] = list(theme.get("captions") or [])
    model["_theme_narration_blocks"] = list(theme.get("narration_blocks") or [])
    _assert_no_uncovered_gold_copy(
        base,
        model,
        theme,
        allow_gold_copy=(
            theme.get("gold_sample") is True
            and str(theme.get("theme_id") or "").strip()
            == str(base.get("project_id") or "").strip()
        ),
    )
    return model, []


def copy_framework(gold: Path, dest: Path) -> None:
    if dest.exists():
        raise SystemExit(f"输出目录已存在，拒绝覆盖: {dest}")
    ignore = shutil.ignore_patterns(
        "node_modules",
        "dist",
        "out",
        "audio-work",
        "qa",
        "reference",
        "theme-packages",
        ".DS_Store",
        "*.mp4",
        "*.wav",
        "pptx-qa",
    )
    shutil.copytree(gold, dest, ignore=ignore)
    # Re-link node_modules like gold
    nm = dest / "node_modules"
    gold_nm = gold / "node_modules"
    if gold_nm.is_symlink() or gold_nm.exists():
        if nm.exists() or nm.is_symlink():
            nm.unlink()
        nm.symlink_to(gold_nm.resolve() if gold_nm.is_symlink() else gold_nm)


def purge_gold_replaceable_files(base: dict, gold: Path, dest: Path) -> None:
    """Remove every copied PNG whose pixels match a replaceable gold image."""

    gold_hashes = _gold_replaceable_hashes(base, gold)
    public = dest / "public"
    for target in public.rglob("*"):
        if target.is_file() and target.suffix.lower() == ".png":
            if _sha256(target) in gold_hashes:
                target.unlink()


def rewrite_gold_replaceable_references(
    base: dict,
    model: dict,
    gold: Path,
    dest: Path,
) -> None:
    """Rebind hard-coded runtime paths and prove no replaceable gold path remains."""

    base_pages = {str(page.get("id")): page for page in base.get("pages") or []}
    model_pages = {str(page.get("id")): page for page in model.get("pages") or []}
    model_assets = model.get("assets") or {}
    replacements: dict[str, str] = {}
    for page_id, base_page in base_pages.items():
        compiled_page = model_pages.get(page_id) or {}
        compiled_elements = compiled_page.get("elements") or {}
        for role, source_element in (base_page.get("elements") or {}).items():
            if source_element.get("replace") not in {
                "business_authorized",
                "theme_illustration",
            }:
                continue
            source_key = source_element.get("asset")
            compiled_key = (compiled_elements.get(role) or {}).get("asset")
            source_path = (base.get("assets") or {}).get(source_key)
            compiled_path = model_assets.get(compiled_key)
            if isinstance(source_path, str) and isinstance(compiled_path, str):
                replacements[source_path] = compiled_path

    source_paths = _gold_replaceable_paths(base, gold)
    runtime_files = [
        path
        for path in dest.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path.suffix.lower() in RUNTIME_TEXT_SUFFIXES
        and "node_modules" not in path.parts
    ]
    for path in runtime_files:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rewritten = content
        for source, target in replacements.items():
            rewritten = rewritten.replace(source, target)
        if rewritten != content:
            path.write_text(rewritten, encoding="utf-8")

    residual: list[str] = []
    for path in runtime_files:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for source in source_paths:
            if source in content:
                residual.append(f"{path.relative_to(dest)} -> {source}")
    if residual:
        raise ThemeContractError(
            [f"编译 workspace 仍引用金样可替换图片：{item}" for item in residual]
        )


def _normalized_captions(theme: dict) -> list[dict]:
    normalized: list[dict] = []
    cursor = 0.0
    for item in theme.get("captions") or []:
        if isinstance(item, str):
            duration = max(1.2, min(4.5, len(item) / 4.8))
            normalized.append(
                {
                    "start": round(cursor, 3),
                    "end": round(cursor + duration, 3),
                    "text": item.strip(),
                }
            )
            cursor += duration + 0.08
            continue
        start = float(item.get("start", cursor))
        end = float(item.get("end", start + max(1.2, len(item["text"]) / 4.8)))
        normalized.append({"start": start, "end": end, "text": item["text"].strip()})
        cursor = end + 0.08
    return normalized


def update_storyboard(dest: Path, model: dict, theme: dict) -> None:
    """Write a source-clean storyboard; never retain gold narration or brand assets."""

    sb_path = dest / "storyboard.json"
    sb = load_json(sb_path)
    sb["project_id"] = model["project_id"]
    sb["title"] = model["title"]
    sb["source_authority"] = {
        "mode": "theme-replication",
        "content": "business-approved-theme",
        "pixel_policy": "source-gold-layout-only-never-import-brand-pixels",
    }
    sb["audio"] = {
        "file": None,
        "source": model.get("voice_pack_id"),
        "status": "pending-theme-tts",
    }
    sb["packshot_policy"] = (
        "仅使用主题包内业务授权包装/Logo；已清除源金样包装，禁止回退。"
    )
    sb["theme_replication"] = {
        "source_gold": "sufuda-product-courseware-3-gold-v1",
        "theme_id": theme.get("theme_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    sb["assets"] = deepcopy(model.get("assets") or {})
    sb["captions"] = _normalized_captions(theme)
    if sb["captions"]:
        sb["duration"] = float(sb["captions"][-1]["end"])
    # Page ranges/types are the fixed timing contract; source chapter titles are copy.
    sb["pages"] = [
        {key: value for key, value in page.items() if key in {"id", "range", "type"}}
        for page in sb.get("pages") or []
    ]

    write_json(sb_path, sb)


def export_pptx(dest: Path, *, gold: Path = DEFAULT_GOLD) -> Path:
    # Run the canonical exporter from the source framework. Its artifact-tool
    # import is repository-relative; the compiled theme itself may live in /tmp
    # or a WorkBuddy job workspace at any depth.
    script = gold / "scripts" / "export-sufuda-pptx.mjs"
    if not script.exists():
        raise RuntimeError(f"缺少 PPTX 导出脚本: {script}")
    out = dest / "out" / f"{dest.name}_可编辑课件.pptx"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "node",
            str(script),
            "--model",
            str(dest / "content-model.json"),
            "--assets",
            str(dest / "public"),
            "--out",
            str(out),
        ],
        check=True,
        cwd=str(dest),
    )
    return out


def maybe_clone_tts(dest: Path, voice: Path, skip: bool) -> None:
    if skip:
        return
    script = ROOT / "scripts" / "generate_courseware_cloned_narration.py"
    if not script.exists():
        raise RuntimeError(f"缺少克隆旁白生成器: {script}")
    out_dir = dest / "audio-work" / "clone-theme-v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(script),
        "--storyboard",
        str(dest / "storyboard.json"),
        "--voice-pack",
        str(voice),
        "--out-dir",
        str(out_dir),
        "--copy-to-assets",
        str(dest / "public" / "assets" / "narration-cloned.wav"),
        "--apply-to-storyboard",
    ]
    print("Running TTS:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Replicate sufuda courseware gold to a new product theme")
    ap.add_argument("--theme", type=Path, required=True, help="Theme package directory containing theme.json")
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    ap.add_argument("--out-parent", type=Path, default=DEFAULT_OUT_PARENT)
    ap.add_argument("--out-slug", type=str, default=None, help="Output folder name under validation/courseware/")
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--skip-pptx", action="store_true")
    ap.add_argument(
        "--voice-pack",
        type=Path,
        default=ROOT / "production-library/voices/sufuda-courseware-pharmacist-v1",
    )
    args = ap.parse_args()

    theme_dir = args.theme.resolve()
    theme_json = theme_dir / "theme.json"
    if not theme_json.exists():
        raise SystemExit(f"缺少 theme.json: {theme_json}")

    theme = load_json(theme_json)
    gold = args.gold.resolve()
    slug = args.out_slug or theme.get("slug") or theme.get("theme_id") or theme_dir.name
    dest = (args.out_parent / slug).resolve()

    print(f"Gold:  {gold}")
    print(f"Theme: {theme_dir}")
    print(f"Out:   {dest}")

    base_model = load_json(gold / "content-model.json")
    try:
        resolved_assets = validate_theme_contract(
            base_model,
            theme,
            theme_dir=theme_dir,
            gold=gold,
            require_captions=not args.skip_tts,
        )
    except ThemeContractError as exc:
        raise SystemExit(f"主题包不完整，已阻断金样继承与正式生成：\n{exc}") from exc

    copy_framework(gold, dest)
    purge_gold_replaceable_files(base_model, gold, dest)
    normalized_assets = _normalized_asset_map(resolved_assets, dest)

    model, gaps = merge_content(
        base_model,
        theme,
        normalized_assets=normalized_assets,
    )
    write_json(dest / "content-model.json", {k: v for k, v in model.items() if not str(k).startswith("_")})

    # Rebuild layer-manifest from merged model
    layers = []
    for page in model.get("pages") or []:
        for role, el in (page.get("elements") or {}).items():
            layers.append(
                {
                    "element_id": el["id"],
                    "page_id": page["id"],
                    "page_type": page.get("type"),
                    "role": role,
                    "kind": el.get("kind"),
                    "slot": el.get("slot"),
                    "asset_key": el.get("asset"),
                    "replace_rule": el.get("replace"),
                    "default_text": el.get("text") if el.get("kind") == "text" else None,
                }
            )
    write_json(
        dest / "layer-manifest.json",
        {
            "project_id": model.get("project_id"),
            "template_id": model.get("template_id"),
            "style_pack_id": model.get("style_pack_id"),
            "status": "theme-replication",
            "source_theme": theme.get("theme_id"),
            "layer_count": len(layers),
            "layers": layers,
            "pages": [
                {
                    "id": p["id"],
                    "type": p.get("type"),
                    "title": p.get("title"),
                    "element_ids": [e["id"] for e in (p.get("elements") or {}).values()],
                }
                for p in model.get("pages") or []
            ],
        },
    )

    update_storyboard(dest, model, theme)
    rewrite_gold_replaceable_references(base_model, model, gold, dest)

    pptx_path: Path | None = None
    if not args.skip_pptx:
        pptx_path = export_pptx(dest, gold=gold)
        if not pptx_path.is_file():
            raise RuntimeError(f"PPTX 导出未产出文件: {pptx_path}")

    maybe_clone_tts(dest, args.voice_pack, args.skip_tts)

    report = {
        "ok": True,
        "contract": "courseware3-theme-complete-v1",
        "theme_id": theme.get("theme_id"),
        "slug": slug,
        "output": str(dest),
        "pptx": str(pptx_path) if pptx_path else None,
        "gaps": gaps,
        "gap_count": len(gaps),
        "next_steps": [
            "核对 content-model 文案与业务审核稿哈希一致",
            "逐页检查 editable PPTX 的文字、图片与溢出",
            "去掉 --skip-tts 生成克隆旁白后 npm run render",
            "业务确认前不要晋升到 templates/settled/",
        ],
    }
    write_json(dest / "gap-report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
