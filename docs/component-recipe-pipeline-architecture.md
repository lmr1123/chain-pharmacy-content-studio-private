# 构件化课件流水线方案（component + recipe + 布局规则 + 生长闸门）

**状态：** 执行方案（2026-08-07 用户拍板：直接按中期+长期路线，交下一模型执行）
**前置阅读：** `AGENTS.md`、`docs/handover-user-intent-2026-08-07.md`、`docs/flexible-theme-quality-architecture.md`
**约束：** 金样优先、审核文案锁定、无授权不仿包装、settled 纪律（均不变）

---

## 0. 用户意图（先对齐，再动手）

> 不是交付麦金利课件本身（它只是验证料），也不是引入 open-kimi（已评估否决）。
> **真正目标：项目具备「任意业务大纲进、稳定金样级课件出」的生成能力。**
> 现实约束：业务不可能按金样的形状提供内容；也不可能预先穷尽所有板式和金样。
> 要解的矛盾：质量锚定（金样）带来的刚性 vs 内容千变万化需要的柔性。

### 已否决的三条路（勿再走）

| 模式 | 为何被否 |
|------|----------|
| 固定壳填槽（绿系 5 页一对一塞内容） | 用户：旧实现，不是架构（`archive-shell-fill-v1/`） |
| 色块字卡骨架（assemble python 无图字卡） | 用户：跟 AI 直出无区别（`archive-skeleton-v2/`） |
| open-kimi-ppt-skill 作主引擎 | 见 §0.1 评估结论 |

### 0.1 open-kimi-ppt-skill 评估结论（2026-08-07）

它是什么：Moonshot Kimi PPT 的非官方复刻 skill——PPTD（YAML DSL，每页自包含的 OOXML 抽象）+ 30+ design.md 风格预设 + 本地 WASM 导出可编辑 PPTX + 浏览器截图 QA（7 项清单）+ pptx→pptd 可逆编辑。

- **更灵活吗？是。** 新页型零代码（AI 直接写页面元素）、换风格 = 换 design.md、截图 QA 成熟。
- **能独立交出本项目定义的高质量培训课件吗？不能。** 四个硬伤：
  1. 其 SKILL.md 明文默认对大纲「搜索扩写补料」——与文案锁定/药师终审/禁 AI 扩写功效直接冲突；无文案溯源机制。
  2. 每页组件气质靠 AI 当场发挥，跨页跨课一致性无机制（系列生产要的是"下次还长这样"）。
  3. 无授权占位槽语义，默认搜图/生图填产品位——踩"无授权不仿包装"红线概率高。
  4. 非官方逆向包，上游仓库 2026-08-07 已因版权清空（仅存 fork）；架构文档 §7 早已定性：不作主链路唯一引擎。
- **定位：** 不进主链路，不做对照 POC（用户 2026-08-07 决定砍掉）。**仅借鉴两点**：① 截图 QA 7 项检查清单（已并入本方案 G6）；② design.md 人类可读风格规格写法（tokens.json 各配一份）。

---

## 1. 破题：灵活度从哪来

**把页型从「整页硬编码」降级为「金样构件的声明式组合（recipe）」；把布局从「穷举板式」换成「规则求解」；新形态走「提案→签样→注册」的生长通道。**
N 个构件 × 布局规则组合出的页面远超 N 个页型；每个构件拆自已签样金样，质量有血缘。金样角色从「整页复制模板」变为「构件与语法的拆解来源」。

```text
业务大纲（任意/残缺格式）
  ↓ AI 结构化 + 人审（长期 L2 半自动化）
script.structured.json（内容层，文案锁定，唯一文案来源）
  ↓ 生成器：页型映射（留痕：复用/跨模板/新增+理由）
scene-plan.json（中间稿，可人工 review）
  ↓ recipe 展开 + 布局规则求解（条数/字数/图槽自适应）
content-model.json（引擎输入）
  ↓ 通用引擎 = 构件库（只读 style tokens）渲染
可编辑 PPTX（原生 textbox/image/shape）
  ↓ QA：7 项截图清单 + 文本溯源 + 金样并排
交付（validation/，content_lock 未过不进 settled）
```

---

## 2. 四层机制（设计细则）

### 2.1 构件库（灵活度主战场）

从课件4 / 康爱森金样拆解，初版构件清单（每个构件 = 输入槽 + 布局参数 + 只读 tokens，**禁止字面量颜色/字号**）：

