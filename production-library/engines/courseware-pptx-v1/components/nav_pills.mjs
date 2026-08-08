/**
 * Nav pills — N adaptive (not hard-coded to 2).
 * items: string[]; activeIndex: number
 * Gold 2-pill: opts.goldTwo = true uses cw4 fixed {x,w} layout.
 */
export function navPills(ctx, slide, pageId, items, activeIndex = 0, opts = {}) {
  const {eid, shape, text, centerBox, C, TS} = ctx;
  const nav = items || [];
  if (!nav.length) return;

  const y = opts.y ?? -340;
  const h = opts.h ?? 64;
  const n = nav.length;

  // cw4 gold related_meds: two asymmetric pills
  let slots;
  if ((opts.goldTwo || n === 2) && !opts.forceEqual) {
    slots = [
      {x: -380, w: 720},
      {x: 420, w: 700},
    ].slice(0, n);
  } else {
    const totalSpan = opts.totalSpan ?? 1600;
    const gap = opts.gap ?? 24;
    const pillW = Math.min(opts.maxPillW ?? 720, (totalSpan - gap * (n - 1)) / n);
    const used = pillW * n + gap * (n - 1);
    let x0 = -used / 2 + pillW / 2;
    slots = [];
    for (let i = 0; i < n; i++) {
      slots.push({x: x0 + i * (pillW + gap), w: pillW});
    }
  }

  for (let i = 0; i < n; i++) {
    const {x, w} = slots[i] || {x: 0, w: 600};
    const on = i === activeIndex;
    shape(
      slide,
      'roundRect',
      centerBox(x, y, w, h),
      on ? C.red : C.pillOff,
      on ? C.red : C.pillOff,
      eid(pageId, `nav.${i + 1}__pill`),
    );
    shape(
      slide,
      'ellipse',
      centerBox(x - w / 2 + 28, y, 36, 36),
      on ? C.white : C.red,
      on ? C.white : C.red,
    );
    text(
      slide,
      eid(pageId, `nav.${i + 1}__n`),
      String(i + 1),
      centerBox(x - w / 2 + 28, y, 32, 32),
      {fontSize: TS.navNum, color: on ? C.red : C.white},
    );
    text(
      slide,
      eid(pageId, `nav.${i + 1}`),
      nav[i],
      centerBox(x + 20, y, w - 90, 52),
      {fontSize: TS.nav, color: on ? C.white : C.muted, align: 'left'},
    );
  }
}
