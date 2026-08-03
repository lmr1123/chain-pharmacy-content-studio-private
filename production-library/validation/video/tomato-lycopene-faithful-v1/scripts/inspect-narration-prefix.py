#!/usr/bin/env python3
import json
from pathlib import Path

import mlx_whisper


ROOT = Path(__file__).resolve().parents[1]
MODEL = "mlx-community/whisper-turbo"


def main():
    results = []
    for wav in sorted((ROOT / "audio").glob("[0-9][0-9]-*.wav")):
        transcript = mlx_whisper.transcribe(
            str(wav),
            path_or_hf_repo=MODEL,
            language="zh",
            verbose=False,
            word_timestamps=True,
        )
        results.append(
            {
                "file": wav.name,
                "text": transcript.get("text", "").strip(),
                "segments": transcript.get("segments", []),
            }
        )
        print(wav.name, results[-1]["text"][:80], flush=True)
    (ROOT / "qa" / "narration-segment-transcripts.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