| 构件 | 槽位 | 来源金样 |
|------|------|----------|
| `chrome_bg` | 无（风格底：丝绸/米白） | 两者 |
| `chapter_title` | chapter 文本（描边/填充由 tokens 定） | 课件4 |
| `section_label` | 编号+文本（chevron 前缀） | 课件4 |
| `nav_pills` | items[]、active_index（N 自适应） | 课件4 关联用药 |
| `image_chain` | asset 列表 + 连接符（auto-center） | 课件4 功效链 |
| `data_stat` | 大数字、单位、注释、出处小字 | 新增（痛点数据页用） |
| `row_card` | label + body（行卡，N 自适应） | 康爱森白卡 / 课件4 总结表 |
| `pack_slot` | 标签 + 授权状态（缺图必出「待业务授权」占位） | 课件4 |
| `icon_bullet` | icon + 条目文本 | 康爱森 |
| `audience_card` | 插画 + 标签（N 卡栅格） | 课件4 人群页 |
| `white_stage` | 容器（白卡舞台） | 课件4 |
| `note_bar` | 底部说明/提示条 | 课件4 |

recipe 示例（页型 = 构件的声明式组合，JSON 数据不是代码）：

```json
{
  "page_type": "benefit_chain",
  "family": "product-training",
  "components": [
    {"use": "chrome_bg"},
    {"use": "chapter_title", "slot": "chapter"},
    {"use": "section_label", "slot": "section"},
    {"use": "image_chain", "slot": "chain", "layout": "auto-center"},
    {"use": "note_bar", "slot": "body"}
  ]
}
```

### 2.2 布局规则（回答"不可能穷尽板式"）

- **条数自适应：** 1 卡横铺 / 2 对半 / 3 等分 / 4→2×2 / 5–6→2×3 / 超 `max_per_page` 拆页（沿用 registry 规则，下沉为构件级布局函数，不再按页型写死坐标）。
- **字数自适应：** 文本长度 → 字号降档 + 行数估算 + 溢出检测（进 QA）。
- **图槽自适应：** 有图槽走图文版式；无图走数据卡/大字版式（不硬塞图，不留空卡）。
- **empty_cards=forbidden** 与 hidden 排除在生成器层硬校验。

### 2.3 风格纯数据

- 每套 style_pack = `tokens.json`（机器读）+ `design.md`（人读，学 open-kimi 写法）。
- 构件渲染只读 tokens；同一套构件几何，不同皮肤。
- 首批两套：`lycopene-health-edu-cream-red-v1`（康爱森实测值，来源 `kangaisen-lycopene-health-edu-v1/style-pack.json`）、`courseware-4-silk-yellow-red-v1`（从 cw4 导出器 `C` 常量+字体+丝绸底参数抽取）。

### 2.4 新形态生长闸门（治理下的灵活）

内容出现注册表没有的形态时，生成器不静默硬套：
1. 输出**页型候选提案** JSON（按内容结构推断形态 + 建议构件组合）；
2. 用现有构件组合渲染 QA 图；
3. 用户签样 → 注册进 registry（status: candidate → settled）。
页型池按业务自然生长，每个新页型都过签样。**不是穷尽，也不是放任。**

**操作手册（L1）：** `docs/page-type-growth-channel.md`  
**提案 schema：** `production-library/schemas/page-type-proposal.schema.json`  
**提案落盘：** `production-library/page-types/<family>/proposals/`

### 2.5 AI 的位置（受控点）

AI 可做：大纲结构化、页型映射建议、截图目检。渲染全是确定性代码。**文案唯一来源 = script.structured.json，生成器不造字。**

---

## 3. 现状盘点（执行起点，已核实）

| 资产 | 路径 | 事实 |
|------|------|------|
| 金样引擎（课件4） | `production-library/validation/courseware/product-courseware-4-faithful-replica-v1/` | `scripts/export-cw4-pptx.mjs`（914 行）：原生可编辑 PPTX（仓内 `@oai/artifact-tool`），已支持 `--model/--out/--assets`；12 个 scene-type builder；占位槽机制内置（缺图→「待业务授权」标签卡） |
| 引擎硬编码点（要解耦） | 同上 | 色板/字体 `C` 常量；丝绸底 `silkBg()`；`CHAIN_LAYOUTS` 按 scene id 查表（S04 兜底）；related_meds nav 写死 2 个；`build_layer_manifest.py` 的 MODEL/OUT/PREFIX 写死 |
| artifact-tool 路径坑 | `poc/courseware-export/work/node_modules/@oai/artifact-tool/` | 仓内相对路径引用；**新引擎须用仓根绝对解析或 npm file: 依赖，单独搬目录会断** |
| 页型注册表 | `production-library/page-types/product-training/registry.json` | 8 页型 + max_per_page + mapper_hints；与 cw4 builder 不对齐（combination_guidance/summary_matrix/precautions/hook_intro 无渲染器） |
| 风格 | `production-library/styles/` 仅 dashenlin 绿 | cream-red 实测值在康爱森 `style-pack.json`（colors_measured/type/shadow/layout 全）；丝黄红无 tokens |
| 插画资产 | cw4 `assets/generated/` 31 张 | tomato/prostate/nk-cell/o2/flex_arm/softgel/five_tomatoes/skincare_woman/map_xinjiang/couple/audience_*/slot-pack-*/slot-photo-*/time_magazine 等；`asset-provenance.json` 登记来源 |
| 组件库规范 | `assets/component-library/README.md` | `<category>/<id>/{component.json,candidates/,master/,transparent/,prompts/}`，状态机 candidate→selected→approved，系列绑 `series_id`；建资产前查 `production-library/catalog.json` |
| 内容脚本 | `…/fuler-maikenli-lycopene-v1/script.structured.json` | schema product-training-script/v1；7 section；`content_lock=business-provided-draft-pending-pharmacist-review`；features 第 4 条 hidden（大品牌关闭） |
| 金样 QA 对照图 | `…/fuler-maikenli-lycopene-v1/qa-cw4-gold/`、康爱森 `preview/` | 并排自检锚点 |
| assemble python | `scripts/assemble_product_training_pptx.py` | **仅结构实验通道，勿当交付**；若触及 pptxgenjs 注意：shadow 对象必须每次新建（lessons 教训） |
| QA 转换惯例 | 归档目录先例 | `soffice --convert-to pdf` → `pdftoppm -png` → 每页 QA 图 + montage |
| 编辑器（:9012） | cw4 `npm run start:editor` | 视频轨/业务编辑器，**本线无关，勿动**；editor-bg 不得烧录可编辑层（视频轨教训，若日后做视频遵守） |

