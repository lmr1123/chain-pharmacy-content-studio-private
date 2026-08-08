#!/usr/bin/env python3
"""Business guided portal — minimal two blocks only.

1) Template preview & select (4 compact cards per row; key frames large when selected)
2) Real fill examples shown inline for the selected template (no download)

Primary workflow is conversational with WorkBuddy after install.
"""

from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path


def extract_docx_paragraphs(path: Path, *, max_paras: int = 80) -> list[str]:
    """Plain paragraphs from a business filled-example docx."""
    try:
        from docx import Document
    except ImportError as exc:
        raise SystemExit("python-docx required to embed fill examples") from exc
    if not path.is_file():
        return []
    doc = Document(str(path))
    out: list[str] = []
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if not t:
            continue
        out.append(t)
        if len(out) >= max_paras:
            break
    return out


def _is_heading_line(text: str) -> bool:
    if len(text) > 28:
        return False
    if text.endswith(("。", "；", "!", "？", "?", "…")):
        return False
    # section-like titles
    if text.endswith(("：", ":")) and len(text) <= 20:
        return True
    if text in {
        "商品介绍",
        "核心卖点",
        "适宜人群",
        "联合用药话术",
        "注意事项",
        "课程小结",
        "什么是风热证",
        "典型表现",
        "调理思路",
        "日常注意事项",
        "问题引入",
        "基本概念与典型表现",
        "商品基础信息",
        "核心知识",
        "适宜人群与联合方案",
        "为什么要了解辅酶 Q10",
        "一、疾病篇",
        "二、商品介绍",
        "课程基本信息",
    }:
        return True
    # short title without period
    return len(text) <= 16 and "｜" not in text and "。" not in text


def paragraphs_to_html_blocks(paragraphs: list[str]) -> str:
    """Render example paras as safe HTML (headings + body)."""
    parts: list[str] = []
    for i, raw in enumerate(paragraphs):
        t = html.escape(raw)
        is_disclaimer = any(
            k in raw
            for k in (
                "填写参考",
                "真实已填",
                "样本",
                "仅用于",
                "不代表",
                "审核终稿",
                "演示占位",
            )
        )
        if i == 0 or is_disclaimer:
            parts.append(f'<p class="ex-note">{t}</p>')
        elif _is_heading_line(raw):
            parts.append(f"<h4>{t}</h4>")
        else:
            parts.append(f"<p>{t}</p>")
    return "\n".join(parts) if parts else '<p class="ex-note">暂无填写示例正文。</p>'


def build_business_command(template: dict) -> str:
    """Return an approval-first command matching the actual deliverable."""
    name = template["name_zh"]
    slug = str(template.get("slug") or "")
    category = str(template.get("category") or "")
    capabilities = template.get("capabilities") or {}
    can_pptx = bool(capabilities.get("new_theme_pptx"))
    can_mp4 = bool(capabilities.get("new_theme_mp4"))
    subject = "商品名" if category == "商品培训" else "病名或健康主题"

    if not can_pptx and not can_mp4:
        return (
            f"我选【{name}】，目前仅查看金样和填写参考。"
            "请先告诉我这套模板还缺哪些换主题能力，不要生成正式成品。"
        )
    if can_pptx and can_mp4:
        return (
            f"我选【{name}】，需要【可编辑 PPTX / 完整 MP4，请保留我选择的一项】。\n"
            f"{subject}是【请填写】，审核要点是【要点1、要点2、要点3】。"
            "请先整理内容初稿和所需素材缺口供我确认；确认后再检查本机能力并生成正式成品。"
        )
    if can_mp4:
        if slug == "product-video-faithful-v1":
            return (
                f"我选【{name}】，商品名是【请填写】，并附上已获业务授权的商品包装图。\n"
                "审核要点是【要点1、要点2、要点3】。请先整理完整脚本和分镜、列出素材与授权缺口供我确认；"
                "确认后再检查本机能力并生成完整 MP4，不要跳过确认。"
            )
        if slug == "health-video-reference-tech-v1":
            return (
                f"我选【{name}】，病名或健康主题是【请填写】，并提交已审核的 7 段内容要点。\n"
                "请先整理完整脚本、分镜和主题画面复核包，缺少的医学内容只列缺口；"
                "内容与全部画面确认后，再检查本机能力并生成完整 MP4。"
            )
        return (
            f"我选【{name}】，{subject}是【请填写】，审核要点是【要点1、要点2、要点3】。\n"
            "请先整理完整脚本和分镜、列出素材与授权缺口供我确认；"
            "确认后再检查本机能力并生成完整 MP4，不要跳过确认。"
        )
    return (
        f"我选【{name}】，{subject}是【请填写】，审核要点是【要点1、要点2、要点3】。\n"
        "请先整理内容初稿和缺口供我确认；确认后再检查本机能力并生成可编辑 PPTX。"
    )


