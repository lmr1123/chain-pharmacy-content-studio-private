# 初始化资产库规划：主题 · 系列 · 来源 · 管理

> 状态：后勤规划（从属）；主线见 `decision.gold-sample-first` 与 `docs/project-brief.md` §1.1。  
> 本文只规范主题/系列/来源与外补；**禁止**将「先囤通用元件」当作项目主目标。

---

## 1. 结论先说

业务新增培训主题时，**不要新增一套固定模板**，也不要每条视频单独产一套素材。正确的管理单位是：

| 层级 | ID 形态 | 固定什么 | 随主题变什么 |
| --- | --- | --- | --- |
| 风格包 | `style_pack_id` | 母版、字体、色板、字幕、音色、运动语法、兼容子画风 | 几乎不变；一项目只能绑一个 |
| 场景配方 | `scene_recipe_id` | 内容意图 → 构图与动画契约 | 章节有无、顺序、是否续镜 |
| 组件 / 动效 | `component_id` / `effect_id` | 可参数化槽位与动效预设 | 文案、条目数、站位、时长 |
| **视觉系列** | **`series_id`** | 色板、材质、角色比例、构图槽、动画契约 | **系列成员**（器官/症状/商品…） |
| **业务主题** | **`theme_id`** | 无（主题是内容容器） | 审核脚本、授权包装、证据、章节结构 |
| 课程/项目 | `project_id` / `course_id` | 绑定一个 style_pack | 一次交付的成片与导出物 |

**一句话**：主题管「讲什么」；系列管「长什么样」；风格包管「整片像不像一家人」；外部来源只进参考层，自研/授权才进生产层。

---

## 2. 核心概念辨析（必须分清）

### 2.1 主题 Theme（业务内容单位）

**定义**：一门可交付的培训内容身份，通常对应「一个疾病知识点」或「一个商品培训」。

| 字段 | 说明 | 示例 |
| --- | --- | --- |
| `theme_id` | 稳定主题 ID | `theme.disease.wind-heat`、`theme.product.andrographolide-drop-pills` |
| `theme_kind` | 主题类型 | `disease` / `product` / `scenario` / `mixed` |
| `title_zh` | 业务可见名称 | 风热证、穿心莲内酯滴丸 |
| `approved_script_ref` | 审核脚本来源 | Word/内部课件路径或文档 ID |
| `authorized_asset_refs` | 授权包装/Logo/说明书/证据 | 公司资产路径或 DAM ID |
| `default_style_pack_id` | 默认风格（可覆盖但需合规） | 健康 → medical-tech；商品 → product-blue |
| `tags` | 检索标签 | 咽喉、呼吸系统、中成药 |

**主题不是**：

- 不是画风（画风在 series / style_pack）
- 不是场景顺序（顺序由脚本章节决定）
- 不是单张 PNG 的目录名（单图是 asset member）

**主题如何复用系列**：

```text
theme.disease.wind-heat
  └─ 使用 series: asset-series.mechanism.reference-medical-tech-v1
       └─ members: whole_body, larynx, pathogen_field, …
  └─ 使用 series: series.symptom.pharmacy-health-cartoon-v1
       └─ members: fever, cough, sore-throat, …

theme.product.q10
  └─ 可继续用同一 cartoon 症状系列（若风格包白名单允许）
  └─ 新增 series.product-packshot.authorized-v1 下的 Q10 包装成员
```

同一主题可以引用多个 series（机制 + 症状 + 草本 + 包装），但**必须全部兼容当前 `style_pack_id` 的 `allowed_asset_styles`**。

### 2.2 系列 Series（视觉一致性单位）

**定义**：共享同一套视觉令牌与动画契约的、可横向扩展的成员集合。系列回答「这些图是不是同一套画」。

| 字段 | 说明 | 示例 |
| --- | --- | --- |
| `series_id` | 稳定系列 ID | `asset-series.mechanism.reference-medical-tech-v1` |
| `series_style_id` | 系列画风令牌 ID | `medical-mechanism-cyan-volumetric-v1` |
| `style_pack_ids` | 可挂载的风格包（白名单） | medical-tech-v1 |
| `role_contracts` | 成员角色槽（全身/器官/介质…） | `whole_body_front` |
| `visual_tokens` | 色板、材质、线宽 | 见既有 `series.json` |
| `animation_contract` | 摇摆、呼吸、脉冲范围 | 与 effect 绑定 |
| `extension_gate` | 扩员门槛 | 先查库再补成员 |

**系列扩展规则**：

1. 先按 `style_pack_id + series_id + role_id` 查库。
2. 已有角色能表达新主题 → **只加成员**，不新建系列。
3. 画风/材质无法表达 → **先签 1 张代表图**，再建新 series。
4. 系列状态 `user-approved` **不自动继承**到新成员；成员各自走审核。

