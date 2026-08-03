# 交给其他模型执行：K03／K13 高质量重做合同

> 这是一份可直接转发的执行任务。它不是创意建议，也不是让模型自由选择版式。

> **用途更正（2026-08-01）：** 本合同提供了目标样片、派生素材、正式声音、时码和逐镜状态，
> 只能用于验证“受控规格实现能力”，不能用于判断模型能否从业务原始输入独立创作。若要测试模型
> 独立能力，请使用同目录的 `OTHER_MODEL_ZERO_START_BENCHMARK.md`，不要执行本合同。

## 一、先说结论：模型是否真的能做到

能，但有条件。

- 如果模型能读取工程、编写 Revideo／Remotion／Canvas 动画、运行渲染、播放成片并根据抽帧返工，
  完成这两个片段的概率较高。因为旁白、资产、时码、视觉状态和目标样片已经明确，不再要求它独立发明风格。
- 如果模型只会生成页面、PPT、静态设计稿或只做一次代码输出而不播放返工，它做不到。
- 即使是强代码模型，也不能可靠地自证“审美已经合格”。技术指标可自动检查，教学语义和画面节奏仍需人审。
- 对当前两个片段，我估计强执行模型在严格合同下能达到目标的 **75%～90%**；如果继续让它自由设计整片，
  成功率仍可能低于 **30%**。这不是模型不会写动画，而是开放式任务会诱导它优先追求覆盖率和代码复用。

正确方法不是永远逐镜人工制作，而是：**代表片段逐段过门禁 → 从通过的成品中抽象组件 → 再批量扩展**。

## 二、为什么上一轮做不到

1. 任务要求“58 个微镜头全部完成”，完成率成为最容易优化的目标。
2. R01～R10 是通用运动名称，不是具体的教学状态，模型用轻移、淡入、圆点移动也能宣称完成。
3. 一个全局共享图层池服务所有场景，人物、工艺、商品组合最终都长成同一种页面。
4. 正式旁白没有先进入时间线，动画无法准确响应“醒来、提取、浓缩”等动词。
5. 验收只检查 ID、文件、像素变化和黑场，没有检查动作是否改变观众的理解。
6. 没有明确停止条件，模型做完首个差镜头后仍继续批量复制错误。

## 三、本次工作方式

按两个门禁顺序执行，不允许一次重做整片：

1. **门禁 A：K03 人物情境。** 完成成片、接触表和自检；未通过不得进入 K13。
2. **门禁 B：K13 工艺流程。** 完成成片、接触表和自检；未通过不得抽象模板。
3. 两段都通过后，只提交“可复用组件候选清单”，不得继续自动扩展 K01～K18。

这不是每句话单独做一条视频。每个片段必须是一个连续场景，三句旁白在同一教学世界中推进。

## 四、权威输入

工作区：`/Users/liminrong/Projects/chain-pharmacy-content-studio`

必须先读取：

- `AGENTS.md`
- `skills/pharmacy-template-replication/SKILL.md`
- `production-library/validation/reference-analysis/pfizer-antacid-h2-ppi-v1/shot-breakdown-v1.md`
- `production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/remake-comparison-v1/INDEPENDENT_EVALUATION.md`
- `production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/remake-comparison-v1/semantic-action-contract.json`

目标质量样片，只用于视觉与节奏比对：

- `.../remake-comparison-v1/k03-after.mp4`
- `.../remake-comparison-v1/k13-after.mp4`

正式音频，必须直接使用，不得重新 TTS 或改速：

- `.../remake-comparison-v1/audio/k03-mix-final.wav`
- `.../remake-comparison-v1/audio/k13-mix-final.wav`

主要资产：

- `poc/gold-sample/public/kekang-remake-v1/k03-sleep-wide.png`
- `poc/gold-sample/public/kekang-lingzhi/v3/ganoderma-hero-v3.png`

主风格只允许：`style-pack.kekang-pfizer-green-candidate-v1`。

## 五、必须实现的画面

逐条执行 `semantic-action-contract.json`。以下是最核心的不可替代要求。

### K03

- 0.00～2.80s：完整卧室建立，清醒人物为主角；眼部提示一次，时钟推进。
- 2.80～6.63s：不换页；1:00、3:00、5:00 依次形成时间历史，时钟持续转动。
- 6.63～10.47s：夜色逐步转为晨光，时间历史降权保留，疲倦／精神下降成为结果。
- 10.47～至少 11.62s：保持最终状态，旁白尾音完整。

### K13

- 0.00～2.87s：灵芝原料颗粒必须实际进入第一提取罐，罐内发生液体／气泡变化。
- 2.87～6.73s：提取物必须沿管路进入第二浓缩罐；第一罐保留，第二罐液位和颜色变化。
- 6.73～11.47s：浓缩状态收束并形成无品牌输出；证据门禁最后才出现。
- 11.47～至少 12.62s：保持工艺全景和证据提示，旁白尾音完整。

