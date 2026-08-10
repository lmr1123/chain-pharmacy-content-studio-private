#!/usr/bin/env python3
"""业务课件绿线（课件3 速福达壳 · 优先 PPTX）：theme 包 → content-model → PPTX + gap-report。

对业务只讲三步；本脚本由 WorkBuddy 在本机执行。

示例：

  # 结构验证主题（无 TTS）
  python3 scripts/generate_business_courseware.py \\
    --template courseware3 \\
    --theme production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/theme-packages/demo-product-b \\
    --out-slug demo-product-b-courseware-smoke \\
    --skip-tts

  # 从聊天整理的 theme.json（目录内需有 theme.json）
  python3 scripts/generate_business_courseware.py \\
    --template courseware3 \\
    --theme path/to/my-theme-dir \\
    --skip-tts

  # 有 TTS 环境时再出克隆旁白（视频另 npm run render）
  .venv-qwen-tts/bin/python scripts/generate_business_courseware.py \\
    --template courseware3 --theme path/to/theme

课件4 入口预留（--template courseware4）：当前走同一 replicate 框架尚未接线，会明确报错并提示用 validation export。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

TEMPLATES: dict[str, dict[str, Any]] = {
    "courseware3": {
        "aliases": [
            "cw3",
            "sufuda",
            "速福达",
            "商品培训课件3",
            "sufuda-mabaloshawei-product-courseware-3-v1",
        ],
        "settled": ROOT
        / "production-library/templates/settled/sufuda-mabaloshawei-product-courseware-3-v1",
        "gold": ROOT
        / "production-library/validation/courseware/sufuda-product-courseware-3-gold-v1",
        "voice_pack": ROOT / "production-library/voices/sufuda-courseware-pharmacist-v1",
        "voice_id": "voice.sufuda-courseware-pharmacist-v1",
        "name_zh": "商品培训课件3（视频+PPT，速福达壳）",
        "replicate": True,
    },
    "courseware4": {
        "aliases": [
            "cw4",
            "番茄",
            "番茄红素",
            "商品培训课件4",
            "fuler-fanqiehongsu-product-courseware-4-v1",
        ],
        "settled": ROOT
        / "production-library/templates/settled/fuler-fanqiehongsu-product-courseware-4-v1",
        "gold": ROOT
        / "production-library/validation/courseware/product-courseware-4-faithful-replica-v1",
        "voice_pack": ROOT / "production-library/voices/sufuda-courseware-pharmacist-v1",
        "voice_id": "voice.sufuda-courseware-pharmacist-v1",
        "name_zh": "商品培训课件4（视频+PPT，番茄红素壳）",
        # 换主题 merge 未接线；支持 --export-gold-pptx 从金样 content-model 重导
        "replicate": False,
        "export_pptx_script": "scripts/export-cw4-pptx.mjs",
    },
}


def resolve_template(name: str) -> tuple[str, dict[str, Any]]:
    key = name.strip()
    for tid, meta in TEMPLATES.items():
        if key == tid or key in meta["aliases"]:
            return tid, meta
    raise SystemExit(
        f"未知模板: {name!r}。可用: courseware3 / courseware4（及其中文别名）"
    )


def probe_json() -> dict[str, Any]:
    script = ROOT / "scripts" / "probe_production_env.py"
    r = subprocess.run(
        [sys.executable, str(script), "--json"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    if r.returncode not in (0, 2):
        return {"ok": False, "error": r.stderr or r.stdout}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "probe JSON parse failed", "raw": r.stdout}


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Business courseware green line (courseware3 PPTX first)")
    ap.add_argument("--template", required=True, help="courseware3 / courseware4 / 中文名")
    ap.add_argument(
        "--theme",
        type=Path,
        default=None,
        help="theme 包目录（含 theme.json）；课件3 必填；课件4 换主题未接线",
    )
    ap.add_argument(
        "--export-gold-pptx",
        action="store_true",
        help="从金样 content-model 重导 PPTX（课件3/4 均支持；不换主题）",
    )
    ap.add_argument("--out-slug", type=str, default=None)
    ap.add_argument("--out-parent", type=Path, default=None)
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--skip-pptx", action="store_true")
    ap.add_argument(
        "--copy-to-business-delivery",
        action="store_true",
        help="复制 PPTX/gap 到 outputs/业务使用资料包/.../05_交付物放这里/",
    )
    args = ap.parse_args()

    tid, meta = resolve_template(args.template)

    env = probe_json()
    caps = (env.get("capabilities") or {}) if isinstance(env, dict) else {}

    status: dict[str, Any] = {
        "template_id": tid,
        "name_zh": meta["name_zh"],
        "voice_id": meta["voice_id"],
        "style_from_theme": bool(args.theme),
        "env": {
            "pptx_export": caps.get("pptx_export"),
            "video_tts": caps.get("video_tts"),
            "video_full": caps.get("video_full"),
        },
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # 金样重导（不换主题）
    if args.export_gold_pptx:
        if not caps.get("pptx_export"):
            status["ok"] = False
            status["error"] = "本机无法导出 PPTX（缺 node 或 artifact-tool）"
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return 2
        gold: Path = meta["gold"]
        script_rel = meta.get("export_pptx_script")
        if tid == "courseware3":
            script = gold / "scripts" / "export-sufuda-pptx.mjs"
            out_name = f"{gold.name}_金样_可编辑课件_v2.pptx"
        else:
            script = gold / (script_rel or "scripts/export-cw4-pptx.mjs")
            out_name = f"{gold.name}_金样_可编辑课件_v2.pptx"
        out = gold / "out" / out_name
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["node", str(script), "--out", str(out)]
        print("Running:", " ".join(cmd), flush=True)
        r = subprocess.run(cmd, cwd=str(gold))
        status.update(
            {
                "ok": r.returncode == 0 and out.is_file(),
                "mode": "export-gold-pptx",
                "pptx": str(out) if out.is_file() else None,
                "voice_id": meta["voice_id"],
                "note_zh": "仅重导金样 PPTX，未换主题。换主题请用 courseware3 --theme。",
            }
        )
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0 if status["ok"] else 2

    if not args.theme:
        raise SystemExit("换主题出片需要 --theme <含 theme.json 的目录>；仅重导金样用 --export-gold-pptx")

    theme_dir = args.theme.resolve()
    if not (theme_dir / "theme.json").is_file():
        raise SystemExit(f"theme 目录缺少 theme.json: {theme_dir}")

    if not meta.get("replicate"):
        status["ok"] = False
        status["error"] = (
            f"{meta['name_zh']} 换主题 CLI 尚未接线（P2-1）。"
            f"金样 PPTX 见 settled：{meta['settled']}；"
            "可先：python3 scripts/generate_business_courseware.py --template courseware4 --export-gold-pptx"
        )
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 2

    if not args.skip_pptx and not caps.get("pptx_export"):
        status["ok"] = False
        status["error"] = "本机无法导出 PPTX（缺 node 或 artifact-tool）。" + (
            " " + "; ".join((env.get("messages_zh") or [])[:3]) if isinstance(env, dict) else ""
        )
        status["honest_degrade"] = (env.get("honest_degrade") or {}).get("no_artifact_tool")
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 2

    skip_tts = args.skip_tts
    if not skip_tts and not caps.get("video_tts"):
        skip_tts = True
        status["tts_skipped_reason"] = (
            "本机无 Qwen3-TTS 环境：已自动 --skip-tts。"
            "PPTX 仍会导出；正式旁白/MP4 待配音环境，禁止系统 TTS 冒充。"
        )

    out_parent = args.out_parent or (
        ROOT / "production-library/validation/courseware"
    )
    slug = args.out_slug
    if not slug:
        theme = json.loads((theme_dir / "theme.json").read_text(encoding="utf-8"))
        slug = theme.get("slug") or theme.get("theme_id") or theme_dir.name
        # avoid clobber: append stamp if exists
        if (out_parent / slug).exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            slug = f"{slug}-{stamp}"

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "replicate_courseware_theme.py"),
        "--theme",
        str(theme_dir),
        "--gold",
        str(meta["gold"]),
        "--out-parent",
        str(out_parent),
        "--out-slug",
        slug,
        "--voice-pack",
        str(meta["voice_pack"]),
    ]
    if skip_tts:
        cmd.append("--skip-tts")
    if args.skip_pptx:
        cmd.append("--skip-pptx")

    print("Running:", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(ROOT))
    dest = (out_parent / slug).resolve()
    gap_path = dest / "gap-report.json"
    gap: dict[str, Any] = {}
    if gap_path.is_file():
        gap = json.loads(gap_path.read_text(encoding="utf-8"))

    status.update(
        {
            "ok": r.returncode == 0,
            "exit_code": r.returncode,
            "output_dir": str(dest),
            "pptx": gap.get("pptx"),
            "gaps": gap.get("gaps"),
            "gap_count": gap.get("gap_count"),
            "voice_id": meta["voice_id"],
            "delivery_note_zh": [
                f"课型：{meta['name_zh']}",
                f"输出目录：{dest}",
                f"PPTX：{gap.get('pptx') or '（未生成）'}",
                f"voice_id：{meta['voice_id']}（正式旁白禁止系统音色）",
                "包装/Logo 缺口见 gap-report；无授权不仿包装。",
            ],
        }
    )
    if status.get("tts_skipped_reason"):
        status["delivery_note_zh"].append(status["tts_skipped_reason"])

    write_json(dest / "business-delivery-status.json", status)

    if args.copy_to_business_delivery and gap.get("pptx"):
        biz = (
            ROOT
            / "outputs/业务使用资料包/药店培训内容工厂-业务包/05_交付物放这里"
            / slug
        )
        biz.mkdir(parents=True, exist_ok=True)
        import shutil

        src_pptx = Path(gap["pptx"])
        if src_pptx.is_file():
            shutil.copy2(src_pptx, biz / src_pptx.name)
        if gap_path.is_file():
            shutil.copy2(gap_path, biz / "gap-report.json")
        write_json(biz / "business-delivery-status.json", status)
        status["business_delivery_dir"] = str(biz)

    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if r.returncode == 0 else r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
