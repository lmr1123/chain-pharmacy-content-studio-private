#!/usr/bin/env python3
"""片段编排工作室：删隐片段 / 改旁白 / TTS 重生成 / 时长回填 / 重建成片。

权威：content-model.json + out/segment-studio/state.json
音频策略：
  - reference_slice：从原始参考旁白按「原始时码」切片（删段后仍可还原）
  - tts：edge-tts / say / 可选 Qwen 克隆
  - silence：静音占位

Usage:
  python3 scripts/segment_studio.py init
  python3 scripts/segment_studio.py list
  python3 scripts/segment_studio.py hide --id S05_benefit_2
  python3 scripts/segment_studio.py enable --id S05_benefit_2
  python3 scripts/segment_studio.py set-narration --id S12_related_1 --text "……"
  python3 scripts/segment_studio.py regen-tts --id S12_related_1
  python3 scripts/segment_studio.py rebuild
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "content-model.json"
STATE_DIR = ROOT / "out" / "segment-studio"
STATE_PATH = STATE_DIR / "state.json"
SEG_AUDIO = STATE_DIR / "segments"
WORK = STATE_DIR / "work"
# 原始参考旁白（勿被工作轨覆盖）
REF_NARRATION = ROOT / "web" / "reference-narration.mp3"
# 编辑器 / 成片使用的工作旁白轨
WORK_NARRATION = ROOT / "web" / "working-narration.mp3"
PUBLIC_NARRATION = ROOT / "public" / "narration.mp3"

MIN_SCENE_S = 1.2
MAX_ATEMPO = 1.18
PAD_AFTER_VO = 0.18

# Qwen3 克隆（mlx-audio，本机缓存模型）
QWEN_MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16"
MLX_AUDIO_ROOT = ROOT.parents[3] / "third_party" / "mlx-audio"
if not MLX_AUDIO_ROOT.exists():
    MLX_AUDIO_ROOT = Path(
        "/Users/liminrong/Projects/chain-pharmacy-content-studio/third_party/mlx-audio"
    )
REF_PROMPT_WAV = STATE_DIR / "reference-prompt.wav"
# 必须与 ensure_clone_prompt 切片严格对齐。
# 旧版 -ss 0.58 -t 5.4 只录到「贡献」中途，ref_text 却写完整句，
# Qwen3 ICL 会在每段 TTS 开头补念「最大的十种健康食品…」（S12/S13 已踩坑）。
# 词级时码（reference/asr）：「美」2.36 →「品」7.76。
REF_PROMPT_SS = "2.30"
REF_PROMPT_T = "5.55"
REF_PROMPT_TEXT = "美国《时代杂志》评选的对人类健康贡献最大的十种健康食品。"
REF_PROMPT_META = STATE_DIR / "reference-prompt.meta.json"
_qwen_model = None


def load_model() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def save_model(model: dict) -> None:
    MODEL_PATH.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_state() -> dict:
    if not STATE_PATH.exists():
        return init_state()
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def narration_text_from_scene(sc: dict) -> str:
    if sc.get("narration"):
        return str(sc["narration"]).strip()
    subs = sc.get("subtitles") or []
    parts = [str(s.get("text") or "").strip() for s in subs if s.get("text")]
    if parts:
        return "，".join(parts)
    # fallbacks
    for k in ("card_title", "chapter", "section", "note", "footer", "title_pill"):
        if sc.get(k):
            return str(sc[k]).strip()
    return ""


def init_state() -> dict:
    model = load_model()
    scenes = []
    for sc in model.get("scenes") or []:
        start = float(sc["start"])
        end = float(sc["end"])
        snap = copy.deepcopy(sc)
        scenes.append(
            {
                "id": sc["id"],
                "type": sc.get("type") or "",
                "enabled": sc.get("enabled", True) is not False,
                "title": sc.get("chapter")
                or sc.get("card_title")
                or sc.get("title_pill")
                or sc["id"],
                "narration_text": narration_text_from_scene(sc),
                "audio_source": "reference_slice",  # reference_slice | tts | silence
                "reference_start": start,
                "reference_end": end,
                "duration_s": round(end - start, 3),
                "min_duration_s": MIN_SCENE_S,
                "tts_file": None,
                "layer": sc.get("layer") or "observed_reference",
                # 完整 scene 快照，删段后仍可恢复字段
                "content_snapshot": snap,
            }
        )
    state = {
        "version": 1,
        "project_id": model.get("project_id") or "product-courseware-4",
        "ref_narration": str(REF_NARRATION),
        "scenes": scenes,
        "last_rebuild": None,
        "notes": "reference_start/end 固定绑原始参考轨时码；删段只改 enabled，不破坏切片。",
    }
    save_state(state)
    return state


def ffprobe_duration(path: Path) -> float:
    if not path.exists():
        return 0.0
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return max(0.0, float((r.stdout or "").strip()))
    except ValueError:
        return 0.0


def ensure_ref() -> Path:
    if REF_NARRATION.exists():
        return REF_NARRATION
    # fallback from Downloads
    alt = Path("/Users/liminrong/Downloads/商品培训课件4/商品培训课件4.mp3")
    if alt.exists():
        return alt
    raise FileNotFoundError(f"reference narration missing: {REF_NARRATION}")


def extract_reference_slice(start: float, end: float, out: Path) -> float:
    ref = ensure_ref()
    dur = max(0.05, end - start)
    out.parent.mkdir(parents=True, exist_ok=True)
    ref_dur = ffprobe_duration(ref)
    if start >= ref_dur - 0.05:
        # past end of VO → silence
        make_silence(dur, out)
        return dur
    take = min(dur, max(0.05, ref_dur - start))
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{take:.3f}",
            "-i",
            str(ref),
            "-ac",
            "1",
            "-ar",
            "44100",
            str(out),
        ],
        check=True,
    )
    if take + 0.02 < dur:
        # pad silence to requested duration
        pad = WORK / f"pad-{out.stem}.wav"
        make_silence(dur - take, pad)
        concat_audio([out, pad], out)
    return ffprobe_duration(out) or dur


def make_silence(seconds: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    seconds = max(0.05, seconds)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            f"{seconds:.3f}",
            str(out),
        ],
        check=True,
    )


def concat_audio(parts: list[Path], out: Path) -> float:
    out.parent.mkdir(parents=True, exist_ok=True)
    lst = WORK / "concat-list.txt"
    WORK.mkdir(parents=True, exist_ok=True)
    lines = []
    for p in parts:
        # re-encode each to wav first for safe concat
        lines.append(f"file '{p.resolve()}'")
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(out),
        ],
        check=True,
    )
    return ffprobe_duration(out)


def to_wav(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            "44100",
            str(dst),
        ],
        check=True,
    )


def ensure_clone_prompt() -> Path:
    """Slice a complete phrase from reference narration as clone prompt.

    Cached wav is invalidated when slice window or ref_text changes (meta file).
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "ss": REF_PROMPT_SS,
        "t": REF_PROMPT_T,
        "ref_text": REF_PROMPT_TEXT,
        "source": str(REF_NARRATION),
    }
    meta_ok = False
    if REF_PROMPT_META.exists() and REF_PROMPT_WAV.exists():
        try:
            prev = json.loads(REF_PROMPT_META.read_text(encoding="utf-8"))
            meta_ok = (
                prev.get("ss") == meta["ss"]
                and prev.get("t") == meta["t"]
                and prev.get("ref_text") == meta["ref_text"]
            )
        except Exception:
            meta_ok = False
    if (
        meta_ok
        and REF_PROMPT_WAV.exists()
        and REF_PROMPT_WAV.stat().st_size > 1000
    ):
        return REF_PROMPT_WAV
    ref = ensure_ref()
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            REF_PROMPT_SS,
            "-t",
            REF_PROMPT_T,
            "-i",
            str(ref),
            "-ac",
            "1",
            "-ar",
            "24000",
            str(REF_PROMPT_WAV),
        ],
        check=True,
    )
    REF_PROMPT_META.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return REF_PROMPT_WAV


