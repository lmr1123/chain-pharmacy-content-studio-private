#!/usr/bin/env python3
"""P0 regression tests for safe business-video delivery publication."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

from generate_business_video import (
    build_delivery_qa,
    delivery_publish_readiness,
    publish_business_delivery,
)


def _write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_test_video(path: Path, duration_s: float = 0.4) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise unittest.SkipTest("ffmpeg is required for delivery media QA tests")
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s=320x180:r=10:d={duration_s}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:sample_rate=48000:duration={duration_s}",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )


def _write_test_wav(path: Path, duration_s: float = 0.2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 8000
    frames = int(sample_rate * duration_s)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\0\0" * frames)


def _successful_status(
    out_dir: Path, template: str = "product-video-faithful-v1"
) -> dict:
    segment_ids = (
        (
            "intro",
            "character",
            "mechanism",
            "symptoms",
            "treatment",
            "medication",
            "summary",
        )
        if template == "health-video-reference-tech-v1"
        else (
            "opening",
            "brand",
            "faithful",
            "efficacy",
            "features",
            "audience",
            "combination",
            "summary",
        )
    )
    segment_count = len(segment_ids)
    mp4 = out_dir / "主题_培训视频_v1.mp4"
    _write_test_video(mp4, segment_count * 0.2)
    (out_dir / "content.json").write_text(
        json.dumps(
            {
                "theme": "测试主题",
                "sections": [
                    {"title": f"第{index + 1}段", "narration": "审核旁白"}
                    for index in range(segment_count)
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write(out_dir / "storyboard.html", "<html>storyboard</html>")
    _write(out_dir / "gap-report.json", '{"gaps":[]}')
    _write(out_dir / "DELIVERY.md", "delivery")
    first_segment = out_dir / "segments" / f"{segment_ids[0]}.mp4"
    _write_test_video(first_segment, 0.2)
    for index, segment_id in enumerate(segment_ids):
        _write_test_wav(out_dir / "audio" / "sections" / f"{segment_id}.wav")
        if index:
            target = out_dir / "segments" / f"{segment_id}.mp4"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(first_segment, target)
    if template == "health-video-reference-tech-v1":
        full_source = {
            "theme_package": {
                "approval": {
                    "visuals_approved": True,
                    "approved_by": "业务审核人",
                    "approved_at": "2026-08-08T12:00:00+08:00",
                    "approved_payload_sha256": "c" * 64,
                },
                "payload_sha256": "c" * 64,
            }
        }
    else:
        full_source = {
            "authorized_product_packshot": True,
            "approval": {
                "ok": True,
                "approved": True,
                "approved_by": "业务审核人",
                "approved_at": "2026-08-08T12:00:00+08:00",
                "authorization_reference": "AUTH-TEST-001",
                "approved_content_sha256": "a" * 64,
                "approved_product_image_sha256": "b" * 64,
            },
        }
    status = {
        "package_ok": True,
        "template": template,
        "mode": "full",
        "want_tts": True,
        "want_mp4": True,
        "voice_id": "test-voice",
        "tts": {"ok": True},
        "mp4": {"ok": True, "path": str(mp4)},
        "full": {
            "ok": True,
            **full_source,
            "content_gaps": [],
            "segment_plan": {
                segment_id: {"status": "included"} for segment_id in segment_ids
            },
            "segments": {
                segment_id: {"status": "included"} for segment_id in segment_ids
            },
        },
    }
    status["qa"] = build_delivery_qa(out_dir, status)
    (out_dir / "delivery-qa.json").write_text(
        json.dumps(status["qa"], ensure_ascii=False), encoding="utf-8"
    )
    if status["qa"]["state"] != "qa_passed":
        raise AssertionError(status["qa"])
    return status


class DeliveryPublishTests(unittest.TestCase):
    def test_failure_does_not_create_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "run"
            dest = root / "delivery" / "task-a"
            _write(out_dir / "DELIVERY.md")
            status = _successful_status(out_dir)
            status["mp4"] = {"ok": False, "error": "render failed"}

            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("mp4" in reason.lower() for reason in reasons))

            published = publish_business_delivery(out_dir, dest, status)
            self.assertFalse(published["published"])
            self.assertFalse(dest.exists())

    def test_success_publishes_only_business_whitelist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "run"
            dest = root / "delivery" / "task-b"
            _write(out_dir / "DELIVERY.md", "delivery")
            _write(out_dir / "run-status.json", json.dumps({"raw": True}))
            _write(out_dir / "full-render-status.json")
            _write(out_dir / "render-workspace" / "node_modules" / "pkg" / "index.js")
            _write(out_dir / "render-workspace" / "raw-stack.txt")
            _write(out_dir / "source" / "private-input.docx")
            status = _successful_status(out_dir)

            published = publish_business_delivery(out_dir, dest, status)

            self.assertTrue(published["published"])
            files = {
                p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()
            }
            self.assertEqual(
                files,
                {
                    "DELIVERY.md",
                    "delivery-qa.json",
                    "storyboard.html",
                    "content.json",
                    "gap-report.json",
                    *{
                        f"audio/sections/{segment_id}.wav"
                        for segment_id in (
                            "opening",
                            "brand",
                            "faithful",
                            "efficacy",
                            "features",
                            "audience",
                            "combination",
                            "summary",
                        )
                    },
                    "主题_培训视频_v1.mp4",
                },
            )
            self.assertFalse((dest / "render-workspace").exists())
            self.assertFalse((dest / "run-status.json").exists())
            self.assertFalse((dest / "source").exists())

    def test_failed_rerun_never_overwrites_old_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "run"
            dest = root / "delivery" / "task-c"
            _write(out_dir / "DELIVERY.md", "new failed delivery")
            _write(dest / "终稿.mp4", "previous good delivery")
            status = _successful_status(out_dir)
            status["full"]["qa"] = {"ok": False, "error": "black frame"}

            published = publish_business_delivery(out_dir, dest, status)

            self.assertFalse(published["published"])
            self.assertEqual(
                (dest / "终稿.mp4").read_text(encoding="utf-8"),
                "previous good delivery",
            )
            self.assertFalse((dest / "DELIVERY.md").exists())

    def test_missing_qa_non_final_mode_and_post_qa_mutation_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            status = _successful_status(out_dir)
            qa = status.pop("qa")

            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("QA" in reason for reason in reasons))

            status["qa"] = qa
            status["mode"] = "plan"
            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("mode=full" in reason for reason in reasons))

            status["mode"] = "audio-shell"
            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("mode=full" in reason for reason in reasons))

            status["mode"] = "full"
            with Path(status["mp4"]["path"]).open("ab") as handle:
                handle.write(b"changed-after-qa")
            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("changed" in reason for reason in reasons))

    def test_source_approval_hashes_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "product"
            status = _successful_status(out_dir)
            status["full"]["approval"].pop("approved_content_sha256")
            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("status changed" in reason for reason in reasons))
            qa = build_delivery_qa(out_dir, status)
            self.assertEqual(qa["state"], "qa_failed")
            self.assertFalse(
                next(item for item in qa["checks"] if item["id"] == "source_gate")[
                    "passed"
                ]
            )

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "health"
            status = _successful_status(
                out_dir, template="health-video-reference-tech-v1"
            )
            status["full"]["theme_package"]["approval"].pop(
                "approved_payload_sha256"
            )
            status["full"]["theme_package"].pop("payload_sha256")
            qa = build_delivery_qa(out_dir, status)
            self.assertEqual(qa["state"], "qa_failed")

    def test_post_qa_wav_and_qa_report_mutation_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            status = _successful_status(out_dir)
            with (
                out_dir / "audio" / "sections" / "opening.wav"
            ).open("ab") as handle:
                handle.write(b"tampered")
            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("artifact" in reason.lower() for reason in reasons))

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            status = _successful_status(out_dir)
            (out_dir / "delivery-qa.json").write_text(
                '{"state":"tampered"}', encoding="utf-8"
            )
            ready, reasons = delivery_publish_readiness(status)
            self.assertFalse(ready)
            self.assertTrue(any("QA report" in reason for reason in reasons))

    def test_corrupt_segment_and_truncated_final_duration_fail_qa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            status = _successful_status(out_dir)
            (out_dir / "segments" / "opening.mp4").write_text(
                "not a video", encoding="utf-8"
            )
            qa = build_delivery_qa(out_dir, status)
            self.assertEqual(qa["state"], "qa_failed")
            self.assertFalse(
                next(
                    item
                    for item in qa["checks"]
                    if item["id"] == "segment_consistency"
                )["passed"]
            )

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            status = _successful_status(out_dir)
            _write_test_video(Path(status["mp4"]["path"]), 0.2)
            qa = build_delivery_qa(out_dir, status)
            self.assertEqual(qa["state"], "qa_failed")

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            status = _successful_status(out_dir)
            _write_test_wav(
                out_dir / "audio" / "sections" / "opening.wav",
                duration_s=20.0,
            )
            qa = build_delivery_qa(out_dir, status)
            self.assertEqual(qa["state"], "qa_failed")

    def test_stale_full_narration_is_not_published_by_segment_full_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "run"
            dest = root / "delivery"
            _write(
                out_dir / "audio" / "full-narration.wav",
                "stale-not-a-wav",
            )
            status = _successful_status(out_dir)

            published = publish_business_delivery(out_dir, dest, status)

            self.assertTrue(published["published"])
            self.assertFalse((dest / "audio" / "full-narration.wav").exists())


if __name__ == "__main__":
    unittest.main()
