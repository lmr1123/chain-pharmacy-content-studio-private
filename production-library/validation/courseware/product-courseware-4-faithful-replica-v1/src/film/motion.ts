/**
 * film 编排（阶段 3：15 页动效全量）。
 * 时码锁定：只消费页内时间，不动 scenes[].start/end。
 * 红线：入场单次弹出后冻结；循环仅 表头白箭头/链路红箭头/S01 »；主视觉禁 idle。
 * 阶段 3 落点：S07 四段式（pop→静观→单次推镜头→章节装饰线扫入）、S10 按字幕
 * 时码序贯揭示、S11 行级联（chevron/label→body）、S02/S08 Ken Burns 单向、
 * S09 单次 pulse 消死区、S15 末 0.5s 淡丝绸底（非黑帧）。
 */
import {
  all,
  easeInCubic,
  easeInOutCubic,
  easeOutCubic,
  linear,
  loop,
  waitFor,
} from '@revideo/core';

import type {Scene} from '../content';
import {
  makeClock,
  nodeOf,
  oncePulse,
  popIn,
  pulseArrowX,
} from '../motion/primitives';
import {chromeKey, pageRootKey, wrapKey} from './parts';

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
    if (n) yield* clk.play(popIn(n, 0.34), 0.34);
    yield* clk.spend(0.08);
  }
  // S15 收尾：末 0.5s 整页淡到丝绸底色（含字幕；非黑帧）
  if (page === 'S15_end') {
    const root = view.findKey(pageRootKey(page));
    yield* clk.spend(dur - 0.55 - clk.elapsed());
    if (root) yield* clk.play(root.opacity(0, 0.5, easeInCubic), 0.5);
  }
  yield* clk.spend(clk.remain());
}

