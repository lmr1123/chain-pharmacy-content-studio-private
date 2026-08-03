/**
 * 福尔番茄红素 · 商品培训课件4 原生可编辑 PPTX 导出
 *
 * 对标速福达金样 export-sufuda-pptx.mjs：
 * - 单一内容源 content-model.json（+ 可选 editor patches）
 * - Artifact Tool 原生文本 / 形状 / 图片（PowerPoint 可改）
 * - 1920×1080 视频设计坐标 → 1280×720 标准 16:9
 * - 图片按原生宽高比 contain 装箱，禁 stretch
 * - 稳定 ID：editable:cw4:{page}:{role}
 * - 导出后 patch HarmonyOS Sans SC 字体
 *
 * Usage:
 *   node scripts/export-cw4-pptx.mjs
 *   node scripts/export-cw4-pptx.mjs /path/to/project-snapshot.json
 *   node scripts/export-cw4-pptx.mjs --model /path/to/content-model.json --out /path/to/out.pptx
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {
  Presentation,
  PresentationFile,
} from '../../../../../poc/courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const REPO = path.resolve(ROOT, '../../../../');

const args = process.argv.slice(2);
function argValue(flag, fallback) {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : fallback;
}

const snapshotPath = args.find(
  (a, idx) =>
    a.endsWith('.json') &&
    !a.startsWith('--') &&
    !(args[idx - 1] && args[idx - 1].startsWith('--')),
);
const modelPath = path.resolve(argValue('--model', path.join(ROOT, 'content-model.json')));
const outPath = path.resolve(
  argValue(
    '--out',
    path.join(ROOT, 'out', '福尔番茄红素_商品培训课件4_可编辑课件_v1.pptx'),
  ),
);
const assetsRoot = path.resolve(argValue('--assets', ROOT));

/** 视频设计坐标 */
const DW = 1920;
const DH = 1080;
/** PPT 画布（标准 16:9，与速福达 / 其它课件一致） */
const W = 1280;
const H = 720;
const SX = W / DW;
const SY = H / DH;
const FS = SY;

const model = JSON.parse(await fs.readFile(modelPath, 'utf8'));
const patches = snapshotPath
  ? JSON.parse(await fs.readFile(snapshotPath, 'utf8')).patches ?? {}
  : {};

/** 品牌色（对齐 project.tsx / 参考片） */
const C = {
  silk: '#cecbc4',
  silkDeep: '#b8b4ab',
  silkLight: '#e4e1da',
  ink: '#1a1a1a',
  red: '#c43c2c',
  redDeep: '#a83224',
  white: '#ffffff',
  yellow: '#ffe33c',
  brown: '#6a3a30',
  dark: '#4f4f4f',
  lime: '#e9f200',
  muted: '#555555',
  pillOff: '#d8d4cc',
  cardBorder: '#e0dcd4',
  tableBorder: '#8a8680',
  gold: '#e8c020',
  titlePill: '#787878',
  hill: '#bebebe',
};

const FONT_FINAL =
  (model.fonts?.display || 'HarmonyOS Sans SC, Source Han Sans SC, PingFang SC')
    .split(',')[0]
    .trim();

/** 视频字号 → PPT */
const TS = {
  coverTitle: Math.round(48 * FS),
  coverBenefit: Math.round(40 * FS),
  chapter: Math.round(56 * FS),
  section: Math.round(42 * FS),
  nav: Math.round(24 * FS),
  navNum: Math.round(22 * FS),
  cardTitle: Math.round(32 * FS),
  listItem: Math.round(48 * FS),
  body32: Math.round(32 * FS),
  body28: Math.round(28 * FS),
  body26: Math.round(26 * FS),
  body24: Math.round(24 * FS),
  body22: Math.round(22 * FS),
  body20: Math.round(20 * FS),
  body18: Math.round(18 * FS),
  heroEq: Math.round(100 * FS),
  plus: Math.round(90 * FS),
  timeLabel: Math.round(64 * FS),
  caption: Math.round(16 * FS),
  rowLabel: Math.round(26 * FS),
  rowBody: Math.round(20 * FS),
  footer: Math.round(20 * FS),
  eyebrow: Math.round(26 * FS),
  mapCap: Math.round(26 * FS),
};

