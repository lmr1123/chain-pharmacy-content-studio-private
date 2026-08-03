#!/usr/bin/env python3
"""Generate paragraph-level narration for the 28–43.84s mechanism gap."""

import json
import subprocess
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model


MODEL = (
    "/Users/liminrong/.cache/huggingface/hub/"
    "models--mlx-community--Qwen3-TTS-12Hz-0.6B-Base-bf16/"
    "snapshots/1eccf1cb2519b5a4e8a95b5f0544f3303568164f"
)
REF_AUDIO = Path(
    "poc/reference-replica/reference-analysis/audio/reference-clone-prompt.wav"
)
REF_TEXT = (
    "喉咙又肿又痛，咳嗽停不下来。咳出来的痰还黄黄的。"
    "鼻涕又黄又稠，身上发烫。"
)
OUTPUT_DIR = Path(
    "poc/reference-replica/reference-analysis/audio/qwen-clone-mechanism-gap-v1"
)
FINAL_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/qwen-cloned-mechanism-gap-v1.wav"
)
TIMING_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/"
    "qwen-cloned-mechanism-gap-v1-timing.json"
)
TIMELINE_DURATION = 15.84
CROSSFADE_SECONDS = 0.035

BLOCKS = [
    {
        "id": "overview",
        "text": "风热证就是风加热一起入侵身体，风热证并不复杂。",
    },
    {
        "id": "invasion",
        "text": "就是风邪和热邪凑一块，一起钻进咱们身体里了。",
    },
    {
        "id": "result",
        "text": "导致体表不舒服，肺气不顺畅，所以才会出现各种难受的症状。",
    },
]


def atempo_chain(tempo: float) -> str:
    filters = []
    remaining = tempo
    while remaining > 2:
        filters.append("atempo=2")
        remaining /= 2
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.8f}")
    return ",".join(filters)


def process_blocks(
    raw_paths: list[Path],
    tempo: float,
    sample_rate: int,
) -> tuple[np.ndarray, list[dict]]:
    processed = []
    for index, raw in enumerate(raw_paths):
        fitted = OUTPUT_DIR / f"{index:02d}-uniform.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(raw),
                "-af",
                f"{atempo_chain(tempo)},aresample={sample_rate}",
                str(fitted),
            ],
            check=True,
        )
        audio, rate = sf.read(fitted, dtype="float32")
        if rate != sample_rate:
            raise RuntimeError(f"unexpected sample rate: {rate}")
        processed.append(audio)

    crossfade = round(CROSSFADE_SECONDS * sample_rate)
    timeline = processed[0].copy()
    timing = [
        {
            "id": BLOCKS[0]["id"],
            "start": 0.0,
            "end": len(timeline) / sample_rate,
        }
    ]
    fade_in = np.sin(np.linspace(0, np.pi / 2, crossfade)) ** 2
    fade_out = np.cos(np.linspace(0, np.pi / 2, crossfade)) ** 2
    for index, audio in enumerate(processed[1:], start=1):
        overlap = min(crossfade, len(timeline), len(audio))
        start_sample = len(timeline) - overlap
        mixed = (
            timeline[-overlap:] * fade_out[:overlap]
            + audio[:overlap] * fade_in[:overlap]
        )
        timeline = np.concatenate(
            [timeline[:-overlap], mixed, audio[overlap:]]
        )
        timing.append(
            {
                "id": BLOCKS[index]["id"],
                "start": start_sample / sample_rate,
                "end": len(timeline) / sample_rate,
            }
        )
    return timeline.astype(np.float32), timing


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    model = load_model(MODEL)
    sample_rate = model.sample_rate
    raw_paths = []
    raw_durations = []

    for index, block in enumerate(BLOCKS):
        raw = OUTPUT_DIR / f"{index:02d}-raw.wav"
        raw_paths.append(raw)
        if not raw.exists():
            mx.random.seed(20260741 + index)
            result = list(
                model.generate(
                    text=block["text"],
                    ref_audio=str(REF_AUDIO),
                    ref_text=REF_TEXT,
                    lang_code="Chinese",
                    temperature=0.64,
                    top_k=40,
                    top_p=0.94,
                    repetition_penalty=1.05,
                )
            )[0]
            sf.write(
                raw,
                np.asarray(result.audio, dtype=np.float32),
                result.sample_rate,
            )
        audio, rate = sf.read(raw, dtype="float32")
        raw_durations.append(len(audio) / rate)

    desired = (
        TIMELINE_DURATION + CROSSFADE_SECONDS * (len(BLOCKS) - 1)
    )
    tempo = sum(raw_durations) / desired
    timeline, timing = process_blocks(raw_paths, tempo, sample_rate)
    tempo *= (len(timeline) / sample_rate) / TIMELINE_DURATION
    timeline, timing = process_blocks(raw_paths, tempo, sample_rate)

    target_samples = round(TIMELINE_DURATION * sample_rate)
    if len(timeline) < target_samples:
        timeline = np.pad(timeline, (0, target_samples - len(timeline)))
    else:
        timeline = timeline[:target_samples]

    assembled = OUTPUT_DIR / "assembled-before-mastering.wav"
    sf.write(assembled, timeline, sample_rate)
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(assembled),
            "-af",
            (
                "highpass=f=65,lowpass=f=12000,"
                "adeclick=w=55:o=75:a=2:t=2,"
                "loudnorm=I=-16:LRA=6:TP=-1.5,"
                f"aresample={sample_rate},asetpts=PTS-STARTPTS,"
                "apad=whole_dur=15.84"
            ),
            "-t",
            f"{TIMELINE_DURATION:.5f}",
            str(FINAL_OUTPUT),
        ],
        check=True,
    )
    timing[-1]["end"] = TIMELINE_DURATION
    payload = {
        "duration": TIMELINE_DURATION,
        "crossfadeSeconds": CROSSFADE_SECONDS,
        "uniformTempo": tempo,
        "rawDurations": raw_durations,
        "blocks": timing,
    }
    TIMING_OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"saved={FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
