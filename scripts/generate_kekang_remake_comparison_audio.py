#!/usr/bin/env python3
"""Generate formal narration and restrained SFX for K03/K13 remake comparisons."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_cloned_product_all_narration import (  # noqa: E402
    MODEL,
    build_natural_timeline,
    load_model,
)
from generate_kekang_k08_audiovisual_audio import (  # noqa: E402
    SAMPLE_RATE,
    measure_lufs,
    normalize_to_lufs,
    place,
    synth_ambient_bed,
    synth_focus_pulse,
    synth_line_sweep,
    synth_point,
    synth_whoosh,
    write_wav,
)


OUT = ROOT / (
    "production-library/validation/reference-analysis/kekang-pfizer-framework-v1/"
    "production-v2/qa/remake-comparison-v1"
)
PUBLIC = ROOT / "poc/gold-sample/public/kekang-remake-v1"
SOURCE_TIMING = ROOT / "poc/gold-sample/kekang-remake-v1-timing.json"
SEG_ROOT = OUT / "audio/segments"

SEGMENTS = {
    "k03": [
        "失眠常见的表现，包括入睡困难。",
        "夜里可能反复醒来、早醒，醒后难以再次入睡。",
        "到了第二天，也容易感到疲倦，影响精神状态。",
    ],
    "k13": [
        "第二项产品特点，是双重提取工艺。",
        "原料经过第一次提取后，再进入第二次浓缩提取。",
        "经过两次提取，原料逐步浓缩，最终形成胶囊。",
    ],
    "k16": [
        "如果晚上睡不着、夜里容易醒，",
        "可以了解谷维素片和灵芝胶囊这组搭配。",
        "需要关注肝脏健康时，",
        "可以了解护肝片和灵芝胶囊这组搭配。",
        "如果平时容易反复不舒服、抵抗力比较弱，",
        "可以了解转移因子口服溶液和灵芝胶囊这组搭配。",
    ],
}


def build_mix(key: str, narration: np.ndarray, cues: list[dict], duration: float) -> np.ndarray:
    n = int(round(duration * SAMPLE_RATE))
    bus = np.zeros(n, dtype=np.float32)
    bed = synth_ambient_bed(duration)
    place(bus, bed, 0, SAMPLE_RATE, 0.72)
    place(bus, narration, 0, SAMPLE_RATE, 1.0)
    place(bus, synth_whoosh(0.48), max(0.02, cues[0]["start"] - 0.05), SAMPLE_RATE, 0.45)
    for index, cue in enumerate(cues):
        if key in {"k13", "k16"}:
            place(bus, synth_line_sweep(0.34), cue["start"] + 0.08, SAMPLE_RATE, 0.32)
            place(bus, synth_point(760 - index * 80, 0.14), cue["end"] - 0.12, SAMPLE_RATE, 0.38)
        else:
            place(bus, synth_focus_pulse(620 - index * 70, 0.13), cue["start"] + 0.12, SAMPLE_RATE, 0.32)
    return normalize_to_lufs(bus, SAMPLE_RATE, -16.0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    SEG_ROOT.mkdir(parents=True, exist_ok=True)
    model = load_model(MODEL)
    report_path = OUT / "audio/audio-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    else:
        report = {
            "voice_id": "voice.reference-pharmacist-qwen-v1",
            "generation_mode": "one-complete-semantic-segment-per-remake",
            "segments": {},
        }
    selected = sys.argv[1:] or list(SEGMENTS)
    unknown = [key for key in selected if key not in SEGMENTS]
    if unknown:
        raise SystemExit(f"unknown segment(s): {', '.join(unknown)}")
    for key in selected:
        texts = SEGMENTS[key]
        seg_dir = SEG_ROOT / key
        if seg_dir.exists():
            shutil.rmtree(seg_dir)
        seg_dir.mkdir(parents=True, exist_ok=True)
        cues = [{"text": text} for text in texts]
        narration, timed_cues, pace_reports = build_natural_timeline(
            model, model.sample_rate, cues, seg_dir
        )
        native_path = OUT / f"audio/{key}-narration-native.wav"
        native_path.parent.mkdir(parents=True, exist_ok=True)
        write_wav(native_path, narration, model.sample_rate)
        narration_48 = OUT / f"audio/{key}-narration-48k.wav"
        if model.sample_rate != SAMPLE_RATE:
            import subprocess

            subprocess.run(
                [
                    "ffmpeg", "-loglevel", "error", "-y", "-i", str(native_path),
                    "-ar", str(SAMPLE_RATE), str(narration_48),
                ],
                check=True,
            )
            import soundfile as sf

            narration, _ = sf.read(narration_48, dtype="float32")
            if narration.ndim > 1:
                narration = narration.mean(axis=1)
        else:
            shutil.copy2(native_path, narration_48)
        speech_end = timed_cues[-1]["end"]
        duration = round(speech_end + 1.15, 3)
        mix = build_mix(key, narration.astype(np.float32), timed_cues, duration)
        mix_path = OUT / f"audio/{key}-mix-final.wav"
        write_wav(mix_path, mix, SAMPLE_RATE)
        shutil.copy2(mix_path, PUBLIC / f"{key}-mix-final.wav")
        report["segments"][key] = {
            "texts": texts,
            "cues": timed_cues,
            "duration_seconds": duration,
            "pace_reports": pace_reports,
            "mix_file": str(mix_path.relative_to(ROOT)),
            "mix_metrics": measure_lufs(mix_path),
        }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    timing_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (PUBLIC / "timing.json").write_text(timing_json, encoding="utf-8")
    SOURCE_TIMING.write_text(timing_json, encoding="utf-8")
    print(json.dumps({k: report["segments"][k]["duration_seconds"] for k in selected}))


if __name__ == "__main__":
    main()
