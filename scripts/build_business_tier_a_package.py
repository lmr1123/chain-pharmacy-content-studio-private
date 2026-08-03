#!/usr/bin/env python3
"""Build listed-company quality Tier-A business delivery package (offline).

Output:
  outputs/业务使用资料包/药店培训内容工厂-业务包/
  outputs/业务使用资料包/药店培训内容工厂-业务包.zip

Requires previews already materialized:
  python3 scripts/sync_settled_template_previews.py
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[1]
SETTLED = REPO / "production-library/templates/settled"
OUT_ROOT = REPO / "outputs/业务使用资料包"
PKG_NAME = "药店培训内容工厂-业务包"
PKG = OUT_ROOT / PKG_NAME

sys.path.insert(0, str(REPO / "scripts"))
from business_guided_portal import (  # noqa: E402
    build_guided_portal_html,
    extract_docx_paragraphs,
    write_upload_folder_readme,
)


ONE_PAGE = """# 一页怎么用（内部培训课件 / 视频）

## 安装

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

## 三步

### 1. 看模板

打开引导页（一行四个小卡片）→ 点看关键页预览 → 选用模板。

### 2. 输入培训内容

在 WorkBuddy 直接说主题和要点，例如：

```text
整理可可康灵芝胶囊商品，主要是围绕宁心安神助睡眠、提升免疫力、保肝护肝抗衰老3个方面来完善，你先整理符合内容再生成ppt
```

### 3. 下载与修改

可下载 PPT 修改，或输入指令批量修改，例如：

```text
第二页卖点改成…
批量把联合用药改成 2 条
```

---

网页：模板预览选择 + 对应内容示例（页面内直接展示）。
"""

ACCEPTANCE = """# 业务验收清单（你点头后再成片）

把本页当核对表。WorkBuddy 交初稿时，你按项勾选。

## 必过

- [ ] 课型中文名与货架一致  
- [ ] 章节/模块与你 Word 一致；**没有的节没有被硬凑出来**  
- [ ] 联合用药/列表：**条数 = 你写的条数**（例如 2 组只有 2 行，没有空白第三行）  
- [ ] 医学/功效/价格/竞品：要么是你的审核稿，要么明确标「待确认」——没有瞎编  
- [ ] 包装/Logo：有授权图或「待补」槽位——**没有假包装**  
- [ ] 视频：说明使用的克隆语音包/voice_id；**不是系统机器人音色**  
- [ ] 你已书面确认「可以出成片」之后，才出现终稿 PPTX/MP4  

## 可选

- [ ] 分镜/初稿里的屏显短句你已过目  
- [ ] 缺口清单里的图你已安排补传或接受槽位上线  

## 不通过时怎么回

直接回复 WorkBuddy，例如：

- 「联合用药我只交了 2 组，请删掉第三空行后重出初稿」  
- 「第 2 节功效改成附件审核稿原文，再出」  
- 「包装下周才有，先槽位出初稿，成片等我补图」  
"""

COMMAND_CARD = """# WorkBuddy 口令（复制即用）

## 安装

```
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用
```

## 第 2 步 · 输入培训内容

```
整理可可康灵芝胶囊商品，主要是围绕宁心安神助睡眠、提升免疫力、保肝护肝抗衰老3个方面来完善，你先整理符合内容再生成ppt
```

## 第 3 步 · 下载与修改

```
第二页卖点改成……
批量把联合用药改成 2 条
```
"""

FRAMEWORK_GUIDE = """# 框架填写说明（全课型通用）

> 权威总案：仓库内 `docs/business-workbuddy-foolproof-delivery.md`  
> 本页是业务填写的**硬规则**，WorkBuddy 与制作必须遵守。

## 1. 框架 ≠ 必须填满

| 原则 | 含义 |
|------|------|
| 模块可删 | 不需要的整节标题+内容直接删掉 |
| 有几条写几条 | 联合用药/卖点/人群等列表按真实条数 |
| 禁止空行凑满 | 金样示例若是 3 行，业务只交 2 条 → 成品只出 2 行 |
| 未提供不编造 | 价格/功效/竞品无审核稿 → 标「待确认」或缺口，不写假数据 |
| 无授权图不仿装 | 包装/Logo 无授权原图 → 槽位「待补」，禁止 AI 仿品牌包装 |

## 2. 常见模块（按课型选用）

### 商品 PPT（绿色单品 / 课件3 / 课件4 共性）

| 模块 | 填什么 | 不填时 |
|------|--------|--------|
| 商品介绍 | 名称、定位、规格等 | 弱化或「待确认」 |
| 核心卖点 | 1～N 条 | 有几条出几条 |
| 适宜人群 | 1～N 类 | 同上 |
| 联合用药话术 | 1～N 组 | **2 组 → 2 行，禁止第 3 空行** |
| 品种对比 | 可选 | 无则整节省略 |
| 注意事项 | 可选 | 无则省略或最短合规句（须审） |

### 商品培训视频

