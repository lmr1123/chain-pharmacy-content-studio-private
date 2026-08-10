#!/usr/bin/env python3
"""Truth tests for the business-facing multi-gold component workflow docs."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATHS = {
    "agents": ROOT / "AGENTS.md",
    "business": ROOT / "docs/business-usage-and-test-cases.md",
    "install": ROOT / "docs/workbuddy-install-and-guide.md",
    "prompt": ROOT / "docs/workbuddy-system-prompt.md",
}
EVIDENCE_ROOT = (
    "production-library/validation/courseware/multi-gold-composition-uat-v1/"
)
FIXTURE_README = ROOT / EVIDENCE_ROOT / "README.md"
REUSABLE_CHINESE_TABS = (
    "商品信息总览",
    "门店咨询框架",
    "商品证据阶梯",
)


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class ComponentMultiGoldBusinessDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.docs = {
            name: path.read_text(encoding="utf-8") for name, path in DOC_PATHS.items()
        }
        cls.fixture_readme = FIXTURE_README.read_text(encoding="utf-8")

    def test_all_core_docs_name_reusable_cross_courseware_tabs(self) -> None:
        for name, text in self.docs.items():
            for tab in REUSABLE_CHINESE_TABS:
                self.assertIn(tab, text, f"{name}: missing {tab}")
            self.assertRegex(text, r"registered new page|已经登记|已登记")

    def test_workbuddy_owns_page_sequence_and_business_sees_chinese_outline(self) -> None:
        agents = self.docs["agents"]
        install = self.docs["install"]
        prompt = self.docs["prompt"]
        business = self.docs["business"]

        self.assertIn("internal `page_sequence`", agents)
        self.assertIn("业务确认后内部生成 `page_sequence`", install)
        self.assertIn("内部选择 `page_sequence`", prompt)
        for name, text in (("install", install), ("prompt", prompt), ("business", business)):
            self.assertIn("中文页签大纲", text, name)
            self.assertIn("来源解释", text, name)
            self.assertRegex(text, r"统一视觉|唯一视觉")

    def test_business_is_not_asked_to_edit_json_or_page_type_ids(self) -> None:
        self.assertIn(
            "Business never edits JSON or page-type IDs", normalized(self.docs["agents"])
        )
        self.assertIn("你不需要填写 JSON、页型 ID", self.docs["install"])
        self.assertIn("不得要求业务选择或填写 page type", self.docs["prompt"])
        self.assertIn("不需要准备结构化 JSON、页型 ID", self.docs["business"])
        self.assertNotIn("完整脚本路径：", self.docs["business"])
        self.assertNotIn("本机有一份经药师/合规审核的 `script.structured.json`", self.docs["business"])

    def test_component_formal_path_uses_workbuddy_confirmed_script_json(self) -> None:
        outline_only = (
            "notes-only 入口只生成“待确认中文页签大纲”草稿，绝不能作为正式锁定编排"
        )
        confirmed_path = (
            "业务确认大纲、来源解释和单一视觉后，由 WorkBuddy 内部生成确认版 script-json，再创建统一任务"
        )
        for name, text in self.docs.items():
            self.assertIn(outline_only, text, name)
            self.assertIn(confirmed_path, text, name)

        self.assertNotIn(
            "new --route <confirmed-route> --theme <主题> --notes '...' --auto-draft",
            self.docs["agents"],
        )
        self.assertNotIn(
            "new --route <所选的 active PPT route> --theme <主题> --auto-draft",
            self.docs["install"],
        )
        self.assertIn(
            "new --route <confirmed-fixed-route> --theme <主题> --notes '...' --auto-draft",
            self.docs["agents"],
        )
        self.assertIn(
            "new --route <所选固定 PPT route> --theme <主题> --notes '<业务资料>' --auto-draft",
            self.docs["install"],
        )

        for name, text in self.docs.items():
            for block in re.findall(r"```(?:bash)?\n(.*?)```", text, flags=re.S):
                commands = re.findall(
                    r"python3 scripts/business_job\.py new(?: \\\n[^\n]*)*",
                    block,
                )
                for command in commands:
                    if "product-pptx-component-v1" not in command:
                        continue
                    self.assertIn("--script-json", command, name)
                    self.assertNotIn("--notes", command, name)

    def test_each_workflow_locks_one_style_pack(self) -> None:
        self.assertIn(
            "locks exactly one `style_pack_id`", normalized(self.docs["agents"])
        )
        self.assertIn("一套课件只锁一个 style pack", self.docs["install"])
        self.assertIn("同一课件只能锁定一个 `style_pack_id`", self.docs["prompt"])
        self.assertIn("同一份课件必须锁定一个 style pack", self.docs["business"])

    def test_all_core_docs_report_r4_pass_and_synced_portal_suite_v3(self) -> None:
        stale_status = (
            "r2 逐页视觉复核尚未确认",
            "r2 per-slide visual review is still pending",
            "r1 自动渲染记录",
            "r1 automated evidence only",
        )
        for name, text in self.docs.items():
            flat = normalized(text)
            self.assertIn(EVIDENCE_ROOT, text, name)
            self.assertIn("7 / 6 / 5", flat, name)
            self.assertIn("r4 逐页已通过", flat, name)
            self.assertIn("18 / 18", flat, name)
            self.assertIn("人工逐页复核", flat, name)
            self.assertIn("suite v3", flat, name)
            self.assertIn("hash-bound", flat, name)
            self.assertRegex(flat, r"(is now synced|已通过并完成同步|已同步到门户)", name)
            self.assertRegex(flat, r"(fail-closed|哈希失配.*隐藏)", name)
            for stale in stale_status:
                self.assertNotIn(stale, flat, f"{name}: stale UAT status")

    def test_fixture_readme_reports_r4_and_portal_as_synced(self) -> None:
        flat = normalized(self.fixture_readme)
        self.assertIn("r4 逐页已通过", flat)
        self.assertIn("7 / 6 / 5", flat)
        self.assertIn("18 / 18", flat)
        self.assertIn("suite v3 hash-bound", flat)
        self.assertIn("已经合格并完成同步", flat)
        self.assertIn("fail-closed", flat)

    def test_business_doc_contains_three_explicit_structural_cases_and_manual_uat(self) -> None:
        text = self.docs["business"]
        for row in (
            "| A | 绿色商品总览 + 穿心莲咨询框架 + 速福达证据阶梯 + 新增异议应答",
            "| B | 先证据、后总览，并加入变更应答",
            "| C | 咨询路径、判定表与封存凭证",
        ):
            self.assertIn(row, text)
        self.assertIn("TC-PPT-09 · WorkBuddy 自动组合中文页签", text)
        self.assertIn("TC-PPT-01～05、07～09", text)


if __name__ == "__main__":
    unittest.main()
