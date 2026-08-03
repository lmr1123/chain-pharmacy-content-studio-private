# 商品培训课件4 · 保真复刻 v1

> **不是** `tomato-lycopene-faithful-v1`。那条线已否决。见 `VERSION.md`。

## 当前进度

| 阶段 | 状态 |
|------|------|
| 参考抽帧 / ASR / 场景切点 | ✅ |
| 逐屏登记 `docs/screen-registry.json` | ✅ |
| 门禁：1 静态页 + 1 微镜头 + 对照 | ✅ 用户已确认可继续 |
| 全片 13 场景 HTML 预览 | ✅ `web/full-film.html` |
| 全片内容模型 | ✅ `content-model.json` |
| 全片视频 | ✅ `out/商品培训课件4_保真复刻_全片_v1.mp4`（≈**156.6s**，15 场景） |
| 叙事顺序 | ✅ …适宜人群 → **关联用药** → **三大核心功效表** → 结尾（已删 S14 总表） |
| 插画 / 包装 | 插画结构重建；包装/实拍**占坑** → 调优时替换 |
| 关键动效烤进视频轨 | ⏳ **下一阶段：视频调优** |
| **内容源 / 静帧成片** | ✅ `content-model` → `export-full-film-video.py` |
| **图层合同** | ✅ `layer-manifest.json`（`editable:cw4:…`） |
| **可编辑视频（项目流程）** | ✅ **已对接** Revideo 业务编辑器 `npm run start:editor` → :9012 |
| **片段编排 + 扩展旁白** | ✅ `docs/segment-studio-v1.md` · S12–S13 克隆有声（已去 prompt 泄漏） |
| **可编辑 PPTX** | ✅ `npm run export:pptx` → **15 页**原生可编辑（对标速福达） |
| **经验沉淀** | ✅ `docs/video-pptx-grammar-and-experience-v1.md` · 根 `tasks/lessons.md` |
| **模板整包 settled** | ✅ `templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/`（**2026-08-03 已更新归档**） |
| **案例汇总** | ✅ `gold-samples/index.html` · 预览 `web/full-film.html` |
| **任务板** | `tasks-todo.md`（旁白阶段已收口 → 视频调优待开做） |

## 可编辑视频 / PPTX = 项目既有流程

权威说明：仓库根目录 `docs/revideo-business-editor-usage.md`  
样板：速福达 `npm run export:pptx` / `start:editor`（Artifact Tool 原生层 + Revideo `editable:`）

本包说明：`docs/editable-video-v1.md` · 经验：`docs/video-pptx-grammar-and-experience-v1.md`

```bash
# 业务编辑器（项目既有流程）
npm run start:editor
# → http://127.0.0.1:9012/  图层 editable:cw4:*

# CLI 重建签样静帧成片
python3 scripts/export-full-film-video.py

# 原生可编辑 PPTX（15 页，与视频共用 content-model）
npm run export:pptx
# → out/福尔番茄红素_商品培训课件4_可编辑课件_v1.pptx

# 视频 + PPTX 一并重建
python3 scripts/build_deliverables.py
```

## 怎么验收门禁

```bash
# 浏览器打开对照页（推荐）
open production-library/validation/courseware/product-courseware-4-faithful-replica-v1/gate/compare.html
```

对照约定：

- **左**：参考视频同一时刻截帧（或循环片段）
- **右**：本次重建（静态定格 / 微镜头动画）
- 缺素材处必须是**灰底占坑 + 标签**，不得换成自创主视觉

确认话术（请明确回复其一）：

- 「**确实是同一个版本**，可以扩全片」
- 「不是同一版本，问题点：……」

## 参考权威

- 视频：`/Users/liminrong/Downloads/商品培训课件4/商品培训课件4.mp4`
- 音频：同目录 `商品培训课件4.mp3`
- 屏显原文以视频帧为准；ASR 仅辅助时码，域词错误已按屏显校正写入 registry
