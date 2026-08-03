# 可可康绿色培训视频：其他模型完整制作交接书

> **已废止：不得再作为执行入口。** 本文仍以章节为主要描述单位，容易被错误实现为“一章一页”。
> 新执行入口是 [`handoff-v2/EXECUTION_PROMPT.md`](handoff-v2/EXECUTION_PROMPT.md)，并且必须先通过
> `handoff-v2/validate_handoff_v2.py`。本文仅保留历史追溯。

> 版本：v1.0  
> 日期：2026-08-01  
> 用途：交给另一模型直接执行。  
> 当前目标：先完成 K08 有声视听片段，确认运动与声音语法；随后在内容／授权门禁齐全后，制作 K01–K18 完整绿色视频金样。  
> 本文是 production plan，不是医学审核稿，也不授权使用商品包装或旧课件截图像素。

## 0. 一句话任务

使用现有 Revideo 工程，将 Pfizer 案例提炼出的“聚焦式讲解语法”迁移到可可康绿色培训视频：

1. 先把当前无声 K08 片段升级为 **7～9 秒、带中性旁白和轻音效的完整视听片段**；
2. 用户确认后，按同一视觉与声音语法完成 **K01–K18、约 3～4 分钟的完整绿色金样**；
3. 完整金样通过后才能抽取正式 `style_pack`，不得先堆组件或批量生产。

## 1. 必须先读的文件

按以下顺序阅读，不要凭聊天记忆执行：

1. `AGENTS.md`
2. `skills/pharmacy-template-replication/SKILL.md`
3. `production-library/assembly-protocol.md`
4. `tasks/lessons.md` 中 2026-07-31、2026-07-30 的可可康相关教训
5. `production-library/validation/reference-analysis/pfizer-antacid-h2-ppi-v1/shot-breakdown-v1.md`
6. `production-library/validation/reference-analysis/kekang-pfizer-framework-v1/content-mapping-v1.md`
7. `production-library/validation/reference-analysis/kekang-pfizer-framework-v1/storyboard-v1.json`
8. `production-library/validation/reference-analysis/kekang-pfizer-framework-v1/可可康绿色视频金样_逐镜内容审核确认表_v1.docx`
9. `production-library/validation/reference-analysis/kekang-pfizer-framework-v1/animation-k08-v1/contract.json`
10. `poc/gold-sample/src/kekang-pfizer-k08-motion-project.tsx`

开始前必须查询生产库：

```bash
python3 scripts/query_production_library.py --type decision --text 金样
python3 scripts/query_production_library.py --text 可可康
python3 scripts/query_production_library.py --type voice --text 药师
python3 scripts/query_production_library.py --type component --text 字幕
```

## 2. 事实源与使用边界

| 层级 | 文件／内容 | 允许用途 | 禁止用途 |
|---|---|---|---|
| 内容骨架 | `content-mapping-v1.md`、`storyboard-v1.json` | 课程结构、镜头顺序、风险识别 | 当作审核终稿 |
| 内容审核 | 业务／药师填写后的逐镜确认表 | 正式旁白和屏显的唯一内容输入 | 未签字版本直接生产 |
| 叙事参考 | Pfizer 逐镜拆解 | 教学节奏、主体聚焦、分支关系、标签回扣 | 复制参考视频像素或品牌视觉 |
| K08 候选 | 当前 K08 TSX、MP4、`contract.json` | 绿色视觉与分支动画的起点 | 宣称正式 `style_pack` 已通过 |
| 公司旧 PPT | `production-library/themes/kekang-lingzhi-capsule/refs/` | 查找旧课件出现过的文字与页码 | 证明医学已审核；直接复用截图像素 |
| 商品资产 | 业务提供的高清包装、Logo、说明书、证据 | 正式商品镜头 | AI 仿包装、低清截图替代 |

### 必须停止继承的历史方向

