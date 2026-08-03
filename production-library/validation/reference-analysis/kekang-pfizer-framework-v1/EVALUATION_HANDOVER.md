# 可可康绿色培训视频 · 完整评价交接文档

> **用途**：交给其他模型独立评价当前实现是否符合合同、是否仍是「一章一页 PPT」、技术 QA 是否可信、下一步是否可继续。  
> **日期**：2026-08-01  
> **工作区**：`/Users/liminrong/Projects/chain-pharmacy-content-studio`  
> **评价范围**：阶段 A（K08 有声）+ 阶段 B 结构 animatic（58 微镜头 production-v2）。**不是**完整有声金样，**不是**可批量模板。

---

## 0. 一句话结论（制作侧自述）

1. **K08 有声片段**（约 7.93s）已做出：药师克隆旁白 + 字幕 + 同步音效 + 混音 QA；用户以「继续」推进后续。  
2. **第一版 M2 结构 animatic（production-v1）被用户否决**——实质是「章节页 + 空槽卡片」，已**删除**。  
3. **第二版 M2** 按 `handoff-v2` 合同重做：宣称实现 **58 个微镜头** 的静音结构 animatic，产物在 `production-v2/`。  
4. **内容与授权门禁仍未齐**：不得宣称完整金样完成；55/58 微镜头不可写正式医学旁白；包装/Logo 禁止仿造。

**评价模型请勿采信聊天记忆，只信本文件路径 + 本地文件 + 命令输出。**

---

## 1. 评价前必读文件（按顺序）

| 顺序 | 路径 | 为什么读 |
|---:|---|---|
| 1 | `AGENTS.md`（若存在） | 项目总规则 |
| 2 | `skills/pharmacy-template-replication/SKILL.md` | 金样优先、禁止仿包装 |
| 3 | `handoff-v2/EXECUTION_PROMPT.md` | **执行合同唯一指令** |
| 4 | `handoff-v2/README.md` | 微镜头强约束说明 |
| 5 | `handoff-v2/scene-recipes.md` | R01–R10 动态构图合同 |
| 6 | `handoff-v2/microshot-timeline.json` | 58 微镜头权威时码与图层合同 |
| 7 | `handoff-v2/asset-manifest.json` | 素材权限（候选 / 待授权 / 禁止） |
| 8 | `handoff-v2/narration-audio-plan.md` | 旁白审核状态与音效事件 |
| 9 | 本文 `EVALUATION_HANDOVER.md` | 实现对照与已知缺口 |
| 10 | `production-v2/qa/qa-report.json` | 结构片技术 QA 摘要 |
| 11 | `production-v1/.../qa/k08/qa-report.json` | K08 有声 QA 摘要 |

### 开工校验命令（合同要求）

```bash
cd /Users/liminrong/Projects/chain-pharmacy-content-studio
python3 production-library/validation/reference-analysis/kekang-pfizer-framework-v1/handoff-v2/build_handoff_v2.py
python3 production-library/validation/reference-analysis/kekang-pfizer-framework-v1/handoff-v2/validate_handoff_v2.py
```

**最近一次校验结果（以磁盘 `handoff-v2/validation-report.json` 为准）：**

- `passed: true`
- `error_count: 0`
- `warning_count: 8`（均为 business-authorized 资产等待）
- `microshot_count: 58`
- `total_duration_seconds`（合同汇总）：**238.5**（见下文「时长偏差」）

---

## 2. 项目绑定与目录地图

### 2.1 绑定

```json
{
  "project_id": "validation.kekang-green-gold-sample-v1",
  "theme_id": "theme.product.kekang-lingzhi-capsule",
  "style_pack_id": "style-pack.kekang-pfizer-green-candidate-v1",
  "style_pack_status": "validation-candidate-not-registered",
  "voice_id": "voice.reference-pharmacist-qwen-v1",
  "chapter_is_not_page": true
}
```

### 2.2 权威目录

