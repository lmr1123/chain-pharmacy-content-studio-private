#!/usr/bin/env python3
"""Materialize production-quality preview/ for every settled template.

Source frames come only from already-signed gold samples / settled canonicals.
Does not invent demo artwork. Re-run after gold media updates.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SETTLED = REPO / "production-library/templates/settled"
VAL = REPO / "production-library/validation"
GS = VAL / "courseware/gold-samples"
GUIDES = REPO / "assets/business-input-guides"

# Business-facing catalog (Chinese names only for shelf)
CATALOG: list[dict] = [
    {
        "slug": "health-video-reference-tech-v1",
        "name_zh": "疾病科普视频（如风热证）",
        "one_liner": "健康知识讲解视频：症状 · 机理 · 治疗与用药建议",
        "gallery_title_zh": "疾病科普视频 · 风热证金样",
        "outputs": ["MP4 培训视频"],
        "category": "疾病科普",
        "production_ready": False,
        "status_label": "金样对照 · 新主题制作前请与制作确认",
        "status_note": "manifest 标记 visual-rework-required；业务可看效果与填框架，新病种量产前须制作确认。",
        "cover_src": GS / "wind-heat-video-gold-v1/web/media/cover-product.jpg",
        "keys": [
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/cover.jpg", "开场"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/symptoms.jpg", "典型症状"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/mechanism.jpg", "病因机理"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/treatment.jpg", "治疗思路"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/medication.jpg", "用药建议"),
            (GS / "wind-heat-video-gold-v1/web/media/thumbs/summary.jpg", "总结"),
        ],
        "fallback_keys": [
            (GUIDES / "settled-template-frames/health-template-reference-005s.png", "母版角色"),
            (GUIDES / "settled-template-frames/health-template-reference-018s.png", "症状页"),
            (GUIDES / "settled-template-frames/health-template-reference-026s.png", "机理页"),
            (GUIDES / "final-video-frames/health-wind-heat-003s-intro.png", "开场帧"),
            (GUIDES / "final-video-frames/health-wind-heat-021s-mechanism.png", "机理帧"),
            (GUIDES / "final-video-frames/health-wind-heat-052s-treatment.png", "治疗帧"),
        ],
        "voice_id": "voice.reference-pharmacist-qwen-v1",
    },
    {
        "slug": "product-video-faithful-v1",
        "name_zh": "商品培训视频（如辅酶 Q10）",
        "one_liner": "单品店员培训视频：介绍 · 功效 · 证据 · 人群 · 联合 · 总结",
        "gallery_title_zh": "商品培训视频 · 辅酶 Q10 金样",
        "outputs": ["MP4 培训视频"],
        "category": "商品培训",
        "production_ready": True,
        "status_label": "已签样 · 可换主题量产",
        "status_note": "换商品须提供审核旁白与授权包装图；讲解声走模板克隆语音包。",
        "cover_src": GS / "product-q10-video-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "product-q10-video-gold-v1/web/media/thumbs/opening.jpg", "开场"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/brand.jpg", "品牌/品类"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/efficacy.jpg", "核心功效"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/features.jpg", "产品特点"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/audience.jpg", "适宜人群"),
            (GS / "product-q10-video-gold-v1/web/media/thumbs/combo.jpg", "联合用药"),
        ],
        "fallback_keys": [
            (GUIDES / "settled-template-frames/product-template-reference-pair01.png", "讲师页"),
            (GUIDES / "settled-template-frames/product-template-reference-pair04.png", "图文讲解"),
            (GUIDES / "settled-template-frames/product-template-reference-pair06.png", "包装主视觉"),
            (GUIDES / "final-video-frames/product-q10-007s-overview.png", "概览"),
            (GUIDES / "final-video-frames/product-q10-015s-efficacy.png", "功效"),
            (GUIDES / "final-video-frames/product-q10-025s-evidence.png", "证据"),
        ],
        "voice_id": "voice.reference-pharmacist-qwen-v1",
    },
    {
        "slug": "product-courseware-green-v1",
        "name_zh": "绿色单品 PPT（如金银花露）",
        "one_liner": "五页绿色商品培训：介绍/卖点/人群 · 联合用药 · 对标 · 注意",
        "gallery_title_zh": "绿色商品培训 · 5 页",
        "outputs": ["可编辑 PPTX"],
        "category": "商品培训",
        "production_ready": True,
        "status_label": "已签样 · 可换主题量产",
        "status_note": "联合用药有几条排几行，禁止空白凑行。",
        "cover_src": GS / "jinyinhualu-pptx-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-01.png", "封面/介绍"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-02.png", "卖点与人群"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-03.png", "联合用药"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-04.png", "品种对标"),
            (GS / "jinyinhualu-pptx-gold-v1/web/media/slides/slide-05.png", "注意事项"),
        ],
        "fallback_keys": [
            (GUIDES / "courseware-template-slides/honeysuckle-template-slide-01.png", "页 1"),
            (GUIDES / "courseware-template-slides/honeysuckle-template-slide-02.png", "页 2"),
            (GUIDES / "courseware-template-slides/honeysuckle-template-slide-03.png", "页 3"),
        ],
        "voice_id": None,
    },
    {
        "slug": "disease-product-scenario-v1",
        "name_zh": "疾病+商品场景 PPT（如穿心莲）",
        "one_liner": "辨证知识 + 商品知识 + 销售场景的可编辑长课件",
        "gallery_title_zh": "疾病辨证与商品场景 · 穿心莲金样",
        "outputs": ["可编辑 PPTX"],
        "category": "商品培训",
        "production_ready": True,
        "status_label": "已签样 · 可换主题量产",
        "status_note": "章节可按内容增减；无资料的模块可整节省略。",
        "cover_src": GS / "chuanxinlian-pptx-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-01.png", "封面"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-03.png", "辨证/知识"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-09.png", "商品知识"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-14.png", "销售场景"),
            (GS / "chuanxinlian-pptx-gold-v1/web/media/slides/slide-18.png", "收尾页"),
        ],
        "fallback_keys": [
            (GUIDES / "courseware-template-slides/andrographolide-template-slide-01.png", "页 1"),
            (GUIDES / "courseware-template-slides/andrographolide-template-slide-09.png", "页 9"),
            (GUIDES / "courseware-template-slides/andrographolide-template-slide-14.png", "页 14"),
        ],
        "voice_id": None,
    },
    {
        "slug": "sufuda-mabaloshawei-product-courseware-3-v1",
        "name_zh": "商品培训课件3（视频+PPT，速福达壳）",
        "one_liner": "抗流感培训：讲解视频 + 可编辑 PPT 同源内容模型",
        "gallery_title_zh": "商品培训课件3 · 速福达金样",
        "outputs": ["MP4", "可编辑 PPTX"],
        "category": "商品培训",
        "production_ready": True,
        "status_label": "已签样 · 可换主题量产",
        "status_note": "默认使用速福达课件药师克隆语音包；包装/Logo 须授权原图。",
        "cover_src": VAL
        / "courseware/sufuda-product-courseware-3-gold-v1/web/media/cover-product.png",
        "keys": [
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-cover.png",
                "封面",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-flu.png",
                "流感背景",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-benefit.png",
                "核心利益",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-feature.png",
                "产品特点",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-audience.png",
                "适宜人群",
            ),
            (
                VAL / "courseware/sufuda-product-courseware-3-gold-v1/web/media/t-combo.png",
                "联合用药",
            ),
        ],
        "fallback_keys": [
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-01.png",
                "PPT 封面",
            ),
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-04.png",
                "PPT 卖点",
            ),
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-08.png",
                "PPT 人群",
            ),
            (
                VAL
                / "courseware/sufuda-product-courseware-3-gold-v1/web/media/pptx-slides/slide-10.png",
                "PPT 联合",
            ),
        ],
        "voice_id": "voice.sufuda-courseware-pharmacist-v1",
    },
    {
        "slug": "fuler-fanqiehongsu-product-courseware-4-v1",
        "name_zh": "商品培训课件4（视频+PPT，番茄红素壳）",
        "one_liner": "保健品培训：全片视频 + 16 页可编辑 PPT（关联用药/总结行标题语法）",
        "gallery_title_zh": "商品培训课件4 · 福尔番茄红素金样",
        "outputs": ["MP4", "可编辑 PPTX"],
        "category": "商品培训",
        "production_ready": True,
        "status_label": "已签样 · 可换主题量产",
        "status_note": "关联用药 note 在上、总结行标题完整句；无包装图时槽位待补，不仿包装。",
        "cover_src": VAL
        / "courseware/product-courseware-4-faithful-replica-v1/web/media/cover-product.png",
        "keys": [
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S00_cover.png",
                "封面",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S03_product_intro.png",
                "商品介绍",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S04_benefit_1.png",
                "利益点",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S10_audience.png",
                "适宜人群",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S12_related_1.png",
                "关联用药",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/stills/S11_summary.png",
                "总结",
            ),
        ],
        "fallback_keys": [
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/pptx-slides/slide-01.png",
                "PPT 1",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/pptx-slides/slide-05.png",
                "PPT 5",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/pptx-slides/slide-12.png",
                "PPT 12",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/thumbs/01.png",
                "缩略 1",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/thumbs/04.png",
                "缩略 4",
            ),
            (
                VAL
                / "courseware/product-courseware-4-faithful-replica-v1/web/media/thumbs/08.png",
                "缩略 8",
            ),
        ],
        "voice_id": "voice.sufuda-courseware-pharmacist-v1",
    },
    {
        "slug": "disease-health-shenke-blue-v1",
        "name_zh": "疾病健康知识培训 PPT（参课蓝）",
        "one_liner": "门店健康顾问疾病知识培训：概览、表现、检查、用药、关怀、一页通",
        "gallery_title_zh": "疾病健康知识培训 · 参课蓝金样",
        "outputs": ["可编辑 PPTX"],
        "category": "健康培训",
        "production_ready": True,
        "status_label": "已签样 · 可换病种量产",
        "status_note": "版式锁定参课蓝；换病改 content JSON 后重建。包装须授权原图；医学表述须业务复核。",
        "cover_src": GS / "uri-shenke-health-pptx-gold-v1/web/media/cover-product.png",
        "keys": [
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-02.png", "疾病概览"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-03.png", "临床表现"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-09.png", "对症用药表"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-14.png", "专业关怀"),
            (GS / "uri-shenke-health-pptx-gold-v1/web/media/slides/slide-18.png", "竖版一页通"),
        ],
        "fallback_keys": [
            # validation 媒体可能被 gitignore；settled 内 preview 作回退源
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/cover.png",
                "封面",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-01.png",
                "疾病概览",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-02.png",
                "临床表现",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-03.png",
                "对症用药表",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-04.png",
                "专业关怀",
            ),
            (
                SETTLED / "disease-health-shenke-blue-v1/preview/key-05.png",
                "竖版一页通",
            ),
        ],
        "voice_id": None,
    },
]


def ensure_rgb_png(src: Path, dest: Path, max_w: int = 1600) -> None:
    """Copy/convert to PNG; downscale only if wider than max_w (keep quality)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        if im.width > max_w:
            ratio = max_w / im.width
            im = im.resize((max_w, max(1, int(im.height * ratio))), Image.Resampling.LANCZOS)
        im.save(dest, "PNG", optimize=True)


