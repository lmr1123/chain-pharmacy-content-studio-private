# 生产模板复刻与装配协议

方向锁定见 `decision.gold-sample-first` 与 `docs/project-brief.md` §1.1：先完整金样，再框架与风格，后延伸；禁止以元件囤积为主线。

## 1. 不可跳过的顺序

1. 确认所属课型金样与 `style_pack_id`；无金样时先完整复刻签样，再谈延伸。
2. 锁定参考范围与验收帧，形成逐句时码和画面节点（复刻时）。
3. 查询公共库，优先选择已有模板、场景、组件、特效、音色和图片资产。
4. 为项目绑定一个 `style_pack_id`，冻结母版、字体、色板、角色和图片兼容规则。
5. 将审核稿映射为**金样框架内的**场景类型与内容槽位，不直接改写已审核文案。
6. 只补齐框架槽位语义真正缺失的组件或资产；先完成单个代表项签样。禁止无槽位依据的大规模预囤。
7. 组装、渲染并按动态行为、音频、末帧和可读性验收。
8. 通过签样后回写注册表；失败项记录到 `tasks/lessons.md` 和结构化教训表。

## 2. 风格锁定

每个视频或课件必须声明且只能声明一个主风格包：

```json
{
  "style_pack_id": "style-pack.reference-medical-tech-v1",
  "locked": true
}
```

风格包负责统一：

- 品牌母版、背景、Logo、章节导航和声明；
- 标题、正文、字幕字体及字号层级；
- 主色、强调色、圆角、描边、阴影和发光强度；
- 数字人身份、比例、线条和动作语法；
- 可进入该项目的图片子风格白名单。

同一视频可以包含卡通症状图、写实草本图和商品包装图，但它们必须同时被主风格包列为兼容子风格，并通过相同卡片结构、色彩蒙层、圆角和动效统一到同一视觉系统。不得在单个镜头临时采用未登记画风。

## 3. 结构化装配对象

```json
{
  "project_id": "health.wind-heat.v1",
  "template_id": "template.health-reference-tech-v1",
  "style_pack_id": "style-pack.reference-medical-tech-v1",
  "content_lock": "approved-script",
  "voice_id": "voice.reference-pharmacist-qwen-v1",
  "scenes": [
    {
      "scene_type": "advice_list",
      "component_ids": ["component.card.advice-row"],
      "effect_ids": [
        "effect.border.rounded-trace-v1",
        "effect.background.four-way-current-v1"
      ],
      "slots": {
        "title": "生活禁忌与建议",
        "items": []
      }
    }
  ]
}
```

主题、商品和疾病变化只替换 `slots`、审核资产和场景顺序。底层组件只有在现有能力无法表达需求时才新增。

## 4. 复用优先级

1. 原样复用已通过生产验收的组件。
2. 在组件公开参数范围内换文案、图片、颜色、时码、站位或尺寸。
3. 基于现有组件派生新版本，同时保留原版本和兼容关系。
4. 只有前三种均不能满足时才新增组件。

禁止复制一份组件后只改名称；禁止把模板参数硬编码到新的主题文件中。

## 5. 资产新增规则

- 图片：先查资产注册表；缺失时先签样一张，再批量扩展。
- 商品图：优先公司已授权原图；PoC 无授权原图时只能使用明确标注的无品牌示意。
- 角色：同片保持同一角色身份；新姿势必须共享脚底基线和归一化面部锚点。
- 音色：必须有授权状态；按完整语义段生成，禁止微句暴力变速。
- 特效：每镜头只保留一个主要运动焦点；扫描光、背景电流和卡片入场不得同时抢夺注意力。

## 6. 签样与状态

统一状态：

- `candidate`：候选，不能进入批量任务；
- `selected`：方向已选，仍需技术和内容 QA；
- `technical-qa-passed`：文件技术指标通过；
- `visual-reviewed`：视觉一致性通过；
- `user-approved`：用户已确认；
- `production-validated`：已在真实成片中通过完整验收；
- `deprecated`：历史兼容，不再用于新项目。

只有 `user-approved` 或 `production-validated` 组件可以默认进入批量生产。

### 正式模板与验证目录

- 用户确认沉淀的完整视频或 PPTX 必须进入
  `production-library/templates/settled/<template-slug>/`，一套模板一目录。
- 每个正式目录保存唯一 canonical 产物、`业务提交_空白模板.docx`、
  `业务提交_填写参考.docx` 与 `manifest.json`；生成入口、Word 权威源和源工程通过
  manifest 引用，不把阶段稿复制进正式目录。
- 探索稿、分段稿、阶段签样、被否决版本、对比稿、QA 和接触表统一进入
  `production-library/validation/`。
- `production-library/registries/templates.json` 的 `settled_template_dir`、
  `canonical_artifact`、`business_template`、`business_sample` 和 `validation_root`
  必须与物理目录一致。
- 禁止正式模板与过程产物继续混放在同一个 `out`／`output` 目录，也禁止保留第二份
  canonical 文件作为“兼容副本”。

## 7. 每次交付的验收证据

- 1920×1080、30fps、H.264/AAC；
- 完整解码、无黑场；
- 50% 预览下有效字号达标；
- 人物嘴型、停顿和末帧稳定；
- 音频 ASR、响度、段间连续性通过；
- 动态组件用两个以上时刻的关键帧证明真实运动；
- 所有生产图片来源和 `style_id` 可追溯；
- 新增组件、决策和教训已回写公共库。

## 8. 主题素材系列化沉淀

同类主题资产除 `style_pack_id` 外，还必须绑定稳定 `series_id` 和一个或多个
`role_ids`。系列负责统一色板、材质、构图安全区、提示词变量和动画契约；成员负责
具体疾病、器官、症状或病邪内容。

新增素材前依次执行：

1. 按 `style_pack_id`、`series_id` 和角色查询公共库。
2. 已有系列能表达时，新增或升级系列成员，不另建近似画风。
3. 组件只引用稳定资产 ID，不直接硬编码一次性文件路径。
4. 新成员独立完成视觉、技术、来源和医学审核，不能继承其他成员状态。
5. 通过后更新系列 `members`，使后续视频、PPTX 和 PDF 均可检索和组合。
