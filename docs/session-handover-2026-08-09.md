# 会话交接 · 2026-08-09（收工 → 明日续）

**读者：** 明日继续的工程师 / 代理  
**Private main：** 以远端 `origin/main` 当前提交为准（本页提交号仅是历史快照，不作为运行真值）
**进度清单：** `tasks/todo.md` 顶部「进度快照」

> **业务验收补记（同日，覆盖本文件的旧状态）：** 构件化 PPT 仍是默认通用路线；金银花绿色固定课型、穿心莲疾病-商品-场景固定课型、速福达课件3 PPT 固定课型现均为 active 并可通过 WorkBuddy 真实生成。此前“绿色五页下线”的决定已被本次验收决定取代。速福达课件3 MP4 仍未上线，不得承诺。

---

## 1. 今天做到哪了

### 当时已合入 main（历史背景）

1. **P1/P2 业务主线（PR #4）**
   - `business_job` 统一任务：draft → approve → render → 白名单交付
   - 默认 PPT：`product-pptx-component-v1`（构件 + recipe + `generate_courseware.py`）
   - 绿色五页当时为下线状态；该状态已被页首业务验收补记取代，当前以 `business-routes.json` 为准
   - profiles / doctor / bootstrap soft-repair / on-demand packages / clean-clone 测试

2. **商品正式视频环境工具（`e0f06dd`）**
   - `scripts/video_full_env.py`：`check | soft-repair | package | restore`
   - 文档：`docs/video-full-env-package.md`
   - doctor `--profile video-full` 会挂上该检查摘要

### 工程师侧已验证

| 项 | 结果 |
|----|------|
| 构件 PPT 任务冒烟 | `p2-smoke-component-pptx` → delivered，~10MB，无金样残留 |
| P1 / P2 / clean-clone 测试 | 通过（合入前） |
| `validate_production_readiness` | PASS |
| `video_full_env.py check`（开发机） | video_full=true |

### 当时明确未做（历史计划）

| 专项 | 内容 | 说明 |
|------|------|------|
| **A. 业务验 PPT** | 已进入验收，并据此恢复/补齐三条固定 PPT 课型 | 当前状态见页首补记与事实源 |
| **B. 健康视频自助** | 疾病/健康科普 **MP4** 业务开放 | 不是商品 PPT；路线现仍 `active=false` |

---

## 2. 当前事实源（别写歪）

| 用途 | 路径 |
|------|------|
| 业务路线 | `production-library/business-routes.json` |
| 运行时 profile | `production-library/runtime-profiles.json` |
| 货架 | `production-library/templates/settled/business-catalog.json` |
| 默认 PPT 引擎 | `production-library/engines/courseware-pptx-v1/` |
| PPT 生成器 | `scripts/generate_courseware.py` |
| 任务编排 | `scripts/business_job.py` |
| 视频 kit 解析 | `scripts/video_runtime.py` |
| 视频环境包 | `scripts/video_full_env.py` |
| 代理说明 | `AGENTS.md` |

**Active 路线（业务可 new）：**

- `product-pptx-component-v1` — 可编辑 PPT（默认）
- `product-pptx-green-v1` — 金银花绿色固定课型可编辑 PPT
- `product-pptx-disease-scenario-v1` — 穿心莲疾病-商品-场景固定课型可编辑 PPT
- `courseware3-pptx-v1` — 速福达课件3固定课型可编辑 PPT
- `product-mp4-full-v1` — 商品完整 MP4（需 content + product_image 审批 + video_full 环境）

**Inactive：**

- `health-mp4-full-v1`（健康视频，专项 B）
- `courseware3-mp4-v1`（速福达课件3 MP4；PPTX 上线不代表视频上线）
- 其他门户明确标为未接线的路线

---

## 3. 业务验 PPT（专项 A）· 验收目标

**一句话：** 业务不用工程师，按同一条完整流程交付默认通用 PPT 或三种固定标准 PPT。

**业务使用说明 + 完整测试案例（含记录表）：**  
→ **`docs/business-usage-and-test-cases.md`**

放行：默认构件路线通过 **TC-PPT-01～05、07、08**；三条固定课型另通过 **TC-FIXED-01～03**。

| # | 检查 | 通过标准 |
|---|------|----------|
| 1 | 选对课型 | 通用需求默认选「构件化商品培训 PPT」；明确要金银花绿色、穿心莲疾病-商品-场景或速福达课件3时，选择对应 active 固定课型 |
| 2 | 交内容 | 商品名 + 若干要点可出草稿；有完整 `script.structured.json` 更好 |
| 3 | 审稿 | 能看懂初稿/缺口；确认前**不**生成终稿，不要求业务编辑内部 JSON/CLI |
| 4 | 补图审批 | 业务给授权包装/Logo/证据；WorkBuddy 生成/绑定非商品插图并验代表图，完成 content + product_image + visual 三道确认 |
| 5 | 出片与 QA | `终稿.pptx` 可打开、文字可编辑、文案是自己的；逐页 QA 通过 |
| 6 | 取件与安全 | 只在 QA 通过后进入 `05_交付物放这里/<job_id>/`；无金样残留、无伪造包装、无技术垃圾目录 |

建议命令见业务文档 §1.4；业务侧优先用 WorkBuddy 口语（§1.2）。

---

## 4. 健康视频自助（专项 B）· 边界

- **是：** 店员内部「疾病/健康知识」讲解 **MP4**（金样如风热证参考技术片）
- **不是：** 商品构件 PPT；也不是立刻做新模板扩库
- **开放前至少要有：**
  1. 主题包 + 内容/画面审批哈希（已有健康 full 闸门设计）
  2. 本机 `video_full`（TTS + kit + ffmpeg）— 基建已有 `video_full_env`
  3. `business-routes.json` 里 `health-mp4-full-v1` 验证后 `active=true`
  4. 门户货架文案与「仅金样」状态同步

实施时先读：`scripts/business_video_health_full.py`、健康模板 settled 目录、现有 `--theme-package` 纪律。

---

## 5. 后续继续建议顺序

1. `git pull` Private `main`，确认 `e0f06dd` 或更新  
2. 读本文件 + `tasks/todo.md` 进度快照  
3. PPT 验收继续覆盖默认构件与三条 fixed route；视频专项另开 scope，尤其不得把课件3 PPT 验收扩写为课件3 MP4 已上线
4. 勿把工作区未跟踪的动画 POC / gold-sample 实验塞进业务 PR  

---

## 6. 已知残余（非阻塞明日专项，但别忘）

- 视频 kit 仍可 symlink `poc/gold-sample`（可用 `video_full_env package/restore` 做离线包）
- 门户能力状态必须从 active routes 派生；固定课型不能再标为“下线/仅金样”
- P3（统一 G0–G4 CI / 度量）未开
- Public 安装器仍无生产能力（设计如此）

---

## 7. 不要做的事

- 不要把金银花、穿心莲、速福达固定 PPT 再标成“下线/仅预览”；它们与默认构件路线并列上线，但构件路线仍是通用默认
- 不要把速福达课件3 PPT 的成功扩大成 MP4 已上线
- 不要静默把健康视频标成已自助
- 不要系统 TTS 冒充正式旁白
- 不要在未审批时把产物写进 `05_交付物放这里`
