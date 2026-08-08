/** Chapter title: fill + outline offsets from style.components.chapter_title. */
import {fitFontSize} from '../layout-rules.mjs';

export function chapterTitle(ctx, slide, pageId, title) {
  const {eid, text, centerBox, C, TS, style} = ctx;
  if (!title) return;
  const conf = style.components?.chapter_title || {};
  const id = eid(pageId, 'chapter');
  const box = style.layout?.chapter_box_design || {cx: 0, cy: -460, w: 1600, h: 100};
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
