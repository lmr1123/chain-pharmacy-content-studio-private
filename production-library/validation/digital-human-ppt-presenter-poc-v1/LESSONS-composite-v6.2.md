# PPT 侧讲数字人合成 · 签样方案 v6.2

**用户确认：** 2026-08-07「可以了」  
**脚本：** `scripts/composite_with_rembg.py`  
**交付样片：** `outputs/ppt-presenter-15s-{A,B,C}-*.mp4`（同步 `~/Downloads/`）

本文是本 POC 的**合成事实源**。后续多页方案 C 必须沿用，勿静默回退到 v6.1 强压或逐帧 bbox 缩放。

---

## 正确流水线

```
HeyGen 原片 mp4（保留 RGB）
  → 抽帧
  → rembg u2net 抠像（不改曝光）
  → 硬 alpha（半透明边 → 0 或 255）
  → 首帧标定 fixed scale + paste_x/y
  → 整段整帧同一 scale/原点叠到讲解安全版 PPT 静帧
  → 编码 + 原片音轨
```

### 硬规则

| 项 | 做 | 不做 |
|----|----|------|
| 抠像 | rembg | ffmpeg colorkey 主路径 |
| 曝光 | 原片 RGB | crush ×0.48、硬 clip 148、二次压肤、colorlevels rimax |
| 缩放 | 首帧定 scale，全程锁 | 每帧 `target_h / content_h` |
| 位置 | 首帧定 paste 原点，全程锁 | 每帧 content 贴底/贴左重算 |
| 白边 | 硬 alpha | 半透明边叠浅蓝 PPT |
| HeyGen | API only | 网页付费下载当默认 |

### 布局常量（A/B 业务认可）

- Canvas 1920×1080；`PERSON_LEFT = 1280`
- A/B：`target_h=1040`，`max_w=620`
- C：`target_h=1000`，`max_w=680`，`y_lift=40`（半身另议，曝光/防抖逻辑与 A/B 相同）

---

## 为何会白 / 为何会黑 / 为何会抖

1. **发白（假白光）**  
   - HeyGen 棚光偏亮是一部分。  
   - 更致命：抠像半透明白边 + 浅蓝 PPT 底 → 叠出来像脸上罩白光。  
   - `colorlevels rimax<1` 会把高光拉爆，越「修」越白。

2. **过黑（v6.1）**  
   - 为消白光把整脸 `×0.48` + 高光再压 + clip 148 → 业务反馈太黑。  
   - **签样纠正：保留原数字人视频曝光，不要为消白光重渲染压暗。**

3. **一大一小 / 移动幅度大**  
   - 根因：每帧 `content_bbox` → `scale = target_h / h`。  
   - 举手/掩膜变高 → scale 变小；放手 → scale 变大；左右贴边也跟着跳。  
   - **修法：首帧标定 + 整帧固定 scale/原点。**

---

## 版本演进（勿回退）

| 版 | 要点 | 业务 |
|----|------|------|
| colorkey / v3–v5 | 色键 + curves 压亮 | 白 / 不稳 |
| v6.1 | rembg + 强 crush | 不白了但太黑；仍可能抖 |
| **v6.2（签样）** | rembg + **原片曝光** + **固定 scale** | **可以了** |

---

## 重跑

```bash
cd production-library/validation/digital-human-ppt-presenter-poc-v1
.venv-rembg/bin/python scripts/composite_with_rembg.py --all --fps 20
```

可选轻调亮度：仅当用户明确说偏亮/偏暗时，加**极轻**全局系数；禁止恢复 v6.1 crush 曲线。

---

## 全局 lessons 索引

同文已写入：`tasks/lessons.md` →「2026-08-07（PPT 侧讲数字人合成 · 曝光与防抖 · v6.2 签样）」
