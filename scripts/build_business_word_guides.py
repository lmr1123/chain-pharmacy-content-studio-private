#!/usr/bin/env python3
"""Generate per-template business fill guides + product notebook filled sample.

Also refreshes settled filled-example mappings for product PPT templates so
business no longer sees 风热证 content as product format reference.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SETTLED = ROOT / "production-library/templates/settled"
OUT_SAMPLES = ROOT / "outputs/courseware-natural-import"

# Recommended modules for business (not fixed page counts)
GUIDES: dict[str, dict] = {
    "health-video-reference-tech-v1": {
        "name_zh": "疾病科普视频（如风热证）",
        "outputs": "MP4 培训视频",
        "modules": [
            "课程主题 / 开场",
            "典型症状",
            "病因与机理",
            "治疗思路",
            "用药与生活建议",
            "总结",
        ],
        "tips": [
            "**业务自助：** 在 WorkBuddy 对话里说病名+要点即可出片，不必找制作代跑。",
            "金样对照：`风热证_疾病科普视频_金样_v1.mp4`；换病种走 full 分段重渲（屏显/病名/旁白随主题换）。",
            "每个自然板块 = 可直接讲解的审核正文；有几章写几章，不需要的整段删。",
            "旁白须药师/合规已审；正式成片用模板克隆药师声，禁止系统朗读。",
        ],
        "chat_example": (
            "我要用【疾病科普视频】模板，主题是【病名，如感冒】。\n"
            "内容围绕：开场、基础认知、病因机理、典型症状、调理建议、用药建议、总结…。\n"
            "请整理后直接生成培训视频（画面随主题换，不要只换声音）。"
        ),
        "agent_commands": [
            "# 业务机 WorkBuddy 执行（默认 full；禁止 audio-shell）",
            ".venv-qwen-tts/bin/python scripts/generate_business_video.py --template health --sections-json <path> --with-tts --with-mp4 --copy-to-business-delivery",
            "# 仅规划（无 TTS 时）",
            "python3 scripts/generate_business_video.py --template health --mode plan --sections-json <path>",
        ],
        "filled_source": "outputs/video-training-natural-import/风热证健康知识视频培训_真实已填样本.docx",
        "blank_source": "outputs/video-training-natural-import/视频培训内容与素材提交_通用模板.docx",
    },
    "product-video-faithful-v1": {
        "name_zh": "商品培训视频（如辅酶 Q10）",
        "outputs": "MP4 培训视频",
        "modules": [
            "为什么要了解本商品",
            "商品基础信息",
            "核心功效 / 证据（审核稿）",
            "产品特点",
            "适宜人群",
            "联合用药（有几组写几组）",
            "总结",
        ],
        "tips": [
            "**业务自助：** 在 WorkBuddy 对话里说商品名+要点即可出片，不必找制作代跑。",
            "金样对照：`辅酶Q10_商品培训视频_金样_v1.mp4`；换商品走 full 分段重渲。",
            "一份内容一个商品；板块可删可重排。",
            "包装图用授权原图；无图则说明缺口，禁止仿包装。正式旁白 = 审核原文 + 模板克隆声。",
        ],
        "chat_example": (
            "我要用【商品培训视频】模板，商品是【商品名】。\n"
            "内容围绕：核心功效…、产品特点…、适宜人群…、联合用药 2 组…。\n"
            "请整理后直接生成培训视频（画面随主题换，不要只换声音）。"
        ),
        "agent_commands": [
            "# 业务机 WorkBuddy 执行（默认 full）",
            ".venv-qwen-tts/bin/python scripts/generate_business_video.py --template product --sections-json <path> --with-tts --with-mp4 --product-image <包装图可选> --copy-to-business-delivery",
            "# 仅规划（无 TTS 时）",
            "python3 scripts/generate_business_video.py --template product --mode plan --sections-json <path>",
        ],
        "filled_source": "outputs/video-training-natural-import/辅酶Q10商品培训视频_真实已填样本.docx",
        "blank_source": "outputs/video-training-natural-import/视频培训内容与素材提交_通用模板.docx",
    },
    "product-courseware-green-v1": {
        "name_zh": "绿色单品 PPT（如金银花露）",
        "outputs": "可编辑 PPTX",
        "modules": [
            "商品介绍（成分/功能/用法）",
            "核心卖点（1～N 条）",
            "适宜人群（1～N 类）",
            "联合用药话术（1～N 组；2 组就 2 行）",
            "品种对标（可选，无则整节删）",
            "注意事项（可选）",
        ],
        "tips": [
            "用空白通用 Word，按上列板块起标题即可；不必写页码。",
            "联合用药只写真实有的组数，禁止为对齐示例空出第三行。",
            "先收「内容初稿 + 缺口清单」，确认后再出 PPTX。",
        ],
        "filled_source": "outputs/courseware-natural-import/商品培训_绿色单品_记事本式填写参考_两行联合用药.docx",
        "blank_source": "outputs/courseware-natural-import/培训课件内容与素材提交_通用模板.docx",
    },
    "disease-product-scenario-v1": {
        "name_zh": "疾病+商品场景 PPT（如穿心莲）",
        "outputs": "可编辑 PPTX",
        "modules": [
            "疾病/辨证知识",
            "商品知识",
            "销售场景与话术",
            "其他需要培训的板块（自定）",
        ],
        "tips": [
            "板块按资料完整度裁剪；没有的整节删除。",
            "填写参考若为他主题，只学结构不抄医学结论。",
        ],
        "filled_source": "outputs/courseware-natural-import/穿心莲内酯滴丸_商品培训课件_业务真实内容样本.docx",
        "blank_source": "outputs/courseware-natural-import/培训课件内容与素材提交_通用模板.docx",
    },
    "sufuda-mabaloshawei-product-courseware-3-v1": {
        "name_zh": "商品培训课件3（视频+PPT，速福达壳）",
        "outputs": "MP4 + 可编辑 PPTX",
        "modules": [
            "课程开场 / 品类背景",
            "商品介绍与核心利益",
            "产品特点 / 证据",
            "适宜人群",
            "联合用药（有几组写几组）",
            "总结",
        ],
        "tips": [
            "视频与 PPT 同源内容：Word 按板块写审核文案即可。",
            "旁白走速福达课件药师克隆语音包。",
            "包装/Logo 必须授权原图。",
        ],
        "filled_source": "outputs/courseware-natural-import/商品培训_绿色单品_记事本式填写参考_两行联合用药.docx",
        "blank_source": "outputs/courseware-natural-import/培训课件内容与素材提交_通用模板.docx",
    },
    "fuler-fanqiehongsu-product-courseware-4-v1": {
        "name_zh": "商品培训课件4（视频+PPT，番茄红素壳）",
        "outputs": "MP4 + 可编辑 PPTX",
        "modules": [
            "开场 / 商品介绍",
            "核心利益点",
            "原料与含量（若有审核稿）",
            "适宜人群",
            "关联用药（有几组写几组）",
            "总结",
        ],
        "tips": [
            "关联用药 note 在上、总结行标题完整句为课件4 语法，业务只需交审核文案。",
            "无包装图 → 槽位待补。",
        ],
        "filled_source": "outputs/courseware-natural-import/商品培训_绿色单品_记事本式填写参考_两行联合用药.docx",
        "blank_source": "outputs/courseware-natural-import/培训课件内容与素材提交_通用模板.docx",
    },
    "disease-health-shenke-blue-v1": {
        "name_zh": "疾病健康知识培训 PPT（参课蓝）",
        "outputs": "可编辑 PPTX",
        "modules": [
            "疾病概览（定义 + 病因）",
            "临床表现",
            "检查方法",
            "治疗用药（一般 / 全身 / 局部 / 对症表）",
            "用药注意事项（禁用须审核稿）",
            "专业关怀",
            "一页通（竖版，可选）",
        ],
        "tips": [
            "业务只写自然板块正文与授权图，不写页码/坐标。",
            "对症表可标重点药名；包装用授权原图，禁止伪造品牌包装。",
            "注意事项：仅「禁用」类表述在成品中标红；医学结论须业务/医学复核。",
            "先收「内容初稿 + 缺口清单」，确认后再出 PPTX。",
        ],
        "list_rules_note": "对症表/注意事项列表：有几条写几条；没有的板块整节删除。",
        "agent_commands": [
            "cd production-library/templates/settled/disease-health-shenke-blue-v1/generator",
            "npm install   # 首次或新 clone 后",
            "node build-editable.mjs content/<主题>.content.json",
        ],
        "filled_source": "outputs/courseware-natural-import/风热证培训课件内容与素材提交_真实已填样本.docx",
        "blank_source": "outputs/courseware-natural-import/培训课件内容与素材提交_通用模板.docx",
    },
}


def _set_run_gray(paragraph, text: str) -> None:
    paragraph.clear()
    run = paragraph.add_run(text)
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)


def build_product_notebook_filled_sample() -> Path:
    """Notebook-style product sample with exactly 2 combination rows."""
    out = OUT_SAMPLES / "商品培训_绿色单品_记事本式填写参考_两行联合用药.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    doc.add_paragraph("培训课件内容与素材提交")
    p = doc.add_paragraph()
    _set_run_gray(
        p,
        "填写参考｜只示范格式。示例医学/价格表述为演示占位，正式主题必须替换为公司审核稿与授权包装。",
    )
    p = doc.add_paragraph()
    _set_run_gray(
        p,
        "联合用药本参考只写 2 组 → 成片必须只出 2 行，禁止空白第三行。",
    )
    doc.add_paragraph("课件主题：示例商品A（演示用，非正式品规）")
    doc.add_paragraph("培训对象（可不填）：连锁药店门店员工")
    doc.add_paragraph("培训目标（可不填）：掌握审核稿中的商品信息与联合推荐话术边界")

    doc.add_heading("商品介绍", level=1)
    doc.add_paragraph("主要成分：【待替换为审核原文】")
    doc.add_paragraph("功能主治/定位：【待替换为审核原文】")
    doc.add_paragraph("用法用量：【待替换为审核原文】")
    doc.add_paragraph("【在此处直接粘贴本品授权包装图；没有可删除本行】")
    doc.add_paragraph("图片说明／来源（可不填）：公司授权包装")

    doc.add_heading("核心卖点", level=1)
    doc.add_paragraph("卖点一：【审核表述】")
    doc.add_paragraph("卖点二：【审核表述】")

    doc.add_heading("适宜人群", level=1)
    doc.add_paragraph("人群一：【审核表述】")
    doc.add_paragraph("人群二：【审核表述】")

    doc.add_heading("联合用药话术", level=1)
    doc.add_paragraph(
        "方案 1｜场景：【场景甲】｜组合：示例商品A + 搭档甲｜话术：【审核话术甲】"
    )
    doc.add_paragraph(
        "方案 2｜场景：【场景乙】｜组合：示例商品A + 搭档乙｜话术：【审核话术乙】"
    )
    doc.add_paragraph("【可粘贴搭档包装图；无图删除本行】")

    doc.add_heading("注意事项", level=1)
    doc.add_paragraph("【说明书或审核注意事项；没有整节可删】")

    doc.save(out)
    return out


def write_guide(slug: str, meta: dict) -> Path:
    lines = [
        f"# 本课型怎么填 · {meta['name_zh']}",
        "",
        f"- 产物：{meta['outputs']}",
        f"- 空白 Word：同目录 `业务提交_空白模板.docx`",
        f"- 填写参考：`../../03_填写参考/{slug}/业务提交_填写参考.docx`（仅学格式）",
        "",
        "## 推荐板块（可删可增）",
        "",
    ]
    for i, m in enumerate(meta["modules"], 1):
        lines.append(f"{i}. {m}")
    lines.extend(["", "## 填写要点", ""])
    for t in meta["tips"]:
        lines.append(f"- {t}")
    chat = meta.get("chat_example") or (
        f"我要用【{meta['name_zh']}】，主题是【病名或商品名】。\n"
        "请按金样整理后生成成片。"
    )
    lines.extend(
        [
            "",
            "## 对话示例（复制给 WorkBuddy）",
            "",
            "```",
            chat,
            "```",
            "",
            "## 列表 / 模块硬规则",
            "",
        ]
    )
    if meta.get("list_rules_note"):
        lines.append(f"- {meta['list_rules_note']}")
    else:
        lines.extend(
            [
                "- 有几条写几条；联合用药 2 组 → 成品 2 行",
                "- 禁止空行凑满金样示例数",
                "- 没有的板块整节删除",
            ]
        )
    if meta.get("agent_commands"):
        lines.extend(["", "## 代理出片命令（业务无需操作）", "", "```bash"])
        lines.extend(meta["agent_commands"])
        lines.append("```")
    lines.append("")
    path = SETTLED / slug / "本课型怎么填.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def sync_words() -> None:
    for slug, meta in GUIDES.items():
        dest_dir = SETTLED / slug
        blank_src = ROOT / meta["blank_source"]
        filled_src = ROOT / meta["filled_source"]
        if not blank_src.is_file():
            raise FileNotFoundError(blank_src)
        if not filled_src.is_file():
            raise FileNotFoundError(filled_src)
        import shutil

        shutil.copy2(blank_src, dest_dir / "业务提交_空白模板.docx")
        shutil.copy2(filled_src, dest_dir / "业务提交_填写参考.docx")
        write_guide(slug, meta)
        print(f"OK words+guide {slug}")


def main() -> None:
    sample = build_product_notebook_filled_sample()
    print(f"Wrote {sample.relative_to(ROOT)}")
    sync_words()
    # update sync_settled mapping file note via rewrite of MAPPINGS is done in this script as SSOT
    catalog_note = SETTLED / "business-word-sources.json"
    catalog_note.write_text(
        __import__("json").dumps(
            {
                "version": "1.0.0",
                "note": "Authoritative Word sources for settled templates; regenerated by build_business_word_guides.py",
                "templates": {
                    slug: {
                        "blank": meta["blank_source"],
                        "filled": meta["filled_source"],
                        "name_zh": meta["name_zh"],
                    }
                    for slug, meta in GUIDES.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {catalog_note.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
