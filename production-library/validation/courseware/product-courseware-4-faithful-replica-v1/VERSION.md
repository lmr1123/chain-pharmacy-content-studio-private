# 商品培训课件4 · 保真复刻版本（唯一有效线）

| 字段 | 值 |
|------|-----|
| **版本 ID** | `product-courseware-4-faithful-replica-v1` |
| **状态** | `user-approved-gold-settled`（2026-08-03 更新归档） |
| **settled 目录** | `templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/` |
| **template_id** | `template.fuler-fanqiehongsu-product-courseware-4-v1` |
| **金样 revision** | `2026-08-03-motion-editor`（叙事/动效/编辑器动效/15 页 PPT） |
| **经验文档** | `docs/video-pptx-grammar-and-experience-v1.md` |
| **可编辑视频** | `npm run start:editor` · :9012 · `editable:cw4:*` |
| **重建静帧成片** | `python3 scripts/export-full-film-video.py` |
| **可编辑 PPTX** | `npm run export:pptx` · **15 页**原生可编辑 · 已同步金样 settled |
| **图层合同** | `layer-manifest.json` |
| **自建 HTML 编辑器** | ❌ 禁止 |
| **案例汇总** | `gold-samples/index.html` · 预览 `web/full-film.html` |
| **参考权威** | `/Users/liminrong/Downloads/商品培训课件4/商品培训课件4.mp4`（127.833s，854×480，30fps）+ 同目录 `.mp3` |
| **目标画布** | 1920×1080，30fps（由参考 2.25× 等比放大） |
| **产品名（屏显）** | 福尔番茄红素软胶囊 / 华圣元牌番茄红素软胶囊（以参考屏显为准） |
| **成片音频策略** | **双轨**：保真段复用参考切片；扩展段（**S12–S13 关联用药**）Qwen3 克隆补录。见下文 |
| **叙事顺序（扩展）** | …S10 适宜人群 → **S12/S13 关联用药** → **S11 三大核心功效表** → S15 结尾（**无** S14 四列表总表） |
| **片段工作室** | `docs/segment-studio-v1.md` · `scripts/segment_studio.py` · 状态 `out/segment-studio/state.json` |
| **当前全片时长** | ≈ **156.6s**（2026-08-03 删总表 + 重排后） |

---

## 音频与扩展（重要）

| 项 | 当前实现 | 说明 |
|----|----------|------|
| 参考原轨（只读） | `web/reference-narration.mp3` | 与下载参考 MD5 对齐；**禁止覆盖** |
| 工作旁白轨 | `web/working-narration.mp3` → `public/narration.mp3` | 编辑器与成片 mux 用此轨 |
| 保真段（含 S11 功效表、S15） | `audio_source=reference_slice` | 按 `reference_start/end` 从原轨切片（与成片顺序无关） |
| 扩展段 **S12–S13** | `audio_source=tts` · `tts_backend=clone` | 完整口播 + Qwen3 克隆；插在适宜人群与功效表之间 |
| ~~S14 四列表总表~~ | **已删除** | 用户裁定：参考无此段；收口用 S11 三大核心功效表 |
| 克隆 prompt | `out/segment-studio/reference-prompt.wav` | **必须**与 `ref_text` 词级对齐（见 segment-studio 门禁 / lesson） |

**硬教训（2026-08-03）**：prompt 音频截断 + 完整 ref_text → 每段开头泄漏「最大的十种…」。  
lesson：`lesson.qwen3-clone-prompt-audio-must-match-ref-text` · `lesson.cloned-tts-requires-post-generation-asr-gate`

---

## 与项目内其他目录的边界（必读）

本项目历史产物混杂，**只有本目录**才是「商品培训课件4 · 100% 参考保真复刻」工作线。

| 路径 | 关系 | 可否当母版 |
|------|------|------------|
| **本目录** `validation/courseware/product-courseware-4-faithful-replica-v1/` | 课件4 保真复刻（当前唯一有效） | 签样后才可 |
| `validation/video/tomato-lycopene-faithful-v1/` | **已否决**：同色系重设计，非参考复刻（`status: rejected-not-reference-faithful`） | **禁止** |
| `validation/courseware/sufuda-product-courseware-3-gold-v1/` 等 | **课件3** 金样线，另一参考片 | 禁止混入课件4 |
| `poc/gold-sample/`、`poc/reference-replica/` | 历史 PoC / 其他参考（感冒药等） | 禁止当课件4 构图源 |
| `production-library/templates/settled/` | 已签样业务模板 | 课件4 未签样前不写入 |

**硬规则**

1. 不读、不复用 `tomato-lycopene-faithful-v1` 的主视觉、文案重写稿、通用器官/盾牌插画作为“已复刻”。
2. 不套用 `template.product-training-faithful-v1` 的公共页骨架替代参考构图。
3. 缺包装 / Logo / 证据图 → **同位置同尺寸占坑**，禁止语义替换。
4. 用户确认「确实是同一个版本」前，**禁止扩制全片**、禁止抽取模板/槽位/动效语法进 settled。

---

## 推进闸门（用户已锁定）

```
[1] 逐屏/逐时码登记 observed_reference
        ↓
[2] 门禁：1 静态页 + 1 动态微镜头，与参考同一时刻左右并排
        ↓
[3] 用户确认门禁可继续          ← 已通过（2026-08-02）
        ↓
[4] 扩制全片 + 技术/视觉 QA
        ↓
[5] 全片通过后 → 抽取模板 / 槽位 / 动效语法
        ↓
[6] PPTX + 视频可编辑导出；主题槽位扩展
```

### 经验沉淀（2026-08-02 / 2026-08-03）

已写入全局经验（**视频与 PPT 共用** + **可编辑金样双轨** + **扩展段克隆**）：

| 产出 | 路径 / id |
|------|-----------|
| 语法全文 | `docs/video-pptx-grammar-and-experience-v1.md` |
| 可编辑视频门禁 | `docs/editable-video-v1.md` §双轨静帧 |
| 片段旁白工作室 | `docs/segment-studio-v1.md` §克隆 prompt 门禁 |
| lessons | `lesson.editor-bg-must-omit-editable-layers-gold-template` · **`lesson.qwen3-clone-prompt-audio-must-match-ref-text`** · `lesson.cloned-tts-requires-post-generation-asr-gate` |
| scene-recipe | `scene-recipe.related-meds.courseware-training-v1` · `scene-recipe.summary-row-headers.courseware-training-v1` |
| component | `component.scene.related-meds-note-above-v1` · `component.scene.summary-row-headers-v1` |
| 叙述源 | 仓库根 `tasks/lessons.md` · 2026-08-02 / **2026-08-03** |
| 任务板 | 本包 `tasks-todo.md`（下一阶段：**视频调优**） |

---

## 本目录结构

```
product-courseware-4-faithful-replica-v1/
├── VERSION.md                 ← 本文件
├── README.md
├── tasks-todo.md              ← 本版本任务（与根 tasks/todo 交叉引用）
├── docs/
│   └── screen-registry.json   ← 逐屏登记（原文/对象/位置/尺寸/层级/动作）
├── reference/                 ← 仅分析用，不进成片像素
│   ├── frames/ keyframes/ audio/ asr/
├── gate/                      ← 门禁交付（静态 + 微镜头 + 对照）
│   ├── static-time-list.html
│   ├── micro-time-reveal.html
│   ├── compare.html
│   └── reference-clips/
└── out/                       ← 渲染产物（签样前仅门禁）
```
