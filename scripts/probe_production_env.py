#!/usr/bin/env python3
"""探测本机出片环境：node / ffmpeg / Qwen3-TTS / voice pack。

用法：
  python3 scripts/probe_production_env.py
  python3 scripts/probe_production_env.py --json
  python3 scripts/probe_production_env.py --require pptx
  python3 scripts/probe_production_env.py --require video-full

退出码：
  0 = 所需能力齐全
  2 = 缺必需项（配合 --require）
  1 = 脚本错误
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER_REL = Path("distribution") / "private-production.json"
PRIVATE_MARKER_KIND = "chain-pharmacy-private-production"
PRIVATE_REPO_URL = (
    "https://github.com/lmr1123/chain-pharmacy-content-studio-private.git"
)
OFFICIAL_PRIVATE_ORIGINS = {
    PRIVATE_REPO_URL,
    PRIVATE_REPO_URL.removesuffix(".git"),
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private.git",
    "git@github.com:lmr1123/chain-pharmacy-content-studio-private",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private.git",
    "ssh://git@github.com/lmr1123/chain-pharmacy-content-studio-private",
}
PRIVATE_ASSET_PATHS = (
    Path("production-library/catalog.json"),
    Path("production-library/templates/settled/business-catalog.json"),
    Path("production-library/voices/reference-pharmacist-qwen-v1/voice-pack.json"),
    Path("poc/gold-sample/scripts/render-product-segment.mjs"),
    Path("poc/gold-sample/scripts/render-health-segment.mjs"),
)

# Prefer Homebrew ffmpeg over broken stubs
FFMPEG_CANDIDATES = [
    Path("/opt/homebrew/bin/ffmpeg"),
    Path("/usr/local/bin/ffmpeg"),
]
FFPROBE_CANDIDATES = [
    Path("/opt/homebrew/bin/ffprobe"),
    Path("/usr/local/bin/ffprobe"),
]


def which(name: str) -> str | None:
    return shutil.which(name)


def git_origin_url(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=8.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def private_production_status(root: Path) -> dict[str, Any]:
    marker_path = root / PRIVATE_MARKER_REL
    if not marker_path.is_file():
        return {
            "ready": False,
            "marker": False,
            "origin": None,
            "missing_paths": [],
            "reason": "missing_marker",
        }
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        marker = None
    expected_marker = {
        "kind": PRIVATE_MARKER_KIND,
        "version": 1,
        "repository_url": PRIVATE_REPO_URL,
        "production_assets": True,
    }
    if marker != expected_marker:
        return {
            "ready": False,
            "marker": False,
            "origin": None,
            "missing_paths": [],
            "reason": "invalid_marker",
        }
    origin = git_origin_url(root)
    if origin not in OFFICIAL_PRIVATE_ORIGINS:
        return {
            "ready": False,
            "marker": True,
            "origin": origin,
            "missing_paths": [],
            "reason": "wrong_origin",
        }
    missing_paths = [str(path) for path in PRIVATE_ASSET_PATHS if not (root / path).exists()]
    return {
        "ready": not missing_paths,
        "marker": True,
        "origin": origin,
        "missing_paths": missing_paths,
        "reason": "missing_assets" if missing_paths else None,
    }


def find_ffmpeg() -> str | None:
    for p in FFMPEG_CANDIDATES:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return which("ffmpeg")


def find_ffprobe() -> str | None:
    for p in FFPROBE_CANDIDATES:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return which("ffprobe")


def voice_pack_ready(pack_dir: Path) -> bool:
    manifest = pack_dir / "voice-pack.json"
    if not manifest.is_file():
        return False
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    prompt = payload.get("prompt") or {}
    audio = prompt.get("audio")
    return bool(
        payload.get("id")
        and isinstance(audio, str)
        and (pack_dir / audio).is_file()
        and str(prompt.get("ref_text") or "").strip()
    )


def run_ok(cmd: list[str], timeout: float = 8.0) -> bool:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def command_version(
    executable: str | None,
    *args: str,
    timeout: float = 8.0,
) -> str | None:
    """Return a concise version line without turning a probe into an exception."""
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    output = (result.stdout or result.stderr).strip()
    return output.splitlines()[0].strip() if output else None


def probe() -> dict[str, Any]:
    node = which("node")
    npm = which("npm")
    git = which("git")
    python = sys.executable
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()

    venv_tts = ROOT / ".venv-qwen-tts" / "bin" / "python"
    tts_python = str(venv_tts) if venv_tts.is_file() else None

    voice_ref = ROOT / "production-library/voices/reference-pharmacist-qwen-v1"
    voice_sufuda = ROOT / "production-library/voices/sufuda-courseware-pharmacist-v1"

    qwen_ok = False
    mlx_ok = False
    mlx_audio_tts_ok = False
    if tts_python:
        # 生产克隆旁白实际入口：mlx_audio.tts（见 generate_business_video.py）
        mlx_audio_tts_ok = run_ok(
            [
                tts_python,
                "-c",
                "from mlx_audio.tts.utils import load_model; print('ok')",
            ],
            timeout=25.0,
        )
        qwen_ok = run_ok(
            [tts_python, "-c", "import qwen_tts; print('ok')"],
            timeout=20.0,
        )
        mlx_ok = run_ok(
            [tts_python, "-c", "import mlx; print('ok')"],
            timeout=15.0,
        )
    # The production worker imports mlx_audio.tts directly. qwen_tts alone is
    # diagnostic information, not a usable business-video capability.
    tts_import_ok = mlx_audio_tts_ok

    artifact_tool = (
        ROOT
        / "poc/courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"
    )
    reference_voice_ready = voice_pack_ready(voice_ref)
    sufuda_voice_ready = voice_pack_ready(voice_sufuda)
    video_runtime_files = (
        ROOT / "poc/gold-sample/scripts/render-product-segment.mjs",
        ROOT / "poc/gold-sample/scripts/render-health-segment.mjs",
        ROOT / "poc/gold-sample/node_modules",
    )
    video_runtime_ready = all(path.exists() for path in video_runtime_files)
    render_ready = bool(node) and bool(ffmpeg) and bool(ffprobe) and video_runtime_ready
    tts_ready = bool(tts_python) and tts_import_ok and reference_voice_ready
    private_status = private_production_status(ROOT)
    private_assets_ready = bool(private_status["ready"])

    caps = {
        "private_production_assets": private_assets_ready,
        "pptx_export": private_assets_ready and bool(node) and artifact_tool.is_file(),
        "courseware_theme_replicate": private_assets_ready
        and bool(node)
        and artifact_tool.is_file(),
        "video_plan": private_assets_ready,
        "video_tts": private_assets_ready and tts_ready,
        "video_render": private_assets_ready and render_ready,
        "video_full": private_assets_ready and tts_ready and render_ready,
    }

    report: dict[str, Any] = {
        "ok": True,
        "root": str(ROOT),
        "tools": {
            "python": python,
            "git": git,
            "node": node,
            "npm": npm,
            "ffmpeg": ffmpeg,
            "ffprobe": ffprobe,
            "tts_python": tts_python,
        },
        "versions": {
            "python": command_version(python, "--version"),
            "git": command_version(git, "--version"),
            "node": command_version(node, "--version"),
            "npm": command_version(npm, "--version"),
            "ffmpeg": command_version(ffmpeg, "-version"),
            "ffprobe": command_version(ffprobe, "-version"),
            "tts_python": command_version(tts_python, "--version"),
        },
        "imports": {
            "mlx_audio_tts": mlx_audio_tts_ok,
            "qwen_tts": qwen_ok,
            "mlx": mlx_ok,
        },
        "private_production": private_status,
        "paths": {
            "artifact_tool": str(artifact_tool) if artifact_tool.is_file() else None,
            "voice_reference_pharmacist": str(voice_ref) if reference_voice_ready else None,
            "voice_sufuda_courseware": str(voice_sufuda) if sufuda_voice_ready else None,
            "video_runtime": str(ROOT / "poc/gold-sample") if video_runtime_ready else None,
        },
        "capabilities": caps,
        "honest_degrade": {
            "no_private_assets": "当前目录不是已验证的 Private 生产仓；所有生产能力均关闭。",
            "no_tts": "可出 PPTX / 规划包；禁止系统机器人音色冒充正式旁白；不得假装已出正式 MP4。",
            "no_ffmpeg_or_node": "可整理 content-model 与 gap；视频渲染需补 ffmpeg/node。",
            "no_artifact_tool": "PPTX 原生导出不可用；检查 poc/courseware-export/work 依赖。",
        },
        "messages_zh": [],
    }

    if private_status["reason"] == "missing_marker":
        report["messages_zh"].append(
            "缺少 Private 生产标记：当前目录按 Public 空壳处理，所有生产能力关闭。"
        )
    elif private_status["reason"] == "invalid_marker":
        report["messages_zh"].append(
            "Private 生产标记无效：所有生产能力关闭。"
        )
    elif private_status["reason"] == "wrong_origin":
        report["messages_zh"].append(
            "Private 生产仓 origin 不匹配官方地址：所有生产能力关闭。"
        )
    elif private_status["reason"] == "missing_assets":
        report["messages_zh"].append(
            "Private 生产资产不完整："
            + ", ".join(private_status["missing_paths"])
            + "；所有生产能力关闭。"
        )

    if not node:
        report["messages_zh"].append("缺少 node：PPTX 导出与视频渲染不可用。")
    if not ffmpeg:
        report["messages_zh"].append("缺少 ffmpeg：视频合成不可用（建议 Homebrew /opt/homebrew/bin/ffmpeg）。")
    if not ffprobe:
        report["messages_zh"].append("缺少 ffprobe：正式视频媒体质检不可用。")
    if not tts_python:
        report["messages_zh"].append("缺少 .venv-qwen-tts：克隆旁白不可用。")
    elif not tts_import_ok:
        report["messages_zh"].append(
            ".venv-qwen-tts 存在但无法 import mlx_audio.tts：生产克隆旁白不可用。"
        )
    if not reference_voice_ready:
        report["messages_zh"].append("参考药师 voice pack 缺 manifest、prompt.wav 或 ref_text。")
    if not video_runtime_ready:
        report["messages_zh"].append("视频分段渲染脚本或 node_modules 不完整。")
    if not artifact_tool.is_file():
        report["messages_zh"].append("缺少 artifact-tool：课件 PPTX 导出会失败。")

    if not report["messages_zh"]:
        report["messages_zh"].append("环境探测通过：PPTX + 视频 full 所需工具齐全。")

    return report


REQUIRE_MAP = {
    "production-assets": ["private_production_assets"],
    "pptx": ["pptx_export"],
    "courseware": ["courseware_theme_replicate"],
    "video-plan": ["video_plan"],
    "video-tts": ["video_tts"],
    "video-full": ["video_full"],
}


def apply_requirements(
    report: dict[str, Any], requirements: list[str]
) -> dict[str, Any]:
    """Apply requested task capabilities to the report's authoritative status."""
    missing: list[str] = []
    for requirement in requirements:
        for capability in REQUIRE_MAP[requirement]:
            if not report["capabilities"].get(capability) and capability not in missing:
                missing.append(capability)
    report["require"] = list(requirements)
    report["missing_capabilities"] = missing
    report["ok"] = not missing
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe production environment for business delivery")
    ap.add_argument("--json", action="store_true", help="Print full JSON report")
    ap.add_argument(
        "--require",
        action="append",
        default=[],
        choices=sorted(REQUIRE_MAP.keys()),
        help="Require capability (repeatable). Exit 2 if missing.",
    )
    args = ap.parse_args()
    report = apply_requirements(probe(), args.require)
    missing = report["missing_capabilities"]

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("=== 生产环境探测 ===")
        t = report["tools"]
        print(f"python:      {t['python']}")
        print(f"node:        {t['node'] or 'MISSING'}")
        print(f"ffmpeg:      {t['ffmpeg'] or 'MISSING'}")
        print(f"ffprobe:     {t['ffprobe'] or 'MISSING'}")
        print(f"tts_python:  {t['tts_python'] or 'MISSING'}")
        print("--- versions ---")
        for key, value in report["versions"].items():
            print(f"  {key}: {value or 'UNKNOWN'}")
        print(f"mlx_audio:   {report['imports']['mlx_audio_tts']}")
        print(f"qwen_tts:    {report['imports']['qwen_tts']}")
        print(f"mlx:         {report['imports']['mlx']}")
        print("--- capabilities ---")
        for k, v in report["capabilities"].items():
            print(f"  {k}: {'OK' if v else 'NO'}")
        print("---")
        for msg in report["messages_zh"]:
            print(f"· {msg}")
        if missing:
            print("缺少能力:", ", ".join(missing))
            degrade_key = (
                "no_private_assets"
                if "private_production_assets" in missing
                else "no_tts"
            )
            print(report["honest_degrade"][degrade_key])

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
