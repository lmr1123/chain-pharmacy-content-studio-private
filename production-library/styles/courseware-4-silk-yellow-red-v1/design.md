# 课件4 · 丝绸底黄字红描边 v1

**style_pack_id:** `style-pack.courseware-4-silk-yellow-red-v1`<br>
**状态:** `candidate`<br>
**机器可读:** 同目录 `tokens.json`<br>
**来源:** `product-courseware-4-faithful-replica-v1` 导出器 `C` 常量 + `silkBg()` + 字号表 `TS` + `primitives.ts`<br>
**用途:** 商品培训课件4 金样皮肤；通用引擎构件只读本 tokens，**旧 `export-cw4-pptx.mjs` 一行不动**

---

## 一句话气质

丝绸灰褐舞台底 + **黄字红描边**章节标题 + 品牌红强调，偏「线下培训片 / 舞台感商品课件」，信息密度高、对比强。

---

## 画布与坐标

| 项 | 值 |
|----|-----|
| 设计坐标（视频） | 1920 × 1080 |
| PPT 画布 | 1280 × 720 |
| 缩放 | `SX = SY = FS = 720/1080 ≈ 0.6667` |
| 字号换算 | `pptx_pt = round(design_px × FS)` |
| 定位习惯 | 支持中心坐标 `centerBox(cx, cy, w, h)`（原点在画布中心） |

导出后字体 patch：**HarmonyOS Sans SC**（与金样一致）。

---

## 色板（来自导出器 `C`）

| 角色 | 色值 | 用途 |
|------|------|------|
| `silk` 底 | `#cecbc4` | 全页丝绸底 |
| `silk_deep` / `silk_light` | `#b8b4ab` / `#e4e1da` | 底层次（可选） |
| `card` / 舞台 | `#f3efe6` | **暖米卡片**（禁止纯白 `#fff` 贴丝绸底） |
| `card_soft` / note_bar | `#ebe6dc` | 说明条、次级面板 |
| `ink` | `#1a1a1a` | 主文近黑 |
| `red` | `#c43c2c` | 品牌红 · nav 激活 · 连接符 |
| `red_deep` | `#a83224` | 加深 |
| `red_outline` | `#ba3034` | 章节描边同源 |
| `yellow` | `#ffe33c` | **章节标题填充** |
| `lime` | `#e9f200` | chevron / 高亮点缀 |
| `brown` | `#6a3a30` | 小节标签、行卡标签 |
| `brown_label` | `#a05040` | 视频轨标签同源 |
| `label` / `body_brown` | `#9a3c2e` / `#8a3a28` | 标签 / 暖棕正文 |
| `muted` / `dark` | `#555555` / `#4f4f4f` | 次文 |
| `gold` | `#e8c020` | 大号等号 / 点缀 |
| `pill_off` | `#d8d4cc` | nav 未激活 / 占位底 |
| `card_border` | `#e0dcd4` | 白卡边 |
| `white` | `#ffffff` | 卡面、激活字 |
| `caption` | `#111111` | 底栏讲解字幕（禁白字字幕） |

### 禁止

- 构件内字面量色（只读 tokens）
- 字幕用白字（金样锁定近黑 caption）
- 图片 stretch（`image_fit = contain`）
- 无授权包装；缺图 →「待业务授权」占位槽

---

## 丝绸底 `chrome_bg`（`silkBg`）

1. 全幅 rect 填 `#cecbc4`
2. 顶边细高光条：高 8（设计坐标），`rgba(255,255,255,0.22)`
3. 右下极淡椭圆晕：中心约 (720, 460)、尺寸 720×360，`rgba(255,255,255,0.08)`

**不要**加半透明大块矩形——会被当成空白内容卡。

---

## 章节标题（金样签名件）

- 填充：`#ffe33c` 黄字（顶层 editable 主对象）
- 描边：4 向偏移红字（±2.5 设计 px）色 `#c43c2c`
- 设计字号：56 → PPT ≈ 37 pt
- 位置：`centerBox(0, -460, 1400, 90)`

---

## 字体与字号

| 项 | 值 |
|----|-----|
| 主字体 | **HarmonyOS Sans SC** |
| 回退 | Source Han Sans SC → PingFang SC → Microsoft YaHei |
| **培训放大** | `type.scale_factor = 1.28`（投影可读） |
| **正文下限** | ≥ **16 pt**；说明 ≥ **14 pt** |

### 设计字号 → 培训 PPT pt（×1.28 后约）

| 角色 | design px | 培训 ppt pt（约） |
|------|-----------|-------------------|
| 封面标题 | 48 | ~41 |
| 章节 | 56 | ~47 |
| 小节 | 42 | ~36 |
| 列表主项 | 48 | ~41 |
| 正文档 | 24–32 | ≥16 |
| 大号等号 | 100 | ~86 |

对齐 `docs/courseware-visual-spec-1080p.md`：培训投影以可读为先，不机械沿用视频轨缩到过小。

## 插图去底

主视觉插画（番茄/器官/箭头/人群等）**必须 RGBA 透明底**，四角 alpha≤8，贴丝绸底无白块。<br>
流程：`whitekey-cutout.py` → `check-alpha.py` / `ensure_transparent_assets.py`。<br>
豁免：`slot-pack-*` 包装占位卡、`slot-photo-*` 实拍、`slot-time-*` 杂志封面。

---

## 构件皮肤约定

| 构件 | 本风格表现 |
|------|------------|
| `chrome_bg` | 丝绸底 + 顶光 + 淡晕 |
| `chapter_title` | 黄字红描边 4 向 |
| `section_label` | 棕色字 + 柠檬 chevron |
| `nav_pills` | 激活红底白字 · 未激活丝灰底灰字 · **N 自适应**（勿写死 2 个） |
| `white_stage` | 白卡 + `#e0dcd4` 边 |
| `row_card` | 棕标签 + 深灰正文 |
| `image_chain` | contain 装箱 + 红连接符 · auto-center |
| `pack_slot` | 丝灰底 +「待业务授权」 |
| `data_stat` | 红大数字 + 灰单位（新页型共用） |
| `note_bar` | 暖棕近黑说明字 |
| `audience_card` | 上图下墨字标签 |
| `icon_bullet` | 深灰条目 |

---

## 与米白番茄红的差异

| 维度 | 本包 silk-yellow-red | cream-red |
|------|----------------------|-----------|
| 底 | 丝绸舞台 | 米白平铺 |
| 章节 | 黄+红描边 | 番茄红 |
| 字体 | HarmonyOS Sans SC | Noto Sans SC |
| 导航未激活 | `#d8d4cc` | `#EDE7DF` |
| 气质 | 培训片舞台 | 科普杂志 |

---

## 金样回归纪律

- 新引擎用金样 content-model + **本 style** 导出后，QA 须与<br>
  `templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/preview/`（或 validation 金样预览）并排一致<br>
- 不一致 = 重构破金样，停下修<br>
- 旧导出器路径保持可复现，禁止「顺手改 cw4」

---

## 签样与升级

- 当前：`candidate`（数据化抽取完成，待 M2 引擎挂载）
- 升 `production-validated`：金样回归通过 + 用户签样
- 稳定 ID 约定（金样）：`editable:cw4:{page}:{role}` —— 新引擎可泛化为 `editable:{engine}:{page}:{role}`

---

## 红线

1. 不改 `export-cw4-pptx.mjs` 硬编码作「快捷修色」<br>
2. 文案不进本文件<br>
3. 无授权不仿包装<br>
4. 图片 contain，禁 stretch<br>
5. 纠正写 `tasks/lessons.md`
