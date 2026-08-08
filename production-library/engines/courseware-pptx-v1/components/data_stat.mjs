import {fitFontSize} from '../layout-rules.mjs';

/**
 * Big number card — Chinese training layout:
 *   note (lead-in, top) → NUMBER (+ unit) → optional source (bottom)
 * All text clamped inside card; title/body share same content width.
 */
export function dataStat(ctx, slide, pageId, data, box) {
  const {eid, text, shape, centerBox, C, TS} = ctx;
  const {cx, cy, w, h} = box;
  const number = data.number ?? data.value ?? '';
  const unit = data.unit ?? '';
  const note = data.note ?? data.caption ?? '';
  const source = data.source ?? '';
  const role = data.role || 'stat';
  const padX = 28;
  const contentW = Math.max(80, w - padX * 2);

  if (data.card !== false) {
    // silk-warm card — never pure white on silk bg
    shape(
      slide,
      'roundRect',
      centerBox(cx, cy, w, h),
      C.card || C.silkLight,
      C.cardBorder,
      eid(pageId, `${role}__card`),
    );
  }

  // vertical bands inside card (relative to cy)
  const top = cy - h / 2;
  const noteH = note ? h * 0.22 : 0;
  const numH = h * (note ? 0.42 : 0.55);
  const unitH = unit ? h * 0.12 : 0;
  const srcH = source ? h * 0.14 : 0;

  let y = top + h * 0.1;
  if (note) {
    const fit = fitFontSize(note, {
      preferred: TS.body18,
      min: TS.minimum,
      boxW: contentW,
      maxLines: 2,
    });
    text(slide, eid(pageId, `${role}.note`), note, centerBox(cx, y + noteH / 2, contentW, noteH), {
      fontSize: fit.fontSize,
      color: C.body,
      bold: false,
      align: 'center',
      vAlign: 'middle',
    });
    y += noteH + 4;
  }

  const numFit = fitFontSize(String(number), {
    preferred: TS.dataStatNumber,
    min: Math.max(TS.minimum + 8, 28),
    boxW: contentW,
    maxLines: 1,
  });
  text(slide, eid(pageId, `${role}.number`), String(number), centerBox(cx, y + numH / 2, contentW, numH), {
    fontSize: numFit.fontSize,
    color: C.red,
    align: 'center',
    vAlign: 'middle',
  });
  y += numH;

  if (unit) {
    text(slide, eid(pageId, `${role}.unit`), unit, centerBox(cx, y + unitH / 2, contentW, unitH), {
      fontSize: TS.dataStatUnit,
      color: C.muted,
      align: 'center',
      vAlign: 'middle',
    });
    y += unitH;
  }

  if (source) {
    const sFit = fitFontSize(source, {
      preferred: TS.dataStatSource,
      min: TS.minimum,
      boxW: contentW,
      maxLines: 2,
    });
    text(
      slide,
      eid(pageId, `${role}.source`),
      source,
      centerBox(cx, Math.min(y + srcH / 2, cy + h / 2 - srcH / 2 - 8), contentW, srcH),
      {fontSize: sFit.fontSize, color: C.muted, bold: false, align: 'center'},
    );
  }
}
