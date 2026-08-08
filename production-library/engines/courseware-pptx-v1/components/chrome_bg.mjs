/** Full-slide background from style.chrome_bg (silk or flat). */
export function chromeBg(ctx, slide) {
  const {shape, px, centerBox, W, H, DW, C, style} = ctx;
  const chrome = style.chrome_bg || {};
  const fill = chrome.fill || C.bg || C.silk;

  shape(slide, 'rect', {left: 0, top: 0, width: W, height: H}, fill, 'none', 'bg-chrome');

  if (chrome.mode === 'silk') {
    const top = chrome.top_edge || {};
    const h = top.height_design ?? 8;
    const topFill = top.fill || 'rgba(255,255,255,0.22)';
    shape(slide, 'rect', px(0, 0, DW, h), topFill, 'none', 'bg-top-edge');

    const glow = chrome.glow || {};
    if (glow.shape === 'ellipse' || !glow.shape) {
      shape(
        slide,
        'ellipse',
        centerBox(
          glow.cx_design ?? 720,
          glow.cy_design ?? 460,
          glow.w_design ?? 720,
          glow.h_design ?? 360,
        ),
        glow.fill || 'rgba(255,255,255,0.08)',
        'none',
        'bg-glow-soft',
      );
    }
  }
}
