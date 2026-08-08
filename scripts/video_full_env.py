#!/usr/bin/env python3
"""商品正式 MP4 环境：探测 / soft-repair / 打包 kit / 从离线包恢复。

业务目标：干净机装好 Private 后，一条命令看清缺什么；开发机可打离线 kit 包给授权机恢复。

  python3 scripts/video_full_env.py check
  python3 scripts/video_full_env.py soft-repair
  python3 scripts/video_full_env.py package --out /tmp/video-runtime-kit.tgz
  python3 scripts/video_full_env.py restore --from /tmp/video-runtime-kit.tgz

不安装付费服务、不默认 brew/pip 联网安装；只做本地 soft-repair 与离线包操作。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import probe_production_env as probe  # noqa: E402
import video_runtime as vr  # noqa: E402

ENGINE = ROOT / "production-library" / "engines" / "video-revideo-runtime-v1"
KIT_DIR = ENGINE / "kit"
VOICE_REF = ROOT / "production-library" / "voices" / "reference-pharmacist-qwen-v1"
TTS_VENV = ROOT / ".venv-qwen-tts"
PACKAGE_META_NAME = "video-runtime-kit.meta.json"

# Keep package smaller: exclude build outputs and media dumps.
EXCLUDE_NAMES = {
    ".git",
    ".DS_Store",
    "dist",
    ".render-work",
    "__pycache__",
    ".turbo",
    ".cache",
}
EXCLUDE_SUFFIXES = (".mp4", ".mov", ".wav", ".map")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tts_status() -> dict[str, Any]:
    py = TTS_VENV / "bin" / "python"
    if not py.is_file():
        return {
            "ok": False,
            "python": None,
            "error": f"缺少 {TTS_VENV.as_posix()}（不随 Git 分发）",
        }
    try:
        proc = subprocess.run(
            [
                str(py),
                "-c",
                "from mlx_audio.tts.utils import load_model; print('ok')",
            ],
            capture_output=True,
            text=True,
            timeout=45,
            cwd=str(ROOT),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "python": str(py), "error": str(exc)}
    ok = proc.returncode == 0 and "ok" in (proc.stdout or "")
    return {
        "ok": ok,
        "python": str(py),
        "error": None if ok else (proc.stderr or proc.stdout or f"exit {proc.returncode}")[
            -500:
        ],
    }


def voice_status() -> dict[str, Any]:
    ok = (
        (VOICE_REF / "voice-pack.json").is_file()
        and (VOICE_REF / "prompt.wav").is_file()
        and (VOICE_REF / "ref_text.txt").is_file()
    )
    return {
        "ok": ok,
        "path": str(VOICE_REF),
        "error": None if ok else "voice pack 缺 voice-pack.json / prompt.wav / ref_text.txt",
    }


def tool_status() -> dict[str, Any]:
    report = probe.probe()
    tools = report.get("tools") or {}
    return {
        "node": tools.get("node"),
        "ffmpeg": tools.get("ffmpeg"),
        "ffprobe": tools.get("ffprobe"),
        "ok": bool(tools.get("node") and tools.get("ffmpeg") and tools.get("ffprobe")),
    }


def kit_status() -> dict[str, Any]:
    formal = KIT_DIR
    resolved = vr.resolve_video_kit_root_or_none(require_node_modules=True)
    resolved_no_nm = vr.resolve_video_kit_root_or_none(require_node_modules=False)
    return {
        "formal_path": str(formal),
        "formal_is_symlink": formal.is_symlink(),
        "formal_exists": formal.exists(),
        "resolved": str(resolved) if resolved else None,
        "resolved_without_node_modules": str(resolved_no_nm) if resolved_no_nm else None,
        "ready": resolved is not None,
        "markers_ok_without_node_modules": resolved_no_nm is not None,
    }


def build_check_report() -> dict[str, Any]:
    tools = tool_status()
    kit = kit_status()
    tts = tts_status()
    voice = voice_status()
    caps = probe.probe().get("capabilities") or {}
    missing: list[str] = []
    if not tools["ok"]:
        missing.append("node_or_ffmpeg")
    if not kit["ready"]:
        missing.append("video_runtime_kit")
    if not tts["ok"]:
        missing.append("tts_venv")
    if not voice["ok"]:
        missing.append("voice_pack")
    if not caps.get("video_full"):
        missing.append("video_full_capability")

    hints: list[str] = []
    if "node_or_ffmpeg" in missing:
        hints.append("安装 Node 18+ 与 ffmpeg/ffprobe（Homebrew: brew install node ffmpeg）")
    if "video_runtime_kit" in missing:
        hints.extend(
            [
                "恢复视频 kit：python3 scripts/video_full_env.py soft-repair",
                "或从离线包：python3 scripts/video_full_env.py restore --from <kit.tgz>",
                "开发机打包：python3 scripts/video_full_env.py package --out <kit.tgz>",
            ]
        )
    if "tts_venv" in missing:
        hints.extend(
            [
                "本机准备 .venv-qwen-tts，并验证：",
                "  .venv-qwen-tts/bin/python -c \"from mlx_audio.tts.utils import load_model; print('OK')\"",
                "详见 docs/workbuddy-video-first-check.md；禁止系统 TTS 冒充正式旁白",
            ]
        )
    if "voice_pack" in missing:
        hints.append(
            "确认 Private 含 production-library/voices/reference-pharmacist-qwen-v1/"
        )

    return {
        "ok": not missing and bool(caps.get("video_full")),
        "checked_at": utc_now(),
        "capabilities": {
            "video_tts": caps.get("video_tts"),
            "video_render": caps.get("video_render"),
            "video_full": caps.get("video_full"),
        },
        "tools": tools,
        "kit": kit,
        "tts": tts,
        "voice": voice,
        "missing": missing,
        "install_hints_zh": hints,
        "business_route": "product-mp4-full-v1",
        "next_step_zh": (
            "环境就绪：可用 business_job 走 product-mp4-full-v1"
            if not missing
            else "先按 install_hints_zh 补齐，再 doctor --profile video-full"
        ),
    }


def cmd_check(args: argparse.Namespace) -> int:
    report = build_check_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("商品正式视频环境检查")
        print(f"  video_full: {report['capabilities'].get('video_full')}")
        print(f"  video_tts:  {report['capabilities'].get('video_tts')}")
        print(f"  video_render: {report['capabilities'].get('video_render')}")
        print(f"  kit: {report['kit'].get('resolved') or '缺失'}")
        print(f"  tts: {'OK' if report['tts'].get('ok') else report['tts'].get('error')}")
        print(f"  voice: {'OK' if report['voice'].get('ok') else report['voice'].get('error')}")
        if report["missing"]:
            print("缺少：", ", ".join(report["missing"]))
            print("提示：")
            for h in report["install_hints_zh"]:
                print(f"  - {h}")
        else:
            print("通过：可走 product-mp4-full-v1 正式任务")
        print("下一步：", report["next_step_zh"])
    return 0 if report["ok"] else 2


def cmd_soft_repair(args: argparse.Namespace) -> int:
    actions = vr.soft_repair_kit_symlink(ROOT)
    # Also try linking formal kit node_modules from legacy if kit dir exists but nm missing
    kit = KIT_DIR
    if kit.exists() and not (kit / "node_modules").exists():
        legacy_nm = ROOT / "poc" / "gold-sample" / "node_modules"
        if legacy_nm.is_dir():
            try:
                rel = Path(os.path.relpath(legacy_nm, start=kit))
                (kit / "node_modules").symlink_to(rel, target_is_directory=True)
                actions.append(f"已链接 kit/node_modules → {rel.as_posix()}")
            except OSError as exc:
                actions.append(f"kit node_modules 链接失败: {exc}")
    report = build_check_report()
    payload = {"actions": actions, "check": report}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if actions:
            for a in actions:
                print(a)
        else:
            print("soft-repair：无需改动或无法本地修复")
        print("check ok:", report["ok"], "missing:", report["missing"])
    return 0 if report["ok"] else 2


def _should_exclude(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = set(rel.parts)
    if parts & EXCLUDE_NAMES:
        return True
    if any(path.name.endswith(sfx) for sfx in EXCLUDE_SUFFIXES):
        return True
    # optional: skip huge nested node caches
    if "node_modules" in rel.parts and path.name in {".cache", "cache"}:
        return True
    return False


def package_kit(
    *,
    source: Path,
    out_path: Path,
    include_node_modules: bool,
) -> dict[str, Any]:
    if not vr.kit_ready(source, require_node_modules=include_node_modules):
        # allow packaging without nm if markers otherwise ok
        if not vr.kit_ready(source, require_node_modules=False):
            raise SystemExit(f"源 kit 不完整: {source}")
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    file_count = 0
    total_bytes = 0
    with tarfile.open(out_path, "w:gz") as tar:
        for path in sorted(source.rglob("*")):
            if not path.is_file() and not path.is_symlink():
                continue
            if path.is_dir():
                continue
            rel = path.relative_to(source)
            if not include_node_modules and rel.parts and rel.parts[0] == "node_modules":
                continue
            if _should_exclude(path, source):
                continue
            # skip broken symlinks
            if path.is_symlink() and not path.exists():
                continue
            tar.add(path, arcname=str(Path("kit") / rel), recursive=False)
            file_count += 1
            try:
                total_bytes += path.stat().st_size
            except OSError:
                pass

        meta = {
            "schema": "video-runtime-kit-package-v1",
            "created_at": utc_now(),
            "source": str(source.resolve()),
            "include_node_modules": include_node_modules,
            "file_count": file_count,
            "approx_bytes": total_bytes,
            "engine_id": "video-revideo-runtime-v1",
            "required_kit_markers": vr.load_manifest().get("required_kit_markers"),
        }
        meta_bytes = (json.dumps(meta, ensure_ascii=False, indent=2) + "\n").encode(
            "utf-8"
        )
        info = tarfile.TarInfo(name=PACKAGE_META_NAME)
        info.size = len(meta_bytes)
        tar.addfile(info, fileobj=__import__("io").BytesIO(meta_bytes))

    return {
        "ok": True,
        "out": str(out_path),
        "sha256": sha256_file(out_path),
        "size": out_path.stat().st_size,
        "file_count": file_count,
        "include_node_modules": include_node_modules,
        "source": str(source.resolve()),
    }


def cmd_package(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve() if args.source else None
    if source is None:
        source = vr.resolve_video_kit_root(require_node_modules=not args.without_node_modules)
    out = Path(args.out).expanduser()
    result = package_kit(
        source=source,
        out_path=out,
        include_node_modules=not args.without_node_modules,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"已打包: {result['out']}")
        print(f"size: {result['size']}  sha256: {result['sha256']}")
        print(f"files: {result['file_count']}  node_modules: {result['include_node_modules']}")
    return 0


def restore_kit_from_archive(archive: Path, *, force: bool = False) -> dict[str, Any]:
    archive = archive.expanduser().resolve()
    if not archive.is_file():
        raise SystemExit(f"离线包不存在: {archive}")

    ENGINE.mkdir(parents=True, exist_ok=True)
    target = KIT_DIR

    if target.exists() or target.is_symlink():
        if not force:
            raise SystemExit(
                f"目标已存在: {target}；确认覆盖请加 --force（会替换 symlink/目录）"
            )
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)

    with tempfile.TemporaryDirectory(prefix="video-kit-restore-") as tmp:
        tmp_path = Path(tmp)
        with tarfile.open(archive, "r:gz") as tar:
            # Python 3.12+ filter; fall back for older
            try:
                tar.extractall(tmp_path, filter="data")  # type: ignore[call-arg]
            except TypeError:
                tar.extractall(tmp_path)
        kit_src = tmp_path / "kit"
        if not kit_src.is_dir():
            # allow archive root = kit contents
            if (tmp_path / "package.json").is_file():
                kit_src = tmp_path
            else:
                raise SystemExit("离线包内找不到 kit/ 目录")
        shutil.copytree(kit_src, target, symlinks=True)

    ready = vr.kit_ready(target, require_node_modules=False)
    ready_full = vr.kit_ready(target, require_node_modules=True)
    return {
        "ok": ready,
        "path": str(target.resolve()),
        "markers_ok": ready,
        "with_node_modules": ready_full,
        "note_zh": (
            "kit 已恢复"
            if ready_full
            else "kit 主体已恢复；若缺 node_modules，请在授权环境 npm install 或使用含 node_modules 的包"
        ),
    }


def restore_kit_from_dir(source: Path, *, force: bool = False) -> dict[str, Any]:
    source = source.expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"源目录不存在: {source}")
    if not vr.kit_ready(source, require_node_modules=False):
        raise SystemExit(f"源目录不是完整 kit: {source}")

    ENGINE.mkdir(parents=True, exist_ok=True)
    target = KIT_DIR
    if target.exists() or target.is_symlink():
        if not force:
            raise SystemExit(f"目标已存在: {target}；加 --force 覆盖")
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)

    # Prefer symlink when same filesystem and user wants lightweight (default copy for portability)
    shutil.copytree(source, target, symlinks=True)
    return {
        "ok": vr.kit_ready(target, require_node_modules=False),
        "path": str(target.resolve()),
        "with_node_modules": vr.kit_ready(target, require_node_modules=True),
    }


def cmd_restore(args: argparse.Namespace) -> int:
    src = Path(args.from_path)
    if src.is_file() and (
        str(src).endswith(".tgz")
        or str(src).endswith(".tar.gz")
        or tarfile.is_tarfile(src)
    ):
        result = restore_kit_from_archive(src, force=args.force)
    elif src.is_dir():
        result = restore_kit_from_dir(src, force=args.force)
    else:
        raise SystemExit(f"--from 必须是 .tgz 包或 kit 目录: {src}")

    check = build_check_report()
    payload = {"restore": result, "check": check}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("video_full:", check["capabilities"].get("video_full"))
        if check["missing"]:
            print("仍缺:", ", ".join(check["missing"]))
    return 0 if result.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="商品正式视频环境：check / package / restore")
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="诚实探测 video_full 依赖")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("soft-repair", help="本地 soft-repair kit 链接（无网络）")
    p.set_defaults(func=cmd_soft_repair)

    p = sub.add_parser("package", help="从当前可用 kit 打离线包")
    p.add_argument("--out", required=True, help="输出 .tgz 路径")
    p.add_argument(
        "--source",
        default=None,
        help="kit 源目录（默认 resolve 当前 formal/legacy kit）",
    )
    p.add_argument(
        "--without-node-modules",
        action="store_true",
        help="不打包 node_modules（体积小，目标机需自备依赖）",
    )
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("restore", help="从 .tgz 或目录恢复 formal kit")
    p.add_argument("--from", dest="from_path", required=True, help="离线包或 kit 目录")
    p.add_argument("--force", action="store_true", help="覆盖已有 kit")
    p.set_defaults(func=cmd_restore)

    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
