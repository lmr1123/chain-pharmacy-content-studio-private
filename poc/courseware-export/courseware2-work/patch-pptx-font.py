#!/usr/bin/env python3
"""Inject a CJK-capable typeface into every text run of a PPTX.

artifact-tool often omits fontFamily on body runs; PowerPoint then falls back
to Calibri. This patch writes latin/ea/cs typeface on each a:rPr.
"""
from __future__ import annotations

import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path


def inject(xml: str, font: str) -> str:
    font_xml = (
        f'<a:latin typeface="{font}" panose="020B0604030504040204" '
        f'pitchFamily="34" charset="-122"/>'
        f'<a:ea typeface="{font}" pitchFamily="34" charset="-122"/>'
        f'<a:cs typeface="{font}" pitchFamily="34" charset="-122"/>'
    )

    def repl_rpr(m: re.Match[str]) -> str:
        tag = m.group(0)
        if "typeface=" in tag:
            return tag
        if tag.endswith("/>"):
            return tag[:-2] + ">" + font_xml + "</a:rPr>"
        if tag.endswith(">"):
            return tag + font_xml
        return tag

    def repl_epr(m: re.Match[str]) -> str:
        tag = m.group(0)
        if "typeface=" in tag:
            return tag
        if tag.endswith("/>"):
            return tag[:-2] + ">" + font_xml + "</a:endParaRPr>"
        if tag.endswith(">"):
            return tag + font_xml
        return tag

    xml = re.sub(r"<a:rPr\b[^>/]*(?:/>|>)", repl_rpr, xml)
    xml = re.sub(r"<a:endParaRPr\b[^>/]*(?:/>|>)", repl_epr, xml)
    return xml


def patch(path: Path, font: str = "HarmonyOS Sans SC") -> int:
    buf = BytesIO()
    changed = 0
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(
        buf, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            name = info.filename
            if (
                name.startswith("ppt/slides/slide")
                and name.endswith(".xml")
                and "Rel" not in name
            ):
                text = data.decode("utf-8")
                new = inject(text, font)
                if new != text:
                    changed += 1
                data = new.encode("utf-8")
            elif name == "ppt/theme/theme1.xml":
                text = data.decode("utf-8")
                text = re.sub(
                    r'(typeface=")Calibri(?: Light)?"',
                    rf'\1{font}"',
                    text,
                )
                data = text.encode("utf-8")
            zout.writestr(info, data)
    path.write_bytes(buf.getvalue())
    return changed


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: patch-pptx-font.py <file.pptx> [font-name]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    font = sys.argv[2] if len(sys.argv) > 2 else "HarmonyOS Sans SC"
    n = patch(path, font)
    print(f"patched_slides={n} font={font} out={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
