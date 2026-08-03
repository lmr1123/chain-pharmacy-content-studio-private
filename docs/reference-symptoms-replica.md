# 参考视频“典型症状”段复刻记录

## 复刻范围

- 参考片范围：约 43.84–66.06 秒；
- 当前签样：27.50 秒，末尾增加约 1.4 秒闭口停留；
- 内容：三个典型信号、三组症状总览、角色与总览并列、进入“疏风清热”节点。

## 画面节点

| 当前时间 | 画面行为 |
|---:|---|
| 0.00–4.18s | 数字人居中提示“三个典型信号”，口型随克隆旁白变化 |
| 4.18–5.30s | 标题及三组症状板依次展开 |
| 5.30–8.74s | 第一组“全身症状”强调 |
| 8.74–13.66s | 第二组“呼吸道症状”强调 |
| 13.66–18.22s | 第三组“其他症状”强调 |
| 20.10s | 数字人直接出现在左侧，三组症状板缩放并移到右侧 |
| 22.22s | 直接切换到“调理核心 / 疏风清热”节点 |
| 26.10–27.50s | 数字人保持闭口微笑 |

## 手动布局参数

`poc/gold-sample/src/reference-symptoms-project.tsx` 顶部的 `LAYOUT` 集中管理：

- 标题 X/Y/宽度；
- 症状板组 X/Y/宽度、单行高度和行间距；
- 居中数字人 X/Y/宽高；
- 左侧数字人 X/Y/宽高；
- 分栏状态下症状板组 X/Y/缩放；
- 调理节点人物与信息板 X/Y/宽高。

当前仍通过代码数值修改，但参数结构已经适合映射为网页画布拖拽、方向键微调和右侧属性栏数值输入。AI 只负责初排；人工锁定后的布局参数不应被后续生成覆盖。

## 输出与验证

- 视频：`production-library/validation/video/reference-typical-symptoms-replica.mp4`
- 接触表：`production-library/validation/video/reference-typical-symptoms-contact-sheet.png`
- 克隆旁白：`poc/gold-sample/public/reference-audio/qwen-cloned-symptoms-27s.wav`
- 回听转写：`poc/reference-replica/reference-analysis/audio/qwen-cloned-symptoms-27s-review.txt`
- 规格：1920×1080、30fps、H.264/AAC、27.50 秒
- 检查：TypeScript 类型检查通过；未检测到黑场；片尾保留闭口嘴型。

## 生产插图库升级

2026-07-29 起，本段不再使用从参考视频裁切的 11 张症状图。参考截图仅保留在分析目录用于风格与构图对标。

- 风格母版：`pharmacy-health-cartoon-v1`，由用户选择“发热”候选 B；
- 正式主图：`assets/component-library/symptoms/*/master/`；
- 编辑器缩略图：`assets/component-library/symptoms/*/thumbnails/`；
- 注册表：`assets/component-library/symptoms/registry.json`；
- 生成配方：`assets/component-library/symptoms/symptoms-v1-generation-recipes.md`；
- 视频运行资产：`poc/gold-sample/public/production-symptoms/`。

11 张插图均为重新生成的 1254×1254 PNG。标题胶囊图标已改为代码绘制，因此当前症状卡画面不再依赖参考截图像素。
