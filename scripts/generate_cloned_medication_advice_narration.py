#!/usr/bin/env python3
"""Generate reference-style narration for the medication/advice replica."""

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
    "poc/reference-replica/reference-analysis/audio/qwen-clone-medication-advice-segments"
)
FINAL_OUTPUT = Path(
    "poc/gold-sample/public/reference-audio/"
    "qwen-cloned-medication-advice-41s.wav"
)
TIMELINE_DURATION = 41.10

CUES = [
    (0.00, 2.74, "也可以搭配银翘解毒颗粒"),
    (2.74, 4.96, "连花清瘟胶囊来调理"),
    (4.96, 6.44, "效果更好哦"),
    (6.44, 8.42, "另外，风热期间"),
    (8.42, 10.38, "还有几个小细节要注意"),
    (10.38, 12.36, "做好了恢复得更快"),
    (12.36, 14.66, "一，房间多开窗通风"),
    (14.66, 16.10, "保持空气流通"),
    (16.10, 17.02, "别闷着"),
    # “斜”仅作为 TTS 同音发音提示；审核字幕仍为“热邪”。
    (17.02, 19.22, "闷着热斜更散不出去"),
    (19.22, 19.86, "二"),
    (19.86, 21.08, "多喝温水"),
    (21.08, 22.56, "少量多次喝"),
    (22.56, 24.12, "及时给身体补水"),
    (24.12, 26.16, "缓解口渴和大便干"),
    (26.16, 26.74, "三"),
    (26.74, 28.38, "饮食一定要清淡"),
    (28.38, 30.94, "别吃辛辣、油炸的东西"),
    (30.94, 33.44, "还有那些容易上火的燥热食物"),
    (33.44, 34.72, "越吃越严重"),
    (34.72, 37.02, "四，暂时把烟酒戒掉"),
    (37.02, 39.06, "温补类的食物也别碰"),
    (39.06, 41.10, "不然会加重体内的热"),
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
            mx.random.seed(20261020 + index)
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