```text
production-library/validation/reference-analysis/kekang-pfizer-framework-v1/
├── handoff-v2/                          # 合同源：时间线 / recipe / 资产 / 旁白计划 / 校验
├── EVALUATION_HANDOVER.md               # 本文件
├── OTHER_MODEL_PRODUCTION_PLAN.md       # 较早交接（v1 计划；以 handoff-v2 为准）
├── production-v1/                       # K08 有声试点产物
│   ├── renders/k08-audiovisual-v2.mp4
│   ├── audio/                           # 旁白 / 音效 / 混音 / SRT
│   ├── qa/k08/
│   └── review.html
└── production-v2/                       # 58 微镜头结构 animatic 产物
    ├── renders/kekang-green-microshot-animatic-v2.mp4
    ├── qa/frames/<Kxx-Syy>/{entry,performance,exit}.png
    ├── qa/contact-sheets/K01..K18-contact.png
    ├── qa/qa-report.json
    ├── review.html
    ├── review-data.js
    ├── project-lock.json
    └── src/                             # 实现副本 + timeline
```

### 2.3 可运行源工程（Revideo）

| 角色 | 路径 |
|---|---|
| 主实现 | `poc/gold-sample/src/kekang-pfizer-v2-animatic-project.tsx` |
| 主题/标签工具 | `poc/gold-sample/src/kekang-v2/{theme,types,labels}.ts` |
| 内嵌合同副本 | `poc/gold-sample/src/kekang-v2/microshot-timeline.json` |
| 渲染入口 | `poc/gold-sample/src/render-kekang-pfizer-v2-animatic.ts` |
| npm 脚本 | `poc/gold-sample` → `npm run render:kekang-pfizer:v2-animatic` |
| K08 有声实现 | `poc/gold-sample/src/kekang-pfizer-k08-audiovisual-project.tsx` |
| K08 渲染 | `npm run render:kekang-pfizer:k08-audiovisual` |
| TTS 混音 | `scripts/generate_kekang_k08_audiovisual_audio.py`（venv：`.venv-qwen-tts`） |

### 2.4 审片入口

| 入口 | 路径 |
|---|---|
| v2 专属审片 | `production-v2/review.html` |
| 统一门户 | `production-library/validation/review-hub.html` → Tab「可可康·视频」 |
| K08 有声 | `production-v1/renders/k08-audiovisual-v2.mp4` |

---

## 3. 合同要求（评价标尺）

摘自 `handoff-v2/EXECUTION_PROMPT.md`，评价时逐项打分。

### 3.1 必须满足

1. **章节不是页面**：K01–K18 只组织内容；最小单位是微镜头 `Kxx-Syy`。  
2. **58 微镜头**按 `microshot-timeline.json` **顺序与时长**实现，不得擅自合并/删除/重排。  
3. 每镜有 **entry / performance / exit**；`animated_nontext_layers` 至少一个非文字层真实运动。  
4. 遵守 `transition_to` 承接；禁止统一整页黑/白场或整页卡片切换。  
5. 同一时刻一个主运动焦点；字幕不计入非文字动画层。  
6. 禁止：一章一个全屏组件只换文案；18 张设计稿淡入淡出；PPT 截图主体；Ken Burns 代替主体运动。  
7. 未审核医学内容不得做正式旁白/机制/疗效；不得仿造包装/Logo。  
8. 结构阶段允许静音 animatic + 清晰占位；**production_ready=true** 才允许正式旁白（当前仅 K08 三镜）。  
9. 产物只进 `production-v2/`（及既有 K08 的 `production-v1/`）；不得进 `templates/settled/`。

### 3.2 完成定义（合同原文摘要）

- `validate_handoff_v2.py` 通过  
- 58 微镜头存在，顺序/时长/`transition_to` 一致  
- 每镜非文字运动 + 入场/表演/退场  
- 逐镜三帧 + 全片接触表能证明**不是**一章一页  
- 视频可解码、无黑场、无冻结/溢出  
- K08 ASR/字幕权威词「灵芝多糖、灵芝三萜」  
- 声音指标合格（有声阶段）  
- 未审核内容阻断、未授权品牌资产未仿造  
- `review.html` 可播放并按微镜头定位  

---

