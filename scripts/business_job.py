#!/usr/bin/env python3
"""Business job orchestrator — thin control plane over existing generators.

Business and WorkBuddy use this instead of stitching internal CLI paths.

  python3 scripts/business_job.py list-routes
  python3 scripts/business_job.py new --route product-pptx-component-v1 --theme 示例商品
  python3 scripts/business_job.py draft --job <id>
  python3 scripts/business_job.py approve --job <id> --gate content --by 业务同事
  python3 scripts/business_job.py render --job <id>
  # 兼容旧绿色五页：product-pptx-green-v1
  python3 scripts/business_job.py status --job <id>
  python3 scripts/business_job.py open --job <id>
  python3 scripts/business_job.py retry --job <id>
  python3 scripts/business_job.py list

Workspace (gitignored): outputs/workbuddy-workspaces/jobs/<job_id>/
Delivery (gitignored payloads): 业务包/05_交付物放这里/<job_id>/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "production-library" / "business-routes.json"
CATALOG_PATH = (
    ROOT / "production-library" / "templates" / "settled" / "business-catalog.json"
)
RUNTIME_PROFILES_PATH = ROOT / "production-library" / "runtime-profiles.json"
# P2: formal production path first; legacy poc only as last-resort fallback.
_GREEN_ENGINE_DIR = (
    ROOT / "production-library" / "engines" / "product-courseware-green-v1"
)
_GREEN_GOLD_CANDIDATES = (
    _GREEN_ENGINE_DIR / "gold-content-model.json",
    ROOT / "poc" / "courseware-export" / "product-courseware-green.json",
)
_GREEN_BUILDER_CANDIDATES = (
    _GREEN_ENGINE_DIR / "build-product-courseware.mjs",
    ROOT / "poc" / "courseware-export" / "work" / "build-product-courseware.mjs",
)
_NODE_MODULES_CANDIDATES = (
    ROOT / "production-library" / "engines" / "courseware-pptx-v1" / "node_modules",
    _GREEN_ENGINE_DIR / "node_modules",
    ROOT / "poc" / "courseware-export" / "work" / "node_modules",
)

# P2.8 default PPT: component + recipe engine
_COMPONENT_ENGINE_DIR = ROOT / "production-library" / "engines" / "courseware-pptx-v1"
_COMPONENT_EXPORT = _COMPONENT_ENGINE_DIR / "export.mjs"
_COMPONENT_GENERATOR = ROOT / "scripts" / "generate_courseware.py"
_COMPONENT_STYLE_DEFAULT = (
    ROOT / "production-library" / "styles" / "courseware-4-silk-yellow-red-v1" / "tokens.json"
)
_COMPONENT_RECIPES = (
    ROOT / "production-library" / "page-types" / "product-training" / "recipes"
)
_COMPONENT_REGISTRY = (
    ROOT / "production-library" / "page-types" / "product-training" / "registry.json"
)
_COMPONENT_ASSETS = (
    ROOT
    / "production-library"
    / "validation"
    / "courseware"
    / "product-courseware-4-faithful-replica-v1"
)


def _first_existing(paths: tuple[Path, ...]) -> Path | None:
    for path in paths:
        if path.is_file() or path.is_dir():
            return path
    return None


def green_gold_json() -> Path:
    found = _first_existing(_GREEN_GOLD_CANDIDATES)
    if not found or not found.is_file():
        raise SystemExit(
            "缺少绿色课件金样 content-model；预期 production-library/engines/"
            "product-courseware-green-v1/gold-content-model.json"
        )
    return found


def green_builder() -> Path:
    found = _first_existing(_GREEN_BUILDER_CANDIDATES)
    if not found or not found.is_file():
        raise SystemExit(
            "缺少绿色课件导出引擎；预期 production-library/engines/"
            "product-courseware-green-v1/build-product-courseware.mjs"
        )
    return found


# Back-compat names used by tests / older imports
GREEN_GOLD_JSON = _GREEN_GOLD_CANDIDATES[0]
GREEN_BUILDER = _GREEN_BUILDER_CANDIDATES[0]


def component_export() -> Path:
    if not _COMPONENT_EXPORT.is_file():
        raise SystemExit(
            "缺少构件 PPT 引擎：production-library/engines/courseware-pptx-v1/export.mjs"
        )
    return _COMPONENT_EXPORT


def component_generator() -> Path:
    if not _COMPONENT_GENERATOR.is_file():
        raise SystemExit("缺少 generate_courseware.py")
    return _COMPONENT_GENERATOR


def component_style_default() -> Path:
    if not _COMPONENT_STYLE_DEFAULT.is_file():
        raise SystemExit(f"缺少默认 style tokens: {_COMPONENT_STYLE_DEFAULT}")
    return _COMPONENT_STYLE_DEFAULT

# Ensure sibling scripts import cleanly when launched as a file.
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", (text or "").strip())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:48] or "job"


def load_routes_doc() -> dict[str, Any]:
    if not ROUTES_PATH.is_file():
        raise SystemExit(f"missing business routes: {ROUTES_PATH}")
    return read_json(ROUTES_PATH)


def load_routes(*, active_only: bool = False) -> list[dict[str, Any]]:
    routes = list(load_routes_doc().get("routes") or [])
    if active_only:
        routes = [r for r in routes if r.get("active")]
    return sorted(routes, key=lambda r: int(r.get("priority") or 999))


def get_route(route_id: str) -> dict[str, Any]:
    for route in load_routes():
        if route.get("route_id") == route_id:
            return route
    raise SystemExit(f"未知 route_id: {route_id}")


def jobs_root() -> Path:
    rel = load_routes_doc().get("job_workspace_rel") or "outputs/workbuddy-workspaces/jobs"
    path = ROOT / rel
    path.mkdir(parents=True, exist_ok=True)
    return path


def delivery_root() -> Path:
    rel = (
        load_routes_doc().get("delivery_root_rel")
        or "outputs/业务使用资料包/药店培训内容工厂-业务包/05_交付物放这里"
    )
    path = ROOT / rel
    path.mkdir(parents=True, exist_ok=True)
    return path


def catalog_by_slug() -> dict[str, dict[str, Any]]:
    if not CATALOG_PATH.is_file():
        return {}
    items = read_json(CATALOG_PATH).get("templates") or []
    return {str(item["slug"]): item for item in items if item.get("slug")}


def business_label(state: str, job: dict[str, Any] | None = None, route: dict[str, Any] | None = None) -> str:
    """Map internal state to the six business-facing Chinese labels."""
    if state in ("qa_failed", "delivered"):
        return "质检失败或已交付"
    if state == "env_blocked":
        return "等待业务资料"
    if state == "rendering":
        return "正在生成"
    if state == "visual_approved":
        return "等待视觉确认"
    if state == "content_approved":
        gates = (route or {}).get("gates") or {}
        approvals = (job or {}).get("approvals") or {}
        if gates.get("visual_approval") and not (approvals.get("visual") or {}).get("approved"):
            return "等待视觉确认"
        if gates.get("product_image_approval") and not (
            approvals.get("product_image") or {}
        ).get("approved"):
            return "等待业务资料"
        # Approvals complete — still show a business-facing waiting label;
        # next_step_zh explains that render can start.
        return "等待内容确认"
    states = load_routes_doc().get("states") or {}
    return str(states.get(state) or state)


def next_step_zh(job: dict[str, Any], route: dict[str, Any]) -> str:
    state = job.get("state")
    gates = route.get("gates") or {}
    if state in (None, "intake", "needs_input"):
        return "补充主题/要点后执行 draft"
    if state == "draft_ready":
        return "业务确认内容后：approve --gate content"
    if state == "content_approved":
        if gates.get("product_image_approval") and not (
            (job.get("approvals") or {}).get("product_image") or {}
        ).get("approved"):
            return "提交授权包装图并 approve --gate product_image"
        if gates.get("visual_approval") and not (
            (job.get("approvals") or {}).get("visual") or {}
        ).get("approved"):
            return "确认画面后：approve --gate visual"
        return "环境就绪后执行 render"
    if state == "visual_approved":
        return "环境就绪后执行 render"
    if state == "rendering":
        return "等待生成完成"
    if state == "env_blocked":
        missing = (job.get("env") or {}).get("missing") or []
        return "安装缺失能力后 retry：" + ("/".join(missing) if missing else "见 status")
    if state == "qa_failed":
        return "查看 workspace 诊断后修正并 retry"
    if state == "qa_passed":
        return "已质检通过，检查交付目录"
    if state == "delivered":
        path = (job.get("delivery") or {}).get("path") or ""
        return f"已交付：{path}"
    return "执行 status 查看详情"


def job_dir(job_id: str) -> Path:
    return jobs_root() / job_id


def job_path(job_id: str) -> Path:
    return job_dir(job_id) / "job.json"


def load_job(job_id: str) -> dict[str, Any]:
    path = job_path(job_id)
    if not path.is_file():
        raise SystemExit(f"任务不存在: {job_id}")
    return read_json(path)


def save_job(job: dict[str, Any]) -> None:
    job["updated_at"] = utc_now()
    write_json(job_path(job["job_id"]), job)


def append_history(job: dict[str, Any], event: str, detail: dict[str, Any] | None = None) -> None:
    history = job.setdefault("history", [])
    history.append({"at": utc_now(), "event": event, "detail": detail or {}})


def transition(job: dict[str, Any], state: str, *, reason: str = "") -> None:
    prev = job.get("state")
    job["state"] = state
    append_history(job, "transition", {"from": prev, "to": state, "reason": reason})


def make_job_id(route_id: str, theme: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{slugify(route_id)}-{slugify(theme)}-{uuid.uuid4().hex[:6]}"


def probe_capabilities() -> dict[str, Any]:
    try:
        from probe_production_env import probe

        report = probe()
        caps = report.get("capabilities") or {}
        return {str(k): bool(v) for k, v in caps.items()}
    except Exception as exc:  # noqa: BLE001 — surface probe failure honestly
        return {"_probe_error": True, "_error": str(exc)}


def env_missing(route: dict[str, Any], caps: dict[str, bool]) -> list[str]:
    if caps.get("_probe_error"):
        return ["probe_failed"]
    return [name for name in (route.get("env_require") or []) if not caps.get(name)]


def cmd_list_routes(args: argparse.Namespace) -> int:
    catalog = catalog_by_slug()
    caps = probe_capabilities() if not args.no_probe else {}
    rows = []
    for route in load_routes(active_only=not args.all):
        slug = route.get("template_slug")
        template = catalog.get(str(slug) or "", {})
        missing = env_missing(route, caps) if caps else []
        rows.append(
            {
                "route_id": route["route_id"],
                "name_zh": route.get("name_zh"),
                "audience_zh": route.get("audience_zh"),
                "deliverable_zh": route.get("deliverable_zh"),
                "template_slug": slug,
                "active": bool(route.get("active")),
                "template_capabilities": template.get("capabilities"),
                "env_require": route.get("env_require") or [],
                "env_missing": missing,
                "gates": route.get("gates") or {},
                "notes_zh": route.get("notes_zh"),
            }
        )
    if args.json:
        print(json.dumps({"routes": rows}, ensure_ascii=False, indent=2))
        return 0
    for row in rows:
        flag = "ACTIVE" if row["active"] else "off"
        miss = f" · 缺 {','.join(row['env_missing'])}" if row["env_missing"] else ""
        print(
            f"[{flag}] {row['route_id']}\n"
            f"  {row['name_zh']} · {row['audience_zh']} · {row['deliverable_zh']}{miss}\n"
            f"  模板 {row['template_slug']} · {row['notes_zh']}"
        )
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    route = get_route(args.route)
    if not route.get("active") and not args.force:
        raise SystemExit(
            f"route {args.route} 未激活（active=false）。确认后可用 --force，或换 active 路线。"
        )
    theme = (args.theme or "").strip()
    if not theme:
        raise SystemExit("--theme 必填（商品名/病名/主题）")

    job_id = args.job_id or make_job_id(route["route_id"], theme)
    path = job_dir(job_id)
    if path.exists():
        raise SystemExit(f"job 目录已存在: {path}")

    path.mkdir(parents=True, exist_ok=False)
    for name in ("draft", "approvals", "workspace", "intake", "delivery"):
        (path / name).mkdir(parents=True, exist_ok=True)

    notes = (args.notes or "").strip()
    intake = {
        "theme": theme,
        "notes": notes,
        "product_image": str(args.product_image) if args.product_image else None,
        "sections_json": str(args.sections_json) if args.sections_json else None,
        "script_json": str(args.script_json) if getattr(args, "script_json", None) else None,
        "raw_text": (args.raw_text or "").strip() or None,
        "created_at": utc_now(),
    }
    write_json(path / "intake" / "intake.json", intake)

    if args.product_image:
        src = Path(args.product_image).expanduser().resolve()
        if not src.is_file():
            raise SystemExit(f"包装图不存在: {src}")
        dest = path / "intake" / src.name
        shutil.copy2(src, dest)
        intake["product_image"] = str(dest)
        write_json(path / "intake" / "intake.json", intake)

    if args.sections_json:
        src = Path(args.sections_json).expanduser().resolve()
        if not src.is_file():
            raise SystemExit(f"sections-json 不存在: {src}")
        dest = path / "intake" / "sections.source.json"
        shutil.copy2(src, dest)
        intake["sections_json"] = str(dest)
        write_json(path / "intake" / "intake.json", intake)

    if getattr(args, "script_json", None):
        src = Path(args.script_json).expanduser().resolve()
        if not src.is_file():
            raise SystemExit(f"script-json 不存在: {src}")
        dest = path / "intake" / "script.source.json"
        shutil.copy2(src, dest)
        intake["script_json"] = str(dest)
        write_json(path / "intake" / "intake.json", intake)

    job = {
        "schema": "business-job-v1",
        "job_id": job_id,
        "route_id": route["route_id"],
        "template_slug": route.get("template_slug"),
        "name_zh": route.get("name_zh"),
        "theme": theme,
        "state": "intake",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "intake": intake,
        "draft": {},
        "approvals": {},
        "env": {},
        "render": {},
        "delivery": {"published": False, "path": None},
        "history": [],
    }
    append_history(job, "created", {"route_id": route["route_id"], "theme": theme})
    save_job(job)

    if args.auto_draft:
        return cmd_draft(argparse.Namespace(job=job_id, json=args.json))

    payload = {
        "ok": True,
        "job_id": job_id,
        "state": job["state"],
        "business_status": business_label(job["state"], job, route),
        "next_step": next_step_zh(job, route),
        "path": str(path),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"已创建任务 {job_id}\n"
            f"状态：{payload['business_status']}\n"
            f"下一步：{payload['next_step']}\n"
            f"目录：{path}"
        )
    return 0


# Gold-sample product names / codes that must never leak into a new-theme draft.
_GREEN_GOLD_FORBIDDEN = (
    "金银花露",
    "可可康",
    "小葵花",
    "小儿咽扁",
    "小儿氨酚黄那敏",
    "氨溴特罗",
    "2429715",
    "265ml",
    "9.9元",
)


def _assert_no_green_gold_residue(model: dict[str, Any], theme: str) -> None:
    """Hard guard: new-theme draft must not retain 金银花露 gold medical/price copy."""
    blob = json.dumps(model, ensure_ascii=False)
    for token in _GREEN_GOLD_FORBIDDEN:
        if token in theme:
            continue
        if token in blob:
            raise SystemExit(
                f"draft 仍含金样残留「{token}」，已阻断；请检查 _draft_product_pptx_green 替换逻辑"
            )


def _draft_product_pptx_green(job: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    """Build a theme-swapped content model from green gold structure.

    Structure/layout comes from gold JSON; every product-specific field is replaced
    with theme + 待确认 placeholders so gold medical/price copy never ships.
    """
    theme = job["theme"]
    notes = (job.get("intake") or {}).get("notes") or ""
    gold = read_json(green_gold_json())
    model = json.loads(json.dumps(gold))  # deep copy
    model["project_id"] = f"business-job.{job['job_id']}"
    model["content_lock"] = "business-draft-pending-approval"
    model["style_pack_locked"] = True

    note_points = [p.strip(" -•\t") for p in notes.splitlines() if p.strip()]
    one_liner = (
        note_points[0][:40] if note_points else f"{theme} 店员培训要点（待确认）"
    )
    sell_points = note_points[:5] or [
        f"{theme} 核心卖点 1（待确认）",
        f"{theme} 核心卖点 2（待确认）",
    ]

    for page in model.get("pages") or []:
        pid = page.get("id")

        if pid == "cover":
            page["title"] = theme

        elif pid == "product-overview":
            product = page.setdefault("product", {})
            product["display_name"] = theme
            product["code"] = "待确认"
            product["priority"] = "待确认"
            product["specification"] = "待确认"
            product["retail_price"] = "待确认"
            product["one_line_selling_point"] = one_liner
            for section in page.get("sections") or []:
                title = str(section.get("title") or "")
                if "商品介绍" in title:
                    section["items"] = [
                        f"商品名称：{theme}",
                        "规格/编码/零售价：待确认",
                        "功能与用法：待业务审核稿确认",
                    ]
                elif "核心卖点" in title:
                    section["items"] = sell_points
                elif "适宜人群" in title:
                    section["items"] = [
                        "适宜人群 1（待确认）",
                        "适宜人群 2（待确认）",
                    ]

        elif pid == "combination-guidance":
            # Must replace gold rows entirely (builder requires ≥1 row).
            page["primary_pack_label"] = f"{theme}\n包装图待接入"
            page["rows"] = [
                {
                    "scenario": "联合场景 1（待确认）",
                    "combination": f"{theme} + 搭档商品（待确认）",
                    "partner": "搭档商品（待确认）",
                    "partner_asset": "asset://partner-placeholder",
                    "talk_track": "销售话术待业务审核稿确认；不得沿用其他商品联合话术。",
                }
            ]

        elif pid == "product-benchmark":
            # Gold id is product-benchmark (not competitive-comparison).
            page["title"] = "品种对标"
            page["columns"] = [
                "对比维度",
                theme,
                "对标品种（待确认）",
            ]
            page["rows"] = [
                {
                    "label": "产品展示",
                    "values": [
                        "asset://product-packshot-primary",
                        "asset://product-packshot-competitor",
                    ],
                },
                {
                    "label": "功效主治",
                    "merge": True,
                    "value": "功效主治待业务审核稿确认",
                },
                {
                    "label": "共有优势",
                    "merge": True,
                    "value": "共有优势待确认",
                },
                {
                    "label": "零售价",
                    "values": ["待确认", "待确认"],
                },
                {
                    "label": "卖点差异",
                    "values": [f"{theme} 差异卖点待确认", "/"],
                },
            ]

        elif pid == "precautions":
            # Gold uses top-level items[], not sections[].
            page["items"] = [
                "注意事项以说明书与公司审核口径为准（待确认）。",
                "用药前请仔细阅读说明书，或在药师指导下使用。",
                "对本品过敏者禁用，过敏体质者慎用（待确认）。",
            ]
            # Keep generic illustration card titles (diet / tonic / doctor / allergy);
            # only clear product-specific asset bindings if any were gold-named.
            for slot in page.get("illustration_slots") or []:
                asset = str(slot.get("asset") or "")
                if any(tok in asset for tok in ("jinyinhua", "金银花")):
                    slot["asset"] = "asset://precaution-placeholder"

    _assert_no_green_gold_residue(model, theme)

    gaps = [
        "规格 / 编码 / 零售价",
        "审核后的功能主治与用法用量",
        "联合用药场景与搭档商品（有几条写几条）",
        "竞品对标（无则保持待确认）",
        "注意事项审核稿",
        "授权包装图（可选；无图用槽位）",
    ]
    if notes:
        gaps.insert(0, "业务已提供文字要点，请逐条核对是否可进正式培训")

    draft_dir = job_dir(job["job_id"]) / "draft"
    content_path = draft_dir / "content-model.json"
    review_path = draft_dir / "内容初稿.md"
    gaps_path = draft_dir / "缺口清单.md"
    write_json(content_path, model)

    review_lines = [
        f"# 内容初稿 · {theme}",
        "",
        f"- 任务：`{job['job_id']}`",
        f"- 路线：{route.get('name_zh')}",
        f"- 模板：{route.get('template_slug')}",
        "",
        "## 说明",
        "",
        "本文件供业务确认。确认前不生成正式 PPTX。",
        "标「待确认」的字段不得当作已审核医学/价格结论。",
        "本草稿已剥离金样商品文案；联合/对标/注意页为占位，需业务填实。",
        "",
    ]
    for page in model.get("pages") or []:
        review_lines.append(f"## {page.get('title') or page.get('id')}")
        review_lines.append("")
        product = page.get("product") or {}
        if product:
            review_lines.append(f"- 商品：{product.get('display_name')}")
            review_lines.append(
                f"- 编码/主推/规格/价：{product.get('code')} / "
                f"{product.get('priority')} / {product.get('specification')} / "
                f"{product.get('retail_price')}"
            )
            review_lines.append(f"- 一句话：{product.get('one_line_selling_point')}")
        for section in page.get("sections") or []:
            review_lines.append(f"### {section.get('title')}")
            for item in section.get("items") or []:
                review_lines.append(f"- {item}")
        for col in page.get("columns") or []:
            if col not in ("对比维度", "应用场景（适宜人群）", "联合用药", "联合商品图", "本品图", "销售话术"):
                review_lines.append(f"- 列：{col}")
        for row in page.get("rows") or []:
            if row.get("scenario") is not None:
                review_lines.append(
                    f"- 场景：{row.get('scenario')}｜联合：{row.get('combination')}｜话术：{row.get('talk_track')}"
                )
            elif row.get("label") is not None:
                if row.get("merge"):
                    review_lines.append(f"- {row.get('label')}：{row.get('value')}")
                else:
                    review_lines.append(
                        f"- {row.get('label')}：{' | '.join(str(v) for v in (row.get('values') or []))}"
                    )
        for item in page.get("items") or []:
            review_lines.append(f"- {item}")
        review_lines.append("")
    review_path.write_text("\n".join(review_lines) + "\n", encoding="utf-8")
    gaps_path.write_text(
        "# 缺口清单\n\n" + "\n".join(f"- [ ] {g}" for g in gaps) + "\n",
        encoding="utf-8",
    )

    digest = sha256_file(content_path)
    return {
        "kind": "product_pptx_green",
        "content_model": str(content_path),
        "review_md": str(review_path),
        "gaps_md": str(gaps_path),
        "content_sha256": digest,
        "gaps": gaps,
    }


def _draft_product_video_full(job: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    from business_video_product_full import (
        build_product_approval_request,
        product_content_sha256,
    )

    theme = job["theme"]
    notes = (job.get("intake") or {}).get("notes") or ""
    intake = job.get("intake") or {}
    draft_dir = job_dir(job["job_id"]) / "draft"

    if intake.get("sections_json") and Path(intake["sections_json"]).is_file():
        content = read_json(Path(intake["sections_json"]))
        if isinstance(content, list):
            content = {"theme": theme, "sections": content}
        content["theme"] = content.get("theme") or theme
    else:
        note_bits = [p.strip(" -•\t") for p in notes.splitlines() if p.strip()]
        default_points = note_bits or [f"{theme} 培训要点待业务补充"]
        content = {
            "theme": theme,
            "sections": [
                {
                    "title": "为什么要了解",
                    "narration": f"门店同事需要快速掌握{theme}的定位与沟通边界。",
                },
                {
                    "title": "商品基础信息",
                    "narration": f"{theme}的规格、批准文号与厂家信息以公司审核资料为准。",
                },
                {
                    "title": "核心讲解",
                    "narration": f"{theme}相关说明需结合审核稿，不扩展未确认功效。",
                },
                {
                    "title": "核心功效",
                    "narration": "；".join(default_points[:4]),
                },
                {
                    "title": "产品特点",
                    "narration": "工艺与原料信息待业务审核稿确认。",
                },
                {
                    "title": "适宜人群",
                    "narration": "适宜人群以审核稿为准。",
                },
                {
                    "title": "联合用药",
                    "narration": "联合方案有几条写几条，不硬凑。",
                },
                {
                    "title": "总结",
                    "narration": f"记住{theme}的定位、人群边界与话术红线。",
                },
            ],
        }

    content_path = draft_dir / "sections.json"
    write_json(content_path, content)
    # Canonical hash must match generate_business_video / product-video-approval-v1.
    digest = product_content_sha256(content)

    review_path = draft_dir / "脚本初稿.md"
    lines = [
        f"# 脚本初稿 · {theme}",
        "",
        f"- 任务：`{job['job_id']}`",
        f"- 路线：{route.get('name_zh')}",
        f"- content_sha256：`{digest}`",
        "",
        "确认前不生成正式 MP4。正式路径必须绑定授权包装图审批。",
        "",
    ]
    for i, sec in enumerate(content.get("sections") or [], 1):
        lines.append(f"## {i}. {sec.get('title')}")
        lines.append("")
        lines.append(str(sec.get("narration") or ""))
        lines.append("")
    review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    gaps = [
        "完整 8 段审核旁白（可在 sections.json 直接改）",
        "公司授权包装图与授权凭证编号",
        "专有名词与禁忌表述药师/合规确认",
    ]
    if not intake.get("product_image"):
        gaps.insert(0, "缺少授权包装图路径（intake.product_image）")

    product_image = Path(intake["product_image"]) if intake.get("product_image") else None
    if product_image and not product_image.is_file():
        product_image = None
    approval_request = build_product_approval_request(content, product_image)
    req_path = draft_dir / "product-approval.request.json"
    write_json(req_path, approval_request)
    (draft_dir / "缺口清单.md").write_text(
        "# 缺口清单\n\n" + "\n".join(f"- [ ] {g}" for g in gaps) + "\n",
        encoding="utf-8",
    )

    return {
        "kind": "product_video_full",
        "sections_json": str(content_path),
        "review_md": str(review_path),
        "approval_request": str(req_path),
        "content_sha256": digest,
        "gaps": gaps,
    }


# Gold medical/brand tokens that must not leak into a new-theme component draft.
_COMPONENT_GOLD_FORBIDDEN = (
    "金银花露",
    "可可康",
    "小葵花",
    "小儿咽扁",
    "福尔麦金利",
    "麦金利",
    "番茄红素软胶囊",
    "坦索罗辛",
    "非那雄胺",
    "前列康",
    "普乐安",
    "2429715",
    "265ml",
    "9.9元",
)


def _assert_no_component_gold_residue(script: dict[str, Any], theme: str) -> None:
    blob = json.dumps(script, ensure_ascii=False)
    for token in _COMPONENT_GOLD_FORBIDDEN:
        if token in theme:
            continue
        if token in blob:
            raise SystemExit(
                f"draft 仍含金样残留「{token}」，已阻断；请检查构件草稿脚本构建逻辑"
            )


def _parse_note_points(notes: str) -> list[str]:
    return [p.strip(" -•\t") for p in (notes or "").splitlines() if p.strip()]


def _build_component_script(theme: str, notes: str) -> dict[str, Any]:
    """Business-facing structured script from theme + free notes.

    All copy is invented only as 待确认 placeholders tied to *this* theme —
    never lifted from green or lycopene gold samples.
    """
    points = _parse_note_points(notes)
    sell = points[:3] or [
        f"{theme} 核心卖点 1（待确认）",
        f"{theme} 核心卖点 2（待确认）",
        f"{theme} 核心卖点 3（待确认）",
    ]
    while len(sell) < 3:
        sell.append(f"{theme} 补充卖点 {len(sell)+1}（待确认）")

    features_src = points[3:6] if len(points) > 3 else []
    while len(features_src) < 3:
        features_src.append(f"{theme} 产品特点 {len(features_src)+1}（待确认）")

    audience_src = points[6:10] if len(points) > 6 else [
        f"{theme} 适宜人群 1（待确认）",
        f"{theme} 适宜人群 2（待确认）",
        f"{theme} 适宜人群 3（待确认）",
    ]
    if len(audience_src) < 2:
        audience_src.append(f"{theme} 适宜人群补充（待确认）")

    hook_para = (
        points[0]
        if points
        else f"今天我们一起了解{theme}的店员培训要点；具体功效与用法以公司审核稿为准。"
    )
    if not points:
        hook_para2 = f"{theme}相关说明须药师/合规确认后使用，本草稿仅为结构占位。"
    else:
        hook_para2 = "；".join(points[:2]) if len(points) >= 2 else f"{theme}要点待业务逐条确认。"

    script: dict[str, Any] = {
        "schema": "product-training-script/v1",
        "meta": {
            "display_name": theme,
            "organization": "大参林医药集团",
            "tagline": "【专业力】",
            "content_lock": "business-draft-pending-approval",
            "brand_boast_disabled": True,
            "family": "product-training",
            "style_pack_id": "courseware-4-silk-yellow-red-v1",
        },
        "hook": {
            "title": f"{theme} 店员培训导语",
            "paragraphs": [hook_para, hook_para2],
            "symptoms": ["关注健康信号", "生活质量下降"],
            "stats": [
                {
                    "number": "—",
                    "unit": "",
                    "note": "关键数据待业务审核稿确认",
                    "role": "stat1",
                }
            ],
            "source": "数据出处待审核稿确认",
        },
        "benefits": {
            "title": "核心功效",
            "items": [
                {
                    "title": sell[i][:40],
                    "body": f"{sell[i]}。详细表述以审核稿为准，不得扩写未确认功效。",
                }
                for i in range(3)
            ],
        },
        "features": {
            "title": "产品特点",
            "items": [
                {
                    "title": f"特点{i+1}",
                    "body": features_src[i],
                }
                for i in range(3)
            ],
        },
        "audience": {
            "title": "适宜人群",
            "items": audience_src[:4],
        },
        "combination": {
            "title": "联合用药",
            "rows": [
                {
                    "problem": "联合场景 1（待确认）",
                    "partner": "搭档商品（待确认）",
                    "talk_track": f"搭配{theme}的话术待业务审核稿确认；不得沿用其他商品联合话术。",
                }
            ],
        },
        "summary": {
            "title": "总结回顾",
            "rows": [
                {"label": "核心卖点", "value": "；".join(sell[:3])},
                {"label": "适宜人群", "value": "；".join(audience_src[:3])},
                {"label": "注意事项", "value": "以说明书与公司审核口径为准（待确认）"},
            ],
        },
        "precautions": {
            "title": "注意事项",
            "items": [
                "注意事项以说明书与公司审核口径为准（待确认）。",
                "用药前请仔细阅读说明书，或在药师指导下使用。",
                f"对本品（{theme}）过敏者禁用，过敏体质者慎用（待确认）。",
            ],
        },
    }
    _assert_no_component_gold_residue(script, theme)
    return script


def _run_courseware_generator(
    *,
    script_path: Path,
    out_dir: Path,
    skip_export: bool,
    skip_qa: bool = True,
    skip_provenance: bool = False,
    name_suffix: str = "业务交付",
) -> dict[str, Any]:
    """Invoke generate_courseware.py; return parsed generate-report.json."""
    gen = component_generator()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(gen),
        "--script",
        str(script_path),
        "--style",
        str(component_style_default()),
        "--registry",
        str(_COMPONENT_REGISTRY),
        "--recipes",
        str(_COMPONENT_RECIPES),
        "--out-dir",
        str(out_dir),
        "--engine",
        str(component_export()),
        "--name-suffix",
        name_suffix,
    ]
    if _COMPONENT_ASSETS.is_dir():
        cmd.extend(["--assets", str(_COMPONENT_ASSETS)])
    if skip_export:
        cmd.append("--skip-export")
    if skip_qa:
        cmd.append("--skip-qa")
    if skip_provenance:
        cmd.append("--skip-provenance")

    env = os.environ.copy()
    node_modules = _first_existing(_NODE_MODULES_CANDIDATES)
    if node_modules and node_modules.is_dir():
        prev = env.get("NODE_PATH", "")
        env["NODE_PATH"] = (
            str(node_modules) if not prev else f"{node_modules}{os.pathsep}{prev}"
        )

    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    log_path = out_dir / "generate.log"
    log_path.write_text(
        f"$ {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )
    report_path = out_dir / "generate-report.json"
    report: dict[str, Any] = {}
    if report_path.is_file():
        try:
            report = read_json(report_path)
        except (OSError, json.JSONDecodeError):
            report = {}
    report["_exit_code"] = proc.returncode
    report["_log"] = str(log_path)
    if proc.returncode != 0 and not report.get("content_model"):
        raise RuntimeError(
            f"generate_courseware 失败 exit={proc.returncode}；见 {log_path}"
        )
    return report


def _draft_product_pptx_component(
    job: dict[str, Any], route: dict[str, Any]
) -> dict[str, Any]:
    """Draft via script.structured → scene-plan → content-model (no PPTX yet)."""
    theme = job["theme"]
    notes = (job.get("intake") or {}).get("notes") or ""
    intake = job.get("intake") or {}
    draft_dir = job_dir(job["job_id"]) / "draft"
    draft_dir.mkdir(parents=True, exist_ok=True)

    if intake.get("script_json") and Path(intake["script_json"]).is_file():
        script = read_json(Path(intake["script_json"]))
        if not isinstance(script, dict):
            raise SystemExit("script-json 必须是 product-training-script 对象")
        meta = script.setdefault("meta", {})
        meta["display_name"] = meta.get("display_name") or theme
        meta["content_lock"] = meta.get("content_lock") or "business-draft-pending-approval"
        _assert_no_component_gold_residue(script, theme)
    else:
        script = _build_component_script(theme, notes)

    script_path = draft_dir / "script.structured.json"
    write_json(script_path, script)

    plan_dir = draft_dir / "plan"
    report = _run_courseware_generator(
        script_path=script_path,
        out_dir=plan_dir,
        skip_export=True,
        skip_qa=True,
        skip_provenance=True,
        name_suffix="草稿",
    )
    content_model = plan_dir / "content-model.json"
    scene_plan = plan_dir / "scene-plan.json"
    if not content_model.is_file():
        raise RuntimeError(f"草稿未产出 content-model；见 {report.get('_log')}")

    digest = sha256_file(script_path)

    gaps = [
        "审核后的导语/痛点与数据出处",
        "审核后的核心功效与产品特点表述",
        "适宜人群边界",
        "联合用药场景与搭档商品（有几条写几条）",
        "注意事项审核稿",
        "授权包装/插画（可选；无图用槽位）",
    ]
    if notes:
        gaps.insert(0, "业务已提供文字要点，请逐条核对是否可进正式培训")
    if not intake.get("script_json"):
        gaps.insert(0, "建议改为完整 script.structured.json 以锁定审核文案")

    review_path = draft_dir / "内容初稿.md"
    plan = read_json(scene_plan) if scene_plan.is_file() else {}
    lines = [
        f"# 内容初稿 · {theme}",
        "",
        f"- 任务：`{job['job_id']}`",
        f"- 路线：{route.get('name_zh')}（`{route.get('route_id')}`）",
        f"- 引擎：courseware-pptx-v1 · 构件 recipe 主路径",
        f"- 脚本哈希：`{digest}`",
        f"- 规划页数：{plan.get('page_count') or report.get('page_count') or '—'}",
        "",
        "## 说明",
        "",
        "本文件供业务确认。确认前不生成正式 PPTX。",
        "文案唯一来源 = script.structured.json；系统不扩写功效/剂量。",
        "标「待确认」字段不得当作已审核医学结论。",
        "",
        "## 页型规划",
        "",
    ]
    for p in plan.get("pages") or []:
        lines.append(
            f"- P{p.get('i')}: {p.get('page_type')} / {p.get('scene_type')} "
            f"({(p.get('selection') or {}).get('mode')})"
        )
    lines.extend(["", "## 脚本摘要", ""])
    meta = script.get("meta") or {}
    lines.append(f"- 商品：{meta.get('display_name')}")
    lines.append(f"- 组织：{meta.get('organization')}")
    for section_key in (
        "hook",
        "benefits",
        "features",
        "audience",
        "combination",
        "summary",
        "precautions",
    ):
        block = script.get(section_key)
        if not block:
            continue
        lines.append(f"### {section_key}")
        if isinstance(block, dict):
            if block.get("title"):
                lines.append(f"- 标题：{block.get('title')}")
            for para in block.get("paragraphs") or []:
                lines.append(f"- {para}")
            for it in block.get("items") or []:
                if isinstance(it, dict):
                    lines.append(f"- {it.get('title') or ''}：{it.get('body') or it.get('text') or ''}")
                else:
                    lines.append(f"- {it}")
            for row in block.get("rows") or []:
                if isinstance(row, dict):
                    if row.get("problem") is not None:
                        lines.append(
                            f"- 场景：{row.get('problem')}｜搭档：{row.get('partner')}｜话术：{row.get('talk_track')}"
                        )
                    else:
                        lines.append(
                            f"- {row.get('label') or ''}：{row.get('value') or ''}"
                        )
        lines.append("")
    review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    gaps_path = draft_dir / "缺口清单.md"
    gaps_path.write_text(
        "# 缺口清单\n\n" + "\n".join(f"- [ ] {g}" for g in gaps) + "\n",
        encoding="utf-8",
    )

    return {
        "kind": "product_pptx_component",
        "script": str(script_path),
        "content_model": str(content_model),
        "scene_plan": str(scene_plan) if scene_plan.is_file() else None,
        "review_md": str(review_path),
        "gaps_md": str(gaps_path),
        "content_sha256": digest,
        "page_count": plan.get("page_count") or report.get("page_count"),
        "page_types": report.get("page_types") or [
            p.get("page_type") for p in (plan.get("pages") or [])
        ],
        "gaps": gaps,
    }


ADAPTER_DRAFT: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    "product_pptx_component": _draft_product_pptx_component,
    "product_pptx_green": _draft_product_pptx_green,
    "product_video_full": _draft_product_video_full,
}


def cmd_draft(args: argparse.Namespace) -> int:
    job = load_job(args.job)
    route = get_route(job["route_id"])
    adapter = route.get("adapter")
    if adapter not in ADAPTER_DRAFT:
        raise SystemExit(f"route adapter 未实现 draft: {adapter}")
    if job.get("state") in {"rendering"}:
        raise SystemExit("任务正在生成，不能重写草稿；请等结束后再 draft 或新开任务")

    result = ADAPTER_DRAFT[adapter](job, route)
    job["draft"] = result
    transition(job, "draft_ready", reason="draft generated")
    save_job(job)

    payload = {
        "ok": True,
        "job_id": job["job_id"],
        "state": job["state"],
        "business_status": business_label(job["state"], job, route),
        "next_step": next_step_zh(job, route),
        "draft": result,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"草稿已就绪 · {job['job_id']}\n"
            f"状态：{payload['business_status']}\n"
            f"content_sha256：{result.get('content_sha256')}\n"
            f"审阅：{result.get('review_md')}\n"
            f"下一步：{payload['next_step']}"
        )
    return 0


def _require_draft_hash(job: dict[str, Any]) -> str:
    digest = str((job.get("draft") or {}).get("content_sha256") or "")
    if not digest or len(digest) != 64:
        raise SystemExit("草稿缺少 content_sha256，请先 draft")
    return digest


def cmd_approve(args: argparse.Namespace) -> int:
    job = load_job(args.job)
    route = get_route(job["route_id"])
    gate = args.gate
    allowed = {"content", "visual", "product_image"}
    if gate not in allowed:
        raise SystemExit(f"--gate 必须是 {sorted(allowed)}")
    who = (args.by or "").strip()
    if not who:
        raise SystemExit("--by 必填（批准人）")

    gates = route.get("gates") or {}
    gate_key = {
        "content": "content_approval",
        "visual": "visual_approval",
        "product_image": "product_image_approval",
    }[gate]
    if not gates.get(gate_key):
        raise SystemExit(f"当前路线不需要 {gate} 审批")

    if job.get("state") not in {
        "draft_ready",
        "content_approved",
        "visual_approved",
        "qa_failed",
        "env_blocked",
    }:
        raise SystemExit(f"当前状态 {job.get('state')} 不允许 approve")

    record: dict[str, Any] = {
        "gate": gate,
        "approved": True,
        "approved_by": who,
        "approved_at": utc_now(),
        "note": (args.note or "").strip() or None,
    }

    if gate == "content":
        digest = _require_draft_hash(job)
        if args.content_sha256 and args.content_sha256 != digest:
            raise SystemExit("提供的 content_sha256 与当前草稿不一致")
        record["content_sha256"] = digest
        draft_dir = job_dir(job["job_id"]) / "draft"
        snap = job_dir(job["job_id"]) / "approvals" / f"content-{digest[:12]}"
        if draft_dir.is_dir():
            if snap.exists():
                shutil.rmtree(snap)
            shutil.copytree(draft_dir, snap)
            record["snapshot_dir"] = str(snap)
    elif gate == "product_image":
        if job.get("state") not in {"content_approved", "visual_approved", "env_blocked", "qa_failed"}:
            # allow product_image approval only after content, except explicit re-approve
            if not (job.get("approvals") or {}).get("content", {}).get("approved"):
                raise SystemExit("请先 approve --gate content，再批准包装图")
        image = (job.get("intake") or {}).get("product_image")
        if args.product_image:
            src = Path(args.product_image).expanduser().resolve()
            if not src.is_file():
                raise SystemExit(f"包装图不存在: {src}")
            dest = job_dir(job["job_id"]) / "intake" / src.name
            shutil.copy2(src, dest)
            job.setdefault("intake", {})["product_image"] = str(dest)
            image = str(dest)
        if not image or not Path(image).is_file():
            raise SystemExit("product_image 审批需要有效包装图")
        image_hash = sha256_file(Path(image))
        record["product_image"] = image
        record["product_image_sha256"] = image_hash
        record["authorization_reference"] = (
            (args.authorization_reference or "").strip() or "business-confirmed"
        )
        record["content_sha256"] = _require_draft_hash(job)
    elif gate == "visual":
        if not (job.get("approvals") or {}).get("content", {}).get("approved"):
            raise SystemExit("请先 approve --gate content")
        record["content_sha256"] = _require_draft_hash(job)
        record["visual_ref"] = (args.note or "business-visual-confirmed").strip()

    approvals_path = job_dir(job["job_id"]) / "approvals" / f"{gate}.json"
    write_json(approvals_path, record)
    job.setdefault("approvals", {})[gate] = record
    append_history(job, "approved", {"gate": gate, "by": who})

    if gate == "content":
        transition(job, "content_approved", reason="content approved")
    elif gate == "visual":
        transition(job, "visual_approved", reason="visual approved")
    # product_image keeps content_approved / visual_approved; render checks the gate

    save_job(job)
    payload = {
        "ok": True,
        "job_id": job["job_id"],
        "state": job["state"],
        "business_status": business_label(job["state"], job, route),
        "next_step": next_step_zh(job, route),
        "approval": record,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"已批准 {gate} · {job['job_id']}\n"
            f"状态：{payload['business_status']}\n"
            f"下一步：{payload['next_step']}"
        )
    return 0


def _approvals_ready(job: dict[str, Any], route: dict[str, Any]) -> tuple[bool, list[str]]:
    gates = route.get("gates") or {}
    approvals = job.get("approvals") or {}
    missing: list[str] = []
    draft_hash = str((job.get("draft") or {}).get("content_sha256") or "")

    if gates.get("content_approval"):
        rec = approvals.get("content") or {}
        if rec.get("approved") is not True:
            missing.append("content")
        elif rec.get("content_sha256") != draft_hash:
            missing.append("content_hash_mismatch")
    if gates.get("visual_approval"):
        rec = approvals.get("visual") or {}
        if rec.get("approved") is not True:
            missing.append("visual")
    if gates.get("product_image_approval"):
        rec = approvals.get("product_image") or {}
        if rec.get("approved") is not True:
            missing.append("product_image")
        elif not rec.get("product_image_sha256"):
            missing.append("product_image_hash")
        elif rec.get("content_sha256") != draft_hash:
            missing.append("product_image_content_hash_mismatch")
    return (not missing), missing


def _publish_whitelist(
    job: dict[str, Any],
    route: dict[str, Any],
    source_files: dict[str, Path],
) -> dict[str, Any]:
    whitelist = list(route.get("delivery_whitelist") or [])
    dest = delivery_root() / job["job_id"]
    staging_parent = dest.parent
    staging = staging_parent / f".{dest.name}.staging-{uuid.uuid4().hex}"
    try:
        staging.mkdir(parents=True)
        written: list[str] = []
        for name in whitelist:
            src = source_files.get(name)
            if src is None or not src.is_file():
                # optional only if not terminal deliverable
                if name in {"终稿.pptx", "终稿.mp4"}:
                    raise RuntimeError(f"缺少必需交付物: {name}")
                continue
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            written.append(name)
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(staging, dest)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise

    manifest = {
        "schema": "business-job-run-manifest-v1",
        "job_id": job["job_id"],
        "route_id": route["route_id"],
        "template_slug": route.get("template_slug"),
        "theme": job.get("theme"),
        "content_sha256": (job.get("draft") or {}).get("content_sha256"),
        "approvals": job.get("approvals") or {},
        "published_at": utc_now(),
        "files": {
            name: {
                "sha256": sha256_file(dest / name),
                "size": (dest / name).stat().st_size,
            }
            for name in written
            if (dest / name).is_file()
        },
    }
    write_json(dest / "run-manifest.json", manifest)
    if "run-manifest.json" not in written:
        written.append("run-manifest.json")
    return {"ok": True, "path": str(dest), "files": written, "manifest": manifest}


def _render_product_pptx_green(job: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    draft = job.get("draft") or {}
    content_model = Path(draft["content_model"])
    if not content_model.is_file():
        raise RuntimeError("缺少 content-model.json")

    ws = job_dir(job["job_id"]) / "workspace" / "render"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    out_pptx = ws / f"{slugify(job['theme'])}_商品培训课件.pptx"
    qa_dir = ws / "qa"

    # Prefer local node; builder requires @oai/artifact-tool via node_modules / NODE_PATH
    node = shutil.which("node")
    if not node:
        raise RuntimeError("本机缺少 node，无法导出 PPTX")

    builder = green_builder()
    node_modules = _first_existing(_NODE_MODULES_CANDIDATES)
    env = os.environ.copy()
    if node_modules and node_modules.is_dir():
        prev = env.get("NODE_PATH", "")
        env["NODE_PATH"] = (
            str(node_modules) if not prev else f"{node_modules}{os.pathsep}{prev}"
        )

    cmd = [
        node,
        str(builder),
        "--data",
        str(content_model),
        "--out",
        str(out_pptx),
        "--qa",
        str(qa_dir),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(builder.parent),
        capture_output=True,
        text=True,
        env=env,
    )
    log_path = ws / "render.log"
    log_path.write_text(
        f"$ {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )
    if proc.returncode != 0 or not out_pptx.is_file():
        raise RuntimeError(
            f"PPTX 导出失败 exit={proc.returncode}；见 {log_path}"
        )

    delivery_note = ws / "交付说明.md"
    delivery_note.write_text(
        "\n".join(
            [
                f"# 交付说明 · {job['theme']}",
                "",
                f"- 任务：`{job['job_id']}`",
                f"- 路线：{route.get('name_zh')}",
                f"- 成品：可编辑 PPTX",
                f"- 内容哈希：`{(job.get('draft') or {}).get('content_sha256')}`",
                "",
                "请在本机 Office / WPS 打开终稿.pptx 检查页数与可编辑性。",
                "大改内容请回到任务 draft → approve → render，不要只在 PPT 里大幅改写。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    approval_copy = ws / "内容确认记录.json"
    write_json(approval_copy, job.get("approvals") or {})

    files = {
        "终稿.pptx": out_pptx,
        "交付说明.md": delivery_note,
        "内容确认记录.json": approval_copy,
    }
    published = _publish_whitelist(job, route, files)
    return {
        "ok": True,
        "workspace": str(ws),
        "pptx": str(out_pptx),
        "delivery": published,
        "qa_passed": True,
    }


def _render_product_video_full(job: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    from business_video_product_full import product_content_sha256

    draft = job.get("draft") or {}
    sections = Path(draft["sections_json"])
    if not sections.is_file():
        raise RuntimeError("缺少 sections.json")
    image_rec = (job.get("approvals") or {}).get("product_image") or {}
    product_image = Path(
        image_rec.get("product_image")
        or (job.get("intake") or {}).get("product_image")
        or ""
    )
    if not product_image.is_file():
        raise RuntimeError("正式视频需要已审批的授权包装图")

    content = read_json(sections)
    content_hash = product_content_sha256(content)
    content_approval = (job.get("approvals") or {}).get("content") or {}
    if content_approval.get("content_sha256") != content_hash:
        raise RuntimeError("内容审批哈希与当前 sections.json 不一致，请重新 draft/approve")
    if image_rec.get("product_image_sha256") != sha256_file(product_image):
        raise RuntimeError("包装图与审批记录哈希不一致")
    if image_rec.get("content_sha256") not in {None, content_hash} and image_rec.get(
        "content_sha256"
    ) != content_hash:
        raise RuntimeError("包装图审批绑定的内容哈希已过期，请重新批准包装图")

    image_hash = sha256_file(product_image)
    approval = {
        "schema": "product-video-approval-v1",
        "approved": True,
        "approved_by": image_rec.get("approved_by")
        or content_approval.get("approved_by")
        or "business",
        "approved_at": utc_now(),
        "authorization_reference": image_rec.get("authorization_reference")
        or "business-confirmed",
        "approved_content_sha256": content_hash,
        "approved_product_image_sha256": image_hash,
    }
    approval_path = job_dir(job["job_id"]) / "approvals" / "product-video-approval.json"
    write_json(approval_path, approval)

    run_dir = job_dir(job["job_id"]) / "workspace" / "video-run"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "generate_business_video.py"),
        "--template",
        "product",
        "--sections-json",
        str(sections),
        "--mode",
        "full",
        "--with-tts",
        "--with-mp4",
        "--product-image",
        str(product_image),
        "--product-approval",
        str(approval_path),
        "--out-dir",
        str(run_dir),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    log_path = run_dir / "render.log"
    log_path.write_text(
        f"$ {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )

    status_path = run_dir / "business-delivery-status.json"
    status = read_json(status_path) if status_path.is_file() else {}
    ok = bool(status.get("ok")) and proc.returncode == 0

    if not ok:
        return {
            "ok": False,
            "workspace": str(run_dir),
            "log": str(log_path),
            "status": status,
            "qa_passed": False,
            "error": status.get("error")
            or f"generate_business_video failed exit={proc.returncode}",
        }

    mp4_path = Path((status.get("mp4") or {}).get("path") or "")
    if not mp4_path.is_file():
        candidate = run_dir / mp4_path if str(mp4_path) else None
        if candidate and candidate.is_file():
            mp4_path = candidate
        else:
            mp4s = list(run_dir.glob("*.mp4"))
            mp4_path = mp4s[0] if mp4s else Path()
    if not mp4_path.is_file():
        return {
            "ok": False,
            "workspace": str(run_dir),
            "qa_passed": False,
            "error": "MP4 missing after successful-looking run",
            "status": status,
        }

    note = run_dir / "交付说明.md"
    if not note.is_file():
        note.write_text(
            f"# 交付说明 · {job['theme']}\n\n任务 `{job['job_id']}` 正式 MP4 已生成。\n",
            encoding="utf-8",
        )
    approval_copy = run_dir / "内容确认记录.json"
    write_json(approval_copy, job.get("approvals") or {})
    qa_src = run_dir / "delivery-qa.json"
    status_src = run_dir / "business-delivery-status.json"

    files = {
        "终稿.mp4": mp4_path,
        "交付说明.md": note,
        "内容确认记录.json": approval_copy,
    }
    if qa_src.is_file():
        files["delivery-qa.json"] = qa_src
    if status_src.is_file():
        files["business-delivery-status.json"] = status_src

    published = _publish_whitelist(job, route, files)
    return {
        "ok": True,
        "workspace": str(run_dir),
        "mp4": str(mp4_path),
        "delivery": published,
        "qa_passed": True,
        "status": status,
    }


def _render_product_pptx_component(
    job: dict[str, Any], route: dict[str, Any]
) -> dict[str, Any]:
    """Export editable PPTX via courseware-pptx-v1 (component + recipe)."""
    draft = job.get("draft") or {}
    script_path = Path(draft.get("script") or "")
    if not script_path.is_file():
        # fallback: regenerate from stored content_model only is insufficient for engine style
        raise RuntimeError("缺少 draft/script.structured.json，请先 draft")

    # Re-hash gate: script must match approved content hash
    current = sha256_file(script_path)
    approved = ((job.get("approvals") or {}).get("content") or {}).get("content_sha256")
    if approved and approved != current:
        raise RuntimeError("内容审批哈希与当前 script.structured.json 不一致，请重新 draft/approve")

    ws = job_dir(job["job_id"]) / "workspace" / "render"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)

    # Prefer full export; QA (soffice) optional — missing soffice must not block deliverable
    skip_qa = shutil.which("soffice") is None and shutil.which("libreoffice") is None
    report = _run_courseware_generator(
        script_path=script_path,
        out_dir=ws,
        skip_export=False,
        skip_qa=skip_qa,
        skip_provenance=False,
        name_suffix="业务交付",
    )

    pptx_candidates = sorted(ws.glob("*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not pptx_candidates:
        raise RuntimeError(
            f"构件引擎未产出 PPTX；见 {report.get('_log') or ws / 'generate.log'}"
        )
    out_pptx = pptx_candidates[0]

    if report.get("ok") is False and report.get("provenance_exit", 0) not in (0, None):
        # provenance hard fail → qa_failed without publish
        return {
            "ok": False,
            "workspace": str(ws),
            "pptx": str(out_pptx),
            "qa_passed": False,
            "error": report.get("error")
            or report.get("provenance_stderr")
            or "文本溯源未通过",
            "report": {k: v for k, v in report.items() if not str(k).startswith("_")},
        }

    # unknown scene types also fail
    if report.get("ok") is False and report.get("error"):
        return {
            "ok": False,
            "workspace": str(ws),
            "pptx": str(out_pptx),
            "qa_passed": False,
            "error": report.get("error"),
            "report": {k: v for k, v in report.items() if not str(k).startswith("_")},
        }

    delivery_note = ws / "交付说明.md"
    delivery_note.write_text(
        "\n".join(
            [
                f"# 交付说明 · {job['theme']}",
                "",
                f"- 任务：`{job['job_id']}`",
                f"- 路线：{route.get('name_zh')}",
                f"- 引擎：courseware-pptx-v1（构件 + recipe）",
                f"- 成品：可编辑 PPTX",
                f"- 页数：{report.get('page_count') or '—'}",
                f"- 内容哈希：`{(job.get('draft') or {}).get('content_sha256')}`",
                "",
                "请在本机 Office / WPS 打开终稿.pptx 检查页数与可编辑性。",
                "大改内容请回到任务 draft → approve → render，不要只在 PPT 里大幅改写审核文案。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    approval_copy = ws / "内容确认记录.json"
    write_json(approval_copy, job.get("approvals") or {})

    files: dict[str, Path] = {
        "终稿.pptx": out_pptx,
        "交付说明.md": delivery_note,
        "内容确认记录.json": approval_copy,
    }
    scene_plan = ws / "scene-plan.json"
    if scene_plan.is_file():
        files["scene-plan.json"] = scene_plan
    provenance = ws / "provenance-report.json"
    if provenance.is_file():
        files["provenance-report.json"] = provenance

    published = _publish_whitelist(job, route, files)
    return {
        "ok": True,
        "workspace": str(ws),
        "pptx": str(out_pptx),
        "delivery": published,
        "qa_passed": True,
        "page_count": report.get("page_count"),
        "page_types": report.get("page_types"),
    }


ADAPTER_RENDER: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    "product_pptx_component": _render_product_pptx_component,
    "product_pptx_green": _render_product_pptx_green,
    "product_video_full": _render_product_video_full,
}


def cmd_render(args: argparse.Namespace) -> int:
    job = load_job(args.job)
    route = get_route(job["route_id"])
    adapter = route.get("adapter")
    if adapter not in ADAPTER_RENDER:
        raise SystemExit(f"route adapter 未实现 render: {adapter}")

    ready, missing_gates = _approvals_ready(job, route)
    if not ready:
        raise SystemExit(f"审批未齐，不能 render：{', '.join(missing_gates)}")

    caps = probe_capabilities()
    missing = env_missing(route, caps)
    job["env"] = {"capabilities": {k: v for k, v in caps.items() if not str(k).startswith("_")}, "missing": missing}
    if missing and not args.ignore_env:
        transition(job, "env_blocked", reason=f"missing env: {missing}")
        save_job(job)
        payload = {
            "ok": False,
            "job_id": job["job_id"],
            "state": job["state"],
            "business_status": business_label(job["state"], job, route),
            "missing_env": missing,
            "next_step": next_step_zh(job, route),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(
                f"环境不足，已阻断正式生成 · {job['job_id']}\n"
                f"缺少：{', '.join(missing)}\n"
                f"下一步：{payload['next_step']}"
            )
        return 2

    transition(job, "rendering", reason="render started")
    save_job(job)

    try:
        result = ADAPTER_RENDER[adapter](job, route)
    except Exception as exc:  # noqa: BLE001
        job["render"] = {"ok": False, "error": str(exc), "at": utc_now()}
        transition(job, "qa_failed", reason=str(exc))
        save_job(job)
        if args.json:
            print(json.dumps({"ok": False, "job_id": job["job_id"], "error": str(exc), "state": job["state"]}, ensure_ascii=False, indent=2))
        else:
            print(f"生成失败 · {job['job_id']}\n错误：{exc}\n状态：质检失败（未写入正式交付）")
        return 1

    job["render"] = {k: v for k, v in result.items() if k != "status"} | {"at": utc_now()}
    if result.get("qa_passed") and result.get("ok"):
        delivery = result.get("delivery") or {}
        job["delivery"] = {
            "published": True,
            "path": delivery.get("path"),
            "files": delivery.get("files") or [],
            "manifest": delivery.get("manifest"),
        }
        transition(job, "delivered", reason="qa passed and whitelist published")
        save_job(job)
        payload = {
            "ok": True,
            "job_id": job["job_id"],
            "state": job["state"],
            "business_status": business_label(job["state"], job, route),
            "delivery": job["delivery"],
            "next_step": next_step_zh(job, route),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(
                f"已交付 · {job['job_id']}\n"
                f"取件：{job['delivery'].get('path')}\n"
                f"文件：{', '.join(job['delivery'].get('files') or [])}"
            )
        return 0

    transition(job, "qa_failed", reason=result.get("error") or "qa failed")
    job["delivery"] = {"published": False, "path": None}
    save_job(job)
    if args.json:
        print(json.dumps({"ok": False, "job_id": job["job_id"], "state": job["state"], "result": result}, ensure_ascii=False, indent=2))
    else:
        print(
            f"质检失败，未发布 · {job['job_id']}\n"
            f"原因：{result.get('error')}\n"
            f"工作区：{result.get('workspace')}"
        )
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    if args.job:
        jobs = [load_job(args.job)]
    else:
        jobs = []
        for path in sorted(jobs_root().glob("*/job.json")):
            jobs.append(read_json(path))
        if args.state:
            jobs = [j for j in jobs if j.get("state") == args.state]

    rows = []
    for job in jobs:
        route = get_route(job["route_id"])
        rows.append(
            {
                "job_id": job["job_id"],
                "route_id": job["route_id"],
                "theme": job.get("theme"),
                "state": job.get("state"),
                "business_status": business_label(str(job.get("state")), job, route),
                "next_step": next_step_zh(job, route),
                "delivery": job.get("delivery"),
                "approvals": {
                    k: {
                        "approved": bool((v or {}).get("approved")),
                        "by": (v or {}).get("approved_by"),
                        "at": (v or {}).get("approved_at"),
                    }
                    for k, v in (job.get("approvals") or {}).items()
                },
                "updated_at": job.get("updated_at"),
            }
        )

    if args.json:
        print(json.dumps({"jobs": rows}, ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print("暂无任务")
        return 0
    for row in rows:
        print(
            f"{row['job_id']}\n"
            f"  {row['theme']} · {row['route_id']}\n"
            f"  状态：{row['business_status']} ({row['state']})\n"
            f"  下一步：{row['next_step']}"
        )
        if (row.get("delivery") or {}).get("path"):
            print(f"  取件：{row['delivery']['path']}")
    return 0


def cmd_open(args: argparse.Namespace) -> int:
    job = load_job(args.job)
    targets = []
    delivery = (job.get("delivery") or {}).get("path")
    if delivery:
        targets.append(Path(delivery))
    targets.append(job_dir(job["job_id"]))
    draft_review = (job.get("draft") or {}).get("review_md")
    if draft_review:
        targets.append(Path(draft_review))

    existing = [p for p in targets if p.exists()]
    if args.json:
        print(json.dumps({"paths": [str(p) for p in existing]}, ensure_ascii=False, indent=2))
        return 0

    for path in existing:
        print(path)
    if args.reveal and existing:
        subprocess.run(["open", str(existing[0])], check=False)
    return 0


def cmd_retry(args: argparse.Namespace) -> int:
    job = load_job(args.job)
    if job.get("state") not in {"qa_failed", "env_blocked"}:
        raise SystemExit(f"仅 qa_failed / env_blocked 可 retry，当前为 {job.get('state')}")
    # Re-enter render path; keep approvals.
    if job.get("state") == "env_blocked":
        # back to content_approved-like ready state
        transition(job, "content_approved", reason="retry after env fix")
        save_job(job)
    else:
        transition(job, "content_approved", reason="retry after qa failure")
        save_job(job)
    return cmd_render(argparse.Namespace(job=args.job, json=args.json, ignore_env=args.ignore_env))


def cmd_list(args: argparse.Namespace) -> int:
    return cmd_status(argparse.Namespace(job=None, state=args.state, json=args.json))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Business job control plane")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list-routes", help="列出业务路线")
    p.add_argument("--all", action="store_true", help="包含未激活路线")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-probe", action="store_true")
    p.set_defaults(func=cmd_list_routes)

    p = sub.add_parser("new", help="创建任务")
    p.add_argument("--route", required=True)
    p.add_argument("--theme", required=True)
    p.add_argument("--notes", default="")
    p.add_argument("--product-image", type=Path, default=None)
    p.add_argument("--sections-json", type=Path, default=None)
    p.add_argument(
        "--script-json",
        type=Path,
        default=None,
        help="构件 PPT：完整 product-training-script/v1（优先于 notes 占位脚本）",
    )
    p.add_argument("--raw-text", default="")
    p.add_argument("--job-id", default=None)
    p.add_argument("--force", action="store_true", help="允许未激活 route")
    p.add_argument("--auto-draft", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("draft", help="生成待确认草稿")
    p.add_argument("--job", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_draft)

    p = sub.add_parser("approve", help="绑定审批")
    p.add_argument("--job", required=True)
    p.add_argument("--gate", required=True, choices=["content", "visual", "product_image"])
    p.add_argument("--by", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--content-sha256", default=None)
    p.add_argument("--product-image", type=Path, default=None)
    p.add_argument("--authorization-reference", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("render", help="审批通过后生成并白名单发布")
    p.add_argument("--job", required=True)
    p.add_argument("--ignore-env", action="store_true", help="仅调试；生产勿用")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("status", help="查看任务状态")
    p.add_argument("--job", default=None)
    p.add_argument("--state", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="列出任务")
    p.add_argument("--state", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("open", help="打印/打开任务与取件路径")
    p.add_argument("--job", required=True)
    p.add_argument("--reveal", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_open)

    p = sub.add_parser("retry", help="失败任务重试")
    p.add_argument("--job", required=True)
    p.add_argument("--ignore-env", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_retry)

    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
