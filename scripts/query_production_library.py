#!/usr/bin/env python3
"""Query the project production library without external dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "production-library/catalog.json"
APPROVED_STATUSES = {
    "user-approved",
    "user-approved-gold",
    "production-validated",
    "approved",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_entries() -> list[dict[str, Any]]:
    catalog = load_json(CATALOG_PATH)
    entries: list[dict[str, Any]] = []
    for relative_path in catalog["registries"] + catalog["asset_registries"]:
        registry_path = PROJECT_ROOT / relative_path
        registry = load_json(registry_path)
        registry_type = registry.get("registry_type", registry.get("library", "asset"))
        raw_items = [
            *registry.get("items", []),
            *registry.get("components", []),
            *registry.get("modes", []),
        ]
        for raw_item in raw_items:
            item = dict(raw_item)
            if "id" not in item and item.get("mode_id"):
                item["id"] = item["mode_id"]
            item["_registry_type"] = registry_type
            item["_registry_path"] = relative_path
            item["_search_text"] = json.dumps(
                raw_item, ensure_ascii=False
            ).lower()
            entries.append(item)
    return entries


def contains(value: Any, needle: str) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return any(needle in str(part).lower() for part in value)
    return needle in str(value).lower()


def matches(item: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.type and not contains(item["_registry_type"], args.type.lower()):
        return False
    if args.status and not contains(item.get("status"), args.status.lower()):
        return False
    if args.approved_only and item.get("status") not in APPROVED_STATUSES:
        return False
    if args.tag and not contains(item.get("tags"), args.tag.lower()):
        return False
    if args.style_pack:
        compatible = item.get("compatible_style_packs", [])
        default_style = item.get("default_style_pack_id")
        if (
            item.get("style_pack_id") != args.style_pack
            and item.get("id") != args.style_pack
            and default_style != args.style_pack
            and args.style_pack not in compatible
        ):
            return False
    if args.text and args.text.lower() not in item["_search_text"]:
        return False
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="按类型、标签、风格包、状态或文本查询公共生产库。"
    )
    parser.add_argument(
        "--type",
        help="template/theme/component/effect/style/voice/business-mode/decision/lesson/asset-series/scene-recipe",
    )
    parser.add_argument("--tag", help="标签，例如：数字人、商品培训、扫描线")
    parser.add_argument("--style-pack", help="风格包 ID")
    parser.add_argument("--status", help="状态，例如 production-validated")
    parser.add_argument("--text", help="全文关键词")
    parser.add_argument("--approved-only", action="store_true", help="仅显示已批准条目")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = [item for item in load_entries() if matches(item, args)]
    results.sort(key=lambda item: (item["_registry_type"], item.get("id", "")))
    if args.json:
        clean = [
            {key: value for key, value in item.items() if not key.startswith("_")}
            for item in results
        ]
        print(json.dumps(clean, ensure_ascii=False, indent=2))
        return
    if not results:
        print("未找到匹配条目。")
        return
    for item in results:
        item_id = item.get("id", "(no-id)")
        name = item.get("name_zh", item.get("name", ""))
        status = item.get("status", "")
        source = item.get("source", item.get("_registry_path", ""))
        print(f"{item['_registry_type']}\t{item_id}\t{name}\t{status}\t{source}")


if __name__ == "__main__":
    main()
