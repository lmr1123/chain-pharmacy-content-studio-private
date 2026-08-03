#!/usr/bin/env python3
"""Generate reference-style narration for the treatment replica segment."""

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
    "poc/reference-replica/reference-analysis/audio/qwen-clone-treatment-segments"
)
FINAL_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/qwen-cloned-treatment-41s.wav"
)
TIMELINE_DURATION = 41.94

CUES = [
    (0.00, 2.44, "就是把身体里的风散出去"),
    (2.44, 3.66, "把热清掉"),
    (3.66, 6.40, "不舒服的感觉自然就缓解了"),
    (6.40, 8.72, "日常生活中有这几样"),
    (8.72, 10.74, "用来调理特别方便"),
    (10.74, 11.50, "记好了"),
    (11.50, 13.02, "一，桑叶"),
    (13.02, 14.18, "能散风热"),
    (14.18, 15.72, "还能滋润肺部"),
    (15.72, 16.84, "缓解咳嗽"),
    (16.84, 18.16, "二，菊花"),
    (18.16, 19.64, "不仅能散风热"),
    (19.64, 21.14, "还能清热解毒"),
    (21.14, 23.26, "平时泡着喝也舒服"),
    (23.26, 24.60, "三，薄荷"),
    (24.60, 26.68, "散风热的效果特别快"),
    (26.68, 28.10, "还能清头目"),
    (28.10, 29.32, "缓解喉咙痛"),
    (29.32, 30.78, "平常在家时"),
    (30.78, 34.22, "用桑叶、菊花、薄荷各三至五克"),
    (34.22, 35.52, "泡一杯水喝"),
    (35.52, 38.56, "就是简单又管用的桑菊薄荷饮"),
    (38.56, 39.86, "喝一至两天"),
    (39.86, 41.94, "就能感觉到舒服不少"),
]


def fit_audio(source: Path, target: Path, duration: float, sample_rate: int) -> float:
    audio, rate = sf.read(source, dtype="float32")
    raw_duration = len(audio) / rate
    tempo = raw_duration / duration
    filters = []
    remaining = tempo
    while remaining > 2:
        filters.append("atempo=2")
        remaining /= 2
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.extend([f"atempo={remaining:.8f}", f"aresample={sample_rate}"])
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-af",
            ",".join(filters),
            "-t",
            f"{duration:.5f}",
            str(target),
        ],
        check=True,
    )
    return raw_duration


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
        if not raw.exists():
            mx.random.seed(20260991 if index == 1 else 20260790 + index)
            result = list(
                model.generate(
                    text=text,
                    ref_audio=str(REF_AUDIO),
                    ref_text=REF_TEXT,
                    lang_code="Chinese",
                    temperature=0.68,
                    top_k=40,
                    top_p=0.95,
                    repetition_penalty=1.05,
                )
            )[0]
            sf.write(raw, np.asarray(result.audio, dtype=np.float32), result.sample_rate)
        raw_duration = fit_audio(raw, fitted, target_duration, sample_rate)
        fitted_audio, fitted_rate = sf.read(fitted, dtype="float32")
        if fitted_rate != sample_rate:
            raise RuntimeError(f"unexpected sample rate: {fitted_rate}")
        begin = round(start * sample_rate)
        available = min(len(fitted_audio), len(timeline) - begin)
        timeline[begin : begin + available] = fitted_audio[:available]
        print(
            f"cue={index} raw={raw_duration:.3f}s "
            f"target={target_duration:.3f}s"
        )

    peak = max(float(np.max(np.abs(timeline))), 1e-6)
    timeline *= min(10 ** (-0.5 / 20) / peak, 2.0)
    sf.write(FINAL_OUTPUT, timeline, sample_rate)
    print(f"saved={FINAL_OUTPUT} duration={len(timeline) / sample_rate:.3f}s")


if __name__ == "__main__":
    main()
