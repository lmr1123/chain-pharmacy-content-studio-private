/** Content stage — silk-warm surface (not pure white). */
export function whiteStage(ctx, slide, name, cx, cy, w, h, opts = {}) {
  const {shape, centerBox, C, style} = ctx;
  const tokenFill =
    style?.colors?.white_stage_fill || style?.colors?.card || C.card || C.silkLight;
  const fill = opts.fill ?? tokenFill;
  const line = opts.line ?? C.cardBorder;
  return shape(slide, 'roundRect', centerBox(cx, cy, w, h), fill, line, name || 'white-stage');
}
