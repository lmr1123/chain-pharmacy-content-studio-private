# other-model-remake-attempt-v1

独立重做 **K03** 与 **K13** 的尝试目录（合同指定输出位置）。

## 状态

**待人审** — 模型不得自行报告金样通过。

## 渲染

```bash
cd production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/other-model-remake-attempt-v1
node src/render.mjs k03
node src/render.mjs k13
```

场景源码在 `src/`；`poc/gold-sample` 仅提供薄桥接 project 与 Revideo / public 资产宿主。

## 主交付

| 文件 | 说明 |
|---|---|
| `k03-remake.mp4` | K03 成片 |
| `k13-remake.mp4` | K13 成片 |
| `frames/k03-contact.png` | 8 帧接触表 |
| `frames/k13-contact.png` | 8 帧接触表 |
| `frames/K0*-S0*-{entry,performance,exit}.png` | 逐镜三帧 |
| `SELF_REVIEW.md` | 逐镜语义自检 |
| `qa-report.json` | 技术与门禁记录 |
| `review.html` | 并排审片页 |

未覆盖 `remake-comparison-v1/` 既有整改样片。
