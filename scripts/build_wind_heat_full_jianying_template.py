#!/usr/bin/env python3
"""Build the canonical 181.2s wind-heat replica as a versioned Jianying draft."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD_ROOT = PROJECT_ROOT / "poc/gold-sample"
VALIDATION_ROOT = PROJECT_ROOT / "production-library/validation/video"
VECTCUT_ROOT = Path("/Users/liminrong/Projects/VectCutAPI")
VERSION = "1.0.0"
TEMPLATE_NAME = f"风热证-完整视频模板-v{VERSION}"
VERSION_ROOT = (
    PROJECT_ROOT
    / "outputs/jianying-template-versions"
    / "template.health-reference-tech-v1"
    / VERSION
)
JIANYING_ROOT = Path.home() / "Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
CANONICAL_VIDEO = (
    PROJECT_ROOT
    / "production-library/templates/settled/health-video-reference-tech-v1"
    / "wind-heat-reference-full-181s.mp4"
)
CANONICAL_AUDIO = VERSION_ROOT / "风热证-完整旁白.mp3"
WIDTH = 1920
HEIGHT = 1080
FPS = 30
FRAME_COUNT = 5436
DURATION = FRAME_COUNT / FPS

sys.path.insert(0, str(VECTCUT_ROOT))


@dataclass(frozen=True)
class Segment:
    id: str
    name: str
    source: str
    target_start_frame: int
    frame_count: int
    source_start_frame: int = 0
    cue_source: str | None = None

    @property
    def target_start(self) -> float:
        return self.target_start_frame / FPS

    @property
    def duration(self) -> float:
        return self.frame_count / FPS

    @property
    def source_start(self) -> float:
        return self.source_start_frame / FPS


SEGMENTS = [
    Segment("intro", "原生片头", "reference-native-intro.mp4", 0, 136),
    Segment(
        "presenter",
        "数字人导入",
        "reference-character-action-replica.mp4",
        136,
        704,
        136,
        "reference-replica-project.tsx",
    ),
    Segment(
        "mechanism",
        "形成机制",
        "reference-mechanism-gap-replica.mp4",
        840,
        475,
        cue_source="reference-mechanism-gap-project.tsx",
    ),
    Segment(
        "symptoms",
        "典型症状",
        "reference-typical-symptoms-replica.mp4",
        1315,
        790,
        cue_source="reference-symptoms-project.tsx",
    ),
    Segment(
        "treatment",
        "调理方法",
        "reference-treatment-replica.mp4",
        2105,
        1258,
        cue_source="reference-treatment-project.tsx",
    ),
    Segment(
        "medication_advice",
        "药物与生活建议",
        "reference-medication-advice-replica.mp4",
        3363,
        1233,
        cue_source="reference-medication-advice-project.tsx",
    ),
    Segment(
        "summary_outro",
        "总结与片尾",
        "reference-summary-outro-replica.mp4",
        4596,
        840,
        cue_source="reference-summary-outro-project.tsx",
    ),
]


def require_files(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing canonical inputs:\n" + "\n".join(missing))


def extract_cues() -> list[dict[str, object]]:
    pattern = re.compile(
        r"\{\s*start:\s*([0-9.]+),\s*end:\s*([0-9.]+),"
        r"\s*text:\s*'([^']*)',?\s*\}",
        re.DOTALL,
    )
    cues: list[dict[str, object]] = []
    for segment in SEGMENTS:
        if not segment.cue_source:
            continue
        source = (GOLD_ROOT / "src" / segment.cue_source).read_text(encoding="utf-8")
        for start, end, text in pattern.findall(source):
            source_start = max(float(start), segment.source_start)
            source_end = min(float(end), segment.source_start + segment.duration)
            cue_start = segment.target_start + source_start - segment.source_start
            cue_end = segment.target_start + source_end - segment.source_start
            if cue_end - cue_start < 0.2:
                continue
            cues.append(
                {
                    "segment_id": segment.id,
                    "start": round(cue_start, 3),
                    "end": round(cue_end, 3),
                    "text": text,
                }
            )
    return cues


def srt_stamp(value: float) -> str:
    milliseconds = round(value * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def write_srt(cues: list[dict[str, object]]) -> Path:
    target = VERSION_ROOT / "风热证-完整字幕.srt"
    blocks = [
        (
            f"{index}\n{srt_stamp(float(cue['start']))} --> "
            f"{srt_stamp(float(cue['end']))}\n{cue['text']}\n"
        )
        for index, cue in enumerate(cues, start=1)
    ]
    target.write_text("\n".join(blocks), encoding="utf-8")
    return target


def extract_audio() -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(CANONICAL_VIDEO),
            "-vn",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(CANONICAL_AUDIO),
        ],
        check=True,
    )


def rewrite_draft_paths(draft_dir: Path) -> int:
    info_path = draft_dir / "draft_info.json"
    data = json.loads(info_path.read_text(encoding="utf-8"))
    data["name"] = TEMPLATE_NAME
    count = 0
    for material_type, subdir, name_field in (
        ("videos", "video", "material_name"),
        ("images", "image", "material_name"),
        ("audios", "audio", "name"),
    ):
        for material in data.get("materials", {}).get(material_type, []) or []:
            filename = material.get(name_field)
            if not filename:
                continue
            local_path = str(draft_dir / "assets" / subdir / filename)
            material["path"] = local_path
            if "media_path" in material:
                material["media_path"] = local_path
            count += 1
    info_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    meta_path = draft_dir / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["draft_name"] = TEMPLATE_NAME
    meta["draft_fold_path"] = str(draft_dir)
    meta["draft_root_path"] = str(draft_dir.parent)
    meta["tm_duration"] = round(DURATION * 1_000_000)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return count


def jianying_running() -> bool:
    return any(
        subprocess.run(
            ["pgrep", "-x", process_name],
            capture_output=True,
            check=False,
        ).returncode
        == 0
        for process_name in ("JianyingPro", "VideoFusion-macOS")
    )


def write_json_atomic(path: Path, data: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    temporary.replace(path)


def draft_store_entry(draft_dir: Path) -> dict[str, object]:
    meta = json.loads((draft_dir / "draft_meta_info.json").read_text(encoding="utf-8"))
    return {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "draft_cloud_last_action_download": False,
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": str(draft_dir / "draft_cover.jpg"),
        "draft_fold_path": str(draft_dir),
        "draft_id": meta["draft_id"],
        "draft_is_ai_shorts": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_invisible": False,
        "draft_is_pippit_draft": False,
        "draft_is_web_article_video": False,
        "draft_json_file": str(draft_dir / "draft_info.json"),
        "draft_name": TEMPLATE_NAME,
        "draft_new_version": "",
        "draft_root_path": str(JIANYING_ROOT),
        "draft_timeline_materials_size": meta.get("draft_timeline_materials_size_", 0),
        "draft_type": "",
        "draft_web_article_video_enter_from": "",
        "pippit_avatar_url": "",
        "pippit_extra_info": "",
        "pippit_id": "",
        "pippit_user_name": "",
        "streaming_edit_draft_ready": True,
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": meta["tm_draft_create"],
        "tm_draft_modified": meta["tm_draft_modified"],
        "tm_draft_removed": 0,
        "tm_duration": meta["tm_duration"],
    }


def install_jianying_draft(version_draft: Path) -> Path:
    if jianying_running():
        raise RuntimeError("Quit Jianying before installing the draft.")
    target = JIANYING_ROOT / TEMPLATE_NAME
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(version_draft, target)
    rewrite_draft_paths(target)

    root_meta_path = JIANYING_ROOT / "root_meta_info.json"
    root_meta = json.loads(root_meta_path.read_text(encoding="utf-8"))
    draft_id = draft_store_entry(target)["draft_id"]
    root_meta["all_draft_store"] = [
        item
        for item in root_meta.get("all_draft_store", [])
        if item.get("draft_id") != draft_id and item.get("draft_name") != TEMPLATE_NAME
    ]
    root_meta["all_draft_store"].append(draft_store_entry(target))
    write_json_atomic(root_meta_path, root_meta)

    recycle_root = JIANYING_ROOT / ".recycle_bin"
    recycle_meta_path = recycle_root / "root_meta_info.json"
    if recycle_meta_path.is_file():
        recycle_meta = json.loads(recycle_meta_path.read_text(encoding="utf-8"))
        recycle_meta["all_draft_store"] = [
            item
            for item in recycle_meta.get("all_draft_store", [])
            if item.get("draft_id") != draft_id and item.get("draft_name") != TEMPLATE_NAME
        ]
        write_json_atomic(recycle_meta_path, recycle_meta)
    recycled_target = recycle_root / TEMPLATE_NAME
    if recycled_target.exists():
        shutil.rmtree(recycled_target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--install-existing",
        action="store_true",
        help="Install the existing versioned draft and register it in Jianying.",
    )
    args = parser.parse_args()
    if args.install_existing:
        existing = next(VERSION_ROOT.glob("dfd_*"), None)
        if not existing:
            raise FileNotFoundError(f"No versioned draft under {VERSION_ROOT}")
        print(install_jianying_draft(existing))
        return

    from add_audio_track import add_audio_track
    from add_text_impl import add_text_impl
    from add_video_track import add_video_track
    from create_draft import create_draft
    from save_draft_impl import save_draft_impl

    sources = [VALIDATION_ROOT / segment.source for segment in SEGMENTS]
    require_files([CANONICAL_VIDEO, *sources])
    VERSION_ROOT.mkdir(parents=True, exist_ok=True)
    extract_audio()
    cues = extract_cues()
    srt_path = write_srt(cues)

    before = {path for path in VECTCUT_ROOT.glob("dfd_*") if path.is_dir()}
    _script, draft_id = create_draft(WIDTH, HEIGHT)

    for index, segment in enumerate(SEGMENTS, start=1):
        add_video_track(
            video_url=str(VALIDATION_ROOT / segment.source),
            draft_id=draft_id,
            width=WIDTH,
            height=HEIGHT,
            start=segment.source_start,
            end=segment.source_start + segment.duration,
            target_start=segment.target_start,
            duration=segment.source_start + segment.duration,
            volume=0,
            track_name=f"{index:02d}-Revideo保真-{segment.name}",
            relative_index=index,
        )

    add_audio_track(
        audio_url=str(CANONICAL_AUDIO),
        draft_id=draft_id,
        start=0,
        end=DURATION,
        target_start=0,
        duration=DURATION,
        volume=1,
        track_name="完整旁白",
        width=WIDTH,
        height=HEIGHT,
    )

    for cue in cues:
        add_text_impl(
            text=str(cue["text"]),
            start=float(cue["start"]),
            end=float(cue["end"]),
            draft_id=draft_id,
            transform_x=0,
            transform_y=-0.79,
            font_color="#FFFFFF",
            font_size=9,
            track_name="可编辑字幕",
            border_width=0.06,
            border_color="#00101C",
            background_color="#071B2C",
            background_alpha=0.96,
            background_round_radius=0.12,
            background_height=0.15,
            background_width=0.82,
            shadow_enabled=False,
            fixed_width=0.78,
            width=WIDTH,
            height=HEIGHT,
        )

    result = save_draft_impl(draft_id)
    if not result.get("success"):
        raise RuntimeError(f"save_draft failed: {result}")

    after = {path for path in VECTCUT_ROOT.glob("dfd_*") if path.is_dir()}
    created = sorted(after - before, key=lambda path: path.stat().st_mtime)
    if len(created) != 1:
        raise RuntimeError(f"Expected one new draft, got: {[str(path) for path in created]}")
    source_draft = created[0]

    for previous in VERSION_ROOT.glob("dfd_*"):
        if previous.is_dir():
            shutil.rmtree(previous)
    version_draft = VERSION_ROOT / draft_id
    shutil.copytree(source_draft, version_draft)
    rewritten = rewrite_draft_paths(version_draft)

    jianying_target = None
    if JIANYING_ROOT.is_dir() and not jianying_running():
        jianying_target = install_jianying_draft(version_draft)

    manifest = {
        "version_id": f"template.health-reference-tech-v1@{VERSION}-jianying",
        "status": "draft-structure-qa-pending-business-editability-limited",
        "created_at": datetime.now().astimezone().isoformat(),
        "template_id": "template.health-reference-tech-v1",
        "style_pack_id": "style-pack.reference-medical-tech-v1",
        "theme_id": "theme.disease.wind-heat",
        "source_content": "samples/health-training-script/风热证视频培训_业务填写真实样本.json",
        "canonical_video": str(CANONICAL_VIDEO.relative_to(PROJECT_ROOT)),
        "assembly_contract": "production-library/examples/wind-heat-full-frame-assembly.json",
        "draft_id": draft_id,
        "draft_name": TEMPLATE_NAME,
        "project_draft": str(version_draft),
        "jianying_draft": str(jianying_target) if jianying_target else None,
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "frame_count": FRAME_COUNT,
        "duration": DURATION,
        "segments": [
            {
                "id": segment.id,
                "name": segment.name,
                "source": f"production-library/validation/video/{segment.source}",
                "start": segment.target_start,
                "duration": segment.duration,
                "track": f"{index:02d}-Revideo保真-{segment.name}",
            }
            for index, segment in enumerate(SEGMENTS, start=1)
        ],
        "subtitle_file": str(srt_path),
        "subtitle_count": len(cues),
        "self_contained_asset_paths_rewritten": rewritten,
        "editable_boundary": {
            "native": [
                "seven scene clips: reorder, trim, split, replace, transform",
                "complete narration audio",
                "individual subtitle cues",
                "Jianying-native effects, transitions and keyframes added after import",
            ],
            "baked_in_revideo_clips": [
                "presenter rig and mouth animation",
                "scene-internal text and illustration layers",
                "particle/current effects and programmatic motion",
            ],
        },
        "promotion": {
            "jianying_roundtrip_status": "pending-manual-open-edit-save-reopen",
            "business_editability_status": "scene-clips-only-not-fully-layered",
            "formal_template_status": "unchanged-production-validated",
            "rule": "This delivery is limited to scene-level finishing unless the presenter, illustrations, text and components are proven as independent Jianying objects.",
        },
    }
    (VERSION_ROOT / "version.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    shutil.rmtree(source_draft)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
