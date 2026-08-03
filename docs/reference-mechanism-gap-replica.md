# 风热证 28–43.84 秒机理段复刻

## 绑定

- `template.health-reference-tech-v1`
- `style-pack.reference-medical-tech-v1`
- `asset-series.mechanism.reference-medical-tech-v1`
- `voice.reference-pharmacist-qwen-v1`

本段为独立补段，没有修改或拼接任何已验收前序成片。参考片 43.84 秒起已由“典型症状”独立工程覆盖，因此 43.84–45.00 秒只用于衔接核验。

## 镜头

1. 中央药师短停后直接换位至右侧扩音器姿势。
2. 相对 0.45–9.78 秒：风邪、加号、热邪和平滑蓝青半透明全身人体依次组装；风热持续向人体聚拢，人体表面扫描线往复通过并伴随柔和脉动。
3. 相对 9.78–11.74 秒：药师直接换到左侧，右侧显示“体表受邪”肺部机制图；肺部红光呼吸，两张紫蓝体积邪气相位在人体外侧交叉过渡，并分别上涌、漂移和明暗呼吸。
4. 相对 11.74–12.86 秒：切换为正面咽喉聚焦，红光在咽喉局部连续收放。
5. 相对 12.86–15.84 秒：切换为侧面喉部与气道剖面，喉部红光脉动，气流粒子沿气道方向循环。

四张人体图及两张体积邪气背景均为重新生成的原创医学可视化资产。用户截图只用于细节等级、构图和症状区域参考，不含截图像素；红光、邪气、扫描线和气流均为独立动画层。邪气已从 Unicode 波浪线返修为带透明层次、高光和羽化边缘的紫蓝体积纹理。

## 声音与 QA

- 三个完整语义段生成，统一速度系数约 `0.976`。
- 段间 `35ms` 交叉衔接，去点击并归一化至约 `-16 LUFS`。
- 母带为 24kHz 单声道，成片为 48kHz AAC 双声道。
- 离线 Whisper 覆盖全部台词；“证/症、邪/鞋”为同音转写，不写回审核字幕。
- 成片：1920×1080、30fps、H.264/AAC、477 帧、封装约 15.90 秒。
- TypeScript、完整解码、黑场、关键帧、末帧闭口和动态差分检查通过。
- 四个局部动态裁切区 SSIM 分别为 `0.939708`、`0.979781`、`0.998065`、`0.984879`，均小于 1；咽喉段因只改变小范围光晕，整体裁切区差异较小但连续可见。

## 产物

- 视频：`production-library/validation/video/reference-mechanism-gap-replica.mp4`
- 四镜头动态接触表：`production-library/validation/video/reference-mechanism-gap-qa/dynamic-v2-contact-sheet.png`
- 人体 200% 边缘：`production-library/validation/video/reference-mechanism-gap-qa/dynamic-v2-body-200pct.png`
- 局部动态差分：`production-library/validation/video/reference-mechanism-gap-qa/dynamic-v2-motion-evidence.md`
- 体积邪气参考/旧版/新版对照：`production-library/validation/video/reference-mechanism-gap-qa/volumetric-mist-v1/reference-old-new.png`
- 体积邪气动态接触表：`production-library/validation/video/reference-mechanism-gap-qa/volumetric-mist-v1/contact-sheet.png`
- 体积邪气局部预览：`production-library/validation/video/reference-mechanism-gap-qa/volumetric-mist-v1/volumetric-mist-preview.mp4`
- ASR：`production-library/validation/video/reference-mechanism-gap-qa/asr/`
- 平滑医学人体四镜头资产：`assets/component-library/mechanisms/wind-heat-dynamic-v1/`
- 资产接触表：`assets/component-library/mechanisms/wind-heat-dynamic-v1/contact-sheet.png`
- 系列扩展规范：`assets/component-library/mechanisms/reference-medical-tech-series-v1/series.json`
- 新成员清单模板：`assets/component-library/mechanisms/reference-medical-tech-series-v1/asset-template.json`
