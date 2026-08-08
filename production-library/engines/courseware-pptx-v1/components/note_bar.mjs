/** Bottom / mid note bar. */
export function noteBar(ctx, slide, pageId, textVal, opts = {}) {
  const {eid, shape, text, centerBox, C, TS} = ctx;
  if (!textVal) return;
  const cx = opts.cx ?? 0;
  const cy = opts.cy ?? 420;
  const w = opts.w ?? 1600;
  const h = opts.h ?? 64;
  if (opts.withBg !== false) {
    shape(
      slide,
      'roundRect',
      centerBox(cx, cy, w, h),
      opts.fill ?? C.noteBarFill ?? C.cardSoft ?? C.silkLight ?? C.card,
      opts.line ?? C.cardBorder,
      opts.name || 'note-bar',
    );
  }
  text(slide, eid(pageId, opts.role || 'hint'), textVal, centerBox(cx, cy, w - 80, h - 8), {
    fontSize: opts.fontSize ?? TS.body24,
    color: opts.color ?? C.brown,
    bold: opts.bold ?? true,
  });
}
