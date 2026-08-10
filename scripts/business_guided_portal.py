#!/usr/bin/env python3
"""Business portal for settled courseware and gated production modes.

Template capability comes from business routes. Prompt/digital-human modes use a
separate machine-readable catalog so they never masquerade as local PPTX/MP4 routes.
The primary workflow remains conversational with WorkBuddy after installation.
"""

from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path


def extract_docx_paragraphs(path: Path, *, max_paras: int = 80) -> list[str]:
    """Plain paragraphs from a business filled-example docx."""
    try:
        from docx import Document
    except ImportError as exc:
        raise SystemExit("python-docx required to embed fill examples") from exc
    if not path.is_file():
        return []
    doc = Document(str(path))
    out: list[str] = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if not t:
            continue
        out.append(t)
        if len(out) >= max_paras:
            break
    return out


def _is_heading_line(text: str) -> bool:
    if len(text) > 28:
        return False
    if text.endswith(("。", "；", "!", "？", "?", "…")):
        return False
    # section-like titles
    if text.endswith(("：", ":")) and len(text) <= 20:
        return True
    if text in {
        "商品介绍",
        "核心卖点",
        "适宜人群",
        "联合用药话术",
        "注意事项",
        "课程小结",
        "什么是风热证",
        "典型表现",
        "调理思路",
        "日常注意事项",
        "问题引入",
        "基本概念与典型表现",
        "商品基础信息",
        "核心知识",
        "适宜人群与联合方案",
        "为什么要了解辅酶 Q10",
        "一、疾病篇",
        "二、商品介绍",
        "课程基本信息",
    }:
        return True
    # short title without period
    return len(text) <= 16 and "｜" not in text and "。" not in text


def paragraphs_to_html_blocks(paragraphs: list[str]) -> str:
    """Render example paras as safe HTML (headings + body)."""
    parts: list[str] = []
    for i, raw in enumerate(paragraphs):
        t = html.escape(raw)
        is_disclaimer = any(
            k in raw
            for k in (
                "填写参考",
                "真实已填",
                "样本",
                "仅用于",
                "不代表",
                "审核终稿",
                "演示占位",
            )
        )
        if i == 0 or is_disclaimer:
            parts.append(f'<p class="ex-note">{t}</p>')
        elif _is_heading_line(raw):
            parts.append(f"<h4>{t}</h4>")
        else:
            parts.append(f"<p>{t}</p>")
    return "\n".join(parts) if parts else '<p class="ex-note">暂无填写示例正文。</p>'


DEFAULT_GENERAL_TEMPLATE = "product-courseware-component-v1"
COMPONENT_PORTAL_COPY = {
    "name_zh": "灵活构件商品培训 PPT（兜底）",
    "one_liner": "未命中 5/18/13/20 页固定课型时使用；按审核大纲动态编排",
    "gallery_title_zh": "灵活构件商品培训 · 兜底路线",
}
COMPONENT_PAGE_TYPE_LABELS_ZH = {
    "cover": "商品封面",
    "courseware_cover": "封面",
    "hook": "问题引入",
    "hook_intro": "培训导语",
    "hook_pain_data": "痛点与数据",
    "pain-map": "需求痛点",
    "pain_map": "需求痛点",
    "product-overview": "商品信息总览",
    "product_overview": "商品信息总览",
    "composition-map": "商品信息总览",
    "composition_map": "商品信息总览",
    "ingredient-proof": "成分与证据",
    "ingredient_proof": "成分与证据",
    "evidence-ladder": "证据阶梯",
    "evidence_ladder": "证据阶梯",
    "benefit-chain": "利益链路",
    "benefit_chain": "利益链路",
    "audience": "适宜人群",
    "disease-bridge": "疾病知识衔接",
    "disease_bridge": "疾病知识衔接",
    "scenario": "门店场景",
    "recommendation": "咨询框架",
    "consultation-framework": "咨询框架",
    "consultation_framework": "咨询框架",
    "objection-handling": "异议应答",
    "objection_handling": "异议应答",
    "precautions": "注意事项",
    "new-comparison-matrix": "对比矩阵（新增页型）",
    "new_comparison_matrix": "对比矩阵（新增页型）",
    "action-checklist": "行动清单",
    "action_checklist": "行动清单",
    "summary": "课程总结",
    "summary_matrix": "总结回顾",
}


def _component_page_type_label_zh(page_type: object) -> str:
    return COMPONENT_PAGE_TYPE_LABELS_ZH.get(str(page_type), "自定义页签")


def _component_preview_suite_for_portal(raw: object) -> dict | None:
    """Strip internal UAT/style/page-type identifiers from business-facing JSON."""
    if not isinstance(raw, dict) or not isinstance(raw.get("cases"), list):
        return None
    cases: list[dict] = []
    for case in raw["cases"]:
        if not isinstance(case, dict):
            return None
        suite_slot = str(case.get("suite_slot") or "")
        name_zh = str(case.get("name_zh") or "构件业务验收案例")
        try:
            page_count = int(case.get("page_count") or 0)
            portal_media_index = int(case.get("portal_media_index") or 0)
            representative_page_number = int(
                case.get("representative_page_number") or 0
            )
        except (TypeError, ValueError):
            return None
        if (
            not (len(suite_slot) == 1 and "A" <= suite_slot <= "Z")
            or page_count <= 0
            or portal_media_index <= 0
            or not 1 <= representative_page_number <= page_count
        ):
            return None
        source_labels = [
            str(label) for label in case.get("source_capability_labels_zh") or []
        ]
        sequence_labels = [
            _component_page_type_label_zh(page_type)
            for page_type in case.get("page_type_sequence") or []
        ]
        new_page_type_labels = [
            _component_page_type_label_zh(page_type)
            for page_type in case.get("new_page_types") or []
        ]
        representative_page_type_label = _component_page_type_label_zh(
            case.get("representative_page_type")
        )
        minimum_pages = {"A": 7, "B": 6, "C": 5}.get(suite_slot, 5)
        if (
            len(sequence_labels) != page_count
            or not source_labels
            or page_count < minimum_pages
        ):
            return None
        source_text = " / ".join(source_labels)
        sequence_text = " → ".join(sequence_labels)
        new_text = (
            " / ".join(new_page_type_labels)
            or "本案例无；suite 其他案例已提供新增页型证据"
        )
        cases.append(
            {
                "suite_slot": suite_slot,
                "name_zh": name_zh,
                "page_count": page_count,
                "tab_label_zh": f"案例 {suite_slot} · {name_zh} · {page_count} 页",
                "title_zh": (
                    f"案例 {suite_slot} · {name_zh} · {page_count} 页｜"
                    f"页序：{sequence_text}｜来源：{source_text}｜新增页型：{new_text}"
                ),
                "source_capability_labels_zh": source_labels,
                "page_type_sequence_labels_zh": sequence_labels,
                "new_page_type_labels_zh": new_page_type_labels,
                "representative_page_label_zh": (
                    f"第 {representative_page_number} 页 · "
                    f"{representative_page_type_label}"
                ),
                "portal_media_index": portal_media_index,
            }
        )
    slots = [case["suite_slot"] for case in cases]
    media_indices = [case["portal_media_index"] for case in cases]
    if (
        len(cases) < 3
        or not {"A", "B", "C"}.issubset(slots)
        or len(slots) != len(set(slots))
        or len(media_indices) != len(set(media_indices))
        or not any(case["new_page_type_labels_zh"] for case in cases)
    ):
        return None
    capability_labels = list(
        dict.fromkeys(
            label
            for case in cases
            for label in case["source_capability_labels_zh"]
        )
    )
    suite_new_page_type_labels = list(
        dict.fromkeys(
            label
            for case in cases
            for label in case["new_page_type_labels_zh"]
        )
    )
    return {
        "case_count": len(cases),
        "style_label_zh": "统一浅蓝商品培训视觉",
        "settled_capability_labels_zh": capability_labels,
        "new_page_type_labels_zh": suite_new_page_type_labels,
        "cases": cases,
    }


SIGNED_STANDARD_TEMPLATES = frozenset(
    {
        "product-courseware-green-v1",
        "disease-product-scenario-v1",
        "sufuda-mabaloshawei-product-courseware-3-v1",
        "kangaisen-lycopene-health-edu-v1",
    }
)
SHELF_GROUPS = (
    {
        "id": "default-general",
        "title": "灵活构件兜底",
        "hint": "未命中已签样固定课型时使用；按已确认内容动态编排可编辑课件。",
    },
    {
        "id": "signed-standard",
        "title": "已签样标准课型",
        "hint": "金样、结构与填写参考可复用；每种交付物是否可生成，以卡片上的实时状态为准。",
    },
    {
        "id": "production-modes",
        "title": "动画与数字人制作模式",
        "hint": "这里选择制作流程，不替代课型；WorkBuddy 先交复核包，确认后才放行提示词或外部制作。",
    },
    {
        "id": "other",
        "title": "其他课型",
        "hint": "按培训目的选择；没有激活生产路线的课型只开放金样参考。",
    },
)

DELIVERABLE_LABELS = {
    "pptx": "PPTX",
    "mp4": "MP4",
    "preview": "金样预览",
}
RUNTIME_CAPABILITY_NAMES = {
    "pptx_export",
    "video_full",
    "video_tts",
    "video_render",
}
BUSINESS_MODES_PATH = (
    Path(__file__).resolve().parents[1]
    / "production-library"
    / "business-modes.json"
)
BUSINESS_MODES_SCHEMA = "business-production-mode-catalog-v1"
BUSINESS_ROUTE_SELECTOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "production-library"
    / "business-route-selector.json"
)

