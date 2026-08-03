# 可可康完整视频 · 微镜头强约束生产包 v2

这套文件用于解决“其他模型把一个章节做成一页 PPT”的问题。执行模型不再自行把章节转换为页面，必须按 `microshot-timeline.json` 的微镜头顺序实现约 4 分钟的连续视频，并完成全片正式语音。

## 交付包组成

| 文件 | 用途 |
|---|---|
| `microshot-timeline.json` | K01–K18 的逐句、逐镜头、逐图层时间线合同 |
| `scene-recipes.md` | 动态构图、图层几何和动画语法 |
| `asset-manifest.json` | 现有候选素材、待生成插图、授权包装和禁用素材 |
| `narration-audio-plan.md` | 58 镜正式金样旁白、屏幕短文案、内容状态、音效和混音事件 |
| `formal-voice-script.md` | K01～K18 可直接生成的正式金样旁白与分章文件名 |
| `formal-voice-contract.json` | 18 个语义段、58 镜同步锚点、音色参数和声音验收交付物 |
| `EXECUTION_PROMPT.md` | 可直接交给其他模型的执行指令 |
| `build_handoff_v2.py` | 从锁定数据确定性生成 JSON／音频计划 |
| `validate_handoff_v2.py` | 拒绝一章一页、静态长停留和未审核内容误生产 |
| `validation-report.json` | 合同校验结果 |

## 执行顺序

```bash
python3 production-library/validation/reference-analysis/kekang-pfizer-framework-v1/handoff-v2/build_handoff_v2.py
python3 production-library/validation/reference-analysis/kekang-pfizer-framework-v1/handoff-v2/validate_handoff_v2.py
```

校验通过后，执行模型只能按以下顺序制作：

1. K01～K18 全片正式金样旁白与同步合同；
2. 58 微镜头完整分层 animatic；
3. 完整音画粗剪；
4. 医学／授权终稿到齐后替换对应内容与素材；
5. 完整绿色金样与 QA。

## 不得修改的规则

- 一章不是一页。一章必须由 2～6 个连续微镜头组成。
- 每个微镜头必须有独立的进入、场内表演、退场和下镜承接。
- 禁止连续展示全屏卡片、固定表格、整页栏目和整页推拉。
- 单个静态完成帧最长 2.2 秒；超过时必须有局部运动或镜头运动。
- 每个微镜头至少包含 4 个图层，并且至少一个非文字图层真实运动。
- 旁白句子绑定到微镜头，禁止整章旁白配一张静态画面。
- 医学／证据／授权状态与声音验收分开：全片必须生成正式质量的金样旁白，同时保留内容门禁，
  不把验证口径误标为最终批准结论。
- 唯一候选风格：`style-pack.kekang-pfizer-green-candidate-v1`。

## 设计结果由谁决定

颜色、字号、构图、转场、缓动、字幕样式和普通音效已经由本包约束，执行模型自行完成，不再询问用户。只有以下事项允许阻断并请求输入：

- 药师／合规批准终稿；
- 真包装、Logo、说明书、证据和工厂素材授权；
- 用户对全片金样声音、节奏和同步结果的确认。

## 输出位置

所有候选和 QA 只能写入：

```text
production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/
```

用户批准完整金样前，不得写入 `templates/settled/` 或正式注册表。
