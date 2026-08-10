#!/usr/bin/env python3
"""Build listed-company quality Tier-A business delivery package (offline).

Output:
  outputs/业务使用资料包/药店培训内容工厂-业务包/
  outputs/业务使用资料包/药店培训内容工厂-业务包.zip

Requires previews already materialized:
  python3 scripts/sync_settled_template_previews.py
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

REPO = Path(__file__).resolve().parents[1]
SETTLED = REPO / "production-library/templates/settled"
STATIC_PACKAGE = REPO / "production-library/business-package-static"
OUT_ROOT = REPO / "outputs/业务使用资料包"
PKG_NAME = "药店培训内容工厂-业务包"
PKG = OUT_ROOT / PKG_NAME
RUNTIME_PORTAL_NAME = "index.local.html"
REPRODUCIBLE_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MODE_REQUIRED_FILES = {
    "08_数字人侧讲模式": (
        "README.md",
        "业务复核包-模板.md",
        "代理执行清单.md",
        "口令卡.md",
    ),
    "09_健康科普Seedance模式": (
        "README.md",
        "业务复核包-模板.md",
        "代理执行清单.md",
        "口令卡.md",
    ),
    "10_健康科普九宫格模式": (
        "README.md",
        "业务复核包-模板.md",
        "代理执行清单.md",
        "口令卡.md",
    ),
    "11_健康科普九宫格合规版": (
        "README.md",
        "代理执行清单.md",
        "口令卡.md",
    ),
}
GENERATED_PATH_NAMES = (
    "00_一页怎么用.md",
    "01_模板货架",
    "02_空白Word",
    "03_填写参考",
    "04_WorkBuddy口令卡.md",
    "06_你将收到的初稿长什么样",
    "README.md",
    "index.html",
    RUNTIME_PORTAL_NAME,
    "业务验收清单.md",
    "交付质量说明.md",
    "框架填写说明.md",
    *MODE_REQUIRED_FILES.keys(),
)

sys.path.insert(0, str(REPO / "scripts"))
from business_guided_portal import (  # noqa: E402
    build_guided_portal_html,
    extract_docx_paragraphs,
    load_business_modes,
    write_upload_folder_readme,
)


ONE_PAGE = """# 一页怎么用（内部培训课件 / 视频）

## 安装

