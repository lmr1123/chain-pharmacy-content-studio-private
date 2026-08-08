#!/usr/bin/env python3
"""Scaffold Seedance health-edu delivery package from filled variables JSON.

Does not call any paid video API. Produces review pack + segmented prompts
for copy-paste into Seedance 2.0 / Jimeng.

Usage:
  python3 scripts/scaffold_seedance_health_edu.py \\
    --vars production-library/templates/prompt-modes/seedance-health-edu-v1/example-暴雨避险.json

  python3 scripts/scaffold_seedance_health_edu.py --vars path/to/vars.json --slug baoyu-bixian
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODE_DIR = ROOT / "production-library/templates/prompt-modes/seedance-health-edu-v1"
DEFAULT_OUT = ROOT / "outputs/business-video-runs/seedance-health-edu"
DISCLAIMER = (
    "⚠️ AI 生成技术辅助创作。本视频仅供生活常识分享，"
    "非专业医疗或应急决策建议。平安第一。"
)


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


def global_anchor(v: dict) -> str:
    ca = v.get("character_a") or {}
    cb = v.get("character_b") or {}
    ar = v.get("aspect_ratio") or "9:16"
    return (
        f"{'竖屏' if ar == '9:16' else '横屏'} {ar}，3D Pixar 电影级画质，8K，"
        f"{g(v, 'tone_lighting', default='明亮自然光影')}。"
        f"角色 A：{g(ca, 'age_gender')}，身着 {g(ca, 'outfit_color_block')}，"
        f"表情亲切，打破第四面墙看向镜头。"
        f"角色 B：{g(cb, 'age_gender')}，身着 {g(cb, 'outfit_color_block')}。"
        f"主场景：{g(v, 'core_scene')}。"
        f"强调物理质感：{g(v, 'physical_particles')}。"
        "合规：严禁白大褂、医疗器材、专业病理术语；仅生活习惯、环境安全、情绪调节表达。"
        "禁止：水印、字幕、跳切、2D 动漫感、文字 logo、写实医疗器械。"
    )


def build_segments(v: dict) -> list[dict]:
    sec = int(v.get("segment_seconds") or 12)
    sec = max(4, min(15, sec))
    h, s, d, e, w = (
        v.get("hook") or {},
        v.get("solution") or {},
        v.get("deep_dive") or {},
        v.get("extreme") or {},
        v.get("wrapup") or {},
    )
    return [
        {
            "id": 1,
            "title": "反差感·痛点切入",
            "seconds": sec,
            "body": (
                f"镜头从{g(h, 'core_env_element')}特写切入，紧迫混乱感。"
                f"角色 A 出现在画面一侧，手指向身后{g(h, 'pain_visual')}。"
                f"物理：{g(h, 'pain_physics')}。"
                f"口播：「家人们，{g(h, 'core_pain_phrase')}这种事儿，咱真不能硬冲！"
                f"看着这{g(h, 'env_state_phrase')}，咱心里准在打鼓吧？」"
            ),
            "tail": "定格在角色 A 看镜头、身后痛点仍在发生的画面。",
        },
        {
            "id": 2,
            "title": "秩序感·干货演播",
            "seconds": sec,
            "body": (
                f"背景虚化，角色 A 举起{g(s, 'medium')}，"
                f"空中浮现{g(s, 'level_icons')}，动态变色脉动。"
                f"角色 B 停下错误动作转为观察。"
                f"物理：屏幕高光折射，图标微弱震动。"
                f"口播：「别慌！认准这份指引：{g(s, 'level_a')}咱就按兵不动；"
                f"{g(s, 'level_b')}咱就稳坐泰山。安全第一，这才是聪明人的做法！」"
            ),
            "tail": "角色 A 收起媒介，表情笃定，指引图标缓缓淡出。",
        },
        {
            "id": 3,
            "title": "沉浸式·细节避险",
            "seconds": sec,
            "body": (
                f"场景切换至{g(d, 'high_risk_env')}。"
                f"角色 A 指导角色 B 演示关键动作；镜头聚焦{g(d, 'key_body_focus')}。"
                f"物理：{g(d, 'material_interaction')}。"
                f"口播：「尤其是这种时候，{g(d, 'hazard_a')}和{g(d, 'hazard_b')}咱得绕着走！"
                f"记住，{g(d, 'relief_info')}，咱求的就是个踏实。」"
            ),
            "tail": "正确动作完成，两人站稳，环境危险仍在背景。",
        },
        {
            "id": 4,
            "title": "避险常识·扩展场景",
            "seconds": sec,
            "body": (
                f"镜头拉远至{g(e, 'special_scene')}，展示{g(e, 'extreme_situation')}。"
                f"演示逃生：{g(e, 'escape_path')}。"
                f"物理：{g(e, 'extreme_physics')}。"
                f"口播：「万一在野外碰上{g(e, 'danger_name')}，千万别顺着跑！"
                f"要往{g(e, 'correct_direction')}撤。这可是咱全家的保命智慧！」"
            ),
            "tail": "两人到达相对安全的高处/安全区，回望风险区。",
        },
        {
            "id": 5,
            "title": "利他性·情感结尾",
            "seconds": sec,
            "body": (
                f"阴霾散去，阳光穿透云层（上帝光）。"
                f"两名主角在{g(w, 'safe_env', default='安全温馨环境')}并排，"
                f"看向镜头温暖微笑并挥手。"
                f"画面中心升起 3D 艺术字：「{g(w, 'art_text', default='平安是福')}」。"
                f"物理：丁达尔效应，发丝金色光晕。"
                f"口播：「日子要过，安全要火。这份指引，赶紧转给咱身边的"
                f"{g(v, 'target_audience')}。"
                f"{g(w, 'season_line', default='平安过春天，咱公园见！')}」"
            ),
            "tail": "艺术字与笑容定格，暖光收束。",
        },
    ]


def render_review_md(v: dict, segments: list[dict]) -> str:
    lines = [
        f"# 科普脚本复核包 · {g(v, 'theme')}",
        "",
        f"**模式：** seedance-health-edu-v1  ",
        f"**目标人群：** {g(v, 'target_audience')}  ",
        f"**日期：** {date.today().isoformat()}  ",
        f"**状态：** 待业务确认",
        "",
        "## 视觉锚定",
        "",
        f"- 色调：{g(v, 'tone_lighting')}",
        f"- 物理：{g(v, 'physical_particles')}",
        f"- 角色 A：{g(v.get('character_a') or {}, 'age_gender')} / {g(v.get('character_a') or {}, 'outfit_color_block')}",
        f"- 角色 B：{g(v.get('character_b') or {}, 'age_gender')} / {g(v.get('character_b') or {}, 'outfit_color_block')}",
        f"- 主场景：{g(v, 'core_scene')}",
        "",
        "合规：无白大褂 / 无医疗器材 / 无病理术语 / 生活常识表达",
        "",
        "## 五拍剧本",
        "",
    ]
    for seg in segments:
        lines += [
            f"### 第 {seg['id']} 拍 · {seg['title']}",
            "",
            seg["body"],
            "",
            f"*建议时长：{seg['seconds']}s*",
            "",
        ]
    pub = v.get("publish") or {}
    title = (
        f"{g(pub, 'emotion_word')}{g(pub, 'subject')}｜{g(pub, 'crowd_tag')}"
        f"{g(pub, 'emoji', default='')}"
    )
    lines += [
        "## 发布草案",
        "",
        f"- 标题：{title}",
        f"- 免责：{DISCLAIMER}",
        f"- 转发：{g(pub, 'forward_text')}",
        "",
        "## 确认区",
        "",
        "业务确认句示例：`脚本通过。可以出 Seedance 提示词。`",
        "",
    ]
    return "\n".join(lines)


def render_prompts_md(v: dict, segments: list[dict]) -> str:
    anchor = global_anchor(v)
    lines = [
        f"# Seedance 2.0 分段提示词 · {g(v, 'theme')}",
        "",
        "每段单独复制到即梦 / Seedance 2.0。单段 ≤15 秒。",
        "第 2 段起可用「视频延长」：上传上一段为 @视频1。",
        "",
        f"**比例：** {v.get('aspect_ratio') or '9:16'}  ",
        f"**风格锚：** 3D Pixar · 角色服装色块锁定",
        "",
    ]
    for i, seg in enumerate(segments):
        lines += [
            "---",
            "",
            f"## 第 {seg['id']} 段 · {seg['title']}（{seg['seconds']} 秒）",
            "",
        ]
        if i == 0:
            lines += [
                "**操作：** 纯文本生成（或全能参考，勿上传写实真人脸）",
                "",
                "### 提示词（复制区）",
                "",
                "```",
                f"{anchor}",
                f"{seg['body']}",
                f"镜头流畅电影感，一镜或软过渡，无硬切花字。时长约 {seg['seconds']} 秒。",
                f"结尾画面：{seg['tail']}",
                "```",
            ]
        else:
            lines += [
                "**操作（延长）：** 将上一段成片上传为 @视频1，生成时长选本段秒数",
                "",
                "### 提示词（复制区）",
                "",
                "```",
                f"将@视频1延长{seg['seconds']}秒。保持同一角色服装色块与 3D Pixar 画质。",
                f"{anchor}",
                f"{seg['body']}",
                f"与上段自然衔接。结尾画面：{seg['tail']}",
                "```",
                "",
                "### 备选（独立生成，后期剪辑）",
                "",
                "```",
                f"{anchor}",
                f"{seg['body']}",
                f"时长约 {seg['seconds']} 秒。结尾：{seg['tail']}",
                "```",
            ]
        lines += [
            "",
            f"**衔接点：** {seg['tail']}",
            "",
        ]
    return "\n".join(lines)


def render_publish_md(v: dict) -> str:
    pub = v.get("publish") or {}
    title = (
        f"{g(pub, 'emotion_word')}{g(pub, 'subject')}｜{g(pub, 'crowd_tag')}"
        f"{g(pub, 'emoji', default='')}"
    )
    return "\n".join(
        [
            f"# 视频号发布全家桶 · {g(v, 'theme')}",
            "",
            "## 标题",
            "",
            title,
            "",
            "## 免责置顶（建议置顶评论或简介首行）",
            "",
            DISCLAIMER,
            "",
            "## 利他转发语",
            "",
            g(pub, "forward_text")
            or f"@家人，这条关于「{g(v, 'theme')}」讲得很清楚，花 1 分钟看看。",
            "",
            "## 话题建议（可选）",
            "",
            f"#{g(pub, 'subject') or g(v, 'theme')} #生活常识 #平安是福",
            "",
        ]
    )


def render_delivery_md(v: dict, out_dir: Path) -> str:
    return "\n".join(
        [
            f"# DELIVERY · {g(v, 'theme')}",
            "",
            f"- **模式 ID：** `seedance-health-edu-v1`",
            f"- **日期：** {date.today().isoformat()}",
            f"- **目录：** `{out_dir}`",
            "",
            "## 文件",
            "",
            "| 文件 | 用途 |",
            "|------|------|",
            "| `00-主题变量.json` | 变量留痕 |",
            "| `01-科普脚本复核包.md` | 业务审稿 |",
            "| `02-Seedance提示词-分段.md` | **复制到 Seedance** |",
            "| `03-视频号发布全家桶.md` | 标题/免责/转发 |",
            "",
            "## 使用",
            "",
            "1. 业务确认 `01` 后使用 `02` 逐段复制到即梦 / Seedance 2.0。",
            "2. 发布时贴上 `03` 免责与转发语。",
            "3. 本包不含本机培训 MP4；与疾病科普 Remotion 线无关。",
            "",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold Seedance health-edu package")
    ap.add_argument("--vars", required=True, help="Path to filled variables JSON")
    ap.add_argument("--slug", default="", help="Output folder slug")
    ap.add_argument(
        "--out-root",
        default=str(DEFAULT_OUT),
        help="Output root directory",
    )
    args = ap.parse_args()

    vars_path = Path(args.vars).expanduser().resolve()
    if not vars_path.is_file():
        raise SystemExit(f"vars not found: {vars_path}")

    v = json.loads(vars_path.read_text(encoding="utf-8"))
    if not g(v, "theme"):
        raise SystemExit("vars.theme is required")

    slug = args.slug or slugify(g(v, "theme"))
    out_dir = Path(args.out_root).expanduser().resolve() / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    segments = build_segments(v)
    (out_dir / "00-主题变量.json").write_text(
        json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "01-科普脚本复核包.md").write_text(
        render_review_md(v, segments), encoding="utf-8"
    )
    (out_dir / "02-Seedance提示词-分段.md").write_text(
        render_prompts_md(v, segments), encoding="utf-8"
    )
    (out_dir / "03-视频号发布全家桶.md").write_text(
        render_publish_md(v), encoding="utf-8"
    )
    (out_dir / "DELIVERY.md").write_text(
        render_delivery_md(v, out_dir), encoding="utf-8"
    )

    # pointer to meta-prompt
    meta = MODE_DIR / "meta-prompt.md"
    if meta.is_file():
        (out_dir / "README-模式说明.txt").write_text(
            f"模式资产: {meta}\n总规: docs/seedance-health-edu-video-mode.md\n",
            encoding="utf-8",
        )

    print(f"OK scaffold → {out_dir}")
    print("  01-科普脚本复核包.md")
    print("  02-Seedance提示词-分段.md")
    print("  03-视频号发布全家桶.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
