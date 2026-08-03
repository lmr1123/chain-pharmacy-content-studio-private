# 业务 WorkBuddy 傻瓜交付方案

**状态：** 方案锁定 · 持续迭代  
**更新日期：** 2026-08-03  
**目标读者：** 产品 / 制作 / 代理（WorkBuddy）实现侧；业务只读「§0 一页给业务」与「§9 口令卡」  

**关联：**

| 文档 / 资产 | 关系 |
|-------------|------|
| `docs/project-brief.md` | 金样优先、可培训交付、不编造药学结论 |
| `docs/product-training-script-driven-assembly.md` | 风格包 + 场景配方 + 内容驱动 |
| `docs/revideo-business-editor-usage.md` | 画面图层编辑器（返修，非默认门槛） |
| `docs/seed-asset-library-bootstrap.md` §9 | 业务新增主题傻瓜路径 |
| `production-library/templates/settled/` | 正式模板与业务 Word |
| `production-library/voices/` + `registries/voices.json` | 克隆语音包 |
| `outputs/业务使用资料包/` | 现有业务 Word 资料包雏形 |
| `production-library/validation/courseware/gold-samples/index.html` | 金样汇总（货架雏形） |

**一句话目标：**

> **业务 + WorkBuddy** 协作交付：业务只做「看模板 → 选模板 → 填框架 → 审初稿 → 拿成片」；  
> WorkBuddy 执行工厂（套 settled、内容驱动、克隆声、出 PPTX/MP4）；  
> **正常路径不经制作手工**；制作仅异常返修。禁止系统机器人音色与假包装。

---

## 0. 一页给业务（可直接转发）

### 你怎么用（4 步）

1. **看效果**：打开「模板货架」页面，点每个模板的关键页截图 / 金样视频，确认观感。  
2. **选模板**：记住中文课型名（见下表）。  
3. **填框架**：复制该模板的「空白 Word」，按章节填**已审核**文案；没有的章节整段删掉；条数有几条写几条。  
4. **交给 WorkBuddy**：发 Word + 授权包装图，说：「先出初稿/分镜预览给我确认，确认后再出 PPTX/视频。」

### 你不需要

- 装 Node、起端口、懂「可编辑图层」  
- 指定字号、坐标、页数、动画参数  
- 为对齐示例硬凑 3 条联合用药（2 条就 2 条）  
- 用系统朗读当正式旁白  

### 课型菜单（业务只认中文名）

| 业务说法 | 典型产物 | 仓库模板目录（代理侧） |
|----------|----------|------------------------|
| 疾病科普视频（如风热证） | MP4 | `settled/health-video-reference-tech-v1` |
| 商品培训视频（如辅酶 Q10） | MP4 | `settled/product-video-faithful-v1` |
| 绿色单品 PPT（如金银花露） | 可编辑 PPTX | `settled/product-courseware-green-v1` |
| 疾病+商品场景 PPT（如穿心莲） | 可编辑 PPTX | `settled/disease-product-scenario-v1` |
| 商品培训课件3（视频+PPT，速福达壳） | MP4 + PPTX | `settled/sufuda-mabaloshawei-product-courseware-3-v1` |
| 商品培训课件4（视频+PPT，番茄红素壳） | MP4 + PPTX | `settled/fuler-fanqiehongsu-product-courseware-4-v1` |

---

## 1. 问题与原则

### 1.1 要解决的问题

1. 模板多，业务**不知道每种长什么样** → 必须有关键页预览货架。  
2. 填表若固定 3 行/固定页码 → 出现空白行或硬凑 → **禁止**；改为内容驱动。  
3. 视频比 PPT 多旁白与出图 → 业务不能碰 TTS 参数；应用 **模板绑定的克隆语音包** + 系列插画策略。  
4. 整库工程不能当业务安装包 → 分层交付（业务包 / 代理站 / 制作站）。

### 1.2 硬原则（迭代时不得偏离）

| # | 原则 |
|---|------|
| P1 | **金样优先**：只套已 settled / 已签样模板的风格与框架，不现场自由发挥。 |
| P2 | **内容驱动**：有几条出几条；未填则空或省略模块；禁止空行凑满金样示例数。 |
| P3 | **审核旁白锁定**：TTS 只朗读业务（药师/合规）已审原文；默认禁止 AI 编造功效与数据。 |
| P4 | **真包装业务供**：无授权包装用槽位「待补」；禁止仿品牌包装。 |
| P5 | **讲解声跟模板走**：默认用模板 `voice pack` 本地克隆；禁止默认系统机器人音色。 |
| P6 | **先确认后成片**：PPT 先内容初稿；视频先分镜预览 + 缺口清单。 |
| P7 | **编辑器是返修不是门槛**：默认路径不要求业务打开 Revideo 端口。 |

