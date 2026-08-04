/**
 * film 编排（阶段 1：1:1 复刻 PIL 时序 + S05 红叉淡出修复）。
 * 时码锁定：只消费页内时间，不动 scenes[].start/end。
 * 红线：入场单次弹出后冻结；循环仅 表头白箭头/链路红箭头/S01 »；主视觉禁 idle。
 * 阶段 3 将在此替换 S07 推镜头、S10 序贯、S11 级联。
 */
import {all, easeInCubic, easeOutCubic, loop, waitFor} from '@revideo/core';

import type {Scene} from '../content';
import {makeClock, nodeOf, popIn, pulseArrowX} from '../motion/primitives';
import {chromeKey, wrapKey} from './parts';

/** 链路入场：scale 0.92→1 + 上移 rise + 快淡入（对齐 PIL pop_scale overshoot=False） */
function* chainPop(node: any, dur = 0.4, rise = 22) {
  if (!node) return;
  yield* all(
    node.opacity(1, 0.08, easeOutCubic),
    node.scale(1, dur, easeOutCubic),
    node.position.y(node.position.y() - rise, dur, easeOutCubic),
  );
}

/** 带 overshoot 的上升弹入（杂志/卡片，PIL easeOutBack 系） */
function* popRise(node: any, dur = 0.5, rise = 28) {
  if (!node) return;
  yield* all(
    node.opacity(1, Math.min(0.2, dur * 0.4), easeOutCubic),
    node.scale(1, dur),
    node.position.y(node.position.y() - rise, dur),
  );
}

function* fadeIn(node: any, dur = 0.16) {
  if (!node) return;
  yield* node.opacity(1, dur, easeOutCubic);
}

/** 表头白箭头：小幅上下循环（唯一允许的表头强调） */
function* bounceY(node: any, amp: number, period: number, seconds: number) {
  if (!node) return;
  if (seconds <= 0.05) return;
  const y0 = node.position.y();
  const n = Math.max(1, Math.floor(seconds / period));
  yield* loop(n, function* () {
    yield* node.position.y(y0 - amp, period * 0.49, easeOutCubic);
    yield* node.position.y(y0, period * 0.51, easeOutCubic);
  });
  const left = seconds - n * period;
  if (left > 0.02) yield* waitFor(left);
}

/** S01 黄绿 » 极轻左右（PIL accent_nudge_x：±3px 正弦） */
function* nudgeX(node: any, amp: number, period: number, seconds: number) {
  if (!node || seconds <= 0.05) return;
  const x0 = node.position.x();
  const n = Math.max(1, Math.floor(seconds / period));
  yield* loop(n, function* () {
    yield* node.position.x(x0 + amp, period * 0.25, easeOutCubic);
    yield* node.position.x(x0, period * 0.25, easeOutCubic);
    yield* node.position.x(x0 - amp, period * 0.25, easeOutCubic);
    yield* node.position.x(x0, period * 0.25, easeOutCubic);
  });
  const left = seconds - n * period;
  if (left > 0.02) yield* waitFor(left);
}

/** 章节 + 表头入场（含表头箭头后续 bounce 整页） */
function* headerMotion(view: any, page: string, dur: number) {
  const chapter = view.findKey(wrapKey(page, 'chapter'));
  const chev = nodeOf(view, page, 'section_chevron');
  yield* waitFor(0.05);
  const jobs: any[] = [];
  if (chapter) jobs.push(popIn(chapter, 0.28));
  if (chev) jobs.push(popIn(chev, 0.28));
  if (jobs.length) yield* all(...jobs);
  if (chev) yield* bounceY(chev, 8, 0.7, dur - 0.33);
  else yield* waitFor(Math.max(0.05, dur - 0.33));
}

// ── 各页内容编排 ─────────────────────────────────────────────────────────

function* coverMotion(view: any, sc: Scene) {
  const page = sc.id;
  const dur = sc.end - sc.start;
  const clk = makeClock(dur);
  yield* clk.spend(0.1);
  for (const role of ['pack_a', 'pack_b', 'pack_bottle']) {
    const n = nodeOf(view, page, role);
    if (n) yield* popIn(n, 0.34);
    yield* clk.spend(0.08);
  }
  yield* clk.spend(clk.remain());
}

