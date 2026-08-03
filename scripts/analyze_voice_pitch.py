#!/usr/bin/env python3
"""Estimate voiced fundamental-frequency statistics from a mono PCM WAV."""

import sys
import wave

import numpy as np


def main(path: str) -> None:
    with wave.open(path, "rb") as wav:
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")

    samples = samples.reshape(-1, channels).mean(axis=1) / 32768.0
    frame_size = int(sample_rate * 0.04)
    hop = int(sample_rate * 0.01)
    minimum_lag = sample_rate // 400
    maximum_lag = sample_rate // 80
    pitches = []

    for start in range(0, len(samples) - frame_size, hop):
        frame = samples[start : start + frame_size]
        frame = frame - frame.mean()
        if np.sqrt(np.mean(frame * frame)) < 0.015:
            continue
        correlation = np.correlate(frame, frame, mode="full")[frame_size - 1 :]
        correlation /= max(correlation[0], 1e-9)
        local = correlation[minimum_lag:maximum_lag]
        lag = minimum_lag + int(np.argmax(local))
        if correlation[lag] >= 0.3:
            pitches.append(sample_rate / lag)

    if not pitches:
        raise SystemExit("no voiced frames detected")
    values = np.asarray(pitches)
    print(
        f"voiced_frames={len(values)} "
        f"f0_median_hz={np.median(values):.1f} "
        f"f0_p10_hz={np.percentile(values, 10):.1f} "
        f"f0_p90_hz={np.percentile(values, 90):.1f}"
    )


if __name__ == "__main__":
    main(sys.argv[1])
