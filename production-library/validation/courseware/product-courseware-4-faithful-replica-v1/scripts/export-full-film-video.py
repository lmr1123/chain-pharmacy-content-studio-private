#!/usr/bin/env python3
"""Render full-film stills per scene and assemble MP4 with reference narration.

Editable video entrypoint: content-model.json (+ optional editable-patches.json)
drives all screen copy / pack slots. Rebuild = re-run this script.

Usage:
  python3 scripts/export-full-film-video.py
  python3 scripts/export-full-film-video.py --patches editable-patches.json
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "generated"
OUT = ROOT / "out"
FRAMES = OUT / "scene-stills"
FONTS = Path.home() / "Library" / "Fonts"
MODEL_PATH = ROOT / "content-model.json"


def apply_patches(model: dict, patches: dict) -> dict:
    """Merge editable patches into content-model (deep copy)."""
    if not patches:
        return model
    m = copy.deepcopy(model)
    for sid, fields in (patches.get("scenes") or {}).items():
        for sc in m.get("scenes") or []:
            if sc.get("id") == sid and isinstance(fields, dict):
                for k, v in fields.items():
                    if k.startswith("_"):
                        continue
                    sc[k] = v
    # asset path overrides: { "slot-pack-box-a.png": "assets/..." }
    m["_asset_overrides"] = patches.get("assets") or {}
    return m


def resolve_asset(name: str, model: dict | None = None) -> Path:
    ov = (model or {}).get("_asset_overrides") or {}
    if name in ov:
        p = Path(ov[name])
        return p if p.is_absolute() else ROOT / p
    return ASSETS / name


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        FONTS / name,
        FONTS / "HarmonyOS" / name,
        Path("/System/Library/Fonts/PingFang.ttc"),
    ]
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def silk_bg(w=1920, h=1080) -> Image.Image:
    """Warm silk-like wash without tiled checkerboard seams."""
    im = Image.new("RGB", (w, h), (206, 203, 196))
    d = ImageDraw.Draw(im, "RGBA")
    # soft diagonal folds
    for i, alpha in enumerate([18, 14, 10, 8]):
        x0 = -200 + i * 180
        d.polygon([(x0, 0), (x0 + 420, 0), (x0 + 820, h), (x0 + 200, h)], fill=(255, 255, 255, alpha))
    for i, alpha in enumerate([12, 9, 6]):
        x0 = 400 + i * 220
        d.polygon([(x0, 0), (x0 + 280, 0), (x0 + 100, h), (x0 - 180, h)], fill=(170, 165, 158, alpha))
    return im.convert("RGB")


def load_rgba(name: str, model: dict | None = None) -> Image.Image:
    path = resolve_asset(name, model)
    if not path.exists():
        path = ASSETS / name
    return Image.open(path).convert("RGBA")


def paste_c(
    base: Image.Image,
    layer: Image.Image,
    cx: int,
    cy: int,
    max_h: int | None = None,
    *,
    scale: float = 1.0,
    dx: float = 0.0,
    dy: float = 0.0,
    rot: float = 0.0,
    opacity: float = 1.0,
):
    im = layer
    if max_h and im.height > 0:
        r = max_h / im.height
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    if abs(scale - 1.0) > 1e-3:
        nw = max(1, int(im.width * scale))
        nh = max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.LANCZOS)
    if abs(rot) > 0.05:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if opacity < 0.999:
        a = im.split()[-1].point(lambda p: int(p * max(0.0, min(1.0, opacity))))
        im = im.copy()
        im.putalpha(a)
    x = int(cx - im.width / 2 + dx)
    y = int(cy - im.height / 2 + dy)
    base.alpha_composite(im, (x, y))


def ease_out_back(t: float) -> float:
    """Mild overshoot pop 0→1 (培训课件：轻弹，不夸张)."""
    t = max(0.0, min(1.0, t))
    c1 = 1.2  # softer than classic 1.7
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def pop_scale(t_local: float, t0: float, dur: float = 0.45, *, overshoot: bool = True) -> float:
    """0 before t0, ease to 1 over dur. Used for entrance only."""
    if t_local < t0:
        return 0.0
    if t_local >= t0 + dur:
        return 1.0
    u = (t_local - t0) / dur
    return ease_out_back(u) if overshoot else ease_out_cubic(u)


def accent_bounce_y(t_local: float, period: float = 0.7, amp: float = 8.0) -> float:
    """表头白箭头：小幅上下（仅表头，非链路红箭头）。"""
    return amp * abs(math.sin(math.pi * t_local / max(0.05, period)))


def accent_nudge_x(t_local: float, period: float = 0.85, amp: float = 4.0) -> float:
    """极轻左右（仅 S01 黄绿 »）。"""
    return amp * math.sin(2.0 * math.pi * t_local / max(0.05, period))


def accent_point_dx(t_local: float, period: float = 0.65, amp: float = 12.0) -> float:
    """链路红箭头：沿指向方向（向右）脉冲位移 0→amp→0，不是上下跳。"""
    # abs-sine → always forward along arrow, reads as 「往前顶」
    return amp * abs(math.sin(math.pi * t_local / max(0.05, period)))


# ── 动效语法（对标参考片实测，禁止全屏抖）────────────────────────────
# 1. 入场：单次 scale/opacity 弹出（0.4–0.6s），到位后冻结
# 2. 强调循环：仅 表头白箭头 / 链路红箭头 / S01 黄绿»  小幅 bounce
# 3. 主视觉（番茄、器官、杂志、卡片、列表字、O2、NK、手臂图）到位后静止
# 4. 序贯揭示：S05 番茄→O2→叉→女；S06 番茄→NK→手臂；元素出现是阶跃不是晃
# 5. 禁止：主图标 idle、卡片呼吸、杂志摇、手臂乱转、多元素同相位大振幅
MOTION_SCENE_IDS = {
    "S01_time_list",
    "S04_benefit_1",
    "S05_benefit_2",
    "S06_benefit_3",
}
MOTION_FPS = 12.0
# 强调循环统一参数（1080p）
ACCENT_ARROW_AMP = 14.0  # 沿指向方向的像素位移
ACCENT_ARROW_PERIOD = 0.6
ACCENT_SECTION_AMP = 8.0
ACCENT_SECTION_PERIOD = 0.7
ACCENT_S01_CHEV_AMP = 7.0


def chain_centers(
    sizes: list[int],
    gap: int = 48,
    canvas_w: int = 1920,
) -> list[int]:
    """Return cx for each item so the whole chain is horizontally centered."""
    if not sizes:
        return []
    total = sum(sizes) + gap * (len(sizes) - 1)
    x = (canvas_w - total) / 2.0
    out: list[int] = []
    for w in sizes:
        out.append(int(round(x + w / 2.0)))
        x += w + gap
    return out


def paste_chain_centered(
    base: Image.Image,
    load,
    items: list[tuple[str, int]],
    cy: int = 580,
    gap: int = 48,
) -> list[int]:
    """Paste (asset, max_h) items as a centered horizontal chain. Returns cxs.

    Uses **actual resized widths** so the group is truly canvas-centered.
    """
    prepared: list[Image.Image] = []
    for name, mh in items:
        im = load(name)
        if mh and im.height > mh:
            r = mh / im.height
            im = im.resize((max(1, int(im.width * r)), mh), Image.LANCZOS)
        elif mh and im.height < mh and im.width < mh:
            # upscale small assets to target height for visual weight
            r = mh / im.height
            im = im.resize((max(1, int(im.width * r)), mh), Image.LANCZOS)
        prepared.append(im)
    widths = [im.width for im in prepared]
    cxs = chain_centers(widths, gap=gap)
    for im, cx in zip(prepared, cxs):
        x = int(cx - im.width / 2)
        y = int(cy - im.height / 2)
        base.alpha_composite(im, (x, y))
    return cxs


def subtitle_segments(sc: dict, fallback: str = "") -> list[tuple[float, float, str]]:
    """Split a scene into (t0, t1, text) segments so captions track narration."""
    start = float(sc["start"])
    end = float(sc["end"])
    if end <= start:
        end = start + 0.1
    raw = sc.get("subtitles") or []
    if not raw:
        text = fallback or sc.get("subtitle") or ""
        return [(start, end, str(text))]

    # normalize cues within scene
    cues: list[tuple[float, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        t = float(item.get("t", start))
        text = str(item.get("text") or "")
        cues.append((t, text))
    cues.sort(key=lambda x: x[0])
    if not cues:
        return [(start, end, fallback)]

    segs: list[tuple[float, float, str]] = []
    for i, (t, text) in enumerate(cues):
        t0 = start if i == 0 else max(start, t)
        t1 = float(cues[i + 1][0]) if i + 1 < len(cues) else end
        t1 = min(end, max(t0 + 0.05, t1))
        segs.append((t0, t1, text or fallback))
    # ensure cover full scene
    if segs[0][0] > start + 0.02:
        segs.insert(0, (start, segs[0][0], segs[0][2]))
    last_t0, _, last_text = segs[-1]
    segs[-1] = (last_t0, end, last_text)
    return segs


def text_outline(draw, xy, text, font, fill, outline="#ffffff", width=3):
    x, y = xy
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def chapter_title(draw, text, y=40):
    # 培训课件章节字：明显大于文档体（对标参考黄字红描边）
    f = font("HarmonyOS_Sans_SC_Black.ttf", 88)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    x = (1920 - tw) // 2
    for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (0, 4), (-3, 0), (3, 0)]:
        draw.text((x + dx, y + dy), text, font=f, fill="#ba3034")
    draw.text((x, y), text, font=f, fill="#ffe33c")


def section_label(draw, text, y=150):
    # 左上小节：位图绿箭头 + 大号棕红字
    chev = load_rgba("icon-chevron-lime.png")
    chev = chev.resize((56, 56), Image.LANCZOS)
    # draw is on base via caller — section_label only draws text; chevron pasted by caller if needed
    f = font("HarmonyOS_Sans_SC_Bold.ttf", 52)
    draw.text((168, y + 4), text, font=f, fill="#a05040")
    return chev  # caller pastes at (100, y-4)


def paste_section_label(
    base: Image.Image,
    draw,
    text: str,
    y: int = 150,
    *,
    bounce: float = 0.0,
    chev_name: str = "icon-chevron-white.png",
    omit_text: bool = False,
):
    """表头双箭头：参考为白色，并持续跳动。"""
    chev_path = ASSETS / chev_name
    if not chev_path.exists():
        chev_name = "icon-chevron-lime.png"
    chev = load_rgba(chev_name).resize((62, 62), Image.LANCZOS)
    by = int(y - 4 - bounce)
    base.alpha_composite(chev, (92, by))
    if omit_text:
        return
    f = font("HarmonyOS_Sans_SC_Bold.ttf", 56)
    # 小节标题：棕红字 + 轻白描边（对标参考丝纹底可读性）
    text_outline(draw, (170, y + 4), text, f, "#a05040", "#ffffff", 2)


def subtitle(draw, text):
    """底栏讲解字幕：对标参考 — 近黑字 + 白描边（丝绸底高对比，禁止白字）。"""
    if not text:
        return
    f = font("HarmonyOS_Sans_SC_Bold.ttf", 56)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    x = (1920 - tw) // 2
    y = 988
    # 白描边略收，保证黑芯清晰可读
    text_outline(draw, (x, y), text, f, "#111111", "#ffffff", 3)


def wrap_text(draw, text: str, font_obj, max_w: int) -> list[str]:
    lines: list[str] = []
    cur = ""
    for ch in text:
        test = cur + ch
        bb = draw.textbbox((0, 0), test, font=font_obj)
        if bb[2] - bb[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def render_scene(
    scene_id: str,
    sub: str = "",
    scene: dict | None = None,
    model: dict | None = None,
    *,
    omit_text: bool = False,
    t_local: float = 0.0,
) -> Image.Image:
    """Render one scene from content-model.

    omit_text=True: keep layout/images/shapes only (editor background, no burned copy).
    t_local: seconds from scene start — drives pop-in / bounce / sequential reveals.
    """
    sc = scene or {}
    base = silk_bg().convert("RGBA")
    d = ImageDraw.Draw(base)
    # freeze motion for editor bg / representative still when t_local huge
    tl = float(t_local)

    def L(name: str) -> Image.Image:
        return load_rgba(name, model)

    def L_pref(*names: str) -> Image.Image:
        for n in names:
            p = resolve_asset(n, model)
            if p.exists():
                return load_rgba(n, model)
        return load_rgba(names[-1], model)

    def draw_text(*args, **kwargs):
        if not omit_text:
            d.text(*args, **kwargs)

    def draw_outline(*args, **kwargs):
        if not omit_text:
            text_outline(*args, **kwargs)

    def draw_chapter(text, y=40):
        if omit_text:
            return
        chapter_title(d, text, y=y)

    def draw_section(text, y=150):
        # 表头白箭头：克制循环（唯一表头强调，不全屏抖）
        b = (
            0.0
            if omit_text
            else accent_bounce_y(tl, ACCENT_SECTION_PERIOD, ACCENT_SECTION_AMP)
        )
        paste_section_label(
            base,
            d,
            text,
            y=y,
            bounce=b,
            chev_name="icon-chevron-white.png",
            omit_text=omit_text,
        )

    def arrow_img() -> Image.Image:
        return L_pref("arrow-red-ref.png", "arrow-red.png")


    if scene_id in ("S00_cover", "S15_end", "S12_end"):
        # 远山 + 标题胶囊 + 好物推荐徽章 + 三点勾选（位图）+ 包装槽
        d.polygon(
            [(0, 1080), (0, 860), (300, 780), (600, 900), (960, 740), (1400, 880), (1920, 800), (1920, 1080)],
            fill=(190, 190, 190, 120),
        )
        f = font("HarmonyOS_Sans_SC_Bold.ttf", 68)
        pill = sc.get("title_pill") or "福尔番茄红素软胶囊"
        bb = d.textbbox((0, 0), pill, font=f)
        tw = bb[2] - bb[0]
        d.rounded_rectangle(
            [960 - tw // 2 - 56, 52, 960 + tw // 2 + 56, 152],
            radius=56,
            fill=(120, 120, 120, 200),
        )
        draw_text((960 - tw // 2, 72), pill, font=f, fill="white")
        # 好物推荐
        paste_c(base, L("badge-hot-recommend.png"), 1720, 140, 200)
        # 三点：参考为红底白勾圆形图标 + 大字（位图可复用）
        check = L("icon-check-red.png")
        fb = font("HarmonyOS_Sans_SC_Medium.ttf", 52)
        benefits = sc.get("benefits") or [
            "保护前列腺，提高精子活力",
            "抗氧化，延缓衰老",
            "增强免疫力",
        ]
        for i, line in enumerate(benefits):
            yy = 290 + i * 108
            icon = check.resize((76, 76), Image.LANCZOS)
            base.alpha_composite(icon, (108, yy))
            draw_text((210, yy + 14), line, font=fb, fill="#1a1a1a")
        # 包装槽（编辑器底板上不画，留给可编辑 Img 层）
        if not omit_text:
            paste_c(base, L("slot-pack-box-a.png"), 1120, 540, 420)
            paste_c(base, L("slot-pack-box-b.png"), 1400, 540, 420)
            paste_c(base, L("slot-pack-bottle.png"), 1660, 520, 460)

    elif scene_id == "S01_time_list":
        # 语法：杂志弹入 → 半透明卡弹入 → 列表行依次出现 → 仅黄绿»轻跳；其余冻结
        mag_s = pop_scale(tl, 0.05, 0.5) if not omit_text else 1.0
        card_s = pop_scale(tl, 0.28, 0.5) if not omit_text else 1.0
        list_s = pop_scale(tl, 0.55, 0.45) if not omit_text else 1.0
        chev_y = (
            accent_bounce_y(tl, 0.72, ACCENT_S01_CHEV_AMP) if not omit_text else 0.0
        )
        chev_x = accent_nudge_x(tl, 0.9, 3.0) if not omit_text else 0.0

        mag_path = ASSETS / "slot-time-magazine.png"
        if mag_path.exists() and not omit_text and mag_s > 0.02:
            mag = L("slot-time-magazine.png")
            sc_mag = 0.88 + 0.12 * mag_s if mag_s < 1.0 else 1.0
            paste_c(
                base,
                mag,
                211 + 389 // 2,
                261 + 558 // 2 + int((1 - mag_s) * 36),
                558,
                scale=sc_mag,
                opacity=min(1.0, 0.3 + mag_s * 0.7),
            )
        elif not mag_path.exists() and not omit_text:
            d.rectangle(
                [211, 261, 211 + 389, 261 + 558],
                fill="white",
                outline="#b11a1a",
                width=10,
            )

        if card_s > 0.02:
            card = Image.new("RGBA", (978, 520), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            # 半透明深灰（参考黑卡）
            alpha = int(188 * min(1.0, card_s * 1.05))
            cd.rounded_rectangle([0, 0, 977, 519], radius=48, fill=(50, 50, 50, alpha))
            cx, cy = 769 + 978 // 2, 277 + 520 // 2
            sc_card = 0.92 + 0.08 * card_s if card_s < 1.0 else 1.0
            cw, ch = int(978 * sc_card), int(520 * sc_card)
            card_r = card.resize((max(1, cw), max(1, ch)), Image.LANCZOS)
            base.alpha_composite(
                card_r,
                (
                    int(cx - card_r.width / 2),
                    int(cy - card_r.height / 2 + (1 - min(1.0, card_s)) * 28),
                ),
            )
            if card_s > 0.85:
                chev = L("icon-chevron-lime.png").resize((72, 72), Image.LANCZOS)
                base.alpha_composite(
                    chev, (int(820 + chev_x), int(330 - chev_y))
                )
                if not omit_text:
                    draw_text(
                        (910, 340),
                        sc.get("card_title")
                        or "对人类健康贡献最大的10种健康食品",
                        font=font("HarmonyOS_Sans_SC_Regular.ttf", 42),
                        fill="#e9f200",
                    )
                    d.line([(820, 420), (1680, 420)], fill="#e9f200", width=4)
                    if list_s > 0.05:
                        fl = font("HarmonyOS_Sans_SC_Medium.ttf", 68)
                        lines = sc.get("list") or ["1.番茄", "2.***", "3.***"]
                        for i, line in enumerate(lines[:3]):
                            row_p = pop_scale(tl, 0.55 + i * 0.16, 0.35, overshoot=False)
                            if row_p < 0.05:
                                continue
                            # 行只入场上移，到位后冻结（无 idle 晃）
                            draw_text(
                                (860, int(460 + i * 100 + (1 - row_p) * 28)),
                                line,
                                font=fl,
                                fill="#f2f2f2",
                            )
                else:
                    d.line([(820, 420), (1680, 420)], fill="#e9f200", width=4)

    elif scene_id == "S02_broll":
        if not omit_text:
            paste_c(base, L("slot-photo-tomato.png"), 960, 480, 640)

    elif scene_id == "S03_product_intro":
        if not omit_text:
            vine = L_pref("slot-photo-vine-cutout.png", "slot-photo-vine.png")
            paste_c(base, vine, 400, 500, 440)
            paste_c(base, L("slot-pack-box-a.png"), 1000, 520, 440)
            paste_c(base, L("slot-pack-box-b.png"), 1280, 520, 440)
            paste_c(base, L("slot-pack-bottle.png"), 1560, 500, 480)

    elif scene_id == "S04_benefit_1":
        draw_chapter(sc.get("chapter") or "一、三大核心功效")
        draw_section("1、保护前列腺、提高精子活力")
        if not omit_text:
            # 序贯：番茄 → 红箭头 → 前列腺；仅箭头循环轻跳，图标到位冻结
            tomato_p = pop_scale(tl, 0.4, 0.45, overshoot=False)
            arrow_p = pop_scale(tl, 1.0, 0.35, overshoot=False)
            prost_p = pop_scale(tl, 1.6, 0.45, overshoot=False)
            # 红箭头：沿指向方向（右）跳动
            adx = (
                accent_point_dx(tl, ACCENT_ARROW_PERIOD, ACCENT_ARROW_AMP)
                if arrow_p >= 1.0
                else 0.0
            )

            # (im, max_h, scale, dx, dy)
            prepared: list[tuple[Image.Image, int, float, float, float]] = []
            if tomato_p > 0.02:
                prepared.append(
                    (L("tomato.png"), 360, 0.92 + 0.08 * tomato_p, 0.0, (1 - tomato_p) * 24)
                )
            if arrow_p > 0.02:
                prepared.append((arrow_img(), 110, 0.92 + 0.08 * arrow_p, adx, 0.0))
            if prost_p > 0.02:
                prepared.append(
                    (
                        L("prostate-diagram.png"),
                        400,
                        0.92 + 0.08 * prost_p,
                        0.0,
                        (1 - prost_p) * 24,
                    )
                )
            if prepared:
                widths = [
                    max(1, int(im.width * (mh / max(1, im.height)) * scv))
                    for im, mh, scv, _, _ in prepared
                ]
                cxs = chain_centers(widths, gap=56)
                for (im, mh, scv, dx, dy), cx in zip(prepared, cxs):
                    paste_c(base, im, cx, 580, mh, scale=scv, dx=dx, dy=dy)

    elif scene_id == "S05_benefit_2":
        draw_chapter(sc.get("chapter") or "一、三大核心功效")
        draw_section("2、抗氧化，延缓衰老")
        if not omit_text:
            # 序贯揭示（参考）：番茄 → O2 → 叉盖住 O2 → 女+第二箭（叉消失）
            # 仅红箭头轻跳；图标/叉到位后静止
            tomato_p = pop_scale(tl, 0.7, 0.4, overshoot=False)
            a1_p = pop_scale(tl, 1.2, 0.35, overshoot=False)
            o2_p = pop_scale(tl, 1.4, 0.4, overshoot=False)
            x_p = 0.0
            if 3.6 <= tl < 9.0:
                x_p = pop_scale(tl, 3.6, 0.35, overshoot=False)
            woman_p = pop_scale(tl, 9.0, 0.45, overshoot=False)
            a2_p = pop_scale(tl, 8.9, 0.35, overshoot=False)
            adx1 = (
                accent_point_dx(tl, ACCENT_ARROW_PERIOD, ACCENT_ARROW_AMP)
                if a1_p >= 1.0
                else 0.0
            )
            adx2 = (
                accent_point_dx(tl + 0.2, ACCENT_ARROW_PERIOD, ACCENT_ARROW_AMP)
                if a2_p >= 1.0
                else 0.0
            )

            o2_im = L_pref("o2-cutout.png", "o2.png")
            woman_im = L("skincare-woman.png")
            x_im = L_pref("mark-red-x-hand.png", "mark-red-x.png")

            # (im, max_h, scale, dx, dy, tag)
            chain: list[tuple[Image.Image, int, float, float, float, str]] = []
            if tomato_p > 0.02:
                chain.append(
                    (L("tomato.png"), 260, 0.92 + 0.08 * tomato_p, 0.0, (1 - tomato_p) * 22, "t")
                )
            if a1_p > 0.02:
                chain.append((arrow_img(), 110, 0.92 + 0.08 * a1_p, adx1, 0.0, "a1"))
            if o2_p > 0.02:
                chain.append((o2_im, 260, 0.92 + 0.08 * o2_p, 0.0, (1 - o2_p) * 22, "o2"))
            if a2_p > 0.02:
                chain.append((arrow_img(), 110, 0.92 + 0.08 * a2_p, adx2, 0.0, "a2"))
            if woman_p > 0.02:
                chain.append(
                    (woman_im, 280, 0.92 + 0.08 * woman_p, 0.0, (1 - woman_p) * 24, "w")
                )

            if chain:
                widths = [
                    max(1, int(im.width * (mh / max(1, im.height)) * scv))
                    for im, mh, scv, _, _, _ in chain
                ]
                cxs = chain_centers(widths, gap=40)
                o2_cx = o2_cy = None
                for (im, mh, scv, dx, dy, tag), cx in zip(chain, cxs):
                    paste_c(base, im, cx, 580, mh, scale=scv, dx=dx, dy=dy)
                    if tag == "o2":
                        o2_cx, o2_cy = cx, 580
                # 手绘叉：单次淡入到位后静止
                if x_p > 0.05 and o2_cx is not None and x_im is not None:
                    paste_c(
                        base,
                        x_im,
                        o2_cx,
                        o2_cy,
                        250,
                        scale=0.88 + 0.12 * x_p,
                        opacity=min(1.0, x_p),
                        rot=-6,  # 略倾斜，更像手写
                    )

    elif scene_id == "S06_benefit_3":
        draw_chapter(sc.get("chapter") or "一、三大核心功效")
        draw_section("3、增强免疫力")
        if not omit_text:
            # 序贯：番茄 → NK-cell → 原手臂图；仅箭头轻跳
            # 手臂：原 flex-arm 位图 + 极轻 scale 呼吸（资产自带动感线，勿乱转）
            tomato_p = pop_scale(tl, 0.5, 0.4, overshoot=False)
            a1_p = pop_scale(tl, 1.0, 0.35, overshoot=False)
            nk_p = pop_scale(tl, 1.3, 0.45, overshoot=False)
            a2_p = pop_scale(tl, 5.2, 0.35, overshoot=False)
            arm_p = pop_scale(tl, 5.5, 0.45, overshoot=False)
            adx1 = (
                accent_point_dx(tl, ACCENT_ARROW_PERIOD, ACCENT_ARROW_AMP)
                if a1_p >= 1.0
                else 0.0
            )
            adx2 = (
                accent_point_dx(tl + 0.15, ACCENT_ARROW_PERIOD, ACCENT_ARROW_AMP)
                if a2_p >= 1.0
                else 0.0
            )
            # 手臂：约 ±3% 呼吸，无位移无旋转
            arm_sc = 1.0
            if arm_p >= 1.0:
                arm_sc = 1.0 + 0.03 * math.sin(2 * math.pi * tl / 0.9)

            nk_im = L_pref("nk-cell-labeled.png", "nk-cell.png")
            arm_im = L_pref("flex-arm-cutout.png", "flex-arm.png")

            # (im, max_h, scale, dx, dy, rot)
            chain = []
            if tomato_p > 0.02:
                chain.append(
                    (L("tomato.png"), 260, 0.92 + 0.08 * tomato_p, 0.0, (1 - tomato_p) * 22, 0.0)
                )
            if a1_p > 0.02:
                chain.append((arrow_img(), 110, 0.92 + 0.08 * a1_p, adx1, 0.0, 0.0))
            if nk_p > 0.02:
                chain.append((nk_im, 300, 0.92 + 0.08 * nk_p, 0.0, (1 - nk_p) * 22, 0.0))
            if a2_p > 0.02:
                chain.append((arrow_img(), 110, 0.92 + 0.08 * a2_p, adx2, 0.0, 0.0))
            if arm_p > 0.02:
                chain.append(
                    (
                        arm_im,
                        300,
                        (0.92 + 0.08 * arm_p) * arm_sc,
                        0.0,
                        (1 - arm_p) * 24,
                        0.0,
                    )
                )
            if chain:
                widths = [
                    max(1, int(im.width * (mh / max(1, im.height)) * scv))
                    for im, mh, scv, _, _, _ in chain
                ]
                cxs = chain_centers(widths, gap=40)
                for (im, mh, scv, dx, dy, rot), cx in zip(chain, cxs):
                    paste_c(base, im, cx, 580, mh, scale=scv, dx=dx, dy=dy, rot=rot)

    elif scene_id == "S07_origin":
        draw_chapter(sc.get("chapter") or "二、产品特点")
        draw_section("1、产地好")
        f = font("HarmonyOS_Sans_SC_Medium.ttf", 36)
        cap = "中国分省地图—新疆维吾尔自治区"
        bb = d.textbbox((0, 0), cap, font=f)
        draw_text(((1920 - (bb[2] - bb[0])) // 2, 240), cap, font=f, fill="#555555")
        if not omit_text:
            paste_c(base, L("map-xinjiang.png"), 960, 580, 460)

    elif scene_id == "S08_material":
        draw_chapter(sc.get("chapter") or "二、产品特点")
        draw_section("2、原料优")
        if not omit_text:
            paste_c(
                base,
                L_pref("slot-photo-vine-cutout.png", "slot-photo-vine.png"),
                960,
                560,
                520,
            )

    elif scene_id == "S09_content":
        draw_chapter(sc.get("chapter") or "二、产品特点")
        draw_section("3、含量高")
        if not omit_text:
            # softgel = five tomatoes，整组居中
            cxs = chain_centers([300, 140, 400], gap=40)
            paste_c(base, L("softgel.png"), cxs[0], 560, 280)
            eq_f = font("HarmonyOS_Sans_SC_Black.ttf", 140)
            bb = d.textbbox((0, 0), "=", font=eq_f)
            draw_text(
                (cxs[1] - (bb[2] - bb[0]) // 2, 470),
                "=",
                font=eq_f,
                fill="#e8c020",
            )
            paste_c(base, L("five-tomatoes.png"), cxs[2], 560, 380)

    elif scene_id == "S10_audience":
        draw_chapter(sc.get("chapter") or "三、适宜人群")
        items = [
            ("prostate-diagram.png", "前列腺患病"),
            ("couple.png", "备孕男士和女士"),
            ("audience-beauty.png", "爱美人士"),
            ("audience-weak.png", "身体虚弱人群"),
        ]
        margin_x = 100
        col_w = (1920 - 2 * margin_x) / 4
        xs = [int(margin_x + col_w * (i + 0.5)) for i in range(4)]
        icon_h = 300
        icon_cy = 500
        label_ty = icon_cy + icon_h // 2 + 30
        # 对标参考：亮黄字 + 红描边（丝绸底纯黄会看不清）
        fl = font("HarmonyOS_Sans_SC_Black.ttf", 42)
        for cx, (icon, label) in zip(xs, items):
            if not omit_text:
                paste_c(base, L(icon), cx, icon_cy, icon_h)
            bb = d.textbbox((0, 0), label, font=fl)
            tw = bb[2] - bb[0]
            tx = cx - tw // 2
            text_outline(
                d,
                (tx, label_ty),
                label,
                fl,
                fill="#ffe33c",
                outline="#ba3034",
                width=4,
            )

    elif scene_id == "S11_summary":
        # 对标参考汇总表：黄字红描边标题 + 左列功效名（大号+白描边）+ 右列正文（统一中号）
        # + 左右竖排说明。培训课件：字号整体偏大，层级固定两档，避免杂乱。
        draw_chapter(sc.get("chapter") or "五、福尔番茄红素三大核心功效", y=22)
        # 表格区域（左右竖排字留边）
        table = (148, 138, 1772, 980)
        d.rectangle(table, outline="#6a6a6a", width=3)
        if sc.get("rows"):
            rows = [(r.get("label", ""), r.get("body", "")) for r in sc["rows"]]
        else:
            rows = [
                (
                    "保护前列腺、\n提高精子活力",
                    "番茄红素具有抗氧化与调节细胞生长代谢的功能，能活化前列腺细胞，抑制致癌物的产生，保护前列腺，提高精子活力",
                ),
                (
                    "抗氧化，\n延缓衰老",
                    "番茄红素可通过物理和化学方式猝灭单线态氧或捕捉过氧化自由基，抗氧化能力是维E的100倍，从而达到延缓衰老的作用",
                ),
                (
                    "增强免疫力",
                    "番茄红素可活化免疫细胞，保护吞噬细胞免受自身的氧化损伤，促进淋巴细胞增殖，从而增强免疫力",
                ),
            ]
        left_w = 420  # 左列加宽，容纳大号功效名
        top, bot = table[1], table[3]
        left, right = table[0], table[2]
        fh = (bot - top) // 3
        # 两档字号：左列功效名 > 右列正文，各自统一，不再参差
        fl = font("HarmonyOS_Sans_SC_Black.ttf", 48)   # 左列大号
        fb = font("HarmonyOS_Sans_SC_Medium.ttf", 40)  # 右列统一中号（培训偏大）
        chev = L("icon-chevron-lime.png").resize((52, 52), Image.LANCZOS)
        label_fill = "#9a3c2e"
        body_fill = "#8a3a28"
        for i, (lab, body) in enumerate(rows):
            y0 = top + i * fh
            if i < 2:
                d.line([(left, y0 + fh), (right, y0 + fh)], fill="#6a6a6a", width=2)
            d.line([(left + left_w, y0), (left + left_w, y0 + fh)], fill="#6a6a6a", width=2)
            # 左列：绿箭头 + 多行功效名（白描边，对标参考）
            lab_lines = lab.split("\n")
            lh = 58
            block_h = len(lab_lines) * lh
            ty = y0 + (fh - block_h) // 2
            base.alpha_composite(chev, (left + 22, y0 + fh // 2 - 26))
            for j, ln in enumerate(lab_lines):
                draw_outline(
                    d,
                    (left + 88, ty + j * lh),
                    ln,
                    fl,
                    label_fill,
                    outline="#ffffff",
                    width=3,
                )
            # 右列正文：自动换行、垂直居中；统一字号行距，略描白边便于丝纹底可读
            max_w = right - (left + left_w) - 56
            body_lines = wrap_text(d, body, fb, max_w)
            blh = 54
            bbh = len(body_lines) * blh
            by = y0 + (fh - bbh) // 2
            for j, ln in enumerate(body_lines):
                draw_outline(
                    d,
                    (left + left_w + 32, by + j * blh),
                    ln,
                    fb,
                    body_fill,
                    outline="#ffffff",
                    width=2,
                )
        # 左右竖排说明（参考）— 培训课件略加大
        side_f = font("HarmonyOS_Sans_SC_Medium.ttf", 30)
        left_note = sc.get("side_left") or "不适宜人群：少年儿童、孕妇、乳母"
        right_note = sc.get("side_right") or "每日1次，每次1粒，建议固定随餐服用，避免漏服"

        def vtext(text, x, y0, color="#4a4a4a"):
            for i, ch in enumerate(text):
                draw_text((x, y0 + i * 36), ch, font=side_f, fill=color)

        vtext(left_note, 42, 200)
        vtext(right_note, 1810, 180)

    elif scene_id in ("S12_related_1", "S13_related_2"):
        # 金样旁白顺序：章节 → 导航 → 讲解句（上）→ 包装（下）；文案/包装来自 content-model
        draw_chapter(sc.get("chapter") or "四、关联用药", y=36)
        nav = sc.get("nav") or [
            "番茄红素+锌/硒（备孕与男性健康）",
            "番茄红素+维生素E（抗氧化协同）",
        ]
        active = int(sc.get("active_nav") if sc.get("active_nav") is not None else (0 if scene_id == "S12_related_1" else 1))
        pill_y, pill_h = 150, 62
        widths = [860, 820]
        xs = [100, 1000]
        fn = font("HarmonyOS_Sans_SC_Bold.ttf", 26)
        for i, label in enumerate(nav[:2]):
            px, pw = xs[i], widths[i]
            fill = "#c43c2c" if i == active else "#d8d4cc"
            tfill = "#ffffff" if i == active else "#555555"
            d.rounded_rectangle([px, pill_y, px + pw, pill_y + pill_h], radius=30, fill=fill)
            cx0 = px + 34
            cy0 = pill_y + pill_h // 2
            d.ellipse([cx0 - 16, cy0 - 16, cx0 + 16, cy0 + 16], fill="#ffffff" if i == active else "#c43c2c")
            nf = font("HarmonyOS_Sans_SC_Black.ttf", 24)
            num = str(i + 1)
            bb = d.textbbox((0, 0), num, font=nf)
            draw_text(
                (cx0 - (bb[2] - bb[0]) // 2, cy0 - (bb[3] - bb[1]) // 2 - 2),
                num,
                font=nf,
                fill="#c43c2c" if i == active else "#ffffff",
            )
            draw_text((px + 64, pill_y + 16), label, font=fn, fill=tfill)

        note = sc.get("note") or ""
        fn_note = font("HarmonyOS_Sans_SC_Black.ttf", 36)
        bb = d.textbbox((0, 0), note, font=fn_note)
        draw_text(((1920 - (bb[2] - bb[0])) // 2, 250), note, font=fn_note, fill="#3a2a28")

        card = (120, 330, 1800, 980)
        d.rounded_rectangle(card, radius=36, fill=(255, 255, 255, 240))
        left_pack = sc.get("left_pack") or "slot-pack-lycopene.png"
        right_pack = sc.get("right_pack") or "slot-pack-zinc.png"
        if not omit_text:
            paste_c(base, L(left_pack), 520, 620, 400)
        plus_f = font("HarmonyOS_Sans_SC_Black.ttf", 120)
        bb = d.textbbox((0, 0), "+", font=plus_f)
        # + 号保留在编辑器底板上作布局锚点
        d.text((960 - (bb[2] - bb[0]) // 2, 540), "+", font=plus_f, fill="#c43c2c")
        if not omit_text:
            paste_c(base, L(right_pack), 1320, 620, 360)
        fl = font("HarmonyOS_Sans_SC_Bold.ttf", 32)
        for cx, lab in [
            (520, sc.get("left_label") or "福尔番茄红素软胶囊"),
            (1320, sc.get("right_label") or "关联品"),
        ]:
            bb = d.textbbox((0, 0), lab, font=fl)
            draw_text((cx - (bb[2] - bb[0]) // 2, 870), lab, font=fl, fill="#6a3a30")

    elif scene_id == "S14_summary_key":
        # 行标题布局；文案来自 content-model columns / footer / eyebrow
        d.rounded_rectangle([780, 28, 1140, 96], radius=34, fill="#c43c2c")
        ft = font("HarmonyOS_Sans_SC_Black.ttf", 42)
        ch = sc.get("chapter") or "总结"
        bb = d.textbbox((0, 0), ch, font=ft)
        draw_text((960 - (bb[2] - bb[0]) // 2, 40), ch, font=ft, fill="#ffffff")
        fe = font("HarmonyOS_Sans_SC_Bold.ttf", 30)
        d.ellipse([72, 40, 116, 84], fill="#e8a090")
        d.ellipse([86, 52, 114, 80], fill="#c43c2c")
        eyebrow = sc.get("eyebrow") or "敲重点 · 一页复习"
        draw_text((132, 46), eyebrow, font=fe, fill="#c43c2c")

        if sc.get("columns"):
            rows = []
            for col in sc["columns"]:
                header = col.get("header") or ""
                if header == "适宜人群与用法":
                    header = "适宜人群\n与用法"
                body = "\n".join(col.get("items") or [])
                # 压缩【】标题行的复习体为更紧凑屏显：保留完整句
                rows.append((header, body))
        else:
            rows = [
                (
                    "核心功效",
                    "① 保护前列腺、提高精子活力：活化前列腺细胞，抑制致癌物产生，保护前列腺并提高精子活力。\n"
                    "② 抗氧化，延缓衰老：猝灭单线态氧、捕捉自由基，抗氧化能力约为维E的100倍，从而延缓衰老。\n"
                    "③ 增强免疫力：活化免疫细胞，保护吞噬细胞免受自身氧化损伤，促进淋巴细胞增殖。",
                ),
            ]
        x0, y0, x1, y1 = 60, 120, 1860, 990
        label_w = 220
        n = len(rows)
        row_h = (y1 - y0) / n
        d.rectangle([x0, y0, x1, y1], fill=(255, 255, 255, 242), outline="#b0aaa0", width=2)
        d.line([(x0 + label_w, y0), (x0 + label_w, y1)], fill="#d0ccc4", width=2)

        flab = font("HarmonyOS_Sans_SC_Black.ttf", 34)
        fbody = font("HarmonyOS_Sans_SC_Medium.ttf", 28)
        body_fill = "#3a2a28"
        for i, (lab, body) in enumerate(rows):
            ry0 = y0 + i * row_h
            ry1 = ry0 + row_h
            if i > 0:
                d.line([(x0 + label_w, ry0), (x1, ry0)], fill="#e0dcd4", width=2)
            # 左列：实色行标题底 + 白字（避免红底红字看不见）
            d.rectangle([x0 + 1, ry0 + 1, x0 + label_w, ry1 - (0 if i == n - 1 else 0)], fill="#c43c2c")
            lab_lines = lab.split("\n")
            lh = 42
            block = len(lab_lines) * lh
            ty = ry0 + (row_h - block) / 2
            for j, ln in enumerate(lab_lines):
                bb = d.textbbox((0, 0), ln, font=flab)
                tw = bb[2] - bb[0]
                draw_text((x0 + (label_w - tw) / 2, ty + j * lh), ln, font=flab, fill="#ffffff")
            # 右列完整正文
            max_w = int(x1 - (x0 + label_w) - 48)
            body_lines: list[str] = []
            for para in body.split("\n"):
                body_lines.extend(wrap_text(d, para, fbody, max_w))
            blh = 38
            bbh = len(body_lines) * blh
            by = ry0 + (row_h - bbh) / 2
            if by < ry0 + 14:
                by = ry0 + 14
            for j, ln in enumerate(body_lines):
                if by + j * blh > ry1 - 10:
                    break
                draw_text((x0 + label_w + 28, by + j * blh), ln, font=fbody, fill=body_fill)

        foot = sc.get("footer") or "复习口诀：三大功效讲机理 · 三点特点讲依据 · 四类人群讲场景 · 两组关联讲怎么推"
        ff = font("HarmonyOS_Sans_SC_Bold.ttf", 28)
        bb = d.textbbox((0, 0), foot, font=ff)
        draw_text(((1920 - (bb[2] - bb[0])) // 2, 1010), foot, font=ff, fill="#2a2a2a")

    subtitle(d, sub) if not omit_text else None
    return base.convert("RGB")


def main() -> int:
    ap = argparse.ArgumentParser(description="Export editable courseware video from content-model")
    ap.add_argument("--model", default=str(MODEL_PATH))
    ap.add_argument("--patches", default="")
    ap.add_argument("--out-mp4", default="")
    args = ap.parse_args()

    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    patches_path = Path(args.patches) if args.patches else ROOT / "editable-patches.json"
    if patches_path.exists():
        patches = json.loads(patches_path.read_text(encoding="utf-8"))
        model = apply_patches(model, patches)
        print("applied patches", patches_path)

    FRAMES.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    # pick a representative subtitle for still
    still_subs = {
        "S01_time_list": "“对人类健康贡献最大的10种健康食品”",
        "S02_broll": "及欧美国家一日三餐都有番茄供应",
        "S03_product_intro": "我们今天就来学习福尔番茄红素软胶囊",
        "S04_benefit_1": "能活化前列腺细胞，保护前列腺，提高精子活力",
        "S05_benefit_2": "抗氧化能力是维E的100倍，从而达到延缓衰老的作用",
        "S06_benefit_3": "从而增强免疫力",
        "S07_origin": "因此新疆被誉为“世界上最好的番茄产区”",
        "S08_material": "福尔选择最优的番茄肉提炼而成",
        "S09_content": "吃1粒番茄红素相当于5个新鲜大番茄",
        "S10_audience": "身体虚弱人群",
        "S11_summary": "",
        "S12_related_1": "",
        "S13_related_2": "",
        "S14_summary_key": "",
    }
    # allow model-level still_subs override
    still_subs.update(model.get("still_subs") or {})

    list_path = FRAMES / "concat.txt"
    lines: list[str] = []
    total_dur = 0.0
    last_still_path: Path | None = None
    bg_dir = FRAMES.parent / "scene-stills-editor-bg"
    bg_dir.mkdir(parents=True, exist_ok=True)

    def sub_at(segs: list[tuple[float, float, str]], t: float, end: float) -> str:
        for a, b, text in segs:
            if a <= t < b or (abs(b - end) < 1e-6 and a <= t <= b + 1e-6):
                return text
        return segs[-1][2] if segs else ""

    for sc in model["scenes"]:
        sid = sc["id"]
        fallback = still_subs.get(sid, "")
        segs = subtitle_segments(sc, fallback=fallback)
        start = float(sc["start"])
        end = float(sc["end"])
        # editor-bg：终态布局（无烧录字/可编图）
        bg_img = render_scene(
            sid, "", scene=sc, model=model, omit_text=True, t_local=max(0.0, end - start)
        )
        bg_img.save(bg_dir / f"{sid}.png", "PNG")

        page_last: Path | None = None
        frame_i = 0

        if sid in MOTION_SCENE_IDS and not sc.get("enabled") is False:
            # 动效场景：按 MOTION_FPS 采样，字幕跟 t
            step = 1.0 / MOTION_FPS
            t = start
            while t < end - 1e-6:
                t1 = min(end, t + step)
                text = sub_at(segs, t, end)
                t_local = t - start
                img = render_scene(
                    sid, text, scene=sc, model=model, t_local=t_local
                )
                path = FRAMES / f"{sid}_{frame_i:03d}.png"
                img.save(path, "PNG")
                dur = max(0.04, float(t1) - float(t))
                total_dur += dur
                lines.append(f"file '{path}'")
                lines.append(f"duration {dur:.3f}")
                page_last = path
                last_still_path = path
                if frame_i % 10 == 0:
                    print(
                        f"motion {sid}[{frame_i}] t={t_local:.2f}s sub={text[:20]!r} -> {path.name}"
                    )
                frame_i += 1
                t = t1
        else:
            # 成片：按旁白字幕分时静帧
            for j, (t0, t1, text) in enumerate(segs):
                t_local = max(0.0, (float(t0) + float(t1)) / 2.0 - start)
                img = render_scene(
                    sid, text, scene=sc, model=model, t_local=t_local
                )
                path = FRAMES / f"{sid}_{j:02d}.png"
                img.save(path, "PNG")
                dur = max(0.05, float(t1) - float(t0))
                total_dur += dur
                lines.append(f"file '{path}'")
                lines.append(f"duration {dur:.3f}")
                page_last = path
                last_still_path = path
                print(f"still {sid}[{j}] {dur:.2f}s sub={text[:28]!r} -> {path.name}")
                frame_i += 1

        # 页面代表帧（QA/预览）= 终态
        if page_last is not None:
            rep = FRAMES / f"{sid}.png"
            final = render_scene(
                sid,
                segs[-1][2] if segs else fallback,
                scene=sc,
                model=model,
                t_local=max(0.0, end - start),
            )
            final.save(rep, "PNG")
    if last_still_path is None:
        raise SystemExit("no stills rendered")
    # ffmpeg concat demuxer needs last file repeated without duration
    lines.append(f"file '{last_still_path}'")
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 优先工作旁白轨（片段工作室改稿后）；否则原始参考轨
    audio = ROOT / "web" / "working-narration.mp3"
    if not audio.exists():
        audio = ROOT / "web" / "reference-narration.mp3"
    if not audio.exists():
        audio = Path("/Users/liminrong/Downloads/商品培训课件4/商品培训课件4.mp3")
    mp4 = Path(args.out_mp4) if args.out_mp4 else OUT / "商品培训课件4_保真复刻_全片_v1.mp4"

    # concat 静帧序列：强制 CFR 30，避免部分播放器把相邻近似帧当静态
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-i", str(audio),
        "-filter_complex",
        f"[0:v]fps=30,format=yuv420p[v];[1:a]apad=whole_dur={total_dur:.3f}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total_dur:.3f}",
        "-movflags", "+faststart",
        str(mp4),
    ]
    print("running ffmpeg total_dur=", f"{total_dur:.2f}s ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        return r.returncode
    print("wrote", mp4, "size", mp4.stat().st_size)
    stills = sorted(FRAMES.glob("S*.png"))
    if stills:
        thumbs = [Image.open(p).resize((320, 180), Image.LANCZOS) for p in stills]
        cols = 4
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 320, rows * 180), (20, 20, 20))
        for i, th in enumerate(thumbs):
            sheet.paste(th, ((i % cols) * 320, (i // cols) * 180))
        sheet_path = OUT / "full-film-contact-sheet.png"
        sheet.save(sheet_path)
        print("wrote", sheet_path)

    # write runtime index for editor
    idx = {
        "project_id": model.get("project_id"),
        "mp4": str(mp4.relative_to(ROOT)) if str(mp4).startswith(str(ROOT)) else str(mp4),
        "stills": "out/scene-stills",
        "content_model": "content-model.json",
        "layer_manifest": "layer-manifest.json",
        "patches": str(patches_path.relative_to(ROOT)) if patches_path.exists() else None,
        "total_duration_s": total_dur,
        "scene_count": len(model["scenes"]),
    }
    (OUT / "EDITABLE_VIDEO_INDEX.json").write_text(
        json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
