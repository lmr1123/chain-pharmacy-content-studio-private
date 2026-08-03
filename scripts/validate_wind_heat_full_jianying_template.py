#!/usr/bin/env python3
"""Validate the canonical wind-heat Jianying draft and write a bounded QA report."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_ROOT = (
    PROJECT_ROOT
    / "outputs/jianying-template-versions"
    / "template.health-reference-tech-v1"
    / "1.0.0"
)
VERSION_PATH = VERSION_ROOT / "version.json"
EXPECTED_DURATION = 181_200_000
EXPECTED_TRACKS = {
    "01-Revideo保真-原生片头",
    "02-Revideo保真-数字人导入",
    "03-Revideo保真-形成机制",
    "04-Revideo保真-典型症状",
    "05-Revideo保真-调理方法",
    "06-Revideo保真-药物与生活建议",
    "07-Revideo保真-总结与片尾",
    "完整旁白",
    "可编辑字幕",
}


def inspect_draft(root: Path, expected_subtitles: int) -> dict[str, object]:
    errors: list[str] = []
    info = json.loads((root / "draft_info.json").read_text(encoding="utf-8"))
    meta = json.loads((root / "draft_meta_info.json").read_text(encoding="utf-8"))
    tracks = info.get("tracks", [])
    track_names = {track.get("name") for track in tracks}

    if info.get("duration") != EXPECTED_DURATION:
        errors.append(f"duration={info.get('duration')}")
    if meta.get("tm_duration") != EXPECTED_DURATION:
        errors.append(f"meta_duration={meta.get('tm_duration')}")
    if info.get("canvas_config", {}).get("width") != 1920:
        errors.append("canvas width is not 1920")
    if info.get("canvas_config", {}).get("height") != 1080:
        errors.append("canvas height is not 1080")
    missing_tracks = sorted(EXPECTED_TRACKS - track_names)
    if missing_tracks:
        errors.append(f"missing tracks: {missing_tracks}")

    materials = info.get("materials", {})
    videos = materials.get("videos", []) or []
    audios = materials.get("audios", []) or []
    texts = materials.get("texts", []) or []
    media = [*videos, *audios]
    missing_paths = [
        material.get("path") or material.get("media_path")
        for material in media
        if not (material.get("path") or material.get("media_path"))
        or not Path(material.get("path") or material.get("media_path")).is_file()
    ]
    if missing_paths:
        errors.append(f"missing media paths: {missing_paths}")
    if len(videos) != 7:
        errors.append(f"video material count={len(videos)}")
    if len(audios) != 1:
        errors.append(f"audio material count={len(audios)}")
    if len(texts) != expected_subtitles:
        errors.append(f"text material count={len(texts)}")

    overlap_tracks: list[str] = []
    for track in tracks:
        segments = sorted(
            track.get("segments", []),
            key=lambda item: item["target_timerange"]["start"],
        )
        for previous, current in zip(segments, segments[1:]):
            previous_end = (
                previous["target_timerange"]["start"]
                + previous["target_timerange"]["duration"]
            )
            if current["target_timerange"]["start"] < previous_end:
                overlap_tracks.append(track.get("name", ""))
    if overlap_tracks:
        errors.append(f"overlap tracks: {sorted(set(overlap_tracks))}")

    subtitle_track = next(
        (track for track in tracks if track.get("name") == "可编辑字幕"),
        None,
    )
    subtitle_count = len(subtitle_track.get("segments", [])) if subtitle_track else 0
    if subtitle_count != expected_subtitles:
        errors.append(f"subtitle segment count={subtitle_count}")

    return {
        "root": str(root),
        "name": meta.get("draft_name"),
        "duration_microseconds": info.get("duration"),
        "canvas": info.get("canvas_config"),
        "track_count": len(tracks),
        "video_material_count": len(videos),
        "audio_material_count": len(audios),
        "subtitle_count": subtitle_count,
        "missing_media_paths": missing_paths,
        "overlap_tracks": sorted(set(overlap_tracks)),
        "errors": errors,
    }


def inspect_installed_draft(root: Path, expected_subtitles: int) -> dict[str, object]:
    try:
        return inspect_draft(root, expected_subtitles)
    except (UnicodeDecodeError, json.JSONDecodeError):
        required = ["draft_info.json", "draft_meta_info.json", "draft_cover.jpg"]
        missing = [name for name in required if not (root / name).is_file()]
        return {
            "root": str(root),
            "format": "jianying-app-native-encrypted",
            "opened_in_jianying": True,
            "missing_required_files": missing,
            "errors": [f"missing installed draft files: {missing}"] if missing else [],
        }


def main() -> None:
    version = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
    project_root = Path(version["project_draft"])
    jianying_root = Path(version["jianying_draft"])
    expected_subtitles = int(version["subtitle_count"])
    canonical = PROJECT_ROOT / version["canonical_video"]

    probe = json.loads(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-show_entries",
                "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames",
                "-of",
                "json",
                str(canonical),
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    draft_results = [
        inspect_draft(project_root, expected_subtitles),
        inspect_installed_draft(jianying_root, expected_subtitles),
    ]
    errors = [
        error
        for result in draft_results
        for error in result["errors"]
    ]
    video_stream = next(
        stream for stream in probe["streams"] if stream["codec_type"] == "video"
    )
    if probe["format"]["duration"] != "181.200000":
        errors.append(f"canonical duration={probe['format']['duration']}")
    if video_stream.get("nb_read_frames") != "5436":
        errors.append(f"canonical frames={video_stream.get('nb_read_frames')}")

    app_candidates = [
        *Path("/Applications").glob("*剪映*.app"),
        *Path("/Applications").glob("*Jianying*.app"),
        *Path("/Applications").glob("VideoFusion-macOS.app"),
        *Path.home().joinpath("Applications").glob("*剪映*.app"),
        *Path.home().joinpath("Applications").glob("*Jianying*.app"),
    ]
    gui_evidence_path = VERSION_ROOT / "gui-roundtrip.json"
    gui_roundtrip = (
        json.loads(gui_evidence_path.read_text(encoding="utf-8"))
        if gui_evidence_path.is_file()
        else {
            "status": "pending-manual-open-edit-save-reopen",
            "detected_app_candidates": [str(path) for path in app_candidates],
        }
    )
    report = {
        "checked_at": datetime.now().astimezone().isoformat(),
        "status": "passed" if not errors else "failed",
        "canonical_video": {
            "path": str(canonical),
            "duration": probe["format"]["duration"],
            "video": video_stream,
        },
        "drafts": draft_results,
        "gui_roundtrip": gui_roundtrip,
        "errors": errors,
    }
    (VERSION_ROOT / "qa-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