def _load_qwen_model():
    global _qwen_model
    if _qwen_model is not None:
        return _qwen_model
    if str(MLX_AUDIO_ROOT) not in sys.path:
        sys.path.insert(0, str(MLX_AUDIO_ROOT))
    from mlx_audio.tts.utils import load_model  # type: ignore

    print(f"[segment_studio] loading Qwen3 clone model {QWEN_MODEL} …", flush=True)
    _qwen_model = load_model(QWEN_MODEL)
    return _qwen_model


def _write_f32_wav_via_ffmpeg(samples, sample_rate: int, out_wav: Path) -> None:
    """Write mono float32 PCM without soundfile dependency."""
    import numpy as np

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    raw = out_wav.with_suffix(".f32le")
    arr = np.asarray(samples, dtype=np.float32).reshape(-1)
    raw.write_bytes(arr.tobytes())
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "f32le",
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-i",
            str(raw),
            "-ac",
            "1",
            "-ar",
            "44100",
            str(out_wav),
        ],
        check=True,
    )
    raw.unlink(missing_ok=True)


def synthesize_qwen_clone(text: str, out_wav: Path) -> float:
    """Clone reference speaker via mlx-audio Qwen3-TTS."""
    import numpy as np

    model = _load_qwen_model()
    prompt = ensure_clone_prompt()
    token_limit = min(900, max(260, len(text) * 5))
    # API compatibility: some builds use lang_code, others language
    kwargs = dict(
        text=text,
        ref_audio=str(prompt),
        ref_text=REF_PROMPT_TEXT,
        temperature=0.64,
        top_k=35,
        top_p=0.94,
        repetition_penalty=1.06,
        max_tokens=token_limit,
        verbose=False,
    )
    try:
        result = list(model.generate(**kwargs, lang_code="Chinese"))[0]
    except TypeError:
        result = list(model.generate(**kwargs, language="Chinese"))[0]
    audio = np.asarray(result.audio, dtype=np.float32)
    # mlx array → numpy
    if hasattr(audio, "tolist") and not isinstance(audio, np.ndarray):
        audio = np.array(audio.tolist(), dtype=np.float32)
    sr = int(getattr(result, "sample_rate", 24000) or 24000)
    peak = max(0.001, float(np.max(np.abs(audio))))
    audio = audio * min(1.0, 0.86 / peak)
    pad_pre = np.zeros(int(0.08 * sr), dtype=np.float32)
    pad_post = np.zeros(int(0.24 * sr), dtype=np.float32)
    segment = np.concatenate([pad_pre, audio.reshape(-1), pad_post])
    _write_f32_wav_via_ffmpeg(segment, sr, out_wav)
    return ffprobe_duration(out_wav)


