# QA 报告 · 番茄红素商品培训课件4 film v2

日期：2026-08-05（阶段5 插画重生成后重渲）

## 技术门禁（render-film 硬校验 + 实测）

| 检查项 | 结果 |
| --- | --- |
| 分辨率 | 1920×1080 PASS |
| 帧率 | 30 fps PASS |
| 时长 | 156.620 s（旁白轨合同 156.62 s）PASS |
| 总帧数 | 4695（逐页帧量化理论值）PASS |
| 黑场 blackdetect | 未检出 PASS |
| 音频响度 | 实测 −16.4 LUFS（loudnorm 一遍测），TP 限幅 −1.5 dB PASS |
| 音频内容抽查 | 30–35 s 切片 mean −16.8 dB / max −1.5 dB，旁白在轨 PASS |

## 合同锁定（本轮未动）

- 文案、时码（scenes[].start/end 总和 = 156.62 s）、旁白轨 `web/working-narration.mp3`、包装/实拍占位槽（slot-pack-* / slot-photo-*）。

## v2 变更范围

| 阶段 | 内容 | 验证 |
| --- | --- | --- |
| 1 | PIL→Revideo 迁移，film 骨架 | 门禁1 签样（2026-08-04） |
| 2 | editor-bg Revideo 化 + 导出引擎切换 | S10/S11 叠合 |
| 3 | 15 页动效编排 | 门禁2 签样（2026-08-05） |
| 5 | 7 张主视觉插画重生成（暖调扁平 v1） | 门禁3 编辑器签样（2026-08-05） |

## 插画重生成门禁（阶段5）

- 风格基线 `assets/style-brief-v1.md`（锚点 couple.png）；生成通路 codex-cli + `--ref` 风格锚。
- alpha 硬门禁（`scripts/check-alpha.py`）：7/7 四角 alpha=0、白晕环带 0%（基线与重生成对照：`qa/asset-alpha-baseline.json` / `qa/asset-alpha-regen.json`）。
- 丝绸底横排：`qa/regen-p0-silk.jpg`、`qa/regen-p1-silk.jpg`、`qa/regen-s07-gate-silk.jpg`。
- 成片抽帧验证：`qa/regen-film-frames/`（S04 前列腺 / S05 O₂+护肤 / S06 NK 细胞 / S10 适宜人群四卡，含序贯入场末帧 112.8 s）。
- 原图备份：`assets/generated/_regen_v1/originals-backup/`（7 张，可整体回退）。
- 登记：`assets/asset-provenance.json`（regen v1 段）。

## 已知差距（诚实记录）

1. **包装/照片**：slot-pack-* / slot-photo-* 为授权占位槽，非品牌授权图；编辑器可换授权资产，不动时间轴。
2. **PPTX 导出**：版式落后于 v2 视频（本轮未同步），见交付说明。
3. **旁白音色**：工作轨为既有合成音色，非真人录制。
4. **o2.png / nk-cell.png 旧资产**仍在 assets 中（layout 未引用），留作素材库，不进成片。
