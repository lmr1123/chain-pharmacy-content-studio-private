#!/usr/bin/env python3
"""Real non-gold E2E for the three signed fixed PPTX business routes."""

from __future__ import annotations

import json
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from copy import deepcopy
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import business_job as bj  # noqa: E402
import replicate_courseware_theme as courseware3  # noqa: E402
from test_courseware3_theme_replicate import build_complete_theme  # noqa: E402


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_test_png(path: Path, rgb: tuple[int, int, int] = (38, 145, 91)) -> None:
    width = height = 24
    raw = (b"\x00" + bytes(rgb) * width) * height
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )


def pptx_slide_count(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        return len(
            [
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ]
        )


def replace_strings(value: object, replacements: dict[str, str]) -> object:
    if isinstance(value, str):
        for source, target in replacements.items():
            value = value.replace(source, target)
        return value
    if isinstance(value, list):
        return [replace_strings(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item, replacements) for key, item in value.items()}
    return value


class FixedCoursewareBusinessRouteE2E(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="fixed-routes-e2e-"))
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.jobs = self.temp / "jobs"
        self.delivery = self.temp / "delivery"
        self.jobs.mkdir()
        self.delivery.mkdir()
        self.jobs_root = bj.jobs_root
        self.delivery_root = bj.delivery_root
        bj.jobs_root = lambda: self.jobs  # type: ignore[assignment]
        bj.delivery_root = lambda: self.delivery  # type: ignore[assignment]
        bj.set_active_scope("uat")
        self.addCleanup(self._restore)
        self.image = self.temp / "uat-authorized-input.png"
        write_test_png(self.image)

    def _restore(self) -> None:
        bj.jobs_root = self.jobs_root  # type: ignore[assignment]
        bj.delivery_root = self.delivery_root  # type: ignore[assignment]
        bj.set_active_scope("production")

    def run_route(
        self,
        *,
        route: str,
        theme: str,
        script: Path,
        job_id: str,
        expected_pages: int,
    ) -> Path:
        self.assertEqual(
            bj.main(
                [
                    "new",
                    "--scope",
                    "uat",
                    "--route",
                    route,
                    "--theme",
                    theme,
                    "--script-json",
                    str(script),
                    "--product-image",
                    str(self.image),
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
                    "UAT测试员",
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
                    "UAT测试员",
                    "--authorization-reference",
                    "UAT-FIXTURE-NOT-FOR-PRODUCTION",
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
                    "UAT测试员",
                    "--note",
                    "自动化 UAT 固定图片，仅验证绑定与版式，不作业务素材",
                    "--json",
                ]
            ),
            0,
        )
        with mock.patch.object(bj, "probe_capabilities", return_value={"pptx_export": True}):
            self.assertEqual(
                bj.main(["render", "--scope", "uat", "--job", job_id, "--json"]),
                0,
            )
        job = bj.load_job(job_id)
        self.assertEqual(job["state"], "delivered")
        delivery = Path(job["delivery"]["path"])
        pptx = delivery / "终稿.pptx"
        self.assertTrue(pptx.is_file())
        self.assertEqual(pptx_slide_count(pptx), expected_pages)
        self.assertTrue((delivery / "qa-summary.json").is_file())
        self.assertTrue((delivery / "run-manifest.json").is_file())
        return pptx

    def test_green_fixed_route_non_gold_e2e(self) -> None:
        theme = "非金样商品甲"
        model = {
            "project_id": "uat.green.a",
            "template_id": "template.product-courseware-dashenlin-green-v1",
            "style_pack_id": "style-pack.dashenlin-courseware-green-v1",
            "style_pack_locked": True,
            "content_lock": "uat-approved-input",
            "brand": {
                "display_name": "示范连锁",
                "primary": "#009900",
                "secondary": "#45A817",
                "internal_notice": "仅供内部学习",
            },
            "pages": [
                {
                    "id": "cover",
                    "scene_type": "courseware_cover",
                    "title": theme,
                    "organization": "示范连锁培训中心",
                    "tagline": "专业培训",
                    "reference": "UAT输入",
                },
                {
                    "id": "product-overview",
                    "scene_type": "product_overview",
                    "page_number": "01",
                    "title": "商品介绍、核心卖点、适宜人群",
                    "product": {
                        "display_name": theme,
                        "image_slot": str(self.image),
                        "code": "UAT-A01",
                        "priority": "A",
                        "specification": "审核规格甲",
                        "retail_price": "审核价格甲",
                        "one_line_selling_point": "业务审核的一句话信息甲",
                    },
                    "sections": [
                        {"title": "一、商品介绍：", "items": ["审核字段甲一", "审核字段甲二"]},
                        {"title": "二、核心卖点：", "items": ["审核卖点甲一", "审核卖点甲二"]},
                        {"title": "三、适宜人群：", "items": ["审核人群甲一", "审核人群甲二"]},
                    ],
                    "reference": "UAT输入",
                },
                {
                    "id": "combination-guidance",
                    "scene_type": "combination_guidance",
                    "page_number": "02",
                    "title": "联合用药话术",
                    "columns": ["应用场景", "联合用药", "联合商品图", "本品图", "销售话术"],
                    "primary_asset": str(self.image),
                    "primary_pack_label": f"{theme}包装图",
                    "rows": [
                        {
                            "scenario": "审核场景甲",
                            "combination": f"{theme} + 审核搭档甲",
                            "partner": "审核搭档甲",
                            "partner_asset": str(self.image),
                            "talk_track": "业务已审核的场景话术甲。",
                        }
                    ],
                    "reference": "UAT输入",
                },
                {
                    "id": "product-benchmark",
                    "scene_type": "product_benchmark",
                    "page_number": "03",
                    "title": "品种对标",
                    "columns": ["对比维度", theme, "审核对标品甲"],
                    "rows": [
                        {"label": "产品展示", "values": [str(self.image), str(self.image)]},
                        {"label": "资料字段", "merge": True, "value": "业务审核共同字段甲"},
                        {"label": "共有优势", "merge": True, "value": "业务审核共有信息甲"},
                        {"label": "零售价", "values": ["审核价格甲", "审核价格乙"]},
                        {"label": "卖点差异", "values": ["审核差异甲", "审核差异乙"]},
                    ],
                    "reference": "UAT输入",
                },
                {
                    "id": "precautions",
                    "scene_type": "precautions",
                    "page_number": "04",
                    "title": "注意事项",
                    "items": ["审核注意甲一", "审核注意甲二", "审核注意甲三", "审核注意甲四"],
                    "illustration_slots": [
                        {"title": f"审核提示甲{index + 1}", "asset": str(self.image), "fit": "cover"}
                        for index in range(4)
                    ],
                    "reference": "UAT输入",
                },
            ],
        }
        script = self.temp / "green-theme.json"
        script.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
        self.run_route(
            route="product-pptx-green-v1",
            theme=theme,
            script=script,
            job_id="uat-green-non-gold",
            expected_pages=5,
        )

    def test_disease_scenario_fixed_route_non_gold_e2e(self) -> None:
        source = bj._DISEASE_SAMPLE
        model = json.loads(source.read_text(encoding="utf-8"))
        model = replace_strings(
            model,
            {"示例": "核验", "演示": "审核", "虚构": "测试", "非业务发布": "内部验收"},
        )
        for _binding, container, key in bj._disease_image_bindings(model):
            raw = Path(container[key])
            container[key] = str((source.parent / raw).resolve())
        script = self.temp / "disease-theme.json"
        script.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
        self.run_route(
            route="product-pptx-disease-scenario-v1",
            theme="核验商品乙",
            script=script,
            job_id="uat-disease-non-gold",
            expected_pages=18,
        )

    def test_courseware3_fixed_route_non_gold_e2e(self) -> None:
        theme_dir = self.temp / "courseware3-source"
        theme_dir.mkdir()
        base = courseware3.load_json(courseware3.DEFAULT_GOLD / "content-model.json")
        theme = deepcopy(build_complete_theme(theme_dir, base))
        theme["product"]["display_name"] = "核验商品丙"
        theme["title"] = "核验商品丙 · 专项培训"
        (theme_dir / "theme.json").write_text(
            json.dumps(theme, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.image = theme_dir / "assets" / "authorized-product.png"
        self.run_route(
            route="courseware3-pptx-v1",
            theme="核验商品丙",
            script=theme_dir / "theme.json",
            job_id="uat-courseware3-non-gold",
            expected_pages=13,
        )


if __name__ == "__main__":
    unittest.main()
