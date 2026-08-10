#!/usr/bin/env python3
"""业务视频绿线：内容 → 交付包 → 换文案/屏显/包装 → 克隆旁白 → 分段重渲 MP4。

用法示例：

  # 仅规划包（无 TTS）
  python3 scripts/generate_business_video.py \\
    --template product --sections-json path/to/sections.json

  # 商品培训视频全量（文案+画面槽位+包装图+旁白+分段重渲）
  .venv-qwen-tts/bin/python scripts/generate_business_video.py \\
    --template product --sections-json path/to/sections.json \\
    --mode full --with-tts --with-mp4 \\
    --product-image path/to/pack.png \\
    --product-approval path/to/product-approval.json

  # 疾病科普视频全量（经审批的主题包 · 7 段重渲）
  .venv-qwen-tts/bin/python scripts/generate_business_video.py \\
    --template health --theme-package path/to/approved-theme-package \\
    --mode full --with-tts --with-mp4

  # 旧：仅叠旁白到金样壳（不推荐，仅兼容）
  ... --mode audio-shell --with-tts --with-mp4

sections.json：
  {
    "theme": "商品名",
    "sections": [
      {"title": "开场", "narration": "审核旁白……"},
      {"title": "核心功效", "narration": "……"}
    ]
  }
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
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
from content_driven_rules import segment_has_content  # noqa: E402

BUSINESS_DELIVERY_FIXED_FILES = (
    "DELIVERY.md",
    "delivery-qa.json",
    "storyboard.html",
    "content.json",
    "gap-report.json",
)
DELIVERY_QA_SCHEMA = "business-video-delivery-qa-v1"


def _gate_rejection(label: str, gate: Any) -> str | None:
    """Return a reason only when a declared approval/QA gate rejects delivery."""
    if gate is None:
        return None
    if isinstance(gate, bool):
        return None if gate else f"{label} 未通过"
    if isinstance(gate, str):
        value = gate.strip().lower()
        if value in {
            "approved",
            "passed",
            "pass",
            "allowed",
            "ok",
            "qa_passed",
            "通过",
            "已批准",
        }:
            return None
        if value in {
            "rejected",
            "failed",
            "fail",
            "blocked",
            "pending",
            "拒绝",
            "未通过",
            "待审批",
        }:
            return f"{label} 状态不允许发布: {gate}"
        return f"{label} 状态无法识别: {gate}"
    if not isinstance(gate, dict):
        return f"{label} 格式无效"
    if not gate:
        return f"{label} 为空"

    for key in ("ok", "approved", "passed", "allowed"):
        if key in gate and gate[key] is not True:
            return f"{label}.{key} != true"
    state = gate.get("status") or gate.get("state")
    if state is not None:
        rejection = _gate_rejection(label, state)
        if rejection:
            return rejection
    if "visuals_approved" in gate:
        if gate.get("visuals_approved") is not True:
            return f"{label}.visuals_approved != true"
        if not str(gate.get("approved_by") or "").strip():
            return f"{label}.approved_by 为空"
    return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _media_tool(name: str) -> str | None:
    for prefix in (Path("/opt/homebrew/bin"), Path("/usr/local/bin")):
        candidate = prefix / name
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def inspect_video_structure(path: Path) -> dict[str, Any]:
    """Verify that an MP4 has non-empty audio/video streams and a duration."""
    ffprobe = _media_tool("ffprobe")
    base = {
        "bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": _sha256_file(path) if path.is_file() else None,
    }
    if not ffprobe:
        return {**base, "ok": False, "error": "缺少 ffprobe，无法完成媒体质检"}
    try:
        probe = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if probe.returncode != 0:
            return {
                **base,
                "ok": False,
                "error": f"ffprobe 失败: {(probe.stderr or probe.stdout).strip()[-500:]}",
            }
        payload = json.loads(probe.stdout)
        streams = payload.get("streams") or []
        video_streams = sum(item.get("codec_type") == "video" for item in streams)
        audio_streams = sum(item.get("codec_type") == "audio" for item in streams)
        duration = float((payload.get("format") or {}).get("duration") or 0)
        audio_durations = []
        for item in streams:
            if item.get("codec_type") != "audio":
                continue
            try:
                audio_durations.append(float(item.get("duration") or 0))
            except (TypeError, ValueError):
                continue
        audio_duration = max(audio_durations, default=0) or duration
        ok = bool(
            base["bytes"]
            and duration > 0
            and video_streams >= 1
            and audio_streams >= 1
        )
        result = {
            **base,
            "ok": ok,
            "duration_s": round(duration, 3),
            "audio_duration_s": round(audio_duration, 3),
            "video_streams": video_streams,
            "audio_streams": audio_streams,
        }
        if not ok:
            result["error"] = "视频须包含视频轨、音频轨和有效时长"
        return result
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        return {**base, "ok": False, "error": f"媒体质检失败: {exc}"}


def inspect_final_video(path: Path) -> dict[str, Any]:
    """Verify that the final artifact also fully decodes."""
    structure = inspect_video_structure(path)
    if structure.get("ok") is not True:
        return {**structure, "decode_ok": False}
    ffmpeg = _media_tool("ffmpeg")
    if not ffmpeg:
        return {
            **structure,
            "ok": False,
            "decode_ok": False,
            "error": "缺少 ffmpeg，无法完成整片解码质检",
        }
    try:
        decode = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=900,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            **structure,
            "ok": False,
            "decode_ok": False,
            "error": f"整片解码质检失败: {exc}",
        }
    decode_ok = decode.returncode == 0
    return {
        **structure,
        "ok": decode_ok,
        "decode_ok": decode_ok,
        **(
            {}
            if decode_ok
            else {
                "error": (decode.stderr or "").strip()[-500:]
                or "最终成片无法完整解码"
            }
        ),
    }


def inspect_wav(path: Path) -> dict[str, Any]:
    """Verify that a narration WAV is readable and has audio frames."""
    base = {
        "bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": _sha256_file(path) if path.is_file() else None,
    }
    try:
        with wave.open(str(path), "rb") as handle:
            frames = handle.getnframes()
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
            duration = frames / sample_rate if sample_rate else 0
    except (OSError, EOFError, wave.Error) as exc:
        return {**base, "ok": False, "error": f"WAV 质检失败: {exc}"}
    ok = bool(base["bytes"] and frames > 0 and sample_rate > 0 and channels > 0)
    return {
        **base,
        "ok": ok,
        "duration_s": round(duration, 3),
        "sample_rate": sample_rate,
        "channels": channels,
        **({} if ok else {"error": "WAV 须包含可读取的有效音频帧"}),
    }


def _is_sha256(value: Any) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(value or "")))


def _status_evidence_sha256(status: dict[str, Any]) -> str:
    """Bind the mutable generation/approval state that justified QA."""
    payload = {
        "package_ok": status.get("package_ok"),
        "template": status.get("template"),
        "mode": status.get("mode"),
        "want_tts": status.get("want_tts"),
        "want_mp4": status.get("want_mp4"),
        "voice_id": status.get("voice_id"),
        "tts": status.get("tts"),
        "mp4": status.get("mp4"),
        "full": status.get("full"),
        "delivery_requirements": status.get("delivery_requirements"),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_business_artifact_manifest(
    out_dir: Path, status: dict[str, Any]
) -> list[dict[str, Any]]:
    """Bind every copied business artifact except the self-describing QA JSON."""
    candidates = [
        out_dir / name
        for name in BUSINESS_DELIVERY_FIXED_FILES
        if name != "delivery-qa.json"
    ]
    if status.get("want_tts"):
        candidates.extend(sorted((out_dir / "audio" / "sections").glob("*.wav")))
    if status.get("want_mp4"):
        mp4_value = (status.get("mp4") or {}).get("path")
        if mp4_value:
            candidates.append(Path(mp4_value))

    records: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for candidate in candidates:
        safe = _safe_delivery_source(out_dir, candidate)
        if safe is None:
            continue
        resolved, relative = safe
        if relative in seen:
            continue
        seen.add(relative)
        records.append(
            {
                "relative_path": relative.as_posix(),
                "bytes": resolved.stat().st_size,
                "sha256": _sha256_file(resolved),
            }
        )
    return sorted(records, key=lambda item: item["relative_path"])


def build_delivery_qa(out_dir: Path, status: dict[str, Any]) -> dict[str, Any]:
    """Build the fail-closed P0 release gate for a formal business video."""
    checks: list[dict[str, Any]] = []

    def check(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"id": check_id, "passed": bool(passed), "detail": detail})

    check("final_mode", status.get("mode") == "full", "正式交付只接受 full 模式")
    check(
        "requested_outputs",
        status.get("want_tts") is True and status.get("want_mp4") is True,
        "正式交付必须同时请求克隆旁白与完整 MP4",
    )
    package_files = ("content.json", "storyboard.html", "gap-report.json")
    package_ok = status.get("package_ok") is True and all(
        (out_dir / name).is_file()
        and not (out_dir / name).is_symlink()
        and (out_dir / name).stat().st_size > 0
        for name in package_files
    )
    check("package", package_ok, "内容、分镜和缺口报告均须存在且非空")

    full = status.get("full") or {}
    generation_ok = (
        (status.get("tts") or {}).get("ok") is True
        and (status.get("mp4") or {}).get("ok") is True
        and full.get("ok") is True
        and bool(str(status.get("voice_id") or "").strip())
    )
    check("generation_state", generation_ok, "TTS、MP4、full 和 voice_id 均须成功")

    expected_ids = {
        "product-video-faithful-v1": (
            "opening",
            "brand",
            "faithful",
            "efficacy",
            "features",
            "audience",
            "combination",
            "summary",
        ),
        "health-video-reference-tech-v1": (
            "intro",
            "character",
            "mechanism",
            "symptoms",
            "treatment",
            "medication",
            "summary",
        ),
    }.get(status.get("template"), ())
    expected_segments = len(expected_ids)
    segment_plan = full.get("segment_plan") or {}
    segment_status = full.get("segments") or {}
    included_ids = {
        key for key, item in segment_plan.items() if item.get("status") == "included"
    }
    completed_ids = {
        key for key, item in segment_status.items() if item.get("status") == "included"
    }
    wavs = [
        path
        for path in (out_dir / "audio" / "sections").glob("*.wav")
        if path.is_file() and not path.is_symlink() and path.stat().st_size > 0
    ]
    segment_mp4s = [
        path
        for path in (out_dir / "segments").glob("*.mp4")
        if path.is_file() and not path.is_symlink() and path.stat().st_size > 0
    ]
    wav_reports = {path.stem: inspect_wav(path) for path in wavs}
    segment_reports = {
        path.stem: inspect_video_structure(path) for path in segment_mp4s
    }
    content_section_ids: set[int] = set()
    try:
        content_payload = json.loads((out_dir / "content.json").read_text(encoding="utf-8"))
        content_section_ids = {
            index
            for index, section in enumerate(content_payload.get("sections") or [])
            if segment_has_content(section)
        }
    except (OSError, TypeError, json.JSONDecodeError):
        content_section_ids = set()

    mp4_value = (status.get("mp4") or {}).get("path")
    mp4_path = Path(mp4_value) if mp4_value else None
    safe_mp4 = _safe_delivery_source(out_dir, mp4_path) if mp4_path else None
    media = (
        inspect_final_video(safe_mp4[0])
        if safe_mp4 is not None
        else {"ok": False, "error": "最终 MP4 缺失、为符号链接或不在本次运行目录"}
    )
    segment_duration = sum(
        float(report.get("duration_s") or 0) for report in segment_reports.values()
    )
    final_duration = float(media.get("duration_s") or 0)
    duration_tolerance = max(1.0, segment_duration * 0.03)
    duration_matches = bool(segment_duration) and (
        abs(final_duration - segment_duration) <= duration_tolerance
    )
    audio_coverage_ok = all(
        float(segment_reports.get(segment_id, {}).get("audio_duration_s") or 0)
        + max(
            0.35,
            float(wav_reports.get(segment_id, {}).get("duration_s") or 0) * 0.03,
        )
        >= float(wav_reports.get(segment_id, {}).get("duration_s") or 0)
        for segment_id in expected_ids
    )
    expected_id_set = set(expected_ids)
    segment_ok = bool(expected_ids) and all(
        (
            included_ids == expected_id_set,
            completed_ids == expected_id_set,
            set(wav_reports) == expected_id_set,
            set(segment_reports) == expected_id_set,
            len(content_section_ids) == expected_segments,
            all(report.get("ok") is True for report in wav_reports.values()),
            all(report.get("ok") is True for report in segment_reports.values()),
            duration_matches,
            audio_coverage_ok,
        )
    )
    check(
        "segment_consistency",
        segment_ok,
        (
            f"正式成片须精确包含 {expected_segments or '规定'} 段审核内容、同 ID "
            "WAV/MP4，且每段媒体有效、整片时长与分段合计一致"
        ),
    )

    source_ok = not (full.get("content_gaps") or [])
    if status.get("template") == "product-video-faithful-v1":
        approval = full.get("approval") or {}
        source_ok = (
            source_ok
            and full.get("authorized_product_packshot") is True
            and approval.get("ok") is True
            and approval.get("approved") is True
            and bool(str(approval.get("approved_by") or "").strip())
            and bool(str(approval.get("approved_at") or "").strip())
            and bool(str(approval.get("authorization_reference") or "").strip())
            and _is_sha256(approval.get("approved_content_sha256"))
            and _is_sha256(approval.get("approved_product_image_sha256"))
        )
        source_detail = "商品正式成片须无内容缺口，且审核稿与授权包装审批绑定当前 SHA-256"
    elif status.get("template") == "health-video-reference-tech-v1":
        theme_package = full.get("theme_package") or {}
        approval = theme_package.get("approval") or {}
        approved_hash = approval.get("approved_payload_sha256")
        current_hash = theme_package.get("payload_sha256")
        source_ok = source_ok and all(
            (
                approval.get("visuals_approved") is True,
                bool(str(approval.get("approved_by") or "").strip()),
                bool(str(approval.get("approved_at") or "").strip()),
                _is_sha256(approved_hash),
                _is_sha256(current_hash),
                approved_hash == current_hash,
            )
        )
        source_detail = "健康正式成片须无内容缺口，且画面审批绑定当前主题包 SHA-256"
    else:
        source_ok = False
        source_detail = "模板不在正式视频发布白名单"
    check("source_gate", source_ok, source_detail)

    check("final_media_integrity", media.get("ok") is True, str(media.get("error") or "通过"))

    passed = all(item["passed"] for item in checks)
    artifact = None
    if safe_mp4 is not None:
        artifact = {
            "relative_path": safe_mp4[1].as_posix(),
            **{key: media.get(key) for key in (
                "bytes",
                "sha256",
                "duration_s",
                "video_streams",
                "audio_streams",
                "decode_ok",
            )},
        }
    return {
        "schema": DELIVERY_QA_SCHEMA,
        "state": "qa_passed" if passed else "qa_failed",
        "ok": passed,
        "checks": checks,
        "status_evidence_sha256": _status_evidence_sha256(status),
        "artifact": artifact,
        "business_artifacts": _build_business_artifact_manifest(out_dir, status),
        "segment_media": {
            "wavs": wav_reports,
            "mp4s": segment_reports,
            "segment_duration_s": round(segment_duration, 3),
            "final_duration_s": round(final_duration, 3),
            "duration_tolerance_s": round(duration_tolerance, 3),
            "audio_coverage_ok": audio_coverage_ok,
        },
        "limitations": [
            "不替代业务/药师对医学内容的人工复核",
            "不替代人工审美验收",
            "不验证包装图片法律授权声明的真实性",
            "P0 不含 ASR、黑场、静音和响度阈值检查",
        ],
    }


def _declared_delivery_gates(status: dict[str, Any]) -> list[tuple[str, Any]]:
    gates = [("approval", status.get("approval")), ("qa", status.get("qa"))]
    full = status.get("full")
    if isinstance(full, dict):
        gates.extend(
            [
                ("full.approval", full.get("approval")),
                ("full.qa", full.get("qa")),
                ("full.gate", full.get("gate")),
            ]
        )
        theme_package = full.get("theme_package")
        if isinstance(theme_package, dict):
            gates.append(
                ("full.theme_package.approval", theme_package.get("approval"))
            )
    return gates


def delivery_publish_readiness(
    status: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Check final run state before anything can enter the business delivery area."""
    reasons: list[str] = []
    if status.get("mode") != "full":
        reasons.append("formal delivery requires mode=full")
    if status.get("want_tts") is not True or status.get("want_mp4") is not True:
        reasons.append("formal delivery requires cloned TTS and MP4")
    if status.get("package_ok") is not True:
        reasons.append("package_ok != true")

    want_tts = bool(status.get("want_tts"))
    want_mp4 = bool(status.get("want_mp4"))
    if want_tts and (status.get("tts") or {}).get("ok") is not True:
        reasons.append("required tts.ok != true")
    if want_mp4 and (status.get("mp4") or {}).get("ok") is not True:
        reasons.append("required mp4.ok != true")
    if status.get("mode") == "full" and (want_tts or want_mp4):
        if (status.get("full") or {}).get("ok") is not True:
            reasons.append("required full.ok != true")

    requirements = status.get("delivery_requirements") or {}
    if requirements.get("visual_approval"):
        full = status.get("full") or {}
        theme_package = full.get("theme_package") or {}
        approval = theme_package.get("approval")
        if approval is None:
            reasons.append("required visual approval missing")

    qa = status.get("qa")
    if not isinstance(qa, dict):
        reasons.append("required delivery QA missing")
    else:
        if qa.get("schema") != DELIVERY_QA_SCHEMA:
            reasons.append("delivery QA schema mismatch")
        if qa.get("state") != "qa_passed" or qa.get("ok") is not True:
            reasons.append("delivery QA did not reach qa_passed")
        if qa.get("status_evidence_sha256") != _status_evidence_sha256(status):
            reasons.append("generation or approval status changed after QA")
        checks = qa.get("checks")
        if not isinstance(checks, list) or not checks or any(
            not isinstance(item, dict) or item.get("passed") is not True
            for item in checks
        ):
            reasons.append("delivery QA checks are incomplete or failed")
        artifact = qa.get("artifact") or {}
        mp4_path_value = (status.get("mp4") or {}).get("path")
        mp4_path = Path(mp4_path_value) if mp4_path_value else None
        if (
            not mp4_path
            or not mp4_path.is_file()
            or mp4_path.is_symlink()
            or artifact.get("bytes") != mp4_path.stat().st_size
            or artifact.get("sha256") != _sha256_file(mp4_path)
        ):
            reasons.append("final MP4 changed or became invalid after QA")
        run_dir = mp4_path.parent if mp4_path else None
        if run_dir is None:
            reasons.append("cannot resolve run directory for QA evidence")
        else:
            qa_path = run_dir / "delivery-qa.json"
            try:
                qa_from_disk = json.loads(qa_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                qa_from_disk = None
            if (
                qa_path.is_symlink()
                or not isinstance(qa_from_disk, dict)
                or qa_from_disk != qa
            ):
                reasons.append("delivery QA report file does not match verified status")

            files, artifact_reasons = _business_delivery_files(run_dir, status)
            reasons.extend(artifact_reasons)
            expected_artifacts = {
                relative.as_posix(): source
                for source, relative in files
                if relative.as_posix() != "delivery-qa.json"
            }
            manifest = qa.get("business_artifacts")
            manifest_by_path: dict[str, dict[str, Any]] = {}
            if isinstance(manifest, list):
                for item in manifest:
                    if not isinstance(item, dict):
                        continue
                    relative_value = str(item.get("relative_path") or "")
                    relative = Path(relative_value)
                    if (
                        not relative_value
                        or relative.is_absolute()
                        or ".." in relative.parts
                        or relative_value in manifest_by_path
                    ):
                        continue
                    manifest_by_path[relative_value] = item
            if set(manifest_by_path) != set(expected_artifacts):
                reasons.append("business artifact manifest does not match publish whitelist")
            else:
                for relative_value, source in expected_artifacts.items():
                    evidence = manifest_by_path[relative_value]
                    if (
                        source.is_symlink()
                        or not source.is_file()
                        or evidence.get("bytes") != source.stat().st_size
                        or evidence.get("sha256") != _sha256_file(source)
                    ):
                        reasons.append(
                            f"business artifact changed after QA: {relative_value}"
                        )

    for label, gate in _declared_delivery_gates(status):
        rejection = _gate_rejection(label, gate)
        if rejection:
            reasons.append(rejection)

    return not reasons, reasons


def _safe_delivery_source(out_dir: Path, source: Path) -> tuple[Path, Path] | None:
    """Resolve an artifact and reject symlinks or paths outside this run directory."""
    if source.is_symlink() or not source.is_file():
        return None
    root = out_dir.resolve()
    resolved = source.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None
    return resolved, relative


def _business_delivery_files(
    out_dir: Path, status: dict[str, Any]
) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Build the explicit business artifact whitelist; never copy a run directory."""
    files: list[tuple[Path, Path]] = []
    reasons: list[str] = []
    seen: set[Path] = set()

    def add(source: Path, *, required: bool = False) -> None:
        safe = _safe_delivery_source(out_dir, source)
        if safe is None:
            if required:
                reasons.append(f"required delivery artifact missing/unsafe: {source}")
            return
        resolved, relative = safe
        if relative not in seen:
            seen.add(relative)
            files.append((resolved, relative))

    for name in BUSINESS_DELIVERY_FIXED_FILES:
        add(out_dir / name, required=True)

    if status.get("want_tts"):
        sections_dir = out_dir / "audio" / "sections"
        if sections_dir.is_dir() and not sections_dir.is_symlink():
            for wav in sorted(sections_dir.glob("*.wav")):
                add(wav)

    if status.get("want_mp4"):
        mp4_path = (status.get("mp4") or {}).get("path")
        if not mp4_path:
            reasons.append("required mp4.path missing")
        else:
            add(Path(mp4_path), required=True)

    return files, reasons


def _remove_delivery_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def publish_business_delivery(
    out_dir: Path,
    destination: Path,
    status: dict[str, Any],
) -> dict[str, Any]:
    """Publish a verified whitelist via same-parent staging and atomic rename."""
    ready, reasons = delivery_publish_readiness(status)
    if not ready:
        return {"ok": False, "published": False, "reasons": reasons}

    files, artifact_reasons = _business_delivery_files(out_dir, status)
    if artifact_reasons:
        return {"ok": False, "published": False, "reasons": artifact_reasons}

    destination = destination.parent.resolve() / destination.name
    if destination.is_symlink():
        return {
            "ok": False,
            "published": False,
            "reasons": [f"delivery destination must not be a symlink: {destination}"],
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    nonce = uuid4().hex
    staging = destination.parent / f".{destination.name}.staging-{nonce}"
    backup = destination.parent / f".{destination.name}.backup-{nonce}"
    try:
        staging.mkdir()
        for source, relative in files:
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        had_previous = destination.exists() or destination.is_symlink()
        if had_previous:
            os.replace(destination, backup)
        try:
            os.replace(staging, destination)
        except Exception:
            if had_previous and backup.exists():
                os.replace(backup, destination)
            raise
    except Exception as exc:
        if staging.exists() or staging.is_symlink():
            _remove_delivery_path(staging)
        return {
            "ok": False,
            "published": False,
            "reasons": [f"atomic publish failed: {exc}"],
        }

    # The new delivery is already active. A stale hidden backup is safer than
    # reporting a false failure or rolling back a complete publication.
    cleanup_warning = None
    if backup.exists() or backup.is_symlink():
        try:
            _remove_delivery_path(backup)
        except OSError as exc:
            cleanup_warning = f"stale backup cleanup failed: {exc}"

    result = {
        "ok": True,
        "published": True,
        "path": str(destination),
        "files": [relative.as_posix() for _, relative in files],
    }
    if cleanup_warning:
        result["warning"] = cleanup_warning
    return result


def _import_parse_video_docx():
    """Lazy import so --sections-json works in TTS-only venvs without python-docx."""
    sys.path.insert(0, str(ROOT / "poc" / "video-training-natural-import"))
    sys.path.insert(0, str(ROOT / "poc" / "courseware-export" / "text-word-import"))
    from import_universal_video_content import parse_video_docx

    return parse_video_docx


def _ensure_video_gold(path: Path) -> Path:
    """Materialize sparse-excluded gold MP4 at full quality before use."""
    if path.is_file() and path.stat().st_size > 1024:
        return path
    try:
        from ensure_gold_assets import ensure_path

        rel = path.resolve().relative_to(ROOT.resolve()).as_posix()
        return ensure_path(rel, root=ROOT)
    except Exception as exc:  # noqa: BLE001
        raise FileNotFoundError(
            f"缺少视频金样且按需拉取失败: {path}\n{exc}\n"
            f"可手动执行: python3 scripts/ensure_gold_assets.py --path {path}"
        ) from exc


TEMPLATES: dict[str, dict[str, Any]] = {
    "product-video-faithful-v1": {
        "aliases": ["product", "q10", "商品培训视频"],
        "video_type": "product",
        "template_id": "template.product-training-faithful-v1",
        "style_pack_id": "style-pack.reference-product-blue-v1",
        "name_zh": "商品培训视频（如辅酶 Q10）",
        "settled": ROOT
        / "production-library/templates/settled/product-video-faithful-v1",
        "gold_mp4": ROOT
        / "production-library/templates/settled/product-video-faithful-v1"
        / "辅酶Q10_商品培训视频_金样_v1.mp4",
        "voice_pack": ROOT
        / "production-library/voices/reference-pharmacist-qwen-v1",
        "segment_labels": [
            "开场",
            "核心讲解",
            "品牌品类",
            "核心功效",
            "产品特点",
            "适宜人群",
            "联合用药",
            "总结",
        ],
    },
    "health-video-reference-tech-v1": {
        "aliases": ["health", "wind-heat", "风热", "疾病科普视频"],
        "video_type": "health",
        "template_id": "template.health-reference-tech-v1",
        "style_pack_id": "style-pack.reference-medical-tech-v1",
        "name_zh": "疾病科普视频（如风热证）",
        "settled": ROOT
        / "production-library/templates/settled/health-video-reference-tech-v1",
        "gold_mp4": ROOT
        / "production-library/templates/settled/health-video-reference-tech-v1"
        / "风热证_疾病科普视频_金样_v1.mp4",
        "voice_pack": ROOT
        / "production-library/voices/reference-pharmacist-qwen-v1",
        "segment_labels": [
            "开场",
            "人物情境",
            "病因机理",
            "典型症状",
            "治疗思路",
            "用药建议",
            "总结",
        ],
    },
}

DEFAULT_TEMPO = 1.16
MAX_TEMPO = 1.18
LEAD_IN = 0.06
LEAD_OUT = 0.10
CROSSFADE = 0.035
MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"


def resolve_template(key: str) -> tuple[str, dict[str, Any]]:
    k = key.strip()
    if k in TEMPLATES:
        return k, TEMPLATES[k]
    low = k.lower()
    for slug, meta in TEMPLATES.items():
        if low == slug or low in {a.lower() for a in meta["aliases"]}:
            return slug, meta
        if k in meta["aliases"] or k == meta["name_zh"]:
            return slug, meta
    raise SystemExit(
        f"未知模板: {key}；可选: {', '.join(TEMPLATES)} / product / health"
    )


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80] or "video-run"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_voice_pack(pack_dir: Path) -> dict[str, Any]:
    pack_json = pack_dir / "voice-pack.json"
    if not pack_json.exists():
        raise SystemExit(f"缺少 voice pack: {pack_json}")
    pack = json.loads(pack_json.read_text(encoding="utf-8"))
    prompt = pack_dir / (pack.get("prompt", {}) or {}).get("audio", "prompt.wav")
    ref_text = (pack.get("prompt", {}) or {}).get("ref_text")
    if not ref_text:
        ref_path = pack_dir / "ref_text.txt"
        ref_text = ref_path.read_text(encoding="utf-8").strip() if ref_path.exists() else ""
    if not prompt.exists() or not ref_text:
        raise SystemExit(f"voice pack 不完整: {pack_dir}")
    return {
        "id": pack.get("id", "voice.reference-pharmacist-qwen-v1"),
        "prompt_audio": prompt,
        "ref_text": ref_text,
        "pack_dir": pack_dir,
        "raw": pack,
    }


def sections_from_docx(docx: Path, video_type: str, asset_root: Path) -> dict[str, Any]:
    parse_video_docx = _import_parse_video_docx()
    manifest = parse_video_docx(docx, asset_root, video_type)
    sections = []
    for sec in manifest.get("sections") or []:
        paras = sec.get("approved_narration") or []
        text = "\n".join(p for p in paras if str(p).strip())
        if not text.strip():
            continue
        sections.append(
            {
                "title": sec.get("title") or f"板块{len(sections)+1}",
                "narration": text.strip(),
                "images": sec.get("images") or [],
            }
        )
    theme = (manifest.get("video") or {}).get("theme") or docx.stem
    return {
        "theme": theme,
        "sections": sections,
        "source": {"kind": "docx", "path": str(docx)},
        "routing": manifest.get("routing"),
        "raw_manifest": manifest,
    }


def sections_from_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"theme": path.stem, "sections": data}
    sections = []
    for i, sec in enumerate(data.get("sections") or []):
        nar = sec.get("narration") or sec.get("approved_narration") or sec.get("text") or ""
        if isinstance(nar, list):
            nar = "\n".join(str(x).strip() for x in nar if str(x).strip())
        nar = str(nar).strip()
        if not nar:
            continue
        sections.append(
            {
                "title": sec.get("title") or sec.get("heading") or f"板块{i+1}",
                "narration": nar,
                "images": sec.get("images") or [],
            }
        )
    return {
        "theme": data.get("theme") or path.stem,
        "sections": sections,
        "source": {"kind": "json", "path": str(path)},
    }


def build_gap_report(
    content: dict[str, Any], meta: dict[str, Any], *, mode: str
) -> dict[str, Any]:
    gaps = []
    for i, sec in enumerate(content["sections"]):
        imgs = sec.get("images") or []
        if not imgs:
            gaps.append(
                {
                    "id": f"gap-section-{i+1}-image",
                    "section": sec["title"],
                    "kind": "optional_image",
                    "message": "本板块未附授权图；无图可继续，有包装/Logo 请业务补传",
                    "business_provides": True,
                    "blocking": False,
                }
            )
    if mode != "full":
        gaps.append(
            {
                "id": "note-formal-rerender",
                "kind": "workflow_note",
                "message": "当前为规划包；正式成片须通过内容/素材审批、完整分段重渲与发布质检。",
                "business_provides": False,
                "blocking": False,
            }
        )
    return {
        "schema": "business-gap-list-v1",
        "template_id": meta["template_id"],
        "style_pack_id": meta["style_pack_id"],
        "gap_count": len(gaps),
        "blocking_gap_count": sum(bool(item.get("blocking")) for item in gaps),
        "gaps": gaps,
    }


def build_storyboard_html(content: dict[str, Any], meta: dict[str, Any], out: Path) -> None:
    cards = []
    for i, sec in enumerate(content["sections"], 1):
        nar = (
            str(sec["narration"])
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )
        title = (
            str(sec["title"])
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        cards.append(
            f"""
<article style="border:1px solid #ddd;border-radius:12px;padding:14px 16px;margin:0 0 12px;background:#fff">
  <header style="display:flex;gap:10px;align-items:baseline">
    <span style="font-weight:800;color:#2b6cb0">{i:02d}</span>
    <h2 style="margin:0;font-size:16px">{title}</h2>
  </header>
  <p style="margin:10px 0 0;line-height:1.65;color:#222">{nar}</p>
</article>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<title>{content['theme']} · 分镜预览</title>
<style>
body{{font-family:PingFang SC,Microsoft YaHei,sans-serif;background:#f6f7f9;margin:0;padding:24px}}
.wrap{{max-width:880px;margin:0 auto}}
h1{{font-size:22px;margin:0 0 6px}}
.meta{{color:#666;font-size:13px;margin-bottom:18px}}
</style></head><body><div class="wrap">
<h1>{content['theme']}</h1>
<p class="meta">模板：{meta['name_zh']} · style_pack：{meta['style_pack_id']} · 板块 {len(content['sections'])} 个</p>
{''.join(cards)}
</div></body></html>
"""
    out.write_text(html, encoding="utf-8")


def detect_tts_python() -> Path | None:
    candidates = [
        ROOT / ".venv-qwen-tts/bin/python",
        ROOT
        / "production-library/validation/courseware/product-courseware-4-faithful-replica-v1/.venv-tts/bin/python",
        Path(sys.executable),
    ]
    for py in candidates:
        if not py.exists():
            continue
        try:
            r = subprocess.run(
                [str(py), "-c", "from mlx_audio.tts.utils import load_model"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return None


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def generate_section_tts(
    *,
    text: str,
    out_wav: Path,
    voice: dict[str, Any],
    py: Path,
) -> dict[str, Any]:
    """Generate one semantic-block wav via Qwen3 clone in the TTS venv."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = _media_tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("缺少 ffmpeg，无法生成正式旁白")
    worker = out_wav.parent / f"_tts_worker_{out_wav.stem}.py"
    worker.write_text(
        f"""
import json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
import mlx.core as mx
from mlx_audio.tts.utils import load_model

text = {text!r}
ref_audio = {str(voice['prompt_audio'])!r}
ref_text = {voice['ref_text']!r}
out = {str(out_wav)!r}
ffmpeg = {ffmpeg!r}
model_id = {MODEL_ID!r}
tempo = {DEFAULT_TEMPO}

model = load_model(model_id)
sr = model.sample_rate
results = list(model.generate(
    text=text,
    voice="",
    speed=1.0,
    lang_code="Chinese",
    ref_audio=ref_audio,
    ref_text=ref_text,
))
if not results:
    raise SystemExit("TTS empty")
chunks = []
for r in results:
    arr = np.array(r.audio, copy=True)
    if arr.ndim > 1:
        arr = arr.reshape(-1)
    chunks.append(arr)
audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
raw_path = Path(out).with_suffix(".raw.wav")
sf.write(raw_path, audio, sr)
# mild tempo
import subprocess
subprocess.run([
    ffmpeg,"-loglevel","error","-y","-i",str(raw_path),
    "-af",f"atempo={{tempo:.6f}},aresample={{sr}}",
    str(out),
], check=True)
raw_path.unlink(missing_ok=True)
print(json.dumps({{"ok": True, "sample_rate": sr}}))
""",
        encoding="utf-8",
    )
    try:
        r = subprocess.run(
            [str(py), str(worker)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if r.returncode != 0:
            raise RuntimeError(
                f"TTS failed for {out_wav.name}: {r.stderr[-800:] or r.stdout[-800:]}"
            )
    finally:
        worker.unlink(missing_ok=True)

    # lead in/out pad via ffmpeg
    padded = out_wav.with_suffix(".pad.wav")
    subprocess.run(
        [
            ffmpeg,
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(out_wav),
            "-af",
            f"adelay={int(LEAD_IN*1000)}|{int(LEAD_IN*1000)},apad=pad_dur={LEAD_OUT}",
            str(padded),
        ],
        check=True,
    )
    padded.replace(out_wav)
    dur = wav_duration(out_wav)
    return {
        "file": str(out_wav.relative_to(out_wav.parents[1]) if False else out_wav.name),
        "path": str(out_wav),
        "duration_s": round(dur, 3),
        "tempo": DEFAULT_TEMPO,
        "chars": len(re.sub(r"\s+", "", text)),
    }


def concat_wavs(paths: list[Path], out: Path, gap_s: float = 0.12) -> float:
    """Concatenate mono wavs with short gaps using ffmpeg."""
    ffmpeg = _media_tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("缺少 ffmpeg，无法拼接旁白")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not paths:
        raise ValueError("no wavs")
    if len(paths) == 1:
        shutil.copy2(paths[0], out)
        return wav_duration(out)
    list_file = out.with_suffix(".concat.txt")
    silence = out.parent / "_gap.wav"
    # create silence matching first file format
    with wave.open(str(paths[0]), "rb") as w0:
        sr = w0.getframerate()
        ch = w0.getnchannels()
        sw = w0.getsampwidth()
    n = int(sr * gap_s)
    with wave.open(str(silence), "wb") as ws:
        ws.setnchannels(ch)
        ws.setsampwidth(sw)
        ws.setframerate(sr)
        ws.writeframes(b"\x00" * n * ch * sw)
    lines = []
    for i, p in enumerate(paths):
        lines.append(f"file '{p.resolve()}'")
        if i < len(paths) - 1:
            lines.append(f"file '{silence.resolve()}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(
        [
            ffmpeg,
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(out),
        ],
        check=True,
    )
    silence.unlink(missing_ok=True)
    list_file.unlink(missing_ok=True)
    return wav_duration(out)


def probe_duration(path: Path) -> float:
    ffprobe = _media_tool("ffprobe")
    if not ffprobe:
        raise RuntimeError("缺少 ffprobe，无法读取媒体时长")
    out = subprocess.check_output(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def mux_audio_on_gold(
    *,
    gold_mp4: Path,
    narration_wav: Path,
    out_mp4: Path,
) -> dict[str, Any]:
    """Overlay new narration on gold video; stretch/pad to match audio."""
    if not gold_mp4.exists():
        raise FileNotFoundError(gold_mp4)
    ffmpeg = _media_tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("缺少 ffmpeg，无法合成视频")
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    v_dur = probe_duration(gold_mp4)
    a_dur = probe_duration(narration_wav)
    # match video length to audio (prefer extend/slow slightly rather than cut speech)
    if a_dur <= 0.1:
        raise RuntimeError("narration too short")
    ratio = a_dur / v_dur if v_dur > 0 else 1.0
    # setpts: >1 slows video
    vf = f"setpts=PTS*{ratio:.6f}" if abs(ratio - 1.0) > 0.02 else "null"
    cmd = [
        ffmpeg,
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(gold_mp4),
        "-i",
        str(narration_wav),
        "-filter_complex",
        f"[0:v]{vf}[v];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-16:LRA=7:TP=-1.5[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return {
        "path": str(out_mp4),
        "gold_duration_s": round(v_dur, 3),
        "audio_duration_s": round(a_dur, 3),
        "video_time_stretch": round(ratio, 4),
        "method": "gold-visual-shell + cloned-narration-mux",
    }


def write_delivery_md(
    path: Path,
    *,
    content: dict[str, Any],
    meta: dict[str, Any],
    slug: str,
    status: dict[str, Any],
) -> None:
    mp4 = status.get("mp4")
    tts = status.get("tts")
    lines = [
        f"# 交付说明 · {content['theme']}",
        "",
        f"- 模板：{meta['name_zh']}（`{meta['template_id']}`）",
        f"- style_pack：`{meta['style_pack_id']}`",
        f"- voice：`{status.get('voice_id')}`",
        f"- 运行目录：`{slug}`",
        f"- 生成时间：{status.get('created_at')}",
        "",
        "## 产物",
        "",
        "| 文件 | 说明 |",
        "|------|------|",
        "| `content.json` | 解析后的板块与旁白 |",
        "| `storyboard.html` | 分镜预览（可浏览器打开） |",
        "| `gap-report.json` | 缺口清单 |",
        "| `delivery-qa.json` | 正式发布结构与媒体完整性质检 |",
    ]
    if tts and tts.get("ok"):
        if (path.parent / "audio" / "full-narration.wav").is_file() and status.get(
            "mode"
        ) == "audio-shell":
            lines.append("| `audio/full-narration.wav` | 克隆药师旁白母带 |")
        lines.append("| `audio/sections/*.wav` | 分板块旁白 |")
    if mp4 and mp4.get("ok"):
        method = (mp4 or {}).get("method") or ""
        if "segment" in method or "full" in method or "health" in method:
            desc = "培训视频（分段重渲：文案/屏显/旁白）"
        else:
            desc = "培训视频（兼容：金样画面壳 + 新旁白）"
        lines.append(f"| `{Path(mp4['path']).name}` | {desc} |")
    lines.extend(
        [
            "",
            "## 状态",
            "",
            f"- 规划包：{'✅' if status.get('package_ok') else '❌'}",
            f"- 克隆旁白：{('✅' if tts and tts.get('ok') else ('⏭ 跳过' if not status.get('want_tts') else '❌ ' + str((tts or {}).get('error'))))}",
            f"- MP4：{('✅' if mp4 and mp4.get('ok') else ('⏭ 跳过' if not status.get('want_mp4') else '❌ ' + str((mp4 or {}).get('error'))))}",
            f"- 发布质检：{('✅ qa_passed' if (status.get('qa') or {}).get('state') == 'qa_passed' else '❌ 未通过，不得进入正式交付')}",
            "",
            "## 使用说明",
            "",
            "1. 打开 `storyboard.html` 核对旁白与板块。",
            "2. 有 MP4 则可直接内训试看；需改文案后重新运行本命令。",
            "3. 商品/疾病科普 full 模式会按主题分段重渲；audio-shell 仅为兼容旧路径。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="业务视频绿线：内容→交付包→可选 TTS/MP4")
    ap.add_argument(
        "--template",
        required=True,
        help="product-video-faithful-v1 | health-video-reference-tech-v1 | product | health",
    )
    src = ap.add_mutually_exclusive_group(required=False)
    src.add_argument("--docx", type=Path, help="记事本式业务 Word")
    src.add_argument("--sections-json", type=Path, help="板块 JSON")
    ap.add_argument("--out-dir", type=Path, default=None, help="输出目录（默认自动）")
    ap.add_argument("--slug", type=str, default=None, help="输出目录名")
    ap.add_argument("--with-tts", action="store_true", help="生成克隆旁白")
    ap.add_argument(
        "--with-mp4",
        action="store_true",
        help="导出 MP4：product/health 默认分段重渲；audio-shell 模式为叠金样壳",
    )
    ap.add_argument(
        "--mode",
        choices=["full", "plan", "audio-shell"],
        default="full",
        help="full=换文案/画面槽位+重渲(商品/疾病科普)；plan=仅规划；audio-shell=旧叠声壳",
    )
    ap.add_argument(
        "--product-image",
        type=Path,
        default=None,
        help="授权包装图（png/jpg），写入画面 product 槽位",
    )
    ap.add_argument(
        "--product-approval",
        type=Path,
        default=None,
        help="商品内容/包装审批 JSON（绑定审核稿与包装图 SHA-256）",
    )
    ap.add_argument(
        "--copy-to-business-delivery",
        action="store_true",
        help="复制到业务包 05_交付物放这里/",
    )
    ap.add_argument(
        "--theme-package",
        type=Path,
        default=None,
        help="健康科普主题制作包目录（含 screen.json / assets / approval.json）",
    )
    ap.add_argument(
        "--skip-visual-approval",
        action="store_true",
        help="调试用：跳过画面过目门闸（正式交付禁止）",
    )
    args = ap.parse_args()

    if not args.docx and not args.sections_json and not args.theme_package:
        raise SystemExit("须提供 --docx / --sections-json / --theme-package 之一")
    if args.theme_package and (args.docx or args.sections_json):
        raise SystemExit(
            "--theme-package 已冻结并审批其内部 sections.json；禁止再叠加外部 --docx/--sections-json"
        )

    slug_key, meta = resolve_template(args.template)
    if args.with_mp4 and not args.with_tts:
        args.with_tts = True
    if args.mode == "plan":
        args.with_tts = False
        args.with_mp4 = False
    if args.skip_visual_approval and (
        args.mode != "plan"
        or args.with_tts
        or args.with_mp4
        or args.copy_to_business_delivery
    ):
        print(
            "ERROR: --skip-visual-approval 仅限 --mode plan 本地规划调试；旁白、渲染和交付均禁止跳过画面审批。",
            file=sys.stderr,
        )
        return 2

    # 环境探测：无 TTS 时禁止假装 full 出片；强制后续 status 写入 voice_id
    env_probe: dict[str, Any] = {}
    try:
        probe_script = ROOT / "scripts" / "probe_production_env.py"
        pr = subprocess.run(
            [sys.executable, str(probe_script), "--json"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        if pr.stdout.strip():
            env_probe = json.loads(pr.stdout)
    except (OSError, json.JSONDecodeError) as e:
        env_probe = {"ok": False, "error": str(e), "capabilities": {}}

    caps = env_probe.get("capabilities") or {}
    if args.with_tts and not caps.get("video_tts"):
        print(
            "ERROR: 本机无可用克隆 TTS（.venv-qwen-tts + mlx_audio.tts）。\n"
            "诚实降级：可改 --mode plan 只交规划包；禁止系统 say/机器人音色冒充正式旁白；\n"
            "不得对业务声称已出正式 MP4。\n"
            "探测：python3 scripts/probe_production_env.py",
            file=sys.stderr,
        )
        return 2
    if args.with_mp4 and not caps.get("video_render"):
        print(
            "ERROR: 本机缺 node/ffmpeg，无法渲染/合成 MP4。\n"
            "诚实降级：去掉 --with-mp4，或先补环境。\n"
            "探测：python3 scripts/probe_production_env.py",
            file=sys.stderr,
        )
        return 2

    # 主题包可自带 sections
    theme_pkg: Path | None = (
        args.theme_package.resolve() if args.theme_package else None
    )
    if theme_pkg and not args.sections_json and not args.docx:
        sec_path = theme_pkg / "sections.json"
        if not sec_path.is_file():
            raise SystemExit(f"主题包缺少 sections.json: {theme_pkg}")
        content = sections_from_json(sec_path)
        if not content.get("theme"):
            pkg_meta = {}
            if (theme_pkg / "package.json").is_file():
                pkg_meta = json.loads(
                    (theme_pkg / "package.json").read_text(encoding="utf-8")
                )
            content["theme"] = pkg_meta.get("theme") or theme_pkg.name
    elif args.docx:
        asset_root = ROOT / "tmp" / "business-video-assets" / slugify(args.docx.stem)
        content = sections_from_docx(
            args.docx.resolve(), meta["video_type"], asset_root
        )
    else:
        content = sections_from_json(args.sections_json.resolve())

    if not content["sections"]:
        raise SystemExit("未解析到任何有效板块旁白")

    theme = content["theme"]
    run_slug = args.slug or f"{slugify(theme)}-{slug_key}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out_dir = (
        args.out_dir.resolve()
        if args.out_dir
        else (ROOT / "outputs" / "business-video-runs" / run_slug)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # package
    content_out = {
        "theme": theme,
        "template_slug": slug_key,
        "template_id": meta["template_id"],
        "style_pack_id": meta["style_pack_id"],
        "name_zh": meta["name_zh"],
        "sections": content["sections"],
        "source": content.get("source"),
        "segment_labels_hint": meta["segment_labels"],
    }
    write_json(out_dir / "content.json", content_out)
    gaps = build_gap_report(content, meta, mode=args.mode)
    write_json(out_dir / "gap-report.json", gaps)
    build_storyboard_html(content, meta, out_dir / "storyboard.html")
    if slug_key == "product-video-faithful-v1":
        sys.path.insert(0, str(ROOT / "scripts"))
        from business_video_product_full import build_product_approval_request  # type: ignore

        request_path = out_dir / "product-approval.request.json"
        supplied_approval = (
            args.product_approval.resolve() if args.product_approval else None
        )
        if supplied_approval != request_path.resolve():
            write_json(
                request_path,
                build_product_approval_request(
                    content,
                    args.product_image.resolve() if args.product_image else None,
                ),
            )

    status: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_ok": True,
        "template": slug_key,
        "mode": args.mode,
        "want_tts": bool(args.with_tts),
        "want_mp4": bool(args.with_mp4),
        "voice_id": None,
        "out_dir": str(out_dir),
        "delivery_requirements": {
            "visual_approval": bool(
                slug_key == "health-video-reference-tech-v1"
                and args.mode == "full"
                and args.with_mp4
            ),
        },
        "env_capabilities": {
            "video_tts": caps.get("video_tts"),
            "video_render": caps.get("video_render"),
            "video_full": caps.get("video_full"),
        },
    }

    voice_meta = load_voice_pack(meta["voice_pack"])
    status["voice_id"] = voice_meta["id"]
    if not status["voice_id"]:
        raise SystemExit("voice pack 缺少 id：禁止无 voice_id 出正式旁白")
    write_json(
        out_dir / "voice-plan.json",
        {
            "voice_id": voice_meta["id"],
            "pack_dir": str(voice_meta["pack_dir"].relative_to(ROOT)),
            "pace": {"default_tempo": DEFAULT_TEMPO, "max_tempo": MAX_TEMPO},
            "forbid_system_tts": True,
            "sections": [
                {"title": s["title"], "chars": len(re.sub(r"\s+", "", s["narration"]))}
                for s in content["sections"]
            ],
        },
    )

    tts_status: dict[str, Any] = {"ok": False}
    mp4_status: dict[str, Any] = {"ok": False}
    full_status: dict[str, Any] | None = None

    # --- product / health full content+visual+audio re-render ---
    use_product_full = (
        args.mode == "full"
        and slug_key == "product-video-faithful-v1"
        and (args.with_tts or args.with_mp4)
    )
    use_health_full = (
        args.mode == "full"
        and slug_key == "health-video-reference-tech-v1"
        and (args.with_tts or args.with_mp4)
    )
    if use_product_full:
        sys.path.insert(0, str(ROOT / "scripts"))
        from business_video_product_full import run_product_full  # type: ignore

        try:
            full_status = run_product_full(
                content=content,
                out_dir=out_dir,
                voice_pack_dir=meta["voice_pack"],
                with_tts=bool(args.with_tts),
                with_render=bool(args.with_mp4),
                product_image=args.product_image.resolve()
                if args.product_image
                else None,
                product_approval=args.product_approval.resolve()
                if args.product_approval
                else None,
            )
            tts_status = {
                "ok": bool(full_status.get("ok")) and bool(args.with_tts),
                "mode": "full-segment-clone",
                "segments": (full_status or {}).get("segments"),
                "error": full_status.get("error") if full_status else None,
            }
            mp4 = (full_status or {}).get("mp4") or {}
            mp4_status = {
                "ok": bool(mp4.get("ok")),
                "path": mp4.get("path"),
                "method": "segment-rerender-content-visual-audio",
                "error": mp4.get("error") or full_status.get("error"),
            }
        except Exception as e:
            tts_status = {"ok": False, "error": str(e)}
            mp4_status = {"ok": False, "error": str(e)}
            full_status = {"ok": False, "error": str(e)}
    elif use_health_full:
        sys.path.insert(0, str(ROOT / "scripts"))
        from business_video_health_full import run_health_full  # type: ignore

        try:
            full_status = run_health_full(
                content=content,
                out_dir=out_dir,
                voice_pack_dir=meta["voice_pack"],
                with_tts=bool(args.with_tts),
                with_render=bool(args.with_mp4),
                theme_package=theme_pkg,
                require_visual_approval=not bool(args.skip_visual_approval),
            )
            tts_status = {
                "ok": bool(full_status.get("ok")) and bool(args.with_tts),
                "mode": "full-segment-clone-health",
                "segments": (full_status or {}).get("segments"),
                "error": full_status.get("error") if full_status else None,
            }
            mp4 = (full_status or {}).get("mp4") or {}
            mp4_status = {
                "ok": bool(mp4.get("ok")),
                "path": mp4.get("path"),
                "method": "health-segment-rerender-content-visual-audio",
                "error": mp4.get("error") or full_status.get("error"),
            }
        except Exception as e:
            tts_status = {"ok": False, "error": str(e)}
            mp4_status = {"ok": False, "error": str(e)}
            full_status = {"ok": False, "error": str(e)}

    # --- legacy audio-shell path (explicit only) ---
    if args.mode == "audio-shell":
        if args.with_tts:
            py = detect_tts_python()
            if not py:
                tts_status = {
                    "ok": False,
                    "error": "未找到可用 Qwen3-TTS 环境（期望 .venv-qwen-tts）",
                }
            else:
                try:
                    audio_dir = out_dir / "audio" / "sections"
                    audio_dir.mkdir(parents=True, exist_ok=True)
                    section_reports = []
                    wavs: list[Path] = []
                    for i, sec in enumerate(content["sections"], 1):
                        wav = audio_dir / f"{i:02d}-{slugify(sec['title'])[:40]}.wav"
                        print(f"[tts] {i}/{len(content['sections'])} {sec['title']} …")
                        rep = generate_section_tts(
                            text=sec["narration"],
                            out_wav=wav,
                            voice=voice_meta,
                            py=py,
                        )
                        rep["title"] = sec["title"]
                        section_reports.append(rep)
                        wavs.append(wav)
                    full = out_dir / "audio" / "full-narration.wav"
                    full_dur = concat_wavs(wavs, full)
                    tts_status = {
                        "ok": True,
                        "python": str(py),
                        "full_narration": str(full),
                        "full_duration_s": round(full_dur, 3),
                        "sections": section_reports,
                        "mode": "audio-shell",
                    }
                    write_json(out_dir / "audio" / "tts-report.json", tts_status)
                except Exception as e:
                    tts_status = {"ok": False, "error": str(e)}
        if args.with_mp4:
            if not tts_status.get("ok"):
                mp4_status = {
                    "ok": False,
                    "error": "需要成功的 --with-tts 才能叠轨 MP4",
                }
            else:
                try:
                    gold = _ensure_video_gold(Path(meta["gold_mp4"]))
                    if not gold.exists():
                        alts = list(meta["settled"].glob("*.mp4"))
                        gold = next(
                            (p for p in alts if "可编辑" not in p.name),
                            alts[0] if alts else gold,
                        )
                    out_mp4 = out_dir / f"{slugify(theme)}_培训视频_v1.mp4"
                    mux = mux_audio_on_gold(
                        gold_mp4=gold,
                        narration_wav=Path(tts_status["full_narration"]),
                        out_mp4=out_mp4,
                    )
                    mp4_status = {"ok": True, **mux, "method": "audio-shell"}
                except Exception as e:
                    mp4_status = {"ok": False, "error": str(e)}

    status["tts"] = tts_status
    status["mp4"] = mp4_status
    if full_status is not None:
        status["full"] = full_status

    # DELIVERY.md displays the in-memory gate state. Rebuild QA after writing it
    # so the final evidence manifest binds every copied file except QA's own JSON.
    status["qa"] = build_delivery_qa(out_dir, status)
    write_delivery_md(
        out_dir / "DELIVERY.md",
        content=content,
        meta=meta,
        slug=run_slug,
        status=status,
    )
    status["qa"] = build_delivery_qa(out_dir, status)
    write_json(out_dir / "delivery-qa.json", status["qa"])
    publish_ready, publish_reasons = delivery_publish_readiness(status)
    status["delivery_publish_readiness"] = {
        "ok": publish_ready,
        "reasons": publish_reasons,
    }
    write_json(out_dir / "run-status.json", status)

    if args.copy_to_business_delivery:
        dest_root = (
            ROOT
            / "outputs/业务使用资料包/药店培训内容工厂-业务包/05_交付物放这里"
            / run_slug
        )
        publish_result = publish_business_delivery(out_dir, dest_root, status)
        status["business_delivery"] = publish_result
        if publish_result.get("published"):
            status["business_delivery_copy"] = str(dest_root)
        write_json(out_dir / "run-status.json", status)

    # summary to stdout
    generation_ok = (
        status["package_ok"]
        and (not args.with_tts or tts_status.get("ok"))
        and (not args.with_mp4 or mp4_status.get("ok"))
        and (
            args.mode != "full"
            or not (args.with_tts or args.with_mp4)
            or bool((full_status or {}).get("ok"))
        )
    )
    formal_qa_ok = not (args.mode == "full" and args.with_mp4) or (
        (status.get("qa") or {}).get("state") == "qa_passed"
        and (status.get("qa") or {}).get("ok") is True
    )
    delivery_ok = not args.copy_to_business_delivery or bool(
        (status.get("business_delivery") or {}).get("published")
    )
    summary = {
        "ok": bool(generation_ok and formal_qa_ok and delivery_ok),
        "generation_ok": bool(generation_ok),
        "qa_state": (status.get("qa") or {}).get("state"),
        "delivery_ready": bool(publish_ready),
        "out_dir": str(out_dir),
        "theme": theme,
        "template": slug_key,
        "mode": args.mode,
        "method": mp4_status.get("method") or tts_status.get("mode"),
        "sections": len(content["sections"]),
        "tts": tts_status.get("ok"),
        "mp4": mp4_status.get("ok"),
        "mp4_path": mp4_status.get("path"),
        "storyboard": str(out_dir / "storyboard.html"),
        "business_delivery": status.get("business_delivery"),
        "error": tts_status.get("error")
        or mp4_status.get("error")
        or (
            next(iter(publish_reasons), None)
            if (not formal_qa_ok or args.copy_to_business_delivery)
            else None
        )
        or next(iter((status.get("business_delivery") or {}).get("reasons") or []), None),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
