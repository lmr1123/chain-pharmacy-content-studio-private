import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

import {
  Presentation,
  PresentationFile,
} from '../../courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, '..');
const snapshotFile = path.resolve(process.argv[2] ?? '');

if (!process.argv[2]) throw new Error('Missing current-project snapshot.');

const exportDir = path.dirname(snapshotFile);
const snapshot = JSON.parse(await fs.readFile(snapshotFile, 'utf8'));
const patches = snapshot.patches ?? {};
const outputName = '风热证_当前作品_可编辑课件.pptx';
const outputFile = path.resolve(exportDir, outputName);

const W = 1280;
const H = 720;
const FONT = 'PingFang SC';
const COLORS = {
  background: '#06111D',
  panel: '#142838',
  panel2: '#1D3545',
  cyan: '#34E3E5',
  cyanSoft: '#A6F2EF',
  white: '#F7FAF8',
  muted: '#9CB3BA',
  yellow: '#F5D35C',
  magenta: '#C8447B',
  line: '#4BA8B0',
};

const presentation = Presentation.create({
  slideSize: {width: W, height: H},
});

function transform(key) {
  const patch = patches[key] ?? {};
  const value = patch.transform ?? patch;
  return {
    x: Number(value.x ?? 0) * (W / 1920),
    y: Number(value.y ?? 0) * (H / 1080),
    scale: Number(value.scale ?? 1),
    rotation: Number(value.rotation ?? 0),
    opacity: Number(value.opacity ?? 1),
  };
}

function patchedText(key, fallback) {
  return patches[key]?.text ?? fallback;
}

function patchedStyle(key, fallbackSize, fallbackFill = COLORS.white) {
  return {
    fontSize: Math.max(12, Number(patches[key]?.fontSize ?? fallbackSize)),
    color: patches[key]?.fill ?? fallbackFill,
  };
}

function applyPosition(position, key) {
  const value = transform(key);
  const centerX = position.left + position.width / 2 + value.x;
  const centerY = position.top + position.height / 2 + value.y;
  const width = position.width * value.scale;
  const height = position.height * value.scale;
  return {
    left: centerX - width / 2,
    top: centerY - height / 2,
    width,
    height,
  };
}

function addShape(slide, name, position, fill, line = 'none', radius = false) {
  return slide.shapes.add({
    geometry: radius ? 'roundRect' : 'rect',
    name,
    position,
    fill,
    line: {style: 'solid', fill: line, width: line === 'none' ? 0 : 1.5},
    ...(radius ? {borderRadius: 'rounded-xl'} : {}),
  });
}

function addText(
  slide,
  key,
  fallback,
  position,
  {
    fontSize = 24,
    color = COLORS.white,
    bold = false,
    align = 'left',
  } = {},
) {
  const patchTransform = transform(key);
  if (patchTransform.opacity <= 0.01) return null;
  const shape = addShape(
    slide,
    key,
    applyPosition(position, key),
    'none',
  );
  const style = patchedStyle(key, fontSize, color);
  shape.text = patchedText(key, fallback);
  shape.text.style = {
    fontFamily: FONT,
    fontSize: style.fontSize * patchTransform.scale,
    color: style.color,
    bold,
    alignment: align,
  };
  shape.rotation = patchTransform.rotation;
  return shape;
}

async function assetPath(key, fallbackPath) {
  const source = patches[key]?.src;
  if (typeof source === 'string' && source.startsWith('assets/')) {
    return path.resolve(exportDir, source);
  }
  return fallbackPath ? path.resolve(projectRoot, 'public', fallbackPath) : null;
}

async function addImage(slide, key, fallbackPath, position, alt) {
  const value = transform(key);
  if (value.opacity <= 0.01) return;
  const target = await assetPath(key, fallbackPath);
  if (!target) return;
  try {
    const bytes = await fs.readFile(target);
    slide.images.add({
      blob: bytes.buffer.slice(
        bytes.byteOffset,
        bytes.byteOffset + bytes.byteLength,
      ),
      contentType: target.endsWith('.jpg') ? 'image/jpeg' : 'image/png',
      alt,
      fit: 'contain',
      position: applyPosition(position, key),
      geometry: 'roundRect',
      borderRadius: 'rounded-lg',
      rotation: value.rotation,
    });
  } catch {
    addShape(slide, `${key}:missing`, position, COLORS.panel2, COLORS.line, true);
    addText(slide, `${key}:missing-label`, '图片位置', position, {
      fontSize: 18,
      color: COLORS.muted,
      align: 'center',
    });
  }
}

