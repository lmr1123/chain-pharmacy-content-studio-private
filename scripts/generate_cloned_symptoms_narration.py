#!/usr/bin/env python3
"""Generate the reference-style narration for the typical-symptoms sample."""

import subprocess
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model


MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
REF_AUDIO = Path(
    "poc/reference-replica/reference-analysis/audio/reference-clone-prompt.wav"
)
REF_TEXT = (
    "喉咙又肿又痛，咳嗽停不下来。咳出来的痰还黄黄的。"
    "鼻涕又黄又稠，身上发烫。"
)
OUTPUT_DIR = Path(
    "poc/reference-replica/reference-analysis/audio/qwen-clone-symptoms-segments"
)
FINAL_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/qwen-cloned-symptoms-27s.wav"
)
TIMELINE_DURATION = 27.50

CUES = [
    (0.00, 2.08, "它有三个典型信号"),
    (2.08, 3.42, "记好这几点"),
    (3.42, 4.48, "一看就懂"),
    (4.48, 7.60, "一，发热、口渴、嘴巴干"),
    (7.60, 8.74, "心里烦躁"),
    # “谈”仅作为 TTS 同音发音提示；画面审核稿仍为“痰黄”。
    (8.74, 12.16, "二，喉咙肿痛、咳嗽、谈黄"),
    (12.16, 13.66, "鼻涕又黄又稠"),
    (13.66, 15.56, "三，舌头偏红"),
    (15.56, 17.16, "舌苔微微发黄"),
    (17.16, 18.22, "大便干结"),
    (18.22, 20.10, "只要你出现这些情况"),
    (20.10, 22.22, "基本就是风热证没跑了"),
    (22.22, 23.64, "对付风热证"),
    (23.64, 25.08, "记住一个核心"),
    # “青”用于稳定 qing 音；审核字幕仍为“疏风清热”。
    (25.08, 26.10, "疏风青热"),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    model = load_model(MODEL)
    sample_rate = model.sample_rate
    timeline = np.zeros(round(TIMELINE_DURATION * sample_rate), dtype=np.float32)

    for index, (start, end, text) in enumerate(CUES):
        raw = OUTPUT_DIR / f"{index:02d}-raw.wav"
        fitted = OUTPUT_DIR / f"{index:02d}-fitted.wav"
        target_duration = end - start
        if fitted.exists():
            raw_audio, raw_rate = sf.read(raw, dtype="float32")
            raw_duration = len(raw_audio) / raw_rate
            tempo = raw_duration / target_duration
        else:
            mx.random.seed(20260914 if index == 14 else 20260750 + index)
            result = list(
                model.generate(
                    text=text,
                    ref_audio=str(REF_AUDIO),
                    ref_text=REF_TEXT,
                    lang_code="Chinese",
                    temperature=0.55 if index == 14 else 0.72,
                    top_k=40,
                    top_p=0.95,
                    repetition_penalty=1.05,
                )
            )[0]
            audio = np.asarray(result.audio, dtype=np.float32)
            sf.write(raw, audio, result.sample_rate)
            raw_duration = len(audio) / result.sample_rate
            tempo = raw_duration / target_duration
            subprocess.run(
                [
                    "ffmpeg",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(raw),
                    "-af",
                    f"atempo={tempo:.8f},aresample={sample_rate}",
                    "-t",
                    f"{target_duration:.5f}",
                    str(fitted),
                ],
                check=True,
            )
        fitted_audio, fitted_rate = sf.read(fitted, dtype="float32")
        if fitted_rate != sample_rate:
            raise RuntimeError(f"unexpected sample rate: {fitted_rate}")
        begin = round(start * sample_rate)
        available = min(len(fitted_audio), len(timeline) - begin)
        timeline[begin : begin + available] = fitted_audio[:available]
        print(
            f"cue={index} raw={raw_duration:.3f}s "
            f"target={target_duration:.3f}s tempo={tempo:.4f}"
        )

    peak = max(float(np.max(np.abs(timeline))), 1e-6)
    timeline *= min(10 ** (-0.5 / 20) / peak, 2.0)
    sf.write(FINAL_OUTPUT, timeline, sample_rate)
    print(f"saved={FINAL_OUTPUT} duration={len(timeline) / sample_rate:.3f}s")


if __name__ == "__main__":
    main()
