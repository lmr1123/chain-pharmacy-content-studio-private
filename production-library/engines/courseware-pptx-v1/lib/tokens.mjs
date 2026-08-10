/**
 * Load + normalize style_pack tokens for component rendering.
 * Components must never hardcode colors/font sizes — only read from the returned bag.
 *
 * Training courseware policy (docs/courseware-visual-spec-1080p.md):
 * - Body effective size must stay readable on projection; floors applied after scale.
 * - type.scale_factor multiplies all PPT pt (default 1.0; silk/cream use 1.28 for training).
 */
import fs from 'node:fs/promises';
import path from 'node:path';

export async function loadStylePack(stylePath) {
  const abs = path.resolve(stylePath);
  const raw = JSON.parse(await fs.readFile(abs, 'utf8'));
  const colors = raw.colors || {};
  const type = normalizeTypeScale(raw.type || {});
  const font =
    raw.type?.font_family ||
    (Array.isArray(raw.type?.font_fallback) ? raw.type.font_fallback[0] : null) ||
    'Microsoft YaHei';

  return {
    id: raw.style_pack_id,
    name_zh: raw.name_zh,
    visual_grammar: raw.visual_grammar || raw.layout?.composition_grammar || 'legacy-centered',
    path: abs,
    raw,
    colors,
    type,
    font,
    shadow: raw.shadow || raw.shadow_card || {},
    layout: raw.layout || {},
    chrome_bg: raw.chrome_bg || {mode: 'flat', fill: colors.bg || colors.silk || '#ffffff'},
    components: raw.components || {},
    policy: raw.policy || {},
    canvas: raw.canvas || {},
  };
}

/** Unify cream-red flat pt keys and silk pptx_pt / design_px keys into one scale (PPT pt). */
function normalizeTypeScale(type) {
  const ppt = type.pptx_pt || {};
  const design = type.design_px || {};
  // Video design → 1280×720 base scale; training_boost raises projected readability
  const FS = 720 / 1080;
  const scale = Number(type.scale_factor ?? type.training_scale ?? 1) || 1;
  // floors: training courseware (projection / 培训) — body never below 16pt
  const floorBody = type.minimum_body_pt ?? type.minimum_pt ?? 16;
  const floorCaption = type.minimum_caption_pt ?? 14;

  const fromDesign = (key, fallback) => {
    if (ppt[key] != null) return ppt[key];
    if (design[key] != null) return Math.round(design[key] * FS);
    return fallback;
  };

  const bump = (v, floor = floorBody) => Math.max(floor, Math.round(Number(v) * scale));

  const out = {
    cover_title: bump(ppt.cover_title ?? type.cover_title_pt ?? fromDesign('cover_title', 32), 28),
    cover_benefit: bump(ppt.cover_benefit ?? type.cover_benefit_pt ?? fromDesign('cover_benefit', 27), 24),
    chapter: bump(ppt.chapter ?? type.chapter_title_pt ?? fromDesign('chapter', 37), 32),
    chapter_num: bump(ppt.chapter_num ?? type.chapter_num_pt ?? 64, 40),
    section: bump(ppt.section ?? type.section_pt ?? fromDesign('section', 28), 24),
    page_title: bump(ppt.page_title ?? type.page_title_pt ?? 36, 28),
    nav: bump(ppt.nav ?? type.nav_pt ?? fromDesign('nav', 16), 16),
    nav_num: bump(ppt.nav_num ?? type.nav_num_pt ?? fromDesign('nav_num', 15), 15),
    card_title: bump(ppt.card_title ?? type.card_title_pt ?? fromDesign('card_title', 21), 20),
    list_item: bump(ppt.list_item ?? type.list_item_pt ?? fromDesign('list_item', 32), 26),
    body_32: bump(ppt.body_32 ?? fromDesign('body_32', 21), floorBody),
    body_28: bump(ppt.body_28 ?? fromDesign('body_28', 19), floorBody),
    body_26: bump(ppt.body_26 ?? fromDesign('body_26', 17), floorBody),
    body_24: bump(ppt.body_24 ?? type.body_emphasis_pt ?? fromDesign('body_24', 16), floorBody),
    body_22: bump(ppt.body_22 ?? type.body_pt ?? fromDesign('body_22', 15), floorBody),
    body_20: bump(ppt.body_20 ?? fromDesign('body_20', 13), floorBody),
    body_18: bump(ppt.body_18 ?? type.caption_pt ?? fromDesign('body_18', 12), floorCaption),
    body: bump(ppt.body ?? type.body_pt ?? fromDesign('body_22', 14), floorBody),
    hero_eq: bump(ppt.hero_eq ?? fromDesign('hero_eq', 67), 48),
    plus: bump(ppt.plus ?? fromDesign('plus', 60), 40),
    time_label: bump(ppt.time_label ?? fromDesign('time_label', 43), 32),
    caption: bump(ppt.caption ?? type.caption_pt ?? fromDesign('caption', 11), floorCaption),
    row_label: bump(ppt.row_label ?? type.row_label_pt ?? fromDesign('row_label', 17), 18),
    row_body: bump(ppt.row_body ?? type.row_body_pt ?? fromDesign('row_body', 13), floorBody),
    footer: bump(ppt.footer ?? type.note_bar_pt ?? fromDesign('footer', 13), floorCaption),
    eyebrow: bump(ppt.eyebrow ?? fromDesign('eyebrow', 17), 16),
    map_cap: bump(ppt.map_cap ?? fromDesign('map_cap', 17), 16),
    data_stat_number: bump(ppt.data_stat_number ?? type.data_stat_number_pt ?? 48, 40),
    data_stat_unit: bump(ppt.data_stat_unit ?? type.data_stat_unit_pt ?? 18, 16),
    data_stat_source: bump(ppt.data_stat_source ?? type.data_stat_source_pt ?? 11, floorCaption),
    note_bar: bump(ppt.note_bar ?? type.note_bar_pt ?? 12, floorCaption),
    placeholder: bump(ppt.placeholder ?? type.placeholder_pt ?? 14, floorCaption),
    audience_label: bump(ppt.audience_label ?? type.audience_label_pt ?? 16, 18),
    icon_bullet: bump(ppt.icon_bullet ?? type.icon_bullet_pt ?? 14, floorBody),
    minimum: Math.max(floorCaption, ppt.minimum_pt ?? type.minimum_pt ?? floorBody),
    scale_factor: scale,
    font_family: type.font_family,
    font_fallback: type.font_fallback || [],
  };
  return out;
}

/**
 * Resolve a color token key or raw hex against style.colors.
 * Accepts: "red", "title_red", "#D32F2F", "rgba(...)"
 */
export function colorOf(style, keyOrHex, fallback = '#000000') {
  if (!keyOrHex) return fallback;
  if (typeof keyOrHex !== 'string') return fallback;
  if (keyOrHex.startsWith('#') || keyOrHex.startsWith('rgb')) return keyOrHex;
  const c = style.colors || {};
  if (c[keyOrHex] != null) return c[keyOrHex];
  const snake = keyOrHex.replace(/[A-Z]/g, (m) => '_' + m.toLowerCase());
  if (c[snake] != null) return c[snake];
  return fallback;
}
