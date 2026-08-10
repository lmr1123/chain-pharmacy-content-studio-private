/** Full-slide background from the locked style pack. */
export function chromeBg(ctx, slide) {
  const {shape, px, centerBox, W, H, DW, DH, C, style} = ctx;
  const chrome = style.chrome_bg || {};
  const fill = chrome.fill || C.bg || C.silk;

  shape(slide, 'rect', {left: 0, top: 0, width: W, height: H}, fill, 'none', 'bg-chrome');

  if (chrome.mode === 'product-blue-grid') {
    const grid = chrome.grid || {};
    const columns = Math.max(2, grid.columns ?? 12);
    const rows = Math.max(2, grid.rows ?? 6);
    const size = grid.size_design ?? 58;
    const gridFill = grid.fill || C.grid || 'rgba(255,255,255,0.12)';
    for (let row = 0; row < rows; row += 1) {
      const cy = -DH / 2 + ((row + 0.5) * DH) / rows;
      for (let col = 0; col < columns; col += 1) {
        const cx = -DW / 2 + ((col + 0.5) * DW) / columns;
        shape(
          slide,
          'roundRect',
          centerBox(cx, cy, size, size),
          gridFill,
          'none',
          `bg-grid-${row + 1}-${col + 1}`,
        );
      }
    }

    for (let index = 0; index < (chrome.waves || []).length; index += 1) {
      const wave = chrome.waves[index];
      shape(
        slide,
        'ellipse',
        centerBox(
          wave.cx_design ?? 0,
          wave.cy_design ?? 0,
          wave.w_design ?? 900,
          wave.h_design ?? 500,
        ),
        wave.fill || C.wave || 'rgba(255,255,255,0.10)',
        'none',
        `bg-wave-${index + 1}`,
      );
    }
    return;
  }

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
