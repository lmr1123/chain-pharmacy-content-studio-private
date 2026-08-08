import {cardGrid} from '../layout-rules.mjs';
import {fitFontSize} from '../layout-rules.mjs';

/**
 * Row cards — N adaptive via cardGrid.
 * rows: [{label, body}]
 */
export function rowCards(ctx, slide, pageId, rows, opts = {}) {
  const {eid, shape, text, centerBox, C, TS} = ctx;
  const list = rows || [];
  if (!list.length) return {pages: []};

  const grid = cardGrid(list.length, {
    areaW: opts.areaW ?? 1600,
    areaH: opts.areaH ?? 560,
    originX: opts.originX ?? 0,
    originY: opts.originY ?? 40,
    gap: opts.gap ?? 20,
    maxPerPage: opts.maxPerPage ?? 6,
  });

  // first page only for single-slide builders; multi-page handled by caller
  const pageItems = grid.pages[0] || [];
  for (const cell of pageItems) {
    const row = list[cell.index];
    if (!row) continue;
    const i = cell.index;
    shape(
      slide,
      'roundRect',
      centerBox(cell.cx, cell.cy, cell.w, cell.h),
      C.card,
      C.cardBorder,
      eid(pageId, `row_card.${i + 1}`),
    );
    const labelFit = fitFontSize(row.label || '', {
      preferred: TS.rowLabel,
      min: TS.minimum,
      boxW: cell.w - 48,
      maxLines: 2,
    });
    text(
      slide,
      eid(pageId, `row.${i + 1}.label`),
      row.label || '',
      centerBox(cell.cx, cell.cy - cell.h * 0.28, cell.w - 40, cell.h * 0.28),
      {fontSize: labelFit.fontSize, color: C.brown},
    );
    const bodyFit = fitFontSize(row.body || '', {
      preferred: TS.rowBody,
      min: TS.minimum,
      boxW: cell.w - 48,
      maxLines: 4,
    });
    text(
      slide,
      eid(pageId, `row.${i + 1}.body`),
      row.body || '',
      centerBox(cell.cx, cell.cy + cell.h * 0.12, cell.w - 40, cell.h * 0.5),
      {fontSize: bodyFit.fontSize, color: C.ink, bold: false, align: 'left'},
    );
  }
  return grid;
}

/** Full-width table rows (efficacy / summary style). */
export function rowTable(ctx, slide, pageId, rows, opts = {}) {
  const {eid, shape, text, imageFit, centerBox, C, TS, FS} = ctx;
  const list = rows || [];
  const tableW = opts.tableW ?? 1600;
  const tableH = opts.tableH ?? 720;
  const topY = opts.topY ?? 40;
  const withChevron = opts.withChevron !== false;

  shape(slide, 'roundRect', centerBox(0, topY, tableW, tableH), C.white, C.tableBorder, 'row-table');
  const fh = tableH / Math.max(list.length, 1);

  for (let i = 0; i < list.length; i++) {
    const row = list[i];
    const y = topY - tableH / 2 + fh * (i + 0.5);
    if (i > 0) {
      shape(
        slide,
        'rect',
        centerBox(0, y - fh / 2, tableW - 8, 2),
        C.tableBorder,
        C.tableBorder,
        `row-div-${i}`,
      );
    }
    shape(slide, 'rect', centerBox(-400, y, 2, fh - 8), C.tableBorder, C.tableBorder, `row-vdiv-${i}`);
    if (withChevron) {
      // fire-and-forget style: caller should await imageFit; we return promises
    }
    text(
      slide,
      eid(pageId, `row.${i + 1}.label`),
      row.label,
      centerBox(-560, y, 300, fh - 24),
      {fontSize: Math.round(30 * FS), color: C.brown, align: 'left'},
    );
    text(
      slide,
      eid(pageId, `row.${i + 1}.body`),
      row.body,
      centerBox(200, y, 1100, fh - 24),
      {fontSize: Math.round(24 * FS), color: C.brown, align: 'left', bold: false},
    );
  }

  return async function paintChevrons() {
    if (!withChevron) return;
    for (let i = 0; i < list.length; i++) {
      const y = topY - tableH / 2 + fh * (i + 0.5);
      await imageFit(
        slide,
        eid(pageId, `row.${i + 1}.chevron`),
        'icon-chevron-lime.png',
        -720,
        y,
        44,
        44,
        '»',
      );
    }
  };
}
