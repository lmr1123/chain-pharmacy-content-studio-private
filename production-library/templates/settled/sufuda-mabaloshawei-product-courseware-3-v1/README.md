# 速福达®玛巴洛沙韦 · 商品培训课件3 金样 v1

**一句话**：连锁药店内部培训用「商品培训课件3」形态的金样，商品为 **速福达®（玛巴洛沙韦）**。

> **业务自助状态（2026-08-09）：** 该固定课型的新主题 **PPTX 已上线**（13 页、可编辑、逐页 QA）；金样 MP4 仅是历史签样预览，不代表新主题 MP4 可生成。`courseware3-mp4-v1` 尚未上线，WorkBuddy 不得承诺或交付新主题课件3 MP4。

| 看什么 | 文件 |
|--------|------|
| 视频金样 | `速福达玛巴洛沙韦_商品培训课件3_金样_v1.mp4`（约 94s · 1920×1080） |
| 可编辑 PPT | `速福达玛巴洛沙韦_商品培训课件3_金样_可编辑课件_v1.pptx`（13 页） |
| 元数据 | `manifest.json` |
| 内容快照 | `content-model.snapshot.json` |
| 业务 Word | `业务提交_空白模板.docx` / `业务提交_填写参考.docx` |

## 命名约定

```
{商品名}{通用名}_{课件系列}_金样_v{n}.{ext}
```

例：`速福达玛巴洛沙韦_商品培训课件3_金样_v1.mp4`  
扫 `templates/settled/` 时一眼能对应到哪个药。

## 工程与再导出

完整可改工程（Revideo + 导出脚本）在：

`production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/`

```bash
cd production-library/validation/courseware/sufuda-product-courseware-3-gold-v1
npm run export:pptx   # 可编辑 PPT
npm run render        # 视频（需依赖就绪）
npm run start:editor  # 业务图层编辑器
```

签样日期：**2026-08-02**（用户确认归档）。

## 业务整片预览

给业务打开（本地需能访问工程目录）：

```text
production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/web/full-film.html
```

金样案例汇总（后续各金样点进预览）：

```text
production-library/validation/courseware/gold-samples/index.html
```

快捷打开（仓库根目录）：

```bash
open production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/web/full-film.html
# 或起本地静态服务（推荐，避免 file:// 限制）
cd production-library/validation/courseware && python3 -m http.server 8765
# 浏览器打开 http://127.0.0.1:8765/gold-samples/
```
