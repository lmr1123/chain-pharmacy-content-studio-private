#!/usr/bin/env python3
"""构件化课件生成器（M4）

流水线：
  script.structured.json
    → scene-plan.json（页型选择留痕：reuse / cross_template / new + 理由）
    → content-model.json（引擎输入）
    → layer-manifest.json
    → courseware-pptx-v1 export → PPTX
    → QA 图（项目内 artifact-tool 逐页 PNG）

硬校验：
  - hidden 条目排除
  - empty_cards = forbidden
  - 文案只取自 script（生成器不造功效/剂量）
  - 缺图 → 引擎 labeled 占位槽

用法：
  python3 scripts/generate_courseware.py \\
    --script /path/to/new-theme/script.structured.json \\
    --style production-library/styles/reference-product-blue-v1/tokens.json \\
    --out-dir /path/to/new-theme/output
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from product_pptx_asset_plan import asset_file_info, cw4_gold_image_hashes

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "production-library/page-types/product-training/registry.json"
DEFAULT_RECIPES = ROOT / "production-library/page-types/product-training/recipes"
DEFAULT_STYLE = ROOT / "production-library/styles/reference-product-blue-v1/tokens.json"
DEFAULT_ENGINE = ROOT / "production-library/engines/courseware-pptx-v1/export.mjs"
DEFAULT_ARTIFACT_RENDERER = (
    ROOT / "production-library/engines/courseware-pptx-v1/render-pptx.mjs"
)
DEFAULT_MANIFEST = ROOT / "production-library/engines/courseware-pptx-v1/build_layer_manifest.py"
DEFAULT_ASSETS = ROOT / "assets"

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
    "好物推荐",  # cover badge 文案仅在业务显式提供时使用
}


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
    for k in (
        "display_name",
        "organization",
        "tagline",
        "cover_badge",
        "cover_stage_tag",
    ):
        if meta.get(k):
            atoms.append(str(meta[k]))
    for item in visible_items(meta.get("cover_points")):
        atoms.append(
            str(item if not isinstance(item, dict) else item.get("text") or item.get("label") or "")
        )

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
    if aud.get("body"):
        atoms.append(str(aud["body"]))
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
    for illo in prec.get("illustrations") or []:
        if isinstance(illo, dict) and illo.get("label"):
            atoms.append(str(illo["label"]))

    overview = script.get("product_overview") or {}
    for key in ("title", "statement"):
        if overview.get(key):
            atoms.append(str(overview[key]))
    for fact in overview.get("facts") or []:
        if isinstance(fact, dict):
            for key in ("label", "value"):
                if fact.get(key):
                    atoms.append(str(fact[key]))

    consultation = script.get("consultation") or {}
    if consultation.get("title"):
        atoms.append(str(consultation["title"]))
    for step in consultation.get("steps") or []:
        if isinstance(step, dict):
            for key in ("question", "why"):
                if step.get(key):
                    atoms.append(str(step[key]))

    evidence = script.get("evidence") or {}
    if evidence.get("title"):
        atoms.append(str(evidence["title"]))
    for item in evidence.get("items") or []:
        if isinstance(item, dict):
            for key in ("metric", "label", "source"):
                if item.get(key):
                    atoms.append(str(item[key]))

    objections = script.get("objection_handling") or {}
    if objections.get("title"):
        atoms.append(str(objections["title"]))
    for row in objections.get("rows") or []:
        if isinstance(row, dict):
            for key in ("objection", "response", "boundary"):
                if row.get(key):
                    atoms.append(str(row[key]))

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
        symptoms = []

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
        # prefer first two meaningful percentages without topic-specific rewrites
        pct_stats = [s for s in stats if "%" in s["number"] or s.get("unit") in ("%", "％", "")]
        if len(pct_stats) >= 2:
            stats = pct_stats[:2]
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
    """No theme illustration may be inferred from audience copy."""
    return "audience_pending"


def benefit_chain_assets(title: str, index: int) -> list[str]:
    """Draft-only neutral gap; formal runs require an explicit real chain visual."""
    return ["benefit_source_pending", "arrow", "benefit_result_pending"]


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


def combo_icon_file(row: dict) -> Any:
    """Use only an explicit combination visual; otherwise keep a visible gap."""
    if row.get("icon"):
        return row["icon"]
    return "__missing__/combination-pending.png"


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


FORMAL_PENDING_TOKENS = ("待确认", "待业务", "待补充", "待审核")
FORMAL_SYSTEM_SOURCE_KINDS = {
    "system_generated",
    "approved_library",
    "business_evidence",
    "business_authorized_partner_packshot",
}


def _pending_paths(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        if value.get("hidden") is True:
            return hits
        for key, item in value.items():
            hits.extend(_pending_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_pending_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str) and any(token in value for token in FORMAL_PENDING_TOKENS):
        hits.append(path)
    return hits


def validate_formal_assets(script: dict, *, script_path: Path) -> dict[str, Any]:
    """Fail closed unless every formal image slot has a safe, traceable real file."""
    pending = _pending_paths(script)
    if pending:
        raise GeneratorError(
            "formal render contains pending fields: " + ", ".join(pending[:8])
        )

    script_path = script_path.expanduser().resolve()
    job_root = script_path.parent.parent if script_path.parent.name == "draft" else None
    intake_root = job_root / "intake" if job_root else None
    generated_root = intake_root / "generated-assets" if intake_root else None
    component_root = (ROOT / "assets/component-library").resolve()
    records: list[dict[str, Any]] = []
    errors: list[str] = []

    def under(path: Path, root: Path | None) -> bool:
        return bool(root and (path == root or path.is_relative_to(root)))

    def validate_one(
        value: Any,
        *,
        slot: str,
        product: bool = False,
    ) -> None:
        info = asset_file_info(value, base_dir=script_path.parent)
        if not info.get("ok"):
            errors.append(f"{slot}: {info.get('error')}")
            return
        path = Path(str(info["path"])).resolve()
        source_kind = str(info.get("source_kind") or "")
        if product:
            task_bound = bool(
                intake_root
                and path.parent == intake_root
                and path.name.startswith("product-packshot")
            )
            allowed_source = source_kind == "business_authorized"
        else:
            task_bound = under(path, generated_root) or under(path, component_root)
            allowed_source = source_kind in FORMAL_SYSTEM_SOURCE_KINDS
        if not task_bound and not allowed_source:
            errors.append(f"{slot}: source_policy_not_satisfied")
            return
        records.append(
            {
                "slot": slot,
                "path": str(path),
                "sha256": info.get("sha256"),
                "source_kind": source_kind or ("task_bound" if task_bound else ""),
            }
        )

    validate_one(
        (script.get("meta") or {}).get("product_packshot"),
        slot="cover.product_packshot",
        product=True,
    )

    for index, item in enumerate(((script.get("benefits") or {}).get("items") or [])):
        if isinstance(item, dict) and item.get("hidden") is True:
            continue
        row = item if isinstance(item, dict) else {}
        chain = row.get("chain") or []
        if not isinstance(chain, list) or not chain:
            errors.append(f"benefits.items[{index}].chain: missing")
            continue
        for chain_index, visual in enumerate(chain):
            if not isinstance(visual, dict):
                errors.append(
                    f"benefits.items[{index}].chain[{chain_index}]: explicit_file_required"
                )
                continue
            validate_one(
                visual,
                slot=f"benefits.items[{index}].chain[{chain_index}]",
            )

    for index, item in enumerate(((script.get("features") or {}).get("items") or [])):
        if isinstance(item, dict) and item.get("hidden") is True:
            continue
        row = item if isinstance(item, dict) else {}
        validate_one(row.get("visual"), slot=f"features.items[{index}].visual")

    audience = script.get("audience") or {}
    if audience.get("items"):
        validate_one(audience.get("visual"), slot="audience.visual")

    for index, item in enumerate(((script.get("combination") or {}).get("rows") or [])):
        if isinstance(item, dict) and item.get("hidden") is True:
            continue
        row = item if isinstance(item, dict) else {}
        validate_one(row.get("icon"), slot=f"combination.rows[{index}].icon")

    precautions = script.get("precautions") or {}
    if precautions.get("items"):
        illustrations = precautions.get("illustrations") or []
        if not illustrations:
            errors.append("precautions.illustrations: missing")
        elif not (
            (len(illustrations) == 1 and isinstance(illustrations[0], dict) and illustrations[0].get("wide"))
            or len(illustrations) == 4
        ):
            errors.append("precautions.illustrations: require_one_wide_or_four_explicit")
        for index, visual in enumerate(illustrations):
            validate_one(visual, slot=f"precautions.illustrations[{index}]")

    if errors:
        raise GeneratorError("formal asset validation failed: " + "; ".join(errors[:12]))
    return {
        "ok": True,
        "validated_files": len(records),
        "assets": records,
        "cw4_hash_blocklist_size": len(cw4_gold_image_hashes()),
    }


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
        for key in ("items", "rows", "paragraphs", "symptoms", "stats", "facts", "steps"):
            if key in slots and isinstance(slots[key], list) and len(slots[key]) == 0:
                raise GeneratorError(f"empty_cards forbidden: {page_type}.{key}")
        # copy provenance: all string leaves in slots must come from script (except chrome keys)
        def walk(obj: Any, path: str) -> None:
            if isinstance(obj, str):
                leaf = path.rsplit(".", 1)[-1]
                if (
                    leaf
                    in {
                        "role",
                        "icon",
                        "file",
                        "asset",
                        "visual",
                        "src",
                        "packshot",
                        "product_packshot",
                        "fit",
                        "crop",
                        "slot_ratio",
                        "safe_area",
                        "source_kind",
                    }
                ):
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
            "packshot": meta.get("product_packshot") or "",
            "badge": meta.get("cover_badge") or "",
            "cover_points": visible_items(meta.get("cover_points")),
            "stage_tag": meta.get("cover_stage_tag") or "",
            "benefits": [
                it.get("title") if isinstance(it, dict) else str(it)
                for it in visible_items((script.get("benefits") or {}).get("items"))
            ][:3],
        },
        mode="reuse",
        reason="registry courseware_cover settled; meta fields",
        source_section="meta",
    )

    # Green gold-sample contract: authorized packshot + explicit product facts.
    overview = script.get("product_overview") or {}
    overview_facts = visible_items(overview.get("facts"))
    if overview_facts:
        max_overview = reg["product_overview"].get("max_per_page", 6)
        for group in chunk(overview_facts, max_overview):
            add(
                "product_overview",
                "product_overview",
                {
                    "chapter": overview.get("title") or "",
                    "facts": group,
                    "statement": overview.get("statement") or "",
                    "product_packshot": meta.get("product_packshot") or "",
                },
                mode="cross_template",
                reason="绿色金样商品总览 → 仅复用信息层级与授权商品图槽",
                source_section="product_overview",
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
        # Preserve the approved paragraph in full; the renderer owns wrapping and fit.
        list_lines = []
        for p in paras[:3]:
            list_lines.append(p)
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

    # 3) benefits → one benefit_chain page per item
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
                "chain": (
                    it.get("chain")
                    if isinstance(it, dict) and it.get("chain")
                    else benefit_chain_assets(title, group_i)
                ),
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
        if isinstance(it, dict) and it.get("visual"):
            slots["visual"] = it["visual"]
        # 产地页正文走 noteBar（subtitles/body），勿用 map_caption 硬截断造成「半截文案」
        add(
            "feature_cards",
            st,
            slots,
            mode="reuse",
            reason=f"feature「{title}」→ {st} 变体",
            source_section="features",
        )

    # Courseware-3 gold contract: evidence and its traceable source remain paired.
    evidence = script.get("evidence") or {}
    evidence_items = visible_items(evidence.get("items"))
    if evidence_items:
        max_evidence = reg["evidence_ladder"].get("max_per_page", 5)
        for group in chunk(evidence_items, max_evidence):
            add(
                "evidence_ladder",
                "evidence_ladder",
                {
                    "chapter": evidence.get("title") or "",
                    "items": group,
                },
                mode="cross_template",
                reason="速福达课件3 feature_3 → 仅复用证据层级合同",
                source_section="evidence",
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
                row = {"label": label, "icon": guess_audience_icon(label)}
                if isinstance(lab, dict) and lab.get("asset"):
                    row["asset"] = lab["asset"]
                    row["icon"] = ""
                items.append(row)
            audience_slots: dict[str, Any] = {
                "chapter": aud.get("title") or "适宜人群",
                "items": items,
            }
            if aud.get("body"):
                audience_slots["body"] = aud["body"]
            if aud.get("visual"):
                audience_slots["visual"] = aud["visual"]
            add(
                "audience_list",
                "audience",
                audience_slots,
                mode="reuse",
                reason="audience_list settled；主题插图仅接受显式绑定",
                source_section="audience",
            )

    # Disease-product gold contract: reusable consultation questions and rationale.
    consultation = script.get("consultation") or {}
    consultation_steps = visible_items(consultation.get("steps"))
    if consultation_steps:
        max_consultation = reg["consultation_framework"].get("max_per_page", 4)
        for group in chunk(consultation_steps, max_consultation):
            add(
                "consultation_framework",
                "consultation_framework",
                {
                    "chapter": consultation.get("title") or "",
                    "steps": group,
                },
                mode="cross_template",
                reason="穿心莲课件2咨询框架 → 仅复用问询路径合同",
                source_section="consultation",
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

    # New business component: objection, approved response and escalation boundary.
    objections = script.get("objection_handling") or {}
    objection_rows = visible_items(objections.get("rows"))
    if objection_rows:
        max_objections = reg["objection_handling"].get("max_per_page", 3)
        for group in chunk(objection_rows, max_objections):
            add(
                "objection_handling",
                "objection_handling",
                {
                    "chapter": objections.get("title") or "",
                    "rows": group,
                },
                mode="new",
                reason="新增门店异议应答合同；文案全部来自业务审核稿",
                source_section="objection_handling",
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
            pending_only = all("待确认" in x or "待业务" in x for x in items)
            illos = prec.get("illustrations") or [
                {
                    "file": "__missing__/precautions-pending.png",
                    "label": "注意事项素材待业务资料",
                }
            ]
            add(
                "precautions",
                "precautions",
                {
                    "chapter": prec.get("title") or "注意事项",
                    "items": items,
                    "illustrations": illos,
                },
                mode="reuse",
                reason=(
                    "precautions 未审核 → 中性素材占位"
                    if pending_only
                    else "precautions 内容已填；正式插图仍需显式绑定"
                ),
                source_section="precautions",
            )

    requested_sequence = meta.get("page_sequence")
    if requested_sequence is not None:
        if not isinstance(requested_sequence, list) or not requested_sequence:
            raise GeneratorError("meta.page_sequence must be a non-empty list")
        queues: dict[str, list[dict]] = {}
        for page in pages:
            queues.setdefault(page["page_type"], []).append(page)
        ordered: list[dict] = []
        for position, page_type in enumerate(requested_sequence, 1):
            if not isinstance(page_type, str) or page_type not in reg:
                raise GeneratorError(
                    f"meta.page_sequence[{position}] is not a registered page_type: {page_type!r}"
                )
            candidates = queues.get(page_type) or []
            if not candidates:
                raise GeneratorError(
                    f"meta.page_sequence[{position}] requests unavailable occurrence: {page_type}"
                )
            ordered.append(candidates.pop(0))
        for page_type in set(requested_sequence):
            if queues.get(page_type):
                raise GeneratorError(
                    f"meta.page_sequence omits generated occurrence: {page_type}; "
                    "repeat the page_type to deliver the next content chunk"
                )
        pages = ordered

    if not pages:
        raise GeneratorError("scene plan empty — script has no usable sections")

    # Page ids express the delivered order. Repeated page types consume the next
    # chunk of that type and remain uniquely addressable.
    for index, page in enumerate(pages, 1):
        page["i"] = index
        page["id"] = f"P{index:02d}_{page['page_type']}"

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
        "requested_page_sequence": requested_sequence,
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
            sc["cover_points"] = slots.get("cover_points") or []
            sc["subtitle"] = slots.get("organization") or ""
            sc["product_packshot"] = slots.get("packshot") or ""
            sc["badge"] = slots.get("badge") or ""
            sc["stage_tag"] = slots.get("stage_tag") or ""
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
            if slots.get("visual"):
                sc["visual"] = slots["visual"]
            if slots.get("subtitles"):
                sc["subtitles"] = slots["subtitles"]
            elif slots.get("body"):
                sc["subtitles"] = [{"text": slots["body"]}]
        elif st == "audience":
            sc["chapter"] = slots.get("chapter")
            sc["items"] = slots.get("items") or []
            if slots.get("body"):
                sc["body"] = slots["body"]
            if slots.get("visual"):
                sc["visual"] = slots["visual"]
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
        elif st == "product_overview":
            sc["chapter"] = slots.get("chapter")
            sc["facts"] = slots.get("facts") or []
            sc["statement"] = slots.get("statement") or ""
            sc["product_packshot"] = slots.get("product_packshot") or ""
        elif st == "consultation_framework":
            sc["chapter"] = slots.get("chapter")
            sc["steps"] = slots.get("steps") or []
        elif st == "evidence_ladder":
            sc["chapter"] = slots.get("chapter")
            sc["items"] = slots.get("items") or []
        elif st == "objection_handling":
            sc["chapter"] = slots.get("chapter")
            sc["rows"] = slots.get("rows") or []
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
        "sources": script.get("sources") or [],
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
        "editable:component",
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
            "editable:component",
        ]
    )
    if proc.returncode != 0:
        raise GeneratorError(f"build_layer_manifest failed:\n{proc.stderr or proc.stdout}")


def _qa_slide_pngs(qa_dir: Path) -> list[Path]:
    def slide_number(path: Path) -> int:
        match = re.fullmatch(r"slide-(\d+)\.png", path.name, flags=re.IGNORECASE)
        return int(match.group(1)) if match else 10**9

    return sorted(qa_dir.glob("slide-*.png"), key=slide_number)


def _validate_qa_pngs(qa_dir: Path, *, expected: int | None = None) -> list[Path]:
    produced = _qa_slide_pngs(qa_dir)
    if not produced:
        raise GeneratorError("renderer produced no slide PNG")
    if expected is not None and len(produced) != expected:
        raise GeneratorError(
            f"renderer slide count mismatch: expected {expected}, got {len(produced)}"
        )
    empty = [path.name for path in produced if path.stat().st_size < 100]
    if empty:
        raise GeneratorError(f"renderer produced empty PNG: {', '.join(empty)}")
    return produced


def render_qa(pptx: Path, qa_dir: Path) -> list[str]:
    """Render every slide with the project artifact-tool runtime, fail closed."""
    qa_dir.mkdir(parents=True, exist_ok=True)
    for stale in _qa_slide_pngs(qa_dir):
        stale.unlink()

    attempts: list[dict[str, Any]] = []
    artifact_error = ""
    if not DEFAULT_ARTIFACT_RENDERER.is_file():
        artifact_error = f"renderer_missing: {DEFAULT_ARTIFACT_RENDERER}"
    else:
        try:
            proc = run_cmd(
                [
                    "node",
                    str(DEFAULT_ARTIFACT_RENDERER),
                    "--input",
                    str(pptx),
                    "--output-dir",
                    str(qa_dir),
                    "--scale",
                    "1",
                ]
            )
            if proc.returncode != 0:
                artifact_error = (
                    proc.stderr or proc.stdout or "artifact renderer failed"
                ).strip()
            else:
                payload = json.loads(proc.stdout.strip().splitlines()[-1])
                expected = int(payload.get("slideCount") or 0)
                if expected <= 0:
                    raise GeneratorError("artifact-tool reported zero slides")
                produced = _validate_qa_pngs(qa_dir, expected=expected)
                attempts.append(
                    {"backend": "artifact-tool", "ok": True, "slides": len(produced)}
                )
                write_json(
                    qa_dir / "qa-render-report.json",
                    {
                        "ok": True,
                        "backend": "artifact-tool",
                        "slide_count": len(produced),
                        "attempts": attempts,
                    },
                )
                return [
                    str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
                    for path in produced
                ]
        except (
            GeneratorError,
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            artifact_error = str(error)

    attempts.append(
        {"backend": "artifact-tool", "ok": False, "error": artifact_error}
    )
    for stale in _qa_slide_pngs(qa_dir):
        stale.unlink()
    write_json(
        qa_dir / "qa-render-report.json",
        {"ok": False, "backend": None, "slide_count": 0, "attempts": attempts},
    )
    errors = "; ".join(
        f"{attempt['backend']}: {attempt.get('error') or 'failed'}" for attempt in attempts
    )
    raise GeneratorError(f"QA render failed closed: {errors}")


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
    """Create the run asset directories without bulk-importing any template media.

    ``assets_root`` and ``extra_dirs`` remain accepted for CLI compatibility. Formal
    visuals are resolved from explicit script bindings and validated before export.
    """
    out_assets.mkdir(parents=True, exist_ok=True)
    (out_assets / "generated").mkdir(parents=True, exist_ok=True)
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
        help="Compatibility-only asset root; formal visuals must be explicitly bound",
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
    formal_asset_report = (
        None
        if args.skip_export
        else validate_formal_assets(script, script_path=script_path)
    )

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
    prepare_assets(args.assets.resolve(), out_dir / "assets")
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
    if formal_asset_report is not None:
        result["formal_asset_validation"] = formal_asset_report

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
            result["ok"] = False
            result["error"] = "QA slide rendering failed"
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
