/**
 * Layout rules: N-card grid, type size steps, page split, image-slot branch.
 * Geometry only — no colors/fonts (those come from style tokens).
 */

/** 1 横铺 / 2 对半 / 3 等分 / 4→2×2 / 5–6→2×3 */
export function cardGrid(n, opts = {}) {
  const count = Math.max(0, n | 0);
  const areaW = opts.areaW ?? 1760;
  const areaH = opts.areaH ?? 620;
  const originX = opts.originX ?? 0;
  const originY = opts.originY ?? 40;
  const gap = opts.gap ?? 32;
  const maxPerPage = opts.maxPerPage ?? 6;

  if (count === 0) return {pages: [[]], meta: {cols: 0, rows: 0, overflow: false}};

  const pages = [];
  let remaining = count;
  let offset = 0;
  while (remaining > 0) {
    const take = Math.min(remaining, maxPerPage);
    pages.push(layoutPage(take, areaW, areaH, originX, originY, gap, offset));
    remaining -= take;
    offset += take;
  }
  return {
    pages,
    meta: {
      total: count,
      pageCount: pages.length,
      overflow: pages.length > 1,
      maxPerPage,
    },
  };
}

function layoutPage(n, areaW, areaH, originX, originY, gap, indexOffset) {
  let cols;
  let rows;
  if (n === 1) {
    cols = 1;
    rows = 1;
  } else if (n === 2) {
    cols = 2;
    rows = 1;
  } else if (n === 3) {
    cols = 3;
    rows = 1;
  } else if (n === 4) {
    cols = 2;
    rows = 2;
  } else {
    cols = 3;
    rows = 2;
  }

  const cellW = (areaW - gap * (cols - 1)) / cols;
  const cellH = (areaH - gap * (rows - 1)) / rows;
  const items = [];
  for (let i = 0; i < n; i++) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const cx = originX - areaW / 2 + cellW / 2 + col * (cellW + gap);
    const cy = originY - areaH / 2 + cellH / 2 + row * (cellH + gap);
    items.push({
      index: indexOffset + i,
      cx,
      cy,
      w: cellW,
      h: cellH,
      col,
      row,
    });
  }
  return items;
}

/**
 * Type size ladder: start at preferred, step down while estimated lines exceed maxLines.
 * Returns {fontSize, lines, overflow}.
 */
export function fitFontSize(text, opts = {}) {
  const preferred = opts.preferred ?? 18;
  const min = opts.min ?? 11;
  const step = opts.step ?? 1;
  const boxW = opts.boxW ?? 400;
  const maxLines = opts.maxLines ?? 4;
  // rough CJK-aware: ~1em per char width in pt ≈ box width / fontSize * 1.1
  const chars = String(text || '').length || 1;
  let fontSize = preferred;
  let lines = 1;
  while (fontSize > min) {
    const charsPerLine = Math.max(1, Math.floor((boxW / fontSize) * 1.05));
    lines = Math.ceil(chars / charsPerLine);
    if (lines <= maxLines) break;
    fontSize -= step;
  }
  const charsPerLine = Math.max(1, Math.floor((boxW / fontSize) * 1.05));
  lines = Math.ceil(chars / charsPerLine);
  return {
    fontSize,
    lines,
    overflow: lines > maxLines,
  };
}

/**
 * Image-chain auto-center layout (design coords, origin center).
 * items: [{role, file|asset, size?}]
 */
export function imageChainLayout(items, opts = {}) {
  const list = items || [];
  const n = list.length;
  if (n === 0) return [];
  const y = opts.y ?? 80;
  const defaultSize = opts.defaultSize ?? 280;
  const arrowSize = opts.arrowSize ?? 90;
  const totalSpan = opts.totalSpan ?? 1600;

  const dimensions = list.map((it) => {
    const isArrow = /arrow|connector|plus/i.test(it.role || '') || it.kind === 'connector';
    const fallback = it.size ?? (isArrow ? arrowSize : defaultSize);
    return {
      width: it.w ?? it.width ?? fallback,
      height: it.h ?? it.height ?? fallback,
    };
  });
  const gap = 16;
  const totalW = dimensions.reduce((sum, dim) => sum + dim.width, 0) + gap * (n - 1);
  const scale = totalW > totalSpan ? totalSpan / totalW : 1;
  const scaled = dimensions.map((dim) => ({
    width: dim.width * scale,
    height: dim.height * scale,
  }));
  const used = scaled.reduce((sum, dim) => sum + dim.width, 0) + gap * (n - 1);
  let x = -used / 2;
  return list.map((it, i) => {
    const w = scaled[i].width;
    const h = scaled[i].height;
    const cx = x + w / 2;
    x += w + gap;
    return {
      ...it,
      cx,
      cy: y,
      size: w,
      width: w,
      height: h,
      index: i,
    };
  });
}

/** Normalize only explicit chain entries; never infer theme media from copy or scene ids. */
export function defaultChainItems(rolesOrCount) {
  if (Array.isArray(rolesOrCount)) {
    return rolesOrCount.map((role) => ({
      role: typeof role === 'string' ? role : role.role,
      file: typeof role === 'object' ? role.file || role.asset || role.src : undefined,
      size: typeof role === 'object' ? role.size : undefined,
      w: typeof role === 'object' ? role.w ?? role.width : undefined,
      h: typeof role === 'object' ? role.h ?? role.height : undefined,
      fit: typeof role === 'object' ? role.fit : undefined,
      crop: typeof role === 'object' ? role.crop : undefined,
    }));
  }
  return [];
}

/**
 * Explicit chain lookup. A missing file remains a labeled draft gap.
 */
export function resolveChainItems(scene) {
  if (Array.isArray(scene.chain) && scene.chain.length) {
    return defaultChainItems(scene.chain);
  }
  if (Array.isArray(scene.chain_items) && scene.chain_items.length) {
    return defaultChainItems(scene.chain_items);
  }
  return [];
}

/** 有图槽 → 图文；无图 → 数据/大字（不硬塞图） */
export function imageSlotBranch(hasImage) {
  return hasImage ? 'image_text' : 'data_or_type';
}

/** Split a list into pages of maxPerPage (for empty_cards=forbidden upstream). */
export function splitPages(items, maxPerPage = 6) {
  const list = items || [];
  if (!list.length) return [[]];
  const pages = [];
  for (let i = 0; i < list.length; i += maxPerPage) {
    pages.push(list.slice(i, i + maxPerPage));
  }
  return pages;
}
