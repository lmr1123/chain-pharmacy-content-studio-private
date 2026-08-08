/**
 * Render context: canvas math + asset resolution + draw helpers bound to style tokens.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {colorOf} from './tokens.mjs';

export function createContext({
  model,
  style,
  assetsRoot,
  repoRoot,
  patches = {},
  eidPrefix = 'editable:cw4',
  modelPath = '',
}) {
  const canvas = style.canvas || {};
  const DW = canvas.design_width_px || canvas.width_px || 1920;
  const DH = canvas.design_height_px || canvas.height_px || 1080;
  const W = canvas.pptx_width_px || 1280;
  const H = canvas.pptx_height_px || 720;
  const SX = W / DW;
  const SY = H / DH;
  const FS = SY;
  const T = style.type;
  const font = style.font;

  function px(x, y, w, h) {
    return {
      left: x * SX,
      top: y * SY,
      width: w * SX,
      height: h * SY,
    };
  }

  function centerBox(cx, cy, w, h) {
    return px(cx - w / 2 + DW / 2, cy - h / 2 + DH / 2, w, h);
  }

  function eid(pageId, role) {
    return `${eidPrefix}:${pageId}:${role}`;
  }

  function patchedText(elementId, fallback) {
    return patches[elementId]?.text ?? fallback ?? '';
  }

  function patchedSrc(elementId, fallback) {
    return patches[elementId]?.src ?? fallback;
  }

  function c(key, fallback) {
    return colorOf(style, key, fallback);
  }

  /** Convenience palette aliases used by scene builders (mapped from tokens). */
  const C = {
    silk: c('silk', c('bg', '#cecbc4')),
    silkDeep: c('silk_deep', '#b8b4ab'),
    silkLight: c('silk_light', c('bg_warm', '#e4e1da')),
    ink: c('ink', '#1a1a1a'),
    red: c('red', c('title_red', c('accent_red', '#c43c2c'))),
    redDeep: c('red_deep', c('deep_red', '#a83224')),
    redOutline: c('red_outline', c('chapter_outline', '#ba3034')),
    white: c('white', c('card', '#ffffff')),
    yellow: c('yellow', c('chapter_fill', '#ffe33c')),
    brown: c('brown', c('section_label', '#6a3a30')),
    brownLabel: c('brown_label', '#a05040'),
    label: c('label', '#9a3c2e'),
    bodyBrown: c('body_brown', c('body', '#8a3a28')),
    dark: c('dark', '#4f4f4f'),
    lime: c('lime', c('accent_green', '#e9f200')),
    muted: c('muted', c('body_muted', '#555555')),
    pillOff: c('pill_off', c('nav_inactive', '#d8d4cc')),
    cardBorder: c('card_border', c('line', c('white_stage_border', '#e0dcd4'))),
    tableBorder: c('table_border', c('line', '#8a8680')),
    gold: c('gold', c('data_stat_number', '#e8c020')),
    titlePill: c('title_pill', '#787878'),
    hill: c('hill', '#bebebe'),
    caption: c('caption', c('ink', '#111111')),
    card: c('card', c('silk_light', '#f3efe6')),
    cardSoft: c('card_soft', c('silk_light', '#ebe6dc')),
    noteBarFill: c('note_bar_fill', c('silk_light', '#ebe6dc')),
    bg: c('bg', c('silk', '#cecbc4')),
    body: c('body', c('ink', '#505050')),
  };

  const TS = {
    coverTitle: T.cover_title,
    coverBenefit: T.cover_benefit,
    chapter: T.chapter,
    section: T.section,
    nav: T.nav,
    navNum: T.nav_num,
    cardTitle: T.card_title,
    listItem: T.list_item,
    body32: T.body_32,
    body28: T.body_28,
    body26: T.body_26,
    body24: T.body_24,
    body22: T.body_22,
    body20: T.body_20,
    body18: T.body_18,
    heroEq: T.hero_eq,
    plus: T.plus,
    timeLabel: T.time_label,
    caption: T.caption,
    rowLabel: T.row_label,
    rowBody: T.row_body,
    footer: T.footer,
    eyebrow: T.eyebrow,
    mapCap: T.map_cap,
    dataStatNumber: T.data_stat_number,
    dataStatUnit: T.data_stat_unit,
    dataStatSource: T.data_stat_source,
    noteBar: T.note_bar,
    placeholder: T.placeholder,
    audienceLabel: T.audience_label,
    iconBullet: T.icon_bullet,
    minimum: T.minimum,
  };

  function readImageSize(buf) {
    if (!buf || buf.length < 24) return null;
    if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47) {
      const w = (buf[16] << 24) | (buf[17] << 16) | (buf[18] << 8) | buf[19];
      const h = (buf[20] << 24) | (buf[21] << 16) | (buf[22] << 8) | buf[23];
      if (w > 0 && h > 0) return {w, h};
    }
    if (buf[0] === 0xff && buf[1] === 0xd8) {
      let i = 2;
      while (i < buf.length - 8) {
        if (buf[i] !== 0xff) {
          i += 1;
          continue;
        }
        const marker = buf[i + 1];
        if (marker === 0xd9 || marker === 0xda) break;
        const len = (buf[i + 2] << 8) | buf[i + 3];
        if (
          (marker >= 0xc0 && marker <= 0xc3) ||
          (marker >= 0xc5 && marker <= 0xc7) ||
          (marker >= 0xc9 && marker <= 0xcb) ||
          (marker >= 0xcd && marker <= 0xcf)
        ) {
          const h = (buf[i + 5] << 8) | buf[i + 6];
          const w = (buf[i + 7] << 8) | buf[i + 8];
          if (w > 0 && h > 0) return {w, h};
        }
        i += 2 + len;
      }
    }
    return null;
  }

  function containBox(cx, cy, maxW, maxH, iw, ih) {
    if (!iw || !ih) return centerBox(cx, cy, maxW, maxH);
    const ar = iw / ih;
    let w = maxW;
    let h = maxW / ar;
    if (h > maxH) {
      h = maxH;
      w = maxH * ar;
    }
    return centerBox(cx, cy, w, h);
  }

  function resolveAssetPath(keyOrPath) {
    if (!keyOrPath) return null;
    if (typeof keyOrPath === 'object' && keyOrPath.src) keyOrPath = keyOrPath.src;
    if (typeof keyOrPath !== 'string') return null;

    const assets = model.assets || {};
    let rel = assets[keyOrPath];
    if (rel && typeof rel === 'object') rel = rel.src;
    if (!rel) rel = keyOrPath;

    if (rel.startsWith('/')) rel = rel.slice(1);
    if (!rel.includes('/') && !path.isAbsolute(rel)) {
      rel = path.join('assets/generated', rel);
    }
    return path.isAbsolute(rel) ? rel : path.join(assetsRoot, rel);
  }

  async function loadAsset(keyOrPath) {
    const full = resolveAssetPath(keyOrPath);
    if (!full) return null;
    try {
      const buf = await fs.readFile(full);
      return {buf: new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength), full};
    } catch {
      return null;
    }
  }

  function contentTypeOf(full) {
    if (!full) return 'image/png';
    const lower = full.toLowerCase();
    if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return 'image/jpeg';
    if (lower.endsWith('.webp')) return 'image/webp';
    return 'image/png';
  }

  function shape(slide, geometry, position, fill, line = 'none', name) {
    return slide.shapes.add({
      geometry,
      name,
      position,
      fill,
      line: {
        style: 'solid',
        fill: line === 'none' ? 'none' : line,
        width: line === 'none' ? 0 : 1.5,
      },
      ...(geometry === 'roundRect' ? {borderRadius: 'rounded-xl'} : {}),
    });
  }

  function text(slide, elementId, value, position, opts = {}) {
    const box = shape(
      slide,
      'textbox',
      position,
      opts.fill ?? 'none',
      opts.line ?? 'none',
      elementId,
    );
    box.text = patchedText(elementId, value);
    box.text.style = {
      fontFamily: font,
      fontSize: opts.fontSize ?? TS.body22,
      bold: opts.bold ?? true,
      color: opts.color ?? C.ink,
      alignment: opts.align ?? 'center',
      verticalAlignment: opts.vAlign ?? 'middle',
    };
    return box;
  }

  function drawPlaceholderCard(slide, elementId, cx, cy, maxW, maxH, label) {
    // outer frame uses style chrome tint so placeholders blend with silk/cream (not pure white plate)
    const outerFill = C.silkLight || C.card || C.white;
    const innerFill = C.bg || C.silk || C.silkLight;
    shape(slide, 'roundRect', centerBox(cx, cy, maxW, maxH), outerFill, C.red, elementId);
    shape(
      slide,
      'roundRect',
      centerBox(cx, cy, Math.max(40, maxW - 24), Math.max(40, maxH - 24)),
      innerFill,
      C.cardBorder,
      elementId + '__inner',
    );
    text(
      slide,
      `${elementId}__slot`,
      label || '图片占位\n待业务替换',
      centerBox(cx, cy + 10, maxW - 36, maxH * 0.4),
      {fontSize: TS.body20, color: C.brown},
    );
    text(
      slide,
      `${elementId}__hint`,
      '可替换',
      centerBox(cx, cy - maxH * 0.28, maxW - 40, 32),
      {fontSize: TS.caption, color: C.muted},
    );
    return null;
  }

  async function imageFit(
    slide,
    elementId,
    assetKey,
    cx,
    cy,
    maxW,
    maxH,
    alt = '',
    placeholderLabel = '',
  ) {
    const key = patchedSrc(elementId, assetKey);
    const loaded = await loadAsset(key);
    if (!loaded) {
      return drawPlaceholderCard(
        slide,
        elementId,
        cx,
        cy,
        maxW,
        maxH,
        placeholderLabel || alt || '图片占位\n待业务替换',
      );
    }
    const size = readImageSize(loaded.buf);
    const position = containBox(cx, cy, maxW, maxH, size?.w, size?.h);
    return slide.images.add({
      blob: loaded.buf,
      contentType: contentTypeOf(loaded.full),
      alt: alt || elementId,
      fit: 'fill',
      position,
      name: elementId,
    });
  }

  return {
    model,
    style,
    assetsRoot,
    repoRoot,
    patches,
    modelPath,
    eidPrefix,
    DW,
    DH,
    W,
    H,
    SX,
    SY,
    FS,
    C,
    TS,
    font,
    px,
    centerBox,
    eid,
    patchedText,
    patchedSrc,
    c,
    shape,
    text,
    imageFit,
    loadAsset,
    resolveAssetPath,
    drawPlaceholderCard,
    containBox,
  };
}
