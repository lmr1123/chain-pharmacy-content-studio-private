#!/usr/bin/env python3
"""为辅酶 Q10 商品培训各分段生成大参林药师克隆旁白（连读 + 轻微整体加速）。

可复用策略（decision.semantic-block-voice-speed-gate +
lesson.voice-continuous-segment-smooth / v5-smooth）：

1. 整段 cue 用逗号拼成一次 TTS 连读，禁止逐 cue 独立合成再硬拼
2. DEFAULT_TEMPO≈1.16，MAX_TEMPO≤1.18；放不下则延时间轴，禁止暴力贴窗
3. LEAD_IN/LEAD_OUT 仅 0.06/0.10s 极短垫，句间无固定静音槽
4. 字幕用字数比例 split_timeline_by_chars 重切，不贴旧参考窗
5. 短句/序号设最小可听时长（min_audible_seconds）
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "poc/gold-sample"
MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
REF_AUDIO = ROOT / (
    "poc/reference-replica/reference-analysis/audio/reference-clone-prompt.wav"
)
REF_TEXT = (
    "喉咙又肿又痛，咳嗽停不下来。咳出来的痰还黄黄的。"
    "鼻涕又黄又稠，身上发烫。"
)
AUDIO_DIR = GOLD / "public/product-training-audio"
SEG_ROOT = AUDIO_DIR / "qwen-product-smooth-v5"
VERSION = "v5-smooth"

# 整段连读 + 整体略快；禁止逐句硬停顿。
MAX_TEMPO = 1.18
DEFAULT_TEMPO = 1.16
MILD_FIT_TEMPO = 1.16
MIN_TEMPO = 0.95
LEAD_IN = 0.06
LEAD_OUT = 0.10
MAX_CHARS_PER_SEC = 5.5

SEGMENTS = [
    "product-training-opening.json",
    "product-training-faithful.json",
    "product-training-brand-overview.json",
    "product-training-efficacy.json",
    "product-training-features.json",
    "product-training-audience.json",
    "product-training-combination.json",
    "product-training-summary.json",
]


def neutralize_brand(text: str) -> str:
    replacements = [
        (r"远大医药旗下原研品牌能气朗辅酶Q10", "连锁药店在售的辅酶Q10相关商品"),
        (r"远大医药旗下原研品牌能气朗", "辅酶Q10相关商品"),
        (r"能气朗作为原研辅酶Q10制剂", "辅酶Q10作为常用辅酶制剂"),
        (r"能气朗凭借独家红光生产工艺与避光专利", "通过避光工艺与稳定制剂技术"),
        (r"能气朗可营养心肌", "辅酶Q10可营养心肌"),
        (r"能气朗可缓解", "辅酶Q10可缓解"),
        (r"复方丹参滴丸＋能气朗", "复方丹参滴丸＋辅酶Q10"),
        (r"他汀＋能气朗", "他汀＋辅酶Q10"),
        (r"能气朗®", "辅酶Q10"),
        (r"能气朗", "辅酶Q10"),
        (r"远大健康", "大参林"),
        (r"远大医药", "大参林"),
        (r"CGE HEALTHCARE", "DASHENLIN"),
        (r"CGE", "大参林"),
    ]
    out = text
    for pat, rep in replacements:
        out = re.sub(pat, rep, out)
    return out


def min_audible_seconds(text: str) -> float:
    """短句/序号最小可听时长。"""
    t = re.sub(r"\s+", "", text)
    n = max(1, len(t))
    # 至少 0.55s；按字数保证不太赶
    by_chars = n / MAX_CHARS_PER_SEC
    if n <= 2:
        return max(0.55, by_chars)
    if n <= 6:
        return max(0.75, by_chars)
    return max(0.9, by_chars)


def ffmpeg_atempo(src: Path, dst: Path, tempo: float, sample_rate: int) -> None:
    """atempo 仅支持 0.5–2.0；超过时链式。"""
    filters: list[str] = []
    t = tempo
    # chain atempo in 0.5–2.0 range
    while t > 2.0 + 1e-6:
        filters.append("atempo=2.0")
        t /= 2.0
    while t < 0.5 - 1e-6:
        filters.append("atempo=0.5")
        t /= 0.5
    filters.append(f"atempo={t:.6f}")
    filters.append(f"aresample={sample_rate}")
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(src),
            "-af",
            ",".join(filters),
            str(dst),
        ],
        check=True,
    )


def generate_raw(
    model,
    text: str,
    raw_path: Path,
    seed: int,
) -> tuple[np.ndarray, int]:
    if raw_path.exists():
        audio, sr = sf.read(raw_path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        return audio.astype(np.float32), int(sr)

    mx.random.seed(seed)
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
    audio = np.asarray(result.audio, dtype=np.float32)
    sf.write(raw_path, audio, result.sample_rate)
    return audio, int(result.sample_rate)


def _read_mono(path: Path, sample_rate: int) -> np.ndarray:
    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    if sr == sample_rate:
        return audio
    tmp = path.with_suffix(f".{sample_rate}.wav")
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(path),
            "-af",
            f"aresample={sample_rate}",
            str(tmp),
        ],
        check=True,
    )
    return _read_mono(tmp, sample_rate)


def naturalize_chunk(
    model,
    sample_rate: int,
    text: str,
    preferred_slot: float | None,
    seg_dir: Path,
    index: int,
) -> tuple[np.ndarray, float, dict]:
    """生成略加快的自然语速片段，返回 (audio, used_duration, report).

    策略：
    1. 先自然 TTS；
    2. 统一乘 DEFAULT_TEMPO（约 1.07×）略加快；
    3. 仅当旧槽仍略短且 ≤ MILD_FIT_TEMPO 时再小幅贴合；
    4. 更长则延长时间轴，禁止顶满 1.18×。
    """
    raw_path = seg_dir / f"{index:02d}-raw.wav"
    out_path = seg_dir / f"{index:02d}-out.wav"
    text = neutralize_brand(text)
    generate_raw(model, text, raw_path, seed=20260801 + index * 31)
    audio = _read_mono(raw_path, sample_rate)
    raw_dur = max(1e-3, len(audio) / sample_rate)
    min_dur = min_audible_seconds(text) / DEFAULT_TEMPO  # 加快后仍够听
    tempo = DEFAULT_TEMPO
    policy = f"default-brisk-{DEFAULT_TEMPO:.2f}"

    # 默认整体略快
    work = seg_dir / f"{index:02d}-tempo.wav"
    ffmpeg_atempo(raw_path, work, tempo, sample_rate)
    audio = _read_mono(work, sample_rate)
    used = len(audio) / sample_rate

    # 过短：略减速到最小可听
    if used < min_dur * 0.92:
        tempo = max(MIN_TEMPO, (raw_dur * DEFAULT_TEMPO) / min_dur)
        tempo = min(tempo, DEFAULT_TEMPO)
        ffmpeg_atempo(raw_path, work, tempo, sample_rate)
        audio = _read_mono(work, sample_rate)
        used = len(audio) / sample_rate
        policy = "brisk-then-slow-for-min-audible"
    elif preferred_slot is not None and used > preferred_slot * 1.02:
        needed = used / preferred_slot
        if needed <= MILD_FIT_TEMPO / DEFAULT_TEMPO:
            # 在默认加快基础上再极小幅贴合
            tempo = min(MILD_FIT_TEMPO, DEFAULT_TEMPO * needed)
            ffmpeg_atempo(raw_path, work, tempo, sample_rate)
            audio = _read_mono(work, sample_rate)
            used = len(audio) / sample_rate
            policy = f"brisk-mild-fit-{tempo:.3f}"
        else:
            # 保持 DEFAULT_TEMPO，时间轴后延
            policy = f"brisk-extend-timeline-{DEFAULT_TEMPO:.2f}"

    # 若仍短于最小可听，句末补静音
    if used < min_dur:
        pad = int(round((min_dur - used) * sample_rate))
        audio = np.concatenate([audio, np.zeros(pad, dtype=np.float32)])
        used = len(audio) / sample_rate
        policy = f"{policy}+silence-pad"

    sf.write(out_path, audio, sample_rate)
    report = {
        "text": text,
        "raw_duration": round(raw_dur, 3),
        "used_duration": round(used, 3),
        "tempo": round(tempo, 4),
        "default_tempo": DEFAULT_TEMPO,
        "preferred_slot": None if preferred_slot is None else round(preferred_slot, 3),
        "min_audible": round(min_dur, 3),
        "policy": policy,
        "gate": "ok" if tempo <= MAX_TEMPO + 1e-6 else "violation",
    }
    return audio, used, report


def join_cues_for_tts(cues: list[dict]) -> tuple[str, list[str]]:
    """把多条字幕拼成一整段口播稿，减少逐句 TTS 造成的硬停顿。"""
    parts: list[str] = []
    for cue in cues:
        t = neutralize_brand(str(cue["text"])).strip()
        t = re.sub(r"\s+", "", t)
        if not t:
            continue
        # 已有句读则保留，否则用逗号连接，最后一句用句号
        parts.append(t)
    cleaned: list[str] = []
    for i, t in enumerate(parts):
        if t[-1] in "。！？；，、：":
            cleaned.append(t)
        elif i < len(parts) - 1:
            cleaned.append(t + "，")
        else:
            cleaned.append(t + "。")
    full = "".join(cleaned)
    # 供字幕回写的纯文案（去我们追加的连接符时仍用 neutralize 后的原文）
    texts = [neutralize_brand(str(c["text"])).strip() for c in cues]
    return full, texts


def split_timeline_by_chars(
    cues: list[dict],
    texts: list[str],
    speech_start: float,
    speech_dur: float,
) -> list[dict]:
    """按字数比例把整段音频切回字幕窗（连续、无额外句间空隙）。"""
    weights = [max(1, len(re.sub(r"\s+", "", t))) for t in texts]
    total_w = sum(weights) or 1
    cursor = speech_start
    out: list[dict] = []
    for cue, text, w in zip(cues, texts, weights):
        dur = speech_dur * (w / total_w)
        start = cursor
        end = cursor + dur
        cue = dict(cue)
        cue["start"] = round(start, 3)
        cue["end"] = round(end, 3)
        cue["text"] = text
        out.append(cue)
        cursor = end
    # 修正浮点：最后一条贴齐
    if out:
        out[-1]["end"] = round(speech_start + speech_dur, 3)
    return out


def build_natural_timeline(
    model,
    sample_rate: int,
    cues: list[dict],
    seg_dir: Path,
) -> tuple[np.ndarray, list[dict], list[dict]]:
    """整段连读生成 + 默认加快；字幕按时长比例回切，避免一小句一停。"""
    full_text, texts = join_cues_for_tts(cues)
    # 整段一次 TTS（preferred_slot=None → 只用 DEFAULT_TEMPO）
    audio, used, report = naturalize_chunk(
        model, sample_rate, full_text, None, seg_dir, index=0
    )
    report["index"] = 0
    report["mode"] = "full-segment-continuous"
    report["joined_text"] = full_text

    lead_in = int(round(LEAD_IN * sample_rate))
    lead_out = int(round(LEAD_OUT * sample_rate))
    speech = audio
    timeline = np.concatenate(
        [
            np.zeros(lead_in, dtype=np.float32),
            speech,
            np.zeros(lead_out, dtype=np.float32),
        ]
    )
    peak = float(np.max(np.abs(timeline)) or 1.0)
    timeline = timeline / peak * 0.95

    speech_start = LEAD_IN
    speech_dur = len(speech) / sample_rate
    new_cues = split_timeline_by_chars(cues, texts, speech_start, speech_dur)
    return timeline, new_cues, [report]


def process_summary(model, sample_rate: int, data: dict, stem: str) -> dict:
    text = neutralize_brand(
        data.get("tagline") or "大参林内部培训，辅酶Q10商品知识"
    )
    data["tagline"] = text
    seg_dir = SEG_ROOT / stem
    if seg_dir.exists():
        shutil.rmtree(seg_dir)
    seg_dir.mkdir(parents=True, exist_ok=True)
    audio, used, report = naturalize_chunk(
        model, sample_rate, text, None, seg_dir, 0
    )
    # 总结至少 2.8s，便于封底停留
    duration = max(2.8, used + 0.35)
    n = int(round(duration * sample_rate))
    timeline = np.zeros(n, dtype=np.float32)
    timeline[: min(n, len(audio))] = audio[:n]
    peak = float(np.max(np.abs(timeline)) or 1.0)
    out = AUDIO_DIR / f"qwen-cloned-{stem}-{VERSION}.wav"
    sf.write(out, timeline / peak * 0.95, sample_rate)
    data["audio"] = {
        "source": "voice.reference-pharmacist-qwen-v1",
        "file": f"/product-training-audio/{out.name}",
        "disclosure": "大参林药师克隆音色；自然语速（最大加速1.18×）",
        "pace_policy": {
            "max_tempo": MAX_TEMPO,
            "version": VERSION,
            "report": report,
        },
    }
    if "range" in data:
        data["range"]["duration"] = round(duration, 3)
    return {"stem": stem, "duration": duration, "reports": [report]}


def process_segment(model, sample_rate: int, rel_json: str) -> dict:
    path = GOLD / rel_json
    data = json.loads(path.read_text(encoding="utf-8"))
    stem = path.stem
    cues = data.get("cues") or []
    seg_dir = SEG_ROOT / stem
    if seg_dir.exists():
        shutil.rmtree(seg_dir)
    seg_dir.mkdir(parents=True, exist_ok=True)

    if not cues:
        info = process_summary(model, sample_rate, data, stem)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"[summary] {stem} duration={info['duration']:.2f}s")
        return info

    timeline, cues, reports = build_natural_timeline(
        model, sample_rate, cues, seg_dir
    )
    duration = len(timeline) / sample_rate
    out = AUDIO_DIR / f"qwen-cloned-{stem}-{VERSION}.wav"
    sf.write(out, timeline, sample_rate)

    tempos = [r["tempo"] for r in reports]
    data["cues"] = cues
    data["audio"] = {
        "source": "voice.reference-pharmacist-qwen-v1",
        "file": f"/product-training-audio/{out.name}",
        "disclosure": "大参林药师克隆音色；自然语速铺轨，禁止超1.18×暴力加速",
        "pace_policy": {
            "max_tempo": MAX_TEMPO,
            "min_tempo": MIN_TEMPO,
            "lead_in": LEAD_IN,
            "lead_out": LEAD_OUT,
            "mode": "full-segment-continuous",
            "version": VERSION,
            "max_observed_tempo": round(max(tempos), 4),
            "reports": reports,
        },
    }
    # 同步时长字段，供渲染 DURATION 读取
    if "range" in data and isinstance(data["range"], dict):
        data["range"]["duration"] = round(duration, 3)
    if "referenceRange" in data and isinstance(data["referenceRange"], dict):
        data["referenceRange"]["duration"] = round(duration, 3)
        # 保留历史 start 仅作溯源；播放以 cues 为准
    data["playback_duration"] = round(duration, 3)

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"[ok] {stem} cues={len(cues)} duration={duration:.2f}s "
        f"max_tempo={max(tempos):.3f}"
    )
    return {"stem": stem, "duration": duration, "reports": reports}


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    SEG_ROOT.mkdir(parents=True, exist_ok=True)
    model = load_model(MODEL)
    sample_rate = model.sample_rate
    all_reports = []
    for rel in SEGMENTS:
        all_reports.append(process_segment(model, sample_rate, rel))
    report_path = AUDIO_DIR / f"pace-report-{VERSION}.json"
    report_path.write_text(
        json.dumps(all_reports, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"pace report -> {report_path}")
    print("done: natural-pace narration for all product-training segments")


if __name__ == "__main__":
    main()
