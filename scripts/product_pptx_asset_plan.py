#!/usr/bin/env python3
"""Build the business/system/template asset split for component product PPT drafts."""

from __future__ import annotations

import hashlib
import json
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_PATH = (
    ROOT
    / "production-library"
    / "page-types"
    / "product-training"
    / "image-slot-contracts.json"
)

CW4_SETTLED_DIR = (
    ROOT
    / "production-library"
    / "templates"
    / "settled"
    / "fuler-fanqiehongsu-product-courseware-4-v1"
)
CW4_VALIDATION_MEDIA_DIR = (
    ROOT
    / "production-library"
    / "validation"
    / "courseware"
    / "product-courseware-4-faithful-replica-v1"
    / "assets"
    / "generated"
)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
CW4_SOURCE_FILENAMES = {
    "arrow-red-ref.png",
    "arrow-red.png",
    "audience-beauty.png",
    "audience-weak.png",
    "badge-hot-recommend.png",
    "couple.png",
    "five-tomatoes.png",
    "flex-arm-cutout.png",
    "flex-arm-ref.png",
    "flex-arm.png",
    "icon-check-red.png",
    "icon-chevron-lime.png",
    "icon-chevron-white.png",
    "map-xinjiang.png",
    "mark-red-x-hand.png",
    "mark-red-x.png",
    "nk-cell-labeled.png",
    "nk-cell.png",
    "o2-cutout.png",
    "o2.png",
    "prostate-diagram.png",
    "skincare-woman.png",
    "slot-pack-bottle.png",
    "slot-pack-box-a.png",
    "slot-pack-box-b.png",
    "slot-pack-lycopene.png",
    "slot-pack-vite.png",
    "slot-pack-zinc.png",
    "slot-photo-tomato.jpg",
    "slot-photo-tomato.png",
    "slot-photo-vine-cutout.png",
    "slot-photo-vine.jpg",
    "slot-photo-vine.png",
    "slot-time-magazine.png",
    "softgel.png",
    "tomato.png",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def cw4_gold_image_hashes() -> frozenset[str]:
    """Hashes of every image embedded in the settled CW4 canonical artifacts."""
    hashes: set[str] = set()
    for pptx in CW4_SETTLED_DIR.glob("*.pptx"):
        try:
            with zipfile.ZipFile(pptx) as archive:
                for member in archive.namelist():
                    if member.startswith("ppt/media/") and not member.endswith("/"):
                        hashes.add(_sha256_bytes(archive.read(member)))
        except (OSError, zipfile.BadZipFile):
            continue
    if CW4_VALIDATION_MEDIA_DIR.is_dir():
        for image in CW4_VALIDATION_MEDIA_DIR.iterdir():
            if image.is_file() and image.suffix.lower() in IMAGE_SUFFIXES:
                try:
                    hashes.add(_sha256_file(image))
                except OSError:
                    continue
    # Also union global settled gold media (cross-template fail-closed).
    try:
        from gold_asset_guard import all_settled_gold_media_hashes

        hashes |= set(all_settled_gold_media_hashes())
    except Exception:
        pass
    return frozenset(hashes)


def asset_file_info(value: Any, *, base_dir: Path = ROOT) -> dict[str, Any]:
    """Resolve and validate one formal visual without trusting a non-empty string."""
    source_kind = ""
    src: Any = value
    if isinstance(value, dict):
        src = value.get("src") or value.get("file") or value.get("asset")
        source_kind = str(value.get("source_kind") or "").strip()
    normalized = str(src or "").strip()
    result: dict[str, Any] = {
        "ok": False,
        "src": normalized or None,
        "path": None,
        "sha256": None,
        "source_kind": source_kind,
        "error": "missing",
    }
    if not normalized:
        return result
    if normalized.startswith("__missing__/"):
        result["error"] = "placeholder"
        return result
    path = Path(normalized).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()
    result["path"] = str(path)
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        result["error"] = "unsupported_image_type"
        return result
    if path.name.lower() in CW4_SOURCE_FILENAMES:
        result["error"] = "cw4_source_filename"
        return result
    if not path.is_file():
        result["error"] = "file_not_found"
        return result
    try:
        digest = _sha256_file(path)
    except OSError:
        result["error"] = "file_unreadable"
        return result
    result["sha256"] = digest
    if digest in cw4_gold_image_hashes():
        result["error"] = "cw4_source_sha256"
        return result
    result["ok"] = True
    result["error"] = None
    return result


def _visual_src(value: Any) -> str | None:
    info = asset_file_info(value)
    return str(info["path"]) if info["ok"] else None


def _slot(contracts: dict[str, Any], slot_id: str) -> dict[str, Any]:
    defaults = contracts.get("defaults") or {}
    current = (contracts.get("slots") or {}).get(slot_id) or {}
    return {**defaults, **current, "slot_id": slot_id}


def _feature_slot_id(title: str, index: int) -> str:
    if "产地" in title:
        return "feature.origin.visual"
    if "原料" in title:
        return "feature.material.visual"
    if "含量" in title or "粒" in title:
        return "feature.content.visual"
    return (
        "feature.origin.visual",
        "feature.material.visual",
        "feature.content.visual",
    )[min(index, 2)]


def _contains_pending(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_pending(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_pending(item) for item in value)
    text = str(value or "")
    return any(token in text for token in ("待确认", "待业务", "待补充"))


def _generated_item(
    contracts: dict[str, Any],
    *,
    slot_id: str,
    script_path: str,
    semantic: str,
    existing: Any = None,
    content_context: Any = None,
    binding: dict[str, Any] | None = None,
    evidence_boundary: str | None = None,
) -> dict[str, Any]:
    spec = _slot(contracts, slot_id)
    file_info = asset_file_info(existing)
    src = str(file_info["path"]) if file_info["ok"] else None
    pending = _contains_pending(content_context if content_context is not None else semantic)
    item = {
        "script_path": script_path,
        "semantic": semantic,
        "status": (
            "blocked_pending_content"
            if pending
            else "ready"
            if src
            else "generate_after_content_approval"
        ),
        "existing_src": src,
        "asset_validation": file_info,
        "width": spec["width"],
        "height": spec["height"],
        "cx": spec.get("cx"),
        "cy": spec.get("cy"),
        "aspect_ratio": f"{spec['width']}:{spec['height']}",
        "fit": spec["fit"],
        "safe_area": spec.get("safe_area") or "center",
        "subject_coverage": spec.get("subject_coverage") or "65%-85%",
        "prompt_constraints": [
            "只生成当前图槽所需内容，不设计整页 PPT",
            "不在图片内部预留文案区，不重复 PPT 标题或正文",
            "无品牌包装、Logo、医学功效文字、水印",
            "与本任务唯一 style_pack 保持一致",
        ],
        "slot_contract": spec["slot_id"],
        "source_policy": spec.get("source_policy"),
    }
    if binding:
        item["binding"] = binding
    if evidence_boundary:
        item["evidence_boundary"] = evidence_boundary
    return item


def build_product_pptx_asset_plan(
    script: dict[str, Any], *, template_slug: str
) -> dict[str, Any]:
    contracts = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
    meta = script.get("meta") or {}
    system_generated: list[dict[str, Any]] = []
    packshot_spec = _slot(contracts, "cover.product_packshot")

    for i, item in enumerate(((script.get("benefits") or {}).get("items") or []), 1):
        if isinstance(item, dict) and item.get("hidden") is True:
            continue
        row = item if isinstance(item, dict) else {"title": str(item)}
        chain = row.get("chain") or []
        existing = chain[0] if chain else row.get("visual")
        system_generated.append(
            _generated_item(
                contracts,
                slot_id="benefit.chain_wide_visual",
                script_path=f"benefits.items[{i - 1}].chain",
                semantic=str(row.get("title") or row.get("body") or f"核心知识 {i}"),
                existing=existing,
                content_context=row,
                binding={
                    "kind": "single_wide_chain",
                    "target": f"benefits.items[{i - 1}].chain",
                    "value_shape": [
                        {
                            "role": f"benefit_visual_{i}",
                            "file": "<generated-file>",
                            "w": 1200,
                            "h": 580,
                            "fit": "cover",
                            "source_kind": "system_generated",
                        }
                    ],
                },
            )
        )

    for i, item in enumerate(((script.get("features") or {}).get("items") or []), 1):
        if isinstance(item, dict) and item.get("hidden") is True:
            continue
        row = item if isinstance(item, dict) else {"title": str(item)}
        title = str(row.get("title") or "")
        system_generated.append(
            _generated_item(
                contracts,
                slot_id=_feature_slot_id(title, i - 1),
                script_path=f"features.items[{i - 1}].visual",
                semantic=str(row.get("title") or row.get("body") or f"商品特点 {i}"),
                existing=row.get("visual"),
                content_context=row,
                binding={
                    "kind": "visual_object",
                    "target": f"features.items[{i - 1}].visual",
                    "value_shape": {
                        "src": "<generated-file>",
                        "fit": "cover",
                        "source_kind": "system_generated",
                    },
                },
                evidence_boundary=(
                    "只可生成概念示意图；产地、原料、含量、配方、工艺或检测结论必须由本品授权证据支持，插图不得充当证据。"
                ),
            )
        )

    audience = script.get("audience") or {}
    if audience:
        system_generated.append(
            _generated_item(
                contracts,
                slot_id="audience.visual",
                script_path="audience.visual",
                semantic=str(audience.get("title") or audience.get("body") or "咨询场景"),
                existing=audience.get("visual"),
                content_context=audience,
                binding={
                    "kind": "visual_object",
                    "target": "audience.visual",
                    "value_shape": {
                        "src": "<generated-file>",
                        "fit": "cover",
                        "source_kind": "system_generated",
                    },
                },
            )
        )

    combination = script.get("combination") or {}
    for i, item in enumerate(combination.get("rows") or [], 1):
        if isinstance(item, dict) and item.get("hidden") is True:
            continue
        row = item if isinstance(item, dict) else {"problem": str(item)}
        semantic = " / ".join(
            str(value).strip()
            for value in (row.get("problem"), row.get("partner"))
            if str(value or "").strip()
        ) or f"联合场景 {i}"
        system_generated.append(
            _generated_item(
                contracts,
                slot_id="combination.row_icon",
                script_path=f"combination.rows[{i - 1}].icon",
                semantic=semantic,
                existing=row.get("icon"),
                content_context=row,
                binding={
                    "kind": "visual_object",
                    "target": f"combination.rows[{i - 1}].icon",
                    "value_shape": {
                        "src": "<generated-file>",
                        "fit": "contain",
                        "source_kind": "system_generated",
                    },
                },
                evidence_boundary="若展示搭档商品包装，必须改用业务授权真图；系统仅生成无品牌的场景/概念图标。",
            )
        )

    precautions = script.get("precautions") or {}
    if precautions and precautions.get("items"):
        illustrations = precautions.get("illustrations") or []
        existing = illustrations[0] if illustrations else None
        system_generated.append(
            _generated_item(
                contracts,
                slot_id="precautions.visual_wide",
                script_path="precautions.illustrations",
                semantic=str(precautions.get("title") or "标签、用量、边界与专业咨询"),
                existing=existing,
                content_context=precautions,
                binding={
                    "kind": "single_wide_precaution",
                    "target": "precautions.illustrations",
                    "value_shape": [
                        {
                            "src": "<generated-file>",
                            "wide": True,
                            "fit": "cover",
                            "source_kind": "system_generated",
                        }
                    ],
                },
            )
        )

    packshot_info = asset_file_info(meta.get("product_packshot"))
    return {
        "schema": "product-pptx-asset-plan/v1",
        "template_slug": template_slug,
        "style_pack_id": meta.get("style_pack_id") or "style-pack.reference-product-blue-v1",
        "policy": {
            "business_never_runs_image_prompts": True,
            "generate_only_after_content_approval": True,
            "first_representative_slot_qa": True,
            "no_fake_brand_packaging": True,
            "slot_contracts": str(CONTRACTS_PATH.relative_to(ROOT)),
        },
        "business_provides": [
            {
                "asset": "商品正式包装图",
                "required": True,
                "status": "ready" if packshot_info["ok"] else "missing",
                "asset_validation": packshot_info,
                "reason": "品牌/包装事实只能使用业务授权真图，禁止 AI 仿造。",
                "slot_contract": "cover.product_packshot",
                "width": packshot_spec["width"],
                "height": packshot_spec["height"],
                "fit": packshot_spec["fit"],
                "safe_area": packshot_spec.get("safe_area") or "center",
            },
            {
                "asset": "品牌 Logo",
                "required": False,
                "status": "ready" if meta.get("brand_logo") else "optional_missing",
                "reason": "需要展示品牌时使用业务授权透明原图。",
            },
            {
                "asset": "标签、备案/批准或检测证据图",
                "required": False,
                "status": "provide_if_claimed",
                "reason": "商品专属含量、用量、人群、功效或工艺证据只认本品正式资料。",
            },
        ],
        "system_generates": system_generated,
        "template_reuses": [
            "已签样版式、字体、色板与页型 recipe",
            "已批准的箭头、勾选、分隔线和简单图标",
            "统一页眉、页脚、标题与正文构件",
        ],
    }


def formal_render_blockers(plan: dict[str, Any]) -> list[str]:
    """Return asset gaps that must block a formal product-PPT render."""
    blockers: list[str] = []
    for item in plan.get("business_provides") or []:
        if item.get("required") and item.get("status") != "ready":
            reason = (item.get("asset_validation") or {}).get("error")
            blockers.append(f"缺少业务授权真图：{item.get('asset')}（{reason or 'missing'}）")
    for item in plan.get("system_generates") or []:
        status = item.get("status")
        if status == "blocked_pending_content":
            blockers.append(f"内容待确认，不能生图：{item.get('semantic')}")
        elif status != "ready":
            reason = (item.get("asset_validation") or {}).get("error")
            blockers.append(f"主题插图尚未补齐：{item.get('semantic')}（{reason or status}）")
    return blockers


def render_asset_plan_markdown(plan: dict[str, Any], *, theme: str) -> str:
    status_zh = {
        "ready": "已就绪",
        "missing": "待业务提供",
        "optional_missing": "按需补充",
        "provide_if_claimed": "涉及该结论时必须提供",
        "blocked_pending_content": "内容待确认，暂不生图",
        "generate_after_content_approval": "内容确认后由系统生成",
    }
    lines = [
        f"# 素材计划 · {theme}",
        "",
        "这份计划由系统执行。业务只需提供真实品牌/商品证据，不需要自己写生图提示词。",
        "",
        "## 需要业务提供",
        "",
    ]
    for item in plan.get("business_provides") or []:
        flag = "必需" if item.get("required") else "按需"
        status = status_zh.get(str(item.get("status")), str(item.get("status")))
        lines.append(f"- {item['asset']}（{flag}，{status}）：{item['reason']}")
    lines.extend(["", "## 系统自动处理", ""])
    for item in plan.get("system_generates") or []:
        status = status_zh.get(str(item.get("status")), str(item.get("status")))
        lines.append(
            f"- {item['semantic']}：{item['aspect_ratio']} / {item['fit']} / "
            f"主体 {item['subject_coverage']}（{status}）"
        )
        if item.get("evidence_boundary"):
            lines.append(f"  - 证据边界：{item['evidence_boundary']}")
    lines.extend(["", "## 模板直接复用", ""])
    lines.extend(f"- {item}" for item in plan.get("template_reuses") or [])
    lines.extend(
        [
            "",
            "## 自动质检顺序",
            "",
            "1. 内容确认后先生成 1 张代表图。",
            "2. 放入真实 PPT 图槽检查裁切、主体大小、清晰度和风格。",
            "3. 代表图通过后批量补齐同系列插图。",
            "4. 全页渲染检查后才进入交付目录。",
            "5. 任一必需真图、待确认内容或计划插图未就绪，正式交付自动阻断。",
            "",
        ]
    )
    return "\n".join(lines)
