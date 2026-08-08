# 产品模式：真人数字人侧讲（方案 C）

**模式 ID：** `digital-human-presenter-scheme-C`  
**状态：** 用户签样可用（2026-08-08）  
**适用范围：** 本课 POC **及后续任意课件** 转为「真人数字人侧讲」时的二次调整标准。

> 一句话：  
> **关键页** = 收窄课件 + 动态数字人侧讲；  
> **非关键页** = 全宽课件放大 + 旁白、无人；  
> **全课同一药师克隆声**；  
> **布局从 PPT 比例改起**，禁止后期强行拉升。

---

## 0. 文档索引（本模式全家桶）

| 文档 | 内容 |
|------|------|
| **本文** | 模式总规 + 声音一致性 + 其他课件二次调整 SOP |
| `KEY-PAGE-INTERLEAVE-RULES.md` | 关键页头-腰-尾穿插规则 |
| `work/key_pages.json` | 本课关键页配置（改页号改配置） |
| `LESSONS-composite-v6.2.md` | 抠像/曝光/固定缩放（合成） |
| `scripts/composite_with_rembg.py` | v6.2 合成实现 |
| `scripts/scheme_c_interleave_review.py` | 穿插审片拼片 |
| 项目级入口 | `docs/digital-human-presenter-mode.md` |

---

## 1. 模式定义

| 层 | 规则 |
|----|------|
| **转化目标** | 任意标准课件 →「内容栏收窄 + 右侧数字人侧讲」可交付形态 |
| **用量（方案 C）** | **仅关键页**动态数字人；合计约 **1～3 分钟**；禁止默认全程动口型 |
| **穿插** | 头-腰-尾锚点，非整课只出镜一次（见穿插规则） |
| **非关键页** | **全宽 PPT 放大内容**，**不叠人**（含静帧站人禁止） |
| **旁白** | **全课都有**（关键页驱动口型；非关键页全宽也要讲） |
| **声源（全局硬规则）** | **全课同一 voice pack**，见 §3 |
| **布局源头** | Generator / PPT **双布局**先定比例，再叠人；禁止 ffmpeg 强行拉升构图 |
| **合成** | rembg + **v6.2**（原片曝光 + 首帧固定 scale）；HeyGen **仅 API** |

---

## 2. 双布局（硬规则）

| 页类型 | PPT 布局 | 人像 | 旁白 |
|--------|----------|------|------|
| **关键页** | 讲解安全版：内容约 **60%**，右侧留白 | **动态数字人** | 必有（=口型驱动音频） |
| **非关键页** | **全宽金样**（内容铺满可用区） | **无** | 必有 |
| 封面 / 目录 / 尾页 | 品牌全幅 | 无 | 可短可无 |

### 禁止

| 错误 | 为何 |
|------|------|
| 非关键页 + 静帧药师站旁边 | 假站人、像半成品 |
| 全宽页事后 scale 成侧讲构图 | 字糊、比例畸变 |
| 逐帧按 bbox 重算缩放 | 一大一小抖动 |
| 关键页 / 非关键页 **不同 TTS 引擎** | 音色语速割裂（已踩坑） |
| edge-tts / 系统 `say` 混进克隆课 | 与数字人轨不一致 |

### 正确顺序（任意课件二次调整）

```text
1. 确认本课走「真人数字人侧讲模式」
2. 定关键页清单 → 写入 key_pages.json（头-腰-尾）
3. Generator 双布局：关键页 --presenter；非关键页全宽
4. 导出两套静帧（各自正确比例，不互 stretch）
5. 全课旁白：统一 voice pack 一次生成（§3）
6. 仅关键页：旁白 → HeyGen API → rembg → v6.2 叠讲解安全版
7. 非关键页：全宽静帧 + 同声源旁白
8. 按页拼接；成片 loudnorm ≈ -16 LUFS
```

---

## 3. 全局声音一致性（已签样）

### 3.1 唯一声源

| 项 | 值 |
|----|-----|
| Voice pack | `production-library/voices/reference-pharmacist-qwen-v1` |
| 引擎 | `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16`（`mlx_audio.tts`） |
| Prompt | `voices/.../prompt.wav` + `ref_text.txt` |
| 语速 | voice-pack pace：`default_tempo ≈ 1.12～1.16`，`max ≤ 1.18` |
| 响度 | **loudnorm I=-16:TP=-1.5**（全课统一） |
| 字速参考 | 约 **5.5～6.5 字/秒**（与样片同量级即可） |

### 3.2 硬规则