**系列不是**：

- 不是「风热证文件夹」（那是主题或成员命名）
- 不是「整条视频工程」
- 不是「外部素材网站分类页」

### 2.3 主题 vs 系列（对照）

| 维度 | 主题 Theme | 系列 Series |
| --- | --- | --- |
| 归属 | 业务/内容 | 设计/制作 |
| 变化频率 | 每上新课就新增 | 少而稳，跨课复用 |
| 主键 | `theme_id` | `series_id` |
| 主要产物 | 审核脚本、授权证据、分镜清单 | PNG/分层图、动效契约、提示词配方 |
| 业务是否填写 | 是（Word） | 否（系统匹配） |
| 失败表现 | 内容缺口、合规缺口 | 画风拼凑、角色不一致 |

错误示范：为「胃病培训」再复制一整套与风热几乎相同的画风资产但不归入系列 → 库膨胀且无法组合。  
正确示范：胃病主题复用 `mechanism` 系列，只补 `organ_torso=stomach` 等成员。

### 2.4 风格包 Style Pack

全片唯一视觉法律。控制母版 UI、字体、字幕、讲师身份、转场节奏，以及**允许进入的 series_style 白名单**。  
主题切换时 style_pack 通常不变；**禁止单镜头临时换未登记画风**。

### 2.5 场景配方 Scene Recipe

「内容意图 → 画面结构」的映射，与具体疾病/商品解耦。

- 意图示例：`symptom_overview`、`mechanism_explanation`、`product_hero`
- 业务脚本可省略、重复、重排意图
- 配方声明需要的 `role_id`，由系列提供成员填充

### 2.6 组件 Component / 动效 Effect

可装配的程序化单元（卡片、母版、药师口型、边框扫光等）。  
组件吃「槽位数据 + 系列成员图」；**组件本身尽量主题无关**。

### 2.7 课程 / 项目 Course · Project

一次生产任务：`theme` + `style_pack` + 脚本版本 + 导出物。  
可复用主题与系列，但渲染产物与 QA 记录挂在 project 上。

---

## 3. 来源分层：自研 · 授权 · 外部（管理核心）

所有资产必须登记 **来源层级** 与 **可进入生产的边界**。混用是画风拼凑与合规风险的主因。

### 3.1 来源类型枚举 `source_class`

| 值 | 含义 | 能否进生产 master | 典型内容 |
| --- | --- | --- | --- |
| `in_house_generated` | 本项目自研生成（AI/手绘/程序绘制）并完成签样 | 可以（通过审核后） | 症状卡通、机理人体、原创图标 |
| `in_house_authored` | 公司设计/制作直接出品 | 可以 | 品牌母版、企业数字人 |
| `company_authorized` | 公司持有授权的商业资产 | 可以（真包装/Logo/证据优先） | 商品包装、说明书图、检测报告图、Logo |
| `licensed_third_party` | 已采购且许可证覆盖本用途 | 可以（记录许可证与范围） | 正版图标包、已购 AE 包中重制后的自有导出 |
| `open_source_reusable` | 许可证明确允许且已审计 | 有条件（代码/方法优先；像素看条款） | SMART 署名矢量、MIT 引擎 |
| `external_reference_only` | 外部平台仅作风格/结构参考 | **禁止**像素进 master | 来画/万彩模板、光厂 MG、参考片截帧 |
| `poc_placeholder` | PoC 占位、无品牌示意 | **禁止**对外与批量生产 | 假包装、示意药盒 |
| `unknown` | 来源不清 | **禁止** | 网图、未记录提示词的历史文件 |

### 3.2 存放与引用分层

```text
A. 生产层（可渲染默认路径）
   assets/component-library/**
   production-library/registries/**
   → 仅 in_house_* / company_authorized / licensed_* / 已审计 open_source

B. 参考层（禁止默认装配）
   docs/references/** 或 assets/_reference/**（可选）
   poc/**/reference-analysis/**
   → external_reference_only、拆解笔记、节奏卡、对标截图

C. 候选层（签样前）
   assets/component-library/**/candidates/**
   → 未 approved 的自研候选；不得批量生产默认选中

D. 项目临时层
   out/**、tmp/**、poc/**/work/**
   → 不回写公共库；通过签样后才晋升
```

### 3.3 外部来源白名单（初始化参考，非生产库）

下列只用于 **结构拆解 / 运动语法 / 信息密度对标**，拆解结果写入文档，**像素与工程文件不进生产 master**。

