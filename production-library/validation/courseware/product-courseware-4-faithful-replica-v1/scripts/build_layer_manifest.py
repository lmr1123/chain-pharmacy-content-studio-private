#!/usr/bin/env python3
"""Build layer-manifest.json from content-model.json (stable editable IDs).

Usage:
  python3 scripts/build_layer_manifest.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "content-model.json"
OUT = ROOT / "layer-manifest.json"
PREFIX = "editable:cw4"


def eid(page: str, role: str) -> str:
    return f"{PREFIX}:{page}:{role}"


def text_layer(page: str, role: str, text: str, replace: str = "theme_copy") -> dict:
    return {
        "element_id": eid(page, role),
        "page_id": page,
        "role": role,
        "kind": "text",
        "replace_rule": replace,
        "default_text": text or "",
        "slot": None,
        "asset_key": None,
    }


def image_layer(
    page: str,
    role: str,
    asset_key: str,
    slot: str,
    replace: str = "business_authorized",
) -> dict:
    return {
        "element_id": eid(page, role),
        "page_id": page,
        "role": role,
        "kind": "image",
        "replace_rule": replace,
        "default_text": None,
        "slot": slot,
        "asset_key": asset_key,
    }


def build(model: dict) -> dict:
    layers: list[dict] = []
    pages: list[dict] = []

    for sc in model["scenes"]:
        sid = sc["id"]
        stype = sc.get("type", "")
        layer_class = sc.get("layer", "observed_reference")
        page = {
            "id": sid,
            "type": stype,
            "layer": layer_class,
            "start": sc.get("start"),
            "end": sc.get("end"),
            "pptx_slide": True,
            "video_scene": True,
        }
        pages.append(page)

        if stype == "cover" or sid in ("S00_cover", "S15_end"):
            layers.append(text_layer(sid, "title_pill", sc.get("title_pill", "")))
            layers.append(text_layer(sid, "badge", sc.get("badge", "好物推荐")))
            for i, b in enumerate(sc.get("benefits") or []):
                layers.append(text_layer(sid, f"benefit.{i+1}", b))
            layers.append(
                image_layer(sid, "icon_check", "icon-check-red.png", "slot.icon.check", "theme_illustration")
            )
            layers.append(
                image_layer(sid, "badge_img", "badge-hot-recommend.png", "slot.badge.hot", "theme_illustration")
            )
            for role, key, slot in [
                ("pack_a", "slot-pack-box-a.png", "slot.pack.box_a"),
                ("pack_b", "slot-pack-box-b.png", "slot.pack.box_b"),
                ("pack_bottle", "slot-pack-bottle.png", "slot.pack.bottle"),
            ]:
                layers.append(image_layer(sid, role, key, slot))

        elif stype == "time_list":
            # 左侧时代杂志封面为位图槽，非 TIME 可编文字
            layers.append(
                image_layer(
                    sid,
                    "magazine",
                    "slot-time-magazine.png",
                    "slot.time.magazine",
                    "authorization_dependency",
                )
            )
            layers.append(text_layer(sid, "card_title", sc.get("card_title") or "对人类健康贡献最大的10种健康食品"))
            for i, line in enumerate(sc.get("list") or ["1.番茄", "2.***", "3.***"]):
                layers.append(text_layer(sid, f"list.{i+1}", line))

        elif stype == "broll":
            layers.append(
                image_layer(sid, "photo", "slot-photo-tomato.png", "slot.photo.tomato", "authorization_dependency")
            )

        elif stype == "product_intro":
            layers.append(
                image_layer(sid, "vine", "slot-photo-vine.png", "slot.photo.vine", "authorization_dependency")
            )
            for role, key, slot in [
                ("pack_a", "slot-pack-box-a.png", "slot.pack.box_a"),
                ("pack_b", "slot-pack-box-b.png", "slot.pack.box_b"),
                ("pack_bottle", "slot-pack-bottle.png", "slot.pack.bottle"),
            ]:
                layers.append(image_layer(sid, role, key, slot))

        elif stype == "benefit_chain":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "三大核心功效")))
            layers.append(text_layer(sid, "section", sc.get("section", "")))
            layers.append(
                image_layer(sid, "chevron", "icon-chevron-lime.png", "slot.icon.chevron", "theme_illustration")
            )
            # default chain assets by scene
            chain_assets = {
                "S04_benefit_1": [("tomato", "tomato.png"), ("arrow", "arrow-red.png"), ("prostate", "prostate-diagram.png")],
                "S05_benefit_2": [
                    ("tomato", "tomato.png"),
                    ("arrow1", "arrow-red.png"),
                    ("o2", "o2.png"),
                    ("arrow2", "arrow-red.png"),
                    ("woman", "skincare-woman.png"),
                ],
                "S06_benefit_3": [
                    ("tomato", "tomato.png"),
                    ("arrow1", "arrow-red.png"),
                    ("nk", "nk-cell.png"),
                    ("arrow2", "arrow-red.png"),
                    ("arm", "flex-arm.png"),
                ],
            }
            for role, key in chain_assets.get(sid, []):
                layers.append(
                    image_layer(sid, role, key, f"slot.illu.{role}", "theme_illustration")
                )

        elif stype == "feature_origin":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "产品特点")))
            layers.append(text_layer(sid, "section", sc.get("section", "1、产地好")))
            layers.append(text_layer(sid, "map_caption", sc.get("map_caption", "中国分省地图—新疆维吾尔自治区")))
            layers.append(
                image_layer(sid, "map", "map-xinjiang.png", "slot.illu.map_xinjiang", "theme_illustration")
            )

        elif stype == "feature_material":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "产品特点")))
            layers.append(text_layer(sid, "section", sc.get("section", "2、原料优")))
            layers.append(
                image_layer(sid, "vine", "slot-photo-vine.png", "slot.photo.vine", "authorization_dependency")
            )

        elif stype == "feature_content":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "产品特点")))
            layers.append(text_layer(sid, "section", sc.get("section", "3、含量高")))
            layers.append(text_layer(sid, "eq", "="))
            layers.append(
                image_layer(sid, "softgel", "softgel.png", "slot.illu.softgel", "theme_illustration")
            )
            layers.append(
                image_layer(sid, "five_tomatoes", "five-tomatoes.png", "slot.illu.five_tomatoes", "theme_illustration")
            )

        elif stype == "audience":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "适宜人群")))
            items = sc.get("items") or []
            icon_map = {
                "prostate": "prostate-diagram.png",
                "couple": "couple.png",
                "audience_beauty": "audience-beauty.png",
                "audience_weak": "audience-weak.png",
            }
            for i, it in enumerate(items):
                layers.append(text_layer(sid, f"label.{i+1}", it.get("label", "")))
                icon = it.get("icon", "")
                key = icon_map.get(icon, "prostate-diagram.png")
                layers.append(
                    image_layer(sid, f"icon.{i+1}", key, f"slot.illu.audience.{i+1}", "theme_illustration")
                )

        elif stype in ("efficacy_recap_table", "summary_table") or sid == "S11_summary":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "")))
            layers.append(text_layer(sid, "side_left", sc.get("side_left", "")))
            layers.append(text_layer(sid, "side_right", sc.get("side_right", "")))
            for i, row in enumerate(sc.get("rows") or []):
                layers.append(text_layer(sid, f"row.{i+1}.label", row.get("label", "")))
                layers.append(text_layer(sid, f"row.{i+1}.body", row.get("body", "")))

        elif stype == "related_meds":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "四、关联用药")))
            for i, n in enumerate(sc.get("nav") or []):
                layers.append(text_layer(sid, f"nav.{i+1}", n))
            layers.append(text_layer(sid, "note", sc.get("note", "")))
            layers.append(text_layer(sid, "left_label", sc.get("left_label", "")))
            layers.append(text_layer(sid, "right_label", sc.get("right_label", "")))
            layers.append(
                image_layer(
                    sid,
                    "pack_left",
                    sc.get("left_pack", "slot-pack-lycopene.png"),
                    "slot.pack.primary",
                )
            )
            layers.append(
                image_layer(
                    sid,
                    "pack_right",
                    sc.get("right_pack", "slot-pack-zinc.png"),
                    "slot.pack.related",
                )
            )

        elif stype in ("summary_4col", "summary_row_headers") or sid == "S14_summary_key":
            layers.append(text_layer(sid, "chapter", sc.get("chapter", "总结")))
            layers.append(text_layer(sid, "eyebrow", sc.get("eyebrow", "敲重点 · 一页复习")))
            layers.append(text_layer(sid, "footer", sc.get("footer", "")))
            # Prefer row_headers schema if present in columns
            cols = sc.get("columns") or []
            if sc.get("layout") == "row_headers" or True:
                # map columns -> rows for manifest (label = header, body = joined items)
                for i, col in enumerate(cols):
                    header = col.get("header", f"row{i+1}")
                    body = "\n".join(col.get("items") or [])
                    layers.append(text_layer(sid, f"row.{i+1}.label", header))
                    layers.append(text_layer(sid, f"row.{i+1}.body", body))

        # optional subtitle sample
        subs = sc.get("subtitles") or []
        if subs:
            layers.append(text_layer(sid, "subtitle_sample", subs[-1].get("text", ""), "system"))

    return {
        "project_id": model.get("project_id", "product-courseware-4-faithful-replica-v1"),
        "template_id": "template.product-courseware-4-faithful-replica-v1",
        "status": "editable-delivery",
        "content_model": "content-model.json",
        "channels": ["video_still", "pptx"],
        "interaction_contract": {
            "edit_text": "改 content-model 对应字段或 patches JSON，再 build_deliverables",
            "replace_image": "替换 assets/generated 槽位文件或 patches 中的 asset 路径",
            "export_pptx": "python3 scripts/export_editable_pptx.py",
            "export_video": "python3 scripts/export-full-film-video.py",
            "export_all": "python3 scripts/build_deliverables.py",
            "theme_replication": "复制 content-model + assets 槽位，改 theme_copy / business_authorized 字段",
        },
        "layer_count": len(layers),
        "pages": pages,
        "layers": layers,
        "experience": model.get("experience_settled"),
    }


def main() -> int:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    man = build(model)
    OUT.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} layers={man['layer_count']} pages={len(man['pages'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