- 旧 v4／v7 只保留追溯，不是当前金样基线。
- 不以“顾客说睡不好、门店怎么问、销售口诀、销售案例”作为主课叙事。
- 不把浅蓝商品视频模板与绿色 PPTX 风格包混绑。
- 不使用固定页眉、整页栏目、完整表格和底部整段念稿构成主要镜头。
- 不让数字人常驻角落念卡片。
- 不制作未经审核的受体、靶点、细胞结合、吸收倍数、治疗前后对比。

## 3. 项目绑定与目录

当前唯一候选绑定：

```json
{
  "project_id": "validation.kekang-green-gold-sample-v1",
  "theme_id": "theme.product.kekang-lingzhi-capsule",
  "template_reference": "pfizer-antacid-h2-ppi-v1:F01-F10",
  "style_pack_id": "style-pack.kekang-pfizer-green-candidate-v1",
  "style_pack_status": "validation-candidate-not-registered",
  "voice_id": "voice.reference-pharmacist-qwen-v1"
}
```

所有新产物放入：

```text
production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v1/
├── project-lock.json
├── approved-content.json
├── audio/
│   ├── narration/
│   ├── sfx/
│   ├── music/
│   └── mix-reports/
├── assets/
│   ├── authorized/
│   └── candidate/
├── renders/
│   ├── k08-audiovisual-v2.mp4
│   └── kekang-green-gold-sample-v1.mp4
├── qa/
│   ├── k08/
│   └── full/
└── review.html
```

禁止创建通用 `out/`、`output/`，禁止把验证稿放入 `templates/settled/`。

## 4. 阶段 A：K08 有声视听片段

### 4.1 成功标准

交付一个 7～9 秒的完整片段，用户直接播放时能够同时判断：

- 绿色视觉是否合适；
- 主体进入、双路径展开、标签聚焦的节奏是否清楚；
- 旁白、音效和字幕是否形成完整培训视频体验；
- 画面是否摆脱 PPT 翻页感。

### 4.2 允许使用的文字

旁白建议稿：

> 从灵芝主体，可以认识两类成分：灵芝多糖和灵芝三萜。

屏幕文字：

- 从灵芝主体，认识两类成分
- 灵芝主体
- 01 灵芝多糖
- 02 灵芝三萜
- 两条知识路径由同一灵芝主体展开
- 名称来自内部课件 · 局部运动语法验证 · 非医学审核结论

不要出现“核心有效成分”、功效、机制、治疗结果或人群适应结论，除非业务／药师在确认表中明确批准。

### 4.3 精确视听时间表

| 时间 | 画面 | 旁白／字幕 | 音效 |
|---:|---|---|---|
| 0.00–0.35s | 奶油白背景与浅绿环境形状稳定出现 | 无 | 极轻环境底音淡入 |
| 0.35–1.35s | 标题和灵芝主体进入 | “从灵芝主体” | 柔和上升 `whoosh`，不使用强科技冲击声 |
| 1.35–2.65s | 主体稳定，虚线轨道出现 | “可以认识两类成分” | 极轻圆环空气声 |
| 2.65–3.75s | 左侧绿色路径展开，01 标签进入 | “灵芝多糖” | 线条扫过声 + 轻木质／玻璃点音 |
| 3.75–4.95s | 右侧金色路径展开，02 标签进入 | “和灵芝三萜” | 第二个音色略低的点音 |
| 4.95–6.20s | 01、02 轮流聚焦 | 字幕完成，不追加医学解释 | 两次很轻的聚焦提示音 |
| 6.20–7.80s | 完成提示出现，主体与轨道低强度呼吸 | 无 | 尾音收束，环境底音淡出 |

允许根据自然旁白长度把总片长放宽到 9 秒；禁止把语音强制压到超过 1.18×。

### 4.4 声音规范

