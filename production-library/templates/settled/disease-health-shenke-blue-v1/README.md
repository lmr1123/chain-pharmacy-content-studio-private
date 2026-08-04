# 疾病健康知识培训 · 参课蓝金样 v1

| 项 | 说明 |
|----|------|
| template_id | `template.disease-health-shenke-blue-v1` |
| 分类 | **健康培训** |
| 主交付 | `急性上呼吸道感染_疾病健康知识培训_可编辑金样_v3.pptx`（v2 文件保留为历史签样版） |
| 风格 | 参课蓝（蓝方章号 / Logo / 角标 / 虚线正文框） |
| 状态 | 已签样 settled |

## 目录

| 路径 | 作用 |
|------|------|
| `*.pptx` | 权威可编辑金样 |
| `generator/` | JSON → PPTX 生成器 + 样例 content（首次 `npm install`） |
| `assets/` | 重绘插图 + 包装命名坑位 |
| `业务提交_空白模板.docx` | 业务填内容入口 |
| `业务提交_填写参考.docx` | 结构示范（非医学结论） |
| `本课型怎么填.md` | 业务口令与板块说明 |
| `preview/` | 目录/画廊预览帧 |
| `manifest.json` | 元数据 |

## 与 validation 关系

探索与迭代过程在：

`production-library/validation/courseware/disease-uri-shenke-blue-v1/`

本目录为 **用户确认后的 settled 权威副本**，量产与换病优先从此复制。

## 业务替换包装图

```text
assets/packshots/复方氨酚烷胺胶囊.png   # 授权实拍优先
# 或直接替换 placeholders 后重建
```

## 验收要点（金样锁定）

- [x] 正文可编辑（非整页死图）
- [x] 参课版式 chrome
- [x] 对症表重点药名深蓝加粗
- [x] 注意事项仅「禁用」标红
- [x] 末页竖版一页通（手机可看比例）
- [x] 包装命名坑位，不伪造品牌包装
