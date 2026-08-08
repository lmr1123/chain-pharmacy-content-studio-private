# 健康科普九宫格（合规版 · 无医疗内容）· 全局入口

**模式 ID：** `jiugongge-health-edu-compliance-v1`  
**模式名：** 九宫格合规版 / 九宫格无医疗 / 健康生活总导演 / 小林生活科普  
**并列：** 九宫格原版（林医生）→ `docs/jiugongge-health-edu-video-mode.md`  
**状态：** 生产可用  
**更新日期：** 2026-08-08  

> **定位：** 微信视频号 **零医疗红线** 动画科普。只谈现象、习惯、常识。  
> **角色：** 小林 (Xiaolin) + 受众角色；服装贴合主题。  
> **结构：** 60s · **1+1+3+1** 六段；九宫格/视频提示词默认 **English**。  

---

## 一句话

业务给 **生活主题 + 受众 + 习惯点** → 先脱敏 → 交付视觉资产 + 六段（九宫格英 + 视频英 + 口播中）+ 发布全家桶。

---

## 权威资产

| 路径 | 用途 |
|------|------|
| `production-library/templates/prompt-modes/jiugongge-health-edu-compliance-v1/meta-prompt.md` | Gem 总导演指令 |
| `…/character-sheets.md` | 小林 + 受众 |
| `…/example-告别办公久坐僵硬.json` | 职场示例 |
| scaffold | `scripts/scaffold_jiugongge_health_edu_compliance.py` |
| 业务包 | `11_健康科普九宫格合规版/` |

---

## 触发语

- 「九宫格合规版」「九宫格无医疗」「合规无医疗内容」
- 「健康生活总导演」「小林生活科普」
- 「视频号要避开医疗资质 / 不要医生白大褂」

未指明时：若说「九宫格」且强调视频号避险 → 本模式；若说林医生/诊室 → 原版。

---

## 红线（最高）

禁：医生、白大褂、护士、医院、诊室、听诊器等器材、预防/治疗/缓解/病名话术。  
转：生活习惯 / 情绪调节 / 环境安全。

---

## 流程

```text
① 生活主题 + 受众(中老年/职场/宝妈) + 风格 + 习惯点1～3
② 合规脱敏说明 + 六段口播复核
③ 确认 → 角色/场景资产 + 六段英提示词 + 发布全家桶（含3条转发语）
```

```bash
python3 scripts/scaffold_jiugongge_health_edu_compliance.py --vars <json>
# 默认仅生成合规复核包 + approval.json
# 业务明确确认后，代理填写 approved=true / approved_by（保留 input_sha256 与 review_sha256），再运行：
python3 scripts/scaffold_jiugongge_health_edu_compliance.py --vars <json> \
  --release --approval <输出目录/approval.json>
# 输入/复核稿 hash 不匹配或终稿禁词命中时会拒绝 release
```

---

## 1+1+3+1 结构

| 段 | 功能 |
|----|------|
| 1 | 痛点引入（焦虑表情） |
| 2 | 习惯对照开场 |
| 3–5 | 三条干货（扶稳/坐稳安全补丁） |
| 6 | 温馨收束（舒展表情 + 软 CTA，无分享图标） |

---

## 交付物

`outputs/business-video-runs/jiugongge-health-edu-compliance/<slug>/`  
`01` 合规复核 · `02` 视觉资产 · `03` 六段提示词 · `04` 发布全家桶  
