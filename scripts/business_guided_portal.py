#!/usr/bin/env python3
"""Business guided portal — minimal two blocks only.

1) Template preview & select (4 compact cards per row; key frames large when selected)
2) Real fill examples (copy / download)

Primary workflow is conversational with WorkBuddy after install; the page only helps
pick a template and reference real examples.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def build_guided_portal_html(templates: list[dict], *, pack_date: str | None = None) -> str:
    pack_date = pack_date or date.today().isoformat()
    catalog_js = json.dumps(templates, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>内部培训 · 选模板</title>
<style>
:root {{
  --bg: #f4f6f9;
  --card: #fff;
  --text: #1a2332;
  --dim: #5c6b7e;
  --line: #e2e8f0;
  --accent: #1d4ed8;
  --accent-soft: #eff6ff;
  --ok: #047857;
  --ok-soft: #ecfdf5;
  --radius: 12px;
  --font: "PingFang SC","Microsoft YaHei","Noto Sans SC",system-ui,sans-serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font);
  color: var(--text);
  background: var(--bg);
  line-height: 1.5;
  min-height: 100vh;
}}
.shell {{ max-width: 1080px; margin: 0 auto; padding: 20px 16px 56px; }}
header {{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px 20px;
  margin-bottom: 16px;
}}
header h1 {{ font-size: 20px; font-weight: 800; margin-bottom: 6px; }}
header .sub {{ font-size: 13px; color: var(--dim); max-width: 70ch; }}
.how {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
}}
@media (max-width: 720px) {{ .how {{ grid-template-columns: 1fr; }} }}
.how div {{
  background: var(--accent-soft);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  color: var(--dim);
}}
.how b {{ display: block; color: var(--text); font-size: 13px; margin-bottom: 2px; }}
.how code {{
  font-family: ui-monospace, Menlo, monospace;
  font-size: 11px;
  background: #fff;
  border: 1px solid var(--line);
  padding: 1px 5px;
  border-radius: 4px;
  color: #1e3a8a;
  word-break: break-all;
}}
section.block {{
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px 18px;
  margin-bottom: 14px;
}}
section.block h2 {{
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
section.block h2 .n {{
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--accent); color: #fff;
  font-size: 12px; display: inline-flex; align-items: center; justify-content: center;
}}
section.block > .hint {{ font-size: 12px; color: var(--dim); margin-bottom: 12px; }}

/* 4 per row, compact */
.grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}}
@media (max-width: 900px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 480px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
.tcard {{
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  background: #fafbfc;
  cursor: pointer;
  transition: border-color .12s, box-shadow .12s;
}}
.tcard:hover {{ border-color: #93c5fd; }}
.tcard.selected {{
  border-color: var(--ok);
  box-shadow: 0 0 0 2px rgba(4,120,87,.2);
  background: var(--ok-soft);
}}
.tcard img.cover {{
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
  background: #0f172a;
}}
.tcard .body {{ padding: 8px 9px 10px; }}
.tcard h3 {{
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
  margin-bottom: 2px;
}}
.tcard .meta {{
  font-size: 10px;
  color: var(--dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}

/* large key frames when selected */
.preview-pane {{
  display: none;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}}
.preview-pane.show {{ display: block; }}
.preview-pane .title-row {{
  display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between;
  gap: 8px; margin-bottom: 10px;
}}
.preview-pane .title-row strong {{ font-size: 14px; }}
.preview-pane .title-row span {{ font-size: 12px; color: var(--dim); }}
.keys {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}}
.keys figure {{
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  background: #0f172a;
}}
.keys img {{
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
}}
.keys figcaption {{
  font-size: 11px;
  text-align: center;
  padding: 6px 8px;
  color: var(--dim);
  background: #fff;
}}
.actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
.btn {{
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--text);
  text-decoration: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}}
.btn.primary {{ background: var(--accent); border-color: transparent; color: #fff; }}
.btn.ok {{ background: var(--ok); border-color: transparent; color: #fff; }}
.btn:disabled {{ opacity: .45; cursor: not-allowed; }}

.cmdbox {{
  margin-top: 10px;
  padding: 12px;
  border-radius: 10px;
  background: #0f172a;
  color: #e2e8f0;
  font-family: ui-monospace, Menlo, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  display: none;
}}
.cmdbox.show {{ display: block; }}
.toast {{ font-size: 12px; color: var(--ok); margin-top: 6px; min-height: 1.2em; }}

/* examples */
.ex-list {{ display: flex; flex-direction: column; gap: 8px; }}
.ex-row {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fafbfc;
}}
.ex-row .name {{ font-size: 13px; font-weight: 700; flex: 1 1 180px; }}
.ex-row .tag {{
  font-size: 11px;
  color: var(--dim);
  flex: 1 1 160px;
}}
.ex-row .btns {{ display: flex; flex-wrap: wrap; gap: 6px; }}

footer {{
  margin-top: 8px;
  font-size: 11px;
  color: var(--dim);
  text-align: center;
}}
</style>
</head>
<body>
<div class="shell">
  <header>
    <h1>内部培训课件 · 选模板</h1>
    <p class="sub">商品 / 疾病内部培训课件与视频。页面只做两件事：选模板、看真实示例。内容在 WorkBuddy 对话里说即可。</p>
    <div class="how">
      <div>
        <b>① 安装</b>
        在 WorkBuddy 输入：<br />
        <code>请安装 https://github.com/lmr1123/chain-pharmacy-content-studio.git，然后指引我使用</code>
      </div>
      <div>
        <b>② 选模板</b>
        在本页点一个课型，看关键页截图，点「选用」
      </div>
      <div>
        <b>③ 说内容 → 出片</b>
        回 WorkBuddy 描述商品/疾病要点；它先出内容初稿，你确认后再生成 PPT / 视频
      </div>
    </div>
  </header>

  <section class="block" id="sec-templates">
    <h2><span class="n">1</span> 模板预览与选择</h2>
    <p class="hint">一行 4 个；点卡片看<strong>关键页面截图</strong>（大图）。选好后复制口令回 WorkBuddy 即可。</p>
    <div class="grid" id="template-grid"></div>

    <div class="preview-pane" id="preview-pane">
      <div class="title-row">
        <strong id="sel-name">—</strong>
        <span id="sel-meta"></span>
      </div>
      <div class="keys" id="sel-keys"></div>
      <div class="actions">
        <button type="button" class="btn ok" id="btn-use">选用此模板 · 复制口令</button>
        <a class="btn" id="btn-blank" href="#" download>下载空白 Word（可选）</a>
      </div>
      <div class="cmdbox" id="cmdbox"></div>
      <p class="toast" id="toast"></p>
    </div>
  </section>

  <section class="block" id="sec-examples">
    <h2><span class="n">2</span> 填报真实示例</h2>
    <p class="hint">只示范结构和写法，可下载对照。医学与包装以贵司审核稿为准，不要直接当新项目终稿。</p>
    <div class="ex-list" id="ex-list"></div>
  </section>

  <footer>内部培训 · {pack_date} · 预览来自已签样金样</footer>
</div>

<script>
const TEMPLATES = {catalog_js};
let selected = null;

function mediaCover(slug) {{
  return "01_模板货架/media/" + slug + "/cover.png";
}}
function mediaKey(slug, i) {{
  return "01_模板货架/media/" + slug + "/key-" + String(i).padStart(2, "0") + ".png";
}}
function blankHref(slug) {{
  return "02_空白Word/" + slug + "/业务提交_空白模板.docx";
}}
function refHref(slug) {{
  return "03_填写参考/" + slug + "/业务提交_填写参考.docx";
}}

function buildCmd(t) {{
  return (
    "我选 【" + t.name_zh + "】。\\n" +
    "请按这个模板整理【商品名或病名】内部培训内容。\\n" +
    "要点：【用几句话写卖点/培训重点，例如：宁心安神助睡眠、提升免疫力、保肝护肝抗衰老】\\n" +
    "你先整理成符合模板结构的内容初稿给我确认；我确认后再生成可编辑 PPT（或视频）。\\n" +
    "有几条写几条，不要空行凑满；无授权包装用槽位，不要仿包装。"
  );
}}

function renderGrid() {{
  const grid = document.getElementById("template-grid");
  grid.innerHTML = "";
  TEMPLATES.forEach(t => {{
    const card = document.createElement("article");
    card.className = "tcard" + (selected && selected.slug === t.slug ? " selected" : "");
    card.innerHTML =
      '<img class="cover" src="' + mediaCover(t.slug) + '" alt="' + t.name_zh + '" loading="lazy" />' +
      '<div class="body">' +
      "<h3>" + t.name_zh + "</h3>" +
      '<div class="meta">' + (t.outputs || []).join(" · ") + "</div>" +
      "</div>";
    card.addEventListener("click", () => selectTemplate(t));
    grid.appendChild(card);
  }});
}}

function selectTemplate(t) {{
  selected = t;
  try {{
    localStorage.setItem("cpc_selected_template", JSON.stringify({{ slug: t.slug, name_zh: t.name_zh }}));
  }} catch (e) {{}}
  renderGrid();

  const pane = document.getElementById("preview-pane");
  pane.classList.add("show");
  document.getElementById("sel-name").textContent = t.name_zh;
  document.getElementById("sel-meta").textContent =
    (t.one_liner || "") + (t.production_ready === false ? " · 新主题请与制作确认" : "");

  const keys = document.getElementById("sel-keys");
  keys.innerHTML = "";
  (t.key_frame_labels_zh || []).forEach((lab, idx) => {{
    const i = idx + 1;
    const fig = document.createElement("figure");
    fig.innerHTML =
      '<img src="' + mediaKey(t.slug, i) + '" alt="' + lab + '" loading="lazy" />' +
      "<figcaption>" + lab + "</figcaption>";
    keys.appendChild(fig);
  }});

  document.getElementById("btn-blank").href = blankHref(t.slug);
  const box = document.getElementById("cmdbox");
  box.textContent = buildCmd(t);
  box.classList.add("show");
  document.getElementById("toast").textContent = "";
  pane.scrollIntoView({{ behavior: "smooth", block: "nearest" }});
}}

function renderExamples() {{
  const list = document.getElementById("ex-list");
  list.innerHTML = "";
  TEMPLATES.forEach(t => {{
    const row = document.createElement("div");
    row.className = "ex-row";
    row.innerHTML =
      '<div class="name">' + t.name_zh + "</div>" +
      '<div class="tag">' + (t.one_liner || "") + "</div>" +
      '<div class="btns">' +
      '<a class="btn primary" href="' + refHref(t.slug) + '" download>下载填写示例</a>' +
      '<a class="btn" href="' + blankHref(t.slug) + '" download>空白模板</a>' +
      "</div>";
    list.appendChild(row);
  }});
}}

document.getElementById("btn-use").addEventListener("click", async () => {{
  if (!selected) return;
  const text = buildCmd(selected);
  document.getElementById("cmdbox").textContent = text;
  document.getElementById("cmdbox").classList.add("show");
  try {{
    await navigator.clipboard.writeText(text);
    document.getElementById("toast").textContent =
      "已复制。回到 WorkBuddy 粘贴，把【商品名或病名】和要点改成你的内容即可。";
  }} catch (e) {{
    document.getElementById("toast").textContent = "请手动选中下方口令复制。";
  }}
}});

try {{
  const raw = localStorage.getItem("cpc_selected_template");
  if (raw) {{
    const saved = JSON.parse(raw);
    const t = TEMPLATES.find(x => x.slug === saved.slug);
    if (t) selected = t;
  }}
}} catch (e) {{}}

renderGrid();
renderExamples();
if (selected) selectTemplate(selected);
</script>
</body>
</html>
"""


def write_upload_folder_readme(path: Path) -> None:
    """Kept for optional offline drop-box; not part of the simplified portal UX."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# 可选 · 文件投递箱

主流程请在 **WorkBuddy 聊天** 直接说内容 / 发附件。

本目录仅备用：若要把已填 Word 或授权图放进仓库，可放入 `待处理/`。
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    print("business_guided_portal: import build_guided_portal_html")
