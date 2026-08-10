#!/usr/bin/env python3
"""Gold media fail-closed guard — unit + business-job integration."""

from __future__ import annotations

import json
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import business_job as bj  # noqa: E402
import gold_asset_guard as guard  # noqa: E402


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_test_png(path: Path, rgb: tuple[int, int, int] = (12, 34, 56)) -> None:
    width = height = 16
    raw = (b"\x00" + bytes(rgb) * width) * height
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )


def extract_one_gold_media(pptx: Path, dest: Path) -> Path:
    with zipfile.ZipFile(pptx) as archive:
        for name in archive.namelist():
            if name.startswith("ppt/media/") and not name.endswith("/"):
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(name))
                return dest
    raise AssertionError(f"no media in {pptx}")


class GoldAssetGuardUnit(unittest.TestCase):
    def test_guard_summary_has_hashes(self) -> None:
        summary = guard.guard_summary()
        self.assertGreater(summary["global_hash_count"], 10)
        self.assertIn("disease-product-scenario-v1", summary["hashes_per_slug"])
        self.assertGreater(
            summary["hashes_per_slug"]["disease-product-scenario-v1"], 0
        )

    def test_blocks_disease_gold_pixels(self) -> None:
        pptx = (
            ROOT
            / "production-library"
            / "templates"
            / "settled"
            / "disease-product-scenario-v1"
            / "穿心莲内酯滴丸_商品培训课件2_可编辑重建版.pptx"
        )
        self.assertTrue(pptx.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            stolen = Path(tmp) / "stolen-from-gold.png"
            extract_one_gold_media(pptx, stolen)
            hits = guard.check_image_file(
                stolen,
                binding="disease.symptoms[0].image",
                template_slug="disease-product-scenario-v1",
                allow_gold=False,
            )
            self.assertTrue(hits, msg="must block gold media bytes")
            self.assertTrue(any("SHA" in item or "源图" in item for item in hits))

            allowed = guard.check_image_file(
                stolen,
                binding="disease.symptoms[0].image",
                template_slug="disease-product-scenario-v1",
                allow_gold=True,
            )
            self.assertEqual(allowed, [])

    def test_fresh_png_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "fresh.png"
            write_test_png(fresh, (200, 10, 10))
            hits = guard.check_image_file(
                fresh,
                binding="product.image",
                template_slug="disease-product-scenario-v1",
                allow_gold=False,
            )
            self.assertEqual(hits, [])

    def test_path_marker_block(self) -> None:
        settled = (
            ROOT
            / "production-library"
            / "templates"
            / "settled"
            / "disease-product-scenario-v1"
            / "preview"
            / "cover.png"
        )
        if not settled.is_file():
            self.skipTest("settled preview missing")
        hits = guard.check_image_file(
            settled,
            binding="cover",
            template_slug="disease-product-scenario-v1",
            allow_gold=False,
        )
        self.assertTrue(hits)


class DiseaseGoldImageBusinessJob(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="gold-guard-job-"))
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.jobs = self.temp / "jobs"
        self.delivery = self.temp / "delivery"
        self.jobs.mkdir()
        self.delivery.mkdir()
        self._jobs_root = bj.jobs_root
        self._delivery_root = bj.delivery_root
        bj.jobs_root = lambda: self.jobs  # type: ignore[assignment]
        bj.delivery_root = lambda: self.delivery  # type: ignore[assignment]
        bj.set_active_scope("uat")
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        bj.jobs_root = self._jobs_root  # type: ignore[assignment]
        bj.delivery_root = self._delivery_root  # type: ignore[assignment]
        bj.set_active_scope("production")

    def test_disease_content_approve_blocks_gold_media(self) -> None:
        source = bj._DISEASE_SAMPLE
        model = json.loads(source.read_text(encoding="utf-8"))
        # Replace every image with a unique fresh PNG first so structure is complete,
        # then overwrite one slot with real gold media bytes.
        assets_dir = self.temp / "assets"
        assets_dir.mkdir()
        for index, (_binding, container, key) in enumerate(
            bj._disease_image_bindings(model)
        ):
            fresh = assets_dir / f"fresh-{index}.png"
            write_test_png(fresh, (index + 1, 40, 80))
            container[key] = str(fresh)

        pptx = (
            ROOT
            / "production-library"
            / "templates"
            / "settled"
            / "disease-product-scenario-v1"
            / "穿心莲内酯滴丸_商品培训课件2_可编辑重建版.pptx"
        )
        gold_copy = assets_dir / "gold-leaked.png"
        extract_one_gold_media(pptx, gold_copy)
        # Put gold bytes on disease definition slot (common leak)
        page = (model.get("pages") or {}).get("disease_definition") or {}
        if "image" in page:
            page["image"] = str(gold_copy)
        else:
            # fallback first symptom
            model["disease"]["symptoms"][0]["image"] = str(gold_copy)

        # Complete formal text markers from sample (neutral sample uses 核验-friendly tokens)
        model = json.loads(
            json.dumps(model)
            .replace("示例", "核验")
            .replace("演示", "审核")
            .replace("虚构", "测试")
            .replace("非业务发布", "内部验收")
        )
        theme = "核验商品防金样泄漏"
        model.setdefault("product", {})["name"] = theme
        model.setdefault("meta", {})["gold_sample"] = False
        model.setdefault("meta", {})["theme_id"] = "business-job.leak-test"

        script = self.temp / "disease-leak.json"
        script.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
        product = self.temp / "pack.png"
        write_test_png(product, (9, 9, 9))

        job_id = "uat-disease-gold-leak"
        self.assertEqual(
            bj.main(
                [
                    "new",
                    "--scope",
                    "uat",
                    "--route",
                    "product-pptx-disease-scenario-v1",
                    "--theme",
                    theme,
                    "--script-json",
                    str(script),
                    "--product-image",
                    str(product),
                    "--job-id",
                    job_id,
                    "--auto-draft",
                    "--json",
                ]
            ),
            0,
        )
        with self.assertRaises(SystemExit) as raised:
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
                    "UAT",
                    "--json",
                ]
            )
        message = str(raised.exception)
        self.assertTrue(
            "金样" in message or "源图" in message or "SHA" in message,
            msg=message,
        )


if __name__ == "__main__":
    unittest.main()