登记对齐：`decision.gold-sample-first`、`lesson-multi-theme-courseware-input-must-be-content-driven`、`decision.semantic-block-voice-speed-gate`。

---

## 2. 角色与交付分层

### 2.1 三种角色

| 角色 | 工具 | 职责 |
|------|------|------|
| **业务** | 浏览器看货架 + Word + WorkBuddy 对话 | 选模板、填审核内容、附授权图、审初稿/分镜 |
| **WorkBuddy（代理）** | 本机项目 + 本方案系统提示 | 解析 Word、套模板、自适应排版、克隆旁白、列缺口、导出 |
| **制作** | 全库 + 业务编辑器 + 剪映 | 金样沉淀、新页型、语音包、返修疑难 |

### 2.2 三档交付物（按对方能力发）

#### 档 A · 纯业务包（默认发给一线）

```text
药店培训内容工厂-业务包/
  00_一页怎么用.md                 # 摘自本文 §0
  01_模板货架/                     # 或 online_url
    index.html
  02_空白Word/                     # 按课型
  03_填写参考/                     # 标明「仅示范格式」
  04_WorkBuddy口令卡.md            # §9
  05_交付物放这里/                 # 空目录
```

**不含** `poc/`、`node_modules`、端口表、validation 工程。

#### 档 B · 代理工作站（业务电脑已装 WorkBuddy）

在档 A 基础上增加：

- 本仓库（或精简 monorepo）  
- WorkBuddy **系统提示词**（本文 §8）  
- 只读访问 `templates/settled`、`voices`、生成脚本入口  

#### 档 C · 制作完整环境

全库 + 金样汇总 + `npm run start:*-editable` 等；**不对业务默认开放**。

---

## 3. 模板货架与关键页预览（迭代项 A）

### 3.1 业务体验

安装/打开后第一动作是打开货架，而不是空白 Word：

```text
模板货架
  ├─ 卡片：封面 + 中文名 + 一句话适用场景
  ├─ 关键帧 3～6 张（PPT 关键页 / 视频关键镜头）
  ├─ 点开：整片预览（视频）或逐页预览（PPT）
  └─ 「就用这个模板」→ 给出对应空白 Word 路径或下载
```

### 3.2 每个 settled 模板强制结构（目标契约）

```text
production-library/templates/settled/<slug>/
  manifest.json
  业务提交_空白模板.docx
  业务提交_填写参考.docx
  <canonical 成片>.pptx | .mp4
  preview/
    cover.png                 # 16:9 货架封面
    key-01.png … key-0N.png   # 关键页/镜头
    preview.html              # 可离线打开的单模板预览（可选）
  voice/                      # 仅视频类或视频+PPT 类（见 §6）
    voice-pack.json
    prompt.wav
    ref_text.txt
```

### 3.3 manifest 预览字段（目标）

```json
"preview": {
  "cover": "preview/cover.png",
  "key_frames": ["preview/key-01.png", "preview/key-02.png"],
  "gallery_title_zh": "绿色商品培训 · 5 页",
  "one_liner": "单品店员培训：介绍 / 卖点 / 联合用药 / 对标 / 注意",
  "online_url": null
}
```

### 3.4 实现来源（减少重复劳动）

| 来源 | 用途 |
|------|------|
| `gold-samples/*/web/media/cover-*` 与 thumbs | 批量生成 `preview/key-*.png` |
| `gold-samples/index.html` | 升格为「业务模板货架」或生成 `交付/业务包/01_模板货架` |
| 各 validation `web/full-film.html` / `preview.html` | 深度预览链接 |

### 3.5 验收

- [x] 六个 settled 模板均有 cover + ≥3 关键帧  
- [x] 业务不打开仓库也能在货架页辨认课型差异  
- [x] 选模板后 1 步到达空白 Word  

**实现：** `scripts/sync_settled_template_previews.py` → 各模板 `preview/`；`scripts/build_business_tier_a_package.py` → 档 A 货架。

