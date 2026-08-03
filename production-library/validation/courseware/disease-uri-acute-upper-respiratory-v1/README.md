# 急性上呼吸道感染 · 疾病类健康知识培训课件

## 交付物

| 文件 | 说明 |
|------|------|
| `急性上呼吸道感染_呼吸系统疾病健康知识培训_v1.pptx` | **截图像素复刻** 18 页（全幅贴图，已去真人） |
| `cleaned-slides/slide-01.png` … `slide-18.png` | 去真人后的逐页底图（1920×1080） |
| `reference-frames/ref-01.png` … | 原始截图备份 |
| `build-faithful-from-screenshots.mjs` | 用 cleaned-slides 打成 PPTX |
| `build-uri-disease-courseware.mjs` | ~~自研版式~~ 已弃用（勿再当主产物） |

**来源**：`~/Downloads/呼吸系统疾病健康知识培训.png` 参课真人讲解截图（18 帧）。  
**原则**：视觉与截图一致，**不另做一套 UI**；只抠掉右侧讲解真人。

### 重建说明

- 每页 PPT = 对应 `cleaned-slides` 全幅图片（参课原版式/配色/插图/表格）。
- 真人用 `u2net_human_seg` 分割后硬填充背景；被手挡到的局部可能有轻微残影或缺口。
- 原截图水印「大参林 10077502」会随画面保留。
- 未入 settled，待业务确认后再迁模板库。

### 页结构（18）

| # | 章节 |
|---|------|
| 1 | 封面 |
| 2 | 目录 |
| 3 | 01 疾病概览 |
| 4 | 02 临床表现 |
| 5 | 03 检查方法 |
| 6–8 | 04 一般 / 全身 / 局部用药 |
| 9 | 04 对症选药 |
| 10–14 | 04 注意事项 |
| 15–16 | 05 专业关怀 |
| 17 | 结束页 |
| 18 | 一页总结 |

### 重新打包 PPTX

```bash
cd production-library/validation/courseware/disease-uri-acute-upper-respiratory-v1
node build-faithful-from-screenshots.mjs
```

---

## 后续：用数字人替代真人讲解（方案）

### 你的机器（决策前提）

- **MacBook Pro · Apple M5 · 32 GB**
- **无 NVIDIA GPU** → 评论区「单卡 5090 多并发实时数字人」**本机跑不动**，那是 CUDA/Windows 或 Linux 工位方案。

### 评论区项目澄清

| 说法 | 实际项目 | 算力 | 是否适合本机 |
|------|----------|------|--------------|
| 美团开源数字人 | [LongCat-Video-Avatar 1.5](https://github.com/meituan-longcat/LongCat-Video)（图/音 → 说话视频，偏成片质量） | 大显存 NVIDIA 为主 | ❌ 不轻松 |
| 5090 多并发实时 | 多为 [SoulX-FlashHead](https://github.com/Soul-AILab/SoulX-FlashHead) / CyberVerse+FlashHead，**非美团** | RTX 4090/5090 | ❌ 不轻松 |
| 轻量可实时 | [DH_live / MatesX](https://github.com/kleinlee/DH_live) | 可无 GPU、甚至手机 | ✅ 可试 |
| 云端数字孪生 | [HeyGen Digital Twin](https://www.heygen.com/)（剪藏笔记推荐） | 云端 | ✅ 最省事 |

剪藏笔记《Codex + Hyperframes + HeyGen + 声音克隆》对**本项目很有帮助**，可直接复用四件套思路：

1. **主控**：Codex / Claude / Grok 编排  
2. **画面**：HyperFrames / 本仓库剪映模板 / Remotion  
3. **数字人**：HeyGen 左下角小窗对口型  
4. **声音**：IndexTTS2 / 本仓库已有 **Qwen3-TTS + mlx-audio（Apple Silicon）**

### 推荐路径（按「本机轻松」排序）

#### 路径 A — 生产默认（质量稳，费用可控）★ 推荐

```
脚本（按 18 页口播） 
  → 本地 Qwen3-TTS / IndexTTS2 克隆店员或专家声线（M5 可跑，零按量费）
  → 音频上传 HeyGen Digital Twin / Avatar III（约 $1/分钟量级，以官网为准）
  → 数字人竖条/圆窗导出
  → 与本 PPTX 画面在剪映模板或 HyperFrames 合成
```

- **优点**：口型与表情过审级；不占本机 GPU；与现有「健康知识视频」模板左下角讲解窗一致。  
- **注意**：HeyGen 会按用量计费 → 批量前先确认额度（见全局费用原则）。  
- **素材**：需 1 段授权真人出镜训练片（宿凌式专家形象或自有药师形象均可）。

#### 路径 B — 全本地免费（够用、偏 2D）

```
脚本 → Qwen3-TTS（本地）
     → DH_live_mini / MatesX（照片驱动 2D 说话头，可实时/可离线）
     → FFmpeg 叠在 PPT 翻页视频上
```

- **优点**：零数字人云费；M5 压力小。  
- **缺点**：拟真度弱于 HeyGen / LongCat；内训可用，对外品牌片建议 A。

#### 路径 C — 美团 LongCat 高质量成片（需另备算力）

- 适合：单条精品、长视频口型要求极高。  
- **不要在本机强上**；用云 GPU（AutoDL / 公司 4090 机）批处理。  
- 工作流：参考图 + 本地 TTS 音轨 → LongCat-Video-Avatar → 成片。

#### 不建议本机硬上

- SoulX-FlashHead / 5090 多路实时：买/租 NVIDIA 工位再考虑，与 Mac 培训生产流水线解耦。

### 与本仓库的接法（疾病视频线）

已有资产可复用：

| 能力 | 位置 |
|------|------|
| 健康知识视频金样 / 风格 | `templates/settled/health-video-reference-tech-v1` |
| 声音克隆脚本 | `scripts/generate_cloned_*_narration.py`、`third_party/Qwen3-TTS`、`third_party/mlx-audio` |
| 剪映草稿模板 | `outputs/jianying-template-versions/` |

建议疾病 PPT 签样通过后：

1. 按页写 **口播稿**（每页 20–40 秒）。  
2. 本地 TTS 出全片 wav + srt。  
3. 选路径 A 或 B 出数字人轨。  
4. 进健康知识视频模板合成，不新建 style_pack。

### 费用提醒

| 项 | 费用属性 |
|----|----------|
| 本 PPTX 生成 | 本地免费 |
| Qwen3-TTS / mlx-audio | 本地免费 |
| HeyGen | **付费额度**，调用前确认 |
| LongCat / FlashHead 云 GPU | **租卡计费**，调用前确认 |

---

## 审核清单（业务）

- [ ] 病原体/用药表述是否与门店 SOP / 说明书一致  
- [ ] 品牌与「参课」露出是否保留  
- [ ] 商品包装图是否由业务授权后补入  
- [ ] 是否需要从 validation 升格为 `templates/settled/disease-uri-acute-v1/`