_DEFAULT_ROUTE_SELECTOR = {
    "title_zh": "我不懂模板，帮我选",
    "description_zh": (
        "只选交付物、内容类型和结构偏好，或直接粘贴业务需求。"
        "WorkBuddy 会先解释推荐与原因；你确认模板前不会创建任务。"
    ),
    "deliverables": [
        {"value": "unsure", "label_zh": "不确定，帮我判断"},
        {"value": "pptx", "label_zh": "可编辑 PPTX"},
        {"value": "mp4", "label_zh": "完整 MP4"},
    ],
    "content_types": [
        {"value": "unsure", "label_zh": "不确定，按需求判断"},
        {"value": "product-training", "label_zh": "单品商品培训"},
        {"value": "disease-product-scenario", "label_zh": "疾病 + 商品 + 场景演练"},
        {"value": "ingredient-health-edu", "label_zh": "成分健康科普"},
        {"value": "product-video", "label_zh": "商品培训视频"},
    ],
    "structures": [
        {"value": "unsure", "label_zh": "不确定，帮我推荐"},
        {"value": "dynamic", "label_zh": "动态页数 · 灵活构件兜底 PPT"},
        {"value": "fixed-5", "label_zh": "固定 5 页 · 绿色紧凑课"},
        {"value": "fixed-18", "label_zh": "固定 18 页 · 疾病商品场景课"},
        {"value": "fixed-13", "label_zh": "固定 13 页 · 专项商品讲解"},
        {"value": "fixed-20", "label_zh": "固定 20 页 · 成分健康科普"},
    ],
    "boundaries": [
        {
            "title_zh": "动态页数",
            "detail_zh": "灵活构件兜底 · 可编辑 PPTX；未命中固定课型时按确认内容组织页数。",
        },
        {
            "title_zh": "固定 5 页",
            "detail_zh": "绿色紧凑商品培训 · 可编辑 PPTX。",
        },
        {
            "title_zh": "固定 18 页",
            "detail_zh": "疾病 + 商品 + 场景演练 · 可编辑 PPTX。",
        },
        {
            "title_zh": "固定 13 页",
            "detail_zh": "专项商品讲解 · 当前只承诺 PPTX，MP4 尚未开放。",
        },
        {
            "title_zh": "固定 20 页",
            "detail_zh": "成分健康科普 · 可编辑 PPTX。",
        },
        {
            "title_zh": "完整 MP4",
            "detail_zh": (
                "走固定 8 段商品培训视频路线（不是 PPT 页数）；"
                "固定页 PPT 课型不等于同时生成视频。"
            ),
        },
    ],
}

_ROUTE_SELECTOR_PROMPT_TEMPLATE = """我不懂模板，请先让 WorkBuddy 调用已安装项目的 business_job recommend 只读推荐能力，不要直接创建任务。工具结果只用于判断，不要原样回显内部路线标识、脚本命令或建草稿命令：
- 交付物：[[DELIVERABLE]]
- 内容类型：[[CONTENT_TYPE]]
- 结构偏好：[[STRUCTURE]]
- 补充需求：[[REQUIREMENT]]

请先只输出：
1. 推荐模板（最多 2 个候选）；
2. 每个候选的推荐理由；
3. 各候选实际可生成的交付物（PPTX / MP4）与页数规则（动态页数或固定页数）；
4. 仍需补充或确认的内容。

如我的偏好与当前生产能力冲突，请明确说明，不要承诺不存在的 PPTX 或 MP4；如有两个候选，只追问一个最关键的问题。
在我明确回复“确认模板【模板名】”之前，不得创建任务、不得生成正式成品。"""


def _default_route_selector() -> dict:
    """Return an isolated copy so a caller cannot mutate the fallback."""
    return json.loads(json.dumps(_DEFAULT_ROUTE_SELECTOR, ensure_ascii=False))


def _selector_option_list(value: object) -> list[dict[str, str]]:
    if isinstance(value, dict):
        value = value.get("options") or value.get("values") or []
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for raw in value:
        if isinstance(raw, str):
            option_value = raw.strip()
            label = option_value
        elif isinstance(raw, dict):
            option_value = str(
                raw.get("value") or raw.get("id") or raw.get("key") or ""
            ).strip()
            label = str(
                raw.get("label_zh")
                or raw.get("label")
                or raw.get("name_zh")
                or raw.get("name")
                or ""
            ).strip()
        else:
            continue
        if option_value and label:
            out.append({"value": option_value, "label_zh": label})
    return out


def _merge_selector_options(
    defaults: list[dict[str, str]], configured: object
) -> list[dict[str, str]]:
    """Allow display-label overrides, but never expose selector route profiles."""
    configured_by_value = {
        option["value"]: option for option in _selector_option_list(configured)
    }
    return [
        configured_by_value.get(option["value"], dict(option))
        for option in defaults
    ]


def load_business_route_selector(path: Path | None = None) -> dict:
    """Load portal-safe intent labels; route IDs remain server-side truth."""
    selector = _default_route_selector()
    catalog_path = path or BUSINESS_ROUTE_SELECTOR_PATH
    if not catalog_path.is_file():
        return selector
    try:
        doc = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return selector
    if not isinstance(doc, dict):
        return selector

    portal = doc.get("portal") if isinstance(doc.get("portal"), dict) else {}
    intent: dict = {}
    for key in ("options", "intent_options", "intent"):
        if isinstance(doc.get(key), dict):
            intent.update(doc[key])
    if isinstance(portal.get("intent"), dict):
        intent = {**intent, **portal["intent"]}
    if isinstance(intent.get("options"), dict):
        intent = {**intent["options"], **intent}

    title = portal.get("title_zh") or doc.get("title_zh")
    description = portal.get("description_zh") or doc.get("description_zh")
    if isinstance(title, str) and title.strip():
        selector["title_zh"] = title.strip()
    if isinstance(description, str) and description.strip():
        selector["description_zh"] = description.strip()

    sources = {
        "deliverables": (
            intent.get("deliverables")
            or intent.get("deliverable")
            or portal.get("deliverables")
            or doc.get("deliverables")
        ),
        "content_types": (
            intent.get("content_types")
            or intent.get("content_type")
            or portal.get("content_types")
        ),
        "structures": (
            intent.get("structure_preferences")
            or intent.get("structure_preference")
            or intent.get("structures")
            or intent.get("structure_mode")
            or portal.get("structure_preferences")
            or portal.get("structures")
        ),
    }
    for key, configured in sources.items():
        if configured:
            selector[key] = _merge_selector_options(selector[key], configured)
    return selector


def build_route_selector_prompt(
    deliverable: str,
    content_type: str,
    structure: str,
    requirement: str = "",
) -> str:
    values = {
        "[[DELIVERABLE]]": deliverable.strip() or "不确定，帮我判断",
        "[[CONTENT_TYPE]]": content_type.strip() or "不确定，按需求判断",
        "[[STRUCTURE]]": structure.strip() or "不确定，帮我推荐",
        "[[REQUIREMENT]]": requirement.strip() or "暂无；请根据以上选择先推荐",
    }
    prompt = _ROUTE_SELECTOR_PROMPT_TEMPLATE
    for marker, value in values.items():
        prompt = prompt.replace(marker, value)
    return prompt


def load_business_modes(path: Path | None = None) -> list[dict]:
    """Load the production-mode shelf without mixing it into route truth."""
    catalog_path = path or BUSINESS_MODES_PATH
    doc = json.loads(catalog_path.read_text(encoding="utf-8"))
    if doc.get("schema") != BUSINESS_MODES_SCHEMA:
        raise ValueError(f"unsupported business mode catalog schema: {doc.get('schema')}")
    modes = doc.get("modes")
    if not isinstance(modes, list):
        raise ValueError("business mode catalog must contain a modes list")
    required = {
        "mode_id",
        "name_zh",
        "one_liner",
        "prompt_only",
        "workbuddy_direct_generation",
        "input_quality_boundary",
        "local_artifact_types",
        "workbuddy_outputs",
        "badges",
        "approval_gate",
        "external_render",
        "workflow",
        "selection_command",
    }
    seen: set[str] = set()
    for mode in modes:
        missing = sorted(required.difference(mode))
        if missing:
            raise ValueError(
                f"business mode {mode.get('mode_id') or '<unknown>'} missing: "
                + ", ".join(missing)
            )
        mode_id = str(mode["mode_id"])
        if mode_id in seen:
            raise ValueError(f"duplicate business mode: {mode_id}")
        seen.add(mode_id)
    return modes


def _mode_example_paragraphs(mode: dict) -> list[str]:
    stage_labels = {
        "review": "确认前",
        "after_script_approval": "脚本确认后",
    }
    output_heading = (
        "WorkBuddy 可直接交付："
        if mode["workbuddy_direct_generation"]
        else "可用复核材料："
    )
    paragraphs = [output_heading]
    for output in mode["workbuddy_outputs"]:
        stage = stage_labels.get(str(output.get("stage") or ""), "按闸门")
        paragraphs.append(f"• {output['label']}（{stage}）。")
    gate = mode["approval_gate"]
    paragraphs.extend(
        [
            "输入完整性边界：",
            str(mode["input_quality_boundary"]),
            "确认闸门：",
            str(gate["before_approval_zh"]),
            f"确认口令：{gate['confirmation_phrase']}。",
            "外部出片边界：",
            str(mode["external_render"]["boundary_zh"]),
        ]
    )
    requirements = mode.get("production_requirements") or []
    if requirements:
        paragraphs.append("条件式制作依赖：")
        paragraphs.extend(f"• {requirement}。" for requirement in requirements)
    return paragraphs


