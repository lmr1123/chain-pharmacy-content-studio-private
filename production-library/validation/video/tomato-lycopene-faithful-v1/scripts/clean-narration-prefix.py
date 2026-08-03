#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
PROJECT_FILE = ROOT / "project.json"
TARGET_STARTS = [2.82, 2.76, 2.90, 3.06, 2.26, 2.16, 2.22, 2.22, 2.30, 2.28]


def split_cues(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[。！？；])", text) if part.strip()]
    cues: list[str] = []
    for part in parts:
        if len(part) <= 30:
            cues.append(part)
            continue
        pieces = [piece for piece in re.split(r"(?<=[，：])", part) if piece]
        buffer = ""
        for piece in pieces:
            if buffer and len(buffer) + len(piece) > 30:
                cues.append(buffer)
                buffer = piece
            else:
                buffer += piece
        if buffer:
            cues.append(buffer)
    return cues


def timestamp(value: float) -> str:
    milliseconds = max(0, round(value * 1000))
    hour, milliseconds = divmod(milliseconds, 3_600_000)
    minute, milliseconds = divmod(milliseconds, 60_000)
    second, milliseconds = divmod(milliseconds, 1000)
    return f"{hour:02d}:{minute:02d}:{second:02d},{milliseconds:03d}"


def read_pcm(path: Path) -> tuple[wave._wave_params, bytes]:
    with wave.open(str(path), "rb") as wav:
        params = wav.getparams()
        return params, wav.readframes(params.nframes)


def write_pcm(path: Path, params: wave._wave_params, frames: bytes) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setparams(params)
        wav.writeframes(frames)


def main() -> None:
    project = json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    source_paths = sorted(AUDIO.glob("[0-9][0-9]-*.wav"))
    if len(source_paths) != len(TARGET_STARTS) or len(source_paths) != len(project["scenes"]):
        raise RuntimeError("Narration segment count does not match the project.")

    clean_frames: list[bytes] = []
    timings: list[dict] = []
    cursor = 0.0
    base_params = None
    for source, start, scene in zip(source_paths, TARGET_STARTS, project["scenes"]):
        params, frames = read_pcm(source)
        if base_params is None:
            base_params = params
        if (params.nchannels, params.sampwidth, params.framerate) != (
            base_params.nchannels,
            base_params.sampwidth,
            base_params.framerate,
        ):
            raise RuntimeError(f"Incompatible WAV format: {source.name}")

        frame_size = params.nchannels * params.sampwidth
        trim_frames = round(start * params.framerate)
        trimmed = frames[trim_frames * frame_size :]
        leading_silence = bytes(round(0.08 * params.framerate) * frame_size)
        cleaned = leading_silence + trimmed
        clean_path = AUDIO / f"clean-{source.name}"
        write_pcm(clean_path, params, cleaned)
        clean_frames.append(cleaned)

        duration = len(cleaned) / frame_size / params.framerate
        scene["duration"] = round(max(duration + 0.32, 5.0), 3)
        timings.append(
            {
                "scene_id": scene["id"],
                "start": round(cursor, 3),
                "end": round(cursor + duration, 3),
                "duration": round(duration, 3),
                "file": clean_path.name,
                "removed_reference_prefix_seconds": start,
            }
        )
        cursor += duration

    assert base_params is not None
    write_pcm(AUDIO / "narration-clean.wav", base_params, b"".join(clean_frames))

    srt: list[str] = []
    number = 1
    for scene, timing in zip(project["scenes"], timings):
        cues = split_cues(scene["narration"])
        total_chars = max(1, sum(len(cue) for cue in cues))
        local = timing["start"]
        for cue in cues:
            cue_duration = max(0.4, (timing["duration"] - 0.1) * len(cue) / total_chars)
            end = min(timing["end"], local + cue_duration)
            srt.extend([str(number), f"{timestamp(local)} --> {timestamp(end)}", cue, ""])
            number += 1
            local = end

    total_duration = len(b"".join(clean_frames)) / (
        base_params.nchannels * base_params.sampwidth * base_params.framerate
    )
    (AUDIO / "narration.srt").write_text("\n".join(srt), encoding="utf-8")
    (AUDIO / "timing.json").write_text(
        json.dumps(
            {"total_duration": round(total_duration, 3), "segments": timings},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    PROJECT_FILE.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audio": str(AUDIO / "narration-clean.wav"), "duration": round(total_duration, 3)}))


if __name__ == "__main__":
    main()
