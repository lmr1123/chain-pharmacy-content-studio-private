# 商品培训模板 30 秒代表性签样

## 产物

- 成片：`production-library/validation/video/product-training-template-signoff.mp4`
- 结构化输入：`poc/gold-sample/product-training-signoff.json`
- 场景工程：`poc/gold-sample/src/product-training-project.tsx`
- 渲染入口：`poc/gold-sample/src/render-product-training.ts`
- 旁白：`poc/gold-sample/public/product-training-audio/product-training-signoff-30s.wav`
- 关键帧：`production-library/validation/video/product-training-signoff-qa/`

## 场景

| 时间 | 场景 | 验证目标 |
| ---: | --- | --- |
| 0.00–9.40 秒 | 商品英雄页 | 商品名、通用名、规格、包装和三项标签独立可替换 |
| 9.40–19.40 秒 | 核心功效页 | 标题、机制节点、审核结论和脚注分层 |
| 19.40–30.00 秒 | 产品特点与证据 | 工艺、原料、医疗资料分别记录来源、版本和审核状态 |

## 资产说明

项目中没有能气朗包装、企业 Logo 和真实证据资料原图。本签样使用新生成的无品牌辅酶 Q10 通用包装示意：

- 主资产：`assets/component-library/products/generic-coq10/`
- 生成方式：内置 `imagegen`
- 参考视频像素：未使用
- 真实品牌包装：未使用
- 包装内文字：未生成，商品信息由模板文字层独立绘制

该资产可以用于内部模板结构签样，不能冒充真实商品包装，也不能直接用于对外广告或销售物料。接入内部批准的包装原图后，仅需替换结构化输入中的 `product.packshot`。

## 旁白与字幕

- 旁白由本机 Qwen3-TTS 零样本链路生成，未上传第三方。
- 六句旁白分别拟合既定时间窗，总音轨 30.00 秒。
- 最后 0.30 秒为数字静音，字幕保持到末帧。
- 本地 Whisper 回听确认主体语义完整；对“辅酶”仍可能输出同音字，因此正式专业词必须继续以审核字幕为准。

## 验收结果

- TypeScript 类型检查：通过；
- MP4 完整解码：通过；
- 规格：1920×1080、30fps、H.264/AAC；
- 时长：30.00 秒；
- 黑场检查：未检出；
- 商品英雄页、核心功效页、产品特点页关键帧：人工复检通过；
- 末帧字幕、卡片边界和内部声明：人工复检通过。

## 下一步替换项

1. 内部批准的商品包装高清原图；
2. 企业与商品品牌 Logo；
3. 工艺、原料、说明书、文献或检测资料原图；
4. 经药师与合规法务确认的正式商品文案；
5. 正式商品培训 PPT 页面的布局映射。
