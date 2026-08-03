#!/usr/bin/env python3
"""Generate local Chinese speech from a reference voice using Qwen3-TTS MLX."""

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref-audio", required=True)
    parser.add_argument("--ref-text", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--model",
        default="mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16",
    )
    args = parser.parse_args()

    model = load_model(args.model)
    results = list(
        model.generate(
            text=args.text,
            ref_audio=args.ref_audio,
            ref_text=args.ref_text,
            lang_code="Chinese",
            temperature=0.75,
            top_k=40,
            top_p=0.95,
            repetition_penalty=1.05,
            verbose=True,
        )
    )
    if not results:
        raise RuntimeError("Qwen3-TTS returned no audio")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    audio = np.asarray(results[0].audio, dtype=np.float32)
    sample_rate = getattr(results[0], "sample_rate", model.sample_rate)
    sf.write(output, audio, sample_rate)
    print(f"saved={output} sample_rate={sample_rate} samples={len(audio)}")


if __name__ == "__main__":
    main()
