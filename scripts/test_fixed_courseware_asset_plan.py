#!/usr/bin/env python3
"""Fixed courseware asset plan + visual binding tests."""

from __future__ import annotations

import json
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import business_job as bj  # noqa: E402
import fixed_courseware_asset_plan as plan  # noqa: E402


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_test_png(path: Path, rgb: tuple[int, int, int] = (11, 22, 33)) -> None:
    width = height = 12
    raw = (b"\x00" + bytes(rgb) * width) * height
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )


class FixedAssetPlanUnit(unittest.TestCase):
    def test_disease_plan_classifies_slots(self) -> None:
        source = bj._DISEASE_SAMPLE
        model = json.loads(source.read_text(encoding="utf-8"))
        for _b, container, key in bj._disease_image_bindings(model):
            container[key] = ""
        built = plan.build_disease_asset_plan(model, theme="核验商品")
        self.assertEqual(built["schema"], "fixed-courseware-asset-plan/v1")
        self.assertGreaterEqual(len(built["system_generates"]), 8)
        self.assertGreaterEqual(len(built["business_provides"]), 2)
        statuses = {item["status"] for item in built["system_generates"]}
        self.assertIn("generate_after_content_approval", statuses)

    def test_courseware3_and_ingredient_plans(self) -> None:
        import replicate_courseware_theme as cw3

        base = cw3.load_json(cw3.DEFAULT_GOLD / "content-model.json")
        theme = {
            "product": {
                "brand_name": "核验",
                "generic_name": "成分",
                "display_name": "核验商品",
            },
            "title": "核验商品 · 培训",
            "assets": {},
            "pages": [{"id": page["id"], "elements": {}} for page in base["pages"]],
            "style_pack_id": base.get("style_pack_id"),
        }
        cw3_plan = plan.build_courseware3_asset_plan(
            theme, theme_name="核验商品", base=base
        )
        self.assertEqual(cw3_plan["schema"], "fixed-courseware-asset-plan/v1")
        self.assertGreaterEqual(len(cw3_plan["system_generates"]), 20)
        self.assertGreaterEqual(len(cw3_plan["business_provides"]), 4)
        self.assertTrue(
            any(
                item["script_path"] == "assets.packGroup"
                for item in cw3_plan["business_provides"]
            )
        )

        ingredient = {
            "theme_name": "膳食纤维",
            "pages": [
                {
                    "slide": 1,
                    "texts": {"2": "膳食纤维定义"},
                    "images": {"shape-fill-12": ""},
                }
            ],
            "template_images": {"master:x": ""},
            "assets": {},
        }
        ing_plan = plan.build_ingredient_asset_plan(
            ingredient, theme_name="膳食纤维"
        )
        self.assertEqual(len(ing_plan["system_generates"]), 2)
        self.assertEqual(ing_plan["business_provides"], [])
        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "i.png"
            write_test_png(img)
            plan.apply_image_bindings(
                ingredient,
                {"pages[0].images.shape-fill-12": str(img)},
                ing_plan,
                mode="ingredient",
            )
            key = ingredient["pages"][0]["images"]["shape-fill-12"]
            self.assertTrue(key)
            self.assertEqual(
                Path(ingredient["assets"][key]).resolve(), img.resolve()
            )

    def test_set_at_and_apply_bindings(self) -> None:
        model: dict = {"disease": {"symptoms": [{"name": "A"}, {"name": "B"}]}}
        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "a.png"
            write_test_png(img)
            plan.set_at(model, "disease.symptoms[0].image", str(img))
            self.assertEqual(model["disease"]["symptoms"][0]["image"], str(img))
            built = {
                "system_generates": [
                    {"script_path": "disease.symptoms[0].image"},
                    {"script_path": "disease.symptoms[1].image"},
                ],
                "business_provides": [],
            }
            img2 = Path(tmp) / "b.png"
            write_test_png(img2, (90, 90, 90))
            plan.apply_image_bindings(
                model,
                {"disease.symptoms[1].image": str(img2)},
                built,
                green=False,
            )
            self.assertEqual(
                Path(model["disease"]["symptoms"][1]["image"]).resolve(),
                img2.resolve(),
            )


