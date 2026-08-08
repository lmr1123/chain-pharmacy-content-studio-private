#!/usr/bin/env python3
"""Build layer-manifest.json from content-model.json (parameterized).

Usage:
  python3 build_layer_manifest.py --model PATH --out PATH [--prefix editable:cw4]

Defaults (if flags omitted) keep cw4 gold path behavior for local re-runs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent
REPO = ENGINE_ROOT.parents[2]
DEFAULT_MODEL = (
    REPO
    / "production-library/validation/courseware/product-courseware-4-faithful-replica-v1/content-model.json"
)
DEFAULT_OUT = (
    REPO
    / "production-library/validation/courseware/product-courseware-4-faithful-replica-v1/layer-manifest.json"
)
DEFAULT_PREFIX = "editable:cw4"


def eid(prefix: str, page: str, role: str) -> str:
    return f"{prefix}:{page}:{role}"


def text_layer(prefix: str, page: str, role: str, text: str, replace: str = "theme_copy") -> dict:
    return {
        "element_id": eid(prefix, page, role),
        "page_id": page,
        "role": role,
        "kind": "text",
        "replace_rule": replace,
        "default_text": text or "",
        "slot": None,
        "asset_key": None,
    }


def image_layer(
    prefix: str,
    page: str,
    role: str,
    asset_key: str,
    slot: str,
    replace: str = "business_authorized",
) -> dict:
    return {
        "element_id": eid(prefix, page, role),
        "page_id": page,
        "role": role,
        "kind": "image",
        "replace_rule": replace,
        "default_text": None,
        "slot": slot,
        "asset_key": asset_key,
    }


def build(model: dict, prefix: str) -> dict:
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
            layers.append(text_layer(prefix, sid, "title_pill", sc.get("title_pill", "")))
            layers.append(text_layer(prefix, sid, "badge", sc.get("badge", "好物推荐")))
            for i, b in enumerate(sc.get("benefits") or []):
                layers.append(text_layer(prefix, sid, f"benefit.{i+1}", b))
            layers.append(
                image_layer(
                    prefix, sid, "icon_check", "icon-check-red.png", "slot.icon.check", "theme_illustration"
                )
            )
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "badge_img",
                    "badge-hot-recommend.png",
                    "slot.badge.hot",
                    "theme_illustration",
                )
            )
            for role, key, slot in [
                ("pack_a", "slot-pack-box-a.png", "slot.pack.box_a"),
                ("pack_b", "slot-pack-box-b.png", "slot.pack.box_b"),
                ("pack_bottle", "slot-pack-bottle.png", "slot.pack.bottle"),
            ]:
                layers.append(image_layer(prefix, sid, role, key, slot))

        elif stype == "time_list":
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "magazine",
                    "slot-time-magazine.png",
                    "slot.time.magazine",
                    "authorization_dependency",
                )
            )
            layers.append(
                text_layer(
                    prefix,
                    sid,
                    "card_title",
                    sc.get("card_title") or "对人类健康贡献最大的10种健康食品",
                )
            )
            for i, line in enumerate(sc.get("list") or ["1.番茄", "2.***", "3.***"]):
                layers.append(text_layer(prefix, sid, f"list.{i+1}", line))

        elif stype == "broll":
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "photo",
                    "slot-photo-tomato.png",
                    "slot.photo.tomato",
                    "authorization_dependency",
                )
            )

        elif stype == "product_intro":
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "vine",
                    "slot-photo-vine.png",
                    "slot.photo.vine",
                    "authorization_dependency",
                )
            )
            for role, key, slot in [
                ("pack_a", "slot-pack-box-a.png", "slot.pack.box_a"),
                ("pack_b", "slot-pack-box-b.png", "slot.pack.box_b"),
                ("pack_bottle", "slot-pack-bottle.png", "slot.pack.bottle"),
            ]:
                layers.append(image_layer(prefix, sid, role, key, slot))

        elif stype == "benefit_chain":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "三大核心功效")))
            layers.append(text_layer(prefix, sid, "section", sc.get("section", "")))
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "chevron",
                    "icon-chevron-lime.png",
                    "slot.icon.chevron",
                    "theme_illustration",
                )
            )
            chain_assets = {
                "S04_benefit_1": [
                    ("tomato", "tomato.png"),
                    ("arrow", "arrow-red.png"),
                    ("prostate", "prostate-diagram.png"),
                ],
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
                    image_layer(prefix, sid, role, key, f"slot.illu.{role}", "theme_illustration")
                )

        elif stype == "feature_origin":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "产品特点")))
            layers.append(text_layer(prefix, sid, "section", sc.get("section", "1、产地好")))
            layers.append(
                text_layer(
                    prefix,
                    sid,
                    "map_caption",
                    sc.get("map_caption", "中国分省地图—新疆维吾尔自治区"),
                )
            )
            layers.append(
                image_layer(
                    prefix, sid, "map", "map-xinjiang.png", "slot.illu.map_xinjiang", "theme_illustration"
                )
            )

        elif stype == "feature_material":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "产品特点")))
            layers.append(text_layer(prefix, sid, "section", sc.get("section", "2、原料优")))
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "vine",
                    "slot-photo-vine.png",
                    "slot.photo.vine",
                    "authorization_dependency",
                )
            )

        elif stype == "feature_content":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "产品特点")))
            layers.append(text_layer(prefix, sid, "section", sc.get("section", "3、含量高")))
            layers.append(text_layer(prefix, sid, "eq", "="))
            layers.append(
                image_layer(prefix, sid, "softgel", "softgel.png", "slot.illu.softgel", "theme_illustration")
            )
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "five_tomatoes",
                    "five-tomatoes.png",
                    "slot.illu.five_tomatoes",
                    "theme_illustration",
                )
            )

        elif stype == "audience":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "适宜人群")))
            items = sc.get("items") or []
            icon_map = {
                "prostate": "prostate-diagram.png",
                "couple": "couple.png",
                "audience_beauty": "audience-beauty.png",
                "audience_weak": "audience-weak.png",
            }
            for i, it in enumerate(items):
                layers.append(text_layer(prefix, sid, f"label.{i+1}", it.get("label", "")))
                icon = it.get("icon", "")
                key = icon_map.get(icon, "prostate-diagram.png")
                layers.append(
                    image_layer(
                        prefix, sid, f"icon.{i+1}", key, f"slot.illu.audience.{i+1}", "theme_illustration"
                    )
                )

        elif stype in ("efficacy_recap_table", "summary_table") or sid == "S11_summary":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "")))
            layers.append(text_layer(prefix, sid, "side_left", sc.get("side_left", "")))
            layers.append(text_layer(prefix, sid, "side_right", sc.get("side_right", "")))
            for i, row in enumerate(sc.get("rows") or []):
                layers.append(text_layer(prefix, sid, f"row.{i+1}.label", row.get("label", "")))
                layers.append(text_layer(prefix, sid, f"row.{i+1}.body", row.get("body", "")))

        elif stype == "related_meds":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "四、关联用药")))
            for i, n in enumerate(sc.get("nav") or []):
                layers.append(text_layer(prefix, sid, f"nav.{i+1}", n))
            layers.append(text_layer(prefix, sid, "note", sc.get("note", "")))
            layers.append(text_layer(prefix, sid, "left_label", sc.get("left_label", "")))
            layers.append(text_layer(prefix, sid, "right_label", sc.get("right_label", "")))
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "pack_left",
                    sc.get("left_pack", "slot-pack-lycopene.png"),
                    "slot.pack.primary",
                )
            )
            layers.append(
                image_layer(
                    prefix,
                    sid,
                    "pack_right",
                    sc.get("right_pack", "slot-pack-zinc.png"),
                    "slot.pack.related",
                )
            )

        elif stype in ("summary_4col", "summary_row_headers") or sid == "S14_summary_key":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "总结")))
            layers.append(
                text_layer(prefix, sid, "eyebrow", sc.get("eyebrow", "敲重点 · 一页复习"))
            )
            layers.append(text_layer(prefix, sid, "footer", sc.get("footer", "")))
            cols = sc.get("columns") or []
            for i, col in enumerate(cols):
                header = col.get("header", f"row{i+1}")
                body = "\n".join(col.get("items") or [])
                layers.append(text_layer(prefix, sid, f"row.{i+1}.label", header))
                layers.append(text_layer(prefix, sid, f"row.{i+1}.body", body))

        elif stype == "hook_pain_data":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter") or sc.get("title", "")))
            for i, chip in enumerate(sc.get("symptoms") or sc.get("chips") or []):
                layers.append(text_layer(prefix, sid, f"chip.{i+1}", chip if isinstance(chip, str) else chip.get("text", "")))
            for i, st in enumerate(sc.get("stats") or []):
                layers.append(text_layer(prefix, sid, f"stat{i+1}.number", str(st.get("number", st.get("value", "")))))
                layers.append(text_layer(prefix, sid, f"stat{i+1}.unit", st.get("unit", "")))

        elif stype == "combination_guidance":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "")))
            for i, row in enumerate(sc.get("rows") or sc.get("items") or []):
                layers.append(text_layer(prefix, sid, f"row.{i+1}.label", row.get("scene") or row.get("label", "")))
                layers.append(
                    text_layer(
                        prefix,
                        sid,
                        f"row.{i+1}.body",
                        row.get("body") or row.get("script", ""),
                    )
                )

        elif stype == "precautions":
            layers.append(text_layer(prefix, sid, "chapter", sc.get("chapter", "")))
            for i, it in enumerate(sc.get("items") or sc.get("list") or []):
                t = it if isinstance(it, str) else it.get("text", "")
                layers.append(text_layer(prefix, sid, f"item.{i+1}", t))

        subs = sc.get("subtitles") or []
        if subs:
            layers.append(
                text_layer(prefix, sid, "subtitle_sample", subs[-1].get("text", ""), "system")
            )

    return {
        "project_id": model.get("project_id", "unknown"),
        "template_id": model.get("template_id") or model.get("project_id"),
        "status": "editable-delivery",
        "engine": "courseware-pptx-v1",
        "element_id_prefix": prefix,
        "content_model": "content-model.json",
        "channels": ["video_still", "pptx"],
        "layer_count": len(layers),
        "pages": pages,
        "layers": layers,
        "experience": model.get("experience_settled"),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build layer-manifest.json (parameterized)")
    p.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="content-model.json path")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output layer-manifest.json")
    p.add_argument("--prefix", default=DEFAULT_PREFIX, help="element id prefix")
    args = p.parse_args(argv)

    model_path = args.model.resolve()
    out_path = args.out.resolve()
    if not model_path.is_file():
        print(f"ERROR: model not found: {model_path}", file=sys.stderr)
        return 2

    model = json.loads(model_path.read_text(encoding="utf-8"))
    man = build(model, args.prefix)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} layers={man['layer_count']} pages={len(man['pages'])} prefix={args.prefix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
