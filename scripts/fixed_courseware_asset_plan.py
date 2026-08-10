#!/usr/bin/env python3
"""Asset plans for fixed PPTX courseware (disease-product-scenario + green).

Mirrors the component-route split:
  business_provides  → authorized packshots / partner packs (business only)
  system_generates   → knowledge / symptom / audience / care illustrations
                       (WorkBuddy generates after content approval)

Bindings JSON shape (same as component visual):
  { "script_path": "/abs/path/to.png", ... }
  or { "bindings": { ... } }
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from gold_asset_guard import check_image_file, is_authorized_gold_theme
from product_pptx_asset_plan import asset_file_info, render_asset_plan_markdown

ROOT = Path(__file__).resolve().parents[1]

_PENDING_TOKENS = (
    "待确认",
    "待业务",
    "待补充",
    "待审核",
    "TODO",
    "TBD",
    "占位",
)


def _contains_pending(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_pending(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_pending(item) for item in value)
    text = str(value or "")
    return any(token in text for token in _PENDING_TOKENS)


def _at(model: dict[str, Any], script_path: str) -> Any:
    current: Any = model
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", script_path):
        if part.startswith("[") and part.endswith("]"):
            index = int(part[1:-1])
            if not isinstance(current, list) or index >= len(current):
                return None
            current = current[index]
        else:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
    return current


def set_at(model: dict[str, Any], script_path: str, value: Any) -> None:
    """Set model[script_path] supporting a.b[0].c paths."""
    tokens: list[str | int] = []
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", script_path):
        if part.startswith("[") and part.endswith("]"):
            tokens.append(int(part[1:-1]))
        else:
            tokens.append(part)
    if not tokens:
        raise ValueError(f"empty script_path: {script_path!r}")
    current: Any = model
    for index, token in enumerate(tokens[:-1]):
        nxt_token = tokens[index + 1]
        if isinstance(token, int):
            if not isinstance(current, list):
                raise ValueError(f"path {script_path} expects list at [{token}]")
            while len(current) <= token:
                current.append([] if isinstance(nxt_token, int) else {})
            if current[token] is None:
                current[token] = [] if isinstance(nxt_token, int) else {}
            current = current[token]
        else:
            if not isinstance(current, dict):
                raise ValueError(f"path {script_path} expects object at {token}")
            if token not in current or current[token] is None:
                current[token] = [] if isinstance(nxt_token, int) else {}
            current = current[token]
    last = tokens[-1]
    if isinstance(last, int):
        if not isinstance(current, list):
            raise ValueError(f"path {script_path} expects list at leaf")
        while len(current) <= last:
            current.append(None)
        current[last] = value
    else:
        if not isinstance(current, dict):
            raise ValueError(f"path {script_path} expects object at leaf")
        current[last] = value


def _slot_item(
    *,
    script_path: str,
    semantic: str,
    role: str,
    existing: Any,
    content_context: Any = None,
    width: int = 720,
    height: int = 720,
    fit: str = "contain",
    subject_coverage: str = "65%-85%",
    business: bool = False,
    required: bool = True,
    template_slug: str | None = None,
    allow_gold: bool = False,
) -> dict[str, Any]:
    file_info = asset_file_info(existing)
    # asset_file_info blocks gold via global hashes; for plan display also mark gold
    src = str(file_info["path"]) if file_info.get("ok") else None
    if src and not allow_gold and template_slug:
        gold_hits = check_image_file(
            src,
            binding=script_path,
            template_slug=template_slug,
            allow_gold=False,
        )
        if gold_hits:
            file_info = {
                **file_info,
                "ok": False,
                "error": "gold_source_sha256",
                "gold_blockers": gold_hits,
            }
            src = None

    pending = _contains_pending(
        content_context if content_context is not None else semantic
    )
    if business:
        status = "ready" if src else ("missing" if required else "optional_missing")
    else:
        if pending:
            status = "blocked_pending_content"
        elif src:
            status = "ready"
        else:
            status = "generate_after_content_approval"

    item: dict[str, Any] = {
        "script_path": script_path,
        "semantic": semantic,
        "role": role,
        "status": status,
        "existing_src": src,
        "asset_validation": file_info,
        "width": width,
        "height": height,
        "aspect_ratio": f"{width}:{height}",
        "fit": fit,
        "safe_area": "center",
        "subject_coverage": subject_coverage,
        "prompt_constraints": [
            "只生成当前图槽所需内容，不设计整页 PPT",
            "不在图片内部预留文案区，不重复 PPT 标题或正文",
            "无品牌包装、Logo、批准文号、水印",
            "与本任务唯一 style_pack 保持一致",
            "禁止复用任一签样金样像素（gold_asset_guard）",
        ],
        "binding": {
            "kind": "image_path",
            "target": script_path,
            "value_shape": "<generated-file>",
        },
    }
    if business:
        item["provider"] = "business"
        item["required"] = required
        item["asset"] = semantic
        item["reason"] = "品牌/包装或竞品事实只能使用业务授权真图，禁止 AI 仿造。"
    else:
        item["provider"] = "system"
        item["evidence_boundary"] = (
            "概念示意图；不得充当功效、批准、含量或本品包装证据。"
        )
    return item


def build_disease_asset_plan(
    model: dict[str, Any],
    *,
    theme: str,
    template_slug: str = "disease-product-scenario-v1",
) -> dict[str, Any]:
    allow_gold = is_authorized_gold_theme(
        template_slug=template_slug, theme=theme, model=model
    )
    business: list[dict[str, Any]] = []
    system: list[dict[str, Any]] = []

    product = model.get("product") if isinstance(model.get("product"), dict) else {}
    pages = model.get("pages") if isinstance(model.get("pages"), dict) else {}
    cover = pages.get("cover") if isinstance(pages.get("cover"), dict) else {}
    disease = model.get("disease") if isinstance(model.get("disease"), dict) else {}
    weighted = model.get("weighted") if isinstance(model.get("weighted"), dict) else {}

    business.append(
        _slot_item(
            script_path="product.image",
            semantic=f"{theme} 本品正式包装图",
            role="product_packshot",
            existing=product.get("image"),
            width=640,
            height=800,
            fit="contain",
            business=True,
            template_slug=template_slug,
            allow_gold=allow_gold,
        )
    )
    business.append(
        _slot_item(
            script_path="pages.cover.image",
            semantic=f"{theme} 封面商品图（通常同本品包装）",
            role="cover_packshot",
            existing=cover.get("image"),
            width=640,
            height=800,
            fit="contain",
            business=True,
            required=True,
            template_slug=template_slug,
            allow_gold=allow_gold,
        )
    )

    for index, item in enumerate(weighted.get("items") or []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("title") or f"权重商品 {index + 1}")
        business.append(
            _slot_item(
                script_path=f"weighted.items[{index}].image",
                semantic=f"权重/对标商品包装图 · {name}",
                role="weighted_packshot",
                existing=item.get("image"),
                content_context=item,
                width=640,
                height=800,
                fit="contain",
                business=True,
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    definition = (
        pages.get("disease_definition")
        if isinstance(pages.get("disease_definition"), dict)
        else {}
    )
    disease_name = str(disease.get("name") or theme)
    system.append(
        _slot_item(
            script_path="pages.disease_definition.image",
            semantic=f"疾病定义主图 · {disease_name}",
            role="disease_definition",
            existing=definition.get("image"),
            content_context=disease.get("definition") or disease_name,
            width=960,
            height=720,
            fit="cover",
            template_slug=template_slug,
            allow_gold=allow_gold,
        )
    )

    for index, symptom in enumerate(disease.get("symptoms") or []):
        if not isinstance(symptom, dict):
            continue
        title = str(symptom.get("name") or symptom.get("title") or f"症状 {index + 1}")
        system.append(
            _slot_item(
                script_path=f"disease.symptoms[{index}].image",
                semantic=f"典型表现插图 · {title}",
                role="symptom",
                existing=symptom.get("image"),
                content_context=symptom,
                width=640,
                height=640,
                fit="contain",
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    for index, audience in enumerate(product.get("audience") or []):
        if not isinstance(audience, dict):
            continue
        title = str(
            audience.get("name") or audience.get("title") or f"重点人群 {index + 1}"
        )
        system.append(
            _slot_item(
                script_path=f"product.audience[{index}].image",
                semantic=f"重点人群插图 · {title}",
                role="audience",
                existing=audience.get("image"),
                content_context=audience,
                width=640,
                height=640,
                fit="contain",
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    for index, care in enumerate(product.get("daily_care") or []):
        if not isinstance(care, dict):
            continue
        title = str(care.get("title") or care.get("name") or f"日常护理 {index + 1}")
        system.append(
            _slot_item(
                script_path=f"product.daily_care[{index}].image",
                semantic=f"日常护理插图 · {title}",
                role="daily_care",
                existing=care.get("image"),
                content_context=care,
                width=640,
                height=640,
                fit="contain",
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    return {
        "schema": "fixed-courseware-asset-plan/v1",
        "template_slug": template_slug,
        "theme": theme,
        "policy": {
            "business_never_runs_image_prompts": True,
            "generate_only_after_content_approval": True,
            "first_representative_slot_qa": True,
            "no_fake_brand_packaging": True,
            "gold_pixels_forbidden": True,
            "style_pack_id": "style-pack.dashenlin-courseware-green-v1",
        },
        "business_provides": business,
        "system_generates": system,
        "template_reuses": [
            "已签样 18 页版式、栏目顺序与绿色 style pack",
            "页眉页脚、标题构件与表格结构",
            "不继承穿心莲金样文案与源图像素",
        ],
    }


def _courseware3_page_map(theme: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(page.get("id")): page
        for page in (theme.get("pages") or [])
        if isinstance(page, dict) and page.get("id")
    }


def _courseware3_override_asset_key(value: Any) -> str | None:
    if isinstance(value, dict):
        raw = value.get("asset")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _courseware3_illustration_slots(
    base: dict[str, Any],
    theme: dict[str, Any] | None = None,
) -> list[tuple[str, str, str]]:
    """Return (page_id, role, asset_key) for every theme_illustration slot.

    Prefer the theme page element override asset key (e.g. illustration.flu.x)
    when present; otherwise fall back to the gold base default asset key.
    One assets.* key emits one system slot (first page/role wins for label).
    """
    page_map = _courseware3_page_map(theme or {})
    slots: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for page in base.get("pages") or []:
        if not isinstance(page, dict):
            continue
        page_id = str(page.get("id") or "")
        override = page_map.get(page_id) or {}
        element_overrides = (
            override.get("elements") if isinstance(override.get("elements"), dict) else {}
        )
        for role, element in (page.get("elements") or {}).items():
            if not isinstance(element, dict):
                continue
            if element.get("kind") != "image":
                continue
            if element.get("replace") != "theme_illustration":
                continue
            key = _courseware3_override_asset_key(element_overrides.get(role))
            if not key:
                key = str(element.get("asset") or "").strip()
            if not key:
                key = f"illustration.{page_id}.{role}"
            if key in seen:
                continue
            seen.add(key)
            slots.append((page_id, str(role), key))
    return slots


def _courseware3_business_keys(base: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for page in base.get("pages") or []:
        if not isinstance(page, dict):
            continue
        for element in (page.get("elements") or {}).values():
            if not isinstance(element, dict):
                continue
            if element.get("kind") != "image":
                continue
            if element.get("replace") != "business_authorized":
                continue
            key = str(element.get("asset") or "").strip()
            if key and key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def build_courseware3_asset_plan(
    theme: dict[str, Any],
    *,
    theme_name: str,
    base: dict[str, Any],
    theme_dir: Path | None = None,
    template_slug: str = "sufuda-mabaloshawei-product-courseware-3-v1",
) -> dict[str, Any]:
    """Asset plan for courseware3: business pack/logo vs 23 theme illustrations."""
    allow_gold = is_authorized_gold_theme(
        template_slug=template_slug, theme=theme_name, model=theme
    )
    assets = theme.get("assets") if isinstance(theme.get("assets"), dict) else {}
    root = Path(theme_dir) if theme_dir else None

    def _existing(key: str) -> Any:
        raw = assets.get(key)
        if not isinstance(raw, str) or not raw.strip():
            return None
        path = Path(raw).expanduser()
        if not path.is_absolute() and root is not None:
            path = root / path
        return str(path) if path.is_file() else raw

    business: list[dict[str, Any]] = []
    for key in _courseware3_business_keys(base):
        role = "product_packshot" if key == "packGroup" else "business_authorized"
        business.append(
            _slot_item(
                script_path=f"assets.{key}",
                semantic=(
                    f"{theme_name} 本品正式包装图"
                    if key == "packGroup"
                    else f"业务授权真图 · {key}"
                ),
                role=role,
                existing=_existing(key),
                width=640,
                height=800,
                fit="contain",
                business=True,
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    system: list[dict[str, Any]] = []
    page_map = _courseware3_page_map(theme)
    for page_id, role, key in _courseware3_illustration_slots(base, theme):
        # Only use page title / non-pending text for status — not whole elements map
        page_override = page_map.get(page_id) or {}
        content_context = page_override.get("title") or page_id
        system.append(
            _slot_item(
                script_path=f"assets.{key}",
                semantic=f"主题插图 · {page_id}.{role}",
                role="theme_illustration",
                existing=_existing(key),
                content_context=content_context,
                width=720,
                height=720,
                fit="contain",
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    return {
        "schema": "fixed-courseware-asset-plan/v1",
        "template_slug": template_slug,
        "theme": theme_name,
        "policy": {
            "business_never_runs_image_prompts": True,
            "generate_only_after_content_approval": True,
            "first_representative_slot_qa": True,
            "no_fake_brand_packaging": True,
            "gold_pixels_forbidden": True,
            "style_pack_id": str(
                theme.get("style_pack_id")
                or base.get("style_pack_id")
                or "style-pack.sufuda-courseware-green-v1"
            ),
        },
        "business_provides": business,
        "system_generates": system,
        "template_reuses": [
            "已签样课件3（13 页）版式、栏目与 style pack",
            "不继承速福达金样文案与源图像素",
        ],
    }


def build_ingredient_asset_plan(
    theme: dict[str, Any],
    *,
    theme_name: str,
    theme_dir: Path | None = None,
    template_slug: str = "kangaisen-lycopene-health-edu-v1",
) -> dict[str, Any]:
    """Asset plan for 20-page ingredient health edu: all image slots are system-generated."""
    allow_gold = is_authorized_gold_theme(
        template_slug=template_slug, theme=theme_name, model=theme
    )
    assets = theme.get("assets") if isinstance(theme.get("assets"), dict) else {}
    root = Path(theme_dir) if theme_dir else None

    def _resolve_asset_key(key: str) -> Any:
        if not key:
            return None
        raw = assets.get(key)
        if not isinstance(raw, str) or not raw.strip():
            return None
        path = Path(raw).expanduser()
        if not path.is_absolute() and root is not None:
            path = root / path
        return str(path) if path.is_file() else raw

    system: list[dict[str, Any]] = []
    pages = theme.get("pages") if isinstance(theme.get("pages"), list) else []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        slide = page.get("slide") or (index + 1)
        texts = page.get("texts") if isinstance(page.get("texts"), dict) else {}
        images = page.get("images") if isinstance(page.get("images"), dict) else {}
        for image_id, asset_key in images.items():
            key = str(asset_key or "").strip()
            existing = _resolve_asset_key(key) if key else None
            system.append(
                _slot_item(
                    script_path=f"pages[{index}].images.{image_id}",
                    semantic=f"第{slide}页插图 · {image_id}",
                    role="slide_image",
                    existing=existing,
                    content_context=texts or f"slide-{slide}",
                    width=960,
                    height=720,
                    fit="cover",
                    template_slug=template_slug,
                    allow_gold=allow_gold,
                )
            )

    template_images = (
        theme.get("template_images")
        if isinstance(theme.get("template_images"), dict)
        else {}
    )
    for slot_key, asset_key in template_images.items():
        key = str(asset_key or "").strip()
        existing = _resolve_asset_key(key) if key else None
        system.append(
            _slot_item(
                script_path=f"template_images.{slot_key}",
                semantic=f"母版/版式图 · {slot_key}",
                role="template_image",
                existing=existing,
                content_context=theme_name,
                width=960,
                height=720,
                fit="cover",
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    return {
        "schema": "fixed-courseware-asset-plan/v1",
        "template_slug": template_slug,
        "theme": theme_name,
        "policy": {
            "business_never_runs_image_prompts": True,
            "generate_only_after_content_approval": True,
            "first_representative_slot_qa": True,
            "no_fake_brand_packaging": True,
            "gold_pixels_forbidden": True,
            "style_pack_id": str(
                theme.get("style_pack_id") or "style-pack.lycopene-health-edu-cream-red-v1"
            ),
        },
        "business_provides": [],
        "system_generates": system,
        "template_reuses": [
            "已签样 20 页米白番茄红版式与 15 类页型",
            "不继承康爱森金样医学正文与源图像素",
        ],
    }


def build_green_asset_plan(
    model: dict[str, Any],
    *,
    theme: str,
    template_slug: str = "product-courseware-green-v1",
) -> dict[str, Any]:
    allow_gold = is_authorized_gold_theme(
        template_slug=template_slug, theme=theme, model=model
    )
    business: list[dict[str, Any]] = []
    system: list[dict[str, Any]] = []

    pages = {
        str(page.get("id")): page
        for page in (model.get("pages") or [])
        if isinstance(page, dict) and page.get("id")
    }
    overview = pages.get("product-overview") or {}
    product = overview.get("product") if isinstance(overview.get("product"), dict) else {}
    business.append(
        _slot_item(
            script_path="product-overview.product.image_slot",
            semantic=f"{theme} 本品正式包装图",
            role="product_packshot",
            existing=product.get("image_slot"),
            width=640,
            height=800,
            fit="contain",
            business=True,
            template_slug=template_slug,
            allow_gold=allow_gold,
        )
    )

    combo = pages.get("combination-guidance") or {}
    for field in ("primary_asset", "primary_pack_asset", "product_asset"):
        if field in combo:
            business.append(
                _slot_item(
                    script_path=f"combination-guidance.{field}",
                    semantic=f"{theme} 联合页本品包装图",
                    role="combo_primary",
                    existing=combo.get(field),
                    width=640,
                    height=800,
                    fit="contain",
                    business=True,
                    template_slug=template_slug,
                    allow_gold=allow_gold,
                )
            )
            break
    for index, row in enumerate(combo.get("rows") or []):
        if not isinstance(row, dict):
            continue
        partner = str(row.get("partner") or f"搭档 {index + 1}")
        business.append(
            _slot_item(
                script_path=f"combination-guidance.rows[{index}].partner_asset",
                semantic=f"联合搭档包装图 · {partner}",
                role="partner_packshot",
                existing=row.get("partner_asset"),
                content_context=row,
                width=640,
                height=800,
                fit="contain",
                business=True,
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    benchmark = pages.get("product-benchmark") or {}
    for row_index, row in enumerate(benchmark.get("rows") or []):
        if not isinstance(row, dict) or row.get("label") != "产品展示":
            continue
        values = row.get("values") or []
        labels = (f"{theme} 本品", "竞品包装")
        for index in range(min(2, len(values))):
            business.append(
                _slot_item(
                    script_path=f"product-benchmark.rows[{row_index}].values[{index}]",
                    semantic=f"品种对标 · {labels[index]}",
                    role="benchmark_pack",
                    existing=values[index],
                    width=640,
                    height=800,
                    fit="contain",
                    business=True,
                    template_slug=template_slug,
                    allow_gold=allow_gold,
                )
            )

    precautions = pages.get("precautions") or {}
    for index, slot in enumerate(precautions.get("illustration_slots") or []):
        if not isinstance(slot, dict):
            continue
        title = str(slot.get("title") or f"注意事项 {index + 1}")
        existing = slot.get("asset") or slot.get("file") or slot.get("src")
        system.append(
            _slot_item(
                script_path=f"precautions.illustration_slots[{index}].asset",
                semantic=f"注意事项插图 · {title}",
                role="precaution",
                existing=existing,
                content_context=slot,
                width=720,
                height=540,
                fit="cover",
                template_slug=template_slug,
                allow_gold=allow_gold,
            )
        )

    return {
        "schema": "fixed-courseware-asset-plan/v1",
        "template_slug": template_slug,
        "theme": theme,
        "policy": {
            "business_never_runs_image_prompts": True,
            "generate_only_after_content_approval": True,
            "first_representative_slot_qa": True,
            "no_fake_brand_packaging": True,
            "gold_pixels_forbidden": True,
            "style_pack_id": "style-pack.dashenlin-courseware-green-v1",
        },
        "business_provides": business,
        "system_generates": system,
        "template_reuses": [
            "已签样 5 页绿色版式与栏目结构",
            "不继承金银花金样文案与源图像素",
        ],
    }


def formal_asset_blockers(plan: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for item in plan.get("business_provides") or []:
        if item.get("required") is False:
            continue
        if item.get("status") != "ready":
            reason = (item.get("asset_validation") or {}).get("error")
            blockers.append(
                f"缺少业务授权真图：{item.get('semantic') or item.get('asset')}"
                f"（{reason or item.get('status') or 'missing'}）"
            )
    for item in plan.get("system_generates") or []:
        status = item.get("status")
        if status == "blocked_pending_content":
            blockers.append(f"内容待确认，不能生图：{item.get('semantic')}")
        elif status != "ready":
            reason = (item.get("asset_validation") or {}).get("error")
            blockers.append(
                f"主题插图尚未补齐：{item.get('semantic')}（{reason or status}）"
            )
    return blockers


def content_asset_notes(plan: dict[str, Any]) -> list[str]:
    """Non-blocking notes for draft gaps: what WorkBuddy must generate after content."""
    notes: list[str] = []
    for item in plan.get("system_generates") or []:
        if item.get("status") in {
            "generate_after_content_approval",
            "blocked_pending_content",
        }:
            notes.append(
                f"系统插图待生成：{item.get('semantic')} → {item.get('script_path')}"
            )
        elif item.get("status") != "ready":
            notes.append(
                f"系统插图未就绪：{item.get('semantic')}（{item.get('status')}）"
            )
    for item in plan.get("business_provides") or []:
        if item.get("required") is False:
            continue
        if item.get("status") != "ready":
            notes.append(
                f"业务真图待提供：{item.get('semantic') or item.get('asset')}"
            )
    return notes


def apply_image_bindings(
    model: dict[str, Any],
    mapping: dict[str, str],
    plan: dict[str, Any],
    *,
    green: bool = False,
    mode: str = "disease",
    base: dict[str, Any] | None = None,
) -> list[str]:
    """Apply {script_path: file} into model. Returns list of applied paths.

    mode:
      - disease: nested content-model paths via set_at
      - green: green pages[] heterogeneous keys
      - courseware3: theme.assets.* (+ page element wiring when base given)
      - ingredient: pages[i].images / template_images + assets map
    """
    plan_paths = {
        str(item.get("script_path"))
        for item in (plan.get("system_generates") or [])
        + (plan.get("business_provides") or [])
    }
    applied: list[str] = []
    for target, source in mapping.items():
        if target not in plan_paths:
            raise ValueError(f"素材绑定目标不在当前计划中: {target}")
        path = Path(source).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"生成素材不存在: {path}")
        if green or mode == "green":
            _set_green_binding(model, target, str(path))
        elif mode == "courseware3":
            _set_courseware3_binding(model, target, str(path), base=base)
        elif mode == "ingredient":
            _set_ingredient_binding(model, target, str(path))
        else:
            set_at(model, target, str(path))
        applied.append(target)
    return applied


def _set_courseware3_binding(
    theme: dict[str, Any],
    script_path: str,
    value: str,
    *,
    base: dict[str, Any] | None = None,
) -> None:
    if not script_path.startswith("assets."):
        raise ValueError(f"课件3绑定路径须为 assets.<key>：{script_path}")
    key = script_path[len("assets.") :]
    if not key:
        raise ValueError(f"课件3绑定缺少 asset key：{script_path}")
    theme.setdefault("assets", {})[key] = value
    if not isinstance(base, dict):
        return
    # Ensure every illustration role that should use this key has an override
    pages = theme.setdefault("pages", [])
    if not isinstance(pages, list):
        return
    page_map = {
        str(page.get("id")): page
        for page in pages
        if isinstance(page, dict) and page.get("id")
    }
    for page_id, role, slot_key in _courseware3_illustration_slots(base, theme):
        if slot_key != key:
            # Also wire base default key matches when theme has no override yet
            continue
        override = page_map.get(page_id)
        if override is None:
            override = {"id": page_id, "elements": {}}
            pages.append(override)
            page_map[page_id] = override
        elements = override.setdefault("elements", {})
        if not isinstance(elements, dict):
            override["elements"] = {}
            elements = override["elements"]
        elements[str(role)] = {"asset": key}
    # If theme had no override yet, also match base default asset keys
    for page in base.get("pages") or []:
        if not isinstance(page, dict):
            continue
        page_id = str(page.get("id") or "")
        for role, element in (page.get("elements") or {}).items():
            if not isinstance(element, dict):
                continue
            if element.get("kind") != "image":
                continue
            if element.get("replace") != "theme_illustration":
                continue
            if str(element.get("asset") or "") != key:
                continue
            override = page_map.get(page_id)
            if override is None:
                override = {"id": page_id, "elements": {}}
                pages.append(override)
                page_map[page_id] = override
            elements = override.setdefault("elements", {})
            if not isinstance(elements, dict):
                override["elements"] = {}
                elements = override["elements"]
            if str(role) not in elements:
                elements[str(role)] = {"asset": key}


def _set_ingredient_binding(
    theme: dict[str, Any], script_path: str, value: str
) -> None:
    assets = theme.setdefault("assets", {})
    if not isinstance(assets, dict):
        theme["assets"] = {}
        assets = theme["assets"]

    if script_path.startswith("template_images."):
        slot_key = script_path[len("template_images.") :]
        template_images = theme.setdefault("template_images", {})
        if not isinstance(template_images, dict):
            raise ValueError("template_images 必须是对象")
        asset_key = str(template_images.get(slot_key) or "").strip()
        if not asset_key:
            safe = re.sub(r"[^A-Za-z0-9._-]+", "-", slot_key).strip("-") or "tmpl"
            asset_key = f"template-{safe}"
        assets[asset_key] = value
        template_images[slot_key] = asset_key
        return

    m = re.fullmatch(r"pages\[(\d+)\]\.images\.(.+)", script_path)
    if not m:
        raise ValueError(f"无法解析成分课型绑定路径: {script_path}")
    index = int(m.group(1))
    image_id = m.group(2)
    pages = theme.setdefault("pages", [])
    if not isinstance(pages, list):
        raise ValueError("pages 必须是数组")
    while len(pages) <= index:
        pages.append({"slide": len(pages) + 1, "texts": {}, "images": {}})
    page = pages[index]
    if not isinstance(page, dict):
        raise ValueError(f"pages[{index}] 格式错误")
    images = page.setdefault("images", {})
    if not isinstance(images, dict):
        page["images"] = {}
        images = page["images"]
    asset_key = str(images.get(image_id) or "").strip()
    if not asset_key:
        slide = page.get("slide") or (index + 1)
        safe_id = re.sub(r"[^A-Za-z0-9._-]+", "-", image_id).strip("-") or "img"
        asset_key = f"s{int(slide):02d}-{safe_id}"
    assets[asset_key] = value
    images[image_id] = asset_key


def _set_green_binding(model: dict[str, Any], script_path: str, value: str) -> None:
    """Green model uses pages[] + heterogeneous keys; map plan paths carefully."""
    pages = {
        str(page.get("id")): page
        for page in (model.get("pages") or [])
        if isinstance(page, dict) and page.get("id")
    }
    if script_path == "product-overview.product.image_slot":
        overview = pages.get("product-overview") or {}
        overview.setdefault("product", {})["image_slot"] = value
        return
    if script_path.startswith("combination-guidance."):
        combo = pages.get("combination-guidance") or {}
        rest = script_path[len("combination-guidance.") :]
        if rest in ("primary_asset", "primary_pack_asset", "product_asset"):
            combo[rest] = value
            return
        m = re.fullmatch(r"rows\[(\d+)\]\.partner_asset", rest)
        if m:
            rows = combo.setdefault("rows", [])
            index = int(m.group(1))
            while len(rows) <= index:
                rows.append({})
            rows[index]["partner_asset"] = value
            return
    if script_path.startswith("product-benchmark."):
        m = re.fullmatch(
            r"product-benchmark\.rows\[(\d+)\]\.values\[(\d+)\]", script_path
        )
        if m:
            bench = pages.get("product-benchmark") or {}
            rows = bench.setdefault("rows", [])
            ri, vi = int(m.group(1)), int(m.group(2))
            while len(rows) <= ri:
                rows.append({"label": "产品展示", "values": []})
            row = rows[ri]
            values = list(row.get("values") or [])
            while len(values) <= vi:
                values.append("")
            values[vi] = value
            row["values"] = values
            return
    if script_path.startswith("precautions.illustration_slots["):
        m = re.fullmatch(
            r"precautions\.illustration_slots\[(\d+)\]\.asset", script_path
        )
        if m:
            precautions = pages.get("precautions") or {}
            slots = precautions.setdefault("illustration_slots", [])
            index = int(m.group(1))
            while len(slots) <= index:
                slots.append({"title": f"注意事项 {len(slots) + 1}", "asset": ""})
            slots[index]["asset"] = value
            return
    raise ValueError(f"无法解析绿色课型绑定路径: {script_path}")


def plan_visual_manifest(plan: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Hash every system_generates file for visual approval record."""
    import hashlib

    manifest: dict[str, dict[str, str]] = {}
    for item in plan.get("system_generates") or []:
        target = str(item.get("script_path") or "")
        source = str(item.get("existing_src") or "")
        path = Path(source).expanduser().resolve() if source else None
        if not target or path is None or not path.is_file():
            raise RuntimeError(
                f"主题插图未绑定真实文件：{item.get('semantic') or target}"
            )
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        manifest[target] = {"path": str(path), "sha256": digest.hexdigest()}
    return manifest


# Re-export markdown helper so callers need one import
__all__ = [
    "apply_image_bindings",
    "build_courseware3_asset_plan",
    "build_disease_asset_plan",
    "build_green_asset_plan",
    "build_ingredient_asset_plan",
    "content_asset_notes",
    "formal_asset_blockers",
    "plan_visual_manifest",
    "render_asset_plan_markdown",
    "set_at",
]
