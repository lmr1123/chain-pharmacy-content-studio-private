# 症状插图 v1 生成配方

## 公共提示词

```text
Use case: scientific-educational
Asset type: reusable square health-education symptom illustration component
Style anchor: pharmacy-health-cartoon-v1 approved master
Style: friendly flat 2D Chinese pharmacy-training cartoon; medium dark-brown outline;
rounded simplified anatomy; flat cel colors; restrained soft shading.
Composition: square 1:1; centered; 10% safe margin; readable at 150px.
Constraints: new original artwork; no reference pixels; no text, label, logo,
watermark, extra person, photorealism, 3D, horror or UI border.
```

## 组件变量

| 组件 | 主体 | 关键动作/表达 | 背景与符号 |
|---|---|---|---|
| 发热 | 青年患者 | 面部潮红、疲惫、汗滴 | 珊瑚红、热浪 |
| 口渴 | 同一患者系统 | 双手持水杯靠近嘴部 | 淡黄、水滴 |
| 嘴巴干 | 下半脸特写 | 干燥嘴唇和舌面 | 桃色、干燥线 |
| 心里烦躁 | 同一患者系统 | 双手扶头、紧张眉眼 | 蓝灰、折线 |
| 喉咙肿痛 | 同一患者系统 | 手扶咽喉、局部红色 | 天蓝、疼痛折线 |
| 咳嗽 | 同一患者系统 | 弯肘遮挡咳嗽、手扶胸 | 天蓝、气流 |
| 痰黄 | 症状符号 | 黄色黏稠液滴 | 淡黄、呼吸曲线 |
| 鼻涕黄稠 | 侧脸特写 | 单侧黄稠鼻涕 | 薄荷蓝、气流 |
| 舌头红 | 舌象特写 | 舌体均匀偏红 | 暖灰、无装饰 |
| 舌苔黄 | 舌象特写 | 舌中后部薄黄苔、边缘红 | 薄荷蓝、无装饰 |
| 大便干结 | 症状符号 | 分离硬便球、干裂纹 | 米色、干裂纹 |

## 生产规则

- 每个不同组件使用独立生成任务，不用同一提示词随机抽取；
- 人物类引用已选 B 母版作为角色与画风锚点；
- 参考截图只提供症状语义，不作为编辑目标；
- 主图归档后生成 300×300 编辑器缩略图；
- 未经公司药师审核的医学内容状态不得标记为 `approved`。
