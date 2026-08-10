#!/usr/bin/env python3
"""Fail-closed structural and gold-residue checks for the 20-page red courseware."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


SOURCE_SHA256 = "b5787a64b1febca3fb32f6b6037830cb4e768a362950a96c28b76baaefd227bc"
ALLOWED_SOURCE_MEDIA = {"ppt/media/image2.jpeg", "ppt/media/image4.jpeg"}
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip()


def xml_text_nodes(archive: zipfile.ZipFile, names: list[str]) -> list[str]:
    result: list[str] = []
    for name in names:
        try:
            root = ET.fromstring(archive.read(name))
        except ET.ParseError:
            continue
        result.extend(node.text or "" for node in root.findall(".//a:t", NS))
    return result


def run(
    source: Path,
    pptx: Path,
    theme_name: str,
    approved_assets: dict[str, dict[str, str]],
) -> dict[str, object]:
    errors: list[str] = []
    source_sha = sha256_file(source)
    if source_sha != SOURCE_SHA256:
        errors.append(f"source SHA-256 mismatch: {source_sha}")

    try:
        source_zip = zipfile.ZipFile(source)
        output_zip = zipfile.ZipFile(pptx)
    except zipfile.BadZipFile as exc:
        return {"ok": False, "errors": [f"invalid PPTX ZIP: {exc}"]}

    with source_zip, output_zip:
        source_media_names = sorted(
            name for name in source_zip.namelist() if name.startswith("ppt/media/")
        )
        allowed_hashes = {
            sha256_bytes(source_zip.read(name))
            for name in source_media_names
            if name in ALLOWED_SOURCE_MEDIA
        }
        forbidden_hashes = {
            sha256_bytes(source_zip.read(name))
            for name in source_media_names
            if name not in ALLOWED_SOURCE_MEDIA
        }
        output_media_names = sorted(
            name for name in output_zip.namelist() if name.startswith("ppt/media/")
        )
        output_media_hashes = {
            name: sha256_bytes(output_zip.read(name)) for name in output_media_names
        }
        output_hash_set = set(output_media_hashes.values())
        missing_assets = sorted(
            key
            for key, value in approved_assets.items()
            if str(value.get("sha256") or "") not in output_hash_set
        )
        if missing_assets:
            errors.append(
                "approved image assets missing from PPTX: "
                + ", ".join(missing_assets[:12])
            )
        leaked_media = sorted(
            name
            for name, digest in output_media_hashes.items()
            if digest in forbidden_hashes
        )
        if leaked_media:
            errors.append("source media SHA-256 survived: " + ", ".join(leaked_media[:12]))

        slide_names = sorted(
            (
                name
                for name in output_zip.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=lambda name: int(re.search(r"(\d+)", Path(name).stem).group(1)),
        )
        if len(slide_names) != 20:
            errors.append(f"slide count {len(slide_names)}/20")
        output_nodes = xml_text_nodes(output_zip, slide_names)
        output_text = "\n".join(output_nodes)
        if len(output_nodes) < 100:
            errors.append(f"native text nodes too few: {len(output_nodes)}")
        if theme_name not in output_text:
            errors.append("theme_name missing from native slide text")
        if "康爱森" in output_text:
            errors.append("source identity 康爱森 survived")
        if not re.search(r"番茄红素|lycopene", theme_name, re.I) and re.search(
            r"番茄红素|lycopene", output_text, re.I
        ):
            errors.append("non-lycopene theme contains source topic identity")

        source_slide_names = sorted(
            name
            for name in source_zip.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        source_nodes = xml_text_nodes(source_zip, source_slide_names)
        output_normalized = normalized(output_text)
        leaked_fragments: list[str] = []
        for raw in source_nodes:
            fragment = normalized(raw)
            if len(fragment) >= 8 and fragment in output_normalized:
                leaked_fragments.append(fragment)
        if leaked_fragments:
            errors.append(
                "source medical/reference copy survived: "
                + " | ".join(sorted(set(leaked_fragments), key=len, reverse=True)[:8])
            )

        missing_parts = [
            name
            for name in ("[Content_Types].xml", "ppt/presentation.xml")
            if name not in output_zip.namelist()
        ]
        if missing_parts:
            errors.append("missing OOXML parts: " + ", ".join(missing_parts))

    return {
        "schema": "ingredient-health-edu-pptx-validator/v1",
        "ok": not errors,
        "errors": errors,
        "source_sha256": source_sha,
        "page_count": len(slide_names),
        "native_text_nodes": len(output_nodes),
        "output_media_count": len(output_media_names),
        "forbidden_source_media_hashes": len(forbidden_hashes),
        "allowed_style_media_hashes": len(allowed_hashes),
        "source_media_leaks": leaked_media,
        "approved_asset_count": len(approved_assets),
        "approved_assets_missing": missing_assets,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--theme-name", required=True)
    parser.add_argument("--approved-assets", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    approved_assets = json.loads(args.approved_assets.read_text(encoding="utf-8"))
    report = run(
        args.source.resolve(),
        args.pptx.resolve(),
        args.theme_name.strip(),
        approved_assets,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