function addMaster(slide, chapter, page) {
  slide.background.fill = COLORS.background;
  addShape(slide, `master:top:${page}`, {left: 0, top: 0, width: W, height: 54}, '#0B1B28');
  addText(
    slide,
    `master:brand:${page}`,
    '连锁药店 · 营运培训',
    {left: 42, top: 13, width: 310, height: 30},
    {fontSize: 18, color: COLORS.white, bold: true},
  );
  addText(
    slide,
    `master:notice:${page}`,
    '内部学习资料 请勿外传',
    {left: 930, top: 14, width: 300, height: 28},
    {fontSize: 15, color: COLORS.muted, align: 'right'},
  );
  addShape(slide, `master:footer:${page}`, {left: 0, top: 678, width: W, height: 42}, '#0B1B28');
  addText(
    slide,
    `master:chapter:${page}`,
    chapter,
    {left: 72, top: 687, width: 300, height: 24},
    {fontSize: 15, color: COLORS.cyanSoft, bold: true},
  );
  addText(
    slide,
    `master:page:${page}`,
    String(page).padStart(2, '0'),
    {left: 1160, top: 687, width: 60, height: 24},
    {fontSize: 15, color: COLORS.muted, align: 'right'},
  );
}

function addTitle(slide, key, fallback) {
  addShape(slide, `${key}:dot-1`, {left: 382, top: 80, width: 13, height: 13}, COLORS.yellow, 'none', true);
  addShape(slide, `${key}:dot-2`, {left: 402, top: 69, width: 18, height: 18}, COLORS.magenta, 'none', true);
  addText(
    slide,
    key,
    fallback,
    {left: 420, top: 65, width: 650, height: 58},
    {fontSize: 38, color: COLORS.white, bold: true},
  );
}

function addBulletList(slide, name, items, position) {
  const rowHeight = position.height / items.length;
  items.forEach((item, index) => {
    const top = position.top + rowHeight * index;
    addShape(
      slide,
      `${name}:${index}:surface`,
      {left: position.left, top, width: position.width, height: rowHeight - 10},
      COLORS.panel,
      COLORS.line,
      true,
    );
    addText(
      slide,
      `${name}:${index}:text`,
      item,
      {left: position.left + 22, top: top + 16, width: position.width - 44, height: rowHeight - 38},
      {fontSize: 23, color: COLORS.white},
    );
  });
}

// 1. Intro
{
  const slide = presentation.slides.add();
  addMaster(slide, '基础认知', 1);
  addText(
    slide,
    'editable:intro:title:eyebrow',
    '中医基础知识',
    {left: 168, top: 190, width: 430, height: 46},
    {fontSize: 24, color: COLORS.cyanSoft, bold: true},
  );
  addText(
    slide,
    'editable:intro:title:main',
    '风热证',
    {left: 160, top: 238, width: 620, height: 130},
    {fontSize: 72, color: COLORS.white, bold: true},
  );
  addShape(slide, 'intro:accent', {left: 168, top: 391, width: 360, height: 5}, COLORS.cyan);
  addText(
    slide,
    'intro:subtitle',
    '营运培训 · 专业赋能',
    {left: 168, top: 418, width: 520, height: 44},
    {fontSize: 25, color: COLORS.muted},
  );
}

// 2. Basic understanding
{
  const slide = presentation.slides.add();
  addMaster(slide, '基础认知', 2);
  addTitle(slide, 'editable:character:title:text', '什么是风热证');
  addText(
    slide,
    'editable:character:text:mechanism-title',
    '风邪与热邪一起侵入身体',
    {left: 120, top: 180, width: 1040, height: 70},
    {fontSize: 38, color: COLORS.white, bold: true, align: 'center'},
  );
  ['风邪', '+', '热邪', '→', '风热证'].forEach((label, index) => {
    const left = 120 + index * 214;
    addShape(
      slide,
      `editable:character:equation:${index}:surface`,
      {left, top: 302, width: 170, height: 105},
      index === 4 ? '#174B56' : COLORS.panel,
      COLORS.line,
      true,
    );
    addText(
      slide,
      `editable:character:equation:${index}`,
      label,
      {left, top: 330, width: 170, height: 48},
      {fontSize: 28, color: index === 4 ? COLORS.cyan : COLORS.white, bold: true, align: 'center'},
    );
  });
  addText(
    slide,
    'character:takeaway',
    '常见表现：发热、口渴、咽痛、咳嗽痰黄、鼻涕黄稠、心烦',
    {left: 160, top: 486, width: 960, height: 74},
    {fontSize: 27, color: COLORS.cyanSoft, align: 'center'},
  );
}