function px(x, y, w, h) {
  return {
    left: x * SX,
    top: y * SY,
    width: w * SX,
    height: h * SY,
  };
}

/** 设计坐标：中心 (cx,cy) + 宽高，原点在画布中心 */
function centerBox(cx, cy, w, h) {
  return px(cx - w / 2 + DW / 2, cy - h / 2 + DH / 2, w, h);
}

function eid(pageId, role) {
  return `editable:cw4:${pageId}:${role}`;
}

function patchedText(elementId, fallback) {
  return patches[elementId]?.text ?? fallback ?? '';
}

function patchedSrc(elementId, fallback) {
  return patches[elementId]?.src ?? fallback;
}

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

/** 解析 content-model assets 或直接文件名 → 绝对路径 */
function resolveAssetPath(keyOrPath) {
  if (!keyOrPath) return null;
  if (typeof keyOrPath === 'object' && keyOrPath.src) {
    keyOrPath = keyOrPath.src;
  }
  if (typeof keyOrPath !== 'string') return null;

  const assets = model.assets || {};
  let rel = assets[keyOrPath];
  if (rel && typeof rel === 'object') rel = rel.src;
  if (!rel) rel = keyOrPath;

  // strip leading slash /assets/ → assets/
  if (rel.startsWith('/')) rel = rel.slice(1);
  // filename-only → assets/generated/
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
    fontFamily: FONT_FINAL,
    fontSize: opts.fontSize ?? TS.body22,
    bold: opts.bold ?? true,
    color: opts.color ?? C.ink,
    alignment: opts.align ?? 'center',
    verticalAlignment: opts.vAlign ?? 'middle',
  };
  return box;
}

function drawPlaceholderCard(slide, elementId, cx, cy, maxW, maxH, label) {
  shape(slide, 'roundRect', centerBox(cx, cy, maxW, maxH), C.white, C.red, elementId);
  shape(
    slide,
    'roundRect',
    centerBox(cx, cy, Math.max(40, maxW - 24), Math.max(40, maxH - 24)),
    C.silkLight,
    C.cardBorder,
    elementId + '__inner',
  );
  text(slide, `${elementId}__slot`, label || '图片占位\n待业务替换', centerBox(cx, cy + 10, maxW - 36, maxH * 0.4), {
    fontSize: TS.body20,
    color: C.brown,
  });
  text(slide, `${elementId}__hint`, '可替换', centerBox(cx, cy - maxH * 0.28, maxW - 40, 32), {
    fontSize: TS.caption,
    color: C.muted,
  });
  return null;
}

