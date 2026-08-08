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

  const sizes = list.map((it) => {
    const isArrow = /arrow|connector|plus/i.test(it.role || '') || it.kind === 'connector';
    return it.size ?? (isArrow ? arrowSize : defaultSize);
  });
  const gap = 16;
  const totalW = sizes.reduce((a, b) => a + b, 0) + gap * (n - 1);
  const scale = totalW > totalSpan ? totalSpan / totalW : 1;
  const scaled = sizes.map((s) => s * scale);
  const used = scaled.reduce((a, b) => a + b, 0) + gap * (n - 1);
  let x = -used / 2;
  return list.map((it, i) => {
    const w = scaled[i];
    const cx = x + w / 2;
    x += w + gap;
    return {
      ...it,
      cx,
      cy: y,
      size: w,
      index: i,
    };
  });
}

/** Legacy gold chain presets by semantic length (not hard scene id). */
export function defaultChainItems(rolesOrCount) {
  if (Array.isArray(rolesOrCount)) {
    return rolesOrCount.map((role) => ({
      role: typeof role === 'string' ? role : role.role,
      file: typeof role === 'string' ? roleToFile(role) : role.file || roleToFile(role.role),
      size: typeof role === 'object' ? role.size : undefined,
    }));
  }
  const n = rolesOrCount | 0;
  if (n <= 3) {
    return [
      {role: 'tomato', file: 'tomato.png', size: 320},
      {role: 'arrow', file: 'arrow-red.png', size: 100},
      {role: 'prostate', file: 'prostate-diagram.png', size: 360},
    ];
  }
  return [
    {role: 'tomato', file: 'tomato.png', size: 240},
    {role: 'arrow1', file: 'arrow-red.png', size: 90},
    {role: 'mid', file: 'o2.png', size: 240},
    {role: 'arrow2', file: 'arrow-red.png', size: 90},
    {role: 'end', file: 'skincare-woman.png', size: 280},
  ];
}

function roleToFile(role) {
  const map = {
    tomato: 'tomato.png',
    arrow: 'arrow-red.png',
    arrow1: 'arrow-red.png',
    arrow2: 'arrow-red.png',
    prostate: 'prostate-diagram.png',
    o2: 'o2.png',
    woman: 'skincare-woman.png',
    skincare_woman: 'skincare-woman.png',
    nk: 'nk-cell.png',
    nk_cell: 'nk-cell.png',
    arm: 'flex-arm.png',
    flex_arm: 'flex-arm.png',
  };
  return map[role] || `${role}.png`;
}

/**
 * Gold-compatible chain lookup (scene id → items), falling back to model.chain / length rules.
 */
export function resolveChainItems(scene) {
  // Fixed design-coord x from cw4 CHAIN_LAYOUTS (gold regression)
  const GOLD = {
    S04_benefit_1: [
      {role: 'tomato', file: 'tomato.png', x: -420, y: 80, size: 320},
      {role: 'arrow', file: 'arrow-red.png', x: -80, y: 80, size: 100},
      {role: 'prostate', file: 'prostate-diagram.png', x: 360, y: 80, size: 360},
    ],
    S05_benefit_2: [
      {role: 'tomato', file: 'tomato.png', x: -620, y: 80, size: 240},
      {role: 'arrow1', file: 'arrow-red.png', x: -360, y: 80, size: 90},
      {role: 'o2', file: 'o2.png', x: -120, y: 80, size: 240},
      {role: 'arrow2', file: 'arrow-red.png', x: 160, y: 80, size: 90},
      {role: 'woman', file: 'skincare-woman.png', x: 480, y: 80, size: 280},
    ],
    S06_benefit_3: [
      {role: 'tomato', file: 'tomato.png', x: -620, y: 80, size: 240},
      {role: 'arrow1', file: 'arrow-red.png', x: -360, y: 80, size: 90},
      {role: 'nk', file: 'nk-cell.png', x: -80, y: 80, size: 260},
      {role: 'arrow2', file: 'arrow-red.png', x: 220, y: 80, size: 90},
      {role: 'arm', file: 'flex-arm.png', x: 520, y: 80, size: 280},
    ],
  };
  if (GOLD[scene.id]) return GOLD[scene.id];

  // Semantic match for generator scene ids (P0x_benefit_cards etc.)
  const roles = Array.isArray(scene.chain)
    ? scene.chain.map((r) => (typeof r === 'string' ? r : r.role || '')).join('|')
    : '';
  const section = `${scene.section || ''} ${scene.chapter || ''}`;
  if (
    roles.includes('skincare_woman') ||
    roles.includes('woman') ||
    /抗氧化|衰老/.test(section)
  ) {
    // Prefer full gold 5-node layout when chain mentions beauty or antioxidant
    if (!roles || roles.includes('o2') || roles.includes('skincare') || /抗氧化|衰老/.test(section)) {
      return GOLD.S05_benefit_2;
    }
  }
  if (roles.includes('flex_arm') || roles.includes('nk_cell') || /免疫/.test(section)) {
    if (roles.includes('nk') || roles.includes('flex') || /免疫/.test(section)) {
      return GOLD.S06_benefit_3;
    }
  }
  if (roles.includes('prostate') || /前列腺|精子/.test(section)) {
    return GOLD.S04_benefit_1;
  }

  if (Array.isArray(scene.chain) && scene.chain.length) {
    return defaultChainItems(scene.chain);
  }
  if (Array.isArray(scene.chain_items) && scene.chain_items.length) {
    return scene.chain_items;
  }
  return defaultChainItems(3);
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
