#!/usr/bin/env python3
"""Regression: 2 combo rows → 2 rows; never pad to gold 3."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from content_driven_rules import (  # noqa: E402
    ContentDrivenError,
    assert_no_empty_padding,
    build_gap_list,
    plan_combination_guidance,
    plan_list_block,
)


def test_two_combo_rows_no_third_empty() -> None:
    rows = [
        {
            "scenario": "咽喉肿痛",
            "combination": "本品 + 搭档A",
            "talk_track": "审核话术A",
        },
        {
            "scenario": "发热鼻塞",
            "combination": "本品 + 搭档B",
            "talk_track": "审核话术B",
        },
    ]
    plan = plan_combination_guidance(rows, gold_example_count=3)
    assert plan["status"] == "included"
    assert plan["item_count"] == 2
    assert len(plan["items"]) == 2
    assert_no_empty_padding(plan)
    # must not invent a third empty shell
    assert all(
        (it.get("scenario") or it.get("combination") or it.get("talk_track"))
        for it in plan["items"]
    )


def test_zero_combo_omitted() -> None:
    plan = plan_combination_guidance([], gold_example_count=3)
    assert plan["status"] == "omitted"
    assert plan["item_count"] == 0
    assert_no_empty_padding(plan)


def test_reject_empty_shell_if_forced() -> None:
    plan = {
        "module_id": "combination_guidance",
        "status": "included",
        "item_count": 3,
        "items": [
            {"scenario": "a", "combination": "x", "talk_track": "t"},
            {"scenario": "b", "combination": "y", "talk_track": "u"},
            {"scenario": "待补充", "combination": "", "talk_track": ""},
        ],
        "gold_example_count": 3,
    }
    try:
        assert_no_empty_padding(plan)
    except ContentDrivenError:
        return
    raise AssertionError("expected ContentDrivenError for empty shell")


def test_selling_points_five_vs_two() -> None:
    p2 = plan_list_block(
        module_id="selling_points",
        title="核心卖点",
        items=["卖点一", "卖点二"],
        gold_example_count=4,
    )
    p5 = plan_list_block(
        module_id="selling_points",
        title="核心卖点",
        items=[f"卖点{i}" for i in range(1, 6)],
        gold_example_count=4,
    )
    assert p2["item_count"] == 2
    assert p5["item_count"] == 5
    assert_no_empty_padding(p2)
    assert_no_empty_padding(p5)


def test_gap_list_schema() -> None:
    gap = build_gap_list(
        theme="示例商品",
        template_id="template.product-courseware-dashenlin-green-v1",
        missing_fields=["零售价"],
        missing_assets=[{"role": "本品包装", "note": "待授权原图"}],
        pending_confirmations=["联合话术是否用审核稿 v2"],
    )
    assert gap["schema"] == "business-gap-list-v1"
    assert gap["policy"]["no_fake_packaging"] is True


def main() -> None:
    test_two_combo_rows_no_third_empty()
    test_zero_combo_omitted()
    test_reject_empty_shell_if_forced()
    test_selling_points_five_vs_two()
    test_gap_list_schema()
    print("OK content_driven_rules regressions passed")


if __name__ == "__main__":
    main()
