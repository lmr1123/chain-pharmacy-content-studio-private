#!/usr/bin/env python3
"""HeyGen Image-to-Video 15s 样片：本机音频驱动口型（禁止 HeyGen 再配音）。

用法：
  export HEYGEN_API_KEY=sk_...
  python3 heygen_15s_sample.py
  # 指定人像 / 输出（业务对比多版本）：
  python3 heygen_15s_sample.py --image inputs/portrait-business-chin-v1.jpg \\
      --out outputs/sample-15s-business-chin-v1.mp4 --tag business_chin_v1

素材默认：
  inputs/portrait-pharmacist-standing-v1.jpg
  inputs/narration-15s.mp3
输出：
  outputs/sample-15s.mp4
  work/job-state.json 更新

姿态约束（motion_prompt + expressiveness）：
  - 画面仅 1 人
  - 双手多数时间自然下垂（勿托腮僵住）
  - 偶有抬手/强调，像真实培训师
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "outputs"
STATE = WORK / "job-state.json"

DEFAULT_IMAGE = ROOT / "inputs" / "portrait-pharmacist-standing-v1.jpg"
if not DEFAULT_IMAGE.exists():
    DEFAULT_IMAGE = ROOT / "inputs" / "portrait-pharmacist-standing-v1-cutout.png"
DEFAULT_AUDIO = ROOT / "inputs" / "narration-15s.mp3"
DEFAULT_OUT = OUT / "sample-15s.mp4"

API = "https://api.heygen.com"
UPLOAD = "https://upload.heygen.com"

# 培训师真实肢体语言：双手为主放下，偶有抬手；严格单人
# 源图若是托腮/抱臂，也要求动画中放下双手，勿锁死证件照姿势
MOTION_PROMPT = (
    "Single person only — one professional female trainer, no second person, "
    "no extra people, no duplicate limbs. "
    "Do NOT keep the chin-rest or arm-crossed photo pose frozen. "
    "Lower both hands to a relaxed natural position at the sides for most of the clip, "
    "like a calm standing presenter. "
    "Occasionally raise one hand slightly for emphasis while speaking, "
    "like a real corporate trainer giving a short pharmacy training talk — "
    "subtle, natural, infrequent. "
    "Soft natural head nods and small upper-body micro-movements only. "
    "No exaggerated waving, no continuous gesturing, no pointing repeatedly, "
    "no walking, no props, no hand on chin."
)
# medium：允许偶发手势；low 过静、high 易过度
EXPRESSIVENESS = "medium"

# runtime paths set in main()
IMAGE: Path = DEFAULT_IMAGE
AUDIO: Path = DEFAULT_AUDIO
SAMPLE_OUT: Path = DEFAULT_OUT
RUN_TAG: str = "default"


def load_key() -> str:
    key = (
        os.environ.get("HEYGEN_API_KEY")
        or os.environ.get("HEYGEN_API_TOKEN")
        or os.environ.get("HEYGEN_KEY")
        or ""
    ).strip()
    if not key:
        print(
            "缺少 HEYGEN_API_KEY。\n"
            "请在 https://app.heygen.com  → Settings → API 复制 Key 后执行：\n"
            "  export HEYGEN_API_KEY='你的key'\n"
            "  python3 scripts/heygen_15s_sample.py",
            file=sys.stderr,
        )
        sys.exit(2)
    return key


def http_json(method: str, url: str, headers: dict, data: bytes | None = None, timeout: int = 120, retries: int = 3):
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype or body[:1] in (b"{", b"["):
                    return json.loads(body.decode("utf-8"))
                return {"raw": body}
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} {url}: {err[:800]}") from e
        except Exception as e:
            last_err = e
            if attempt < retries:
                wait = 2 * attempt
                print(f"  network retry {attempt}/{retries} after {wait}s: {e}")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP failed {url}: {e}") from e
    raise RuntimeError(f"HTTP failed {url}: {last_err}")


def upload_asset_v1(path: Path, api_key: str) -> dict:
    """旧版二进制上传（社区常用，返回 id/url）。"""
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    data = path.read_bytes()
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": mime,
    }
    return http_json("POST", f"{UPLOAD}/v1/asset", headers, data=data)


def upload_asset_v3(path: Path, api_key: str) -> dict:
    """multipart /v3/assets"""
    boundary = "----HeyGenBoundary7MA4YWxkTrZu0gW"
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    file_bytes = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    return http_json("POST", f"{API}/v3/assets", headers, data=body)


def upload(path: Path, api_key: str) -> tuple[str | None, str | None, dict]:
    """返回 (asset_id, url, raw_response)"""
    last_err = None
    for fn in (upload_asset_v1, upload_asset_v3):
        try:
            r = fn(path, api_key)
            data = r.get("data") or r
            asset_id = data.get("id") or data.get("asset_id") or data.get("image_key")
            url = data.get("url") or data.get("image_url") or data.get("file_url")
            if asset_id or url:
                return asset_id, url, r
            last_err = RuntimeError(f"unexpected upload response: {json.dumps(r)[:400]}")
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"upload failed for {path.name}: {last_err}")


def _scrub(o):
    if isinstance(o, dict):
        return {k: _scrub(v) for k, v in o.items() if v is not None}
    if isinstance(o, list):
        return [_scrub(x) for x in o]
    return o


def create_image_to_video(
    *,
    api_key: str,
    image_url: str | None,
    image_asset_id: str | None,
    audio_url: str | None,
    audio_asset_id: str | None,
    title: str,
) -> str:
    """创建 Image-to-Video，返回 video_id。优先音频驱动，不用 script+voice。"""
    headers = {
        "X-Api-Key": api_key,
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    # v3 官方 image 块
    if image_asset_id:
        image_block_v3 = {"type": "asset_id", "asset_id": image_asset_id}
    elif image_url:
        image_block_v3 = {"type": "url", "url": image_url}
    else:
        raise RuntimeError("need image_asset_id or image_url")

    candidates: list[tuple[str, dict]] = []

    # ① 首选：POST /v3/videos  type=image + motion_prompt + expressiveness
    body_v3: dict = {
        "type": "image",
        "title": title,
        "image": image_block_v3,
        "motion_prompt": MOTION_PROMPT,
        "expressiveness": EXPRESSIVENESS,
        "aspect_ratio": "auto",
        "resolution": "720p",
        "output_format": "mp4",
    }
    if audio_asset_id:
        body_v3["audio_asset_id"] = audio_asset_id
    elif audio_url:
        body_v3["audio_url"] = audio_url
    candidates.append((f"{API}/v3/videos", body_v3))

    # ② 兼容旧 v2 talking_photo（无 motion_prompt 时仍可出片）
    voice_block: dict = {"type": "audio"}
    if audio_asset_id:
        voice_block["audio_asset_id"] = audio_asset_id
    elif audio_url:
        voice_block["audio_url"] = audio_url
    character: dict = {"type": "talking_photo"}
    if image_url:
        character["talking_photo_url"] = image_url
    if image_asset_id:
        character["talking_photo_id"] = image_asset_id
    body_v2 = {
        "video_inputs": [
            {
                "character": character,
                "voice": voice_block,
            }
        ],
        "dimension": {"width": 720, "height": 1280},
        "title": title,
    }
    candidates.append((f"{API}/v2/video/generate", body_v2))

    # ③ 更旧的 image 风格 body（部分租户仍可用）
    image_block_legacy = (
        {"type": "asset", "asset_id": image_asset_id}
        if image_asset_id
        else {"type": "url", "url": image_url}
    )
    body_legacy = {
        "type": "image",
        "title": title,
        "image": image_block_legacy,
        "motion_prompt": MOTION_PROMPT,
        "expressiveness": EXPRESSIVENESS,
    }
    if audio_asset_id:
        body_legacy["audio_asset_id"] = audio_asset_id
    elif audio_url:
        body_legacy["audio_url"] = audio_url
    candidates.append((f"{API}/v2/video/generate", body_legacy))

    errors = []
    for url, body in candidates:
        payload = json.dumps(_scrub(body)).encode("utf-8")
        try:
            r = http_json("POST", url, headers, data=payload)
            data = r.get("data") or r
            vid = data.get("video_id") or data.get("id") or data.get("videoId")
            if vid:
                print("create ok via", url, "video_id=", vid)
                print("  motion_prompt applied:", MOTION_PROMPT[:80] + "…")
                print("  expressiveness=", EXPRESSIVENESS)
                return str(vid)
            errors.append(f"{url}: no video_id in {json.dumps(r)[:300]}")
        except Exception as e:
            errors.append(f"{url}: {e}")
            continue
    raise RuntimeError("create video failed:\n" + "\n".join(errors))


def wait_video(api_key: str, video_id: str, timeout_s: int = 600) -> str:
    headers = {
        "X-Api-Key": api_key,
        "x-api-key": api_key,
        "Accept": "application/json",
    }
    urls = [
        f"{API}/v1/video_status.get?video_id={video_id}",
        f"{API}/v3/videos/{video_id}",
        f"{API}/v2/videos/{video_id}",
    ]
    t0 = time.time()
    last = ""
    while time.time() - t0 < timeout_s:
        for url in urls:
            try:
                r = http_json("GET", url, headers)
                data = r.get("data") or r
                status = (data.get("status") or data.get("video_status") or "").lower()
                last = json.dumps(data)[:200]
                if status in ("completed", "done", "success"):
                    vurl = (
                        data.get("video_url")
                        or data.get("url")
                        or data.get("video_url_caption")
                        or (data.get("video") or {}).get("url")
                    )
                    if vurl:
                        return vurl
                if status in ("failed", "error"):
                    raise RuntimeError(f"video failed: {data}")
                print(f"  status={status or '?'} elapsed={int(time.time()-t0)}s")
                break
            except RuntimeError:
                raise
            except Exception:
                continue
        time.sleep(8)
    raise TimeoutError(f"wait video timeout last={last}")


def download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=300) as resp:
        dest.write_bytes(resp.read())


def update_state(**kwargs):
    state = {}
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    hey = state.setdefault("heygen", {})
    # 多版本对比：按 tag 写入 variants，同时更新 latest 指针
    tag = kwargs.pop("run_tag", None) or RUN_TAG
    variant = hey.setdefault("variants", {}).setdefault(tag, {})
    variant.update(kwargs)
    variant["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    variant["image"] = str(IMAGE.relative_to(ROOT)) if IMAGE.is_relative_to(ROOT) else str(IMAGE)
    variant["sample_path"] = (
        str(SAMPLE_OUT.relative_to(ROOT)) if SAMPLE_OUT.is_relative_to(ROOT) else str(SAMPLE_OUT)
    )
    # 兼容旧字段：最新一次 run 同步到 heygen 顶层
    hey.update(kwargs)
    hey["latest_tag"] = tag
    hey["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args():
    p = argparse.ArgumentParser(description="HeyGen 15s audio-driven sample")
    p.add_argument(
        "--image",
        type=Path,
        default=None,
        help="人像路径（默认站姿药师）",
    )
    p.add_argument(
        "--audio",
        type=Path,
        default=None,
        help="旁白 mp3（默认 narration-15s.mp3）",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="输出 mp4 路径",
    )
    p.add_argument(
        "--tag",
        type=str,
        default="default",
        help="写入 job-state 的版本标签，便于业务对比",
    )
    p.add_argument(
        "--title",
        type=str,
        default="pharmacy-ppt-presenter-15s-sample",
        help="HeyGen 任务标题",
    )
    return p.parse_args()


def main():
    global IMAGE, AUDIO, SAMPLE_OUT, RUN_TAG
    args = parse_args()
    IMAGE = (args.image if args.image else DEFAULT_IMAGE).expanduser()
    if not IMAGE.is_absolute():
        IMAGE = (ROOT / IMAGE).resolve()
    AUDIO = (args.audio if args.audio else DEFAULT_AUDIO).expanduser()
    if not AUDIO.is_absolute():
        AUDIO = (ROOT / AUDIO).resolve()
    SAMPLE_OUT = (args.out if args.out else DEFAULT_OUT).expanduser()
    if not SAMPLE_OUT.is_absolute():
        SAMPLE_OUT = (ROOT / SAMPLE_OUT).resolve()
    RUN_TAG = args.tag

    if not IMAGE.exists():
        raise SystemExit(f"missing image: {IMAGE}")
    if not AUDIO.exists():
        raise SystemExit(f"missing audio: {AUDIO} — 先生成 narration-15s.mp3")

    api_key = load_key()
    print("tag:", RUN_TAG)
    print("image:", IMAGE)
    print("audio:", AUDIO, "size", AUDIO.stat().st_size)
    print("out:", SAMPLE_OUT)
    print("motion: hands-down default + occasional raise; single person; no chin-lock")
    print("expressiveness:", EXPRESSIVENESS)

    print("upload image…")
    img_id, img_url, _ = upload(IMAGE, api_key)
    print("  image_id=", img_id, "url=", (img_url or "")[:80])
    update_state(
        run_tag=RUN_TAG,
        image_asset_id=img_id,
        image_url=img_url,
        status="uploaded_image",
        motion_prompt=MOTION_PROMPT,
        expressiveness=EXPRESSIVENESS,
    )

    print("upload audio…")
    aud_id, aud_url, _ = upload(AUDIO, api_key)
    print("  audio_id=", aud_id, "url=", (aud_url or "")[:80])
    update_state(run_tag=RUN_TAG, audio_asset_id=aud_id, audio_url=aud_url, status="uploaded_audio")

    print("create 15s sample (audio-driven, no HeyGen TTS)…")
    video_id = create_image_to_video(
        api_key=api_key,
        image_url=img_url,
        image_asset_id=img_id,
        audio_url=aud_url,
        audio_asset_id=aud_id,
        title=args.title,
    )
    update_state(run_tag=RUN_TAG, sample_video_id=video_id, status="rendering")

    print("wait render…")
    vurl = wait_video(api_key, video_id)
    print("download…", vurl[:100])
    download(vurl, SAMPLE_OUT)
    update_state(
        run_tag=RUN_TAG,
        status="sample_ready",
        sample_download_url_redacted=True,
        sample_confirmed=False,
    )
    print("OK →", SAMPLE_OUT)
    print("请打开样片确认：单人 / 双手多放下 / 偶有抬手 / 本机旁白口型。")


if __name__ == "__main__":
    main()

