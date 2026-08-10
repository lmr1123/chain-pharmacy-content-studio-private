/** Chapter title: fill + outline offsets from style.components.chapter_title. */
import {fitFontSize} from '../layout-rules.mjs';

export function chapterTitle(ctx, slide, pageId, title) {
  const {eid, shape, text, centerBox, C, TS, style} = ctx;
  if (!title) return;
  const conf = style.components?.chapter_title || {};
  const id = eid(pageId, 'chapter');
  const rawBox = style.layout?.chapter_box_design || {cx: 0, cy: -460, w: 1600, h: 100};
  // Artifact export can clip CJK ascenders/descenders in a 100px-high box.
  // Keep the same top edge and expand downward so titles remain fully visible.
  const box = {
    ...rawBox,
    cy: rawBox.cy + 20,
    h: Math.max(rawBox.h, 140),
  };
  if (conf.mode === 'left-lockup' || style.visual_grammar === 'product-blue-asymmetric-v1') {
    const left = box.cx - box.w / 2;
    const fit = fitFontSize(title, {
      preferred: TS.chapter,
      min: Math.max(TS.body28 || 22, 26),
      boxW: box.w - 130,
      maxLines: 1,
    });
    shape(
      slide,
      'roundRect',
      centerBox(left + 16, box.cy, 28, 98),
      C.coral,
      C.coral,
      `${id}__accent-rail`,
    );
    text(slide, id, title, centerBox(box.cx + 52, box.cy - 4, box.w - 120, box.h), {
      fontSize: fit.fontSize,
      color: C.white,
      align: 'left',
    });
    shape(
      slide,
      'rect',
      centerBox(left + 126, box.cy + 66, 220, 7),
      C.yellow,
      C.yellow,
      `${id}__highlight-line`,
    );
    return;
  }
  const offsets = conf.outline_offsets_design || conf.outline_offsets_px || [
    [-2.5, 0],
    [2.5, 0],
    [0, -2.5],
    [0, 2.5],
  ];
  const fill = C.yellow || C.red;
  const outline = C.red;
  // 培训章标：尽量单行，略降字号而非折行
  const fit = fitFontSize(title, {
    preferred: TS.chapter,
    min: Math.max(TS.body28 || 22, 26),
    boxW: (box.w || 1600) - 40,
    maxLines: 1,
  });
  const fontSize = fit.fontSize;

  for (const [dx, dy] of offsets) {
    text(
      slide,
      `${id}__o_${dx}_${dy}`,
      title,
      centerBox(box.cx + dx, box.cy + dy, box.w, box.h),
      {fontSize, color: outline},
    );
  }
  text(slide, id, title, centerBox(box.cx, box.cy, box.w, box.h), {
    fontSize,
    color: fill,
  });
}
