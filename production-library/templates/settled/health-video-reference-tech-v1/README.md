# 风热证 · 疾病科普视频 金样

**一句话**：连锁药店内部培训用「疾病科普 / 健康知识」视频形态的金样，主题为 **风热证**。

| 看什么 | 文件 |
|--------|------|
| 视觉对照金样（用户 2026-07-30 确认） | `风热证_疾病科普视频_金样_v1.mp4`（≈ **181.2s** · 1920×1080） |
| 同内容技术名 | `wind-heat-reference-full-181s.mp4`（硬链） |
| **可编辑生产金样 v2**（零参考像素 · 元素可编 · 统一声） | `风热证_疾病科普视频_可编辑金样_v2.mp4`（≈ **181.2s**） |
| 元数据 | `manifest.json` |
| 元素审计快照 | `element-audit.snapshot.json`（62 可编层） |
| 语音包 | `voice/` → `voice.reference-pharmacist-qwen-v1` |
| 业务 Word | `业务提交_空白模板.docx` / `业务提交_填写参考.docx` |
| 货架预览 | `preview/` |

## 状态说明（必读）

| 产物 | 角色 | 业务怎么用 |
|------|------|------------|
| **金样 v1（181s）** | 用户确认的完整视觉对照成片 | 看效果、学章节结构、货架预览 |
| **可编辑金样 v2** | 重制技术金样：零参考截图像素、统一数字人/声音、元素可编 | 新病种量产时的**生产基线**（仍须审核旁白 + 授权 Logo） |

- 片尾公司授权透明 Logo 若未补齐，不得把单条主题标为 `production-validated` 终局，但不妨碍金样包作为可用样板交付。
- 禁止默认系统机器人音色；正式旁白走 `voice/` 克隆包。

## 章节结构（约）

1. 开场 · 基础认知  
2. 人物情境  
3. 病因机理  
4. 典型症状  
5. 治疗思路  
6. 用药建议  
7. 总结片尾  

## 工程与再导出

完整可改工程（Revideo）：

```text
poc/gold-sample/          # 源工程与场景
production-library/validation/revideo-editability/wind-heat-v2/  # v2 QA 与成片
```

```bash
# 装配历史对照成片（v1）
node poc/gold-sample/scripts/assemble-wind-heat-full.mjs

# v2 可编辑成片 / 编辑器（见 gold-sample package scripts）
cd poc/gold-sample
# npm run start:wind-heat-editable 等 — 以 package.json 为准
```

装配合同：`production-library/examples/wind-heat-full-frame-assembly.json`  
记录：`docs/wind-heat-full-assembly.md`  
v2 QA：`production-library/validation/revideo-editability/wind-heat-v2/qa-report-v2.json`

## 业务整片预览

```text
production-library/validation/courseware/gold-samples/wind-heat-video-gold-v1/web/full-film.html
production-library/validation/courseware/gold-samples/index.html
```

```bash
cd production-library/validation/courseware && python3 -m http.server 8765
# http://127.0.0.1:8765/gold-samples/
```

## 命名约定

```
{主题}_{课型}_金样_v{n}.mp4
{主题}_{课型}_可编辑金样_v{n}.mp4
```
