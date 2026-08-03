# style-pack.sufuda-pearl-silk-orange-v1 · 槽位与批量复用说明

## 项目目标对齐

本金样服务连锁药店 **AI 批量制作内部培训课件/视频**（见 `docs/project-brief.md`）：

1. 先签完整高质量金样 → 锁定框架 + `style_pack`  
2. 同风格换审核内容批量出新主题  
3. 真包装 / Logo / 证据由业务提供，不仿造  

禁止：SVG 火柴人、程序化 demo 图标当主视觉；禁止无槽位依据的通用元素囤积。

## 风格包

| 字段 | 值 |
| --- | --- |
| `style_pack_id` | `style-pack.sufuda-pearl-silk-orange-v1` |
| 背景 | 珍珠白丝绸 + 淡橙轨道线 |
| 主色 | 橙 `#e98200`、藏青 `#123c78` / `#22579b` |
| 字幕 | 底部深色字，无重字幕条 |
| 插画 | **AI 生图**中国药店培训扁平风（圆润、东亚人物、商业级），非 SVG |
| 包装 | 业务授权槽位；当前为示意包装 |

## 可替换槽位（批量主题只换这些）

| 槽位 ID | 当前资产 | 换主题时 |
| --- | --- | --- |
| `slot.logo` | 文字 Logo 示意 | 业务透明 Logo |
| `slot.pack.group` | 示意包装组 | 授权包装拼组 |
| `slot.pack.tablet` / `suspension` | 示意 | 授权分剂型图 |
| `slot.illu.season-tree` | AI 四季树 | 可复用或按病种重绘 |
| `slot.illu.patient` | AI 口罩患者 | 按病种情境重绘 |
| `slot.illu.family-shield` | AI 家庭盾 | 可复用防护语义 |
| `slot.illu.char.elder/child/chronic` | AI 人群 | 按适宜人群改提示词 |
| `slot.illu.mechanism-cell` | AI 细胞病毒 | 按机制改绘 |
| `slot.icon.*` | AI 医疗图标 | 系列内复用 |
| `slot.copy.*` | storyboard 文案 | Word/审核稿导入 |
| `slot.audio.narration` | 金样可先用重录原声签样 | **量产用克隆轨**（见下） |

文字层（章节标题、导航、表格、字幕）保持程序化可编辑，**不烧进插画**。

## 讲解音色克隆（换主题必用）

| 项 | 值 |
| --- | --- |
| 音色包 ID | `voice.sufuda-courseware-pharmacist-v1` |
| 目录 | `production-library/voices/sufuda-courseware-pharmacist-v1/` |
| 引擎 | Qwen3-TTS 0.6B Base BF16（本地 MLX） |
| 语速策略 | `v5-smooth`：语义块连读，`DEFAULT_TEMPO=1.16`，`MAX_TEMPO≤1.18` |
| 入口脚本 | `scripts/generate_courseware_cloned_narration.py` |

**金样当前成片**：为验收画面对齐，旁白轨仍是 **2026-08-02 重录原声**（非克隆）。  
**批量新主题**：不要复用原声轨；用同一音色包 + 新 `storyboard.json` 文案 **克隆重新生成**。

```bash
# 1) 冒烟：证明克隆能读新文案（非复读原轨）
.venv-qwen-tts/bin/python scripts/generate_courseware_cloned_narration.py \
  --storyboard production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/storyboard.json \
  --voice-pack production-library/voices/sufuda-courseware-pharmacist-v1 \
  --smoke-text "本课程介绍某某商品的核心功效、产品特点与联合用药要点。"

# 2) 整课克隆（按 pages 语义块连读）
.venv-qwen-tts/bin/python scripts/generate_courseware_cloned_narration.py \
  --storyboard path/to/new-theme/storyboard.json \
  --voice-pack production-library/voices/sufuda-courseware-pharmacist-v1 \
  --out-dir path/to/new-theme/audio-work/clone-v1 \
  --copy-to-assets path/to/new-theme/public/assets/narration-cloned.wav \
  --apply-to-storyboard
```

禁止：40 条字幕逐句 TTS 硬拼；单句 `atempo`>1.18 贴旧窗。放不下就延长画面时间轴。

## 生图规范（新主题补图）

统一前缀：

```text
Enterprise Chinese chain-pharmacy internal training illustration,
premium commercial 2D medical flat style, East Asian characters,
soft orange and navy accents, pearl-white background, no text,
no watermark, no logo, no real brand packaging, polished corporate
e-learning quality, not stick figure, not SVG demo.
```

输出：≥1024 边长 PNG；近白底可做 soft alpha 叠丝绸背景。  
提示词与 raw 图保存在 `public/assets/gen/` 与本目录。

## 批量路径（签样后）

1. 复制本工程时间轴与 chrome（章节带 / 导航 / 字幕系统）  
2. 业务 Word 填审核文案 → 回填 `storyboard.json` captions / 表格  
3. 仅补本课语义所需插画槽位 + 授权包装  
4. 渲染 MP4；可选同源导出 PPTX  

不把本金样与辅酶 Q10 / 风热 / 可可康金样混目录。
