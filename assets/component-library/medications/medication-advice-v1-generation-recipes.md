# 药物调理与生活建议组件 v1：生成记录

生成方式：Codex 内置 `imagegen`。参考视频只用于构图与比例测量，以下素材均为重新生成的原创画面。

## 无品牌颗粒剂包装

- 文件：`granule-package/transparent/granule-package-v1.png`
- 用途：药品卡中的颗粒剂通用包装主体。
- 提示词摘要：无品牌白色自立药袋、青绿植物山水装饰、无字标签区、洋红抠图底、商业药品摄影质感。
- 限制：不出现药名、厂家、Logo、批准文号或真实包装识别元素。

## 无品牌胶囊纸盒

- 文件：`capsule-carton/transparent/capsule-carton-v1.png`
- 用途：药品卡中的胶囊通用包装主体。
- 提示词摘要：无品牌白色药盒、蓝青色斜切色块、无字标签区、洋红抠图底、商业药品摄影质感。
- 限制：不出现药名、厂家、Logo、批准文号或真实包装识别元素。

## 四项生活建议图标

- 通风：`../advice-icons/ventilation/transparent/ventilation-v1.png`
- 温水：`../advice-icons/warm-water/transparent/warm-water-v1.png`
- 清淡饮食：`../advice-icons/light-diet/master/light-diet-badge-v2.png`
- 戒烟戒酒：`../advice-icons/no-smoking-alcohol/master/no-smoking-alcohol-badge-v2.png`

首轮四宫格使用洋红抠图底。通风和温水图标透明化通过；清淡饮食和戒烟戒酒的红色主体与洋红键色冲突，因此没有保留被误抠的结果，而是重新生成深蓝底完整徽章 v2。

## 复用规则

- 药名、剂型、提示语全部由程序文字层绘制。
- 无品牌包装必须显示“包装示意”，不能被当作真实商品图。
- 公司正式生产时，可在同一 `MedicationCard` 中替换为内部授权且审核通过的包装图。
- 图标只表达生活行为，不承载药学结论。
