# 桑菊薄荷饮组件 v1

- 主文件：`master/sangju-mint-tea-v1-magenta.png`
- 透明文件：`transparent/sangju-mint-tea-v1.png`
- 缩略图：`thumbnails/sangju-mint-tea-v1.png`
- 生成方式：Codex 内置 `imagegen`
- 素材来源：全新生成，不包含参考视频截图

提示词：

> 生成一只青瓷茶杯和茶托的高质量单体素材，杯中是浅黄绿色热茶，清楚可见一片桑叶、一朵白菊花和几片薄荷叶。正面略俯视构图，物体完整，商业健康科普课件质感，轮廓干净，光线柔和。背景必须为纯洋红色抠图底，无文字、无水印、无蒸汽、无阴影落到背景。

处理：

- 使用 `remove_chroma_key.py` 的 border 自动取色、soft matte 和 despill 生成透明 PNG。
- 蒸汽不烘焙进图片，渲染时作为独立动效图层，便于控制速度、透明度和位置。
