#!/usr/bin/env python3
"""构件化课件生成器（M4）

流水线：
  script.structured.json
    → scene-plan.json（页型选择留痕：reuse / cross_template / new + 理由）
    → content-model.json（引擎输入）
    → layer-manifest.json
    → courseware-pptx-v1 export → PPTX
    → QA 图（soffice → pdftoppm）

硬校验：
  - hidden 条目排除
  - empty_cards = forbidden
  - 文案只取自 script（生成器不造功效/剂量）
  - 缺图 → 引擎 labeled 占位槽

用法：
  python3 scripts/generate_courseware.py \\
    --script production-library/validation/courseware/fuler-maikenli-lycopene-v1/script.structured.json \\
    --style production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json \\
    --out-dir production-library/validation/courseware/fuler-maikenli-lycopene-v1/m4-generator-out
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "production-library/page-types/product-training/registry.json"
DEFAULT_RECIPES = ROOT / "production-library/page-types/product-training/recipes"
DEFAULT_STYLE = ROOT / "production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json"
DEFAULT_ENGINE = ROOT / "production-library/engines/courseware-pptx-v1/export.mjs"
DEFAULT_MANIFEST = ROOT / "production-library/engines/courseware-pptx-v1/build_layer_manifest.py"
DEFAULT_ASSETS = (
    ROOT
    / "production-library/validation/courseware/product-courseware-4-faithful-replica-v1"
)

# 引擎 chrome / 占位槽允许的非 script 文案（不进「扩写」判定）
ENGINE_CHROME_ALLOW = {
    "待业务授权",
    "可替换",
    "图片占位",
    "待业务替换",
    "TIME",
    "Big",
    "Title",
    "敲重点",
    "好物推荐",  # cover badge 槽位 alt；有图时不进文本
    # precautions 2×2 插画 chrome 标签（与 verify_text_provenance CHROME_ALLOWLIST 对齐）
    "不代替药物",
    "禁忌人群",
    "随餐服用",
    "就医咨询",
}

# 注意事项四插画（component-library 入库后文件名；引擎 resolve 为 assets/generated/<file>）
PRECAUTION_ILLUSTRATIONS = [
    {"file": "pre-not-medicine.png", "label": "不代替药物"},
    {"file": "pre-special-pop.png", "label": "禁忌人群"},
    {"file": "pre-with-meal.png", "label": "随餐服用"},
    {"file": "pre-consult.png", "label": "就医咨询"},
]

PRECAUTIONS_LIBRARY_DIR = (
    ROOT / "assets/component-library/product-training-precautions/transparent"
)


class GeneratorError(Exception):
    """Hard validation / generation failure."""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def chunk(items: list, n: int) -> list[list]:
    if n <= 0:
        return [items] if items else []
    return [items[i : i + n] for i in range(0, len(items), n)]


def visible_items(items: list | None) -> list:
    """Drop hidden rows; hard rule for brand_boast / closed claims."""
    out = []
    for it in items or []:
        if isinstance(it, dict) and it.get("hidden"):
            continue
        out.append(it)
    return out


def collect_script_text_atoms(script: dict) -> list[str]:
    """All user-facing copy atoms from script (for provenance / no-invention checks)."""
    atoms: list[str] = []
    meta = script.get("meta") or {}
    for k in ("display_name", "organization", "tagline"):
        if meta.get(k):
            atoms.append(str(meta[k]))

    hook = script.get("hook") or {}
    if hook.get("title"):
        atoms.append(str(hook["title"]))
    for p in hook.get("paragraphs") or []:
        atoms.append(str(p))
    for s in hook.get("symptoms") or []:
        atoms.append(str(s if not isinstance(s, dict) else s.get("label") or s.get("text") or ""))
    for st in hook.get("stats") or []:
        if isinstance(st, dict):
            for k in ("number", "unit", "note", "source"):
                if st.get(k):
                    atoms.append(str(st[k]))
    if hook.get("source"):
        atoms.append(str(hook["source"]))

    for key in ("benefits", "features"):
        block = script.get(key) or {}
        if block.get("title"):
            atoms.append(str(block["title"]))
        for it in visible_items(block.get("items")):
            if isinstance(it, dict):
                if it.get("title"):
                    atoms.append(str(it["title"]))
                if it.get("body"):
                    atoms.append(str(it["body"]))
            else:
                atoms.append(str(it))

    aud = script.get("audience") or {}
    if aud.get("title"):
        atoms.append(str(aud["title"]))
    for it in aud.get("items") or []:
        atoms.append(str(it if not isinstance(it, dict) else it.get("label") or it.get("text") or ""))

    combo = script.get("combination") or {}
    if combo.get("title"):
        atoms.append(str(combo["title"]))
    for r in combo.get("rows") or []:
        if isinstance(r, dict):
            for k in ("problem", "scenario", "partner", "talk_track"):
                if r.get(k):
                    atoms.append(str(r[k]))

    summary = script.get("summary") or {}
    if summary.get("title"):
        atoms.append(str(summary["title"]))
    for r in summary.get("rows") or []:
        if isinstance(r, dict):
            for k in ("label", "value", "body"):
                if r.get(k):
                    atoms.append(str(r[k]))

    prec = script.get("precautions") or {}
    if prec.get("title"):
        atoms.append(str(prec["title"]))
    for it in prec.get("items") or []:
        atoms.append(str(it if not isinstance(it, dict) else it.get("text") or ""))

    return [a.strip() for a in atoms if a and str(a).strip()]


def assert_text_from_script(text: str | None, script_atoms: list[str], where: str) -> None:
    """Hard rule: generated content-model copy must be taken from script (substring)."""
    if text is None:
        return
    t = str(text).strip()
    if not t:
        return
    # short chrome / punctuation-only ok
    if t in ENGINE_CHROME_ALLOW or len(t) <= 1:
        return
    # allow pure numbering prefixes used for section labels
    if re.fullmatch(r"[一二三四五六七八九十\d]+[、.．].*", t):
        # body after prefix still must match
        body = re.sub(r"^[一二三四五六七八九十\d]+[、.．]\s*", "", t)
        if body:
            assert_text_from_script(body, script_atoms, where)
        return
    for atom in script_atoms:
        if t == atom or t in atom or atom in t:
            return
    # section titles often = item title with chapter prefix
    raise GeneratorError(f"copy not from script at {where}: {t[:80]!r}")


def extract_hook_pain(hook: dict) -> dict | None:
    """Build hook_pain_data slots from structured fields or paragraph mining."""
    symptoms = hook.get("symptoms")
    stats = hook.get("stats")
    source = hook.get("source")
    paragraphs = hook.get("paragraphs") or []
    joined = "\n".join(str(p) for p in paragraphs)

    if not symptoms:
        # common symptom phrases in 前列腺 / 慢病 hook copy
        candidates = [
            "尿频",
            "尿急",
            "会阴坠胀",
            "排尿灼痛",
            "易疲劳",
            "记忆力下降",
            "前列腺不适",
            "皮肤暗沉",
        ]
        found = [c for c in candidates if c in joined]
        symptoms = found[:4] if found else []

    if not stats:
        stats = []
        # e.g. 32.9% / 40%
        for m in re.finditer(
            r"(?:最高可达|占比高达|约|可达)?\s*(\d+(?:\.\d+)?%?)\s*(人|%|％)?",
            joined,
        ):
            num = m.group(1)
            unit = m.group(2) or ("" if "%" in num or "％" in num else "")
            # context window for note
            start = max(0, m.start() - 24)
            end = min(len(joined), m.end() + 24)
            note = re.sub(r"\s+", "", joined[start:end])[:36]
            stats.append({"number": num, "unit": unit or "", "note": note, "role": f"stat{len(stats)+1}"})
        # prefer first two meaningful percentages
        pct_stats = [s for s in stats if "%" in s["number"] or s.get("unit") in ("%", "％", "")]
        if len(pct_stats) >= 2:
            stats = pct_stats[:2]
            # refine notes as exact script substrings when known patterns present
            if "32.9" in joined:
                note1 = "我国前列腺炎发病率最高可达"
                if note1 not in joined:
                    # include optional 在 prefix
                    note1 = "在我国前列腺炎发病率最高可达" if "在我国前列腺炎发病率最高可达" in joined else "前列腺炎发病率最高可达"
                stats[0] = {
                    "number": "32.9%",
                    "unit": "",
                    "note": note1,
                    "role": "stat1",
                }
            if "40%" in joined or "40％" in joined:
                note2 = "25–34岁的群体占比高达"
                if note2 not in joined:
                    note2 = "25-34岁的群体占比高达" if "25-34岁的群体占比高达" in joined else "群体占比高达"
                stats[1] = {
                    "number": "40%",
                    "unit": "",
                    "note": note2,
                    "role": "stat2",
                }
        elif not stats:
            stats = []

    if not source:
        m = re.search(r"数据来自(《[^》]+》)", joined)
        if m:
            source = f"数据来自{m.group(1)}"
        else:
            m2 = re.search(r"《[^》]+》", joined)
            if m2:
                source = m2.group(0)

    # need at least stats or symptoms to choose this page type
    if not stats and not symptoms:
        return None

    # ensure symptoms non-empty for layout density
    if not symptoms and stats:
        symptoms = ["关注前列腺健康", "生活质量下降"]

    # symptoms must come from script — only use mined ones that appear in paragraphs
    symptoms = [s for s in symptoms if s in joined or s in (hook.get("symptoms") or [])]
    if not symptoms and stats:
        # fallback chips from first paragraph keywords only if present
        symptoms = []

    return {
        "chapter": hook.get("title") or "导语引入",
        "section": "常见信号与数据",
        "symptoms": symptoms,
        "stats": stats,
        "source": source or "",
    }


def guess_audience_icon(label: str) -> str:
    t = label or ""
    if "前列腺" in t:
        return "prostate"
    if "备孕" in t or "男士" in t or "女士" in t:
        return "couple"
    if "爱美" in t or "美白" in t or "皮肤" in t:
        return "audience_beauty"
    if "虚弱" in t or "体虚" in t or "免疫" in t:
        return "audience_weak"
    return "prostate"


def benefit_chain_assets(title: str, index: int) -> list[str]:
    """Align with cw4 gold image chains (S04/S05/S06).

    抗氧化 must be tomato → o2 → skincare_woman（美容），不可停在 O2。
    """
    t = title or ""
    if "前列腺" in t or "精子" in t:
        return ["tomato", "arrow", "prostate"]
    if "抗氧化" in t or "衰老" in t:
        return ["tomato", "arrow", "o2", "arrow", "skincare_woman"]
    if "免疫" in t:
        return ["tomato", "arrow", "nk_cell", "arrow", "flex_arm"]
    defaults = [
        ["tomato", "arrow", "prostate"],
        ["tomato", "arrow", "o2", "arrow", "skincare_woman"],
        ["tomato", "arrow", "nk_cell", "arrow", "flex_arm"],
    ]
    return defaults[min(index, len(defaults) - 1)]


# 大纲结构标签，不宜作正式培训页标题
HOOK_PROCESS_TITLES = {"导语引入", "开场", "引入", "导语", "引言"}


def formal_hook_chapter(hook: dict) -> str:
    """正式页标题：拒绝「导语引入」类过程标签。"""
    t = str(hook.get("title") or "").strip()
    if t and t not in HOOK_PROCESS_TITLES:
        return t
    for k in ("page_title", "chapter", "display_title"):
        v = str(hook.get(k) or "").strip()
        if v and v not in HOOK_PROCESS_TITLES:
            return v
    return t or "导语引入"  # 仍会触发脚本侧修正；生成器不另造功效文案


def combo_problem_label(row: dict) -> str:
    """问题场景短标题：优先 problem；否则从 scenario 的（…）抽取。"""
    if row.get("problem"):
        return str(row["problem"]).strip()
    scen = str(row.get("scenario") or row.get("scene") or "").strip()
    m = re.search(r"[（(]([^）)]+)[）)]", scen)
    if m:
        return m.group(1).strip()
    # 去掉「顾客买」前缀后的药品段仍过长时，用 partner
    if scen.startswith("顾客买"):
        rest = scen[3:].strip()
        if row.get("partner") and str(row["partner"]) in rest:
            return str(row["partner"])
    return scen


def combo_icon_file(row: dict) -> str:
    """组合图槽：按场景/搭配关键词映射主题插画（业务可替换）。"""
    if row.get("icon"):
        return str(row["icon"])
    blob = f"{row.get('problem') or ''}{row.get('scenario') or ''}{row.get('partner') or ''}"
    if any(k in blob for k in ("美白", "胶原", "爱美", "皮肤")):
        return "symptom-skin.png"
    if any(k in blob for k in ("前列康", "普乐安", "中成药")):
        return "combo-daily.png"
    if any(k in blob for k in ("坦索", "非那", "排尿", "前列腺")):
        return "symptom-prostate.png"
    return "combo-daily.png"


def feature_scene_type(title: str, index: int) -> str:
    t = title or ""
    if "产地" in t:
        return "feature_origin"
    if "原料" in t:
        return "feature_material"
    if "含量" in t or "粒" in t:
        return "feature_content"
    order = ["feature_origin", "feature_material", "feature_content"]
    return order[min(index, len(order) - 1)]


def expand_scene_plan(script: dict, registry: dict) -> dict:
    """Content-driven page expansion with selection provenance."""
    reg = {p["id"]: p for p in registry.get("page_types", [])}
    pages: list[dict] = []
    meta = script.get("meta") or {}
    script_atoms = collect_script_text_atoms(script)

    def add(
        page_type: str,
        scene_type: str,
        slots: dict,
        *,
        mode: str,
        reason: str,
        source_section: str,
    ) -> None:
        if page_type not in reg:
            raise GeneratorError(f"unregistered page_type: {page_type}")
        # empty_cards hard check on list-like slots
        for key in ("items", "rows", "paragraphs", "symptoms", "stats"):
            if key in slots and isinstance(slots[key], list) and len(slots[key]) == 0:
                raise GeneratorError(f"empty_cards forbidden: {page_type}.{key}")
        # copy provenance: all string leaves in slots must come from script (except chrome keys)
        def walk(obj: Any, path: str) -> None:
            if isinstance(obj, str):
                if path.endswith(".role") or path.endswith(".icon") or path.endswith(".file"):
                    return
                if path.endswith(".chain") or "chain[" in path:
                    return
                assert_text_from_script(obj, script_atoms, f"{page_type}:{path}")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    walk(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(v, f"{path}[{i}]")

        walk(slots, "")
        idx = len(pages) + 1
        pages.append(
            {
                "i": idx,
                "id": f"P{idx:02d}_{page_type}",
                "page_type": page_type,
                "scene_type": scene_type,
                "selection": {"mode": mode, "reason": reason},
                "source_section": source_section,
                "slots": slots,
            }
        )

    # 1) cover
    add(
        "courseware_cover",
        "cover",
        {
            "title_pill": meta.get("display_name") or script.get("title") or "",
            "organization": meta.get("organization") or "",
            "tagline": meta.get("tagline") or "",
            "benefits": [
                it.get("title") if isinstance(it, dict) else str(it)
                for it in visible_items((script.get("benefits") or {}).get("items"))
            ][:3],
        },
        mode="reuse",
        reason="registry courseware_cover settled; meta fields",
        source_section="meta",
    )

    # 2) hook → prefer hook_pain_data (settled M3), else skip generic time_list dump
    hook = script.get("hook") or {}
    pain = extract_hook_pain(hook) if hook else None
    hook_chapter = formal_hook_chapter(hook)
    if pain and (pain.get("stats") or pain.get("symptoms")):
        # section 仅用 script 已有正式标题，拒绝「导语引入」过程标签
        pain_slots = {
            "chapter": hook_chapter,
            "symptoms": pain.get("symptoms") or [],
            "stats": pain.get("stats") or [],
        }
        if pain.get("source"):
            pain_slots["source"] = pain["source"]
        add(
            "hook_pain_data",
            "hook_pain_data",
            pain_slots,
            mode="reuse",
            reason="hook 含数据/症状结构 → settled hook_pain_data；章标用正式培训标题",
            source_section="hook",
        )
    elif hook.get("paragraphs"):
        # Fallback: one time_list with truncated list lines from paragraphs (still script-only)
        paras = [str(p) for p in hook["paragraphs"] if str(p).strip()]
        if not paras:
            raise GeneratorError("hook.paragraphs empty after strip")
        # time_list expects short list; use first lines shortened but still substrings
        list_lines = []
        for i, p in enumerate(paras[:3], 1):
            snippet = p if len(p) <= 28 else p[:28]
            # ensure substring of original
            assert snippet in p or snippet == p
            list_lines.append(f"{i}.{snippet}")
        add(
            "hook_intro",
            "time_list",
            {
                "card_title": hook_chapter,
                "list": list_lines,
                "paragraphs": paras,
            },
            mode="cross_template",
            reason="hook 无结构化 stats → time_list 变体承载导语要点（script 截断子串）",
            source_section="hook",
        )

    # 3) benefits → one benefit_chain page per item (gold density)
    benefits = script.get("benefits") or {}
    b_items = visible_items(benefits.get("items"))
    chapter_b = benefits.get("title") or "核心功效"
    max_b = reg["benefit_cards"].get("max_per_page", 3)
    for group_i, group in enumerate(chunk(b_items, 1)):  # one visual chain page per benefit
        if not group:
            continue
        if group_i >= 20:
            break
        it = group[0]
        title = it.get("title") if isinstance(it, dict) else str(it)
        body = (it.get("body") if isinstance(it, dict) else "") or ""
        add(
            "benefit_cards",
            "benefit_chain",
            {
                "chapter": chapter_b,
                "section": f"{group_i + 1}、{title}",
                "items": [it],
                "chain": benefit_chain_assets(title, group_i),
                "body": body,
                "subtitles": [{"text": body}] if body else [],
            },
            mode="reuse",
            reason=f"benefit item → benefit_chain image_chain（max_per_page={max_b}，本生成器 1 条/页保密度）",
            source_section="benefits",
        )

    # 4) features → origin/material/content variants by title
    features = script.get("features") or {}
    f_items = visible_items(features.get("items"))
    chapter_f = features.get("title") or "产品特点"
    for i, it in enumerate(f_items):
        title = it.get("title") if isinstance(it, dict) else str(it)
        body = (it.get("body") if isinstance(it, dict) else "") or ""
        st = feature_scene_type(title, i)
        slots: dict[str, Any] = {
            "chapter": chapter_f,
            "section": f"{i + 1}、{title}",
            "items": [it],
            "body": body,
        }
        if body:
            slots["subtitles"] = [{"text": body}]
        # 产地页正文走 noteBar（subtitles/body），勿用 map_caption 硬截断造成「半截文案」
        add(
            "feature_cards",
            st,
            slots,
            mode="reuse",
            reason=f"feature「{title}」→ {st} 变体",
            source_section="features",
        )

    # 5) audience
    aud = script.get("audience") or {}
    a_items = aud.get("items") or []
    if a_items:
        max_a = reg["audience_list"].get("max_per_page", 6)
        for gi, group in enumerate(chunk(a_items, max_a)):
            if not group:
                continue
            items = []
            for lab in group:
                label = lab if isinstance(lab, str) else (lab.get("label") or lab.get("text") or "")
                items.append({"label": label, "icon": guess_audience_icon(label)})
            add(
                "audience_list",
                "audience",
                {
                    "chapter": aud.get("title") or "适宜人群",
                    "items": items,
                },
                mode="reuse",
                reason="audience_list settled; icon 按标签关键词映射金样插画",
                source_section="audience",
            )

    # 6) combination_guidance
    combo = script.get("combination") or {}
    rows = combo.get("rows") or []
    if rows:
        max_c = reg["combination_guidance"].get("max_per_page", 3)
        for gi, group in enumerate(chunk(rows, max_c)):
            if not group:
                continue
            clean = []
            for r in group:
                problem = combo_problem_label(r if isinstance(r, dict) else {})
                clean.append(
                    {
                        "problem": problem,
                        "scenario": problem,  # 引擎 pill 兼容 scenario 字段
                        "partner": r.get("partner") or "",
                        "talk_track": r.get("talk_track") or "",
                        "icon": combo_icon_file(r if isinstance(r, dict) else {}),
                    }
                )
            add(
                "combination_guidance",
                "combination_guidance",
                {
                    "chapter": combo.get("title") or "联合用药",
                    "rows": clean,
                },
                mode="reuse",
                reason="combination_guidance：问题场景短标 + 搭配药 + 话术 + 组合图槽",
                source_section="combination",
            )

    # 7) summary
    summary = script.get("summary") or {}
    srows = summary.get("rows") or []
    if srows:
        mapped = []
        for r in srows:
            mapped.append(
                {
                    "label": r.get("label") or "",
                    "body": r.get("body") or r.get("value") or "",
                }
            )
        add(
            "summary_matrix",
            "efficacy_recap_table",
            {
                "chapter": summary.get("title") or "总结",
                "rows": mapped,
            },
            mode="reuse",
            reason="summary_matrix → efficacy_recap_table（label|body）",
            source_section="summary",
        )

    # 8) precautions
    prec = script.get("precautions") or {}
    pitems = prec.get("items") or []
    if pitems:
        max_p = reg["precautions"].get("max_per_page", 8)
        # one page; if over max, split
        for gi, group in enumerate(chunk(pitems, max_p)):
            if not group:
                continue
            items = [it if isinstance(it, str) else (it.get("text") or str(it)) for it in group]
            # M5：4 张注意事项插画已入库；缺文件时引擎仍可走 labeled 占位
            illos = list(PRECAUTION_ILLUSTRATIONS)
            add(
                "precautions",
                "precautions",
                {
                    "chapter": prec.get("title") or "注意事项",
                    "items": items,
                    "illustrations": illos,
                },
                mode="reuse",
                reason="precautions settled；2×2 接 component-library precautions-illo-v1",
                source_section="precautions",
            )

    if not pages:
        raise GeneratorError("scene plan empty — script has no usable sections")

    return {
        "schema": "courseware-scene-plan/v1",
        "family": "product-training",
        "rules": {
            "empty_cards": "forbidden",
            "hidden": "excluded",
            "copy_source": "script_only",
            "missing_assets": "labeled_placeholder_slot",
        },
        "meta": {
            "display_name": meta.get("display_name"),
            "organization": meta.get("organization"),
            "content_lock": meta.get("content_lock"),
            "brand_boast_disabled": meta.get("brand_boast_disabled"),
        },
        "page_count": len(pages),
        "pages": pages,
        "script_text_atom_count": len(script_atoms),
    }


def scene_plan_to_content_model(plan: dict, script: dict, style_id: str) -> dict:
    """Map scene-plan pages → engine content-model scenes."""
    scenes = []
    for p in plan["pages"]:
        slots = p["slots"]
        st = p["scene_type"]
        pt = p["page_type"]
        sid = p["id"]
        sc: dict[str, Any] = {
            "id": sid,
            "type": st,
            "page_type": pt,
            "layer": "generator_m4",
            "selection": p.get("selection"),
            "source_section": p.get("source_section"),
        }

        if st == "cover":
            sc["title_pill"] = slots.get("title_pill") or ""
            sc["benefits"] = slots.get("benefits") or []
            sc["subtitle"] = slots.get("organization") or ""
        elif st == "hook_pain_data":
            sc["chapter"] = slots.get("chapter")
            sc["section"] = slots.get("section")
            sc["symptoms"] = slots.get("symptoms") or []
            sc["stats"] = slots.get("stats") or []
            sc["source"] = slots.get("source") or ""
        elif st == "time_list":
            sc["card_title"] = slots.get("card_title")
            sc["list"] = slots.get("list") or []
        elif st == "benefit_chain":
            sc["chapter"] = slots.get("chapter")
            sc["section"] = slots.get("section")
            sc["chain"] = slots.get("chain") or []
            if slots.get("subtitles"):
                sc["subtitles"] = slots["subtitles"]
            elif slots.get("body"):
                sc["subtitles"] = [{"text": slots["body"]}]
        elif st in ("feature_origin", "feature_material", "feature_content"):
            sc["chapter"] = slots.get("chapter")
            sc["section"] = slots.get("section")
            if slots.get("map_caption"):
                sc["map_caption"] = slots["map_caption"]
            if slots.get("body"):
                sc["body"] = slots["body"]
            if slots.get("subtitles"):
                sc["subtitles"] = slots["subtitles"]
            elif slots.get("body"):
                sc["subtitles"] = [{"text": slots["body"]}]
        elif st == "audience":
            sc["chapter"] = slots.get("chapter")
            sc["items"] = slots.get("items") or []
        elif st == "combination_guidance":
            sc["chapter"] = slots.get("chapter")
            sc["section"] = slots.get("section")
            sc["rows"] = slots.get("rows") or []
        elif st == "efficacy_recap_table":
            sc["chapter"] = slots.get("chapter")
            sc["rows"] = slots.get("rows") or []
        elif st == "precautions":
            sc["chapter"] = slots.get("chapter")
            sc["items"] = slots.get("items") or []
            sc["illustrations"] = slots.get("illustrations") or []
        else:
            # pass through remaining slots
            sc.update({k: v for k, v in slots.items() if k not in sc})

        scenes.append(sc)

    meta = script.get("meta") or {}
    return {
        "project_id": f"generator-m4.{meta.get('display_name', 'courseware')}",
        "schema": "courseware-content-model/v1",
        "family": "product-training",
        "engine": "courseware-pptx-v1",
        "style_pack_id": style_id,
        "content_lock": meta.get("content_lock"),
        "canvas": {"width": 1920, "height": 1080},
        "asset_policy": {
            "missing_assets": "labeled_placeholder_slot",
            "packshots": "business_authorized_or_placeholder",
        },
        "generator": {
            "name": "scripts/generate_courseware.py",
            "version": "m4",
            "copy_policy": "script_only",
        },
        "scenes": scenes,
    }


def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def export_pptx(
    *,
    model: Path,
    style: Path,
    out_pptx: Path,
    assets: Path,
    recipes: Path,
    engine: Path,
) -> dict:
    cmd = [
        "node",
        str(engine),
        "--model",
        str(model),
        "--style",
        str(style),
        "--out",
        str(out_pptx),
        "--assets",
        str(assets),
        "--recipes",
        str(recipes),
        "--prefix",
        "editable:m4",
    ]
    proc = run_cmd(cmd)
    if proc.returncode != 0:
        raise GeneratorError(
            f"export.mjs failed (code={proc.returncode}):\n{proc.stderr or proc.stdout}"
        )
    # last line JSON inspect
    inspect = {}
    try:
        inspect = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        inspect_path = Path(str(out_pptx) + ".inspect.json")
        if inspect_path.exists():
            inspect = load_json(inspect_path)
    return inspect


def build_manifest(model: Path, out: Path) -> None:
    proc = run_cmd(
        [
            "python3",
            str(DEFAULT_MANIFEST),
            "--model",
            str(model),
            "--out",
            str(out),
            "--prefix",
            "editable:m4",
        ]
    )
    if proc.returncode != 0:
        raise GeneratorError(f"build_layer_manifest failed:\n{proc.stderr or proc.stdout}")


def render_qa(pptx: Path, qa_dir: Path) -> list[str]:
    """soffice → pdf → pdftoppm PNGs."""
    qa_dir.mkdir(parents=True, exist_ok=True)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice or not pdftoppm:
        return []

    tmp = qa_dir / "_tmp_pdf"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    proc = run_cmd(
        [
            soffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmp),
            str(pptx),
        ]
    )
    if proc.returncode != 0:
        raise GeneratorError(f"soffice convert failed:\n{proc.stderr or proc.stdout}")

    pdfs = list(tmp.glob("*.pdf"))
    if not pdfs:
        raise GeneratorError("soffice produced no pdf")
    pdf = pdfs[0]
    prefix = qa_dir / "slide"
    proc2 = run_cmd([pdftoppm, "-png", "-r", "120", str(pdf), str(prefix)])
    if proc2.returncode != 0:
        raise GeneratorError(f"pdftoppm failed:\n{proc2.stderr or proc2.stdout}")

    # normalize names slide-1.png ...
    raw = sorted(qa_dir.glob("slide-*.png")) + sorted(qa_dir.glob("slide*.png"))
    # pdftoppm produces slide-1.png already with - prefix path
    produced = sorted(qa_dir.glob("slide-*.png"))
    if not produced:
        # slide1.png style
        for i, p in enumerate(sorted(qa_dir.glob("slide*.png")), 1):
            dest = qa_dir / f"slide-{i}.png"
            if p.resolve() != dest.resolve():
                p.rename(dest)
            produced.append(dest)

    # cleanup pdf temp
    shutil.rmtree(tmp, ignore_errors=True)
    return [str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p) for p in sorted(qa_dir.glob("slide-*.png"))]


def apply_page_filter(plan: dict, filter_spec: str | None) -> dict:
    """Filter scene-plan pages.

    Spec examples:
      cover,hook_pain_data,benefit_chain:1,combination_guidance,precautions
      (benefit_chain:1 keeps only the first benefit page)

    Re-indexes page i / id after filter.
    """
    if not filter_spec or not str(filter_spec).strip():
        return plan

    rules: list[tuple[str, int | None]] = []
    for part in str(filter_spec).split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            key, n = part.split(":", 1)
            rules.append((key.strip(), int(n.strip())))
        else:
            rules.append((part, None))

    if not rules:
        return plan

    # match by scene_type first, then page_type
    used_counts: dict[str, int] = {}
    kept: list[dict] = []
    for p in plan["pages"]:
        st = p.get("scene_type") or ""
        pt = p.get("page_type") or ""
        for key, max_n in rules:
            if st != key and pt != key:
                continue
            n = used_counts.get(key, 0)
            if max_n is not None and n >= max_n:
                break
            used_counts[key] = n + 1
            kept.append(p)
            break

    if not kept:
        raise GeneratorError(f"page filter removed all pages: {filter_spec!r}")

    reindexed = []
    for i, p in enumerate(kept, 1):
        np = dict(p)
        np["i"] = i
        np["id"] = f"P{i:02d}_{p['page_type']}"
        reindexed.append(np)

    out = dict(plan)
    out["pages"] = reindexed
    out["page_count"] = len(reindexed)
    out["page_filter"] = filter_spec
    return out


def prepare_assets(assets_root: Path, out_assets: Path, extra_dirs: list[Path] | None = None) -> Path:
    """
    Ensure engine can resolve gold icons + optional run assets.
    Prefer symlink/copy of generated/ from cw4 into out_dir/assets.
    """
    out_assets.mkdir(parents=True, exist_ok=True)
    gen = out_assets / "generated"
    gen.mkdir(parents=True, exist_ok=True)

    sources: list[Path] = []
    if (assets_root / "assets" / "generated").is_dir():
        sources.append(assets_root / "assets" / "generated")
    elif (assets_root / "generated").is_dir():
        sources.append(assets_root / "generated")
    else:
        sources.append(assets_root)

    for d in extra_dirs or []:
        if d.is_dir():
            sources.append(d)

    for src in sources:
        if not src.is_dir():
            continue
        for f in src.iterdir():
            if not f.is_file():
                continue
            if f.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            dest = gen / f.name
            if dest.exists():
                continue
            try:
                dest.symlink_to(f.resolve())
            except OSError:
                shutil.copy2(f, dest)

    # also place icons at assets root for resolve paths that don't use generated/
    for f in gen.iterdir():
        if f.is_file() and f.suffix.lower() == ".png":
            dest = out_assets / f.name
            if not dest.exists():
                try:
                    dest.symlink_to(f.resolve())
                except OSError:
                    shutil.copy2(f, dest)

    return out_assets


def main() -> int:
    ap = argparse.ArgumentParser(description="M4 courseware generator: script → plan → model → PPTX → QA")
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--style", type=Path, default=DEFAULT_STYLE)
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--recipes", type=Path, default=DEFAULT_RECIPES)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--assets",
        type=Path,
        default=DEFAULT_ASSETS,
        help="Asset root (cw4 gold assets default for density)",
    )
    ap.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    ap.add_argument("--skip-export", action="store_true")
    ap.add_argument("--skip-qa", action="store_true")
    ap.add_argument("--skip-provenance", action="store_true")
    ap.add_argument(
        "--verify-script",
        type=Path,
        default=None,
        help="override script path for verify_text_provenance (default: --script)",
    )
    ap.add_argument(
        "--page-filter",
        type=str,
        default=None,
        help=(
            "Comma scene_type/page_type filter with optional :max, e.g. "
            "cover,hook_pain_data,benefit_chain:1,combination_guidance,precautions"
        ),
    )
    ap.add_argument(
        "--name-suffix",
        type=str,
        default="M4生成",
        help="PPTX filename suffix after display_name (default M4生成; M5 use M5验证)",
    )
    args = ap.parse_args()

    script_path = args.script.resolve()
    style_path = args.style.resolve()
    registry_path = args.registry.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    script = load_json(script_path)
    registry = load_json(registry_path)
    style = load_json(style_path)
    style_id = style.get("id") or style.get("style_pack_id") or style_path.parent.name

    # ── 1) scene plan ──
    plan = expand_scene_plan(script, registry)
    plan = apply_page_filter(plan, args.page_filter)
    plan["source_script"] = str(script_path.relative_to(ROOT)) if script_path.is_relative_to(ROOT) else str(script_path)
    plan["style"] = str(style_path.relative_to(ROOT)) if style_path.is_relative_to(ROOT) else str(style_path)
    plan["registry"] = str(registry_path.relative_to(ROOT)) if registry_path.is_relative_to(ROOT) else str(registry_path)
    plan_path = out_dir / "scene-plan.json"
    write_json(plan_path, plan)

    # ── 2) content model ──
    model = scene_plan_to_content_model(plan, script, style_id)
    model_path = out_dir / "content-model.json"
    write_json(model_path, model)

    # ── 3) assets for this run ──
    # Engine resolves files as {assetsRoot}/assets/generated/<file>
    # so assetsRoot must be the run out_dir (not out_dir/assets).
    prepare_assets(
        args.assets.resolve(),
        out_dir / "assets",
        extra_dirs=[
            PRECAUTIONS_LIBRARY_DIR,
            ROOT
            / "production-library/validation/courseware/m3-candidate-pages/assets/generated",
        ],
    )
    assets_out = out_dir

    result: dict[str, Any] = {
        "ok": True,
        "out_dir": str(out_dir.relative_to(ROOT)) if out_dir.is_relative_to(ROOT) else str(out_dir),
        "scene_plan": str(plan_path.name),
        "content_model": str(model_path.name),
        "page_count": plan["page_count"],
        "page_types": [p["page_type"] for p in plan["pages"]],
        "scene_types": [p["scene_type"] for p in plan["pages"]],
        "selection_modes": {
            m: sum(1 for p in plan["pages"] if p["selection"]["mode"] == m)
            for m in ("reuse", "cross_template", "new")
        },
        "content_lock": (script.get("meta") or {}).get("content_lock"),
    }

    # ── 4) layer manifest ──
    manifest_path = out_dir / "layer-manifest.json"
    try:
        build_manifest(model_path, manifest_path)
        result["layer_manifest"] = manifest_path.name
    except GeneratorError as e:
        # non-fatal if manifest builder lags new scene types
        result["layer_manifest_error"] = str(e)

    if args.skip_export:
        write_json(out_dir / "generate-report.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # ── 5) export PPTX ──
    display = (script.get("meta") or {}).get("display_name") or "courseware"
    safe_name = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", display)[:40]
    suffix = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", args.name_suffix or "M4生成")[:24]
    pptx_path = out_dir / f"{safe_name}_{suffix}.pptx"
    inspect = export_pptx(
        model=model_path,
        style=style_path,
        out_pptx=pptx_path,
        assets=assets_out,
        recipes=args.recipes.resolve(),
        engine=args.engine.resolve(),
    )
    result["pptx"] = str(pptx_path.relative_to(ROOT)) if pptx_path.is_relative_to(ROOT) else str(pptx_path)
    result["export_inspect"] = {
        "slides": inspect.get("slides"),
        "unknown_types": inspect.get("unknown_types"),
        "recipe_trace": inspect.get("recipe_trace"),
        "font": inspect.get("font"),
    }
    if inspect.get("unknown_types"):
        result["ok"] = False
        result["error"] = f"unknown scene types: {inspect['unknown_types']}"

    # ── 6) QA images ──
    if not args.skip_qa and result.get("ok", True):
        try:
            qa_files = render_qa(pptx_path, out_dir / "qa")
            result["qa"] = qa_files
        except GeneratorError as e:
            result["qa_error"] = str(e)

    # ── 7) text provenance ──
    if not args.skip_provenance and pptx_path.exists():
        verify = ROOT / "scripts/verify_text_provenance.py"
        if verify.exists():
            # 全量默认 0.85；--page-filter 子集页时脚本未出页的原子会缺失，放宽覆盖率
            # 仍强制：禁词 0 命中 + invention_check
            min_cov = "0.55" if args.page_filter else "0.85"
            proc = run_cmd(
                [
                    "python3",
                    str(verify),
                    "--pptx",
                    str(pptx_path),
                    "--script",
                    str(args.verify_script or script_path),
                    "--out",
                    str(out_dir / "provenance-report.json"),
                    "--min-coverage",
                    min_cov,
                ]
            )
            result["provenance_exit"] = proc.returncode
            result["provenance_min_coverage"] = float(min_cov)
            if args.page_filter:
                result["provenance_note"] = (
                    "page_filter subset: coverage threshold relaxed; "
                    "forbidden + invention still hard"
                )
            if proc.returncode != 0:
                result["ok"] = False
                result["provenance_stderr"] = (proc.stderr or proc.stdout)[-2000:]
            else:
                try:
                    result["provenance"] = load_json(out_dir / "provenance-report.json")
                except Exception:
                    result["provenance_stdout"] = proc.stdout[-1000:]

    write_json(out_dir / "generate-report.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GeneratorError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)