async function imageFit(slide, elementId, assetKey, cx, cy, maxW, maxH, alt = '', placeholderLabel = '') {
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

/** 丝绸底 + 极轻装饰（避免半透明大块被当成内容卡） */
function silkBg(slide) {
  shape(slide, 'rect', {left: 0, top: 0, width: W, height: H}, C.silk, 'none', 'bg-silk');
  // 顶部细高光条 + 右下角极淡晕，不形成「空白卡片」错觉
  shape(slide, 'rect', px(0, 0, DW, 8), 'rgba(255,255,255,0.22)', 'none', 'bg-top-edge');
  shape(
    slide,
    'ellipse',
    centerBox(720, 460, 720, 360),
    'rgba(255,255,255,0.08)',
    'none',
    'bg-glow-soft',
  );
}

/**
 * 章节黄字 + 红描边：仅 4 向偏移（企业级可点选：顶层 editable 黄字为主对象）
 */
function chapterTitle(slide, pageId, title) {
  const id = eid(pageId, 'chapter');
  const pos = centerBox(0, -460, 1400, 90);
  for (const [dx, dy] of [
    [-2.5, 0],
    [2.5, 0],
    [0, -2.5],
    [0, 2.5],
  ]) {
    text(slide, `${id}__o_${dx}_${dy}`, title, centerBox(dx, -460 + dy, 1400, 90), {
      fontSize: TS.chapter,
      color: C.red,
    });
  }
  text(slide, id, title, pos, {fontSize: TS.chapter, color: C.yellow});
}

async function sectionLabelAsync(slide, pageId, section) {
  if (!section) return;
  // chevron 中心 -860；左对齐正文左缘 ≈ -800，避免 » 与「1、」粘连
  await imageFit(slide, eid(pageId, 'section_chevron'), 'icon-chevron-lime.png', -860, -360, 48, 48, '»');
  text(slide, eid(pageId, 'section'), section, centerBox(-280, -360, 1040, 56), {
    fontSize: TS.section,
    color: C.brown,
    align: 'left',
  });
}

function notes(slide, scene) {
  slide.speakerNotes.textFrame.setText(
    [
      `[Sources]`,
      `- content-model: ${path.relative(REPO, modelPath)}`,
      `- scene: ${scene.id} (${scene.type || '?'})`,
      `- layer: ${scene.layer || 'observed_reference'}`,
      `- font: ${FONT_FINAL}`,
      `- 图片按原比例装箱；包装/Logo 为业务授权槽位。`,
      scene.note ? `- note: ${scene.note}` : null,
    ]
      .filter(Boolean)
      .join('\n'),
  );
  slide.speakerNotes.setVisible(false);
}

// ───────── scene builders ─────────

async function buildCover(slide, sc) {
  silkBg(slide);
  // far hills
  shape(slide, 'ellipse', centerBox(0, 520, 2200, 420), C.hill, 'none', 'hill');
  shape(slide, 'ellipse', centerBox(-400, 480, 900, 280), 'rgba(190,190,190,0.5)', 'none', 'hill-l');

  const title = sc.title_pill || '福尔番茄红素软胶囊';
  shape(slide, 'roundRect', centerBox(0, -420, 920, 100), C.titlePill, C.titlePill, eid(sc.id, 'title_pill__bar'));
  text(slide, eid(sc.id, 'title_pill'), title, centerBox(0, -420, 880, 88), {
    fontSize: TS.coverTitle,
    color: C.white,
  });

  await imageFit(
    slide,
    eid(sc.id, 'badge_img'),
    'badge-hot-recommend.png',
    760,
    -400,
    200,
    200,
    '好物推荐',
  );

  const benefits = sc.benefits || [
    '保护前列腺，提高精子活力',
    '抗氧化，延缓衰老',
    '增强免疫力',
  ];
  for (let i = 0; i < benefits.length; i++) {
    const y = -160 + i * 110;
    await imageFit(
      slide,
      eid(sc.id, i === 0 ? 'icon_check' : `icon_check.${i + 1}`),
      'icon-check-red.png',
      -820,
      y,
      64,
      64,
      '✓',
    );
    text(slide, eid(sc.id, `benefit.${i + 1}`), benefits[i], centerBox(-420, y, 700, 72), {
      fontSize: TS.coverBenefit,
      color: C.ink,
      align: 'left',
    });
  }

  await imageFit(slide, eid(sc.id, 'pack_a'), 'slot-pack-box-a.png', 280, 60, 280, 400, '盒装A', '盒装 A\n待业务授权');
  await imageFit(slide, eid(sc.id, 'pack_b'), 'slot-pack-box-b.png', 560, 60, 280, 400, '盒装B', '盒装 B\n待业务授权');
  await imageFit(
    slide,
    eid(sc.id, 'pack_bottle'),
    'slot-pack-bottle.png',
    820,
    40,
    260,
    440,
    '瓶装',
    '瓶装\n待业务授权',
  );
}

async function buildTimeList(slide, sc) {
  silkBg(slide);
  // TIME card
  shape(slide, 'rect', centerBox(-560, 40, 400, 560), C.white, C.red, 'time-card');
  text(slide, eid(sc.id, 'time_label'), 'TIME', centerBox(-560, -140, 340, 90), {
    fontSize: TS.timeLabel,
    color: C.red,
  });
  text(slide, eid(sc.id, 'time_sub'), 'Big\nTitle', centerBox(-560, 80, 320, 160), {
    fontSize: Math.round(40 * FS),
    color: C.red,
  });

  // dark list card
  shape(slide, 'roundRect', centerBox(320, 40, 980, 520), C.dark, C.dark, 'list-card');
  await imageFit(slide, eid(sc.id, 'list_chevron'), 'icon-chevron-lime.png', -80, -140, 64, 64, '»');
  text(
    slide,
    eid(sc.id, 'card_title'),
    sc.card_title || '对人类健康贡献最大的10种健康食品',
    centerBox(360, -140, 780, 70),
    {fontSize: TS.cardTitle, color: C.lime, align: 'left'},
  );
  // divider
  shape(slide, 'rect', centerBox(320, -70, 840, 3), C.lime, C.lime, 'list-div');

  const list = sc.list || ['1.番茄', '2.***', '3.***'];
  for (let i = 0; i < list.length; i++) {
    text(slide, eid(sc.id, `list.${i + 1}`), list[i], centerBox(280, 20 + i * 100, 800, 72), {
      fontSize: TS.listItem,
      color: C.white,
      align: 'left',
    });
  }
}

async function buildBroll(slide, sc) {
  silkBg(slide);
  // soft white stage
  shape(slide, 'roundRect', centerBox(0, 20, 1200, 820), 'rgba(255,255,255,0.55)', C.cardBorder, 'photo-stage');
  await imageFit(
    slide,
    eid(sc.id, 'photo'),
    'slot-photo-tomato.png',
    0,
    0,
    1100,
    780,
    '番茄实拍',
    '实拍槽位\n待业务授权',
  );
}

async function buildProductIntro(slide, sc) {
  silkBg(slide);
  await imageFit(
    slide,
    eid(sc.id, 'vine'),
    'slot-photo-vine.png',
    -520,
    20,
    520,
    640,
    '枝头番茄',
    '实拍槽位\n待业务授权',
  );
  await imageFit(slide, eid(sc.id, 'pack_a'), 'slot-pack-box-a.png', 80, 40, 300, 480, '盒装A', '盒装 A\n待授权');
  await imageFit(slide, eid(sc.id, 'pack_b'), 'slot-pack-box-b.png', 400, 40, 300, 480, '盒装B', '盒装 B\n待授权');
  await imageFit(
    slide,
    eid(sc.id, 'pack_bottle'),
    'slot-pack-bottle.png',
    720,
    20,
    300,
    520,
    '瓶装',
    '瓶装\n待授权',
  );
}

const CHAIN_LAYOUTS = {
  S04_benefit_1: [
    {role: 'tomato', file: 'tomato.png', x: -420, size: 320},
    {role: 'arrow', file: 'arrow-red.png', x: -80, size: 100},
    {role: 'prostate', file: 'prostate-diagram.png', x: 360, size: 360},
  ],
  S05_benefit_2: [
    {role: 'tomato', file: 'tomato.png', x: -620, size: 240},
    {role: 'arrow1', file: 'arrow-red.png', x: -360, size: 90},
    {role: 'o2', file: 'o2.png', x: -120, size: 240},
    {role: 'arrow2', file: 'arrow-red.png', x: 160, size: 90},
    {role: 'woman', file: 'skincare-woman.png', x: 480, size: 280},
  ],
  S06_benefit_3: [
    {role: 'tomato', file: 'tomato.png', x: -620, size: 240},
    {role: 'arrow1', file: 'arrow-red.png', x: -360, size: 90},
    {role: 'nk', file: 'nk-cell.png', x: -80, size: 260},
    {role: 'arrow2', file: 'arrow-red.png', x: 220, size: 90},
    {role: 'arm', file: 'flex-arm.png', x: 520, size: 280},
  ],
};

async function buildBenefitChain(slide, sc) {
  silkBg(slide);
  chapterTitle(slide, sc.id, sc.chapter || '一、三大核心功效');
  await sectionLabelAsync(slide, sc.id, sc.section || '');
  const chain = CHAIN_LAYOUTS[sc.id] || CHAIN_LAYOUTS.S04_benefit_1;
  for (const c of chain) {
    await imageFit(slide, eid(sc.id, c.role), c.file, c.x, 80, c.size, c.size, c.role);
  }
  // 副文案：取最后一条 subtitle 作可选说明（培训向）
  const bodyHint = (sc.subtitles || []).slice(-1)[0]?.text;
  if (bodyHint) {
    shape(slide, 'roundRect', centerBox(0, 420, 1600, 64), 'rgba(255,255,255,0.88)', C.cardBorder, 'hint-bar');
    text(slide, eid(sc.id, 'hint'), bodyHint, centerBox(0, 420, 1520, 56), {
      fontSize: TS.body24,
      color: C.brown,
    });
  }
}

async function buildOrigin(slide, sc) {
  silkBg(slide);
  chapterTitle(slide, sc.id, sc.chapter || '二、产品特点');
  await sectionLabelAsync(slide, sc.id, sc.section || '1、产地好');
  text(
    slide,
    eid(sc.id, 'map_caption'),
    sc.map_caption || '中国分省地图—新疆维吾尔自治区',
    centerBox(0, -280, 1200, 48),
    {fontSize: TS.mapCap, color: C.muted},
  );
  // white stage under map
  shape(slide, 'roundRect', centerBox(0, 80, 780, 600), C.white, C.cardBorder, 'map-stage');
  await imageFit(slide, eid(sc.id, 'map'), 'map-xinjiang.png', 0, 60, 720, 560, '新疆地图');
}

async function buildMaterial(slide, sc) {
  silkBg(slide);
  chapterTitle(slide, sc.id, sc.chapter || '二、产品特点');
  await sectionLabelAsync(slide, sc.id, sc.section || '2、原料优');
  shape(slide, 'roundRect', centerBox(0, 80, 960, 680), C.white, C.cardBorder, 'vine-stage');
  await imageFit(
    slide,
    eid(sc.id, 'vine'),
    'slot-photo-vine.png',
    0,
    60,
    900,
    640,
    '原料番茄',
    '原料实拍\n待业务授权',
  );
}

async function buildContent(slide, sc) {
  silkBg(slide);
  chapterTitle(slide, sc.id, sc.chapter || '二、产品特点');
  await sectionLabelAsync(slide, sc.id, sc.section || '3、含量高');
  shape(slide, 'roundRect', centerBox(0, 80, 1600, 620), 'rgba(255,255,255,0.72)', C.cardBorder, 'eq-stage');
  await imageFit(slide, eid(sc.id, 'softgel'), 'softgel.png', -420, 60, 300, 300, '软胶囊');
  text(slide, eid(sc.id, 'eq'), '=', centerBox(0, 40, 160, 160), {
    fontSize: TS.heroEq,
    color: C.gold,
  });
  await imageFit(slide, eid(sc.id, 'five_tomatoes'), 'five-tomatoes.png', 420, 60, 480, 360, '五个番茄');
  const hint = (sc.subtitles || []).find(s => s.text.includes('粒'))?.text
    || '吃1粒番茄红素相当于5个新鲜大番茄';
  text(slide, eid(sc.id, 'eq_caption'), hint, centerBox(0, 380, 1400, 48), {
    fontSize: TS.body26,
    color: C.brown,
  });
}

async function buildAudience(slide, sc) {
  silkBg(slide);
  chapterTitle(slide, sc.id, sc.chapter || '三、适宜人群');
  const items = sc.items || [];
  const iconMap = {
    prostate: 'prostate-diagram.png',
    couple: 'couple.png',
    audience_beauty: 'audience-beauty.png',
    audience_weak: 'audience-weak.png',
  };
  const n = Math.max(items.length, 1);
  const gap = 1760 / n;
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const x = -880 + gap * (i + 0.5);
    // card
    shape(slide, 'roundRect', centerBox(x, 60, gap - 48, 580), C.white, C.cardBorder, `aud-card-${i}`);
    const file = iconMap[it.icon || ''] || 'prostate-diagram.png';
    await imageFit(slide, eid(sc.id, `icon.${i + 1}`), file, x, -40, 260, 260, it.label);
    // yellow label bar
    shape(slide, 'roundRect', centerBox(x, 220, gap - 80, 64), C.redDeep, C.redDeep, `aud-label-bar-${i}`);
    text(slide, eid(sc.id, `label.${i + 1}`), it.label, centerBox(x, 220, gap - 100, 56), {
      fontSize: Math.round(28 * FS),
      color: C.yellow,
    });
  }
}

