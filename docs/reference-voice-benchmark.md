# 参考旁白基准与本地候选音色 A/B

## 测量结果

完整参考片旁白约 666 个汉字、有效时长约 177.22 秒，平均约 225.5 字/分钟。句内节奏连续，信息组之间保留约 0.5–0.64 秒的语义停顿。

| 指标 | 参考原声片段 | 本地候选 Tingting（200） |
|---|---:|---:|
| A/B 片段时长 | 8.52 秒 | 7.70 秒 |
| 平均响度 | -12.8 dB | -16.0 dB |
| 峰值 | -0.4 dB | -1.1 dB |
| F0 中位数（近似） | 296.3 Hz | 235.3 Hz |
| F0 10%–90%（近似） | 235.3–381.0 Hz | 162.1–320.0 Hz |

基频采用 40ms 窗口自相关估算，只用于候选音色的相对筛选，不等同于专业声纹鉴定。

## 判断

- 上一版 28.23 秒复刻样片直接使用参考原声，因此它不是声音克隆。
- macOS 本地候选音色可以离线生成新文案，但音高明显低于参考原声，片段也快约 0.82 秒，不能视为“音色复刻完成”。
- 当前样片已切换为本地 Qwen3-TTS 0.6B Base + MLX Audio 零样本克隆音频；以参考片中 8.34 秒人声为提示，本机生成新音频，未上传第三方服务。
- 八句旁白分别按参考字幕的起止时间生成，并以无变调时间伸缩拟合原时间窗，保留参考语速、停顿和画面节点。

## 克隆结果

| 指标 | 参考原声 | Qwen3-TTS 本地克隆 |
|---|---:|---:|
| F0 中位数（近似） | 296.3 Hz | 307.7 Hz |
| F0 10%–90%（近似） | 235.3–381.0 Hz | 224.3–393.4 Hz |
| 完整时间轴 | 28.10 秒 | 28.10 秒 |

最终克隆音轨已用本地 Whisper 全段转写复核。“痰”的发音问题已修正，审核字幕稿未改动；另生成了一句参考视频中不存在的新文案，证明输出不是原音轨的剪切重放。

## A/B 文件

- 参考原声：`poc/reference-replica/reference-analysis/audio/reference-ab.m4a`
- 本地候选：`poc/reference-replica/reference-analysis/audio/candidate-tingting-200.m4a`
- 声音提示：`poc/reference-replica/reference-analysis/audio/reference-clone-prompt.wav`
- 新句子克隆证明：`poc/reference-replica/reference-analysis/audio/qwen-clone-new-sentence.wav`
- 最终克隆旁白：`poc/gold-sample/public/reference-audio/qwen-cloned-reference-28s.wav`
- 基频测量脚本：`scripts/analyze_voice_pitch.py`