// 3. Mechanism
{
  const slide = presentation.slides.add();
  addMaster(slide, '病因机理', 3);
  addTitle(slide, 'mechanism:title', '风热证怎么找上门');
  const steps = [
    ['风邪', '从外而入'],
    ['热邪', '与风相合'],
    ['体表受邪', '卫表失和'],
    ['肺气不顺', '出现咳嗽、咽痛等表现'],
  ];
  steps.forEach(([title, body], index) => {
    const left = 70 + index * 302;
    addShape(
      slide,
      `editable:mechanism:step:${index}:surface`,
      {left, top: 246, width: 246, height: 210},
      COLORS.panel,
      COLORS.line,
      true,
    );
    addText(
      slide,
      `editable:mechanism:step:${index}:title`,
      title,
      {left: left + 22, top: 282, width: 202, height: 48},
      {fontSize: 27, color: COLORS.cyan, bold: true, align: 'center'},
    );
    addText(
      slide,
      `editable:mechanism:step:${index}:body`,
      body,
      {left: left + 22, top: 346, width: 202, height: 76},
      {fontSize: 20, color: COLORS.white, align: 'center'},
    );
    if (index < steps.length - 1) {
      addText(
        slide,
        `mechanism:arrow:${index}`,
        '→',
        {left: left + 251, top: 320, width: 50, height: 56},
        {fontSize: 30, color: COLORS.yellow, bold: true, align: 'center'},
      );
    }
  });
}

// 4. Symptoms
{
  const slide = presentation.slides.add();
  addMaster(slide, '典型症状', 4);
  addTitle(slide, 'editable:symptoms:title', '风热证的典型症状');
  const groups = [
    {
      heading: '① 全身症状',
      summary: '发热、口渴、嘴巴干、心里烦躁',
      labels: ['发热', '口渴', '嘴巴干', '心里烦躁'],
      images: ['fever.png', 'thirst.png', 'dry-mouth.png', 'irritable.png'],
    },
    {
      heading: '② 呼吸道症状',
      summary: '喉咙肿痛、咳嗽、痰黄、鼻涕黄稠',
      labels: ['喉咙肿痛', '咳嗽', '痰黄', '鼻涕黄稠'],
      images: ['sore-throat.png', 'cough.png', 'yellow-phlegm.png', 'yellow-nasal.png'],
    },
    {
      heading: '③ 其他症状',
      summary: '舌头偏红、舌苔发黄、大便干结',
      labels: ['舌头红', '舌苔黄', '大便干结'],
      images: ['red-tongue.png', 'yellow-coat.png', 'dry-stool.png'],
    },
  ];
  for (const [groupIndex, group] of groups.entries()) {
    const top = 144 + groupIndex * 166;
    addShape(
      slide,
      `editable:symptoms:group:${groupIndex}:root`,
      {left: 54, top, width: 1172, height: 150},
      COLORS.panel,
      COLORS.line,
      true,
    );
    addText(
      slide,
      `editable:symptoms:group:${groupIndex}:heading`,
      group.heading,
      {left: 76, top: top + 20, width: 292, height: 38},
      {fontSize: 24, color: COLORS.white, bold: true},
    );
    addText(
      slide,
      `editable:symptoms:group:${groupIndex}:summary:0`,
      group.summary,
      {left: 76, top: top + 70, width: 340, height: 56},
      {fontSize: 19, color: COLORS.cyan},
    );
    for (const [itemIndex, label] of group.labels.entries()) {
      const left = 460 + itemIndex * 182;
      const key = `editable:symptoms:asset:${['①', '②', '③'][groupIndex]}-${itemIndex}`;
      await addImage(
        slide,
        key,
        `production-symptoms/${group.images[itemIndex]}`,
        {left, top: top + 10, width: 92, height: 92},
        label,
      );
      addText(
        slide,
        `editable:symptoms:item:${groupIndex}:${itemIndex}:label`,
        label,
        {left: left - 8, top: top + 105, width: 108, height: 30},
        {fontSize: 16, color: COLORS.white, align: 'center'},
      );
    }
  }
}

