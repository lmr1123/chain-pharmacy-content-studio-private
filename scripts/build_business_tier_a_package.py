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
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[1]
SETTLED = REPO / "production-library/templates/settled"
OUT_ROOT = REPO / "outputs/业务使用资料包"
PKG_NAME = "药店培训内容工厂-业务包"
PKG = OUT_ROOT / PKG_NAME


ONE_PAGE = """# 一页怎么用（业务）

> 给一线业务：选模板 → 填 Word → 交给 WorkBuddy → 审初稿 → 拿成片。  
> **不需要**装 Node、起端口、懂图层编辑器。

## 四步

1. **看效果**  
   打开本包里的 `01_模板货架/index.html`（双击即可，可离线）。  
   看每个模板的封面和关键页截图，确认观感。

2. **选模板**  
   记住中文课型名（货架卡片上的大标题）。  
   点「就用这个模板」可跳到对应空白 Word 说明。

3. **填框架**  
   复制 `02_空白Word/` 里对应课型的「空白模板.docx」。  
   - 按章节填**公司已审核**的文案与数据  
   - **没有的章节整段删掉**  
   - 列表/联合用药：**有几条写几条**，不要为对齐示例硬凑空行  
   - 授权包装图、Logo 随 Word 一起提交（无图会列入缺口，**不会**用假包装）

4. **交给 WorkBuddy**  
   发 Word + 授权图，复制口令（见 `04_WorkBuddy口令卡.md`）：

   > 我要用 **【课型中文名】**，主题是 **【病名或商品名】**。  
   > Word 和授权图在附件。  
   > 请先出 **初稿/分镜预览 + 待确认项 + 缺图清单**；  
   > 我确认后再出 **可编辑 PPTX / 培训视频**。

## 你不需要做的事

- 指定字号、坐标、页数、动画参数  
- 打开任何「编辑器端口」  
- 用系统朗读当正式旁白（视频旁白由工厂用**模板绑定的药师克隆声**生成）  
- 编造功效、价格、竞品结论

## 填写参考怎么用

`03_填写参考/` 里的文档**只示范格式与模块结构**，  
医学表述、包装、品牌以**贵司审核稿与授权素材**为准，不要直接当新项目终稿。

## 成片放哪里

确认后的 PPTX / MP4 请放在 `05_交付物放这里/`，或按项目单独建文件夹归档。

## 你先会收到什么（不是直接成片）

见 `06_你将收到的初稿长什么样/`：  
内容初稿示例、缺口清单示例、视频分镜预览示例。  
**只有你确认后**，WorkBuddy 才出可编辑 PPTX / 培训视频。

## 推荐起步（第一次用）

1. 货架选 **「绿色单品 PPT」** 或 **「商品培训视频」**（状态为「已签样 · 可换主题量产」）  
2. 打开 `02_空白Word/…/本课型怎么填.md` 看推荐板块  
3. 填空白 Word → 口令卡交给 WorkBuddy  
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

COMMAND_CARD = """# WorkBuddy 口令卡（业务复制）

## 通用（每次必带）

```
我要用 【课型中文名】，主题是 【病名或商品名】。
Word 和授权图在附件。
请先出 初稿/分镜预览 + 待确认项 + 缺图清单；
我确认后再出 可编辑 PPTX / 培训视频。
示例 Word 只作格式参考，医学与包装以我司审核稿为准。
```

课型中文名请与货架卡片标题一致，例如：

- 疾病科普视频（如风热证）
- 商品培训视频（如辅酶 Q10）
- 绿色单品 PPT（如金银花露）
- 疾病+商品场景 PPT（如穿心莲）
- 商品培训课件3（视频+PPT，速福达壳）
- 商品培训课件4（视频+PPT，番茄红素壳）

## PPT / 课件补充

```
联合用药我只写了 N 组，请按 N 行排版，不要空行凑满。
没有的章节整节可删。
若需要「总结总表」等扩展页，请按同风格总结页补页并标明扩展。
```

## 视频补充

