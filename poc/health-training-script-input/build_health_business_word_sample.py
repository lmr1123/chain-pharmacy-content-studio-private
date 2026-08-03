#!/usr/bin/env python3
"""Build the unified business-facing health-training Word sample."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from poc.business_word_common import (  # noqa: E402
    add_chapter,
    add_course_info_page,
    add_cover,
    add_reusable_block,
    create_document,
    save_document,
)


SOURCE = ROOT / "samples/health-training-script/风热证视频培训_业务填写真实样本.json"
SHOWCASE_DIR = ROOT / "assets/business-input-guides/settled-template-frames"
SHOWCASE_FRAMES = [
    {
        "path": SHOWCASE_DIR / "health-template-reference-005s.png",
        "label": "模板角色与固定母版",
        "source_mark": "健康沉淀模板 00:05",
    },
    {
        "path": SHOWCASE_DIR / "health-template-reference-018s.png",
        "label": "典型症状图文页",
        "source_mark": "健康沉淀模板 00:18",
    },
    {
        "path": SHOWCASE_DIR / "health-template-reference-026s.png",
        "label": "病因机理讲解页",
        "source_mark": "健康沉淀模板 00:26",
    },
]
OUTPUT = (
    ROOT
    / "outputs/health-training-script-input/健康知识视频培训_业务Word脚本填写示例_风热证.docx"
)


def build():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    course = data["course"]
    document = create_document("健康知识视频培训")
    add_cover(
        document,
        document_type="健康知识视频培训",
        example_title="中医基础知识——风热证",
        notice=data["sample_notice"],
        showcase_frames=SHOWCASE_FRAMES,
    )
    add_course_info_page(
        document,
        [
            ("培训主题", course["training_title"]),
            ("培训对象", course["audience"]),
            ("学习目标", course["learning_objective"]),
            ("期望时长（可选）", course["expected_duration"]),
            ("内容负责人", course["content_owner"]),
            ("文件级审核引用（可选）", "正式项目填写审批单号或链接；样例留空"),
            ("课程级授权素材", "\n".join(course["authorized_assets"]) or "无"),
        ],
    )
    document.add_page_break()
    document.add_heading(course["training_title"], level=1)
    for index, item in enumerate(data["sections"]):
        add_chapter(
            document,
            heading=f"{item['section_no']}｜{item['section_title']}",
            approved_text=item["approved_text"],
            screen_text=item["must_display"],
            assets=item["authorized_assets"],
            page_break=index > 0,
        )
    add_reusable_block(document, example_hint="病因机理、典型症状、生活建议")
    save_document(
        document,
        OUTPUT,
        title="健康知识视频培训业务 Word 填写示例——风热证",
        subject="统一业务输入母版：审核内容与授权素材驱动的视频培训输入",
        keywords="培训视频, 统一Word母版, 风热证, 审核原文, 授权素材, 真实成片截图",
    )
    print(OUTPUT)


if __name__ == "__main__":
    build()
