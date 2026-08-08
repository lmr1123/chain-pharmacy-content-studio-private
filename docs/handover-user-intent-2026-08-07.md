# 需求意图交接（2026-08-07）

> **2026-08-07 后续：执行方案已定 → `docs/component-recipe-pipeline-architecture.md`（构件化流水线，中期+长期路线，任务规划在 `tasks/todo.md` 顶部）。下一模型以该方案为准，本文档为意图背景。**
>
> 给下一模型/会话：先读本文，再动代码。  
> 项目根：`/Users/liminrong/Projects/chain-pharmacy-content-studio`  
> 约束总则：`AGENTS.md`（金样优先、审核文案锁定、无授权不仿包装）

---

## 1. 用户要的是什么（一句话）

**用业务给的「福尔麦金利番茄红素」大纲，走「内容脚本 → 页型匹配 → 风格套皮」流水线，生成图文并茂、达到金样观感的可编辑培训课件（PPTX 为主），并可后续扩展到 Remotion/交互/视频——不是打开/拷贝一份已有课件交差，也不是固定壳填空，更不是色块字卡骨架。**

---

## 2. 意图演进（按用户纠正顺序）

| 阶段 | 用户说了什么 | 真实意图 |
|------|--------------|----------|
| A | 要金样课件，可复用、可扩展到交互 Remotion；源是康爱森番茄红素 PPTX | 建立**可复用的高质量培训内容生产线**，金样是质量锚，不是一次性复刻交差 |
| B | 框架重画的 PPTX 太差，要 100%（字体/背景/阴影/布局） | **金样 = 原片 OOXML 级真源**；抽象重画 ≠ 金样 |
| C | 把福尔麦金利内容套进金样能力；参考 open-kimi 灵活主题 + 交付质量 | **风格 / 页型 / 脚本三层解耦**；换内容不必重做视觉，换风格不必重写内容 |
| D | 确认：style · page_type · script 独立；输入→脚本→页型→风格→生成 | 写进产品方案并**按此执行**，不是只写文档 |
| E | 「你这还是原实现：一对对塞进绿系金银花露卡槽」 | **禁止**固定 5 页壳（cover/overview/combo/benchmark/precautions）填槽 |
| F | 「效果太差，跟直接 AI 生成有什么区别，没有图文并茂高质量培训课件」 | **观感门槛 = 图文并茂金样级**；无插画/场景的色块三卡不算交付 |
| G | 「你相当于直接复用原金样，完全没有做什么」 | **禁止**把 settled 课件4 拷贝改名当「本次任务完成」；要**按大纲真正生成** |

---

## 3. 目标系统（应建成什么）

### 3.1 三层模型（已共识）

```text
C. content / script     审核文案、数据、话术、图槽、待确认
        ↓ 条数自适应展开
B. page_type            页型骨架（N 卡、联合用药表、总结矩阵…）
        ↓ 套皮
A. style_pack           色板/字体/阴影/组件气质（绿系 / 课件4 丝黄红…）
        ↓
质检 → 可编辑 PPTX（主交付）+ 可选视频/Remotion
```

文档：`docs/flexible-theme-quality-architecture.md`  
对标：open-kimi-ppt-skill 的 design system + 自由内容 + QA 思路。

### 3.2 本次内容主题（不是视觉主题）

- **SKU / 课：** 福尔麦金利牌番茄红素软胶囊 · **商品培训**（非康爱森那种成分科普壳）
- **文案源：** 用户提供的完整大纲（导语、三大功效、特点、适宜人群、联合用药话术、总结、注意事项）
- **结构化稿：**  
  `production-library/validation/courseware/fuler-maikenli-lycopene-v1/script.structured.json`  
  （及同目录 `content-script.md`）

### 3.3 质量锚（观感参考，不是「直接交付原件」）

| 金样 | 路径 | 用途 |
|------|------|------|
| **商品培训课件4 · 福尔番茄红素**（用户 08-03 签样） | `production-library/templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/` | **图文并茂观感与分镜语法** 的主锚（插画、人群图卡、功效分镜、关联用药） |
| 课件4 可改工程 | `production-library/validation/courseware/product-courseware-4-faithful-replica-v1/` | 真·生成/导出入口（export:pptx / video） |
| 绿系金银花露 5 页 | `…/product-courseware-green-v1/`、`gold-samples/jinyinhualu-pptx-gold-v1/` | 仅 style/chrome 参考；**禁止**当唯一固定页序壳填内容 |
| 康爱森番茄红素原片 | `…/kangaisen-lycopene-health-edu-v1/` | **成分科普** family 金样；与商品培训页序不同，勿混壳 |
| 专用插画资产 | `…/tomato-lycopene-faithful-v1/assets/generated/` 及课件4 `assets/generated/` | 番茄→前列腺、抗氧化、免疫、产地、软胶囊等 |

**金样用法：** 量测布局/插画密度/组件 → 驱动**新生成**；**不是** `cp` 改文件名交差。

### 3.4 成功标准（验收）

下一模型交付必须**同时**满足：

1. **内容：** 以用户大纲 / `script.structured.json` 为准生成（联合用药等以大纲为准，不要静默换成旧金样里的锌硒话术却假装完成）。  
2. **结构：** 内容驱动页序（有几条功效就几卡/可拆页；`empty_cards=forbidden`；禁止硬塞进固定 5 槽）。  
3. **观感：** 图文并茂，**目视达到课件4 金样密度**（插画/场景图 + 标题 + 正文；不是纯文字圆角卡）。  
4. **产物：** 可编辑 PPTX 为主；整页导出 QA 图可对照；文案不擅自扩写功效/剂量。  
5. **诚实：** 缺包装授权图用**明确占位槽**，禁止假包装；合规待审写清 `content_lock`。  
6. **过程：** 不能只交付「打开/拷贝已有 settled 文件」；必须有**可复现的生成命令 + 中间产物**（script → plan → 渲染）。

