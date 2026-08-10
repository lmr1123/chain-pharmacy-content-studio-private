#!/usr/bin/env python3
"""Cross-source composition regression for the component PPT route."""

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
REGISTRY = ROOT / "production-library/page-types/product-training/registry.json"
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAQAAAB2iJ3eAAAADElEQVR42mNk+M8AAAICAQB7CYQ0AAAAAElFTkSuQmCC"
)


def base_script(product: Path, sequence: list[str]) -> dict:
    return {
        "meta": {
            "display_name": "跨来源构件验收",
            "product_packshot": str(product),
            "page_sequence": sequence,
        }
    }


def mixed_three_source_script(product: Path) -> dict:
    script = base_script(
        product,
        [
            "courseware_cover",
            "product_overview",
            "evidence_ladder",
            "consultation_framework",
            "evidence_ladder",
            "objection_handling",
            "summary_matrix",
        ],
    )
    script.update(
        {
            "product_overview": {
                "title": "商品信息总览",
                "facts": [
                    {"label": "剂型", "value": "业务审核剂型"},
                    {"label": "规格", "value": "业务审核规格"},
                    {"label": "定位", "value": "门店培训重点商品"},
                ],
                "statement": "先识别商品，再进入培训场景。",
            },
            "consultation": {
                "title": "门店咨询四步法",
                "steps": [
                    {"question": "先问需求", "why": "确认本次咨询目标"},
                    {"question": "再核资料", "why": "回到已批准商品信息"},
                    {"question": "复述要点", "why": "使用统一培训口径"},
                    {"question": "记录疑问", "why": "超出资料时升级确认"},
                ],
            },
            "evidence": {
                "title": "商品证据阶梯",
                "items": [
                    {"metric": "01", "label": "包装信息", "source": "业务授权商品图"},
                    {"metric": "02", "label": "商品资料", "source": "已批准资料包"},
                    {"metric": "03", "label": "培训口径", "source": "内容确认记录"},
                    {"metric": "04", "label": "版本记录", "source": "任务审批记录"},
                    {"metric": "05", "label": "培训反馈", "source": "业务验收记录"},
                    {"metric": "06", "label": "疑问闭环", "source": "升级确认记录"},
                ],
            },
            "objection_handling": {
                "title": "门店异议应答",
                "rows": [
                    {
                        "objection": "资料版本是否一致？",
                        "response": "先核对批准版本，再说明培训要点。",
                        "boundary": "无法核实时暂停回答并升级确认。",
                    }
                ],
            },
            "summary": {
                "title": "培训回顾",
                "rows": [{"label": "闭环", "value": "识别、核对、复述、升级"}],
            },
        }
    )
    return script


def new_tab_script(product: Path) -> dict:
    script = base_script(
        product,
        [
            "courseware_cover",
            "objection_handling",
            "consultation_framework",
            "product_overview",
            "objection_handling",
            "summary_matrix",
        ],
    )
    script.update(
        {
            "objection_handling": {
                "title": "门店异议应答",
                "rows": [
                    {
                        "objection": "资料版本是否一致？",
                        "response": "先核对本任务批准版本，再说明培训要点。",
                        "boundary": "无法核实时暂停回答并升级确认。",
                    },
                    {
                        "objection": "能否补充未提供的结论？",
                        "response": "只使用已审核原文，不自行扩写。",
                        "boundary": "新增结论必须重新走内容确认。",
                    },
                    {
                        "objection": "是否可以跳过版本核对？",
                        "response": "先完成版本核对，再进入培训说明。",
                        "boundary": "未核对前不得按正式口径输出。",
                    },
                    {
                        "objection": "现场疑问能否立即扩展？",
                        "response": "先记录疑问，再回到审核资料。",
                        "boundary": "资料外问题统一升级确认。",
                    },
                ],
            },
            "consultation": {
                "title": "两步咨询检查",
                "steps": [
                    {"question": "核对版本", "why": "确认资料一致"},
                    {"question": "升级疑问", "why": "避免超范围表达"},
                ],
            },
            "product_overview": {
                "title": "商品资料速览",
                "facts": [
                    {"label": "资料", "value": "已批准任务资料"},
                    {"label": "场景", "value": "门店内部培训"},
                ],
                "statement": "先看商品，再处理业务异议。",
            },
            "summary": {
                "title": "应答闭环",
                "rows": [{"label": "动作", "value": "核对、回答、升级"}],
            },
        }
    )
    return script


