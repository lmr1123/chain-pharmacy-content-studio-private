# 多金样组合课件 · 三案例业务 UAT

这三套 fixture 只验证“选择 2–3 个已签样课型能力，并在同一视觉下重新编排”的生产合同，不对应真实商品，不得进入正式业务交付。

统一规则：

- 路线：`product-pptx-component-v1`
- 引擎：`courseware-pptx-v1`
- 唯一视觉：`style-pack.reference-product-blue-v1`
- 来源课型只贡献信息层级或页型能力，不复用来源文案、母版、包装或原图
- 辅酶 Q10 血缘只提供浅蓝 style pack；数字讲师/口型、配音、镜头运动、MP4 时间线和视频字幕均为视频专属能力，不进入 PPT
- 脚本只有内部资料核验内容，不包含医学内容、用量或联推建议
- 商品图使用一张真实存在的无品牌 UAT 文件；授权边界见 `packshot-authorization.json`
- 三案所选页型均由可编辑文字、卡片、步骤路径和数据图形完成，非商品外图槽为 0，因此 `asset-bindings.json` 的空映射是正式合同，不是漏填
- 三案封面均显式包含 3 条组合说明和 `内部 UAT` 阶段标签，便于一眼识别来源组合与页序差异

## 验收矩阵

| 案例 | 业务意图 | 来源课型页签 | 新增页签 | 页数 / 页序 |
|---|---|---|---|---|
| A | 资料核验闭环 | 绿色商品总览 + 穿心莲咨询框架 + 速福达证据阶梯 | 异议与升级 | 7 页：封面 → 导语 → 总览 → 咨询 → 证据 → 异议 → 总结 |
| B | 陈列物料核验 | 速福达证据阶梯 + 绿色商品总览 | 临时变更处理 | 6 页：封面 → 数据钩子 → 证据 → 总览 → 异议 → 总结 |
| C | 交接与封存 | 穿心莲咨询框架 + 速福达证据阶梯 | 无 | 5 页：封面 → 导语 → 咨询 → 判定表 → 证据 |

机器可读的来源边界在 `source-capability-matrix.json`；每案的业务意图、页码、页型、素材槽和视觉验收项在各自的 `case-contract.json`。

## 可直接运行：案例 A

以下命令必须从仓库根目录运行。`--scope uat` 会把任务与正式业务隔离；若同名任务已经存在，请更换 `--job-id`。

```bash
python3 scripts/business_job.py new --scope uat --route product-pptx-component-v1 --theme '晴岚资料核验套装 A（内部 UAT）' --product-image production-library/validation/courseware/component-neutral-business-uat-v1/assets/uat-packshot.png --script-json production-library/validation/courseware/multi-gold-composition-uat-v1/case-a-three-gold-new-tab/script.structured.json --job-id multi-gold-uat-a-20260809 --auto-draft
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-a-20260809 --gate content --by '业务验收人'
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-a-20260809 --gate visual --by '业务验收人' --asset-bindings production-library/validation/courseware/multi-gold-composition-uat-v1/case-a-three-gold-new-tab/asset-bindings.json
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-a-20260809 --gate product_image --by '业务验收人' --product-image production-library/validation/courseware/component-neutral-business-uat-v1/assets/uat-packshot.png --authorization-reference UAT-FIXTURE-NONBRAND-20260809
python3 scripts/business_job.py render --scope uat --job multi-gold-uat-a-20260809
python3 scripts/business_job.py status --scope uat --job multi-gold-uat-a-20260809
python3 scripts/business_job.py open --scope uat --job multi-gold-uat-a-20260809 --reveal
```

## 可直接运行：案例 B

```bash
python3 scripts/business_job.py new --scope uat --route product-pptx-component-v1 --theme '澄明陈列物料 B（内部 UAT）' --product-image production-library/validation/courseware/component-neutral-business-uat-v1/assets/uat-packshot.png --script-json production-library/validation/courseware/multi-gold-composition-uat-v1/case-b-evidence-overview/script.structured.json --job-id multi-gold-uat-b-20260809 --auto-draft
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-b-20260809 --gate content --by '业务验收人'
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-b-20260809 --gate visual --by '业务验收人' --asset-bindings production-library/validation/courseware/multi-gold-composition-uat-v1/case-b-evidence-overview/asset-bindings.json
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-b-20260809 --gate product_image --by '业务验收人' --product-image production-library/validation/courseware/component-neutral-business-uat-v1/assets/uat-packshot.png --authorization-reference UAT-FIXTURE-NONBRAND-20260809
python3 scripts/business_job.py render --scope uat --job multi-gold-uat-b-20260809
python3 scripts/business_job.py status --scope uat --job multi-gold-uat-b-20260809
python3 scripts/business_job.py open --scope uat --job multi-gold-uat-b-20260809 --reveal
```

## 可直接运行：案例 C

```bash
python3 scripts/business_job.py new --scope uat --route product-pptx-component-v1 --theme '星河交接资料 C（内部 UAT）' --product-image production-library/validation/courseware/component-neutral-business-uat-v1/assets/uat-packshot.png --script-json production-library/validation/courseware/multi-gold-composition-uat-v1/case-c-handoff-path/script.structured.json --job-id multi-gold-uat-c-20260809 --auto-draft
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-c-20260809 --gate content --by '业务验收人'
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-c-20260809 --gate visual --by '业务验收人' --asset-bindings production-library/validation/courseware/multi-gold-composition-uat-v1/case-c-handoff-path/asset-bindings.json
python3 scripts/business_job.py approve --scope uat --job multi-gold-uat-c-20260809 --gate product_image --by '业务验收人' --product-image production-library/validation/courseware/component-neutral-business-uat-v1/assets/uat-packshot.png --authorization-reference UAT-FIXTURE-NONBRAND-20260809
python3 scripts/business_job.py render --scope uat --job multi-gold-uat-c-20260809
python3 scripts/business_job.py status --scope uat --job multi-gold-uat-c-20260809
python3 scripts/business_job.py open --scope uat --job multi-gold-uat-c-20260809 --reveal
```

`render` 只有在内容、视觉、包装三道确认齐全且本机 QA 环境通过时才会发布到 UAT 取件目录。正式业务必须替换为业务授权的真实商品包装图和正式授权编号。

## 合同测试

```bash
python3 -m unittest scripts.test_multi_gold_composition_uat
```

测试会核对：来源文件真实存在、三案来源组合不同、A 含三个金样来源和新页签、7/6/5 页序准确、脚本无医学/用量/联推内容、包装 SHA 与授权记录一致、外图槽和空绑定合同一致。

## 最终 UAT 状态

A / B / C r4 已分别以 7 / 6 / 5 页通过 `business_job` 内容 → 视觉 → 商品图三闸并进入 UAT delivered；本机取件证据为 `outputs/workbuddy-workspaces/uat/delivery/uat-component-suite-{a,b,c}-20260810-r4/`。**r4 逐页已通过**：artifact-tool 18 / 18、全部 fixture 业务文字进入 PPT、金样词/源图 SHA/占位为 0、三套 Presentations `slides_test` 无越界，且人工逐页复核完成。

`_engine-qa/` 与 `_engine-qa-r2/` 保留为历史引擎检查记录，不代表当前最终状态。suite v3 hash-bound 校验已经合格并完成同步，门户当前展示 A / B / C 三案例；后续证据哈希失配时必须 fail-closed 隐藏，不能回退旧金样预览。
