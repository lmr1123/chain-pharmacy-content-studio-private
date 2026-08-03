# 视频 × PPT 共用语法与经验沉淀 v1

> 来源：`product-courseware-4-faithful-replica-v1`（福尔番茄红素）  
> 对标：速福达金样 `sufuda-product-courseware-3-gold-v1` 的「关联用药 + 总结」讲解模式  
> 状态：`experience-settled`（经验已入库；整包 template settled 仍待全片视觉签样后）  
> 日期：2026-08-02  
> 适用：商品培训课件 **视频轨** 与 **可编辑 PPTX** 共用同一 content-model / 槽位语义

---

## 1. 分层原则（必须写进 Scene）

| layer | 含义 | 音频 | 可否标「像素级复刻」 |
|-------|------|------|----------------------|
| `observed_reference` | 参考片已有画面与讲解 | 可复用参考原轨 | 是 |
| `business_extension` | 业务扩展（如参考无关联用药时按金样补） | **优先克隆补录完整口播**（禁止长期静音交付）；prompt 须对齐 | **否** |
| `authorization_dependency` | 包装/Logo/实拍待授权 | 不改变 | 占坑，不语义替换 |

**单一内容模型**：`content-model.json` 同时驱动 静帧 MP4、网页预览、后续 PPTX；禁止三套工程各改一版。

---

## 2. 字号与图标（培训课件）

| 规则 | 说明 |
|------|------|
| 字号偏大 | 培训图文并茂；章节 / 列表 / 表文整体大于文档体 |
| 字体 | 优先 HarmonyOS Sans SC Black/Bold（CJK 全）；禁缺字字体 |
| 序列图标位图化 | 红勾、绿 chevron、热点徽章等做成 **可复用 PNG**，禁红色空心圆凑数 |
| 主视觉位图 | 人物/食品/器官/机制 **AI 位图 + 透明底**；几何框线/表格可用矢量 |
| 描边用途 | 丝纹底上功效名/重点句可白描边；标题黄字红描边；**勿与正文层级混用导致杂乱** |

---

## 3. 关联用药 / 联合用药（scene 语法）

**Recipe id（经验）**：`scene-recipe.related-meds.courseware-training-v1`  
**对标金样旁白顺序**（不是装饰顺序）：

```
章节条 → 导航 pill（①②）→ 【讲解句居中、在包装上方】→ 包装 A + 包装 B 白卡 → （无底部重复标题）
```

| 要做 | 不要做 |
|------|--------|
| 讲解句先出现：讲清「为什么一起用 / 场景」 | 先堆包装再在底部重复导航同款标题 |
| 导航 pill 已标明组合名时，**删掉**与导航重复的底部「一、xxx」标题（既不是必要字幕也不是新信息） | 导航 + 底部标题 + 底栏字幕三层同义叠字 |
| 包装大图 + 中间「+」；缺授权用占坑槽 | SVG/假包装冒充品牌；裁参考水印截图 |
| 每组合独立一屏（或同壳切换 active pill） | 用「方案01/02」无业务含义编号主导航 |
| 扩展段无参考音：写完整口播 → Qwen3 克隆补录 → ASR 查泄漏 | 静音交付或把扩展段伪标为 observed_reference |

**口播**：自然完整句（人群/场景 + 本品与关联品搭配）；禁止「接下来展示对应组合」制作腔。  
（继承 `lesson.joint-medication-voiceover-must-use-complete-spoken-sentences`）

**PPTX 槽位建议**：

- `slot.pack.primary` / `slot.pack.related`  
- `text.related.nav.1` / `text.related.nav.2`  
- `text.related.note`（讲解句，**在上**）  
- 不要为与 nav 重复的 `text.related.headline_bottom` 建必填槽

---

## 4. 总结页（scene 语法）

**Recipe id（经验）**：`scene-recipe.summary-row-headers.courseware-training-v1`

### 4.1 不是关键词云

总结页目标：**复习这一页 ≈ 能完整理解**（机理 / 依据 / 场景 / 怎么推），不是只记标签。

每行正文应含完整说明句，可含：

- 核心功效：名称 + 简要机理  
- 产品特点：名称 + 依据（产地/原料/含量数字）  
- 适宜人群与用法：适宜 / 不适宜 / 用法用量  
- 关联用药：组合 + 场景 + 一句话术  

### 4.2 版式：行标题（常规阅读），非四列表头横排

