# 内容模型 · 元素拆解 · 编辑器 · 换主题

## 北极星

业务审核稿 + 授权资产 → 同风格 MP4 / 可编辑 PPTX；不改底层动画代码即可换商品主题。

## 单一内容源

| 文件 | 作用 |
|------|------|
| `content-model.json` | 全课文案、图片槽、页型、稳定 `element_id` |
| `layer-manifest.json` | 编辑器 / 导出 / QA 共用元素清单（136 项） |
| `storyboard.json` | 时码、字幕、旁白轨、渲染资产路径 |
| `src/project.tsx` | 读 content-model（`T`/`K`/`A`）+ `editable:*` key + 动效 |

**禁止**在 PPTX 脚本、视频工程、主题包三处各自改同一句文案。

## 元素 ID

```text
editable:sufuda:{page_id}:{role}
```

例：`editable:sufuda:cover:title`、`editable:sufuda:benefit_2:mech_left`。

替换规则见元素上的 `replace`：

- `theme_copy` — 换主题时改审核文案
- `theme_illustration` — 可按病种/场景重绘插画
- `business_authorized` — 真包装 / Logo，业务提供
- `system` — 系统标注，一般不改

## 导出 PPTX

```bash
cd production-library/validation/courseware/sufuda-product-courseware-3-gold-v1
npm run export:pptx
# → out/速福达_商品培训课件3_可编辑课件_v1.pptx
```

- 12 页语义页，原生文字/形状/图片对象
- 可选传入编辑器 snapshot JSON，应用 patches 后再导出
- 不承诺与视频粒子/入场动画像素级等价

## 业务编辑器

```bash
npm run start:editor
# http://127.0.0.1:9010/
```

- 复用风热证 `editable:` 图层插件（点选、改字、换图、位移缩放、撤销）
- 导出当前作品 PPTX 不要求先「另存模板」
- 状态目录：`production-library/validation/revideo-editability/sufuda/`

## 换主题复刻

1. 复制 `theme-packages/_blank/theme.json` 或参考 `demo-product-b`
2. 只填审核文案、旁白句、授权图路径（不要填坐标）
3. 运行：

```bash
python3 scripts/replicate_courseware_theme.py \
  --theme production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/theme-packages/demo-product-b \
  --out-slug demo-product-b-courseware-v1 \
  --skip-tts
```

4. 查看新目录 `gap-report.json`（缺包装/Logo 等）
5. 授权资产齐后去掉 `--skip-tts` 生成克隆旁白，再 `npm run render`

演示主题 `demo-product-b` 仅结构验证，**无真实医学主张**，不得晋升 settled、不得对外培训。

## 与 Word 入口关系

本阶段机器入口为 **theme.json**。通用 Word（`培训课件内容与素材提交_通用模板.docx`）可二期映射为 theme.json；不要求业务理解 layer_id。
