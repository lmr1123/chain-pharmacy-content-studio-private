#!/usr/bin/env python3
"""Parse notebook-like courseware Word files into content-first manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


SCHEMA_VERSION = "courseware-content-notebook-v1"
META_LABELS = {
    "课件主题": "theme",
    "培训对象（可不填）": "audience",
    "培训对象": "audience",
    "培训目标（可不填）": "objective",
    "培训目标": "objective",
}
PLACEHOLDER_TEXTS = (
    "请填写",
    "板块标题（请替换）",
    "在这里直接写本板块的审核内容",
    "【在此处直接粘贴",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_placeholder(text: str) -> bool:
    compact = normalize(text)
    return not compact or any(compact.startswith(item) for item in PLACEHOLDER_TEXTS)


def image_relationships(paragraph: Paragraph) -> list[str]:
    relationships: list[str] = []
    for blip in paragraph._p.xpath(".//a:blip"):
        relationship = blip.get(qn("r:embed"))
        if relationship:
            relationships.append(relationship)
    return relationships


def layout_candidates(paragraph_count: int, image_count: int) -> list[str]:
    candidates: list[str] = []
    if image_count == 1:
        candidates.extend(["image_text_split", "image_hero"])
    elif image_count == 2:
        candidates.extend(["two_image_comparison", "two_image_gallery"])
    elif image_count >= 3:
        candidates.append("image_gallery_paginated")

    if paragraph_count == 1:
        candidates.extend(["single_focus", "definition"])
    elif paragraph_count == 2:
        candidates.extend(["two_card", "two_column"])
    elif paragraph_count == 3:
        candidates.append("three_card")
    elif paragraph_count == 4:
        candidates.append("four_card_grid")
    elif paragraph_count == 5:
        candidates.extend(["five_card_3_plus_2", "card_grid_paginated"])
    elif paragraph_count > 5:
        candidates.append("card_grid_paginated")
    else:
        candidates.append("section_title")
    return list(dict.fromkeys(candidates))


def write_image(document, relationship_id: str, output_dir: Path, index: int) -> dict:
    part = document.part.related_parts[relationship_id]
    suffix = Path(str(part.partname)).suffix or ".bin"
    filename = f"image-{index:03d}{suffix}"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_bytes(part.blob)
    return {
        "asset_path": str(path),
        "source_filename": Path(str(part.partname)).name,
        "caption_or_source": "",
    }


def parse_docx(path: Path, asset_root: Path) -> dict:
    document = Document(path)
    course = {"theme": "", "audience": "", "objective": ""}
    sections: list[dict] = []
    unattached_images: list[dict] = []
    current_section: dict | None = None
    last_images: list[dict] = []
    image_index = 0

    for item in document.iter_inner_content():
        if not isinstance(item, Paragraph):
            continue

        text = normalize(item.text)
        style_name = normalize(item.style.name if item.style else "")
        relationships = image_relationships(item)

        paragraph_images: list[dict] = []
        for relationship_id in relationships:
            image_index += 1
            image = write_image(
                document,
                relationship_id,
                asset_root,
                image_index,
            )
            if current_section is None:
                unattached_images.append(image)
            else:
                current_section["images"].append(image)
            paragraph_images.append(image)
        if paragraph_images:
            last_images = paragraph_images

        if style_name == "Universal Ignore":
            continue

        for label, key in META_LABELS.items():
            prefix = f"{label}："
            if text.startswith(prefix):
                value = normalize(text[len(prefix) :])
                course[key] = "" if is_placeholder(value) else value
                break
        else:
            if style_name.lower().startswith("heading 1") or style_name.startswith(
                "标题 1"
            ):
                if not is_placeholder(text):
                    current_section = {
                        "title": text,
                        "paragraphs": [],
                        "images": [],
                    }
                    sections.append(current_section)
                    last_images = []
                continue

            caption_match = re.match(
                r"^图片说明[／/]来源(?:（可不填）)?[：:]\s*(.*)$",
                text,
            )
            if caption_match:
                value = normalize(caption_match.group(1))
                if last_images and value:
                    for image in last_images:
                        image["caption_or_source"] = value
                continue

            if is_placeholder(text):
                continue
            if text and current_section is not None:
                current_section["paragraphs"].append(text)

    for index, section in enumerate(sections, start=1):
        section["section_id"] = f"section-{index:02d}"
        section["content_metrics"] = {
            "paragraph_count": len(section["paragraphs"]),
            "image_count": len(section["images"]),
        }
        section["layout_candidates"] = layout_candidates(
            len(section["paragraphs"]),
            len(section["images"]),
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "name": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "course": course,
        "sections": sections,
        "unattached_images": unattached_images,
        "content_metrics": {
            "section_count": len(sections),
            "paragraph_count": sum(
                len(section["paragraphs"]) for section in sections
            ),
            "image_count": image_index,
        },
        "planning_policy": {
            "template_selection": "ai_select_from_approved_page_type_library",
            "style_pack_selection": "one_style_pack_per_project",
            "page_count": "adaptive",
            "layout": "adaptive_to_content_and_image_count",
            "empty_cards": "forbidden",
            "fixed_section_count": False,
            "fixed_item_count": False,
            "business_preview_required": True,
        },
    }


def gather_inputs(values: list[str]) -> list[Path]:
    inputs: list[Path] = []
    for raw in values:
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            inputs.extend(sorted(path.glob("*.docx")))
        elif path.suffix.lower() == ".docx":
            inputs.append(path)
    return inputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将记事本式业务 Word 解析为内容驱动的课件规划输入。"
    )
    parser.add_argument("inputs", nargs="+", help="DOCX 文件或目录")
    parser.add_argument(
        "--output-dir",
        default="outputs/courseware-universal-import",
        help="输出目录",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []

    for path in gather_inputs(args.inputs):
        stem = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", path.stem).strip("-")
        manifest = parse_docx(path, output_dir / "assets" / stem)
        manifest_path = output_dir / "manifests" / f"{stem}.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        index.append(
            {
                "source": path.name,
                "theme": manifest["course"]["theme"],
                "section_count": manifest["content_metrics"]["section_count"],
                "image_count": manifest["content_metrics"]["image_count"],
                "manifest": str(manifest_path.relative_to(output_dir)),
            }
        )

    index_path = output_dir / "批量导入索引.json"
    index_path.write_text(
        json.dumps({"courseware": index}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output_dir": str(output_dir), "courseware": index}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
