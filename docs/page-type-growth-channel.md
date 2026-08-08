# 页型生长 / 签样通道（L1）

**状态：** 操作手册（2026-08-08 · L1 文档化）  
**隶属：** 构件化课件流水线 · `docs/component-recipe-pipeline-architecture.md` §2.4  
**前置：** `AGENTS.md` settled 纪律 · `docs/flexible-theme-quality-architecture.md` G3 · `assets/component-library/README.md` 资产状态机  

---

## 0. 一句话

内容出现注册表没有的形态时：**不静默硬套** → 写提案 → 用已有构件渲 QA → 用户签样 → 注册进页型池。  
页型池按业务自然生长：**不是穷尽，也不是放任。**

---

## 1. 解决什么 / 不解决什么

| 要解决 | 不要做成 |
|--------|----------|
| 新大纲形状可治理地进池 | 生成器偷偷映射到最像的旧页型交差 |
| 每个新页型有血缘（拆自金样构件） | 整页硬编码、色块字卡当新页型 |
| candidate / settled 物理分家 | validation 与 settled 混放、用文件名猜状态 |
| 签样有可勾清单 | 「看起来差不多」口头过关无记录 |

**与插画资产状态机的关系：**  
`component-library` 管图（candidate → selected → approved）；  
本通道管**页型**（proposal → registry.candidate → settled）。两者可并行，但页型签样不等于插画 approved。

---

## 2. 状态机

```text
                    ┌──────────────────────────────────────┐
  内容结构未知 ──►  │ proposal（提案 JSON，未进 registry）   │
                    └──────────────┬───────────────────────┘
                                   │ 实现 recipe + builder（仅 validation）
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ candidate（registry status=candidate） │
                    │ + validation/…-candidate-pages/ QA    │
                    └──────────────┬───────────────────────┘
                                   │ 用户目检签样通过
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ settled（可被 generate_courseware 主  │
                    │ 路径 reuse；mapper_hints 可引用）      │
                    └──────────────────────────────────────┘

  任一步失败 → rejected（提案 JSON status=rejected + reason；产物留 validation）
```

| 状态 | registry | 产物目录 | 生成器 |
|------|----------|----------|--------|
| `proposal` | 无条目 | 仅 `proposals/*.proposal.json` | 不映射 |
| `candidate` | `status: candidate` | `validation/courseware/<id>-candidate-pages/` | 可 `--model` 单独导出；**默认主链路不自动选用**（除非 scene-plan 显式 `mode:new` 且人已审） |
| `settled` | `status: settled` | recipe 在 `page-types/…/recipes/`；示例 QA 可归档 validation | `mode: reuse` 合法 |
| `rejected` | 无 / 或 deprecated 备注 | validation 保留对照 | 禁止再映射 |

**注意：** 页型 `settled` ≠ 某 SKU 课件进 `templates/settled/`。  
页型 settled 只表示「这种排版骨架可复用」；具体课 content_lock 未过药师审仍只进 `validation/`。

---

## 3. 何时触发生长通道

满足**任一**即走提案，禁止硬套：

1. **G3 闸门**（`flexible-theme-quality-architecture.md`）：脚本节结构无法落入现有 `page_types[].id`。
2. 生成器 `expand_scene_plan` 若只能用「砍字段 / 空卡 / 假段落」才能塞进旧页型。
3. `export.mjs` 报 `unknown_types`（content-model 的 `scene.type` 无 builder / 无 scene-type-map）。
4. scene-plan 人为标注 `selection.mode = "new"`（跨课复用不够，需新形态）。
5. 业务明确要求新讲解形态（例：对比表、时间轴、双人对话卡），且现有 recipe 不能无损表达。

**不触发（优先 reuse / cross_template）：**

| 情况 | 动作 |
|------|------|
| 仅条数变化（2 卡→4 卡） | 布局规则 `adapt_n` / 拆页，不新建页型 |
| 仅换 style_pack | 套另一套 tokens |
| 字段可落到已有 slots（别名） | `cross_template` 或 mapper 扩展，写清 reason |
| 缺图 | 授权占位槽，不新建页型 |