```
旁白以 Word 审核稿为准，请用该模板的药师克隆声朗读。
禁止使用系统机器人朗读音色。
包装用附件图；没有的章节先占位并列入缺口清单。
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

- **已签样 · 可换主题量产**：提供审核内容 + 授权素材后可正式交付  
- **金样对照 · 新主题制作前请与制作确认**：可看效果与填框架，量产前须制作确认

## 本包不含

工程源码、`node_modules`、编辑器端口、探索稿、QA 接触表。  
返修级画面编辑仅制作侧使用，不是业务默认路径。
"""


def shelf_html(templates: list[dict]) -> str:
    cards = []
    for t in templates:
        slug = t["slug"]
        ready = t.get("production_ready", False)
        badge_class = "ok" if ready else "warn"
        keys = t.get("key_frame_labels_zh") or []
        key_imgs = []
        for i, lab in enumerate(keys, 1):
            key_imgs.append(
                f'<figure><img src="media/{slug}/key-{i:02d}.png" alt="{lab}" loading="lazy" />'
                f"<figcaption>{lab}</figcaption></figure>"
            )
        outputs = " · ".join(t.get("outputs") or [])
        cards.append(
            f"""
      <article class="card" id="{slug}">
        <a class="cover" href="#detail-{slug}">
          <img src="media/{slug}/cover.png" alt="{t['name_zh']}" />
        </a>
        <div class="body">
          <div class="meta-row">
            <span class="cat">{t.get('category', '')}</span>
            <span class="badge {badge_class}">{t.get('status_label', '')}</span>
          </div>
          <h2>{t['name_zh']}</h2>
          <p class="one">{t.get('one_liner', '')}</p>
          <p class="out">产物：{outputs}</p>
          <div class="actions">
            <a class="btn primary" href="#detail-{slug}">查看关键页</a>
            <a class="btn" href="../02_空白Word/{slug}/业务提交_空白模板.docx">下载空白 Word</a>
            <a class="btn ghost" href="../03_填写参考/{slug}/业务提交_填写参考.docx">格式参考</a>
          </div>
        </div>
      </article>
      <section class="detail" id="detail-{slug}">
        <div class="detail-head">
          <h3>{t['name_zh']}</h3>
          <a class="back" href="#top">↑ 返回货架</a>
        </div>
        <p class="note">{t.get('status_note', '')}</p>
        <p class="path">空白 Word：<code>02_空白Word/{slug}/业务提交_空白模板.docx</code></p>
        <div class="keys">{"".join(key_imgs)}</div>
        <div class="actions sticky">
          <a class="btn primary" href="../02_空白Word/{slug}/业务提交_空白模板.docx">就用这个模板 · 下载空白 Word</a>
          <a class="btn" href="../04_WorkBuddy口令卡.md">复制口令卡</a>
        </div>
      </section>
"""
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>药店培训内容工厂 · 模板货架</title>
<style>
  :root {{
    --bg: #0f1419;
    --panel: #171d25;
    --line: rgba(255,255,255,.10);
    --text: #eef2f6;
    --dim: #9aa7b5;
    --accent: #2f6fed;
    --accent2: #1f9d6a;
    --warn: #c9851a;
    --radius: 16px;
    --font: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, sans-serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: var(--font);
    background: radial-gradient(1200px 600px at 10% -10%, #1a2740 0%, transparent 55%),
                radial-gradient(900px 500px at 100% 0%, #152a22 0%, transparent 50%),
                var(--bg);
    color: var(--text);
    line-height: 1.55;
    min-height: 100vh;
  }}
  .shell {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 80px; }}
  header.hero {{
    padding: 28px 28px 24px;
    border: 1px solid var(--line);
    border-radius: 20px;
    background: linear-gradient(145deg, rgba(47,111,237,.14), rgba(255,255,255,.03));
    margin-bottom: 28px;
  }}
  .badge-top {{
    display: inline-block;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .08em;
    color: #9ec0ff;
    margin-bottom: 10px;
  }}
  h1 {{ font-size: 28px; font-weight: 900; letter-spacing: -.02em; margin-bottom: 10px; }}
  .sub {{ color: var(--dim); font-size: 14px; max-width: 62ch; }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
  .chip {{
    font-size: 12px; font-weight: 700;
    padding: 5px 10px; border-radius: 999px;
    background: rgba(255,255,255,.06); border: 1px solid var(--line); color: var(--dim);
  }}
  .steps {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 22px 0 28px;
  }}
  @media (max-width: 800px) {{ .steps {{ grid-template-columns: 1fr 1fr; }} }}
  .step {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px;
  }}
  .step b {{ display: block; font-size: 13px; margin-bottom: 4px; }}
  .step span {{ font-size: 12px; color: var(--dim); }}
  .n {{
    width: 22px; height: 22px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    background: var(--accent); color: #fff; font-size: 12px; font-weight: 800;
    margin-bottom: 8px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 18px;
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: border-color .15s, transform .15s;
  }}
  .card:hover {{ border-color: rgba(47,111,237,.55); transform: translateY(-2px); }}
  .cover {{ display: block; aspect-ratio: 16/9; background: #0a0e13; overflow: hidden; }}
  .cover img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .body {{ padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 8px; flex: 1; }}
  .meta-row {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }}
  .cat {{ font-size: 11px; font-weight: 800; color: #8eb6ff; letter-spacing: .04em; }}
  .badge {{
    font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 999px;
  }}
  .badge.ok {{ background: rgba(31,157,106,.18); color: #6ee7b0; }}
  .badge.warn {{ background: rgba(201,133,26,.18); color: #f0c674; }}
  h2 {{ font-size: 17px; font-weight: 900; line-height: 1.35; }}
  .one {{ font-size: 13px; color: var(--dim); }}
  .out {{ font-size: 12px; color: #b7c4d3; }}
  .actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: auto; padding-top: 6px; }}
  .btn {{
    display: inline-flex; align-items: center; justify-content: center;
    padding: 8px 12px; border-radius: 10px; font-size: 12px; font-weight: 700;
    text-decoration: none; color: var(--text);
    border: 1px solid var(--line); background: rgba(255,255,255,.04);
  }}
  .btn:hover {{ border-color: rgba(255,255,255,.28); }}
  .btn.primary {{ background: var(--accent); border-color: transparent; color: #fff; }}
  .btn.ghost {{ background: transparent; }}
  .detail {{
    grid-column: 1 / -1;
    margin: 8px 0 24px;
    padding: 20px;
    border-radius: var(--radius);
    border: 1px solid var(--line);
    background: rgba(255,255,255,.03);
    scroll-margin-top: 24px;
  }}
  .detail-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 8px; }}
  .detail h3 {{ font-size: 18px; font-weight: 900; }}
  .back {{ color: #9ec0ff; font-size: 13px; text-decoration: none; }}
  .note {{ color: var(--dim); font-size: 13px; margin-bottom: 8px; }}
  .path {{ font-size: 12px; margin-bottom: 14px; color: #c5d0dc; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px;
    background: rgba(0,0,0,.35); padding: 2px 6px; border-radius: 6px; }}
  .keys {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }}
  .keys figure {{
    margin: 0; border-radius: 12px; overflow: hidden;
    border: 1px solid var(--line); background: #0a0e13;
  }}
  .keys img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }}
  .keys figcaption {{
    font-size: 11px; color: var(--dim); padding: 6px 8px; text-align: center;
    background: rgba(0,0,0,.35);
  }}
  .sticky {{ margin-top: 16px; }}
  footer {{
    margin-top: 36px; padding-top: 18px; border-top: 1px solid var(--line);
    color: var(--dim); font-size: 12px; line-height: 1.7;
  }}
</style>
</head>
<body>
  <div class="shell" id="top">
    <header class="hero">
      <div class="badge-top">连锁药店 · 内部培训内容工厂</div>
      <h1>模板货架</h1>
      <p class="sub">
        先看效果，再选课型。下列均为公司已签样/已登记课型；
        下载空白 Word 填写审核内容后，交给 WorkBuddy 出初稿，确认后再出成片。
      </p>
      <div class="chips">
        <span class="chip">共 {len(templates)} 个课型</span>
        <span class="chip">可离线打开</span>
        <span class="chip">内容驱动 · 禁止空行凑满</span>
        <span class="chip">视频 · 克隆药师声</span>
      </div>
    </header>

    <div class="steps">
      <div class="step"><div class="n">1</div><b>看效果</b><span>封面 + 关键页截图</span></div>
      <div class="step"><div class="n">2</div><b>选模板</b><span>记住中文课型名</span></div>
      <div class="step"><div class="n">3</div><b>填框架</b><span>可删节 · 有几条写几条</span></div>
      <div class="step"><div class="n">4</div><b>交 WorkBuddy</b><span>先初稿，确认后成片</span></div>
    </div>

    <div class="grid">
      {"".join(cards)}
    </div>

    <footer>
      <p>本货架仅供内部培训制作辨认课型。预览图来自已签样金样，请勿将包装/Logo 像素直接用于未授权新项目。</p>
      <p>填写规则见上级目录 <code>框架填写说明.md</code>；口令见 <code>04_WorkBuddy口令卡.md</code>。</p>
      <p>打包日期：{date.today().isoformat()}</p>
    </footer>
  </div>
</body>
</html>
"""


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

    (shelf / "index.html").write_text(shelf_html(templates), encoding="utf-8")
    (shelf / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # README for whole package
    (PKG / "README.md").write_text(
        "# 药店培训内容工厂 · 业务包（档 A）\n\n"
        "本包可直接发给一线业务，**无需**安装开发环境。\n\n"
        "**从这里开始：** 双击 `01_模板货架/index.html` → 读 `00_一页怎么用.md`。\n\n"
        "| 目录/文件 | 用途 |\n"
        "|-----------|------|\n"
        "| `00_一页怎么用.md` | 4 步总览 |\n"
        "| `01_模板货架/index.html` | **双击打开**看模板效果 |\n"
        "| `02_空白Word/` | 空白模板 + **本课型怎么填** |\n"
        "| `03_填写参考/` | 仅示范格式（勿当医学终稿） |\n"
        "| `04_WorkBuddy口令卡.md` | 复制给 WorkBuddy |\n"
        "| `05_交付物放这里/` | 成片归档 |\n"
        "| `06_你将收到的初稿长什么样/` | 初稿/缺口/分镜长什么样 |\n"
        "| `业务验收清单.md` | 你点头前的核对表 |\n"
        "| `框架填写说明.md` | 可删节 / 有几条写几条 |\n"
        "| `交付质量说明.md` | 上市公司交付硬标准 |\n\n"
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