def pick_keys(entry: dict) -> list[tuple[Path, str]]:
    chosen: list[tuple[Path, str]] = []
    for path, label in entry["keys"]:
        if path.is_file():
            chosen.append((path, label))
    if len(chosen) < 3:
        for path, label in entry.get("fallback_keys") or []:
            if path.is_file() and path not in {p for p, _ in chosen}:
                chosen.append((path, label))
            if len(chosen) >= 6:
                break
    return chosen[:6]


def update_manifest(slug: str, entry: dict, key_files: list[str], key_labels: list[str]) -> None:
    manifest_path = SETTLED / slug / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["preview"] = {
        "cover": "preview/cover.png",
        "key_frames": key_files,
        "key_frame_labels_zh": key_labels,
        "gallery_title_zh": entry["gallery_title_zh"],
        "one_liner": entry["one_liner"],
        "name_zh": entry["name_zh"],
        "category_zh": entry["category"],
        "outputs": entry["outputs"],
        "production_ready": entry["production_ready"],
        "status_label": entry["status_label"],
        "online_url": None,
    }
    data["business_catalog"] = {
        "name_zh": entry["name_zh"],
        "one_liner": entry["one_liner"],
        "blank_word": "业务提交_空白模板.docx",
        "filled_example": "业务提交_填写参考.docx",
        "framework_guide": "../../框架填写说明.md",
    }
    if entry.get("voice_id"):
        data["voice"] = {
            "voice_id": entry["voice_id"],
            "engine": "Qwen3-TTS-local-clone",
            "pace_policy": "v5-smooth",
            "forbid_system_tts": True,
        }
        # Keep existing voice_pack_id if already set
        if "voice_pack_id" not in data:
            data["voice_pack_id"] = entry["voice_id"]
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_preview_readme(preview_dir: Path, entry: dict, labels: list[str]) -> None:
    lines = [
        f"# 预览 · {entry['name_zh']}",
        "",
        f"- 一句话：{entry['one_liner']}",
        f"- 状态：{entry['status_label']}",
        f"- 说明：{entry['status_note']}",
        "",
        "## 关键帧",
        "",
    ]
    for i, lab in enumerate(labels, 1):
        lines.append(f"- `key-{i:02d}.png` — {lab}")
    lines.extend(
        [
            "",
            "来源：已签样金样/归档媒体，仅用于业务辨认课型；不得当新项目生产素材直接复用包装与 Logo 像素。",
            "",
        ]
    )
    (preview_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    catalog_out: list[dict] = []
    for entry in CATALOG:
        slug = entry["slug"]
        root = SETTLED / slug
        if not root.is_dir():
            raise SystemExit(f"missing settled template: {slug}")
        preview_dir = root / "preview"
        if preview_dir.exists():
            shutil.rmtree(preview_dir)
        preview_dir.mkdir(parents=True)

        cover_src = entry["cover_src"]
        if not cover_src.is_file():
            # last resort: first available key
            keys_try = pick_keys(entry)
            if not keys_try:
                raise SystemExit(f"no cover or keys for {slug}")
            cover_src = keys_try[0][0]
        ensure_rgb_png(cover_src, preview_dir / "cover.png")

        keys = pick_keys(entry)
        if len(keys) < 3:
            raise SystemExit(
                f"{slug}: need ≥3 key frames, got {len(keys)}: {[str(p) for p, _ in keys]}"
            )

        key_rel: list[str] = []
        key_labels: list[str] = []
        for i, (path, label) in enumerate(keys, 1):
            name = f"key-{i:02d}.png"
            ensure_rgb_png(path, preview_dir / name)
            key_rel.append(f"preview/{name}")
            key_labels.append(label)

        write_preview_readme(preview_dir, entry, key_labels)
        update_manifest(slug, entry, key_rel, key_labels)

        meta = {
            "slug": slug,
            "name_zh": entry["name_zh"],
            "one_liner": entry["one_liner"],
            "gallery_title_zh": entry["gallery_title_zh"],
            "outputs": entry["outputs"],
            "category": entry["category"],
            "production_ready": entry["production_ready"],
            "status_label": entry["status_label"],
            "status_note": entry["status_note"],
            "key_frame_labels_zh": key_labels,
            "voice_id": entry.get("voice_id"),
            "blank_word": "业务提交_空白模板.docx",
            "filled_example": "业务提交_填写参考.docx",
        }
        (preview_dir / "catalog-entry.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        catalog_out.append({**meta, "settled_dir": f"production-library/templates/settled/{slug}"})
        print(f"OK {slug}: cover + {len(keys)} keys")

    catalog_path = SETTLED / "business-catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "updated": "2026-08-03",
                "purpose": "业务模板货架单一数据源；由 sync_settled_template_previews.py 生成",
                "templates": catalog_out,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {catalog_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
