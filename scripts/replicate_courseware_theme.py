#!/usr/bin/env python3
"""从速福达金样框架复刻其他商品主题课件。

输入 theme 包（theme.json + 可选 assets/）→ 复制框架 → 合并 content-model →
可选克隆旁白 → 导出 PPTX → 写出 gap-report。

示例：
  python3 scripts/replicate_courseware_theme.py \\
    --theme production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/theme-packages/demo-product-b \\
    --out-slug demo-product-b-courseware-v1 \\
    --skip-tts
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLD = (
    ROOT
    / "production-library/validation/courseware/sufuda-product-courseware-3-gold-v1"
)
DEFAULT_OUT_PARENT = ROOT / "production-library/validation/courseware"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge_content(base: dict, theme: dict) -> tuple[dict, list[dict]]:
    """Merge theme overrides into gold content-model. Returns (model, gaps)."""
    model = deepcopy(base)
    gaps: list[dict] = []

    product = theme.get("product") or {}
    if product:
        model.setdefault("product", {}).update(product)
        if product.get("display_name"):
            model["title"] = f"{product['display_name']} · 商品培训课件（主题复刻）"

    if theme.get("project_id"):
        model["project_id"] = theme["project_id"]
    if theme.get("title"):
        model["title"] = theme["title"]

    # Asset path overrides (relative to theme package or absolute under new project)
    asset_overrides = theme.get("assets") or {}
    for key, value in asset_overrides.items():
        if value in (None, "", "TODO", "awaiting-business"):
            gaps.append(
                {
                    "type": "asset_missing",
                    "asset_key": key,
                    "detail": "主题包未提供授权资产，保留金样示意或槽位",
                }
            )
            continue
        model.setdefault("assets", {})[key] = value

    # Page element text / asset overrides
    page_overrides = {p["id"]: p for p in theme.get("pages") or [] if "id" in p}
    for page in model.get("pages") or []:
        ov = page_overrides.get(page["id"])
        if not ov:
            continue
        if ov.get("chapter"):
            page["chapter"] = ov["chapter"]
        if ov.get("nav"):
            page["nav"] = ov["nav"]
        if ov.get("title"):
            page["title"] = ov["title"]
        elements_ov = ov.get("elements") or {}
        for role, el_ov in elements_ov.items():
            if role not in page.get("elements", {}):
                gaps.append(
                    {
                        "type": "unknown_element",
                        "page_id": page["id"],
                        "role": role,
                    }
                )
                continue
            target = page["elements"][role]
            if isinstance(el_ov, str):
                if target.get("kind") == "text":
                    target["text"] = el_ov
                elif target.get("kind") == "image":
                    target["asset"] = el_ov
            elif isinstance(el_ov, dict):
                if "text" in el_ov:
                    target["text"] = el_ov["text"]
                if "asset" in el_ov:
                    target["asset"] = el_ov["asset"]
                    model.setdefault("assets", {})[el_ov.get("asset_key", target.get("asset", role))] = el_ov["asset"]

    # Captions / narration blocks for storyboard
    if theme.get("captions"):
        model["_theme_captions"] = theme["captions"]
    if theme.get("narration_blocks"):
        model["_theme_narration_blocks"] = theme["narration_blocks"]

    required_slots = theme.get("required_business_assets") or ["logo", "packGroup"]
    for key in required_slots:
        val = (model.get("assets") or {}).get(key, "")
        if not val or "slot" in str(val) or "TODO" in str(val):
            gaps.append(
                {
                    "type": "business_asset_pending",
                    "asset_key": key,
                    "detail": "需业务提供授权包装/Logo 后替换",
                }
            )

    return model, gaps


def copy_framework(gold: Path, dest: Path) -> None:
    if dest.exists():
        raise SystemExit(f"输出目录已存在，拒绝覆盖: {dest}")
    ignore = shutil.ignore_patterns(
        "node_modules",
        "dist",
        "out",
        "audio-work",
        "qa",
        "reference",
        "theme-packages",
        ".DS_Store",
        "*.mp4",
        "*.wav",
        "pptx-qa",
    )
    shutil.copytree(gold, dest, ignore=ignore)
    # Re-link node_modules like gold
    nm = dest / "node_modules"
    gold_nm = gold / "node_modules"
    if gold_nm.is_symlink() or gold_nm.exists():
        if nm.exists() or nm.is_symlink():
            nm.unlink()
        nm.symlink_to(gold_nm.resolve() if gold_nm.is_symlink() else gold_nm)


def update_storyboard(dest: Path, model: dict, theme: dict) -> None:
    sb_path = dest / "storyboard.json"
    sb = load_json(sb_path)
    sb["project_id"] = model.get("project_id", sb.get("project_id"))
    sb["title"] = model.get("title", sb.get("title"))
    sb["theme_replication"] = {
        "source_gold": "sufuda-product-courseware-3-gold-v1",
        "theme_id": theme.get("theme_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Map content-model assets into storyboard assets (path form /assets/...)
    assets = model.get("assets") or {}
    mapped = {}
    for k, v in assets.items():
        if isinstance(v, str) and v.startswith("/assets/"):
            mapped[k] = v
        elif isinstance(v, str) and v.startswith("assets/"):
            mapped[k] = "/" + v
        elif isinstance(v, str) and "/" in v:
            # external path — leave for manual copy; keep gold path if known
            mapped[k] = v if v.startswith("/") else f"/assets/{Path(v).name}"
        else:
            mapped[k] = v
    # Keep storyboard keys that project.tsx expects
    sb_assets = sb.get("assets") or {}
    for k, v in mapped.items():
        if k in sb_assets or k in (
            "background",
            "logo",
            "packGroup",
            "pack40",
            "pack20",
            "packSusp",
            "icon365",
            "iconTree",
            "iconVirus",
            "iconLungs",
            "iconWarn",
            "iconChina",
            "iconBaby",
            "iconShield",
            "icon24h",
            "iconThumb",
            "iconAward",
            "icon70",
            "iconFlag",
            "iconHand",
            "cell",
            "family",
            "patient",
            "charElder",
            "charChild",
            "charChronic",
            "bust",
            "tablets",
            "granule",
            "boxFever",
            "boxChronic",
        ):
            sb_assets[k] = v if str(v).startswith("/") else f"/assets/{Path(str(v)).name}"
    sb["assets"] = sb_assets

    captions = theme.get("captions") or model.get("_theme_captions")
    if captions:
        # Accept list of strings or {start,end,text}
        normalized = []
        t = 0.0
        for item in captions:
            if isinstance(item, str):
                dur = max(1.2, min(4.5, len(item) / 4.8))
                normalized.append({"start": round(t, 3), "end": round(t + dur, 3), "text": item})
                t += dur + 0.08
            elif isinstance(item, dict) and "text" in item:
                normalized.append(item)
        if normalized:
            sb["captions"] = normalized
            sb["duration"] = max(normalized[-1].get("end", 1), float(sb.get("duration") or 1))

    write_json(sb_path, sb)


def copy_theme_assets(theme_dir: Path, dest: Path) -> None:
    src_assets = theme_dir / "assets"
    if not src_assets.is_dir():
        return
    target = dest / "public" / "assets"
    target.mkdir(parents=True, exist_ok=True)
    for f in src_assets.iterdir():
        if f.is_file():
            shutil.copy2(f, target / f.name)


def export_pptx(dest: Path) -> Path | None:
    script = dest / "scripts" / "export-sufuda-pptx.mjs"
    if not script.exists():
        return None
    out = dest / "out" / f"{dest.name}_可编辑课件.pptx"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "node",
            str(script),
            "--model",
            str(dest / "content-model.json"),
            "--assets",
            str(dest / "public"),
            "--out",
            str(out),
        ],
        check=True,
        cwd=str(dest),
    )
    return out


def maybe_clone_tts(dest: Path, voice: Path, skip: bool) -> None:
    if skip:
        return
    script = ROOT / "scripts" / "generate_courseware_cloned_narration.py"
    if not script.exists():
        print("WARN: clone narration script missing; skip TTS", file=sys.stderr)
        return
    out_dir = dest / "audio-work" / "clone-theme-v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(script),
        "--storyboard",
        str(dest / "storyboard.json"),
        "--voice-pack",
        str(voice),
        "--out-dir",
        str(out_dir),
        "--copy-to-assets",
        str(dest / "public" / "assets" / "narration-cloned.wav"),
        "--apply-to-storyboard",
    ]
    print("Running TTS:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Replicate sufuda courseware gold to a new product theme")
    ap.add_argument("--theme", type=Path, required=True, help="Theme package directory containing theme.json")
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    ap.add_argument("--out-parent", type=Path, default=DEFAULT_OUT_PARENT)
    ap.add_argument("--out-slug", type=str, default=None, help="Output folder name under validation/courseware/")
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--skip-pptx", action="store_true")
    ap.add_argument(
        "--voice-pack",
        type=Path,
        default=ROOT / "production-library/voices/sufuda-courseware-pharmacist-v1",
    )
    args = ap.parse_args()

    theme_dir = args.theme.resolve()
    theme_json = theme_dir / "theme.json"
    if not theme_json.exists():
        raise SystemExit(f"缺少 theme.json: {theme_json}")

    theme = load_json(theme_json)
    gold = args.gold.resolve()
    slug = args.out_slug or theme.get("slug") or theme.get("theme_id") or theme_dir.name
    dest = (args.out_parent / slug).resolve()

    print(f"Gold:  {gold}")
    print(f"Theme: {theme_dir}")
    print(f"Out:   {dest}")

    copy_framework(gold, dest)
    copy_theme_assets(theme_dir, dest)

    base_model = load_json(gold / "content-model.json")
    model, gaps = merge_content(base_model, theme)
    write_json(dest / "content-model.json", {k: v for k, v in model.items() if not str(k).startswith("_")})

    # Rebuild layer-manifest from merged model
    layers = []
    for page in model.get("pages") or []:
        for role, el in (page.get("elements") or {}).items():
            layers.append(
                {
                    "element_id": el["id"],
                    "page_id": page["id"],
                    "page_type": page.get("type"),
                    "role": role,
                    "kind": el.get("kind"),
                    "slot": el.get("slot"),
                    "asset_key": el.get("asset"),
                    "replace_rule": el.get("replace"),
                    "default_text": el.get("text") if el.get("kind") == "text" else None,
                }
            )
    write_json(
        dest / "layer-manifest.json",
        {
            "project_id": model.get("project_id"),
            "template_id": model.get("template_id"),
            "style_pack_id": model.get("style_pack_id"),
            "status": "theme-replication",
            "source_theme": theme.get("theme_id"),
            "layer_count": len(layers),
            "layers": layers,
            "pages": [
                {
                    "id": p["id"],
                    "type": p.get("type"),
                    "title": p.get("title"),
                    "element_ids": [e["id"] for e in (p.get("elements") or {}).values()],
                }
                for p in model.get("pages") or []
            ],
        },
    )

    update_storyboard(dest, model, theme)

    pptx_path = None
    if not args.skip_pptx:
        try:
            pptx_path = export_pptx(dest)
        except subprocess.CalledProcessError as e:
            gaps.append({"type": "pptx_export_failed", "detail": str(e)})
            print("WARN: PPTX export failed", e, file=sys.stderr)

    try:
        maybe_clone_tts(dest, args.voice_pack, args.skip_tts)
    except subprocess.CalledProcessError as e:
        gaps.append({"type": "tts_failed", "detail": str(e)})
        print("WARN: TTS failed", e, file=sys.stderr)

    report = {
        "ok": True,
        "theme_id": theme.get("theme_id"),
        "slug": slug,
        "output": str(dest),
        "pptx": str(pptx_path) if pptx_path else None,
        "gaps": gaps,
        "gap_count": len(gaps),
        "next_steps": [
            "用业务授权包装/Logo 替换 public/assets 槽位图",
            "核对 content-model 文案是否与审核稿一致",
            "去掉 --skip-tts 生成克隆旁白后 npm run render",
            "业务确认前不要晋升到 templates/settled/",
        ],
    }
    write_json(dest / "gap-report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