- 正式候选音色：`voice.reference-pharmacist-qwen-v1`，状态 `user-approved`。
- 按完整语义段一次生成旁白，不要把“灵芝多糖”“灵芝三萜”分别生成后硬拼。
- 默认整体语速 1.16×，上限 1.18×；若放不下，延长画面。
- 必须包含旁白和至少 3 个与动作同步的轻音效；背景音乐可选。
- 若没有来源清晰的音乐，宁可只用旁白＋音效，不使用网络抓取的版权不明音乐。
- 终混目标：综合响度 `-16 ± 1 LUFS`，True Peak 不高于 `-1 dBTP`。
- 人声始终比音乐／环境底音高至少 6 dB；音效不得遮盖成分名称。
- 片头／片尾各留 80～150ms 音频淡入淡出，检查爆音、硬切和直流偏移。

### 4.5 字幕规范

- 字幕必须来自最终旁白，不手写另一套句子。
- 单行优先，最多两行；每行建议不超过 18 个汉字。
- 字号 42～48px，白字＋深绿半透明底或深绿字＋奶油白底，只选一种并全片固定。
- 成分名称字幕时码必须与两个标签进入时刻一致。
- 不显示整段旁白，不使用 PPT 式底部讲义条。

### 4.6 动画修改范围

以 `poc/gold-sample/src/kekang-pfizer-k08-motion-project.tsx` 为起点：

- 保留：奶油白背景、品牌绿、暖金点缀、中央灵芝主体、双路径、椭圆标签。
- 调整：让路径和标签严格跟随旁白语义时码；字幕独立图层；音效按动作触发。
- 可优化：将中央候选灵芝图替换为同抽象层级的更高质量原创图，但必须先只替换一张并做视觉签样。
- 不新增：包装、功效图标、免疫盾牌、肝脏保护层、药师数字人。

### 4.7 K08 交付物

必须同时交付：

1. `renders/k08-audiovisual-v2.mp4`
2. 可重复渲染的 TSX 与 render 入口
3. 最终旁白文本和 TTS 参数
4. 分离的人声、音效、音乐／环境底音与终混文件
5. 字幕 SRT／VTT
6. `qa/k08/qa-report.json`
7. 0.5s、主体完成、双标签完成、01 聚焦、02 聚焦、末帧等至少 6 张 QA 帧
8. 可直接播放的 `review.html`

### 4.8 K08 通过条件

- 1920×1080、30fps、H.264/AAC；完整解码。
- 有可听人声，不再使用静音 WAV 冒充音频完成。
- 无黑场、乱码、截断、重叠和标签出安全区。
- 50% 预览时标题、标签、字幕均可读。
- 至少 3 个时间点证明路径、标签和聚焦动画真实发生。
- 音画事件偏差不超过 120ms。
- ASR 能正确识别“灵芝多糖”“灵芝三萜”；若误识别，先修发音再交付。
- 用户明确确认视觉、节奏和声音方向后，状态才可从 `candidate` 进入 `user-approved`。

## 5. 阶段 B：完整 K01–K18 绿色金样

### 5.1 启动门禁

以下条件未满足时，不得生成正式旁白或宣称完整金样完成：

1. 业务／药师完成逐镜确认表，K01–K18 均有明确“保留／改写／删除”和批准终稿。
2. 说明书、批准信息、功效与卖点证据齐全。
3. 可可康及联合方案商品的高清包装获得使用授权。
4. 大参林 Logo、工厂／产地／GMP 等材料获得使用授权。
5. K08 有声片段已获用户确认。

如果内容审核尚未完成，可以做结构 animatic 和空槽测试，但必须保留 `BLOCKED` 标记，不得填入推测性医学结论。

### 5.2 完整视频目标

- 目标时长：175～215 秒。
- 画布：1920×1080，30fps。
- 编码：H.264 High Profile + AAC，像素格式 `yuv420p`。
- 叙事主体：产品知识，不是门店销售话术。
- 结构：K01–K18，允许根据审核结果删除镜头；禁止为了凑满框架虚构内容。
- F05 受体／靶点配方明确不使用。
- 每镜只保留一个主要运动焦点。
- 数字人只在开场、章节引导、复杂解释或总结承担明确任务，不常驻。

### 5.3 视觉与运动宪法

#### 色彩