function* s01Motion(view: any, sc: Scene) {
  const page = sc.id;
  const dur = sc.end - sc.start;
  const clk = makeClock(dur);
  const mag = nodeOf(view, page, 'magazine');
  const card = view.findKey(chromeKey(page, 'card'));
  const chev = view.findKey(chromeKey(page, 'card_chevron')); // chrome 层（同 S11 row_chev 模式）
  const title = nodeOf(view, page, 'card_title');
  const rule = view.findKey(chromeKey(page, 'rule'));
  // PIL：杂志 0.05 / 卡片 0.28 / 内容（»、标题、线）≈0.73 / 列表 0.55+0.16i
  yield* clk.spend(0.05);
  if (mag) yield* clk.play(popRise(mag, 0.5, 36), 0.5);
  if (card) yield* clk.play(popRise(card, 0.5, 28), 0.5);
  const jobs: any[] = [];
  if (chev) jobs.push(popIn(chev, 0.32));
  if (title) jobs.push(fadeIn(title, 0.16));
  if (rule) jobs.push(fadeIn(rule, 0.16));
  if (jobs.length) yield* clk.play(all(...jobs), 0.32);
  yield* clk.spend(0.05);
  for (let i = 1; i <= 3; i++) {
    const row = nodeOf(view, page, `list.${i}`);
    if (row) {
      yield* clk.play(
        all(
          row.opacity(1, 0.12, easeOutCubic),
          row.position.y(row.position.y() - 28, 0.35, easeOutCubic),
        ),
        0.35,
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
  if (photo) {
    yield* clk.play(chainPop(photo, 0.45, 24), 0.45);
    // Ken Burns 单向推近（红线：仅 S02/S08，1.0→1.05 不回摆）
    yield* photo.scale(1.05, clk.remain(), linear);
  } else {
    yield* clk.spend(clk.remain());
  }
}

function* s03Motion(view: any, sc: Scene) {
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.1);
  for (const role of ['vine', 'pack_a', 'pack_b', 'pack_bottle']) {
    const n = nodeOf(view, sc.id, role);
    if (n) yield* clk.play(popIn(n, 0.4), 0.4);
    yield* clk.spend(0.12);
  }
  yield* clk.spend(clk.remain());
}

/** S04：番茄 0.4 → 红箭头 1.0 → 前列腺 1.6（PIL 绝对时序；clk 记账，尾部按实补齐） */
function* s04Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  const tomato = nodeOf(view, page, 'tomato');
  const arrow = nodeOf(view, page, 'arrow');
  const prost = nodeOf(view, page, 'prostate');
  yield* clk.spend(0.4);
  if (tomato) yield* clk.play(chainPop(tomato, 0.45, 24), 0.45);
  yield* clk.spend(1.0 - 0.4 - 0.45);
  if (arrow) yield* clk.play(chainPop(arrow, 0.35, 0), 0.35);
  yield* clk.spend(1.6 - 1.0 - 0.35);
  if (prost) yield* clk.play(chainPop(prost, 0.45, 24), 0.45);
  const ax = arrow && typeof arrow.position?.x === 'function' ? arrow.position.x() : 0;
  yield* pulseArrowX(arrow, ax, clk.remain(), 14);
}

/** S05：番茄 0.7 → 箭1 1.2 → O2 1.4 → 叉 3.6 →（叉 8.6 淡出）→ 箭2 8.9 → 女 9.0
 *  clk 记账：锚点差为负时 spend 归零，尾部脉冲按 remain 实补齐（页时长锁定） */
function* s05Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  const tomato = nodeOf(view, page, 'tomato');
  const a1 = nodeOf(view, page, 'arrow1');
  const o2 = nodeOf(view, page, 'o2');
  const x = nodeOf(view, page, 'mark_x');
  const a2 = nodeOf(view, page, 'arrow2');
  const woman = nodeOf(view, page, 'woman');
  yield* clk.spend(0.7);
  if (tomato) yield* clk.play(chainPop(tomato, 0.4, 22), 0.4);
  yield* clk.spend(1.2 - 0.7 - 0.4);
  if (a1) yield* clk.play(chainPop(a1, 0.35, 0), 0.35);
  yield* clk.spend(1.4 - 1.2 - 0.35);
  if (o2) yield* clk.play(chainPop(o2, 0.4, 22), 0.4);
  yield* clk.spend(3.6 - 1.4 - 0.4);
  if (x) {
    yield* clk.play(
      all(x.opacity(1, 0.2, easeOutCubic), x.scale(1, 0.35, easeOutCubic)),
      0.35,
    );
  }
  // 红叉 8.6 起 0.28s 淡出（消解 PIL 9s 硬切）
  yield* clk.spend(8.6 - 3.6 - 0.35);
  if (x) yield* clk.play(x.opacity(0, 0.28, easeInCubic), 0.28);
  else yield* clk.spend(0.28);
  yield* clk.spend(8.9 - 8.6 - 0.28);
  const jobs: any[] = [];
  if (a2) jobs.push(chainPop(a2, 0.35, 0));
  if (woman) jobs.push(chainPop(woman, 0.45, 24));
  if (jobs.length) yield* clk.play(all(...jobs), 0.45);
  const ax1 = a1 && typeof a1.position?.x === 'function' ? a1.position.x() : 0;
  const ax2 = a2 && typeof a2.position?.x === 'function' ? a2.position.x() : 0;
  yield* all(
    pulseArrowX(a1, ax1, clk.remain(), 14),
    pulseArrowX(a2, ax2, clk.remain(), 14),
  );
}

