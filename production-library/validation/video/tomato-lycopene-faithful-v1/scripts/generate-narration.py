#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = Path(os.environ.get('PROJECT_FILE', ROOT / 'project.json')).resolve()
SOURCE_AUDIO = Path('/Users/liminrong/Downloads/商品培训课件4/商品培训课件4.mp3')
OUT = ROOT / 'audio'
MODEL = 'mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16'
REF_TEXT = '美国《时代杂志》评选的，对人类健康贡献最大的十种健康食品中。'

def split_cues(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r'(?<=[。！？；])', text) if p.strip()]
    out: list[str] = []
    for part in parts:
        if len(part) <= 30:
            out.append(part)
            continue
        pieces = [p for p in re.split(r'(?<=[，：])', part) if p]
        buf = ''
        for piece in pieces:
            if buf and len(buf) + len(piece) > 30:
                out.append(buf)
                buf = piece
            else:
                buf += piece
        if buf:
            out.append(buf)
    return out

def timestamp(value: float) -> str:
    ms = max(0, round(value * 1000))
    hour, ms = divmod(ms, 3600000)
    minute, ms = divmod(ms, 60000)
    second, ms = divmod(ms, 1000)
    return f'{hour:02d}:{minute:02d}:{second:02d},{ms:03d}'

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ref = OUT / 'reference-prompt.wav'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '0.58', '-t', '5.4', '-i', str(SOURCE_AUDIO), '-ac', '1', '-ar', '24000', str(ref)], check=True)
    project = json.loads(PROJECT_FILE.read_text(encoding='utf-8'))
    model = load_model(MODEL)
    chunks: list[np.ndarray] = []
    timings: list[dict] = []
    cursor = 0.0
    target_rate = 24000
    for index, scene in enumerate(project['scenes']):
        print(f'[{index+1}/{len(project["scenes"])}] {scene["id"]}: {len(scene["narration"])} chars', flush=True)
        mx.random.seed(20260802 + index * 97)
        token_limit = min(900, max(260, len(scene['narration']) * 5))
        result = list(model.generate(text=scene['narration'], ref_audio=str(ref), ref_text=REF_TEXT, lang_code='Chinese', temperature=.64, top_k=35, top_p=.94, repetition_penalty=1.06, max_tokens=token_limit, verbose=True))[0]
        audio = np.asarray(result.audio, dtype=np.float32)
        if result.sample_rate != target_rate:
            raw = OUT / f'{index+1:02d}-raw.wav'
            converted = OUT / f'{index+1:02d}-resampled.wav'
            sf.write(raw, audio, result.sample_rate)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(raw), '-ar', str(target_rate), '-ac', '1', str(converted)], check=True)
            audio, _ = sf.read(converted, dtype='float32')
        peak = max(.001, float(np.max(np.abs(audio))))
        audio = audio * min(1.0, .86 / peak)
        segment = np.concatenate([np.zeros(int(.08 * target_rate), dtype=np.float32), audio, np.zeros(int(.24 * target_rate), dtype=np.float32)])
        segment_path = OUT / f'{index+1:02d}-{scene["id"]}.wav'
        sf.write(segment_path, segment, target_rate)
        duration = len(segment) / target_rate
        scene['duration'] = round(max(duration + .32, 5.0), 3)
        chunks.append(segment)
        timings.append({'scene_id': scene['id'], 'start': round(cursor, 3), 'end': round(cursor + duration, 3), 'duration': round(duration, 3), 'file': segment_path.name})
        cursor += duration
    full = np.concatenate(chunks)
    sf.write(OUT / 'narration.wav', full, target_rate)
    srt: list[str] = []
    number = 1
    for scene, timing in zip(project['scenes'], timings):
        cues = split_cues(scene['narration'])
        total = max(1, sum(len(item) for item in cues))
        local = timing['start']
        for cue in cues:
            duration = (timing['duration'] - .1) * len(cue) / total
            end = local + duration
            srt.extend([str(number), f'{timestamp(local)} --> {timestamp(end)}', cue, ''])
            number += 1
            local = end
    (OUT / 'narration.srt').write_text('\n'.join(srt), encoding='utf-8')
    (OUT / 'timing.json').write_text(json.dumps({'total_duration': round(len(full) / target_rate, 3), 'segments': timings}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    PROJECT_FILE.write_text(json.dumps(project, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'audio': str(OUT / 'narration.wav'), 'duration': round(len(full) / target_rate, 3)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
