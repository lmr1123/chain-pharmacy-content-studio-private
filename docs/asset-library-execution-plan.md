# 资产库后勤计划（从属）

> 从属 `decision.gold-sample-first` / `docs/project-brief.md` §1.1。  
> 只描述资产与缺口后勤；**不得**把囤元素当主进度。真包装由业务提供。

---

## 1. 目标与成功标准

### 1.1 业务目标

在**已有金样课型**上：业务提交审核脚本 + 授权包装后，按框架分镜、匹配素材、列缺口；得到与金样同系列的完整预览/导出。

### 1.2 成功标准（可验收）

| # | 标准 | 度量 |
| --- | --- | --- |
| S1 | 主题可检索 | `query --type theme` 覆盖已上线病种/SKU |
| S2 | 生产图均有系列 | symptoms/herbs/icons 等 master 带 `series_id` |
| S3 | 缺口可外补 | plan 输出结构化 `asset_gap_tasks`；可导出采购/再生清单 |
| S4 | 外补不脏库 | `_intake` 与 master 隔离；参考像素不进 master |
| S5 | 包装业务供 | 真包装 gap 状态为 `awaiting-business-asset`，不阻塞教学插画填充 |
| S6 | 跨主题复用 | 第二疾病/第二课件商品主要靠补成员，不新建 style_pack |
| S7 | 端到端 | 非样例主题 Word → 分镜预览 + 缺口清单 可跑通 |

---

## 2. 边界与非目标

| 做 | 暂不做 / 不做 |
| --- | --- |
| 系列契约、外补流水线、主题登记 | 真包装采购与拍摄（**业务提供**） |
| 通道 B 商用图标/开源适配、通道 C 参考再生 | 伪造品牌包装、未授权爬整站 |
| 场景配方与 plan 增强 | 第三套全新视频风格包（签样稳定前） |
| 课件绿 / 疾病深蓝 / 商品蓝 内扩展 | 竖屏矩阵、学练测平台 |

**真包装策略（锁定）**

```text
装配需要 packshot / logo / evidence
  → asset_gap_tasks.preferred_channel = "A"
  → status = "awaiting-business-asset"
  → 业务 Word/附件或 DAM 投喂后 source_class=company_authorized
  → 制作只做抠图/透明/多角度规范，不生成替代包装图用于生产
```

---

## 3. 阶段总览

```text
Phase 0  基线固化（本周）     计划 + 主题 + 缺口 schema + intake + 系列收敛
Phase 1  外补试点（1–2 周）   B 图标 + C 再生各至少 1 条进 candidates
Phase 2  跨主题验证（2–3 周） 胃肠疾病成员 + 第二课件 SKU（包装业务供）
Phase 3  业务闭环（3–4 周）   Word→plan→预览→确认→导出 傻瓜路径
Phase 4  规模化（持续）       按 gap 批量补系列；Q10 视觉签样后扩商品视频
```

---

## 4. Phase 0 — 基线固化

| ID | 任务 | 产出 | 状态 |
| --- | --- | --- | --- |
| P0.1 | 整体执行计划本文 | `docs/asset-library-execution-plan.md` | 进行中 |
| P0.2 | 主题登记 | 风热 / 金银花露 / 穿心莲 / Q10 | **已完成** |
| P0.3 | 资产规划与外补协议 | `seed-asset-library-bootstrap.md` §3.6 | **已完成** |
| P0.4 | `asset_gap_tasks` schema + 示例 | `production-library/schemas/asset-gap-tasks.schema.json` | 本轮 |
| P0.5 | `_intake` 分通道目录 + README | `assets/_intake/**` | 本轮 |
| P0.6 | 外补/业务待供清单 CSV 模板 | `production-library/templates/asset-gap-worklist.csv` | 本轮 |
| P0.7 | symptoms → series 契约 + 回填 | `series.symptom.pharmacy-health-cartoon-v1` | 本轮 |
| P0.8 | herbs → series 契约 + 回填 | `series.herb.botanical-clean-v1` | 本轮 |
| P0.9 | advice icons / generic packshot 分轨登记 | series + registry 字段 | 本轮 |
| P0.10 | plan 输出对齐 gap schema（通道建议、业务待供） | `plan_training_course.py` | 本轮 |
| P0.11 | catalog / todo 入口 | 可查询 | 本轮 |

**验收**：query 可见 theme + asset-series；缺口 JSON 符合 schema；真包装类 gap 标明 `awaiting-business-asset`。

---

