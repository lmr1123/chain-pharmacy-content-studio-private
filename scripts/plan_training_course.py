#!/usr/bin/env python3
"""Map an approved TXT/Markdown/DOCX script to style-locked scene recipes."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "production-library/registries/scene-recipes.json"


IGNORED_DOCX_STYLES = {"Courseware Ignore", "填写提示"}

FIELD_ALIASES = {
    "approved_text": (
        "审核正文",
        "审核原文",
        "审核旁白原文",
        "审核旁白稿",
        "旁白原文",
        "旁白稿",
    ),
    "on_screen_facts": (
        "必须原样上屏的事实数据短文案",
        "必须原样上屏的事实短文案",
        "必须上屏的事实数据短文案",
        "必须展示的事实数据短文案",
        "必须上屏事实数据短文案",
        "上屏事实数据短文案",
        "上屏短文案",
    ),
    "authorized_assets": (
        "授权素材附件或文件名",
        "本章节随Word提交的授权素材文件名",
        "本章节授权素材",
        "已有需要的授权素材",
        "已有需要的素材",
        "授权素材",
    ),
}

IGNORED_SECTION_HEADINGS = (
    "业务只需",
    "怎么拆场景",
    "可复制的空白",
    "提交前",
    "系统收到",
    "填写说明",
    "使用说明",
    "授权素材提交清单",
)


def _normalize_label(text: str) -> str:
    return re.sub(r"[\s：:／/、·_\-—（）()【】\[\]及与或]+", "", text)


def _field_for_label(text: str) -> str | None:
    normalized = _normalize_label(text)
    for field, aliases in FIELD_ALIASES.items():
        normalized_aliases = {_normalize_label(alias) for alias in aliases}
        if any(normalized == alias or normalized.startswith(alias) for alias in normalized_aliases):
            return field
    return None


def _split_field_paragraph(text: str) -> tuple[str | None, str]:
    for separator in ("：", ":"):
        if separator in text:
            label, value = text.split(separator, 1)
            field = _field_for_label(label)
            if field:
                return field, value.strip()
    return _field_for_label(text), ""


def _new_section(heading: str) -> dict[str, Any]:
    return {
        "heading": heading,
        "approved_text": [],
        "on_screen_facts": [],
        "authorized_assets": [],
        "unmapped_content": [],
    }


def _append_value(section: dict[str, Any], field: str, value: str) -> None:
    value = value.strip()
    if not value:
        return
    values = [value]
    if field in {"on_screen_facts", "authorized_assets"}:
        values = [
            re.sub(r"^[•·▪◦\-]\s*", "", line).strip()
            for line in value.splitlines()
            if re.sub(r"^[•·▪◦\-]\s*", "", line).strip()
        ]
    for item in values:
        if item not in section[field]:
            section[field].append(item)


def _finalize_section(section: dict[str, Any]) -> dict[str, Any]:
    assets = [
        value
        for value in section["authorized_assets"]
        if _normalize_label(value) not in {"无", "暂无", "不提供", "不需要"}
        and not _normalize_label(value).startswith("无未提交授权素材")
    ]
    return {
        "heading": section["heading"],
        "text": "\n".join(section["approved_text"]).strip(),
        "approved_text": "\n".join(section["approved_text"]).strip(),
        "on_screen_facts": section["on_screen_facts"],
        "authorized_assets": assets,
        "unmapped_content": section["unmapped_content"],
    }


def _section_has_content(section: dict[str, Any]) -> bool:
    return any(
        section[field]
        for field in (
            "approved_text",
            "on_screen_facts",
            "authorized_assets",
            "unmapped_content",
        )
    )


def _is_ignored_heading(text: str) -> bool:
    return any(marker in text for marker in IGNORED_SECTION_HEADINGS)


def _iter_docx_blocks(document: DocumentObject):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def parse_markdown(path: Path) -> tuple[str, list[dict[str, Any]]]:
    title = path.stem
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    active_field = "approved_text"
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("# "):
            title = raw_line[2:].strip()
        elif raw_line.startswith("## "):
            if current:
                sections.append(_finalize_section(current))
            current = _new_section(raw_line[3:].strip())
            active_field = "approved_text"
        elif current is not None:
            text = raw_line.strip()
            if not text:
                continue
            field, value = _split_field_paragraph(text)
            if field:
                active_field = field
                _append_value(current, field, value)
            else:
                _append_value(current, active_field, text)
    if current:
        sections.append(_finalize_section(current))
    return title, sections


def parse_docx(path: Path) -> tuple[str, list[dict[str, Any]]]:
    document = Document(path)
    title = path.stem
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    active_field = "approved_text"
    saw_document_title = False
    for block in _iter_docx_blocks(document):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            style_name = block.style.name if block.style else ""
            if not text:
                continue
            if style_name in IGNORED_DOCX_STYLES:
                field, value = _split_field_paragraph(text)
                if current is not None and field:
                    active_field = field
                    _append_value(current, field, value)
                continue
            if style_name == "Title":
                title = text
                saw_document_title = True
                continue
            is_h1 = style_name in {"Heading 1", "标题 1"}
            is_h2 = style_name in {"Heading 2", "标题 2"}
            if is_h1 or is_h2:
                if is_h1 and not saw_document_title and current is None:
                    title = text
                    saw_document_title = True
                    continue
                if (
                    is_h1
                    and current is None
                    and not sections
                    and not re.match(r"^(场景|章节|\d+\s*[｜|])", text)
                ):
                    title = text
                    saw_document_title = True
                    continue
                if _is_ignored_heading(text):
                    if current and _section_has_content(current):
                        sections.append(_finalize_section(current))
                        current = None
                    active_field = "approved_text"
                    continue
                if current and _section_has_content(current):
                    sections.append(_finalize_section(current))
                heading = re.sub(
                    r"^(?:场景|章节)?\s*\d+\s*[｜|]\s*", "", text
                ).strip()
                current = _new_section(heading)
                active_field = "approved_text"
                continue
            if current is None:
                continue
            field, value = _split_field_paragraph(text)
            if field:
                active_field = field
                _append_value(current, field, value)
            elif text not in {"业务实际填写示例"}:
                _append_value(current, active_field, text)
        elif current is not None:
            for row in block.rows:
                values = [cell.text.strip() for cell in row.cells]
                if not any(values):
                    continue
                label = values[0] if values else ""
                value = values[1] if len(values) > 1 else ""
                field = _field_for_label(label)
                if field:
                    _append_value(current, field, value)
                elif label not in {"填写项", "业务填写内容"}:
                    unmapped = "：".join(part for part in (label, value) if part)
                    _append_value(current, "unmapped_content", unmapped)
    if current and _section_has_content(current):
        sections.append(_finalize_section(current))
    return title, sections


def parse_script(path: Path) -> tuple[str, list[dict[str, Any]]]:
    if path.suffix.lower() == ".docx":
        return parse_docx(path)
    if path.suffix.lower() in {".md", ".txt"}:
        return parse_markdown(path)
    raise ValueError(f"unsupported script type: {path.suffix}")


def choose_recipe(
    heading: str, recipes: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, list[str]]:
    normalized = re.sub(r"\s+", "", heading).lower()
    scored: list[tuple[int, int, dict[str, Any], str]] = []
    status_rank = {
        "production-validated": 0,
        "user-approved": 1,
        "visual-reviewed": 2,
        "technical-qa-passed": 3,
        "selected": 4,
        "candidate": 5,
    }
    for recipe in recipes:
        for alias in recipe.get("intent_aliases", []):
            key = re.sub(r"\s+", "", alias).lower()
            if key and key in normalized:
                scored.append(
                    (
                        len(key),
                        status_rank.get(recipe.get("status", ""), 99),
                        recipe,
                        alias,
                    )
                )
    scored.sort(key=lambda row: (-row[0], row[1], row[2]["id"]))
    if not scored:
        return None, []
    return scored[0][2], [row[3] for row in scored]


def _recipe_confidence(heading: str, matched_aliases: list[str]) -> float:
    if not matched_aliases:
        return 0.25
    normalized = re.sub(r"\s+", "", heading).lower()
    if any(re.sub(r"\s+", "", alias).lower() == normalized for alias in matched_aliases):
        return 0.98
    return 0.82


# 缺口通道策略：真包装/Logo/证据由业务提供（通道 A），教学图走 B/C。
ROLE_GAP_POLICY: dict[str, dict[str, Any]] = {
    "authorized_product_packshot": {
        "asset_kind": "packshot",
        "preferred_channel": "A",
        "business_provides": True,
        "series_id": "series.medication.company-authorized-v1",
        "status": "awaiting-business-asset",
        "semantic": "正品商品包装主图（业务授权原图）",
    },
    "authorized_partner_packshot": {
        "asset_kind": "packshot",
        "preferred_channel": "A",
        "business_provides": True,
        "series_id": "series.medication.company-authorized-v1",
        "status": "awaiting-business-asset",
        "semantic": "联合/搭配商品包装（业务授权原图）",
    },
    "authorized_brand_logo": {
        "asset_kind": "logo",
        "preferred_channel": "A",
        "business_provides": True,
        "series_id": "series.medication.company-authorized-v1",
        "status": "awaiting-business-asset",
        "semantic": "品牌 Logo（业务授权透明原图）",
    },
    "approved_efficacy_evidence": {
        "asset_kind": "evidence",
        "preferred_channel": "A",
        "business_provides": True,
        "series_id": None,
        "status": "awaiting-business-asset",
        "semantic": "功效/检测等证据图（业务授权）",
    },
    "approved_feature_evidence": {
        "asset_kind": "evidence",
        "preferred_channel": "A",
        "business_provides": True,
        "series_id": None,
        "status": "awaiting-business-asset",
        "semantic": "工艺/原料等证据图（业务授权）",
    },
    "problem_character": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "fallback_channel": "B",
        "business_provides": False,
        "series_id": "series.symptom.pharmacy-health-cartoon-v1",
        "status": "open",
        "semantic": "问题场景/患者人物插画",
    },
    "audience_illustration": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "fallback_channel": "B",
        "business_provides": False,
        "series_id": "series.audience.lifestyle-flat-v1",
        "status": "open",
        "semantic": "适宜人群插画",
    },
    "symptom_illustration": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "fallback_channel": "B",
        "business_provides": False,
        "series_id": "series.symptom.pharmacy-health-cartoon-v1",
        "status": "open",
        "semantic": "症状插画",
    },
    "botanical_ingredient": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "B",
        "fallback_channel": "C",
        "business_provides": False,
        "series_id": "series.herb.botanical-clean-v1",
        "status": "open",
        "semantic": "草本/成分插画",
    },
    "advice_illustration": {
        "asset_kind": "icon",
        "preferred_channel": "B",
        "fallback_channel": "C",
        "business_provides": False,
        "series_id": "series.icon.advice-safety-v1",
        "status": "open",
        "semantic": "生活建议/禁忌图标",
    },
    "mechanism_subject": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "fallback_channel": "B",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "机理主体（人体/器官）",
    },
    "mechanism_nodes": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "fallback_channel": "B",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "机理节点/流程元素",
    },
    "whole_body_front": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "正面全身人体",
    },
    "organ_torso": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "器官躯干机制图",
    },
    "full_body_front": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "全身人体",
    },
    "symptom_focus": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "症状聚焦",
    },
    "anatomical_cutaway": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "解剖剖面",
    },
    "pathogen_environment": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "病邪/环境介质",
    },
    "process_path": {
        "asset_kind": "teaching_illustration",
        "preferred_channel": "C",
        "business_provides": False,
        "series_id": "asset-series.mechanism.reference-medical-tech-v1",
        "status": "open",
        "semantic": "过程路径",
    },
}


def _asset_role_matches(role_id: str, assets: list[str]) -> list[str]:
    role_keywords = {
        "authorized_product_packshot": ("包装", "药盒", "药瓶", "商品图", "产品图"),
        "authorized_partner_packshot": ("组合包装", "搭配商品", "联合商品"),
        "authorized_brand_logo": ("logo", "标志"),
        "approved_efficacy_evidence": ("功效", "证据", "检测", "研究", "资料"),
        "approved_feature_evidence": ("工艺", "专利", "原料", "检测", "资料"),
        "problem_character": ("人物", "角色", "患者"),
        "audience_illustration": ("人群", "人物", "角色"),
        "symptom_illustration": ("症状", "插画", "患者"),
        "botanical_ingredient": ("草本", "药材", "植物", "成分"),
        "advice_illustration": ("建议", "生活", "插画", "图标"),
        "mechanism_subject": ("机理", "器官", "人体", "线粒体"),
        "mechanism_nodes": ("节点", "机理", "流程"),
    }
    keywords = role_keywords.get(role_id, tuple(part for part in role_id.split("_") if len(part) > 3))
    return [
        asset
        for asset in assets
        if any(keyword.lower() in asset.lower() for keyword in keywords)
    ]


def _build_gap_task(
    role_id: str,
    *,
    style_pack_id: str,
    scene_orders: list[int],
) -> dict[str, Any]:
    policy = ROLE_GAP_POLICY.get(
        role_id,
        {
            "asset_kind": "other",
            "preferred_channel": "C",
            "fallback_channel": "B",
            "business_provides": False,
            "series_id": None,
            "status": "open",
            "semantic": role_id,
        },
    )
    task: dict[str, Any] = {
        "gap_id": f"gap.role.{role_id}",
        "role_id": role_id,
        "asset_kind": policy["asset_kind"],
        "semantic": policy.get("semantic") or role_id,
        "preferred_channel": policy["preferred_channel"],
        "status": policy.get("status") or "open",
        "business_provides": bool(policy.get("business_provides")),
        "style_pack_id": style_pack_id,
        "series_id": policy.get("series_id"),
        "scene_orders": scene_orders,
        "license_requirement": "internal_training_commercial",
    }
    if policy.get("fallback_channel"):
        task["fallback_channel"] = policy["fallback_channel"]
    if task["business_provides"]:
        task["notes"] = "真包装/Logo/证据由业务提供；制作不外购、不生成仿品牌包装。"
    else:
        task["search_queries"] = [
            task["semantic"],
            f"{task['semantic']} commercial medical illustration",
        ]
        task["notes"] = "教学插画：通道 B 商用/开源适配或通道 C 参考再生后进入 series candidates。"
    return task


def _screen_copy(section: dict[str, Any]) -> tuple[list[str], str]:
    if section["on_screen_facts"]:
        return section["on_screen_facts"], "business-approved"
    sentences = [
        sentence.strip(" ；;。.")
        for sentence in re.split(r"[。！？!?\n]", section["approved_text"])
        if 2 <= len(sentence.strip()) <= 28
    ]
    return sentences[:3], "system-suggested"


def build_manifest(script_path: Path, style_pack_id: str) -> dict[str, Any]:
    title, sections = parse_script(script_path)
    registry = json.loads(RECIPES.read_text(encoding="utf-8"))
    compatible = [
        item
        for item in registry["items"]
        if item["style_pack_id"] == style_pack_id
    ]
    scenes = []
    unresolved = []
    required_asset_roles: set[str] = set()
    missing_role_scenes: dict[str, list[int]] = {}
    for index, section in enumerate(sections):
        recipe, aliases = choose_recipe(section["heading"], compatible)
        text = section["approved_text"].strip()
        screen_copy, screen_copy_source = _screen_copy(section)
        content_slots = {
            "section_title": section["heading"],
            "approved_text": text,
            "on_screen_facts": section["on_screen_facts"],
            "screen_copy_suggestion": screen_copy,
            "screen_copy_source": screen_copy_source,
            "authorized_assets": section["authorized_assets"],
            "unmapped_content": section["unmapped_content"],
        }
        if recipe is None:
            unresolved.append(
                {
                    "section_index": index,
                    "heading": section["heading"],
                    "reason": "no-compatible-scene-recipe",
                }
            )
            scenes.append(
                {
                    "order": index,
                    "status": "needs-scene-selection",
                    "match_confidence": _recipe_confidence(
                        section["heading"], aliases
                    ),
                    "slots": content_slots,
                    "asset_matches": [],
                    "asset_gaps": [],
                }
            )
            continue
        asset_matches = []
        asset_gaps = []
        for role_id in recipe.get("asset_roles", []):
            matches = _asset_role_matches(
                role_id, section["authorized_assets"]
            )
            if matches:
                asset_matches.append(
                    {
                        "role_id": role_id,
                        "authorized_assets": matches,
                        "confidence": 0.9,
                    }
                )
            else:
                missing_role_scenes.setdefault(role_id, []).append(index)
                gap = _build_gap_task(
                    role_id,
                    style_pack_id=style_pack_id,
                    scene_orders=[index],
                )
                asset_gaps.append(
                    {
                        "role_id": role_id,
                        "status": gap["status"],
                        "preferred_channel": gap["preferred_channel"],
                        "business_provides": gap["business_provides"],
                        "series_id": gap.get("series_id"),
                    }
                )
        scenes.append(
            {
                "order": index,
                "status": "planned",
                "intent": recipe["intent"],
                "scene_recipe_id": recipe["id"],
                "recipe_status": recipe.get("status", "unknown"),
                "component_ids": recipe.get("components", []),
                "effect_ids": recipe.get("effects", []),
                "asset_roles": recipe.get("asset_roles", []),
                "matched_aliases": aliases,
                "match_confidence": _recipe_confidence(
                    section["heading"], aliases
                ),
                "slots": content_slots,
                "asset_matches": asset_matches,
                "asset_gaps": asset_gaps,
                "constraints": recipe.get("constraints", {}),
            }
        )
        required_asset_roles.update(recipe.get("asset_roles", []))
    try:
        source_script = str(script_path.relative_to(ROOT))
    except ValueError:
        source_script = str(script_path)
    asset_gap_tasks = [
        _build_gap_task(
            role_id,
            style_pack_id=style_pack_id,
            scene_orders=sorted(scene_orders),
        )
        for role_id, scene_orders in sorted(missing_role_scenes.items())
    ]
    return {
        "contract_version": "2.1.0",
        "project_title": title,
        "source_script": source_script,
        "content_lock": "approved-script",
        "style_pack_id": style_pack_id,
        "style_pack_locked": True,
        "scene_order_policy": "source-script-order",
        "scene_selection_policy": "intent-to-compatible-recipe",
        "asset_gap_schema": "production-library/schemas/asset-gap-tasks.schema.json",
        "packshot_policy": "business-provides-authorized-packshots",
        "style_cohesion_policy": {
            "single_style_pack": True,
            "cross_style_components_forbidden": True,
            "asset_series_required_when_declared": True,
            "max_primary_motion_per_scene": 1,
        },
        "scenes": scenes,
        "unresolved_sections": unresolved,
        "required_asset_roles": sorted(required_asset_roles),
        "asset_gap_tasks": asset_gap_tasks,
        "asset_gaps_awaiting_business": [
            task
            for task in asset_gap_tasks
            if task.get("business_provides")
        ],
        "asset_gaps_production_fillable": [
            task
            for task in asset_gap_tasks
            if not task.get("business_provides")
        ],
        "production_gate": {
            "default_batch_requires": ["user-approved", "production-validated"],
            "current_plan_requires_visual_confirmation": any(
                scene.get("recipe_status")
                not in {"user-approved", "production-validated"}
                for scene in scenes
                if scene.get("status") == "planned"
            ),
            "business_packshots_required_for_real_product": True,
        },
    }


def render_storyboard_preview(manifest: dict[str, Any]) -> str:
    def escaped(value: Any) -> str:
        return html.escape(str(value))

    def items(values: list[Any], empty: str) -> str:
        if not values:
            return f'<p class="empty">{escaped(empty)}</p>'
        return "<ul>" + "".join(
            f"<li>{escaped(value)}</li>" for value in values
        ) + "</ul>"

    cards = []
    for scene in manifest["scenes"]:
        slots = scene["slots"]
        matches = [
            f"{match['role_id']} ← {', '.join(match['authorized_assets'])}"
            for match in scene.get("asset_matches", [])
        ]
        gaps = [gap["role_id"] for gap in scene.get("asset_gaps", [])]
        recipe = scene.get("scene_recipe_id", "待人工选择")
        cards.append(
            f"""
            <article class="card">
              <header>
                <span class="order">{scene['order'] + 1:02d}</span>
                <div><h2>{escaped(slots['section_title'])}</h2>
                <p class="recipe">{escaped(recipe)}</p></div>
                <strong>{scene.get('match_confidence', 0):.0%}</strong>
              </header>
              <div class="grid">
                <section class="wide"><h3>审核原文</h3>
                  <p class="approved">{escaped(slots['approved_text']) or '—'}</p>
                </section>
                <section><h3>屏幕短文案</h3>
                  <small>{escaped(slots['screen_copy_source'])}</small>
                  {items(slots['screen_copy_suggestion'], '暂无建议')}
                </section>
                <section><h3>推荐画面配方</h3>
                  <p>{escaped(scene.get('intent', '未匹配'))}</p>
                  {items(scene.get('asset_roles', []), '无需专用素材角色')}
                </section>
                <section><h3>已匹配素材</h3>
                  {items(matches, '尚未匹配授权素材')}
                </section>
                <section><h3>业务提交素材</h3>
                  {items(slots['authorized_assets'], '未提交')}
                </section>
                <section><h3>素材缺口</h3>
                  {items(gaps, '无')}
                </section>
                <section><h3>未映射内容</h3>
                  {items(slots['unmapped_content'], '无')}
                </section>
              </div>
            </article>"""
        )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escaped(manifest['project_title'])}｜分镜预览</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#071722;color:#dceef4;
font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
main{{max-width:1180px;margin:auto;padding:48px 24px}}h1{{font-size:32px;margin:0}}
.meta{{color:#86b9c8;margin:4px 0 28px}}.card{{background:#0d2532;border:1px solid #214958;
border-radius:18px;margin:18px 0;padding:22px;box-shadow:0 16px 40px #0004}}
header{{display:flex;gap:16px;align-items:center;border-bottom:1px solid #214958;padding-bottom:14px}}
header div{{flex:1}}h2{{margin:0;font-size:22px}}.order{{color:#50d7dc;font-size:22px}}
header strong{{color:#50d7dc}}.recipe{{margin:0;color:#80abb8;font-size:12px}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:16px}}
section{{background:#091c27;border-radius:12px;padding:15px}}section.wide{{grid-column:1/-1}}
h3{{font-size:13px;color:#67d7df;margin:0 0 8px}}p,ul{{margin:0}}ul{{padding-left:20px}}
.approved{{white-space:pre-wrap}}small,.empty{{color:#7898a2}}@media(max-width:720px){{
.grid{{grid-template-columns:1fr}}section.wide{{grid-column:auto}}}}
</style></head><body><main><h1>{escaped(manifest['project_title'])}</h1>
<p class="meta">系统生成分镜预览 · {escaped(manifest['style_pack_id'])} ·
业务确认内容与素材，画面配方由系统维护</p>
{''.join(cards)}</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path, help="approved .txt, .md, or .docx")
    parser.add_argument("--style-pack", required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--preview-out",
        type=Path,
        help="optional standalone HTML storyboard preview",
    )
    args = parser.parse_args()
    manifest = build_manifest(args.script.resolve(), args.style_pack)
    output = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    if args.preview_out:
        args.preview_out.parent.mkdir(parents=True, exist_ok=True)
        args.preview_out.write_text(
            render_storyboard_preview(manifest), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
