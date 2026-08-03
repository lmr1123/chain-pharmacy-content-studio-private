# 正式沉淀模板

本目录只保存用户已确认沉淀的模板，一套模板一个子目录。每个子目录必须包含：

- 唯一 canonical 成片或 PPTX；
- `业务提交_空白模板.docx`，供业务直接填写；
- `业务提交_填写参考.docx`，展示当前内容驱动格式的真实填写方式；
- `manifest.json`，记录 `template_id`、`style_pack_id`、生成入口和验证目录；
- 不得放入探索稿、阶段签样、分段稿、对比稿、QA 或接触表。

**业务 WorkBuddy 傻瓜交付总案（货架预览 · 内容驱动 · 克隆语音包 · 迭代 backlog）：**  
`docs/business-workbuddy-foolproof-delivery.md`

目标契约（持续补齐）：每模板 `preview/`（cover + 关键帧）、视频类 `voice/`（克隆 pack）、manifest 的 `preview` / `voice` 字段。

**当前（2026-08-03）：** 六模板均已有 `preview/` + manifest.`preview`；视频类已写 manifest.`voice`（本地 pack 目录仍按 D2 收尾）。  
业务目录清单：`business-catalog.json`。  
刷新预览：`python3 scripts/sync_settled_template_previews.py`  
档 A 业务包：`python3 scripts/build_business_tier_a_package.py` → `outputs/业务使用资料包/药店培训内容工厂-业务包.zip`  
代理提示：`docs/workbuddy-system-prompt.md`

两份 Word 是正式模板业务包的一部分，但其权威生成源仍由 `manifest.json` 记录，
统一通过 `scripts/sync_settled_template_business_words.py` 刷新，禁止混入已经废弃的
固定章节／固定字段提交表。

所有过程产物统一进入 `production-library/validation/`。正式模板的查询入口是
`production-library/registries/templates.json`，不得根据文件名或修改时间猜测。