def synthesize_tts(
    text: str,
    out_wav: Path,
    *,
    voice: str = "zh-CN-YunxiNeural",
    backend: str = "auto",
) -> tuple[float, str]:
    """Generate speech.

    backend: auto | clone | edge | say
      auto = clone (Qwen3) → edge-tts → say → silence
    Returns (duration_s, backend_used).
    """
    text = (text or "").strip()
    if not text:
        make_silence(MIN_SCENE_S, out_wav)
        return MIN_SCENE_S, "silence"
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    tmp_mp3 = out_wav.with_suffix(".mp3")
    order = {
        "auto": ["clone", "edge", "say"],
        "clone": ["clone", "edge", "say"],
        "edge": ["edge", "say"],
        "say": ["say"],
    }.get(backend, ["clone", "edge", "say"])

    errors: list[str] = []

    for kind in order:
        try:
            if kind == "clone":
                d = synthesize_qwen_clone(text, out_wav)
                if d > 0.2 and out_wav.exists() and out_wav.stat().st_size > 500:
                    return d, "clone"
                errors.append("clone: empty output")
            elif kind == "edge":
                r = subprocess.run(
                    [
                        "edge-tts",
                        "--voice",
                        voice,
                        "--text",
                        text,
                        "--write-media",
                        str(tmp_mp3),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if r.returncode == 0 and tmp_mp3.exists() and tmp_mp3.stat().st_size > 500:
                    to_wav(tmp_mp3, out_wav)
                    tmp_mp3.unlink(missing_ok=True)
                    return ffprobe_duration(out_wav), "edge"
                errors.append(f"edge: {(r.stderr or r.stdout or '')[:200]}")
            elif kind == "say":
                aiff = out_wav.with_suffix(".aiff")
                subprocess.run(
                    ["say", "-v", "Tingting", "-o", str(aiff), text],
                    check=True,
                    timeout=120,
                )
                to_wav(aiff, out_wav)
                aiff.unlink(missing_ok=True)
                return ffprobe_duration(out_wav), "say"
        except Exception as e:
            errors.append(f"{kind}: {e}")
            print(f"tts {kind} failed:", e, file=sys.stderr)

    # last resort: estimated silence
    est = max(MIN_SCENE_S, min(40.0, len(text) / 4.5 + 0.4))
    make_silence(est, out_wav)
    print("tts all failed:", errors, file=sys.stderr)
    return est, "silence"


def adapt_duration(audio_s: float, min_s: float = MIN_SCENE_S) -> float:
    """画面时长适配旁白：默认跟旁白走（静帧 hold），不低于 min。"""
    return round(max(min_s, audio_s + PAD_AFTER_VO), 3)


def build_scene_audio(item: dict) -> Path:
    """Materialize one scene's audio file → SEG_AUDIO/{id}.wav, update duration."""
    SEG_AUDIO.mkdir(parents=True, exist_ok=True)
    sid = item["id"]
    out = SEG_AUDIO / f"{sid}.wav"
    src = item.get("audio_source") or "reference_slice"
    if not item.get("enabled", True):
        make_silence(0.05, out)
        item["duration_s"] = 0.05
        return out

    if src == "silence":
        dur = max(MIN_SCENE_S, float(item.get("duration_s") or MIN_SCENE_S))
        make_silence(dur, out)
        item["duration_s"] = adapt_duration(dur, float(item.get("min_duration_s") or MIN_SCENE_S))
        return out

    if src == "tts" and item.get("tts_file"):
        tts_path = Path(item["tts_file"])
        if not tts_path.is_absolute():
            tts_path = ROOT / tts_path
        if tts_path.exists():
            to_wav(tts_path, out)
            audio_s = ffprobe_duration(out)
            item["duration_s"] = adapt_duration(
                audio_s, float(item.get("min_duration_s") or MIN_SCENE_S)
            )
            # pad visual hold if needed
            if item["duration_s"] > audio_s + 0.05:
                pad = WORK / f"{sid}-pad.wav"
                make_silence(item["duration_s"] - audio_s, pad)
                merged = WORK / f"{sid}-merged.wav"
                concat_wavs([out, pad], merged)
                shutil.copy2(merged, out)
            return out

    # reference_slice (default)
    a = float(item.get("reference_start") or 0)
    b = float(item.get("reference_end") or (a + MIN_SCENE_S))
    audio_s = extract_reference_slice(a, b, out)
    item["duration_s"] = adapt_duration(
        audio_s, float(item.get("min_duration_s") or MIN_SCENE_S)
    )
    if item["duration_s"] > audio_s + 0.05:
        pad = WORK / f"{sid}-pad.wav"
        make_silence(item["duration_s"] - audio_s, pad)
        merged = WORK / f"{sid}-merged.wav"
        concat_wavs([out, pad], merged)
        shutil.copy2(merged, out)
    return out


def concat_wavs(parts: list[Path], out: Path) -> None:
    """Concat wavs via intermediate re-encode."""
    # use filter_complex amix? simpler: convert list to mp3 concat then wav
    mp3s = []
    for i, p in enumerate(parts):
        m = WORK / f"cpart-{i}.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(p),
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(m),
            ],
            check=True,
        )
        mp3s.append(m)
    tmp_mp3 = WORK / "cmerged.mp3"
    concat_audio(mp3s, tmp_mp3)
    to_wav(tmp_mp3, out)


