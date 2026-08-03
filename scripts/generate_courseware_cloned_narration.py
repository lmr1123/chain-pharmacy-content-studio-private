#!/usr/bin/env python3
"""商品培训课件 · 克隆旁白生成器（多主题可复用）

基于音色包 voice.sufuda-courseware-pharmacist-v1（或自定义 --voice-pack），
把 storyboard.json 的 captions 按「语义块」连读克隆，语速门禁 v5-smooth：

1. 按章节/页 type 分块，每块一次 TTS 连读（禁止逐 cue 硬拼）
2. DEFAULT_TEMPO=1.16，MAX_TEMPO≤1.18；放不下则延时间轴
3. 字幕按字数比例回切
4. 输出整轨 wav + 更新后的 storyboard（captions/pages/duration）

示例：
  # 用默认速福达音色包，读本金样 storyboard，写出克隆轨（不覆盖原声）
  .venv-qwen-tts/bin/python scripts/generate_courseware_cloned_narration.py \\
    --storyboard production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/storyboard.json \\
    --out-dir production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/audio-work/clone-v1

  # 新主题：只换 storyboard 文案，同一音色
  .venv-qwen-tts/bin/python scripts/generate_courseware_cloned_narration.py \\
    --storyboard path/to/new-theme/storyboard.json \\
    --voice-pack production-library/voices/sufuda-courseware-pharmacist-v1 \\
    --apply-to-storyboard
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VOICE = ROOT / "production-library/voices/sufuda-courseware-pharmacist-v1"
DEFAULT_MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"

MAX_TEMPO = 1.18
DEFAULT_TEMPO = 1.16
MIN_TEMPO = 0.95
LEAD_IN = 0.06
LEAD_OUT = 0.10
MAX_CHARS_PER_SEC = 5.5
CROSSFADE = 0.035


def load_voice_pack(path: Path) -> dict:
    pack = path / "voice-pack.json" if path.is_dir() else path
    data = json.loads(pack.read_text(encoding="utf-8"))
    base = pack.parent if pack.name == "voice-pack.json" else path
    data["_base"] = base
    data["_prompt_audio"] = base / data["prompt"]["audio"]
    data["_ref_text"] = data["prompt"]["ref_text"]
    pace = data.get("pace") or {}
    data["_default_tempo"] = float(pace.get("default_tempo", DEFAULT_TEMPO))
    data["_max_tempo"] = float(pace.get("max_tempo", MAX_TEMPO))
    data["_min_tempo"] = float(pace.get("min_tempo", MIN_TEMPO))
    return data


def min_audible_seconds(text: str) -> float:
    t = re.sub(r"\s+", "", text)
    n = max(1, len(t))
    by_chars = n / MAX_CHARS_PER_SEC
    if n <= 2:
        return max(0.55, by_chars)
    if n <= 6:
        return max(0.75, by_chars)
    return max(0.9, by_chars)


def ffmpeg_atempo(src: Path, dst: Path, tempo: float, sample_rate: int) -> None:
    filters: list[str] = []
    t = tempo
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


def _read_mono(path: Path, sample_rate: int) -> np.ndarray:
    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    if int(sr) == sample_rate:
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


def join_texts(texts: list[str]) -> str:
    parts: list[str] = []
    cleaned = [re.sub(r"\s+", "", t.strip()) for t in texts if t and t.strip()]
    for i, t in enumerate(cleaned):
        if not t:
            continue
        if t[-1] in "。！？；，、：":
            parts.append(t)
        elif i < len(cleaned) - 1:
            parts.append(t + "，")
        else:
            parts.append(t + "。")
    return "".join(parts)


def split_by_chars(
    texts: list[str], speech_start: float, speech_dur: float
) -> list[dict]:
    weights = [max(1, len(re.sub(r"\s+", "", t))) for t in texts]
    total_w = sum(weights) or 1
    cursor = speech_start
    out: list[dict] = []
    for text, w in zip(texts, weights):
        dur = speech_dur * (w / total_w)
        out.append(
            {
                "start": round(cursor, 3),
                "end": round(cursor + dur, 3),
                "text": text,
            }
        )
        cursor += dur
    if out:
        out[-1]["end"] = round(speech_start + speech_dur, 3)
    return out


def semantic_blocks(captions: list[dict], pages: list[dict] | None) -> list[list[dict]]:
    """优先按 pages 分块；无 pages 时按章节标题启发式分块。"""
    if pages:
        blocks: list[list[dict]] = []
        for page in pages:
            rng = page.get("range") or [0, 0]
            start, end = float(rng[0]), float(rng[1])
            # chapter 页可与下一块合并：单独 chapter 太短
            cues = [
                c
                for c in captions
                if float(c["start"]) < end - 1e-6 and float(c["end"]) > start + 1e-6
            ]
            # 取主要落在本页的 cue
            mid = [
                c
                for c in cues
                if (float(c["start"]) + float(c["end"])) / 2 >= start
                and (float(c["start"]) + float(c["end"])) / 2 < end
            ]
            if mid:
                blocks.append(mid)
        if blocks:
            # 合并极短 chapter-only 块到下一块
            merged: list[list[dict]] = []
            i = 0
            while i < len(blocks):
                b = blocks[i]
                total_chars = sum(len(re.sub(r"\s+", "", c["text"])) for c in b)
                if total_chars <= 12 and i + 1 < len(blocks):
                    blocks[i + 1] = b + blocks[i + 1]
                else:
                    merged.append(b)
                i += 1
            return merged or blocks

    # fallback: 按「一、二、三、」章节边界
    blocks = []
    cur: list[dict] = []
    for c in captions:
        t = c["text"].strip()
        if re.match(r"^[一二三四五六七八九十]+[、.．]", t) and cur:
            blocks.append(cur)
            cur = [c]
        else:
            cur.append(c)
    if cur:
        blocks.append(cur)
    return blocks or [captions]


def generate_block(
    model,
    voice: dict,
    sample_rate: int,
    texts: list[str],
    work_dir: Path,
    index: int,
) -> tuple[np.ndarray, float, dict]:
    full = join_texts(texts)
    raw_path = work_dir / f"block{index:02d}-raw.wav"
    tempo_path = work_dir / f"block{index:02d}-tempo.wav"
    out_path = work_dir / f"block{index:02d}-out.wav"

    if not raw_path.exists():
        mx.random.seed(20260802 + index * 17)
        result = list(
            model.generate(
                text=full,
                ref_audio=str(voice["_prompt_audio"]),
                ref_text=voice["_ref_text"],
                lang_code="Chinese",
                temperature=0.68,
                top_k=40,
                top_p=0.95,
                repetition_penalty=1.05,
            )
        )[0]
        audio = np.asarray(result.audio, dtype=np.float32)
        sf.write(raw_path, audio, int(result.sample_rate))

    audio = _read_mono(raw_path, sample_rate)
    raw_dur = max(1e-3, len(audio) / sample_rate)
    tempo = float(voice["_default_tempo"])
    max_tempo = float(voice["_max_tempo"])
    min_tempo = float(voice["_min_tempo"])
    policy = f"default-brisk-{tempo:.2f}"

    ffmpeg_atempo(raw_path, tempo_path, tempo, sample_rate)
    audio = _read_mono(tempo_path, sample_rate)
    used = len(audio) / sample_rate

    min_dur = min_audible_seconds(full) / tempo
    if used < min_dur * 0.92:
        tempo = max(min_tempo, (raw_dur * voice["_default_tempo"]) / min_dur)
        tempo = min(tempo, voice["_default_tempo"])
        ffmpeg_atempo(raw_path, tempo_path, tempo, sample_rate)
        audio = _read_mono(tempo_path, sample_rate)
        used = len(audio) / sample_rate
        policy = "brisk-then-slow-for-min-audible"

    if used < min_dur:
        pad = int(round((min_dur - used) * sample_rate))
        audio = np.concatenate([audio, np.zeros(pad, dtype=np.float32)])
        used = len(audio) / sample_rate
        policy = f"{policy}+silence-pad"

    # runaway guard: if TTS blew up length vs text budget, re-gen once with lower temp
    expected_max = max(8.0, len(re.sub(r"\s+", "", full)) / 3.2)
    if used > expected_max * 1.8:
        policy = f"{policy}+runaway-warning"
        # soft truncate with fade (last resort; prefer re-run)
        keep = int(expected_max * 1.5 * sample_rate)
        if len(audio) > keep:
            fade = int(0.15 * sample_rate)
            audio = audio[:keep].copy()
            audio[-fade:] *= np.linspace(1, 0, fade)
            used = len(audio) / sample_rate
            policy = f"{policy}+soft-trim"

    sf.write(out_path, audio, sample_rate)
    report = {
        "index": index,
        "text": full,
        "raw_duration": round(raw_dur, 3),
        "used_duration": round(used, 3),
        "tempo": round(tempo, 4),
        "policy": policy,
        "gate": "ok" if tempo <= max_tempo + 1e-6 else "violation",
    }
    return audio, used, report


def crossfade_concat(chunks: list[np.ndarray], sample_rate: int, xf: float) -> np.ndarray:
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    if len(chunks) == 1:
        return chunks[0]
    n_xf = int(round(xf * sample_rate))
    out = chunks[0]
    for nxt in chunks[1:]:
        if n_xf <= 0 or len(out) < n_xf or len(nxt) < n_xf:
            out = np.concatenate([out, nxt])
            continue
        a = out[:-n_xf]
        fade_out = out[-n_xf:] * np.linspace(1, 0, n_xf)
        fade_in = nxt[:n_xf] * np.linspace(0, 1, n_xf)
        out = np.concatenate([a, fade_out + fade_in, nxt[n_xf:]])
    return out.astype(np.float32)


def loudnorm_ffmpeg(src: Path, dst: Path, lufs: float = -16.0) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(src),
            "-af",
            f"loudnorm=I={lufs}:TP=-1.5:LRA=9",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(dst),
        ],
        check=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="课件克隆旁白（语义块 v5-smooth）")
    ap.add_argument("--storyboard", type=Path, required=True)
    ap.add_argument("--voice-pack", type=Path, default=DEFAULT_VOICE)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument(
        "--apply-to-storyboard",
        action="store_true",
        help="把克隆轨路径与新 captions/duration 写回 storyboard",
    )
    ap.add_argument(
        "--copy-to-assets",
        type=Path,
        default=None,
        help="可选：复制最终轨到 public/assets/narration-cloned.wav 等路径",
    )
    ap.add_argument("--smoke-text", default=None, help="仅冒烟：合成一句新文案")
    args = ap.parse_args()

    voice = load_voice_pack(args.voice_pack)
    if not voice["_prompt_audio"].exists():
        print(f"missing prompt audio: {voice['_prompt_audio']}", file=sys.stderr)
        return 2

    out_dir = args.out_dir or (args.storyboard.parent / "audio-work" / "clone-v1")
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "blocks"
    work.mkdir(parents=True, exist_ok=True)

    print(f"voice={voice.get('id')} prompt={voice['_prompt_audio']}")
    print(f"loading model {args.model} ...")
    model = load_model(args.model)
    sample_rate = int(model.sample_rate)

    if args.smoke_text:
        audio, used, report = generate_block(
            model, voice, sample_rate, [args.smoke_text], work, 0
        )
        smoke = out_dir / "smoke-clone.wav"
        sf.write(smoke, audio, sample_rate)
        (out_dir / "smoke-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"smoke ok duration={used:.2f}s -> {smoke}")
        return 0

    sb_path = args.storyboard.resolve()
    data = json.loads(sb_path.read_text(encoding="utf-8"))
    captions = list(data.get("captions") or [])
    pages = list(data.get("pages") or [])
    if not captions:
        print("storyboard has no captions", file=sys.stderr)
        return 2

    blocks = semantic_blocks(captions, pages)
    print(f"blocks={len(blocks)} captions={len(captions)}")

    chunk_audios: list[np.ndarray] = []
    all_cues: list[dict] = []
    reports: list[dict] = []
    t_cursor = 0.0

    for bi, block in enumerate(blocks):
        texts = [str(c["text"]).strip() for c in block]
        audio, used, report = generate_block(
            model, voice, sample_rate, texts, work, bi
        )
        lead_in = int(round(LEAD_IN * sample_rate))
        lead_out = int(round(LEAD_OUT * sample_rate))
        piece = np.concatenate(
            [
                np.zeros(lead_in, dtype=np.float32),
                audio,
                np.zeros(lead_out, dtype=np.float32),
            ]
        )
        speech_start = t_cursor + LEAD_IN
        speech_dur = used
        cues = split_by_chars(texts, speech_start, speech_dur)
        all_cues.extend(cues)
        chunk_audios.append(piece)
        piece_dur = len(piece) / sample_rate
        report["block_start"] = round(t_cursor, 3)
        report["block_end"] = round(t_cursor + piece_dur, 3)
        reports.append(report)
        t_cursor += piece_dur
        print(
            f"  block{bi:02d} dur={used:.2f}s cues={len(texts)} "
            f"tempo={report['tempo']} policy={report['policy']}"
        )

    timeline = crossfade_concat(chunk_audios, sample_rate, CROSSFADE)
    peak = float(np.max(np.abs(timeline)) or 1.0)
    timeline = timeline / peak * 0.95
    duration = len(timeline) / sample_rate

    raw_out = out_dir / "narration-cloned-raw.wav"
    sf.write(raw_out, timeline, sample_rate)
    final_out = out_dir / "narration-cloned.wav"
    loudnorm_ffmpeg(raw_out, final_out, lufs=-16.0)

    # rebuild pages ranges from new cues (simple sequential by old page count)
    new_pages = []
    if pages and all_cues:
        # assign each cue to page by order of old blocks
        cue_i = 0
        for pi, page in enumerate(pages):
            # approximate: distribute cues proportional to original page cue counts
            pass
        # simpler: set pages from block reports
        for pi, (page, rep) in enumerate(zip(pages, reports)):
            p = dict(page)
            p["range"] = [rep["block_start"], rep["block_end"]]
            new_pages.append(p)
        # if page count != block count, keep captions only
        if len(new_pages) != len(pages):
            new_pages = pages

    meta = {
        "voice_id": voice.get("id"),
        "engine": voice.get("engine"),
        "duration": round(duration, 3),
        "default_tempo": voice["_default_tempo"],
        "max_tempo": voice["_max_tempo"],
        "blocks": reports,
        "output": str(final_out),
        "policy": "v5-smooth semantic-block continuous clone",
    }
    (out_dir / "clone-report.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if args.apply_to_storyboard:
        data["captions"] = all_cues
        data["duration"] = round(duration, 3)
        if "source_authority" in data:
            data["source_authority"]["duration_deliverable"] = round(duration, 3)
        data["audio"] = {
            "file": "/assets/narration-cloned.wav",
            "source": voice.get("id"),
            "processing": "Qwen3-TTS semantic-block clone v5-smooth + loudnorm-16LUFS",
            "loudness_target_lufs": -16,
            "note": "克隆音色生成轨；非参考原声直出。换主题时重跑本脚本即可。",
            "clone_report": str(out_dir / "clone-report.json"),
        }
        if new_pages and len(new_pages) == len(pages):
            data["pages"] = new_pages
        sb_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"updated storyboard {sb_path}")

    if args.copy_to_assets:
        dest = args.copy_to_assets
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(final_out.read_bytes())
        print(f"copied -> {dest}")

    print(f"done duration={duration:.2f}s -> {final_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
