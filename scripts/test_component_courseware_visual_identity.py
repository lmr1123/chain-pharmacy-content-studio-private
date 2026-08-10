#!/usr/bin/env python3
"""Regression tests for the default component-PPT visual identity."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_courseware as gc  # noqa: E402
import product_pptx_asset_plan as asset_plan  # noqa: E402


STYLE = ROOT / "production-library/styles/reference-product-blue-v1/tokens.json"
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAQAAAB2iJ3eAAAADElEQVR42mNk+M8AAAICAQB7CYQ0AAAAAElFTkSuQmCC"
)
CW4_PALETTE = ("CECBC4", "B8B4AB", "E4E1DA", "C43C2C", "A83224", "BA3034")


def complete_script(product: Path, visual: Path) -> dict:
    return {
        "meta": {
            "display_name": "蓝色构件视觉回归",
            "product_packshot": str(product),
            "cover_points": ["核对商品图", "使用审核稿", "记录培训边界"],
            "cover_stage_tag": "内部培训",
        },
        "hook": {
            "title": "信息识别流程",
            "symptoms": ["核对包装", "确认资料"],
            "stats": [{"number": "3", "unit": "步", "note": "识别、核对、复核"}],
            "source": "内部视觉回归资料",
        },
        "benefits": {
            "title": "核心知识",
            "items": [
                {
                    "title": "资料链清晰",
                    "body": "从商品图进入审核资料，再落到培训清单。",
                    "chain": [
                        {
                            "role": "benefit_visual",
                            "file": str(visual),
                            "source_kind": "system_generated",
                        }
                    ],
                }
            ],
        },
        "features": {
            "title": "商品特点",
            "items": [
                {
                    "title": "资料可追溯",
                    "body": "展示信息均来自本任务资料。",
                    "visual": {"src": str(visual), "source_kind": "business_evidence"},
                }
            ],
        },
        "audience": {
            "title": "培训对象",
            "items": ["门店员工", "内部培训师"],
            "visual": {"src": str(visual), "source_kind": "system_generated"},
        },
        "combination": {
            "title": "资料协同",
            "rows": [
                {
                    "problem": "核对资料",
                    "partner": "已批准资料包",
                    "talk_track": "先核对版本，再复述培训要点。",
                    "icon": {"src": str(visual), "source_kind": "system_generated"},
                }
            ],
        },
        "summary": {
            "title": "培训回顾",
            "rows": [{"label": "结构", "value": "按审核资料组织"}],
        },
        "precautions": {
            "title": "培训边界",
            "items": ["正式业务必须使用审核文案和授权商品图。"],
            "illustrations": [
                {
                    "src": str(visual),
                    "wide": True,
                    "fit": "cover",
                    "source_kind": "system_generated",
                }
            ],
        },
    }


class ComponentCoursewareVisualIdentityTests(unittest.TestCase):
    def test_default_style_is_registered_reference_product_blue(self) -> None:
        self.assertEqual(gc.DEFAULT_STYLE, STYLE)
        style = json.loads(STYLE.read_text(encoding="utf-8"))
        self.assertEqual(style["style_pack_id"], "style-pack.reference-product-blue-v1")
        self.assertEqual(style["visual_grammar"], "product-blue-asymmetric-v1")
        self.assertEqual(style["chrome_bg"]["mode"], "product-blue-grid")
        registry = json.loads(
            (ROOT / "production-library/registries/styles.json").read_text(encoding="utf-8")
        )
        registered = next(
            item for item in registry["items"] if item["id"] == style["style_pack_id"]
        )
        self.assertEqual(registered["tokens_path"], str(STYLE.relative_to(ROOT)))
        self.assertEqual(registered["ppt_adapter"]["engine_id"], "courseware-pptx-v1")
        self.assertEqual(
            asset_plan.build_product_pptx_asset_plan(
                {"meta": {}}, template_slug="product-courseware-component-v1"
            )["style_pack_id"],
            "style-pack.reference-product-blue-v1",
        )

    def test_background_decorations_stay_inside_the_slide_canvas(self) -> None:
        style = json.loads(STYLE.read_text(encoding="utf-8"))
        canvas = style["canvas"]
        half_w = canvas["design_width_px"] / 2
        half_h = canvas["design_height_px"] / 2
        for wave in style["chrome_bg"]["waves"]:
            cx = wave["cx_design"]
            cy = wave["cy_design"]
            half_wave_w = wave["w_design"] / 2
            half_wave_h = wave["h_design"] / 2
            self.assertGreaterEqual(cx - half_wave_w, -half_w)
            self.assertLessEqual(cx + half_wave_w, half_w)
            self.assertGreaterEqual(cy - half_wave_h, -half_h)
            self.assertLessEqual(cy + half_wave_h, half_h)

    def test_default_sources_do_not_point_to_cw4_identity(self) -> None:
        generator = Path(gc.__file__).read_text(encoding="utf-8")
        export = (
            ROOT / "production-library/engines/courseware-pptx-v1/export.mjs"
        ).read_text(encoding="utf-8")
        context = (
            ROOT / "production-library/engines/courseware-pptx-v1/lib/context.mjs"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            'DEFAULT_STYLE = ROOT / "production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json"',
            generator,
        )
        self.assertIn("production-library/styles/reference-product-blue-v1/tokens.json", export)
        self.assertIn("argValue('--prefix', 'editable:component')", export)
        self.assertIn("eidPrefix = 'editable:component'", context)

    def test_default_export_has_blue_grammar_and_no_cw4_palette(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job = root / "job"
            draft = job / "draft"
            generated = job / "intake/generated-assets"
            draft.mkdir(parents=True)
            generated.mkdir(parents=True)
            product = job / "intake/product-packshot.png"
            visual = generated / "training-visual.png"
            product.write_bytes(PNG + b"product")
            visual.write_bytes(PNG + b"visual")
            script = draft / "script.structured.json"
            script.write_text(
                json.dumps(complete_script(product, visual), ensure_ascii=False),
                encoding="utf-8",
            )
            out = job / "render"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/generate_courseware.py"),
                    "--script",
                    str(script),
                    "--out-dir",
                    str(out),
                    "--skip-qa",
                    "--skip-provenance",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            model = json.loads((out / "content-model.json").read_text(encoding="utf-8"))
            self.assertEqual(model["style_pack_id"], "style-pack.reference-product-blue-v1")
            cover = model["scenes"][0]
            self.assertEqual(cover["cover_points"], ["核对商品图", "使用审核稿", "记录培训边界"])
            self.assertEqual(cover["stage_tag"], "内部培训")
            layer_manifest = (out / "layer-manifest.json").read_text(encoding="utf-8").lower()
            for token in (
                "icon-check-red",
                "badge-hot-recommend",
                "slot-pack-box-a",
                "slot-photo-tomato",
                "map-xinjiang",
                "softgel.png",
                "five-tomatoes",
                "prostate-diagram",
            ):
                self.assertNotIn(token, layer_manifest)
            pptx = next(out.glob("*.pptx"))
            with zipfile.ZipFile(pptx) as archive:
                slides = "\n".join(
                    archive.read(name).decode("utf-8", errors="ignore")
                    for name in archive.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )

        self.assertIn("bg-grid-", slides)
        self.assertIn("cover-info-panel", slides)
        self.assertIn("cover-stage-tag", slides)
        self.assertIn("内部培训", slides)
        self.assertIn("记录培训边界", slides)
        self.assertNotIn("__o_", slides)
        upper = slides.upper()
        for color in CW4_PALETTE:
            self.assertNotIn(color, upper)


if __name__ == "__main__":
    unittest.main()