---

## 4. 框架填写与内容驱动（迭代项 B）

### 4.1 框架 = 可选模块清单，不是必填满表

#### 示例：PPT 商品培训（绿色 / 课件 3 / 课件 4 共性）

| 模块 | 业务填什么 | 不填 / 少填时 |
|------|------------|----------------|
| 商品介绍 | 名称、定位、规格等 | 弱化或「待确认」 |
| 核心卖点 | 1～N 条 | 有几条出几条 |
| 适宜人群 | 1～N 类 | 同上 |
| 联合用药话术 | 1～N 组 | **2 组 → 2 行，禁止第 3 空行** |
| 品种对比 | 可选 | 无则整节省略 |
| 注意事项 | 可选 | 无则省略或最短合规句（须审） |
| （临时）总结总表等 | 见 §4.3 | 扩展页规则 |

Word 结构原则：

- 模块标题固定、**整节可删**  
- 列表用「- / 方案 1 / 方案 2」，不要求凑满示例条数  
- 不出现「组件 ID / 坐标 / 时码」字段  

### 4.2 自适应硬规则（代理必须遵守）

```text
1. 业务提供 N 条联合用药 → 版式只生成 N 行；N=0 → 省略该页或该段。
2. 金样示例若为 3 行而业务只交 2 条 → 只出 2 行；禁止空白第三行；
   禁止为对齐金样输出「待补充」空壳行（除非业务明确要求占位）。
3. 未识别/未提供字段 → 空白可编辑槽位或「待确认」，不编造价格/功效/竞品。
4. 布局随内容：字号、合并单元格、分页由制作侧适配，不要求业务改版式。
```

对齐 lesson：`lesson-multi-theme-courseware-input-must-be-content-driven` 等。

### 4.3 临时新增模块（模板没有、业务要）

| 情况 | 策略 |
|------|------|
| 本 `style_pack` 页型库 / scene_recipe **已有**同类（如总结总表、四列表） | **优先复用**，只换审核文案 |
| 本模板无、其他 settled 模板有 | **参考他模板框架 + 本模板视觉 token**（色、字、圆角、页脚）新拼；标记 `business_extension` |
| 全库没有 | 先出文字初稿 + 线框/参考，业务确认后再生成；通过后可沉淀新页型 |

硬约束：

- 不得跨 style_pack 混皮肤  
- 扩展页不得伪称「像素级复刻金样」  
- 大改内容回初稿，不在终稿 PPT 里长期游离  

### 4.4 标准工作流（PPT / 课件）

```text
① 选模板（货架）
② 交资料（可残缺，可仅商品名）
③ 内容初稿 + 待确认项 + 素材缺口  → 业务确认
④ 确认后生成可编辑 PPTX（+ 可选视频）
```

绿色课件详细口令见：  
`production-library/templates/settled/product-courseware-green-v1/业务使用流程.md`

### 4.5 验收

- [ ] 用「2 条联合用药」样本跑任一商品 PPT 模板 → 成品无第 3 空行  
- [ ] 删掉「品种对比」整节 → 成片无该页或无空洞页  
- [ ] 业务新增「总结总表」→ 能复用同风格总结页型或明确扩展页流程  

---

## 5. 视频路径：旁白、出图与 WorkBuddy（迭代项 C）

### 5.1 责任切分

| 内容 | 业务 | WorkBuddy / 工厂 |
|------|------|------------------|
| 讲解旁白原文 | **提供已审定稿** | 原样朗读（TTS），不改医学结论 |
| 屏显短句 | 可写；可不写 | 可从旁白摘，供确认 |
| 包装 / Logo / 证据 | **授权原图** | 只入槽；无图则 gap |
| 教学插画（症状/机理等） | 可写画面意图 | 系列库匹配 / 候选；未签不默认量产 |
| 配音音色与语速 | 不选 | **模板 voice pack** 克隆 + v5-smooth 节奏 |
| 分镜与动画 | 不设计 | 场景配方装配 |
| 医学结论 | 审核稿为准 | **禁止编造** |

### 5.2 视频傻瓜闭环