def _enrich_business_mode(mode: dict) -> dict:
    paragraphs = _mode_example_paragraphs(mode)
    badges = [dict(item) for item in mode["badges"]]
    item = dict(mode)
    video_example = mode.get("portal_video_example") or {}
    item.update(
        {
            "name_zh": str(mode.get("portal_name_zh") or mode["name_zh"]),
            "slug": str(mode["mode_id"]),
            "portal_item_kind": "production_mode",
            "shelf_group": "production-modes",
            "outputs": [item["label"] for item in mode["workbuddy_outputs"]],
            "deliverable_badges": badges,
            "readiness_badge": badges[0],
            "portal_status_kind": badges[0]["kind"],
            "portal_status_label": "；".join(item["label"] for item in badges),
            "portal_status_note": str(mode["external_render"]["boundary_zh"]),
            "selection_command": str(mode["selection_command"]),
            "self_serve": bool(mode["workbuddy_direct_generation"]),
            "preview_steps": [dict(step) for step in mode["workflow"]],
            "key_frame_labels_zh": [],
            "example_paragraphs": paragraphs,
            "example_html": paragraphs_to_html_blocks(paragraphs),
            "portal_video_example": {
                "filename": str(video_example.get("filename") or ""),
                "label": str(video_example.get("label") or "效果案例"),
            }
            if video_example.get("filename")
            else None,
            "generated_prompt_example": str(
                mode.get("generated_prompt_example") or ""
            ),
        }
    )
    item.pop("portal_name_zh", None)
    return item


def _load_routes_by_template() -> dict[str, list[dict]]:
    """Load every configured route, grouped by template and ordered by priority."""
    routes_path = (
        Path(__file__).resolve().parents[1]
        / "production-library"
        / "business-routes.json"
    )
    if not routes_path.is_file():
        return {}
    try:
        doc = json.loads(routes_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, list[dict]] = {}
    for route in doc.get("routes") or []:
        slug = route.get("template_slug")
        if slug:
            out.setdefault(str(slug), []).append(route)
    for routes in out.values():
        routes.sort(key=lambda item: int(item.get("priority") or 9999))
    return out


def _active_routes_by_template(
    routes_by_template: dict[str, list[dict]] | None = None,
) -> dict[str, list[dict]]:
    if routes_by_template is None:
        routes_by_template = _load_routes_by_template()
    return {
        slug: [route for route in routes if route.get("active")]
        for slug, routes in routes_by_template.items()
        if any(route.get("active") for route in routes)
    }


def _load_active_routes_by_template() -> dict[str, list[dict]]:
    """Backward-compatible loader whose values retain all active routes."""
    return _active_routes_by_template()


def _route_deliverables(route: dict) -> list[str]:
    deliverable = str(route.get("deliverable") or "")
    if deliverable == "pptx_and_mp4":
        return ["pptx", "mp4"]
    if deliverable in DELIVERABLE_LABELS:
        return [deliverable]
    return []


def _active_deliverables(routes: list[dict]) -> list[str]:
    deliverables: list[str] = []
    for route in routes:
        if not route.get("active"):
            continue
        for deliverable in _route_deliverables(route):
            if deliverable not in deliverables:
                deliverables.append(deliverable)
    return deliverables


def shelf_group_for_template(template: dict) -> str:
    slug = str(template.get("slug") or "")
    if slug == DEFAULT_GENERAL_TEMPLATE:
        return "default-general"
    if slug in SIGNED_STANDARD_TEMPLATES:
        return "signed-standard"
    return "other"


def business_subject_for_template(template: dict) -> str:
    category = str(template.get("category") or "")
    if category == "商品培训":
        return "商品名"
    if category == "成分健康科普":
        return "成分或健康主题"
    return "病名或健康主题"


def build_job_command(template: dict, route: dict | None = None) -> str | None:
    """Agent-facing job CLI when a settled template is wired to business_job."""
    slug = str(template.get("slug") or "")
    if route is None:
        routes = _load_active_routes_by_template().get(slug) or []
        route = routes[0] if routes else None
    if not route:
        return None
    route_id = route["route_id"]
    subject = business_subject_for_template(template)
    gates = route.get("gates") or {}
    new_line = (
        f"python3 scripts/business_job.py new --route {route_id} "
        f"--theme 【{subject}】 --notes 【要点】"
    )
    if gates.get("product_image_approval"):
        new_line += " --product-image 【授权包装图路径】"
    lines = [
        new_line + " --auto-draft",
        "python3 scripts/business_job.py approve --job <任务ID> --gate content --by 【姓名】",
    ]
    if gates.get("product_image_approval"):
        lines.append(
            "python3 scripts/business_job.py approve --job <任务ID> --gate product_image "
            "--by 【姓名】 --authorization-reference 【凭证】"
        )
    if gates.get("visual_approval"):
        lines.append(
            "python3 scripts/business_job.py approve --job <任务ID> --gate visual "
            "--by 【姓名】 --note 【画面确认说明】"
        )
    lines.append("python3 scripts/business_job.py render --job <任务ID>")
    return "\n".join(lines)


def build_business_command(
    template: dict,
    *,
    routes_by_template: dict[str, list[dict]] | None = None,
) -> str:
    """Return a business-only prompt matching the actual deliverable.

    Internal route IDs and Python commands belong to WorkBuddy's system prompt,
    never to the text copied by business users from the template shelf.
    """
    name = template["name_zh"]
    slug = str(template.get("slug") or "")
    category = str(template.get("category") or "")
    subject = business_subject_for_template(template)
    if routes_by_template is None:
        routes_by_template = _load_routes_by_template()
    configured_routes = routes_by_template.get(slug) or []
    deliverables = _active_deliverables(configured_routes)
    can_pptx = "pptx" in deliverables
    can_mp4 = "mp4" in deliverables

    if not can_pptx and not can_mp4:
        if slug == "health-video-reference-tech-v1" and configured_routes:
            return (
                f"我选【{name}】，病名或健康主题是【请填写】，并提交已审核的 7 段内容要点。\n"
                "请先整理完整脚本、分镜和主题画面复核包，缺少的医学内容只列缺口；"
                "内容与全部画面确认后保留复核包。当前尚未开放，不能生成完整 MP4。"
            )
        if configured_routes or slug in SIGNED_STANDARD_TEMPLATES:
            return (
                f"我选【{name}】，当前状态是【尚未开放，当前不可生成】。\n"
                f"{subject}是【请填写】，已有要点是【请填写；资料不完整也可以】。"
                "请先按该金样结构整理内容初稿、待补字段和素材清单；"
                "不要承诺或生成正式成品，等卡片显示对应交付物可生成后再继续。"
            )
        return (
            f"我选【{name}】，目前仅查看金样和填写参考。"
            "请先告诉我这套模板还缺哪些换主题能力，不要生成正式成品。"
        )
    if slug == DEFAULT_GENERAL_TEMPLATE and can_pptx and not can_mp4:
        return (
            "我要制作一份【可编辑商品培训 PPTX】，采用灵活构件兜底；先不要锁定正式页序。\n"
            "自然语言交付目标：【请填写培训对象、使用场景和希望解决的问题】\n"
            "商品或主题：【请填写】\n"
            "现有内容：【直接粘贴已有文案、要点或资料摘要；不完整也可以】\n"
            "现有素材：【列出包装图、Logo、证据资料、品牌素材；没有的请写暂无】\n"
            "请先不要创建正式任务，也不要生成 PPTX。请先返回：\n"
            "1. 内容缺口和待确认字段；\n"
            "2. 全中文页签大纲：逐页写明中文页名、页面目标和拟放内容；\n"
            "3. 每页能力来源解释：说明借鉴了哪类已验证课型能力，或为什么需要自定义页签；\n"
            "4. 全套只使用一种主视觉的建议；\n"
            "5. 素材分工：哪些正式图片必须由业务提供，哪些插图可由系统生成。\n"
            "业务全程只用中文自然语言，不需要填写 JSON 或任何内部页型编号。"
            "等我明确确认中文页签大纲、每页来源解释和单一视觉后，"
            "再由 WorkBuddy 内部锁定页序、创建正式任务并生成可编辑 PPTX；确认前不得继续。"
        )
    if can_pptx and can_mp4:
        base = (
            f"我选【{name}】，需要【可编辑 PPTX / 完整 MP4，请保留我选择的一项】。\n"
            f"{subject}是【请填写】，审核要点是【要点1、要点2、要点3】。"
            "请先整理内容初稿和所需素材缺口供我确认；确认后再检查本机能力并生成正式成品。"
        )
    elif can_mp4:
        if slug == "product-video-faithful-v1":
            base = (
                f"我选【{name}】，商品名是【请填写】，并附上已获业务授权的商品包装图。\n"
                "审核要点是【要点1、要点2、要点3】。请先整理完整脚本和分镜、列出素材与授权缺口供我确认；"
                "确认后再检查本机能力并生成完整 MP4，不要跳过确认。"
            )
        elif slug == "health-video-reference-tech-v1":
            base = (
                f"我选【{name}】，病名或健康主题是【请填写】，并提交已审核的 7 段内容要点。\n"
                "请先整理完整脚本、分镜和主题画面复核包，缺少的医学内容只列缺口；"
                "内容与全部画面确认后，再检查本机能力并生成完整 MP4。"
            )
        else:
            base = (
                f"我选【{name}】，{subject}是【请填写】，审核要点是【要点1、要点2、要点3】。\n"
                "请先整理完整脚本和分镜、列出素材与授权缺口供我确认；"
                "确认后再检查本机能力并生成完整 MP4，不要跳过确认。"
            )
    else:
        base = (
            f"我选【{name}】，{subject}是【请填写】，审核要点是【要点1、要点2、要点3】。\n"
            "请先整理内容初稿和缺口供我确认；确认后再检查本机能力并生成可编辑 PPTX。"
        )

    return (
        base
        + f"\n我确认先锁定模板【{name}】。请在创建草稿前复述模板名称、交付物和还需补充的内容。"
    )


