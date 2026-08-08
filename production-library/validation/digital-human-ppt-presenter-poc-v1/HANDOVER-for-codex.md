# Handover · PPT + 数字人侧讲 POC → Codex（**API 模式**）

**日期：** 2026-08-07（修订：网页下载需付费 → **改 API**）  
**交接给：** Codex / 下一会话  
**目录根：** `production-library/validation/digital-human-ppt-presenter-poc-v1/`  
**状态：** `work/job-state.json` → `awaiting_heygen_api_key_then_15s_sample`

---

## 一句话

连锁药店培训：**讲解安全版 PPT + 右侧药师**；数字人 **方案 C**（仅开场/关键页动口型，其余静帧+旁白）。  
**不要走 HeyGen 网页下载**（用户反馈生成后下载要付费）。  
**改为 API：** 本机旁白 + 站姿人像 → `scripts/heygen_15s_sample.py` → `outputs/sample-15s.mp4`。  
本机 **尚无** `HEYGEN_API_KEY`，需用户提供后才能出片。

---

## 决策锁定（勿回退）

| 项 | 结论 |
|----|------|
| 产品形态 | PPT 侧讲，**不**替换 MG 金样视频 |
| 构图 | 全屏一张 PPT + **页内内容栏收窄** + 人叠页前右侧（非左右分屏） |
| PPT 产物 | `…/disease-health-shenke-blue-v1/急性上呼吸道感染_疾病健康知识培训_讲解安全版_v1.pptx` |
| 生成命令 | `node build-editable.mjs --presenter`（不覆盖全宽 `…金样_v3.pptx`） |
| 数字人用量 | **方案 C**：动态约 **1～3 分钟**关键页；其余静帧药师+旁白 |
| 样片通道 | **API only**（网页下载路径废弃为默认） |
| 声音 | 本机 Qwen 克隆 `narration-15s.mp3`；**禁止** HeyGen 再 TTS 覆盖 |
| 人像 | 站姿药师 `portrait-pharmacist-standing-v1.jpg`（弃用用户托腮证件照） |

---

## DO

1. 读本文件 + `work/job-state.json` + `DELIVERY.md` + `tasks/todo.md` 顶部专节  
2. **向用户要 `HEYGEN_API_KEY`**（只放环境变量，**禁止写入 git 仓库**）  
3. 确认素材存在后跑：

```bash
export HEYGEN_API_KEY='用户提供的key'   # 勿写入文件/勿 commit

cd production-library/validation/digital-human-ppt-presenter-poc-v1
python3 scripts/heygen_15s_sample.py
```

4. 成功后应有：`outputs/sample-15s.mp4`  
5. 验收：听感=本机旁白；口型/脸可接受  
6. 叠到 `outputs/enterprise-page03-presenter-slide-only.png` 做侧讲预览  
7. 再推进方案 C：关键页清单 + 1 动态 + 1 静帧 concat  
8. 失败不盲目重试（API **按秒扣费**）

## DON'T

1. **不要**引导用户再走网页下载付费路径当默认  
2. **不要**用 script+voice 让 HeyGen 重新配音  
3. **不要**默认渲 10 分钟全程数字人  
4. **不要**覆盖全宽金样 v3  
5. **不要**把 Key 写进代码/文档/commit  
6. **不要**无 Key 时假装已出片  
7. **不要**把数字人并进 MG 风热/商品 full 主线  

---

## 已就绪素材（API 输入）

| 文件 | 用途 |
|------|------|
| `inputs/portrait-pharmacist-standing-v1.jpg` | 上传人像（样片用原图，脸更清） |
| `inputs/portrait-pharmacist-standing-v1-cutout.png` | PPT 叠层用去底（rembg） |
| `inputs/narration-15s.mp3` | 约 **12s** 克隆旁白（驱动口型） |
| `inputs/narration-15s.wav` | 同源 wav |
| `~/Downloads/narration-15s.mp3` | 用户本地副本（网页期用过） |
| `inputs/script.md` | 口播文案（API **不**用文案配音，仅文档） |

旁白文本（若调试需要对照）：

```text
各位同事，我们先看「疾病概览」。急性上呼吸道感染，是鼻腔、咽或喉部急性炎症的概称，也是呼吸道最常见的传染性疾病之一。它全年都可能发生，冬春季节更常见。
```

---

## API 脚本说明

**路径：** `scripts/heygen_15s_sample.py`

**流程：**

```text
上传人像 → 上传 mp3 → Image-to-Video（audio 驱动，非 script+voice）
  → 轮询状态 → 下载 outputs/sample-15s.mp4
  → 更新 work/job-state.json
```