async function buildEfficacyTable(slide, sc) {
  silkBg(slide);
  chapterTitle(slide, sc.id, sc.chapter || '五、福尔番茄红素三大核心功效');
  const rows = sc.rows || [];
  const tableW = 1600;
  const tableH = 720;
  const topY = 40;
  shape(slide, 'roundRect', centerBox(0, topY, tableW, tableH), C.white, C.tableBorder, 'eff-table');

  const fh = tableH / Math.max(rows.length, 1);
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const y = topY - tableH / 2 + fh * (i + 0.5);
    if (i > 0) {
      shape(slide, 'rect', centerBox(0, y - fh / 2, tableW - 8, 2), C.tableBorder, C.tableBorder, `eff-div-${i}`);
    }
    // left col divider
    shape(slide, 'rect', centerBox(-400, y, 2, fh - 8), C.tableBorder, C.tableBorder, `eff-vdiv-${i}`);
    await imageFit(slide, eid(sc.id, `row.${i + 1}.chevron`), 'icon-chevron-lime.png', -720, y, 44, 44, '»');
    text(
      slide,
      eid(sc.id, `row.${i + 1}.label`),
      row.label,
      centerBox(-560, y, 300, fh - 24),
      {fontSize: Math.round(30 * FS), color: C.brown, align: 'left'},
    );
    text(
      slide,
      eid(sc.id, `row.${i + 1}.body`),
      row.body,
      centerBox(200, y, 1100, fh - 24),
      {fontSize: Math.round(24 * FS), color: C.brown, align: 'left', bold: false},
    );
  }

  // side notes (training dosage / contraindication) — compact bottom strip for PPT readability
  if (sc.side_left || sc.side_right) {
    shape(slide, 'roundRect', centerBox(0, 460, 1600, 56), 'rgba(106,58,48,0.08)', 'none', 'side-strip');
    const side = [sc.side_left, sc.side_right].filter(Boolean).join('　|　');
    text(slide, eid(sc.id, 'side_combined'), side, centerBox(0, 460, 1540, 48), {
      fontSize: TS.body18,
      color: C.muted,
      bold: false,
    });
  }
}