class DiseaseAssetPlanJobFlow(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="fixed-plan-"))
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.jobs = self.temp / "jobs"
        self.delivery = self.temp / "delivery"
        self.jobs.mkdir()
        self.delivery.mkdir()
        self._jobs = bj.jobs_root
        self._delivery = bj.delivery_root
        bj.jobs_root = lambda: self.jobs  # type: ignore[assignment]
        bj.delivery_root = lambda: self.delivery  # type: ignore[assignment]
        bj.set_active_scope("uat")
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        bj.jobs_root = self._jobs  # type: ignore[assignment]
        bj.delivery_root = self._delivery  # type: ignore[assignment]
        bj.set_active_scope("production")

    def test_draft_writes_asset_plan_and_visual_accepts_bindings(self) -> None:
        source = bj._DISEASE_SAMPLE
        raw = source.read_text(encoding="utf-8")
        for old, new in (
            ("示例", "核验"),
            ("演示", "审核"),
            ("虚构", "测试"),
            ("非业务发布", "内部验收"),
        ):
            raw = raw.replace(old, new)
        model = json.loads(raw)
        # Strip illustration paths so plan marks generate_after_content_approval
        for binding, container, key in bj._disease_image_bindings(model):
            if binding.endswith("product.image") or "pages.cover" in binding:
                continue
            if "weighted" in binding:
                continue
            container[key] = ""

        assets = self.temp / "assets"
        assets.mkdir()
        pack = assets / "pack.png"
        write_test_png(pack, (1, 2, 3))
        model.setdefault("product", {})["image"] = str(pack)
        model.setdefault("pages", {}).setdefault("cover", {})["image"] = str(pack)
        for index, item in enumerate(model.get("weighted", {}).get("items") or []):
            w = assets / f"w{index}.png"
            write_test_png(w, (4 + index, 5, 6))
            item["image"] = str(w)

        theme = "核验素材计划商品"
        model.setdefault("product", {})["name"] = theme
        model.setdefault("meta", {})["gold_sample"] = False
        # Hard strip residual pending tokens if sample introduces new ones later
        blob = json.dumps(model, ensure_ascii=False)
        for token in ("示例", "虚构", "演示", "非业务发布", "待确认"):
            blob = blob.replace(token, "核验字段")
        model = json.loads(blob)
        model["product"]["name"] = theme
        model["meta"]["gold_sample"] = False
        script = self.temp / "script.json"
        script.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")

        job_id = "uat-disease-asset-plan"
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
                    str(pack),
                    "--job-id",
                    job_id,
                    "--auto-draft",
                    "--json",
                ]
            ),
            0,
        )
        job = bj.load_job(job_id)
        plan_path = Path(job["draft"]["asset_plan_json"])
        self.assertTrue(plan_path.is_file())
        asset_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertTrue(asset_plan["system_generates"])
        pending = [
            item
            for item in asset_plan["system_generates"]
            if item["status"] == "generate_after_content_approval"
        ]
        self.assertTrue(pending)

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
                    "UAT",
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
                    "product_image",
                    "--by",
                    "UAT",
                    "--authorization-reference",
                    "UAT",
                    "--json",
                ]
            ),
            0,
        )

        bindings: dict[str, str] = {}
        for item in pending:
            path = assets / f"{item['script_path'].replace('.', '_').replace('[','').replace(']','')}.png"
            write_test_png(path, (50, 60, 70))
            bindings[item["script_path"]] = str(path)
        bindings_file = self.temp / "bindings.json"
        bindings_file.write_text(
            json.dumps(bindings, ensure_ascii=False), encoding="utf-8"
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
                    "UAT",
                    "--asset-bindings",
                    str(bindings_file),
                    "--note",
                    "UAT generated illustrations",
                    "--json",
                ]
            ),
            0,
        )
        job = bj.load_job(job_id)
        self.assertEqual(job["state"], "visual_approved")
        visual = job["approvals"]["visual"]
        self.assertIn("visual_assets_sha256", visual)
        self.assertTrue(visual.get("asset_bindings"))


if __name__ == "__main__":
    unittest.main()
