# 参课 · 急性上呼吸道感染 · 可编辑金样 v2（交付级）

## 本版相对 v1 的升级（按业务要求）

| # | 要求 | 做法 |
|---|------|------|
| 1 | 图片重新绘制生成 | `assets/` 下医学图/卡通为**重绘**，不再用视频截图裁切 |
| 2 | 字体、字号、排版重调 | 统一字阶（封面 42 / 章节 28 / 正文 16 / 表 14 / 注意事项 13），留白与画框统一 |
| 3 | 商品图命名坑位 | `assets/placeholders/pack-*.png`，品名标注，业务换授权原图即可 |
| 4 | 上市公司可交付质量 | 可编辑形状/文字/表格 + 版式锁定参课 chrome + 不伪造品牌包装 |

版式仍对齐**参课截图中的 PPT**（蓝方章号、Logo、角标、虚线正文框、深蓝表头），**不另起一套 UI**。

---

## 主交付

| 文件 | 作用 |
|------|------|
| `急性上呼吸道感染_疾病健康知识培训_可编辑金样_v2.pptx` | **主交付** |
| `content/急性上呼吸道感染.content.json` | 内容模型（换病改这个） |
| `build-editable.mjs` | JSON → PPTX |
| `assets/*` | 重绘插图 |
| `assets/placeholders/pack-*.png` | 商品包装命名坑位 |

对照用（非主交付）：

- `../disease-uri-acute-upper-respiratory-v1/` — A 级整页截图对照
- `assets/_legacy-crops/` — v1 截图裁切备份

---

## 视觉锁定点（与截图一致）

- 章节头：**蓝方章号**（直角）+ 章节名 + 右上角 **参课 SHENKE Logo**
- 底色：浅冷蓝白 `#F4F7FC`
- 治疗页：左上角角标 + 中部插图画框 + 底部虚线角框正文
- 对症表：深蓝表头双列表 + 右侧 **4 个命名包装坑位**
- 注意事项：风险项红字（内容 JSON `risk: true`）
- 封面 / 结束页：品牌蓝构图；**不放真人**

---

## 业务如何替换商品图

1. 准备授权包装原图（透明底或白底均可）
2. 覆盖同名文件，例如：

```text
assets/placeholders/pack-复方氨酚烷胺胶囊.png
assets/placeholders/pack-冬凌草糖浆.png
assets/placeholders/pack-磷酸奥司他韦颗粒.png
assets/placeholders/pack-阿莫西林胶囊.png
assets/placeholders/pack-summary-group.png   # 总结页
```

3. 重新生成：

```bash
node build-editable.mjs
```

也可直接在 PowerPoint 里右键图片 → 更改图片。

**禁止**：AI 伪造真实品牌包装外观；未授权包装不得升格 settled。

---

## 换下一个病

```bash
cp content/急性上呼吸道感染.content.json content/过敏性鼻炎.content.json
# 改 meta / definition / clinical / tables / care / packshot_slots
# 不要改 scene_type 与页布局

node build-editable.mjs content/过敏性鼻炎.content.json
```

---

## 页序（18）

| # | 页 | scene_type |
|---|----|------------|
| 1 | 封面 | `cover_branded` |
| 2 | 目录 | `agenda` |
| 3 | 01 疾病概览 | `definition_etiology` |
| 4 | 02 临床表现 | `clinical_blocks` |
| 5 | 03 检查方法 | `exam_two_column` |
| 6–8 | 04 一般 / 全身 / 局部 | `treatment_illustration` |
| 9 | 04 对症选药 + 包装坑位 | `two_col_table` |
| 10–14 | 04 注意事项 | `drug_precautions_*` |
| 15–16 | 05 专业关怀 | `care_*` |
| 17 | 结束页 | `outro` |
| 18 | 一页总结 | `one_page_summary` |

---

## 验收清单

- [x] 正文可编辑（文本/表格/形状）
- [x] 插图为重绘（非视频整页截图）
- [x] 字阶与排版统一
- [x] 商品为命名坑位，可替换
- [ ] 业务确认医学表述与对症表
- [ ] 包装图换授权原图
- [ ] 升格 settled + 业务 Word 同步

---

## 说明

- 视频讲解人不是 PPT 图层，金样不包含真人。
- 插图风格：医学教育淡彩 / 扁平卡通，与参课原课件一致。
- 字体声明：`Microsoft YaHei`（Windows 办公环境标准）；Mac 打开可能回退到系统黑体。
