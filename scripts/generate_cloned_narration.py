#!/usr/bin/env python3
"""Generate and retime the complete reference-style narration locally."""

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
    "poc/reference-replica/reference-analysis/audio/qwen-clone-segments"
)
FINAL_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/qwen-cloned-reference-28s.wav"
)

CUES = [
    (0.00, 4.62, "今天，生灵儿带大家学习中医基础知识——风热证"),
    (4.62, 7.14, "你是不是也有过这种情况？"),
    (7.64, 10.92, "喉咙又肿又痛，咳嗽停不下来"),
    # “谈”是仅供 TTS 使用的同音发音提示；审核稿和字幕仍为“痰”。
    (10.92, 13.14, "咳出来的谈还黄黄的"),
    (13.14, 15.98, "鼻涕又黄又稠，身上发烫"),
    (15.98, 19.82, "越喝水越觉得渴，心里还烦躁得不行"),
    (20.46, 23.50, "其实啊，这就是风热证找上门啦"),
    (23.50, 28.10, "简单来说，风热证就是风加热一起入侵身体"),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    model = load_model(MODEL)
    sample_rate = model.sample_rate
    timeline = np.zeros(round(28.10 * sample_rate), dtype=np.float32)

    for index, (start, end, text) in enumerate(CUES):
        mx.random.seed(20260729 + index)
        result = list(
            model.generate(
                text=text,
                ref_audio=str(REF_AUDIO),
                ref_text=REF_TEXT,
                lang_code="Chinese",
                temperature=0.72,
                top_k=40,
                top_p=0.95,
                repetition_penalty=1.05,
            )
        )[0]
        raw = OUTPUT_DIR / f"{index:02d}-raw.wav"
        fitted = OUTPUT_DIR / f"{index:02d}-fitted.wav"
        audio = np.asarray(result.audio, dtype=np.float32)
        sf.write(raw, audio, result.sample_rate)

        target_duration = end - start
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