```text
业务：货架看金样视频 → 填视频 Word（旁白按章）+ 授权图
    ↓
WorkBuddy：
  1. 锁定模板 + style_pack + voice_id
  2. 解析章节（可删可重排；有几章用几章）
  3. 意图 → scene_recipe → 分镜草稿
  4. 审核旁白 → 克隆 TTS → 字幕时间轴
  5. 图：授权包装 + 系列插画匹配 + 缺口清单
  6. 输出分镜预览 HTML（每章：原文 / 屏显 / 画面 / 缺口）
    ↓
业务：确认异常章、补包装、改文案
    ↓
WorkBuddy：渲染 MP4（+ 可选 PPTX）
    ↓
（可选）制作侧业务编辑器改图层 / 剪映做裁切节奏
```

### 5.3 业务禁止路径

- 用系统 `say` / 系统 Speech 出正式旁白  
- 无授权用 AI 仿包装、仿 Logo  
- 跳过「分镜预览」直接当终片发给门店（除非模板已是纯换壳且全自动门禁已过）  

### 5.4 验收

- [ ] 新主题旁白必须用**新文案**生成（证明不是复用原金样音轨）  
- [ ] ASR 抽检无乱读；语速无 1.5×+ 暴力压缩  
- [ ] 无包装时成片为槽位而非假包装  

---

## 6. 克隆语音包（迭代项 D）

### 6.1 为何必须

系统常规音色易「机器人」；培训成片要求与金样**讲解声一致、可复用**。  
正式路径：**从模板金样讲解轨截取干净口播 → 本地 Qwen3-TTS 零样本克隆 → 读新审核文案**。

### 6.2 现有资产

| voice_id | 用途 | 包目录 |
|----------|------|--------|
| `voice.reference-pharmacist-qwen-v1` | 健康科普 / 风热证线 | 见 `registries/voices.json` |
| `voice.sufuda-courseware-pharmacist-v1` | 商品课件批量 | `production-library/voices/sufuda-courseware-pharmacist-v1/` |

参考包结构（速福达）：

```text
voice-pack.json   # 引擎、prompt、pace（v5-smooth）、入口脚本
prompt.wav        # ~10–12s 干净连续口播
full-clean-mono-24k.wav  # 对照轨（可选）
```

引擎：本机 `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16`（见 `docs/local-open-source-reuse-audit.md`）。

### 6.3 语速 / 连读策略（随包交付）

| 规则 | 值 / 含义 |
|------|-----------|
| 生成粒度 | **语义段一次 TTS 连读**，禁止逐 cue 硬拼 |
| DEFAULT_TEMPO | ≈1.16 |
| MAX_TEMPO | ≤1.18；贴不上则延时间轴 |
| 禁止 | 逐句 atempo 暴力压、固定静音槽硬拼接 |
| 字幕 | 按字数比例重切，不硬贴旧参考窗 |
| 验收 | ASR 抽检 + 新文案生成证明 |

登记：`decision.semantic-block-voice-speed-gate`、`lesson.voice-continuous-segment-smooth`。

### 6.4 模板绑定契约（目标）

每个**含视频**的 settled 模板：

```json
"voice": {
  "voice_id": "voice.xxx",
  "pack_dir": "voice/",
  "engine": "Qwen3-TTS-local-clone",
  "pace_policy": "v5-smooth"
}
```

WorkBuddy：**voice_id 只从模板 manifest 读取**，禁止回退系统 TTS。

### 6.5 授权与开源注意

- 人声仅限**公司内部培训授权**范围；开源对外时须脱敏或换企业自有授权包。  
- 参考原声直接贴片仅用于复刻验证，须标注；**新主题必须用克隆生成**。

### 6.6 验收

- [ ] 视频类 settled 均有可用 voice pack 或明确继承的 voice_id  
- [ ] 换主题文案生成试听与金样「像同一讲解员」  
- [ ] 代理日志可追溯使用了哪个 `voice_id`  

---

## 7. 端到端业务路径（PPT + 视频共用）

```text
安装 / 打开
    ↓
【A】模板货架（关键页 + 金样）
    ↓
选中模板 → 框架 Word（模块可删、可空）
    ↓
业务填写 + 授权附件
    ↓
WorkBuddy：
  PPT → 内容初稿 + 待确认 + 缺口
  视频 → 分镜预览 + 试听(可选) + 缺口
    ↓
业务确认
    ↓
导出：可编辑 PPTX 和/或 MP4 → 05_交付物放这里/
    ↓
（可选）业务改 PPT 字图；制作侧编辑器 / 剪映返修
```

