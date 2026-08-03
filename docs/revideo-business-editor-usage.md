# Revideo 业务画面编辑器使用说明

更新日期：2026-07-31  
当前状态：**使用观察期；暂停继续扩展功能**

## 1. 适用范围

### 风热证视频

当前编辑器用于风热证完整视频模板的业务级局部调整：

- 在画布中点选、框选或按 `Shift` 多选已声明的业务图层；
- 直接拖动位置、拖四角缩放、拖顶部圆点旋转；
- 修改文字、透明度、显示状态和基础对齐；
- 单张或多张替换插图；
- 撤销、重做、复制和粘贴调整；
- 将当前个性化项目导出为 MP4 或原生可编辑 PPTX；
- 将确认有复用价值的调整另存为新的模板候选版本。

它复用 Revideo 原有时间线、预览和渲染能力，不是重新开发一套通用动画编辑器。

### 商品培训课件（速福达壳）

同一套 `editable:` 图层插件也用于速福达商品培训金样：

- 内容源：`content-model.json` + `layer-manifest.json`
- 稳定 ID：`editable:sufuda:{page}:{role}`
- 可直接导出 12 页原生 PPTX（不强制另存模板）
- 换主题：`scripts/replicate_courseware_theme.py` + `theme-packages/`

详见：`production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/docs/content-model-and-editor.md`。

### 商品培训课件4（福尔番茄红素）

同一套模式用于课件4保真复刻金样：

- 内容源：`content-model.json` + `layer-manifest.json`
- 稳定 ID：`editable:cw4:{page}:{role}`
- 16 页原生可编辑 PPTX（对标速福达 Artifact Tool 导出；关联用药 note 在上、总结行标题）
- 命令：`npm run export:pptx` / `npm run start:editor`（:9012）

目录：`production-library/validation/courseware/product-courseware-4-faithful-replica-v1/`。

## 2. 启动与入口

### 风热证

```bash
cd poc/gold-sample
npm run start:wind-heat-editable
```

浏览器访问：`http://127.0.0.1:9000/`

### 速福达商品培训课件

```bash
cd production-library/validation/courseware/sufuda-product-courseware-3-gold-v1
npm run start:editor
```

浏览器访问：`http://127.0.0.1:9010/`

仅导出课件（不启编辑器）：

```bash
npm run export:pptx
```

### 福尔番茄红素商品培训课件4

```bash
cd production-library/validation/courseware/product-courseware-4-faithful-replica-v1
npm run start:editor
```

浏览器访问：`http://127.0.0.1:9012/`

仅导出课件：

```bash
npm run export:pptx
# → out/福尔番茄红素_商品培训课件4_可编辑课件_v1.pptx
```

右侧“画面属性”面板是业务操作入口。画布较窄时可以先收起面板，或把浏览器窗口拖宽。

## 3. 常用操作

| 目的 | 操作 |
|---|---|
| 选择一个图层 | 直接点击真实文字、图片或已声明的业务组合 |
| 选择多个图层 | 按住 `Shift` 依次点击，或从画布空白处拖出选框 |
| 整体移动 | 选中后直接拖动；方向键微移，`Shift + 方向键` 每次移动 10px |
| 缩放／旋转 | 拖选择框四角缩放；拖顶部圆点旋转 |
| 修改文字 | 选中文字图层后点击“修改文字” |
| 替换图片 | 选中一张或多张图片后使用“替换图片” |
| 撤销／重做 | 使用右侧按钮，或 `Cmd/Ctrl + Z` |

所有变换都直接在画布完成，右侧不再提供“拖动模式／旋转模式”等额外切换按钮。

## 4. 导出当前作品

“导出视频”和“导出可编辑课件”只消费当前画布中的调整，不要求先保存模板，也不会自动沉淀模板。

- **导出视频**：按完整 Revideo 时间线生成 MP4。
- **导出可编辑课件**：生成 7 页 PPTX；文字、图片和基础形状是 PowerPoint 原生可编辑对象。

PPTX 与视频共用当前内容和素材映射，但由独立课件渲染器生成；不承诺数字人口型、粒子、电流或时间轴动画与视频完全等价。

## 5. 另存模板版本

只有准备在后续项目继续复用当前调整时，才使用“另存为新模板版本”：

1. 第一次点击后，按钮变为“确认另存新版本”，此时不会写文件。
2. 需要在 10 秒内再次点击确认；快速双击不会保存。
3. 新版本号包含毫秒时间和唯一短码，例如 `20260731T023113195Z-a57d`。
4. 每次保存只新增候选版本；正式原模板和所有历史候选版本均不会被覆盖。
5. `current-candidate.json` 只是当前候选指针，不是 settled 正式模板。

## 6. 与剪映的分工

- Revideo 业务编辑器：改模板内部已声明的文字、图片和基础布局，并直接导出当前作品。
- 剪映：继续承担单条视频的裁切、重排、字幕、音频、转场及后加效果精修。
- 剪映修改和 Revideo 候选都不会自动覆盖正式模板；只有经确认、确实可复用的改动才晋升为正式模板新版本。

## 7. 当前边界

- 只能操作已登记稳定 `layer_id` 的业务对象，不支持任意新建图层或重做复杂动画时间线。
- 复杂数字人口型、粒子和程序动画仍由 Revideo 模板代码控制。
- 当前为个人内部使用验证，不以通用设计软件或商用 SaaS 的功能完整度为目标。

## 8. 使用观察期

从 2026-07-31 起暂停继续增加编辑器功能，先在真实业务任务中使用一段时间。后续只根据重复出现、明显影响交付的实际问题继续迭代。

建议每次只记录：

- 调整了什么内容；
- 哪一步操作不顺；
- 是否影响完成导出；
- 是偶发问题还是连续多次出现；
- 希望的最简单改法。

单次偏好或尚未发生的设想不立即扩展为新功能。