| 来源 | 类型 | 学习什么 | 禁止什么 |
| --- | --- | --- | --- |
| 来画 医疗/慢病模板 | 成片工具 | 分镜粒度、业务拖拽路径、AI 配音字幕体验 | 直接套模板成片、混入公共人物 |
| 万彩动画大师 医疗健康 | 成片工具 | 病理路径动画、医疗色系、素材分类法 | 未授权导出素材入库 |
| 闪剪 / 剪映企业玩法 | 数字人营销 | 口播批量、品牌色板锁定思路 | 替代 MG 专业场景配方 |
| 魔珐等药企数字人培训 | 行业案例 | 改脚本重生、培训闭环 | 当作唯一视觉方案 |
| 光厂 / 包图 / 千图 医疗 MG | 素材市场 | 镜头运动、片头结构 | 未购许可证像素入库 |
| AE Medical Explainer Toolkit | 工具包 | 角色动作粒度、背景换色 | 未授权原件进生产 |
| Lottie Medical / Conditions packs | 微动效 | 图标呼吸/脉冲节奏 | 画风未适配直接混用 |
| Servier SMART / BioGDP / SciDraw | 医学矢量 | 解剖正确性、机制表达 | 风格未统一时硬贴进卡通片 |
| **Koboyo Icons**（https://koboyo.com/icons） | 手绘 SVG 图标源头 | 排版符号与小物件一致性（按需匹配获取） | 整库镜像/提交 SVG 包；替代场景插画；对外做成可选可下全库；成片热链官网 |
| 公司参考培训视频 | 内部样片 | 母版、节奏、章节语法 | 参考像素与未授权 Logo/原声外发 |

每次外部拆解应产出一张 **「拆解卡」**（见 §7），而不是下载一堆文件塞进 `assets/`。

### 3.4 自研与授权的优先级（装配时）

```text
真商品包装 / Logo / 说明书 / 检测证据
  → 仅 company_authorized（无授权则 asset_gap，禁止生成假品牌）

教学插画（症状、机理、人群、草本示意）
  → in_house_generated / in_house_authored，且绑定 series_id

图标 / 排版符号 / 微物件（箭头、分行点、勾叉、分隔线、简单医疗物件等）
  → **按需源头** [Koboyo Icons](https://koboyo.com/icons)（商用免费、无需署名）
  → Git 只提交：`assets/_intake/open_source/koboyo/{SOURCE.md,license.txt,manifest.json}`
  → 本机临时：`svg/`（gitignore）仅当次下载；禁止整库镜像/提交
  → 改色/栅格化后经 candidates → master；不替代多色场景系列插画
  → 序号 1–n 优先文本排版；Lottie 等需重绘或适配 series_style 后入库

代码与引擎
  → 见 docs/local-open-source-reuse-audit.md（与像素资产分轨管理）
```

### 3.5 元数据：每条资产必填来源块

建议在 `component.json` / 成员登记中统一：

```json
{
  "id": "asset.mechanism.wind-heat.larynx-v1",
  "series_id": "asset-series.mechanism.reference-medical-tech-v1",
  "role_ids": ["symptom_focus_front"],
  "theme_ids": ["theme.disease.wind-heat"],
  "style_pack_ids": ["style-pack.reference-medical-tech-v1"],
  "source": {
    "source_class": "in_house_generated",
    "method": "image-gen + manual cleanup",
    "prompt_ref": "prompts.md",
    "model_or_tool": "recorded-at-generation-time",
    "created_at": "2026-07-29",
    "license": "company-internal",
    "commercial_use": true,
    "attribution_required": false,
    "reference_inputs": [
      {
        "ref_id": "ref.structure.wind-heat-larynx",
        "source_class": "external_reference_only",
        "note": "仅语义与构图参考，像素未进入 master"
      }
    ]
  },
  "review": {
    "visual": "approved",
    "technical": "approved",
    "medical": "pending-pharmacist",
    "provenance": "approved"
  },
  "status": "selected"
}
```

**规则**：`reference_inputs` 可以指向外部参考，但 `source_class` 为 `external_reference_only` 的对象 **不得** 成为 `master` 文件路径。

### 3.6 外部获取 → 适配 → 入库（填充主题/系列的主路径）

此前规划强调「禁参考像素进 master」，容易被理解成「不从外部补库」。  
正确含义是：**外部必须作为补给源，但只能按缺口、按系列契约、按许可证进入**，而不是整站爬素材塞进主题目录。

#### 3.6.1 总原则

```text
脚本/主题  →  角色缺口清单  →  外部检索/采购/公司授权
                              ↓
                    暂存 staging（非生产）
                              ↓
              风格适配到 series（重绘/AI 重绘/改色/重导出）
                              ↓
              candidates 签样  →  四轨审核  →  master + 回写 series
```

