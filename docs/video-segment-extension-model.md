# 视频扩展模型（段 recipe · 内容驱动）

**状态：** 已确认主路径（2026-08-04）  
**适用：** 商品培训视频、疾病科普视频等 settled 金样风格壳  
**关联：** `docs/project-brief.md` §推进原则 · `scripts/content_driven_rules.py` · `scripts/business_video_*_full.py`

---

## 1. 结论：主方案是否最优？

在「内部培训、金样签样、WorkBuddy 业务自助」约束下，**「风格壳 + 段 recipe 库 + 主题填内容」** 是当前最优可落地路径。

| 备选方案 | 优点 | 问题 | 结论 |
|----------|------|------|------|
| **A. 段 recipe 组合（采纳）** | 与金样质量一致；可登记、可测试；业务只换内容；与 PPT「页型」同构 | 新能力要先做新段 | **主路径** |
| B. 完全自由时间线（类剪映） | 极灵活 | 业务不可用；质量不可控；与金样签样冲突 | 仅制作返修 |
| C. 单长片模板 + 全局参数 | 实现简单 | 模块难增删；列表难自适应；换主题易残片 | 已淘汰（audio-shell 即退化形态） |
| D. 每主题全自动生成分镜 | 看似省人工 | 医学/合规风险高；风格漂移；无法签样 | 不做主路径 |
| E. 纯 PPT 转视频 | 版式自适应成熟 | 不是本项目动效培训片交付形态 | 课件线另走 |

**不采纳「任意新模块自动长出全新动画」**：没有签样 recipe 就没有可靠镜头语言。业务多写的结构 → 并入邻近段或记缺口。

---

## 2. 三层模型

```text
style_pack（风格壳）     色板 / 字体 / 转场 / 音色 / 品牌角标     ← 金样冻结
    └── segment recipes（段模块库）  开场·症状·联合用药…        ← 制作持续丰富
            └── theme content（主题内容）  病名/商品/旁白/列表N条  ← 业务 WorkBuddy
```

| 层 | 扩展什么 | 谁做 |
|----|----------|------|
| 风格壳 | 新系列视觉语言 | 新金样 → 新 style_pack |
| **段 recipe** | 新章节动画结构 | **制作主业：签样 + 登记 + 接入 full** |
| 主题内容 | 感冒 / 新品 / 2 条卖点 | 业务自助；full 重渲 |

一句话：

> **扩展主题 = 填段；扩展能力 = 加段。**  
> 段内必须 **内容驱动**（N 条 → N 行；0 条 → 省略段）。

---

## 3. 「段」的定义

段 recipe = 可复用的**有时序样式片段**：

```text
段 =
  动效骨架（签样）
  + 槽位（标题 / 列表 / 图 / 旁白 / 时长）
  + 布局规则（N 条自适应；禁止空行凑满金样）
  + 映射规则（业务章节标题关键词 → 本段 id）
```

| 段内应自适应 | 段内不自动变 |
|--------------|--------------|
| 列表条数 1…N | 全新镜头语言 |
| 文案在上限内折行/字号 | 未登记插画语义 |
| 本段无业务内容 → **跳过不渲染** | 无 recipe 的「新模块」凭空成段 |

与 PPT 对照：

| | PPT | 视频 |
|--|-----|------|
| 复用单元 | 页型 / 模块 | **段 recipe** |
| 有几条出几条 | `content_driven_rules` | 同规则进 screen JSON + 段内布局 |
| 无内容 | 整节省略 | **空段跳过（不 concat）** |
| 无结构能力 | 加页型 | **加段 recipe 后**再映射 |

---

## 4. 业务自助路径（不变）

业务在 WorkBuddy 只说课型 + 主题 + 要点 → 代理：

1. 锁定 settled 模板 / style_pack / voice  
2. 章节映射到已有段 id  
3. 列表走内容驱动（禁止 pad 到金样条数）  
4. **仅渲染有内容的段** → TTS → 重渲 → concat  
5. 回传 MP4；`run-status` 标明 `included` / `omitted` 段  

禁止默认 audio-shell；禁止把正常 settled 单推回制作。

---

## 5. 制作侧：如何加一段

1. 在金样工程做可签样画面（`poc/gold-sample` 对应 project）  
2. 定义槽位与 `screen` 字段契约  
3. 布局支持 N 条（`items.map`，禁止写死必须 3 行空壳）  
4. 登记：settled manifest / `business_greenline` / 段 id  
5. full 管线 `SEGMENTS` + 关键词映射  
6. 冒烟：有内容纳入 / 无内容 omitted / 2 条不成 3 行  

未完成 1–6 的「新段」不得对业务宣称可用。

---

## 6. 内容驱动硬规则（视频）

与 PPT 对齐，强制：

1. **N 条业务要点 → 屏上 N 条**（可设 max，如 6）；**禁止**用「要点三」等假行凑满金样。  
2. **0 条且无该段旁白 → 段 status=`omitted`，不 TTS、不渲染、不进成片。**  
3. 金样示例条数仅作参考，**不是**输出下限。  
4. 无 recipe 的额外结构：并入邻近段列表或写入 gap，不发明镜头。  
5. 列表规划可复用 `scripts/content_driven_rules.plan_list_block`。

---

## 7. 当前模板段库（基线）

### 商品培训视频（`product-video-faithful-v1`）

| 段 id | 用途 | 列表槽（示例） |
|-------|------|----------------|
| opening | 开场 | — |
| brand | 品牌/品类 | labels |
| faithful | 核心讲解 | — |
| efficacy | 核心功效 | efficacy_sections（N） |
| features | 产品特点 | feature_sections（N） |
| audience | 适宜人群 | — |
| combination | 联合用药 | combo_sections（N） |
| summary | 总结 | summary cells |

### 疾病科普视频（`health-video-reference-tech-v1`）

| 段 id | 用途 | 列表槽（示例） |
|-------|------|----------------|
| intro | 开场 | — |
| character | 基础认知 | character_cards（N） |
| mechanism | 病因机理 | equation 文案 |
| symptoms | 典型症状 | symptom_groups 标签 |
| treatment | 调理建议 | herbs 等 |
| medication | 用药建议 | advice_items（N） |
| summary | 总结 | summary_items |

---

## 8. 实施阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | full 换主题重渲（文案/旁白/主标题） | ✅ 已通 |
| **P1** | **现有段：N 条自适应 + 空段跳过** | **本轮执行** |
| P2 | 重列表段版式随 N 调字号/间距（联合用药、特点、症状卡等） | 后续 |
| P3 | 按业务频率加新段 recipe | 后续 |
| P4 | 总结表等复合版式按「有哪些列」动态列 | 后续 |

---

## 9. 验证口径（P1）

- 业务只给 2 条联合用药 → `combo_sections.length === 2`，屏上不出现空白第 3 条。  
- 业务不写联合用药段 → `combination` 为 `omitted`，成片无该段时长。  
- 疾病科普只给 4 个症状词 → `character_cards` 为 4，不凑满 6 个金样默认词。  
- `full-render-status.json` 含各段 `status: included|omitted`。  

---

## 10. 一句话纪律

**先加厚某风格的段库并做段内内容驱动，再套主题；不拿自由时间线或 AI 乱分镜替代签样段。**
