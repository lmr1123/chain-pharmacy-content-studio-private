# 可编辑视频 · 对接项目 Revideo 编辑器

权威业务操作：`docs/revideo-business-editor-usage.md`  
本包已按 **速福达同一套** 接入（不自建 HTML 编辑器）。

---

## 启动

```bash
cd production-library/validation/courseware/product-courseware-4-faithful-replica-v1
npm run start:editor
# → http://127.0.0.1:9012/
```

前台调试：

```bash
npm run start:editor:fg
```

右侧 **「画面属性」** 面板：点选 `editable:cw4:*` 图层 → 改字 / 换图 / 位移缩放 → **导出视频**。

### 编辑器内动效（2026-08-03）

对齐 **辅酶Q10 / 礼风热证** 业务编辑器：动效在 `src/project.tsx` 的 Revideo 时间轴上播放（`easeOutBack` 入场、`loop` 箭头向右脉冲、S05 手绘叉等），与可编辑补丁并行。

| 场景 | 编辑器可见动效 |
|------|----------------|
| S01 | 杂志弹入、列表错落、黄绿 » 轻跳 |
| S04–S06 | 图标序贯 `popIn`；红箭头 **沿指向方向** 循环；表头白箭头轻跳 |
| S05 | 手绘叉弹出 → 护肤女出现后叉淡出 |
| S06 | 原手臂图 + 轻 scale 呼吸 |
| S00/S03/S10… | 主视觉入场 stagger |

**预览**：时间轴播放 / scrub 即可看动效。点选图层时建议停在终态附近。  
**成片 MP4** 仍以 PIL 多帧轨为准（签样交付）；编辑器导出走 Revideo 渲染时也会带上上述动效。

### 旁白音频（必对）

- 轨：`public/narration.mp3`（工作轨；片段改稿后更新）。原始参考保留为 `web/reference-narration.mp3`
- **每一页** `makeScene2D` 都挂 `<Audio src="/narration.mp3" play volume={1} time={scene.start} />`
- `time` = 该场景在全片时间轴上的绝对起点，切页/scrub 后继续跟口播
- **禁止**只在 S00 挂音频

### 片段编排 · 旁白（1+2+3）

右侧面板 **「片段编排 · 旁白」**（详见 `docs/segment-studio-v1.md`）：

1. **删/恢复片段** → 时间轴跳过/恢复  
2. **改讲解稿 + 重生成旁白** → 默认 **Qwen3 克隆参考声线**（可选手动 edge-tts）→ 时长回填  
3. **应用并重建成片** → 静帧 hold 对齐新时长 + 拼旁白  

改完后 **Cmd+Shift+R** 刷新编辑器。克隆依赖本包 `.venv-tts`（见 `docs/segment-studio-v1.md`）。

**扩展段现状（2026-08-03）**：S12–S13 关联用药已克隆有声；插在 **适宜人群之后、三大核心功效表（S11）之前**。S14 四列表总表已删。prompt 的 `ref_audio`/`ref_text` 必须对齐，否则每段开头会泄漏「最大的十种…」（`lesson.qwen3-clone-prompt-audio-must-match-ref-text`）。regen 后做离线 ASR 再交付。

---

## 结构（对齐速福达）

| 文件 | 作用 |
|------|------|
| `content-model.json` | 文案 / 分镜 / 槽位 |
| `layer-manifest.json` | 稳定 `editable:cw4:{page}:{role}` |
| `src/project.tsx` | 签样版式双轨：`scene-stills-editor-bg`（无字/无主图底板）+ 同坐标/字号 `editable:cw4:*` 文字与图 |
| 视觉权威 | `scripts/export-full-film-video.py`（PIL 调优字号/排版）；成片仍出完整静帧 |
| `src/content.ts` | `K` / `T` / 资源路径 |
| `src/editor/apply-editable-patches.ts` | 与金样相同的补丁回放 |
| `poc/gold-sample/src/cw4-courseware-editable-project.tsx` | Vite bridge（挂 wind-heat 插件） |
| `scripts/start-cw4-editor.mjs` | 编辑器服务（端口 **9012**） |
| `production-library/validation/revideo-editability/courseware-4/` | 候选状态 / 导出记录 |

---

## 金样门禁 · 双轨静帧（强制）

> Lesson：`lesson.editor-bg-must-omit-editable-layers-gold-template`  
> **后续打造任何金样可编辑模版都必须遵守，不得只给首页可编。**

| 轨 | 路径 | 允许烧录 | 禁止 |
|----|------|----------|------|
| **成片静帧** | `out/scene-stills/` | 签样全文 + 主图 + 包装 + 图标 | —（成片视觉权威） |
| **编辑器底板** | `out/scene-stills-editor-bg/`（`omit_text=True`） | 仅 chrome：丝绸底、卡片壳、表格线、「+」锚点、装饰几何、非可编装饰 | **任何** `editable:*` 角色（正文、章节、包装、主视觉、图标…） |

### 固定检查清单

- [ ] `layer-manifest` 中每个 text/image 可编角色，在 `src/project.tsx`（或等价）有对应 `Txt`/`Img` 且 `key=editable:…`
- [ ] 导出 editor-bg 时 **不再** `paste_c` / `draw_text` 这些角色（与成片轨分支）
- [ ] 长文：`width` + `textWrap={true}`（总结表、关联 note 等）
- [ ] **一页一 `makeScene2D`**；禁止同场景多页 `opacity=0` 冒充翻页（插件只点 `absoluteOpacity>0.01`）
- [ ] 同场景 **禁止重复 node key**（重复 chapter 会 `Duplicated node key`）
- [ ] 点选前插件能同步 `PlaybackManager.currentScene`（多场景 scrub 不粘首页）

成片权威 = 完整静帧 + 旁白；**编辑态权威** = editor-bg + 全量 editable 层。

---

## 导出视频

编辑器内「导出视频」会调用：

```bash
python3 scripts/export-full-film-video.py
```

产出签样静帧成片：`out/商品培训课件4_保真复刻_全片_v1.mp4`（视觉以 PIL 静帧为准）。

也可 CLI：

```bash
npm run export:video
```

**PPTX**：本包禁用（用户要求停做 PPT）。

---

## 改内容源后重建

```bash
# 改 content-model.json 或替换 assets/generated/*
python3 scripts/export-full-film-video.py   # 更新 stills
# 刷新编辑器预览
```

---

## 与风热证 / 速福达对照

| 项目 | 端口 | 图层前缀 |
|------|------|----------|
| 风热证 | 9000 | `editable:…` |
| 速福达 | 9010 | `editable:sufuda:…` |
| **课件4** | **9012** | **`editable:cw4:…`** |

操作手势与面板相同，见 `docs/revideo-business-editor-usage.md` §3–4。
