import {cardGrid} from '../layout-rules.mjs';

/**
 * Audience cards.
 * - Gold default: single-row N columns (cw4 geometry).
 * - opts.layout = 'grid' → cardGrid 2×2 etc. for other page types.
 * items: [{label, icon|asset}]
 */
export async function audienceCards(ctx, slide, pageId, items, opts = {}) {
  const {eid, shape, text, imageFit, centerBox, C, FS} = ctx;
  const list = items || [];
  if (!list.length) return;

  const iconMap = {
    prostate: 'prostate-diagram.png',
    couple: 'couple.png',
    audience_beauty: 'audience-beauty.png',
    audience_weak: 'audience-weak.png',
    ...(opts.iconMap || {}),
  };

  // Gold / default: one row of N cards (matches export-cw4 buildAudience)
  if (opts.layout !== 'grid') {
    const n = Math.max(list.length, 1);
    const span = opts.areaW ?? 1760;
    const gap = span / n;
    const cardH = opts.cardH ?? 580;
    const cy = opts.originY ?? 60;
    for (let i = 0; i < list.length; i++) {
      const it = list[i];
      const x = -span / 2 + gap * (i + 0.5);
      shape(
        slide,
        'roundRect',
        centerBox(x, cy, gap - 48, cardH),
        C.card || C.silkLight,
        C.cardBorder,
        `aud-card-${i}`,
      );
      const file = iconMap[it.icon || ''] || it.asset || 'prostate-diagram.png';
      await imageFit(slide, eid(pageId, `icon.${i + 1}`), file, x, -40, 260, 260, it.label);
      shape(
        slide,
        'roundRect',
        centerBox(x, 220, gap - 80, 64),
        C.redDeep,
        C.redDeep,
        `aud-label-bar-${i}`,
      );
      text(slide, eid(pageId, `label.${i + 1}`), it.label, centerBox(x, 220, gap - 100, 56), {
        fontSize: ctx.TS.audienceLabel,
        color: C.yellow,
      });
    }
    return {layout: 'row', n};
  }

  // Optional multi-row grid for non-gold pages
  const grid = cardGrid(list.length, {
    areaW: opts.areaW ?? 1760,
    areaH: opts.areaH ?? 580,
    originX: 0,
    originY: opts.originY ?? 60,
    gap: opts.gap ?? 48,
    maxPerPage: opts.maxPerPage ?? 6,
  });

  for (const cell of grid.pages[0] || []) {
    const it = list[cell.index];
    if (!it) continue;
    const i = cell.index;
    const x = cell.cx;
    const iconSize = Math.min(260, cell.w - 40, cell.h * 0.45);
    shape(
      slide,
      'roundRect',
      centerBox(x, cell.cy, cell.w, cell.h),
      C.white,
      C.cardBorder,
      `aud-card-${i}`,
    );
    const file = iconMap[it.icon || ''] || it.asset || 'prostate-diagram.png';
    await imageFit(
      slide,
      eid(pageId, `icon.${i + 1}`),
      file,
      x,
      cell.cy - cell.h * 0.18,
      iconSize,
      iconSize,
      it.label,
    );
    const labelY = cell.cy + cell.h * 0.32;
    shape(
      slide,
      'roundRect',
      centerBox(x, labelY, cell.w - 80, 64),
      C.redDeep,
      C.redDeep,
      `aud-label-bar-${i}`,
    );
    text(slide, eid(pageId, `label.${i + 1}`), it.label, centerBox(x, labelY, cell.w - 100, 56), {
      fontSize: Math.round(28 * FS),
      color: C.yellow,
    });
  }
  return grid;
}
