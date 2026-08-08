#!/usr/bin/env python3
"""Scaffold 九宫格合规版（无医疗内容）delivery package.

Mode: jiugongge-health-edu-compliance-v1
60s / 6×10s / 1+1+3+1 · Xiaolin + audience · English grid+video prompts.

Usage:
  python3 scripts/scaffold_jiugongge_health_edu_compliance.py \\
    --vars production-library/templates/prompt-modes/jiugongge-health-edu-compliance-v1/example-告别办公久坐僵硬.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODE_DIR = (
    ROOT / "production-library/templates/prompt-modes/jiugongge-health-edu-compliance-v1"
)
DEFAULT_OUT = ROOT / "outputs/business-video-runs/jiugongge-health-edu-compliance"

STYLE_MAP = {
    "3D动画": "3D Pixar style",
    "极简扁平": "Minimalist 2D vector flat illustration",
    "国风水墨": "Soft Chinese Ink Wash painting style",
    "治愈水彩": "Healing watercolor hand-drawn style",
    "中老年": "3D Pixar style",
    "职场人": "Minimalist 2D vector flat illustration",
    "宝妈": "Healing watercolor hand-drawn style",
}

PINNED = (
    "本内容由 AI 辅助生成，仅为生活习惯与经验分享，非医疗建议，"
    "不能替代执业医师诊断或治疗。如有不适请及时前往正规医疗机构。"
)

# Soft scan for agent self-check notes in DELIVERY
BANNED_HINTS = [
    "医生", "白大褂", "护士", "医院", "诊室", "听诊器", "血压计", "药瓶",
    "注射器", "手术刀", "预防", "治疗", "缓解", "药效", "临床", "发病率",
]


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", s)
    return s[:48] or "theme"


def g(d: dict, *keys: str, default: str = "") -> str:
    cur: object = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return str(cur) if cur is not None else default


def resolve_style(v: dict) -> str:
    if g(v, "style_en"):
        return g(v, "style_en")
    key = g(v, "style_key") or g(v, "audience")
    return STYLE_MAP.get(key, "3D Pixar style")


def expand_habits(points: list[str]) -> tuple[str, list[str]]:
    """Return (habit_intro for seg2, three dry goods for seg 3-5)."""
    pts = [p.strip() for p in points if str(p).strip()]
    if not pts:
        pts = ["先扶稳再活动", "慢慢来不逞能", "和家人一起养成小习惯"]
    intro = "先别硬撑，咱们从最小的一步开始"
    if len(pts) == 1:
        return intro, [pts[0], "动作时手扶稳桌子或坐稳椅子", "做完喝口水歇一歇"]
    if len(pts) == 2:
        return intro, [pts[0], pts[1], "每天固定一个小时间做，别一次做满"]
    return intro, pts[:3]


def nine_grid_en(style: str, cells: list[str]) -> str:
    assert len(cells) == 9
    parts = [f"3x3 grid, {style}:"]
    for i, c in enumerate(cells, 1):
        parts.append(f"{i}. {c}")
    return " ".join(parts)


def build_segments(v: dict) -> list[dict]:
    style = resolve_style(v)
    theme = g(v, "theme")
    env = g(
        v,
        "environment_en",
        default="cozy everyday home interior, warm light, no medical elements",
    )
    outfit = g(v, "xiaolin_outfit_en", default="casual home clothes, green crossbody bag")
    aud = v.get("audience_character") or {}
    aud_desc = g(aud, "age_gender_en", default="a friendly Chinese elder")
    aud_outfit = g(aud, "outfit_en", default="comfortable casual clothes")
    end_text = g(v, "ending_chinese_text", default="咱公园见！")
    ar = g(v, "aspect_ratio", default="9:16")
    intro_habit, dry = expand_habits(list(v.get("habit_points") or []))
    h1, h2, h3 = dry[0], dry[1], dry[2]

    consist = (
        f"Xiaolin: short black hair, green crossbody bag, {outfit}. "
        f"Audience: {aud_desc}, {aud_outfit}. Consistent faces. "
        f"NO doctors, NO white coats, NO medical tools, NO hospital."
    )
    safe = "one hand holding a stable table or wall for support, or sitting on a sturdy chair"

    segs: list[dict] = []

    # 1 pain
    segs.append(
        {
            "id": 1,
            "range": "0-10s",
            "module": "痛点引入",
            "grid": nine_grid_en(
                style,
                [
                    f'Wide home shot, Xiaolin frowning slightly looking at camera, Chinese text "家人们"',
                    f"Audience character slumped shoulders, anxious face, looking down, {env}",
                    "Close-up of tight shoulders cartoon gesture without medical symbols",
                    "Xiaolin walks closer with caring expression, green bag visible",
                    f"Emotional peak: audience holds neck gently while {safe}",
                    "Soft light through window, warm but tense mood",
                    "Xiaolin points gently to everyday lifestyle icon (not medical)",
                    "Audience nods slowly, still worried",
                    f'Both in frame, Chinese text "先别慌"',
                ],
            ),
            "video": (
                f"{style} animation, vertical {ar}, 10 seconds. {consist} "
                f"Opening: Xiaolin and audience in {env}. Audience anxious, head down, frowning. "
                f"Xiaolin greets warmly about daily habit topic 「{theme}」. Soft cinematic lighting. "
                f"NO medical tools. NO share buttons."
            ),
            "narration": (
                f"家人们，您是不是也遇到过：跟「{theme}」相关的小烦恼？"
                f"今天咱不吓人，就用大白话聊聊生活里能慢慢改的小习惯。"
            ),
        }
    )

    # 2 intro habit
    segs.append(
        {
            "id": 2,
            "range": "11-20s",
            "module": "习惯对照开场",
            "grid": nine_grid_en(
                style,
                [
                    f'Xiaolin holds up a simple note card, Chinese text "小习惯"',
                    f"Audience sits on sturdy chair, {safe}",
                    "Split mood: rushed wrong way vs calm right way (lifestyle only)",
                    "Xiaolin demonstrates slow breathing, smiling gently",
                    f"Key beat: start of method — {intro_habit}",
                    "Props: water cup, sturdy chair, soft mat — no medical devices",
                    "Audience mirrors carefully with hand on table",
                    "Xiaolin gives approving nod",
                    f'Chinese text "慢慢来"',
                ],
            ),
            "video": (
                f"{style} animation, vertical {ar}, 10s. {consist} "
                f"Xiaolin introduces the first gentle lifestyle approach: {intro_habit}. "
                f"Audience {safe}. Environment: {env}. NO medical tools."
            ),
            "narration": (
                f"别着急，咱们先定个心：{intro_habit}。"
                f"记住，活动的时候手扶稳桌子或坐稳椅子，稳当最重要。"
            ),
        }
    )

    # 3-5 dry goods
    for sid, rng, habit in ((3, "21-30s", h1), (4, "31-40s", h2), (5, "41-50s", h3)):
        segs.append(
            {
                "id": sid,
                "range": rng,
                "module": f"干货 · {habit[:18]}",
                "grid": nine_grid_en(
                    style,
                    [
                        f'Xiaolin points to lifestyle cue, Chinese text "习惯{sid-2}"',
                        f"Audience prepares, {safe}",
                        f"Clear demonstration of: {habit}",
                        "Slow motion friendly exaggeration, no medical glow organs",
                        f"Peak frame: best angle of the habit, {safe}",
                        "Xiaolin coaches with open palm, neighbor tone",
                        "Audience succeeds with relaxed shoulders",
                        "Everyday prop focus (cup / window / chair / hat)",
                        f'Chinese text "稳住"',
                    ],
                ),
                "video": (
                    f"{style} animation, vertical {ar}, 10s. {consist} "
                    f"Demonstrate habit: {habit}. Characters {safe}. "
                    f"Environment {env}. NO medical tools, NO clinical terms on screen."
                ),
                "narration": (
                    f"再教您一招：{habit}。"
                    f"咱不赶时间，您跟着感觉走，扶稳了再动。"
                ),
            }
        )

    # 6 warm end
    segs.append(
        {
            "id": 6,
            "range": "51-60s",
            "module": "温馨收束 · 软CTA",
            "grid": nine_grid_en(
                style,
                [
                    "Audience looks up, relaxed smile, shoulders open",
                    "Xiaolin thumbs-up neighbor style (no medical badge)",
                    f"Park or window daylight, soft warm atmosphere, {env}",
                    "Lifestyle icons float: walking, water, rest — not pills",
                    "Both characters side by side smiling to camera",
                    "Xiaolin holds sun hat or looks toward park outside",
                    "No share icons, no click buttons, no UI overlays",
                    "Gentle camera push-in, golden soft light",
                    f'Chinese text "{end_text}"',
                ],
            ),
            "video": (
                f"{style} animation, vertical {ar}, 10s. {consist} "
                f"Warm ending: characters smile, head up, relaxed. Soft daylight. "
                f"Emotional Chinese text 「{end_text}」 in scene. "
                f"NO share/forward/click icons. NO medical tools. Altruistic neighbor vibe."
            ),
            "narration": (
                f"家人们，这些都是居家小习惯，您觉得有用就跟身边人叨叨一声。"
                f"{end_text}咱们下回聊。"
            ),
        }
    )
    return segs


def render_assets_md(v: dict) -> str:
    style = resolve_style(v)
    outfit = g(v, "xiaolin_outfit_en", default="casual clothes, green crossbody bag")
    aud = v.get("audience_character") or {}
    env = g(v, "environment_en", default="cozy home, no medical elements")
    return "\n".join(
        [
            f"# 视觉资产提示词 · {g(v, 'theme')}",
            "",
            f"**模式：** jiugongge-health-edu-compliance-v1  ",
            f"**Style：** {style}",
            "",
            "## 小林 Character Sheet (English · 复制)",
            "",
            "```",
            f"Character sheet, {style}, a cheerful 28-year-old Chinese man named Xiaolin, "
            f"{outfit}, green crossbody bag, short black hair, T-pose, front/side/back views, "
            f"white background, high-quality 3D/2D render, no medical clothing, no stethoscope.",
            "```",
            "",
            "## 受众角色 Character Sheet (English · 复制)",
            "",
            "```",
            f"Character sheet, {style}, {g(aud, 'age_gender_en', default='friendly Chinese audience character')}, "
            f"{g(aud, 'outfit_en', default='theme-matching casual outfit')}, neutral pose, "
            f"front/side/back views, white background, high-quality 3D/2D render, no medical clothing, no hospital.",
            "```",
            "",
            "## 主题场景 Environment (English · 复制)",
            "",
            "```",
            f"Environment render, {style}, {env}, cinematic lighting, detailed textures, "
            f"warm atmosphere, no medical elements, no hospital, no clinic.",
            "```",
            "",
        ]
    )


def render_review_md(v: dict, segs: list[dict]) -> str:
    lines = [
        f"# 合规版脚本复核包 · {g(v, 'theme')}",
        "",
        f"**模式：** jiugongge-health-edu-compliance-v1（无医疗内容）  ",
        f"**受众：** {g(v, 'audience')}  ",
        f"**日期：** {date.today().isoformat()}  ",
        f"**状态：** 待业务确认",
        "",
        "## 合规脱敏说明",
        "",
        g(v, "compliance_transform") or "（请确认主题已转为生活习惯/情绪调节/环境安全）",
        "",
        f"**原始输入（仅留痕）：** {g(v, 'theme_raw') or '—'}",
        "",
        "## 习惯点",
        "",
    ]
    for i, p in enumerate(list(v.get("habit_points") or []), 1):
        lines.append(f"{i}. {p}")
    lines += ["", "## 六段口播", ""]
    for s in segs:
        lines += [
            f"### 片段 {s['id']}（{s['range']}）· {s['module']}",
            "",
            s["narration"],
            "",
        ]
    lines += [
        "## 确认区",
        "",
        "确认句：`脚本通过。可以出九宫格合规版提示词。`",
        "",
        "红线自检：无医生/白大褂/医院/诊室/器材 □　无预防治疗缓解病名 □　软CTA无分享图标 □",
        "",
    ]
    return "\n".join(lines)


def render_prompts_md(v: dict, segs: list[dict]) -> str:
    lines = [
        f"# 九宫格 + 视频提示词（合规版）· {g(v, 'theme')}",
        "",
        "顺序：① 角色/场景资产 → ② 每段九宫格出图 → ③ 10s 视频 → ④ 拼接 + 发布包。",
        "",
        f"**Style：** {resolve_style(v)} · **画幅：** {g(v, 'aspect_ratio', default='9:16')}",
        "",
    ]
    for s in segs:
        lines += [
            "---",
            "",
            f"## 片段 {s['id']}（{s['range']}）· {s['module']}",
            "",
            "### 九宫格提示词 (English · 复制)",
            "",
            "```",
            s["grid"],
            "```",
            "",
            "### 视频提示词 (English · 复制)",
            "",
            "```",
            s["video"],
            "```",
            "",
            "### 口播语音",
            "",
            s["narration"],
            "",
        ]
    return "\n".join(lines)


def render_publish_md(v: dict) -> str:
    pub = v.get("publish") or {}
    theme = g(v, "theme")
    title = g(pub, "title") or f"家人们｜{theme}"
    body = g(pub, "body") or (
        f"今天聊聊「{theme}」。都是居家小习惯，纯生活经验分享，非医疗建议。"
    )
    tags = pub.get("hashtags") or ["生活习惯", "居家小妙招", "家庭生活", "咱公园见"]
    tag_line = " ".join("#" + t.lstrip("#") for t in tags)
    end_text = g(v, "ending_chinese_text", default="咱公园见！")
    return "\n".join(
        [
            f"# 视频号发布全家桶（合规版）· {theme}",
            "",
            "## 1. 发布文案",
            "",
            f"**标题：** {title}",
            "",
            f"**正文：**",
            "",
            body,
            "",
            f"**标签：** {tag_line}",
            "",
            "## 2. 置顶评论",
            "",
            PINNED,
            "",
            "## 3. 定向转发语（3 条）",
            "",
            f"1. **给老伴：** 老伴你看这条，讲的是居家小习惯，我俩慢慢试试，不吓人。",
            f"2. **给子女：** 孩子，这条是生活经验分享，你们上班也用得上，有空看看。",
            f"3. **给老友：** 老友，这条聊「{theme}」，邻里聊天的劲儿，转你瞅瞅。",
            "",
            f"## 4. 片尾情感文案（画面用 · 禁止分享按钮）",
            "",
            f"Chinese text \"{end_text}\"",
            "",
            "## 5. 平台提醒",
            "",
            "- 勾选 AI 生成/辅助创作（按平台规则）",
            "- 纯生活经验分享，非医疗建议",
            "- 画面禁止转发/点击/分享 UI 图标",
            "",
        ]
    )


def render_delivery(v: dict, out: Path) -> str:
    return "\n".join(
        [
            f"# DELIVERY · {g(v, 'theme')}",
            "",
            f"- **模式 ID：** `jiugongge-health-edu-compliance-v1`",
            f"- **并列原版：** `jiugongge-health-edu-v1`（林医生，非本包）",
            f"- **日期：** {date.today().isoformat()}",
            f"- **目录：** `{out}`",
            "",
            "| 文件 | 用途 |",
            "|------|------|",
            "| `00-主题变量.json` | 留痕 |",
            "| `01-合规脚本复核包.md` | 先审口播+脱敏 |",
            "| `02-视觉资产提示词.md` | 三视图+场景 |",
            "| `03-九宫格与视频提示词-六段.md` | 复制终稿 |",
            "| `04-视频号发布全家桶.md` | 发布/置顶/转发 |",
            "",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vars", required=True)
    ap.add_argument("--slug", default="")
    ap.add_argument("--out-root", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    path = Path(args.vars).expanduser().resolve()
    v = json.loads(path.read_text(encoding="utf-8"))
    if not g(v, "theme"):
        raise SystemExit("theme required")
    if not v.get("habit_points"):
        raise SystemExit("habit_points (1-3) required")

    slug = args.slug or slugify(g(v, "theme"))
    out = Path(args.out_root).expanduser().resolve() / slug
    out.mkdir(parents=True, exist_ok=True)

    segs = build_segments(v)
    (out / "00-主题变量.json").write_text(
        json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "01-合规脚本复核包.md").write_text(render_review_md(v, segs), encoding="utf-8")
    (out / "02-视觉资产提示词.md").write_text(render_assets_md(v), encoding="utf-8")
    (out / "03-九宫格与视频提示词-六段.md").write_text(
        render_prompts_md(v, segs), encoding="utf-8"
    )
    (out / "04-视频号发布全家桶.md").write_text(render_publish_md(v), encoding="utf-8")
    (out / "DELIVERY.md").write_text(render_delivery(v, out), encoding="utf-8")

    print(f"OK compliance scaffold → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
