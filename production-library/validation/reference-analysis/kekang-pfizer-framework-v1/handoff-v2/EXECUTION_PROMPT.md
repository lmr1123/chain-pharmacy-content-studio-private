# 可可康完整视频 v2｜给执行模型的唯一指令

你不是在制作一套翻页 PPT，而是在实现一支约 4 分钟、由 58 个连续微镜头组成的内部培训视频。
章节 K01～K18 只负责组织教学内容，**不是画面页，也不是代码组件的最小单位**。

## 0. 开工前必须做

工作区：`/Users/liminrong/Projects/chain-pharmacy-content-studio`

按顺序完整读取：

1. 根目录 `AGENTS.md`／`CLAUDE.md`（若存在）；
2. `skills/pharmacy-template-replication/SKILL.md`；
3. 本目录 `README.md`；
4. 本目录 `scene-recipes.md`；
5. 本目录 `microshot-timeline.json`；
6. 本目录 `asset-manifest.json`；
7. 本目录 `narration-audio-plan.md`。
8. 本目录 `formal-voice-script.md`；
9. 本目录 `formal-voice-contract.json`。

随后执行：

```bash
python3 production-library/validation/reference-analysis/kekang-pfizer-framework-v1/handoff-v2/build_handoff_v2.py
python3 production-library/validation/reference-analysis/kekang-pfizer-framework-v1/handoff-v2/validate_handoff_v2.py
```

校验未通过，不得开始编码或渲染。

## 1. 实现合同

- 严格按 `microshot-timeline.json` 的顺序和时长实现 `K01-S01` 至 `K18-S04`。
- 一个微镜头对应一个明确的时间段、视觉焦点和动作组合；不得把同章微镜头合并为一张全屏章节页。
- 每个微镜头必须存在独立的背景／环境、主体、路径或道具、焦点提示、文字等分层对象，并让
  `animated_nontext_layers` 中至少一个非文字对象真实运动。
- `entry`、`performance`、`exit` 必须分别实现。不能只有入场后静止，也不能只对整个画面做
  淡入、推拉、缩放或 Ken Burns。
- 严格执行 `transition_to`：上一镜的主体、路径、形状、光点或环境运动应延续到下一镜，不能
  统一套整页黑场／白场／卡片切换。
- 同一时刻只设一个主要运动焦点。字幕跟随旁白，但字幕动画不计入非文字动画层。
- 每个镜头连续静止不得超过 `static_hold_max_seconds`；任何元素的局部呼吸不能被当作整个镜头
  唯一动作。

## 2. 明确禁止

以下任一做法出现，任务即失败：

- 每章一个全屏 React／Remotion／Revideo 页面，只替换标题和正文；
- 先生成 18 张设计稿，再按章节淡入淡出；
- 用 screenshot、PPT 导出图、整页卡片或长文本表格充当视频主体；
- 全片重复“标题进入 → 三行字出现 → 停留 → 整页退出”；
- 只移动摄像机或整个根容器，不移动主体、路径、环境或道具；
- 擅自合并、删除或重排微镜头；
- 对未审核医学内容生成正式旁白、具体机制、疗效结果或疾病预防画面；
- 仿造可可康包装、Logo、说明书或联合商品包装。

## 3. 画面与素材

- 唯一候选风格：`style-pack.kekang-pfizer-green-candidate-v1`。
- 画面配方只使用 `scene-recipes.md` 的 R01～R10；它们是运动构图，不是静态版式模板。
- `asset-manifest.json` 中：
  - `existing-candidate` 可直接用于验证；
  - `generate-one-then-review` 只能按所给提示词先生成一张定稿，再派生姿态／裁切；
  - `business-authorized-only` 必须等待业务原文件，不得伪造；
  - `code-generated-neutral` 应用矢量形状或程序绘制，不要寻找风格不一的图库图标。
- 人物年龄只用于画面演绎，不等于医学分群；不显示具体诊断或治疗承诺。

## 4. 声音执行

- K01～K18 全部必须生成、同步并验收正式金样旁白；不能只制作 K08，也不能以医学／素材门禁
  为由提交静音版本或 guide voice。
- 正式口播文本以 `formal-voice-script.md` 为唯一声音输入，机器字段以
  `formal-voice-contract.json` 为准；不得继续朗读 `narration_candidate` 中的制作备注。