def deliverable_badges(
    template: dict,
    runtime_capabilities: dict[str, bool] | None = None,
    *,
    routes_by_template: dict[str, list[dict]] | None = None,
) -> list[dict[str, str]]:
    """Return one production status per active deliverable, never from catalog booleans."""
    slug = str(template.get("slug") or "")
    if routes_by_template is None:
        routes_by_template = _load_routes_by_template()
    configured_routes = routes_by_template.get(slug) or []
    active_routes = [route for route in configured_routes if route.get("active")]

    by_deliverable: dict[str, dict[str, str]] = {}
    for route in active_routes:
        required = [
            str(item)
            for item in route.get("env_require") or []
            if str(item) in RUNTIME_CAPABILITY_NAMES
        ]
        if runtime_capabilities is None and required:
            kind = "conditional"
            suffix = "生成前检查环境"
        else:
            missing = [
                item
                for item in required
                if runtime_capabilities is not None and not runtime_capabilities.get(item)
            ]
            if missing:
                kind = "conditional"
                suffix = "本机缺 " + "/".join(missing)
            else:
                kind = "ready"
                suffix = "可生成 · 仍需内容/素材确认"
        for deliverable in _route_deliverables(route):
            candidate = {
                "kind": kind,
                "label": f"{DELIVERABLE_LABELS[deliverable]} · {suffix}",
            }
            current = by_deliverable.get(deliverable)
            if current is None or (current["kind"] != "ready" and kind == "ready"):
                by_deliverable[deliverable] = candidate

    for route in configured_routes:
        if route.get("active"):
            continue
        for deliverable in _route_deliverables(route):
            by_deliverable.setdefault(
                deliverable,
                {
                    "kind": "building",
                    "label": f"{DELIVERABLE_LABELS[deliverable]} · 尚未开放（不可生成）",
                },
            )

    if by_deliverable:
        return [
            by_deliverable[key]
            for key in ("pptx", "mp4", "preview")
            if key in by_deliverable
        ]
    if configured_routes or slug in SIGNED_STANDARD_TEMPLATES:
        return [{"kind": "building", "label": "尚未开放（不可生成）"}]
    return [{"kind": "preview", "label": "仅金样预览"}]


def readiness_badge(
    template: dict,
    runtime_capabilities: dict[str, bool] | None = None,
    *,
    routes_by_template: dict[str, list[dict]] | None = None,
) -> dict[str, str]:
    badges = deliverable_badges(
        template,
        runtime_capabilities,
        routes_by_template=routes_by_template,
    )
    return badges[0]