## 六、明确禁止

- 禁止复用 production-v2 的全局标题＋说明段落＋门禁 chip＋底栏结构。
- 禁止把每句旁白做成独立卡片或整页切换。
- 禁止用圆点沿折线移动代替提取、浓缩或材料变化。
- 禁止仅靠透明度、缩放、上下浮动宣称完成 performance 动作。
- 禁止增加 Pfizer 像素、品牌包装、Logo、专利号、吸收率或未经批准的疗效宣称。
- 禁止改写旁白、重新配音、分句 TTS 或通过大幅变速塞进画面。
- 禁止覆盖 `remake-comparison-v1` 已有文件。
- 禁止在两个片段未通过前创建新的通用 recipe 或扩展完整课程。

## 七、输出位置和文件

所有新产物写入：

`production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/other-model-remake-attempt-v1/`

至少包含：

- `k03-remake.mp4`
- `k13-remake.mp4`
- `frames/k03-contact.png`：8 个均匀时刻
- `frames/k13-contact.png`：8 个均匀时刻
- `frames/K03-S01-entry.png`、`performance.png`、`exit.png`，K03-S02／S03 同样输出
- K13-S01／S02／S03 同样输出 entry／performance／exit
- `qa-report.json`
- `SELF_REVIEW.md`
- `review.html`
- 独立源工程和渲染入口

不得把中间帧或失败稿写进 settled 模板目录。

## 八、逐镜头验收问题

对每个 S01～S03，SELF_REVIEW 必须逐项回答并附具体截图路径：

1. 这句旁白的核心动词是什么？
2. entry 与 exit 的教学状态发生了什么变化？
3. 哪个对象从上一镜被继承到这一镜？
4. 如果关闭字幕和声音，审片人能否描述主要变化？
5. 画面中是否存在只为“看起来在动”而运动的对象？有则删除。
6. 是否误加了未经授权的医学、专利、品牌或商品信息？

以下回答均视为失败：

- “元素从左侧进入并放大。”
- “节点依次点亮。”
- “通过淡入突出重点。”
- “增加动态感／科技感／高级感。”

合格回答必须类似：

- “1:00、3:00、5:00 依次留下，构成同一夜多次醒来的历史。”
- “第一罐中的提取物进入第二罐，第二罐液位和颜色改变，说明材料已进入浓缩阶段。”

## 九、技术验收

- 1920×1080、30fps、H.264/AAC。
- K03 不短于音频 11.618s；K13 不短于音频 12.623s。
- 完整解码，无黑场，无标题或字幕越过安全区。
- 字幕逐句来自正式旁白；禁止正文型大段说明。
- 音频直接使用已批准 mix；若重新封装，响度仍为 -16±1 LUFS，True Peak ≤ -1 dBTP。
- 至少抽查 6 个时刻；不能只提交首尾两帧。

## 十、停止与返工规则

- K03 任一微镜头只能描述为“移动／淡入／变亮”，立即停止，不得继续 K13。
- 首次渲染后必须实际播放，不能凭代码和文件数量宣布完成。
- 与目标样片并排对比；若语义对象、动作链或声音时码缺失，修改后重新渲染。
- 最多允许两轮自主返工；两轮后仍不达标，在 SELF_REVIEW 中诚实标记 BLOCKED，不得伪报通过。
- 完成仅表示“待人审”，模型不得自行标记 user-approved 或 production-validated。

## 十一、可直接复制给模型的执行指令

```text
工作区：/Users/liminrong/Projects/chain-pharmacy-content-studio

请严格执行：
production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/remake-comparison-v1/OTHER_MODEL_K03_K13_REMAKE_CONTRACT.md

本次只重做 K03 和 K13，不得扩展全片。先完成并自检 K03；K03 的三组
entry/performance/exit 能说明“入睡困难 → 多次夜醒 → 次日疲倦”后，才开始 K13。

必须直接使用合同指定的正式混音，不得重新 TTS；必须按
semantic-action-contract.json 实现开始状态、语义动作和结束状态。

不得使用 production-v2 的通用页面骨架，不得用淡入、轻移、节点亮起或圆点走线替代语义动作。
必须播放成片、逐镜抽帧、并排对照目标样片并至少自主返工一轮。

所有结果只写入合同指定的 other-model-remake-attempt-v1 目录，不得覆盖现有整改样片。
最终交付两个 MP4、逐镜三帧、8 帧接触表、qa-report.json、SELF_REVIEW.md、review.html 和源工程。
模型只能报告“待人审”，不得自行报告金样通过。
```
