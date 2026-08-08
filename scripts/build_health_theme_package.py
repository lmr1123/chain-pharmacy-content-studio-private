#!/usr/bin/env python3
"""按健康科普段语言 v1 生成主题制作包（脚本 + screen + 画面计划 + 过目页）。

默认不渲染视频。画面须全部过目后写 approval.json，再交给
generate_business_video / business_video_health_full（--theme-package）。

示例：
  python3 scripts/build_health_theme_package.py \\
    --theme 感冒 \\
    --sections-json path/to/sections.json \\
    --out-dir production-library/themes/ganmao-cold-v1
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from business_video_health_full import (
    map_sections_to_segments,
    theme_package_payload_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
LANG_PATH = (
    ROOT
    / "production-library/themes/health-segment-language-v1/language.json"
)
SYMPTOM_MASTER = ROOT / "assets/component-library/symptoms"
HERB_MASTER = ROOT / "assets/component-library/herbs"
ADVICE_MASTER = ROOT / "assets/component-library/advice-icons"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_source(path: Path) -> str:
    """Prefer repository-relative provenance without requiring output under ROOT."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip())
    return re.sub(r"-+", "-", s).strip("-")[:80] or "theme"


def extract_list_items(text: str, max_items: int = 8, max_len: int = 16) -> list[str]:
    raw = re.split(r"[。！？；;\n、,/]|[一二三四五六七八九十]+[、.．]|[0-9]+[\.、]", text)
    items: list[str] = []
    for p in raw:
        p = re.sub(r"^[、.\s]+", "", p.strip())
        p = re.sub(r"^(常见|注意|可见|出现)", "", p)
        p = p.strip(" ，,。；;")
        if 2 <= len(p) <= max_len and p not in items:
            items.append(p)
        if len(items) >= max_items:
            break
    return items


def exact_sentences(text: str, max_items: int = 8, max_len: int = 48) -> list[str]:
    """Split submitted wording without adding or medically interpreting content."""
    items = [
        item.strip(" ，,。；;\n")
        for item in re.split(r"[。！？；;\n]", text)
        if item.strip(" ，,。；;\n")
    ]
    return [item[:max_len] for item in items[:max_items]]


# 库路径解析（key → master png）
LIBRARY: dict[str, Path] = {
    "fever": SYMPTOM_MASTER / "fever/master/fever-v1.png",
    "thirst": SYMPTOM_MASTER / "thirst/master/thirst-v1.png",
    "dry-mouth": SYMPTOM_MASTER / "dry-mouth/master/dry-mouth-v1.png",
    "irritable": SYMPTOM_MASTER / "irritable/master/irritable-v1.png",
    "sore-throat": SYMPTOM_MASTER / "sore-throat/master/sore-throat-v1.png",
    "cough": SYMPTOM_MASTER / "cough/master/cough-v1.png",
    "yellow-phlegm": SYMPTOM_MASTER / "yellow-phlegm/master/yellow-phlegm-v1.png",
    "yellow-nasal": SYMPTOM_MASTER / "yellow-nasal/master/yellow-nasal-v1.png",
    "red-tongue": SYMPTOM_MASTER / "red-tongue/master/red-tongue-v1.png",
    "yellow-coat": SYMPTOM_MASTER / "yellow-coat/master/yellow-coat-v1.png",
    "dry-stool": SYMPTOM_MASTER / "dry-stool/master/dry-stool-v1.png",
    "stomach-discomfort": SYMPTOM_MASTER / "stomach-discomfort/master/stomach-discomfort-v1.png",
    "mulberry-leaf": HERB_MASTER / "mulberry-leaf/master/mulberry-leaf-v1.png",
    "chrysanthemum": HERB_MASTER / "chrysanthemum/master/chrysanthemum-v1.png",
    "mint": HERB_MASTER / "mint/master/mint-v1.png",
    "ventilation": ADVICE_MASTER / "ventilation/transparent/ventilation-v1.png",
    "warm-water": ADVICE_MASTER / "warm-water/transparent/warm-water-v1.png",
    "light-diet": ADVICE_MASTER / "light-diet/master/light-diet-badge-v2.png",
    "no-smoking-alcohol": ADVICE_MASTER
    / "no-smoking-alcohol/master/no-smoking-alcohol-badge-v2.png",
    "medical-human-body": ROOT
    / "assets/component-library/mechanisms/medical-human-body-v1/medical-human-body-v1.png",
    "mechanism-full-body": ROOT
    / "assets/component-library/mechanisms/wind-heat-dynamic-v1/full-body.png",
}