## 4. 交付物清单与事实数据

### 4.1 阶段 A · K08 有声（production-v1）

| 项 | 值 |
|---|---|
| 文件 | `production-v1/renders/k08-audiovisual-v2.mp4` |
| 时长 | **7.933333 s** |
| 规格 | 1920×1080 · 30fps · H.264 + AAC |
| 旁白 | `voice.reference-pharmacist-qwen-v1`，整段连读，tempo **1.16×**（≤1.18） |
| 文案 | 「从灵芝主体，可以认识两类成分：灵芝多糖和灵芝三萜。」 |
| 音效 | whoosh / 路径扫过 / 标签点音 / 聚焦脉冲 / 环境底音（程序生成） |
| 混音 | 约 **-16.1 LUFS**，True Peak 约 **-5.3 dBFS** |
| 字幕 | SRT/VTT，深绿底白字 |
| ASR | large-v3-turbo + 域提示：识别「灵芝多糖」；「三萜」同音「三贴」（已知专业词问题） |
| 状态 | 用户「继续」后进入后续；style_pack **未注册** |

相关：

- `production-v1/qa/k08/qa-report.json`
- `production-v1/audio/k08-mix-final.wav`、`narration/`、`sfx/`
- `production-v1/audio/k08-subtitles.srt`

### 4.2 阶段 B · 58 微镜头结构 animatic（production-v2）

| 项 | 值 |
|---|---|
| 文件 | `production-v2/renders/kekang-green-microshot-animatic-v2.mp4` |
| 成片时长 | **193.333333 s** |
| 合同时长（当前 timeline 汇总） | **238.5 s** |
| 目标窗（handoff 全局） | 175–215 s（见「已知问题」） |
| 规格 | 1920×1080 · 30fps · H.264 + AAC |
| 音频模式 | **静音结构**（silence bed）；非正式旁白 |
| 微镜头数 | **58**（K01-S01 … K18-S04） |
| production_ready | **3**（K08-S01/S02/S03） |
| blocked | **55** |
| 解码 | 完整解码通过 |
| 黑场 | `blackdetect` 未检出持续黑场 |
| QA 帧 | **174** = 58 × (entry/performance/exit) |
| 接触表 | **18** 章 `qa/contact-sheets/Kxx-contact.png` |

### 4.3 Recipe 使用分布（合同）

| Recipe | 数量 | 用途摘要 |
|---|---:|---|
| R03 multi_node_focus | 14 | 多节点依次聚焦 |
| R05 pathway_explain | 8 | 路径解释 + 审核锁 |
| R02 life_context_sequence | 7 | 生活情境人物 |
| R06 evidence_zoom | 7 | 证据/空槽放大 |
| R08 product_pair_relation | 7 | 联合方案双空槽 |
| R01 hero_reveal | 3 | 主体揭示 |
| R04 central_split_orbit | 3 | K08 双路径 |
| R07 process_conveyor | 3 | 工艺 token |
| R09 calendar_progression | 3 | 月历 |
| R10 summary_convergence | 3 | 六维收束 |

### 4.4 已删除（用户否决）

下列**不得再被评价为当前基线**：

- `production-v1/renders/kekang-green-animatic-v1.mp4`（及 visuals/audio 中间件）
- `production-v1/qa/full/`
- `poc/gold-sample/src/kekang-pfizer-full-animatic-project.tsx`
- `poc/gold-sample/kekang-full-animatic-v1.json`

否决原因（用户原意）：一章一张结构页、空槽卡片堆叠，**不符合**微镜头连续视频合同。

---

## 5. 实现架构（供代码审查）

### 5.1 引擎思路

- 单一 Revideo `makeScene2D` 循环 58 个微镜头。  
- 图层池复用：背景、灵芝主体、人物三图、路径 A/B/弧、工艺 path+token、节点卡×6、月历×3、商品空槽 A/B、证据框、审核锁、字幕条、进度条。  
- 按 `recipe_id` 分支执行 entry / performance / exit 动画。  
- 门禁芯片：`READY` / `MEDICAL` / `EVIDENCE` / `HIGH-RISK` / `REVIEW` 等，来自 `content_approval` 与 `production_ready`。  
- 包装：`heroSlot` 虚线空槽文案「授权包装空槽」，**不加载仿包装图**。  
- 人物：仅用已有 candidate 插画（失眠/饮酒/免疫），年龄只作画面覆盖。