- 固定复用 `voice.reference-pharmacist-qwen-v1`，使用现有 Qwen3-TTS 药师参考音色，不重新选音色。
- 全片按 18 个章节语义段生成，每章一次完整连读；禁止按 58 个短句、单字序号或微词分别 TTS。
- 时间线中的约 4 分钟暂定时长，是按每秒约 4.8 个中文语音单位为正式旁白预留的自然语速窗口；
  不得退回旧版 186.8 秒结构并把旁白强行塞入。
- 每段生成后必须用 ffprobe 读取真实时长，写入 `voice-sync-map.json`，再回填到对应微镜头；
  未做真实时长 fit check 的音频不得放入时间线。
- 若音频超过视觉时窗，整体拟合不得超过 1.18×；超限时延长对应微镜头或收紧不改变事实的
  连接语，禁止高速压缩、截尾或让语音跨入错误画面。
- 医学／证据审批状态与金样声音验收是两条独立门禁：可以继续标记内容待批准，但必须完成可听、
  连贯、正式质量的金样旁白，以验证模板声音系统。
- 每个微镜头按 `sfx_events` 绑定局部音效，转场音应服务于路径／主体连续性。
- 最终混音目标：综合响度 `-16 ± 1 LUFS`，True Peak `≤ -1 dBTP`；旁白始终可懂。
- 字幕必须从最终旁白文本生成，不能从 ASR 错误结果反写权威术语。
- 必查术语：可可康、灵芝多糖、灵芝三萜、GMP、九点一三克；ASR 把“三萜”识别成“三贴”
  时不得据此修改权威字幕。

## 5. 推荐工程结构

章节只作为文件夹／数据索引，微镜头才是实现与验收单位：

```text
production-v2/
  src/
    timeline.ts
    recipes/R01...R10
    microshots/K01-S01...K18-S04
    audio/
  renders/
  qa/frames/<microshot-id>/
  qa/contact-sheets/
  review.html
```

可以让多个微镜头共用 recipe 函数，但必须传入各自的图层、动作、时码和资产；不得创建一个
“ChapterSlide”组件承载整章。

## 6. 分阶段交付

### A. 合同和全片正式语音

1. 运行 v2 生成器和校验器；
2. 按正式语音合同生成 K01～K18 共 18 个章节语义段；
3. 读取真实时长、建立 sync map、生成全片母带、SRT/VTT 和章节试听页；
4. 输出响度、峰值、术语、覆盖率和同步验收结果。

### B. 58 微镜头结构 animatic

1. 实现全部微镜头的真实分层运动；
2. 未授权素材使用清晰的结构占位，不使用静态 PPT 卡片；
3. 对每个微镜头至少抽取入场后、表演中、退场前三帧；
4. 生成 18 章接触表，但接触表不得被当作成片素材。

### C. 审核后内容与素材替换

医学文案、授权包装／说明书／联合商品素材到齐后，再替换对应内容和素材。若审核终稿改变口播，
只返修受影响的章节语义段并重新执行真实时长同步；不得退回碎片化 TTS，也不得无验证地改变
已确认的微镜头运动结构。

## 7. 完成定义

必须同时满足：

- `validate_handoff_v2.py` 通过；
- 58 个微镜头全部存在，顺序、时长和 `transition_to` 一致；
- 18 个章节正式旁白、全片旁白母带、SRT/VTT、真实时长 sync map 和试听页全部存在；
- 语音覆盖 K01～K18 达到 100%，不存在静音章、guide voice 章或只完成 K08 的情况；
- 每镜至少一个非文字图层真实运动，且有入场／表演／退场；
- 逐镜三帧和全片接触表能证明不是一章一页；
- 视频可完整解码，无黑场、无冻结、无裁切／重叠／溢出；
- 术语 QA 正确覆盖“可可康、灵芝多糖、灵芝三萜、GMP、九点一三克”；
- 声音指标合格；
- 未审核内容仍被阻断，未授权品牌资产未被仿造；
- `review.html` 能播放视频并按微镜头定位问题。

## 8. 允许向用户提问的范围

只在以下三类阻断点提问：医学文案批准、品牌／证据素材授权、全片金样声音与运动验收。
普通配色、构图、人物姿态、图标形状、转场和镜头运动已经由生产包锁定，不把这些设计工作
重新推回给用户。

每次汇报必须使用微镜头 ID，例如“已完成 K03-S01～K03-S03”，不能只说“完成第三章”。
