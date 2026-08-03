# 商品培训课件4 · 保真复刻任务

> 仅本目录有效。根目录 `tasks/todo.md` 另有课件3/可可康历史任务，勿混。  
> 教训叙述：仓库根 `tasks/lessons.md` · 注册表 `production-library/registries/lessons.json`

## 计划

- [x] 0. 隔离工作区 `product-courseware-4-faithful-replica-v1`，写 VERSION 边界
- [x] 1. 参考抽帧 / 关键帧 / 单声道音频 / ASR
- [x] 2. 逐屏登记 `docs/screen-registry.json`（原文/对象/位置/尺寸/层级/动作）
- [x] 3. 门禁静态页 `gate/static-time-list.html`（S01，t≈5.0s）
- [x] 4. 门禁微镜头 `gate/micro-time-reveal.html`（S01，t=2.0–9.0s）
- [x] 5. 左右对照 `gate/compare.html` + 参考 clip
- [x] 6. 用户确认门禁可继续（「可以了，继续拓展」）
- [x] 7. 扩全片 13 场景：`content-model.json` + `web/full-film.html` + 静帧 MP4
- [x] 8. 关键镜头动效烤进视频（S01 弹跳+箭头跳；S03 去底；S04–S06 序贯揭示/表头白箭头/红箭头跳动/O2 打叉/NK-cell/手臂脉动）← 2026-08-03 首轮
- [x] 9a. AI 位图替换主视觉（禁用 SVG/PIL demo）
- [ ] 9b. 业务包装授权图替换后复渲；个别资产可继续精修 ← **视频调优**
- [ ] 10. 全片 QA（并排接触表 / 响度 / 解码）用户视觉签样 ← **视频调优**
- [x] 11a. 经验沉淀（关联用药版式 + 总结行标题 + 字号/图标/音频扩展）→ `docs/video-pptx-grammar-and-experience-v1.md` + lessons/recipes/components 注册表
- [ ] 11b. 全片视觉签样后抽取整包 template / slots 写入 `templates/settled/`（已有初版 settled，调优签样后再升版）
- [x] 12a. 可编辑 PPTX（对标速福达）：`scripts/export-cw4-pptx.mjs` · `npm run export:pptx` · **15 页**（删 S14 总表后）
- [x] 12b. ~~自建 editable-video.html~~ → 用户否决；已删除
- [x] 12c. 接入 Revideo 可编辑工程：`npm run start:editor` :9012 · `editable:cw4:*` · bridge 在 gold-sample
- [x] 12d. 片段编排 1+2+3 + 扩展段克隆旁白（见 Review 旁白）
- [ ] 12e. 编辑器内图层布局精修（与静帧像素对齐）；主题换品 replicate
- [x] 13. 关联用药 **有声讲解**（S12–S13 完整口播 + 去 prompt 泄漏）
- [x] 14. **场景顺序修正**：适宜人群 → 关联用药 → 三大核心功效表 → 结尾；**删除** S14 四列表总表
- [x] 15. **金样更新归档**（2026-08-03）：成片/PPTX/content-model/layer-manifest → `templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/` · registries · gold-samples

---

## 下一阶段：视频调优（金样已落 · 可继续迭代）

> 用户 2026-08-03：「先更新到金样，后续再继续迭代」  
> 当前金样 revision：`2026-08-03-motion-editor`（见 settled `manifest.json`）。

优先建议（实施前与用户确认顺序）：

1. **关键动效** → 验证: S01 打字/榜单、功效链入场、含量 1=5 等与参考时码对齐，非纯静帧 hold  
2. **画面精修** → 验证: 字号/间距/包装与参考并排；授权包装替换占坑  
3. **音画 QA** → 验证: 全片接触表、响度、扩展段 ASR 无泄漏；用户视觉签样  
4. **编辑器像素对齐** → 验证: `editable:cw4:*` 与成片静帧同位同号  

启动前回顾：`tasks/lessons.md` 2026-08-03 两条 + `docs/editable-video-v1.md` 双轨门禁。

---

## Review（门禁阶段）

- 明确否决兄弟目录 `validation/video/tomato-lycopene-faithful-v1`，禁止当母版。
- 门禁选 S01（TIME 榜单）：参考独有、否决稿完全缺失、无包装授权依赖，最适合验「是否同一版本」。
- 坐标：TIME (94,116,173,248)、Card (342,123,435,231) @854×480 → ×2.25 @1080p。
- 全片与导出架构写在 registry `export_plan_after_full_signoff`，**未执行**。

## Review（扩展：关联用药 · 版式）

