# courseware-pptx-v1

通用可编辑 PPTX 引擎（构件 + style tokens + 布局规则）。

**约束：** 不修改 cw4 旧导出器 `product-courseware-4-faithful-replica-v1/scripts/export-cw4-pptx.mjs`。

## 用法

```bash
# 金样回归（silk style + 金样 content-model + 金样 assets）
node production-library/engines/courseware-pptx-v1/export.mjs \
  --model production-library/validation/courseware/product-courseware-4-faithful-replica-v1/content-model.json \
  --style production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json \
  --assets production-library/validation/courseware/product-courseware-4-faithful-replica-v1 \
  --out production-library/validation/courseware/product-courseware-4-faithful-replica-v1/out/engine-v1-gold.pptx

# 麦金利 cream-red（M5）
node production-library/engines/courseware-pptx-v1/export.mjs \
  --model …/content-model.json \
  --style production-library/styles/lycopene-health-edu-cream-red-v1/tokens.json \
  --out …/out.pptx

# layer manifest（参数化）
python3 production-library/engines/courseware-pptx-v1/build_layer_manifest.py \
  --model PATH/content-model.json \
  --out PATH/layer-manifest.json \
  --prefix editable:cw4

# 默认 --recipes = page-types/product-training/recipes（含 scene-type-map + 9 页型）
# candidate 三页：
node production-library/engines/courseware-pptx-v1/export.mjs \
  --model production-library/validation/courseware/m3-candidate-pages/content-model.json \
  --style production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json \
  --assets production-library/validation/courseware/product-courseware-4-faithful-replica-v1 \
  --out production-library/validation/courseware/m3-candidate-pages/out/m3-candidates.pptx
```

## 新页型生长（L1）

未知内容形态：**提案 → QA 签样 → registry**，禁止静默硬套。  
手册：`docs/page-type-growth-channel.md` · 提案目录：`page-types/product-training/proposals/`

## 目录

| 路径 | 说明 |
|------|------|
| `export.mjs` | CLI：`--model/--style/--recipes/--out/--assets/--prefix` |
| `lib/tokens.mjs` | 加载 style pack，统一字号阶梯 |
| `lib/context.mjs` | 坐标 / shape / text / imageFit（只读 tokens） |
| `components/*` | 构件库（chrome_bg、chapter_title、nav_pills…） |
| `layout-rules.mjs` | N 卡栅格 / 字号降档 / 链路居中 / 拆页 |
| `scenes/builders.mjs` | content-model scene type → 构件组合（金样兼容） |
| `build_layer_manifest.py` | `--model/--out/--prefix` |
| `lib/recipes.mjs` | 加载 page-types recipes + scene 映射 |
| `recipes/` | 占位；正式 recipe 在 `page-types/product-training/recipes/` |

## artifact-tool

从**仓根绝对路径**解析：

`poc/courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs`

## 验收

金样 content-model 经本引擎导出后，QA 图与 **pptx-qa**（cw4 金样 PPT）并排目检；不一致停下修。

## 培训字号

style tokens 使用 `type.scale_factor`（silk 默认 **1.28**）抬升投影可读字号；正文下限 **16pt**，说明 **14pt**。  
对齐 `docs/courseware-visual-spec-1080p.md` 有效字号下限思路。

## 插图去底（强制）

插画贴在丝绸/米白底上，**禁止带不透明底板色**（白/米/灰整块）：

```bash
# 质检
python3 production-library/engines/courseware-pptx-v1/ensure_transparent_assets.py \
  --dir production-library/validation/courseware/product-courseware-4-faithful-replica-v1/assets/generated

# 失败则 whitekey 抠透明（生成 .bak）
python3 …/ensure_transparent_assets.py --dir …/assets/generated --apply

# 单图
python3 …/whitekey-cutout.py in.png out.png --tol 26
python3 …/check-alpha.py out.png
```

门禁：四角 8×8 `max alpha ≤ 8`。`slot-pack-*` 包装占位卡 UI 豁免。  
新生成插画（M5 注意事项等）必须：生图 → whitekey → check-alpha → 入库。