async function buildRelatedMeds(slide, sc) {
  silkBg(slide);
  chapterTitle(slide, sc.id, sc.chapter || '四、关联用药');

  const nav = sc.nav || ['组合1', '组合2'];
  const active = sc.active_nav ?? 0;
  const navLayout = [
    {x: -380, w: 720},
    {x: 420, w: 700},
  ];
  for (let i = 0; i < nav.length; i++) {
    const {x, w} = navLayout[i] || {x: 0, w: 600};
    const on = i === active;
    shape(
      slide,
      'roundRect',
      centerBox(x, -340, w, 64),
      on ? C.red : C.pillOff,
      on ? C.red : C.pillOff,
      eid(sc.id, `nav.${i + 1}__pill`),
    );
    shape(
      slide,
      'ellipse',
      centerBox(x - w / 2 + 28, -340, 36, 36),
      on ? C.white : C.red,
      on ? C.white : C.red,
    );
    text(slide, eid(sc.id, `nav.${i + 1}__n`), String(i + 1), centerBox(x - w / 2 + 28, -340, 32, 32), {
      fontSize: TS.navNum,
      color: on ? C.red : C.white,
    });
    text(slide, eid(sc.id, `nav.${i + 1}`), nav[i], centerBox(x + 20, -340, w - 90, 52), {
      fontSize: TS.nav,
      color: on ? C.white : C.muted,
      align: 'left',
    });
  }

  // note ABOVE packs（金样经验：先讲为什么一起用）
  text(slide, eid(sc.id, 'note'), sc.note || '', centerBox(0, -240, 1600, 70), {
    fontSize: TS.body32,
    color: C.ink,
  });

  // white stage
  shape(slide, 'roundRect', centerBox(0, 100, 1600, 560), C.white, C.cardBorder, 'related-stage');
  // soft cards under packs
  shape(slide, 'roundRect', centerBox(-360, 40, 420, 360), C.silkLight, C.cardBorder, 'pack-l-card');
  shape(slide, 'roundRect', centerBox(360, 40, 420, 360), C.silkLight, C.cardBorder, 'pack-r-card');

  await imageFit(
    slide,
    eid(sc.id, 'pack_left'),
    sc.left_pack || 'slot-pack-lycopene.png',
    -360,
    0,
    320,
    320,
    sc.left_label || '本品',
    `${sc.left_label || '本品'}\n待业务授权`,
  );
  text(slide, eid(sc.id, 'plus'), '+', centerBox(0, 20, 100, 100), {
    fontSize: TS.plus,
    color: C.red,
  });
  await imageFit(
    slide,
    eid(sc.id, 'pack_right'),
    sc.right_pack || 'slot-pack-zinc.png',
    360,
    0,
    300,
    300,
    sc.right_label || '关联品',
    `${sc.right_label || '关联品'}\n待业务授权`,
  );
  text(slide, eid(sc.id, 'left_label'), sc.left_label || '', centerBox(-360, 250, 400, 48), {
    fontSize: TS.body26,
    color: C.brown,
  });
  text(slide, eid(sc.id, 'right_label'), sc.right_label || '', centerBox(360, 250, 400, 48), {
    fontSize: TS.body26,
    color: C.brown,
  });
}

