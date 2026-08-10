/**
 * 从 content-model.json（+ 可选 editor patches snapshot）导出原生可编辑 PPTX。
 * 布局 / 字号对齐视频金样（1920×1080 设计坐标 → 标准 16:9 1280×720 画布）。
 * 图片严格按资源原始宽高比装箱，避免 stretch 变形。
 *
 * Usage:
 *   node scripts/export-sufuda-pptx.mjs
 *   node scripts/export-sufuda-pptx.mjs /path/to/project-snapshot.json
 *   node scripts/export-sufuda-pptx.mjs --model /path/to/content-model.json --out /path/to/out.pptx
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
    path.join(ROOT, 'out', '速福达玛巴洛沙韦_商品培训课件3_金样_可编辑课件_v2.pptx'),
  ),
);
const assetsRoot = path.resolve(argValue('--assets', path.join(ROOT, 'public')));
const qaValue = argValue('--qa', null);
const qaDir = qaValue ? path.resolve(qaValue) : null;
const reportValue = argValue('--report', null);
const reportPath = reportValue
  ? path.resolve(reportValue)
  : qaDir
    ? path.join(qaDir, 'generate-report.json')
    : outPath + '.inspect.json';

/** 视频设计坐标 */
const DW = 1920;
const DH = 1080;
/** PPT 画布（标准 16:9，与其它课件导出一致） */
const W = 1280;
const H = 720;
const SX = W / DW;
const SY = H / DH;
/** 字号：视频像素字号 × 画布缩放（artifact 按 px→pt 再落盘） */
const FS = SY;

const model = JSON.parse(await fs.readFile(modelPath, 'utf8'));
const patches = snapshotPath
  ? JSON.parse(await fs.readFile(snapshotPath, 'utf8')).patches ?? {}
  : {};
const C = model.tokens || {};
const assets = model.assets;

/** 与视频 project.tsx 一致：优先 HarmonyOS Sans SC */
const FONT_FINAL =
  (C.font_family || 'HarmonyOS Sans SC, Source Han Sans SC, PingFang SC')
    .split(',')[0]
    .trim();

/** 视频设计字号 → PPT：优先 content-model tokens.fs_*（v2 单源），缺省回退硬编码 */
function designFs(tokenKey, fallback) {
  const raw = C[tokenKey];
  const n = raw != null && raw !== '' ? Number(raw) : NaN;
  return Math.round((Number.isFinite(n) ? n : fallback) * FS);
}

const TS = {
  coverTitle: designFs('fs_cover_title', 84),
  coverSub: designFs('fs_cover_sub', 36),
  coverCheck: designFs('fs_cover_check', 40),
  chapter: designFs('fs_chapter', 48),
  nav: designFs('fs_nav', 28),
  navNum: designFs('fs_nav_num', 24),
  cardTitle: designFs('fs_card_title', 36),
  cardBody: designFs('fs_card_body', 30),
  heroNum: designFs('fs_hero_num', 72),
  bubble: designFs('fs_bubble', 46),
  labelLg: Math.round(44 * FS),
  labelMd: Math.round(40 * FS),
  body32: Math.round(32 * FS),
  body30: Math.round(30 * FS),
  body28: Math.round(28 * FS),
  body26: Math.round(26 * FS),
  body24: Math.round(24 * FS),
  body22: Math.round(22 * FS),
  body20: Math.round(20 * FS),
  body18: Math.round(18 * FS),
  ageHero: Math.round(78 * FS),
  // 屏显字幕在视频里用 fs_caption；PPT 页脚/小字仍用较小可读字号，避免占满版心
  caption: Math.round(16 * FS),
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

function readImageSize(buf) {
  if (!buf || buf.length < 24) return null;
  // PNG
  if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47) {
    const w = (buf[16] << 24) | (buf[17] << 16) | (buf[18] << 8) | buf[19];
    const h = (buf[20] << 24) | (buf[21] << 16) | (buf[22] << 8) | buf[23];
    if (w > 0 && h > 0) return {w, h};
  }
  // JPEG SOF
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

/** 在 maxW×maxH 内按资源原始比例 contain，中心对齐 (cx,cy) */
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

async function loadAsset(assetKeyOrPath) {
  let rel = assets[assetKeyOrPath] ?? assetKeyOrPath;
  if (typeof rel === 'string' && rel.startsWith('/assets/')) rel = rel.slice(1);
  const full = path.isAbsolute(rel) ? rel : path.join(assetsRoot, rel);
  try {
    const buf = await fs.readFile(full);
    return new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
  } catch {
    return null;
  }
}

function patchedText(elementId, fallback) {
  return patches[elementId]?.text ?? fallback;
}

function patchedSrc(elementId, fallbackAssetKey) {
  return patches[elementId]?.src ?? fallbackAssetKey;
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
    color: opts.color ?? C.ink ?? '#182a43',
    alignment: opts.align ?? 'center',
    verticalAlignment: opts.vAlign ?? 'middle',
  };
  return box;
}

