#!/usr/bin/env python3
"""Generate smooth paragraph-level narration for the medication/advice replica."""

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
    "poc/reference-replica/reference-analysis/audio/"
    "qwen-clone-medication-advice-smooth-v2"
)
FINAL_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/"
    "qwen-cloned-medication-advice-smooth-v2.wav"
)
TIMING_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/"
    "qwen-cloned-medication-advice-smooth-v2-timing.json"
)
TIMELINE_DURATION = 41.10
CROSSFADE_SECONDS = 0.035

BLOCKS = [
    {
        "id": "medication",
        "text": (
            "也可以搭配银翘解毒颗粒，连花清瘟胶囊来调理，"
            "效果更好哦。"
        ),
        "original": [0.00, 6.44],
    },
    {
        "id": "reminder",
        "text": (
            "另外，风热期间还有几个小细节要注意，"
            "做好了恢复得更快。"
        ),
        "original": [6.44, 12.36],
    },
    {
        "id": "ventilation",
        # “斜”仅作为同音发音提示；字幕仍为“热邪”。
        "text": (
            "一，房间多开窗通风，保持空气流通。别闷着，"
            "闷着热斜更散不出去。"
        ),
        "original": [12.36, 19.22],
    },
    {
        "id": "hydration",
        "text": (
            "二，多喝温水，少量多次喝，及时给身体补水，"
            "缓解口渴和大便干。"
        ),
        "original": [19.22, 26.16],
    },
    {
        "id": "diet",
        "text": (
            "三，饮食一定要清淡，别吃辛辣、油炸的东西，"
            "还有那些容易上火的燥热食物，越吃越严重。"
        ),
        "original": [26.16, 34.72],
    },
    {
        "id": "avoidance",
        "text": (
            "四，暂时把烟酒戒掉，温补类的食物也别碰，"
            "不然会加重体内的热。"
        ),
        "original": [34.72, 41.10],
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
            mx.random.seed(20261110 + index)
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
            sf.write(raw, np.asarray(result.audio, dtype=np.float32), result.sample_rate)
        audio, rate = sf.read(raw, dtype="float32")
        raw_durations.append(len(audio) / rate)

    desired_before_crossfade = (
        TIMELINE_DURATION + CROSSFADE_SECONDS * (len(BLOCKS) - 1)
    )
    tempo = sum(raw_durations) / desired_before_crossfade
    timeline, timing = process_blocks(raw_paths, tempo, sample_rate)
    actual_duration = len(timeline) / sample_rate
    tempo *= actual_duration / TIMELINE_DURATION
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
                f"aresample={sample_rate}"
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