| 原则 | 说明 |
| --- | --- |
| 缺口驱动 | 只为 `theme × recipe × role_id` 的空槽补货，禁止「先囤 1000 张再想用哪张」 |
| 系列优先 | 外部图是原料；入库身份必须是某 `series_id` 的成员 |
| 许可先行 | 无商用授权、用途不明的不下载进候选层 |
| 适配后入库 | 原样外图几乎不能直接 master；须贴合 visual_tokens / 构图槽 |
| 真品分流 | 包装/Logo/证据只走公司授权通道，不走素材网站「相似包装」 |

#### 3.6.2 三种外部补给通道（按资产类型）

| 通道 | 适用 | 典型源 | 入库 `source_class` | 适配要求 |
| --- | --- | --- | --- | --- |
| **A. 公司授权通道** | 真包装、Logo、说明书、检测/证据、竞品对标原图 | 采购/供应商包材、内部 DAM、门店主数据、法务授权库 | `company_authorized` | 抠图、多角度规范、透明底；**禁止 AI 伪造品牌包装** |
| **B. 可商用采购/开源通道** | 通用图标、器官线稿、环境、无品牌药盒示意、Lottie | 包图/千图/摄图（企业商用）、Envato、LottieFiles 商用包、Servier SMART、BioGDP、SciDraw | `licensed_third_party` 或 `open_source_reusable` | 统一线宽/色板/圆角；必要时矢量重绘后再挂 series |
| **C. 参考拆解 + 自研再生通道** | 症状人物、机理体积光、人群卡、片头运动语法 | 来画/万彩/光厂 MG/内部参考片/AE Toolkit | 参考=`external_reference_only`；成品=`in_house_generated` | **只学结构与参数**；用 series 提示词/配方重新生成或手绘 |

> 主题「内容」的外部获取主要是 **审核脚本与话术**（业务 Word），不是去网上下载一段文案当审核稿。

#### 3.6.3 缺口单（系统应输出的填充任务）

装配或 `plan_training_course` 在匹配失败时生成 `asset_gap_tasks[]`：

```json
{
  "gap_id": "gap.theme.disease.gastric.organ_torso.stomach",
  "theme_id": "theme.disease.gastric-discomfort",
  "style_pack_id": "style-pack.reference-medical-tech-v1",
  "series_id": "asset-series.mechanism.reference-medical-tech-v1",
  "role_id": "organ_torso",
  "semantic": "胃部不适/胃炎示意（教学友好，非血腥）",
  "preferred_channel": "C",
  "fallback_channel": "B",
  "search_queries": ["medical stomach organ flat illustration commercial", "胃 器官 扁平 医疗 可商用"],
  "must_match": {
    "series_style_id": "medical-mechanism-cyan-volumetric-v1",
    "transparent_subject": true,
    "no_brand_text": true
  },
  "license_requirement": "internal_training_commercial",
  "status": "open"
}
```

制作侧按 `preferred_channel` 执行；不得把 gap 直接用外链 URL 塞进渲染。

#### 3.6.4 暂存目录（外部原料与生产隔离）

```text
assets/_intake/                         # git 可忽略或限权；非生产
  company_authorized/<theme_or_sku>/    # 通道 A 原件
  licensed/<vendor>/<pack_id>/          # 通道 B 采购包 + license.txt
  open_source/<project>/<id>/           # 通道 B 开源 + 许可证副本
  reference_only/<platform>/<ref_id>/   # 通道 C 参考；永不晋升 master

assets/component-library/<category>/
  <series>/candidates/                  # 适配后的候选
  <member>/master/                      # 仅审核通过
```

`_intake` 中的文件 **不能** 被 `query_production_library` 默认匹配。

#### 3.6.5 适配闸门（外图 → 系列成员的必过条件）

任选通道 B/C 的像素，晋升 `candidates` 前必须满足：

1. **风格**：色相/材质/线宽落在 `series.json` 的 `visual_tokens` / `material_contract`  
2. **构图**：主体在 `composition_contract` 安全区；透明底或可抠  
3. **语义**：角色与 `role_id` 一致；50% 缩略可辨  
4. **清洁**：无水印、无外站 Logo、无不可用字体商标、无参考片截图像素  
5. **许可**：`license.txt` 或授权编号；用途含「企业内部培训 / 商用课件」  
6. **元数据**：完整 `source` 块 + `reference_inputs`（若从参考再生）  
7. **医学**：器官/症状表达不过度写实血腥；争议项标 `medical: pending`

适配手段（按成本）：