- 背景：奶油白 `#FBFAF5`、浅薄荷绿 `#EAF5ED`。
- 品牌主绿：`#07863F`。
- 深绿文字：`#103F2D`。
- 暖金点缀：`#C89532`，只用于第二成分、重点序号和收束提示。
- 风险红只用于审核门户，不进入正式培训画面，除非内容语义确需警示。

#### 排版

- 全画面安全边距至少 96px。
- 章节／主标题 64～84px；镜头标题 52～64px；标签 36～48px；字幕 42～48px。
- 标题不长期固定占据页眉；进入 1～2 秒后应让位给主体演绎。
- 主要知识通过空间关系、局部特写和逐步揭示完成，表格只用于 K18 最终复盘。

#### 动画

- 单元素入场 0.35～0.75 秒；场景转场 0.45～0.80 秒。
- 主体使用位置＋尺度＋遮罩组合，不只做透明度淡入。
- 关系建立用路径绘制、节点依次进入、焦点切换；不得一次铺满所有信息。
- 强调尺度 1.025～1.055；非当前项降低到 0.62～0.78 透明度，避免大幅跳动。
- 完成帧至少稳定 0.8 秒；末帧嘴型、字幕和主体都必须稳定。

#### 图片风格

- 统一为清晰、圆润、低细节的企业培训插画；不混入高写实 3D、科技蓝 HUD 或黑金商业海报。
- 人体、器官和医学过程若进入正式画面，必须使用授权或重生成的生产级栅格资产；禁止代码轮廓冒充正式医学视觉。
- 商品包装只能使用业务提供的真包装。

### 5.4 逐镜生产表

| 镜头 | 建议时长 | 教学任务 | 主要画面与唯一运动焦点 | 声音 | 当前门禁 |
|---|---:|---|---|---|---|
| K01 | 7–9s | 产品与课程开场 | 商品／灵芝主体进入，课程目标依次出现 | 药师开场＋主体 `whoosh` | 真包装、Logo |
| K02 | 9–11s | 三类状态总览 | 三个状态节点依次进入，不同时铺满 | 一句总览＋3 个轻提示音 | 医学用词 |
| K03 | 9–11s | 失眠状态 | 夜间→易醒→日间疲倦的连续状态变化 | 状态旁白＋低强度夜间环境音 | 医学用词 |
| K04 | 9–11s | 饮酒与肝脏负担 | 饮酒情境聚焦到肝脏负担，不画未审核体内机制 | 中性旁白＋沉稳转场音 | 高风险表述 |
| K05 | 8–10s | 免疫力低下状态 | 反复不适生活状态依次出现，不诊断疾病 | 中性旁白＋轻提示音 | 医学用词 |
| K06 | 9–11s | 三大产品方向 | 三类状态收束为三个方向标签 | 方向总览＋3 次标签音 | 功效口径 |
| K07 | 7–9s | 产品身份与功能主治 | 真包装特写＋OTC／规格／批准功能主治 | 说明式旁白 | 说明书、真包装 |
| K08 | 7–9s | 两类成分总览 | 复用已签 K08：主体→双路径→标签聚焦 | 已签旁白与音效语法 | “核心有效”称谓 |
| K09 | 11–13s | 灵芝多糖 | 只表现批准后的路径；不自行创造分子靶点 | 完整语义段旁白 | 高风险医学审核 |
| K10 | 11–13s | 灵芝三萜 | 只表现批准后的路径；不画抗肿瘤等未批准结论 | 完整语义段旁白 | 高风险医学审核 |
| K11 | 9–11s | 成分与三方向对应 | 两成分节点与三方向建立批准后的关系 | 关系总结＋路径声 | 医学因果 |
| K12 | 9–11s | 产地与含量 | 产地→原料→数据依次聚焦 | 数据旁白＋轻计数音 | 9.13g/100g 证据、产地图 |
| K13 | 9–11s | 双重提取 | 第一次提取→第二次提取→胶囊剂型 | 工艺旁白＋两段流程声 | 专利／工艺证据 |
| K14 | 7–9s | 生产与质量 | 工厂／生产线／GMP 三节点依次聚焦 | 稳重旁白 | 工厂、GMP 授权 |
| K15 | 9–11s | 联合应用总览 | 三个方案只做章节导航，不讲未审核作用 | 总览旁白 | 联合用药审核、包装 |
| K16 | 17–21s | 三套方案解释 | 每套独立 5～6 秒：问题→组合→作用→注意事项 | 三个完整语义段 | 最高风险门禁 |
| K17 | 7–9s | 建议服用周期 | 月历 1→2→3 推进，禁止擅增剂量频次 | 周期旁白＋日历声 | 说明书／终稿 |
| K18 | 9–12s | 六维总结与封底 | 六维标签依次回到产品，最后品牌封底 | 总结旁白＋收束音 | 全部内容与品牌授权 |

