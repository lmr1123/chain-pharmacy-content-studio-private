#!/usr/bin/env python3
"""Generate K08 audiovisual narration + action SFX + final mix.

Outputs land in production-v1/audio and are mirrored into
poc/gold-sample/public/kekang-k08-av/ for Revideo rendering.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_cloned_product_all_narration import (  # noqa: E402
    DEFAULT_TEMPO,
    LEAD_IN,
    LEAD_OUT,
    MAX_TEMPO,
    MODEL,
    build_natural_timeline,
    load_model,
)

GOLD = ROOT / "poc/gold-sample"
JSON_PATH = GOLD / "kekang-pfizer-k08-audiovisual.json"
PROD = (
    ROOT
    / "production-library/validation/reference-analysis"
    / "kekang-pfizer-framework-v1/production-v1"
)
NARR_DIR = PROD / "audio/narration"
SFX_DIR = PROD / "audio/sfx"
MIX_DIR = PROD / "audio"
REPORT_DIR = PROD / "audio/mix-reports"
PUBLIC = GOLD / "public/kekang-k08-av"
SAMPLE_RATE = 48000
TARGET_LUFS = -16.0
TRUE_PEAK_LIMIT = 10 ** (-1.0 / 20.0)  # -1 dBTP linear approx


def ensure_dirs() -> None:
    for d in (NARR_DIR, SFX_DIR, MIX_DIR, REPORT_DIR, PUBLIC, NARR_DIR / "segments"):
        d.mkdir(parents=True, exist_ok=True)


def write_wav(path: Path, audio: np.ndarray, sr: int = SAMPLE_RATE) -> None:
    peak = float(np.max(np.abs(audio)) or 1.0)
    if peak > 0.99:
        audio = audio / peak * 0.98
    sf.write(path, audio.astype(np.float32), sr)


def fade(audio: np.ndarray, sr: int, fade_in: float = 0.0, fade_out: float = 0.0) -> np.ndarray:
    out = audio.astype(np.float32).copy()
    if fade_in > 0:
        n = min(len(out), int(round(fade_in * sr)))
        if n > 0:
            out[:n] *= np.linspace(0.0, 1.0, n, dtype=np.float32)
    if fade_out > 0:
        n = min(len(out), int(round(fade_out * sr)))
        if n > 0:
            out[-n:] *= np.linspace(1.0, 0.0, n, dtype=np.float32)
    return out


def synth_whoosh(duration: float = 0.55, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(round(duration * sr))
    t = np.arange(n, dtype=np.float32) / sr
    # Band-limited noise with rising low-pass feel via amplitude envelope.
    rng = np.random.default_rng(20260801)
    noise = rng.standard_normal(n).astype(np.float32)
    # Simple one-pole lowpass with rising cutoff via gain envelope.
    y = np.zeros(n, dtype=np.float32)
    state = 0.0
    for i in range(n):
        cutoff = 0.08 + 0.55 * (i / max(1, n - 1))
        state = state + cutoff * (noise[i] - state)
        y[i] = state
    env = np.sin(np.pi * np.clip(t / duration, 0, 1)) ** 1.4
    # Mild rising pitch of a soft sine layer.
    freq = 220 + 280 * (t / duration)
    tone = 0.18 * np.sin(2 * np.pi * np.cumsum(freq) / sr).astype(np.float32)
    out = (0.55 * y + tone) * env * 0.22
    return fade(out, sr, 0.02, 0.12)


def synth_air_ring(duration: float = 0.45, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(round(duration * sr))
    t = np.arange(n, dtype=np.float32) / sr
    env = np.exp(-t * 4.2) * (1 - np.exp(-t * 28))
    a = 0.09 * np.sin(2 * np.pi * 480 * t)
    b = 0.05 * np.sin(2 * np.pi * 720 * t + 0.4)
    return fade((a + b).astype(np.float32) * env.astype(np.float32), sr, 0.01, 0.08)


def synth_line_sweep(duration: float = 0.38, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(round(duration * sr))
    t = np.arange(n, dtype=np.float32) / sr
    freq = 520 + 900 * (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    tone = np.sin(phase).astype(np.float32)
    env = (np.sin(np.pi * t / duration) ** 1.1).astype(np.float32)
    noise = np.random.default_rng(11).standard_normal(n).astype(np.float32) * 0.08
    return fade((0.14 * tone + 0.05 * noise) * env, sr, 0.01, 0.06)


def synth_point(freq: float = 880.0, duration: float = 0.16, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(round(duration * sr))
    t = np.arange(n, dtype=np.float32) / sr
    env = np.exp(-t * 18.0) * (1 - np.exp(-t * 90))
    body = np.sin(2 * np.pi * freq * t)
    glass = 0.35 * np.sin(2 * np.pi * freq * 2.05 * t + 0.2)
    wood = 0.18 * np.sin(2 * np.pi * (freq * 0.5) * t)
    return fade((0.22 * (body + glass + wood) * env).astype(np.float32), sr, 0.002, 0.04)


def synth_focus_pulse(freq: float = 660.0, duration: float = 0.14, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(round(duration * sr))
    t = np.arange(n, dtype=np.float32) / sr
    env = np.exp(-t * 14.0) * (1 - np.exp(-t * 70))
    body = np.sin(2 * np.pi * freq * t) * 0.12
    return fade((body * env).astype(np.float32), sr, 0.002, 0.03)


def synth_ambient_bed(duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    n = int(round(duration * sr))
    t = np.arange(n, dtype=np.float32) / sr
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n).astype(np.float32)
    # very soft filtered noise
    y = np.zeros(n, dtype=np.float32)
    state = 0.0
    for i in range(n):
        state = state + 0.02 * (noise[i] - state)
        y[i] = state
    pad = 0.035 * np.sin(2 * np.pi * 110 * t) + 0.02 * np.sin(2 * np.pi * 164 * t + 0.3)
    out = (0.035 * y + 0.012 * pad).astype(np.float32)
    return fade(out, sr, 0.12, 0.25)


def place(timeline: np.ndarray, clip: np.ndarray, start_s: float, sr: int, gain: float = 1.0) -> None:
    start = int(round(start_s * sr))
    if start >= len(timeline):
        return
    end = min(len(timeline), start + len(clip))
    n = end - start
    if n <= 0:
        return
    timeline[start:end] += clip[:n] * gain


def measure_lufs(path: Path) -> dict:
    """Use ffmpeg ebur128 if available."""
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-af",
        "ebur128=peak=true",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    text = proc.stderr
    report: dict = {"raw": text[-2000:]}
    for line in text.splitlines():
        if "I:" in line and "LUFS" in line:
            # e.g. I:         -16.0 LUFS
            parts = line.strip().split()
            try:
                report["integrated_lufs"] = float(parts[1])
            except (IndexError, ValueError):
                pass
        if "True peak:" in line or "Peak:" in line and "dBFS" in line:
            parts = line.replace(":", " ").split()
            for i, p in enumerate(parts):
                if p in {"peak", "Peak"} and i + 1 < len(parts):
                    try:
                        report.setdefault("true_peak_db", float(parts[i + 1]))
                    except ValueError:
                        pass
        if "True peak:" in line:
            # I: lines and True peak:  -2.3 dBFS
            try:
                report["true_peak_db"] = float(line.split("True peak:")[1].split()[0])
            except (IndexError, ValueError):
                pass
    return report


def normalize_to_lufs(audio: np.ndarray, sr: int, target: float = TARGET_LUFS) -> np.ndarray:
    """Rough integrated loudness normalize via RMS proxy + peak guard."""
    # Write temp, measure, gain, re-measure.
    tmp = MIX_DIR / "_tmp-loudness.wav"
    write_wav(tmp, audio, sr)
    report = measure_lufs(tmp)
    integrated = report.get("integrated_lufs")
    if integrated is None:
        # fallback RMS
        rms = float(np.sqrt(np.mean(audio**2)) or 1e-6)
        current = 20 * math.log10(rms + 1e-12)
        gain = 10 ** ((target - current) / 20)
    else:
        gain = 10 ** ((target - integrated) / 20)
    out = audio * gain
    peak = float(np.max(np.abs(out)) or 1.0)
    if peak > TRUE_PEAK_LIMIT:
        out = out / peak * TRUE_PEAK_LIMIT * 0.98
    return out.astype(np.float32)


def generate_narration(model, sample_rate: int) -> tuple[np.ndarray, dict, list[dict]]:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    cues = data["cues"]
    seg_dir = NARR_DIR / "segments"
    if seg_dir.exists():
        shutil.rmtree(seg_dir)
    seg_dir.mkdir(parents=True, exist_ok=True)

    timeline, new_cues, reports = build_natural_timeline(
        model, sample_rate, cues, seg_dir
    )
    # Resample to 48k if needed for mix consistency.
    if sample_rate != SAMPLE_RATE:
        tmp_in = NARR_DIR / "narration-native.wav"
        tmp_out = NARR_DIR / "narration-48k.wav"
        write_wav(tmp_in, timeline, sample_rate)
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(tmp_in),
                "-ar",
                str(SAMPLE_RATE),
                str(tmp_out),
            ],
            check=True,
        )
        timeline, _ = sf.read(tmp_out, dtype="float32")
        if timeline.ndim > 1:
            timeline = timeline.mean(axis=1)
        timeline = timeline.astype(np.float32)
        # Scale cue times stay the same (duration changes only if resample error).
        native_dur = len(timeline) / SAMPLE_RATE
        # keep cues as-is; duration from samples
    else:
        native_dur = len(timeline) / sample_rate

    narr_path = NARR_DIR / "k08-narration-v5-smooth.wav"
    write_wav(narr_path, timeline, SAMPLE_RATE)

    # Extend after speech for focus + completion hold.
    speech_end = new_cues[-1]["end"] if new_cues else native_dur
    hold_after = 2.6  # focus A/B + completion breathe
    total_dur = max(7.2, min(9.0, speech_end + hold_after))
    # If speech itself is already long, keep within 9s.
    if total_dur > 9.0:
        total_dur = 9.0
    if speech_end + 1.8 > total_dur:
        total_dur = min(9.0, speech_end + 1.8)

    data["cues"] = new_cues
    data["playback_duration"] = round(total_dur, 3)
    data["audio"] = {
        "source": "voice.reference-pharmacist-qwen-v1",
        "file": "/kekang-k08-av/k08-mix-final.wav",
        "narration_file": "/kekang-k08-av/k08-narration-v5-smooth.wav",
        "disclosure": "大参林药师克隆音色；完整语义段连读；默认 1.16×，上限 1.18×",
        "pace_policy": {
            "max_tempo": MAX_TEMPO,
            "default_tempo": DEFAULT_TEMPO,
            "lead_in": LEAD_IN,
            "lead_out": LEAD_OUT,
            "mode": "full-segment-continuous",
            "version": "v5-smooth",
            "max_observed_tempo": round(max(r["tempo"] for r in reports), 4),
            "reports": reports,
        },
    }

    # Derive motion / sfx beats from cue ends so labels sync with ingredient names.
    c0, c1, c2, c3 = new_cues
    beats = {
        "env_start": 0.0,
        "title_hero_start": max(0.12, c0["start"] - 0.08),
        "orbit_lines_start": c1["start"],
        "path_a_start": c2["start"],
        "label_a_start": c2["start"] + 0.12,
        "path_b_start": c3["start"],
        "label_b_start": c3["start"] + 0.12,
        "focus_a_start": c3["end"] + 0.12,
        "focus_b_start": c3["end"] + 0.85,
        "completion_start": c3["end"] + 1.55,
        "speech_end": c3["end"],
        "end": total_dur,
    }
    data["motion_beats"] = {k: round(v, 3) for k, v in beats.items()}
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copy2(JSON_PATH, PROD / "audio/k08-audiovisual-timing.json")
    return timeline, data, new_cues


def build_sfx_bed(data: dict) -> np.ndarray:
    beats = data["motion_beats"]
    duration = float(data["playback_duration"])
    n = int(round(duration * SAMPLE_RATE))
    bed = synth_ambient_bed(duration)
    sfx = np.zeros(n, dtype=np.float32)
    place(sfx, bed, 0.0, SAMPLE_RATE, gain=1.0)

    whoosh = synth_whoosh(0.55)
    air = synth_air_ring(0.42)
    sweep = synth_line_sweep(0.36)
    point_hi = synth_point(920.0, 0.15)
    point_lo = synth_point(720.0, 0.16)
    focus_a = synth_focus_pulse(700.0, 0.13)
    focus_b = synth_focus_pulse(560.0, 0.13)

    write_wav(SFX_DIR / "whoosh-soft.wav", whoosh)
    write_wav(SFX_DIR / "air-ring.wav", air)
    write_wav(SFX_DIR / "line-sweep.wav", sweep)
    write_wav(SFX_DIR / "point-hi.wav", point_hi)
    write_wav(SFX_DIR / "point-lo.wav", point_lo)
    write_wav(SFX_DIR / "focus-a.wav", focus_a)
    write_wav(SFX_DIR / "focus-b.wav", focus_b)
    write_wav(SFX_DIR / "ambient-bed.wav", bed)

    place(sfx, whoosh, beats["title_hero_start"], SAMPLE_RATE, 0.95)
    place(sfx, air, beats["orbit_lines_start"], SAMPLE_RATE, 0.75)
    place(sfx, sweep, beats["path_a_start"], SAMPLE_RATE, 0.85)
    place(sfx, point_hi, beats["label_a_start"], SAMPLE_RATE, 1.0)
    place(sfx, sweep * 0.92, beats["path_b_start"], SAMPLE_RATE, 0.8)
    place(sfx, point_lo, beats["label_b_start"], SAMPLE_RATE, 1.0)
    place(sfx, focus_a, beats["focus_a_start"], SAMPLE_RATE, 0.85)
    place(sfx, focus_b, beats["focus_b_start"], SAMPLE_RATE, 0.85)

    write_wav(SFX_DIR / "k08-sfx-bus.wav", sfx)
    return sfx


def mix(narration: np.ndarray, sfx: np.ndarray, duration: float) -> np.ndarray:
    n = int(round(duration * SAMPLE_RATE))
    mix_bus = np.zeros(n, dtype=np.float32)
    # Narration is king: keep full level; sfx lower.
    place(mix_bus, narration, 0.0, SAMPLE_RATE, 1.0)
    place(mix_bus, sfx, 0.0, SAMPLE_RATE, 0.42)
    # Edge fades 80–150ms
    mix_bus = fade(mix_bus, SAMPLE_RATE, 0.1, 0.12)
    mix_bus = normalize_to_lufs(mix_bus, SAMPLE_RATE, TARGET_LUFS)
    return mix_bus


def mirror_public(data: dict) -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name in (
        "k08-narration-v5-smooth.wav",
        "k08-mix-final.wav",
    ):
        src = NARR_DIR / name if "narration" in name else MIX_DIR / name
        if not src.exists() and name == "k08-mix-final.wav":
            src = MIX_DIR / name
        if src.exists():
            shutil.copy2(src, PUBLIC / name)
    # also copy sfx bus for inspection
    sfx_bus = SFX_DIR / "k08-sfx-bus.wav"
    if sfx_bus.exists():
        shutil.copy2(sfx_bus, PUBLIC / "k08-sfx-bus.wav")
    shutil.copy2(JSON_PATH, PUBLIC / "timing.json")


def write_srt(cues: list[dict], path: Path) -> None:
    def ts(sec: float) -> str:
        ms = int(round(sec * 1000))
        h, rem = divmod(ms, 3600_000)
        m, rem = divmod(rem, 60_000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines: list[str] = []
    for i, cue in enumerate(cues, 1):
        lines.append(str(i))
        lines.append(f"{ts(cue['start'])} --> {ts(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_vtt(cues: list[dict], path: Path) -> None:
    def ts(sec: float) -> str:
        ms = int(round(sec * 1000))
        h, rem = divmod(ms, 3600_000)
        m, rem = divmod(rem, 60_000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    lines = ["WEBVTT", ""]
    for i, cue in enumerate(cues, 1):
        lines.append(str(i))
        lines.append(f"{ts(cue['start'])} --> {ts(cue['end'])}")
        lines.append(cue["text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    print("[1/4] loading TTS model…")
    model = load_model(MODEL)
    sample_rate = int(model.sample_rate)
    print(f"       model={MODEL} sr={sample_rate}")

    print("[2/4] generating full-segment narration…")
    narration, data, cues = generate_narration(model, sample_rate)
    print(
        f"       duration_target={data['playback_duration']}s "
        f"cues={len(cues)} tempo={data['audio']['pace_policy']['max_observed_tempo']}"
    )
    for c in cues:
        print(f"       cue {c['start']:.3f}-{c['end']:.3f}: {c['text']}")

    print("[3/4] synthesizing action SFX…")
    sfx = build_sfx_bed(data)

    print("[4/4] mixing final bed…")
    final = mix(narration, sfx, float(data["playback_duration"]))
    final_path = MIX_DIR / "k08-mix-final.wav"
    write_wav(final_path, final, SAMPLE_RATE)
    # also keep separated narration copy under mix-facing name
    write_wav(NARR_DIR / "k08-narration-v5-smooth.wav", narration, SAMPLE_RATE)

    loud = measure_lufs(final_path)
    report = {
        "target_lufs": TARGET_LUFS,
        "true_peak_limit_dbtp": -1.0,
        "measured": loud,
        "playback_duration": data["playback_duration"],
        "motion_beats": data["motion_beats"],
        "cues": cues,
        "files": {
            "narration": str(NARR_DIR / "k08-narration-v5-smooth.wav"),
            "sfx_bus": str(SFX_DIR / "k08-sfx-bus.wav"),
            "mix": str(final_path),
        },
    }
    report_path = REPORT_DIR / "k08-mix-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    write_srt(cues, PROD / "audio/k08-subtitles.srt")
    write_vtt(cues, PROD / "audio/k08-subtitles.vtt")
    mirror_public(data)

    print(f"[done] mix={final_path}")
    print(f"       report={report_path}")
    if "integrated_lufs" in loud:
        print(f"       LUFS≈{loud['integrated_lufs']}")
    if "true_peak_db" in loud:
        print(f"       TP≈{loud['true_peak_db']} dB")


if __name__ == "__main__":
    main()