| 手段 | 何时用 |
| --- | --- |
| 改色/描边/统一投影（设计工具） | 本就接近 series 的矢量/扁平图标 |
| 程序化重导出（Lottie → 透明序列/静态关键帧） | 微动效角色 |
| AI 图生图 / 提示词再生（锁定 series 配方） | 症状人物、机理体积、人群场景 |
| 手绘/矢量重绘 | 高频复用图标、品牌敏感图形 |
| 放弃外图，纯自研 | 外图怎么改都不贴 series，或许可不清 |

#### 3.6.6 按角色类型的默认外部策略

| 角色 / 资产 | 首选通道 | 外部源示例 | 禁止 |
| --- | --- | --- | --- |
| 真包装 / Logo / 证据 | A | 公司 DAM、供应商包材 PDF | 电商盗图、AI 仿包装 |
| 症状卡通人物 | C→自研 | 内部参考片构图；来画/万彩只学分镜 | 直接下载卡通病人当 master |
| 机制人体/器官 | C 或 B | SMART/BioGDP 对解剖；series 配方再生 | 把科研写实图硬贴进卡通片 |
| 草本/药材 | B 或 C | 写实植物商用库；自研清洁背景 | 带卖家水印的网图 |
| 建议/禁忌图标 | B | 商用 icon 包、Lottie medical | 未改色混多套 icon 风 |
| 人群/办公场景 | C→自研 | 扁平插画包作构图参考 | 照片风混进扁平系列 |
| 片头/转场运动 | C | 光厂/AE MG 拆参数 → 自有 effect | 整段 AE 工程当生产依赖 |
| 数字人音色 | 授权服务或自有克隆 | 已授权企业音色 | 未授权仿名人声 |

#### 3.6.7 主题内容（非像素）的外部/内部获取

| 内容 | 来源 | 入库位置 |
| --- | --- | --- |
| 审核旁白/话术 | 药师+合规审核稿；业务 Word | theme 的 `approved_script_refs` |
| 卖点/联用/对标表 | 商品培训部 + 合规 | 脚本或 courseware JSON 槽位 |
| 疾病定义/机制表述 | 内部医学审核，可参考指南但不自动爬网 | 脚本；插图另走 series |
| 竞品信息 | 合法公开说明书/公司对标表 | 槽位 + 授权策略 |

**主题可快速登记；主题下的图必须走缺口单，不能「登记 theme 时顺手下 50 张网图」。**

#### 3.6.8 工具化落地（建议实现，非一次性人工）

| 能力 | 作用 |
| --- | --- |
| `plan` 输出 `asset_gap_tasks` | 自动列缺角色与 search_queries |
| `scripts/query_production_library.py --gaps`（可后续加） | 汇总 open gaps |
| 采购清单导出 CSV | 给设计/采购：gap_id、语义、系列、渠道、预算 |
| 候选导入校验 | 缺 `source`/许可证则拒绝登记 approved |
| 公司授权投喂入口 | 业务 Word 附件或 DAM ID → 通道 A |

外部 **搜索** 可用：素材站站内搜、SMART/BioGDP、已购 AE/Lottie 库；**不**建议无授权批量爬虫镜像整站。

#### 3.6.9 与「初始化资产库」的关系

- **冷启动**：通道 C 拆 6 张卡 + 通道 B 采 1 套医疗图标/器官矢量 + 通道 A 收齐现有 SKU 包装。  
- **扩主题**：先 theme 元数据 → plan 出 gap → 按 3.6 补成员。  
- **扩系列**：仅当连续多个 gap 无法被现有 series 适配时，才新开 series（代表图签样）。

---

## 4. 管理对象总表（ID 与注册位置）

| 对象 | ID 前缀建议 | 注册位置 | 负责人视角 |
| --- | --- | --- | --- |
| 风格包 | `style-pack.*` | `production-library/registries/styles.json` | 设计系统 |
| 模板框架 | `template.*` | `registries/templates.json` | 产品/制作 |
| 场景配方 | `scene-recipe.*` | `registries/scene-recipes.json` | 制作/分镜 |
| 组件 | `component.*` | `registries/components.json` | 工程 |
| 动效 | `effect.*` | `registries/effects.json` | 工程 |
| 音色 | `voice.*` | `registries/voices.json` | 声音 |
| **视觉系列** | `asset-series.*` 或 `series.*` | 各类 `assets/**/registry.json` + 可汇总 | 设计+工程 |
| **业务主题** | `theme.*` | `production-library/registries/themes.json`（已建骨架） | 业务+内容 |
| 单资产成员 | `asset.*` / `symptom.*` 等 | 系列 members + 分类 registry | 设计 |
| 外部参考卡 | `ref.*` | 建议 `docs/references/catalog.md` 或 `registries/references.json` | 制作研究 |
| 课程项目 | `project.*` / `course.*` | 装配 JSON / 输出索引 | 生产运营 |