| 环节 | PPT | 视频 |
|------|-----|------|
| 预览 | 关键页 PNG | 关键帧 + 整片 MP4 |
| 填写 | 模块框架 Word | 章节旁白 Word |
| 自适应 | N 条 → N 行 | N 组 → N 镜 |
| 扩模块 | 同风格页型库 | 同 style_pack 的 scene_recipe |
| 声 | 一般无 | 模板 voice pack 克隆 |
| 图 | 授权包装 + 槽位 | 授权包装 + 系列插画 |
| 确认点 | 内容初稿 | 分镜预览 |

---

## 8. WorkBuddy 系统提示词（代理侧粘贴用）

> **生产全文（推荐直接打开粘贴）：** `docs/workbuddy-system-prompt.md`  
> 下列为行为约束摘要；冲突时以落盘全文为准。

```text
你是连锁药店培训内容工厂的本地代理。只使用 production-library/templates/settled 中已登记模板。

【业务可见】
- 帮用户选课型、打开/说明模板货架预览
- 指导填写空白 Word；强调：可删整节、有几条写几条
- 收集授权包装/Logo；无图则记入缺口，不伪造

【强制流程】
1. 先确认 template（中文名 → settled slug）
2. PPT：先输出内容初稿 + 待确认项 + 缺口，用户确认后再生成 PPTX
3. 视频：先输出分镜预览结构 + 缺口（+ 可选试听路径），确认后再渲染 MP4
4. 列表/联合用药：按实际条数生成；禁止空白凑行
5. 新模块：优先同 style_pack 页型；否则他模板框架 + 本模板视觉，并标 business_extension

【旁白与音色】
- 旁白 = 业务审核原文；默认不改写医学结论
- 音色 = 模板 manifest 的 voice_id / voice pack 本地克隆
- 禁止默认使用操作系统朗读音色
- 语速遵循 voice pack 的 v5-smooth（连读、tempo≤1.18）

【禁止】
- 编造功效、数据、竞品结论
- AI 仿造品牌包装/Logo
- 要求业务填写坐标、组件 ID、时码
- 把 validation 探索稿当正式模板

【输出目录】
交付/<主题中文名>_<日期>/
  初稿或分镜说明.md
  缺口清单.md
  终稿.pptx / 终稿.mp4（确认后）
```

---

## 9. WorkBuddy 口令卡（业务复制）

### 通用

> 我要用 **【课型中文名】**，主题是 **【病名或商品名】**。  
> Word 和授权图在附件。  
> 请先出 **初稿/分镜预览 + 待确认项 + 缺图清单**；  
> 我确认后再出 **可编辑 PPTX / 培训视频**。  
> 示例 Word 只作格式参考，医学与包装以我司审核稿为准。

### PPT 补充

> 联合用药我只写了 2 组，请按 2 行排版，不要空第三行。  
> 没有品种对比整节可删。若需要「总结总表」请按同风格总结页补一页并标扩展。

### 视频补充

> 旁白以 Word 审核稿为准，请用该模板的药师克隆声朗读。  
> 包装用附件图；没有的章节先占位并列入缺口。

---

## 10. 与现有仓库映射（避免重复造轮）

| 能力 | 现状 | 本方案动作 |
|------|------|------------|
| 金样与 Word | `templates/settled/*` | 补 `preview/`、`voice/`、manifest 字段 |
| 业务资料包 | `outputs/业务使用资料包/` | 升格为档 A 交付结构 |
| 货架雏形 | `gold-samples/index.html` | 升格/同步为业务模板货架 |
| 内容驱动 PPT | 绿色 `业务使用流程.md` + lessons | 全模板统一规则 + 代理提示词 |
| 克隆旁白 | `voices/*`、`generate_cloned_*.py` | 每视频模板绑定 pack |
| 画面编辑器 | 9000/9001/9010/9012 | 仅制作返修；写入「非默认路径」 |
| 脚本驱动组装 | `product-training-script-driven-assembly.md` | 视频分镜仍遵守四层复用 |

---

## 11. 持续迭代 backlog

### P0 · 能让业务「看懂并开填」（优先）