function* s01Motion(view: any, sc: Scene) {
  const page = sc.id;
  const dur = sc.end - sc.start;
  const clk = makeClock(dur);
  const mag = nodeOf(view, page, 'magazine');
  const card = view.findKey(chromeKey(page, 'card'));
  const chev = nodeOf(view, page, 'card_chevron');
  const title = nodeOf(view, page, 'card_title');
  const rule = view.findKey(chromeKey(page, 'rule'));
  // PIL：杂志 0.05 / 卡片 0.28 / 内容（»、标题、线）≈0.73 / 列表 0.55+0.16i
  yield* clk.spend(0.05);
  if (mag) yield* popRise(mag, 0.5, 36);
  if (card) yield* popRise(card, 0.5, 28);
  const jobs: any[] = [];
  if (chev) jobs.push(popIn(chev, 0.32));
  if (title) jobs.push(fadeIn(title, 0.16));
  if (rule) jobs.push(fadeIn(rule, 0.16));
  if (jobs.length) yield* all(...jobs);
  yield* clk.spend(0.05);
  for (let i = 1; i <= 3; i++) {
    const row = nodeOf(view, page, `list.${i}`);
    if (row) {
      yield* all(
        row.opacity(1, 0.12, easeOutCubic),
        row.position.y(row.position.y() - 28, 0.35, easeOutCubic),
      );
    }
    yield* clk.spend(0.11);
  }
  yield* all(
    bounceY(chev, 7, 0.72, clk.remain()),
    nudgeX(chev, 3, 0.9, clk.remain()),
  );
}

function* s02Motion(view: any, sc: Scene) {
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.05);
  const photo = nodeOf(view, sc.id, 'photo');
  if (photo) yield* chainPop(photo, 0.45, 24);
  yield* clk.spend(clk.remain());
}

function* s03Motion(view: any, sc: Scene) {
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.1);
  for (const role of ['vine', 'pack_a', 'pack_b', 'pack_bottle']) {
    const n = nodeOf(view, sc.id, role);
    if (n) yield* popIn(n, 0.4);
    yield* clk.spend(0.12);
  }
  yield* clk.spend(clk.remain());
}

/** S04：番茄 0.4 → 红箭头 1.0 → 前列腺 1.6（PIL 绝对时序） */
function* s04Content(view: any, sc: Scene) {
  const page = sc.id;
  const dur = sc.end - sc.start;
  const tomato = nodeOf(view, page, 'tomato');
  const arrow = nodeOf(view, page, 'arrow');
  const prost = nodeOf(view, page, 'prostate');
  yield* waitFor(0.4);
  if (tomato) yield* chainPop(tomato, 0.45, 24);
  yield* waitFor(1.0 - 0.4 - 0.45);
  if (arrow) yield* chainPop(arrow, 0.35, 0);
  yield* waitFor(1.6 - 1.0 - 0.35);
  if (prost) yield* chainPop(prost, 0.45, 24);
  const ax = arrow && typeof arrow.position?.x === 'function' ? arrow.position.x() : 0;
  yield* pulseArrowX(arrow, ax, dur - 2.05, 14);
}

/** S05：番茄 0.7 → 箭1 1.2 → O2 1.4 → 叉 3.6 →（叉 8.6 淡出）→ 箭2 8.9 → 女 9.0 */
function* s05Content(view: any, sc: Scene) {
  const page = sc.id;
  const dur = sc.end - sc.start;
  const tomato = nodeOf(view, page, 'tomato');
  const a1 = nodeOf(view, page, 'arrow1');
  const o2 = nodeOf(view, page, 'o2');
  const x = nodeOf(view, page, 'mark_x');
  const a2 = nodeOf(view, page, 'arrow2');
  const woman = nodeOf(view, page, 'woman');
  yield* waitFor(0.7);
  if (tomato) yield* chainPop(tomato, 0.4, 22);
  yield* waitFor(1.2 - 0.7 - 0.4);
  if (a1) yield* chainPop(a1, 0.35, 0);
  yield* waitFor(1.4 - 1.2 - 0.35);
  if (o2) yield* chainPop(o2, 0.4, 22);
  yield* waitFor(3.6 - 1.4 - 0.4);
  if (x) {
    yield* all(
      x.opacity(1, 0.2, easeOutCubic),
      x.scale(1, 0.35, easeOutCubic),
    );
  }
  // 红叉 8.6 起 0.28s 淡出（消解 PIL 9s 硬切）
  yield* waitFor(8.6 - 3.6 - 0.35);
  const fadeJob = x ? x.opacity(0, 0.28, easeInCubic) : waitFor(0.28);
  yield* all(fadeJob);
  yield* waitFor(8.9 - 8.6 - 0.28);
  const jobs: any[] = [];
  if (a2) jobs.push(chainPop(a2, 0.35, 0));
  if (woman) jobs.push(chainPop(woman, 0.45, 24));
  if (jobs.length) yield* all(...jobs);
  const ax1 = a1 && typeof a1.position?.x === 'function' ? a1.position.x() : 0;
  const ax2 = a2 && typeof a2.position?.x === 'function' ? a2.position.x() : 0;
  const left = dur - 9.35;
  yield* all(pulseArrowX(a1, ax1, left, 14), pulseArrowX(a2, ax2, left, 14));
}