// 5. Treatment
{
  const slide = presentation.slides.add();
  addMaster(slide, '调理建议', 5);
  addTitle(slide, 'editable:treatment:title:core:text', '调理核心');
  addText(
    slide,
    'editable:treatment:core:title',
    '疏风清热',
    {left: 102, top: 164, width: 420, height: 70},
    {fontSize: 42, color: COLORS.cyan, bold: true},
  );
  addText(
    slide,
    'editable:treatment:core:body:0',
    '把身体里的风散出去，把热清掉',
    {left: 102, top: 240, width: 520, height: 54},
    {fontSize: 25, color: COLORS.white},
  );
  addText(
    slide,
    'editable:treatment:core:body:1',
    '让发热、咽痛、咳嗽等不适逐渐缓解',
    {left: 102, top: 300, width: 560, height: 54},
    {fontSize: 23, color: COLORS.cyanSoft},
  );
  const herbs = [
    ['桑叶', '散风热、润肺\n缓解咳嗽', 'mulberry-leaf-v1.png'],
    ['菊花', '散风热、清热解毒\n泡饮清润舒适', 'chrysanthemum-v1.png'],
    ['薄荷', '疏散风热、清头目\n缓解咽喉不适', 'mint-v1.png'],
  ];
  for (const [index, [name, body, image]] of herbs.entries()) {
    const left = 92 + index * 380;
    addShape(
      slide,
      `editable:treatment:herb-large:${index}:surface`,
      {left, top: 402, width: 332, height: 214},
      COLORS.panel,
      COLORS.line,
      true,
    );
    await addImage(
      slide,
      `editable:treatment:herb-large:${index}:image`,
      `treatment-assets/${image}`,
      {left: left + 20, top: 426, width: 120, height: 120},
      name,
    );
    addText(
      slide,
      `editable:treatment:herb-large:${index}:title`,
      name,
      {left: left + 158, top: 430, width: 150, height: 42},
      {fontSize: 25, color: COLORS.white, bold: true},
    );
    addText(
      slide,
      `editable:treatment:herb-large:${index}:body`,
      body,
      {left: left + 158, top: 484, width: 150, height: 92},
      {fontSize: 18, color: COLORS.cyanSoft},
    );
  }
}

// 6. Medication and advice
{
  const slide = presentation.slides.add();
  addMaster(slide, '调理建议', 6);
  addTitle(slide, 'editable:medication:title:药物调理:text', '药物调理与生活建议');
  const medicines = [
    ['银翘解毒颗粒', '用于风热感冒相关表现'],
    ['连花清瘟胶囊', '按审核资料与说明书使用'],
  ];
  medicines.forEach(([name, body], index) => {
    const left = 68 + index * 310;
    addShape(
      slide,
      `editable:medication:group:card-${index + 1}`,
      {left, top: 154, width: 278, height: 174},
      COLORS.panel,
      COLORS.line,
      true,
    );
    addText(
      slide,
      `editable:medication:card:${name}:title`,
      name,
      {left: left + 20, top: 184, width: 238, height: 42},
      {fontSize: 23, color: COLORS.white, bold: true, align: 'center'},
    );
    addText(
      slide,
      `editable:medication:card:${name}:note`,
      body,
      {left: left + 24, top: 246, width: 230, height: 52},
      {fontSize: 17, color: COLORS.cyanSoft, align: 'center'},
    );
  });
  addBulletList(
    slide,
    'medication:advice',
    [
      '保持通风：房间多开窗，保持空气流通',
      '多喝温水：少量多次补水',
      '饮食清淡：避免辛辣、油炸和燥热食物',
      '戒烟戒酒：暂时不碰温补燥热类食物',
    ],
    {left: 686, top: 154, width: 526, height: 452},
  );
  addText(
    slide,
    'medication:notice',
    '药品使用以公司审核资料、说明书及药师指导为准',
    {left: 68, top: 386, width: 588, height: 82},
    {fontSize: 22, color: COLORS.yellow, bold: true, align: 'center'},
  );
}

// 7. Summary
{
  const slide = presentation.slides.add();
  addMaster(slide, '重点总结', 7);
  addTitle(slide, 'editable:summary:title:风热证总结:text', '风热证总结');
  const items = [
    ['病因', '风 + 热一起入侵，肺气不顺'],
    ['症状', '发热口渴、喉咙痛、咳黄痰、流黄涕、心烦'],
    ['调理', '疏风清热，用桑叶、菊花、薄荷，清淡饮食多喝水'],
    ['禁忌', '辛辣刺激、烟酒、温补燥热食物'],
  ];
  items.forEach(([title, body], index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const left = 84 + col * 570;
    const top = 164 + row * 224;
    addShape(
      slide,
      `editable:summary:matrix:item:${index}:surface`,
      {left, top, width: 530, height: 188},
      COLORS.panel,
      COLORS.line,
      true,
    );
    addText(
      slide,
      `editable:summary:matrix:item:${index}:title`,
      title,
      {left: left + 28, top: top + 28, width: 118, height: 42},
      {fontSize: 26, color: COLORS.cyan, bold: true},
    );
    addText(
      slide,
      `editable:summary:matrix:item:${index}:body`,
      body,
      {left: left + 28, top: top + 86, width: 474, height: 76},
      {fontSize: 21, color: COLORS.white},
    );
  });
}

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputFile);
console.log(JSON.stringify({ok: true, output: outputName}));
