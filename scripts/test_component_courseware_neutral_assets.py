#!/usr/bin/env python3
"""Regression tests for the neutral component-courseware asset boundary."""

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


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAQAAAB2iJ3eAAAADElEQVR42mNk+M8AAAICAQB7CYQ0AAAAAElFTkSuQmCC"
)
CW4_SETTLED = (
    ROOT
    / "production-library/templates/settled/fuler-fanqiehongsu-product-courseware-4-v1"
)


def complete_script(product: Path, visual: Path) -> dict:
    return {
        "meta": {
            "display_name": "中性测试商品",
            "product_packshot": str(product),
        },
        "benefits": {
            "title": "核心知识",
            "items": [
                {
                    "title": "卖点一",
                    "body": "经审核的卖点说明",
                    "chain": [
                        {
                            "role": "benefit_visual_1",
                            "file": str(visual),
                            "source_kind": "system_generated",
                        }
                    ],
                }
            ]
        },
        "features": {
            "title": "产品特点",
            "items": [
                {
                    "title": "原料信息",
                    "body": "经审核的原料说明",
                    "visual": {
                        "src": str(visual),
                        "source_kind": "business_evidence",
                    },
                }
            ]
        },
        "audience": {
            "title": "适宜人群",
            "items": ["经审核的人群"],
            "visual": {
                "src": str(visual),
                "source_kind": "system_generated",
            },
        },
        "combination": {
            "title": "咨询场景",
            "rows": [
                {
                    "problem": "经审核的场景",
                    "partner": "经审核的搭档",
                    "icon": {
                        "src": str(visual),
                        "source_kind": "system_generated",
                    },
                }
            ]
        },
        "precautions": {
            "title": "注意事项",
            "items": ["经审核的注意事项"],
            "illustrations": [
                {
                    "src": str(visual),
                    "wide": True,
                    "source_kind": "system_generated",
                }
            ],
        },
    }