### 5.2 时码策略（实现）

每镜时长 `d = duration_seconds`：

- entry ≈ 28% `d`  
- performance ≈ 48% `d`  
- exit ≈ 24% `d`  

chrome（标题/字幕/门禁）与 recipe 入场尽量并行，避免「先 chrome 再整段 recipe」叠时间。

### 5.3 重渲染命令

```bash
cd /Users/liminrong/Projects/chain-pharmacy-content-studio/poc/gold-sample
npm run typecheck
npm run render:kekang-pfizer:v2-animatic
# 输出：
# ../production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/renders/kekang-green-microshot-animatic-v2.mp4
```

K08 有声：

```bash
# 旁白（需 .venv-qwen-tts）
.venv-qwen-tts/bin/python scripts/generate_kekang_k08_audiovisual_audio.py
npm run render:kekang-pfizer:k08-audiovisual
```

### 5.4 技术验收命令

```bash
V2=production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/renders/kekang-green-microshot-animatic-v2.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$V2"
ffmpeg -v error -i "$V2" -f null -
ffmpeg -v info -i "$V2" -vf "blackdetect=d=0.25:pix_th=0.10" -an -f null - 2>&1 | rg -i black_start || echo NO_BLACK

K08=production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v1/renders/k08-audiovisual-v2.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name -of default=nw=1 "$K08"
```

---

## 6. 已知问题与诚实缺口（评价重点）

### 6.1 时长偏差（高优先级）

| 来源 | 秒数 |
|---|---:|
| 当前 `microshot-timeline.json` 合同合计 | **238.5** |
| 成片实测 | **193.3** |
| 全局目标窗（handoff global_constraints） | **175–215** |

说明：

- 实现与渲染时，内嵌/使用的 timeline 曾为约 **186.8s** 一版；合同后来经 `build_handoff_v2.py` 更新为 **238.5s**。  
- 成片 **短于当前合同**，却落在旧目标窗内。  
- **评价模型应判定：是否算「严格按合同时长」失败。** 制作侧自认：**未与最新 238.5s 合同逐镜锁死**，需重对齐后重渲。

### 6.2 「一章一页」风险（高优先级）

尽管使用了 58 个 ID 与 recipe 分支，实现仍是：

- **单场景大循环 + 共享图层池**，不是 58 个独立微镜头模块文件；  
- 部分镜主要靠「标题/门禁/字幕 + 节点/路径/主体切换」区分，信息密度仍偏「讲解卡」；  
- 部分 performance 帧可能出现主体偏弱、空场或节点已汇聚后的收束态；  
- QA 帧按时间比例抽取，**与合同绝对时码可能有漂移**（因成片≠合同总长）。

评价时应抽样对比：

- 合同 `visual_action` / `entry` / `performance` / `exit`  
- 成片对应时段画面  
- `qa/frames/Kxx-Syy/{entry,performance,exit}.png`

建议至少抽查：

- `K01-S01` `K01-S02` `K01-S03`（章内三镜是否不同运动）  
- `K03-S01`～`K03-S03`（生活情境是否连续而非一页）  
- `K08-S01`～`K08-S03`（双路径是否逐步完成）  
- `K13-S01`～`K13-S03`（token 是否沿工艺轴移动）  
- `K16-S01`～`K16-S06`（联合方案是否分段而非一屏三卡）  
- `K18-S01`～`K18-S04`（收束是否分镜）

### 6.3 转场连续性

合同要求 `transition_to` 主体/路径/颜色承接。实现有部分位置继承（如 hero 右移），但**未逐镜形式化验证**承接质量。评价时检查相邻镜是否「硬切成新卡片」。

### 6.4 声音

