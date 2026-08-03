#!/usr/bin/env python3
"""Generate Dashenlin pharmacist-cloned narration for product-training faithful segment."""

from __future__ import annotations

import subprocess
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

ROOT = Path(__file__).resolve().parents[1]
MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
REF_AUDIO = ROOT / (
    "poc/reference-replica/reference-analysis/audio/reference-clone-prompt.wav"
)
REF_TEXT = (
    "喉咙又肿又痛，咳嗽停不下来。咳出来的痰还黄黄的。"
    "鼻涕又黄又稠，身上发烫。"
)
OUTPUT_DIR = ROOT / (
    "poc/gold-sample/public/product-training-audio/qwen-product-faithful-segments"
)
FINAL_OUTPUT = ROOT / (
    "poc/gold-sample/public/product-training-audio/qwen-cloned-product-faithful-v1.wav"
)
TIMELINE_DURATION = 29.06

# 与 product-training-faithful.json cues 对齐；厂商商品名已中性化
CUES = [
    (0.00, 3.40, "一旦缺乏，心肌细胞能量生产下降"),
    (3.64, 6.54, "可导致收缩力减弱，引发一系列症状"),
    (7.00, 12.12, "如易疲劳、乏力、活动后心慌气短、胸闷、心悸等不适"),
    (12.50, 12.92, "因此"),
    (13.40, 19.48, "它常用于慢性心力衰竭、心肌炎、心绞痛的辅助治疗，以改善心肌代谢"),
    (19.88, 22.24, "辅酶Q10作为常用辅酶制剂"),
    (22.54, 24.18, "直接补充这一关键物质"),
    (24.36, 26.80, "从细胞层面优化心肌能量代谢"),
    (27.12, 28.62, "为心脏健康提供支持"),
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
        if not fitted.exists():
            mx.random.seed(20260730 + index)
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
            audio = np.asarray(result.audio, dtype=np.float32)
            sf.write(raw, audio, result.sample_rate)
            raw_duration = len(audio) / result.sample_rate
            tempo = max(0.5, min(2.0, raw_duration / target_duration))
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
            raise RuntimeError(f"sample rate mismatch: {fitted_rate}")
        if fitted_audio.ndim > 1:
            fitted_audio = fitted_audio.mean(axis=1)
        start_i = round(start * sample_rate)
        end_i = min(len(timeline), start_i + len(fitted_audio))
        chunk = fitted_audio[: end_i - start_i]
        # short crossfade into timeline
        fade = min(int(0.035 * sample_rate), len(chunk) // 4)
        if fade > 0:
            ramp = np.linspace(0, 1, fade, dtype=np.float32)
            chunk = chunk.copy()
            chunk[:fade] *= ramp
            chunk[-fade:] *= ramp[::-1]
        timeline[start_i:end_i] += chunk

    peak = float(np.max(np.abs(timeline)) or 1.0)
    timeline = timeline / peak * 0.95
    sf.write(FINAL_OUTPUT, timeline, sample_rate)
    print(f"wrote {FINAL_OUTPUT} duration={len(timeline)/sample_rate:.2f}s")


if __name__ == "__main__":
    main()
