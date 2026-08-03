#!/usr/bin/env python3
"""Build the unified business-facing product-training Word sample."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from poc.business_word_common import (  # noqa: E402
    add_body,
    add_chapter,
    add_course_info_page,
    add_cover,
    add_reusable_block,
    create_document,
    save_document,
)


SOURCE = ROOT / "samples/product-training-script/辅酶Q10商品培训_业务填写样本.txt"
SHOWCASE_DIR = ROOT / "assets/business-input-guides/settled-template-frames"
SHOWCASE_FRAMES = [
    {
        "path": SHOWCASE_DIR / "product-template-reference-pair01.png",
        "label": "模板讲师角色页",
        "source_mark": "商品沉淀模板存档帧 01",
    },
    {
        "path": SHOWCASE_DIR / "product-template-reference-pair04.png",
        "label": "症状图文讲解页",
        "source_mark": "商品沉淀模板存档帧 04",
    },
    {
        "path": SHOWCASE_DIR / "product-template-reference-pair06.png",
        "label": "商品包装主视觉页",
        "source_mark": "商品沉淀模板存档帧 06",
    },
]
OUTPUT = (
    ROOT
    / "outputs/product-training-script-input/商品培训视频课件_业务填写Word样本.docx"
)


def parse_source():
    title = ""
    sections = []
    current = None
    current_field = None
    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            if current:
                sections.append(current)
            current = {
                "heading": line[3:].strip(),
                "narration": [],
                "screen_text": [],
                "assets": [],
            }
            current_field = None
        elif current and line == "【审核旁白原文】":
            current_field = "narration"
        elif current and line == "【必须原样上屏的事实／短文案】":
            current_field = "screen_text"
        elif current and line == "【本章节授权素材】":
            current_field = "assets"
        elif current and line and not line.startswith(">") and current_field:
            current[current_field].append(re.sub(r"^-\s*", "", line))
    if current:
        sections.append(current)
    for section in sections:
        for field in ("narration", "screen_text", "assets"):
            if not section[field]:
                raise ValueError(f"章节缺少 {field}：{section['heading']}")
    return title, sections


def build():
    title, sections = parse_source()
    document = create_document("商品知识培训视频")
    add_cover(
        document,
        document_type="商品知识培训视频",
        example_title="辅酶 Q10 商品培训",
        notice=(
            "重要：本示例只展示填写结构，不代表医学、药学、功效或合规审批已经完成。"
            "正式生产必须替换为公司最终审核原文和授权素材。"
        ),
        showcase_frames=SHOWCASE_FRAMES,
    )
    add_course_info_page(
        document,
        [
            ("培训主题", title),
            ("培训对象", "连锁药店门店员工（示例，请按实际项目替换）"),
            (
                "学习目标",
                "理解审核稿中的商品定位、核心特点、适宜人群、搭配建议和课程重点。",
            ),
            ("期望时长（可选）", "系统按审核原文估算"),
            ("内容负责人", "业务填写"),
            ("文件级审核引用（可选）", "正式项目填写审批单号或链接；样例留空"),
            (
                "课程级授权素材",
                "商品包装、品牌 Logo、说明书、检测或证据资料（按实际文件名填写）",
            ),
        ],
    )
    document.add_page_break()
    document.add_heading(title, level=1)
    for index, item in enumerate(sections):
        add_chapter(
            document,
            heading=item["heading"],
            approved_text="\n".join(item["narration"]),
            screen_text=item["screen_text"],
            assets=item["assets"],
            page_break=index > 0,
        )
    document.add_page_break()
    document.add_heading("提交前检查", level=1)
    for text in (
        "□ 所有旁白、功效、人群和联合方案均已审核。",
        "□ 不需要的栏目已经删除，章节顺序符合课程逻辑。",
        "□ 真实商品、品牌和证据图均为公司授权素材。",
        "□ 未确认内容已明确标注“待确认”，没有自行补写。",
        "□ 未填写画面意图、动效、组件、镜头时码或逐章节审核状态。",
    ):
        add_body(document, text, size=10.5, after=6, style="Courseware Ignore")
    add_reusable_block(document, example_hint="商品定位、核心特点、适宜人群")
    save_document(
        document,
        OUTPUT,
        title="商品知识培训视频业务 Word 填写示例——辅酶 Q10",
        subject="统一业务输入母版：审核内容与授权素材驱动的视频培训输入",
        keywords="培训视频, 统一Word母版, 辅酶Q10, 审核原文, 授权素材, 真实成片截图",
    )
    print(OUTPUT)


if __name__ == "__main__":
    build()