- 结构 animatic：**静音**，符合「未批准不写正式旁白」。  
- 合同中的 `sfx_events` **未逐事件绑定进 v2 成片**（K08 有声片有独立音效系统）。  
- 评价时勿要求 v2 静音片具备完整旁白，除非进入审核后阶段。

### 6.5 素材

- 可用 candidate：灵芝 hero、三类人物、睡眠插画、Logo candidate（仅 animatic）。  
- **禁止/缺失**：真包装、联合商品包装、工厂、产地证据、说明书——用空槽/锁定标，未 AI 仿包装。  
- `asset-manifest` 中 `generate-one-then-review` 场景插画**多数未单独生成定稿**，生活镜主要复用 v7 人物图。

### 6.6 工程结构 vs 合同推荐结构

合同推荐：

```text
production-v2/src/microshots/K01-S01...  recipes/R01...
```

实际：

- 逻辑集中在 **一个大 TSX**；  
- `production-v2/src/microshots/`、`recipes/` 目录存在但**未拆成每镜一文件**。  

评价：是否算「架构合同未满足」——制作侧自认**部分满足功能、未满足推荐目录粒度**。

### 6.7 K08 有声 vs K08 三微镜头合同

- 有声片是 **连续 7.9s 单场景**，语义对齐多糖/三萜。  
- 合同将 K08 拆为 **S01/S02/S03** 三镜。  
- v2 animatic 中有 K08 三镜结构表现，但**有声片并未按三文件微镜头工程拆分重渲**。  
- 评价：K08 有声是否算「与三微镜头合同对齐」——语义对齐有、工程拆分不足。

---

## 7. 门禁状态（停止条件）

| 门禁 | 状态 | 说明 |
|---|---|---|
| K08 运动/声音方向 | 用户「继续」 | 可作后续声音语法参考 |
| 逐镜审核确认表签字 | **BLOCKED** | `可可康绿色视频金样_逐镜内容审核确认表_v1.docx` 业务未回填终稿 |
| 说明书/批准信息 | **BLOCKED** | 功能主治/周期 |
| 真包装授权 | **BLOCKED** | 禁止仿造 |
| 联合方案包装 | **BLOCKED** | K15–K16 |
| Logo/工厂/GMP | **BLOCKED** | 封底与特点三 |
| 卖点证据 | **BLOCKED** | 9.13g/100g、工艺等 |
| 正式 style_pack 登记 | **禁止** | 完整金样用户批准前 |
| 批量扩展主题 | **禁止** | 同上 |

---

## 8. 评价检查清单（请其他模型按此输出）

请用以下格式输出评价，避免空泛好评/差评。

### A. 合同符合性

| # | 检查项 | 通过/失败/部分 | 证据路径或时间点 |
|---:|---|---|---|
| A1 | 非一章一页 |  |  |
| A2 | 58 微镜头齐全且顺序正确 |  |  |
| A3 | 每镜 entry/performance/exit 可辨 |  |  |
| A4 | 非文字层真实运动 |  |  |
| A5 | transition_to 承接 |  |  |
| A6 | 时长与合同一致 |  | 合同 238.5 vs 成片 193.3 |
| A7 | 未仿包装/未写未审医学结论 |  |  |
| A8 | 静音结构策略合理 |  |  |
| A9 | validate_handoff 通过 |  |  |
| A10 | review.html 可审可定位 |  |  |

### B. 质量

| # | 检查项 | 分数 1–5 | 说明 |
|---:|---|---:|---|
| B1 | 绿色视觉统一 |  |  |
| B2 | 信息密度/可读性 |  |  |
| B3 | 动画是否摆脱 PPT 感 |  |  |
| B4 | 人物/情境镜可信度 |  |  |
| B5 | K08 有声质量 |  |  |
| B6 | QA 帧与成片一致性 |  |  |

### C. 风险与建议

1. **必须立即修**（阻塞交付）  
2. **应当修**（质量/合同偏差）  
3. **可接受并进入下一阶段的条件**  
4. **明确禁止的下一步**（例如：在审核表未齐时生成正式联合用药旁白）

### D. 总判

三选一：