### scene-plan 选择留痕（已实现）

| `selection.mode` | 含义 |
|------------------|------|
| `reuse` | 注册表 settled 页型 + 标准映射 |
| `cross_template` | 用邻近 scene/impl 承载，理由必写（例：hook 无 stats → time_list） |
| `new` | **生长通道**：应对应一份 proposal，禁止无提案的 silent new |

当前 `generate_courseware.py` 对**未注册** `page_type` 会直接 `GeneratorError`——正确行为。  
自动化「吐出 proposal JSON」是后续增强（见 §10）；在此之前由执行者按本手册手写提案。

---

## 4. 提案产物

### 4.1 路径约定

```text
production-library/page-types/<family>/
  registry.json
  recipes/
    <page_type_id>.json
    scene-type-map.json
  proposals/
    _TEMPLATE.proposal.json          # 复制用空壳
    <page_type_id>.proposal.json     # 进行中 / 历史提案
    README.md                        # 本目录索引（可选）

production-library/schemas/
  page-type-proposal.schema.json     # 字段约束

production-library/validation/courseware/
  <page_type_id>-candidate-pages/    # 或 m3-candidate-pages 式聚合目录
    content-model.json
    assets/                          # 仅本签样用图；可复用 component-library
    out/
      <name>.pptx
      qa/slide-*.png
    QA-REPORT.md                     # 签样结论与用户原话
```

**family 首发：** `product-training`。  
其他 family（health-edu 等）同构，各自 `page-types/<family>/`。

### 4.2 提案 JSON 必填字段

Schema：`production-library/schemas/page-type-proposal.schema.json`

| 字段 | 说明 |
|------|------|
| `schema` | 固定 `page-type-proposal/v1` |
| `page_type_id` | 蛇形 id，全局 family 内唯一 |
| `name_zh` | 中文名 |
| `family` | 如 `product-training` |
| `status` | `draft` \| `ready_for_qa` \| `signed_off` \| `registered_candidate` \| `settled` \| `rejected` |
| `trigger` | 为何现有页型不够（内容形状描述） |
| `content_shape` | 输入结构信号（哪些数组/字段出现） |
| `slots` | 内容槽声明 |
| `components` | 建议构件组合（`use` 必须已在引擎 `components/` 存在，或并列「需新增构件」清单） |
| `layout` | max_per_page、adapt_n、empty 策略 |
| `scene_type` / `impl` | content-model type 与 builders 名（常同 id） |
| `sample_script_refs` | 示意文案必须可溯源到某 script 或标明「版式示意-非交付」 |
| `gold_lineage` | 拆自哪套金样/哪几个已有 builder |
| `mapper_hints` | 建议写入 registry.mapper_hints 的关键词 |
| `qa_dir` | validation 相对路径 |
| `signoff` | 签样人、日期、用户原话、checklist 勾选 |
| `rejection` | 若 rejected：原因与替代方案 |

**红线（提案阶段即生效）：**

- 文案不得 AI 扩写功效/剂量；示意稿须标注非药师审定。
- 无授权包装 → 带标签占位槽。
- 构件禁止写死色值/字号，只读 style tokens。
- 优先组合**已有**构件；新构件须说明拆自哪页金样，另开构件实现任务。

---

## 5. 签样流程（逐步）

### 步骤 A — 提案（约 30–60 min 文档）

1. 复制 `proposals/_TEMPLATE.proposal.json` → `<id>.proposal.json`。
2. 填 trigger / content_shape / slots / components / layout。
3. 对照 registry：确认 id 不冲突；说明为何不能 reuse。
4. `status = draft` → 自评完整后 `ready_for_qa`。

### 步骤 B — 最小实现（仅 validation）

1. 写 `recipes/<id>.json`（components + impl_by_scene）。
2. 更新 `recipes/scene-type-map.json` 增加 scene → page_type + impl。
3. 在 `engines/courseware-pptx-v1/scenes/builders.mjs` 增加 builder（组合已有构件；**禁止**复制 cw4 旧导出器改色交差）。
4. registry 增加条目，`status: candidate`（未签样前不得写 settled）。
5. 准备 `validation/courseware/<…>-candidate-pages/content-model.json`（1–3 页代表性场景即可）。
6. 导出：

