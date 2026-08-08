# 真人数字人侧讲模式 · 全局入口

**模式 ID：** `digital-human-presenter-scheme-C`  
**用户签样：** 2026-08-08（布局 / 穿插 / 合成 v6.2 / **全课声源一致**）

任意课件若要走「真人数字人侧讲」，**二次调整一律按此模式**，不另起规则。

---

## 一句话

关键页收窄 + 动态数字人；非关键页全宽放大、无人但有旁白；**全课同一药师 Qwen 克隆声**；布局从 PPT 比例改起。

---

## 权威文档（POC 目录）

路径前缀：

`production-library/validation/digital-human-ppt-presenter-poc-v1/`

| 文件 | 用途 |
|------|------|
| **`PRODUCT-MODE-presenter-scheme-C.md`** | **总规 + 声音一致性 + 其他课件二次调整 SOP** |
| `KEY-PAGE-INTERLEAVE-RULES.md` | 关键页头-腰-尾穿插 |
| `work/key_pages.json` | 本课关键页配置示例 |
| `LESSONS-composite-v6.2.md` | 抠像 / 曝光 / 固定缩放 |
| `scripts/composite_with_rembg.py` | 合成实现 |
| `scripts/scheme_c_interleave_review.py` | 穿插审片 |

Voice pack（全局唯一默认）：

`production-library/voices/reference-pharmacist-qwen-v1/`

---

## 二次调整触发语

用户说类似：

- 「这个课件用数字人模式 / 真人数字人侧讲」  
- 「按方案 C 转」  
- 「关键页出数字人」  

→ Agent **必须**打开 `PRODUCT-MODE-presenter-scheme-C.md` §4 清单执行，并保证：

1. 双布局（presenter / full）  
2. 关键页穿插（非只第一页）  
3. **全课同一 voice pack**（禁止 edge-tts 混用）  
4. v6.2 合成  
5. 非关键页无人  
6. **生成数字人前**：把最终脚本 + 数字人页清单交业务确认（见下）

---

## 业务复核闸门（生成前 · 强制）

```text
整理脚本 + key_pages 草案
  → 发给业务《业务复核包》（页码写清哪些页有数字人）
  → 业务确认「可以生成」
  → 才允许：克隆旁白终轨 / HeyGen / 成片
```

| 材料 | 路径（业务包） |
|------|----------------|
| 业务怎么用 | `outputs/业务使用资料包/药店培训内容工厂-业务包/08_数字人侧讲模式/README.md` |
| 口令 | `…/08_数字人侧讲模式/口令卡.md` |
| 复核包模板 | `…/08_数字人侧讲模式/业务复核包-模板.md` |
| 代理清单 | `…/08_数字人侧讲模式/代理执行清单.md` |

未确认前：可出 PPT 静帧与脚本；**禁止 HeyGen**。  

---

## 相关 lessons

`tasks/lessons.md` 条目：

- 2026-08-08 侧讲模式产品化 · 双布局 · 禁静帧站人  
- 2026-08-08 关键页穿插 + 非关键页也要旁白  
- 2026-08-08 数字人与非关键页旁白必须同声源  
