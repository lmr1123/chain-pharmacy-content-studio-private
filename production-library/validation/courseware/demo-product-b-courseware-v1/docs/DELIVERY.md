# 速福达®玛巴洛沙韦 · 商品培训课件3 独立金样 v1

## 定位

- **独立金样**：目录与工程均不与可可康、辅酶Q10、风热证或其他金样混用。
- **权威来源**：仅以用户提供的参考视频为视觉/时码权威  
  `/Users/liminrong/Downloads/商品培训课件3/商品培训课件3.mp4`
- **从 0→1 复刻**：未套用其他模型的复刻工程或改写模板；结构、章节、导航、动效顺序按参考片重建。

## 成片

| 项 | 值 |
| --- | --- |
| 路径 | `out/速福达_商品培训课件3_独立金样_v1.mp4` |
| 分辨率 | 1920×1080 |
| 帧率 | 30 fps |
| 编码 | H.264 + AAC |
| 时长 | **约 97 s**（v2.0：2026-08-02 重录旁白对齐） |
| 响度 | 约 −16 LUFS |
| 旁白 | **金样签样 = 重录原声**；**量产扩主题 = 克隆音色生成** |

### 讲解音色（扩主题）

| 项 | 值 |
| --- | --- |
| 音色包 | `voice.sufuda-courseware-pharmacist-v1` |
| 目录 | `production-library/voices/sufuda-courseware-pharmacist-v1/` |
| 生成脚本 | `scripts/generate_courseware_cloned_narration.py` |
| 策略 | 语义块连读 + 语速 1.16×（上限 1.18×），禁止逐句硬拼 |

金样成片当前仍用重录原声做画面/时码验收。换其他商品主题时：更新 `storyboard.json` 文案 → 跑克隆脚本 → 出新旁白轨。

### 截断说明

新录音源约 **136 s**（含尾部静音）。有效口播约至 **96 s**，成片交付 **97 s**。旧版 103 s / 147 s 截断策略已由 v2.0 重录音频时码替代。

## 章节映射（与参考一致）

1. 封面总览（产品名 + 三点卖点 + 包装组）
2. 流感背景三卡（365 天 / 危害 / 1.4 亿 + 黄金 48 小时）
3. 一、三大核心功效  
   - 专治甲流乙流  
   - 全程 1 次 / 机制对比（玛巴洛沙韦 vs 奥司他韦）  
   - 治疗自己、保护身边人  
4. 二、产品特点（安全性 / 双剂型 / 原研品牌证据）
5. 三、适宜人群（≥5 岁 + 三类重点人群）
6. 三、联合用药（退烧药 / 慢病药）
7. 总结四列表

## 资产策略（合规 · v1.1 企业插画升级）

| 类型 | 处理 |
| --- | --- |
| 人物 / 家庭 / 树木 / 机制细胞 / 人群 / 医疗图标 | **AI 生图**企业级药店培训扁平风（禁止 SVG/程序化 demo 主视觉） |
| 丝绸背景、橙带、导航、表格、字幕 | 程序化可编辑层（批量换文案） |
| 速福达 Logo | 文字重绘示意（非官方矢量源文件） |
| 包装图 | **业务授权槽位**；当前为无商标示意包装，路径可整组替换 |
| 参考原声 | 0–103 s 裁切并 loudnorm；交付标注「参考原声验证节奏」 |

**禁止**：参考视频像素入库；SVG 火柴人/半成品当主视觉。  
**批量复用**：见 `docs/style-pack-and-slots.md`（style_pack + 槽位清单）。

## 工程入口（本目录独立）

```
sufuda-product-courseware-3-gold-v1/
  storyboard.json          # 时码/字幕/页面合同
  src/project.tsx          # Revideo 全片
  src/render.ts
  public/assets/           # 自制资产 + 旁白
  out/                     # 成片
  qa/pair/                 # 与参考并排对照帧
  reference/               # 抽帧与转写（仅测量）
  docs/DELIVERY.md
```

渲染：

```bash
cd production-library/validation/courseware/sufuda-product-courseware-3-gold-v1
# 已 symlink poc/gold-sample/node_modules
npx tsc && node dist/src/render.js
```

## QA 摘要

- [x] 1920×1080 / 30fps / 完整解码  
- [x] 无 blackdetect 黑场  
- [x] 时长锁 103 s 级（与旁白对齐）  
- [x] 页面顺序与参考一致；关键时点（18/36/55/86/100 s）章节语义对齐  
- [x] 字幕按合同逐条烧录  
- [ ] 官方包装/Logo 授权后像素级替换（当前为槽位示意）  
- [ ] 人物插画可再升一级（更贴近参考卡通细节）  
- [ ] 克隆药师音色（当前参考原声）  

## 未混入

- 不写入 `production-library/templates/settled/`（须用户视觉确认后再沉淀）  
- 不与 `product-courseware-3-gold-sample-v1/v2`、辅酶Q10 faithful、风热证金样共用输出目录  
- 不绑定 `template.product-training-faithful-v1` 蓝底人物模板  

## 下一步（签样后）

1. 业务提供：授权包装高清图、Logo 透明底、可选原 PPTX  
2. 替换 `public/assets/pack-*.png` 与 logo  
3. 用户确认后复制到  
   `production-library/templates/settled/sufuda-product-courseware-3-v1/`  
4. 可选：Qwen 克隆旁白替换参考原声  
