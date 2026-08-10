#!/usr/bin/env python3
"""Courseware-3 theme compiler: fail-closed contract and editable PPTX smoke."""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import replicate_courseware_theme as replicate  # noqa: E402


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_test_png(path: Path, *, rgb: tuple[int, int, int] = (37, 140, 92)) -> None:
    """Write a small valid RGB PNG without third-party dependencies."""

    width = height = 16
    row = b"\x00" + bytes(rgb) * width
    raw = row * height
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def build_complete_theme(theme_dir: Path, base: dict) -> dict:
    business_asset = theme_dir / "assets" / "authorized-product.png"
    illustration_asset = theme_dir / "assets" / "theme-illustration.png"
    write_test_png(business_asset)
    write_test_png(illustration_asset, rgb=(217, 118, 28))
    business_assets = sorted(replicate._business_asset_keys(base))
    assets = {key: "assets/authorized-product.png" for key in business_assets}

    pages: list[dict] = []
    illustration_count = 0
    for page in base.get("pages") or []:
        elements: dict[str, object] = {}
        for role, element in (page.get("elements") or {}).items():
            if element.get("kind") == "text" and element.get("replace") == "theme_copy":
                elements[role] = (
                    "示例康® 示例成分"
                    if page["id"] == "cover" and role == "title"
                    else f"{page['id']} · {role} · 已审核内容"
                )
            if element.get("kind") == "image" and element.get("replace") == "theme_illustration":
                asset_key = f"illustration.{page['id']}.{role}"
                elements[role] = {"asset": asset_key}
                assets[asset_key] = "assets/theme-illustration.png"
                illustration_count += 1
        pages.append(
            {
                "id": page["id"],
                "title": f"{page['id']} · 已审核页面",
                "elements": elements,
            }
        )
    if illustration_count != 23:
        raise AssertionError(f"课件3 theme_illustration 槽应为 23，实际 {illustration_count}")

    theme = {
        "theme_id": "theme.example-courseware3-v1",
        "slug": "example-courseware3-v1",
        "project_id": "courseware.example-product-v1",
        "style_pack_id": base["style_pack_id"],
        "voice_pack_id": base["voice_pack_id"],
        "product": {
            "brand_name": "示例康®",
            "generic_name": "示例成分",
            "display_name": "示例康® 示例成分",
        },
        "title": "示例康® 示例成分 · 商品培训课件",
        "assets": assets,
        "pages": pages,
        "captions": ["示例课程开始", "以下内容均来自业务审核稿"],
    }
    (theme_dir / "theme.json").write_text(
        json.dumps(theme, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return theme


def convert_to_explicit_gold_update(theme: dict, base: dict, gold: Path) -> None:
    theme["gold_sample"] = True
    theme["theme_id"] = base["project_id"]
    theme["product"] = {
        field: base["product"][field] for field in replicate.REQUIRED_PRODUCT_FIELDS
    }
    theme["title"] = base["title"]
    theme["assets"] = {}

    overrides = {page["id"]: page for page in theme["pages"]}
    base_assets = base.get("assets") or {}
    for key in replicate._replaceable_asset_keys(base):
        theme["assets"][key] = str(gold / "public" / str(base_assets[key]).removeprefix("/"))
    for page in base.get("pages") or []:
        target = overrides[page["id"]]
        target["title"] = page.get("title") or page["id"]
        for role, element in (page.get("elements") or {}).items():
            if element.get("kind") == "text" and element.get("replace") == "theme_copy":
                target["elements"][role] = element["text"]
            if element.get("kind") == "image" and element.get("replace") == "theme_illustration":
                target["elements"][role] = {"asset": element["asset"]}


class Courseware3ThemeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gold = replicate.DEFAULT_GOLD
        cls.base = replicate.load_json(cls.gold / "content-model.json")

    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="cw3-theme-test-"))
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.theme_dir = self.temp / "theme"
        self.theme_dir.mkdir()
        self.theme = build_complete_theme(self.theme_dir, self.base)

    def validate(self, theme: dict) -> dict[str, Path]:
        return replicate.validate_theme_contract(
            self.base,
            theme,
            theme_dir=self.theme_dir,
            gold=self.gold,
        )

    def run_compiler(self, *, export_pptx: bool) -> tuple[subprocess.CompletedProcess[str], Path]:
        out_parent = self.temp / "out"
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "replicate_courseware_theme.py"),
            "--theme",
            str(self.theme_dir),
            "--out-parent",
            str(out_parent),
            "--out-slug",
            "compiled",
            "--skip-tts",
        ]
        if not export_pptx:
            cmd.append("--skip-pptx")
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        return result, out_parent / "compiled"

    def test_missing_theme_copy_fails_closed(self) -> None:
        page = next(item for item in self.theme["pages"] if item["id"] == "cover")
        del page["elements"]["tagline"]
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("pages.cover.elements.tagline", str(ctx.exception))
        self.assertIn("禁止继承金样", str(ctx.exception))

    def test_explicit_gold_copy_is_rejected_for_new_theme(self) -> None:
        page = next(item for item in self.theme["pages"] if item["id"] == "cover")
        source_page = next(item for item in self.base["pages"] if item["id"] == "cover")
        page["elements"]["tagline"] = source_page["elements"]["tagline"]["text"]
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("新主题显式内容仍含速福达金样文案", str(ctx.exception))

    def test_cli_rejects_partial_theme_before_copying_framework(self) -> None:
        page = next(item for item in self.theme["pages"] if item["id"] == "cover")
        del page["elements"]["tagline"]
        (self.theme_dir / "theme.json").write_text(
            json.dumps(self.theme, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result, dest = self.run_compiler(export_pptx=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pages.cover.elements.tagline", result.stdout + result.stderr)
        self.assertFalse(dest.exists())

    def test_missing_authorized_asset_fails_closed(self) -> None:
        del self.theme["assets"]["packGroup"]
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("assets.packGroup", str(ctx.exception))
        self.assertIn("禁止生成", str(ctx.exception))

    def test_business_asset_cannot_bypass_authorized_map(self) -> None:
        cover = next(item for item in self.theme["pages"] if item["id"] == "cover")
        cover["elements"]["pack"] = "/assets/pack-group-slot-v1.png"
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("不接受直接图片路径", str(ctx.exception))
        self.assertIn("assets.packGroup", str(ctx.exception))

    def test_gold_packaging_hash_is_rejected_for_new_theme(self) -> None:
        self.theme["assets"]["packGroup"] = str(
            self.gold / "public/assets/pack-group-slot-v1.png"
        )
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("仍是速福达金样可替换图片", str(ctx.exception))

    def test_missing_theme_illustration_binding_fails_closed(self) -> None:
        page = next(item for item in self.theme["pages"] if item["id"] == "flu")
        del page["elements"]["card1_icon_a"]
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("pages.flu.elements.card1_icon_a", str(ctx.exception))
        self.assertIn("禁止继承金样插图", str(ctx.exception))

    def test_gold_illustration_hash_is_rejected_for_new_theme(self) -> None:
        page = next(item for item in self.theme["pages"] if item["id"] == "flu")
        asset_key = page["elements"]["card1_icon_a"]["asset"]
        self.theme["assets"][asset_key] = str(
            self.gold / "public/assets/icon-365-v1.png"
        )
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn(f"assets.{asset_key}", str(ctx.exception))
        self.assertIn("金样可替换图片", str(ctx.exception))

    def test_exact_gold_identity_and_flag_allow_explicit_gold_update(self) -> None:
        convert_to_explicit_gold_update(self.theme, self.base, self.gold)
        resolved = self.validate(self.theme)
        self.assertEqual(
            replicate._gold_sample_theme_id(self.base, self.gold),
            "courseware.sufuda-product-training-3.gold-v1",
        )
        self.assertEqual(set(resolved), replicate._replaceable_asset_keys(self.base))
        (self.theme_dir / "theme.json").write_text(
            json.dumps(self.theme, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result, dest = self.run_compiler(export_pptx=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        model = replicate.load_json(dest / "content-model.json")
        self.assertEqual(model["product"]["display_name"], "速福达® 玛巴洛沙韦")
        self.assertNotIn("/assets/icon-365-v1.png", json.dumps(model, ensure_ascii=False))

    def test_similar_product_name_does_not_allow_gold_illustration(self) -> None:
        self.theme["product"]["brand_name"] = "速福达新品®"
        self.theme["product"]["display_name"] = "速福达新品® 示例成分"
        page = next(item for item in self.theme["pages"] if item["id"] == "flu")
        asset_key = page["elements"]["card1_icon_a"]["asset"]
        self.theme["assets"][asset_key] = str(
            self.gold / "public/assets/icon-365-v1.png"
        )
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("金样可替换图片", str(ctx.exception))

    def test_gold_sample_flag_without_canonical_id_cannot_bypass(self) -> None:
        self.theme["gold_sample"] = True
        page = next(item for item in self.theme["pages"] if item["id"] == "flu")
        asset_key = page["elements"]["card1_icon_a"]["asset"]
        self.theme["assets"][asset_key] = str(
            self.gold / "public/assets/icon-365-v1.png"
        )
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("gold_sample:true 仅允许登记金样 theme_id", str(ctx.exception))
        self.assertIn("金样可替换图片", str(ctx.exception))

    def test_canonical_id_without_gold_sample_flag_cannot_bypass(self) -> None:
        self.theme["theme_id"] = self.base["project_id"]
        page = next(item for item in self.theme["pages"] if item["id"] == "flu")
        asset_key = page["elements"]["card1_icon_a"]["asset"]
        self.theme["assets"][asset_key] = str(
            self.gold / "public/assets/icon-365-v1.png"
        )
        with self.assertRaises(replicate.ThemeContractError) as ctx:
            self.validate(self.theme)
        self.assertIn("金样可替换图片", str(ctx.exception))

    def test_compile_removes_gold_copy_and_packaging(self) -> None:
        result, dest = self.run_compiler(export_pptx=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        model = replicate.load_json(dest / "content-model.json")
        storyboard = replicate.load_json(dest / "storyboard.json")
        blob = json.dumps({"model": model, "storyboard": storyboard}, ensure_ascii=False)
        for forbidden in (
            "速福达® 玛巴洛沙韦",
            "全球首个单次口服的流感药",
            "玛巴洛沙韦+退烧药",
            "logo-sufuda-text-v1.png",
            "pack-group-slot-v1.png",
            "pack-tablet-40-slot-v1.png",
            "pack-suspension-slot-v1.png",
        ):
            self.assertNotIn(forbidden, blob)

        illustration_slots = 0
        for page in model["pages"]:
            for element in page.get("elements", {}).values():
                if element.get("replace") == "theme_illustration":
                    illustration_slots += 1
                    self.assertTrue(
                        model["assets"][element["asset"]].startswith("/assets/theme/")
                    )
        self.assertEqual(illustration_slots, 23)

        for key in replicate._replaceable_asset_keys(self.base):
            source_rel = str((self.base.get("assets") or {}).get(key) or "").removeprefix("/")
            if source_rel:
                self.assertFalse((dest / "public" / source_rel).exists(), msg=key)
                self.assertNotIn(f"/{source_rel}", blob)

        gold_hashes = replicate._gold_replaceable_hashes(self.base, self.gold)
        residual_gold_pngs = [
            str(path.relative_to(dest))
            for path in (dest / "public").rglob("*.png")
            if replicate._sha256(path) in gold_hashes
        ]
        self.assertEqual(residual_gold_pngs, [])

        source_asset_refs = replicate._gold_replaceable_paths(self.base, self.gold)
        runtime_blob_parts: list[str] = []
        for path in dest.rglob("*"):
            if (
                path.is_file()
                and not path.is_symlink()
                and path.suffix.lower() in replicate.RUNTIME_TEXT_SUFFIXES
                and "node_modules" not in path.parts
            ):
                try:
                    runtime_blob_parts.append(path.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    pass
        runtime_blob = "\n".join(runtime_blob_parts)
        for source_ref in source_asset_refs:
            self.assertNotIn(source_ref, runtime_blob)
        self.assertIn(
            "/assets/theme/illustration.flu.card2_icon_a.png",
            (dest / "src/project.tsx").read_text(encoding="utf-8"),
        )

        for key in replicate._business_asset_keys(self.base):
            self.assertTrue(model["assets"][key].startswith("/assets/theme/"), msg=key)

        report = replicate.load_json(dest / "gap-report.json")
        self.assertTrue(report["ok"])
        self.assertEqual(report["gap_count"], 0)

    def test_complete_non_gold_theme_exports_editable_pptx(self) -> None:
        artifact = (
            ROOT
            / "poc/courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"
        )
        if shutil.which("node") is None or not artifact.is_file():
            self.skipTest("local artifact-tool runtime unavailable")

        result, dest = self.run_compiler(export_pptx=True)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        pptx = dest / "out" / "compiled_可编辑课件.pptx"
        self.assertTrue(pptx.is_file())
        self.assertGreater(pptx.stat().st_size, 20_000)

        with zipfile.ZipFile(pptx) as archive:
            slide_xml = sorted(
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            self.assertGreaterEqual(len(slide_xml), 12)
            text_blob = b"\n".join(archive.read(name) for name in slide_xml)
        self.assertIn("示例康".encode(), text_blob)
        self.assertIn("已审核内容".encode(), text_blob)
        self.assertNotIn("玛巴洛沙韦".encode(), text_blob)


if __name__ == "__main__":
    unittest.main()
