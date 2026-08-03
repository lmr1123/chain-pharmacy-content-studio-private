# validation · 急性上呼吸道感染 · 参课蓝（已升格 settled）

本目录为**探索与迭代过程**；权威金样已沉淀：

**`production-library/templates/settled/disease-health-shenke-blue-v1/`**

| 分类 | 健康培训 |
|------|----------|
| template_id | `template.disease-health-shenke-blue-v1` |
| 主交付 | 疾病健康知识培训可编辑 PPTX |
| 示例主题 | 急性上呼吸道感染 |

换病量产、业务 Word、生成器请以 settled 目录为准。

## 本目录保留

- 迭代中的 `build-editable.mjs` / content / assets
- `qa/` 渲染抽检
- v1/v2 历史成片对照

## 复用（推荐 settled）

```bash
cd production-library/templates/settled/disease-health-shenke-blue-v1/generator
cp content/急性上呼吸道感染.content.json content/<新病名>.content.json
# 编辑 JSON 后
node build-editable.mjs content/<新病名>.content.json
```