```text
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio-private.git，然后指引我使用
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

## 你要交 / 不用交

- **要交**：审核文案；商品视频正式成片还须交业务确认授权的包装图；其他包装/Logo/证据按课型提供。
- **不用交**：箭头、序号圆点、勾叉等小图标——代理按模板匹配。  
- **禁止**：用未授权网图冒充正式包装或证据。
"""

ACCEPTANCE = """# 业务验收清单（你点头后再成片）

把本页当核对表。WorkBuddy 交初稿时，你按项勾选。

## 必过

- [ ] 课型中文名与货架一致  
- [ ] 章节/模块与你 Word 一致；**没有的节没有被硬凑出来**  
- [ ] 联合用药/列表：**条数 = 你写的条数**（例如 2 组只有 2 行，没有空白第三行）  
- [ ] 医学/功效/价格/竞品：要么是你的审核稿，要么明确标「待确认」——没有瞎编  
- [ ] 包装/Logo：初稿可标「待补」；商品视频正式成片必须使用业务确认授权图——**没有假包装**
- [ ] 视频：说明使用的克隆语音包/voice_id；**不是系统机器人音色**  
- [ ] 你已书面确认「可以出成片」之后，才出现终稿 PPTX/MP4  
- [ ] 未要求你自备小图标；排版符号由代理按模板处理  

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
请安装 https://github.com/lmr1123/chain-pharmacy-content-studio-private.git，然后指引我使用
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
> **出片路径：** 业务在 WorkBuddy 对话里说内容 → 代理本机出片。正常 settled 单不经制作代做。

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

按章节写**已审旁白原文**（可删可重排章节），并提供业务确认授权的商品包装图。
无包装图时先交内容/分镜初稿，不生成正式视频；资料齐后代理 full 重渲，不是只换声音。

### 疾病科普视频

按「开场 / 基础认知 / 病因机理 / 典型症状 / 调理建议 / 用药建议 / 总结」提交完整 7 段审核稿。
WorkBuddy 先交脚本/画面复核包；内容缺口与主题画面补齐、业务全量过目并完成当前载荷哈希审批后，才 full 重渲正式片。

### 疾病+商品场景 PPT

辨证、商品、销售场景模块均可按资料完整度裁剪。

## 3. 怎么交给 WorkBuddy

1. **推荐：** 直接在对话写主题 + 要点 +「请生成 ppt/培训视频」（不必先填 Word）  
2. 有 Word/包装图可附件；商品视频无授权包装图或未完成内容/素材哈希审批时，只能先出初稿
3. 口令示例：`我要用【疾病科普视频】，主题是感冒。…请生成培训视频`

## 4. 成片与修改

| 类型 | 你收到 | 要改时 |
|------|--------|--------|
| PPT | 成片路径 + 可改指令 | 「第二页…改成…再出」 |
| 视频 | MP4 + 分镜预览 | 「症状段改成…再出一版」 |

门店发放前请业务自行复核医学表述。
"""

QUALITY_NOTICE = """# 交付质量说明（内部培训 · 上市公司标准）

本业务包仅含**已签样课型**的预览帧、空白 Word 与填写指引。  
**默认：业务在 WorkBuddy 本机自助出片**；制作只处理异常/新页型。

## 硬标准

1. **金样优先**：只套货架内模板，不现场自由发挥版式。  
2. **内容驱动**：有几条出几条；禁止空白行凑满示例条数。  
3. **审核锁定**：医学/药事结论以业务审核稿为准；禁止 AI 编造功效与数据。  
4. **真包装**：无授权包装不得仿造；初稿可标「待补」，商品视频正式成片必须有业务确认授权图及绑定内容/素材哈希的批准记录。
5. **讲解声**：视频默认模板克隆药师声；**禁止**系统机器人音色作正式旁白。  
6. **视频 full 重渲**：商品/疾病科普视频换主题时换文案+屏显+旁白并分段重渲；禁止默认只叠声壳。健康视频另须内容/画面无缺口且审批哈希匹配。
7. **图标与符号**：业务**不需要**自己找图标。场景插画用已签样组件库；业务交**审核文案 + 授权包装/证据**。
8. **发布质检**：正式视频只有在完整生成、审批门闸与结构/媒体完整性 QA 全部通过，状态达到 `qa_passed` 后，才进入 `05_交付物放这里`。

## 状态说明

- **已签样金样**只代表可查看的视觉事实源；是否能在本机正式换主题，以货架能力标识、环境探测和发布门闸共同判定。
- 内容草稿、正式 PPTX、正式 MP4 分开标识；未通过门闸时只交草稿或缺口，不冒充成品。

## 本包不含

工程源码、`node_modules`、编辑器端口、探索稿。  
返修级画面编辑（任意改图层时间线）才是制作路径，不是业务默认。
"""

DELIVERY_FOLDER_README = """# 本机交付目录

WorkBuddy 生成的 PPTX、MP4、运行工作区和日志只保存在业务机器本地，默认不进入 Git。

- 正式交付由生成器在发布闸门通过后写入本目录。
- 不要使用 `git add -f` 提交本目录里的业务产物。
- 重建业务包 zip 时，本目录只收录本说明与空目录标记，不打包本地交付物。
"""

UPLOAD_PRIVACY_NOTICE = """

## 数据与版本库边界

`待处理/`、`已提交/` 中的业务文案、包装、Logo、证据和个人信息只在本机处理，默认不进入 Git，也不会被业务包重建 zip 收录。请勿使用 `git add -f` 强制提交。
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


def shelf_html(
    templates: list[dict],
    examples: dict[str, list[str]],
    runtime_capabilities: dict[str, bool] | None = None,
) -> str:
    """Shelf page reuses the same simplified portal with relative paths fixed."""
    html = build_guided_portal_html(
        templates,
        examples=examples,
        pack_date=date.today().isoformat(),
        runtime_capabilities=runtime_capabilities,
    )
    # JS builds paths as "01_模板货架/media/..." — rewrite for this subfolder.
    html = html.replace("01_模板货架/media/", "media/")
    html = html.replace("02_空白Word/", "../02_空白Word/")
    html = html.replace("03_填写参考/", "../03_填写参考/")
    return html


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def prepare_package_directory() -> None:
    """Refresh generated files without deleting local business payloads."""
    if PKG.is_symlink():
        raise SystemExit(f"refusing to rebuild through package symlink: {PKG}")
    missing_mode_files = [
        f"{mode}/{filename}"
        for mode, filenames in MODE_REQUIRED_FILES.items()
        for filename in filenames
        if not (STATIC_PACKAGE / mode / filename).is_file()
    ]
    if missing_mode_files:
        raise SystemExit(
            "canonical business package source is incomplete: "
            + ", ".join(missing_mode_files)
        )
    PKG.mkdir(parents=True, exist_ok=True)
    for name in GENERATED_PATH_NAMES:
        path = PKG / name
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


def copy_static_modes() -> None:
    for mode, filenames in MODE_REQUIRED_FILES.items():
        for filename in filenames:
            copy_file(STATIC_PACKAGE / mode / filename, PKG / mode / filename)


def copy_portal_mode_media() -> None:
    """Copy reviewed mode examples into the self-contained business portal."""
    destination = PKG / "01_模板货架" / "media" / "production-modes"
    for mode in load_business_modes():
        example = mode.get("portal_video_example") or {}
        source_value = str(example.get("source") or "")
        filename = str(example.get("filename") or "")
        if not source_value and not filename:
            continue
        if not source_value or not filename or Path(filename).name != filename:
            raise SystemExit(f"invalid portal video example for {mode['mode_id']}")
        source = (REPO / source_value).resolve()
        if REPO.resolve() not in source.parents or not source.is_file():
            raise SystemExit(f"missing portal video example for {mode['mode_id']}: {source}")
        copy_file(source, destination / filename)


def include_in_business_zip(path: Path) -> bool:
    """Exclude local uploads and generated deliverables from the distributable zip."""
    relative = path.relative_to(PKG)
    if not relative.parts:
        return False
    if relative.parts == (RUNTIME_PORTAL_NAME,):
        return False
    if relative.parts[0] == "05_交付物放这里":
        return relative.parts in {
            ("05_交付物放这里", ".gitkeep"),
            ("05_交付物放这里", "README.md"),
        }
    if relative.parts[0] == "07_业务填报上传":
        return relative.parts in {
            ("07_业务填报上传", "README.md"),
            ("07_业务填报上传", "待处理", ".gitkeep"),
            ("07_业务填报上传", "已提交", ".gitkeep"),
        }
    return True


def write_business_zip(zip_path: Path) -> None:
    """Write a byte-reproducible archive without source filesystem metadata."""
    members: list[Path] = []
    for path in PKG.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"refusing to archive symlink: {path}")
        if (
            path.is_file()
            and path.name != ".DS_Store"
            and include_in_business_zip(path)
        ):
            members.append(path)

    with ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(
            members, key=lambda item: item.relative_to(PKG).as_posix()
        ):
            archive_name = (
                Path(PKG_NAME) / path.relative_to(PKG)
            ).as_posix()
            info = ZipInfo(archive_name, date_time=REPRODUCIBLE_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            zf.writestr(
                info,
                path.read_bytes(),
                compress_type=ZIP_DEFLATED,
                compresslevel=6,
            )


def write_portal_files(
    catalog: dict,
    templates: list[dict],
    examples: dict[str, list[str]],
    runtime_capabilities: dict[str, bool] | None,
) -> None:
    shelf = PKG / "01_模板货架"
    if not shelf.is_dir():
        raise SystemExit(f"missing template shelf for portal refresh: {shelf}")
    (shelf / "index.html").write_text(
        shelf_html(templates, examples, runtime_capabilities), encoding="utf-8"
    )
    (shelf / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (PKG / "index.html").write_text(
        build_guided_portal_html(
            templates,
            examples=examples,
            pack_date=date.today().isoformat(),
            runtime_capabilities=runtime_capabilities,
        ),
        encoding="utf-8",
    )


def write_runtime_portal(
    templates: list[dict],
    examples: dict[str, list[str]],
    runtime_capabilities: dict[str, bool] | None,
) -> Path:
    """Write machine-specific capability state to an ignored local portal."""
    if not PKG.is_dir():
        raise SystemExit(f"missing business package for portal refresh: {PKG}")
    portal = PKG / RUNTIME_PORTAL_NAME
    portal.write_text(
        build_guided_portal_html(
            templates,
            examples=examples,
            pack_date=date.today().isoformat(),
            runtime_capabilities=runtime_capabilities,
        ),
        encoding="utf-8",
    )
    return portal


def parse_runtime_capabilities(raw: str | None) -> dict[str, bool] | None:
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid --runtime-capabilities-json: {exc}") from exc
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or not isinstance(available, bool)
        for key, available in value.items()
    ):
        raise SystemExit("--runtime-capabilities-json must be an object of booleans")
    return value


def _build_full_package(
    runtime_capabilities: dict[str, bool] | None = None,
) -> dict[str, int | Path]:
    catalog_path = SETTLED / "business-catalog.json"
    if not catalog_path.is_file():
        raise SystemExit("missing business-catalog.json — run sync_settled_template_previews.py first")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    templates = catalog["templates"]

    prepare_package_directory()
    copy_static_modes()

    # Root docs
    (PKG / "00_一页怎么用.md").write_text(ONE_PAGE, encoding="utf-8")
    (PKG / "框架填写说明.md").write_text(FRAMEWORK_GUIDE, encoding="utf-8")
    (PKG / "交付质量说明.md").write_text(QUALITY_NOTICE, encoding="utf-8")
    (PKG / "业务验收清单.md").write_text(ACCEPTANCE, encoding="utf-8")
    (PKG / "04_WorkBuddy口令卡.md").write_text(COMMAND_CARD, encoding="utf-8")
    (PKG / "05_交付物放这里").mkdir(parents=True, exist_ok=True)
    (PKG / "05_交付物放这里" / ".gitkeep").write_text("", encoding="utf-8")
    (PKG / "05_交付物放这里" / "README.md").write_text(
        DELIVERY_FOLDER_README, encoding="utf-8"
    )

    # Upload inbox for business submissions
    upload_root = PKG / "07_业务填报上传"
    (upload_root / "待处理").mkdir(parents=True, exist_ok=True)
    (upload_root / "已提交").mkdir(parents=True, exist_ok=True)
    (upload_root / "待处理" / ".gitkeep").write_text("", encoding="utf-8")
    (upload_root / "已提交" / ".gitkeep").write_text("", encoding="utf-8")
    write_upload_folder_readme(upload_root / "README.md")
    with (upload_root / "README.md").open("a", encoding="utf-8") as handle:
        handle.write(UPLOAD_PRIVACY_NOTICE)

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
    copy_portal_mode_media()

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

        video_example = t.get("portal_video_example") or {}
        video_filename = str(video_example.get("filename") or "").strip()
        video_source = str(video_example.get("source") or "").strip()
        if video_filename or video_source:
            if (
                not video_filename
                or Path(video_filename).name != video_filename
                or not video_source
                or Path(video_source).is_absolute()
            ):
                raise SystemExit(f"invalid portal_video_example for {slug}")
            source = (REPO / video_source).resolve()
            if REPO.resolve() not in source.parents or not source.is_file():
                raise SystemExit(
                    f"missing portal gold video for {slug}: {video_source}"
                )
            copy_file(source, dest_media / video_filename)

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

    # Tracked portals are machine-neutral. Runtime state only belongs in ignored local HTML.
    write_portal_files(catalog, templates, examples, None)
    if runtime_capabilities is not None:
        write_runtime_portal(templates, examples, runtime_capabilities)

    # README for whole package — keep short; UI is index.html
    (PKG / "README.md").write_text(
        "# 内部培训 · 业务引导包\n\n"
        "## 使用方法\n\n"
        "1. WorkBuddy 输入：\n\n"
        "```text\n"
        "请安装 https://github.com/lmr1123/chain-pharmacy-content-studio-private.git，然后指引我使用\n"
        "```\n\n"
        "2. 打开 `index.html`：**看模板**（一行四个小卡片 + 关键页预览）  \n"
        "3. WorkBuddy **输入培训内容** → **下载 PPT 修改，或输入指令批量修改**  \n\n"
        "示例口令见 `04_WorkBuddy口令卡.md`。\n\n"
        "| 业务会点开的 | 说明 |\n"
        "|--------------|------|\n"
        "| **`index.html`** | 仅两块：模板预览选择 · **内容示例直接展示** |\n"
        "| `03_填写参考/` | 源 docx（页面已内嵌正文，无需下载） |\n"
        "| `02_空白Word/` | 代理侧可选 |\n\n"
        "## 素材边界（业务）\n\n"
        "- **要交的**：审核文案、授权包装/Logo/证据（如有）；商品视频成片前还要确认绑定内容和包装图哈希的审批记录。<br>\n"
        "- **不用交的**：箭头/序号/分行点等排版小图标、通用物件符号——由代理按模板与按需源头匹配。  \n"
        "- **禁止**：用未授权网图冒充正式包装或证据。\n\n"
        f"生成日期：{date.today().isoformat()}\n",
        encoding="utf-8",
    )

    # Zip
    zip_path = PKG.parent / f"{PKG.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    write_business_zip(zip_path)

    # Size summary
    total = sum(p.stat().st_size for p in PKG.rglob("*") if p.is_file())
    return {
        "zip_path": zip_path,
        "zip_bytes": zip_path.stat().st_size,
        "file_count": sum(1 for path in PKG.rglob("*") if path.is_file()),
        "unpacked_bytes": total,
        "template_count": len(templates),
    }


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _refresh_preserved_readmes(package: Path) -> None:
    delivery = package / "05_交付物放这里"
    delivery.mkdir(parents=True, exist_ok=True)
    (delivery / ".gitkeep").write_text("", encoding="utf-8")
    (delivery / "README.md").write_text(DELIVERY_FOLDER_README, encoding="utf-8")

    upload = package / "07_业务填报上传"
    (upload / "待处理").mkdir(parents=True, exist_ok=True)
    (upload / "已提交").mkdir(parents=True, exist_ok=True)
    (upload / "待处理" / ".gitkeep").write_text("", encoding="utf-8")
    (upload / "已提交" / ".gitkeep").write_text("", encoding="utf-8")
    write_upload_folder_readme(upload / "README.md")
    with (upload / "README.md").open("a", encoding="utf-8") as handle:
        handle.write(UPLOAD_PRIVACY_NOTICE)


