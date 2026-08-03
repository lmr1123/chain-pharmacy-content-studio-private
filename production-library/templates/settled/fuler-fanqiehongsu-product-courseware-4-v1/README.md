# 福尔番茄红素软胶囊 · 商品培训课件4 金样 v1

**一句话**：连锁药店内部培训用「商品培训课件4」形态的金样，商品为 **福尔番茄红素软胶囊**。

| 看什么 | 文件 |
|--------|------|
| 视频金样 | `福尔番茄红素_商品培训课件4_金样_v1.mp4`（约 **156.7s** · 1920×1080） |
| 可编辑 PPT | `福尔番茄红素_商品培训课件4_金样_可编辑课件_v1.pptx`（**15** 页） |
| 元数据 | `manifest.json` |
| 内容快照 | `content-model.snapshot.json` · `layer-manifest.snapshot.json` |
| 编辑器动效源 | `src-snapshot/project.tsx` |
| 业务 Word | `业务提交_空白模板.docx` / `业务提交_填写参考.docx` |

## 本版要点（2026-08-03 更新归档）

- 叙事：**适宜人群 → 关联用药 → 三大核心功效表 → 结尾**（已删速福达式四列表总表）
- 章节带序号：一、三大核心功效 … 四、关联用药 … 五、功效总表
- 成片：PIL 多帧动效（入场 / 箭头沿指向方向 / 手绘叉）
- 业务编辑器：`:9012` 内 **Revideo 可播放动效**（对齐辅酶 Q10 / 礼风热证）
- 扩展旁白：S12–S13 Qwen3 克隆（prompt 须与 ref_text 对齐）

## 命名约定

```
{商品名}_{课件系列}_金样_v{n}.{ext}
```

例：`福尔番茄红素_商品培训课件4_金样_v1.mp4`

## 工程与再导出

完整可改工程（Revideo + 导出脚本）在：

`production-library/validation/courseware/product-courseware-4-faithful-replica-v1/`

```bash
cd production-library/validation/courseware/product-courseware-4-faithful-replica-v1
npm run export:pptx     # 可编辑 PPT
npm run export:video    # 视频静帧成片
npm run start:editor    # 业务图层编辑器 :9012
```

签样 / 更新归档：**2026-08-03**（用户确认写入金样，后续可再迭代）。

## 业务整片预览

```text
production-library/validation/courseware/product-courseware-4-faithful-replica-v1/web/full-film.html
```

金样案例汇总：

```text
production-library/validation/courseware/gold-samples/index.html
```

```bash
cd production-library/validation/courseware && python3 -m http.server 8765
# 浏览器打开 http://127.0.0.1:8765/gold-samples/
```
