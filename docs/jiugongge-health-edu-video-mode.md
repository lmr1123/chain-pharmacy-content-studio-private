# 健康科普九宫格模式（原版）· 全局入口

**模式 ID：** `jiugongge-health-edu-v1`  
**模式名：** 九宫格版本 / 九宫格科普 / 林医生王大爷科普  
**并列：** 九宫格（合规版 · 无医疗内容）→ `docs/jiugongge-health-edu-compliance-mode.md`  
**状态：** 生产可用  
**更新日期：** 2026-08-08  

> **定位：** 面向 **50 岁以上中老年** 的对外短视频健康科普。  
> **角色：** 林医生 + 王大爷（卡通诊室/白大褂允许）。  
> **管线：** 角色三视图 → 6×九宫格分镜 → 6×片段视频提示词 → 社媒合规包。  

若业务需要**视频号严格避开医疗资质红线**，请走 **合规版**，不要用本模式。

---

## 一句话

业务给 **科普主题 + 1～3 个核心知识点** → 交付 60 秒完整脚本（口播 + 九宫格 + 视频提示词）。

---

## 权威资产

| 路径 | 用途 |
|------|------|
| `production-library/templates/prompt-modes/jiugongge-health-edu-v1/meta-prompt.md` | 原版元提示词 |
| `…/character-sheets.md` | 林医生 / 王大爷 |
| `…/example-阿尔茨海默早期筛查.json` | 示例 |
| scaffold | `scripts/scaffold_jiugongge_health_edu.py` |
| 业务包 | `10_健康科普九宫格模式/` |

---

## 触发语

- 「九宫格版本」「九宫格科普」「林医生 / 王大爷」
- 「60 秒中老年科普」（未提合规/无医疗时，默认可走本版；若强调视频号避险则问是否合规版）

**不要** 与下列混淆：

| 想要 | 模式 |
|------|------|
| 无医生无医院无病名话术 | `jiugongge-health-edu-compliance-v1` |
| 生活避险五拍 | `seedance-health-edu-v1` |
| 店员培训 MG | 疾病科普视频 health full |

---

## 流程

```text
① 主题 + 知识点 1～3
② 《九宫格科普脚本复核包》六段口播
③ 确认后 → 三视图 + 六段（口播+九宫格+视频）+ 发布包
④ 业务出图 → 出视频 → 拼接
```

```bash
python3 scripts/scaffold_jiugongge_health_edu.py --vars <json>
# 默认仅生成复核包 + approval.json
# 业务明确确认后，代理填写 approved=true / approved_by（保留 input_sha256 与 review_sha256），再运行：
python3 scripts/scaffold_jiugongge_health_edu.py --vars <json> \
  --release --approval <输出目录/approval.json>
```

输入变量或复核稿在审批后改变时，hash 门必须拒绝 release，须重新复核。

---

## 六段骨架

| # | 功能 |
|---|------|
| 1 | 场景引入 & 医生开场 |
| 2–4 | 核心知识点 1～3 |
| 5 | 紧急救助 / 行动指南（如 120） |
| 6 | 温馨总结 & 预防呼吁 |

---

## 交付物

`outputs/business-video-runs/jiugongge-health-edu/<slug>/`  
`01` 复核 · `02` 角色三视图 · `03` 六段提示词 · `04` 发布包  
