#!/usr/bin/env python3
"""Content-driven layout rules for business delivery (no empty padding rows).

Used by WorkBuddy / generation planning. Business never fills coordinates;
agents must call these rules before emitting PPT/video plans.
"""

from __future__ import annotations

from typing import Any


class ContentDrivenError(ValueError):
    pass


def normalize_items(items: list[Any] | None) -> list[Any]:
    if not items:
        return []
    out: list[Any] = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, str) and not item.strip():
            continue
        if isinstance(item, dict):
            # empty dict or all-empty values → drop
            vals = [v for v in item.values() if str(v or "").strip()]
            if not vals:
                continue
        out.append(item)
    return out


def plan_list_block(
    *,
    module_id: str,
    title: str,
    items: list[Any] | None,
    gold_example_count: int | None = None,
) -> dict[str, Any]:
    """Plan a list/table module from actual business items.

    Rules:
    - N items → N rows/cards
    - N=0 → omit module (status=omitted)
    - Never pad to gold_example_count with empty shells
    """
    cleaned = normalize_items(items)
    n = len(cleaned)
    if n == 0:
        return {
            "module_id": module_id,
            "title": title,
            "status": "omitted",
            "item_count": 0,
            "items": [],
            "layout": None,
            "forbid_empty_padding": True,
            "note": "业务未提供该模块内容，整节省略",
        }
    if gold_example_count is not None and n < gold_example_count:
        # explicit: do NOT pad
        pass
    layout = "rows" if n <= 6 else "rows_paginated"
    return {
        "module_id": module_id,
        "title": title,
        "status": "included",
        "item_count": n,
        "items": cleaned,
        "layout": layout,
        "forbid_empty_padding": True,
        "gold_example_count": gold_example_count,
        "note": f"业务 {n} 条 → 版式 {n} 行；禁止凑满 {gold_example_count or '金样'} 空行",
    }


def plan_combination_guidance(
    rows: list[dict[str, Any]] | None,
    *,
    gold_example_count: int = 3,
) -> dict[str, Any]:
    """联合用药：有几组出几行。"""
    cleaned: list[dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        scenario = str(row.get("scenario") or row.get("应用场景") or "").strip()
        combo = str(row.get("combination") or row.get("联合用药") or "").strip()
        talk = str(row.get("talk_track") or row.get("销售话术") or "").strip()
        if not (scenario or combo or talk):
            continue
        cleaned.append(
            {
                "scenario": scenario,
                "combination": combo,
                "partner": str(row.get("partner") or row.get("联合商品") or "").strip(),
                "talk_track": talk,
            }
        )
    plan = plan_list_block(
        module_id="combination_guidance",
        title="联合用药话术",
        items=cleaned,
        gold_example_count=gold_example_count,
    )
    plan["rule"] = "lesson-multi-theme-courseware-input-must-be-content-driven"
    return plan


def assert_no_empty_padding(plan: dict[str, Any]) -> None:
    if plan.get("status") == "omitted":
        return
    items = plan.get("items") or []
    if plan.get("item_count") != len(items):
        raise ContentDrivenError(
            f"{plan.get('module_id')}: item_count={plan.get('item_count')} != len(items)={len(items)}"
        )
    gold = plan.get("gold_example_count")
    if gold is not None and len(items) < gold and plan.get("status") == "included":
        # must not invent empty items to match gold
        if any(_is_empty_shell(x) for x in items):
            raise ContentDrivenError(f"{plan.get('module_id')}: empty shell row forbidden")
    if any(_is_empty_shell(x) for x in items):
        raise ContentDrivenError(f"{plan.get('module_id')}: empty shell row forbidden")


def _is_empty_shell(item: Any) -> bool:
    if item is None:
        return True
    if isinstance(item, str):
        return not item.strip() or item.strip() in {"待补充", "待填写", "（空）", "-"}
    if isinstance(item, dict):
        meaningful = []
        for k, v in item.items():
            if k in {"partner_asset", "image_slot"}:
                continue
            if str(v or "").strip() and str(v).strip() not in {"待补充", "待填写", "包装图待接入"}:
                meaningful.append(v)
        return len(meaningful) == 0
    return False


def build_gap_list(
    *,
    theme: str,
    template_id: str,
    missing_fields: list[str] | None = None,
    missing_assets: list[dict[str, str]] | None = None,
    pending_confirmations: list[str] | None = None,
) -> dict[str, Any]:
    """Standard gap list payload for business confirmation."""
    return {
        "schema": "business-gap-list-v1",
        "theme": theme,
        "template_id": template_id,
        "missing_fields": missing_fields or [],
        "missing_assets": missing_assets or [],
        "pending_confirmations": pending_confirmations or [],
        "policy": {
            "no_fake_packaging": True,
            "no_invented_medical_claims": True,
            "forbid_system_tts_for_final_narration": True,
        },
    }


def gap_list_to_markdown(gap: dict[str, Any]) -> str:
    lines = [
        f"# 缺口清单 · {gap.get('theme', '')}",
        "",
        f"- 模板：`{gap.get('template_id', '')}`",
        f"- schema：`{gap.get('schema', '')}`",
        "",
        "## 待确认字段",
        "",
    ]
    fields = gap.get("missing_fields") or []
    if not fields:
        lines.append("- （无）")
    else:
        for f in fields:
            lines.append(f"- [ ] {f}")
    lines.extend(["", "## 素材缺口", ""])
    assets = gap.get("missing_assets") or []
    if not assets:
        lines.append("- （无）")
    else:
        for a in assets:
            role = a.get("role") or a.get("slot") or "素材"
            note = a.get("note") or a.get("status") or "待补"
            lines.append(f"- [ ] **{role}**：{note}")
    lines.extend(["", "## 待业务确认表述", ""])
    pend = gap.get("pending_confirmations") or []
    if not pend:
        lines.append("- （无）")
    else:
        for p in pend:
            lines.append(f"- [ ] {p}")
    lines.extend(
        [
            "",
            "## 硬策略（不可突破）",
            "",
            "- 无授权包装 → 槽位「待补」，禁止 AI 仿品牌包装",
            "- 无审核医学结论 → 标「待确认」，禁止编造",
            "- 视频正式旁白 → 模板克隆药师声，禁止系统机器人音色",
            "",
        ]
    )
    return "\n".join(lines)
