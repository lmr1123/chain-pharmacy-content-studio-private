#!/usr/bin/env python3
"""Import one product per TXT/Markdown/DOCX into editable courseware manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from image_prompt_protocol import IMAGE_STYLE_ID, build_image_prompt


TEMPLATE_ID = "template.product-courseware-dashenlin-green-v1"
STYLE_PACK_ID = "style-pack.dashenlin-courseware-green-v1"
DISEASE_PRODUCT_TEMPLATE_ID = "template.dashenlin-disease-product-scenario-v1"
SUPPORTED_SUFFIXES = {".txt", ".md", ".docx"}

COURSEWARE_TYPE_PROFILES = {
    "简版商品培训课件（5页）": {
        "profile": "product-brief-5",
        "template_id": TEMPLATE_ID,
    },
    "疾病—商品—场景培训课件（18页）": {
        "profile": "disease-product-scenario-18",
        "template_id": DISEASE_PRODUCT_TEMPLATE_ID,
    },
}

SECTION_ALIASES = {
    "introduction": ("商品介绍", "产品介绍", "基本信息", "药品介绍"),
    "selling_points": ("核心卖点", "产品卖点", "商品卖点", "主要卖点", "产品特点"),
    "audiences": ("适宜人群", "适用人群", "适合人群", "目标人群"),
    "combinations": ("联合用药话术", "联合用药", "搭配用药", "用药搭配"),
    "benchmarks": ("品种对标", "竞品对比", "竞品分析", "产品对比"),
    "precautions": ("注意事项", "使用注意", "用药注意", "禁忌"),
}

METADATA_ALIASES = {
    "display_name": ("商品名称", "产品名称", "药品名称", "商品名", "品名"),
    "brand_name": ("品牌名称", "品牌"),
    "code": ("商品编码", "产品编码", "编码"),
    "priority": ("主推级别", "主推"),
    "specification": ("商品规格", "产品规格", "规格"),
    "retail_price": ("零售价", "销售价", "售价"),
    "one_line_selling_point": ("一句话卖点", "一句话推荐"),
    "primary_asset": ("商品主图", "产品图片", "商品图片"),
}

INTRO_LABELS = (
    "主要成分",
    "功能主治",
    "适应症",
    "用法用量",
    "批准文号",
    "剂型",
    "生产企业",
)
COMBINATION_FIELDS = {
    "scenario": ("应用场景", "适宜人群", "适用场景", "场景"),
    "combination": ("联合用药", "搭配用药", "联合商品", "搭配商品"),
    "product_image": ("产品图片展示", "产品图片", "商品图片", "图片"),
    "talk_track": ("销售话术", "推荐话术", "话术"),
}
IMAGE_REQUEST_FIELDS = {
    "target": ("使用位置", "课件位置", "PPT位置", "页面位置"),
    "topic": ("图片主题", "配图主题", "生图主题"),
    "notes": ("补充要求", "画面要求", "备注"),
}
UNMAPPED_HEADINGS = ("其他内容", "补充内容", "备注", "待确认内容")


@dataclass
class Block:
    kind: str
    text: str = ""
    heading_hint: bool = False
    headers: list[str] | None = None
    rows: list[list[str]] | None = None


def normalize_space(value: Any) -> str:
    return re.sub(r"[ \t\u3000]+", " ", str(value or "")).strip()


def normalize_business_value(value: Any) -> str:
    normalized = normalize_space(value)
    if normalized.startswith("【业务填写】"):
        return ""
    return normalized


def strip_item_prefix(text: str) -> str:
    return re.sub(
        r"^\s*(?:[-•●▪◦·]\s*|(?:\d+|[一二三四五六七八九十]+)[、.．）)]\s*)",
        "",
        text,
    ).strip()


def split_label(text: str) -> tuple[str, str] | None:
    match = re.match(r"^\s*([^：:]{1,20})\s*[：:]\s*(.*)$", text)
    if not match:
        return None
    return normalize_space(match.group(1)), normalize_space(match.group(2))


def match_alias(label: str, aliases: dict[str, tuple[str, ...]]) -> str | None:
    compact = re.sub(r"\s+", "", label)
    for key, names in aliases.items():
        if compact in names:
            return key
    return None


def match_section_heading(text: str) -> tuple[str, str] | None:
    cleaned = re.sub(
        r"^\s*(?:第?[一二三四五六七八九十\d]+[章节、.．）)]?\s*)",
        "",
        text,
    ).strip()
    for key, aliases in SECTION_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            match = re.match(
                rf"^{re.escape(alias)}\s*(?:[：:]\s*(.*))?$",
                cleaned,
            )
            if match:
                return key, normalize_space(match.group(1))
    return None


def text_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = normalize_space(raw)
        if line:
            blocks.append(Block(kind="paragraph", text=line))
    return blocks


def docx_blocks(path: Path) -> list[Block]:
    document = Document(path)
    blocks: list[Block] = []
    for item in document.iter_inner_content():
        if isinstance(item, Paragraph):
            text = normalize_space(item.text)
            if text:
                style_name = normalize_space(item.style.name if item.style else "")
                if style_name in {"填写提示", "Courseware Ignore"}:
                    continue
                blocks.append(
                    Block(
                        kind="paragraph",
                        text=text,
                        heading_hint=style_name.lower().startswith("heading")
                        or style_name.startswith("标题"),
                    )
                )
        elif isinstance(item, Table):
            rows = [
                [normalize_space(cell.text) for cell in row.cells]
                for row in item.rows
            ]
            rows = [row for row in rows if any(row)]
            if rows:
                blocks.append(
                    Block(
                        kind="table",
                        headers=rows[0],
                        rows=rows[1:],
                    )
                )
    return blocks


def read_source(path: Path) -> tuple[list[Block], str]:
    if path.suffix.lower() == ".docx":
        return docx_blocks(path), "docx"
    return text_blocks(path.read_text(encoding="utf-8-sig")), "text"


def empty_manifest(source_name: str, source_type: str) -> dict[str, Any]:
    return {
        "schema_version": "courseware-natural-input-v1",
        "template_id": TEMPLATE_ID,
        "style_pack_id": STYLE_PACK_ID,
        "style_pack_locked": True,
        "layout_policy": "preserve-source-layout",
        "content_lock": "source-import-review-required",
        "source": {
            "name": source_name,
            "type": source_type,
            "sha256": "",
        },
        "product": {
            "display_name": "",
            "brand_name": "",
            "code": "",
            "priority": "",
            "specification": "",
            "retail_price": "",
            "one_line_selling_point": "",
            "primary_asset": "",
        },
        "introduction": [],
        "selling_points": [],
        "audiences": [],
        "combinations": [],
        "benchmarks": [],
        "precautions": [],
        "image_requests": [],
        "unmapped_content": [],
        "image_generation_policy": {
            "style_id": IMAGE_STYLE_ID,
            "workflow": "auto-or-copy-prompt-then-paste-final-to-pptx",
            "generated_asset_status": "candidate",
            "medical_review_required": True,
            "visual_review_required": True,
            "generated_text_forbidden": True,
            "real_product_and_evidence_assets": "authorized-source-only",
        },
        "editable_blank_policy": {
            "keep_section_titles": True,
            "keep_text_boxes": True,
            "keep_image_slots": True,
            "missing_content": "blank",
            "unmapped_content": "review-list",
        },
    }


def add_intro(manifest: dict[str, Any], text: str, source_ref: str) -> None:
    clean = strip_item_prefix(text)
    pair = split_label(clean)
    if pair and pair[0] in INTRO_LABELS:
        field_name, content = pair
    else:
        field_name, content = "", clean
    manifest["introduction"].append(
        {"field_name": field_name, "content": content, "source_ref": source_ref}
    )


def add_selling_point(
    manifest: dict[str, Any], text: str, source_ref: str
) -> None:
    clean = strip_item_prefix(text)
    pair = split_label(clean)
    title, content = pair if pair else ("", clean)
    manifest["selling_points"].append(
        {"title": title, "content": content, "source_ref": source_ref}
    )


def add_audience(manifest: dict[str, Any], text: str, source_ref: str) -> None:
    clean = strip_item_prefix(text).rstrip("；;。")
    if clean:
        manifest["audiences"].append(
            {"description": clean, "source_ref": source_ref}
        )


def add_precaution(
    manifest: dict[str, Any], text: str, source_ref: str
) -> None:
    clean = strip_item_prefix(text)
    if clean:
        manifest["precautions"].append(
            {"content": clean, "source_ref": source_ref}
        )


def blank_combination(source_ref: str) -> dict[str, str]:
    return {
        "scenario": "",
        "combination": "",
        "product_image": "",
        "talk_track": "",
        "source_text": "",
        "source_ref": source_ref,
    }


def combination_field(label: str) -> str | None:
    compact = re.sub(r"\s+", "", label)
    for key, aliases in COMBINATION_FIELDS.items():
        if compact in aliases:
            return key
    return None


def image_request_field(label: str) -> str | None:
    compact = re.sub(r"\s+", "", label)
    compact = re.sub(r"[（(].*?[）)]", "", compact)
    for key, aliases in IMAGE_REQUEST_FIELDS.items():
        if compact in aliases:
            return key
    return None


def parse_image_request_table(
    manifest: dict[str, Any], headers: list[str], rows: list[list[str]], source_ref: str
) -> bool:
    mapping = [image_request_field(header) for header in headers]
    if "topic" not in mapping:
        return False
    for row_index, row in enumerate(rows, start=1):
        values = {"target": "", "topic": "", "notes": ""}
        for index, value in enumerate(row):
            if index < len(mapping) and mapping[index]:
                values[mapping[index]] = normalize_space(value)
        if not values["topic"]:
            continue
        generated = build_image_prompt(
            values["target"],
            values["topic"],
            values["notes"],
        )
        manifest["image_requests"].append(
            {
                **values,
                **generated,
                "source_ref": f"{source_ref}/row-{row_index}",
            }
        )
    return True


def parse_combination_table(
    manifest: dict[str, Any], headers: list[str], rows: list[list[str]], source_ref: str
) -> bool:
    mapping = [combination_field(header) for header in headers]
    if not any(mapping):
        return False
    for row_index, row in enumerate(rows, start=1):
        record = blank_combination(f"{source_ref}/row-{row_index}")
        for index, value in enumerate(row):
            if index < len(mapping) and mapping[index]:
                record[mapping[index]] = normalize_space(value)
        record["source_text"] = " | ".join(value for value in row if value)
        manifest["combinations"].append(record)
    return True


def parse_key_value_table(
    manifest: dict[str, Any], headers: list[str], rows: list[list[str]], source_ref: str
) -> bool:
    table_rows = [headers, *rows]
    if not table_rows or any(len(row) != 2 for row in table_rows):
        return False
    recognized = 0
    leftovers: list[str] = []
    for row_index, row in enumerate(table_rows, start=1):
        label = normalize_space(row[0])
        value = normalize_space(row[1])
        metadata_key = match_alias(label, METADATA_ALIASES)
        if metadata_key:
            manifest["product"][metadata_key] = value
            recognized += 1
        elif label in INTRO_LABELS:
            add_intro(
                manifest,
                f"{label}：{value}",
                f"{source_ref}/row-{row_index}",
            )
            recognized += 1
        elif label or value:
            leftovers.append("：".join(part for part in (label, value) if part))
    if not recognized:
        return False
    for text in leftovers:
        manifest["unmapped_content"].append(
            {"text": text, "source_ref": source_ref}
        )
    return True


def add_combination_line(
    manifest: dict[str, Any],
    text: str,
    source_ref: str,
    current: dict[str, str] | None,
) -> dict[str, str] | None:
    clean = strip_item_prefix(text)
    pair = split_label(clean)
    field = combination_field(pair[0]) if pair else None
    if field:
        if field == "scenario" and current and any(
            current[key] for key in ("scenario", "combination", "talk_track")
        ):
            manifest["combinations"].append(current)
            current = None
        current = current or blank_combination(source_ref)
        current[field] = pair[1]
        current["source_text"] = (
            f'{current["source_text"]}\n{clean}'.strip()
        )
        return current

    if pair and ("+" in pair[1] or "＋" in pair[1]):
        if current:
            manifest["combinations"].append(current)
        record = blank_combination(source_ref)
        record["scenario"] = pair[0]
        record["combination"] = pair[1]
        record["source_text"] = clean
        return record

    if current:
        current["source_text"] = f'{current["source_text"]}\n{clean}'.strip()
        if not current["talk_track"]:
            current["talk_track"] = clean
        return current

    record = blank_combination(source_ref)
    record["source_text"] = clean
    return record


def classify_unheaded(text: str) -> str | None:
    if split_label(text) and split_label(text)[0] in INTRO_LABELS:
        return "introduction"
    if re.search(r"禁用|慎用|不宜|注意|停药|就诊|咨询医师|过敏", text):
        return "precautions"
    if re.search(r"联合用药|搭配用药|销售话术|推荐话术", text) or (
        ("+" in text or "＋" in text)
        and re.search(r"颗粒|片|胶囊|口服液|溶液|药", text)
    ):
        return "combinations"
    return None


def standardized_courseware_type(blocks: list[Block]) -> str:
    for block in blocks:
        if block.kind != "table":
            continue
        for row in [block.headers or [], *(block.rows or [])]:
            if len(row) != 2:
                continue
            label = re.sub(r"\s+", "", normalize_space(row[0]))
            label = re.sub(r"[（(]请勿修改[）)]", "", label)
            if label != "课件类型":
                continue
            value = normalize_space(row[1])
            if value in COURSEWARE_TYPE_PROFILES:
                return value
    return ""


def table_records(headers: list[str], rows: list[list[str]]) -> list[dict[str, str]]:
    return [
        {
            normalize_space(header): normalize_business_value(
                row[index] if index < len(row) else ""
            )
            for index, header in enumerate(headers)
        }
        for row in rows
        if any(normalize_space(value) for value in row)
    ]


def key_value_records(block: Block) -> dict[str, str]:
    return {
        normalize_space(row[0]): normalize_business_value(row[1])
        for row in block.rows or []
        if len(row) == 2 and (normalize_space(row[0]) or normalize_space(row[1]))
    }


def standardized_manifest(
    blocks: list[Block],
    source_name: str,
    source_type: str,
    courseware_type: str,
) -> dict[str, Any]:
    profile = COURSEWARE_TYPE_PROFILES[courseware_type]
    manifest = empty_manifest(source_name, source_type)
    manifest["schema_version"] = "courseware-business-input-v2"
    manifest["template_id"] = profile["template_id"]
    manifest["courseware_type"] = courseware_type
    manifest["courseware_profile"] = profile["profile"]
    manifest["course"] = {
        "title": "",
        "disease_theme": "",
        "primary_product": "",
        "training_audience": "",
        "lead": "",
    }
    manifest["content_sections"] = {}
    manifest["authorized_assets"] = []
    manifest["source_blocks"] = [
        {
            "kind": block.kind,
            "text": block.text,
            "heading_hint": block.heading_hint,
            "headers": block.headers or [],
            "rows": block.rows or [],
        }
        for block in blocks
    ]

    course_aliases = {
        "课程标题": "title",
        "疾病主题": "disease_theme",
        "主推商品": "primary_product",
        "培训对象": "training_audience",
        "一句话导语": "lead",
    }
    product_aliases = {
        "商品名称": "display_name",
        "品牌名称": "brand_name",
        "商品编码": "code",
        "主推级别": "priority",
        "规格": "specification",
        "零售价": "retail_price",
        "一句话卖点": "one_line_selling_point",
    }
    signature_sections = {
        ("商品字段", "审核原文"): "product_information",
        ("卖点名称", "支撑内容"): "selling_points",
        ("适宜人群",): "audiences",
        ("应用场景", "联合用药", "销售话术"): "combinations",
        ("对比维度", "本品", "竞品"): "benchmarks",
        ("注意事项",): "precautions",
        ("典型症状", "审核说明"): "disease_symptoms",
        ("鉴别维度", "风热证", "对照证型"): "syndrome_comparison",
        ("治疗原则", "审核原文"): "treatment_principles",
        ("证候名称", "典型表现", "处理重点"): "syndrome_subtypes",
        ("卖点分组", "卖点名称", "支撑内容／依据说明"): "product_advantages",
        ("人群", "典型场景", "需求说明"): "audience_scenarios",
        ("沟通步骤", "培训口径"): "consultation_framework",
        ("场景名称", "辨证沟通", "核心用药", "关联服务", "服务要点"): "scenario_solutions",
        ("日常生活叮嘱",): "daily_care",
        ("权重商品", "核心信息", "推荐边界／备注"): "weighted_product_detail",
        ("对比维度", "白云山安宫", "宏济堂安宫"): "weighted_product_comparison",
    }

    for block_index, block in enumerate(blocks, start=1):
        source_ref = f"block-{block_index}"
        if block.kind != "table":
            if block.heading_hint:
                continue
            manifest["unmapped_content"].append(
                {"text": block.text, "source_ref": source_ref}
            )
            continue
        headers = tuple(normalize_space(value) for value in (block.headers or []))
        rows = block.rows or []
        if not rows:
            continue

        if headers == ("填写项目", "业务填写内容"):
            values = key_value_records(block)
            if "课件类型（请勿修改）" in values:
                for label, value in values.items():
                    if label in course_aliases:
                        manifest["course"][course_aliases[label]] = value
                    elif label in product_aliases:
                        manifest["product"][product_aliases[label]] = value
                continue
            if "疾病定义" in values:
                manifest["content_sections"]["disease_definition"] = values
                continue
            if "核心优势总结" in values:
                manifest["content_sections"]["product_advantage_summary"] = values
                continue

        if headers == (
            "课件位置／栏目",
            "文件名",
            "来源与授权范围",
            "是否必须使用",
        ):
            manifest["authorized_assets"] = table_records(list(headers), rows)
            continue

        if headers == ("其他待确认内容",):
            for row in rows:
                text = normalize_space(row[0] if row else "")
                if text and text != "无":
                    manifest["unmapped_content"].append(
                        {"text": text, "source_ref": source_ref}
                    )
            continue

        section_key = signature_sections.get(headers)
        if section_key:
            manifest["content_sections"].setdefault(section_key, []).extend(
                table_records(list(headers), rows)
            )
            continue

        manifest["unmapped_content"].append(
            {
                "text": f"未识别表格：{'｜'.join(headers)}",
                "source_ref": source_ref,
            }
        )

    if profile["profile"] == "product-brief-5":
        sections = manifest["content_sections"]
        for record in sections.get("product_information", []):
            label = record.get("商品字段", "")
            value = record.get("审核原文", "")
            if label in INTRO_LABELS:
                add_intro(manifest, f"{label}：{value}", "standardized")
        for record in sections.get("selling_points", []):
            manifest["selling_points"].append(
                {
                    "title": record.get("卖点名称", ""),
                    "content": record.get("支撑内容", ""),
                    "source_ref": "standardized",
                }
            )
        for record in sections.get("audiences", []):
            add_audience(manifest, record.get("适宜人群", ""), "standardized")
        for record in sections.get("combinations", []):
            manifest["combinations"].append(
                {
                    **blank_combination("standardized"),
                    "scenario": record.get("应用场景", ""),
                    "combination": record.get("联合用药", ""),
                    "talk_track": record.get("销售话术", ""),
                }
            )
        if sections.get("benchmarks"):
            manifest["benchmarks"].append(
                {
                    "headers": ["对比维度", "本品", "竞品"],
                    "rows": [
                        [row["对比维度"], row["本品"], row["竞品"]]
                        for row in sections["benchmarks"]
                    ],
                    "source_ref": "standardized",
                }
            )
        for record in sections.get("precautions", []):
            add_precaution(
                manifest, record.get("注意事项", ""), "standardized"
            )
        max_page01_items = max(
            len(manifest["introduction"]),
            len(manifest["selling_points"]),
            len(manifest["audiences"]),
        )
        manifest["page_rules"] = {
            "cover": {"page_count": 1, "layout": "locked-company-cover"},
            "page01": {
                "layout": "product-overview",
                "page_count": max(1, (max_page01_items + 2) // 3),
            },
            "page02": {
                "layout": "combination-guidance",
                "page_count": max(1, (len(manifest["combinations"]) + 2) // 3),
            },
            "page03": {"layout": "product-benchmark", "page_count": 1},
            "page04": {
                "layout": "precautions",
                "page_count": max(1, (len(manifest["precautions"]) + 4) // 5),
            },
        }
    else:
        manifest["product"]["display_name"] = (
            manifest["course"]["primary_product"]
        )
        sections = manifest["content_sections"]
        scenario_count = len(sections.get("scenario_solutions", []))
        manifest["page_rules"] = {
            "cover": {"page_count": 1, "layout": "locked-company-cover"},
            "opening": {"page_count": 2, "layouts": ["opening-thesis", "agenda"]},
            "disease": {"page_count": 5, "layout_family": "disease-section"},
            "product": {"page_count": 3, "layout_family": "product-section"},
            "audience": {"page_count": 2, "layout_family": "audience-section"},
            "scenarios": {
                "page_count": max(1, scenario_count),
                "layout": "scenario-solution",
            },
            "daily_care": {"page_count": 1, "layout": "daily-care-guidance"},
            "weighted_products": {
                "page_count": 2,
                "layout_family": "weighted-product-section",
            },
        }

    manifest["blank_fields"] = collect_blank_fields(manifest)
    manifest["template_dependency"] = (
        f"批量生成必须使用已登记模板 {manifest['template_id']}；"
        "公司封面、封底和品牌位保持锁定。"
    )
    return manifest


def parse_blocks(
    blocks: Iterable[Block], source_name: str, source_type: str
) -> dict[str, Any]:
    block_list = list(blocks)
    courseware_type = standardized_courseware_type(block_list)
    if courseware_type:
        return standardized_manifest(
            block_list, source_name, source_type, courseware_type
        )
    manifest = empty_manifest(source_name, source_type)
    manifest["source_blocks"] = [
        {
            "kind": block.kind,
            "text": block.text,
            "heading_hint": block.heading_hint,
            "headers": block.headers or [],
            "rows": block.rows or [],
        }
        for block in block_list
    ]
    current_section: str | None = None
    current_combination: dict[str, str] | None = None

    for block_index, block in enumerate(block_list, start=1):
        source_ref = f"block-{block_index}"
        if block.kind == "table":
            headers = block.headers or []
            rows = block.rows or []
            if parse_image_request_table(
                manifest, headers, rows, source_ref
            ):
                continue
            if parse_key_value_table(
                manifest, headers, rows, source_ref
            ):
                continue
            if parse_combination_table(
                manifest, headers, rows, source_ref
            ):
                continue
            manifest["benchmarks"].append(
                {
                    "headers": headers,
                    "rows": rows,
                    "source_ref": source_ref,
                }
            )
            continue

        text = block.text
        metadata_pair = split_label(text)
        metadata_key = (
            match_alias(metadata_pair[0], METADATA_ALIASES)
            if metadata_pair
            else None
        )
        if metadata_key:
            manifest["product"][metadata_key] = metadata_pair[1]
            continue

        if (
            current_section == "combinations"
            and metadata_pair
            and combination_field(metadata_pair[0])
        ):
            current_combination = add_combination_line(
                manifest, text, source_ref, current_combination
            )
            continue

        unmapped_heading = re.sub(
            r"^\s*(?:第?[一二三四五六七八九十\d]+[章节、.．）)]?\s*)",
            "",
            text,
        )
        if re.sub(r"[：:\s]", "", unmapped_heading) in UNMAPPED_HEADINGS:
            if current_combination:
                manifest["combinations"].append(current_combination)
                current_combination = None
            current_section = None
            continue

        section_match = match_section_heading(text)
        if section_match:
            if current_combination:
                manifest["combinations"].append(current_combination)
                current_combination = None
            current_section, inline_content = section_match
            if inline_content:
                if current_section == "introduction":
                    add_intro(manifest, inline_content, source_ref)
                elif current_section == "selling_points":
                    add_selling_point(manifest, inline_content, source_ref)
                elif current_section == "audiences":
                    add_audience(manifest, inline_content, source_ref)
                elif current_section == "combinations":
                    current_combination = add_combination_line(
                        manifest, inline_content, source_ref, None
                    )
                elif current_section == "precautions":
                    add_precaution(manifest, inline_content, source_ref)
                else:
                    manifest["benchmarks"].append(
                        {"raw_text": inline_content, "source_ref": source_ref}
                    )
            continue

        inferred = current_section or classify_unheaded(text)
        if inferred == "introduction":
            add_intro(manifest, text, source_ref)
        elif inferred == "selling_points":
            add_selling_point(manifest, text, source_ref)
        elif inferred == "audiences":
            add_audience(manifest, text, source_ref)
        elif inferred == "combinations":
            current_combination = add_combination_line(
                manifest, text, source_ref, current_combination
            )
        elif inferred == "benchmarks":
            manifest["benchmarks"].append(
                {"raw_text": strip_item_prefix(text), "source_ref": source_ref}
            )
        elif inferred == "precautions":
            add_precaution(manifest, text, source_ref)
        else:
            if (
                not manifest["product"]["display_name"]
                and (block.heading_hint or block_index == 1)
                and len(text) <= 40
            ):
                manifest["product"]["display_name"] = text
            else:
                manifest["unmapped_content"].append(
                    {"text": text, "source_ref": source_ref}
                )

    if current_combination:
        manifest["combinations"].append(current_combination)

    max_page01_items = max(
        len(manifest["introduction"]),
        len(manifest["selling_points"]),
        len(manifest["audiences"]),
    )
    manifest["page_rules"] = {
        "cover": {
            "mode": "locked-source-slide",
            "source_template_id": "company-pptx-required",
        },
        "page01": {
            "layout": "source-page-01",
            "required_sections": ["商品介绍", "核心卖点", "适宜人群"],
            "items_per_page": 3,
            "page_count": max(1, (max_page01_items + 2) // 3),
        },
        "page02": {
            "layout": "source-page-02",
            "required_columns": [
                "应用场景",
                "联合用药",
                "产品图片展示",
                "销售话术",
            ],
            "rows_per_page": 3,
            "page_count": max(1, (len(manifest["combinations"]) + 2) // 3),
        },
        "page03": {
            "layout": "source-page-03",
            "page_count": max(1, (len(manifest["benchmarks"]) + 4) // 5),
        },
        "page04": {
            "layout": "source-page-04",
            "items_per_page": 5,
            "page_count": max(1, (len(manifest["precautions"]) + 4) // 5),
        },
    }
    manifest["blank_fields"] = collect_blank_fields(manifest)
    manifest["template_dependency"] = (
        "精确继承公司封面及原 01/02/03/04 页面，需要公司原始 PPTX。"
    )
    return manifest


def collect_blank_fields(manifest: dict[str, Any]) -> list[str]:
    if manifest.get("courseware_profile") == "disease-product-scenario-18":
        blanks = [
            f"course.{key}"
            for key, value in manifest["course"].items()
            if not normalize_space(value)
        ]
        required_sections = (
            "disease_definition",
            "disease_symptoms",
            "syndrome_comparison",
            "treatment_principles",
            "syndrome_subtypes",
            "product_information",
            "product_advantages",
            "product_advantage_summary",
            "audience_scenarios",
            "consultation_framework",
            "scenario_solutions",
            "daily_care",
            "weighted_product_detail",
            "weighted_product_comparison",
        )
        for key in required_sections:
            if not manifest["content_sections"].get(key):
                blanks.append(f"content_sections.{key}")
        if not manifest["authorized_assets"]:
            blanks.append("authorized_assets")
        return blanks

    if manifest.get("courseware_profile") == "product-brief-5":
        required_product_fields = (
            "display_name",
            "code",
            "specification",
            "one_line_selling_point",
        )
        blanks = [
            f"product.{key}"
            for key in required_product_fields
            if not normalize_space(manifest["product"].get(key, ""))
        ]
        for key in (
            "introduction",
            "selling_points",
            "audiences",
            "combinations",
            "benchmarks",
            "precautions",
        ):
            if not manifest[key]:
                blanks.append(key)
        if not manifest["authorized_assets"]:
            blanks.append("authorized_assets")
        return blanks

    blanks = [
        f"product.{key}"
        for key, value in manifest["product"].items()
        if not normalize_space(value)
    ]
    for key in (
        "introduction",
        "selling_points",
        "audiences",
        "combinations",
        "benchmarks",
        "precautions",
    ):
        if not manifest[key]:
            blanks.append(key)
    return blanks


def safe_stem(value: str) -> str:
    clean = re.sub(r'[\\/:*?"<>|\s]+', "-", value).strip("-")
    return clean[:80] or "未命名商品"


def source_hash(path: Path | None, text: str | None = None) -> str:
    payload = path.read_bytes() if path else (text or "").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def gather_inputs(paths: list[str]) -> list[Path]:
    sources: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            sources.extend(
                sorted(
                    candidate
                    for candidate in path.rglob("*")
                    if candidate.suffix.lower() in SUPPORTED_SUFFIXES
                )
            )
        elif path.suffix.lower() in SUPPORTED_SUFFIXES:
            sources.append(path)
        else:
            raise ValueError(f"不支持的输入：{path}")
    return sources


def write_manifest(
    manifest: dict[str, Any], output_dir: Path, used_names: set[str]
) -> dict[str, Any]:
    preferred = (
        manifest["product"]["code"]
        or manifest["product"]["display_name"]
        or Path(manifest["source"]["name"]).stem
    )
    stem = safe_stem(preferred)
    base = stem
    suffix = 2
    while stem in used_names:
        stem = f"{base}-{suffix}"
        suffix += 1
    used_names.add(stem)

    manifest["project_id"] = f"courseware.{stem}"
    manifest_path = output_dir / "manifests" / f"{stem}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    prompt_package = ""
    if manifest["image_requests"]:
        prompt_path = output_dir / "prompts" / f"{stem}_图片生成提示词.txt"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        sections = []
        for index, request in enumerate(manifest["image_requests"], start=1):
            header = (
                f"图片 {index}｜{request['target'] or '未指定位置'}"
                f"｜主题：{request['topic']}"
            )
            body = request["prompt"] or (
                "该位置涉及真实商品、包装、说明书或证据资料，"
                "必须使用公司授权原图，不生成 AI 仿制图。"
            )
            sections.append(f"{header}\n\n{body}")
        prompt_path.write_text(
            "\n\n".join(sections) + "\n",
            encoding="utf-8",
        )
        prompt_package = str(prompt_path.relative_to(output_dir))
    return {
        "project_id": manifest["project_id"],
        "product_name": manifest["product"]["display_name"],
        "source": manifest["source"]["name"],
        "courseware_type": manifest.get("courseware_type", "未指定（旧版输入）"),
        "template_id": manifest["template_id"],
        "planned_page_count": sum(
            rule.get("page_count", 0)
            for rule in manifest["page_rules"].values()
            if isinstance(rule, dict)
        ),
        "blank_fields": manifest["blank_fields"],
        "unmapped_count": len(manifest["unmapped_content"]),
        "image_request_count": len(manifest["image_requests"]),
        "prompt_package": prompt_package,
        "manifest": str(manifest_path.relative_to(output_dir)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将一份商品文本/Word自动整理为一份可编辑课件清单。"
    )
    parser.add_argument("inputs", nargs="*", help="TXT、Markdown、DOCX 文件或目录")
    parser.add_argument("--stdin", action="store_true", help="从标准输入读取一件商品")
    parser.add_argument("--name", default="粘贴文本", help="标准输入的商品/来源名称")
    parser.add_argument(
        "--output-dir",
        default="outputs/courseware-natural-import",
        help="输出目录",
    )
    args = parser.parse_args()

    if not args.inputs and not args.stdin:
        parser.error("请提供至少一个文件/目录，或使用 --stdin。")

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()
    index: list[dict[str, Any]] = []

    for path in gather_inputs(args.inputs):
        blocks, source_type = read_source(path)
        manifest = parse_blocks(blocks, path.name, source_type)
        manifest["source"]["sha256"] = source_hash(path)
        index.append(write_manifest(manifest, output_dir, used_names))

    if args.stdin:
        raw_text = sys.stdin.read()
        manifest = parse_blocks(text_blocks(raw_text), args.name, "pasted-text")
        manifest["source"]["sha256"] = source_hash(None, raw_text)
        index.append(write_manifest(manifest, output_dir, used_names))

    index_path = output_dir / "批量导入索引.json"
    index_path.write_text(
        json.dumps({"products": index}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"output_dir": str(output_dir), "products": index},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