# 渲染工程内文件名（症状段读 /production-symptoms/{image}）
RENDER_BASENAME = {
    "fever": "fever.png",
    "thirst": "thirst.png",
    "dry-mouth": "dry-mouth.png",
    "irritable": "irritable.png",
    "sore-throat": "sore-throat.png",
    "cough": "cough.png",
    "yellow-phlegm": "yellow-phlegm.png",
    "yellow-nasal": "yellow-nasal.png",
    "red-tongue": "red-tongue.png",
    "yellow-coat": "yellow-coat.png",
    "dry-stool": "dry-stool.png",
    "stomach-discomfort": "stomach-discomfort.png",
    "runny-nose": "runny-nose.png",
    "nasal-congestion": "nasal-congestion.png",
    "sneeze": "sneeze.png",
    "fatigue": "fatigue.png",
    "body-ache": "body-ache.png",
    "mulberry-leaf": "mulberry-leaf-v1.png",
    "chrysanthemum": "chrysanthemum-v1.png",
    "mint": "mint-v1.png",
    "ginger": "ginger-v1.png",
    "scallion-white": "scallion-white-v1.png",
    "ventilation": "ventilation-v1.png",
    "warm-water": "warm-water-v1.png",
    "light-diet": "light-diet-badge-v2.png",
    "no-smoking-alcohol": "no-smoking-alcohol-badge-v2.png",
}


def resolve_alias(label: str, lang: dict) -> str | None:
    alias = lang.get("asset_alias") or {}
    if label in alias:
        return alias[label]
    for k, v in alias.items():
        if k in label or label in k:
            return v
    return None


def gen_prompt(kind: str, label: str, key: str) -> str:
    base = (
        "Use case: scientific-educational pharmacy training. "
        "Style: friendly flat 2D Chinese pharmacy-training cartoon; medium dark-brown outline; "
        "rounded simplified anatomy; flat cel colors; restrained soft shading; "
        "pharmacy-health-cartoon-v1. Square 1:1, centered, 10% margin. "
        "No text, no logo, no watermark, no photorealism, no 3D."
    )
    specs = {
        "sneeze": "Young East-Asian adult mid-sneeze, hand near nose, soft airflow lines, mint-blue bg.",
        "runny-nose": "Side face close-up, clear runny nose droplet (not yellow thick), gentle discomfort, mint bg.",
        "nasal-congestion": "Person gently pinching bridge of nose, stuffy feeling, soft blue-grey bg.",
        "fatigue": "Young adult looking tired, low energy, soft shoulders, pale mint bg.",
        "body-ache": "Person holding shoulder and lower back with mild ache marks, soft coral accents.",
        "ginger": "Clean botanical illustration of fresh ginger root and slice, white/transparent bg.",
        "scallion-white": "Clean botanical of scallion white stems (葱白), flat botanical, white/transparent bg.",
    }
    detail = specs.get(key, f"Illustration for concept: {label} ({key}).")
    return f"{base} Subject: {detail}"