- `REJECT`：仍属章节页/严重违约，需推倒重来  
- `CONDITIONAL`：方向正确，列出必须修补项后再进 M3  
- `ACCEPT-STRUCTURE`：结构阶段可接受，仅待内容门禁  

---

## 9. 建议评价流程（可复制）

```text
你是独立评审模型。工作区：
/Users/liminrong/Projects/chain-pharmacy-content-studio

1. 阅读 handoff-v2/EXECUTION_PROMPT.md 与 microshot-timeline.json。
2. 运行 validate_handoff_v2.py，记录 error/warning。
3. 播放 production-v2/renders/kekang-green-microshot-animatic-v2.mp4 全片或抽检 ≥12 个微镜头。
4. 对照 qa/frames 与 contact-sheets，判断是否一章一页。
5. 检查 K08 有声 production-v1/renders/k08-audiovisual-v2.mp4。
6. 阅读 EVALUATION_HANDOVER.md §6 已知问题，确认是否仍存在。
7. 按 §8 检查清单输出：A 表 + B 表 + C 建议 + D 总判。
8. 禁止因「文件很多」给通过；禁止忽略时长偏差与工程未按微镜头拆分。
```

---

## 10. 制作侧自评分（供对照，非结论）

| 维度 | 自评分 | 备注 |
|---|---:|---|
| 删除错误方向 | 5/5 | 旧 animatic 已删 |
| 合同可读/可校验 | 5/5 | handoff-v2 完整 |
| 微镜头数量与 ID | 4/5 | 58 个 ID 有；时长未对齐最新合同 |
| 反 PPT 结构 | 2.5/5 | 有分支运动，仍偏讲解卡 |
| 分层运动真实性 | 3/5 | 有路径/token/人物；部分镜弱 |
| 转场承接 | 2.5/5 | 未系统验证 |
| 医学/资产合规 | 5/5 | 空槽+门禁，无仿包装 |
| K08 有声 | 4/5 | 技术达标；ASR 三萜同音 |
| 文档与可复现 | 4/5 | 有审片页与脚本 |
| **综合（结构阶段）** | **3/5** | 建议 CONDITIONAL，先锁时长与抽检失败镜 |

---

## 11. 下一步（业务 / 制作）

### 业务必须提供

1. 填写并回传逐镜审核确认表（保留/改写/删除 + 终稿）。  
2. 真包装、联合商品包装、说明书、Logo、工厂/GMP、含量与工艺证据及授权范围。  

### 制作在评价通过后

1. **对齐最新 `microshot-timeline.json` 时长（238.5s 或重新 build 锁定）并重渲**。  
2. 对评价点名的失败微镜头做定向运动加强（仍禁止补医学结论）。  
3. 门禁齐后：按镜正式旁白（仅 approved）+ 音效事件 + 授权素材替换；**不改**已确认运动结构除非改合同重校验。  
4. 完整金样用户批准前：不登记 `style_pack`，不批量扩主题。  

---

## 12. 关键哈希与复现备忘（可选命令）

```bash
shasum -a 256 \
  production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/renders/kekang-green-microshot-animatic-v2.mp4 \
  production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v1/renders/k08-audiovisual-v2.mp4 \
  production-library/validation/reference-analysis/kekang-pfizer-framework-v1/handoff-v2/microshot-timeline.json
```

（哈希随重渲变化；评价时以当前磁盘文件为准。）

---

## 13. 联系本交接的决策记录

| 决策 | 状态 |
|---|---|
| 金样优先，不先堆组件 | 遵守中 |
| 绿色候选 style_pack 未注册 | 遵守 |
| 旧 v4/v7 不作当前基线 | 遵守 |
| 否决 production-v1 章节页 animatic | 已删除 |
| 以 handoff-v2 微镜头合同为权威 | 执行中（时长待重对齐） |
| 正式旁白依赖审核表 | 阻断中 |

---

**文档结束。** 评价模型请直接输出 §8 清单结果；制作侧将按 `REJECT` / `CONDITIONAL` / `ACCEPT-STRUCTURE` 执行下一步，不围绕模糊意见返工。
