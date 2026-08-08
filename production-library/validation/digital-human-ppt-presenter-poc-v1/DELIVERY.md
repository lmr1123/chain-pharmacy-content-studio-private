# 讲解安全版 PPT · 企业交付说明

**状态：** 已由金样生成器产出（非 PIL mock）  
**样式：** 与 `disease-health-shenke-blue-v1` 全宽金样同源（色板 C、字阶 T、chrome、卡片、投影）  
**差异：** 仅页内内容栏右边界收至约 60% 画幅，右侧同页留白供数字人叠层  

## 交付物

| 文件 | 说明 |
|------|------|
| `templates/settled/disease-health-shenke-blue-v1/急性上呼吸道感染_疾病健康知识培训_讲解安全版_v1.pptx` | **企业可编辑 PPTX（讲解安全版）** |
| 同目录 `generator/` 下同名文件 | 构建输出源 |
| `outputs/qa-presenter-v1/slide-*.png` | 18 页 QA 静帧 |
| `outputs/enterprise-page03-presenter-slide-only.png` | 第 3 页（疾病概览）仅课件 |
| `outputs/enterprise-page03-presenter-composite.png` | 第 3 页 + **站姿中国药师**去底叠层（非用户托腮证件照） |
| `inputs/portrait-pharmacist-standing-v1.jpg` | 讲解 IP 源图（站姿、双手自然、白大褂） |
| `inputs/portrait-pharmacist-standing-v1-cutout.png` | 去底版，供合成 / HeyGen 参考 |

全宽金样 **未覆盖**：`…可编辑金样_v3.pptx` 仍为纯课件下发版。

## 如何重新构建

```bash
cd production-library/templates/settled/disease-health-shenke-blue-v1/generator
node build-editable.mjs --presenter
# → 急性上呼吸道感染_疾病健康知识培训_讲解安全版_v1.pptx
```

全宽金样（默认）：

```bash
node build-editable.mjs
# → …可编辑金样_v3.pptx
```

## 实现要点（B 路径）

1. `build-editable.mjs` 增加 `L` 布局与 `--presenter` 开关  
2. **同一套** `C` / `T` / `addShenkeChrome` / 卡片阴影 / 字号  
3. 内容区 `L.x1 = 8.05"`（约 60% @ 13.333" 宽）  
4. 原右侧插图/包装栏：移入内容栏或竖排，**不进站人区**  
5. 封面/目录/outro 保持品牌全幅（通常不叠讲解人）  

## 数字人用量策略（2026-08-08 用户锁定 · 方案 C · 可复用其他课件）

> **完整产品定义见 `PRODUCT-MODE-presenter-scheme-C.md`。**

> **只关键页 / 开场用动态数字人（HeyGen 口型）。**  
> **非关键页 = 全宽 PPT 放大课件内容，不叠数字人（含静帧站人也不要）。**  
> 布局从 generator PPT 比例改起（全宽 vs 讲解安全版双布局），禁止后期强行拉升画面。  
> 不替换 MG 金样视频；不默认 10 分钟全程动口型。

### 建议动口型页（急性上呼 18 页 · 可调）

| 类型 | 建议页 | 说明 |
|------|--------|------|
| 开场 | 封面后或第 1 内容页（如目录后「疾病概览」） | 建立药师 IP 信任感 |
| 关键知识 | 「疾病概览」「临床表现」等 1～2 页 | 信息密度高、适合真人感讲解 |
| 收尾（可选） | 总结 / 专业关怀 1 页 | 强化记忆；可省 |

**默认预算目标：** 动态数字人合计 **约 1～3 分钟**（非全程 10 分钟）。  
非关键页：全宽金样静帧 + 该页旁白（无站人）。

### 费用粗算（HeyGen，按秒）

| 范围 | 动态数字人时长 | 约费用（Avatar III～IV） |
|------|----------------|--------------------------|
| 仅 15s 样片 | ~12s | **$0.2～$0.6** |
| 方案 C 默认（1～3 分钟） | 1～3 min | **$1～$9** |
| 若改全程 10 分钟 | ~10 min | **$10～$30**（已否决为默认） |

本机旁白全程 **$0**。

### 制作流水线（方案 C）

```text
1. 定关键页清单
2. Generator 双布局：关键页 --presenter（收窄）；非关键页全宽金样
3. 本机 Qwen：每页旁白 wav
4. 仅关键页：HeyGen 图+音频 → rembg → v6.2 固定 scale 叠讲解安全版
5. 非关键页：全宽静帧 + 旁白（无人）
6. 按页拼接 → 成片 MP4
```

**硬规则：** 动态片段只用上传音频驱动口型；禁止 HeyGen 再 TTS 覆盖；禁止非关键页静帧站人；禁止成片阶段 stretch 改构图；**全课旁白同一 voice pack**（`reference-pharmacist-qwen-v1`），禁止 edge-tts 与数字人轨混用。

**模式入库：** 见仓库 `docs/digital-human-presenter-mode.md` 与本目录 `PRODUCT-MODE-presenter-scheme-C.md`。其他课件走真人数字人侧讲时按该文档 §4 二次调整。

## 验收

- [x] 由 generator 产出，非手绘 mock  
- [x] 第 3 页样式为参课蓝 chrome + 引用卡 + 病因卡  
- [x] 内容不越过约 60% 线  
- [x] 站姿药师 IP（非托腮证件照）  
- [x] 人像 **rembg 去底**，叠 PPT 无白底色块遮挡  
- [x] **用量策略 = 方案 C**（关键页动态 / 其余静帧）  
- [ ] 业务确认 18 页密度/可读性  
- [ ] 业务确认「哪些页算关键页」清单  
- [ ] 网页/API 出 15s 样片  
- [ ] 方案 C 拼片 POC（1 动态 + 1 静帧）  

**进度快照：** 2026-08-07 · 交 **Codex · API 模式**。  
- 已齐：讲解安全版 PPTX、方案 C、去底药师、15s 旁白、`scripts/heygen_15s_sample.py`  
- **网页下载需付费 → 默认改 API**；待用户提供 `HEYGEN_API_KEY` 后出 `outputs/sample-15s.mp4`  
- 详见：`HANDOVER-for-codex.md`、`work/job-state.json`  
