# 企业内部培训课件 · 字体规范（商品 PPT）

## 问题根因

`@oai/artifact-tool` 导出 PPTX 时，`a:rPr` 只写入字号/粗体，**不写 typeface**；主题默认又是 Calibri。  
PowerPoint 打开后中文全部回退成同一默认字体，看起来像「字体全丢了」。

## 统一选型（本项目）

| 角色 | 字体 | 说明 |
|------|------|------|
| **正文 / 标题 / 表格（唯一主字体）** | **微软雅黑**（`Microsoft YaHei` / `微软雅黑`） | 门店与办公 PC 以 Windows 为主，预装率高 |
| macOS 预览 | 系统可映射到相近无衬线黑体 | 正式交付以 Windows 打开为准 |
| 禁止 | 未授权商用字体、细体艺术字、同一页混用 3 种以上中文字体 | 可读性与合规 |

### 为什么不优先 PingFang SC？

视觉规范视频侧可用 `PingFang SC`，但 **PPT 内训下发 Windows 时 PingFang 常缺失**，会再次回退。  
微软雅黑在连锁药店终端更稳。

### 字重与层级（与绿模板一致）

| 层级 | 建议 |
|------|------|
| 封面主标题 | 粗体，约 36–48pt（长品名自适应缩小） |
| 页标题 | 粗体，约 22–24pt |
| 小节标题 / 表头 | 粗体，约 16–18pt |
| 正文 / 话术 | 常规或半粗，约 14–16pt |
| 页脚「仅供内部学习」 | 常规，约 10–11pt |

同一课件只保留 **一种中文字体家族**；用字号和粗细做层级，不靠换字体。

## 技术落地

1. 生成脚本声明 `fontFamily = "Microsoft YaHei"`（影响 PNG 预览渲染）。  
2. `postprocess-product-courseware-pptx.py`：  
   - 改写 `ppt/theme/theme1.xml` 的 major/minor 字体；  
   - 为全部 `a:rPr` 注入 `latin` / `ea` / `cs` typeface。  
3. 业务在 PowerPoint 里「替换字体」时，应整份统一替换为微软雅黑，不要只改某一页。

## 注意事项插图

最后一页 4 张图为 **AI 示例图（可替换）**，语义如下：

| 槽位 | 文件 | 含义 |
|------|------|------|
| 不替代药物治疗 | `assets/precautions/01-not-replace-drug.png` | 保健品 ≠ 处方药 |
| 特殊人群慎用 | `assets/precautions/02-special-groups.png` | 孕妇/儿童/乳母等 |
| 按量随餐服用 | `assets/precautions/03-with-meal.png` | 按量 + 随餐 |
| 不适及时就医 | `assets/precautions/04-see-doctor.png` | 不适去医院 |

业务可直接在 PPT 里右键换图，或替换上述 PNG 后重跑生成脚本。
