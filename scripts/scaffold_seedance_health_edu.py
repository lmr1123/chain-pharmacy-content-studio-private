#!/usr/bin/env python3
"""Scaffold Seedance health-edu delivery package from filled variables JSON.

Does not call any paid video API. Default output is review-only. Segmented
prompts and the publish pack require an explicit hash-bound approval release.

Usage:
  python3 scripts/scaffold_seedance_health_edu.py \\
    --vars production-library/templates/prompt-modes/seedance-health-edu-v1/example-暴雨避险.json

  python3 scripts/scaffold_seedance_health_edu.py --vars path/to/vars.json --slug baoyu-bixian
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODE_DIR = ROOT / "production-library/templates/prompt-modes/seedance-health-edu-v1"
DEFAULT_OUT = ROOT / "outputs/business-video-runs/seedance-health-edu"
MODE_ID = "seedance-health-edu-v1"
DISCLAIMER = (
    "⚠️ AI 生成技术辅助创作。本视频仅供生活常识分享，"
    "非专业医疗或应急决策建议。平安第一。"
)

RELEASE_FILES = [
    "02-Seedance提示词-分段.md",
    "03-视频号发布全家桶.md",
    "DELIVERY.md",
    "release-manifest.json",
]

RELEASE_REQUIRED_FIELDS = [
    (("theme",), "theme（主题）"),
    (("target_audience",), "target_audience（目标人群）"),
    (("core_pain",), "core_pain（核心痛点）"),
    (("character_a", "age_gender"), "character_a.age_gender（角色 A 年龄/性别）"),
    (
        ("character_a", "outfit_color_block"),
        "character_a.outfit_color_block（角色 A 固定服装色块）",
    ),
    (("character_b", "age_gender"), "character_b.age_gender（角色 B 年龄/性别）"),
    (
        ("character_b", "outfit_color_block"),
        "character_b.outfit_color_block（角色 B 固定服装色块）",
    ),
    (("core_scene",), "core_scene（主场景）"),
    (("hook", "core_env_element"), "hook.core_env_element（开场环境元素）"),
    (("hook", "pain_visual"), "hook.pain_visual（痛点画面）"),
    (("hook", "pain_physics"), "hook.pain_physics（痛点物理表现）"),
    (("hook", "env_state_phrase"), "hook.env_state_phrase（环境状态口播）"),
    (("solution", "medium"), "solution.medium（交互媒介）"),
    (("solution", "level_icons"), "solution.level_icons（等级图标）"),
    (("solution", "level_a"), "solution.level_a（等级 A 口径）"),
    (("solution", "level_b"), "solution.level_b（等级 B 口径）"),
    (("deep_dive", "high_risk_env"), "deep_dive.high_risk_env（高风险环境）"),
    (("deep_dive", "key_body_focus"), "deep_dive.key_body_focus（关键动作）"),
    (
        ("deep_dive", "material_interaction"),
        "deep_dive.material_interaction（材质交互）",
    ),
    (("deep_dive", "hazard_a"), "deep_dive.hazard_a（危险物 A）"),
    (("deep_dive", "hazard_b"), "deep_dive.hazard_b（危险物 B）"),
    (("deep_dive", "relief_info"), "deep_dive.relief_info（生活向免责/利好信息）"),
    (("extreme", "special_scene"), "extreme.special_scene（扩展场景）"),
    (("extreme", "extreme_situation"), "extreme.extreme_situation（扩展险情）"),
    (("extreme", "escape_path"), "extreme.escape_path（正确行动路径）"),
    (("extreme", "extreme_physics"), "extreme.extreme_physics（物理表现）"),
    (("extreme", "danger_name"), "extreme.danger_name（险情名称）"),
    (("extreme", "correct_direction"), "extreme.correct_direction（正确方向）"),
    (("wrapup", "safe_env"), "wrapup.safe_env（安全收束环境）"),
    (("publish", "emotion_word"), "publish.emotion_word（标题情绪词）"),
    (("publish", "subject"), "publish.subject（发布主题）"),
    (("publish", "crowd_tag"), "publish.crowd_tag（人群标签）"),
    (("publish", "forward_text"), "publish.forward_text（定向转发语）"),
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


def missing_release_fields(v: dict) -> list[str]:
    return [
        label
        for keys, label in RELEASE_REQUIRED_FIELDS
        if not g(v, *keys).strip()
    ]


def input_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def approval_template(digest: str, review_digest: str) -> dict:
    return {
        "schema": "prompt-release-approval-v1",
        "mode_id": MODE_ID,
        "approved": False,
        "approved_by": "",
        "input_sha256": digest,
        "review_sha256": review_digest,
        "note": "确认 01-科普脚本复核包后，将 approved 改为 true 并填写 approved_by。",
    }


def require_release_approval(path: Path, digest: str, review_digest: str) -> dict:
    if not path.is_file():
        raise SystemExit(f"approval file not found: {path}")
    approval = json.loads(path.read_text(encoding="utf-8"))
    if approval.get("mode_id") != MODE_ID:
        raise SystemExit(f"approval.mode_id must be {MODE_ID}")
    if approval.get("approved") is not True:
        raise SystemExit("approval.approved must be true")
    if not str(approval.get("approved_by") or "").strip():
        raise SystemExit("approval.approved_by is required")
    if approval.get("input_sha256") != digest:
        raise SystemExit("approval input hash mismatch; regenerate review and approve again")
    if approval.get("review_sha256") != review_digest:
        raise SystemExit("approval review hash mismatch; regenerate review and approve again")
    return approval


def write_release_manifest(
    out_dir: Path,
    digest: str,
    review_digest: str,
    approval_path: Path,
    approval: dict,
) -> None:
    manifest = {
        "schema": "prompt-release-v1",
        "mode_id": MODE_ID,
        "input_sha256": digest,
        "review_sha256": review_digest,
        "approved_by": approval["approved_by"],
        "approval_file": str(approval_path),
        "released_on": date.today().isoformat(),
        "files": RELEASE_FILES[:-1],
    }
    (out_dir / "release-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
        f"强调物理质感：{g(v, 'physical_particles', default='环境粒子与材质交互')}。"
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
    core_pain = g(v, "core_pain") or g(h, "core_pain_phrase")
    return [
        {
            "id": 1,
            "title": "反差感·痛点切入",
            "seconds": sec,
            "body": (
                f"镜头从{g(h, 'core_env_element')}特写切入，紧迫混乱感。"
                f"角色 A 出现在画面一侧，手指向身后{g(h, 'pain_visual')}。"
                f"物理：{g(h, 'pain_physics')}。"
                f"口播：「家人们，{core_pain}这种事儿，咱真不能硬冲！"
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


def render_review_md(v: dict, segments: list[dict], missing_fields: list[str]) -> str:
    is_draft = bool(missing_fields)
    lines = [
        f"# 科普脚本复核包 · {g(v, 'theme') or '待补主题'}",
        "",
        f"**模式：** seedance-health-edu-v1  ",
        f"**目标人群：** {g(v, 'target_audience') or '待补'}  ",
        f"**日期：** {date.today().isoformat()}  ",
        f"**状态：** {'草稿·待补字段' if is_draft else '待业务确认'}",
        "",
    ]
    if missing_fields:
        lines += [
            "## 待补字段（正式发布前必须补齐）",
            "",
            *[f"- {field}" for field in missing_fields],
            "",
            "当前仅生成结构草稿，不生成含空槽的五拍伪成稿。补齐后重新运行即可复核完整脚本。",
            "",
        ]
    lines += [
        "## 视觉锚定",
        "",
        f"- 色调：{g(v, 'tone_lighting', default='明亮自然光影')}",
        f"- 物理：{g(v, 'physical_particles', default='环境粒子与材质交互')}",
        f"- 角色 A：{g(v.get('character_a') or {}, 'age_gender') or '待补'} / {g(v.get('character_a') or {}, 'outfit_color_block') or '待补'}",
        f"- 角色 B：{g(v.get('character_b') or {}, 'age_gender') or '待补'} / {g(v.get('character_b') or {}, 'outfit_color_block') or '待补'}",
        f"- 主场景：{g(v, 'core_scene') or '待补'}",
        "",
        "合规：无白大褂 / 无医疗器材 / 无病理术语 / 生活常识表达",
        "",
        "## 五拍剧本" if not is_draft else "## 五拍结构草稿",
        "",
    ]
    if is_draft:
        for seg in segments:
            lines.append(f"- 第 {seg['id']} 拍：{seg['title']}（补齐本拍变量后生成）")
        lines.append("")
    else:
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
    title = "待补" if is_draft else (
        f"{g(pub, 'emotion_word')}{g(pub, 'subject')}｜{g(pub, 'crowd_tag')}"
        f"{g(pub, 'emoji', default='')}"
    )
    lines += [
        "## 发布草案",
        "",
        f"- 标题：{title}",
        f"- 免责：{DISCLAIMER}",
        f"- 转发：{g(pub, 'forward_text') or '待补'}",
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
    ap.add_argument(
        "--release",
        action="store_true",
        help="Release prompts/publish pack after hash-bound approval",
    )
    ap.add_argument(
        "--approval",
        default="",
        help="Path to approval.json; required with --release",
    )
    args = ap.parse_args()

    vars_path = Path(args.vars).expanduser().resolve()
    if not vars_path.is_file():
        raise SystemExit(f"vars not found: {vars_path}")

    v = json.loads(vars_path.read_text(encoding="utf-8"))
    if not isinstance(v, dict):
        raise SystemExit("vars must be a JSON object")

    digest = input_sha256(vars_path)
    slug = args.slug or slugify(g(v, "theme"))
    out_dir = Path(args.out_root).expanduser().resolve() / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    missing_fields = missing_release_fields(v)
    segments = build_segments(v)
    review_text = render_review_md(v, segments, missing_fields)
    review_digest = text_sha256(review_text)
    if args.release:
        for name in RELEASE_FILES:
            (out_dir / name).unlink(missing_ok=True)
    approval_path: Path | None = None
    approval: dict | None = None
    if args.release:
        if not args.approval:
            raise SystemExit("--release requires --approval <approval.json>")
        approval_path = Path(args.approval).expanduser().resolve()
        approval = require_release_approval(approval_path, digest, review_digest)
        if missing_fields:
            raise SystemExit(
                "release blocked：缺少正式发布必填字段：" + "；".join(missing_fields)
            )

    (out_dir / "00-主题变量.json").write_text(
        json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "01-科普脚本复核包.md").write_text(
        review_text, encoding="utf-8"
    )

    if not args.release:
        (out_dir / "approval.json").write_text(
            json.dumps(
                approval_template(digest, review_digest), ensure_ascii=False, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        for name in RELEASE_FILES:
            (out_dir / name).unlink(missing_ok=True)
        print(f"OK review scaffold → {out_dir}")
        print("  01-科普脚本复核包.md")
        print("  approval.json（确认后填写，再用 --release --approval 发布）")
        return 0

    (out_dir / "02-Seedance提示词-分段.md").write_text(
        render_prompts_md(v, segments), encoding="utf-8"
    )
    (out_dir / "03-视频号发布全家桶.md").write_text(
        render_publish_md(v), encoding="utf-8"
    )
    (out_dir / "DELIVERY.md").write_text(
        render_delivery_md(v, out_dir), encoding="utf-8"
    )
    assert approval_path is not None and approval is not None
    if approval_path != out_dir / "approval.json":
        (out_dir / "approval.json").write_text(
            json.dumps(approval, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    write_release_manifest(out_dir, digest, review_digest, approval_path, approval)

    # pointer to meta-prompt
    meta = MODE_DIR / "meta-prompt.md"
    if meta.is_file():
        (out_dir / "README-模式说明.txt").write_text(
            f"模式资产: {meta}\n总规: docs/seedance-health-edu-video-mode.md\n",
            encoding="utf-8",
        )

    print(f"OK released scaffold → {out_dir}")
    print("  01-科普脚本复核包.md")
    print("  02-Seedance提示词-分段.md")
    print("  03-视频号发布全家桶.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
