# 会话交接 · 2026-08-09（收工 → 明日续）

**读者：** 明日继续的工程师 / 代理  
**Private main：** `e0f06dd`（`lmr1123/chain-pharmacy-content-studio-private`）  
**进度清单：** `tasks/todo.md` 顶部「进度快照」

---

## 1. 今天做到哪了

### 已合入 main

1. **P1/P2 业务主线（PR #4）**
   - `business_job` 统一任务：draft → approve → render → 白名单交付
   - 默认 PPT：`product-pptx-component-v1`（构件 + recipe + `generate_courseware.py`）
   - 绿色五页：`product-pptx-green-v1` **下线**（`active=false`，`retired=true`）
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

### 明确未做（用户指定明日/专项）

| 专项 | 内容 | 说明 |
|------|------|------|
| **A. 业务验 PPT** | 真实业务同事试跑默认 PPT | 不是再写引擎，是人机流程验收 |
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
- `product-mp4-full-v1` — 商品完整 MP4（需 content + product_image 审批 + video_full 环境）

**Inactive：**

- `product-pptx-green-v1`（已下线）
- `health-mp4-full-v1`（健康视频，专项 B）
- `courseware3-pptx-mp4-v1` 等

---

## 3. 业务验 PPT（专项 A）· 验收目标

**一句话：** 业务不用工程师，按五步交一单能用的培训 PPT。

| # | 检查 | 通过标准 |
|---|------|----------|
| 1 | 选对课型 | 选「构件化商品培训 PPT」，不会误走已下线绿色五页 |
| 2 | 交内容 | 商品名 + 若干要点可出草稿；有完整 `script.structured.json` 更好 |
| 3 | 审稿 | 能看懂初稿/缺口；确认前**不**生成终稿 |
| 4 | 出片 | `终稿.pptx` 可打开、页数合理、文案是自己的 |
| 5 | 取件 | `05_交付物放这里/<job_id>/`，无技术垃圾目录 |
| 6 | 安全 | 无其他商品金样残留；无授权包装不伪造包装图 |

建议命令（业务由 WorkBuddy 代跑亦可）：

```bash
python3 scripts/business_job.py new --route product-pptx-component-v1 \
  --theme <真实商品名> --notes $'审核要点…' --auto-draft
python3 scripts/business_job.py approve --job <id> --gate content --by <业务姓名>
python3 scripts/business_job.py render --job <id>
python3 scripts/business_job.py open --job <id>
```

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

## 5. 明日开工建议顺序

1. `git pull` Private `main`，确认 `e0f06dd` 或更新  
2. 读本文件 + `tasks/todo.md` 进度快照  
3. 按用户指定开 **专项 A** 或 **专项 B**（不要两线同时扩 scope）  
4. 勿把工作区未跟踪的动画 POC / gold-sample 实验塞进业务 PR  

---

## 6. 已知残余（非阻塞明日专项，但别忘）

- 视频 kit 仍可 symlink `poc/gold-sample`（可用 `video_full_env package/restore` 做离线包）
- 构件模板门户 preview 图仍是占位，不影响出片
- P3（统一 G0–G4 CI / 度量）未开
- Public 安装器仍无生产能力（设计如此）

---

## 7. 不要做的事

- 不要重新打开绿色五页业务入口（除非用户明确回滚）
- 不要静默把健康视频标成已自助
- 不要系统 TTS 冒充正式旁白
- 不要在未审批时把产物写进 `05_交付物放这里`