def _commit_package(
    staging: Path,
    staging_zip: Path,
    final_package: Path,
    final_zip: Path,
) -> None:
    nonce = uuid4().hex
    package_backup = final_package.parent / f".{final_package.name}.backup-{nonce}"
    zip_backup = final_zip.parent / f".{final_zip.name}.backup-{nonce}"
    preserved = ("05_交付物放这里", "07_业务填报上传")
    had_package = final_package.exists()
    had_zip = final_zip.exists()
    try:
        if had_package:
            os.replace(final_package, package_backup)
            for name in preserved:
                old_local = package_backup / name
                if old_local.exists():
                    _remove_path(staging / name)
                    os.replace(old_local, staging / name)
        _refresh_preserved_readmes(staging)
        if had_zip:
            os.replace(final_zip, zip_backup)
        os.replace(staging, final_package)
        os.replace(staging_zip, final_zip)
    except Exception:
        local_source_root = final_package if final_package.exists() else staging
        if had_package and package_backup.exists():
            for name in preserved:
                source = local_source_root / name
                target = package_backup / name
                if source.exists() and not target.exists():
                    os.replace(source, target)
        if final_package.exists():
            _remove_path(final_package)
        if package_backup.exists():
            os.replace(package_backup, final_package)
        if final_zip.exists():
            _remove_path(final_zip)
        if zip_backup.exists():
            os.replace(zip_backup, final_zip)
        raise
    if package_backup.exists():
        _remove_path(package_backup)
    if zip_backup.exists():
        _remove_path(zip_backup)