- 对标速福达金样：**仅** S12/S13 关联用药双屏（`business_extension`）
- **S14 四列表「敲重点」总表已删除**（用户 2026-08-03：参考片无此段；收口用参考片 S11 三大核心功效表）
- 版式经验：`docs/video-pptx-grammar-and-experience-v1.md` · note 在包装上方

## Review（2026-08-03 · 旁白补录与克隆泄漏）

| 问题 | 根因 | 处置 |
|------|------|------|
| 关联用药「没有讲解」 | S12–S13 为 extension，参考轨 EO-VO 后切片无声 | notes 完整口播 + `regen-tts --backend clone` + rebuild |
| 关联段循环「最大的十种…」 | 克隆 `reference-prompt` 音频截断（只到「贡献」）而 `ref_text` 写完整句 → 每段开头补念半句 | 切片改 ss=2.30 / t=5.55，与 ref_text 对齐；meta 缓存失效；重生成 S12–S13 |
| 验收 | 仅看 rms/时长会漏检 | 离线 ASR：S12 开头「四、关联用药」；S13「第二组…」 |

**CLI**：`.venv-tts/bin/python scripts/segment_studio.py regen-tts --id … --backend clone` → `python3 scripts/segment_studio.py rebuild --film`  
**教训 id**：`lesson.qwen3-clone-prompt-audio-must-match-ref-text` · `lesson.cloned-tts-requires-post-generation-asr-gate`

## Review（2026-08-03 · 编辑器内 Revideo 动效）

对齐辅酶Q10 / 礼风热证：在 `src/project.tsx` 用 `easeOutBack` 入场、`loop` 箭头向右脉冲、S05 手绘叉等；与字幕/补丁 `yield* all` 并行。  
启动：`npm run start:editor` → http://127.0.0.1:9012/ 时间轴播放即可看到。

## Review（2026-08-03 · 金样更新归档）

用户：「先更新到金样，后续再继续迭代」

| 产物 | 路径 |
|------|------|
| settled 目录 | `templates/settled/fuler-fanqiehongsu-product-courseware-4-v1/` |
| 金样 MP4 | `…/福尔番茄红素_商品培训课件4_金样_v1.mp4` ≈156.7s |
| 金样 PPTX | `…/福尔番茄红素_商品培训课件4_金样_可编辑课件_v1.pptx` 15 页 |
| 快照 | content-model / layer-manifest / `src-snapshot/project.tsx` |
| 注册表 | `registries/templates.json` · revision `2026-08-03-motion-editor` |
| 案例汇总 | `gold-samples/index.html` 已改 15 页 |

## Review（2026-08-03 · 动效首轮 → 语法纠偏）

用户反馈：成片「整屏在抖」。根因是多元素同相位大振幅 idle。

**对标参考实测重定语法（培训剪辑）：**
1. **入场单次** scale/opacity 弹出，到位冻结  
2. **强调循环仅限**：表头白箭头 / 链路红箭头 / S01 黄绿»（约 7–9px）  
3. **主视觉禁止 idle**（番茄、器官、杂志、卡片、列表、O2、NK、手臂不乱晃）  
4. **序贯揭示** S05/S06；叉单次弹出后静止  
5. **手臂**：原 `flex-arm` 位图 + 极轻 ±3% 呼吸，无旋转位移  

实现：`export-full-film-video.py` 12fps 采样；成片 `out/商品培训课件4_保真复刻_全片_v1.mp4`

## Review（2026-08-03 · 叙事顺序修正）

| 项 | 说明 |
|----|------|
| 问题 | 关联用药后加，曾插在参考片功效总表 **之后**，且多了一页速福达式四列表总表 |
| 用户裁定 | 参考片无关联用药；关联用药应在 **适宜人群之后**；其后是 **三大核心功效表**；**删除** 此前新增总表 |
| 成片顺序 | … → **S10 适宜人群** → **S12/S13 关联用药** → **S11 三大核心功效表** → **S15 结尾** |
| 当前成片 | `out/商品培训课件4_保真复刻_全片_v1.mp4` ≈ **156.6s**（15 场景） |
| 时间轴 | S10 ≈104.8–114.0 · S12 ≈114.0–129.8 · S13 ≈129.8–140.3 · S11 ≈140.3–152.4 · S15 ≈152.4–156.6 |

## Review（可编辑金样双轨 · 摘要）

- editor-bg 禁止烧 `editable:*` 角色；一页一 `makeScene2D`；见 `docs/editable-video-v1.md`  
- lesson：`lesson.editor-bg-must-omit-editable-layers-gold-template`