/**
 * 缺图时画可见占位卡（圆角底 + 描边 + 说明文案），避免空白不知所云。
 */
function drawPlaceholderCard(slide, elementId, cx, cy, maxW, maxH, label) {
  const pos = centerBox(cx, cy, maxW, maxH);
  shape(slide, 'roundRect', pos, C.row_bg ?? '#fff3e0', C.orange, elementId);
  // 内框
  shape(
    slide,
    'roundRect',
    centerBox(cx, cy, Math.max(40, maxW - 28), Math.max(40, maxH - 28)),
    '#ffffff',
    C.orange2 ?? C.orange,
    elementId + '__inner',
  );
  text(slide, `${elementId}__slot`, label || '图片占位\n待业务替换', centerBox(cx, cy + maxH * 0.12, maxW - 40, maxH * 0.45), {
    fontSize: TS.body20,
    color: C.navy ?? C.ink,
  });
  text(slide, `${elementId}__hint`, '可替换', centerBox(cx, cy - maxH * 0.22, maxW - 48, 36), {
    fontSize: TS.caption,
    color: C.muted,
  });
  return null;
}

/**
 * 放置图片：按资源原生比例装箱，杜绝 stretch 变形。
 * maxW/maxH 为设计坐标中的最大占用；缺图时用 slotPlaceholder 或占位卡。
 */
