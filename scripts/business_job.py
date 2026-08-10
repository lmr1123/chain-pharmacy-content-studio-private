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

UAT simulation is explicitly isolated with ``--scope uat``:
  outputs/workbuddy-workspaces/uat/jobs/<job_id>/
  outputs/workbuddy-workspaces/uat/delivery/<job_id>/
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from product_pptx_asset_plan import (
    build_product_pptx_asset_plan,
    formal_render_blockers,
    render_asset_plan_markdown,
)
import recommend_business_route as route_recommender


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
    ROOT / "production-library" / "styles" / "reference-product-blue-v1" / "tokens.json"
)
_COMPONENT_RECIPES = (
    ROOT / "production-library" / "page-types" / "product-training" / "recipes"
)
_COMPONENT_REGISTRY = (
    ROOT / "production-library" / "page-types" / "product-training" / "registry.json"
)
_DISEASE_ENGINE_DIR = (
    ROOT / "production-library" / "engines" / "disease-product-scenario-pptx-v1"
)
_DISEASE_EXPORT = _DISEASE_ENGINE_DIR / "export.mjs"
_DISEASE_SAMPLE = _DISEASE_ENGINE_DIR / "samples" / "neutral-theme.json"
_DISEASE_STYLE = (
    ROOT / "production-library" / "styles" / "dashenlin-courseware-green-v1" / "tokens.json"
)

_COURSEWARE3_ENGINE_DIR = ROOT / "production-library" / "engines" / "courseware3-pptx-v1"
_COURSEWARE3_EXPORT = _COURSEWARE3_ENGINE_DIR / "export.mjs"
_COURSEWARE3_REPLICATOR = ROOT / "scripts" / "replicate_courseware_theme.py"
_COURSEWARE3_GOLD = (
    ROOT / "production-library" / "validation" / "courseware" / "sufuda-product-courseware-3-gold-v1"
)

_INGREDIENT_HEALTH_ENGINE_DIR = (
    ROOT / "production-library" / "engines" / "ingredient-health-edu-pptx-v1"
)
_INGREDIENT_HEALTH_EXPORT = _INGREDIENT_HEALTH_ENGINE_DIR / "export.mjs"
_INGREDIENT_HEALTH_SETTLED = (
    ROOT
    / "production-library"
    / "templates"
    / "settled"
    / "kangaisen-lycopene-health-edu-v1"
)

