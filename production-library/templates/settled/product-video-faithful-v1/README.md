# 辅酶 Q10 · 商品培训视频 金样

**一句话**：连锁药店内部培训用「单品商品培训视频」形态的金样，商品为 **辅酶 Q10**（大参林壳扩展已签样）。

| 看什么 | 文件 |
|--------|------|
| 视频金样 | `辅酶Q10_商品培训视频_金样_v1.mp4`（≈ **156.2s** · 1920×1080） |
| 同内容技术名 | `product-training-reference-full-script-system-v3-final-exact.mp4`（硬链） |
| 元数据 | `manifest.json` |
| 场景清单快照 | `scene-inventory.snapshot.json`（8 段工程） |
| 语音包 | `voice/` → `voice.reference-pharmacist-qwen-v1` |
| 业务 Word | `业务提交_空白模板.docx` / `业务提交_填写参考.docx` |
| 货架预览 | `preview/` |

## 状态说明

| 项 | 说明 |
|----|------|
| 金样签样 | 用户 2026-07-30 确认完整复刻 + 大参林扩展层可沉淀 |
| 业务可用 | 换商品须提供 **审核旁白原文** + **授权包装/Logo**；讲解声走本包 `voice/` 克隆 |
| 真包装 | 示例包装仅为槽位示范，不得当授权素材 |

## 章节结构（8 段）

1. 开场教育  
2. 核心讲解 / 功效关系  
3. 品牌与品类  
4. 核心功效  
5. 产品特点  
6. 适宜人群  
7. 联合用药  
8. 总结  

分段成片（validation，非 settled 必带）：

```text
production-library/validation/video/product-training-*-replica.mp4
```

大参林扩展预览：

```text
production-library/validation/video/review-q10-dashenlin.html
production-library/validation/video/cover-q10-dashenlin.jpg
```

## 工程与再导出

源工程均在 `poc/gold-sample/src/product-training-*.tsx`，壳组件：

```text
poc/gold-sample/src/components/product-training-dashenlin-chrome.tsx
```

```bash
# 克隆各段旁白（v5-smooth）
python3 scripts/generate_cloned_product_all_narration.py

# 分段渲染后拼接为全片（见 gold-sample / validation 既有流程）
# 编辑器：
# cd poc/gold-sample && npm run start:q10-editor  # 以 package.json 为准
```

## 业务整片预览

```text
production-library/validation/courseware/gold-samples/product-q10-video-gold-v1/web/full-film.html
production-library/validation/courseware/gold-samples/index.html
```

## 命名约定

```
{商品名}_商品培训视频_金样_v{n}.mp4
```
