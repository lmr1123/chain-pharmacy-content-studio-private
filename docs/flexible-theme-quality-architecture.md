# 产品方案：灵活主题 × 交付质量（style · page_type · script）

**状态：** 正式产品方案（2026-08-07）  
**对标：** [open-kimi-ppt-skill](https://github.com/Binaryify/open-kimi-ppt-skill) 的 design system + 自由内容 + 质检思路  
**约束：** 服从 `AGENTS.md` 金样优先、审核文案锁定、无授权不仿包装  

### 0. 反模式（禁止再当「执行方案」）

| 反模式 | 正路径 |
|--------|--------|
| 把内容**一对一对进**金银花露绿系 5 页固定槽（cover / overview / combo / benchmark / precautions） | 内容脚本 → **页型池展开**（N 卡自适应）→ style token 套皮 |
| 用 `build-product-courseware*.mjs` 换 JSON 当「架构首跑」 | 用 `scripts/assemble_product_training_pptx.py` |
| 理想页型写在 plan 里却「折叠进 overview」交差 | 每节独立 `page_type` 成页 |

**反例归档：**  
- `validation/courseware/fuler-maikenli-lycopene-v1/archive-shell-fill-v1/`（绿壳填槽）  
- `validation/courseware/fuler-maikenli-lycopene-v1/archive-skeleton-v2/`（页型展开但 **无图** 色块字卡 — 用户判定等同 AI 直出）

**本 SKU 质量正例（图文并茂 · 已签样）：**  
`templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/`  
→ 校验副本：`validation/courseware/fuler-maikenli-lycopene-v1/福尔麦金利番茄红素_商品培训课件4_金样_可编辑_v2.pptx`

**硬门槛：** 培训交付必须有 **页型插画/场景图 + 金样级排版**；仅 style token 画圆角字卡 **不算交付**。

---

## 1. 问题与目标

| 要解决 | 不要做成 |
|--------|----------|
| 换商品/病种不必重做整套视觉 | 一份固定 20 页大纲绑死所有主题 |
| 内容结构可变（3 卡/4 卡/拆页） | 业务按固定页码填空 |
| 观感与培训可用度可验收 | 抽象框架重画冒充金样、或无限自由发挥发飘 |
| 药学表述可控 | AI 扩写功效/剂量/卖点 |

**目标一句话：**  
**视觉风格独立、页型排版独立、内容脚本独立；输入内容 → 脚本 → 匹配页型 → 匹配风格 → 质检 → 交付。**

---

## 2. 三层资产模型

```text
┌─────────────────────────────────────────────────────────────┐
│  C. 内容脚本 content / script                                 │
│     审核文案、数据、话术、图槽说明、待确认项                   │
│     换「福尔麦金利 / 感冒 / 任意 SKU」只动这一层               │
└───────────────────────────┬─────────────────────────────────┘
                            │ 映射（条数自适应）
┌───────────────────────────▼─────────────────────────────────┐
│  B. 页型 page_type（排版骨架）                                │
│     联合用药表、功效 N 卡、总结矩阵、科普定义页…              │
│     属于「课型家族 family」的页型池，须签样后注册               │
└───────────────────────────┬─────────────────────────────────┘
                            │ 套皮
┌───────────────────────────▼─────────────────────────────────┐
│  A. 视觉风格 style_pack                                      │
│     色板、字体、阴影、底、组件气质（类 open-kimi design.md）  │
│     点名使用；未点名则用家族默认，禁止裸奔混风                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 命名澄清

| 口语里的「主题」 | 本方案用语 | 例子 |
|------------------|------------|------|
| 讲什么商品/病 | **内容主题** / script | 福尔麦金利番茄红素 |
| 长什么样 | **style_pack** | cream-red / dashenlin-green |
| 一页怎么排 | **page_type** | combination_guidance |
| 整课叙事族 | **family** | product-training / health-edu |

---

## 3. 课型家族（family）与页型池

### 3.1 `product-training`（商品培训）

| page_type | 用途 | 内容槽 |
|-----------|------|--------|
| `courseware_cover` | 封面 | 品名、组织、角标 |
| `hook_intro` | 导语/需求钩子 | 痛点、数据、引入本品 |
| `benefit_cards` | 核心功效 N 卡 | title + body × N（2–4，超出拆页） |
| `feature_cards` | 产品特点 N 卡 | 同上；可选隐藏「大品牌」 |
| `audience_list` | 适宜人群 | 条目列表 |
| `combination_guidance` | 联合用药 + 话术 | 场景 / 联合品 / 话术 × M |
| `summary_matrix` | 总结表 | 功效·特点·人群·联合 |
| `product_overview` | 压缩总览（兼容绿系 5 页壳） | 多 section 合并 |
| `precautions` | 注意事项 | 条目 + 插图槽 |

**当前生产可用（绿系壳已实现）：**  
`courseware_cover` · `product_overview` · `combination_guidance` · `product_benchmark` · `precautions`  

**扩展中（方案已登记，生成器逐步补齐）：**  
`hook_intro` · `benefit_cards` · `feature_cards` · `audience_list` · `summary_matrix`

### 3.2 `health-edu`（成分/健康科普）

| page_type | 用途 |
|-----------|------|
| `cover` / `toc` / `chapter` | 封面、目录、章节扉页 |
| `two_card_media` / `list_media` / `three_process` … | 见康爱森金样 `page-types.md` |

金样真源：原片 OOXML 级归档（非框架重画）。  
路径：`production-library/validation/courseware/kangaisen-lycopene-health-edu-v1/`

### 3.3 `disease-scenario`（疾病科普视频/课件）

沿用风热壳 + 段 recipe + 主题包（既有主线，本文不重复展开）。

---

## 4. 视觉风格（style_pack）

| style_pack_id | 来源/气质 | 默认 family |
|---------------|-----------|-------------|
| `style-pack.dashenlin-courseware-green-v1` | 大参林绿 · 已签样 5 页商品课 | product-training |
| `style-pack.courseware-4-silk-yellow-red-v1` | 课件4 丝黄红 · 视频+PPT 金样 | product-training |
| `style-pack.lycopene-health-edu-cream-red-v1` | 康爱森原片实测 · 米白番茄红 | health-edu |
| `style-pack.reference-medical-tech-v1` | 深色医疗科技 | disease-scenario |

规则：

1. **一点名一套**，禁止同课混用未登记风格。  
2. 新风格须从金样/原片**实测**写入 design 规格（色/字号/阴影），再注册。  
3. style 与 page_type **正交**：同一联合用药页可套绿或红。

---

## 5. 端到端流水线（强制顺序）

```text
① 输入内容
   大纲 / 通用 Word / 聊天要点 / 图片槽
        ↓
② 生成内容脚本（script）
   章节、要点、旁白候选、待确认、素材缺口
   content_lock = pending | business-approved
        ↓
   ★ 业务/药师确认（未确认不出正式 PPTX）
        ↓
③ 选择 family → 匹配 page_type 序列
   有几条写几条；empty_cards=forbidden；过密拆页
        ↓
④ 选择 style_pack（点名或家族默认）
        ↓
⑤ 组装中间稿（content-model / deck）
        ↓
⑥ 质检闸门
   结构：空卡、溢出风险、页边距
   合规：无擅自扩写功效；包装仅授权槽
   视觉：整页导出图检查（对齐 open-kimi QA 方向）
        ↓
⑦ 交付
   可编辑 PPTX（主）+ 可选 Remotion/交互/视频
```

与业务四步对齐（`business-pptx-courseware-word-input-contract.md`）：

1. 先选模板（family + style）  
2. 再交资料  
3. 先出内容初稿  
4. 确认后再生成 PPTX  

---

## 6. 质量闸门清单

| # | 闸门 | 失败动作 |
|---|------|----------|
| G0 | 已选 family + style | 停止，请点名或给默认 |
| G1 | 内容初稿已确认 | 仅允许「草稿水印」预览，不写 settled |
| G2 | 医学/功效未超审核稿 | 回脚本层删补写 |
| G3 | 页型均在注册表 | 未知结构 → 新页型候选，不静默硬套（操作：`docs/page-type-growth-channel.md`） |
| G4 | 无空卡、可读字号 | 拆页或减字 |
| G5 | 包装/Logo 槽位合法 | 灰槽+「待接入」，不伪造品牌包装 |
| G6 | 视觉抽检通过 | 修页后复检 |

---

## 7. 与 open-kimi 的关系

| 借鉴 | 本仓库落点 |
|------|------------|
| design system 不绑内容 | style_pack + design 规格文档 |
| 中间层好改 | content-model / deck JSON |
| 导出前视觉质检 | validation QA 帧 + 后续 overview 拼图 |
| 点名主题才稳 | 点名 style_pack；禁止裸奔 |

**不**把非官方逆向包作为药店主链路唯一引擎；可作旁路导出/编辑 POC。主链路仍是 production-library 金样 + 生成器。

---

## 8. 实现入口（正路径）

| 资产 | 路径 |
|------|------|
| 页型注册表 | `production-library/page-types/product-training/registry.json` |
| style tokens | `production-library/styles/<style>/tokens.json` |
| 组装引擎 | `scripts/assemble_product_training_pptx.py` |
| 麦金利脚本 | `…/fuler-maikenli-lycopene-v1/script.structured.json` |
| L2 内容入口 | `docs/product-training-script-content-entry.md` · `scripts/draft_product_training_script.py` |
| 展开页表 | `…/expanded-page-plan.v2.json` |
| 成片 v2 | `…/福尔麦金利_商品培训_引擎组装_v2.pptx` |

```bash
python3 scripts/assemble_product_training_pptx.py \
  --script production-library/validation/courseware/fuler-maikenli-lycopene-v1/script.structured.json \
  --style production-library/styles/dashenlin-courseware-green-v1/tokens.json \
  --out production-library/validation/courseware/fuler-maikenli-lycopene-v1/福尔麦金利_商品培训_引擎组装_v2.pptx \
  --plan-out production-library/validation/courseware/fuler-maikenli-lycopene-v1/expanded-page-plan.v2.json
```

**麦金利 v2 页序（由脚本展开，非 5 页硬编码）：**  
cover → hook_intro → benefit_cards(3) → feature_cards(3，大品牌 hidden) → audience_list(4) → combination(3) → summary_matrix → precautions  

---

## 9. 演进路线

| 阶段 | 内容 |
|------|------|
| **P0** | 方案入库；**真引擎** + 麦金利 8 页 v2；v1 填槽归档为反例 |
| **P1** | 观感向绿系金样靠拢（字号/chrome/联合表原生组件）；overview QA 拼图 |
| **P2** | cream-red 等第二 style 可热切换；WorkBuddy「贴大纲 → 引擎组装」 |
| **P3** | 同一 structured script → Remotion/交互 |

---

## 10. 相关文档

- 输入契约：`production-library/business-pptx-courseware-word-input-contract.md`  
- 推进原则：`docs/project-brief.md` §1.1  
- 绿系签样：`production-library/templates/settled/product-courseware-green-v1/`  
- 课件4 金样：`production-library/templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/`  
- 科普金样：`production-library/validation/courseware/kangaisen-lycopene-health-edu-v1/`  
- 视频段扩展：`docs/video-segment-extension-model.md`  