**环境变量（任选其一）：**

- `HEYGEN_API_KEY`（优先）
- `HEYGEN_API_TOKEN` / `HEYGEN_KEY`

**注意：**

- 脚本内对 upload/create 做了多 endpoint 回退（官方文档有迭代）；若全失败，按报错补最新 API  
- 扣费按**实际生成秒数**；样片约 12s → 粗算 **$0.2～$0.6**（Avatar III～IV 档）  
- **网页 Free 配额通常不能直接当 API 余额**；用户需在 [HeyGen API](https://app.heygen.com) / Developer 开通 API 并有 balance  
- Pay-as-you-go 常见最低充值约 $5（以官网为准）

---

## 费用备忘（方案 C）

| 范围 | 动态时长 | 约费用（API） |
|------|----------|----------------|
| 本 15s 样片 | ~12s | **$0.2～$0.6** |
| 方案 C 默认 | 1～3 min | **$1～$9** |
| 全程 10 min（非默认） | ~10 min | **$10～$30** |
| 本机 Qwen 旁白 | — | **$0** |

---

## 已完成（工程侧）

| 项 | 位置 |
|----|------|
| 讲解安全版 18 页 PPTX | `templates/settled/disease-health-shenke-blue-v1/急性上呼吸道感染_疾病健康知识培训_讲解安全版_v1.pptx` |
| 生成器 `--presenter` | `…/generator/build-editable.mjs` |
| QA 静帧 | `outputs/qa-presenter-v1/slide-*.png` |
| 第 3 页仅课件 | `outputs/enterprise-page03-presenter-slide-only.png` |
| 第 3 页静帧叠人示意 | `outputs/enterprise-page03-presenter-composite.png` |
| 去底验收棋盘格 | `outputs/portrait-cutout-checker-preview.png` |
| 网页指南（仅作对照，**非默认路径**） | `HEYGEN-网页版操作指南.md` |
| API 脚本 | `scripts/heygen_15s_sample.py` |

---

## 待 Codex 完成（顺序）

1. [ ] 用户提供并 `export HEYGEN_API_KEY=...`  
2. [ ] 跑 `python3 scripts/heygen_15s_sample.py`  
3. [ ] 得到 `outputs/sample-15s.mp4`  
4. [ ] 听感+口型验收；失败读报错改 endpoint，**勿盲重试**  
5. [ ] 叠讲解安全第 3 页预览  
6. [ ] 确认关键动口型页（默认：疾病概览 ±0～2 页）  
7. [ ] 方案 C 拼片：1 动态 + 1 静帧+旁白  

---

## 重建命令

```bash
# 讲解安全版 PPTX
cd production-library/templates/settled/disease-health-shenke-blue-v1/generator
node build-editable.mjs --presenter

# API 15s 样片（需 Key）
export HEYGEN_API_KEY='...'   # 用户提供，勿入库
cd ../../../validation/digital-human-ppt-presenter-poc-v1
# 或从仓库根：
# cd production-library/validation/digital-human-ppt-presenter-poc-v1
python3 scripts/heygen_15s_sample.py
```

---

## 贴给 Codex 的提示词（可直接复制）

```text
接着 chain-pharmacy-content-studio 的 PPT+数字人侧讲 POC。

必读：
production-library/validation/digital-human-ppt-presenter-poc-v1/HANDOVER-for-codex.md
production-library/validation/digital-human-ppt-presenter-poc-v1/work/job-state.json

要点：
- 方案C：仅关键页/开场动口型，其余静帧药师+本机旁白；不要全程10分钟数字人
- 网页版下载要付费 → 改 API 模式
- 素材已齐：inputs/portrait-pharmacist-standing-v1.jpg + inputs/narration-15s.mp3（~12s）
- 脚本：scripts/heygen_15s_sample.py（音频驱动口型，禁止 HeyGen 再TTS）
- 本机可能还没有 HEYGEN_API_KEY：先向我要 Key，export 后跑脚本，输出 outputs/sample-15s.mp4
- Key 禁止写入仓库；失败不要盲目重试扣费
- 样片 OK 后叠到 outputs/enterprise-page03-presenter-slide-only.png 做侧讲预览
```

---

## 用户需准备

1. 登录 HeyGen → **API / Developer** 创建 **API Key**  
2. 确认 **API 余额**（与网页订阅/免费条可能分离；可能需 Pay-as-you-go 充值）  
3. 把 Key 交给 Codex（对话里粘贴或本机 `export`），**不要** commit 到 git  
