from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ENGINE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ENGINE_DIR.parents[2]
EXPORTER = ENGINE_DIR / "export.mjs"
SAMPLE = ENGINE_DIR / "samples" / "neutral-theme.json"
FORBIDDEN = (
    "穿心莲",
    "内酯滴丸",
    "风热证",
    "复方氨酚烷胺片",
    "安宫牛黄丸",
    "熊胆薄荷含片",
    "97%",
    "95%",
    "5–10分钟",
    "5-10分钟",
    "38℃",
)


class DiseaseProductScenarioEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="disease-pptx-engine-test-"))
        cls.out = cls.temp_dir / "neutral.pptx"
        cls.qa = cls.temp_dir / "qa"
        cls.result = subprocess.run(
            [
                "node",
                str(EXPORTER),
                "--data",
                str(SAMPLE),
                "--out",
                str(cls.out),
                "--qa",
                str(cls.qa),
            ],
            cwd=REPO_DIR,
            text=True,
            capture_output=True,
            timeout=120,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_render_succeeds_with_expected_qa_contract(self) -> None:
        self.assertEqual(self.result.returncode, 0, self.result.stderr + self.result.stdout)
        self.assertTrue(self.out.is_file())
        self.assertTrue(zipfile.is_zipfile(self.out))
        report = json.loads((self.qa / "generate-report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["ok"])
        self.assertEqual(report["page_count"], 18)
        self.assertEqual(report["qa"]["slide_pngs"], 18)
        self.assertEqual(report["qa"]["slide_layouts"], 18)
        self.assertEqual(report["forbidden_input_hits"], [])
        self.assertEqual(report["forbidden_output_hits"], [])
        self.assertEqual(report["cover_source"], "editable-native-layout")
        self.assertGreater(report["editable_textboxes"], 250)
        self.assertEqual(report["input_images"], report["rendered_images"])
        self.assertGreater(report["input_images"], 10)
        self.assertEqual(len(list(self.qa.glob("slide-*.png"))), 18)
        self.assertEqual(len(list(self.qa.glob("slide-*.layout.json"))), 18)
        self.assertTrue((self.qa / "deck-montage.webp").is_file())
        self.assertTrue((self.qa / "inspection.ndjson").is_file())

    def test_theme_copy_is_editable_and_gold_copy_is_absent(self) -> None:
        inspection = (self.qa / "inspection.ndjson").read_text(encoding="utf-8")
        self.assertIn('"kind":"textbox"', inspection)
        self.assertIn("示例证候A", inspection)
        self.assertIn("示例商品A", inspection)
        self.assertIn("场景一：信息不完整时如何推进", inspection)
        self.assertIn("由中性测试输入指定的示例商品A包装图", inspection)
        for token in FORBIDDEN:
            self.assertNotIn(token, inspection)

        with zipfile.ZipFile(self.out) as deck:
            slide_xml = "\n".join(
                deck.read(name).decode("utf-8")
                for name in deck.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
        self.assertIn("示例证候A", slide_xml)
        self.assertIn("示例商品A", slide_xml)
        self.assertIn("场景一：信息不完整时如何推进", slide_xml)
        self.assertGreater(slide_xml.count("<a:t>"), 250)
        for token in FORBIDDEN:
            self.assertNotIn(token, slide_xml)

    def test_cover_is_native_editable_layout_not_full_slide_screenshot(self) -> None:
        layout = json.loads((self.qa / "slide-01.layout.json").read_text(encoding="utf-8"))
        elements = layout["elements"]
        title_elements = [item for item in elements if item.get("name") == "cover-title"]
        self.assertEqual(len(title_elements), 1)
        self.assertEqual(title_elements[0].get("text"), "示例证候A与示例商品A门店培训")
        image_elements = [item for item in elements if item.get("kind") == "image"]
        self.assertEqual(len(image_elements), 1)
        for image in image_elements:
            _, _, width, height = image["bbox"]
            self.assertLess(width * height, 1280 * 720 * 0.5)
        self.assertTrue(any(item.get("name") == "cover-left-field" for item in elements))
        self.assertTrue(any(item.get("name") == "cover-right-field" for item in elements))

    def test_non_gold_input_with_gold_token_is_hard_blocked(self) -> None:
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["product"]["name"] = "穿心莲测试残留"
        blocked_input = self.temp_dir / "blocked.json"
        blocked_input.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        blocked_out = self.temp_dir / "blocked.pptx"
        blocked_qa = self.temp_dir / "blocked-qa"
        result = subprocess.run(
            [
                "node",
                str(EXPORTER),
                "--data",
                str(blocked_input),
                "--out",
                str(blocked_out),
                "--qa",
                str(blocked_qa),
            ],
            cwd=REPO_DIR,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 3, result.stderr + result.stdout)
        self.assertIn("settled gold tokens", result.stderr)
        self.assertFalse(blocked_out.exists())


if __name__ == "__main__":
    unittest.main()