查询入口保持：`production-library/catalog.json` + `scripts/query_production_library.py`。  
规划落地后应把 `themes`、`references` 登记进 catalog 的 `registries` / `entrypoints`。

---

## 5. 状态机（对象通用，审核分轨）

### 5.1 生命周期状态

| 状态 | 含义 | 可被自动装配 |
| --- | --- | --- |
| `candidate` | 候选，待风格/内容签样 | 否 |
| `selected` | 已选母版方向，未完成生产验收 | 仅 PoC / 预览 |
| `technical-qa-passed` | 技术 QA 通过 | 预览可；批量需业务/视觉策略 |
| `user-approved` | 用户视觉确认 | 内部分发可 |
| `production-validated` | 可默认进入批量生产 | **是** |
| `deprecated` | 保留引用，不进新项目 | 否 |
| `blocked` | 来源/合规/医学未过 | 否 |

### 5.2 四轨审核（不可互相替代）

| 轨道 | 管什么 | 谁签 |
| --- | --- | --- |
| `provenance` | 来源层级、许可证、是否含参考像素 | 制作/法务策略 |
| `visual` | 画风、系列一致性、可读性 | 用户/设计签样 |
| `technical` | 透明通道、锚点、时长、渲染 | 工程 QA |
| `medical` / `compliance` | 医学表述、药学、广告法、授权证据 | 药师/法务 |

系列 `user-approved` ≠ 成员四轨全过。  
主题脚本「已审核」≠ 画面医学图示已审核。

---

## 6. 初始化资产蓝图（Seed）

### 6.1 风格包种子（先 2+1，勿一次铺 10 套）

| style_pack_id | 用途 | 当前状态（以注册表为准） | 种子策略 |
| --- | --- | --- | --- |
| `style-pack.reference-medical-tech-v1` | 健康/疾病科普视频 | production-validated | 锁为疾病线默认 |
| `style-pack.reference-product-blue-v1` | 商品培训视频 | selected / 待视觉签样 | 签样后升生产 |
| `style-pack.dashenlin-courseware-green-v1` | 商品课件 PPTX/PDF | technical-qa / user-approved 课件线 | 与视频线分轨，不混母版 |

### 6.2 主题种子（业务内容，不是画风）

| theme_id | kind | 说明 | 默认风格 | 关联系列（规划） |
| --- | --- | --- | --- | --- |
| `theme.disease.wind-heat` | disease | 已有参考复刻基线 | medical-tech | mechanism-cyan、symptom-cartoon、herb、advice-icons |
| `theme.product.honeysuckle-dew` | product | **已拆解复刻**绿色 5 页课件 + 品牌升级签样 | courseware-green | packshot-authorized；封面/介绍/联用/对标/注意 |
| `theme.product.andrographolide-drop-pills` | product | 18 页疾病+商品场景课件真实样本 | courseware-green / product-blue（视频） | packshot-authorized、症状/机制按脚本 |
| `theme.product.coenzyme-q10` | product | 商品培训脚本样例 | product-blue | packshot、audience、efficacy 角色 |
| `theme.disease.gastric-*` | disease | 胃肠线扩展种子 | medical-tech | 复用 mechanism 系列补胃/肠成员 |
| `theme.disease.metabolic-cardio-*` | disease | 心代谢扩展种子 | medical-tech / product-blue | 按课程类型绑定 |

> 主题 ID 稳定后，脚本与授权图可版本化（`script_v`、`asset_bundle_v`），主题 ID 本身不随小改文案而变。

### 6.3 视觉系列种子（P0 必须先立契约）