---

## 4. 任务规划（中期 M1–M5 + 长期 L1–L2，直接执行）

> 每步验收不过不进下一步。**金样回归纪律贯穿 M2/M3**：用金样 content-model 跑新引擎，QA 图与 settled preview 逐页并排，不一致 = 重构破金样，停下修。

### M1 风格数据化

- [x] 1.1 注册 `production-library/styles/lycopene-health-edu-cream-red-v1/tokens.json`（从康爱森 style-pack.json 实测值映射：bg #FBF7F0、title_red #D32F2F、Noto Sans SC、卡片阴影 emu 值、边距）+ 同目录 `design.md`
- [x] 1.2 抽取 `production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json`（cw4 导出器 C 常量、HarmonyOS Sans SC、丝绸底色）+ `design.md`
- [x] 1.3 两套 style_pack 登记 `production-library/catalog.json` + `registries/styles.json`（2026-08-07）
- 验收：tokens 字段覆盖构件渲染所需全部色/字/影/距；catalog 可查 ✅

### M2 通用引擎 + 构件库

- [x] 2.1 新建 `production-library/engines/courseware-pptx-v1/`：`export.mjs` 泛化自 `export-cw4-pptx.mjs`，flags `--model --style --recipes --out --assets`；artifact-tool 用仓根绝对路径解析（注意 §3 坑）；**cw4 旧导出器一行不动**
- [x] 2.2 构件库 `engines/courseware-pptx-v1/components/*.mjs`（§2.1 清单），全部只读 tokens；从 cw4 builder 抽取逻辑（`chapterTitle/imageFit/centerBox/nav pill/占位槽` 等）
- [x] 2.3 布局规则模块 `layout-rules.mjs`（§2.2：N 卡栅格/字号降档/拆页/图槽分支）
- [x] 2.4 `build_layer_manifest` 参数化（`--model/--out/--prefix`）
- [x] 2.5 冒烟：15 页 `out/engine-v1-gold.pptx` + `out/engine-v1-gold-qa/slide-*.png`；视觉并排目检待用户确认
- 验收：**金样回归**——金样 content-model 经新引擎导出，QA 图与 `templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/preview/` 并排一致

### M3 页型 recipe 化

- [x] 3.1 registry 页型各写 recipe（`page-types/product-training/recipes/*.json`），`scene-type-map.json` 映射 cw4 12 scene type → page_type+impl
- [x] 3.2 新页型入 registry（status: candidate）：`hook_pain_data` / `combination_guidance` / `precautions`；export 默认 `--recipes` 指向该目录，`recipe_trace` 写入 inspect
- 验收：金样 15 页 recipe 导出 `out/engine-v1-gold-recipe.pptx` + QA；candidate 三页用户签样通过（2026-08-08）→ `validation/courseware/m3-candidate-pages/`

### M4 生成器

- [x] 4.1 `scripts/generate_courseware.py`：`--script --registry --style --out-dir` → scene-plan.json（每 section 页型选择留痕：reuse/cross_template/new+理由）→ content-model → manifest → 调引擎 → QA 图
- [x] 4.2 硬校验：hidden 排除、empty_cards、**文案只取自 script**、缺图→带标签占位槽
- [x] 4.3 `scripts/verify_text_provenance.py`：提取 PPTX 全部文本 ↔ script 逐条比对；禁词表（锌/硒/维生素E/好物推荐）0 命中
- 验收：麦金利 script 一条命令出稿；溯源报告通过 ✅（2026-08-08；`…/fuler-maikenli-lycopene-v1/m4-generator-out/` 12 页）