def plan_slot(
    *,
    slot_id: str,
    segment: str,
    label: str,
    key: str | None,
    lang: dict,
    out_assets: Path,
    category: str,
) -> dict[str, Any]:
    """category: symptoms | herbs | advice | mechanism"""
    slot: dict[str, Any] = {
        "slot_id": slot_id,
        "segment": segment,
        "label": label,
        "asset_key": key,
        "status": "gap",
        "source": None,
        "theme_relpath": None,
        "render_basename": RENDER_BASENAME.get(key or "", f"{key or 'unknown'}.png"),
        "gen_prompt": None,
        "review_required": True,
    }
    if not key:
        slot["status"] = "gap"
        slot["gen_prompt"] = gen_prompt(category, label, "unknown")
        return slot

    lib = LIBRARY.get(key)
    dest_dir = out_assets / category
    dest_dir.mkdir(parents=True, exist_ok=True)
    basename = slot["render_basename"]
    dest = dest_dir / basename

    if lib and lib.is_file():
        shutil.copy2(lib, dest)
        slot["status"] = "library_matched"
        slot["source"] = str(lib.relative_to(ROOT))
        slot["theme_relpath"] = str(dest.relative_to(out_assets.parent))
    else:
        # theme-local already?
        if dest.is_file():
            slot["status"] = "theme_local"
            slot["source"] = display_source(dest)
            slot["theme_relpath"] = str(dest.relative_to(out_assets.parent))
        else:
            slot["status"] = "needs_generation"
            slot["gen_prompt"] = gen_prompt(category, label, key)
            slot["theme_relpath"] = str((Path("assets") / category / basename).as_posix())
    return slot


def map_sections(sections: list[dict], disease: str) -> dict[str, dict]:
    """Use the exact same segment mapper as the formal renderer."""
    return map_sections_to_segments(sections, disease)


