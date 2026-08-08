#!/usr/bin/env python3
"""Force training typeface (HarmonyOS Sans SC) into every text run of a PPTX.

artifact-tool often omits fontFamily or writes Calibri; PowerPoint / Preview
then fall back to system fonts. This patch:
  - injects latin/ea/cs typeface on every a:rPr / a:endParaRPr
  - rewrites any existing typeface= to the target font
  - rewrites theme major/minor fonts away from Calibri
"""
from __future__ import annotations

import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path


def inject(xml: str, font: str) -> str:
    font_kids = (
        f'<a:latin typeface="{font}" panose="020B0604030504040204" '
        f'pitchFamily="34" charset="-122"/>'
        f'<a:ea typeface="{font}" pitchFamily="34" charset="-122"/>'
        f'<a:cs typeface="{font}" pitchFamily="34" charset="-122"/>'
    )

    # Force-replace any existing typeface attributes in text runs
    xml = re.sub(
        r'(<(?:a:latin|a:ea|a:cs)\b[^>]*?\btypeface=")[^"]*(")',
        rf'\1{font}\2',
        xml,
    )

    def ensure_font_children(open_tag: str, close_name: str) -> str:
        """If rPr has no typeface children, append them."""
        if "typeface=" in open_tag:
            return open_tag
        if open_tag.endswith("/>"):
            return open_tag[:-2] + ">" + font_kids + f"</{close_name}>"
        if open_tag.endswith(">"):
            return open_tag + font_kids
        return open_tag

    def repl_rpr(m: re.Match[str]) -> str:
        return ensure_font_children(m.group(0), "a:rPr")

    def repl_epr(m: re.Match[str]) -> str:
        return ensure_font_children(m.group(0), "a:endParaRPr")

    # Only match opening tags without nested content for empty rPr
    xml = re.sub(r"<a:rPr\b[^>/]*(?:/>|>)", repl_rpr, xml)
    xml = re.sub(r"<a:endParaRPr\b[^>/]*(?:/>|>)", repl_epr, xml)
    return xml


def patch_theme(xml: str, font: str) -> str:
    # major/minor latin + ea fonts in theme
    xml = re.sub(
        r'(typeface=")(?:Calibri(?: Light)?|Arial|Helvetica|sans-serif)(")',
        rf'\1{font}\2',
        xml,
    )
    xml = re.sub(
        r'(<(?:a:latin|a:ea|a:cs)\b[^>]*?\btypeface=")[^"]*(")',
        rf'\1{font}\2',
        xml,
    )
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
            elif name.startswith("ppt/theme/") and name.endswith(".xml"):
                text = data.decode("utf-8")
                data = patch_theme(text, font).encode("utf-8")
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