```bash
node production-library/engines/courseware-pptx-v1/export.mjs \
  --model production-library/validation/courseware/<dir>/content-model.json \
  --style production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json \
  --assets <assets-root> \
  --out production-library/validation/courseware/<dir>/out/<name>.pptx
```

7. QA 图：`soffice --convert-to pdf` → `pdftoppm -png` → `out/qa/slide-*.png`（或项目惯用 pptx-qa 流程）。
8. 插画若新生成：先走 component-library（whitekey + check-alpha），再贴页。

### 步骤 C — 目检清单（G6 · 7 项）

对齐 M5 / open-kimi 借鉴清单，每页勾：

| # | 检查项 | 失败动作 |
|---|--------|----------|
| 1 | 章标/标题单行或可控折行，无裁切 | 调 chapter_title / 字号阶梯 |
| 2 | 正文培训可读（style `scale_factor`；正文≥16pt） | 抬 tokens 或减字 |
| 3 | 无空卡、无幽灵占位 | 减 max 或拆页 |
| 4 | 图槽：有图则去底合格；无图不硬塞 | whitekey / 删槽 |
| 5 | 对齐/边距/卡片阴影与金样气质一致 | 对照 silk 或 cream 金样 QA |
| 6 | 文案可溯源（示意稿除外且已标注） | 回 script |
| 7 | 原生可编辑（inspect 有 text/image 层，非整页位图） | 修 builder |

另写 `QA-REPORT.md`：页列表、已知限制、待业务替换项。

### 步骤 D — 用户签样

1. 打开 `out/*.pptx` 或 `qa/slide-*.png` 请用户复核。
2. 用户通过句记入 `signoff.user_quote`（历史惯例：「可以」「没问题了」等）。
3. 提案 `status = signed_off`；registry 可保持 candidate 直至步骤 E 完成登记核对。
4. 若驳回：`status = rejected`，写清原因；代码可留 validation 对照，**registry 删 candidate 或标 deprecated**。

### 步骤 E — 注册为 settled（可进主映射）

核对清单全部勾选后：

- [ ] `registry.json`：`status` → `settled`；slots / max_per_page / layout 与 recipe 一致  
- [ ] `recipes/<id>.json`：`status: settled`  
- [ ] `scene-type-map.json` 已映射  
- [ ] `builders` 导出表已注册  
- [ ] `mapper_hints` 关键词已加（避免下次又提案）  
- [ ] `generate_courseware.py` 如需从 script section 自动展开，补 `expand_scene_plan` 分支，`mode: reuse` + reason  
- [ ] 提案 JSON：`status = settled`，`signoff` 填齐  
- [ ] `tasks/todo.md` / lessons 如有纠正则更新  
- [ ] **不**把未过 content_lock 的 SKU 课件拷进 `templates/settled/`

### 步骤 F — 金样回归（若动了共享构件）

若 builder 改了公共 `components/*` 或 layout-rules：

1. 用课件4 金样 content-model 跑 engine 全量导出。  
2. QA 与 settled preview / 既有 gold QA **并排**；不一致 = 停下修，不升 settled。

---

## 6. 与 M3 范例对齐（已走过一次）

| 页型 | 提案动机 | 签样目录 | 结果 |
|------|----------|----------|------|
| `hook_pain_data` | 导语含症状 chips + 大数字 stats，旧 hook_intro/time_list 不够 | `validation/courseware/m3-candidate-pages/` | 2026-08-08 用户「可以」→ settled |
| `combination_guidance` | 联合行卡（问题/搭配/话术）≠ 旧 related_meds 双包装导航 | 同上 | settled；M5 又修短场景标签 |
| `precautions` | 左编号列表 + 右 2×2 插画 | 同上 | settled；M5 入库 4 插画 |

历史提案归档（示意已落地）：  
`production-library/page-types/product-training/proposals/hook_pain_data.proposal.json` 等。

复跑 candidate 导出命令见引擎 README。

---

## 7. 目录与文件职责速查

