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
# → out/速福达玛巴洛沙韦_商品培训课件3_金样_可编辑课件_v1.pptx
# 金样归档：templates/settled/sufuda-mabaloshawei-product-courseware-3-v1/
```

- **13 页**语义页（适宜人群拆成「≥5 岁门槛」+「三类人群」两页，对齐参考视频），原生文字/形状/图片
- **字体**：`HarmonyOS Sans SC`（与视频一致；本机需安装该字体，否则 PowerPoint 会回退）
- **字号/排版**：视频 1920×1080 设计坐标按比例缩到 16:9 画布，字号同比例缩放
- **图片比例**：按资源原始宽高比装箱（不 stretch），避免人物/包装被压扁拉长
- **正式终稿口径**：导出文案不得含「示例 / 模板示例 / 占位」等演示标注
- **后续拓展**：改 `content-model.json` → `npm run export:pptx`；或在 PPTX 内直接改字换图
- 不承诺与视频粒子/入场动画像素级等价

### 产品特点页包装图（业务必换槽）

| 场景 | element_id | 说明 |
|------|------------|------|
| 产品特点·安全性 中间圆 | `editable:sufuda:feature_1:pack` | 中心包装组，可点选换图 |
| 产品特点·双剂型 中间圆 | `editable:sufuda:feature_2:pack` | 中心包装组 |
| 双剂型左/右剂型图 | `…:tablets` / `…:granule` | 片剂特写 / 干混悬剂 |
| 联合用药左侧包装 | `editable:sufuda:combo_1:pack` 等 | 与 `slot.pack.group` 同源 |

视频编辑器与 PPTX 导出共用上述 ID；换公司授权包装时优先改 `content-model.assets.packGroup`（及 tablets/granule），或编辑器内逐层换图。

## 业务编辑器（视频时间轴 + 图层）

```bash
cd production-library/validation/courseware/sufuda-product-courseware-3-gold-v1
npm run start:editor
# 浏览器打开：http://127.0.0.1:9010/
```

- 这是 **Revideo 视频工程编辑器**（全片时间轴预览），不是静态 PPT 页
- 复用风热证 `editable:` 图层插件（点选、改字、换图、位移缩放、撤销）
- 右侧「画面属性」：导出视频 MP4 / 可编辑 PPTX（不要求先另存模板）
- 状态目录：`production-library/validation/revideo-editability/sufuda/`
- 若页面空白：确认终端无 `outside of Vite serving allow list`；启动脚本已允许 `poc/gold-sample/node_modules` 与本金样目录

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
