/**
 * 从 content-model.json（+ 可选 editor patches snapshot）导出原生可编辑 PPTX。
 * 与视频共用内容模型；不承诺动画等价。
 *
 * Usage:
 *   node scripts/export-sufuda-pptx.mjs
 *   node scripts/export-sufuda-pptx.mjs /path/to/project-snapshot.json
 *   node scripts/export-sufuda-pptx.mjs --model /path/to/content-model.json --out /path/to/out.pptx
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {
  Presentation,
  PresentationFile,
} from '../../../../../poc/courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
// .../validation/courseware/sufuda-... → repo root is 5 levels up from scripts (scripts→gold→courseware→validation→production-library→repo)
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
    path.join(ROOT, 'out', '速福达_商品培训课件3_可编辑课件_v1.pptx'),
  ),
);
const assetsRoot = path.resolve(argValue('--assets', path.join(ROOT, 'public')));

const W = 1280;
const H = 720;
const SX = W / 1920;
const SY = H / 1080;
const FONT = 'PingFang SC';

const model = JSON.parse(await fs.readFile(modelPath, 'utf8'));
const patches = snapshotPath
  ? JSON.parse(await fs.readFile(snapshotPath, 'utf8')).patches ?? {}
  : {};

const C = model.tokens;
const assets = model.assets;

function px(x, y, w, h) {
  return {
    left: x * SX,
    top: y * SY,
    width: w * SX,
    height: h * SY,
  };
}

function centerBox(cx, cy, w, h) {
  return px(cx - w / 2 + 960, cy - h / 2 + 540, w, h);
}

async function loadAsset(assetKeyOrPath) {
  let rel = assets[assetKeyOrPath] ?? assetKeyOrPath;
  if (rel.startsWith('/assets/')) rel = rel.slice(1);
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
  const p = patches[elementId]?.src;
  if (p) return p;
  return fallbackAssetKey;
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
    fontFamily: FONT,
    fontSize: opts.fontSize ?? 22,
    bold: opts.bold ?? true,
    color: opts.color ?? C.ink ?? '#182a43',
    alignment: opts.align ?? 'center',
    verticalAlignment: opts.vAlign ?? 'middle',
  };
  return box;
}

async function image(slide, elementId, assetKey, position, alt = '') {
  const key = patchedSrc(elementId, assetKey);
  let blob = null;
  if (typeof key === 'string' && key.startsWith('assets/')) {
    const full = path.join(path.dirname(outPath), key);
    try {
      const buf = await fs.readFile(full);
      blob = new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
    } catch {
      blob = null;
    }
  } else {
    blob = await loadAsset(key);
  }
  if (!blob) {
    shape(slide, 'roundRect', position, C.row_bg ?? '#fff3e0', C.orange, elementId);
    text(slide, `${elementId}__slot`, '图片槽位', position, {
      fontSize: 16,
      color: C.muted,
    });
    return null;
  }
  return slide.images.add({
    blob,
    contentType: 'image/png',
    alt: alt || elementId,
    fit: 'contain',
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
  await image(slide, el.id, el.asset ?? 'logo', centerBox(790, -478, 300, 86), 'logo');
}

function chapterRibbon(slide, pageId, chapterText) {
  const el = model.pages.find(p => p.id === pageId)?.elements?.chapter;
  const id = el?.id ?? `editable:sufuda:${pageId}:chapter`;
  shape(slide, 'roundRect', centerBox(0, -458, 720, 90), C.orange, C.orange);
  text(slide, id, chapterText ?? el?.text ?? '', centerBox(0, -458, 680, 80), {
    fontSize: 28,
    color: C.white,
  });
}

function navPills(slide, page, active) {
  const items = page.nav ?? [];
  if (!items.length) return;
  const total = items.length;
  const widths = total === 2 ? [560, 640] : total === 3 ? [380, 420, 460] : items.map(() => 360);
  const gap = 24;
  const totalW = widths.reduce((a, b) => a + b, 0) + gap * (total - 1);
  let x = -totalW / 2;
  items.forEach((label, i) => {
    const w = widths[i] ?? 360;
    const on = i === (active ?? page.active_nav ?? 0);
    const role = `nav${i + 1}`;
    const el = page.elements[role];
    const id = el?.id ?? `editable:sufuda:${page.id}:${role}`;
    const cx = x + w / 2;
    shape(
      slide,
      'roundRect',
      centerBox(cx, -348, w, 64),
      on ? C.orange : C.gray,
      on ? C.orange : C.gray,
      id + '__pill',
    );
    shape(slide, 'ellipse', centerBox(cx - w / 2 + 30, -348, 46, 46), C.white, C.white);
    text(slide, id + '__n', String(i + 1), centerBox(cx - w / 2 + 30, -348, 40, 40), {
      fontSize: 16,
      color: on ? C.orange : C.muted,
    });
    text(slide, id, label, centerBox(cx + 12, -348, w - 80, 50), {
      fontSize: 16,
      color: C.white,
    });
    x += w + gap;
  });
}

function el(page, role) {
  return page.elements[role];
}

async function buildCover(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  text(slide, el(page, 'title').id, el(page, 'title').text, centerBox(0, -320, 1200, 90), {
    fontSize: 40,
    color: C.navy2,
  });
  shape(slide, 'roundRect', centerBox(0, -220, 780, 64), C.orange, C.orange);
  text(slide, el(page, 'tagline').id, el(page, 'tagline').text, centerBox(0, -220, 760, 56), {
    fontSize: 22,
    color: C.white,
  });
  const checks = ['check1', 'check2', 'check3'];
  checks.forEach((role, i) => {
    const y = -40 + i * 90;
    shape(slide, 'ellipse', centerBox(-750, y, 46, 46), C.orange, C.orange);
    text(slide, el(page, role).id + '__tick', '✓', centerBox(-750, y, 40, 40), {
      fontSize: 18,
      color: C.white,
    });
    text(slide, el(page, role).id, el(page, role).text, centerBox(-420, y, 520, 60), {
      fontSize: 22,
      color: C.ink,
      align: 'left',
    });
  });
  await image(slide, el(page, 'pack').id, el(page, 'pack').asset, centerBox(400, 90, 720, 500), 'pack');
  text(slide, el(page, 'pack_note').id, el(page, 'pack_note').text, centerBox(780, 490, 360, 28), {
    fontSize: 11,
    color: C.muted,
  });
}

async function buildFlu(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  const cards = [
    {x: -520, roles: ['card1_icon_a', 'card1_title', 'card1_icon_b', 'card1_body']},
    {x: 0, roles: ['card2_icon_a', 'card2_t1', 'card2_icon_b', 'card2_t2', 'card2_icon_c', 'card2_t3']},
    {x: 520, roles: ['card3_icon', 'card3_num', 'card3_body']},
  ];
  for (const card of cards) {
    shape(slide, 'roundRect', centerBox(card.x, -20, 400, 560), C.white, '#e8edf2');
  }
  await image(slide, el(page, 'card1_icon_a').id, 'icon365', centerBox(-520, -210, 160, 160));
  text(slide, el(page, 'card1_title').id, el(page, 'card1_title').text, centerBox(-520, -40, 340, 50), {
    fontSize: 22,
    color: C.navy,
  });
  await image(slide, el(page, 'card1_icon_b').id, 'iconTree', centerBox(-520, 100, 160, 160));
  text(slide, el(page, 'card1_body').id, el(page, 'card1_body').text, centerBox(-520, 250, 340, 80), {
    fontSize: 18,
    color: C.navy2,
  });

  await image(slide, el(page, 'card2_icon_a').id, 'iconVirus', centerBox(0, -220, 100, 100));
  text(slide, el(page, 'card2_t1').id, el(page, 'card2_t1').text, centerBox(0, -120, 320, 40), {
    fontSize: 22,
    color: C.navy,
  });
  await image(slide, el(page, 'card2_icon_b').id, 'iconLungs', centerBox(0, -20, 90, 90));
  text(slide, el(page, 'card2_t2').id, el(page, 'card2_t2').text, centerBox(0, 70, 320, 40), {
    fontSize: 22,
    color: C.navy,
  });
  await image(slide, el(page, 'card2_icon_c').id, 'iconWarn', centerBox(0, 160, 80, 80));
  text(slide, el(page, 'card2_t3').id, el(page, 'card2_t3').text, centerBox(0, 250, 320, 40), {
    fontSize: 22,
    color: C.navy,
  });

  await image(slide, el(page, 'card3_icon').id, 'iconChina', centerBox(520, -190, 150, 130));
  text(slide, el(page, 'card3_num').id, el(page, 'card3_num').text, centerBox(520, -20, 320, 70), {
    fontSize: 40,
    color: C.orange,
  });
  text(slide, el(page, 'card3_body').id, el(page, 'card3_body').text, centerBox(520, 100, 320, 90), {
    fontSize: 18,
    color: C.navy,
  });

  shape(slide, 'roundRect', centerBox(0, 400, 1000, 70), 'rgba(255,255,255,0.95)', '#e8edf2');
  text(slide, el(page, 'footer').id, el(page, 'footer').text, centerBox(0, 400, 960, 60), {
    fontSize: 20,
    color: C.navy,
  });
}

async function buildBenefit1(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  await image(slide, el(page, 'pack').id, 'packGroup', centerBox(0, 50, 560, 400));
  await image(slide, el(page, 'badge_jia').id, 'badgeJia', centerBox(-430, -20, 160, 160));
  text(slide, el(page, 'badge_jia_label').id, el(page, 'badge_jia_label').text, centerBox(-430, -20, 80, 80), {
    fontSize: 36,
    color: C.navy2,
  });
  await image(slide, el(page, 'badge_yi').id, 'badgeYi', centerBox(-220, 120, 140, 140));
  text(slide, el(page, 'badge_yi_label').id, el(page, 'badge_yi_label').text, centerBox(-220, 120, 70, 70), {
    fontSize: 32,
    color: C.orange,
  });
  await image(slide, el(page, 'bubble').id, 'bubbleSpeech', centerBox(430, -10, 340, 280));
  text(slide, el(page, 'bubble_text').id, el(page, 'bubble_text').text, centerBox(430, -10, 240, 160), {
    fontSize: 28,
    color: C.white,
  });
}

async function buildBenefit2(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  shape(slide, 'roundRect', centerBox(0, 40, 1600, 560), 'rgba(255,255,255,0.96)', '#e8edf2');
  shape(slide, 'roundRect', centerBox(-620, -80, 240, 70), C.orange, C.orange);
  text(slide, el(page, 'dose1').id, el(page, 'dose1').text, centerBox(-620, -80, 220, 60), {
    fontSize: 18,
    color: C.white,
  });
  shape(slide, 'roundRect', centerBox(-620, 20, 260, 70), C.orange, C.orange);
  text(slide, el(page, 'drug_a').id, el(page, 'drug_a').text, centerBox(-620, 20, 240, 60), {
    fontSize: 20,
    color: C.white,
  });
  shape(slide, 'roundRect', centerBox(-620, 140, 260, 70), C.orange2, C.orange2);
  text(slide, el(page, 'dose24').id, el(page, 'dose24').text, centerBox(-620, 140, 240, 60), {
    fontSize: 16,
    color: C.white,
  });
  await image(slide, el(page, 'cell').id, 'cell', centerBox(40, 40, 420, 300));
  text(slide, el(page, 'mech_left').id, el(page, 'mech_left').text, centerBox(40, -200, 480, 80), {
    fontSize: 18,
    color: C.orange,
  });
  shape(slide, 'roundRect', centerBox(560, 20, 260, 70), '#8e949c', '#8e949c');
  text(slide, el(page, 'drug_b').id, el(page, 'drug_b').text, centerBox(560, 20, 240, 60), {
    fontSize: 20,
    color: C.white,
  });
  text(slide, el(page, 'mech_right').id, el(page, 'mech_right').text, centerBox(560, 140, 300, 80), {
    fontSize: 16,
    color: C.muted,
  });
}

async function buildBenefit3(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  await image(slide, el(page, 'patient').id, 'patient', centerBox(-420, 40, 280, 440));
  await image(slide, el(page, 'family').id, 'family', centerBox(280, 20, 480, 480));
  text(slide, el(page, 'patient_label').id, el(page, 'patient_label').text, centerBox(-420, 340, 360, 50), {
    fontSize: 18,
    color: C.navy,
  });
  text(slide, el(page, 'family_label').id, el(page, 'family_label').text, centerBox(280, 340, 420, 50), {
    fontSize: 18,
    color: C.navy,
  });
}

async function buildFeature1(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  await image(slide, el(page, 'icon_baby').id, 'iconBaby', centerBox(-560, 0, 150, 150));
  text(slide, el(page, 'label_left').id, el(page, 'label_left').text, centerBox(-560, 140, 280, 50), {
    fontSize: 24,
    color: C.navy,
  });
  shape(slide, 'ellipse', centerBox(0, 30, 520, 520), C.white, C.orange2);
  await image(slide, el(page, 'pack').id, 'packGroup', centerBox(0, 30, 400, 300));
  await image(slide, el(page, 'icon_shield').id, 'iconShield', centerBox(560, 0, 140, 140));
  text(slide, el(page, 'label_right').id, el(page, 'label_right').text, centerBox(560, 140, 280, 50), {
    fontSize: 22,
    color: C.navy,
  });
}

async function buildFeature2(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  shape(slide, 'roundRect', centerBox(-500, 20, 360, 460), C.white, '#e8edf2');
  await image(slide, el(page, 'tablets').id, 'tablets', centerBox(-500, -40, 260, 260));
  text(slide, el(page, 'dose_20').id, el(page, 'dose_20').text, centerBox(-590, 160, 140, 70), {
    fontSize: 12,
    color: C.navy,
  });
  text(slide, el(page, 'dose_40').id, el(page, 'dose_40').text, centerBox(-410, 160, 140, 70), {
    fontSize: 12,
    color: C.navy,
  });
  shape(slide, 'roundRect', centerBox(-620, -210, 180, 80), C.orange, C.orange);
  text(slide, el(page, 'tab_bubble').id, el(page, 'tab_bubble').text, centerBox(-620, -210, 160, 70), {
    fontSize: 14,
    color: C.white,
  });
  shape(slide, 'ellipse', centerBox(0, 20, 380, 380), C.white, C.orange2);
  await image(slide, el(page, 'pack').id, 'packGroup', centerBox(0, 20, 300, 220));
  shape(slide, 'roundRect', centerBox(500, 20, 360, 460), C.white, '#e8edf2');
  await image(slide, el(page, 'granule').id, 'granule', centerBox(500, -30, 260, 260));
  text(slide, el(page, 'granule_label').id, el(page, 'granule_label').text, centerBox(500, 180, 300, 60), {
    fontSize: 14,
    color: C.navy,
  });
  shape(slide, 'roundRect', centerBox(620, -210, 200, 70), C.orange, C.orange);
  text(slide, el(page, 'strawberry').id, el(page, 'strawberry').text, centerBox(620, -210, 180, 60), {
    fontSize: 16,
    color: C.white,
  });
}

async function buildFeature3(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  const rows = [
    {role: 'row1', y: -170, w: 1400, icon: 'iconFlag'},
    {role: 'row2', y: 0, w: 640, icon: 'icon70', x: -360},
    {role: 'row3', y: 0, w: 640, icon: 'iconThumb', x: 360},
    {role: 'row4', y: 170, w: 920, icon: 'iconAward'},
  ];
  for (const row of rows) {
    const x = row.x ?? 0;
    shape(slide, 'roundRect', centerBox(x, row.y, row.w, 100), C.row_bg2, C.row_bg2);
    await image(
      slide,
      el(page, row.role === 'row1' ? 'icon_flag' : row.role === 'row2' ? 'icon_70' : row.role === 'row3' ? 'icon_thumb' : 'icon_award').id,
      row.icon,
      centerBox(x - row.w / 2 + 60, row.y, 64, 64),
    );
    text(slide, el(page, row.role).id, el(page, row.role).text, centerBox(x + 40, row.y, row.w - 160, 80), {
      fontSize: 18,
      color: C.navy,
      align: 'left',
    });
  }
}

async function buildAudience(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  text(slide, el(page, 'headline').id, el(page, 'headline').text, centerBox(0, -300, 1500, 50), {
    fontSize: 18,
    color: C.navy,
  });
  const cards = [
    {role: 'elder', x: -480, img: 'charElder', label: 'elder_label'},
    {role: 'child', x: 0, img: 'charChild', label: 'child_label'},
    {role: 'chronic', x: 480, img: 'charChronic', label: 'chronic_label'},
  ];
  for (const c of cards) {
    shape(slide, 'roundRect', centerBox(c.x, 60, 360, 460), C.white, '#e8edf2');
    await image(
      slide,
      el(page, `${c.role}_img`).id,
      c.img,
      centerBox(c.x, -20, 220, 300),
    );
    text(slide, el(page, c.label).id, el(page, c.label).text, centerBox(c.x, 200, 320, 50), {
      fontSize: 18,
      color: C.navy,
    });
  }
  shape(slide, 'roundRect', centerBox(320, 20, 420, 320), C.orange, C.orange);
  text(slide, el(page, 'age').id, el(page, 'age').text, centerBox(320, -40, 360, 80), {
    fontSize: 40,
    color: C.white,
  });
  text(slide, el(page, 'age_body').id, el(page, 'age_body').text, centerBox(320, 80, 340, 140), {
    fontSize: 14,
    color: C.white,
  });
}

async function buildCombo(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  chapterRibbon(slide, page.id, page.chapter);
  navPills(slide, page, page.active_nav);
  text(slide, el(page, 'note').id, el(page, 'note').text, centerBox(0, -200, 1300, 60), {
    fontSize: 20,
    color: C.navy,
  });
  shape(slide, 'roundRect', centerBox(0, 80, 1400, 400), 'rgba(255,255,255,0.96)', '#e8edf2');
  await image(slide, el(page, 'pack').id, 'packGroup', centerBox(-360, 80, 420, 300));
  text(slide, el(page, 'plus').id, '+', centerBox(0, 80, 80, 80), {
    fontSize: 48,
    color: C.orange,
  });
  await image(slide, el(page, 'other').id, el(page, 'other').asset, centerBox(360, 80, 320, 240));
}

async function buildSummary(slide, page) {
  await bg(slide);
  await logo(slide, page.id);
  await image(slide, el(page, 'icon_hand').id, 'iconHand', centerBox(-780, -430, 80, 80));
  text(slide, el(page, 'eyebrow').id, el(page, 'eyebrow').text, centerBox(-680, -430, 160, 40), {
    fontSize: 18,
    color: C.orange,
  });
  chapterRibbon(slide, page.id, page.chapter);
  shape(slide, 'rect', centerBox(0, -300, 1500, 60), C.orange, C.orange);
  ['col_h1', 'col_h2', 'col_h3', 'col_h4'].forEach((role, i) => {
    text(slide, el(page, role).id, el(page, role).text, centerBox(-630 + i * 420, -300, 360, 50), {
      fontSize: 20,
      color: C.white,
    });
  });
  shape(slide, 'roundRect', centerBox(0, 40, 1500, 540), 'rgba(255,255,255,0.96)', '#e8edf2');
  text(slide, el(page, 'e1').id, el(page, 'e1').text, centerBox(-630, -160, 340, 50), {
    fontSize: 16,
    color: C.orange,
  });
  text(slide, el(page, 'e2').id, el(page, 'e2').text, centerBox(-630, 0, 340, 50), {
    fontSize: 16,
    color: C.orange,
  });
  text(slide, el(page, 'e3').id, el(page, 'e3').text, centerBox(-630, 160, 340, 50), {
    fontSize: 15,
    color: C.orange,
  });
  text(slide, el(page, 'f1').id, el(page, 'f1').text, centerBox(-210, -160, 340, 80), {
    fontSize: 14,
    color: C.navy,
  });
  text(slide, el(page, 'f2').id, el(page, 'f2').text, centerBox(-210, 0, 340, 80), {
    fontSize: 14,
    color: C.navy,
  });
  text(slide, el(page, 'f3').id, el(page, 'f3').text, centerBox(-210, 160, 340, 80), {
    fontSize: 14,
    color: C.navy,
  });
  text(slide, el(page, 'a1').id, el(page, 'a1').text, centerBox(210, 20, 320, 360), {
    fontSize: 12,
    color: C.orange,
  });
  text(slide, el(page, 'c1').id, el(page, 'c1').text, centerBox(630, 20, 320, 280), {
    fontSize: 13,
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
  audience: buildAudience,
  'combo-1': buildCombo,
  'combo-2': buildCombo,
  summary: buildSummary,
};

const presentation = Presentation.create({slideSize: {width: W, height: H}});
const pages = model.pages.filter(p => p.pptx_slide !== false);

for (const page of pages) {
  const slide = presentation.slides.add();
  const builder = builders[page.type] ?? builders[page.id];
  if (!builder) {
    await bg(slide);
    text(slide, `editable:sufuda:${page.id}:title`, page.title ?? page.id, centerBox(0, 0, 800, 80), {
      fontSize: 28,
      color: C.navy,
    });
    continue;
  }
  await builder(slide, page);
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n- content-model: ${path.relative(REPO, modelPath)}\n- page: ${page.id} (${page.type})\n- style_pack: ${model.style_pack_id}\n- 包装/Logo 为业务授权槽位；未使用参考视频像素。`,
  );
  slide.speakerNotes.setVisible(false);
}

await fs.mkdir(path.dirname(outPath), {recursive: true});
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outPath);

const inspect = {
  ok: true,
  out: outPath,
  slides: pages.length,
  page_ids: pages.map(p => p.id),
  model: path.relative(REPO, modelPath),
  patches: Object.keys(patches).length,
  style_pack_id: model.style_pack_id,
};
const inspectPath = outPath + '.inspect.json';
await fs.writeFile(inspectPath, JSON.stringify(inspect, null, 2) + '\n');
console.log(JSON.stringify(inspect, null, 2));