/** S06：番茄 0.5 → 箭1 1.0 → NK 1.3 → 箭2 5.2 → 手臂 5.5（无呼吸，红线；clk 记账尾部实补） */
function* s06Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  const tomato = nodeOf(view, page, 'tomato');
  const a1 = nodeOf(view, page, 'arrow1');
  const nk = nodeOf(view, page, 'nk');
  const a2 = nodeOf(view, page, 'arrow2');
  const arm = nodeOf(view, page, 'arm');
  yield* clk.spend(0.5);
  if (tomato) yield* clk.play(chainPop(tomato, 0.4, 22), 0.4);
  yield* clk.spend(1.0 - 0.5 - 0.4);
  if (a1) yield* clk.play(chainPop(a1, 0.35, 0), 0.35);
  yield* clk.spend(1.3 - 1.0 - 0.35);
  if (nk) yield* clk.play(chainPop(nk, 0.45, 22), 0.45);
  yield* clk.spend(5.2 - 1.3 - 0.45);
  if (a2) yield* clk.play(chainPop(a2, 0.35, 0), 0.35);
  yield* clk.spend(5.5 - 5.2 - 0.35);
  if (arm) yield* clk.play(chainPop(arm, 0.45, 24), 0.45);
  const ax1 = a1 && typeof a1.position?.x === 'function' ? a1.position.x() : 0;
  const ax2 = a2 && typeof a2.position?.x === 'function' ? a2.position.x() : 0;
  yield* all(
    pulseArrowX(a1, ax1, clk.remain(), 14),
    pulseArrowX(a2, ax2, clk.remain(), 14),
  );
}

/** S07 四段式：地图 pop → 静观 → 单次推镜头（同图 ×2.2 交叉淡入淡出）→ 章节装饰线扫入 */
function* s07Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.15);
  const cap = nodeOf(view, page, 'map_caption');
  if (cap) yield* clk.play(fadeIn(cap, 0.2), 0.2);
  yield* clk.spend(0.1);
  const map = nodeOf(view, page, 'map');
  if (map) yield* clk.play(chainPop(map, 0.45, 24), 0.45);
  // 静观至 6.2s（旁白"世界上最好的番茄产区"起），0.8s 交叉淡入放大局部层
  const zoom = view.findKey(`film:decor:${page}:map-zoom`);
  yield* clk.spend(6.2 - clk.elapsed());
  const zoomIn: any[] = [];
  if (zoom) zoomIn.push(zoom.opacity(1, 0.8, easeInOutCubic));
  if (map) zoomIn.push(map.opacity(0, 0.8, easeInOutCubic));
  if (cap) zoomIn.push(cap.opacity(0, 0.8, easeInOutCubic));
  if (zoomIn.length) yield* clk.play(all(...zoomIn), 0.8);
  // 静观放大局部至 11.5s（"含量高达62毫克"前），0.8s 交叉淡回
  yield* clk.spend(11.5 - clk.elapsed());
  const zoomOut: any[] = [];
  if (zoom) zoomOut.push(zoom.opacity(0, 0.8, easeInOutCubic));
  if (map) zoomOut.push(map.opacity(1, 0.8, easeInOutCubic));
  if (cap) zoomOut.push(cap.opacity(1, 0.8, easeInOutCubic));
  if (zoomOut.length) yield* clk.play(all(...zoomOut), 0.8);
  // 章节装饰线扫入（单次，左→右）
  const rule = view.findKey(`film:decor:${page}:chapter-rule`);
  yield* clk.spend(12.7 - clk.elapsed());
  if (rule) yield* clk.play(rule.end(1, 0.5, easeOutCubic), 0.5);
  yield* clk.spend(clk.remain());
}

function* s08Content(view: any, sc: Scene) {
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.2);
  const photo = nodeOf(view, sc.id, 'vine');
  if (photo) {
    yield* clk.play(chainPop(photo, 0.45, 24), 0.45);
    // Ken Burns 单向推近（1.0→1.06，不回摆）
    yield* photo.scale(1.06, clk.remain(), linear);
  } else {
    yield* clk.spend(clk.remain());
  }
}

