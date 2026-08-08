# 商品培训课件 · 内容入口（L2）

**状态：** 操作手册（2026-08-08 · L2）  
**目标：** 业务 Word / 大纲 → `script.structured.json` 草稿 → **人审确认** → 再跑 `generate_courseware.py`  
**契约：** `production-library/business-pptx-courseware-word-input-contract.md`  
**下游：** 构件化流水线 `docs/component-recipe-pipeline-architecture.md` · 页型生长 `docs/page-type-growth-channel.md`

---

## 0. 一句话

业务只交**审核原文**（记事本式 Word / 大纲 md/txt）；系统做**确定性结构化**成 `product-training-script/v1`，**不扩写功效/剂量**；人审勾完清单后，才允许生成 PPTX。

---

## 1. 协作四步（强制顺序）

| 步 | 动作 | 产物 | 谁确认 |
|----|------|------|--------|
| **① 先选模板** | 点名 family + style_pack | 例：`product-training` + cream-red / silk | 业务/内容 |
| **② 再交资料** | Word 或大纲；图可后补 | 源文件进 validation 或会话附件 | 业务 |
| **③ 先出内容初稿** | 跑草稿脚本 → 人审清单 | `script.structured.json` + `REVIEW-CHECKLIST.md` | **业务/药师** |
| **④ 确认后再成片** | `generate_courseware.py` | scene-plan / PPTX / QA（仅 validation，除非 content_lock 已过） | 内容锁定后 |

**禁止：** 跳过 ③ 直接从随意大纲「一次性出成片」并当交付；禁止 AI 补写医学结论后不经人审写入 script。

绿色壳业务口令（并行参考）：  
`production-library/templates/settled/product-courseware-green-v1/业务使用流程.md`

---

## 2. 输入形态（都接受）

| 形态 | 路径/格式 | 说明 |
|------|-----------|------|
| **通用业务 Word** | `outputs/courseware-natural-import/培训课件内容与素材提交_通用模板.docx` | 记事本式：主题 + 自然板块 + 审核正文 + 可贴图 |
| **分栏业务 Word** | 历史样本（穿心莲等） | Heading + 列表；解析时跳过「填写提示 / Courseware Ignore」 |
| **大纲 Markdown/TXT** | `## 章节` + 正文/列表 | 推荐内部快速迭代 |
| **已有 structured** | `*.json` schema `product-training-script/v1` | 仅校验 / 出人审清单，不二次编造 |

**业务 Word 不得出现：** 模板 ID、页码、坐标、卡片数、动画、图片提示词、技术字段。

---

## 3. 中间层：`product-training-script/v1`

Schema：`production-library/schemas/product-training-script.schema.json`  
金样参考：`…/fuler-maikenli-lycopene-v1/script.structured.json`

| 顶层键 | 用途 | 生成器页型倾向 |
|--------|------|----------------|
| `meta` | 品名、组织、角标、`content_lock` | cover |
| `hook` | 导语段落；可选 symptoms/stats | hook_pain_data / hook_intro |
| `benefits` | `items[{title,body}]` | benefit_chain |
| `features` | 同上；可 `hidden` | feature_* |
| `audience` | `items[string]` | audience |
| `combination` | `rows[{problem,partner,talk_track}]` | combination_guidance |
| `summary` | `rows[{label,value}]` | summary_matrix |
| `precautions` | `items[string]` | precautions |

### content_lock 取值

| 值 | 含义 | 产物目录 |
|----|------|----------|
| `business-provided-draft-pending-pharmacist-review` | **草稿默认** | 只 `validation/` |
| `business-approved` / 药师终审等价标记 | 业务书面确认后 | 仍建议 validation 至合规放行 |
| 未过药师审 | 禁止进 `templates/settled/` | — |

**工具永不自动升锁。** 升锁必须人改 JSON 并记录。

---

## 4. 半自动工具

```bash
# 大纲 / Word → 草稿 script + 人审清单
python3 scripts/draft_product_training_script.py \
  --input path/to/outline.md \
  --out-dir production-library/validation/courseware/<slug>/l2-draft-out \
  --display-name "商品显示名" \
  --organization "大参林医药集团"

# 已有 script 只出人审清单
python3 scripts/draft_product_training_script.py \
  --input …/script.structured.json \
  --out-dir …/l2-review-only \
  --review-only
```

### 工具做什么

1. 解析 txt/md/docx 为「板块标题 + 正文/列表/简单表」。
2. 用 **registry mapper_hints + 固定别名** 把板块归入上表键（确定性，非联网扩写）。
3. 在**原文子串**内切条目（列表、`标题：正文`、联合行 `|` 等）；切不动的整段落进对应 `paragraphs`/`items` 或 `unmapped`。
4. 写出：
   - `script.structured.json`（`content_lock` 默认 pending）
   - `REVIEW-CHECKLIST.md`（映射置信度、未归类板块、空节、禁词提示）
   - `source-map.json`（板块 → script 键 + 理由）
5. **自检：** script 内业务字符串必须能在源文中溯源（固定 chrome 除外）；失败则退出码非 0。

### 工具不做什么

- 不补写功效、剂量、发病率、联用结论  
- 不静默丢弃无法归类的正文（进 unmapped + 清单）  
- 不调用付费 API  
- 不直接导出 PPTX（那是第四步）

人 / 会话模型可在**清单约束下**协助改草稿（仍须原文依据）；改完再跑 `--review-only` 或重跑草稿。

---

## 5. 人审清单（最低必勾）

`REVIEW-CHECKLIST.md` 模板含下列项，**全部勾选**才进入第四步：

- [ ] 品名 / 组织 / 角标正确  
- [ ] 各板块映射是否合理（低置信度项已人工改键或改文）  
- [ ] 未归类正文已处理（并入某节或明确删除）  
- [ ] 功效 / 数据 / 话术与审核稿一致，无工具或 AI 补写  
- [ ] `hidden` 条目（如大品牌）符合业务意图  
- [ ] 联合用药三列齐全或有意留空  
- [ ] 注意事项足够覆盖标签/禁忌口径  
- [ ] `content_lock` 仍为 pending，或已按流程升锁并留痕  
- [ ] 素材缺口已知（包装占位可接受）

---

## 6. 第四步：成片（确认后）

```bash
python3 scripts/generate_courseware.py \
  --script <out-dir>/script.structured.json \
  --style production-library/styles/lycopene-health-edu-cream-red-v1/tokens.json \
  --out-dir <validation-out>
```

- 页型未知 → **L1 生长通道**，不硬套  
- 文案溯源：`scripts/verify_text_provenance.py`  
- 禁词表与 content_lock 纪律见架构 §6  

---

## 7. 与既有入口的关系

| 资产 | 关系 |
|------|------|
| 通用 Word 契约 | 业务提交格式权威；L2 解析服从它 |
| `plan_training_course.py` | **视频**场景配方规划，输出不是 product-training-script |
| 绿系 `assemble_product_training_pptx.py` | 结构实验通道；正式图文交付走 courseware-pptx-v1 |
| natural-import manifests | 旧绿壳导入中间态；新主链路以 structured script 为准 |
| L1 页型提案 | script 确认后映射失败时启用 |

---

## 8. 验收（L2 完成标准）

1. 手册 + schema 入库  
2. `draft_product_training_script.py` 对样例大纲可出草稿 + 清单  
3. 草稿经 provenance 自检  
4. 文档写明四步与 generate 衔接  
5. **不**自动把 content_lock 标为已审  

可选后续：WorkBuddy 一键、从 Word 抽图到 asset gap、CI schema 校验。
