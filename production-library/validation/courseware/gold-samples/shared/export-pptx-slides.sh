#!/usr/bin/env bash
# 将 PPTX 导出为 preview 用的逐页 PNG（依赖本机 Microsoft PowerPoint + pdftoppm）
# Usage:
#   bash export-pptx-slides.sh /path/to/file.pptx /path/to/out-dir
set -euo pipefail
PPTX="${1:?pptx path}"
OUT="${2:?out dir}"
PDF="$(mktemp -t gold-pptx).pdf"
mkdir -p "$OUT"
osascript <<APPLESCRIPT
set pptxPath to POSIX file "$PPTX"
set pdfPath to POSIX file "$PDF"
tell application "Microsoft PowerPoint"
  open pptxPath
  delay 1.5
  set thePres to active presentation
  save thePres in pdfPath as save as PDF
  close thePres saving no
end tell
APPLESCRIPT
pdftoppm -png -r 120 "$PDF" "$OUT/slide"
rm -f "$PDF"
echo "slides -> $OUT ($(ls "$OUT"/slide-*.png 2>/dev/null | wc -l | tr -d ' ') pages)"
