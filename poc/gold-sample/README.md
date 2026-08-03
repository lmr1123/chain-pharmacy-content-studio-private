# 风热证金标准样片工程

> 正式模板定位以生产库为准。当前唯一正式完整复刻金样是
> `production-library/templates/settled/health-video-reference-tech-v1/wind-heat-reference-full-181s.mp4`；
> 登记入口为
> `template.health-reference-tech-v1.canonical_gold_sample`。
> `production-library/validation/video/wind-heat-gold-sample-master.mp4`
> 是早期内部探索稿，文件名中的
> `master` 不代表正式沉淀状态。

目标：使用最终拟采用的参数化场景体系，复刻用户参考视频的视觉语言并输出可评审 MP4。

## 产物

- `script.md`：正式验证旁白；
- `storyboard.json`：可批量替换内容的场景数据；
- `assets/`：正式视觉资产；
- `src/`：动画与渲染工程；
- `audio/`：逐场景配音和字幕；
- `production-library/validation/video/`：MP4 阶段稿、QA 抽帧和对比结果。

正式完整复刻金样：

- `production-library/templates/settled/health-video-reference-tech-v1/wind-heat-reference-full-181s.mp4`

早期探索稿及当时 QA（非当前模板定位入口）：

- `production-library/validation/video/wind-heat-gold-sample-master.mp4`
- `production-library/validation/video/qa/final-contact-sheet.png`

当前优先评审的 30 秒视觉签样：

- `production-library/validation/video/wind-heat-30s-visual-approval-master.mp4`
- `production-library/validation/video/qa/review-contact-sheet.png`

该短片只用于确认片头、角色画风、口型、眨眼、表情、手势和动画节奏。上述方向确认前，不继续扩展其他内容场景。

## 样片范围

1. 科技医疗片头；
2. 卡通药师与症状钩子；
3. 风与热的机制流程；
4. 三个典型信号；
5. 三种常见食材；
6. 四点总结。

## 验收

- 1920×1080，30fps；
- 60–90 秒；
- 无占位素材；
- 人物、图片、文字和动画均达到可直接评审的完成度；
- Scene JSON 可替换文字和素材；
- 输出 MP4 和逐场景 QA 帧。

## 本地复现

```bash
npm install
npm run audio
npm run typecheck
npm run render
```

旁白脚本默认调用 macOS 本地 `say`，不会把文本发送到外部语音服务。渲染完成后可使用 FFmpeg 做成片音量标准化。

30 秒视觉签样：

```bash
npm run audio:review
npm run render:review
```

## 已验证边界

- 已验证：正式视觉资产、6 类动画场景、字幕、旁白时长联动、1080p MP4 和 Scene JSON 参数化；
- 尚未验证：网页编辑器、Excel 批量导入、PPTX/PDF、批量任务队列和真人数字人；
- 人物嘴型当前为说话状态循环，不是音素级嘴型同步。
