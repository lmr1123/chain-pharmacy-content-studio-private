# 本机开源项目复用审计

## 推荐结论

生产核心优先采用 Revideo（MIT）作为程序化动画与批量渲染引擎；本机其他项目主要复用方法、动效配方或可选素材能力。许可证不清晰或标注为 `UNLICENSED` 的代码不进入生产核心。

| 项目 | 本机位置 | 审计结论 | 在本项目中的用途 |
|---|---|---|---|
| Revideo 0.11.0 | `poc/gold-sample/node_modules/@revideo/core` | MIT；直接复用 | 当前样片与后续批量 MP4 渲染核心 |
| video-shotcraft | `/Users/liminrong/Projects/video-shotcraft` | Apache-2.0；改造复用 | 镜头节奏、缓动、音效和逐帧 QA 方法 |
| open-design | `/Users/liminrong/Projects/open-design` | Apache-2.0；改造复用 | 设计令牌、组件规范和编辑器交互参考 |
| explainer-video | `/Users/liminrong/Projects/explainer-video` | `UNLICENSED`；只复用方法 | 配音先行、字幕时码、渲染 QA 流程；不复制生产代码 |
| ai-video-course | `/Users/liminrong/Projects/ai-video-course` | 工作流参考 | 批任务、素材处理、失败重试思路 |
| muyang-flat-animation | `/Users/liminrong/Projects/muyang-flat-animation` | 可选内容能力 | 非参考母版场景中的抽象概念 B-roll |
| gbro-collage-broll | `/Users/liminrong/Projects/gbro-collage-broll` | 可选内容能力 | 后续扩展拼贴 B-roll；不用于首阶段复刻 |
| HyperFrames | 本机已安装版本 0.6.46 | 未找到明确许可证；暂不接入 | 只有补齐许可证和维护性验证后再评估 |
| Qwen3-TTS 0.6B Base | `third_party/Qwen3-TTS` | Apache-2.0；本地复用 | 参考旁白零样本声音克隆 |
| MLX Audio | `third_party/mlx-audio` | MIT；本地复用 | Apple Silicon 本地 TTS 推理与音频生成 |

## 为什么不以 Remotion 作为当前核心

Remotion 技术成熟，但对较大规模营利性企业存在商业许可边界。当前用户明确无采购计划，因此首阶段不把它作为生产核心；若未来公司决定采购，可重新评估其生态、编辑器接入和渲染服务。

## 数字人路线

数字人不是本次卡通药师复刻的替代物，而是可插拔场景类型：

- 卡通药师：使用分层角色、局部口型、语义动作片段；
- 真人数字人：后续可接已授权的私有化口型/数字人服务；
- 两者共用同一份结构化脚本、字幕时码和场景时间轴。

当前声音验证使用许可证明确的 Qwen3-TTS 与 MLX Audio，并在本机完成推理；参考人声不上传第三方。来源不明的声音克隆或人物肖像模型仍不进入默认工作流。

## 接入优先级

1. 保留 Revideo 渲染核心和当前已验证角色状态机。
2. 把母版、角色、字幕、卡片、机制图转成数据驱动组件。
3. 建立网页场景编辑器，只暴露受约束参数，不做通用动画软件。
4. 增加 PPTX/PDF 导出适配层；复杂视频动画在 PPTX 中降级为原生可编辑的入场/强调动画。
5. 将已验证的本地 Qwen3-TTS 克隆链路接入结构化旁白时码，并用同一时码驱动口型。

## 风险边界

- 开源许可证审计与药学内容合规是两件事；内容仍由公司药师和法务审核。
- AI 生成插图必须记录来源、提示词、模型和人工确认状态。
- 参考视频的 Logo、角色和原声仅用于公司内部复刻验证；对外使用需再次确认权利边界。
- 任何许可证不清楚的本机项目默认不进入可分发产物。