def retime_and_apply_to_model(state: dict) -> dict:
    """Write start/end + subtitles + narration into content-model; rebuild full narration."""
    model = load_model()
    by_id = {s["id"]: s for s in state["scenes"]}
    cursor = 0.0
    new_scenes = []
    audio_parts: list[Path] = []

    # 顺序以 state.scenes 为准；内容以 content_snapshot / model 合并
    model_by_id = {s["id"]: s for s in (model.get("scenes") or [])}

    for item in state["scenes"]:
        base = item.get("content_snapshot") or model_by_id.get(item["id"]) or {
            "id": item["id"],
            "type": item.get("type") or "",
        }
        sc = copy.deepcopy(base)
        sc["id"] = item["id"]

        if not item.get("enabled", True):
            sc["enabled"] = False
            sc["start"] = round(cursor, 3)
            sc["end"] = round(cursor, 3)
            sc["duration"] = 0
            new_scenes.append(sc)
            continue

        wav = build_scene_audio(item)
        # ensure exact scene duration file
        d = float(item["duration_s"])
        # trim/pad wav to d
        fixed = WORK / f"{item['id']}-fixed.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(wav),
                "-t",
                f"{d:.3f}",
                "-af",
                f"apad=whole_dur={d:.3f}",
                "-ac",
                "1",
                "-ar",
                "44100",
                str(fixed),
            ],
            check=True,
        )
        audio_parts.append(fixed)

        sc = dict(sc)
        sc["enabled"] = True
        sc["start"] = round(cursor, 3)
        sc["end"] = round(cursor + d, 3)
        sc["duration"] = d
        text = (item.get("narration_text") or "").strip()
        if text:
            sc["narration"] = text
            # single full-scene subtitle + split by punctuation for timed stills
            cues = split_cues(text)
            if not cues:
                cues = [text]
            sc["subtitles"] = []
            t0 = sc["start"]
            total_chars = max(1, sum(len(c) for c in cues))
            for c in cues:
                share = len(c) / total_chars
                t1 = t0 + d * share
                sc["subtitles"].append(
                    {"t": round(t0, 3), "text": c}
                )
                t0 = t1
        new_scenes.append(sc)
        cursor += d

    model["scenes"] = new_scenes
    # archive disabled
    model.setdefault("segment_studio", {})["disabled_ids"] = [
        s["id"] for s in state["scenes"] if not s.get("enabled", True)
    ]
    model["segment_studio"]["total_duration_s"] = round(cursor, 3)
    save_model(model)

    # full narration track
    WORK.mkdir(parents=True, exist_ok=True)
    if audio_parts:
        full_mp3 = WORK / "full-narration.mp3"
        concat_audio(audio_parts, full_mp3)
        # working + public 旁白轨；绝不覆盖 reference-narration.mp3
        shutil.copy2(full_mp3, WORK_NARRATION)
        PUBLIC_NARRATION.parent.mkdir(parents=True, exist_ok=True)
        if PUBLIC_NARRATION.is_symlink() or PUBLIC_NARRATION.exists():
            try:
                PUBLIC_NARRATION.unlink()
            except OSError:
                pass
        shutil.copy2(full_mp3, PUBLIC_NARRATION)
    save_state(state)
    return {
        "total_duration_s": round(cursor, 3),
        "scene_count": len(new_scenes),
        "disabled": model["segment_studio"]["disabled_ids"],
        "narration": str(PUBLIC_NARRATION),
    }