async function buildSummaryRows(slide, sc) {
  silkBg(slide);
  // eyebrow
  shape(slide, 'ellipse', centerBox(-820, -460, 28, 28), C.red, C.red, 'eyebrow-dot');
  text(slide, eid(sc.id, 'eyebrow'), sc.eyebrow || '敲重点', centerBox(-640, -460, 280, 48), {
    fontSize: TS.eyebrow,
    color: C.red,
    align: 'left',
  });
  // chapter pill
  shape(slide, 'roundRect', centerBox(0, -460, 280, 72), C.red, C.red, eid(sc.id, 'chapter__pill'));
  text(slide, eid(sc.id, 'chapter'), sc.chapter || '总结', centerBox(0, -460, 250, 64), {
    fontSize: Math.round(40 * FS),
    color: C.white,
  });

  const cols = sc.columns || [];
  const n = Math.max(cols.length, 1);
  const tableW = 1760;
  const tableH = 720;
  const topY = 20;
  shape(slide, 'roundRect', centerBox(0, topY, tableW, tableH), C.white, C.cardBorder, 'sum-table');

  const rowH = tableH / n;
  for (let i = 0; i < cols.length; i++) {
    const col = cols[i];
    const y = topY - tableH / 2 + rowH * (i + 0.5);
    if (i > 0) {
      shape(slide, 'rect', centerBox(0, y - rowH / 2, tableW - 4, 2), C.cardBorder, C.cardBorder, `sum-div-${i}`);
    }
    // red row header
    shape(
      slide,
      'rect',
      centerBox(-tableW / 2 + 120, y, 240, rowH - 2),
      C.red,
      C.red,
      eid(sc.id, `row.${i + 1}.label__bar`),
    );
    text(
      slide,
      eid(sc.id, `row.${i + 1}.label`),
      col.header,
      centerBox(-tableW / 2 + 120, y, 220, rowH - 16),
      {fontSize: TS.rowLabel, color: C.white},
    );
    const body = (col.items || []).join('\n');
    text(
      slide,
      eid(sc.id, `row.${i + 1}.body`),
      body,
      centerBox(140, y, 1400, rowH - 20),
      {fontSize: TS.rowBody, color: C.ink, align: 'left', bold: false, vAlign: 'middle'},
    );
  }

  if (sc.footer) {
    text(slide, eid(sc.id, 'footer'), sc.footer, centerBox(0, 470, 1700, 44), {
      fontSize: TS.footer,
      color: C.ink,
    });
  }
}