def alternate_sequence_script(product: Path) -> dict:
    script = base_script(
        product,
        [
            "courseware_cover",
            "evidence_ladder",
            "product_overview",
            "objection_handling",
            "consultation_framework",
        ],
    )
    script.update(
        {
            "evidence": {
                "title": "资料证据清单",
                "items": [
                    {"metric": "A", "label": "商品图", "source": "业务提交"},
                    {"metric": "B", "label": "审核稿", "source": "内容确认"},
                ],
            },
            "product_overview": {
                "title": "商品快速识别",
                "facts": [
                    {"label": "名称", "value": "跨来源构件验收"},
                    {"label": "用途", "value": "内部培训"},
                ],
            },
            "objection_handling": {
                "title": "答疑边界",
                "rows": [
                    {
                        "objection": "资料外问题",
                        "response": "记录问题，不即时扩写。",
                        "boundary": "交由业务或合规确认。",
                    }
                ],
            },
            "consultation": {
                "title": "资料咨询路径",
                "steps": [
                    {"question": "先识别来源", "why": "确认内容可追溯"},
                    {"question": "再确认边界", "why": "避免资料外扩写"},
                ],
            },
        }
    )
    return script


class ComponentCoursewareCrossSourceCompositionTests(unittest.TestCase):
    def test_registry_declares_honest_source_contracts_and_one_new_tab(self) -> None:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        pages = {item["id"]: item for item in data["page_types"]}
        expected = {
            "product_overview": "template.product-courseware-dashenlin-green-v1",
            "consultation_framework": "template.dashenlin-disease-product-scenario-v1",
            "evidence_ladder": "template.sufuda-mabaloshawei-product-courseware-3-v1",
        }
        for page_type, source in expected.items():
            self.assertEqual(pages[page_type]["source_contract"]["template_id"], source)
            self.assertNotEqual(pages[page_type]["status"], "settled")
        self.assertEqual(pages["product_overview"]["max_per_page"], 6)
        overview_recipe = json.loads(
            (
                ROOT
                / "production-library/page-types/product-training/recipes/product_overview.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(overview_recipe["max_per_page"], 6)
        self.assertEqual(
            pages["objection_handling"]["source_contract"]["kind"],
            "new_business_contract",
        )

    def test_three_distinct_sequences_export_in_one_blue_style(self) -> None:
        cases = [
            (
                "mixed-three-source",
                mixed_three_source_script,
                [
                    "courseware_cover",
                    "product_overview",
                    "evidence_ladder",
                    "consultation_framework",
                    "evidence_ladder",
                    "objection_handling",
                    "summary_matrix",
                ],
                [
                    "cover",
                    "product_overview",
                    "evidence_ladder",
                    "consultation_framework",
                    "evidence_ladder",
                    "objection_handling",
                    "efficacy_recap_table",
                ],
            ),
            (
                "new-business-tab",
                new_tab_script,
                [
                    "courseware_cover",
                    "objection_handling",
                    "consultation_framework",
                    "product_overview",
                    "objection_handling",
                    "summary_matrix",
                ],
                [
                    "cover",
                    "objection_handling",
                    "consultation_framework",
                    "product_overview",
                    "objection_handling",
                    "efficacy_recap_table",
                ],
            ),
            (
                "alternate-order",
                alternate_sequence_script,
                [
                    "courseware_cover",
                    "evidence_ladder",
                    "product_overview",
                    "objection_handling",
                    "consultation_framework",
                ],
                [
                    "cover",
                    "evidence_ladder",
                    "product_overview",
                    "objection_handling",
                    "consultation_framework",
                ],
            ),
        ]
        observed: list[tuple[str, ...]] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, builder, page_types, scene_types in cases:
                job = root / name
                draft = job / "draft"
                intake = job / "intake"
                draft.mkdir(parents=True)
                intake.mkdir(parents=True)
                product = intake / "product-packshot.png"
                product.write_bytes(PNG + name.encode("utf-8"))
                script_path = draft / "script.structured.json"
                script_data = builder(product)
                script_path.write_text(
                    json.dumps(script_data, ensure_ascii=False), encoding="utf-8"
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
                model = json.loads((out / "content-model.json").read_text(encoding="utf-8"))
                self.assertEqual(report["page_types"], page_types)
                self.assertEqual(report["scene_types"], scene_types)
                self.assertEqual(model["style_pack_id"], "style-pack.reference-product-blue-v1")
                self.assertEqual(len({scene["id"] for scene in model["scenes"]}), len(page_types))
                expected_facts = (script_data.get("product_overview") or {}).get("facts") or []
                delivered_facts = [
                    fact
                    for scene in model["scenes"]
                    if scene["type"] == "product_overview"
                    for fact in scene["facts"]
                ]
                self.assertEqual(delivered_facts, expected_facts)
                manifest = json.loads((out / "layer-manifest.json").read_text(encoding="utf-8"))
                overview_packshots = [
                    layer
                    for layer in manifest["layers"]
                    if layer["role"] == "product_packshot"
                    and layer["page_id"].endswith("product_overview")
                ]
                if "product_overview" in scene_types:
                    self.assertTrue(overview_packshots)
                    self.assertTrue(
                        all(layer["replace_rule"] == "business_authorized" for layer in overview_packshots)
                    )
                pptx = next(out.glob("*.pptx"))
                with zipfile.ZipFile(pptx) as archive:
                    slide_names = [
                        item
                        for item in archive.namelist()
                        if item.startswith("ppt/slides/slide") and item.endswith(".xml")
                    ]
                    slide_xml = b"\n".join(archive.read(item) for item in slide_names)
                self.assertEqual(len(slide_names), len(page_types))
                self.assertIn(b"bg-grid-", slide_xml)
                self.assertNotIn(b"cover-stage-tag", slide_xml)
                observed.append(tuple(report["page_types"]))

        self.assertEqual({len(sequence) for sequence in observed}, {5, 6, 7})
        self.assertEqual(len(set(observed)), 3)

    def test_hook_intro_preserves_full_approved_paragraphs(self) -> None:
        paragraphs = [
            "多人协作时，文件名相同不代表内容相同，交接必须同时说明版本、状态与确认来源。",
            "本页完整保留业务审核原句，并在信息不一致时记录问题、暂停扩写并升级确认。",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job = root / "hook-copy"
            draft = job / "draft"
            intake = job / "intake"
            draft.mkdir(parents=True)
            intake.mkdir(parents=True)
            product = intake / "product-packshot.png"
            product.write_bytes(PNG + b"hook-copy")
            script_path = draft / "script.structured.json"
            script_path.write_text(
                json.dumps(
                    {
                        "meta": {
                            "display_name": "长句完整性回归",
                            "product_packshot": str(product),
                            "page_sequence": ["courseware_cover", "hook_intro"],
                        },
                        "hook": {"title": "完整信息交接", "paragraphs": paragraphs},
                    },
                    ensure_ascii=False,
                ),
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
            model = json.loads((out / "content-model.json").read_text(encoding="utf-8"))
            hook_scene = next(scene for scene in model["scenes"] if scene["type"] == "time_list")
            self.assertEqual(hook_scene["list"], paragraphs)
            pptx = next(out.glob("*.pptx"))
            with zipfile.ZipFile(pptx) as archive:
                slide_xml = archive.read("ppt/slides/slide2.xml").decode("utf-8")
            for paragraph in paragraphs:
                self.assertIn(paragraph, slide_xml)


if __name__ == "__main__":
    unittest.main()