按章节写**已审旁白原文**（可删可重排章节）。  
屏显短句可不写，由工厂从旁白摘出供你确认。

### 疾病科普视频

按「症状 / 机理 / 治疗 / 用药建议 / 总结」等章节写审核稿；  
无章节整段删。新病种量产前请与制作确认模板状态。

### 疾病+商品场景 PPT

辨证、商品、销售场景模块均可按资料完整度裁剪。

## 3. 提交物清单

1. 对应课型的**空白 Word 已填版**（一份主题一份）  
2. **授权**包装图 / Logo（有则附）  
3. WorkBuddy 口令（课型中文名 + 主题名 + 「先初稿后成片」）

## 4. 确认后再成片

| 类型 | 确认物 |
|------|--------|
| PPT | 内容初稿 + 待确认项 + 缺口 |
| 视频 | 分镜预览 + 缺口（+ 可选试听） |

未确认前不向门店发放终稿。
"""

QUALITY_NOTICE = """# 交付质量说明（内部培训 · 上市公司标准）

本业务包仅含**已签样课型**的预览帧、空白 Word 与填写指引。

## 硬标准

1. **金样优先**：只套货架内模板，不现场自由发挥版式。  
2. **内容驱动**：有几条出几条；禁止空白行凑满示例条数。  
3. **审核锁定**：医学/药事结论以业务审核稿为准；禁止 AI 编造功效与数据。  
4. **真包装**：无授权包装不得仿造；成片用「待补」槽位。  
5. **讲解声**：视频默认模板克隆药师声；**禁止**系统机器人音色作正式旁白。  
6. **先确认后成片**：PPT 先初稿；视频先分镜预览。

## 状态说明

货架卡片上的状态文案来自 `manifest`：

- **已签样 · 可换主题量产** / **已签样金样 · 可参考换主题**：提供审核内容 + 授权素材后可正式交付（视频类另需克隆语音环境）  
- 货架不再使用「仅金样对照 / visual-rework」冻结态；风热 / Q10 视频金样包已齐
## 本包不含