/** S06：番茄 0.5 → 箭1 1.0 → NK 1.3 → 箭2 5.2 → 手臂 5.5（无呼吸，红线） */
function* s06Content(view: any, sc: Scene) {
  const page = sc.id;
  const dur = sc.end - sc.start;
  const tomato = nodeOf(view, page, 'tomato');
  const a1 = nodeOf(view, page, 'arrow1');
  const nk = nodeOf(view, page, 'nk');
  const a2 = nodeOf(view, page, 'arrow2');
  const arm = nodeOf(view, page, 'arm');
  yield* waitFor(0.5);
  if (tomato) yield* chainPop(tomato, 0.4, 22);
  yield* waitFor(1.0 - 0.5 - 0.4);
  if (a1) yield* chainPop(a1, 0.35, 0);
  yield* waitFor(1.3 - 1.0 - 0.35);
  if (nk) yield* chainPop(nk, 0.45, 22);
  yield* waitFor(5.2 - 1.3 - 0.45);
  if (a2) yield* chainPop(a2, 0.35, 0);
  yield* waitFor(5.5 - 5.2 - 0.35);
  if (arm) yield* chainPop(arm, 0.45, 24);
  const ax1 = a1 && typeof a1.position?.x === 'function' ? a1.position.x() : 0;
  const ax2 = a2 && typeof a2.position?.x === 'function' ? a2.position.x() : 0;
  const left = dur - 5.95;
  yield* all(pulseArrowX(a1, ax1, left, 14), pulseArrowX(a2, ax2, left, 14));
}

function* s07Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.15);
  const cap = nodeOf(view, page, 'map_caption');
  if (cap) yield* fadeIn(cap, 0.2);
  yield* clk.spend(0.1);
  const map = nodeOf(view, page, 'map');
  if (map) yield* chainPop(map, 0.45, 24);
  // 阶段 3：单次推镜头 + 装饰线扫入（17.7s 最长死区）
  yield* clk.spend(clk.remain());
}

function* s08Content(view: any, sc: Scene) {
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.2);
  const photo = nodeOf(view, sc.id, 'vine');
  if (photo) yield* chainPop(photo, 0.45, 24);
  // 阶段 3：Ken Burns 单向推近
  yield* clk.spend(clk.remain());
}

function* s09Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.3);
  const softgel = nodeOf(view, page, 'softgel');
  if (softgel) yield* chainPop(softgel, 0.4, 22);
  yield* clk.spend(0.1);
  const eq = nodeOf(view, page, 'eq');
  if (eq) yield* popIn(eq, 0.32);
  yield* clk.spend(0.05);
  const five = nodeOf(view, page, 'five_tomatoes');
  if (five) yield* chainPop(five, 0.45, 24);
  yield* clk.spend(clk.remain());
}

function* s10Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  // 阶段 1：四组 0.25s 级联；阶段 3 改字幕时码序贯揭示
  for (let i = 1; i <= 4; i++) {
    yield* clk.spend(i === 1 ? 0.2 : 0.05);
    const icon = nodeOf(view, page, `icon.${i}`);
    const label = view.findKey(wrapKey(page, `label.${i}`));
    const jobs: any[] = [];
    if (icon) jobs.push(chainPop(icon, 0.4, 22));
    if (label) jobs.push(popIn(label, 0.32));
    if (jobs.length) yield* all(...jobs);
    yield* clk.spend(0.2);
  }
  yield* clk.spend(clk.remain());
}

