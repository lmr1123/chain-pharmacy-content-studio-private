#!/usr/bin/env python3
"""Generate the 30-second product-training template signoff narration locally."""

import json
import subprocess
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model


MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
DATA_FILE = Path("poc/gold-sample/product-training-signoff.json")
REF_AUDIO = Path(
    "poc/reference-replica/reference-analysis/audio/reference-clone-prompt.wav"
)
REF_TEXT = (
    "喉咙又肿又痛，咳嗽停不下来。咳出来的痰还黄黄的。"
    "鼻涕又黄又稠，身上发烫。"
)
SEGMENT_DIR = Path("poc/product-training-signoff/audio")
FINAL_OUTPUT = Path(
    "poc/gold-sample/public/product-training-audio/"
    "product-training-signoff-30s.wav"
)
DURATION = 30.0


def main() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    cues = data["cues"]
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    model = load_model(MODEL)
    sample_rate = model.sample_rate
    timeline = np.zeros(round(DURATION * sample_rate), dtype=np.float32)

    for index, cue in enumerate(cues):
        start = float(cue["start"])
        end = float(cue.get("ttsEnd", cue["end"]))
        text = str(cue.get("ttsText", cue["text"]))
        mx.random.seed(20260729 + 100 + index)
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

        raw = SEGMENT_DIR / f"{index:02d}-raw.wav"
        fitted = SEGMENT_DIR / f"{index:02d}-fitted.wav"
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
    timeline *= min(10 ** (-0.8 / 20) / peak, 2.0)
    sf.write(FINAL_OUTPUT, timeline, sample_rate)
    print(f"saved={FINAL_OUTPUT} duration={len(timeline) / sample_rate:.3f}s")


if __name__ == "__main__":
    main()