1. **数字人轨与非关键页旁白必须同源**：同一 pack、同一引擎、同一 ref。  
2. **禁止** edge-tts / 系统音 / 其它克隆包默认混用。  
3. 关键页：该页旁白 wav **原样**上传 HeyGen 驱动口型（禁止 HeyGen 再 TTS 覆盖）。  
4. 非关键页：同一批生成的 wav/mp3 贴全宽页，再拼片。  
5. 成片最后可整轨 loudnorm 一次，避免段间忽大忽小。  
6. 换主题也**先**用本 pack 生成新文案试听，证明不是复用旧轨（voice-pack lessons）。

### 3.3 实现入口

- 本机克隆参考：`scripts/generate_cloned_narration.py` 等同系脚本  
- 环境：项目 `.venv-qwen-tts` 或已装 `mlx_audio` 的 venv  
- 本 POC 验收旁白目录：`inputs/narration-review/`（p04/p10 已用克隆重出）  
- 数字人驱动旁白：`inputs/narration-15s.{wav,mp3}`（同源体系）

---

## 4. 其他课件「二次调整」SOP（开用本模式时）

当用户说：**这个课件要用真人数字人模式** → 按下列清单执行，不另起炉灶。

### Step A · 立项

- [ ] 确认模式 ID：`digital-human-presenter-scheme-C`  
- [ ] 挂已签样视觉系统（色板/字阶/chrome），不新开 UI  
- [ ] 复制/填写 `key_pages.json` 草案（页号 + 角色 + 理由）

### Step B · **业务复核闸门（生成数字人前 · 强制）**

- [ ] 写全课旁白终稿脚本  
- [ ] 用业务包模板填《业务复核包》：  
  `outputs/业务使用资料包/药店培训内容工厂-业务包/08_数字人侧讲模式/业务复核包-模板.md`  
- [ ] **明确列出**：哪些页有数字人（页码 + 节名 + 理由）；其余页全宽无人  
- [ ] 发给业务；**等待**「脚本通过 / 数字人页确认 / 可以生成」  
- [ ] **未确认：禁止 HeyGen、禁止产生数字人费用**（可先出 PPT 静帧）

### Step C · 版式

- [ ] 关键页 → 讲解安全版（`--presenter` / 内容约 60%）  
- [ ] 非关键页 → 全宽金样布局（信息放大）  
- [ ] 壳页保持全幅  
- [ ] **禁止**对成片做构图 stretch

### Step D · 声音（全局一致 · 确认后）

- [ ] 只使用 `reference-pharmacist-qwen-v1`  
- [ ] 按**已确认**旁白稿 → **整课一次克隆生成**  
- [ ] tempo / loudnorm 按 §3  
- [ ] 抽听：关键页轨 vs 非关键页轨，音色语速无跳变

### Step E · 数字人（确认后）

- [ ] 仅**业务确认过的** `key_pages` 调 HeyGen API（音频驱动口型）  
- [ ] 合成走 **v6.2**（`composite_with_rembg.py`）  
- [ ] 预算：动态合计 1～3 分钟

### Step F · 成片与验收

- [ ] 拼接：壳 → 关键 → 全宽旁白 → 关键 → …  
- [ ] 业务听：**声源一致**、**穿插出镜**、**非关键无人但有讲解**  
- [ ] 记档：本课 `key_pages.json` + 输出路径写入 job-state / 交付说明  

---

## 5. 本课 POC 资产对照

| 用途 | 路径 |
|------|------|
| 全宽静帧 | `validation/courseware/gold-samples/uri-shenke-health-pptx-gold-v1/web/media/slides/` |
| 讲解安全版静帧 | `outputs/qa-presenter-v1/` |
| 关键① 动态 | `outputs/ppt-presenter-15s-A-pharmacist-standing.mp4` |
| 关键②③ 示意 | `outputs/ppt-presenter-key-p09-reuse-dh.mp4` / `p15-...` |
| 穿插审片 | `outputs/scheme-c-interleave-review.mp4`（≈ `~/Downloads/`） |
| 克隆旁白验收 | `inputs/narration-review/page-04-*.mp3`、`page-10-*.mp3` |
| 全宽 / 讲解安全版 PPTX | settled `disease-health-shenke-blue-v1` 下金样与讲解安全版 |

---

## 6. 修订历史

| 日期 | 变更 |
|------|------|
| 2026-08-07 | 方案 C 初定；误写「非关键=静帧药师」 |
| 2026-08-08 | 非关键=全宽无人；布局从 PPT 起；穿插规则；可复用其他课件 |
| 2026-08-08 | **声音一致性签样**：全课 Qwen 药师克隆；禁止 edge-tts 混用；写入二次调整 SOP |
