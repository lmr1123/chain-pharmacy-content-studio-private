#!/usr/bin/env python3

from __future__ import annotations

import copy
import contextlib
import io
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import business_job as bj  # noqa: E402

ENGINE = (
    ROOT
    / "production-library"
    / "engines"
    / "ingredient-health-edu-pptx-v1"
    / "export.mjs"
)
SOURCE = (
    ROOT
    / "production-library"
    / "templates"
    / "settled"
    / "kangaisen-lycopene-health-edu-v1"
    / "番茄红素_健康科普金样_v1.pptx"
)


def _png(path: Path, seed: int) -> None:
    width = height = 96
    color = ((seed * 47) % 180 + 30, (seed * 71) % 160 + 40, (seed * 29) % 150 + 55)
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            stripe = 20 if ((x + y + seed * 3) // 12) % 2 else 0
            row.extend((min(255, color[0] + stripe), min(255, color[1] + stripe), color[2], 255))
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(data)


class IngredientHealthEduPptxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not shutil.which("node"):
            raise unittest.SkipTest("node unavailable")
        if not SOURCE.is_file():
            raise unittest.SkipTest("settled canonical PPTX unavailable")
        cls.tmp = Path(tempfile.mkdtemp(prefix="ingredient-health-edu-pptx-"))
        draft = cls.tmp / "theme.json"
        proc = subprocess.run(
            [
                "node",
                str(ENGINE),
                "--emit-draft",
                str(draft),
                "--theme-name",
                "膳食纤维",
                "--theme-id",
                "test.fiber-v1",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise unittest.SkipTest(f"artifact-tool unavailable: {proc.stderr}")
        theme = json.loads(draft.read_text(encoding="utf-8"))
        assets_dir = cls.tmp / "assets"
        assets_dir.mkdir()
        bindings: list[tuple[dict[str, str], str, str]] = []
        for page in theme["pages"]:
            for text_id in page["texts"]:
                page["texts"][text_id] = "膳食纤维"
            for image_id in page["images"]:
                bindings.append(
                    (page["images"], image_id, f"s{page['slide']:02d}-i{image_id}")
                )
        for key in theme["template_images"]:
            bindings.append(
                (theme["template_images"], key, f"template-{len(bindings) + 1}")
            )
        for index, (owner, slot, asset_key) in enumerate(bindings, 1):
            asset = assets_dir / f"{index:03d}.png"
            _png(asset, index)
            theme["assets"][asset_key] = f"assets/{asset.name}"
            owner[slot] = asset_key
        theme["asset_authorization"] = {
            "confirmed": True,
            "authorized_by": "自动化业务验收",
            "authorization_reference": "test-generated-original-assets",
            "scope": "all-theme-images",
        }
        cls.complete = theme
        if len(bindings) != 69:
            raise AssertionError(f"unexpected image-slot count: {len(bindings)}")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _write_theme(self, name: str, theme: dict) -> Path:
        path = self.tmp / name
        path.write_text(
            json.dumps(theme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return path

    def _validate(self, theme_path: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
        report = theme_path.with_suffix(".report.json")
        proc = subprocess.run(
            [
                "node",
                str(ENGINE),
                "--theme",
                str(theme_path),
                "--validate-only",
                "--report",
                str(report),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return proc, json.loads(report.read_text(encoding="utf-8"))

    def test_complete_non_lycopene_theme_validates(self) -> None:
        proc, report = self._validate(self._write_theme("complete.json", self.complete))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["contract"]["text_slots"], 107)
        self.assertEqual(report["contract"]["slide_image_slots"], 67)
        self.assertEqual(report["contract"]["template_image_slots"], 2)

    def test_missing_text_slot_fails_closed(self) -> None:
        theme = copy.deepcopy(self.complete)
        theme["pages"][0]["texts"].pop(next(iter(theme["pages"][0]["texts"])))
        proc, report = self._validate(self._write_theme("missing-text.json", theme))
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any("missing" in item for item in report["errors"]))

    def test_source_image_sha_fails_closed(self) -> None:
        theme = copy.deepcopy(self.complete)
        source_asset = self.tmp / "assets" / "source-image3.png"
        with zipfile.ZipFile(SOURCE) as archive:
            source_asset.write_bytes(archive.read("ppt/media/image3.png"))
        first_page = theme["pages"][0]
        first_slot = next(iter(first_page["images"]))
        old_key = first_page["images"][first_slot]
        theme["assets"].pop(old_key)
        theme["assets"]["forbidden-source"] = "assets/source-image3.png"
        first_page["images"][first_slot] = "forbidden-source"
        proc, report = self._validate(self._write_theme("source-image.json", theme))
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any("source/gold image SHA-256" in item for item in report["errors"]))

    def test_same_topic_new_copy_is_allowed(self) -> None:
        theme = copy.deepcopy(self.complete)
        theme["theme_id"] = "test.lycopene-new-copy-v1"
        theme["theme_name"] = "番茄红素"
        for page in theme["pages"]:
            for text_id in page["texts"]:
                page["texts"][text_id] = "全新稿件"
        first_text = next(iter(theme["pages"][0]["texts"]))
        theme["pages"][0]["texts"][first_text] = "番茄红素"
        proc, report = self._validate(self._write_theme("same-topic-new.json", theme))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(report["ok"])

    def test_same_topic_source_long_fragment_is_blocked(self) -> None:
        theme = copy.deepcopy(self.complete)
        theme["theme_id"] = "test.lycopene-source-copy-v1"
        theme["theme_name"] = "番茄红素"
        for page in theme["pages"]:
            for text_id in page["texts"]:
                page["texts"][text_id] = "全新稿件"
        theme["pages"][0]["texts"]["6"] = "一种类胡萝卜素的全面解析"
        first_other = next(
            key for key in theme["pages"][0]["texts"] if key != "6"
        )
        theme["pages"][0]["texts"][first_other] = "番茄红素"
        proc, report = self._validate(self._write_theme("same-topic-source.json", theme))
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(any("source" in item for item in report["errors"]))

    def test_formal_non_lycopene_export_has_complete_qa_and_no_gold_media(self) -> None:
        theme_path = self._write_theme("formal.json", self.complete)
        proc, report = self._validate(theme_path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        approval = self.tmp / "approval.json"
        approval.write_text(
            json.dumps(
                {
                    "content": {
                        "approved": True,
                        "approved_by": "自动化业务验收",
                        "content_sha256": report["content_sha256"],
                    },
                    "visual": {
                        "approved": True,
                        "approved_by": "自动化业务验收",
                        "content_sha256": report["content_sha256"],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        out = self.tmp / "膳食纤维_健康科普课件.pptx"
        qa = self.tmp / "qa"
        generate_report = self.tmp / "generate-report.json"
        export = subprocess.run(
            [
                "node",
                str(ENGINE),
                "--theme",
                str(theme_path),
                "--approval",
                str(approval),
                "--out",
                str(out),
                "--qa",
                str(qa),
                "--report",
                str(generate_report),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(export.returncode, 0, export.stderr)
        result = json.loads(generate_report.read_text(encoding="utf-8"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["page_count"], 20)
        self.assertEqual(len(list(qa.glob("slide-*.png"))), 20)
        self.assertEqual(len(list(qa.glob("slide-*.layout.json"))), 20)
        self.assertTrue((qa / "deck-montage.webp").is_file())
        self.assertEqual(result["pptx_validation"]["source_media_leaks"], [])
        self.assertEqual(result["pptx_validation"]["approved_assets_missing"], [])
        self.assertEqual(result["pptx_validation"]["approved_asset_count"], 69)

    def test_active_business_route_non_lycopene_e2e(self) -> None:
        jobs = self.tmp / "business-route-jobs"
        delivery = self.tmp / "business-route-delivery"
        jobs.mkdir(exist_ok=True)
        delivery.mkdir(exist_ok=True)
        old_jobs_root = bj.jobs_root
        old_delivery_root = bj.delivery_root
        bj.jobs_root = lambda: jobs  # type: ignore[assignment]
        bj.delivery_root = lambda: delivery  # type: ignore[assignment]
        bj.set_active_scope("uat")
        job_id = "ingredient-health-non-gold-e2e"
        theme_path = self._write_theme("business-route-theme.json", self.complete)
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    bj.main(
                        [
                            "new",
                            "--scope",
                            "uat",
                            "--route",
                            "ingredient-health-edu-pptx-v1",
                            "--theme",
                            "膳食纤维",
                            "--script-json",
                            str(theme_path),
                            "--job-id",
                            job_id,
                            "--auto-draft",
                            "--json",
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    bj.main(
                        [
                            "approve",
                            "--scope",
                            "uat",
                            "--job",
                            job_id,
                            "--gate",
                            "content",
                            "--by",
                            "自动化业务验收",
                            "--json",
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    bj.main(
                        [
                            "approve",
                            "--scope",
                            "uat",
                            "--job",
                            job_id,
                            "--gate",
                            "visual",
                            "--by",
                            "自动化业务验收",
                            "--note",
                            "测试生成的原创占位图片，仅用于验证换槽与门闸",
                            "--json",
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    bj.main(
                        [
                            "render",
                            "--scope",
                            "uat",
                            "--job",
                            job_id,
                            "--ignore-env",
                            "--json",
                        ]
                    ),
                    0,
                )
            job = bj.load_job(job_id)
            self.assertEqual(job["state"], "delivered")
            delivered = Path(job["delivery"]["path"])
            self.assertTrue((delivered / "终稿.pptx").is_file())
            qa = json.loads((delivered / "qa-summary.json").read_text(encoding="utf-8"))
            self.assertTrue(qa["ok"])
            self.assertEqual(qa["page_count"], 20)
            self.assertEqual(qa["text_slots"], 107)
            self.assertEqual(qa["explicit_image_bindings"], 69)
            self.assertIn("source-medical-copy-zero", qa["checks"])
            self.assertIn("source-media-sha-zero", qa["checks"])
        finally:
            bj.jobs_root = old_jobs_root  # type: ignore[assignment]
            bj.delivery_root = old_delivery_root  # type: ignore[assignment]
            bj.set_active_scope("production")


if __name__ == "__main__":
    unittest.main()