### M5 麦金利验证（验证料，不是目的）

- [x] 5.1 先 5 页验证稿（cream-red）：cover / hook_pain_data / benefit_chain×1 / combination_guidance / precautions → `…/m5-validation-out/`（2026-08-08）
- [x] 5.2 4 张注意事项插画：whitekey+14% pad → check-alpha PASS → `assets/component-library/product-training-precautions/` + catalog `asset_registries` 登记
- [x] 5.3 QA：7 项清单 + montage + inspect（原生可编辑）→ `m5-validation-out/QA-REPORT.md`
- [x] **用户目检签样通过**（2026-08-08：「没问题了」）
- [ ] 5.4 5 页过后可选全量 16 页（页序见 §5）
- 验收：对照 `handover-user-intent-2026-08-07.md` §3.4 成功标准 1–6 ✅（5 页验证闸）

### L1 生长通道

- [x] 页型候选提案机制（§2.4）文档化：提案 JSON schema + 模板 + 状态机 proposal→candidate→settled
- [x] 签样流程文档化（步骤 A–F + 7 项 QA），接入 settled 纪律
- **操作手册：** `docs/page-type-growth-channel.md`
- **Schema / 提案目录：** `production-library/schemas/page-type-proposal.schema.json` · `page-types/product-training/proposals/`
- **先例：** M3 三页提案历史回填（hook_pain_data / combination_guidance / precautions）
- 未做（可选增强）：生成器自动吐 proposal、CI schema 校验、WorkBuddy 入口

### L2 内容入口

- [x] 业务 Word/大纲 → script.structured.json 半自动（确定性结构化 + 人审清单；不扩写）
- [x] 对接 `production-library/business-pptx-courseware-word-input-contract.md` 四步流
- **操作手册：** `docs/product-training-script-content-entry.md`
- **Schema：** `production-library/schemas/product-training-script.schema.json`
- **工具：** `scripts/draft_product_training_script.py`
- **样例：** `samples/product-training-script/示例大纲_商品培训_L2.md` → `validation/courseware/l2-draft-smoke/`
- 未做（可选）：WorkBuddy 一键、Word 贴图抽资产、CI schema 校验

---

## 5. 麦金利全量页序参考（M5.4 用，内容驱动 16 页）

cover（麦金利品名+【专业力】+大参林）→ time_list（时代杂志）→ broll（餐桌）→ hook_pain_data（症状+32.9%/40%+白皮书）→ product_intro（包装占位槽）→ benefit_chain ×3（大纲全文）→ feature ×3（产地/原料/含量；大品牌 hidden 排除）→ audience ×4 → combination_guidance 单页 3 行（坦索罗辛/前列康/胶原美白，全部占位槽）→ summary 4 行（功效/特点/人群/联合）→ precautions（7 条+4 新插画）→ 结尾 cover。

---

## 6. 红线（执行全程）

1. 文案唯一来源 script.structured.json；禁 AI 扩写功效/剂量；`content_lock` 未过药师审 → 只进 validation/ 不进 settled，speaker notes 注明待终审。
2. 无授权包装一律带标签占位槽（「待业务授权」），禁仿真包装图。
3. 主视觉插画一律 AI 位图/授权实拍，禁 SVG/PIL 假图（失败资产归 `_demo_svg_pil_rejected/`）。
4. 金样回归不一致不进下一步；金样旧链路（cw4 导出器、编辑器）保持可复现。
5. 新资产先查 catalog，入库按 component-library 规范，登记 series_id。
6. 纠正记录写 `tasks/lessons.md`。

---

## 7. 交付物清单（本轮执行完应存在）

- `production-library/styles/{lycopene-health-edu-cream-red-v1,courseware-4-silk-yellow-red-v1}/{tokens.json,design.md}`
- `production-library/engines/courseware-pptx-v1/`（export.mjs + components/ + layout-rules.mjs）
- `production-library/page-types/product-training/recipes/*.json` + registry 新增 3 个 candidate 页型
- `docs/page-type-growth-channel.md` + `schemas/page-type-proposal.schema.json` + `page-types/…/proposals/`（L1）
- `docs/product-training-script-content-entry.md` + `schemas/product-training-script.schema.json` + `scripts/draft_product_training_script.py`（L2）
- `scripts/generate_courseware.py`、`scripts/verify_text_provenance.py`
- `…/fuler-maikenli-lycopene-v1/`：scene-plan.json、content-model、manifest、5 页（或 16 页）PPTX、QA 图、溯源报告
- `assets/component-library/` 4 张注意事项插画 + catalog 登记
- 金样回归 QA 对比记录；tasks/todo.md 勾选；tasks/lessons.md 新增教训
