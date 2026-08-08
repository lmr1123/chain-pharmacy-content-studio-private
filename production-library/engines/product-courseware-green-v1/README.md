# product-courseware-green-v1 正式导出引擎

绿色单品商品培训 PPT（5 页）的**正式生产路径**。业务任务经 `business_job` 调用本目录，不再依赖 `poc/courseware-export` 作为入口。

## 入口

```bash
node production-library/engines/product-courseware-green-v1/build-product-courseware.mjs \
  --data /path/to/content-model.json \
  --out /path/to/out.pptx \
  --qa /path/to/qa
```

无参数时默认使用本目录 `gold-content-model.json`（金银花露金样结构，仅供回归）。

## 依赖

- Node.js
- `@oai/artifact-tool`（目录下 `node_modules` 或 `NODE_PATH`）
- 本机 Python3（postprocess 注入微软雅黑）

开发机可把 `node_modules` symlink 到历史 `poc/courseware-export/work/node_modules`。
正式安装见 `production-library/runtime-profiles.json` 的 `pptx` profile。

## 换主题纪律

业务草稿由 `scripts/business_job.py` 的 `_draft_product_pptx_green` 生成，必须剥离金样商品名/编码/价/联合/对标/注意文案；本引擎只负责渲染，不做医学补写。
