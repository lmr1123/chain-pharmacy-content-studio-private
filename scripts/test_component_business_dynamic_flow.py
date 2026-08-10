#!/usr/bin/env python3
"""Focused contracts for WorkBuddy's dynamic component-courseware intake."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "production-library/schemas/product-training-script.schema.json"


class ComponentBusinessDynamicFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_schema_declares_explicit_dynamic_page_sequence(self) -> None:
        meta = self.schema["properties"]["meta"]["properties"]
        sequence = meta["page_sequence"]
        self.assertEqual(sequence["type"], "array")
        self.assertEqual(sequence["minItems"], 1)
        self.assertEqual(sequence["items"]["type"], "string")

    def test_schema_declares_all_cross_source_and_new_sections(self) -> None:
        properties = self.schema["properties"]
        expected = {
            "product_overview": ("facts",),
            "consultation": ("steps",),
            "evidence": ("items",),
            "objection_handling": ("rows",),
        }
        for section, fields in expected.items():
            with self.subTest(section=section):
                self.assertIn(section, properties)
                self.assertEqual(properties[section]["type"], "object")
                for field in fields:
                    self.assertIn(field, properties[section]["properties"])


if __name__ == "__main__":
    unittest.main()