const builders = {
  cover: buildCover,
  time_list: buildTimeList,
  broll: buildBroll,
  product_intro: buildProductIntro,
  benefit_chain: buildBenefitChain,
  feature_origin: buildOrigin,
  feature_material: buildMaterial,
  feature_content: buildContent,
  audience: buildAudience,
  efficacy_recap_table: buildEfficacyTable,
  related_meds: buildRelatedMeds,
  summary_4col: buildSummaryRows,
};

// ───────── main ─────────

const presentation = Presentation.create({slideSize: {width: W, height: H}});
const scenes = model.scenes || [];
const pageIds = [];

for (const sc of scenes) {
  const slide = presentation.slides.add();
  const builder = builders[sc.type] || (sc.type === 'cover' ? buildCover : null);
  if (!builder) {
    silkBg(slide);
    text(slide, eid(sc.id, 'fallback'), sc.id, centerBox(0, 0, 800, 80), {
      fontSize: TS.chapter,
      color: C.ink,
    });
  } else {
    await builder(slide, sc);
  }
  notes(slide, sc);
  pageIds.push(sc.id);
}

await fs.mkdir(path.dirname(outPath), {recursive: true});
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outPath);

const patchScript = path.join(__dirname, 'patch-pptx-font.py');
const patch = spawnSync('python3', [patchScript, outPath, FONT_FINAL], {encoding: 'utf8'});
if (patch.status !== 0) {
  console.warn('font patch failed:', patch.stderr || patch.stdout);
} else if (patch.stdout) {
  console.log(patch.stdout.trim());
}

const inspect = {
  ok: true,
  out: outPath,
  slides: pageIds.length,
  page_ids: pageIds,
  model: path.relative(REPO, modelPath),
  patches: Object.keys(patches).length,
  project_id: model.project_id,
  font: FONT_FINAL,
  layout: 'video-design-coords-scaled-1280x720',
  image_fit: 'native-aspect-contain-box',
  element_id_prefix: 'editable:cw4',
  font_patched: patch.status === 0,
  experience: {
    related_meds: 'note-above-packs',
    summary: 'row_headers_full_sentences',
  },
};
const inspectPath = outPath + '.inspect.json';
await fs.writeFile(inspectPath, JSON.stringify(inspect, null, 2) + '\n');
console.log(JSON.stringify(inspect, null, 2));