class ComponentCoursewareNeutralAssetTests(unittest.TestCase):
    def test_asset_plan_requires_a_real_file(self) -> None:
        script = complete_script(Path("/not/real/product.png"), Path("/not/real/visual.png"))
        plan = asset_plan.build_product_pptx_asset_plan(
            script, template_slug="product-courseware-component-v1"
        )
        self.assertNotEqual(plan["business_provides"][0]["status"], "ready")
        self.assertTrue(asset_plan.formal_render_blockers(plan))

    def test_formal_validation_accepts_task_bound_non_gold_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            draft = job / "draft"
            generated = job / "intake/generated-assets"
            draft.mkdir(parents=True)
            generated.mkdir(parents=True)
            product = job / "intake/product-packshot.png"
            visual = generated / "new-theme.png"
            product.write_bytes(PNG + b"product")
            visual.write_bytes(PNG + b"visual")
            report = gc.validate_formal_assets(
                complete_script(product, visual), script_path=draft / "script.structured.json"
            )
        self.assertTrue(report["ok"])
        self.assertEqual(report["validated_files"], 6)

    def test_complete_non_gold_theme_exports_editable_pptx(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            draft = job / "draft"
            generated = job / "intake/generated-assets"
            draft.mkdir(parents=True)
            generated.mkdir(parents=True)
            product = job / "intake/product-packshot.png"
            visual = generated / "new-theme.png"
            product.write_bytes(PNG + b"product")
            visual.write_bytes(PNG + b"visual")
            script_path = draft / "script.structured.json"
            script_path.write_text(
                json.dumps(complete_script(product, visual), ensure_ascii=False),
                encoding="utf-8",
            )
            out = job / "render"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/generate_courseware.py"),
                    "--script",
                    str(script_path),
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
            report = json.loads((out / "generate-report.json").read_text(encoding="utf-8"))
            pptx = Path(report["pptx"])
            if not pptx.is_absolute():
                pptx = ROOT / pptx
            self.assertTrue(pptx.is_file())
            self.assertGreater(pptx.stat().st_size, 10_000)
            self.assertTrue(report["formal_asset_validation"]["ok"])
            with zipfile.ZipFile(pptx) as archive:
                slide_xml = archive.read("ppt/slides/slide1.xml")
                all_slide_xml = b"\n".join(
                    archive.read(name)
                    for name in archive.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
            self.assertIn(b"<p:sp", slide_xml)
            self.assertIn(b"<p:pic", slide_xml)
            self.assertIn("经审核的人群".encode("utf-8"), all_slide_xml)

    def test_formal_validation_blocks_placeholder_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            draft = job / "draft"
            draft.mkdir(parents=True)
            script = complete_script(
                job / "intake/product-packshot.png",
                Path("__missing__/visual.png"),
            )
            with self.assertRaises(gc.GeneratorError):
                gc.validate_formal_assets(
                    script, script_path=draft / "script.structured.json"
                )

    def test_formal_validation_blocks_cw4_media_even_when_renamed(self) -> None:
        pptx = next(CW4_SETTLED.glob("*.pptx"))
        with zipfile.ZipFile(pptx) as zf:
            member = next(name for name in zf.namelist() if name.startswith("ppt/media/"))
            gold_bytes = zf.read(member)
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            draft = job / "draft"
            generated = job / "intake/generated-assets"
            draft.mkdir(parents=True)
            generated.mkdir(parents=True)
            product = job / "intake/product-packshot.png"
            visual = generated / "innocent-new-name.png"
            product.write_bytes(PNG + b"product")
            visual.write_bytes(gold_bytes)
            with self.assertRaises(gc.GeneratorError):
                gc.validate_formal_assets(
                    complete_script(product, visual),
                    script_path=draft / "script.structured.json",
                )

    def test_formal_validation_blocks_cw4_source_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            draft = job / "draft"
            generated = job / "intake/generated-assets"
            draft.mkdir(parents=True)
            generated.mkdir(parents=True)
            product = job / "intake/product-packshot.png"
            visual = generated / "tomato.png"
            product.write_bytes(PNG + b"product")
            visual.write_bytes(PNG + b"not-gold-bytes")
            with self.assertRaises(gc.GeneratorError):
                gc.validate_formal_assets(
                    complete_script(product, visual),
                    script_path=draft / "script.structured.json",
                )

    def test_formal_validation_blocks_pending_copy_even_with_real_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            draft = job / "draft"
            generated = job / "intake/generated-assets"
            draft.mkdir(parents=True)
            generated.mkdir(parents=True)
            product = job / "intake/product-packshot.png"
            visual = generated / "new-theme.png"
            product.write_bytes(PNG + b"product")
            visual.write_bytes(PNG + b"visual")
            script = complete_script(product, visual)
            script["benefits"]["items"][0]["body"] = "内容待确认"
            with self.assertRaises(gc.GeneratorError):
                gc.validate_formal_assets(
                    script,
                    script_path=draft / "script.structured.json",
                )

    def test_prepare_assets_does_not_import_cw4_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "cw4/assets/generated"
            source.mkdir(parents=True)
            (source / "tomato.png").write_bytes(PNG)
            out = root / "out/assets"
            gc.prepare_assets(root / "cw4", out)
            self.assertFalse((out / "generated/tomato.png").exists())

    def test_layout_never_infers_source_gold_chain_files(self) -> None:
        layout = ROOT / "production-library/engines/courseware-pptx-v1/layout-rules.mjs"
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp) / "check.mjs"
            runner.write_text(
                "\n".join(
                    [
                        f"import {{resolveChainItems}} from {json.dumps(layout.as_uri())};",
                        "const implicit = resolveChainItems({id:'S04_benefit_1', chain:['source','arrow','result']});",
                        "const empty = resolveChainItems({id:'anything'});",
                        "console.log(JSON.stringify({implicit, empty}));",
                    ]
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["node", str(runner)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        payload = json.loads(proc.stdout)
        blob = json.dumps(payload, ensure_ascii=False).lower()
        for token in ("tomato", "lycopene", "prostate", "softgel", "xinjiang"):
            self.assertNotIn(token, blob)
        self.assertEqual(payload["empty"], [])

    def test_default_engine_sources_have_no_cw4_product_fallbacks(self) -> None:
        files = [
            ROOT / "scripts/generate_courseware.py",
            ROOT / "production-library/engines/courseware-pptx-v1/scenes/builders.mjs",
            ROOT / "production-library/engines/courseware-pptx-v1/layout-rules.mjs",
            ROOT / "production-library/engines/courseware-pptx-v1/components/audience_card.mjs",
            ROOT / "production-library/engines/courseware-pptx-v1/components/icon_bullet.mjs",
            ROOT / "production-library/engines/courseware-pptx-v1/components/section_label.mjs",
            ROOT / "production-library/engines/courseware-pptx-v1/components/row_card.mjs",
        ]
        blob = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()
        forbidden = (
            "slot-photo-tomato",
            "slot-photo-vine",
            "slot-pack-lycopene",
            "five-tomatoes",
            "softgel.png",
            "prostate-diagram",
            "map-xinjiang",
            "badge-hot-recommend",
            "icon-check-red",
            "icon-chevron-lime",
            "福尔番茄红素",
        )
        for token in forbidden:
            self.assertNotIn(token, blob)


if __name__ == "__main__":
    unittest.main()