function* s11Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  // 阶段 1：三行 0.3s 级联淡入上移；阶段 3 精修行内时序
  for (let i = 1; i <= 3; i++) {
    yield* clk.spend(i === 1 ? 0.35 : 0.1);
    const label = view.findKey(wrapKey(page, `row.${i}.label`));
    const body = view.findKey(wrapKey(page, `row.${i}.body`));
    const jobs: any[] = [];
    for (const n of [label, body]) {
      if (n) {
        jobs.push(
          all(
            n.opacity(1, 0.16, easeOutCubic),
            n.position.y(n.position.y() - 18, 0.32, easeOutCubic),
          ),
        );
      }
    }
    if (jobs.length) yield* all(...jobs);
    yield* clk.spend(0.2);
  }
  yield* clk.spend(clk.remain());
}

function* relatedContent(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.05);
  const card = view.findKey(chromeKey(page, 'card'));
  if (card) yield* popRise(card, 0.4, 16);
  for (let i = 1; i <= 2; i++) {
    const label = nodeOf(view, page, `nav.${i}`);
    if (label) yield* fadeIn(label, 0.16);
  }
  const note = nodeOf(view, page, 'note');
  if (note) yield* fadeIn(note, 0.2);
  yield* clk.spend(0.05);
  const plus = nodeOf(view, page, 'plus');
  const packL = nodeOf(view, page, 'pack_left');
  if (packL) yield* popIn(packL, 0.38);
  if (plus) yield* popIn(plus, 0.28);
  const packR = nodeOf(view, page, 'pack_right');
  if (packR) yield* popIn(packR, 0.38);
  const leftLabel = nodeOf(view, page, 'left_label');
  const rightLabel = nodeOf(view, page, 'right_label');
  const jobs: any[] = [];
  if (leftLabel) jobs.push(fadeIn(leftLabel, 0.18));
  if (rightLabel) jobs.push(fadeIn(rightLabel, 0.18));
  if (jobs.length) yield* all(...jobs);
  yield* clk.spend(clk.remain());
}

// ── 主入口 ───────────────────────────────────────────────────────────────

export function* playFilmMotion(view: any, sc: Scene) {
  const page = sc.id;
  const dur = Math.max(0.1, sc.end - sc.start);
  switch (page) {
    case 'S00_cover':
    case 'S15_end':
      yield* coverMotion(view, sc);
      return;
    case 'S01_time_list':
      yield* s01Motion(view, sc);
      return;
    case 'S02_broll':
      yield* s02Motion(view, sc);
      return;
    case 'S03_product_intro':
      yield* s03Motion(view, sc);
      return;
    case 'S04_benefit_1':
      yield* all(headerMotion(view, page, dur), s04Content(view, sc));
      return;
    case 'S05_benefit_2':
      yield* all(headerMotion(view, page, dur), s05Content(view, sc));
      return;
    case 'S06_benefit_3':
      yield* all(headerMotion(view, page, dur), s06Content(view, sc));
      return;
    case 'S07_origin':
      yield* all(headerMotion(view, page, dur), s07Content(view, sc));
      return;
    case 'S08_material':
      yield* all(headerMotion(view, page, dur), s08Content(view, sc));
      return;
    case 'S09_content':
      yield* all(headerMotion(view, page, dur), s09Content(view, sc));
      return;
    case 'S10_audience': {
      const chapter = view.findKey(wrapKey(page, 'chapter'));
      yield* all(
        (function* () {
          yield* waitFor(0.05);
          if (chapter) yield* popIn(chapter, 0.28);
          yield* waitFor(dur - 0.33);
        })(),
        s10Content(view, sc),
      );
      return;
    }
    case 'S11_summary': {
      const chapter = view.findKey(wrapKey(page, 'chapter'));
      yield* all(
        (function* () {
          yield* waitFor(0.05);
          if (chapter) yield* popIn(chapter, 0.28);
          yield* waitFor(dur - 0.33);
        })(),
        s11Content(view, sc),
      );
      return;
    }
    case 'S12_related_1':
    case 'S13_related_2': {
      const chapter = view.findKey(wrapKey(page, 'chapter'));
      yield* all(
        (function* () {
          yield* waitFor(0.05);
          if (chapter) yield* popIn(chapter, 0.28);
          yield* waitFor(dur - 0.33);
        })(),
        relatedContent(view, sc),
      );
      return;
    }
    default:
      yield* waitFor(dur);
  }
}