def split_cues(text: str) -> list[str]:
    import re

    parts = [p.strip() for p in re.split(r"(?<=[。！？；])", text) if p.strip()]
    if len(parts) <= 1:
        parts = [p.strip() for p in re.split(r"(?<=[，、])", text) if p.strip()]
    out: list[str] = []
    for part in parts:
        if len(part) <= 28:
            out.append(part)
            continue
        buf = ""
        for ch in part:
            buf += ch
            if len(buf) >= 24 and ch in "，、； ":
                out.append(buf.strip())
                buf = ""
        if buf.strip():
            out.append(buf.strip())
    return out or ([text] if text else [])


def _film_python() -> str:
    """export-full-film needs Pillow; prefer system python if venv lacks PIL."""
    try:
        import PIL  # noqa: F401

        return sys.executable
    except ImportError:
        return "python3"


def rebuild_film() -> dict:
    """Retime model + export full film."""
    state = load_state()
    meta = retime_and_apply_to_model(state)
    r = subprocess.run(
        [_film_python(), str(ROOT / "scripts" / "export-full-film-video.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    meta["export_ok"] = r.returncode == 0
    meta["export_log_tail"] = (r.stdout or "")[-1500:] + (r.stderr or "")[-800:]
    from datetime import datetime, timezone

    state["last_rebuild"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    return meta


def cmd_list(_: argparse.Namespace) -> int:
    state = load_state()
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def cmd_init(_: argparse.Namespace) -> int:
    state = init_state()
    print(json.dumps({"ok": True, "scenes": len(state["scenes"])}, ensure_ascii=False))
    return 0


def find_scene(state: dict, sid: str) -> dict:
    for s in state["scenes"]:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def cmd_hide(args: argparse.Namespace) -> int:
    state = load_state()
    s = find_scene(state, args.id)
    s["enabled"] = False
    save_state(state)
    print(json.dumps({"ok": True, "id": args.id, "enabled": False}, ensure_ascii=False))
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    state = load_state()
    s = find_scene(state, args.id)
    s["enabled"] = True
    save_state(state)
    print(json.dumps({"ok": True, "id": args.id, "enabled": True}, ensure_ascii=False))
    return 0


def cmd_set_narration(args: argparse.Namespace) -> int:
    state = load_state()
    s = find_scene(state, args.id)
    s["narration_text"] = args.text.strip()
    # mark dirty — needs regen unless still using reference intentionally
    if args.keep_reference:
        s["audio_source"] = "reference_slice"
    else:
        s["audio_source"] = "tts"
        s["tts_file"] = None  # force regen
    save_state(state)
    print(
        json.dumps(
            {
                "ok": True,
                "id": args.id,
                "narration_text": s["narration_text"],
                "audio_source": s["audio_source"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_regen_tts(args: argparse.Namespace) -> int:
    state = load_state()
    s = find_scene(state, args.id)
    text = (args.text or s.get("narration_text") or "").strip()
    if not text:
        print(json.dumps({"ok": False, "error": "empty narration"}, ensure_ascii=False))
        return 2
    s["narration_text"] = text
    SEG_AUDIO.mkdir(parents=True, exist_ok=True)
    out = SEG_AUDIO / f"{args.id}-tts.wav"
    backend = getattr(args, "backend", None) or "auto"
    dur, used = synthesize_tts(text, out, voice=args.voice, backend=backend)
    s["audio_source"] = "tts"
    s["tts_backend"] = used
    s["tts_file"] = str(out.relative_to(ROOT))
    s["duration_s"] = adapt_duration(dur, float(s.get("min_duration_s") or MIN_SCENE_S))
    save_state(state)
    print(
        json.dumps(
            {
                "ok": True,
                "id": args.id,
                "audio_s": round(dur, 3),
                "duration_s": s["duration_s"],
                "tts_file": s["tts_file"],
                "audio_source": "tts",
                "backend": used,
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    if args.film:
        meta = rebuild_film()
    else:
        state = load_state()
        meta = retime_and_apply_to_model(state)
        meta["export_ok"] = None
    print(json.dumps({"ok": True, **meta}, ensure_ascii=False, indent=2))
    return 0 if meta.get("export_ok") is not False else 1


def cmd_api_payload(_: argparse.Namespace) -> int:
    """Compact list for editor UI."""
    state = load_state()
    rows = []
    t = 0.0
    for s in state["scenes"]:
        d = float(s.get("duration_s") or 0)
        rows.append(
            {
                "id": s["id"],
                "title": s.get("title") or s["id"],
                "enabled": bool(s.get("enabled", True)),
                "type": s.get("type"),
                "layer": s.get("layer"),
                "narration_text": s.get("narration_text") or "",
                "audio_source": s.get("audio_source"),
                "duration_s": d,
                "tts_backend": s.get("tts_backend"),
                "timeline_start": round(t, 3) if s.get("enabled", True) else None,
                "timeline_end": round(t + d, 3) if s.get("enabled", True) else None,
            }
        )
        if s.get("enabled", True):
            t += d
    print(
        json.dumps(
            {
                "ok": True,
                "total_duration_s": round(t, 3),
                "last_rebuild": state.get("last_rebuild"),
                "scenes": rows,
            },
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="CW4 segment studio")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Initialize state from content-model")
    sub.add_parser("list", help="Dump full state JSON")
    sub.add_parser("api-list", help="Compact list for editor")

    p = sub.add_parser("hide")
    p.add_argument("--id", required=True)

    p = sub.add_parser("enable")
    p.add_argument("--id", required=True)

    p = sub.add_parser("set-narration")
    p.add_argument("--id", required=True)
    p.add_argument("--text", required=True)
    p.add_argument(
        "--keep-reference",
        action="store_true",
        help="Keep reference audio slice (only update text/subtitles)",
    )

    p = sub.add_parser("regen-tts")
    p.add_argument("--id", required=True)
    p.add_argument("--text", default="")
    p.add_argument("--voice", default="zh-CN-YunxiNeural")
    p.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "clone", "edge", "say"],
        help="auto=Qwen3克隆→edge→say；clone=强制参考声线",
    )

    p = sub.add_parser("rebuild")
    p.add_argument(
        "--film",
        action="store_true",
        help="Also run export-full-film-video.py",
    )

    args = ap.parse_args()
    if not STATE_PATH.exists() and args.cmd != "init":
        init_state()

    return {
        "init": cmd_init,
        "list": cmd_list,
        "api-list": cmd_api_payload,
        "hide": cmd_hide,
        "enable": cmd_enable,
        "set-narration": cmd_set_narration,
        "regen-tts": cmd_regen_tts,
        "rebuild": cmd_rebuild,
    }[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
