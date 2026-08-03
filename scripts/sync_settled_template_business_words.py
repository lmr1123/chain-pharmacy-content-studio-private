#!/usr/bin/env python3
"""Refresh business Word files stored beside the four settled templates."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MAPPINGS = {
    "health-video-reference-tech-v1": {
        "业务提交_空白模板.docx": (
            "outputs/video-training-natural-import/"
            "视频培训内容与素材提交_通用模板.docx"
        ),
        "业务提交_填写参考.docx": (
            "outputs/video-training-natural-import/"
            "风热证健康知识视频培训_真实已填样本.docx"
        ),
    },
    "product-video-faithful-v1": {
        "业务提交_空白模板.docx": (
            "outputs/video-training-natural-import/"
            "视频培训内容与素材提交_通用模板.docx"
        ),
        "业务提交_填写参考.docx": (
            "outputs/video-training-natural-import/"
            "辅酶Q10商品培训视频_真实已填样本.docx"
        ),
    },
    "product-courseware-green-v1": {
        "业务提交_空白模板.docx": (
            "outputs/courseware-natural-import/"
            "培训课件内容与素材提交_通用模板.docx"
        ),
        "业务提交_填写参考.docx": (
            "outputs/courseware-natural-import/"
            "风热证培训课件内容与素材提交_真实已填样本.docx"
        ),
    },
    "disease-product-scenario-v1": {
        "业务提交_空白模板.docx": (
            "outputs/courseware-natural-import/"
            "培训课件内容与素材提交_通用模板.docx"
        ),
        "业务提交_填写参考.docx": (
            "outputs/courseware-natural-import/"
            "风热证培训课件内容与素材提交_真实已填样本.docx"
        ),
    },
    "sufuda-mabaloshawei-product-courseware-3-v1": {
        "业务提交_空白模板.docx": (
            "outputs/courseware-natural-import/"
            "培训课件内容与素材提交_通用模板.docx"
        ),
        "业务提交_填写参考.docx": (
            "outputs/courseware-natural-import/"
            "风热证培训课件内容与素材提交_真实已填样本.docx"
        ),
    },
    "fuler-fanqiehongsu-product-courseware-4-v1": {
        "业务提交_空白模板.docx": (
            "outputs/courseware-natural-import/"
            "培训课件内容与素材提交_通用模板.docx"
        ),
        "业务提交_填写参考.docx": (
            "outputs/courseware-natural-import/"
            "风热证培训课件内容与素材提交_真实已填样本.docx"
        ),
    },
}


def main() -> None:
    settled_root = ROOT / "production-library/templates/settled"
    for template_slug, documents in MAPPINGS.items():
        template_dir = settled_root / template_slug
        if not template_dir.is_dir():
            raise FileNotFoundError(f"settled template directory missing: {template_dir}")
        for destination_name, source_relative in documents.items():
            source = ROOT / source_relative
            if not source.is_file():
                raise FileNotFoundError(f"business Word source missing: {source}")
            destination = template_dir / destination_name
            shutil.copy2(source, destination)
            print(f"{source_relative} -> {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
