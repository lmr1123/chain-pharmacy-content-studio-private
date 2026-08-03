#!/usr/bin/env python3
"""Reject incomplete or slide-like handoff contracts before production starts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[4]
TIMELINE_PATH = ROOT / "microshot-timeline.json"
ASSET_PATH = ROOT / "asset-manifest.json"
VOICE_CONTRACT_PATH = ROOT / "formal-voice-contract.json"
REPORT_PATH = ROOT / "validation-report.json"

BANNED_VALUES = {
    "static_slide",
    "chapter_page",
    "ppt_page",
    "fullpage_card",
    "table_page",
    "whole_frame_push_only",
    "repeated_fullpage_fade",
}
TEXT_ONLY_WORDS = ("title", "text", "subtitle", "caption", "label")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    timeline = json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))
    asset_manifest = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    voice_contract = json.loads(VOICE_CONTRACT_PATH.read_text(encoding="utf-8"))
    chapters = timeline.get("chapters", [])
    assets = {item["id"]: item for item in asset_manifest.get("assets", [])}

    expected_chapters = [f"K{i:02d}" for i in range(1, 19)]
    actual_chapters = [chapter.get("id") for chapter in chapters]
    if actual_chapters != expected_chapters:
        errors.append(f"chapter order must be K01-K18, got {actual_chapters}")

    shot_ids: set[str] = set()
    all_shots: list[tuple[str, dict]] = []
    total_duration = 0.0

    for chapter in chapters:
        chapter_id = chapter.get("id", "UNKNOWN")
        shots = chapter.get("microshots", [])
        if not 2 <= len(shots) <= 6:
            errors.append(f"{chapter_id}: requires 2-6 microshots, got {len(shots)}")

        recipes = {shot.get("recipe_id") for shot in shots}
        focals = {shot.get("focal_subject") for shot in shots}
        if len(shots) >= 3 and len(recipes) == 1 and len(focals) == 1:
            errors.append(f"{chapter_id}: all microshots reuse one recipe and focal subject")

        for shot in shots:
            shot_id = shot.get("id", "MISSING")
            all_shots.append((chapter_id, shot))
            if shot_id in shot_ids:
                errors.append(f"duplicate microshot_id: {shot_id}")
            shot_ids.add(shot_id)

            duration = shot.get("duration_seconds")
            if not isinstance(duration, (int, float)) or not 1.8 <= duration <= 8.0:
                errors.append(f"{shot_id}: duration must be 1.8-8.0 seconds, got {duration}")
            else:
                total_duration += duration

            if shot.get("frame_mode") != "continuous_microshot":
                errors.append(f"{shot_id}: frame_mode must be continuous_microshot")

            serialized = json.dumps(shot, ensure_ascii=False).lower()
            for banned in BANNED_VALUES:
                if banned in serialized:
                    errors.append(f"{shot_id}: contains banned slide pattern {banned}")

            layers = shot.get("layers", [])
            animated = shot.get("animated_nontext_layers", [])
            if len(layers) < 4:
                errors.append(f"{shot_id}: requires at least 4 independent layers")
            if not animated:
                errors.append(f"{shot_id}: requires at least one animated non-text layer")
            for layer in animated:
                if layer not in layers:
                    errors.append(f"{shot_id}: animated layer {layer} is absent from layers")
            if animated and all(any(word in layer.lower() for word in TEXT_ONLY_WORDS) for layer in animated):
                errors.append(f"{shot_id}: animation cannot be text-only")

            for field in (
                "narration_candidate",
                "subtitle",
                "focal_subject",
                "visual_action",
                "entry",
                "performance",
                "exit",
                "camera_motion",
                "transition_to",
            ):
                if not str(shot.get(field, "")).strip():
                    errors.append(f"{shot_id}: missing {field}")

            static_hold = shot.get("static_hold_max_seconds")
            if not isinstance(static_hold, (int, float)) or static_hold > 2.2:
                errors.append(f"{shot_id}: static hold must be <=2.2 seconds")

            for asset_id in shot.get("asset_ids", []):
                if asset_id not in assets:
                    errors.append(f"{shot_id}: unknown asset {asset_id}")

            approval = shot.get("content_approval")
            production_ready = shot.get("production_ready")
            if approval != "approved" and production_ready is not False:
                errors.append(f"{shot_id}: unapproved content cannot be production_ready")
            if shot.get("voice_render_policy") == "allowed-for-k08-pilot" and chapter_id != "K08":
                errors.append(f"{shot_id}: K08 pilot voice policy used outside K08")
            if shot.get("voice_render_policy") != "formal-gold-sample-required":
                errors.append(f"{shot_id}: full gold-sample voice is required")
            if shot.get("gold_sample_voice_ready") is not True:
                errors.append(f"{shot_id}: gold_sample_voice_ready must be true")
            if not str(shot.get("formal_narration", "")).strip():
                errors.append(f"{shot_id}: missing formal_narration")
            if shot.get("formal_subtitle") != shot.get("formal_narration"):
                errors.append(f"{shot_id}: formal subtitle must derive from final narration")

    if not 225 <= total_duration <= 250:
        errors.append(f"total duration must be 225-250 seconds for natural formal narration, got {total_duration:.1f}")

    for index, (_, shot) in enumerate(all_shots):
        expected_transition = "END" if index == len(all_shots) - 1 else all_shots[index + 1][1].get("id")
        if shot.get("transition_to") != expected_transition:
            errors.append(
                f"{shot.get('id')}: transition_to must be {expected_transition}, "
                f"got {shot.get('transition_to')}"
            )

    for asset_id, asset in assets.items():
        path = asset.get("path")
        if path and not (WORKSPACE / path).exists():
            errors.append(f"{asset_id}: declared path does not exist: {path}")
        if asset.get("status") == "authorized-required" and not path:
            warnings.append(f"{asset_id}: waiting for business-authorized source")

    voice_segments = voice_contract.get("segments", [])
    if len(voice_segments) != 18:
        errors.append(f"formal voice contract requires 18 segments, got {len(voice_segments)}")
    covered_voice_shots: list[str] = []
    for segment in voice_segments:
        segment_id = segment.get("segment_id", "VOICE-MISSING")
        microshot_ids = segment.get("microshot_ids", [])
        cues = segment.get("cues", [])
        if not microshot_ids or len(cues) != len(microshot_ids):
            errors.append(f"{segment_id}: cue count must match covered microshots")
        if segment.get("generation_unit") != "one-semantic-chapter-segment":
            errors.append(f"{segment_id}: must be generated as one semantic chapter segment")
        if segment.get("gold_sample_voice_status") != "must-generate-and-accept":
            errors.append(f"{segment_id}: formal voice acceptance is mandatory")
        if not str(segment.get("text", "")).strip():
            errors.append(f"{segment_id}: missing formal voice text")
        covered_voice_shots.extend(microshot_ids)
    ordered_shot_ids = [shot["id"] for _, shot in all_shots]
    if covered_voice_shots != ordered_shot_ids:
        errors.append("formal voice contract must cover every microshot exactly once and in timeline order")

    required_deliverables = set(voice_contract.get("required_deliverables", []))
    for deliverable in {
        "18 chapter WAV files",
        "full narration master WAV",
        "SRT and VTT generated from final authoritative text",
        "voice-sync-map.json with real durations and final placements",
        "loudness-report.json",
        "pronunciation-qa.json",
        "review.html with chapter audition and full-master audition",
    }:
        if deliverable not in required_deliverables:
            errors.append(f"formal voice contract missing deliverable: {deliverable}")

    report = {
        "schema": "kekang-handoff-v2-validation/1.0",
        "passed": not errors,
        "summary": {
            "chapter_count": len(chapters),
            "microshot_count": len(all_shots),
            "total_duration_seconds": round(total_duration, 1),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "formal_voice_segment_count": len(voice_segments),
            "formal_voice_microshot_coverage": len(covered_voice_shots),
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