def build_guided_portal_html(
    templates: list[dict],
    *,
    examples: dict[str, list[str]] | None = None,
    pack_date: str | None = None,
    runtime_capabilities: dict[str, bool] | None = None,
    production_modes: list[dict] | None = None,
) -> str:
    pack_date = pack_date or date.today().isoformat()
    examples = examples or {}
    if production_modes is None:
        production_modes = load_business_modes()
    route_selector = load_business_route_selector()

    # Enrich catalog for JS: paragraphs + pre-rendered HTML
    routes_by_template = _load_routes_by_template()
    active_routes = _active_routes_by_template(routes_by_template)
    enriched: list[dict] = []
    for t in templates:
        slug = t["slug"]
        paras = examples.get(slug) or []
        item = dict(t)
        if slug == DEFAULT_GENERAL_TEMPLATE:
            item.update(COMPONENT_PORTAL_COPY)
            item["preview_identity_qualified"] = (
                t.get("preview_identity_qualified") is True
            )
            item["preview_identity_note_zh"] = str(
                t.get("preview_identity_note_zh")
                or "至少 3 套正式差异化非金样 UAT suite 尚未通过 QA；为避免误认成课件4，门户暂不展示旧图。"
            )
            suite_evidence = t.get("preview_suite_evidence")
            item["preview_suite_evidence"] = (
                _component_preview_suite_for_portal(suite_evidence)
                if item["preview_identity_qualified"]
                and isinstance(suite_evidence, dict)
                else None
            )
        for stale_key in (
            "capabilities",
            "production_ready",
            "requirements",
            "blockers",
            "status_label",
            "status_note",
        ):
            item.pop(stale_key, None)
        item["example_paragraphs"] = paras
        item["example_html"] = paragraphs_to_html_blocks(paras)
        item["selection_command"] = build_business_command(
            item, routes_by_template=routes_by_template
        )
        item["portal_item_kind"] = "template"
        item["self_serve"] = bool(active_routes.get(slug))
        item["shelf_group"] = shelf_group_for_template(t)
        badges = deliverable_badges(
            t,
            runtime_capabilities,
            routes_by_template=routes_by_template,
        )
        item["deliverable_badges"] = badges
        item["readiness_badge"] = badges[0]
        item["portal_status_kind"] = badges[0]["kind"]
        if badges[0]["kind"] == "building":
            item["portal_status_label"] = "尚未开放 · 当前不可生成 · 金样可查看"
            item["portal_status_note"] = (
                "金样、关键页和填写参考可以复用；正式换主题生产路线尚未激活。"
            )
        elif badges[0]["kind"] == "preview":
            item["portal_status_label"] = "仅金样预览"
            item["portal_status_note"] = "当前仅用于辨认课型，不承诺生成新主题正式成品。"
        else:
            item["portal_status_label"] = "；".join(
                badge["label"] for badge in badges
            )
            item["portal_status_note"] = (
                "生产路线已激活；仍需按流程确认内容、正式素材和本机环境。"
            )
        if slug == DEFAULT_GENERAL_TEMPLATE:
            item["portal_status_note"] += " " + item["preview_identity_note_zh"]
        enriched.append(item)

    enriched_modes = [_enrich_business_mode(mode) for mode in production_modes]
    collisions = {item["slug"] for item in enriched}.intersection(
        item["slug"] for item in enriched_modes
    )
    if collisions:
        raise ValueError("portal slug collision: " + ", ".join(sorted(collisions)))
    catalog_js = json.dumps(enriched, ensure_ascii=False)
    modes_js = json.dumps(enriched_modes, ensure_ascii=False)
    groups_js = json.dumps(SHELF_GROUPS, ensure_ascii=False)
    selector_prompt_js = json.dumps(
        _ROUTE_SELECTOR_PROMPT_TEMPLATE, ensure_ascii=False
    )
    component_slug_js = json.dumps(DEFAULT_GENERAL_TEMPLATE, ensure_ascii=False)

    def selector_options_html(key: str) -> str:
        return "\n".join(
            '<option value="{}">{}</option>'.format(
                html.escape(str(option["value"]), quote=True),
                html.escape(str(option["label_zh"])),
            )
            for option in route_selector[key]
        )

    selector_boundaries_html = "\n".join(
        '<div class="selector-boundary"><b>{}</b><span>{}</span></div>'.format(
            html.escape(str(boundary["title_zh"])),
            html.escape(str(boundary["detail_zh"])),
        )
        for boundary in route_selector["boundaries"]
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>内部培训 · 选课型或制作模式</title>
<style>
:root {{
  --bg: #f4f6f9;
  --card: #fff;
  --text: #1a2332;
  --dim: #5c6b7e;
  --line: #e2e8f0;
  --accent: #1d4ed8;
  --accent-soft: #eff6ff;
  --ok: #047857;
  --ok-soft: #ecfdf5;
  --radius: 12px;
  --font: "PingFang SC","Microsoft YaHei","Noto Sans SC",system-ui,sans-serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font);
  color: var(--text);
  background: var(--bg);
  line-height: 1.5;
  min-height: 100vh;
}}
.shell {{ max-width: 1080px; margin: 0 auto; padding: 20px 16px 56px; }}
header {{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px 20px;
  margin-bottom: 16px;
}}
header h1 {{ font-size: 20px; font-weight: 800; margin-bottom: 6px; }}
header .sub {{ font-size: 13px; color: var(--dim); max-width: 70ch; }}
.how {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-top: 12px;
}}
@media (max-width: 900px) {{ .how {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 520px) {{ .how {{ grid-template-columns: 1fr; }} }}
.how div {{
  background: var(--accent-soft);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  color: var(--dim);
}}
.how b {{ display: block; color: var(--text); font-size: 13px; margin-bottom: 2px; }}
.how code {{
  font-family: ui-monospace, Menlo, monospace;
  font-size: 11px;
  background: #fff;
  border: 1px solid var(--line);
  padding: 1px 5px;
  border-radius: 4px;
  color: #1e3a8a;
  word-break: break-all;
}}
section.block {{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px 18px;
  margin-bottom: 14px;
}}
section.block h2 {{
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
section.block h2 .n {{
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--accent); color: #fff;
  font-size: 12px; display: inline-flex; align-items: center; justify-content: center;
}}
section.block > .hint {{ font-size: 12px; color: var(--dim); margin-bottom: 12px; }}

.route-selector {{
  border: 1px solid #bfdbfe;
  border-left: 4px solid var(--accent);
  background: var(--accent-soft);
  padding: 16px;
  margin: 4px 0 18px;
}}
.selector-head {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}}
.selector-eyebrow {{
  color: var(--accent);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .08em;
  margin-bottom: 2px;
}}
.selector-head h3 {{ font-size: 17px; line-height: 1.3; }}
.selector-head p {{ color: var(--dim); font-size: 12px; margin-top: 3px; max-width: 66ch; }}
.selector-gate {{
  flex: none;
  border: 1px solid #a7f3d0;
  background: var(--ok-soft);
  color: var(--ok);
  padding: 5px 8px;
  font-size: 10px;
  font-weight: 800;
}}
.selector-layout {{
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(250px, .75fr);
  gap: 14px;
}}
.selector-form-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
}}
.selector-field {{ display: block; min-width: 0; }}
.selector-field > span {{ display: block; font-size: 11px; font-weight: 800; margin-bottom: 4px; }}
.selector-field select,
.selector-field textarea {{
  width: 100%;
  border: 1px solid #bfdbfe;
  background: #fff;
  color: var(--text);
  font: inherit;
  font-size: 12px;
  padding: 8px 9px;
}}
.selector-field select {{ min-height: 38px; }}
.selector-field textarea {{ min-height: 90px; resize: vertical; line-height: 1.5; }}
.selector-field select:focus-visible,
.selector-field textarea:focus-visible {{ outline: 3px solid #93c5fd; outline-offset: 1px; }}
.selector-requirement {{ margin-top: 9px; }}
.selector-boundaries {{
  border-left: 1px solid #bfdbfe;
  padding-left: 14px;
}}
.selector-boundaries > b {{ display: block; font-size: 12px; margin-bottom: 6px; }}
.selector-boundary {{ display: grid; grid-template-columns: 72px 1fr; gap: 7px; padding: 5px 0; }}
.selector-boundary + .selector-boundary {{ border-top: 1px solid rgba(147,197,253,.45); }}
.selector-boundary b {{ font-size: 11px; }}
.selector-boundary span {{ color: var(--dim); font-size: 10px; }}
.selector-note {{ color: var(--dim); font-size: 11px; margin-top: 8px; }}
@media (max-width: 760px) {{
  .selector-head {{ display: block; }}
  .selector-gate {{ display: inline-block; margin-top: 8px; }}
  .selector-layout {{ grid-template-columns: minmax(0, 1fr); }}
  .selector-form-grid {{ grid-template-columns: minmax(0, 1fr); }}
  .selector-boundaries {{ border-left: 0; border-top: 1px solid #bfdbfe; padding: 12px 0 0; }}
}}

.template-group + .template-group {{
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}}
.template-group-head {{ margin-bottom: 8px; }}
.template-group-head h3 {{ font-size: 14px; font-weight: 800; }}
.template-group-head p {{ font-size: 11px; color: var(--dim); margin-top: 2px; }}
.grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}}
@media (max-width: 900px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 480px) {{ .grid {{ grid-template-columns: 1fr; }} }}
.tcard {{
  appearance: none;
  width: 100%;
  padding: 0;
  text-align: left;
  font: inherit;
  color: inherit;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  background: #fafbfc;
  cursor: pointer;
  transition: border-color .12s, box-shadow .12s;
}}
.tcard:hover {{ border-color: #93c5fd; }}
.tcard:focus-visible {{ outline: 3px solid #93c5fd; outline-offset: 2px; }}
.tcard.selected {{
  border-color: var(--ok);
  box-shadow: 0 0 0 2px rgba(4,120,87,.2);
  background: var(--ok-soft);
}}
.tcard img.cover {{
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
  background: #0f172a;
}}
.mode-cover {{
  aspect-ratio: 16/9;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 14px;
  color: #fff;
  background:
    radial-gradient(circle at 82% 18%, rgba(255,255,255,.28), transparent 28%),
    linear-gradient(135deg, #1e3a8a, #0f766e);
}}
.mode-cover span {{
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .08em;
  opacity: .78;
}}
.mode-cover strong {{ font-size: 20px; line-height: 1.15; margin-top: 3px; }}
.preview-pending-cover {{
  aspect-ratio: 16/9;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px;
  color: #334155;
  background: linear-gradient(135deg, #e2e8f0, #f8fafc);
  border-bottom: 1px solid var(--line);
}}
.preview-pending-cover span {{ font-size: 10px; font-weight: 800; color: #64748b; }}
.preview-pending-cover strong {{ font-size: 16px; line-height: 1.35; margin-top: 5px; }}
.tcard .body {{ padding: 8px 9px 10px; }}
.tcard h3 {{
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
  margin-bottom: 2px;
}}
.tcard .meta {{
  font-size: 10px;
  color: var(--dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.readiness-badge {{
  display: inline-block;
  margin-top: 6px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #92400e;
  background: #fffbeb;
}}
.readiness-badge.preview {{ color: #475569; background: #f1f5f9; }}
.readiness-badge.ready {{ color: var(--ok); background: var(--ok-soft); }}
.readiness-badge.building {{ color: #9a3412; background: #fff7ed; }}
.readiness-badge.gated {{ color: #92400e; background: #fffbeb; }}
.readiness-badge.external {{ color: #3730a3; background: #eef2ff; }}
.readiness-list {{ display: flex; flex-wrap: wrap; gap: 4px; }}

.preview-pane {{
  display: none;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}}
.preview-pane.show {{ display: block; }}
.selection-confirm {{
  margin-top: 12px;
  padding: 13px 14px;
  border: 1px solid #b7e4cf;
  border-radius: 10px;
  background: #f1fbf6;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
}}
.selection-confirm-head {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}}
.selection-confirm-copy span {{
  display: block;
  color: var(--ok);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .08em;
}}
.selection-confirm-copy strong {{ display: block; font-size: 14px; margin-top: 2px; }}
.selection-confirm-copy p {{ color: var(--dim); font-size: 11px; margin-top: 2px; }}
@media (max-width: 620px) {{
  .selection-confirm-head {{ align-items: stretch; flex-direction: column; }}
  .selection-confirm-head .btn {{ width: 100%; }}
}}
.preview-pane .title-row {{
  display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between;
  gap: 8px; margin-bottom: 10px;
}}
.preview-pane .title-row strong {{ font-size: 14px; }}
.preview-pane .title-row span {{ font-size: 12px; color: var(--dim); }}
.keys {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}}
.keys figure {{
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  background: #0f172a;
}}
.keys img {{
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
}}
.keys figcaption {{
  font-size: 11px;
  text-align: center;
  padding: 6px 8px;
  color: var(--dim);
  background: #fff;
}}
.keys.component-suite {{ display: block; }}
.suite-evidence {{
  border: 1px solid #a7d8c2;
  border-radius: 12px;
  background: rgba(255,255,255,.8);
  overflow: hidden;
}}
.suite-summary {{
  padding: 11px 12px;
  border-bottom: 1px solid #c7e8d7;
  color: #315a48;
  font-size: 11px;
  line-height: 1.55;
}}
.suite-summary b {{ display: block; color: var(--ok); font-size: 12px; }}
.suite-tabs {{
  display: flex;
  gap: 6px;
  padding: 9px 10px;
  overflow-x: auto;
  border-bottom: 1px solid #d7eadf;
  background: #f8fcfa;
}}
.suite-tab {{
  flex: 0 0 auto;
  border: 1px solid #b7dcca;
  border-radius: 999px;
  background: #fff;
  color: #315a48;
  font: inherit;
  font-size: 11px;
  font-weight: 800;
  padding: 7px 10px;
  cursor: pointer;
}}
.suite-tab[aria-selected="true"] {{
  color: #fff;
  background: var(--ok);
  border-color: var(--ok);
}}
.suite-tab:focus-visible {{ outline: 3px solid #86efac; outline-offset: 2px; }}
.suite-panel {{ padding: 12px; }}
.suite-panel h4 {{ font-size: 13px; margin-bottom: 9px; }}
.suite-proof-grid {{
  display: grid;
  grid-template-columns: minmax(240px, .8fr) minmax(0, 1.2fr);
  gap: 12px;
}}
.suite-proof-media {{
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  background: #0f172a;
}}
.suite-proof-media img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }}
.suite-proof-media figcaption {{ padding: 6px 8px; background: #fff; color: var(--dim); font-size: 11px; text-align: center; }}
.suite-proof-list {{ display: grid; align-content: start; gap: 7px; }}
.suite-proof {{
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr);
  gap: 8px;
  padding: 7px 8px;
  border: 1px solid #d7eadf;
  border-radius: 8px;
  background: #f8fcfa;
  font-size: 11px;
  line-height: 1.5;
}}
.suite-proof b {{ color: #315a48; }}
.suite-proof span {{ min-width: 0; overflow-wrap: anywhere; }}
@media (max-width: 700px) {{
  .suite-proof-grid {{ grid-template-columns: 1fr; }}
}}
.keys.mode-steps {{ grid-template-columns: repeat(3, 1fr); }}
@media (max-width: 700px) {{ .keys.mode-steps {{ grid-template-columns: 1fr; }} }}
.case-preview {{
  display: none;
  grid-template-columns: minmax(0, 1.35fr) minmax(240px, .65fr);
  gap: 12px;
  margin-bottom: 12px;
}}
.case-preview.show {{ display: grid; }}
.case-preview.video-only {{ grid-template-columns: minmax(0, 1fr); }}
.case-video {{
  overflow: hidden;
  border: 1px solid #a7d8c2;
  border-radius: 10px;
  background: #10231b;
}}
.case-video video {{
  width: 100%;
  aspect-ratio: 16/9;
  display: block;
  background: #10231b;
}}
.case-video p {{ padding: 8px 10px; color: #dff7e9; font-size: 11px; }}
.case-copy {{
  border: 1px solid #c7e8d7;
  border-radius: 10px;
  background: rgba(255,255,255,.74);
  padding: 12px;
}}
.case-copy h4 {{ font-size: 12px; margin-bottom: 5px; }}
.case-copy > p {{ color: var(--dim); font-size: 11px; }}
.prompt-example {{ margin-top: 9px; }}
.prompt-example summary {{
  color: var(--ok);
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
}}
.prompt-example pre {{
  max-height: 280px;
  overflow: auto;
  margin-top: 8px;
  padding: 10px;
  border: 1px solid #d7eadf;
  border-radius: 8px;
  background: #f8fcfa;
  color: #294337;
  font-family: var(--font);
  font-size: 11px;
  line-height: 1.65;
  white-space: pre-wrap;
}}
@media (max-width: 760px) {{ .case-preview {{ grid-template-columns: 1fr; }} }}
.mode-step {{
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px;
  background: #f8fafc;
}}
.mode-step span {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 11px;
  font-weight: 800;
}}
.mode-step b {{ display: block; font-size: 12px; margin: 8px 0 3px; }}
.mode-step p {{ font-size: 11px; color: var(--dim); }}
.preview-pending {{
  grid-column: 1 / -1;
  border: 1px dashed #94a3b8;
  border-radius: 10px;
  padding: 18px;
  color: #475569;
  background: #f8fafc;
  font-size: 12px;
}}
.actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
.btn {{
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--text);
  text-decoration: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}}
.btn.primary {{ background: var(--accent); border-color: transparent; color: #fff; }}
.btn.ok {{ background: var(--ok); border-color: transparent; color: #fff; }}
.btn:disabled {{ opacity: .45; cursor: not-allowed; }}

.cmdbox {{
  margin-top: 10px;
  padding: 12px;
  border-radius: 10px;
  background: #0f172a;
  color: #e2e8f0;
  font-family: ui-monospace, Menlo, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  display: none;
}}
.cmdbox.show {{ display: block; }}
.toast {{ font-size: 12px; color: var(--ok); margin-top: 6px; min-height: 1.2em; }}

/* inline example body */
.ex-empty {{
  padding: 28px 16px;
  text-align: center;
  color: var(--dim);
  font-size: 13px;
  background: #fafbfc;
  border: 1px dashed var(--line);
  border-radius: 10px;
}}
.ex-head {{
  display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between;
  gap: 8px; margin-bottom: 10px;
}}
.ex-head strong {{ font-size: 14px; }}
.ex-head span {{ font-size: 12px; color: var(--dim); }}
.ex-body {{
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fafbfc;
  padding: 14px 16px 16px;
  max-height: 520px;
  overflow: auto;
}}
.ex-body h4 {{
  font-size: 13px;
  font-weight: 800;
  margin: 14px 0 6px;
  color: #0f172a;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--line);
}}
.ex-body h4:first-child {{ margin-top: 0; }}
.ex-body p {{
  font-size: 13px;
  color: #334155;
  margin: 0 0 8px;
  white-space: pre-wrap;
}}
.ex-body .ex-note {{
  font-size: 12px;
  color: var(--dim);
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 10px;
}}

footer {{
  margin-top: 8px;
  font-size: 11px;
  color: var(--dim);
  text-align: center;
}}
</style>
</head>
<body>
<div class="shell">
  <header>
    <h1>内部培训内容工厂 · 选课型或制作模式</h1>
    <p class="sub">五步完成一单：选课型或模式 → 交内容 → 审复核稿 → 按闸门生成 → 一个地方取件。也可以先把内容发给 WorkBuddy，由它推荐匹配入口；创建草稿前都会请你确认所选课型或模式。</p>
    <div class="how">
      <div>
        <b>① 选我要做什么</b>
        课件选课型，动画或数字人选制作模式；点卡片看真实交付边界
      </div>
      <div>
        <b>② 交已有内容</b>
        回 WorkBuddy 说主题与要点；资料可残缺
      </div>
      <div>
        <b>③ 审初稿</b>
        先审内容/变量/脚本/关键页复核包；未确认不放行下一阶段
      </div>
      <div>
        <b>④ 生成与质检</b>
        课型走生产路线，模式按各自闸门执行；外部账号出片另确认
      </div>
      <div>
        <b>⑤ 一个地方取件</b>
        WorkBuddy 返回准确本机路径；生产路线发布件进入「05_交付物放这里」
      </div>
    </div>
  </header>

  <section class="block" id="sec-entry">
    <h2><span class="n">0</span> 选择开始方式</h2>
    <div class="how">
      <div><b>A · 先选课型或模式（推荐）</b>看预览、复核闸门与真实交付边界，确认后再提交内容。</div>
      <div><b>B · 先交内容</b>直接把主题、用途和已有要点发给 WorkBuddy，由它推荐匹配课型或模式，再由你确认。</div>
    </div>
    <p class="hint">两种方式都会先锁定一个已入库课型或制作模式；未确认复核稿时，不生成正式成品或放行正式提示词包。</p>
  </section>

  <section class="block" id="sec-templates">
    <h2><span class="n">1</span> 课型与制作模式</h2>
    <p class="hint">课型卡按生产路线实时计算能力，一个课型可分别显示 PPTX、MP4 等逐交付物状态；制作模式卡显示 WorkBuddy 可交付的复核/提示词包，以及外部账号出片边界。</p>
    <aside class="route-selector" id="route-selector" aria-labelledby="route-selector-title">
      <div class="selector-head">
        <div>
          <div class="selector-eyebrow">不会选也能开始</div>
          <h3 id="route-selector-title">{html.escape(str(route_selector["title_zh"]))}</h3>
          <p>{html.escape(str(route_selector["description_zh"]))}</p>
        </div>
        <span class="selector-gate">只推荐 · 确认模板前不建任务</span>
      </div>
      <div class="selector-layout">
        <div id="route-selector-form">
          <div class="selector-form-grid">
            <label class="selector-field">
              <span>我要什么交付物</span>
              <select id="selector-deliverable">{selector_options_html("deliverables")}</select>
            </label>
            <label class="selector-field">
              <span>内容更接近哪一类</span>
              <select id="selector-content-type">{selector_options_html("content_types")}</select>
            </label>
            <label class="selector-field">
              <span>结构偏好</span>
              <select id="selector-structure">{selector_options_html("structures")}</select>
            </label>
          </div>
          <label class="selector-field selector-requirement">
            <span>也可以直接粘贴需求</span>
            <textarea id="selector-requirement" placeholder="例如：给店员做一个新品培训，有商品资料和包装图，希望能讲清卖点与注意事项；页数不确定。"></textarea>
          </label>
          <div class="actions">
            <button type="button" class="btn primary" id="selector-build">生成选课口令</button>
            <button type="button" class="btn" id="selector-copy" disabled>复制给 WorkBuddy</button>
          </div>
          <div class="cmdbox" id="selector-cmdbox"></div>
          <p class="toast" id="selector-toast" aria-live="polite"></p>
          <p class="selector-note">这一步只让 WorkBuddy 推荐并说明原因；你明确回复“确认模板【模板名】”后，才进入建任务与内容初稿流程。</p>
        </div>
        <div class="selector-boundaries" aria-label="课型页数与交付边界">
          <b>先看清页数与交付边界</b>
          {selector_boundaries_html}
        </div>
      </div>
    </aside>
    <div class="template-groups" id="template-grid"></div>
    <div id="selection-cluster-home" hidden>
      <div id="selection-cluster">
        <div class="selection-confirm" id="selection-confirm">
        <div class="selection-confirm-head">
          <div class="selection-confirm-copy">
            <span>已选择</span>
            <strong id="confirm-name">—</strong>
            <p>WorkBuddy 提示词与关键截图、视频或数字人效果都在本区域展示。</p>
          </div>
          <button type="button" class="btn ok" id="btn-use">确认选用 · 复制给 WorkBuddy</button>
        </div>
        <div class="cmdbox" id="cmdbox"></div>
        <p class="toast" id="toast"></p>
        </div>

        <div class="preview-pane" id="preview-pane">
      <div class="title-row">
        <strong id="sel-name">—</strong>
        <span id="sel-meta"></span>
      </div>
      <div class="case-preview" id="case-preview">
        <div class="case-video">
          <video id="case-video" controls playsinline preload="metadata"></video>
          <p id="case-video-label"></p>
        </div>
        <div class="case-copy" id="case-copy">
          <h4>对应提示词示例</h4>
          <p>展开查看本案例的生成提示词；可单独复制给 WorkBuddy 复用结构。</p>
          <details class="prompt-example" id="prompt-example">
            <summary>展开完整提示词</summary>
            <pre id="prompt-example-text"></pre>
          </details>
          <button type="button" class="btn" id="btn-copy-prompt">复制提示词示例</button>
        </div>
      </div>
      <div class="keys" id="sel-keys"></div>
      <div class="actions">
        <button type="button" class="btn" id="btn-copy-ex">复制内容示例</button>
      </div>
      <p class="toast" id="preview-toast"></p>
        </div>
      </div>
    </div>
  </section>

  <section class="block" id="sec-assets">
    <h2><span class="n">2</span> 素材怎么处理</h2>
    <div class="how">
      <div><b>业务提供真图</b>商品正式包装、品牌 Logo、标签/备案/批准或检测证据；系统不仿造。</div>
      <div><b>系统自动生成</b>知识解释图、场景插图、人物咨询图；按模板真实图槽比例生成并逐页检查。</div>
      <div><b>正式交付门闸</b>待确认内容不生图；包装真图、计划插图和逐页质检没有全部完成时，不发布占位稿。</div>
      <div><b>模板直接复用</b>版式、字体、色板、箭头、勾选、分隔线和已批准小构件。</div>
    </div>
    <p class="hint">内容确认后，系统先把 1 张代表图放入真实图槽验收，再自动补齐同系列；业务不需要自己写生图提示词。</p>
  </section>

  <section class="block" id="sec-examples">
    <h2><span class="n">3</span> 填报示例与模式说明</h2>
    <p class="hint">课型展示对应填写内容；制作模式展示 WorkBuddy 直接交付、确认闸门和外部出片边界。医学与包装以贵司审核稿为准。</p>
    <div id="ex-panel">
      <div class="ex-empty" id="ex-empty">请先在上方点选一个课型或制作模式，这里会展示对应填写示例或流程边界。</div>
      <div id="ex-content" class="hidden">
        <div class="ex-head">
          <strong id="ex-title">—</strong>
          <span id="ex-caption">仅示范怎么写 · 可复制</span>
        </div>
        <div class="ex-body" id="ex-body"></div>
      </div>
    </div>
  </section>

  <footer>内部培训 · {pack_date} · 课型能力来自生产路线 · 制作模式按复核闸门与外部账号边界交付</footer>
</div>

<script>
const TEMPLATES = {catalog_js};
const PRODUCTION_MODES = {modes_js};
const PORTAL_ITEMS = TEMPLATES.concat(PRODUCTION_MODES);
const SHELF_GROUPS = {groups_js};
const ROUTE_SELECTOR_PROMPT = {selector_prompt_js};
const COMPONENT_TEMPLATE_SLUG = {component_slug_js};
let selected = null;

function mediaCover(slug) {{
  return "01_模板货架/media/" + slug + "/cover.png";
}}
function mediaKey(slug, i) {{
  return "01_模板货架/media/" + slug + "/key-" + String(i).padStart(2, "0") + ".png";
}}
function mediaModeVideo(filename) {{
  return "01_模板货架/media/production-modes/" + filename;
}}

function buildCmd(t) {{
  return t.selection_command || "";
}}

function selectedOptionLabel(id) {{
  const select = document.getElementById(id);
  return select.options[select.selectedIndex].textContent.trim();
}}

function buildRouteSelectorPrompt() {{
  const values = {{
    "[[DELIVERABLE]]": selectedOptionLabel("selector-deliverable"),
    "[[CONTENT_TYPE]]": selectedOptionLabel("selector-content-type"),
    "[[STRUCTURE]]": selectedOptionLabel("selector-structure"),
    "[[REQUIREMENT]]": document.getElementById("selector-requirement").value.trim() ||
      "暂无；请根据以上选择先推荐",
  }};
  let prompt = ROUTE_SELECTOR_PROMPT;
  Object.entries(values).forEach(([marker, value]) => {{
    prompt = prompt.split(marker).join(value);
  }});
  return prompt;
}}

function showRouteSelectorPrompt() {{
  const prompt = buildRouteSelectorPrompt();
  const box = document.getElementById("selector-cmdbox");
  box.textContent = prompt;
  box.classList.add("show");
  document.getElementById("selector-copy").disabled = false;
  return prompt;
}}

function renderGrid() {{
  const host = document.getElementById("template-grid");
  const selectionCluster = document.getElementById("selection-cluster");
  const selectionClusterHome = document.getElementById("selection-cluster-home");
  if (selectionCluster && host.contains(selectionCluster)) {{
    selectionClusterHome.appendChild(selectionCluster);
  }}
  host.innerHTML = "";
  SHELF_GROUPS.forEach(group => {{
    const items = PORTAL_ITEMS.filter(t => t.shelf_group === group.id);
    if (!items.length) return;
    const section = document.createElement("section");
    section.className = "template-group";
    section.innerHTML =
      '<div class="template-group-head"><h3>' + group.title + "</h3><p>" + group.hint + "</p></div>";
    const grid = document.createElement("div");
    grid.className = "grid";
    items.forEach(t => {{
      const card = document.createElement("button");
      card.type = "button";
      card.dataset.slug = t.slug;
      card.className = "tcard" +
        (t.portal_item_kind === "production_mode" ? " mode-card" : "") +
        (selected && selected.slug === t.slug ? " selected" : "");
      card.setAttribute("aria-pressed", selected && selected.slug === t.slug ? "true" : "false");
      const badges = (t.deliverable_badges || [t.readiness_badge]).map(badge =>
        '<span class="readiness-badge ' + (badge.kind || "preview") + '">' +
        (badge.label || "能力待确认") + "</span>"
      ).join("");
      const hasQualifiedPreview =
        t.slug !== COMPONENT_TEMPLATE_SLUG ||
        (t.preview_identity_qualified === true && t.preview_suite_evidence &&
          t.preview_suite_evidence.case_count >= 3 &&
          Array.isArray(t.preview_suite_evidence.cases) &&
          t.preview_suite_evidence.cases.length >= 3);
      const cover = t.portal_item_kind === "production_mode"
        ? '<div class="mode-cover"><span>制作模式</span><strong>' +
          (t.cover_label || "MODE") + "</strong></div>"
        : !hasQualifiedPreview
        ? '<div class="preview-pending-cover"><span>灵活构件兜底</span>' +
          '<strong>差异化预览待 QA</strong></div>'
        : '<img class="cover" src="' + mediaCover(t.slug) + '" alt="' +
          t.name_zh + '" loading="lazy" />';
      card.innerHTML =
        cover +
        '<div class="body">' +
        "<h3>" + t.name_zh + "</h3>" +
        '<div class="meta">' + (t.outputs || []).join(" · ") + "</div>" +
        '<div class="readiness-list">' + badges + "</div>" +
        "</div>";
      card.addEventListener("click", () => selectTemplate(t));
      grid.appendChild(card);
    }});
    section.appendChild(grid);
    host.appendChild(section);
  }});
}}

function showExample(t) {{
  const empty = document.getElementById("ex-empty");
  const content = document.getElementById("ex-content");
  if (!t) {{
    empty.style.display = "block";
    content.classList.add("hidden");
    content.style.display = "none";
    return;
  }}
  empty.style.display = "none";
  content.classList.remove("hidden");
  content.style.display = "block";
  const isMode = t.portal_item_kind === "production_mode";
  document.getElementById("ex-title").textContent =
    t.name_zh + (isMode ? " · 制作边界" : " · 内容示例");
  document.getElementById("ex-caption").textContent =
    isMode ? "复核闸门与外部账号边界 · 可复制" : "仅示范怎么写 · 可复制";
  document.getElementById("ex-body").innerHTML = t.example_html || "<p class=\\"ex-note\\">暂无示例</p>";
}}

function renderComponentSuiteEvidence(t, host) {{
  const evidence = t.preview_suite_evidence;
  const cases = evidence && Array.isArray(evidence.cases) ? evidence.cases : [];
  const wrap = document.createElement("section");
  wrap.className = "suite-evidence";

  const summary = document.createElement("div");
  summary.className = "suite-summary";
  const summaryTitle = document.createElement("b");
  summaryTitle.textContent =
    evidence.case_count + " 套正式非金样 UAT · 同一非课件4风格 · 每套独立逐页 QA/哈希绑定";
  const summaryLine = document.createElement("span");
  summaryLine.textContent =
    "组合来源：" + (evidence.settled_capability_labels_zh || []).join(" / ") +
    "；suite 新增页型：" + (evidence.new_page_type_labels_zh || []).join(" / ") +
    "；统一视觉：" + evidence.style_label_zh;
  summary.appendChild(summaryTitle);
  summary.appendChild(summaryLine);

  const tabs = document.createElement("div");
  tabs.className = "suite-tabs";
  tabs.setAttribute("role", "tablist");
  tabs.setAttribute("aria-label", "构件 UAT 案例证据");
  const panel = document.createElement("div");
  panel.className = "suite-panel";
  panel.setAttribute("role", "tabpanel");

  function addProof(list, label, value) {{
    const row = document.createElement("div");
    row.className = "suite-proof";
    const title = document.createElement("b");
    title.textContent = label;
    const text = document.createElement("span");
    text.textContent = value;
    row.appendChild(title);
    row.appendChild(text);
    list.appendChild(row);
  }}

  function activateCase(activeIndex) {{
    Array.from(tabs.children).forEach((button, index) => {{
      button.setAttribute("aria-selected", index === activeIndex ? "true" : "false");
      button.tabIndex = index === activeIndex ? 0 : -1;
    }});
    const item = cases[activeIndex];
    panel.innerHTML = "";
    const sourceText = (item.source_capability_labels_zh || []).join(" / ");
    const sequenceText = (item.page_type_sequence_labels_zh || []).join(" → ");
    const newText = (item.new_page_type_labels_zh || []).length
      ? item.new_page_type_labels_zh.join(" / ")
      : "本案例无；suite 其他案例已提供新增页型证据";
    const heading = document.createElement("h4");
    heading.textContent = item.title_zh;
    panel.appendChild(heading);

    const grid = document.createElement("div");
    grid.className = "suite-proof-grid";
    const figure = document.createElement("figure");
    figure.className = "suite-proof-media";
    const image = document.createElement("img");
    image.src = mediaKey(t.slug, item.portal_media_index);
    image.alt = "案例 " + item.suite_slot + " 差异化关键页";
    image.loading = "lazy";
    const caption = document.createElement("figcaption");
    caption.textContent =
      "案例 " + item.suite_slot + " · " + item.representative_page_label_zh;
    figure.appendChild(image);
    figure.appendChild(caption);

    const proofList = document.createElement("div");
    proofList.className = "suite-proof-list";
    addProof(proofList, "验收来源", "独立业务验收任务已通过");
    addProof(proofList, "代表预览", item.representative_page_label_zh);
    addProof(proofList, "课型能力", sourceText);
    addProof(proofList, "页序组合", sequenceText);
    addProof(proofList, "新增页型", newText);
    grid.appendChild(figure);
    grid.appendChild(proofList);
    panel.appendChild(grid);
  }}

  cases.forEach((item, index) => {{
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "suite-tab";
    tab.setAttribute("role", "tab");
    tab.textContent = item.tab_label_zh;
    tab.addEventListener("click", () => activateCase(index));
    tab.addEventListener("keydown", event => {{
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();
      const offset = event.key === "ArrowRight" ? 1 : -1;
      const nextIndex = (index + offset + cases.length) % cases.length;
      activateCase(nextIndex);
      tabs.children[nextIndex].focus();
    }});
    tabs.appendChild(tab);
  }});
  wrap.appendChild(summary);
  wrap.appendChild(tabs);
  wrap.appendChild(panel);
  host.appendChild(wrap);
  activateCase(0);
}}

function selectTemplate(t) {{
  selected = t;
  try {{
    localStorage.setItem("cpc_selected_template", JSON.stringify({{ slug: t.slug, name_zh: t.name_zh }}));
  }} catch (e) {{}}
  renderGrid();

  const pane = document.getElementById("preview-pane");
  const selectedCard = Array.from(document.querySelectorAll(".tcard"))
    .find(card => card.dataset.slug === t.slug);
  const selectedGroup = selectedCard && selectedCard.closest(".template-group");
  const selectionCluster = document.getElementById("selection-cluster");
  if (selectedGroup) selectedGroup.appendChild(selectionCluster);
  pane.classList.add("show");
  document.getElementById("confirm-name").textContent = t.name_zh;
  document.getElementById("sel-name").textContent = t.name_zh;
  document.getElementById("sel-meta").textContent =
    (t.one_liner || "") + " · " + (t.portal_status_label || "能力待确认") +
    " · " + (t.portal_status_note || "");

  const keys = document.getElementById("sel-keys");
  keys.innerHTML = "";
  const isMode = t.portal_item_kind === "production_mode";
  const casePreview = document.getElementById("case-preview");
  const caseVideo = document.getElementById("case-video");
  const caseCopy = document.getElementById("case-copy");
  const videoExample = t.portal_video_example;
  if (videoExample && videoExample.filename) {{
    caseVideo.src = mediaModeVideo(videoExample.filename);
    document.getElementById("case-video-label").textContent = videoExample.label;
    document.getElementById("prompt-example-text").textContent =
      t.generated_prompt_example || "";
    document.getElementById("prompt-example").open = false;
    caseCopy.style.display = t.generated_prompt_example ? "block" : "none";
    casePreview.classList.toggle("video-only", !t.generated_prompt_example);
    casePreview.classList.add("show");
  }} else {{
    caseVideo.pause();
    caseVideo.removeAttribute("src");
    caseVideo.load();
    casePreview.classList.remove("show");
  }}
  const hasQualifiedPreview =
    t.slug !== COMPONENT_TEMPLATE_SLUG ||
    (t.preview_identity_qualified === true && t.preview_suite_evidence &&
      t.preview_suite_evidence.case_count >= 3 &&
      Array.isArray(t.preview_suite_evidence.cases) &&
      t.preview_suite_evidence.cases.length >= 3);
  const hasComponentSuite =
    t.slug === COMPONENT_TEMPLATE_SLUG && hasQualifiedPreview &&
    t.preview_suite_evidence && t.preview_suite_evidence.case_count >= 3;
  keys.classList.toggle("mode-steps", isMode);
  keys.classList.toggle("component-suite", Boolean(hasComponentSuite));
  if (isMode) {{
    (t.preview_steps || []).forEach((step, idx) => {{
      const block = document.createElement("div");
      block.className = "mode-step";
      block.innerHTML = "<span>" + String(idx + 1).padStart(2, "0") + "</span>" +
        "<b>" + step.title + "</b><p>" + step.text + "</p>";
      keys.appendChild(block);
    }});
  }} else if (!hasQualifiedPreview) {{
    const block = document.createElement("div");
    block.className = "preview-pending";
    block.textContent = t.preview_identity_note_zh ||
      "至少 3 套正式差异化非金样 UAT suite 尚未通过 QA；为避免误认成课件4，门户暂不展示旧图。";
    keys.appendChild(block);
  }} else if (hasComponentSuite) {{
    renderComponentSuiteEvidence(t, keys);
  }} else {{
    (t.key_frame_labels_zh || []).forEach((lab, idx) => {{
      const i = idx + 1;
      const fig = document.createElement("figure");
      fig.innerHTML =
        '<img src="' + mediaKey(t.slug, i) + '" alt="' + lab + '" loading="lazy" />' +
        "<figcaption>" + lab + "</figcaption>";
      keys.appendChild(fig);
    }});
  }}

  const box = document.getElementById("cmdbox");
  box.textContent = buildCmd(t);
  box.classList.add("show");
  document.getElementById("btn-copy-ex").textContent =
    isMode ? "复制模式说明" : "复制内容示例";
  document.getElementById("toast").textContent = "";
  document.getElementById("preview-toast").textContent = "";
  showExample(t);
}}

document.getElementById("selector-build").addEventListener("click", () => {{
  showRouteSelectorPrompt();
  document.getElementById("selector-toast").textContent =
    "选课口令已生成。它只要求推荐与说明原因，不会在你确认模板前创建任务。";
}});

document.getElementById("selector-copy").addEventListener("click", async () => {{
  const text = showRouteSelectorPrompt();
  try {{
    await navigator.clipboard.writeText(text);
    document.getElementById("selector-toast").textContent =
      "选课口令已复制。回到 WorkBuddy 粘贴；先看推荐与原因，再决定是否确认模板。";
  }} catch (e) {{
    document.getElementById("selector-toast").textContent =
      "请手动选中上方选课口令复制。";
  }}
}});

document.getElementById("route-selector-form").addEventListener("input", () => {{
  document.getElementById("selector-cmdbox").classList.remove("show");
  document.getElementById("selector-copy").disabled = true;
  document.getElementById("selector-toast").textContent = "";
}});

document.getElementById("btn-use").addEventListener("click", async () => {{
  if (!selected) return;
  const text = buildCmd(selected);
  document.getElementById("cmdbox").textContent = text;
  document.getElementById("cmdbox").classList.add("show");
  try {{
    await navigator.clipboard.writeText(text);
    document.getElementById("toast").textContent =
      selected.portal_item_kind === "production_mode"
        ? "已复制制作模式口令。回到 WorkBuddy 粘贴；它会先整理变量或复核包，收到明确确认后才放行提示词或条件式外部制作。"
        : selected.slug === "product-courseware-component-v1" && selected.self_serve
        ? "已复制灵活构件口令。WorkBuddy 会先返回内容缺口、中文页签大纲、每页来源解释、单一视觉与素材分工；你确认后才会建任务并生成 PPTX。"
        : selected.self_serve
        ? "已复制业务口令。回到 WorkBuddy 粘贴；它会先复述已锁定模板，再收集内容、出初稿，确认后才生成。"
        : selected.portal_status_kind === "building"
          ? "已复制接入中课型口令。可先整理初稿和素材清单；当前不会承诺或生成正式成品。"
          : "已复制金样参考口令。回到 WorkBuddy 粘贴后可查看课型缺口。";
  }} catch (e) {{
    document.getElementById("toast").textContent = "请手动选中下方口令复制。";
  }}
}});

document.getElementById("btn-copy-ex").addEventListener("click", async () => {{
  if (!selected) return;
  const paras = selected.example_paragraphs || [];
  const text = paras.join("\\n");
  try {{
    await navigator.clipboard.writeText(text);
    document.getElementById("preview-toast").textContent =
      selected.portal_item_kind === "production_mode"
        ? "模式说明已复制到剪贴板。"
        : "内容示例已复制到剪贴板。";
  }} catch (e) {{
    document.getElementById("preview-toast").textContent =
      "复制失败，请在下方示例区手动选择复制。";
  }}
}});

document.getElementById("btn-copy-prompt").addEventListener("click", async () => {{
  if (!selected || !selected.generated_prompt_example) return;
  try {{
    await navigator.clipboard.writeText(selected.generated_prompt_example);
    document.getElementById("preview-toast").textContent =
      "提示词示例已复制到剪贴板。";
  }} catch (e) {{
    document.getElementById("prompt-example").open = true;
    document.getElementById("preview-toast").textContent =
      "复制失败，请在展开区域手动选择复制。";
  }}
}});

try {{
  const raw = localStorage.getItem("cpc_selected_template");
  if (raw) {{
    const saved = JSON.parse(raw);
    const t = PORTAL_ITEMS.find(x => x.slug === saved.slug);
    if (t) selected = t;
  }}
}} catch (e) {{}}

renderGrid();
if (selected) selectTemplate(selected);
else showExample(null);
</script>
</body>
</html>
"""


def write_upload_folder_readme(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# 可选 · 文件投递箱

主流程请在 **WorkBuddy 聊天** 直接说内容 / 发附件。

本目录仅备用：若要把已填 Word 或授权图放进仓库，可放入 `待处理/`。
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    print("business_guided_portal: import build_guided_portal_html / extract_docx_paragraphs")
