# 注意事项四插画 · 生成配方 v1

风格锚：`assets/component-library/styles/dashenlin-medical-flat-illustration-v1.md`  
用途：商品培训 PPTX `precautions` 页右侧 2×2。

## 公共约束

- 方形 1:1，主体居中，四周 ≥14% 安全区（入库时脚本再 pad）
- 纯白底；无图内文字、字母、数字、Logo、水印
- 扁平医药培训插画；深色圆润线稿；4–6 主色；无照片/3D
- 药品物件仅无标签通用药瓶/胶囊，不仿真实包装

## 四角色主题

| 文件 | 主题 |
|------|------|
| pre-not-medicine | 保健营养品不能代替处方药物：胶囊+药瓶旁红色叉号 |
| pre-special-pop | 特殊/禁忌人群须谨慎：老年顾客 + 警示徽章 |
| pre-with-meal | 建议随餐：热汤/饭碗旁软胶囊 |
| pre-consult | 就医/药师咨询：柜台药师向顾客说明药品 |

## 后处理

```bash
python3 production-library/engines/courseware-pptx-v1/whitekey-cutout.py \
  source/PRE-src.jpg transparent/PRE-raw.png --tol 34
# 再 pad 到 1024×1024（14% 边距）→ check-alpha.py
```
