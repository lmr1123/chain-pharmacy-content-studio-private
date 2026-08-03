from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from build_universal_video_business_words import (
    build_blank,
    build_health_sample,
    build_product_sample,
)
from import_universal_video_content import parse_video_docx


class UniversalVideoInputTest(unittest.TestCase):
    def parse(self, document, video_type: str):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        path = root / "input.docx"
        document.save(path)
        return parse_video_docx(path, root / "assets", video_type)

    def test_blank_template_has_no_fake_sections(self):
        manifest = self.parse(build_blank(), "health")
        self.assertEqual(manifest["video"]["theme"], "")
        self.assertEqual(manifest["sections"], [])
        self.assertEqual(manifest["content_metrics"]["image_count"], 0)
        self.assertFalse(manifest["planning_policy"]["fixed_section_count"])

    def test_health_sample_routes_without_fixed_chapter_contract(self):
        manifest = self.parse(build_health_sample(), "health")
        self.assertEqual(
            manifest["routing"]["template_id"],
            "template.health-reference-tech-v1",
        )
        self.assertEqual(
            manifest["routing"]["style_pack_id"],
            "style-pack.reference-medical-tech-v1",
        )
        self.assertEqual(manifest["content_metrics"]["section_count"], 5)
        self.assertEqual(manifest["content_metrics"]["image_count"], 2)
        self.assertEqual(manifest["unattached_images"], [])

    def test_product_sample_uses_same_word_structure_but_product_route(self):
        manifest = self.parse(build_product_sample(), "product")
        self.assertEqual(
            manifest["routing"]["template_id"],
            "template.product-training-faithful-v1",
        )
        self.assertEqual(
            manifest["routing"]["style_pack_id"],
            "style-pack.reference-product-blue-v1",
        )
        self.assertEqual(manifest["content_metrics"]["section_count"], 5)
        self.assertEqual(manifest["content_metrics"]["image_count"], 1)
        self.assertFalse(manifest["planning_policy"]["fixed_scene_count"])


if __name__ == "__main__":
    unittest.main()
