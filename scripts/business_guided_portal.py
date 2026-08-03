#!/usr/bin/env python3
"""Generate open-source-style guided portal HTML for the business package.

Flow: 了解 → 预览选模板 → 填 Word → 上传提交（给 WorkBuddy）
Offline, no server; catalog + media paths relative to package root.
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
<title>培训内容工厂 · 业务引导</title>
<style>
:root {{
  --bg: #0b1020;
  --panel: #121a2b;
  --panel2: #182235;
  --line: rgba(255,255,255,.10);
  --text: #eef3fb;
  --dim: #9aabbf;
  --accent: #3b82f6;
  --ok: #22c55e;
  --warn: #f59e0b;
  --radius: 16px;
  --font: "PingFang SC","Microsoft YaHei","Noto Sans SC",system-ui,sans-serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font);
  color: var(--text);
  min-height: 100vh;
  background:
    radial-gradient(900px 480px at 0% -10%, rgba(59,130,246,.22), transparent 55%),
    radial-gradient(700px 400px at 100% 0%, rgba(34,197,94,.12), transparent 50%),
    var(--bg);
  line-height: 1.55;
}}
.shell {{ max-width: 1100px; margin: 0 auto; padding: 28px 18px 72px; }}
.topbar {{
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 12px; margin-bottom: 22px;
}}
.brand {{ font-weight: 900; font-size: 18px; letter-spacing: -.02em; }}
.brand span {{ color: var(--dim); font-weight: 600; font-size: 13px; margin-left: 8px; }}
.progress {{
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 22px;
}}
.progress button {{
  border: 1px solid var(--line); background: var(--panel);
  color: var(--dim); border-radius: 999px; padding: 8px 14px;
  font-size: 12px; font-weight: 700; cursor: pointer;
}}
.progress button.active {{ background: var(--accent); border-color: transparent; color: #fff; }}
.progress button.done {{ border-color: rgba(34,197,94,.45); color: #86efac; }}
.card {{
  background: linear-gradient(180deg, var(--panel), var(--panel2));
  border: 1px solid var(--line); border-radius: 20px; padding: 22px 22px 24px;
  margin-bottom: 16px;
}}
h1 {{ font-size: 26px; font-weight: 900; margin-bottom: 8px; letter-spacing: -.02em; }}
h2 {{ font-size: 18px; font-weight: 900; margin-bottom: 10px; }}
p, li {{ color: var(--dim); font-size: 14px; }}
.lead {{ color: #c9d6e8; font-size: 15px; max-width: 62ch; margin-bottom: 14px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }}
.tcard {{
  border: 1px solid var(--line); border-radius: 16px; overflow: hidden;
  background: rgba(0,0,0,.22); display: flex; flex-direction: column;
  cursor: pointer; transition: border-color .15s, transform .15s;
}}
.tcard:hover {{ border-color: rgba(59,130,246,.55); transform: translateY(-2px); }}
.tcard.selected {{ border-color: var(--ok); box-shadow: 0 0 0 1px rgba(34,197,94,.35); }}
.tcard img.cover {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; background: #000; }}
.tcard .body {{ padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 6px; flex: 1; }}
.badge {{ display: inline-flex; align-self: flex-start; font-size: 11px; font-weight: 800;
  padding: 3px 8px; border-radius: 999px; }}
.badge.ok {{ background: rgba(34,197,94,.16); color: #86efac; }}
.badge.warn {{ background: rgba(245,158,11,.16); color: #fcd34d; }}
.tcard h3 {{ font-size: 15px; font-weight: 900; color: var(--text); }}
.tcard .one {{ font-size: 12px; color: var(--dim); }}
.keys {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px; margin-top: 10px; }}
.keys figure {{ margin: 0; border-radius: 10px; overflow: hidden; border: 1px solid var(--line); background: #000; }}
.keys img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }}
.keys figcaption {{ font-size: 10px; text-align: center; padding: 4px; color: var(--dim); }}
.actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
.btn {{
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  border: 1px solid var(--line); background: rgba(255,255,255,.04);
  color: var(--text); text-decoration: none; border-radius: 12px;
  padding: 10px 16px; font-size: 13px; font-weight: 800; cursor: pointer;
}}
.btn.primary {{ background: var(--accent); border-color: transparent; color: #fff; }}
.btn.ok {{ background: var(--ok); border-color: transparent; color: #052e16; }}
.btn:disabled {{ opacity: .45; cursor: not-allowed; }}
.panel-selected {{
  margin-top: 14px; padding: 14px; border-radius: 14px;
  border: 1px dashed rgba(34,197,94,.4); background: rgba(34,197,94,.06);
}}
.panel-selected strong {{ color: #bbf7d0; }}
ol.steps-list {{ margin: 10px 0 0 18px; }}
ol.steps-list li {{ margin: 8px 0; }}
code, .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px;
  background: rgba(0,0,0,.35); padding: 2px 6px; border-radius: 6px; color: #dbeafe; }}
.upload-zone {{
  margin-top: 12px; border: 2px dashed rgba(59,130,246,.45); border-radius: 16px;
  padding: 28px 18px; text-align: center; background: rgba(59,130,246,.06);
  cursor: pointer;
}}
.upload-zone.drag {{ border-color: var(--ok); background: rgba(34,197,94,.08); }}
.upload-zone h3 {{ color: var(--text); margin-bottom: 6px; }}
.file-list {{ margin-top: 12px; text-align: left; }}
.file-list li {{ color: #c7d2fe; font-size: 13px; margin: 4px 0 4px 18px; }}
.cmdbox {{
  margin-top: 12px; padding: 14px; border-radius: 12px;
  background: #0a0f1a; border: 1px solid var(--line);
  white-space: pre-wrap; font-family: ui-monospace, Menlo, monospace;
  font-size: 12px; color: #e2e8f0; line-height: 1.6;
}}
.hidden {{ display: none !important; }}
.note {{ font-size: 12px; color: var(--dim); margin-top: 10px; }}
.checklist {{ list-style: none; margin-top: 10px; }}
.checklist li {{ margin: 6px 0; color: #cbd5e1; font-size: 13px; }}
.checklist li::before {{ content: "☐ "; color: var(--accent); font-weight: 800; }}
footer {{ margin-top: 28px; color: var(--dim); font-size: 12px; }}
</style>
</head>
<body>
<div class="shell">
  <div class="topbar">
    <div class="brand">培训内容工厂 <span>业务引导 · 开源式四步</span></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <a class="btn" href="01_模板货架/index.html">仅打开货架</a>
      <a class="btn" href="04_WorkBuddy口令卡.md">口令卡</a>
      <a class="btn" href="业务验收清单.md">验收清单</a>
    </div>
  </div>

  <nav class="progress" id="progress">
    <button type="button" data-step="1" class="active">1 了解</button>
    <button type="button" data-step="2">2 预览选模板</button>
    <button type="button" data-step="3">3 填 Word</button>
    <button type="button" data-step="4">4 上传提交</button>
  </nav>

  <!-- STEP 1 -->
  <section class="card" id="step-1">
    <h1>开始使用</h1>
    <p class="lead">
      默认由 <strong style="color:#fff">WorkBuddy</strong> 安装 GitHub 仓库后打开本页（业务不必自己解压 zip）。
      流程按开源项目「先看清 → 再选用 → 再填报 → 再提交」组织：你选模板并填 Word，WorkBuddy 出初稿与成片。
    </p>
    <ol class="steps-list">
      <li><strong style="color:#fff">预览并选择模板</strong> — 看封面与关键页，确认观感</li>
      <li><strong style="color:#fff">下载空白 Word 填报</strong> — 可删节，有几条写几条</li>
      <li><strong style="color:#fff">上传提交</strong> — 附件发给 WorkBuddy，或拖入本页 / 放入提交箱</li>
      <li><strong style="color:#fff">审初稿后收成片</strong> — 先确认，再出 PPTX / 视频</li>
    </ol>
    <div class="actions">
      <button type="button" class="btn primary" id="go-step-2">下一步：预览选模板</button>
    </div>
    <p class="note">在 WorkBuddy 输入「请安装 …chain-pharmacy-content-studio.git，然后指引我使用」即可被引导到本页。无需装 Node / 起端口。</p>
  </section>

  <!-- STEP 2 -->
  <section class="card hidden" id="step-2">
    <h1>预览并选择模板</h1>
    <p class="lead">点击卡片查看关键页，再点「选用此模板」。选用后进入 Word 填报步骤。</p>
    <div class="grid" id="template-grid"></div>
    <div class="panel-selected hidden" id="selected-panel">
      <div>已选：<strong id="selected-name"></strong></div>
      <div class="note" id="selected-note"></div>
      <div class="keys" id="selected-keys"></div>
      <div class="actions">
        <button type="button" class="btn ok" id="go-step-3">下一步：按 Word 填报</button>
        <a class="btn" id="open-blank-early" href="#">先下载空白 Word</a>
      </div>
    </div>
    <div class="actions">
      <button type="button" class="btn" data-back="1">上一步</button>
    </div>
  </section>

  <!-- STEP 3 -->
  <section class="card hidden" id="step-3">
    <h1>按 Word 填报</h1>
    <p class="lead">用已选模板的空白 Word 填写<strong style="color:#fff">公司审核内容</strong>。不要填坐标、页数、动画参数。</p>
    <div class="panel-selected">
      <div>当前模板：<strong id="fill-name"></strong></div>
      <ul class="checklist">
        <li>下载空白 Word，另存为「主题名_日期.docx」</li>
        <li>打开「本课型怎么填」，按推荐板块写（可删整节）</li>
        <li>联合用药 / 列表：有几条写几条（2 组就 2 行）</li>
        <li>包装 / Logo：有授权图就插入 Word 对应板块；没有就删图片行</li>
        <li>可对照填写参考学格式，勿照搬示例医学结论</li>
      </ul>
      <div class="actions">
        <a class="btn primary" id="dl-blank" href="#">下载空白 Word</a>
        <a class="btn" id="dl-guide" href="#">本课型怎么填</a>
        <a class="btn" id="dl-ref" href="#">格式参考（选看）</a>
      </div>
    </div>
    <div class="actions">
      <button type="button" class="btn" data-back="2">上一步</button>
      <button type="button" class="btn primary" id="go-step-4">下一步：上传提交</button>
    </div>
  </section>

  <!-- STEP 4 -->
  <section class="card hidden" id="step-4">
    <h1>上传提交（给 WorkBuddy）</h1>
    <p class="lead">
      浏览器无法直接写入你的磁盘文件夹时，请用下面两种方式之一完成「上传」：
      <strong style="color:#fff">① 点选文件生成提交清单并复制口令</strong>；
      <strong style="color:#fff">② 把文件拷进包内 <span class="mono">07_业务填报上传/待处理/</span></strong>。
    </p>

    <div class="panel-selected">
      <div>提交模板：<strong id="submit-name">（尚未选模板）</strong></div>
      <div class="note">请填写主题名（病名或商品名），便于 WorkBuddy 建交付目录。</div>
      <p style="margin-top:10px;">
        <label style="color:#fff;font-size:13px;font-weight:700;">主题名称　</label>
        <input id="theme-input" type="text" placeholder="例如：金银花露 / 风热证店员培训"
          style="width:min(420px,100%);padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:#0a0f1a;color:#fff;font-size:14px;" />
      </p>
    </div>

    <div class="upload-zone" id="upload-zone" tabindex="0">
      <h3>点击或拖入已填 Word + 授权图片</h3>
      <p>支持 .docx / .doc / .png / .jpg / .jpeg / .webp / .pdf</p>
      <input type="file" id="file-input" class="hidden" multiple
        accept=".docx,.doc,.png,.jpg,.jpeg,.webp,.pdf,image/*" />
    </div>
    <ul class="file-list" id="file-list"></ul>

    <h2 style="margin-top:18px;">发给 WorkBuddy 的口令（复制）</h2>
    <div class="cmdbox" id="cmdbox">请先在第 2 步选用模板，并填写主题名称。</div>
    <div class="actions">
      <button type="button" class="btn primary" id="copy-cmd">复制口令</button>
      <button type="button" class="btn" id="dl-manifest">下载提交清单 .md</button>
      <a class="btn" href="07_业务填报上传/README.md">打开上传目录说明</a>
    </div>
    <p class="note" id="copy-status"></p>

    <div class="actions" style="margin-top:18px;">
      <button type="button" class="btn" data-back="3">上一步</button>
      <a class="btn" href="06_你将收到的初稿长什么样/说明.md">WorkBuddy 会先给什么</a>
      <a class="btn ok" href="05_交付物放这里/">成片放这里</a>
    </div>
  </section>

  <footer>
    业务 + WorkBuddy 协作交付 · 打包日期 {pack_date} · 预览帧来自已签样金样，勿将包装像素用于未授权项目
  </footer>
</div>

<script>
const TEMPLATES = {catalog_js};
const state = {{
  step: 1,
  selected: null,
  files: [],
}};

function $(id) {{ return document.getElementById(id); }}

function showStep(n) {{
  state.step = n;
  for (let i = 1; i <= 4; i++) {{
    const el = $("step-" + i);
    if (el) el.classList.toggle("hidden", i !== n);
  }}
  document.querySelectorAll("#progress button").forEach(btn => {{
    const s = Number(btn.dataset.step);
    btn.classList.toggle("active", s === n);
    btn.classList.toggle("done", s < n);
  }});
  if (n === 2) renderGrid();
  if (n === 3) fillStep3();
  if (n === 4) fillStep4();
  window.scrollTo({{ top: 0, behavior: "smooth" }});
}}

function mediaCover(slug) {{
  return "01_模板货架/media/" + slug + "/cover.png";
}}
function mediaKey(slug, i) {{
  return "01_模板货架/media/" + slug + "/key-" + String(i).padStart(2, "0") + ".png";
}}
function blankHref(slug) {{
  return "02_空白Word/" + slug + "/业务提交_空白模板.docx";
}}
function guideHref(slug) {{
  return "02_空白Word/" + slug + "/本课型怎么填.md";
}}
function refHref(slug) {{
  return "03_填写参考/" + slug + "/业务提交_填写参考.docx";
}}

function renderGrid() {{
  const grid = $("template-grid");
  grid.innerHTML = "";
  TEMPLATES.forEach(t => {{
    const card = document.createElement("article");
    card.className = "tcard" + (state.selected && state.selected.slug === t.slug ? " selected" : "");
    card.innerHTML = `
      <img class="cover" src="${{mediaCover(t.slug)}}" alt="${{t.name_zh}}" />
      <div class="body">
        <span class="badge ${{t.production_ready ? "ok" : "warn"}}">${{t.status_label || ""}}</span>
        <h3>${{t.name_zh}}</h3>
        <p class="one">${{t.one_liner || ""}}</p>
        <p class="one">产物：${{(t.outputs || []).join(" · ")}}</p>
        <div class="actions">
          <button type="button" class="btn primary pick">选用此模板</button>
        </div>
      </div>`;
    card.querySelector(".pick").addEventListener("click", (e) => {{
      e.stopPropagation();
      selectTemplate(t);
    }});
    card.addEventListener("click", () => selectTemplate(t));
    grid.appendChild(card);
  }});
}}

function selectTemplate(t) {{
  state.selected = t;
  try {{ localStorage.setItem("cpc_selected_template", JSON.stringify({{ slug: t.slug, name_zh: t.name_zh }})); }} catch (e) {{}}
  renderGrid();
  const panel = $("selected-panel");
  panel.classList.remove("hidden");
  $("selected-name").textContent = t.name_zh;
  $("selected-note").textContent = t.status_note || "";
  const keys = $("selected-keys");
  keys.innerHTML = "";
  (t.key_frame_labels_zh || []).forEach((lab, idx) => {{
    const i = idx + 1;
    const fig = document.createElement("figure");
    fig.innerHTML = `<img src="${{mediaKey(t.slug, i)}}" alt="${{lab}}" /><figcaption>${{lab}}</figcaption>`;
    keys.appendChild(fig);
  }});
  $("open-blank-early").href = blankHref(t.slug);
}}

function fillStep3() {{
  const t = state.selected;
  if (!t) {{
    $("fill-name").textContent = "尚未选择 — 请回第 2 步";
    return;
  }}
  $("fill-name").textContent = t.name_zh;
  $("dl-blank").href = blankHref(t.slug);
  $("dl-guide").href = guideHref(t.slug);
  $("dl-ref").href = refHref(t.slug);
}}

function buildCommand() {{
  const t = state.selected;
  const theme = ($("theme-input").value || "").trim() || "【病名或商品名】";
  if (!t) {{
    return "请先在第 2 步选用模板，并填写主题名称。";
  }}
  const names = (state.files || []).map(f => f.name);
  const fileLine = names.length
    ? ("附件文件：\\n- " + names.join("\\n- "))
    : "附件：请见同消息上传的 Word / 图片（或 07_业务填报上传/待处理/）";
  return (
    "我要用 【" + t.name_zh + "】，主题是 【" + theme + "】。\\n" +
    "已按业务包引导完成：预览选模板 → Word 填报 → 上传提交。\\n" +
    fileLine + "\\n" +
    "请先出 初稿/分镜预览 + 待确认项 + 缺图清单；\\n" +
    "我确认后再出 可编辑 PPTX / 培训视频。\\n" +
    "示例 Word 只作格式参考，医学与包装以我司审核稿为准。\\n" +
    "联合用药/列表请按实际条数排版，禁止空行凑满。"
  );
}}

function fillStep4() {{
  const t = state.selected;
  $("submit-name").textContent = t ? t.name_zh : "（尚未选模板）";
  $("cmdbox").textContent = buildCommand();
}}

function renderFiles() {{
  const ul = $("file-list");
  ul.innerHTML = "";
  state.files.forEach(f => {{
    const li = document.createElement("li");
    li.textContent = f.name + "  (" + Math.max(1, Math.round(f.size / 1024)) + " KB)";
    ul.appendChild(li);
  }});
  $("cmdbox").textContent = buildCommand();
}}

function addFiles(fileList) {{
  const arr = Array.from(fileList || []);
  const okExt = /\\.(docx|doc|png|jpe?g|webp|pdf)$/i;
  arr.forEach(f => {{
    if (!okExt.test(f.name)) return;
    if (!state.files.some(x => x.name === f.name && x.size === f.size)) {{
      state.files.push(f);
    }}
  }});
  renderFiles();
}}

// events
$("go-step-2").addEventListener("click", () => showStep(2));
$("go-step-3").addEventListener("click", () => {{
  if (!state.selected) {{ alert("请先选用一个模板"); return; }}
  showStep(3);
}});
$("go-step-4").addEventListener("click", () => {{
  if (!state.selected) {{ alert("请先选用一个模板"); return; }}
  showStep(4);
}});
document.querySelectorAll("[data-back]").forEach(btn => {{
  btn.addEventListener("click", () => showStep(Number(btn.dataset.back)));
}});
document.querySelectorAll("#progress button").forEach(btn => {{
  btn.addEventListener("click", () => showStep(Number(btn.dataset.step)));
}});

$("theme-input").addEventListener("input", () => {{
  $("cmdbox").textContent = buildCommand();
}});

const zone = $("upload-zone");
const input = $("file-input");
zone.addEventListener("click", () => input.click());
zone.addEventListener("keydown", (e) => {{ if (e.key === "Enter" || e.key === " ") input.click(); }});
input.addEventListener("change", () => addFiles(input.files));
["dragenter","dragover"].forEach(ev => zone.addEventListener(ev, e => {{
  e.preventDefault(); zone.classList.add("drag");
}}));
["dragleave","drop"].forEach(ev => zone.addEventListener(ev, e => {{
  e.preventDefault(); zone.classList.remove("drag");
}}));
zone.addEventListener("drop", e => addFiles(e.dataTransfer.files));

$("copy-cmd").addEventListener("click", async () => {{
  const text = buildCommand();
  try {{
    await navigator.clipboard.writeText(text);
    $("copy-status").textContent = "口令已复制。请打开 WorkBuddy，粘贴并附上 Word/图片。";
  }} catch (e) {{
    $("copy-status").textContent = "复制失败，请手动选中上方口令框复制。";
  }}
}});

$("dl-manifest").addEventListener("click", () => {{
  const t = state.selected;
  const theme = ($("theme-input").value || "").trim() || "未命名主题";
  const names = state.files.map(f => f.name);
  const md = [
    "# 业务填报提交清单",
    "",
    "- 日期：{pack_date}",
    "- 课型：" + (t ? t.name_zh : "未选"),
    "- slug：" + (t ? t.slug : ""),
    "- 主题：" + theme,
    "- 文件：",
    ...(names.length ? names.map(n => "  - " + n) : ["  - （请同时把文件放入 07_业务填报上传/待处理/）"]),
    "",
    "## WorkBuddy 口令",
    "",
    "```",
    buildCommand(),
    "```",
    "",
    "## 业务自检",
    "",
    "- [ ] 模板已预览选用",
    "- [ ] Word 为审核内容，列表未空行凑满",
    "- [ ] 授权图已附或已声明缺口",
    "",
  ].join("\\n");
  const blob = new Blob([md], {{ type: "text/markdown;charset=utf-8" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "提交清单_" + theme.replace(/[\\\\/:*?\\"<>|]/g, "_") + ".md";
  a.click();
  URL.revokeObjectURL(a.href);
}});

// restore selection
try {{
  const raw = localStorage.getItem("cpc_selected_template");
  if (raw) {{
    const saved = JSON.parse(raw);
    const t = TEMPLATES.find(x => x.slug === saved.slug);
    if (t) state.selected = t;
  }}
}} catch (e) {{}}

showStep(1);
</script>
</body>
</html>
"""


def write_upload_folder_readme(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# 业务填报上传区

配合根目录 `index.html` 第 4 步使用。

## 目录约定

```text
07_业务填报上传/
  待处理/          ← 把「已填 Word + 授权图」放这里
  已提交/          ← WorkBuddy 接单后可移到这里（可选）
  README.md        ← 本说明
```

## 业务怎么做

1. 在引导页 **预览选模板 → 填 Word**
2. 将文件复制到 `待处理/`（或拖入引导页生成提交清单）
3. 复制口令发给 WorkBuddy
4. WorkBuddy 处理后，成片进 `05_交付物放这里/`

## WorkBuddy 怎么做

1. 扫描本目录 `待处理/`
2. 结合业务口令中的课型中文名锁定 settled 模板
3. 先出初稿 + 缺口，确认后再出 PPTX/MP4
4. 处理完可将原材料移至 `已提交/<主题_日期>/`

禁止：假包装、系统机器人音色、空行凑满列表。
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    # smoke: print length only
    demo = [{"slug": "x", "name_zh": "测试", "one_liner": "", "outputs": [], "production_ready": True,
             "status_label": "ok", "status_note": "", "key_frame_labels_zh": ["a"]}]
    html = build_guided_portal_html(demo)
    print(len(html))