未达成第 3 条（图文质量）= **未完成**，即使页型映射正确。

---

## 4. 明确禁止（反模式）

| 禁止 | 为何被否 |
|------|----------|
| 金银花露绿系 5 页固定槽一对一填内容 | 用户：这是旧实现，不是架构方案 |
| python/assemble 色块字卡当培训交付 | 用户：跟 AI 直出无区别 |
| 框架重画冒充康爱森原片金样 | 用户：要 100% OOXML 真源 |
| **拷贝 settled 课件4 改名当「做完了」** | 用户：完全没做事 |
| AI 扩写药学功效/剂量/卖点 | 合规红线 |
| 无授权仿真实包装 | 资产红线 |
| 只写架构文档不跑通可验收生成 | 执行空转 |

归档反例（勿当交付）：

- `fuler-maikenli-lycopene-v1/archive-shell-fill-v1/`  
- `fuler-maikenli-lycopene-v1/archive-skeleton-v2/`  

工具现状：

- `scripts/assemble_product_training_pptx.py`：**仅结构/页序实验**，**不是**交付通道。  
- 交付级渲染应挂在 **课件4 视觉/插画系统**（或同等图文密度实现），并由 script 驱动内容。

---

## 5. 内容要点（大纲摘要 · 生成时以 structured JSON 为准）

- **导语：** 时代杂志番茄第一、前列腺痛点、发病率 32.9% / 年轻化 25–34 岁 40%、引入本品  
- **三大功效：** 护前列腺·提精子活力；抗氧化延衰（维 E 100 倍口径）；增强免疫  
- **特点：** 产地好（新疆）、原料优（番茄肉提炼）、含量高（1 粒≈5 个大番茄）；**大品牌话术关闭**  
- **适宜人群：** 前列腺 / 备孕 / 爱美 / 体虚  
- **联合用药话术（大纲）：** 坦索罗辛·非那雄胺；前列康·普乐安；胶原/美白 —— **与旧课件4 金样中的锌硒/维E 叙事可能不同，应以用户大纲生成为准**  
- **注意事项：** 不代替药物、标签用量、联用咨询药师等  

`content_lock`：业务草稿，**药师/合规终审前非正式培训稿**。

---

## 6. 建议的下一模型执行路径（最小正确路径）

```text
1. 读 AGENTS.md + 本文 + docs/flexible-theme-quality-architecture.md
2. 读 script.structured.json，列出与课件4 content 的 diff（尤其联合用药）
3. 选定渲染真源：product-courseware-4 工程（插画+export），而非 assemble python
4. 用大纲内容驱动：改 content-model / project content / 页型展开
   - 页数可变：功效分镜、特点分镜、人群图卡、联合用药、总结、注意
5. 复用已有插画资产；缺图 → 占位或生成（合规）后入 component-library
6. export 可编辑 PPTX + 全页 QA 静帧
7. 与课件4 金样 key 帧并排自检：图文密度、非色块字卡
8. 写清：生成命令、改了哪些文件、哪些文案仍待药师审
```

**不要：** 再交付一份「打开 settled 金样」或再画一套绿底三卡。

可选后续（用户曾提、非本步必须）：

- 同一 script → Remotion / 交互  
- 第二 style_pack 热切换（绿 / cream-red）  
- 包装高清授权图接入  

---

## 7. 关键路径速查

| 用途 | 路径 |
|------|------|
| 本次校验目录 | `production-library/validation/courseware/fuler-maikenli-lycopene-v1/` |
| 内容脚本 | 同上 `script.structured.json` |
| 产品方案 | `docs/flexible-theme-quality-architecture.md` |
| 课件4 settled 金样 | `production-library/templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/` |
| 课件4 工程 | `production-library/validation/courseware/product-courseware-4-faithful-replica-v1/` |
| 页型注册表（结构层） | `production-library/page-types/product-training/registry.json` |
| 绿系 tokens（仅风格） | `production-library/styles/dashenlin-courseware-green-v1/tokens.json` |
| 组件库 | `assets/component-library/` |
| 教训 | `tasks/lessons.md` |

---

## 8. 前序会话已做错什么（给下一模型避雷）

1. 绿壳 5 页填槽 → 用户否。  
2. assemble 引擎 8 页色块字卡 → 用户否（= AI 直出）。  
3. 拷贝课件4 settled 当交付 → 用户否（= 没做事）。  

**正确理解：**  
- 金样 = **质量标准与资产库**，不是复制粘贴终点。  
- 架构 = **可复现流水线**（新大纲进、高质量课件出）。  
- 本次缺口 = **「大纲驱动 + 课件4 级图文渲染」仍未打通**。

---

## 9. 给用户的确认点（若下一模型开干前需问）

1. 联合用药：严格按大纲（坦索罗辛/前列康/美白）生成，还是保留课件4 锌硒/维E 并另开一页？  
2. 风格：课件4 丝黄红插画线（推荐，已有图）还是绿系大参林 chrome + 同一套插画？  
3. 页数策略：课件4 式「一功效一镜」多页，还是「功效三卡一页」压缩（仍须有图）？  

未问清时默认：**大纲文案为准 + 课件4 图文密度 + 一功效可分镜多页**。
