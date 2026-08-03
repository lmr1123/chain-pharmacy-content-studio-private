> **状态（2026-07-31）：用户要求暂停。**  
> 最新成片为 **v4**（`kekang-lingzhi-training.mp4`），用户判定不满意，**勿自动续改**。  
> **交接文档（下一会话必读）：** [`HANDOVER-2026-07-31.md`](./HANDOVER-2026-07-31.md)

# 可可康灵芝胶囊 — 商品培训视频（第二主题延伸）

**theme_id：** `theme.product.kekang-lingzhi-capsule`  
**模板：** `template.product-training-faithful-v1`  
**风格包：** `style-pack.reference-product-blue-v1`  
**复用：** 大参林扩展四件套（chrome / v5-smooth / MOUTH_RIG / 封面）  
**目的：** 验证「换商品主题」主要靠套壳，而不是重造壳/声/口型。

## 需求背景（为何开这个主题）

- Q10 只证明**一份**商品课能做成大参林版。
- 工厂价值在于**第二个、第 N 个**主题仍快、仍统一。
- 本主题是 todo 支线 A 的实装对象：用户指定商品名 = 可可康灵芝胶囊。

## 当前状态

| 项 | 状态 |
|----|------|
| 主题登记 | 已完成 |
| 脚本 | **v3 全套确认 PPT** → `script-draft-v3.md` |
| 联合用药 | ✅ 三方案：谷维素+灵芝；护肝片+灵芝；转移因子+灵芝（课件原文） |
| 口径状态 | refs/01～09 公司确认截图已归档 |
| 授权包装 | **阻塞** — 批量前必须业务提供 |
| 套壳预览 | 结构封面已有；完整视频等审核通过后再配音 |
| 用户视觉签样 | 未开始 |

## 复用清单（勿重造）

1. `poc/gold-sample/src/components/product-training-dashenlin-chrome.tsx`
2. `scripts/generate_cloned_product_all_narration.py` → `v5-smooth`
3. `MOUTH_RIG` palm `[0.548,0.391]` / point `[0.528,0.418]`
4. 封面：右上角品牌 Logo 安全区（参考 Q10 封面脚本逻辑）

## 审核入口（可视化）

**请在确认门户审脚本，不要只在对话里看：**

```bash
open production-library/validation/review-hub.html
```

Tab「可可康·脚本 v2」+「认识灵芝·分镜」；封面 / 缺口 / 进展同页可切换。

## 下一步

1. 你在确认门户核对多糖/三萜是否与确认 PPTX 一字不差  
2. 回复「脚本 v2 过」后：套「认识灵芝」镜头 + v5-smooth 配音  
3. 栏目签「可可康灵芝胶囊」+ 大参林四件套  
4. 无水印孢子图 / 授权包装到位后替换占位  
5. 门户新增「可可康视频」Tab → 签样  

详见 `script-draft-v2.md`、`asset-gaps.md`、`assembly-plan.json`。
