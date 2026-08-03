# Pharmacy Health Cartoon v1

## 视觉语法

- 二维健康科普卡通；
- 中等粗细深棕色线稿；
- 圆润、简化但成人化的人物比例；
- 扁平色块，只有克制的柔和阴影；
- 单一主题色背景＋奶油色圆形光晕＋少量症状符号；
- 正方形构图，主体居中，至少 10% 安全区；
- 在 150×150 缩略图中仍可直接识别症状。

## 固定约束

- 无文字、标签、Logo、水印和 UI 边框；
- 不使用参考视频像素，不复制参考人物和构图；
- 不做照片、3D、华丽动漫或恐怖医学表现；
- 不通过夸张、恶心或污名化表情强化症状；
- 人物类组件优先复用同一青年患者角色系统；
- 器官/分泌物类组件使用同一线稿与色块逻辑。

## 变量结构

```json
{
  "subject_type": "patient | anatomy-closeup | symptom-symbol",
  "symptom": "fever",
  "expression": "tired",
  "gesture": "front-bust",
  "body_signal": ["flushed-face", "sweat"],
  "symbol": ["heat-wave"],
  "palette": {
    "background": "#ff6b4d",
    "halo": "#ffd39b",
    "accent": "#e74424"
  }
}
```

同一配方更换 `symptom`、`gesture`、`body_signal`、`symbol` 和主题色即可扩展其他疾病、商品培训或护理场景。不得只替换颜色而保留错误症状动作。
