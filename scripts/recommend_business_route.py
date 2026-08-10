#!/usr/bin/env python3
"""Recommend an active business route from plain-language business intent.

The selector contract describes intent and reusable gold-lineage capabilities only.
Route availability, deliverable, environment requirements and gates are always read
live from ``production-library/business-routes.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SELECTOR_PATH = ROOT / "production-library" / "business-route-selector.json"
ROUTES_PATH = ROOT / "production-library" / "business-routes.json"

STRONG_WEIGHT = 10
SUPPORTING_WEIGHT = 2
NEGATIVE_WEIGHT = 6

ROUTE_TRUTH_FIELDS = {
    "active",
    "gates",
    "env_require",
    "adapter",
    "qa_profile",
    "delivery_whitelist",
    "name_zh",
    "deliverable",
    "deliverable_zh",
}


class SelectorContractError(ValueError):
    """The intent contract cannot be joined safely with route truth."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(char for char in normalized if not char.isspace())


def _contains_any(text: str, signals: list[str]) -> bool:
    return any(normalize(signal) in text for signal in signals)


def _matched(text: str, signals: list[str]) -> list[str]:
    return [signal for signal in signals if normalize(signal) in text]


def _route_map(routes_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    routes = routes_doc.get("routes") or []
    route_map = {
        str(route.get("route_id")): route
        for route in routes
        if str(route.get("route_id") or "").strip()
    }
    if len(route_map) != len(routes):
        raise SelectorContractError("business-routes.json 存在空或重复 route_id")
    return route_map


def validate_contract(
    selector_doc: dict[str, Any], routes_doc: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    route_map = _route_map(routes_doc)
    profiles = selector_doc.get("profiles") or []
    if not profiles:
        raise SelectorContractError("selector 缺少 profiles")

    profile_map: dict[str, dict[str, Any]] = {}
    route_profile_map: dict[str, dict[str, Any]] = {}
    required = {
        "profile_id",
        "route_id",
        "business_intent_zh",
        "family",
        "structure_mode",
        "page_count",
        "gold_lineage",
        "reusable_capabilities",
        "signals",
        "explanation_zh",
    }
    for profile in profiles:
        missing = sorted(required - set(profile))
        if missing:
            raise SelectorContractError(
                f"selector profile 缺少字段: {profile.get('profile_id')}: {missing}"
            )
        duplicated_truth = sorted(ROUTE_TRUTH_FIELDS.intersection(profile))
        if duplicated_truth:
            raise SelectorContractError(
                f"selector 不得复制 route 真值: {profile['profile_id']}: {duplicated_truth}"
            )
        profile_id = str(profile["profile_id"])
        route_id = str(profile["route_id"])
        if profile_id in profile_map:
            raise SelectorContractError(f"重复 profile_id: {profile_id}")
        if route_id in route_profile_map:
            raise SelectorContractError(f"一个 route 绑定了多个 selector profile: {route_id}")
        if route_id not in route_map:
            raise SelectorContractError(
                f"selector 指向 business-routes.json 中不存在的 route: {route_id}"
            )
        page_count = profile.get("page_count") or {}
        if page_count.get("mode") not in {"dynamic", "fixed"}:
            raise SelectorContractError(f"非法 page_count.mode: {profile_id}")
        if page_count.get("mode") == "fixed" and not isinstance(
            page_count.get("fixed"), int
        ):
            raise SelectorContractError(f"固定结构必须给出整数页/段数: {profile_id}")
        reusable = profile.get("reusable_capabilities") or {}
        if not all(key in reusable for key in ("page_types", "evidence", "scenes")):
            raise SelectorContractError(
                f"reusable_capabilities 必须含 page_types/evidence/scenes: {profile_id}"
            )
        signals = profile.get("signals") or {}
        if not all(
            isinstance(signals.get(key), list)
            for key in ("strong", "supporting", "negative")
        ):
            raise SelectorContractError(
                f"signals 必须含 strong/supporting/negative 数组: {profile_id}"
            )
        profile_map[profile_id] = profile
        route_profile_map[route_id] = profile

    for rule in selector_doc.get("ambiguity_rules") or []:
        candidates = rule.get("candidate_route_ids") or []
        if len(candidates) != 2:
            raise SelectorContractError(
                f"歧义规则必须恰好返回两个候选: {rule.get('rule_id')}"
            )
        unknown = [route_id for route_id in candidates if route_id not in route_profile_map]
        if unknown:
            raise SelectorContractError(
                f"歧义规则引用未知 selector route: {rule.get('rule_id')}: {unknown}"
            )
        if not str(rule.get("question_zh") or "").strip():
            raise SelectorContractError(
                f"歧义规则缺少一个追问: {rule.get('rule_id')}"
            )
    return route_map, route_profile_map


def _doctor_command(route_id: str, env_require: list[str]) -> str:
    if env_require == ["pptx_export"]:
        return "python3 scripts/probe_production_env.py --require pptx"
    return f"python3 scripts/business_doctor.py --route {route_id}"


def _start_draft_command(route_id: str) -> str:
    if route_id == "product-pptx-component-v1":
        return (
            "python3 scripts/business_job.py new "
            f"--route {route_id} --theme <主题> "
            "--script-json <WorkBuddy内部生成并经业务确认的脚本.json> "
            "--auto-draft"
        )
    return (
        "python3 scripts/business_job.py new "
        f"--route {route_id} --theme <主题> --notes '<业务资料或要求>' --auto-draft"
    )


def _candidate(
    *,
    profile: dict[str, Any],
    route: dict[str, Any],
    capabilities: dict[str, bool] | None,
    matched_signals: dict[str, list[str]] | None = None,
    reason_zh: str | None = None,
) -> dict[str, Any]:
    route_id = str(route["route_id"])
    active = bool(route.get("active"))
    env_require = list(route.get("env_require") or [])
    if capabilities is None:
        missing: list[str] = []
        render_readiness = "not_checked"
        can_render: bool | None = None
    else:
        missing = [name for name in env_require if not capabilities.get(name, False)]
        render_readiness = "blocked" if missing else "ready"
        can_render = active and not missing

    return {
        "profile_id": profile["profile_id"],
        "route_id": route_id,
        "name_zh": route.get("name_zh"),
        "deliverable": route.get("deliverable"),
        "deliverable_zh": route.get("deliverable_zh"),
        "active": active,
        "can_start_draft": active,
        "can_render": can_render,
        "render_readiness": "inactive" if not active else render_readiness,
        "env_require": env_require,
        "missing_capabilities": missing,
        "doctor_command": _doctor_command(route_id, env_require),
        "start_draft_command": _start_draft_command(route_id) if active else None,
        "family": profile["family"],
        "structure_mode": profile["structure_mode"],
        "page_count": profile["page_count"],
        "gold_lineage": profile["gold_lineage"],
        "reusable_capabilities": profile["reusable_capabilities"],
        "matched_signals": matched_signals or {},
        "why_zh": reason_zh or profile["explanation_zh"],
    }


def _ambiguity_match(rule: dict[str, Any], text: str) -> bool:
    signals = rule.get("signals") or {}
    required_any = list(signals.get("required_any") or [])
    absent_all = list(signals.get("absent_all") or [])
    return (
        (not required_any or _contains_any(text, required_any))
        and not _contains_any(text, absent_all)
    )


def _score_profile(profile: dict[str, Any], text: str) -> dict[str, Any]:
    signals = profile.get("signals") or {}
    strong = _matched(text, list(signals.get("strong") or []))
    supporting = _matched(text, list(signals.get("supporting") or []))
    negative = _matched(text, list(signals.get("negative") or []))
    score = (
        len(strong) * STRONG_WEIGHT
        + len(supporting) * SUPPORTING_WEIGHT
        - len(negative) * NEGATIVE_WEIGHT
    )
    return {
        "profile": profile,
        "score": score,
        "matched": {
            "strong": strong,
            "supporting": supporting,
            "negative": negative,
        },
    }


def _result_for_ambiguity(
    *,
    text: str,
    route_ids: list[str],
    question_zh: str,
    explanation_zh: str,
    route_map: dict[str, dict[str, Any]],
    profile_map: dict[str, dict[str, Any]],
    capabilities: dict[str, bool] | None,
) -> dict[str, Any]:
    candidates = [
        _candidate(
            profile=profile_map[route_id],
            route=route_map[route_id],
            capabilities=capabilities,
            reason_zh=explanation_zh,
        )
        for route_id in route_ids
    ]
    return {
        "schema": "business-route-recommendation-v1",
        "query": text,
        "decision": "needs_clarification",
        "recommendation": None,
        "candidates": candidates,
        "question_zh": question_zh,
        "explanation_zh": explanation_zh,
        "route_truth_source": str(ROUTES_PATH.relative_to(ROOT)),
        "environment_checked": capabilities is not None,
    }


def recommend(
    text: str,
    *,
    selector_doc: dict[str, Any] | None = None,
    routes_doc: dict[str, Any] | None = None,
    capabilities: dict[str, bool] | None = None,
) -> dict[str, Any]:
    selector_doc = selector_doc or load_json(SELECTOR_PATH)
    routes_doc = routes_doc or load_json(ROUTES_PATH)
    route_map, profile_map = validate_contract(selector_doc, routes_doc)
    raw_text = str(text or "").strip()
    if not raw_text:
        raise ValueError("业务需求不能为空")
    normalized = normalize(raw_text)

    for rule in selector_doc.get("ambiguity_rules") or []:
        if _ambiguity_match(rule, normalized):
            return _result_for_ambiguity(
                text=raw_text,
                route_ids=list(rule["candidate_route_ids"]),
                question_zh=str(rule["question_zh"]),
                explanation_zh=str(rule.get("explanation_zh") or "业务意图存在歧义"),
                route_map=route_map,
                profile_map=profile_map,
                capabilities=capabilities,
            )

    ranked = [
        _score_profile(profile, normalized)
        for profile in selector_doc.get("profiles") or []
    ]
    ranked = [entry for entry in ranked if entry["score"] > 0]
    ranked.sort(
        key=lambda entry: (
            -entry["score"],
            route_map[entry["profile"]["route_id"]].get("priority", 999),
            entry["profile"]["route_id"],
        )
    )

    if not ranked:
        return {
            "schema": "business-route-recommendation-v1",
            "query": raw_text,
            "decision": "no_match",
            "recommendation": None,
            "candidates": [],
            "question_zh": "请补充：要做普通商品培训 PPT、指定固定页数课型，还是完整商品 MP4？",
            "explanation_zh": "当前描述没有命中可执行的业务路线信号，未擅自选择默认路线。",
            "route_truth_source": str(ROUTES_PATH.relative_to(ROOT)),
            "environment_checked": capabilities is not None,
        }

    strong_matches = [
        entry for entry in ranked if entry["matched"].get("strong")
    ]
    if len(strong_matches) >= 2:
        top_two = strong_matches[:2]
        route_ids = [entry["profile"]["route_id"] for entry in top_two]
        names = [str(route_map[route_id].get("name_zh") or route_id) for route_id in route_ids]
        return _result_for_ambiguity(
            text=raw_text,
            route_ids=route_ids,
            question_zh=f"您要采用“{names[0]}”，还是“{names[1]}”？",
            explanation_zh="描述同时命中两个已定义课型的强信号，需要先确认结构。",
            route_map=route_map,
            profile_map=profile_map,
            capabilities=capabilities,
        )

    winner = ranked[0]
    profile = winner["profile"]
    route = route_map[profile["route_id"]]
    candidate = _candidate(
        profile=profile,
        route=route,
        capabilities=capabilities,
        matched_signals=winner["matched"],
    )
    if not candidate["active"]:
        decision = "route_inactive"
        explanation = "意图匹配该路线，但 business-routes.json 当前未激活，不能创建正式业务任务。"
    elif candidate["render_readiness"] == "blocked":
        decision = "env_blocked"
        explanation = (
            "路线已激活，可先建草稿；当前环境缺少正式渲染能力："
            + "、".join(candidate["missing_capabilities"])
            + "。"
        )
    else:
        decision = "recommended"
        explanation = profile["explanation_zh"]

    return {
        "schema": "business-route-recommendation-v1",
        "query": raw_text,
        "decision": decision,
        "recommendation": candidate,
        "candidates": [candidate],
        "question_zh": None,
        "explanation_zh": explanation,
        "route_truth_source": str(ROUTES_PATH.relative_to(ROOT)),
        "environment_checked": capabilities is not None,
    }


def _probe_capabilities() -> dict[str, bool]:
    if str(ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "scripts"))
    import probe_production_env as probe  # type: ignore

    report = probe.probe()
    return {
        str(name): bool(ready)
        for name, ready in (report.get("capabilities") or {}).items()
    }


def _print_human(result: dict[str, Any]) -> None:
    if result["decision"] == "needs_clarification":
        print("需要确认后再选路线：")
        for index, candidate in enumerate(result["candidates"], start=1):
            count = candidate["page_count"]
            count_text = (
                count.get("description_zh")
                or (str(count.get("fixed")) if count.get("mode") == "fixed" else "动态")
            )
            print(
                f"  {index}. {candidate['name_zh']} [{candidate['route_id']}] · {count_text}"
            )
            if not candidate["active"]:
                print("     当前状态：未激活，不能创建正式任务")
        print(f"追问：{result['question_zh']}")
        return

    candidate = result.get("recommendation")
    if candidate is None:
        print(result["explanation_zh"])
        if result.get("question_zh"):
            print(f"追问：{result['question_zh']}")
        return

    print(f"推荐：{candidate['name_zh']} [{candidate['route_id']}]")
    print(f"原因：{result['explanation_zh']}")
    print(
        f"结构：{candidate['structure_mode']} · {candidate['page_count'].get('description_zh')}"
    )
    if not candidate["active"]:
        print("状态：路线未激活，不能创建正式业务任务。")
        return
    if candidate["render_readiness"] == "not_checked":
        print("环境：尚未检查；推荐成立不等于本机现在可正式渲染。")
        print(f"先检查：{candidate['doctor_command']}")
    elif candidate["render_readiness"] == "blocked":
        print("环境：缺少 " + "、".join(candidate["missing_capabilities"]))
        print(f"修复/复查：{candidate['doctor_command']}")
    else:
        print("环境：已检查，满足该路线的渲染要求。")
    print(f"可先建内容草稿：{candidate['start_draft_command']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="根据业务自然语言推荐正式 business route；不复制或覆盖路由真值。"
    )
    parser.add_argument("request", nargs="?", help="业务需求，例如：做绿色五页商品培训PPT")
    parser.add_argument("--text", help="业务需求；与位置参数二选一")
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="实际探测本机环境；默认只列出路由要求并明确标记未检查",
    )
    parser.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = parser.parse_args(argv)
    if args.request and args.text:
        parser.error("位置参数与 --text 只能使用一个")
    text = args.text or args.request
    if not text:
        parser.error("请提供业务需求文本")

    capabilities = _probe_capabilities() if args.check_env else None
    try:
        result = recommend(text, capabilities=capabilities)
    except (OSError, json.JSONDecodeError, SelectorContractError, ValueError) as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "schema": "business-route-recommendation-v1",
                        "decision": "contract_error",
                        "error_zh": str(exc),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"路线推荐失败：{exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result["decision"] == "recommended" else 2


if __name__ == "__main__":
    raise SystemExit(main())