| 路径 | 职责 |
|------|------|
| `page-types/<family>/registry.json` | 页型池权威：id、status、slots、max_per_page、mapper_hints |
| `page-types/<family>/recipes/*.json` | 声明式构件组合（数据，非代码） |
| `page-types/<family>/recipes/scene-type-map.json` | scene.type → page_type + impl |
| `page-types/<family>/proposals/` | L1 生长提案与签样元数据 |
| `engines/…/components/*.mjs` | 可复用构件实现 |
| `engines/…/scenes/builders.mjs` | scene impl → 调构件 |
| `engines/…/layout-rules.mjs` | N 卡/字号/拆页规则 |
| `scripts/generate_courseware.py` | script → scene-plan（reuse/cross/new）→ model → 导出 |
| `scripts/verify_text_provenance.py` | 文案溯源闸 |
| `validation/courseware/*` | 一切 candidate / 探索 / QA |
| `templates/settled/*` | 仅用户确认沉淀的**整课模板**，不是单个 page_type |

---

## 8. AI 边界（与架构 §2.5 一致）

| AI 可做 | AI 禁止 |
|---------|---------|
| 根据内容形状起草 proposal JSON | 静默改 script 功效/剂量 |
| 建议构件组合与 mapper 关键词 | 无签样把 candidate 标 settled |
| 协助写 builder 调用构件 | 用整页位图/SVG 假图冒充插画线 |
| 截图目检辅助 | 无授权仿真包装 |

渲染必须是确定性代码路径。

---

## 9. 拒收与降级

| 现象 | 处理 |
|------|------|
| 可用 cross_template + 清晰 reason | 不立项新页型 |
| 仅差一张插画系列 | 走 component-library，不新建 page_type |
| 提案要求全新视觉语言（非整课 style） | 先 style_pack 签样，再页型 |
| 用户否决版式 | rejected；保留 QA 作反例，勿删 lessons |
| content_lock 未过 | 页型可 settled；**该 SKU 成片**仍 validation |

---

## 10. 当前实现水位与后续增强

**已具备（可人工跑通全通道）：**

- registry + recipes + scene-type-map + builders  
- scene-plan `selection.mode` 留痕  
- 未注册 page_type → 硬失败  
- unknown scene types 写入 inspect  
- M3/M5 签样先例  

**文档化完成（L1 本文件）：** 提案格式、状态机、步骤 A–F、清单。

**未做（勿假装已有；需要时另开任务）：**

1. `generate_courseware.py` 遇未知结构自动写出 `*.proposal.json`  
2. proposal JSON 的 CI schema 校验脚本  
3. WorkBuddy 一键「提交页型候选」业务入口  
4. health-edu family 页型池同等 registry（康爱森线仍以金样归档为主）

---

## 11. 快速检查清单（执行者）

开新页型前：

- [ ] 已读本文件 + architecture §2.4  
- [ ] 确认不能 reuse / cross_template  
- [ ] 提案 JSON 已建  
- [ ] 只用已有构件或先开构件任务  
- [ ] 产物只在 validation  
- [ ] 7 项 QA + QA-REPORT  
- [ ] 用户原话入库  
- [ ] registry / recipe / map / builder / mapper_hints /（可选）generate 分支 六处一致  
- [ ] 动公共构件则金样回归  

---

## 12. 相关入口

| 文档/资产 | 路径 |
|-----------|------|
| 流水线总方案 | `docs/component-recipe-pipeline-architecture.md` |
| 三层模型 + G3 | `docs/flexible-theme-quality-architecture.md` |
| 本通道 | `docs/page-type-growth-channel.md` |
| 提案 schema | `production-library/schemas/page-type-proposal.schema.json` |
| 提案目录 | `production-library/page-types/product-training/proposals/` |
| 页型注册表 | `production-library/page-types/product-training/registry.json` |
| 引擎 | `production-library/engines/courseware-pptx-v1/README.md` |
| M3 QA 先例 | `production-library/validation/courseware/m3-candidate-pages/` |
| M5 验证先例 | `…/fuler-maikenli-lycopene-v1/m5-validation-out/` |
| 插画状态机 | `assets/component-library/README.md` |
