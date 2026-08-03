#!/usr/bin/env python3
"""Parse notebook-like video training Word files into content-first manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[2]
COURSEWARE_WORD_DIR = ROOT / "poc/courseware-export/text-word-import"
sys.path.insert(0, str(COURSEWARE_WORD_DIR))

from import_universal_courseware_content import (  # noqa: E402
    gather_inputs,
    is_placeholder,
    normalize,
    parse_docx as parse_notebook_docx,
)


SCHEMA_VERSION = "video-content-notebook-v1"
VIDEO_ROUTES = {
    "health": {
        "video_type": "health_knowledge",
        "template_id": "template.health-reference-tech-v1",
        "style_pack_id": "style-pack.reference-medical-tech-v1",
    },
    "product": {
        "video_type": "product_training",
        "template_id": "template.product-training-faithful-v1",
        "style_pack_id": "style-pack.reference-product-blue-v1",
    },
}


def extract_expected_duration(path: Path) -> str:
    document = Document(path)
    for paragraph in document.paragraphs:
        text = normalize(paragraph.text)
        for label in ("期望时长（可不填）", "期望时长"):
            prefix = f"{label}："
            if text.startswith(prefix):
                value = normalize(text[len(prefix) :])
                return "" if is_placeholder(value) else value
    return ""


def parse_video_docx(path: Path, asset_root: Path, video_type: str) -> dict:
    base = parse_notebook_docx(path, asset_root)
    route = VIDEO_ROUTES[video_type]
    sections = []
    for section in base["sections"]:
        sections.append(
            {
                "section_id": section["section_id"],
                "title": section["title"],
                "approved_narration": section["paragraphs"],
                "images": section["images"],
                "content_metrics": section["content_metrics"],
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "source": base["source"],
        "video": {
            **base["course"],
            "expected_duration": extract_expected_duration(path),
        },
        "routing": route,
        "sections": sections,
        "unattached_images": base["unattached_images"],
        "content_metrics": base["content_metrics"],
        "planning_policy": {
            "content_order": "preserve_business_order",
            "scene_recipe_selection": "ai_select_within_bound_style_pack",
            "scene_count": "adaptive",
            "duration": "adaptive_to_approved_narration",
            "fixed_section_count": False,
            "fixed_scene_count": False,
            "template_screenshots_in_input": False,
            "business_storyboard_design_required": False,
            "business_preview_required": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将记事本式业务 Word 解析为内容驱动的视频规划输入。"
    )
    parser.add_argument("inputs", nargs="+", help="DOCX 文件或目录")
    parser.add_argument(
        "--video-type",
        required=True,
        choices=sorted(VIDEO_ROUTES),
        help="由提交入口选择健康知识或商品培训视频路由",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/video-training-universal-import",
        help="输出目录",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for path in gather_inputs(args.inputs):
        stem = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", path.stem).strip("-")
        manifest = parse_video_docx(
            path,
            output_dir / "assets" / stem,
            args.video_type,
        )
        manifest_path = output_dir / "manifests" / f"{stem}.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        index.append(
            {
                "source": path.name,
                "theme": manifest["video"]["theme"],
                "video_type": manifest["routing"]["video_type"],
                "section_count": manifest["content_metrics"]["section_count"],
                "image_count": manifest["content_metrics"]["image_count"],
                "manifest": str(manifest_path.relative_to(output_dir)),
            }
        )

    index_path = output_dir / "批量导入索引.json"
    index_path.write_text(
        json.dumps({"videos": index}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"output_dir": str(output_dir), "videos": index},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
