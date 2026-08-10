#!/usr/bin/env python3
"""Business environment doctor — map routes to runtime profiles and probe honestly.

  python3 scripts/business_doctor.py
  python3 scripts/business_doctor.py --route product-pptx-component-v1
  python3 scripts/business_doctor.py --profile pptx --json
  python3 scripts/business_doctor.py --list-profiles

Does not install paid services. Prints install hints from runtime-profiles.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILES_PATH = ROOT / "production-library" / "runtime-profiles.json"
ROUTES_PATH = ROOT / "production-library" / "business-routes.json"

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import probe_production_env as probe  # noqa: E402


def load_profiles() -> dict[str, Any]:
    if not PROFILES_PATH.is_file():
        raise SystemExit(f"missing runtime profiles: {PROFILES_PATH}")
    return json.loads(PROFILES_PATH.read_text(encoding="utf-8"))


def load_routes() -> list[dict[str, Any]]:
    if not ROUTES_PATH.is_file():
        raise SystemExit(f"missing business routes: {ROUTES_PATH}")
    return list(json.loads(ROUTES_PATH.read_text(encoding="utf-8")).get("routes") or [])


def profile_for_route(doc: dict[str, Any], route_id: str) -> str | None:
    mapping = doc.get("route_to_profile") or {}
    if route_id in mapping:
        return mapping[route_id]
    # fallback: first profile listing this route
    for pid, prof in (doc.get("profiles") or {}).items():
        if route_id in (prof.get("routes") or []):
            return pid
    return None


def doctor(
    *,
    route_id: str | None = None,
    profile_id: str | None = None,
) -> dict[str, Any]:
    doc = load_profiles()
    profiles = doc.get("profiles") or {}

    selected: list[str] = []
    if profile_id:
        if profile_id not in profiles:
            raise SystemExit(f"未知 profile: {profile_id}")
        selected = [profile_id]
    elif route_id:
        pid = profile_for_route(doc, route_id)
        if pid is None:
            return {
                "ok": True,
                "route_id": route_id,
                "profile_id": None,
                "message_zh": "该路线无需额外运行时能力（如仅金样预览）",
                "missing_capabilities": [],
                "install_hints_zh": [],
            }
        selected = [pid]
    else:
        # default: active routes' profiles
        active_ids = {r["route_id"] for r in load_routes() if r.get("active")}
        for rid in sorted(active_ids):
            pid = profile_for_route(doc, rid)
            if pid and pid not in selected:
                selected.append(pid)
        if not selected:
            selected = ["pptx"]

    report = probe.probe()
    require_tokens: list[str] = []
    hints: list[str] = []
    profile_details: list[dict[str, Any]] = []

    for pid in selected:
        prof = profiles[pid]
        for token in prof.get("probe_require") or []:
            if token not in require_tokens:
                require_tokens.append(token)
        for hint in prof.get("install_hints_zh") or []:
            if hint not in hints:
                hints.append(hint)
        profile_details.append(
            {
                "profile_id": pid,
                "name_zh": prof.get("name_zh"),
                "require_capabilities": prof.get("require_capabilities") or [],
                "probe_require": prof.get("probe_require") or [],
                "deps": prof.get("deps") or {},
            }
        )

    checked = probe.apply_requirements(report, require_tokens) if require_tokens else report
    missing = list(checked.get("missing_capabilities") or [])
    ok = bool(checked.get("ok", True)) if require_tokens else True

    pptx_engines = {
        "product-pptx-component-v1": ROOT / "production-library/engines/courseware-pptx-v1/export.mjs",
        "product-pptx-green-v1": ROOT / "production-library/engines/product-courseware-green-v1/build-product-courseware.mjs",
        "product-pptx-disease-scenario-v1": ROOT / "production-library/engines/disease-product-scenario-pptx-v1/export.mjs",
        "courseware3-pptx-v1": ROOT / "production-library/engines/courseware3-pptx-v1/export.mjs",
        "ingredient-health-edu-pptx-v1": ROOT / "production-library/engines/ingredient-health-edu-pptx-v1/export.mjs",
    }
    active_route_ids = {r["route_id"] for r in load_routes() if r.get("active")}
    if route_id:
        required_engine_routes = [route_id]
    elif any(p == "pptx" for p in selected):
        required_engine_routes = [
            rid for rid in pptx_engines if rid in active_route_ids
        ]
    else:
        required_engine_routes = []
    engine_presence = {rid: path.is_file() for rid, path in pptx_engines.items()}
    for rid in required_engine_routes:
        path = pptx_engines.get(rid)
        if path is None or path.is_file():
            continue
        ok = False
        missing_name = f"{rid}_engine"
        if missing_name not in missing:
            missing.append(missing_name)
        hints.append(f"缺少路线引擎：{path.relative_to(ROOT)}")

    video_env: dict[str, Any] | None = None
    if any(p == "video-full" for p in selected):
        try:
            import video_full_env as vfe  # type: ignore

            video_env = vfe.build_check_report()
            for h in video_env.get("install_hints_zh") or []:
                if h not in hints:
                    hints.append(h)
            for m in video_env.get("missing") or []:
                if m not in missing:
                    missing.append(m)
            if not video_env.get("ok"):
                ok = False
        except Exception as exc:  # noqa: BLE001
            hints.append(f"video_full_env 检查跳过: {exc}")

    payload = {
        "ok": ok and not missing,
        "route_id": route_id,
        "profiles": profile_details,
        "require": require_tokens,
        "missing_capabilities": missing,
        "capabilities": checked.get("capabilities") or {},
        "paths": checked.get("paths") or {},
        "messages_zh": checked.get("messages_zh") or [],
        "install_hints_zh": hints if missing else [],
        "engine": {
            "routes": {rid: str(path) for rid, path in pptx_engines.items()},
            "route_present": engine_presence,
            "present": all(engine_presence.get(rid, False) for rid in required_engine_routes),
        },
        "video_full_env": video_env,
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Business runtime doctor")
    ap.add_argument("--route", help="business route_id")
    ap.add_argument("--profile", help="runtime profile id (pptx / video-full / …)")
    ap.add_argument("--list-profiles", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.list_profiles:
        doc = load_profiles()
        if args.json:
            print(json.dumps(doc, ensure_ascii=False, indent=2))
        else:
            print("runtime profiles:")
            for pid, prof in (doc.get("profiles") or {}).items():
                print(f"  - {pid}: {prof.get('name_zh')}")
            print("route_to_profile:")
            for rid, pid in (doc.get("route_to_profile") or {}).items():
                print(f"  - {rid} → {pid}")
        return 0

    result = doctor(route_id=args.route, profile_id=args.profile)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "OK" if result["ok"] else "BLOCKED"
        print(f"doctor · {status}")
        if result.get("route_id"):
            print(f"路线：{result['route_id']}")
        for prof in result.get("profiles") or []:
            print(f"profile：{prof['profile_id']}（{prof.get('name_zh')}）")
        if result.get("missing_capabilities"):
            print("缺失能力：" + ", ".join(result["missing_capabilities"]))
            print("安装提示：")
            for hint in result.get("install_hints_zh") or []:
                print(f"  · {hint}")
        else:
            print("本机满足所选 profile 所需能力。")
        for msg in result.get("messages_zh") or []:
            print(f"- {msg}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