| series_id（建议） | 覆盖角色 | 优先挂主题 | 来源策略 |
| --- | --- | --- | --- |
| `asset-series.mechanism.reference-medical-tech-v1` | 全身/器官/症状聚焦/剖面/病邪/路径 | 风热 → 胃肠/呼吸扩展 | 自研；**已有** |
| `series.symptom.pharmacy-health-cartoon-v1` | 人物症状、局部特写、符号 | 多疾病共享 | 自研；整理现有 symptoms/* |
| `series.herb.botanical-clean-v1` | 草本单株/药食 | 调理、成分 | 自研；写实草本与卡通分系列 |
| `series.medication.generic-packshot-v1` | 无品牌剂型示意 | 仅 PoC | `poc_placeholder`，真品必须授权系列 |
| `series.medication.company-authorized-v1` | 真包装多角度 | 各商品主题 | **仅 company_authorized** |
| `series.presenter.pharmacist-cartoon-v1` | 待机/讲/指/换位/口型层 | 全视频线 | 自研；身份锁定 |
| `series.audience.lifestyle-flat-v1` | 人群卡、场景人物 | 商品适宜人群 | 自研；扁平角色语法 |
| `series.icon.advice-safety-v1` | 建议/禁忌/步骤图标 | 注意与总结 | 自研或 licensed 重绘 |
| `series.ui.master-chrome-v1` | 栏目签、导航、声明（若与组件分离） | 全片 | in_house_authored |

**P1（第二批）**：`series.env.clinic-or-home-v1`、Lottie 适配后的 `series.motion-icon.medical-micro-v1`（必须重绘或改色以贴 series_style）。

### 6.4 场景配方种子（按意图，不按主题复制）

疾病线意图：开场、症状、机制、原则、草本、用药建议、禁忌、总结、片尾。  
商品线意图：需求教育、商品亮相、总览、功效证据、特点、人群、联用、总结。

每意图 **1 个主配方 + 可选 1 个变体构图** 即可启动；信息过载用 `continue_same_recipe` 续镜，不缩字号。

### 6.5 组件 / 动效种子（P0）

- 母版、字幕、讲师状态机  
- 症状板、证据卡、总结矩阵、建议列表  
- 包装主视觉槽、Logo 槽、内部培训声明  
- 机制关系图 / 路径（与 mechanism 系列绑定）  
- 背景电流、边框描边、单焦点强调（effect）

### 6.6 外部参考拆解种子（只进参考层）

建议首批拆 **6 张拆解卡**（每卡 1 页结构即可）：

1. 来画：慢病/流感科普模板 — 分镜粒度与章节时长  
2. 万彩：感冒/鼻塞机理路径 — 路径动画与标注密度  
3. 光厂或 AE：医疗 Explainer 片头 — 片头信息层级  
4. Lottie：症状微动效 — 脉冲/呼吸参数区间  
5. SMART：器官矢量 — 解剖可读性对照（非画风）  
6. 公司参考片：现有风热/商品片 — 已部分完成，补全「意图→配方」对照表  

---

## 7. 外部拆解卡模板（便于管理，禁止像素入库）

每张卡建议独立 Markdown：`docs/references/cards/<ref_id>.md`

```markdown
# ref.<domain>.<name>

- source_class: external_reference_only
- platform: 来画 | 万彩 | 光厂 | Lottie | SMART | 内部参考片 | …
- url_or_path: …
- license_note: 未采购/仅观摩/已购（若已购另开 licensed 记录）
- studied_at: YYYY-MM-DD

## 学到什么（可执行）
- 叙事意图切分：…
- 单镜信息密度：…
- 动效语法：…
- 字数与留白：…

## 映射到本库
- 可能影响的 scene_recipe_id: …
- 可能影响的 effect 参数: …
- 不映射的原因（若无）: …

## 明确不做什么
- 不复制角色形象 / 不下载像素进 assets/component-library
- 不把外部模板 ID 写进生产装配默认路径
```

---

## 8. 目录与命名约定（管理友好）

### 8.1 推荐目录心智

```text
production-library/
  registries/
    styles.json
    templates.json
    scene-recipes.json
    components.json
    effects.json
    voices.json
    themes.json          # 规划新增：业务主题
    references.json      # 规划新增：外部/内部参考索引（无像素）
    decisions.json
    lessons.json
  examples/              # 装配示例（按 theme 或 project）

assets/component-library/
  README.md
  <category>/            # symptoms | mechanisms | herbs | medications | presenters | …
    registry.json        # 成员索引
    <series-folder>/     # series.json + asset-template.json + README
    <member-or-legacy>/  # master | transparent | candidates | prompts

docs/
  seed-asset-library-bootstrap.md   # 本文
  references/
    cards/                          # 拆解卡
    catalog.md                      # 可选：人类可读目录

assets/_reference/                  # 可选：确需落盘的参考图，gitignore 或明确非生产
```

### 8.2 命名

| 对象 | 模式 |
| --- | --- |
| 主题 | `theme.<kind>.<slug>` |
| 系列 | `asset-series.<domain>.<style-slug>-vN` 或已有 `series.<domain>.…` |
| 成员 | `asset.<domain>.<theme-or-concept>.<role>-vN` |
| 参考 | `ref.<platform-or-domain>.<slug>` |
| 禁止 | 用商品名当 series_id；用「最终版」「新」当唯一区分；主题目录下堆无 series 的散图 |

历史目录（如 `symptoms/fever/`）可保留，但登记时必须补 `series_id` 与 `source` 块，逐步收敛。

---

## 9. 业务新增主题的标准作业（傻瓜路径）

```text
1. 业务：复制 Word → 填审核文案与授权附件 → 提交
2. 系统：theme_id 已有则复用；否则创建 theme 草稿（仅元数据）
3. 系统：锁定 style_pack_id（健康/商品默认）
4. 系统：章节 → intent → scene_recipe（低置信进确认队列）
5. 系统：按 recipe.role_ids 在兼容 series 中匹配成员
6. 缺口：
   - 缺授权包装/证据 → asset_gap（业务补授权）
   - 缺系列成员但 series 可表达 → 生成候选成员任务（制作签样）
   - series 无法表达 → 新系列代表图任务（升级决策，非默认）
7. 业务：只确认异常项与关键图
8. 渲染导出；通过后成员/theme 元数据回写公共库
```

业务 **不** 填写：`component_id`、提示词、坐标、时码、series 技术字段。

---

## 10. 防拼凑硬约束（清单）

1. 一项目一个 `style_pack_id`。  
2. 装配只用 `production-validated`（或策略允许的 `user-approved`）成员。  
3. 成员必须带 `series_id`；无系列散图不得默认匹配。  
4. `external_reference_only` 与 `poc_placeholder` 不得进入默认 master。  
5. 真包装/Logo 无 `company_authorized` 则卡死，不生成假品牌。  
6. 跨 series 混用必须双方都在风格包 `allowed_asset_styles` 内，并用同一卡片/色罩/圆角统一。  
7. 每镜最多一个主运动焦点。  
8. 新主题优先扩成员，禁止「复制工程改名」。  
9. 参考片像素禁止进生产资产（catalog 根策略）。  
10. 医学结论以审核脚本为准；插图通过 ≠ 话术通过。

---

## 11. 落地任务拆分（文档之后）

| 序号 | 任务 | 产出 | 验证 |
| --- | --- | --- | --- |
| 1 | 新增 `themes.json` 骨架，登记风热、金银花露、穿心莲、Q10 等主题元数据 | 注册表 | query 可列出 theme（**已完成 2026-07-30**；含金银花露课件复刻沉淀） |
| 2 | 统一 symptoms/herbs 等到 series 契约（可先一个 series.json） | series + 回填 series_id | 无孤儿生产图 |
| 3 | 新增 `references.json` + 6 张拆解卡壳 | docs/references | 无像素进 library |
| 4 | 资产 `source` 块字段进 component 模板 | asset-template 更新 | 新成员缺 source 则校验失败 |
| 5 | catalog 增加 themes/references 入口 | catalog.json | 文档与脚本入口一致 |
| 6 | 胃肠/心代谢 series 成员清单（只列角色，先不产图） | asset-template 填空 | 制作可按表开工 |
| 7 | 外部填充流水线：`asset_gap_tasks` schema + `_intake` 分通道目录 + 采购/授权清单模板 | 协议与模板 | 新主题可导出缺口并按 A/B/C 补货（§3.6 已写方案） |
| 8 | 试点：通道 B 商用图标 + 通道 C 参考再生 + 通道 A 真包装 各 1 条 | candidates + source | 外源可填充且不污染 master |

本文只做规划，不修改注册表状态字段；**未签样对象不得因本文写成 production-validated**。

---

## 12. 与现有文档的关系

| 文档 | 关系 |
| --- | --- |
| `docs/product-training-script-driven-assembly.md` | 业务操作与四层复用；本文细化「主题/系列/来源」管理 |
| `production-library/script-assembly-protocol.md` | 生产链路协议；本文补管理模型与种子清单 |
| `assets/component-library/README.md` | 目录与签样状态；本文补 theme 与 source_class |
| `docs/local-open-source-reuse-audit.md` | 代码/引擎许可；与像素 `source_class` 分轨、互补 |
| `docs/final-recommendation-and-expected-effect.md` | 产品形态；本文是资产侧启动蓝图 |
| `docs/reference-style-component-system.md` | 组件与角色状态机；挂在 style/component 层 |

---

## 13. 一页速查

```text
讲什么？     → theme_id          （业务 Word）
整片什么风？ → style_pack_id     （一项目锁定）
怎么排版动？ → scene_recipe_id   （意图映射）
图像不像一套？→ series_id        （视觉契约 + 成员）
缺什么图？   → asset_gap_tasks   （缺口驱动外补）
图从哪补？   → 通道 A 授权 / B 采购开源 / C 参考再生
图从哪来？   → source_class      （自研/授权/参考分层）
能不能用？   → status × 四轨审核 （来源·视觉·技术·医学）
```

**初始化成功标准**：业务只交脚本与授权材料，系统在同一 style_pack 下用系列成员拼出新主题预览；缺口可列举并按 A/B/C 通道外补；库中可分清主题、系列、自研与外部参考，且外部参考与未适配原件永不污染生产 master。
