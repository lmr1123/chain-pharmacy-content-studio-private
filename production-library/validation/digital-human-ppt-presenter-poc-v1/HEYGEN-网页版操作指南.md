# HeyGen 网页版 · 15 秒样片操作指南

**目标：** 站姿药师图 + 本机克隆旁白 → 约 12s 口型样片（验证脸/口型是否可用）  
**不要：** 让 HeyGen 再配音（会覆盖药师克隆声）

## 0. 准备材料（本机已就绪）

在 Finder 打开：

`production-library/validation/digital-human-ppt-presenter-poc-v1/inputs/`

| 文件 | 用途 |
|------|------|
| `portrait-pharmacist-standing-v1.jpg` | **上传人像**（用原图，脸更清晰；不要先传 cutout） |
| `narration-15s.mp3` | **上传音频**（约 12s，本机 Qwen 克隆） |

可选对照文案：`script.md` 里「15 秒样片截取」段。

---

## 1. 登录

1. 浏览器打开：https://app.heygen.com  
2. 登录账号（有 Free 配额即可先试）  
3. 进入主工作台 **Create / 创建**

---

## 2. 选正确产品（二选一，优先 A）

### 路径 A · Photo / Avatar 口型（推荐，最贴「人说话」）

界面文案可能是其中之一：

- **Photo Avatar** / **Talking Photo** / **Avatar from photo**
- 或 **Create video** → 选 **Photo** / **Upload a photo**

要点：用**一张正脸站姿照**生成会说话的人。

### 路径 B · Image to Video 工具页

直接打开：https://www.heygen.com/tool/image-to-video  

适合「图变动画」；若只能填文案配音、**不能上传自己的 mp3**，改走路径 A 或 Studio 里的 Photo Avatar。

---

## 3. 上传人像

1. 点 **Upload photo** / **上传照片**  
2. 选择：`portrait-pharmacist-standing-v1.jpg`  
3. 确认：正脸清晰、嘴部无遮挡  

**注意：**

- 样片阶段用 **jpg 原图**（白底可接受）  
- 合成到 PPT 时再叠 **去底 cutout**；两步分开

---

## 4. 上传旁白（关键 · 不要用 HeyGen 配音）

1. 找 **Voice / Audio / 语音** 区域  
2. **不要**选「Generate script voice / 选系统音色朗读」作为主声  
3. 选 **Upload audio** / **上传音频** / **Use my own audio**  
4. 选择：`narration-15s.mp3`  
5. 确认轨道上出现你的 mp3，时长约 12 秒  

若只有「粘贴文案 + 选 Voice」而没有上传音频：

- 换入口：Create → Photo Avatar → Script 旁找 **Audio file**  
- 或创建 Video 时 character 用 Photo，Voice 类型选 **Audio** 再上传  

**原则：** 最终成片听的必须是你上传的 `narration-15s.mp3`，不是 HeyGen 另配的女声。

---

## 5. 画幅与简单设置

| 项 | 建议 |
|----|------|
| 比例 | 先 **竖屏 9:16** 或 **1:1**（半身药师）；之后再裁进 16:9 PPT 右侧 |
| 分辨率 | 720p 即可（样片、省额度） |
| 背景 | 先默认 / 纯色；我们最终会叠到讲解安全版 PPT 上 |
| 时长 | 跟随音频（约 12s），不要再拉长空白 |

---

## 6. 生成

1. 点 **Submit / Generate / 生成**  
2. 等 1–5 分钟（队列时更长）  
3. 预览：重点听口型是否跟中文、脸是否崩、肩是否抖  

---

## 7. 下载并放到项目里

1. **Download** → MP4  
2. 保存为（建议）：

```text
production-library/validation/digital-human-ppt-presenter-poc-v1/outputs/sample-15s.mp4
```

3. 告诉我「样片已下好」，我可以帮你：  
   - 去底/抠绿（若需要）  
   - 叠到 `enterprise-page03-presenter-slide-only.png` 上看侧讲效果  

---

## 8. 验收清单（通过再考虑全页）

- [ ] 声音是本机旁白（不是陌生英文/机器人声）  
- [ ] 中文口型基本对得上  
- [ ] 无明显脸崩、双下巴乱抖  
- [ ] 站姿自然，适合放在 PPT 右侧  

不通过：换图姿势 / 略改旁白再试 **一条**；不要连续狂点生成烧额度。

---

## 常见坑

| 现象 | 处理 |
|------|------|
| 生成后声音不是你的 mp3 | 没选「上传音频」，重来并删掉 script+voice |
| 免费额度用完 | 看订阅/配额；或只保留 1 条样片 |
| 入口找不到 Photo | 搜索站内 **Photo Avatar** / **Talking Photo** |
| 界面全英文 | 按图标：人像上传 + 音符/麦克风上传音频 |

---

## 和后续 PPT 侧讲的关系

```text
网页 HeyGen 样片（半身说话人）
  → 你确认口型 OK
  → 再：去底 + 叠讲解安全版第 3 页
  → 再：全页旁白 + 多页（确认后再做）
```

**讲解安全版 PPTX** 已在本地，不必在 HeyGen 里重做课件排版。