function* s09Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.3);
  const softgel = nodeOf(view, page, 'softgel');
  if (softgel) yield* clk.play(chainPop(softgel, 0.4, 22), 0.4);
  yield* clk.spend(0.1);
  const eq = nodeOf(view, page, 'eq');
  if (eq) yield* clk.play(popIn(eq, 0.32), 0.32);
  yield* clk.spend(0.05);
  const five = nodeOf(view, page, 'five_tomatoes');
  if (five) yield* clk.play(chainPop(five, 0.45, 24), 0.45);
  // 消死区：单次强调 pulse（红线允许 1→1.06→1 单次）
  yield* clk.spend(6.5 - clk.elapsed());
  if (five) yield* clk.play(oncePulse(five, 0.06, 0.6), 0.6);
  yield* clk.spend(clk.remain());
}

/** S10 序贯揭示：4 组人群按各自字幕时码逐组 pop（对齐参考片） */
function* s10Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  const ats = (sc.subtitles ?? []).slice(1).map(s => s.t - sc.start);
  for (let i = 1; i <= 4; i++) {
    const at = ats[i - 1] ?? 1.43 + (i - 1) * 2;
    // 字幕亮相前 0.12s 抢拍 pop，观感与旁白同步
    yield* clk.spend(Math.max(0.2, at - 0.12) - clk.elapsed());
    const icon = nodeOf(view, page, `icon.${i}`);
    const label = view.findKey(wrapKey(page, `label.${i}`));
    const jobs: any[] = [];
    if (icon) jobs.push(chainPop(icon, 0.4, 22));
    if (label) jobs.push(popIn(label, 0.32));
    if (jobs.length) yield* clk.play(all(...jobs), 0.4);
  }
  yield* clk.spend(clk.remain());
}

/** S11 表格行级联：chevron+label → body 逐行揭示 */
function* s11Content(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  const rise = (n: any) =>
    all(
      n.opacity(1, 0.16, easeOutCubic),
      n.position.y(n.position.y() - 18, 0.32, easeOutCubic),
    );
  for (let i = 1; i <= 3; i++) {
    yield* clk.spend(i === 1 ? 0.35 : 0.28);
    const chev = view.findKey(chromeKey(page, `row_chev.${i}`));
    const label = view.findKey(wrapKey(page, `row.${i}.label`));
    const body = view.findKey(wrapKey(page, `row.${i}.body`));
    const head: any[] = [];
    if (chev) head.push(popIn(chev, 0.28));
    if (label) head.push(rise(label));
    if (head.length) yield* clk.play(all(...head), 0.32);
    yield* clk.spend(0.12);
    if (body) yield* clk.play(rise(body), 0.32);
  }
  yield* clk.spend(clk.remain());
}

function* relatedContent(view: any, sc: Scene) {
  const page = sc.id;
  const clk = makeClock(sc.end - sc.start);
  yield* clk.spend(0.05);
  const card = view.findKey(chromeKey(page, 'card'));
  if (card) yield* clk.play(popRise(card, 0.4, 16), 0.4);
  for (let i = 1; i <= 2; i++) {
    const label = nodeOf(view, page, `nav.${i}`);
    if (label) yield* clk.play(fadeIn(label, 0.16), 0.16);
  }
  const note = nodeOf(view, page, 'note');
  if (note) yield* clk.play(fadeIn(note, 0.2), 0.2);
  yield* clk.spend(0.05);
  const plus = view.findKey(chromeKey(page, 'plus')); // chrome 层（同 S01 card_chevron）
  const packL = nodeOf(view, page, 'pack_left');
  if (packL) yield* clk.play(popIn(packL, 0.38), 0.38);
  if (plus) yield* clk.play(popIn(plus, 0.28), 0.28);
  const packR = nodeOf(view, page, 'pack_right');
  if (packR) yield* clk.play(popIn(packR, 0.38), 0.38);
  const leftLabel = nodeOf(view, page, 'left_label');
  const rightLabel = nodeOf(view, page, 'right_label');
  const jobs: any[] = [];
  if (leftLabel) jobs.push(fadeIn(leftLabel, 0.18));
  if (rightLabel) jobs.push(fadeIn(rightLabel, 0.18));
  if (jobs.length) yield* clk.play(all(...jobs), 0.18);
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