RUNTIME_CAPABILITY_NAMES = {
    "pptx_export",
    "video_full",
    "video_tts",
    "video_render",
}


def readiness_badge(
    template: dict,
    runtime_capabilities: dict[str, bool] | None = None,
) -> dict[str, str]:
    capabilities = template.get("capabilities") or {}
    if capabilities.get("business_selfserve"):
        return {"kind": "ready", "label": "可自助生成"}
    if not capabilities.get("new_theme_pptx") and not capabilities.get("new_theme_mp4"):
        return {"kind": "preview", "label": "仅金样预览"}

    required = [
        item
        for item in template.get("requirements") or []
        if item in RUNTIME_CAPABILITY_NAMES
    ]
    if runtime_capabilities is None:
        return {"kind": "conditional", "label": "可开始草稿 · 生成前检查环境"}
    missing = [item for item in required if not runtime_capabilities.get(item)]
    if missing:
        return {
            "kind": "conditional",
            "label": "本机缺 " + "/".join(missing) + " · 可先做草稿",
        }
    if required:
        return {"kind": "ready", "label": "本机环境通过 · 仍需内容/素材确认"}
    return {"kind": "preview", "label": "仅金样预览"}


def build_guided_portal_html(
    templates: list[dict],
    *,
    examples: dict[str, list[str]] | None = None,
    pack_date: str | None = None,
    runtime_capabilities: dict[str, bool] | None = None,
) -> str:
    pack_date = pack_date or date.today().isoformat()
    examples = examples or {}

    # Enrich catalog for JS: paragraphs + pre-rendered HTML
    enriched: list[dict] = []
    for t in templates:
        slug = t["slug"]
        paras = examples.get(slug) or []
        item = dict(t)
        item["example_paragraphs"] = paras
        item["example_html"] = paragraphs_to_html_blocks(paras)
        item["selection_command"] = build_business_command(t)
        item["readiness_badge"] = readiness_badge(t, runtime_capabilities)
        enriched.append(item)

    catalog_js = json.dumps(enriched, ensure_ascii=False)
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

.grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}}
@media (max-width: 900px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 480px) {{ .grid {{ grid-template-columns: 1fr; }} }}
.tcard {{
  appearance: none;
  width: 100%;
  padding: 0;
  text-align: left;
  font: inherit;
  color: inherit;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  background: #fafbfc;
  cursor: pointer;
  transition: border-color .12s, box-shadow .12s;
}}
.tcard:hover {{ border-color: #93c5fd; }}
.tcard:focus-visible {{ outline: 3px solid #93c5fd; outline-offset: 2px; }}
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
.readiness-badge {{
  display: inline-block;
  margin-top: 6px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #92400e;
  background: #fffbeb;
}}
.readiness-badge.preview {{ color: #475569; background: #f1f5f9; }}
.readiness-badge.ready {{ color: var(--ok); background: var(--ok-soft); }}

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

/* inline example body */
.ex-empty {{
  padding: 28px 16px;
  text-align: center;
  color: var(--dim);
  font-size: 13px;
  background: #fafbfc;
  border: 1px dashed var(--line);
  border-radius: 10px;
}}
.ex-head {{
  display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between;
  gap: 8px; margin-bottom: 10px;
}}
.ex-head strong {{ font-size: 14px; }}
.ex-head span {{ font-size: 12px; color: var(--dim); }}
.ex-body {{
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fafbfc;
  padding: 14px 16px 16px;
  max-height: 520px;
  overflow: auto;
}}
.ex-body h4 {{
  font-size: 13px;
  font-weight: 800;
  margin: 14px 0 6px;
  color: #0f172a;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--line);
}}
.ex-body h4:first-child {{ margin-top: 0; }}
.ex-body p {{
  font-size: 13px;
  color: #334155;
  margin: 0 0 8px;
  white-space: pre-wrap;
}}
.ex-body .ex-note {{
  font-size: 12px;
  color: var(--dim);
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 10px;
}}

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
    <p class="sub">商品 / 疾病内部培训课件与视频。页面只做两件事：选模板、看对应内容示例。内容在 WorkBuddy 对话里说即可。</p>
    <div class="how">
      <div>
        <b>① 看模板</b>
        按交付物查看模板，点开关键页预览与真实能力，再点「选用」
      </div>
      <div>
        <b>② 输入培训内容</b>
        回 WorkBuddy 说主题+审核要点；系统先给内容初稿和素材缺口
      </div>
      <div>
        <b>③ 下载与修改</b>
        确认后才生成；质检通过的 PPTX / MP4 在同一交付位置取件
      </div>
    </div>
  </header>

  <section class="block" id="sec-templates">
    <h2><span class="n">1</span> 模板预览与选择</h2>
    <p class="hint">点卡片看<strong>关键页面截图</strong>和真实能力。选好后下方会展示该模板的<strong>内容示例</strong>。</p>
    <div class="grid" id="template-grid"></div>

    <div class="preview-pane" id="preview-pane">
      <div class="title-row">
        <strong id="sel-name">—</strong>
        <span id="sel-meta"></span>
      </div>
      <div class="keys" id="sel-keys"></div>
      <div class="actions">
        <button type="button" class="btn ok" id="btn-use">选用此模板 · 复制口令</button>
        <button type="button" class="btn" id="btn-copy-ex">复制内容示例</button>
      </div>
      <div class="cmdbox" id="cmdbox"></div>
      <p class="toast" id="toast"></p>
    </div>
  </section>

  <section class="block" id="sec-examples">
    <h2><span class="n">2</span> 填报真实示例</h2>
    <p class="hint">随上方所选模板展示对应填写内容（结构示范）。医学与包装以贵司审核稿为准，不要照搬示例当新项目终稿。</p>
    <div id="ex-panel">
      <div class="ex-empty" id="ex-empty">请先在上方点选一个模板，这里会展示该课型的内容示例。</div>
      <div id="ex-content" class="hidden">
        <div class="ex-head">
          <strong id="ex-title">—</strong>
          <span>仅示范怎么写 · 可复制</span>
        </div>
        <div class="ex-body" id="ex-body"></div>
      </div>
    </div>
  </section>

  <footer>内部培训 · {pack_date} · 预览来自已签样金样 · 示例正文来自各模板填写参考</footer>
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

function buildCmd(t) {{
  return t.selection_command || "";
}}

function renderGrid() {{
  const grid = document.getElementById("template-grid");
  grid.innerHTML = "";
  TEMPLATES.forEach(t => {{
    const card = document.createElement("button");
    card.type = "button";
    card.className = "tcard" + (selected && selected.slug === t.slug ? " selected" : "");
    card.setAttribute("aria-pressed", selected && selected.slug === t.slug ? "true" : "false");
    card.innerHTML =
      '<img class="cover" src="' + mediaCover(t.slug) + '" alt="' + t.name_zh + '" loading="lazy" />' +
      '<div class="body">' +
      "<h3>" + t.name_zh + "</h3>" +
      '<div class="meta">' + (t.outputs || []).join(" · ") + "</div>" +
      '<span class="readiness-badge ' + (t.readiness_badge.kind || "preview") + '">' +
      (t.readiness_badge.label || "能力待确认") + "</span>" +
      "</div>";
    card.addEventListener("click", () => selectTemplate(t));
    grid.appendChild(card);
  }});
}}

function showExample(t) {{
  const empty = document.getElementById("ex-empty");
  const content = document.getElementById("ex-content");
  if (!t) {{
    empty.style.display = "block";
    content.classList.add("hidden");
    content.style.display = "none";
    return;
  }}
  empty.style.display = "none";
  content.classList.remove("hidden");
  content.style.display = "block";
  document.getElementById("ex-title").textContent = t.name_zh + " · 内容示例";
  document.getElementById("ex-body").innerHTML = t.example_html || "<p class=\\"ex-note\\">暂无示例</p>";
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
    (t.one_liner || "") + " · " + (t.status_label || "能力待确认") +
    ((t.blockers || []).length ? " · 当前缺口：" + t.blockers.join("；") : "");

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

  const box = document.getElementById("cmdbox");
  box.textContent = buildCmd(t);
  box.classList.add("show");
  document.getElementById("toast").textContent = "";
  showExample(t);
}}

document.getElementById("btn-use").addEventListener("click", async () => {{
  if (!selected) return;
  const text = buildCmd(selected);
  document.getElementById("cmdbox").textContent = text;
  document.getElementById("cmdbox").classList.add("show");
  try {{
    await navigator.clipboard.writeText(text);
    document.getElementById("toast").textContent =
      "已复制口令。回到 WorkBuddy 粘贴，把【商品名或病名】和要点改成你的内容即可。";
  }} catch (e) {{
    document.getElementById("toast").textContent = "请手动选中下方口令复制。";
  }}
}});

document.getElementById("btn-copy-ex").addEventListener("click", async () => {{
  if (!selected) return;
  const paras = selected.example_paragraphs || [];
  const text = paras.join("\\n");
  try {{
    await navigator.clipboard.writeText(text);
    document.getElementById("toast").textContent = "内容示例已复制到剪贴板。";
  }} catch (e) {{
    document.getElementById("toast").textContent = "复制失败，请在下方示例区手动选择复制。";
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
if (selected) selectTemplate(selected);
else showExample(null);
</script>
</body>
</html>
"""


def write_upload_folder_readme(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# 可选 · 文件投递箱

主流程请在 **WorkBuddy 聊天** 直接说内容 / 发附件。

本目录仅备用：若要把已填 Word 或授权图放进仓库，可放入 `待处理/`。
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    print("business_guided_portal: import build_guided_portal_html / extract_docx_paragraphs")