### 5.5 完整旁白流程

1. 从已签审核表生成 `approved-content.json`，每个镜头只读取批准终稿。
2. 按镜头写完整语义段；不要把一句话拆成多个微句分别 TTS。
3. 使用 `voice.reference-pharmacist-qwen-v1`。
4. 先生成自然 TTS，再做最多 1.18× 的整体速度调整。
5. 用真实音频时长反推镜头时码；音频放不下时延长画面，不暴力压缩语音。
6. 为每镜生成字幕 cues、ASR 结果、响度和边界连续性报告。
7. 全片完成后统一做跨镜头响度、底噪、停顿和呼吸感检查。

### 5.6 音效与音乐系统

全片只使用一套声音语法：

- 主体进入：柔和空气 `whoosh`。
- 路径绘制：细线扫过声。
- 标签出现：短、轻、音高可区分的提示音。
- 焦点切换：低强度脉冲，不使用游戏 UI 爆点。
- 章节转场：0.4～0.7 秒短桥接声。
- K18 收束：温和上行后稳定落点。

背景音乐若使用：稳重、温暖、低存在感，不带强鼓点，不营造疾病恐惧。必须有可追溯授权；无合适授权时使用人声＋音效完成，不用版权不明素材。

### 5.7 完整视频交付物

1. `renders/kekang-green-gold-sample-v1.mp4`
2. 完整 Revideo 源工程与单一 render 入口
3. `project-lock.json`、`approved-content.json`
4. 18 镜旁白、字幕、分轨音频和混音报告
5. 所有资产来源、授权状态、`style_id`／`series_id` 清单
6. 分镜级 QA 帧、全片接触表、黑场和溢出报告
7. ASR 对照、综合响度、True Peak、音频边界报告
8. 可直接播放的 `review.html`
9. 完整 review 记录；用户批准前不登记正式风格包

## 6. 里程碑与决策门禁

| 里程碑 | 产物 | 谁确认 | 未通过时怎么做 |
|---|---|---|---|
| M0 内容锁定 | 已填写逐镜确认表、`approved-content.json` | 业务／药师／合规 | 停止正式旁白和高风险动画 |
| M1 K08 有声片段 | `k08-audiovisual-v2.mp4` | 用户 | 最多围绕视觉／节奏／声音做定向修改，不扩新片段 |
| M2 完整静音 animatic | K01–K18 结构与时长 | 制作侧＋用户 | 只修结构，不重做风格 |
| M3 完整音画粗剪 | 全部旁白、字幕、关键动画 | 制作侧 | 修同步、信息密度和过渡 |
| M4 完整金样候选 | 3～4 分钟 MP4＋QA | 用户＋业务／药师 | 明确逐镜问题后局部修正 |
| M5 风格沉淀 | 正式 `style_pack` 与模板候选 | 用户批准后 | 未批准不得登记或批量扩主题 |

## 7. 停止条件

遇到以下任一情况，模型必须停止对应镜头并记录 `BLOCKED`，不得自行解决内容事实：

- 审核表未填写或没有最终批准稿；
- 包装、Logo、说明书、证据或工厂图片没有授权；
- 文案涉及降血压、心血管预防、抗肿瘤、联合用药、依赖、服用周期等高风险结论；
- 需要受体、靶点、分子通路或吸收倍数，但来源没有提供；
- 旧 PPT 截图是唯一可用商品图；
- 需要新增 `style_pack`、模板或批量资产，但完整金样尚未获得用户批准。