## 5. Phase 1 — 外补试点（不含真包装）

| ID | 任务 | 通道 | 验收 |
| --- | --- | --- | --- |
| P1.1 | 选 1 个建议/禁忌图标 gap（若库内不足则新语义） | B 商用/开源 → 改色贴 series | candidates + source + license |
| P1.2 | 选 1 个机制/症状成员（如胃肠 organ 或新症状） | C 参考再生 / 自研配方 | candidates 贴 mechanism 或 symptom series |
| P1.3 | 6 张外部拆解卡壳 | 仅 reference | `docs/references/cards/*` |
| P1.4 | 业务包装投喂说明一页 | A 仅说明 | Word/清单里「包装由业务提供」字段对齐 |

**不做**：代业务找商品主图、竞品包装爬取。

---

## 6. Phase 2 — 跨主题验证

| ID | 任务 | 说明 |
| --- | --- | --- |
| P2.1 | `theme.disease.gastric-*` 元数据 | 复用 medical-tech + mechanism/symptom series |
| P2.2 | 机制系列补胃/肠相关 role 成员 | 缺口驱动；先代表图签样 |
| P2.3 | 第二课件商品 theme | 复用绿模板；包装槽 `awaiting-business-asset` |
| P2.4 | 对比风热/金银花露 | 风格一致、成员可查、无新 style_pack |

---

## 7. Phase 3 — 业务闭环

| ID | 任务 |
| --- | --- |
| P3.1 | 统一健康/商品 Word 最小 schema（已部分进行） |
| P3.2 | 分镜预览展示：匹配成员 / 教学图缺口 / **业务待供包装** |
| P3.3 | 业务确认队列：低置信意图 + open gaps |
| P3.4 | 导出 MP4/PPTX/PDF 门禁与状态机一致 |

---

## 8. Phase 4 — 规模化

| ID | 任务 |
| --- | --- |
| P4.1 | Q10 用户视觉签样 → 商品视频线可批量 |
| P4.2 | 按病种清单批量 gap → 周更 series 成员 |
| P4.3 | 采购清单与设计排期对接（仅 B/C） |
| P4.4 | 评估是否需要新 series（非新风格包） |

---

## 9. 日常作业流（执行手册摘要）

### 9.1 新主题

```text
1. themes.json 增加 theme（默认 style_pack + 规划 series）
2. 业务交审核 Word；包装/Logo 附件或标「后补」
3. plan_training_course → scenes + asset_gap_tasks
4. 拆分 gap：
   - teaching illustration → B/C/自研
   - packshot/logo/evidence → awaiting-business-asset
5. 教学图走 _intake → 适配 → candidates → 审核 → master
6. 业务包装到位 → 抠图规范 → company_authorized 成员
7. 预览确认 → 导出 → 回写
```

### 9.2 通道决策树

```text
是否真包装/Logo/证据？
  是 → 通道 A，等待业务（制作不外购替代品）
  否 → 是否已有 series 成员可复用？
         是 → 直接匹配
         否 → 现有 series 画风能否表达？
                是 → 补成员（B 适配或 C 再生）
                否 → 新系列代表图签样（升级决策）
```

---

## 10. 角色分工

| 角色 | 职责 |
| --- | --- |
| 业务/培训 | 审核脚本、真包装与证据、确认异常分镜 |
| 制作/设计 | series 成员、B/C 外补适配、签样 |
| 工程 | plan/gap/registry/渲染门禁 |
| 药师/合规 | 医学与话术；插图医学轨 |
| 采购（可选） | 仅通道 B 商用素材包，不含商品包装 |

---

## 11. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| 等包装阻塞整片 | 教学镜头先用系列插画预览；包装页显式占位 |
| 外补画风漂移 | series tokens 强制；代表图签样 |
| 主题登记过快、成员跟不上 | 主题可先 selected；批量生产门禁看成员与包装 |
| 参考图误入 master | intake 隔离 + provenance 校验 |

---

## 12. 本轮（Phase 0）交付清单

- [x] 执行计划本文  
- [x] 四主题登记（含金银花露）  
- [x] gap schema / intake / worklist  
- [x] symptom + herb series 回填  
- [x] medications/advice/真包装分轨 series（真包装成员空，等业务）  
- [x] plan gap 字段增强（业务待供 vs 制作可填）  
- [x] catalog 挂接  

**Phase 0 完成。** 下一执行波次：Phase 1 试点（通道 B 图标 + 通道 C 再生；包装仍等业务）。