工程源码、`node_modules`、编辑器端口、探索稿、QA 接触表。  
返修级画面编辑仅制作侧使用，不是业务默认路径。
"""


def load_fill_examples(templates: list[dict]) -> dict[str, list[str]]:
    """Extract inline example text from each settled 填写参考 docx."""
    examples: dict[str, list[str]] = {}
    for t in templates:
        slug = t["slug"]
        path = SETTLED / slug / "业务提交_填写参考.docx"
        paras = extract_docx_paragraphs(path)
        if not paras:
            raise SystemExit(f"missing or empty fill example for {slug}: {path}")
        examples[slug] = paras
    return examples


def shelf_html(templates: list[dict], examples: dict[str, list[str]]) -> str:
    """Shelf page reuses the same simplified portal with relative paths fixed."""
    html = build_guided_portal_html(
        templates, examples=examples, pack_date=date.today().isoformat()
    )
    # JS builds paths as "01_模板货架/media/..." — rewrite for this subfolder.
    html = html.replace("01_模板货架/media/", "media/")
    html = html.replace("02_空白Word/", "../02_空白Word/")
    html = html.replace("03_填写参考/", "../03_填写参考/")
    return html


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main() -> None:
    catalog_path = SETTLED / "business-catalog.json"
    if not catalog_path.is_file():
        raise SystemExit("missing business-catalog.json — run sync_settled_template_previews.py first")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    templates = catalog["templates"]

    if PKG.exists():
        shutil.rmtree(PKG)
    PKG.mkdir(parents=True)

    # Root docs
    (PKG / "00_一页怎么用.md").write_text(ONE_PAGE, encoding="utf-8")
    (PKG / "框架填写说明.md").write_text(FRAMEWORK_GUIDE, encoding="utf-8")
    (PKG / "交付质量说明.md").write_text(QUALITY_NOTICE, encoding="utf-8")
    (PKG / "业务验收清单.md").write_text(ACCEPTANCE, encoding="utf-8")
    (PKG / "04_WorkBuddy口令卡.md").write_text(COMMAND_CARD, encoding="utf-8")
    (PKG / "05_交付物放这里").mkdir()
    (PKG / "05_交付物放这里" / ".gitkeep").write_text("", encoding="utf-8")

    # Upload inbox for business submissions
    upload_root = PKG / "07_业务填报上传"
    (upload_root / "待处理").mkdir(parents=True)
    (upload_root / "已提交").mkdir(parents=True)
    (upload_root / "待处理" / ".gitkeep").write_text("", encoding="utf-8")
    (upload_root / "已提交" / ".gitkeep").write_text("", encoding="utf-8")
    write_upload_folder_readme(upload_root / "README.md")

    # What business will receive before final film
    delivery_examples = REPO / "production-library/templates/business-delivery"
    examples_dest = PKG / "06_你将收到的初稿长什么样"
    examples_dest.mkdir()
    for name in (
        "内容初稿模板.md",
        "缺口清单模板.md",
        "分镜预览模板.md",
    ):
        src = delivery_examples / name
        if src.is_file():
            copy_file(src, examples_dest / name)
    ex_dir = delivery_examples / "examples"
    if ex_dir.is_dir():
        for src in ex_dir.glob("*.md"):
            copy_file(src, examples_dest / "示例" / src.name)
    (examples_dest / "说明.md").write_text(
        "# 你将收到的初稿长什么样\n\n"
        "WorkBuddy **不会**一上来丢终稿 PPTX/MP4。\n\n"
        "| 文件 | 何时 |\n"
        "|------|------|\n"
        "| 内容初稿 | 所有 PPT/课件 |\n"
        "| 缺口清单 | 每次 |\n"
        "| 分镜预览 | 视频类 |\n\n"
        "`示例/` 里是结构示范（含「联合用药只 2 行」），不是真实医学终稿。\n"
        "你确认后，成片进 `05_交付物放这里/`。\n",
        encoding="utf-8",
    )

    shelf = PKG / "01_模板货架"
    words = PKG / "02_空白Word"
    refs = PKG / "03_填写参考"
    shelf.mkdir()
    words.mkdir()
    refs.mkdir()

    for t in templates:
        slug = t["slug"]
        src_preview = SETTLED / slug / "preview"
        if not (src_preview / "cover.png").is_file():
            raise SystemExit(f"missing preview for {slug}")
        dest_media = shelf / "media" / slug
        dest_media.mkdir(parents=True)
        copy_file(src_preview / "cover.png", dest_media / "cover.png")
        labels = t.get("key_frame_labels_zh") or []
        for i in range(1, len(labels) + 1):
            kp = src_preview / f"key-{i:02d}.png"
            if not kp.is_file():
                raise SystemExit(f"missing {kp}")
            copy_file(kp, dest_media / f"key-{i:02d}.png")

        blank = SETTLED / slug / "业务提交_空白模板.docx"
        filled = SETTLED / slug / "业务提交_填写参考.docx"
        if not blank.is_file() or not filled.is_file():
            raise SystemExit(f"missing Word for {slug}")
        copy_file(blank, words / slug / "业务提交_空白模板.docx")
        copy_file(filled, refs / slug / "业务提交_填写参考.docx")

        guide = SETTLED / slug / "本课型怎么填.md"
        if guide.is_file():
            copy_file(guide, words / slug / "本课型怎么填.md")
            copy_file(guide, refs / slug / "本课型怎么填.md")

        # Per-template short readme next to Word
        (words / slug / "README.txt").write_text(
            f"课型：{t['name_zh']}\n"
            f"说明：{t.get('one_liner', '')}\n"
            f"状态：{t.get('status_label', '')}\n"
            f"先读：本课型怎么填.md\n"
            f"规则：没有的章节整段删除；列表有几条写几条；不要空行凑满。\n"
            f"提交后请使用口令卡交给 WorkBuddy，先出初稿再成片。\n",
            encoding="utf-8",
        )

    examples = load_fill_examples(templates)

    (shelf / "index.html").write_text(shelf_html(templates, examples), encoding="utf-8")
    (shelf / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Guided entry (primary): templates + inline fill examples
    (PKG / "index.html").write_text(
        build_guided_portal_html(
            templates, examples=examples, pack_date=date.today().isoformat()
        ),
        encoding="utf-8",
    )

    # README for whole package — keep short; UI is index.html
    (PKG / "README.md").write_text(
        "# 内部培训 · 业务引导包\n\n"
        "## 使用方法\n\n"
        "1. WorkBuddy 输入：\n\n"
        "```text\n"
        "请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用\n"
        "```\n\n"
        "2. 打开 `index.html`：**看模板**（一行四个小卡片 + 关键页预览）  \n"
        "3. WorkBuddy **输入培训内容** → **下载 PPT 修改，或输入指令批量修改**  \n\n"
        "示例口令见 `04_WorkBuddy口令卡.md`。\n\n"
        "| 业务会点开的 | 说明 |\n"
        "|--------------|------|\n"
        "| **`index.html`** | 仅两块：模板预览选择 · **内容示例直接展示** |\n"
        "| `03_填写参考/` | 源 docx（页面已内嵌正文，无需下载） |\n"
        "| `02_空白Word/` | 代理侧可选 |\n\n"
        f"生成日期：{date.today().isoformat()}\n",
        encoding="utf-8",
    )

    # Zip
    zip_path = OUT_ROOT / f"{PKG_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(PKG.rglob("*")):
            if path.is_file() and path.name != ".DS_Store":
                zf.write(path, path.relative_to(OUT_ROOT))

    # Size summary
    total = sum(p.stat().st_size for p in PKG.rglob("*") if p.is_file())
    print(f"Package: {PKG}")
    print(f"Zip:     {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")
    print(f"Files:   {sum(1 for _ in PKG.rglob('*') if _.is_file())} ({total / 1e6:.1f} MB unpacked)")
    print(f"Templates: {len(templates)}")


if __name__ == "__main__":
    main()