async function imageFit(slide, elementId, assetKey, cx, cy, maxW, maxH, alt = '', placeholderLabel = '') {
  const key = patchedSrc(elementId, assetKey);
  let blob = null;
  if (typeof key === 'string' && key.startsWith('assets/')) {
    try {
      const buf = await fs.readFile(path.join(path.dirname(outPath), key));
      blob = new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
    } catch {
      blob = null;
    }
  } else {
    blob = await loadAsset(key);
  }
  // 主图缺失 → 通用占位图资源 → 形状占位卡
  if (!blob) {
    blob = await loadAsset('slotPlaceholder');
  }
  if (!blob) {
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
  const size = readImageSize(blob);
  const position = containBox(cx, cy, maxW, maxH, size?.w, size?.h);
  return slide.images.add({
    blob,
    contentType: 'image/png',
    alt: alt || elementId,
    fit: 'fill', // 框已按 AR 计算，fill 即等比显示
    position,
    name: elementId,
  });
}

async function bg(slide) {
  const blob = await loadAsset('background');
  if (blob) {
    slide.images.add({
      blob,
      contentType: 'image/png',
      alt: '丝绸背景',
      fit: 'cover',
      position: {left: 0, top: 0, width: W, height: H},
    });
  } else {
    shape(slide, 'rect', {left: 0, top: 0, width: W, height: H}, '#f7f5f2');
  }
}

async function logo(slide, pageId) {
  const el = model.pages.find(p => p.id === pageId)?.elements?.logo;
  if (!el) return;
  // 与视频 LogoMark: position [790,-478] size [300,86]
  await imageFit(slide, el.id, el.asset ?? 'logo', 790, -478, 300, 86, 'logo');
}

async function chapterRibbon(slide, pageId, chapterText) {
  const el = model.pages.find(p => p.id === pageId)?.elements?.chapter;
  const id = el?.id ?? `editable:sufuda:${pageId}:chapter`;
  const title = (chapterText ?? el?.text ?? pageId).trim() || pageId;
  // 1) 实心橙底条：保证标题永不「白字叠白底」消失
  shape(slide, 'roundRect', centerBox(0, -458, 760, 100), C.orange, C.orange, id + '__bar');
  // 2) 可选丝带装饰（失败不影响可读性）
  try {
    await imageFit(slide, id + '__ribbon', 'ribbonChapter', 0, -458, 720, 100, 'chapter-ribbon');
  } catch {
    /* ignore */
  }
  // 3) 白字标题压在最上层
  text(slide, id, title, centerBox(0, -458, 700, 86), {
    fontSize: TS.chapter,
    color: C.white,
  });
}

function navPills(slide, page, active, layout) {
  const items = page.nav ?? [];
  if (!items.length) return;
  // layout: array of {x, w} in design coords，与视频 NavPill 一致
  const pills =
    layout ??
    (items.length === 3
      ? [
          {x: -520, w: 440},
          {x: 20, w: 480},
          {x: 500, w: 300},
        ]
      : items.length === 2
        ? [
            {x: -360, w: 580},
            {x: 380, w: 660},
          ]
        : items.map((_, i) => ({x: (i - (items.length - 1) / 2) * 400, w: 360})));

  items.forEach((label, i) => {
    const {x, w} = pills[i] ?? {x: 0, w: 360};
    const on = i === (active ?? page.active_nav ?? 0);
    const role = `nav${i + 1}`;
    const el = page.elements[role];
    const id = el?.id ?? `editable:sufuda:${page.id}:${role}`;
    shape(
      slide,
      'roundRect',
      centerBox(x, -348, w, 64),
      on ? C.orange : C.gray,
      on ? C.orange : C.gray,
      id + '__pill',
    );
    shape(slide, 'ellipse', centerBox(x - w / 2 + 30, -348, 46, 46), C.white, C.white);
    text(slide, id + '__n', String(i + 1), centerBox(x - w / 2 + 30, -348, 40, 40), {
      fontSize: TS.navNum,
      color: on ? C.orange : C.muted,
    });
    text(slide, id, el?.text ?? label, centerBox(x + 12, -348, w - 80, 50), {
      fontSize: TS.nav,
      color: C.white,
    });
  });
}

function el(page, role) {
  return page.elements[role];
}

function notes(slide, page) {
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n- content-model: ${path.relative(REPO, modelPath)}\n- page: ${page.id} (${page.type})\n- style_pack: ${model.style_pack_id}\n- font: ${FONT_FINAL}\n- 图片按原比例装箱；包装/Logo 为业务授权槽位。`,
  );
  slide.speakerNotes.setVisible(false);
}

// ───────── builders（坐标对齐 project.tsx） ─────────

async function buildCover(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  text(slide, el(page, 'title').id, el(page, 'title').text, centerBox(0, -320, 1400, 100), {
    fontSize: TS.coverTitle,
    color: C.navy2,
  });
  shape(slide, 'roundRect', centerBox(0, -220, 900, 72), C.orange, C.orange);
  text(slide, el(page, 'tagline').id, el(page, 'tagline').text, centerBox(0, -220, 860, 64), {
    fontSize: TS.coverSub,
    color: C.white,
  });
  ['check1', 'check2', 'check3'].forEach((role, i) => {
    const y = -40 + i * 90;
    shape(slide, 'ellipse', centerBox(-750, y, 46, 46), C.orange, C.orange);
    text(slide, el(page, role).id + '__tick', '✓', centerBox(-750, y, 40, 40), {
      fontSize: TS.body28,
      color: C.white,
    });
    text(slide, el(page, role).id, el(page, role).text, centerBox(-420, y, 560, 70), {
      fontSize: TS.coverCheck,
      color: C.ink,
      align: 'left',
    });
  });
  await imageFit(slide, el(page, 'pack').id, el(page, 'pack').asset, 400, 90, 820, 560, 'pack');
  text(slide, el(page, 'pack_note').id, el(page, 'pack_note').text, centerBox(780, 490, 360, 32), {
    fontSize: TS.caption,
    color: C.muted,
  });
}

async function buildFlu(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  for (const x of [-520, 0, 520]) {
    shape(slide, 'roundRect', centerBox(x, -20, 420, 640), C.white, '#e8edf2');
  }
  await imageFit(slide, el(page, 'card1_icon_a').id, 'icon365', -520, -190, 200, 200);
  text(slide, el(page, 'card1_title').id, el(page, 'card1_title').text, centerBox(-520, -40, 360, 50), {
    fontSize: TS.cardTitle,
    color: C.navy,
  });
  await imageFit(slide, el(page, 'card1_icon_b').id, 'iconTree', -520, 100, 200, 200);
  text(slide, el(page, 'card1_body').id, el(page, 'card1_body').text, centerBox(-520, 250, 360, 90), {
    fontSize: TS.cardBody,
    color: C.navy2,
  });

  await imageFit(slide, el(page, 'card2_icon_a').id, 'iconVirus', 0, -210, 120, 120);
  text(slide, el(page, 'card2_t1').id, el(page, 'card2_t1').text, centerBox(0, -110, 320, 44), {
    fontSize: TS.cardTitle,
    color: C.navy,
  });
  await imageFit(slide, el(page, 'card2_icon_b').id, 'iconLungs', 0, -10, 110, 110);
  text(slide, el(page, 'card2_t2').id, el(page, 'card2_t2').text, centerBox(0, 80, 320, 44), {
    fontSize: TS.cardTitle,
    color: C.navy,
  });
  await imageFit(slide, el(page, 'card2_icon_c').id, 'iconWarn', 0, 170, 100, 100);
  text(slide, el(page, 'card2_t3').id, el(page, 'card2_t3').text, centerBox(0, 255, 320, 44), {
    fontSize: TS.cardTitle,
    color: C.navy,
  });

  await imageFit(slide, el(page, 'card3_icon').id, 'iconChina', 520, -180, 190, 160);
  text(slide, el(page, 'card3_num').id, el(page, 'card3_num').text, centerBox(520, -20, 320, 80), {
    fontSize: TS.heroNum,
    color: C.orange,
  });
  text(slide, el(page, 'card3_body').id, el(page, 'card3_body').text, centerBox(520, 100, 340, 100), {
    fontSize: TS.cardBody,
    color: C.navy,
  });

  shape(slide, 'roundRect', centerBox(0, 400, 1100, 76), 'rgba(255,255,255,0.95)', '#e8edf2');
  text(slide, el(page, 'footer').id, el(page, 'footer').text, centerBox(0, 400, 1040, 64), {
    fontSize: TS.cardTitle,
    color: C.navy,
  });
}

async function buildBenefit1(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav, [
    {x: -520, w: 360},
    {x: 20, w: 400},
    {x: 500, w: 400},
  ]);
  await imageFit(slide, el(page, 'pack').id, 'packGroup', 0, 50, 700, 480);
  await imageFit(slide, el(page, 'badge_jia').id, 'badgeJia', -430, -20, 200, 200);
  text(slide, el(page, 'badge_jia_label').id, el(page, 'badge_jia_label').text, centerBox(-430, -12, 100, 80), {
    fontSize: Math.round(64 * FS),
    color: C.navy2,
  });
  await imageFit(slide, el(page, 'badge_yi').id, 'badgeYi', -220, 120, 170, 170);
  text(slide, el(page, 'badge_yi_label').id, el(page, 'badge_yi_label').text, centerBox(-220, 126, 90, 70), {
    fontSize: Math.round(56 * FS),
    color: C.orange,
  });
  await imageFit(slide, el(page, 'bubble').id, 'bubbleSpeech', 430, -10, 420, 340);
  text(slide, el(page, 'bubble_text').id, el(page, 'bubble_text').text, centerBox(430, -10, 280, 180), {
    fontSize: TS.bubble,
    color: C.white,
  });
}

async function buildBenefit2(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav, [
    {x: -520, w: 360},
    {x: 20, w: 400},
    {x: 500, w: 400},
  ]);
  shape(slide, 'roundRect', centerBox(0, 40, 1600, 560), 'rgba(255,255,255,0.96)', '#e8edf2');
  shape(slide, 'roundRect', centerBox(-620, -80, 260, 70), C.orange, C.orange);
  text(slide, el(page, 'dose1').id, el(page, 'dose1').text, centerBox(-620, -80, 240, 60), {
    fontSize: TS.body32,
    color: C.white,
  });
  shape(slide, 'roundRect', centerBox(-620, 20, 280, 70), C.orange, C.orange);
  text(slide, el(page, 'drug_a').id, el(page, 'drug_a').text, centerBox(-620, 20, 260, 60), {
    fontSize: Math.round(34 * FS),
    color: C.white,
  });
  shape(slide, 'roundRect', centerBox(-620, 140, 280, 70), C.orange2, C.orange2);
  text(slide, el(page, 'dose24').id, el(page, 'dose24').text, centerBox(-620, 140, 260, 60), {
    fontSize: TS.body28,
    color: C.white,
  });
  await imageFit(slide, el(page, 'cell').id, 'cell', 40, 40, 560, 400);
  text(slide, el(page, 'mech_left').id, el(page, 'mech_left').text, centerBox(40, -200, 520, 90), {
    fontSize: TS.body32,
    color: C.orange,
  });
  shape(slide, 'roundRect', centerBox(560, 20, 280, 70), '#8e949c', '#8e949c');
  text(slide, el(page, 'drug_b').id, el(page, 'drug_b').text, centerBox(560, 20, 260, 60), {
    fontSize: Math.round(36 * FS),
    color: C.white,
  });
  text(slide, el(page, 'mech_right').id, el(page, 'mech_right').text, centerBox(560, 140, 320, 90), {
    fontSize: TS.body28,
    color: C.muted,
  });
}

async function buildBenefit3(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav, [
    {x: -520, w: 360},
    {x: 20, w: 400},
    {x: 500, w: 400},
  ]);
  await imageFit(slide, el(page, 'patient').id, 'patient', -420, 40, 320, 520);
  await imageFit(slide, el(page, 'family').id, 'family', 280, 20, 580, 580);
  text(slide, el(page, 'patient_label').id, el(page, 'patient_label').text, centerBox(-420, 340, 360, 50), {
    fontSize: TS.body32,
    color: C.navy,
  });
  text(slide, el(page, 'family_label').id, el(page, 'family_label').text, centerBox(280, 340, 420, 50), {
    fontSize: TS.body32,
    color: C.navy,
  });
}

async function buildFeature1(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  await imageFit(slide, el(page, 'icon_baby').id, 'iconBaby', -560, 0, 180, 180);
  text(slide, el(page, 'label_left').id, el(page, 'label_left').text, centerBox(-560, 140, 300, 56), {
    fontSize: TS.labelLg,
    color: C.navy,
  });
  shape(slide, 'ellipse', centerBox(0, 30, 620, 620), C.white, C.orange2);
  await imageFit(slide, el(page, 'pack').id, 'packGroup', 0, 30, 520, 380);
  await imageFit(slide, el(page, 'icon_shield').id, 'iconShield', 560, 0, 160, 160);
  text(slide, el(page, 'label_right').id, el(page, 'label_right').text, centerBox(560, 140, 300, 56), {
    fontSize: TS.labelMd,
    color: C.navy,
  });
}

async function buildFeature2(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  // left tablet card
  shape(slide, 'roundRect', centerBox(-500, 20, 400, 520), C.white, '#e8edf2');
  await imageFit(slide, el(page, 'tablets').id, 'tablets', -500, -50, 320, 320);
  shape(slide, 'roundRect', centerBox(-590, 150, 150, 72), '#f7f9fc', '#f7f9fc');
  text(slide, el(page, 'dose_20').id, el(page, 'dose_20').text, centerBox(-590, 150, 140, 68), {
    fontSize: TS.body20,
    color: C.navy,
  });
  shape(slide, 'roundRect', centerBox(-410, 150, 150, 72), '#f7f9fc', '#f7f9fc');
  text(slide, el(page, 'dose_40').id, el(page, 'dose_40').text, centerBox(-410, 150, 140, 68), {
    fontSize: TS.body20,
    color: C.navy,
  });
  shape(slide, 'roundRect', centerBox(-620, -210, 200, 96), C.orange, C.orange);
  text(slide, el(page, 'tab_bubble').id, el(page, 'tab_bubble').text, centerBox(-620, -210, 180, 88), {
    fontSize: TS.body26,
    color: C.white,
  });
  // center pack
  shape(slide, 'ellipse', centerBox(0, 20, 440, 440), C.white, C.orange2);
  await imageFit(slide, el(page, 'pack').id, 'packGroup', 0, 20, 360, 270);
  // right granule
  shape(slide, 'roundRect', centerBox(500, 20, 400, 520), C.white, '#e8edf2');
  await imageFit(slide, el(page, 'granule').id, 'granule', 500, -40, 320, 320);
  text(slide, el(page, 'granule_label').id, el(page, 'granule_label').text, centerBox(500, 180, 360, 60), {
    fontSize: TS.body24,
    color: C.navy,
  });
  shape(slide, 'roundRect', centerBox(620, -210, 230, 88), C.orange, C.orange);
  text(slide, el(page, 'strawberry').id, el(page, 'strawberry').text, centerBox(640, -210, 180, 70), {
    fontSize: TS.body28,
    color: C.white,
  });
}

async function buildFeature3(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  // row1 full
  shape(slide, 'roundRect', centerBox(0, -170, 1500, 110), C.row_bg2, C.row_bg2);
  await imageFit(slide, el(page, 'icon_flag').id, 'iconFlag', -640, -170, 72, 72);
  text(slide, el(page, 'row1').id, el(page, 'row1').text, centerBox(40, -170, 1280, 90), {
    fontSize: Math.round(34 * FS),
    color: C.navy,
    align: 'left',
  });
  // row2 left
  shape(slide, 'roundRect', centerBox(-360, 0, 640, 110), C.row_bg2, C.row_bg2);
  await imageFit(slide, el(page, 'icon_70').id, 'icon70', -600, 0, 80, 80);
  text(slide, el(page, 'row2').id, el(page, 'row2').text, centerBox(-280, 0, 480, 80), {
    fontSize: Math.round(34 * FS),
    color: C.navy,
    align: 'left',
  });
  // row3 right
  shape(slide, 'roundRect', centerBox(360, 0, 640, 110), C.row_bg2, C.row_bg2);
  await imageFit(slide, el(page, 'icon_thumb').id, 'iconThumb', 120, 0, 72, 72);
  text(slide, el(page, 'row3').id, el(page, 'row3').text, centerBox(420, 0, 480, 80), {
    fontSize: TS.body32,
    color: C.navy,
    align: 'left',
  });
  // row4
  shape(slide, 'roundRect', centerBox(0, 170, 920, 110), C.row_bg2, C.row_bg2);
  await imageFit(slide, el(page, 'icon_award').id, 'iconAward', -380, 170, 80, 80);
  text(slide, el(page, 'row4').id, el(page, 'row4').text, centerBox(40, 170, 760, 80), {
    fontSize: Math.round(36 * FS),
    color: C.navy,
    align: 'left',
  });
}

/** 适宜人群 A1：人物线稿 + ≥5岁 橙气泡（单独一页，对齐参考视频） */
async function buildAudienceAge(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  await imageFit(slide, el(page, 'person').id, 'personOutline', -360, 40, 360, 480);
  // 大橙圆气泡
  shape(slide, 'ellipse', centerBox(320, 20, 560, 420), C.orange, C.orange);
  text(slide, el(page, 'age').id, el(page, 'age').text, centerBox(320, -50, 420, 100), {
    fontSize: TS.ageHero,
    color: C.white,
  });
  text(slide, el(page, 'age_body').id, el(page, 'age_body').text, centerBox(320, 70, 400, 160), {
    fontSize: TS.body28,
    color: C.white,
  });
}

/** 适宜人群 A2：三类人群卡片（不与 A1 叠放） */
async function buildAudiencePeople(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await chapterRibbon(slide, page.id, page.chapter);
  text(slide, el(page, 'headline').id, el(page, 'headline').text, centerBox(0, -300, 1680, 60), {
    fontSize: TS.body30,
    color: C.navy,
  });
  const cards = [
    {role: 'elder', x: -480, img: 'charElder', label: 'elder_label', maxW: 260, maxH: 360},
    {role: 'child', x: 0, img: 'charChild', label: 'child_label', maxW: 260, maxH: 360},
    {role: 'chronic', x: 480, img: 'charChronic', label: 'chronic_label', maxW: 340, maxH: 300},
  ];
  for (const c of cards) {
    shape(slide, 'roundRect', centerBox(c.x, 60, 400, 520), C.white, '#e8edf2');
    await imageFit(slide, el(page, `${c.role}_img`).id, c.img, c.x, -40, c.maxW, c.maxH);
    text(slide, el(page, c.label).id, el(page, c.label).text, centerBox(c.x, 200, 360, 56), {
      fontSize: c.role === 'chronic' ? TS.body30 : TS.body32,
      color: C.navy,
    });
  }
}

async function buildCombo(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  // 章节标题必须用 page.chapter / elements.chapter，避免白字不可见
  await chapterRibbon(slide, page.id, page.chapter ?? el(page, 'chapter')?.text ?? '三、联合用药');
  navPills(slide, page, page.active_nav, [
    {x: -360, w: 580},
    {x: 380, w: 660},
  ]);
  text(slide, el(page, 'note').id, el(page, 'note').text, centerBox(0, -200, 1400, 70), {
    fontSize: Math.round(36 * FS),
    color: C.navy,
  });
  // 白底舞台，保证包装/占位图有衬底
  shape(slide, 'roundRect', centerBox(0, 80, 1600, 480), 'rgba(255,255,255,0.98)', '#e8edf2');
  // 左右浅底卡片，避免「空着不知道是什么」
  shape(slide, 'roundRect', centerBox(-360, 60, 520, 360), '#f7f9fc', '#e8edf2', el(page, 'pack').id + '__card');
  shape(slide, 'roundRect', centerBox(360, 60, 440, 320), '#f7f9fc', '#e8edf2', el(page, 'other').id + '__card');

  await imageFit(
    slide,
    el(page, 'pack').id,
    'packGroup',
    -360,
    40,
    500,
    320,
    'pack',
    '产品包装\n待业务替换',
  );
  const packLabel = el(page, 'pack_label');
  if (packLabel) {
    text(slide, packLabel.id, packLabel.text, centerBox(-360, 230, 420, 48), {
      fontSize: TS.body28,
      color: C.navy,
    });
  }

  text(slide, el(page, 'plus').id, '+', centerBox(0, 60, 100, 100), {
    fontSize: Math.round(110 * FS),
    color: C.orange,
  });

  await imageFit(
    slide,
    el(page, 'other').id,
    el(page, 'other').asset,
    360,
    40,
    380,
    260,
    'combo-other',
    page.id === 'combo_2' ? '慢病药物\n待业务替换' : '退热药\n待业务替换',
  );
  const otherLabel = el(page, 'other_label');
  if (otherLabel) {
    text(slide, otherLabel.id, otherLabel.text, centerBox(360, 230, 400, 48), {
      fontSize: TS.body24,
      color: C.navy,
    });
  }
}

async function buildSummary(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await imageFit(slide, el(page, 'icon_hand').id, 'iconHand', -780, -430, 100, 100);
  text(slide, el(page, 'eyebrow').id, el(page, 'eyebrow').text, centerBox(-640, -430, 200, 48), {
    fontSize: TS.body32,
    color: C.orange,
  });
  await chapterRibbon(slide, page.id, page.chapter);
  shape(slide, 'rect', centerBox(0, -300, 1680, 70), C.orange, C.orange);
  ['col_h1', 'col_h2', 'col_h3', 'col_h4'].forEach((role, i) => {
    text(slide, el(page, role).id, el(page, role).text, centerBox(-630 + i * 420, -300, 380, 56), {
      fontSize: Math.round(34 * FS),
      color: C.white,
    });
  });
  shape(slide, 'roundRect', centerBox(0, 40, 1680, 560), 'rgba(255,255,255,0.96)', '#e8edf2');
  text(slide, el(page, 'e1').id, el(page, 'e1').text, centerBox(-630, -200, 380, 50), {
    fontSize: TS.body30,
    color: C.orange,
  });
  text(slide, el(page, 'e2').id, el(page, 'e2').text, centerBox(-630, 0, 380, 50), {
    fontSize: TS.body30,
    color: C.orange,
  });
  text(slide, el(page, 'e3').id, el(page, 'e3').text, centerBox(-630, 200, 380, 50), {
    fontSize: TS.body28,
    color: C.orange,
  });
  text(slide, el(page, 'f1').id, el(page, 'f1').text, centerBox(-210, -200, 380, 90), {
    fontSize: TS.body26,
    color: C.navy,
  });
  text(slide, el(page, 'f2').id, el(page, 'f2').text, centerBox(-210, 0, 380, 90), {
    fontSize: TS.body26,
    color: C.navy,
  });
  text(slide, el(page, 'f3').id, el(page, 'f3').text, centerBox(-210, 200, 380, 90), {
    fontSize: TS.body26,
    color: C.navy,
  });
  text(slide, el(page, 'a1').id, el(page, 'a1').text, centerBox(210, 20, 380, 400), {
    fontSize: TS.body20,
    color: C.orange,
  });
  text(slide, el(page, 'c1').id, el(page, 'c1').text, centerBox(630, 20, 380, 320), {
    fontSize: TS.body22,
    color: C.navy,
  });
}

const builders = {
  cover: buildCover,
  'flu-context': buildFlu,
  'benefit-1': buildBenefit1,
  'benefit-2': buildBenefit2,
  'benefit-3': buildBenefit3,
  'feature-1': buildFeature1,
  'feature-2': buildFeature2,
  'feature-3': buildFeature3,
  'combo-1': buildCombo,
  'combo-2': buildCombo,
  summary: buildSummary,
};

const presentation = Presentation.create({slideSize: {width: W, height: H}});
const pages = model.pages.filter(p => p.pptx_slide !== false);
const pageIds = [];

for (const page of pages) {
  if (page.type === 'audience' || page.id === 'audience') {
    // 拆成两页：年龄门槛 → 三类人群（对齐参考视频 A1/A2）
    const s1 = presentation.slides.add();
    await buildAudienceAge(s1, page);
    notes(s1, {...page, id: 'audience_age', type: 'audience-age'});
    pageIds.push('audience_age');

    const s2 = presentation.slides.add();
    await buildAudiencePeople(s2, page);
    notes(s2, {...page, id: 'audience_people', type: 'audience-people'});
    pageIds.push('audience_people');
    continue;
  }

  const slide = presentation.slides.add();
  const builder = builders[page.type] ?? builders[page.id];
  if (!builder) {
    await bg(slide);
    text(slide, `editable:sufuda:${page.id}:title`, page.title ?? page.id, centerBox(0, 0, 800, 80), {
      fontSize: TS.chapter,
      color: C.navy,
    });
  } else {
    await builder(slide, page);
  }
  notes(slide, page);
  pageIds.push(page.id);
}

await fs.mkdir(path.dirname(outPath), {recursive: true});
if (qaDir) {
  await fs.mkdir(qaDir, {recursive: true});
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, '0')}`;
    const png = await presentation.export({slide, format: 'png', scale: 1});
    await fs.writeFile(
      path.join(qaDir, `${stem}.png`),
      new Uint8Array(await png.arrayBuffer()),
    );
    const layout = await slide.export({format: 'layout'});
    await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text());
  }
  const montage = await presentation.export({format: 'webp', montage: true, scale: 1});
  await fs.writeFile(
    path.join(qaDir, 'deck-montage.webp'),
    new Uint8Array(await montage.arrayBuffer()),
  );
  const inspection = await presentation.inspect({
    kind: 'slide,textbox,shape,notes',
    maxChars: 60000,
  });
  await fs.writeFile(path.join(qaDir, 'inspection.ndjson'), inspection.ndjson);
}
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outPath);

// artifact-tool 常丢 body 字体；写入 HarmonyOS Sans SC 到每个 run
const patchScript = path.join(__dirname, 'patch-pptx-font.py');
const patch = spawnSync('python3', [patchScript, outPath, FONT_FINAL], {
  encoding: 'utf8',
});
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
  style_pack_id: model.style_pack_id,
  font: FONT_FINAL,
  layout: 'video-design-coords-scaled',
  image_fit: 'native-aspect-contain-box',
  audience_split: true,
  font_patched: patch.status === 0,
  qa_dir: qaDir,
  qa_previews: qaDir ? presentation.slides.items.length : 0,
  qa_layouts: qaDir ? presentation.slides.items.length : 0,
};
const inspectPath = outPath + '.inspect.json';
await fs.writeFile(inspectPath, JSON.stringify(inspect, null, 2) + '\n');
if (reportPath !== inspectPath) {
  await fs.mkdir(path.dirname(reportPath), {recursive: true});
  await fs.writeFile(reportPath, JSON.stringify(inspect, null, 2) + '\n');
}
console.log(JSON.stringify(inspect, null, 2));