def build_screen_and_plan(
    disease: str, mapped: dict[str, dict], lang: dict, theme_dir: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    assets_root = theme_dir / "assets"
    slots: list[dict[str, Any]] = []

    content_gaps: list[dict[str, str]] = []

    def add_gap(field: str, reason: str) -> None:
        if not any(item["field"] == field for item in content_gaps):
            content_gaps.append({"field": field, "reason": reason})

    required_segments = {
        "intro": "开场",
        "character": "基础认知",
        "mechanism": "病因机理",
        "symptoms": "典型症状",
        "treatment": "调理建议",
        "medication": "用药与生活建议",
        "summary": "总结",
    }
    for sid, label in required_segments.items():
        if sid not in mapped:
            add_gap(f"segment.{sid}", f"健康正式成片需要 7 段，业务审核稿缺少“{label}”")

    def narration(sid: str) -> str:
        return str((mapped.get(sid) or {}).get("narration") or "").strip()

    def title(sid: str, fallback: str) -> str:
        return str((mapped.get(sid) or {}).get("title") or fallback).strip()

    char_nar = narration("character")
    sym_nar = narration("symptoms")
    treat_nar = narration("treatment")
    med_nar = narration("medication")
    mech_nar = narration("mechanism")
    summary_nar = narration("summary")

    chips = extract_list_items(char_nar, max_items=6, max_len=10)
    if "character" in mapped and not chips:
        add_gap("character_cards", "基础认知段未提供可直接上屏的审核原文要点")

    max_groups = int(lang.get("defaults", {}).get("max_symptom_groups") or 2)
    max_groups = max(1, min(3, max_groups))
    sym_items = extract_list_items(sym_nar, max_items=8, max_len=14)
    if "symptoms" in mapped and not sym_items:
        add_gap("symptom_groups", "典型症状段未提供可直接上屏的审核原文要点")

    groups: list[dict[str, Any]] = []
    chunk = max(1, (len(sym_items) + max_groups - 1) // max_groups) if sym_items else 1
    for gi in range(0, min(max_groups, (len(sym_items) + chunk - 1) // chunk)):
        part = sym_items[gi * chunk : (gi + 1) * chunk][:4]
        if not part:
            continue
        items = []
        for lab in part:
            key = resolve_alias(lab, lang) or f"custom-{slugify(lab)}"
            slot = plan_slot(
                slot_id=f"symptoms.{gi}.{lab}",
                segment="symptoms",
                label=lab,
                key=key,
                lang=lang,
                out_assets=assets_root,
                category="symptoms",
            )
            slots.append(slot)
            items.append(
                {
                    "label": lab,
                    "image": slot["render_basename"],
                    "asset_key": key,
                    "slot_id": slot["slot_id"],
                    "visual_status": slot["status"],
                }
            )
        # summary：组内要点合并成两行，避免只显示第一条
        if len(part) >= 4:
            sum_lines = ["、".join(part[:2]), "、".join(part[2:4])]
        elif len(part) == 3:
            sum_lines = ["、".join(part[:2]), part[2]]
        elif len(part) == 2:
            sum_lines = [part[0], part[1]]
        else:
            sum_lines = [part[0], ""]
        groups.append(
            {
                "number": ["①", "②", "③"][len(groups)],
                "title": "审核稿表现",
                "summaryLines": sum_lines,
                "items": items,
            }
        )

    # 草本名称与说明只能来自审核原文；不得从名称补功效或用量。
    herb_names = re.findall(
        r"(桑叶|菊花|薄荷|生姜|葱白|金银花|连翘|板蓝根|甘草|陈皮|红糖|柠檬|蜂蜜)",
        treat_nar,
    )
    # unique preserve order
    seen = set()
    herb_names = [h for h in herb_names if not (h in seen or seen.add(h))][:3]
    herbs = []
    treatment_sentences = exact_sentences(treat_nar, max_items=8, max_len=40)
    for name in herb_names:
        key = resolve_alias(name, lang) or f"custom-{slugify(name)}"
        slot = plan_slot(
            slot_id=f"treatment.herb.{name}",
            segment="treatment",
            label=name,
            key=key,
            lang=lang,
            out_assets=assets_root,
            category="herbs",
        )
        slots.append(slot)
        source_line = next((line for line in treatment_sentences if name in line), name)
        herbs.append(
            {
                "name": name,
                "image": slot["render_basename"],
                "lines": [source_line[:32], ""],
                "asset_key": key,
                "slot_id": slot["slot_id"],
                "visual_status": slot["status"],
            }
        )

    # 生活/用药建议逐条保留审核原文，不自动补通风、饮水等建议。
    advice_lines = extract_list_items(med_nar, max_items=6, max_len=28)
    advice_items = []
    for body in advice_lines:
        key = resolve_alias(body, lang) or f"custom-{slugify(body)}"
        slot = plan_slot(
            slot_id=f"medication.advice.{key}",
            segment="medication",
            label=body,
            key=key,
            lang=lang,
            out_assets=assets_root,
            category="advice",
        )
        slots.append(slot)
        advice_items.append(
            {
                "title": f"{len(advice_items)+1}. 审核稿要点",
                "body": body,
                "image": slot["render_basename"],
                "transparent": True,
                "slot_id": slot["slot_id"],
                "visual_status": slot["status"],
            }
        )
    if "medication" in mapped and not advice_items:
        add_gap("advice_items", "用药与生活建议段未提供可直接上屏的审核原文要点")

    # 机理画面必须按本主题审核原文重新生成/过目，不沿用风热动态层。
    if mech_nar:
        key = f"custom-{slugify(title('mechanism', '机理'))}"
        mechanism_path = assets_root / "mechanism" / "full-body.png"
        slot = {
            "slot_id": "mechanism.theme_visual",
            "segment": "mechanism",
            "label": title("mechanism", "机理审核稿画面"),
            "asset_key": key,
            "status": "theme_local" if mechanism_path.is_file() else "needs_generation",
            "source": (
                display_source(mechanism_path) if mechanism_path.is_file() else None
            ),
            "theme_relpath": "assets/mechanism/full-body.png",
            "render_basename": "full-body.png",
            "gen_prompt": (
                None
                if mechanism_path.is_file()
                else gen_prompt("mechanism", title("mechanism", "机理审核稿画面"), key)
            ),
            "review_required": True,
        }
        slots.append(slot)

    equation = re.search(
        r"([^+＋=＝→。；]{1,24})[+＋]([^=＝→。；]{1,24})[=＝→]([^。；]{1,24})",
        mech_nar,
    )
    eq = tuple(part.strip() for part in equation.groups()) if equation else ("", "", "")
    if "mechanism" in mapped and not equation:
        add_gap("mechanism_equation", "机理段未提供可直接上屏的“A + B = C”审核文案")

    principle = re.search(
        r"(?:核心(?:原则|思路)?|调理原则)(?:是|为)?[：:]?\s*([^，,。！？；;\n]{2,20})",
        treat_nar,
    )
    core = principle.group(1).strip() if principle else ""
    if "treatment" in mapped and not core:
        add_gap("treatment_principle", "调理段未明确提供已审核的核心原则")
    if "treatment" in mapped and len(treatment_sentences) < 2:
        add_gap("treatment_lines", "调理画面需要至少 2 条可直接上屏的审核原文")
    if "treatment" in mapped and not herbs:
        add_gap("treatment_visuals", "当前金样调理段需要审核稿明确草本/食疗对象及对应画面")

    medication_names = [
        item
        for item in advice_lines
        if re.search(r"(?:颗粒|胶囊|口服液|片|丸|滴剂|糖浆|药)", item)
    ][:2]
    medication_cards = [
        {
            "name": item,
            "image": "",
            "body": item,
            "badge": "审核稿",
        }
        for item in advice_lines[:2]
    ]
    if "medication" in mapped and len(medication_cards) < 2:
        add_gap("medication_cards", "用药画面需要至少 2 条可直接上屏的审核原文")

    summary_lines = exact_sentences(summary_nar, max_items=4, max_len=40)
    summary_items = [
        {"title": f"要点 {index + 1}", "body": item}
        for index, item in enumerate(summary_lines)
    ]
    if "summary" in mapped and not summary_items:
        add_gap("summary_items", "总结段未提供可直接上屏的审核原文")
    if "summary" in mapped and not advice_items:
        add_gap("summary_advice_items", "总结版式所需建议要点尚未由审核稿提供")

    recipe_names = " · ".join(herb_names)
    screen = {
        "disease_name": disease,
        "eyebrow": "健康知识培训",
        "tagline": "内部培训",
        "chapter_intro": title("intro", "开场"),
        "chapter_character": title("character", "基础认知"),
        "chapter_mechanism": title("mechanism", "病因机理"),
        "chapter_symptoms": title("symptoms", "典型症状"),
        "chapter_treatment": title("treatment", "调理建议"),
        "chapter_medication": title("medication", "用药与生活建议"),
        "chapter_summary": title("summary", "总结"),
        "character_cards": chips,
        "mechanism_title": title("mechanism", "机理审核稿"),
        "equation_left": eq[0],
        "equation_right": eq[1],
        "equation_result": eq[2],
        "symptoms_title": title("symptoms", "典型表现"),
        "core_heading": "审核稿要点",
        "core_treatment": core,
        "core_body_1": chips[0] if chips else "",
        "core_body_2": chips[1] if len(chips) > 1 else "",
        "core_body_3": chips[2] if len(chips) > 2 else "",
        "treatment_principle": core,
        "treatment_line_1": treatment_sentences[0] if treatment_sentences else "",
        "treatment_line_2": treatment_sentences[1] if len(treatment_sentences) > 1 else "",
        "recipe_text": recipe_names,
        "recipe_effect": treatment_sentences[-1] if herbs and treatment_sentences else "",
        "herbs": herbs,
        "symptom_groups": groups,
        "medication_names": medication_names,
        "medication_cards": medication_cards,
        "advice_items": advice_items,
        "advice_title": title("medication", "审核稿建议"),
        "medication_section_title": title("medication", "审核稿要点"),
        "advice_section_title": title("medication", "审核稿建议"),
        "summary_items": summary_items,
        "summary_title": title("summary", "总结"),
        "slogan": f"内部培训 · {disease}",
        "theme_package": True,
        "language_id": lang.get("id"),
        "source_policy": "business-sections-only",
        "content_gaps": content_gaps,
    }

    return screen, slots


def write_script_md(path: Path, disease: str, mapped: dict[str, dict]) -> None:
    lines = [
        f"# {disease} · 疾病科普培训脚本（主题制作包）",
        "",
        "> 旁白须为审核稿口径；本包文案供制作与过目，**医学结论以公司药师/合规终稿为准**。",
        "",
        f"- 主题：{disease}",
        f"- 语言：health-segment-language-v1",
        f"- 生成时间：{datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    order = [
        "intro",
        "character",
        "mechanism",
        "symptoms",
        "treatment",
        "medication",
        "summary",
    ]
    labels = {
        "intro": "开场",
        "character": "基础认知",
        "mechanism": "病因机理",
        "symptoms": "典型症状",
        "treatment": "调理建议",
        "medication": "用药与生活建议",
        "summary": "总结",
    }
    for sid in order:
        sec = mapped.get(sid)
        if not sec:
            lines += [f"## {labels[sid]}（本主题省略）", ""]
            continue
        lines += [
            f"## {labels[sid]}",
            "",
            f"**章节标题（业务）**：{sec.get('title')}",
            "",
            "**旁白**：",
            "",
            sec.get("narration") or "（空）",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_review_html(
    path: Path,
    disease: str,
    slots: list[dict],
    theme_dir: Path,
    payload_sha256: str,
    content_gaps: list[dict[str, str]],
) -> None:
    cards = []
    for i, s in enumerate(slots, 1):
        rel = s.get("theme_relpath")
        img_html = ""
        if rel:
            img_path = theme_dir / rel
            if img_path.is_file():
                # relative to review.html in theme root
                img_html = f'<img src="{rel}" alt="{s.get("label")}" style="max-width:220px;max-height:220px;background:#1a2744;border-radius:12px;padding:8px"/>'
            else:
                img_html = f'<div class="miss">待生成：{s.get("render_basename")}</div>'
        else:
            img_html = '<div class="miss">无预览</div>'
        st = s.get("status")
        color = {
            "library_matched": "#3d9",
            "theme_local": "#3af",
            "needs_generation": "#e90",
            "gap": "#e45",
        }.get(st, "#999")
        prompt = s.get("gen_prompt") or ""
        cards.append(
            f"""
<div class="card">
  <div class="idx">#{i} · {s.get('segment')} · <span style="color:{color}">{st}</span></div>
  <div class="label"><b>{s.get('label')}</b> <code>{s.get('slot_id')}</code></div>
  {img_html}
  <div class="meta">asset_key={s.get('asset_key')} · render={s.get('render_basename')}</div>
  <div class="src">source: {s.get('source') or '—'}</div>
  {"<pre class='prompt'>"+prompt+"</pre>" if prompt else ""}
</div>"""
        )
    gaps_html = "".join(
        f"<li><code>{gap.get('field')}</code>：{gap.get('reason')}</li>"
        for gap in content_gaps
    ) or "<li>无</li>"
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>{disease} · 画面全量过目</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0f1419;color:#e8eef7;margin:0;padding:24px}}
h1{{font-size:22px}}
.note{{background:#1c2430;border-left:4px solid #f5a;padding:12px 16px;margin:16px 0;border-radius:8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.card{{background:#1a222d;border-radius:14px;padding:14px;border:1px solid #2a3544}}
.idx{{font-size:12px;color:#9ab}}
.label{{margin:8px 0}}
.miss{{width:220px;height:140px;display:flex;align-items:center;justify-content:center;background:#2a2030;border-radius:12px;color:#f8a}}
.meta,.src{{font-size:11px;color:#8a9;margin-top:6px;word-break:break-all}}
pre.prompt{{font-size:10px;white-space:pre-wrap;background:#0d1218;padding:8px;border-radius:8px;color:#cde}}
code{{font-size:11px;color:#8cf}}
</style>
</head>
<body>
<h1>{disease} · 疾病科普主题 · 画面全量过目</h1>
<div class="note">
  <b>门闸：全部过目。</b>请逐张核对语义与画风。确认后在本目录写 <code>approval.json</code>
  （可用下方模板），再运行带 <code>--theme-package</code> 的出片命令。<b>未批准禁止渲染正式成片。</b>
</div>
<div class="note"><b>当前审批载荷 SHA-256：</b><code>{payload_sha256}</code></div>
<h2>内容缺口</h2><ul>{gaps_html}</ul>
<p>槽位共 <b>{len(slots)}</b> 个 · 语言 health-segment-language-v1 · 复用：背景壳+药师+voice+段 recipe；主题换脚本与图槽。</p>
<div class="grid">
{''.join(cards)}
</div>
<h2>approval.json 模板</h2>
<pre class="prompt">{{
  "theme": "{disease}",
  "language_id": "health-segment-language-v1",
  "visuals_approved": true,
  "approved_by": "你的名字",
  "approved_at": "ISO-8601 时间",
  "approved_payload_sha256": "{payload_sha256}",
  "notes": "全部画面已过目"
}}</pre>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", required=True, help="病名，如 感冒")
    ap.add_argument("--sections-json", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    lang = load_json(LANG_PATH)
    raw = load_json(args.sections_json)
    if isinstance(raw, list):
        sections = raw
    else:
        sections = raw.get("sections") or []
    disease = args.theme
    out: Path = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)

    mapped = map_sections(sections, disease)
    screen, slots = build_screen_and_plan(disease, mapped, lang, out)

    write_json(out / "sections.json", {"theme": disease, "sections": sections})
    write_json(out / "segment-map.json", {"included": {k: v.get("title") for k, v in mapped.items()}})
    write_json(out / "screen.json", screen)
    write_json(out / "visual-plan.json", {"slots": slots, "count": len(slots)})
    write_script_md(out / "script.md", disease, mapped)

    # coverage summary
    cov = {
        "library_matched": sum(1 for s in slots if s["status"] == "library_matched"),
        "theme_local": sum(1 for s in slots if s["status"] == "theme_local"),
        "needs_generation": sum(1 for s in slots if s["status"] == "needs_generation"),
        "gap": sum(1 for s in slots if s["status"] == "gap"),
        "total": len(slots),
    }
    write_json(out / "visual-coverage.json", cov)
    payload_sha256 = theme_package_payload_sha256(out)

    # prompts file for generators
    prompts = [
        {
            "slot_id": s["slot_id"],
            "label": s["label"],
            "asset_key": s["asset_key"],
            "out_basename": s["render_basename"],
            "prompt": s["gen_prompt"],
        }
        for s in slots
        if s.get("gen_prompt")
    ]
    write_json(out / "image-gen-prompts.json", prompts)

    write_json(
        out / "package.json",
        {
            "theme": disease,
            "slug": slugify(disease),
            "language_id": lang["id"],
            "style_pack_id": lang["source_gold"]["style_pack_id"],
            "voice_pack_id": lang["source_gold"]["voice_pack_id"],
            "template_id": lang["source_gold"]["template_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approval_gate": lang["approval_gate"],
            "approval_target_sha256": payload_sha256,
            "status": "awaiting_visual_review",
            "visual_coverage": cov,
            "paths": {
                "script": "script.md",
                "screen": "screen.json",
                "visual_plan": "visual-plan.json",
                "review": "review.html",
                "approval": "approval.json",
            },
        },
    )

    # approval stub (not approved)
    write_json(
        out / "approval.json",
        {
            "theme": disease,
            "language_id": lang["id"],
            "visuals_approved": False,
            "approved_by": None,
            "approved_at": None,
            "approval_target_sha256": payload_sha256,
            "approved_payload_sha256": None,
            "notes": "默认未批准：请打开 review.html 全部过目后改为 true",
        },
    )

    write_review_html(
        out / "review.html",
        disease,
        slots,
        out,
        payload_sha256,
        screen.get("content_gaps") or [],
    )

    # copy style brief pointer
    brief_src = ROOT / lang["style_brief"]
    if brief_src.is_file():
        shutil.copy2(brief_src, out / "style-brief.md")

    print(
        json.dumps(
            {
                "ok": True,
                "out_dir": str(out),
                "review": str(out / "review.html"),
                "coverage": cov,
                "approval_target_sha256": payload_sha256,
                "needs_generation": [p["label"] for p in prompts],
                "next": "打开 review.html 全部过目 → 补齐 needs_generation 图 → 改 approval.json → 再 full 渲染",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