培训默认阅读方向 **上→下按主题**：

```
| 行标题（左）     | 完整说明（右）                    |
| 核心功效         | ①… ②… ③…（完整句）              |
| 产品特点         | ①… ②… ③…                      |
| 适宜人群与用法   | 适宜 / 不适宜 / 用法              |
| 关联用药         | ①组合… ②组合… 话术…             |
```

| 要做 | 不要做 |
|------|--------|
| 左列行标题（红底白字或等价高对比） | 仅顶栏四列关键词 + 格内再塞碎片词 |
| 右列完整句，字号培训向偏大 | 只放 2～4 字标签，复习看不懂 |
| 可与参考「功效详表」并存：详表=`efficacy_recap_table`；收口=`summary_row_headers` | 用功效详表冒充「敲重点总结」或反过来 |

**与速福达金样四列表的关系**：金样四列可作信息架构参考；**番茄线用户确认**后，培训默认改为 **行标题** 更符合常规阅读。新主题默认行标题；若业务强制四列，在 content-model 显式 `layout: column_headers`。

**PPTX 槽位建议**：

- `text.summary.row.{efficacy,feature,audience,related}.label`  
- `text.summary.row.*.body`（多行完整句）  
- `text.summary.footer`（复习口诀，可选）

---

## 5. 音频策略（视频）

| 阶段 | 策略 |
|------|------|
| 保真复刻段 | 按 `reference_start/end` **切片复用**参考轨（不覆盖 `reference-narration.mp3`） |
| 业务扩展段 | **完整口播稿** → Qwen3 克隆补录 → 拼入工作轨；禁止长期静音交付 |
| 克隆 prompt | `ref_audio` 词级完整句 **=** `ref_text`；变更失效缓存（见 `docs/segment-studio-v1.md`） |
| 验收 | 每段离线 ASR：查 **泄漏前缀**（如「最大的十种…」）、漏读、药名；未过不得进 MP4 |

禁止：未声明就把克隆轨当参考权威；扩展段不补时长却 `-shortest` 砍画面；只看 rms/时长不听 ASR。

---

## 6. 与 PPT 共用清单

- [ ] 同一 `content-model.json` 场景 id / 文案 / 槽位  
- [ ] 关联用药：note 在上、包装在下、无重复底标题  
- [ ] 总结：行标题 + 完整句，非关键词矩阵  
- [ ] 图标 PNG 资产库可复用（check / chevron / badge）  
- [ ] layer 标注 reference vs extension  
- [ ] 扩展段音频策略写进 model.audio.extension  

---

## 6.1 可编辑金样双轨（强制 · 2026-08-03）

**Lesson id**：`lesson.editor-bg-must-omit-editable-layers-gold-template`  
**详述**：`docs/editable-video-v1.md` §「金样门禁 · 双轨静帧」

| 轨 | 用途 |
|----|------|
| `scene-stills` | 成片 / 签样视觉权威（可烧字烧图） |
| `scene-stills-editor-bg` | Revideo 编辑底板：**不得**烧任何 `editable:*` 图文 |

后续主题金样模版一律：editor-bg 只留 chrome → 全页真实 `editable:` 节点 → 一页一 scene → 无重复 key。  
禁止「只有封面可编、其余烤进 PNG」。

---

## 7. 代表静帧（本包）

| 场景 | 文件 |
|------|------|
| 关联① | `out/scene-stills/S12_related_1.png` |
| 关联② | `out/scene-stills/S13_related_2.png` |
| 总结行标题 | `out/scene-stills/S14_summary_key.png` |
| 参考功效详表 | `out/scene-stills/S11_summary.png` |
| 成片 | `out/商品培训课件4_保真复刻_全片_v1.mp4` |

---

## 8. 注册表交叉引用

- lessons：见 `production-library/registries/lessons.json`  
  - `lesson.related-meds-note-above-packs-no-duplicate-bottom-title`  
  - `lesson.training-summary-must-be-full-sentences-with-row-headers`  
  - `lesson.courseware-type-icons-audio-extension-for-video-pptx`  
  - **`lesson.editor-bg-must-omit-editable-layers-gold-template`**（可编辑金样双轨）  
- scene-recipes：`scene-recipe.related-meds.courseware-training-v1`、`scene-recipe.summary-row-headers.courseware-training-v1`  
- 叙述源：`tasks/lessons.md` · 2026-08-02 / **2026-08-03** 条目  