普通视觉选择不属于停止条件。颜色、字号、版式、转场、动画缓动、字幕样式和常规音效均按本文规范自行完成，不要把这些设计工作再次交给用户。

## 8. 技术验收命令

示例变量名可按实际路径替换：

```bash
npm --prefix poc/gold-sample run typecheck

K08_VIDEO=production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v1/renders/k08-audiovisual-v2.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$K08_VIDEO"
ffmpeg -v error -i "$K08_VIDEO" -f null -
ffmpeg -v info -i "$K08_VIDEO" -vf "blackdetect=d=0.1:pix_th=0.10" -an -f null - 2>&1

FULL_VIDEO=production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v1/renders/kekang-green-gold-sample-v1.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$FULL_VIDEO"
ffmpeg -v error -i "$FULL_VIDEO" -f null -
ffmpeg -v info -i "$FULL_VIDEO" -vf "blackdetect=d=0.1:pix_th=0.10" -an -f null - 2>&1
```

除命令检查外，必须人工查看：

- 每个主运动至少两个时间点；
- 每个场景进入、稳定和退场帧；
- 所有场景切点；
- 每 10 秒一帧；
- 50% 缩放下的标题、标签和字幕；
- 人声开始／结束处、镜头边界和末帧。

## 9. Definition of Done

### K08 完成

- 有真实可听的旁白和音效，不是静音 AAC。
- 音画同步、字幕准确、完整解码、无黑场、无溢出。
- 用户明确确认运动和声音语法。

### 完整金样完成

- K01–K18 根据审核结果全部完成或明确删除。
- 只使用批准文案和授权商品／品牌资产。
- 统一绿色视觉、统一药师音色、统一字幕与音效语法。
- 完整 3～4 分钟视频通过视觉、技术、医学／合规和用户确认。
- 在此之前不得声称“可批量生产”；完整金样通过后，再抽取正式 `style_pack` 并用第二商品验证不改组件代码。

## 10. 可直接复制给执行模型的提示词

```text
你正在 /Users/liminrong/Projects/chain-pharmacy-content-studio 工作。

任务：严格执行
production-library/validation/reference-analysis/kekang-pfizer-framework-v1/OTHER_MODEL_PRODUCTION_PLAN.md。

先完成阶段 A：把现有 K08 无声片段升级为带中性药师旁白、字幕、动作音效和完整混音 QA 的
7～9 秒视听片段。不要先扩 K01–K18。K08 用户确认后，再检查阶段 B 的内容与授权门禁；门禁
齐全才制作完整绿色金样。

必须遵守：
1. 先读 AGENTS.md、pharmacy-template-replication skill、assembly-protocol 和交接书全部内容。
2. 先更新 tasks/todo.md，再执行；每完成一项就勾选并记录 Review。
3. 只使用一个候选 style_pack_id：style-pack.kekang-pfizer-green-candidate-v1。
4. 复用现有 Revideo 工程；不要改成 PPT 翻页、静帧推拉或另起一套黑金／科技蓝风格。
5. 不使用旧 v4／v7 作为当前内容或视觉基线。
6. 不生成仿品牌包装，不复用旧 PPT 截图像素，不补写医学结论。
7. 旁白使用 voice.reference-pharmacist-qwen-v1；完整语义段生成，整体变速不超过 1.18×。
8. K08 必须有可听人声和至少 3 个同步音效；终混 -16±1 LUFS、True Peak≤-1 dBTP。
9. 渲染后必须 typecheck、完整解码、黑场检查、ASR、响度检查和多时刻视觉检查。
10. 所有候选、QA、比较稿只写入交接书指定的 validation/production-v1 目录。

普通视觉与动画选择按交接书直接决定，不要要求用户逐项设计。只有审核文案、授权资产或高风险
医学结论缺失时才停下并列出精确缺口。不得把局部片段通过描述成完整课程或批量模板通过。
```
