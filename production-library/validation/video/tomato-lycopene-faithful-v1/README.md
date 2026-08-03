# 福尔麦金利番茄红素软胶囊·失败版本（禁止作为复刻模板）

> 用户于 2026-08-02 否决：本版本把参考视频重设计为通用图解课件，内容、包装坑位、版式和镜头均未
> 达到 100% 复刻。所有产物仅保留为失败证据，不得复用、扩展、签样或进入 settled。

**课件4 保真复刻请改走：**  
`production-library/validation/courseware/product-courseware-4-faithful-replica-v1/`  
（见该目录 `VERSION.md` / `gate/compare.html`）

本目录仅保存未签样的 validation 产物。用户确认前不进入 `templates/settled/`。

## 内容单一真相源

`project.json` 同时驱动：

- `web/`：可选中、改文字、替换图片、拖动／缩放、撤销／重做的网页编辑器；
- `scripts/build-pptx.mjs`：原生可编辑 PPTX；
- `scripts/render-scenes.mjs` + `scripts/build-video.mjs`：分层渐入的 MP4。

以下为被否决的技术产物，不代表业务交付：

- `福尔麦金利番茄红素软胶囊_完整复刻.mp4`
- `福尔麦金利番茄红素软胶囊_可编辑课件.pptx`
- `review.html` 与 `qa/QA_REPORT.md`

## 启动编辑器

```bash
node scripts/server.mjs
```

访问 `http://127.0.0.1:9014/`。网页导出只消费当前项目快照，不覆盖正式模板。

网页支持直接改文字、选图替换、拖动／缩放、撤销／重做，并从当前快照导出 PPTX 或 MP4。
MP4 使用本项目已审核的固定旁白与字幕；若修改旁白正文，需要先重新生成并通过 ASR 后再导出。
直接双击 `web/index.html` 也可离线编辑和下载项目 JSON；PPTX/MP4 导出按钮需要先启动本地服务。

## 授权素材

`asset.product.packshot` 与 `asset.brand.logo` 等待业务提供独立授权原图。当前工程不从 480p 参考视频裁切包装、Logo 或其他像素。
