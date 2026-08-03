# 片段编排工作室 v1（删段 · 改旁白 · 时长适配）

> 课件4 可编辑视频：`npm run start:editor` → :9012  
> 状态：已接入右侧「片段编排 · 旁白」面板

---

## 能力一览

| 能力 | 操作 | 实现 |
|------|------|------|
| **1 删/恢复片段** | 选中片段 →「删除此片段」/「恢复此片段」 | `enabled=false` 保留快照；时间轴跳过 |
| **2 改讲解稿 + 重生成旁白** | 改文案 →「保存文案」→「重生成旁白」 | **默认 Qwen3 克隆参考声线** → edge-tts → macOS `say` |
| **3 时长与画面一致** | 「应用并重建成片」 | 画面时长 = 旁白时长 + 0.18s hold；静帧拼接；字幕按句切分 |

---

## 数据流

```
out/segment-studio/state.json     ← 编排状态（顺序 / 删隐 / 文案 / TTS 文件）
content-model.json                ← 回填 start/end/subtitles/narration
web/working-narration.mp3         ← 工作旁白轨（不覆盖 reference-narration.mp3）
public/narration.mp3              ← 编辑器播放
export-full-film-video.py         ← 静帧成片
```

`reference_start` / `reference_end` 固定绑**原始参考轨**时码，删段后仍可从原 VO 切片还原。

---

## CLI

```bash
cd production-library/validation/courseware/product-courseware-4-faithful-replica-v1

python3 scripts/segment_studio.py init
python3 scripts/segment_studio.py api-list
python3 scripts/segment_studio.py hide --id S05_benefit_2
python3 scripts/segment_studio.py enable --id S05_benefit_2
python3 scripts/segment_studio.py set-narration --id S12_related_1 --text "……"
python3 scripts/segment_studio.py regen-tts --id S12_related_1 --backend clone
python3 scripts/segment_studio.py rebuild --film
```

### 声线后端

| `--backend` | 说明 |
|-------------|------|
| `auto`（默认） | Qwen3 克隆 → edge-tts → say |
| `clone` | 强制参考声线（见下方 **克隆 prompt 门禁**） |
| `edge` | Microsoft edge-tts 通用中文 |
| `say` | macOS 系统语音 |

克隆模型：`mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16`（本机 HF 缓存）。  

**本机环境**（首次）：

```bash
cd production-library/validation/courseware/product-courseware-4-faithful-replica-v1
python3 -m venv .venv-tts
.venv-tts/bin/pip install mlx-lm soundfile numpy
.venv-tts/bin/pip install -e ../../../third_party/mlx-audio
# 或：.venv-tts/bin/pip install -e /path/to/chain-pharmacy-content-studio/third_party/mlx-audio
```

编辑器与 CLI 优先用 `.venv-tts/bin/python` 跑 `segment_studio.py`。  
成片导出（`rebuild --film` / `export-full-film-video.py`）用 **系统 `python3`**（PIL），勿与 TTS venv 混用导致缺依赖。

---

## 克隆 prompt 门禁（2026-08-03 踩坑后强制）

> Lesson：`lesson.qwen3-clone-prompt-audio-must-match-ref-text`  
> 现象：S12/S13（及已删的 S14）每段开头曾循环「最大的十种健康食品…」

| 项 | 规则 |
|----|------|
| **ref_audio ↔ ref_text** | 必须同一完整句；按 **词级 ASR 时码** 切片，禁止音频截在半句而文本写完整句 |
| **课件4 锁定值** | `ss=2.30` · `t=5.55` · text=`美国《时代杂志》评选的对人类健康贡献最大的十种健康食品。` |
| **缓存** | `out/segment-studio/reference-prompt.wav` + `reference-prompt.meta.json`；ss/t/text 任一变更自动重切 |
| **验收** | 每段 `regen-tts` 后离线 ASR：**开头 3s** 不得含 prompt 尾句；再 `rebuild --film` |
| **扩展段** | `business_extension` 用 `audio_source=tts`；勿对参考 EO-VO 之后做 `reference_slice` 假装有声 |

错误示范（已废弃）：`-ss 0.58 -t 5.4` → 实际只到「贡献」，模型补念「最大的十种…」。

---

## HTTP API（仅课件4 编辑器）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/__cw4_segments/list` | 片段列表 |
| POST | `/__cw4_segments/hide` | `{id}` 删除 |
| POST | `/__cw4_segments/enable` | `{id}` 恢复 |
| POST | `/__cw4_segments/set-narration` | `{id,text}` |
| POST | `/__cw4_segments/regen-tts` | `{id,text?,backend?}` backend=`auto\|clone\|edge` |
| POST | `/__cw4_segments/rebuild` | `{film?:true}` 回填时间轴并重建成片 |

---

## 使用顺序（推荐）

1. 打开编辑器，右侧找到 **片段编排 · 旁白**
2. 点选片段 → 改讲解稿 → **重生成旁白**（自动回填时长）
3. 需要删段：选中 → **删除此片段**
4. **应用并重建成片**（写 content-model + 拼旁白 + 导出 MP4）
5. **Cmd+Shift+R** 刷新页面，加载新时间轴与旁白

---

## 约束与门禁

- **默认优先 Qwen3 克隆参考声线**（与参考旁白同提示音）；失败才回退 edge-tts。
- 参考段改稿后内容变、声线尽量保持；扩展段（原静音）同样可用克隆声补录。
- 画面为静帧 hold：时长变长 = 停更久；变短 = 裁 hold。无剪映级曲线重定向。
- 语速加速上限 **1.18×**（当前策略优先**拉长画面**，不默认压旁白）。
- 重建后必须刷新编辑器；未刷新仍听旧轨。

---

## 与图层编辑的关系

| 图层补丁（原能力） | 片段编排（本工作室） |
|--------------------|--------------------|
| 字/图/位移/透明度 | 分镜结构、旁白、时长 |
| `current-candidate.json` | `out/segment-studio/state.json` |
| 不改时间轴 | 改时间轴并重建成片 |
