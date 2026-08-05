#!/bin/bash
# v2 QA 抽帧：覆盖 16 项精修的每个动效节点
set -e
cd "$(dirname "$0")/.."
OUT=out/速福达_商品培训课件3_独立金样_v2.mp4
D=qa/v2-frames
mkdir -p "$D"
# 时刻:标签
marks="
0.30:cover-in
0.52:cover-slideout
6.20:flu48-rule
6.45:flu48-pulse
10.90:flu-slideout
11.10:ch1-sweepin
12.45:ch1-sweepout
14.70:b2-collision
16.50:b2-orbit-early
21.70:b2-divider-osel
28.00:b2-orbit-late
30.40:b3-shadow-pulse
36.95:shell-slideout
38.60:f1-baby
39.20:f1-ring
39.80:f1-shield
42.60:f1-slideout
63.90:a1-shadow
64.60:a1-pulse
77.20:c1-line
77.60:c1-rule
78.30:c1-sweep
84.00:c2-line
90.30:ch5-sweep
91.00:sm-eyebrow-head
91.60:sm-row2
92.60:sm-collapse
93.10:final
"
echo "$marks" | while IFS=: read -r t tag; do
  [ -z "$t" ] && continue
  ffmpeg -loglevel error -ss "$t" -i "$OUT" -frames:v 1 -y "$D/${tag}_${t}.png"
done
# 拼 4 张 contact sheet（每张 7 帧，2 列）
cd "$D"
ls *.png | sort | split -l 7 - sheet_
for f in sheet_*; do
  montage "$f" -tile 2x -geometry 640x360+4+4 "${f}.jpg"
done
echo "done: $(ls *.png | wc -l) frames"
