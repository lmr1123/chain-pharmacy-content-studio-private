#!/usr/bin/env python3
"""Scaffold 九宫格健康科普 delivery package (60s / 6×10s).

Produces character sheets, per-segment (narration + 9-grid + video prompt),
and social compliance pack. No paid API calls.

Usage:
  python3 scripts/scaffold_jiugongge_health_edu.py \\
    --vars production-library/templates/prompt-modes/jiugongge-health-edu-v1/example-阿尔茨海默早期筛查.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODE_DIR = ROOT / "production-library/templates/prompt-modes/jiugongge-health-edu-v1"
DEFAULT_OUT = ROOT / "outputs/business-video-runs/jiugongge-health-edu"

CHAR_CONSISTENCY = (
    "林医生与王大爷造型与角色设定图完全一致：林医生白大褂浅蓝衬衫听诊器；"
    "王大爷米白衬衫花白短发。3D Pixar 温暖治愈，无写实真人脸，无血腥。"
)

DISCLAIMER_TEXT = (
    "本视频由 AI 技术辅助生成，仅供健康科普与生活参考，"
    "不能替代执业医师面诊、诊断或治疗方案。"
    "如有不适请及时前往正规医疗机构就医。请勿自行用药。"
)

PINNED_COMMENT = (
    "温馨提醒：本内容为 AI 辅助科普，面向中老年朋友的生活化讲解，"
    "不是医疗诊断。每个人身体情况不同，具体请咨询正规医院医生。"
    "转发前也请提醒家人：有不适早就医。🙏"
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


def expand_knowledge(points: list[str]) -> list[str]:
    """Always return 3 beat labels for segments 2-4."""
    pts = [p.strip() for p in points if str(p).strip()]
    if not pts:
        pts = ["关注身体变化", "及时告诉家人", "正规医院评估"]
    if len(pts) == 1:
        return [
            pts[0],
            f"常见误区：别把「{pts[0][:12]}…」只当小事硬扛",
            "记住口诀：早发现、早告知、早去正规医院看看",
        ]
    if len(pts) == 2:
        return [pts[0], pts[1], f"对照记住：{pts[0][:10]} + {pts[1][:10]}，有一条就重视"]
    return pts[:3]


def nine_grid_block(title: str, cells: list[str]) -> str:
    assert len(cells) == 9
    lines = [
        f"一张 3x3 九宫格分镜拼图，正方形构图，温暖 3D Pixar 卡通，统一角色与灯光，"
        f"主题：{title}。从左到右、从上到下共 9 格：",
    ]
    for i, c in enumerate(cells, 1):
        lines.append(f"{i}. {c}")
    lines.append("禁止写实真人脸、血腥、水印文字刷屏。角色：林医生、王大爷造型锁定。")
    return "\n".join(lines)


def build_segments(v: dict) -> list[dict]:
    theme = g(v, "theme")
    k1, k2, k3 = expand_knowledge(list(v.get("knowledge_points") or []))
    clinic = g(v, "clinic_scene", default="温馨明亮的社区诊所卡通诊室，柔和暖光")
    ar = g(v, "aspect_ratio", default="9:16")
    emergency = list(v.get("emergency_actions") or ["保持冷静", "立即拨打120", "协助等待救援"])
    prevent = list(v.get("prevention_tips") or ["规律作息", "适度活动", "定期体检"])
    e1, e2, e3 = (emergency + ["", "", ""])[:3]
    p1, p2, p3 = (prevent + ["", "", ""])[:3]

    segs = []

    # --- 1 ---
    segs.append(
        {
            "id": 1,
            "range": "0-10s",
            "title": "场景引入 & 医生开场",
            "narration": (
                f"各位叔叔阿姨好，我是林医生。今天想跟您聊聊「{theme}」。"
                f"这事儿跟咱们生活质量关系大，咱们用大白话慢慢说，别着急。"
            ),
            "nine_grid": nine_grid_block(
                f"{theme}·开场",
                [
                    f"暖光{clinic}外景或门口",
                    "林医生推门微笑向镜头招手",
                    "诊室全景，绿植与柔光",
                    "林医生整理听诊器特写",
                    "林医生中景面向镜头开口讲解",
                    "桌面出现主题发光 3D 示意图标",
                    "王大爷在等候椅上温和点头",
                    "林医生手势邀请王大爷靠近",
                    "两人同框，林医生竖起一根手指示意「先听重点」",
                ],
            ),
            "video": (
                f"竖屏 {ar}，10 秒，3D Pixar 温暖治愈。{CHAR_CONSISTENCY}\n"
                f"Midshot：林医生站在{clinic}，面带微笑看向镜头开场讲解「{theme}」，"
                f"身旁浮现轻微发光的 3D 科普示意模型，光影柔和。"
                f"背景可见王大爷坐在一旁认真听。镜头缓慢推进，节奏舒缓，无跳切花字水印。"
            ),
        }
    )

    # --- 2-4 knowledge ---
    knowledge_pack = [
        (2, "11-20s", k1, "Close-up 或 Split-screen"),
        (3, "21-30s", k2, "Close-up 或 Split-screen"),
        (4, "31-40s", k3, "Close-up 或 Split-screen"),
    ]
    for sid, rng, kp, lens in knowledge_pack:
        segs.append(
            {
                "id": sid,
                "range": rng,
                "title": f"核心知识点 · {kp[:20]}",
                "narration": (
                    f"您看啊，{kp}。"
                    f"这就像家里电器突然不听使唤，不是吓唬您，是提醒咱们早点留意。"
                    f"林医生带着王大爷，把这个表现给您演示清楚。"
                ),
                "nine_grid": nine_grid_block(
                    f"知识点演示：{kp[:24]}",
                    [
                        "林医生指向说明卡片或发光图标",
                        "王大爷做出相关生活化动作/表情",
                        "问题表现部位或行为用柔和红光示意（卡通）",
                        "林医生轻轻指导王大爷的手势",
                        f"高潮格：最清晰地展示「{kp[:18]}」",
                        "王大爷恍然大悟的表情",
                        "分屏左：错误忽视；右：正确重视（卡通符号）",
                        "林医生摇头否定危险做法（温和）",
                        "林医生点头肯定正确应对，定格微笑",
                    ],
                ),
                "video": (
                    f"竖屏 {ar}，10 秒，3D Pixar。{CHAR_CONSISTENCY}\n"
                    f"{lens}：林医生指导王大爷演示与「{kp}」相关的生活化表现；"
                    f"重点部位或行为用柔和发光/红光卡通示意，不血腥不惊悚。"
                    f"可短暂 split-screen 对比「不当回事」与「重视并告知家人」。"
                    f"口型节奏舒缓，匹配中老年讲解。无水印乱字幕。"
                ),
            }
        )

    # --- 5 emergency ---
    segs.append(
        {
            "id": 5,
            "range": "41-50s",
            "title": "紧急救助 / 行动指南",
            "narration": (
                f"万一情况不对，千万别慌。记住：{e1}，{e2}，{e3}。"
                f"早一分钟求助，就多一分踏实。咱不逞能，听医生的、走正规医院。"
            ),
            "nine_grid": nine_grid_block(
                "紧急行动指南",
                [
                    "林医生严肃但镇定地举手示意「停、别慌」",
                    "卡通手机界面拨打 120（大号数字）",
                    "王大爷在安全位置坐下或平卧示意（得体）",
                    "家人卡通角色协助搀扶",
                    "高潮格：救护车卡通驶来（非写实血腥）",
                    "医院门口红十字卡通标识",
                    "林医生指挥手势：保持呼吸道通畅的示意（科普级）",
                    "家属点头记录医嘱的动作",
                    "林医生竖起大拇指：做对了",
                ],
            ),
            "video": (
                f"竖屏 {ar}，10 秒，3D Pixar。{CHAR_CONSISTENCY}\n"
                f"Montage / Dynamic 但节奏仍偏缓：林医生指挥正确应急——"
                f"卡通拨打 120、协助王大爷安全体位、救护车与医院元素闪现。"
                f"强调「{e1}；{e2}；{e3}」。禁止血腥手术画面，禁止写实真人脸。"
            ),
        }
    )

    # --- 6 wrap ---
    segs.append(
        {
            "id": 6,
            "range": "51-60s",
            "title": "温馨总结 & 预防呼吁",
            "narration": (
                f"平常咱们可以：{p1}，{p2}，{p3}。"
                f"这份提醒，转给家里人看看。平安最重要，咱们下期见。"
            ),
            "nine_grid": nine_grid_block(
                "预防与温馨收尾",
                [
                    "王大爷户外慢走，阳光明媚",
                    "餐桌上清淡健康食物卡通图标",
                    "家人陪伴聊天的温馨画面",
                    "日历/体检提醒图标飘过",
                    "高潮格：林医生 Thumbs up 面向镜头",
                    "王大爷恢复精神微笑招手",
                    "健康生活 icons 漂浮（散步、清水、睡眠）",
                    "林医生与王大爷并排合影式中景",
                    "暖光收束，两人挥手再见",
                ],
            ),
            "video": (
                f"竖屏 {ar}，10 秒，3D Pixar。{CHAR_CONSISTENCY}\n"
                f"Full shot：林医生与精神好转的王大爷站在暖光场景微笑；"
                f"健康生活 icons（散步、清淡饮食、作息）轻轻漂浮。"
                f"林医生 thumbs up，呼吁转发给家人。温暖 ending，无水印。"
            ),
        }
    )
    return segs


def render_characters_md() -> str:
    base = (MODE_DIR / "character-sheets.md").read_text(encoding="utf-8")
    return f"# 角色三视图提示词（复制出图）\n\n{base}\n"


def render_review_md(v: dict, segs: list[dict]) -> str:
    pts = list(v.get("knowledge_points") or [])
    lines = [
        f"# 九宫格科普脚本复核包 · {g(v, 'theme')}",
        "",
        f"**模式：** jiugongge-health-edu-v1  ",
        f"**日期：** {date.today().isoformat()}  ",
        f"**时长：** 60 秒（6×10s）  ",
        f"**状态：** 待业务确认",
        "",
        "## 核心知识点",
        "",
    ]
    for i, p in enumerate(pts, 1):
        lines.append(f"{i}. {p}")
    if g(v, "extra_notes"):
        lines += ["", f"**补充：** {g(v, 'extra_notes')}"]
    lines += ["", "## 六段口播（请先审文案）", ""]
    for s in segs:
        lines += [
            f"### 片段 {s['id']}（{s['range']}）· {s['title']}",
            "",
            s["narration"],
            "",
        ]
    lines += [
        "## 确认区",
        "",
        "业务确认句示例：`脚本通过。可以出九宫格和视频提示词。`",
        "",
        "合规自检：不承诺疗效 □　不写具体用药方案 □　有就医/120 引导 □　中老年大白话 □",
        "",
    ]
    return "\n".join(lines)


def render_prompts_md(v: dict, segs: list[dict]) -> str:
    lines = [
        f"# 九宫格 + 视频提示词 · 六段 · {g(v, 'theme')}",
        "",
        "制作顺序：① 角色三视图定妆 → ② 每段九宫格出图 → ③ 用定妆/九宫格作参考生成 10s 视频 → ④ 拼接 + 片尾免责。",
        "",
        f"**画幅：** {g(v, 'aspect_ratio', default='9:16')}  ",
        "**每段：** 10 秒  ",
        "**一致性：** 九宫格动作/道具须与该段视频提示词一致",
        "",
    ]
    for s in segs:
        lines += [
            "---",
            "",
            f"## 片段 {s['id']}（{s['range']}）· {s['title']}",
            "",
            "### 口播文案",
            "",
            s["narration"],
            "",
            "### 九宫格图片提示词（复制出图）",
            "",
            "```",
            s["nine_grid"],
            "```",
            "",
            "### 片段视频提示词（复制到 Seedance/即梦）",
            "",
            "```",
            s["video"],
            f"本段口播大意（可作口型参考，勿烧成硬字幕水印）：{s['narration']}",
            "```",
            "",
        ]
    return "\n".join(lines)


def render_publish_md(v: dict) -> str:
    pub = v.get("publish") or {}
    theme = g(v, "theme")
    title = g(pub, "title") or f"中老年必看｜{theme}，林医生大白话讲清楚"
    body = g(pub, "body") or (
        f"今天跟叔叔阿姨聊聊「{theme}」。内容用大白话、3D 动画演示，方便转发家里人。"
        f"仅供科普，不能替代医生诊断；有不适请及时就医。"
    )
    tags = pub.get("hashtags") or ["中老年健康", "健康科普", "家庭关怀", "平安是福"]
    tag_line = " ".join("#" + t.lstrip("#") for t in tags)

    disclaimer_bg = (
        "温馨简约 3D 插画背景，浅米与淡蓝渐变，中央大面积留白用于叠字，"
        "角落有卡通听诊器与爱心小图标，无人物正脸特写，无密集文字，8K，适合视频片尾静帧。"
    )

    return "\n".join(
        [
            f"# 社媒合规发布包 · {theme}",
            "",
            "## 1. 平台发布文案",
            "",
            f"**标题：** {title}",
            "",
            f"**正文：**",
            "",
            body,
            "",
            f"**标签：** {tag_line}",
            "",
            "## 2. 评论区置顶声明（复制）",
            "",
            PINNED_COMMENT,
            "",
            "## 3. 视频末尾免责声明 · 背景图提示词",
            "",
            "```",
            disclaimer_bg,
            "```",
            "",
            "## 4. 视频末尾叠置文字（复制）",
            "",
            DISCLAIMER_TEXT,
            "",
            "## 5. 平台合规标注提醒（发布时勾选/备注）",
            "",
            "- 内容标注：AI 生成 / AI 辅助创作（按平台规则勾选）",
            "- 医疗相关：科普向，非诊疗广告；不承诺疗效",
            "- 建议置顶合规评论；片尾保留免责静帧 2–3 秒",
            "",
        ]
    )


def render_delivery_md(v: dict, out_dir: Path) -> str:
    return "\n".join(
        [
            f"# DELIVERY · {g(v, 'theme')}",
            "",
            f"- **模式 ID：** `jiugongge-health-edu-v1`",
            f"- **日期：** {date.today().isoformat()}",
            f"- **目录：** `{out_dir}`",
            "",
            "## 文件",
            "",
            "| 文件 | 用途 |",
            "|------|------|",
            "| `00-主题变量.json` | 变量留痕 |",
            "| `01-科普脚本复核包.md` | 业务先审口播 |",
            "| `02-角色三视图提示词.md` | 定妆出图 |",
            "| `03-九宫格与视频提示词-六段.md` | **九宫格 + 视频复制终稿** |",
            "| `04-社媒合规发布包.md` | 标题/置顶/片尾免责 |",
            "",
            "## 制作顺序",
            "",
            "1. 业务确认 `01` 口播",
            "2. `02` 出林医生/王大爷三视图",
            "3. `03` 每段先九宫格后 10s 视频",
            "4. 拼接 60s + `04` 片尾免责与置顶评论",
            "",
            "本包默认不含付费 API 出片；与疾病科普 Remotion 培训线、Seedance 生活避险五拍线均不同。",
            "",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold jiugongge health-edu package")
    ap.add_argument("--vars", required=True, help="Path to filled variables JSON")
    ap.add_argument("--slug", default="", help="Output folder slug")
    ap.add_argument("--out-root", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    vars_path = Path(args.vars).expanduser().resolve()
    if not vars_path.is_file():
        raise SystemExit(f"vars not found: {vars_path}")

    v = json.loads(vars_path.read_text(encoding="utf-8"))
    if not g(v, "theme"):
        raise SystemExit("vars.theme is required")
    if not v.get("knowledge_points"):
        raise SystemExit("vars.knowledge_points (1-3) is required")

    slug = args.slug or slugify(g(v, "theme"))
    out_dir = Path(args.out_root).expanduser().resolve() / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    segs = build_segments(v)
    (out_dir / "00-主题变量.json").write_text(
        json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "01-科普脚本复核包.md").write_text(
        render_review_md(v, segs), encoding="utf-8"
    )
    (out_dir / "02-角色三视图提示词.md").write_text(
        render_characters_md(), encoding="utf-8"
    )
    (out_dir / "03-九宫格与视频提示词-六段.md").write_text(
        render_prompts_md(v, segs), encoding="utf-8"
    )
    (out_dir / "04-社媒合规发布包.md").write_text(
        render_publish_md(v), encoding="utf-8"
    )
    (out_dir / "DELIVERY.md").write_text(
        render_delivery_md(v, out_dir), encoding="utf-8"
    )

    print(f"OK scaffold → {out_dir}")
    for name in [
        "01-科普脚本复核包.md",
        "02-角色三视图提示词.md",
        "03-九宫格与视频提示词-六段.md",
        "04-社媒合规发布包.md",
    ]:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