| ID | 项 | 验收 | 状态 |
|----|----|------|------|
| A1 | 六个 settled 模板收集/导出 cover + ≥3 key frames 到 `preview/` | 目录齐全 | **已完成** 2026-08-03 |
| A2 | 业务模板货架页（本地 HTML，可离线） | 选模板可达 Word 说明 | **已完成** 档 A `01_模板货架/index.html` |
| A3 | manifest 增加 `preview` 字段 | 查询脚本可读 | **已完成** + `business-catalog.json` |
| B1 | 统一「框架模块」说明写入各空白 Word 指引或一页说明 | 业务知可删节 | **已完成** `框架填写说明.md` |
| B2 | 代理提示词落盘 `docs/workbuddy-system-prompt.md` 或 skills | 可粘贴使用 | **已完成** |
| D1 | 文档声明：禁止默认系统 TTS | 本文 §6 | **本文已写** |

### P1 · 高质量自动交付

| ID | 项 | 验收 | 状态 |
|----|----|------|------|
| B3 | 联合用药/列表自适应回归样例（2 条 → 2 行） | 自动或半自动检查 | **已完成** `scripts/content_driven_rules.py` + `test_content_driven_rules.py` |
| B4 | 扩展页（总结总表）页型检索规则 | 有文档 + 一例 | 待做 |
| C1 | 视频分镜预览 HTML 标准输出格式 | 一主题一例 | **部分完成** MD 标准模板 + 示例（HTML 可视化可后补） |
| C2 | 缺口清单 schema（包装/插画/待确认字段） | 统一 CSV/MD | **已完成** `business-gap-list-v1` |
| D2 | 风热 / Q10 / 课件4 补齐 voice pack 与 manifest.voice | 换文案可克隆试听 | **部分完成**：manifest.voice 已绑；本地 pack 目录仍待补齐 prompt 资产 |
| D3 | WorkBuddy 强制读取 voice_id | 日志可查 | 待做 |

### P2 · 体验与开源

| ID | 项 | 验收 | 状态 |
|----|----|------|------|
| A4 | 可选 online_url 托管货架 | 外网可看脱敏预览 | 待做 |
| E1 | 一键打包脚本：生成档 A zip | 一条命令出业务包 | **已完成** `scripts/build_business_tier_a_package.py` |
| E2 | 开源授权说明（语音包/包装图边界） | LICENSE 或 NOTICE | 待做 |
| E3 | 业务编辑器一键启动写入制作手册（非业务默认） | 制作文档 | 待做 |

### 迭代记录

| 日期 | 变更 |
|------|------|
| 2026-08-03 | 初版：货架预览、内容驱动框架、视频/语音包、WorkBuddy 分层与 backlog |
| 2026-08-03 | **P0 落地（上市公司交付标准）**：六模板 `preview/` 真实金样帧；档 A 业务包 zip（货架+Word+口令+质量说明）；`workbuddy-system-prompt.md`；manifest.preview + 视频类 manifest.voice；刷新命令见下 |
| 2026-08-03 | **业务可上手**：每课型「本课型怎么填」；填写参考纠错（商品不再错挂风热样本）；初稿/缺口/分镜标准模板+示例；业务验收清单；内容驱动规则回归；一键 `scripts/refresh_business_delivery.py` |

**刷新业务包（制作侧 · 推荐一键）：**

```bash
python3 scripts/refresh_business_delivery.py
# → outputs/业务使用资料包/药店培训内容工厂-业务包.zip
```

---

## 12. 完成定义（方案整体 Done）

当且仅当：

1. 业务同事**不打开工程源码**，仅凭档 A + WorkBuddy，能选对模板并提交 Word；  
2. 同一模板换商品/病种，产出风格一致、**无空白凑行**、无假包装；  
3. 视频旁白为**模板克隆声 + 审核原文**，非系统机器人音色；  
4. 每条交付有可追溯：`template_id`、`style_pack_id`、`voice_id`、初稿确认记录。

---

## 13. 下一迭代建议开工顺序

1. ~~**A1 + A2**：货架与 preview~~ **已完成**  
2. ~~**B2**：WorkBuddy 系统提示落盘~~ **已完成**  
3. ~~**E1**：一键业务包~~ **已完成**  
4. **D2 收尾**：风热 / Q10 / 课件4 本地 `voice/` pack 目录与 prompt 资产（manifest.voice 已绑）  
5. **B3 + C1**：联合用药 2→2 行回归样例 + 视频分镜预览标准输出一例  
6. **D3**：代理日志强制记录 voice_id  

本文为**唯一业务傻瓜交付总案**；具体工程实现在对应 PR / `tasks/todo.md` 勾选推进，完成后回写 §11 状态列。