def main(
    runtime_capabilities: dict[str, bool] | None = None,
    *,
    portal_only: bool = False,
) -> None:
    global PKG
    if portal_only:
        catalog_path = SETTLED / "business-catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        templates = catalog["templates"]
        examples = load_fill_examples(templates)
        copy_portal_mode_media()
        portal = write_runtime_portal(templates, examples, runtime_capabilities)
        print(f"Local portal refreshed: {portal}")
        return

    final_package = PKG
    final_zip = OUT_ROOT / f"{PKG_NAME}.zip"
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    staging = OUT_ROOT / f".{PKG_NAME}.staging-{uuid4().hex}"
    PKG = staging
    try:
        report = _build_full_package(runtime_capabilities)
        staging_zip = Path(report["zip_path"])
        PKG = final_package
        _commit_package(staging, staging_zip, final_package, final_zip)
    except Exception:
        PKG = final_package
        if staging.exists() or staging.is_symlink():
            _remove_path(staging)
        candidate_zip = staging.parent / f"{staging.name}.zip"
        candidate_zip.unlink(missing_ok=True)
        raise

    print(f"Package: {final_package}")
    print(f"Zip:     {final_zip} ({final_zip.stat().st_size / 1e6:.1f} MB)")
    print(
        f"Files:   {report['file_count']} "
        f"({int(report['unpacked_bytes']) / 1e6:.1f} MB unpacked)"
    )
    print(f"Templates: {report['template_count']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-capabilities-json",
        help="JSON object returned by probe_production_env.py capabilities",
    )
    parser.add_argument(
        "--portal-only",
        action="store_true",
        help="Write ignored index.local.html without rebuilding templates or the zip",
    )
    arguments = parser.parse_args()
    main(
        parse_runtime_capabilities(arguments.runtime_capabilities_json),
        portal_only=arguments.portal_only,
    )