_VALID_SCOPES = ("production", "uat")
_ACTIVE_SCOPE = "production"
_PRESENTATION_SUFFIXES = {".ppt", ".pptx"}
_MACOS_WPS_APP_CANDIDATES = (
    Path("/Applications/wpsoffice.app"),
    Path("/Applications/WPS Office.app"),
    Path.home() / "Applications" / "wpsoffice.app",
    Path.home() / "Applications" / "WPS Office.app",
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


def set_active_scope(scope: str) -> None:
    global _ACTIVE_SCOPE
    if scope not in _VALID_SCOPES:
        raise SystemExit(f"未知任务 scope: {scope}")
    _ACTIVE_SCOPE = scope


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
    if _ACTIVE_SCOPE == "uat":
        path = ROOT / "outputs" / "workbuddy-workspaces" / "uat" / "jobs"
    else:
        rel = load_routes_doc().get("job_workspace_rel") or "outputs/workbuddy-workspaces/jobs"
        path = ROOT / rel
    path.mkdir(parents=True, exist_ok=True)
    return path


def delivery_root() -> Path:
    if _ACTIVE_SCOPE == "uat":
        path = ROOT / "outputs" / "workbuddy-workspaces" / "uat" / "delivery"
    else:
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


def settled_manifest(slug: str | None) -> dict[str, Any]:
    if not slug:
        return {}
    path = ROOT / "production-library" / "templates" / "settled" / slug / "manifest.json"
    if not path.is_file():
        return {}
    data = read_json(path)
    return data if isinstance(data, dict) else {}


def business_label(state: str, job: dict[str, Any] | None = None, route: dict[str, Any] | None = None) -> str:
    """Map internal state to unambiguous business-facing Chinese labels."""
    if state == "qa_failed":
        return "质检失败"
    if state == "delivered":
        return "已交付"
    if state == "env_blocked":
        return "环境不足"
    if state == "rendering":
        return "正在生成"
    if state == "visual_approved":
        gates = (route or {}).get("gates") or {}
        approvals = (job or {}).get("approvals") or {}
        if gates.get("product_image_approval") and not (
            approvals.get("product_image") or {}
        ).get("approved"):
            return "等待业务资料"
        return "可开始生成"
    if state == "content_approved":
        gates = (route or {}).get("gates") or {}
        approvals = (job or {}).get("approvals") or {}
        if route.get("adapter") == "product_pptx_component" and gates.get(
            "visual_approval"
        ) and not (approvals.get("visual") or {}).get("approved"):
            return "等待视觉确认"
        if gates.get("product_image_approval") and not (
            approvals.get("product_image") or {}
        ).get("approved"):
            return "等待业务资料"
        if gates.get("visual_approval") and not (approvals.get("visual") or {}).get("approved"):
            return "等待视觉确认"
        return "可开始生成"
    states = load_routes_doc().get("states") or {}
    return str(states.get(state) or state)


def next_step_zh(job: dict[str, Any], route: dict[str, Any]) -> str:
    state = job.get("state")
    gates = route.get("gates") or {}
    if state in (None, "intake", "needs_input"):
        return "补充主题/要点后生成初稿"
    if state == "draft_ready":
        if route.get("adapter") == "product_pptx_component":
            return "请业务确认内容；确认后由 WorkBuddy 补齐并实槽检查素材，再生成正式稿"
        return "请业务确认当前初稿，再继续审批与生成"
    if state == "content_approved":
        if route.get("adapter") == "product_pptx_component" and gates.get(
            "visual_approval"
        ) and not (
            (job.get("approvals") or {}).get("visual") or {}
        ).get("approved"):
            return "由 WorkBuddy 按素材计划生成并绑定插图，先给业务确认代表图"
        if gates.get("product_image_approval") and not (
            (job.get("approvals") or {}).get("product_image") or {}
        ).get("approved"):
            return "请提交并确认业务授权包装图"
        if gates.get("visual_approval") and not (
            (job.get("approvals") or {}).get("visual") or {}
        ).get("approved"):
            return "请确认当前画面稿"
        return "环境就绪后由 WorkBuddy 开始生成"
    if state == "visual_approved":
        if gates.get("product_image_approval") and not (
            (job.get("approvals") or {}).get("product_image") or {}
        ).get("approved"):
            return "请提交并确认业务授权包装图"
        return "环境就绪后由 WorkBuddy 开始生成"
    if state == "rendering":
        return "等待生成完成"
    if state == "env_blocked":
        missing = (job.get("env") or {}).get("missing") or []
        return "由 WorkBuddy 安装或修复缺失能力后重试：" + ("/".join(missing) if missing else "查看详情")
    if state == "qa_failed":
        return "由 WorkBuddy 查看诊断、修正后重新生成"
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
    job = read_json(path)
    scope = str(job.get("scope") or "production")
    if scope != _ACTIVE_SCOPE:
        raise SystemExit(
            f"任务 scope 不匹配：任务={scope}，当前={_ACTIVE_SCOPE}；请使用 --scope {scope}"
        )
    return job


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


def cmd_recommend(args: argparse.Namespace) -> int:
    """Recommend first; never create a job until business confirms the template."""
    if args.text and args.request:
        raise SystemExit("位置参数与 --text 只能使用一个")
    request = str(args.text or args.request or "").strip()
    if not request:
        raise SystemExit("请提供业务需求文本")
    capabilities: dict[str, bool] | None = None
    probe_warning: str | None = None
    if args.check_env:
        probed = probe_capabilities()
        if probed.get("_probe_error"):
            probe_warning = str(probed.get("_error") or "环境探测失败")
        else:
            capabilities = {
                str(name): bool(value) for name, value in probed.items()
            }
    try:
        result = route_recommender.recommend(
            request, capabilities=capabilities
        )
    except (
        OSError,
        json.JSONDecodeError,
        route_recommender.SelectorContractError,
        ValueError,
    ) as exc:
        raise SystemExit(f"路线推荐失败：{exc}") from exc
    if probe_warning:
        result["environment_checked"] = False
        result["environment_warning_zh"] = probe_warning

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        route_recommender._print_human(result)
        print("说明：这里只做推荐；业务确认课型前不会创建任务或生成成品。")
        if probe_warning:
            print(f"环境探测未完成：{probe_warning}")
    return 0 if result.get("decision") == "recommended" else 2


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
        intake["script_source_dir"] = str(src.parent)
        write_json(path / "intake" / "intake.json", intake)

    template_manifest = settled_manifest(route.get("template_slug"))
    job = {
        "schema": "business-job-v1",
        "scope": _ACTIVE_SCOPE,
        "job_id": job_id,
        "route_id": route["route_id"],
        "template_slug": route.get("template_slug"),
        "template_id": template_manifest.get("template_id"),
        "style_pack_id": template_manifest.get("style_pack_id") or route.get("style_pack_default"),
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
    append_history(
        job,
        "created",
        {"route_id": route["route_id"], "theme": theme, "scope": _ACTIVE_SCOPE},
    )
    save_job(job)

    if args.auto_draft:
        return cmd_draft(argparse.Namespace(job=job_id, json=args.json))

    payload = {
        "ok": True,
        "job_id": job_id,
        "scope": _ACTIVE_SCOPE,
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
    "宝宝去火",
    "小儿痱毒",
    "暑热口渴",
    "风热感冒",
    "清肺消炎",
    "毛利率高",
)

_GREEN_PENDING_MARKERS = (
    "待确认",
    "待接入",
    "待业务",
    "需确认",
    "asset://",
    "<generated-file>",
    "TODO",
    "TBD",
    "占位",
)


def _green_page_map(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(page.get("id") or ""): page
        for page in (model.get("pages") or [])
        if isinstance(page, dict)
    }


def _asset_source(spec: Any) -> str | None:
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        for key in ("file", "src", "asset"):
            value = spec.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _set_asset_source(container: Any, key: Any, value: str) -> None:
    spec = container[key]
    if isinstance(spec, dict):
        for field in ("file", "src", "asset"):
            if field in spec:
                spec[field] = value
                return
        spec["file"] = value
        return
    container[key] = value


def _green_asset_bindings(model: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    """Return every fixed-template image slot as (stable key, container, index/key)."""
    pages = _green_page_map(model)
    result: list[tuple[str, Any, Any]] = []

    overview = pages.get("product-overview") or {}
    product = overview.get("product") or {}
    if "image_slot" in product:
        result.append(("product-overview.product.image_slot", product, "image_slot"))

    combo = pages.get("combination-guidance") or {}
    for field in ("primary_asset", "primary_pack_asset", "product_asset"):
        if field in combo:
            result.append((f"combination-guidance.{field}", combo, field))
            break
    for index, row in enumerate(combo.get("rows") or []):
        if isinstance(row, dict) and "partner_asset" in row:
            result.append(
                (f"combination-guidance.rows[{index}].partner_asset", row, "partner_asset")
            )

    benchmark = pages.get("product-benchmark") or {}
    for row_index, row in enumerate(benchmark.get("rows") or []):
        if not isinstance(row, dict) or row.get("label") != "产品展示":
            continue
        values = row.get("values") or []
        for index in range(min(2, len(values))):
            result.append(
                (f"product-benchmark.rows[{row_index}].values[{index}]", values, index)
            )

    precautions = pages.get("precautions") or {}
    for index, slot in enumerate(precautions.get("illustration_slots") or []):
        if not isinstance(slot, dict):
            continue
        for field in ("asset", "file", "src"):
            if field in slot:
                result.append((f"precautions.illustration_slots[{index}].{field}", slot, field))
                break
    return result


def _bind_green_primary_image(model: dict[str, Any], image: Path) -> None:
    pages = _green_page_map(model)
    overview = pages.get("product-overview") or {}
    overview.setdefault("product", {})["image_slot"] = str(image)

    combo = pages.get("combination-guidance") or {}
    combo["primary_asset"] = str(image)
    combo["primary_pack_label"] = f"{overview.get('product', {}).get('display_name') or '本品'}包装图"

    benchmark = pages.get("product-benchmark") or {}
    for row in benchmark.get("rows") or []:
        if isinstance(row, dict) and row.get("label") == "产品展示":
            values = list(row.get("values") or [])
            while len(values) < 2:
                values.append("asset://product-packshot-competitor")
            values[0] = str(image)
            row["values"] = values
            break


def _snapshot_green_assets(
    job: dict[str, Any],
    model: dict[str, Any],
    *,
    source_dir: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Copy all resolvable fixed-template images into the job intake."""
    asset_dir = job_dir(job["job_id"]) / "intake" / "fixed-assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, Any]] = {}
    for index, (binding, container, key) in enumerate(_green_asset_bindings(model)):
        source_value = _asset_source(container[key])
        if not source_value or source_value.startswith("asset://"):
            continue
        source = Path(source_value).expanduser()
        if not source.is_absolute() and source_dir:
            source = source_dir / source
        source = source.resolve()
        if not source.is_file():
            continue
        suffix = source.suffix.lower() or ".png"
        digest = sha256_file(source)
        dest = asset_dir / f"{index:02d}-{digest[:12]}{suffix}"
        if source.resolve() != dest.resolve():
            shutil.copy2(source, dest)
        _set_asset_source(container, key, str(dest))
        manifest[binding] = {
            "file": str(dest),
            "sha256": sha256_file(dest),
            "size": dest.stat().st_size,
        }
    return manifest


def _green_content_digest(content_path: Path, model: dict[str, Any]) -> tuple[str, dict[str, dict[str, Any]]]:
    assets: dict[str, dict[str, Any]] = {}
    for binding, container, key in _green_asset_bindings(model):
        value = _asset_source(container[key])
        if not value or value.startswith("asset://"):
            continue
        file = Path(value)
        if file.is_file():
            assets[binding] = {
                "file": str(file),
                "sha256": sha256_file(file),
                "size": file.stat().st_size,
            }
    payload = {
        "content_model_sha256": sha256_file(content_path),
        "assets": {key: assets[key]["sha256"] for key in sorted(assets)},
    }
    digest = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return digest, assets


def _green_pending_fields(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, str):
        if any(marker in value for marker in _GREEN_PENDING_MARKERS):
            hits.append(path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_green_pending_fields(item, f"{path}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            hits.extend(_green_pending_fields(item, f"{path}.{key}"))
    return hits


def _green_formal_blockers(model: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    pages = _green_page_map(model)
    required = {
        "cover": "courseware_cover",
        "product-overview": "product_overview",
        "combination-guidance": "combination_guidance",
        "product-benchmark": "product_benchmark",
        "precautions": "precautions",
    }
    for page_id, scene_type in required.items():
        page = pages.get(page_id)
        if not page:
            blockers.append(f"缺少页面 {page_id}")
        elif page.get("scene_type") != scene_type:
            blockers.append(f"{page_id} scene_type 应为 {scene_type}")

    pending = _green_pending_fields(model)
    if pending:
        blockers.append("仍有待确认/占位字段：" + ", ".join(pending[:8]))

    overview = pages.get("product-overview") or {}
    product = overview.get("product") or {}
    for field in ("display_name", "code", "priority", "specification", "retail_price", "one_line_selling_point"):
        if not str(product.get(field) or "").strip():
            blockers.append(f"商品信息缺少 {field}")
    if not _asset_source(product.get("image_slot")):
        blockers.append("商品介绍页缺少本品包装图")
    for index, section in enumerate(overview.get("sections") or []):
        if not (section.get("items") or []):
            blockers.append(f"商品介绍 section[{index}] 没有审核内容")

    combo = pages.get("combination-guidance") or {}
    if not combo.get("rows"):
        blockers.append("联合用药页至少需要一条经审核内容")
    if not any(field in combo for field in ("primary_asset", "primary_pack_asset", "product_asset")):
        blockers.append("联合用药页缺少本品包装图")
    for index, row in enumerate(combo.get("rows") or []):
        for field in ("scenario", "combination", "partner", "talk_track"):
            if not str((row or {}).get(field) or "").strip():
                blockers.append(f"联合用药 rows[{index}] 缺少 {field}")
        if not _asset_source((row or {}).get("partner_asset")):
            blockers.append(f"联合用药 rows[{index}] 缺少搭档商品包装图")

    benchmark = pages.get("product-benchmark") or {}
    display_rows = [
        row
        for row in (benchmark.get("rows") or [])
        if isinstance(row, dict) and row.get("label") == "产品展示"
    ]
    if not display_rows or len(display_rows[0].get("values") or []) < 2:
        blockers.append("品种对标页缺少本品/竞品两张正式图片")

    precautions = pages.get("precautions") or {}
    if not precautions.get("items"):
        blockers.append("注意事项页没有审核内容")
    if len(precautions.get("illustration_slots") or []) != 4:
        blockers.append("注意事项页需要 4 张正式插图")

    for binding, container, key in _green_asset_bindings(model):
        source = _asset_source(container[key])
        if not source or source.startswith("asset://"):
            blockers.append(f"缺少正式图片 {binding}")
        elif not Path(source).is_file():
            blockers.append(f"图片文件不存在 {binding}: {source}")
    return list(dict.fromkeys(blockers))


def _assert_no_green_gold_residue(model: dict[str, Any], theme: str) -> None:
    """Hard guard: new-theme draft must not retain 金银花露 gold medical/price copy."""
    if "金银花露" in theme:
        return
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
    intake = job.get("intake") or {}
    notes = intake.get("notes") or ""
    script_path = Path(intake.get("script_json") or "")
    supplied_model = script_path.is_file()
    if supplied_model:
        candidate = read_json(script_path)
        if not isinstance(candidate, dict) or not isinstance(candidate.get("pages"), list):
            raise SystemExit("绿色标准课型 --script-json 必须是包含 pages[] 的完整 content-model")
        model = json.loads(json.dumps(candidate))
    else:
        gold = read_json(green_gold_json())
        model = json.loads(json.dumps(gold))  # deep copy
    model["project_id"] = f"business-job.{job['job_id']}"
    model["template_id"] = "template.product-courseware-dashenlin-green-v1"
    model["style_pack_id"] = "style-pack.dashenlin-courseware-green-v1"
    model["content_lock"] = "business-draft-pending-approval"
    model["style_pack_locked"] = True

    if supplied_model:
        pages = _green_page_map(model)
        cover = pages.get("cover") or {}
        cover["title"] = theme
        overview = pages.get("product-overview") or {}
        overview.setdefault("product", {})["display_name"] = theme
        combo = pages.get("combination-guidance") or {}
        combo["primary_pack_label"] = f"{theme}\n包装图"
        benchmark = pages.get("product-benchmark") or {}
        columns = list(benchmark.get("columns") or [])
        if len(columns) >= 2:
            columns[1] = theme
            benchmark["columns"] = columns
        for page in model.get("pages") or []:
            page["reference"] = "业务审核内容"
    else:
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
            page["reference"] = "业务审核内容"

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
                            "功能、用法用量：待业务审核稿确认",
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
                page["primary_asset"] = "asset://product-packshot-primary"
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
                # Never invent medical precautions for a new product.
                page["items"] = [
                    "注意事项 1（待确认）",
                    "注意事项 2（待确认）",
                    "注意事项 3（待确认）",
                    "注意事项 4（待确认）",
                ]
                page["illustration_slots"] = [
                    {
                        "title": f"注意事项插图 {index + 1}",
                        "asset": f"asset://precaution-placeholder-{index + 1}",
                    }
                    for index in range(4)
                ]

    _assert_no_green_gold_residue(model, theme)

    product_image = Path(intake.get("product_image") or "")
    if product_image.is_file():
        _bind_green_primary_image(model, product_image)
    source_dir_value = intake.get("script_source_dir")
    source_dir = Path(source_dir_value) if source_dir_value else None
    _snapshot_green_assets(job, model, source_dir=source_dir)

    if supplied_model:
        gaps = _green_formal_blockers(model)
    else:
        gaps = [
            "规格 / 编码 / 零售价",
            "审核后的功能主治与用法用量",
            "联合用药场景、搭档商品与销售话术",
            "竞品对标内容与竞品正式图片",
            "注意事项审核稿与 4 张正式插图",
            "本品与搭档商品授权包装图（正式生成必填）",
        ]
        if notes:
            gaps.insert(0, "业务已提供文字要点，请逐条核对是否可进正式培训")

    draft_dir = job_dir(job["job_id"]) / "draft"
    content_path = draft_dir / "content-model.json"
    review_path = draft_dir / "内容初稿.md"
    gaps_path = draft_dir / "缺口清单.md"
    asset_manifest_path = draft_dir / "asset-manifest.json"
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

    digest, asset_manifest = _green_content_digest(content_path, model)
    write_json(asset_manifest_path, asset_manifest)
    return {
        "kind": "product_pptx_green",
        "content_model": str(content_path),
        "review_md": str(review_path),
        "gaps_md": str(gaps_path),
        "asset_manifest_json": str(asset_manifest_path),
        "content_model_sha256": sha256_file(content_path),
        "content_sha256": digest,
        "gaps": gaps,
    }


_DISEASE_PENDING_MARKERS = _GREEN_PENDING_MARKERS + (
    "示例",
    "虚构",
    "演示",
    "非业务发布",
)
_DISEASE_GOLD_FORBIDDEN = (
    "穿心莲",
    "内酯滴丸",
    "风热证",
    "复方氨酚烷胺片",
    "安宫牛黄丸",
    "熊胆薄荷含片",
    "97%",
    "95%",
    "5–10分钟",
    "5-10分钟",
    "38℃",
)


def _disease_image_bindings(value: Any, path: str = "$") -> list[tuple[str, dict[str, Any], str]]:
    result: list[tuple[str, dict[str, Any], str]] = []
    if isinstance(value, list):
        for index, item in enumerate(value):
            result.extend(_disease_image_bindings(item, f"{path}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key == "image" and isinstance(item, str):
                result.append((child, value, key))
            else:
                result.extend(_disease_image_bindings(item, child))
    return result


def _bind_disease_primary_image(model: dict[str, Any], image: Path) -> None:
    model.setdefault("product", {})["image"] = str(image)
    model.setdefault("pages", {}).setdefault("cover", {})["image"] = str(image)


def _snapshot_disease_images(
    job: dict[str, Any],
    model: dict[str, Any],
    *,
    source_dir: Path | None,
) -> None:
    target = job_dir(job["job_id"]) / "intake" / "disease-assets"
    target.mkdir(parents=True, exist_ok=True)
    for index, (_binding, container, key) in enumerate(_disease_image_bindings(model)):
        raw = str(container.get(key) or "")
        if not raw or raw.startswith("asset://"):
            continue
        source = Path(raw).expanduser()
        if not source.is_absolute() and source_dir:
            source = source_dir / source
        source = source.resolve()
        if not source.is_file():
            continue
        digest = sha256_file(source)
        dest = target / f"{index:02d}-{digest[:12]}{source.suffix.lower() or '.png'}"
        if source.resolve() != dest.resolve():
            shutil.copy2(source, dest)
        container[key] = str(dest)


def _disease_content_digest(
    content_path: Path, model: dict[str, Any]
) -> tuple[str, dict[str, dict[str, Any]]]:
    assets: dict[str, dict[str, Any]] = {}
    for binding, container, key in _disease_image_bindings(model):
        source = Path(str(container.get(key) or ""))
        if source.is_file():
            assets[binding] = {
                "file": str(source),
                "sha256": sha256_file(source),
                "size": source.stat().st_size,
            }
    payload = {
        "content_model_sha256": sha256_file(content_path),
        "assets": {key: value["sha256"] for key, value in sorted(assets.items())},
    }
    return (
        sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
        assets,
    )


def _disease_formal_blockers(model: dict[str, Any], theme: str) -> list[str]:
    blockers: list[str] = []
    if model.get("schema_version") != "disease-product-scenario-script/v1":
        blockers.append("schema_version 必须是 disease-product-scenario-script/v1")
    blob = json.dumps(model, ensure_ascii=False)
    pending = [marker for marker in _DISEASE_PENDING_MARKERS if marker in blob]
    if pending:
        blockers.append("仍含草稿/演示标记：" + ", ".join(pending))
    if "穿心莲" not in theme:
        leaked = [token for token in _DISEASE_GOLD_FORBIDDEN if token in blob]
        if leaked:
            blockers.append("仍含穿心莲金样内容：" + ", ".join(leaked))

    required_strings = (
        "meta.theme_id",
        "meta.organization",
        "meta.brand_label",
        "meta.internal_notice",
        "product.name",
        "disease.name",
        "pages.cover.title",
    )
    for dotted in required_strings:
        current: Any = model
        for part in dotted.split("."):
            current = current.get(part) if isinstance(current, dict) else None
        if not isinstance(current, str) or not current.strip():
            blockers.append(f"缺少 {dotted}")

    required_lists = (
        ("agenda", 5),
        ("disease.symptoms", 4),
        ("disease.comparison.rows", 4),
        ("disease.treatment_principles", 6),
        ("disease.subtypes", 4),
        ("product.information", 6),
        ("product.advantages", 4),
        ("product.summary.groups", 3),
        ("product.audience", 3),
        ("product.consultation", 4),
        ("product.scenarios", 2),
        ("product.daily_care", 4),
        ("weighted.items", 1),
        ("weighted.comparison.products", 2),
        ("weighted.comparison.rows", 4),
    )
    for dotted, minimum in required_lists:
        current = model
        for part in dotted.split("."):
            current = current.get(part) if isinstance(current, dict) else None
        if not isinstance(current, list) or len(current) != minimum:
            blockers.append(f"固定 18 页课型要求 {dotted} 恰好 {minimum} 项审核内容")

    image_bindings = _disease_image_bindings(model)
    if not image_bindings:
        blockers.append("没有绑定正式商品图/插图")
    for binding, container, key in image_bindings:
        source = Path(str(container.get(key) or ""))
        if not source.is_file():
            blockers.append(f"图片不存在 {binding}: {source}")
    if theme not in blob:
        blockers.append("任务主题未出现在审核内容中")
    return list(dict.fromkeys(blockers))


def _draft_disease_product_scenario(
    job: dict[str, Any], route: dict[str, Any]
) -> dict[str, Any]:
    theme = job["theme"]
    intake = job.get("intake") or {}
    script_path = Path(intake.get("script_json") or "")
    supplied = script_path.is_file()
    if supplied:
        model = read_json(script_path)
        if not isinstance(model, dict):
            raise SystemExit("疾病+商品标准课型 --script-json 必须是 JSON 对象")
        model = json.loads(json.dumps(model))
        model.setdefault("meta", {})["theme_id"] = (
            "theme.product.andrographolide-drop-pills"
            if "穿心莲" in theme
            else f"business-job.{job['job_id']}"
        )
        model["meta"]["gold_sample"] = "穿心莲" in theme
        model.setdefault("product", {})["name"] = theme
    else:
        notes = str(intake.get("notes") or "").strip()
        model = {
            "schema_version": "disease-product-scenario-script/v1",
            "meta": {
                "theme_id": f"business-job.{job['job_id']}",
                "gold_sample": False,
                "organization": "待确认",
                "brand_label": "待确认",
                "internal_notice": "仅供内部学习",
                "source_notes": [notes] if notes else [],
            },
            "pages": {"cover": {"title": f"{theme} 疾病＋商品＋场景培训（待确认）"}},
            "agenda": [],
            "disease": {"name": "待确认"},
            "product": {"name": theme},
            "weighted": {"items": [], "comparison": {"products": [], "rows": []}},
        }

    product_image = Path(str(intake.get("product_image") or ""))
    if product_image.is_file():
        _bind_disease_primary_image(model, product_image)
    source_dir_value = intake.get("script_source_dir")
    source_dir = Path(str(source_dir_value)) if source_dir_value else None
    _snapshot_disease_images(job, model, source_dir=source_dir)

    draft_dir = job_dir(job["job_id"]) / "draft"
    content_path = draft_dir / "content-model.json"
    review_path = draft_dir / "内容初稿.md"
    gaps_path = draft_dir / "缺口清单.md"
    manifest_path = draft_dir / "asset-manifest.json"
    write_json(content_path, model)
    digest, assets = _disease_content_digest(content_path, model)
    write_json(manifest_path, assets)
    gaps = _disease_formal_blockers(model, theme)
    review_path.write_text(
        "\n".join(
            [
                f"# 内容初稿 · {theme}",
                "",
                f"- 课型：{route.get('name_zh')}",
                f"- 疾病主题：{(model.get('disease') or {}).get('name') or '待确认'}",
                f"- 主商品：{(model.get('product') or {}).get('name') or theme}",
                f"- 场景数：{len((model.get('product') or {}).get('scenarios') or [])}",
                f"- 图片数：{len(assets)}",
                "",
                "确认前不生成正式 PPTX；疾病、商品、场景、话术和图片均须来自业务审核资料。",
                "",
                "## 待补 / 待确认",
                "",
                *[f"- {item}" for item in gaps],
                "",
            ]
        ),
        encoding="utf-8",
    )
    gaps_path.write_text(
        "# 缺口清单\n\n" + ("\n".join(f"- [ ] {item}" for item in gaps) or "- [x] 已齐") + "\n",
        encoding="utf-8",
    )
    return {
        "kind": "disease_product_scenario_pptx",
        "content_model": str(content_path),
        "review_md": str(review_path),
        "gaps_md": str(gaps_path),
        "asset_manifest_json": str(manifest_path),
        "content_model_sha256": sha256_file(content_path),
        "content_sha256": digest,
        "gaps": gaps,
        "page_count": 18,
    }


def _courseware3_module() -> Any:
    import replicate_courseware_theme as module

    return module


def _courseware3_base_model() -> dict[str, Any]:
    path = _COURSEWARE3_GOLD / "content-model.json"
    if not path.is_file():
        raise SystemExit("缺少课件3签样 content-model.json")
    data = read_json(path)
    if not isinstance(data, dict):
        raise SystemExit("课件3签样 content-model.json 格式错误")
    return data


def _courseware3_resolved_assets(
    theme: dict[str, Any], theme_dir: Path
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for key, raw in (theme.get("assets") or {}).items():
        if not isinstance(raw, str) or not raw.strip():
            continue
        source = Path(raw).expanduser()
        if not source.is_absolute():
            source = theme_dir / source
        source = source.resolve()
        if source.is_file():
            result[str(key)] = source
    return result


def _snapshot_courseware3_assets(
    theme: dict[str, Any],
    *,
    source_dir: Path,
    theme_dir: Path,
) -> None:
    assets_dir = theme_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    normalized: dict[str, str] = {}
    for key, raw in sorted((theme.get("assets") or {}).items()):
        if not isinstance(raw, str) or not raw.strip():
            normalized[str(key)] = str(raw or "")
            continue
        source = Path(raw).expanduser()
        if not source.is_absolute():
            local_candidate = theme_dir / source
            source = local_candidate if local_candidate.is_file() else source_dir / source
        source = source.resolve()
        if not source.is_file():
            normalized[str(key)] = raw
            continue
        digest = sha256_file(source)
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", str(key)).strip("-") or "asset"
        dest = assets_dir / f"{safe}-{digest[:12]}{source.suffix.lower() or '.png'}"
        if source.resolve() != dest.resolve():
            shutil.copy2(source, dest)
        normalized[str(key)] = f"assets/{dest.name}"
    theme["assets"] = normalized


def _courseware3_content_digest(
    theme_path: Path, theme: dict[str, Any]
) -> tuple[str, dict[str, dict[str, Any]]]:
    assets: dict[str, dict[str, Any]] = {}
    for key, source in sorted(_courseware3_resolved_assets(theme, theme_path.parent).items()):
        assets[key] = {
            "file": str(source),
            "sha256": sha256_file(source),
            "size": source.stat().st_size,
        }
    payload = {
        "theme_sha256": sha256_file(theme_path),
        "assets": {key: value["sha256"] for key, value in sorted(assets.items())},
    }
    return (
        sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
        assets,
    )


def _courseware3_formal_blockers(
    theme: dict[str, Any], theme_dir: Path, job_theme: str
) -> list[str]:
    blockers: list[str] = []
    try:
        module = _courseware3_module()
        module.validate_theme_contract(
            _courseware3_base_model(),
            theme,
            theme_dir=theme_dir,
            gold=_COURSEWARE3_GOLD,
            require_captions=False,
        )
    except Exception as exc:  # ThemeContractError plus malformed input
        errors = getattr(exc, "errors", None)
        if errors:
            blockers.extend(str(item) for item in errors)
        else:
            blockers.append(str(exc))
    blob = json.dumps(theme, ensure_ascii=False)
    if job_theme not in blob:
        blockers.append("任务商品名未出现在课件3审核内容中")
    return list(dict.fromkeys(blockers))


def _draft_courseware3_pptx(job: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    theme_name = job["theme"]
    intake = job.get("intake") or {}
    script_path = Path(intake.get("script_json") or "")
    base = _courseware3_base_model()
    if script_path.is_file():
        theme = read_json(script_path)
        if not isinstance(theme, dict):
            raise SystemExit("课件3 --script-json 必须是完整 theme.json 对象")
        theme = json.loads(json.dumps(theme))
        theme.setdefault("product", {})["display_name"] = theme_name
    else:
        notes = str(intake.get("notes") or "").strip()
        theme = {
            "theme_id": f"business-job.{job['job_id']}",
            "slug": slugify(theme_name),
            "project_id": f"courseware.business.{job['job_id']}",
            "style_pack_id": base.get("style_pack_id"),
            "voice_pack_id": base.get("voice_pack_id"),
            "product": {
                "brand_name": "待确认",
                "generic_name": "待确认",
                "display_name": theme_name,
            },
            "title": f"{theme_name} · 商品培训课件",
            "assets": {},
            "pages": [],
            "captions": [],
            "business_notes": notes,
        }

    product_image = Path(str(intake.get("product_image") or ""))
    if product_image.is_file():
        theme.setdefault("assets", {})["packGroup"] = str(product_image)
    draft_dir = job_dir(job["job_id"]) / "draft"
    theme_dir = draft_dir / "theme-package"
    theme_dir.mkdir(parents=True, exist_ok=True)
    source_dir_value = intake.get("script_source_dir")
    source_dir = Path(str(source_dir_value)) if source_dir_value else theme_dir
    _snapshot_courseware3_assets(theme, source_dir=source_dir, theme_dir=theme_dir)
    theme_path = theme_dir / "theme.json"
    write_json(theme_path, theme)
    digest, assets = _courseware3_content_digest(theme_path, theme)
    manifest_path = draft_dir / "asset-manifest.json"
    write_json(manifest_path, assets)
    gaps = _courseware3_formal_blockers(theme, theme_dir, theme_name)
    review_path = draft_dir / "内容初稿.md"
    gaps_path = draft_dir / "缺口清单.md"
    review_path.write_text(
        "\n".join(
            [
                f"# 内容初稿 · {theme_name}",
                "",
                f"- 课型：{route.get('name_zh')}",
                f"- 主题内容单元覆盖：{len(theme.get('pages') or [])}/12（导出为 13 页）",
                f"- 已绑定图片：{len(assets)}",
                "",
                "确认前不生成正式 PPTX。12 个主题内容单元、正式包装/Logo 与每个主题插图都必须显式提供；不会继承速福达金样内容或图片。",
                "",
                "## 待补 / 待确认",
                "",
                *[f"- {item}" for item in gaps],
                "",
            ]
        ),
        encoding="utf-8",
    )
    gaps_path.write_text(
        "# 缺口清单\n\n" + ("\n".join(f"- [ ] {item}" for item in gaps) or "- [x] 已齐") + "\n",
        encoding="utf-8",
    )
    return {
        "kind": "courseware3_pptx",
        "theme_package": str(theme_dir),
        "content_model": str(theme_path),
        "review_md": str(review_path),
        "gaps_md": str(gaps_path),
        "asset_manifest_json": str(manifest_path),
        "content_model_sha256": sha256_file(theme_path),
        "content_sha256": digest,
        "gaps": gaps,
        "page_count": 13,
    }


def _ingredient_health_resolved_assets(
    theme: dict[str, Any], theme_dir: Path
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for key, raw in sorted((theme.get("assets") or {}).items()):
        if not isinstance(raw, str) or not raw.strip():
            continue
        source = Path(raw).expanduser()
        if not source.is_absolute():
            source = theme_dir / source
        source = source.resolve()
        if source.is_file():
            result[str(key)] = source
    return result


def _snapshot_ingredient_health_assets(
    theme: dict[str, Any],
    *,
    source_dir: Path,
    theme_dir: Path,
) -> None:
    assets_dir = theme_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    normalized: dict[str, str] = {}
    for key, raw in sorted((theme.get("assets") or {}).items()):
        if not isinstance(raw, str) or not raw.strip():
            normalized[str(key)] = str(raw or "")
            continue
        source = Path(raw).expanduser()
        if not source.is_absolute():
            local_candidate = theme_dir / source
            source = local_candidate if local_candidate.is_file() else source_dir / source
        source = source.resolve()
        if not source.is_file():
            normalized[str(key)] = raw
            continue
        digest = sha256_file(source)
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", str(key)).strip("-") or "asset"
        dest = assets_dir / f"{safe}-{digest[:12]}.png"
        if source.resolve() != dest.resolve():
            shutil.copy2(source, dest)
        normalized[str(key)] = f"assets/{dest.name}"
    theme["assets"] = normalized


def _ingredient_health_content_digest(
    theme_path: Path, theme: dict[str, Any]
) -> tuple[str, dict[str, dict[str, Any]]]:
    assets: dict[str, dict[str, Any]] = {}
    for key, source in sorted(
        _ingredient_health_resolved_assets(theme, theme_path.parent).items()
    ):
        assets[key] = {
            "file": str(source),
            "sha256": sha256_file(source),
            "size": source.stat().st_size,
        }
    payload = {
        "theme_sha256": sha256_file(theme_path),
        "assets": {key: value["sha256"] for key, value in sorted(assets.items())},
    }
    return (
        sha256_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        ),
        assets,
    )


def _ingredient_health_validation(theme_path: Path) -> dict[str, Any]:
    report_path = theme_path.parent / "validation-report.json"
    node = shutil.which("node")
    if not node:
        return {"ok": False, "errors": ["本机缺少 node，无法校验 20 页 OOXML 换槽契约"]}
    if not _INGREDIENT_HEALTH_EXPORT.is_file():
        return {"ok": False, "errors": ["缺少 ingredient-health-edu-pptx-v1 正式引擎"]}
    cmd = [
        node,
        str(_INGREDIENT_HEALTH_EXPORT),
        "--theme",
        str(theme_path),
        "--validate-only",
        "--report",
        str(report_path),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if report_path.is_file():
        report = read_json(report_path)
        if isinstance(report, dict):
            report["validation_exit"] = proc.returncode
            return report
    return {
        "ok": False,
        "errors": [
            f"20 页 OOXML 换槽校验未生成报告 exit={proc.returncode}: "
            + (proc.stderr.strip() or proc.stdout.strip() or "未知错误")[:500]
        ],
    }


def _ingredient_health_formal_blockers(
    theme_path: Path, job_theme: str
) -> list[str]:
    report = _ingredient_health_validation(theme_path)
    blockers = [str(item) for item in (report.get("errors") or [])]
    try:
        theme = read_json(theme_path)
    except (OSError, json.JSONDecodeError) as exc:
        blockers.append(f"theme.json 无法读取：{exc}")
        return list(dict.fromkeys(blockers))
    blob = json.dumps(theme, ensure_ascii=False)
    if job_theme not in blob:
        blockers.append("任务成分主题未出现在 20 页审核内容中")
    return list(dict.fromkeys(blockers))


def _draft_ingredient_health_edu_pptx(
    job: dict[str, Any], route: dict[str, Any]
) -> dict[str, Any]:
    theme_name = job["theme"]
    intake = job.get("intake") or {}
    script_path = Path(intake.get("script_json") or "")
    draft_dir = job_dir(job["job_id"]) / "draft"
    theme_dir = draft_dir / "theme-package"
    theme_dir.mkdir(parents=True, exist_ok=True)
    theme_path = theme_dir / "theme.json"

    if script_path.is_file():
        theme = read_json(script_path)
        if not isinstance(theme, dict):
            raise SystemExit("成分健康科普 --script-json 必须是完整 theme.json 对象")
        theme = json.loads(json.dumps(theme))
        theme.setdefault("theme_name", theme_name)
        source_dir_value = intake.get("script_source_dir")
        source_dir = Path(str(source_dir_value)) if source_dir_value else script_path.parent
        _snapshot_ingredient_health_assets(
            theme, source_dir=source_dir, theme_dir=theme_dir
        )
        write_json(theme_path, theme)
    else:
        node = shutil.which("node")
        if not node or not _INGREDIENT_HEALTH_EXPORT.is_file():
            raise SystemExit("缺少 node 或 ingredient-health-edu-pptx-v1，无法创建换槽草稿")
        emit_report = draft_dir / "slot-contract-report.json"
        cmd = [
            node,
            str(_INGREDIENT_HEALTH_EXPORT),
            "--emit-draft",
            str(theme_path),
            "--theme-name",
            theme_name,
            "--theme-id",
            f"business-job.{job['job_id']}",
            "--report",
            str(emit_report),
        ]
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if proc.returncode != 0 or not theme_path.is_file():
            raise SystemExit(
                f"20 页换槽草稿创建失败 exit={proc.returncode}: "
                + (proc.stderr.strip() or proc.stdout.strip() or "未知错误")[:500]
            )
        theme = read_json(theme_path)

    digest, assets = _ingredient_health_content_digest(theme_path, theme)
    manifest_path = draft_dir / "asset-manifest.json"
    write_json(manifest_path, assets)
    gaps = _ingredient_health_formal_blockers(theme_path, theme_name)
    validation_path = theme_dir / "validation-report.json"
    validation = read_json(validation_path) if validation_path.is_file() else {}
    contract = validation.get("contract") or {}
    review_path = draft_dir / "内容初稿.md"
    gaps_path = draft_dir / "缺口清单.md"
    review_path.write_text(
        "\n".join(
            [
                f"# 内容初稿 · {theme_name}",
                "",
                f"- 课型：{route.get('name_zh')}",
                f"- 固定页数：{contract.get('pages') or 20}",
                f"- OOXML 文字槽：{contract.get('text_slots') or 107}",
                f"- 页面图片槽：{contract.get('slide_image_slots') or 67}",
                f"- 母版/版式图片槽：{contract.get('template_image_slots') or 2}",
                f"- 已登记图片资产：{len(assets)}",
                "",
                "确认前不生成正式 PPTX。新主题必须完整填写 107 个文字槽和 69 个图片槽；不会继承金样医学正文、剂量、功效或番茄参考图片。",
                "",
                "## 待补 / 待确认",
                "",
                *[f"- {item}" for item in gaps],
                "",
            ]
        ),
        encoding="utf-8",
    )
    gaps_path.write_text(
        "# 缺口清单\n\n"
        + ("\n".join(f"- [ ] {item}" for item in gaps) or "- [x] 已齐")
        + "\n",
        encoding="utf-8",
    )
    return {
        "kind": "ingredient_health_edu_pptx",
        "theme_package": str(theme_dir),
        "content_model": str(theme_path),
        "review_md": str(review_path),
        "gaps_md": str(gaps_path),
        "asset_manifest_json": str(manifest_path),
        "validation_report_json": str(validation_path),
        "content_model_sha256": sha256_file(theme_path),
        "content_sha256": digest,
        "gaps": gaps,
        "page_count": 20,
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

_COMPONENT_PENDING_TOKENS = (
    "待确认",
    "待业务",
    "待补充",
    "待审核",
    "TODO",
    "TBD",
    "__missing__",
    "<generated-file>",
)


def _component_content_payload(script: dict[str, Any]) -> dict[str, Any]:
    """Return the reviewable copy contract, excluding replaceable visual bindings."""
    payload = copy.deepcopy(script)
    meta = payload.get("meta") or {}
    for key in ("product_packshot", "brand_logo"):
        meta.pop(key, None)

    for row in ((payload.get("benefits") or {}).get("items") or []):
        if isinstance(row, dict):
            row.pop("visual", None)
            row.pop("chain", None)
    for row in ((payload.get("features") or {}).get("items") or []):
        if isinstance(row, dict):
            row.pop("visual", None)
    audience = payload.get("audience") or {}
    if isinstance(audience, dict):
        audience.pop("visual", None)
    for row in ((payload.get("combination") or {}).get("rows") or []):
        if isinstance(row, dict):
            row.pop("icon", None)
    precautions = payload.get("precautions") or {}
    if isinstance(precautions, dict):
        precautions.pop("illustrations", None)
    return payload


def _component_content_sha256(script: dict[str, Any]) -> str:
    payload = json.dumps(
        _component_content_payload(script),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(payload)


_COMPONENT_PRODUCTION_PAGE_STATUSES = {"settled", "production-validated"}


def _component_page_sequence_blockers(script: dict[str, Any]) -> list[str]:
    """Validate the confirmed page order against the registry and active scope."""
    sequence = (script.get("meta") or {}).get("page_sequence")
    if not isinstance(sequence, list) or not sequence:
        return ["缺少已确认页签顺序 meta.page_sequence"]

    registry = read_json(_COMPONENT_REGISTRY)
    registered = {
        str(item.get("id")): item
        for item in registry.get("page_types") or []
        if isinstance(item, dict) and item.get("id")
    }
    allowed_statuses = set(_COMPONENT_PRODUCTION_PAGE_STATUSES)
    if _ACTIVE_SCOPE == "uat":
        allowed_statuses.add("candidate")

    blockers: list[str] = []
    for position, page_type in enumerate(sequence, 1):
        if not isinstance(page_type, str) or page_type not in registered:
            blockers.append(
                f"meta.page_sequence[{position}] 未注册页型：{page_type!r}"
            )
            continue
        status = str(registered[page_type].get("status") or "")
        if status not in allowed_statuses:
            blockers.append(
                f"当前 {_ACTIVE_SCOPE} scope 禁止页型 {page_type}（status={status or 'missing'}）"
            )
    return blockers


def _component_content_blockers(script: dict[str, Any]) -> list[str]:
    """Block formal approval of placeholders while keeping incomplete drafts useful."""
    blob = json.dumps(_component_content_payload(script), ensure_ascii=False)
    blockers = _component_page_sequence_blockers(script)
    blockers.extend(token for token in _COMPONENT_PENDING_TOKENS if token in blob)
    if not str(((script.get("meta") or {}).get("display_name") or "")).strip():
        blockers.append("缺少商品名")
    return blockers


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


_COMPONENT_PAGE_LABELS_ZH = {
    "courseware_cover": "封面",
    "hook_intro": "导语/需求钩子",
    "hook_pain_data": "痛点数据",
    "benefit_cards": "核心功效卡",
    "feature_cards": "产品特点卡",
    "audience_list": "适宜人群",
    "combination_guidance": "联合建议",
    "summary_matrix": "总结矩阵",
    "precautions": "注意事项",
    "product_overview": "商品信息总览",
    "consultation_framework": "门店咨询框架",
    "evidence_ladder": "商品证据阶梯",
    "objection_handling": "门店异议应答",
}

_COMPONENT_NOTE_PAGE_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "product_overview",
        ("商品信息总览", "商品总览", "商品信息", "基础信息", "规格", "物料编号"),
    ),
    (
        "consultation_framework",
        ("门店咨询框架", "咨询框架", "问询框架", "咨询步骤", "问询步骤", "四步法"),
    ),
    (
        "evidence_ladder",
        ("商品证据阶梯", "证据阶梯", "证据来源", "资料来源", "检测依据", "研究依据"),
    ),
    (
        "objection_handling",
        ("异议应答", "异议处理", "答疑边界", "升级边界", "资料外问题"),
    ),
    ("benefit_cards", ("核心功效", "功效要点", "利益点")),
    ("feature_cards", ("产品特点", "核心卖点", "卖点", "产地", "原料", "含量")),
    ("audience_list", ("适宜人群", "适用人群", "人群边界")),
    ("combination_guidance", ("联合建议", "联合用药", "联推", "搭配话术")),
    ("summary_matrix", ("总结矩阵", "总结回顾", "培训总结")),
    ("precautions", ("注意事项", "禁忌", "风险提醒")),
)


def _component_note_fragments(notes: str) -> list[str]:
    fragments: list[str] = []
    for point in _parse_note_points(notes):
        parts = [part.strip() for part in re.split(r"[，,\uff1b;、]+", point) if part.strip()]
        fragments.extend(parts or [point])
    return fragments


def _component_note_page_type(fragment: str) -> str:
    for page_type, hints in _COMPONENT_NOTE_PAGE_HINTS:
        if any(hint in fragment for hint in hints):
            return page_type
    return "hook_intro"


def _component_note_value(fragment: str) -> tuple[str, str]:
    if "：" in fragment:
        label, value = fragment.split("：", 1)
    elif ":" in fragment:
        label, value = fragment.split(":", 1)
    else:
        label, value = "业务资料", fragment
    return label.strip() or "业务资料", value.strip() or fragment.strip()


def _build_component_script(theme: str, notes: str) -> dict[str, Any]:
    """Build a minimal, content-driven outline for business review.

    Notes select only page types evidenced by their own keywords. Missing sections are
    omitted; no fixed benefit/feature/audience/combination shell is pre-filled.
    """
    fragments = _component_note_fragments(notes)
    grouped: dict[str, list[str]] = {}
    ordered_types: list[str] = []
    for fragment in fragments:
        page_type = _component_note_page_type(fragment)
        if page_type not in grouped:
            grouped[page_type] = []
            ordered_types.append(page_type)
        grouped[page_type].append(fragment)

    page_sequence = ["courseware_cover", *ordered_types]
    script: dict[str, Any] = {
        "schema": "product-training-script/v1",
        "meta": {
            "display_name": theme,
            "organization": "大参林医药集团",
            "tagline": "【专业力】",
            "content_lock": "business-draft-pending-approval",
            "brand_boast_disabled": True,
            "family": "product-training",
            "style_pack_id": "style-pack.reference-product-blue-v1",
            "page_sequence": page_sequence,
        },
        "gaps": [
            "中文页签大纲待确认",
            "商品正式包装图由业务提供并单独完成授权确认",
        ],
    }
    if not fragments:
        script["gaps"].insert(1, "请补充交付目标或内容要点")

    if grouped.get("hook_intro"):
        script["hook"] = {
            "title": f"{theme} 培训导语",
            "paragraphs": [f"{'；'.join(grouped['hook_intro'])}（待业务确认）"],
        }
    if grouped.get("product_overview"):
        script["product_overview"] = {
            "title": "商品信息总览",
            "facts": [
                {"label": label, "value": f"{value}（待业务确认）"}
                for label, value in map(_component_note_value, grouped["product_overview"])
            ],
            "statement": "",
        }
    if grouped.get("consultation_framework"):
        script["consultation"] = {
            "title": "门店咨询框架",
            "steps": [
                {
                    "question": _component_note_value(item)[1],
                    "why": "核对目的待业务确认",
                }
                for item in grouped["consultation_framework"]
            ],
        }
    if grouped.get("evidence_ladder"):
        script["evidence"] = {
            "title": "商品证据阶梯",
            "items": [
                {
                    "metric": f"{index:02d}",
                    "label": _component_note_value(item)[1],
                    "source": "来源待业务确认",
                }
                for index, item in enumerate(grouped["evidence_ladder"], 1)
            ],
        }
    if grouped.get("objection_handling"):
        script["objection_handling"] = {
            "title": "门店异议应答",
            "rows": [
                {
                    "objection": _component_note_value(item)[1],
                    "response": "应答口径待业务确认",
                    "boundary": "升级边界待业务确认",
                }
                for item in grouped["objection_handling"]
            ],
        }
    if grouped.get("benefit_cards"):
        labels = [_component_note_value(item)[1] for item in grouped["benefit_cards"]]
        script["benefits"] = {
            "title": "核心功效",
            "items": [
                {"title": labels[0][:40], "body": f"{'；'.join(labels)}（待业务确认）"}
            ],
        }
    if grouped.get("feature_cards"):
        labels = [_component_note_value(item)[1] for item in grouped["feature_cards"]]
        script["features"] = {
            "title": "产品特点",
            "items": [
                {"title": labels[0][:40], "body": f"{'；'.join(labels)}（待业务确认）"}
            ],
        }
    if grouped.get("audience_list"):
        script["audience"] = {
            "title": "适宜人群",
            "items": [
                f"{_component_note_value(item)[1]}（待业务确认）"
                for item in grouped["audience_list"]
            ],
        }
    if grouped.get("combination_guidance"):
        script["combination"] = {
            "title": "联合建议",
            "rows": [
                {
                    "problem": _component_note_value(item)[1],
                    "partner": "搭档商品待业务确认",
                    "talk_track": "店员话术待业务确认",
                }
                for item in grouped["combination_guidance"]
            ],
        }
    if grouped.get("summary_matrix"):
        script["summary"] = {
            "title": "总结矩阵",
            "rows": [
                {"label": label, "value": f"{value}（待业务确认）"}
                for label, value in map(_component_note_value, grouped["summary_matrix"])
            ],
        }
    if grouped.get("precautions"):
        script["precautions"] = {
            "title": "注意事项",
            "items": [
                f"{_component_note_value(item)[1]}（待业务确认）"
                for item in grouped["precautions"]
            ],
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

    if intake.get("product_image"):
        script.setdefault("meta", {})["product_packshot"] = intake["product_image"]

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

    digest = _component_content_sha256(script)

    if "gaps" in script:
        gaps = list(script.get("gaps") or [])
    elif isinstance((script.get("meta") or {}).get("page_sequence"), list):
        content_blob = json.dumps(_component_content_payload(script), ensure_ascii=False)
        gaps = [
            f"所选页签内容仍含「{token}」"
            for token in _COMPONENT_PENDING_TOKENS
            if token in content_blob
        ]
        if not str((script.get("meta") or {}).get("product_packshot") or "").strip():
            gaps.append("商品正式包装图由业务提供并单独完成授权确认")
    else:
        gaps = [
            "审核后的导语/痛点与数据出处",
            "审核后的核心功效与产品特点表述",
            "适宜人群边界",
            "联合用药场景与搭档商品（有几条写几条）",
            "注意事项审核稿",
            "商品正式包装图由业务提供；知识/场景插图由系统按图槽自动生成",
        ]
    if notes and not script.get("gaps"):
        gaps.insert(0, "业务已提供文字要点，请逐条核对是否可进正式培训")
    if not intake.get("script_json") and not script.get("gaps"):
        gaps.insert(0, "建议改为完整 script.structured.json 以锁定审核文案")

    review_path = draft_dir / "内容初稿.md"
    plan = read_json(scene_plan) if scene_plan.is_file() else {}
    lines = [
        f"# 内容初稿 · {theme}",
        "",
        f"- 任务：`{job['job_id']}`",
        f"- 已锁定模板：{route.get('name_zh')}",
        f"- 交付物：{route.get('deliverable_zh') or '可编辑 PPT'}",
        f"- 脚本哈希：`{digest}`",
        f"- 规划页数：{plan.get('page_count') or report.get('page_count') or '—'}",
        "",
        "## 说明",
        "",
        "本文件供业务确认。确认前不生成正式 PPTX。",
        "文案唯一来源 = script.structured.json；系统不扩写功效/剂量。",
        "标「待确认」字段不得当作已审核医学结论。",
        "",
        "## 中文页签大纲（待确认）",
        "",
    ]
    for p in plan.get("pages") or []:
        page_type = str(p.get("page_type") or "")
        label = _COMPONENT_PAGE_LABELS_ZH.get(page_type, page_type)
        lines.append(
            f"- P{p.get('i')}：{label}"
        )
    lines.append("- 页签确认前只保留草稿，不进入正式渲染。")
    lines.extend(["", "## 脚本摘要", ""])
    meta = script.get("meta") or {}
    lines.append(f"- 商品：{meta.get('display_name')}")
    lines.append(f"- 组织：{meta.get('organization')}")
    if isinstance(meta.get("page_sequence"), list):
        labels = [
            _COMPONENT_PAGE_LABELS_ZH.get(str(page_type), str(page_type))
            for page_type in meta["page_sequence"]
        ]
        lines.append(f"- 页签顺序：{' → '.join(labels)}")
    for section_key in (
        "product_overview",
        "hook",
        "benefits",
        "features",
        "audience",
        "consultation",
        "evidence",
        "objection_handling",
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
                    if it.get("metric") is not None:
                        lines.append(
                            f"- {it.get('metric')}｜{it.get('label') or ''}｜来源：{it.get('source') or ''}"
                        )
                    else:
                        lines.append(f"- {it.get('title') or ''}：{it.get('body') or it.get('text') or ''}")
                else:
                    lines.append(f"- {it}")
            for fact in block.get("facts") or []:
                if isinstance(fact, dict):
                    lines.append(f"- {fact.get('label') or ''}：{fact.get('value') or ''}")
            for step in block.get("steps") or []:
                if isinstance(step, dict):
                    lines.append(
                        f"- 问：{step.get('question') or ''}｜核对目的：{step.get('why') or ''}"
                    )
            for row in block.get("rows") or []:
                if isinstance(row, dict):
                    if row.get("problem") is not None:
                        lines.append(
                            f"- 场景：{row.get('problem')}｜搭档：{row.get('partner')}｜话术：{row.get('talk_track')}"
                        )
                    elif row.get("objection") is not None:
                        lines.append(
                            f"- 异议：{row.get('objection')}｜应答：{row.get('response')}｜边界：{row.get('boundary')}"
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
    asset_plan = build_product_pptx_asset_plan(
        script, template_slug=str(route.get("template_slug") or "")
    )
    asset_plan_json = draft_dir / "素材计划.json"
    write_json(asset_plan_json, asset_plan)
    asset_plan_md = draft_dir / "素材计划.md"
    asset_plan_md.write_text(
        render_asset_plan_markdown(asset_plan, theme=theme), encoding="utf-8"
    )

    return {
        "kind": "product_pptx_component",
        "script": str(script_path),
        "content_model": str(content_model),
        "scene_plan": str(scene_plan) if scene_plan.is_file() else None,
        "review_md": str(review_path),
        "gaps_md": str(gaps_path),
        "asset_plan_json": str(asset_plan_json),
        "asset_plan_md": str(asset_plan_md),
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
    "disease_product_scenario_pptx": _draft_disease_product_scenario,
    "courseware3_pptx": _draft_courseware3_pptx,
    "ingredient_health_edu_pptx": _draft_ingredient_health_edu_pptx,
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
        "scope": str(job.get("scope") or "production"),
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


_SCRIPT_PATH_PART = re.compile(r"([^.[\]]+)|\[(\d+)\]")


def _set_script_value(root: dict[str, Any], path: str, value: Any) -> None:
    parts: list[str | int] = []
    for match in _SCRIPT_PATH_PART.finditer(path):
        key, index = match.groups()
        parts.append(int(index) if index is not None else key)
    if not parts:
        raise SystemExit(f"无效素材绑定路径: {path}")
    current: Any = root
    for part in parts[:-1]:
        try:
            current = current[part]
        except (KeyError, IndexError, TypeError) as exc:
            raise SystemExit(f"素材绑定路径不存在: {path}") from exc
    try:
        current[parts[-1]] = value
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"素材绑定路径不可写: {path}") from exc


def _replace_generated_file(value: Any, file_path: str) -> Any:
    if isinstance(value, str):
        return file_path if value == "<generated-file>" else value
    if isinstance(value, list):
        return [_replace_generated_file(item, file_path) for item in value]
    if isinstance(value, dict):
        return {key: _replace_generated_file(item, file_path) for key, item in value.items()}
    return value


def _component_script(job: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    draft = job.get("draft") or {}
    script_path = Path(draft.get("script") or "")
    if not script_path.is_file():
        raise SystemExit("缺少构件 PPT 脚本，请先 draft")
    script = read_json(script_path)
    if not isinstance(script, dict):
        raise SystemExit("构件 PPT 脚本格式错误")
    return script_path, script


def _refresh_component_asset_plan(
    job: dict[str, Any], route: dict[str, Any], script: dict[str, Any]
) -> dict[str, Any]:
    plan = build_product_pptx_asset_plan(
        script, template_slug=str(route.get("template_slug") or "")
    )
    draft = job.get("draft") or {}
    plan_json = Path(draft.get("asset_plan_json") or "")
    plan_md = Path(draft.get("asset_plan_md") or "")
    if plan_json:
        write_json(plan_json, plan)
    if plan_md:
        plan_md.write_text(
            render_asset_plan_markdown(plan, theme=job["theme"]), encoding="utf-8"
        )
    return plan


def _component_visual_manifest(plan: dict[str, Any]) -> dict[str, dict[str, str]]:
    manifest: dict[str, dict[str, str]] = {}
    for item in plan.get("system_generates") or []:
        target = str(item.get("script_path") or "")
        source = str(item.get("existing_src") or "")
        path = Path(source).expanduser().resolve() if source else None
        if not target or path is None or not path.is_file():
            raise SystemExit(f"主题插图未绑定真实文件：{item.get('semantic') or target}")
        manifest[target] = {"path": str(path), "sha256": sha256_file(path)}
    return manifest


def _component_visual_manifest_sha256(
    manifest: dict[str, dict[str, str]],
) -> str:
    hashes = {
        target: str(record.get("sha256") or "")
        for target, record in sorted(manifest.items())
    }
    return sha256_text(
        json.dumps(hashes, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def _prepare_component_content_for_approval(
    job: dict[str, Any], route: dict[str, Any]
) -> str:
    """Freeze approved copy independently from later replaceable visual files."""
    script_path, script = _component_script(job)
    _assert_no_component_gold_residue(script, job["theme"])
    blockers = _component_content_blockers(script)
    if blockers:
        raise SystemExit(
            "内容仍含待补字段，不能正式确认：" + "、".join(blockers[:8])
        )
    script.setdefault("meta", {})["content_lock"] = "business-approved"
    write_json(script_path, script)
    digest = _component_content_sha256(script)
    job.setdefault("draft", {})["content_sha256"] = digest
    _refresh_component_asset_plan(job, route, script)
    return digest


def _prepare_component_visuals_for_approval(
    job: dict[str, Any],
    route: dict[str, Any],
    *,
    bindings_json: Path | None,
) -> dict[str, dict[str, str]]:
    """Bind generated/approved illustrations after copy approval and hash every file."""
    script_path, script = _component_script(job)

    mapping: dict[str, str] = {}
    if bindings_json:
        bindings_path = bindings_json.expanduser().resolve()
        if not bindings_path.is_file():
            raise SystemExit(f"素材绑定文件不存在: {bindings_path}")
        raw = read_json(bindings_path)
        if isinstance(raw, dict) and isinstance(raw.get("bindings"), dict):
            raw = raw["bindings"]
        if not isinstance(raw, dict):
            raise SystemExit("素材绑定文件必须是 {script_path: 本地图片路径} 对象")
        mapping = {str(key): str(value) for key, value in raw.items()}

    initial_plan = build_product_pptx_asset_plan(
        script, template_slug=str(route.get("template_slug") or "")
    )
    plan_by_path = {
        str(item.get("script_path")): item
        for item in initial_plan.get("system_generates") or []
    }
    resolved_sources: dict[str, Path] = {}
    for target, source in mapping.items():
        item = plan_by_path.get(target)
        if not item:
            raise SystemExit(f"素材绑定目标不在当前计划中: {target}")
        if item.get("status") == "blocked_pending_content":
            raise SystemExit(f"内容仍待确认，禁止生图绑定: {item.get('semantic')}")
        binding = item.get("binding") or {}
        shape = binding.get("value_shape")
        if shape is None:
            raise SystemExit(f"素材计划缺少可执行 binding: {target}")
        src = Path(source).expanduser().resolve()
        if not src.is_file():
            raise SystemExit(f"生成素材不存在: {src}")
        resolved_sources[target] = src
        _set_script_value(script, target, _replace_generated_file(shape, str(src)))

    intake_dir = job_dir(job["job_id"]) / "intake"
    generated_dir = intake_dir / "generated-assets"
    generated_dir.mkdir(parents=True, exist_ok=True)

    for target, source in resolved_sources.items():
        suffix = source.suffix.lower() or ".png"
        name = hashlib.sha256(target.encode("utf-8")).hexdigest()[:12] + suffix
        dest = generated_dir / name
        if source != dest:
            shutil.copy2(source, dest)
        item = plan_by_path[target]
        shape = (item.get("binding") or {}).get("value_shape")
        _set_script_value(script, target, _replace_generated_file(shape, str(dest)))

    write_json(script_path, script)
    final_plan = _refresh_component_asset_plan(job, route, script)
    visual_blockers = []
    for item in final_plan.get("system_generates") or []:
        if item.get("status") != "ready":
            visual_blockers.append(
                f"{item.get('semantic') or item.get('script_path')}（{item.get('status')}）"
            )
    if visual_blockers:
        raise SystemExit(
            "主题插图未齐，不能视觉确认：" + "；".join(visual_blockers[:8])
        )
    write_json(intake_dir / "intake.json", job.get("intake") or {})
    return _component_visual_manifest(final_plan)


def _prepare_component_product_image_for_approval(
    job: dict[str, Any], route: dict[str, Any], *, product_image: Path | None
) -> Path:
    """Copy and bind the business-authorized product image without changing copy hash."""
    script_path, script = _component_script(job)
    image = product_image
    if image is None:
        stored = str((job.get("intake") or {}).get("product_image") or "")
        image = Path(stored) if stored else None
    if image is None:
        raise SystemExit("product_image 审批需要有效包装图")
    source = image.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"包装图不存在: {source}")
    intake_dir = job_dir(job["job_id"]) / "intake"
    dest = intake_dir / f"product-packshot{source.suffix.lower() or '.png'}"
    if source != dest:
        shutil.copy2(source, dest)
    job.setdefault("intake", {})["product_image"] = str(dest)
    script.setdefault("meta", {})["product_packshot"] = str(dest)
    write_json(script_path, script)
    _refresh_component_asset_plan(job, route, script)
    write_json(intake_dir / "intake.json", job.get("intake") or {})
    return dest


def _verify_component_asset_approvals(
    job: dict[str, Any], script: dict[str, Any], plan: dict[str, Any]
) -> None:
    approvals = job.get("approvals") or {}
    visual = approvals.get("visual") or {}
    manifest = _component_visual_manifest(plan)
    current_visual_hash = _component_visual_manifest_sha256(manifest)
    if visual.get("visual_assets_sha256") != current_visual_hash:
        raise RuntimeError("主题插图与视觉确认记录不一致，请重新完成 visual 确认")

    product = approvals.get("product_image") or {}
    packshot = str(((script.get("meta") or {}).get("product_packshot") or ""))
    packshot_path = Path(packshot).expanduser().resolve() if packshot else None
    if packshot_path is None or not packshot_path.is_file():
        raise RuntimeError("缺少已绑定的业务授权包装图")
    if product.get("product_image_sha256") != sha256_file(packshot_path):
        raise RuntimeError("包装图与 product_image 确认记录不一致，请重新确认")


def _prepare_green_for_approval(
    job: dict[str, Any],
    *,
    product_image: Path | None,
) -> None:
    """Freeze the full five-page content and every visible image before approval."""
    draft = job.get("draft") or {}
    content_path = Path(draft.get("content_model") or "")
    if not content_path.is_file():
        raise SystemExit("缺少绿色标准课型 content-model，请先 draft")
    model = read_json(content_path)
    if not isinstance(model, dict):
        raise SystemExit("绿色标准课型 content-model 格式错误")

    intake_dir = job_dir(job["job_id"]) / "intake"
    intake = job.setdefault("intake", {})
    source_product: Path | None = None
    if product_image:
        source_product = product_image.expanduser().resolve()
        if not source_product.is_file():
            raise SystemExit(f"包装图不存在: {source_product}")
    elif intake.get("product_image"):
        candidate = Path(str(intake["product_image"]))
        if candidate.is_file():
            source_product = candidate
    if source_product:
        suffix = source_product.suffix.lower() or ".png"
        product_dest = intake_dir / f"product-packshot{suffix}"
        if source_product.resolve() != product_dest.resolve():
            shutil.copy2(source_product, product_dest)
        intake["product_image"] = str(product_dest)
        _bind_green_primary_image(model, product_dest)

    source_dir_value = intake.get("script_source_dir")
    source_dir = Path(str(source_dir_value)) if source_dir_value else None
    _snapshot_green_assets(job, model, source_dir=source_dir)
    model["content_lock"] = "business-content-final-candidate"
    _assert_no_green_gold_residue(model, job["theme"])
    blockers = _green_formal_blockers(model)
    if blockers:
        raise SystemExit("绿色标准课型终稿资料未齐，不能批准：" + "；".join(blockers[:10]))

    write_json(content_path, model)
    digest, manifest = _green_content_digest(content_path, model)
    asset_manifest_path = Path(
        draft.get("asset_manifest_json")
        or (job_dir(job["job_id"]) / "draft" / "asset-manifest.json")
    )
    write_json(asset_manifest_path, manifest)
    draft["asset_manifest_json"] = str(asset_manifest_path)
    draft["content_model_sha256"] = sha256_file(content_path)
    draft["content_sha256"] = digest
    draft["gaps"] = []
    gaps_value = draft.get("gaps_md")
    if gaps_value:
        gaps_path = Path(str(gaps_value))
        gaps_path.write_text(
            "# 缺口清单\n\n- [x] 内容、正式图片与审核字段已齐，等待内容审批。\n",
            encoding="utf-8",
        )
    write_json(intake_dir / "intake.json", intake)


def _prepare_disease_for_approval(
    job: dict[str, Any],
    *,
    product_image: Path | None,
) -> None:
    draft = job.get("draft") or {}
    content_path = Path(draft.get("content_model") or "")
    if not content_path.is_file():
        raise SystemExit("缺少疾病+商品标准课型 content-model，请先 draft")
    model = read_json(content_path)
    if not isinstance(model, dict):
        raise SystemExit("疾病+商品标准课型 content-model 格式错误")

    intake_dir = job_dir(job["job_id"]) / "intake"
    intake = job.setdefault("intake", {})
    source_product: Path | None = None
    if product_image:
        source_product = product_image.expanduser().resolve()
        if not source_product.is_file():
            raise SystemExit(f"包装图不存在: {source_product}")
    elif intake.get("product_image"):
        candidate = Path(str(intake["product_image"]))
        if candidate.is_file():
            source_product = candidate
    if source_product:
        suffix = source_product.suffix.lower() or ".png"
        dest = intake_dir / f"product-packshot{suffix}"
        if source_product.resolve() != dest.resolve():
            shutil.copy2(source_product, dest)
        intake["product_image"] = str(dest)
        _bind_disease_primary_image(model, dest)

    source_dir_value = intake.get("script_source_dir")
    source_dir = Path(str(source_dir_value)) if source_dir_value else content_path.parent
    _snapshot_disease_images(job, model, source_dir=source_dir)
    blockers = _disease_formal_blockers(model, job["theme"])
    if blockers:
        raise SystemExit("疾病+商品标准课型终稿资料未齐，不能批准：" + "；".join(blockers[:10]))

    write_json(content_path, model)
    digest, assets = _disease_content_digest(content_path, model)
    manifest_path = Path(
        draft.get("asset_manifest_json")
        or (job_dir(job["job_id"]) / "draft" / "asset-manifest.json")
    )
    write_json(manifest_path, assets)
    draft["asset_manifest_json"] = str(manifest_path)
    draft["content_model_sha256"] = sha256_file(content_path)
    draft["content_sha256"] = digest
    draft["gaps"] = []
    gaps_value = draft.get("gaps_md")
    if gaps_value:
        Path(str(gaps_value)).write_text(
            "# 缺口清单\n\n- [x] 内容、正式图片与审核字段已齐，等待内容审批。\n",
            encoding="utf-8",
        )
    write_json(intake_dir / "intake.json", intake)


def _prepare_courseware3_for_approval(
    job: dict[str, Any],
    *,
    product_image: Path | None,
) -> None:
    draft = job.get("draft") or {}
    theme_path = Path(draft.get("content_model") or "")
    theme_dir = Path(draft.get("theme_package") or theme_path.parent)
    if not theme_path.is_file():
        raise SystemExit("缺少课件3 theme.json，请先 draft")
    theme = read_json(theme_path)
    if not isinstance(theme, dict):
        raise SystemExit("课件3 theme.json 格式错误")

    intake_dir = job_dir(job["job_id"]) / "intake"
    intake = job.setdefault("intake", {})
    source_product: Path | None = None
    if product_image:
        source_product = product_image.expanduser().resolve()
        if not source_product.is_file():
            raise SystemExit(f"包装图不存在: {source_product}")
    elif intake.get("product_image"):
        candidate = Path(str(intake["product_image"]))
        if candidate.is_file():
            source_product = candidate
    if source_product:
        suffix = source_product.suffix.lower() or ".png"
        dest = intake_dir / f"product-packshot{suffix}"
        if source_product.resolve() != dest.resolve():
            shutil.copy2(source_product, dest)
        intake["product_image"] = str(dest)
        theme.setdefault("assets", {})["packGroup"] = str(dest)

    source_dir_value = intake.get("script_source_dir")
    source_dir = Path(str(source_dir_value)) if source_dir_value else theme_dir
    _snapshot_courseware3_assets(theme, source_dir=source_dir, theme_dir=theme_dir)
    write_json(theme_path, theme)
    blockers = _courseware3_formal_blockers(theme, theme_dir, job["theme"])
    if blockers:
        raise SystemExit("课件3终稿资料未齐，不能批准：" + "；".join(blockers[:12]))

    digest, assets = _courseware3_content_digest(theme_path, theme)
    manifest_path = Path(
        draft.get("asset_manifest_json")
        or (job_dir(job["job_id"]) / "draft" / "asset-manifest.json")
    )
    write_json(manifest_path, assets)
    draft["asset_manifest_json"] = str(manifest_path)
    draft["content_model_sha256"] = sha256_file(theme_path)
    draft["content_sha256"] = digest
    draft["gaps"] = []
    gaps_value = draft.get("gaps_md")
    if gaps_value:
        Path(str(gaps_value)).write_text(
            "# 缺口清单\n\n- [x] 12 个主题内容单元、授权包装/Logo 与主题插图已齐，等待内容审批。\n",
            encoding="utf-8",
        )
    write_json(intake_dir / "intake.json", intake)


def _prepare_ingredient_health_for_approval(job: dict[str, Any]) -> None:
    draft = job.get("draft") or {}
    theme_path = Path(draft.get("content_model") or "")
    theme_dir = Path(draft.get("theme_package") or theme_path.parent)
    if not theme_path.is_file():
        raise SystemExit("缺少成分健康科普 theme.json，请先 draft")
    theme = read_json(theme_path)
    if not isinstance(theme, dict):
        raise SystemExit("成分健康科普 theme.json 格式错误")

    intake = job.setdefault("intake", {})
    source_dir_value = intake.get("script_source_dir")
    source_dir = Path(str(source_dir_value)) if source_dir_value else theme_dir
    _snapshot_ingredient_health_assets(
        theme, source_dir=source_dir, theme_dir=theme_dir
    )
    write_json(theme_path, theme)
    blockers = _ingredient_health_formal_blockers(theme_path, job["theme"])
    if blockers:
        raise SystemExit(
            "20 页成分健康科普终稿资料未齐，不能批准："
            + "；".join(blockers[:12])
        )

    digest, assets = _ingredient_health_content_digest(theme_path, theme)
    manifest_path = Path(
        draft.get("asset_manifest_json")
        or (job_dir(job["job_id"]) / "draft" / "asset-manifest.json")
    )
    write_json(manifest_path, assets)
    draft["asset_manifest_json"] = str(manifest_path)
    draft["content_model_sha256"] = sha256_file(theme_path)
    draft["content_sha256"] = digest
    draft["gaps"] = []
    gaps_value = draft.get("gaps_md")
    if gaps_value:
        Path(str(gaps_value)).write_text(
            "# 缺口清单\n\n- [x] 20 页、107 个文字槽与 69 个授权图片槽已齐，等待内容审批。\n",
            encoding="utf-8",
        )
    write_json(job_dir(job["job_id"]) / "intake" / "intake.json", intake)


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
        if route.get("adapter") == "product_pptx_component":
            if args.product_image or getattr(args, "asset_bindings", None):
                raise SystemExit(
                    "构件路线的内容确认只锁定文案；请先 approve --gate content，"
                    "再分别 approve --gate visual --asset-bindings ... 和 "
                    "approve --gate product_image --product-image ..."
                )
            _prepare_component_content_for_approval(job, route)
        elif route.get("adapter") == "product_pptx_green":
            _prepare_green_for_approval(job, product_image=args.product_image)
        elif route.get("adapter") == "disease_product_scenario_pptx":
            _prepare_disease_for_approval(job, product_image=args.product_image)
        elif route.get("adapter") == "courseware3_pptx":
            _prepare_courseware3_for_approval(job, product_image=args.product_image)
        elif route.get("adapter") == "ingredient_health_edu_pptx":
            _prepare_ingredient_health_for_approval(job)
        digest = _require_draft_hash(job)
        if args.content_sha256 and args.content_sha256 != digest:
            raise SystemExit("提供的 content_sha256 与当前草稿不一致")
        prior_digest = str(
            ((job.get("approvals") or {}).get("content") or {}).get("content_sha256")
            or ""
        )
        if prior_digest and prior_digest != digest:
            invalidated: list[str] = []
            for dependent in ("visual", "product_image"):
                if job.setdefault("approvals", {}).pop(dependent, None):
                    invalidated.append(dependent)
            if invalidated:
                append_history(
                    job,
                    "approvals_invalidated",
                    {"reason": "content hash changed", "gates": invalidated},
                )
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
        if route.get("adapter") == "product_pptx_component":
            image = str(
                _prepare_component_product_image_for_approval(
                    job, route, product_image=args.product_image
                )
            )
        else:
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
        if route.get("adapter") == "product_pptx_green":
            model_path = Path((job.get("draft") or {}).get("content_model") or "")
            model = read_json(model_path) if model_path.is_file() else {}
            overview = _green_page_map(model).get("product-overview") or {}
            bound = _asset_source((overview.get("product") or {}).get("image_slot"))
            if not bound or not Path(bound).is_file() or sha256_file(Path(bound)) != image_hash:
                raise SystemExit(
                    "包装图与已批准内容稿绑定图片不一致；请先重新 approve --gate content "
                    "--product-image <图片>，再批准包装图"
                )
        elif route.get("adapter") == "disease_product_scenario_pptx":
            model_path = Path((job.get("draft") or {}).get("content_model") or "")
            model = read_json(model_path) if model_path.is_file() else {}
            bound = _asset_source((model.get("product") or {}).get("image"))
            if not bound or not Path(bound).is_file() or sha256_file(Path(bound)) != image_hash:
                raise SystemExit(
                    "包装图与已批准疾病+商品内容稿不一致；请先重新 approve --gate content "
                    "--product-image <图片>，再批准包装图"
                )
        elif route.get("adapter") == "courseware3_pptx":
            theme_path = Path((job.get("draft") or {}).get("content_model") or "")
            theme = read_json(theme_path) if theme_path.is_file() else {}
            theme_dir = theme_path.parent
            pack_group = _courseware3_resolved_assets(theme, theme_dir).get("packGroup")
            if not pack_group or sha256_file(pack_group) != image_hash:
                raise SystemExit(
                    "包装图与已批准课件3内容稿不一致；请先重新 approve --gate content "
                    "--product-image <图片>，再批准包装图"
                )
        record["product_image"] = image
        record["product_image_sha256"] = image_hash
        record["authorization_reference"] = (
            (args.authorization_reference or "").strip() or "business-confirmed"
        )
        record["content_sha256"] = _require_draft_hash(job)
    elif gate == "visual":
        if not (job.get("approvals") or {}).get("content", {}).get("approved"):
            raise SystemExit("请先 approve --gate content")
        if route.get("adapter") == "product_pptx_component":
            manifest = _prepare_component_visuals_for_approval(
                job,
                route,
                bindings_json=getattr(args, "asset_bindings", None),
            )
            record["asset_bindings"] = manifest
            record["visual_assets_sha256"] = _component_visual_manifest_sha256(
                manifest
            )
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
        "scope": str(job.get("scope") or "production"),
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
        else:
            if route.get("adapter") in {
                "ingredient_health_edu_pptx",
                "product_pptx_component",
            } and rec.get("content_sha256") != draft_hash:
                missing.append("visual_content_hash_mismatch")
            if route.get("adapter") == "product_pptx_component" and not rec.get(
                "visual_assets_sha256"
            ):
                missing.append("visual_asset_hash")
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
    model = read_json(content_model)
    if not isinstance(model, dict):
        raise RuntimeError("content-model.json 格式错误")
    _assert_no_green_gold_residue(model, job["theme"])
    blockers = _green_formal_blockers(model)
    if blockers:
        raise RuntimeError("终稿仍有未完成内容/素材：" + "；".join(blockers[:10]))
    current_digest, asset_manifest = _green_content_digest(content_model, model)
    if current_digest != draft.get("content_sha256"):
        raise RuntimeError("内容或图片已在审批后变化，请重新 approve --gate content")
    content_approval = (job.get("approvals") or {}).get("content") or {}
    if content_approval.get("content_sha256") != current_digest:
        raise RuntimeError("内容审批哈希与当前终稿不一致")
    image_approval = (job.get("approvals") or {}).get("product_image") or {}
    approved_image = Path(str(image_approval.get("product_image") or ""))
    if not approved_image.is_file():
        raise RuntimeError("缺少已批准的本品包装图")
    approved_image_hash = sha256_file(approved_image)
    if approved_image_hash != image_approval.get("product_image_sha256"):
        raise RuntimeError("本品包装图已在批准后变化")
    overview = _green_page_map(model).get("product-overview") or {}
    bound_primary = _asset_source((overview.get("product") or {}).get("image_slot"))
    if not bound_primary or sha256_file(Path(bound_primary)) != approved_image_hash:
        raise RuntimeError("终稿绑定的本品包装图与授权审批记录不一致")

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

    expected_pages = len(model.get("pages") or [])
    qa_pngs = sorted(qa_dir.glob("slide-*.png"))
    qa_layouts = sorted(qa_dir.glob("slide-*.layout.json"))
    inspection = qa_dir / "inspection.ndjson"
    montage = qa_dir / "deck-montage.webp"
    qa_errors: list[str] = []
    if len(qa_pngs) != expected_pages:
        qa_errors.append(f"逐页 PNG {len(qa_pngs)}/{expected_pages}")
    if len(qa_layouts) != expected_pages:
        qa_errors.append(f"逐页 layout {len(qa_layouts)}/{expected_pages}")
    if not inspection.is_file() or not inspection.read_text(encoding="utf-8").strip():
        qa_errors.append("缺 inspection.ndjson")
    if not montage.is_file() or montage.stat().st_size == 0:
        qa_errors.append("缺 deck-montage.webp")
    try:
        with zipfile.ZipFile(out_pptx) as archive:
            slide_xml = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
        if len(slide_xml) != expected_pages:
            qa_errors.append(f"PPTX 页数 {len(slide_xml)}/{expected_pages}")
    except zipfile.BadZipFile:
        qa_errors.append("PPTX 文件结构损坏")
    if inspection.is_file():
        inspection_text = inspection.read_text(encoding="utf-8")
        leaked = [marker for marker in _GREEN_PENDING_MARKERS if marker in inspection_text]
        if leaked:
            qa_errors.append("页面仍含占位标记：" + ",".join(leaked))
    if qa_errors:
        raise RuntimeError("逐页 QA 未通过：" + "；".join(qa_errors))

    qa_summary = ws / "qa-summary.json"
    write_json(
        qa_summary,
        {
            "schema": "fixed-courseware-qa/v1",
            "ok": True,
            "page_count": expected_pages,
            "preview_count": len(qa_pngs),
            "layout_count": len(qa_layouts),
            "content_sha256": current_digest,
            "asset_sha256s": {
                key: value["sha256"] for key, value in sorted(asset_manifest.items())
            },
            "checks": [
                "pptx-zip-valid",
                "page-count-match",
                "per-page-preview-complete",
                "per-page-layout-complete",
                "placeholder-markers-zero",
                "approved-assets-unchanged",
            ],
        },
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
                "请在本机用 WPS 打开终稿.pptx，检查页数与可编辑性。",
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
        "qa-summary.json": qa_summary,
    }
    published = _publish_whitelist(job, route, files)
    return {
        "ok": True,
        "workspace": str(ws),
        "pptx": str(out_pptx),
        "delivery": published,
        "qa_passed": True,
        "page_count": expected_pages,
        "qa_summary": str(qa_summary),
    }


def _render_disease_product_scenario(
    job: dict[str, Any], route: dict[str, Any]
) -> dict[str, Any]:
    draft = job.get("draft") or {}
    content_path = Path(draft.get("content_model") or "")
    if not content_path.is_file():
        raise RuntimeError("缺少疾病+商品 content-model.json")
    model = read_json(content_path)
    if not isinstance(model, dict):
        raise RuntimeError("疾病+商品 content-model.json 格式错误")
    blockers = _disease_formal_blockers(model, job["theme"])
    if blockers:
        raise RuntimeError("终稿仍有未完成内容/素材：" + "；".join(blockers[:10]))
    current_digest, asset_manifest = _disease_content_digest(content_path, model)
    if current_digest != draft.get("content_sha256"):
        raise RuntimeError("疾病+商品内容或图片已在审批后变化，请重新审批")
    content_approval = (job.get("approvals") or {}).get("content") or {}
    if content_approval.get("content_sha256") != current_digest:
        raise RuntimeError("疾病+商品内容审批哈希与当前终稿不一致")
    image_approval = (job.get("approvals") or {}).get("product_image") or {}
    approved_image = Path(str(image_approval.get("product_image") or ""))
    if not approved_image.is_file():
        raise RuntimeError("缺少已批准的本品包装图")
    approved_hash = sha256_file(approved_image)
    if approved_hash != image_approval.get("product_image_sha256"):
        raise RuntimeError("本品包装图已在批准后变化")
    primary_image = Path(str((model.get("product") or {}).get("image") or ""))
    if not primary_image.is_file() or sha256_file(primary_image) != approved_hash:
        raise RuntimeError("疾病+商品终稿绑定包装图与授权审批记录不一致")

    if not _DISEASE_EXPORT.is_file() or not _DISEASE_STYLE.is_file():
        raise RuntimeError("疾病+商品正式引擎或 style_pack 缺失")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("本机缺少 node，无法导出 PPTX")

    ws = job_dir(job["job_id"]) / "workspace" / "render"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    out_pptx = ws / f"{slugify(job['theme'])}_疾病商品场景培训.pptx"
    qa_dir = ws / "qa"
    report_path = qa_dir / "generate-report.json"
    cmd = [
        node,
        str(_DISEASE_EXPORT),
        "--data",
        str(content_path),
        "--style",
        str(_DISEASE_STYLE),
        "--out",
        str(out_pptx),
        "--qa",
        str(qa_dir),
        "--report",
        str(report_path),
    ]
    proc = subprocess.run(cmd, cwd=str(_DISEASE_ENGINE_DIR), capture_output=True, text=True)
    log_path = ws / "render.log"
    log_path.write_text(
        f"$ {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )
    if proc.returncode != 0 or not out_pptx.is_file() or not report_path.is_file():
        raise RuntimeError(f"疾病+商品 PPTX 导出失败 exit={proc.returncode}；见 {log_path}")
    report = read_json(report_path)
    expected_pages = 18
    qa_errors: list[str] = []
    if report.get("ok") is not True:
        qa_errors.append("引擎报告 ok=false")
    if int(report.get("page_count") or 0) != expected_pages:
        qa_errors.append(f"PPTX 页数 {report.get('page_count')}/{expected_pages}")
    if report.get("forbidden_input_hits") or report.get("forbidden_output_hits"):
        qa_errors.append("发现穿心莲金样残留")
    if int(report.get("editable_textboxes") or 0) < 100:
        qa_errors.append("可编辑文本对象数量异常")
    if int(report.get("rendered_images") or 0) < len(asset_manifest):
        qa_errors.append("正式输入图片未完整渲染")
    if report.get("font_patched") is not True:
        qa_errors.append("正式字体未写入")
    qa_pngs = sorted(qa_dir.glob("slide-*.png"))
    qa_layouts = sorted(qa_dir.glob("slide-*.layout.json"))
    if len(qa_pngs) != expected_pages or len(qa_layouts) != expected_pages:
        qa_errors.append(
            f"逐页 QA 不完整 PNG={len(qa_pngs)} layout={len(qa_layouts)}"
        )
    if not (qa_dir / "deck-montage.webp").is_file() or not (
        qa_dir / "inspection.ndjson"
    ).is_file():
        qa_errors.append("缺 montage/inspection")
    try:
        with zipfile.ZipFile(out_pptx) as archive:
            slides = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
        if len(slides) != expected_pages:
            qa_errors.append(f"PPTX ZIP 页数 {len(slides)}/{expected_pages}")
    except zipfile.BadZipFile:
        qa_errors.append("PPTX 文件结构损坏")
    if qa_errors:
        raise RuntimeError("疾病+商品逐页 QA 未通过：" + "；".join(qa_errors))

    qa_summary = ws / "qa-summary.json"
    write_json(
        qa_summary,
        {
            "schema": "fixed-courseware-qa/v1",
            "ok": True,
            "engine": "disease-product-scenario-pptx-v1",
            "page_count": expected_pages,
            "editable_textboxes": report.get("editable_textboxes"),
            "rendered_images": report.get("rendered_images"),
            "content_sha256": current_digest,
            "asset_sha256s": {
                key: value["sha256"] for key, value in sorted(asset_manifest.items())
            },
            "checks": [
                "gold-residue-zero",
                "pptx-native-text",
                "page-count-match",
                "per-page-preview-complete",
                "per-page-layout-complete",
                "approved-assets-unchanged",
            ],
        },
    )
    delivery_note = ws / "交付说明.md"
    delivery_note.write_text(
        "\n".join(
            [
                f"# 交付说明 · {job['theme']}",
                "",
                f"- 任务：`{job['job_id']}`",
                f"- 路线：{route.get('name_zh')}",
                "- 课型：疾病认知 + 商品知识 + 场景演练（固定 18 页）",
                f"- 内容与图片哈希：`{current_digest}`",
                "- 成品：原生可编辑 PPTX，已完成逐页视觉与布局 QA",
                "",
            ]
        ),
        encoding="utf-8",
    )
    approval_copy = ws / "内容确认记录.json"
    write_json(approval_copy, job.get("approvals") or {})
    published = _publish_whitelist(
        job,
        route,
        {
            "终稿.pptx": out_pptx,
            "交付说明.md": delivery_note,
            "内容确认记录.json": approval_copy,
            "qa-summary.json": qa_summary,
        },
    )
    return {
        "ok": True,
        "workspace": str(ws),
        "pptx": str(out_pptx),
        "delivery": published,
        "qa_passed": True,
        "page_count": expected_pages,
        "qa_summary": str(qa_summary),
    }


def _render_courseware3_pptx(
    job: dict[str, Any], route: dict[str, Any]
) -> dict[str, Any]:
    draft = job.get("draft") or {}
    theme_path = Path(draft.get("content_model") or "")
    theme_dir = Path(draft.get("theme_package") or theme_path.parent)
    if not theme_path.is_file():
        raise RuntimeError("缺少课件3 theme.json")
    theme = read_json(theme_path)
    if not isinstance(theme, dict):
        raise RuntimeError("课件3 theme.json 格式错误")
    blockers = _courseware3_formal_blockers(theme, theme_dir, job["theme"])
    if blockers:
        raise RuntimeError("课件3终稿仍有未完成内容/素材：" + "；".join(blockers[:12]))
    current_digest, asset_manifest = _courseware3_content_digest(theme_path, theme)
    if current_digest != draft.get("content_sha256"):
        raise RuntimeError("课件3内容或图片已在审批后变化，请重新审批")
    content_approval = (job.get("approvals") or {}).get("content") or {}
    if content_approval.get("content_sha256") != current_digest:
        raise RuntimeError("课件3内容审批哈希与当前终稿不一致")
    image_approval = (job.get("approvals") or {}).get("product_image") or {}
    approved_image = Path(str(image_approval.get("product_image") or ""))
    if not approved_image.is_file():
        raise RuntimeError("缺少已批准的本品包装图")
    approved_hash = sha256_file(approved_image)
    if approved_hash != image_approval.get("product_image_sha256"):
        raise RuntimeError("本品包装图已在批准后变化")
    pack_group = _courseware3_resolved_assets(theme, theme_dir).get("packGroup")
    if not pack_group or sha256_file(pack_group) != approved_hash:
        raise RuntimeError("课件3主包装图与授权审批记录不一致")

    if not _COURSEWARE3_REPLICATOR.is_file() or not _COURSEWARE3_EXPORT.is_file():
        raise RuntimeError("课件3正式编译器或 PPTX 引擎缺失")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("本机缺少 node，无法导出课件3 PPTX")

    ws = job_dir(job["job_id"]) / "workspace" / "render"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    compiled_parent = ws / "compiled"
    compiled_parent.mkdir()
    cmd_compile = [
        sys.executable,
        str(_COURSEWARE3_REPLICATOR),
        "--theme",
        str(theme_dir),
        "--gold",
        str(_COURSEWARE3_GOLD),
        "--out-parent",
        str(compiled_parent),
        "--out-slug",
        "theme",
        "--skip-tts",
        "--skip-pptx",
    ]
    compile_proc = subprocess.run(
        cmd_compile, cwd=str(ROOT), capture_output=True, text=True
    )
    compiled = compiled_parent / "theme"
    log_path = ws / "render.log"
    log_path.write_text(
        f"$ {' '.join(cmd_compile)}\n\nSTDOUT:\n{compile_proc.stdout}\n\nSTDERR:\n{compile_proc.stderr}\n",
        encoding="utf-8",
    )
    gap_report = compiled / "gap-report.json"
    if compile_proc.returncode != 0 or not gap_report.is_file():
        raise RuntimeError(f"课件3主题编译失败 exit={compile_proc.returncode}；见 {log_path}")
    compile_report = read_json(gap_report)
    if compile_report.get("ok") is not True or int(compile_report.get("gap_count") or 0):
        raise RuntimeError("课件3主题编译仍有缺口，禁止正式导出")

    out_pptx = ws / f"{slugify(job['theme'])}_专项商品培训课件.pptx"
    qa_dir = ws / "qa"
    report_path = qa_dir / "generate-report.json"
    cmd_export = [
        node,
        str(_COURSEWARE3_EXPORT),
        "--model",
        str(compiled / "content-model.json"),
        "--assets",
        str(compiled / "public"),
        "--out",
        str(out_pptx),
        "--qa",
        str(qa_dir),
        "--report",
        str(report_path),
    ]
    export_proc = subprocess.run(
        cmd_export, cwd=str(_COURSEWARE3_ENGINE_DIR), capture_output=True, text=True
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n$ {' '.join(cmd_export)}\n\nSTDOUT:\n{export_proc.stdout}\n\nSTDERR:\n{export_proc.stderr}\n"
        )
    if export_proc.returncode != 0 or not out_pptx.is_file() or not report_path.is_file():
        raise RuntimeError(f"课件3 PPTX 导出失败 exit={export_proc.returncode}；见 {log_path}")

    report = read_json(report_path)
    expected_pages = 13
    qa_errors: list[str] = []
    if report.get("ok") is not True:
        qa_errors.append("引擎报告 ok=false")
    if int(report.get("slides") or 0) != expected_pages:
        qa_errors.append(f"PPTX 页数 {report.get('slides')}/{expected_pages}")
    if report.get("font_patched") is not True:
        qa_errors.append("正式字体未写入")
    qa_pngs = sorted(qa_dir.glob("slide-*.png"))
    qa_layouts = sorted(qa_dir.glob("slide-*.layout.json"))
    if len(qa_pngs) != expected_pages or len(qa_layouts) != expected_pages:
        qa_errors.append(
            f"逐页 QA 不完整 PNG={len(qa_pngs)} layout={len(qa_layouts)}"
        )
    inspection = qa_dir / "inspection.ndjson"
    if not inspection.is_file() or not (qa_dir / "deck-montage.webp").is_file():
        qa_errors.append("缺 montage/inspection")
    is_gold = (
        theme.get("gold_sample") is True
        and theme.get("theme_id") == "courseware.sufuda-product-training-3.gold-v1"
    )
    if inspection.is_file() and not is_gold:
        inspection_text = inspection.read_text(encoding="utf-8")
        leaked = [
            token
            for token in ("速福达", "玛巴洛沙韦", "logo-sufuda", "pack-group-slot")
            if token in inspection_text
        ]
        if leaked:
            qa_errors.append("仍含速福达金样残留：" + ", ".join(leaked))
    native_text_nodes = 0
    try:
        with zipfile.ZipFile(out_pptx) as archive:
            slides = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
            native_text_nodes = sum(archive.read(name).count(b"<a:t") for name in slides)
        if len(slides) != expected_pages:
            qa_errors.append(f"PPTX ZIP 页数 {len(slides)}/{expected_pages}")
        if native_text_nodes < 100:
            qa_errors.append("原生可编辑文本对象数量异常")
    except zipfile.BadZipFile:
        qa_errors.append("PPTX 文件结构损坏")
    if qa_errors:
        raise RuntimeError("课件3逐页 QA 未通过：" + "；".join(qa_errors))

    qa_summary = ws / "qa-summary.json"
    write_json(
        qa_summary,
        {
            "schema": "fixed-courseware-qa/v1",
            "ok": True,
            "engine": "courseware3-pptx-v1",
            "page_count": expected_pages,
            "native_text_nodes": native_text_nodes,
            "content_sha256": current_digest,
            "asset_sha256s": {
                key: value["sha256"] for key, value in sorted(asset_manifest.items())
            },
            "checks": [
                "gold-copy-and-images-zero",
                "pptx-native-text",
                "page-count-match",
                "per-page-preview-complete",
                "per-page-layout-complete",
                "approved-assets-unchanged",
            ],
        },
    )
    delivery_note = ws / "交付说明.md"
    delivery_note.write_text(
        "\n".join(
            [
                f"# 交付说明 · {job['theme']}",
                "",
                f"- 任务：`{job['job_id']}`",
                f"- 路线：{route.get('name_zh')}",
                "- 课型：专项商品讲解（13 页可编辑 PPTX）",
                f"- 内容与图片哈希：`{current_digest}`",
                "- 已完成逐页视觉、布局、原生文本与金样残留 QA",
                "",
                "MP4 是独立路线；本次只交付已验证的 PPTX。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    approval_copy = ws / "内容确认记录.json"
    write_json(approval_copy, job.get("approvals") or {})
    published = _publish_whitelist(
        job,
        route,
        {
            "终稿.pptx": out_pptx,
            "交付说明.md": delivery_note,
            "内容确认记录.json": approval_copy,
            "qa-summary.json": qa_summary,
        },
    )
    return {
        "ok": True,
        "workspace": str(ws),
        "pptx": str(out_pptx),
        "delivery": published,
        "qa_passed": True,
        "page_count": expected_pages,
        "qa_summary": str(qa_summary),
    }


def _render_ingredient_health_edu_pptx(
    job: dict[str, Any], route: dict[str, Any]
) -> dict[str, Any]:
    draft = job.get("draft") or {}
    theme_path = Path(draft.get("content_model") or "")
    if not theme_path.is_file():
        raise RuntimeError("缺少 20 页成分健康科普 theme.json")
    theme = read_json(theme_path)
    if not isinstance(theme, dict):
        raise RuntimeError("成分健康科普 theme.json 格式错误")
    blockers = _ingredient_health_formal_blockers(theme_path, job["theme"])
    if blockers:
        raise RuntimeError(
            "20 页成分健康科普终稿仍有未完成内容/素材："
            + "；".join(blockers[:12])
        )
    current_digest, asset_manifest = _ingredient_health_content_digest(
        theme_path, theme
    )
    if current_digest != draft.get("content_sha256"):
        raise RuntimeError("成分科普内容或图片已在审批后变化，请重新审批")
    approvals = job.get("approvals") or {}
    for gate in ("content", "visual"):
        record = approvals.get(gate) or {}
        if record.get("approved") is not True:
            raise RuntimeError(f"缺少 {gate} 审批")
        if record.get("content_sha256") != current_digest:
            raise RuntimeError(f"{gate} 审批哈希与当前内容/图片不一致")

    if not _INGREDIENT_HEALTH_EXPORT.is_file():
        raise RuntimeError("缺少 ingredient-health-edu-pptx-v1 正式引擎")
    canonical = _INGREDIENT_HEALTH_SETTLED / "番茄红素_健康科普金样_v1.pptx"
    if not canonical.is_file():
        raise RuntimeError("缺少 settled 20 页 canonical PPTX")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("本机缺少 node，无法导出 20 页可编辑 PPTX")

    ws = job_dir(job["job_id"]) / "workspace" / "render"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    qa_dir = ws / "qa"
    report_path = qa_dir / "generate-report.json"
    approval_path = ws / "engine-approvals.json"
    write_json(approval_path, approvals)
    out_pptx = ws / f"{slugify(job['theme'])}_20页成分健康科普课件.pptx"
    cmd = [
        node,
        str(_INGREDIENT_HEALTH_EXPORT),
        "--theme",
        str(theme_path),
        "--approval",
        str(approval_path),
        "--out",
        str(out_pptx),
        "--qa",
        str(qa_dir),
        "--report",
        str(report_path),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    log_path = ws / "render.log"
    log_path.write_text(
        f"$ {' '.join(cmd)}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )
    if proc.returncode != 0 or not out_pptx.is_file() or not report_path.is_file():
        raise RuntimeError(
            f"20 页成分健康科普 PPTX 导出失败 exit={proc.returncode}；见 {log_path}"
        )

    report = read_json(report_path)
    expected_pages = 20
    qa_errors: list[str] = []
    if report.get("ok") is not True:
        qa_errors.append("引擎报告 ok=false")
    if int(report.get("page_count") or 0) != expected_pages:
        qa_errors.append(f"PPTX 页数 {report.get('page_count')}/{expected_pages}")
    contract = report.get("contract") or {}
    if int(contract.get("text_slots") or 0) != 107:
        qa_errors.append("OOXML 文字槽不是 107")
    if int(contract.get("slide_image_slots") or 0) != 67:
        qa_errors.append("页面图片槽不是 67")
    if int(contract.get("template_image_slots") or 0) != 2:
        qa_errors.append("母版/版式图片槽不是 2")
    if report.get("content_sha256") != current_digest:
        qa_errors.append("引擎内容/图片哈希与审批稿不一致")
    qa_pngs = sorted(qa_dir.glob("slide-*.png"))
    qa_layouts = sorted(qa_dir.glob("slide-*.layout.json"))
    if len(qa_pngs) != expected_pages or len(qa_layouts) != expected_pages:
        qa_errors.append(
            f"逐页 QA 不完整 PNG={len(qa_pngs)} layout={len(qa_layouts)}"
        )
    if not (qa_dir / "deck-montage.webp").is_file():
        qa_errors.append("缺少整套 montage")
    if not (qa_dir / "inspection.ndjson").is_file():
        qa_errors.append("缺少逐对象 inspection")
    pptx_validation = report.get("pptx_validation") or {}
    if pptx_validation.get("ok") is not True:
        qa_errors.append("PPTX ZIP/残留校验失败")
    if pptx_validation.get("source_media_leaks"):
        qa_errors.append("仍含参考源媒体 SHA-256")
    if pptx_validation.get("approved_assets_missing"):
        qa_errors.append("批准图片未全部写入 PPTX")
    if int(pptx_validation.get("approved_asset_count") or 0) != len(asset_manifest):
        qa_errors.append("引擎批准资产数量与任务快照不一致")

    native_text_nodes = 0
    try:
        with zipfile.ZipFile(out_pptx) as archive:
            slides = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
            native_text_nodes = sum(archive.read(name).count(b"<a:t") for name in slides)
        if len(slides) != expected_pages:
            qa_errors.append(f"PPTX ZIP 页数 {len(slides)}/{expected_pages}")
        if native_text_nodes < 100:
            qa_errors.append("原生可编辑文本对象数量异常")
    except zipfile.BadZipFile:
        qa_errors.append("PPTX 文件结构损坏")
    if qa_errors:
        raise RuntimeError("20 页成分健康科普逐页 QA 未通过：" + "；".join(qa_errors))

    qa_summary = ws / "qa-summary.json"
    write_json(
        qa_summary,
        {
            "schema": "fixed-courseware-qa/v1",
            "ok": True,
            "engine": "ingredient-health-edu-pptx-v1",
            "page_count": expected_pages,
            "native_text_nodes": native_text_nodes,
            "text_slots": 107,
            "explicit_image_bindings": 69,
            "content_sha256": current_digest,
            "asset_sha256s": {
                key: value["sha256"] for key, value in sorted(asset_manifest.items())
            },
            "checks": [
                "original-ooxml-structure",
                "all-text-slots-explicit",
                "all-image-slots-explicit",
                "source-medical-copy-zero",
                "source-media-sha-zero",
                "approved-assets-present",
                "pptx-native-text",
                "page-count-match",
                "per-page-preview-complete",
                "per-page-layout-complete",
                "approved-assets-unchanged",
            ],
        },
    )
    delivery_note = ws / "交付说明.md"
    delivery_note.write_text(
        "\n".join(
            [
                f"# 交付说明 · {job['theme']}",
                "",
                f"- 任务：`{job['job_id']}`",
                f"- 路线：{route.get('name_zh')}",
                "- 课型：成分健康科普（20 页、15 类页型）",
                f"- 内容与 69 个图片槽哈希：`{current_digest}`",
                "- 成品：基于签样原 OOXML 结构换槽的可编辑 PPTX",
                "- 已完成 20 页视觉、布局、原生文本、批准资产和金样残留 QA",
                "",
                "金样参考医学正文未作为默认内容继承；本成品只使用本任务已审批稿。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    approval_copy = ws / "内容确认记录.json"
    write_json(approval_copy, approvals)
    published = _publish_whitelist(
        job,
        route,
        {
            "终稿.pptx": out_pptx,
            "交付说明.md": delivery_note,
            "内容确认记录.json": approval_copy,
            "qa-summary.json": qa_summary,
        },
    )
    return {
        "ok": True,
        "workspace": str(ws),
        "pptx": str(out_pptx),
        "delivery": published,
        "qa_passed": True,
        "page_count": expected_pages,
        "qa_summary": str(qa_summary),
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

    script = read_json(script_path)
    if not isinstance(script, dict):
        raise RuntimeError("构件脚本格式错误")

    sequence_blockers = _component_page_sequence_blockers(script)
    if sequence_blockers:
        raise RuntimeError(
            "构件页签未通过正式门闸：" + "；".join(sequence_blockers[:8])
        )

    # Re-hash only business copy. Replaceable, separately approved image paths are
    # intentionally excluded from this digest.
    current = _component_content_sha256(script)
    approved = ((job.get("approvals") or {}).get("content") or {}).get("content_sha256")
    if approved and approved != current:
        raise RuntimeError("内容审批哈希与当前 script.structured.json 不一致，请重新 draft/approve")

    asset_plan = build_product_pptx_asset_plan(
        script, template_slug=str(route.get("template_slug") or "")
    )
    blockers = formal_render_blockers(asset_plan)
    if blockers:
        preview = "；".join(blockers[:6])
        if len(blockers) > 6:
            preview += f"；另有 {len(blockers) - 6} 项"
        raise RuntimeError(f"正式素材未齐，禁止生成/交付：{preview}")
    _verify_component_asset_approvals(job, script, asset_plan)

    ws = job_dir(job["job_id"]) / "workspace" / "render"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)

    report = _run_courseware_generator(
        script_path=script_path,
        out_dir=ws,
        skip_export=False,
        skip_qa=False,
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

    qa_files = report.get("qa") or []
    page_count = int(report.get("page_count") or 0)
    if not qa_files or (page_count and len(qa_files) != page_count):
        return {
            "ok": False,
            "workspace": str(ws),
            "pptx": str(out_pptx),
            "qa_passed": False,
            "error": "未产出完整逐页视觉 QA 预览，禁止发布正式交付；请由 WorkBuddy 检查项目内 artifact-tool 运行环境及逐页 QA 依赖后重试。",
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
                "请在本机用 WPS 打开终稿.pptx，检查页数与可编辑性。",
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
    "disease_product_scenario_pptx": _render_disease_product_scenario,
    "courseware3_pptx": _render_courseware3_pptx,
    "ingredient_health_edu_pptx": _render_ingredient_health_edu_pptx,
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
            "scope": str(job.get("scope") or "production"),
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
                "scope": str(job.get("scope") or "production"),
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
        scope_label = "[UAT模拟] " if row["scope"] == "uat" else ""
        print(
            f"{scope_label}{row['job_id']}\n"
            f"  {row['theme']} · {row['route_id']}\n"
            f"  状态：{row['business_status']} ({row['state']})\n"
            f"  下一步：{row['next_step']}"
        )
        if (row.get("delivery") or {}).get("path"):
            print(f"  取件：{row['delivery']['path']}")
    return 0


def _find_macos_wps_app() -> Path | None:
    return next((path for path in _MACOS_WPS_APP_CANDIDATES if path.is_dir()), None)


def _delivery_presentation(delivery: Path) -> Path | None:
    if delivery.is_file() and delivery.suffix.lower() in _PRESENTATION_SUFFIXES:
        return delivery
    if not delivery.is_dir():
        return None
    for name in ("终稿.pptx", "终稿.ppt"):
        candidate = delivery / name
        if candidate.is_file():
            return candidate
    return next(
        (
            path
            for path in sorted(delivery.iterdir())
            if path.is_file() and path.suffix.lower() in _PRESENTATION_SUFFIXES
        ),
        None,
    )


def _open_business_path(path: Path) -> None:
    if path.is_file() and path.suffix.lower() in _PRESENTATION_SUFFIXES:
        wps_app = _find_macos_wps_app()
        if not wps_app:
            raise SystemExit(
                "未找到 WPS Office，无法打开 PPT/PPTX；请先安装 WPS 后重试。"
            )
        proc = subprocess.run(
            ["open", "-a", str(wps_app), str(path)],
            check=False,
        )
        if proc.returncode != 0:
            raise SystemExit(f"WPS Office 打开失败：{path}")
        return
    subprocess.run(["open", str(path)], check=False)


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
        reveal_target = existing[0]
        if delivery:
            reveal_target = _delivery_presentation(Path(delivery)) or reveal_target
        _open_business_path(reveal_target)
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

    p = sub.add_parser("recommend", help="先按自然语言推荐课型，不创建任务")
    p.add_argument("request", nargs="?", help="业务需求自然语言")
    p.add_argument("--text", help="业务需求自然语言；与位置参数二选一")
    p.add_argument("--check-env", action="store_true", help="同时探测本机渲染能力")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_recommend)

    p = sub.add_parser("list-routes", help="列出业务路线")
    p.add_argument("--all", action="store_true", help="包含未激活路线")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-probe", action="store_true")
    p.set_defaults(func=cmd_list_routes)

    p = sub.add_parser("new", help="创建任务")
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
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
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
    p.add_argument("--job", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_draft)

    p = sub.add_parser("approve", help="绑定审批")
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
    p.add_argument("--job", required=True)
    p.add_argument("--gate", required=True, choices=["content", "visual", "product_image"])
    p.add_argument("--by", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--content-sha256", default=None)
    p.add_argument("--product-image", type=Path, default=None)
    p.add_argument(
        "--asset-bindings",
        type=Path,
        default=None,
        help="构件 PPT visual 确认：WorkBuddy 生成图的 {script_path: 本地图片路径} JSON",
    )
    p.add_argument("--authorization-reference", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("render", help="审批通过后生成并白名单发布")
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
    p.add_argument("--job", required=True)
    p.add_argument("--ignore-env", action="store_true", help="仅调试；生产勿用")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("status", help="查看任务状态")
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
    p.add_argument("--job", default=None)
    p.add_argument("--state", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="列出任务")
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
    p.add_argument("--state", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("open", help="打印/打开任务与取件路径")
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
    p.add_argument("--job", required=True)
    p.add_argument("--reveal", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_open)

    p = sub.add_parser("retry", help="失败任务重试")
    p.add_argument("--scope", choices=_VALID_SCOPES, default="production")
    p.add_argument("--job", required=True)
    p.add_argument("--ignore-env", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_retry)

    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    set_active_scope(getattr(args, "scope", "production"))
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
