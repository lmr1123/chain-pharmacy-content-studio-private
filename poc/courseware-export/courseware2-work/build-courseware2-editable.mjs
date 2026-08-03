import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const currentFile = fileURLToPath(import.meta.url);
const workDir = path.dirname(currentFile);
const repoDir = path.resolve(workDir, "../../..");
const outputPptx = path.join(
  repoDir,
  "production-library",
  "templates",
  "settled",
  "disease-product-scenario-v1",
  "穿心莲内酯滴丸_商品培训课件2_可编辑重建版.pptx",
);
const qaDir = path.join(
  repoDir,
  "production-library/validation/courseware/disease-product-scenario-v1/qa-editable",
);
const sourceDir = path.join(workDir, "source-slides");
const cropDir = path.join(workDir, "reused-pdf-crops");
await fs.mkdir(path.dirname(outputPptx), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const W = 1280;
const H = 720;
const FONT = "PingFang SC";
const GREEN = "#009900";
const GREEN_2 = "#43A817";
const MINT = "#DDF7EA";
const PALE = "#EEF7EA";
const TEAL = "#09B88E";
const RED = "#E60012";
const PINK = "#CB69B4";
const CYAN = "#42B6CF";
const BLACK = "#111111";
const GRAY = "#303741";
const LIGHT_LINE = "#B8E0CF";
const WHITE = "#FFFFFF";

const presentation = Presentation.create({ slideSize: { width: W, height: H } });
const sourceCache = new Map();

async function sourceBytes(slideNumber) {
  if (!sourceCache.has(slideNumber)) {
    const sourceName = `slide-${String(slideNumber - 1).padStart(3, "0")}.png`;
    sourceCache.set(slideNumber, await fs.readFile(path.join(sourceDir, sourceName)));
  }
  return sourceCache.get(slideNumber);
}

function rect(slide, name, x, y, width, height, fill = WHITE, line = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  });
}

function ellipse(slide, name, x, y, width, height, fill = WHITE, line = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry: "ellipse",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  });
}

function text(slide, name, value, x, y, width, height, options = {}) {
  const {
    size = 20,
    color = BLACK,
    bold = false,
    align = "left",
    fill = "none",
    line = "none",
    lineWidth = 0,
    emphasis = [],
  } = options;
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  });
  shape.text = value;
  shape.text.style = {
    fontFamily: FONT,
    fontSize: size,
    color,
    bold,
    alignment: align,
  };
  for (const item of emphasis) {
    const range = shape.text.get(item.text);
    if (item.bold !== undefined) range.bold = item.bold;
    if (item.color) range.fill = item.color;
  }
  return shape;
}

function line(slide, name, x, y, width, height, color = GREEN, lineWidth = 2) {
  return rect(slide, name, x, y, width, height, color, color, lineWidth);
}

function addChrome(slide, number, title) {
  slide.background.fill = WHITE;
  rect(slide, "chrome-left-number", 28, 0, 76, 84, GREEN);
  text(slide, "chrome-page-number", number, 25, 17, 82, 47, {
    size: 30,
    color: WHITE,
    align: "center",
  });
  text(slide, "chrome-title", title, 114, 14, 900, 50, {
    size: 28,
    bold: true,
  });
  line(slide, "chrome-green-rule", 104, 70, 1140, 3, GREEN, 0);
  text(slide, "chrome-brand", "大参林 dashenlin", 1080, 18, 150, 40, {
    size: 15,
    color: GREEN_2,
    bold: true,
    align: "right",
  });
  text(slide, "chrome-internal-notice", "仅限于内部学习", 1075, 685, 170, 24, {
    size: 14,
    align: "right",
  });
}

function addNotes(slide, sourceSlide, reuseItems = []) {
  const items = reuseItems.length
    ? reuseItems.map((item) => `- ${item}`)
    : ["- No source-PDF image crop reused on this editable page."];
  slide.speakerNotes.textFrame.setText(
    [
      "[Sources]",
      "- User-provided internal PDF: /Users/liminrong/Downloads/商品培训课件2.pdf",
      `- Source slide: ${sourceSlide}`,
      ...items,
      "- Visible medical/product copy is transcribed from the supplied internal courseware and still requires the user's normal pharmacist/compliance review.",
      "[/Sources]",
    ].join("\n"),
  );
  slide.speakerNotes.setVisible(true);
}

async function addCrop(slide, name, sourceSlide, crop, frame, alt) {
  slide.images.add({
    blob: await sourceBytes(sourceSlide),
    contentType: "image/png",
    alt,
    fit: "cover",
    crop,
    position: frame,
  });
}

async function addLocalImage(slide, name, fileName, frame, alt, fit = "cover") {
  slide.images.add({
    blob: await fs.readFile(path.join(cropDir, fileName)),
    contentType: "image/png",
    alt,
    fit,
    position: frame,
  });
}

function card(slide, name, x, y, width, height, titleValue, bodyValue, options = {}) {
  const {
    titleColor = GREEN,
    fill = WHITE,
    border = LIGHT_LINE,
    titleSize = 23,
    bodySize = 20,
    bodyBold = false,
    emphasis = [],
  } = options;
  rect(slide, `${name}-surface`, x, y, width, height, fill, border, 1);
  rect(slide, `${name}-accent`, x, y, 6, height, GREEN);
  text(slide, `${name}-title`, titleValue, x + 18, y + 14, width - 32, 38, {
    size: titleSize,
    color: titleColor,
    bold: true,
  });
  line(slide, `${name}-divider`, x + 18, y + 58, width - 36, 1, "#CDE9DE", 0);
  text(slide, `${name}-body`, bodyValue, x + 18, y + 70, width - 36, height - 84, {
    size: bodySize,
    color: GRAY,
    bold: bodyBold,
    emphasis,
  });
}

function callout(slide, name, value, x, y, width, height, options = {}) {
  const { fill = GREEN, color = WHITE, size = 18, bold = true, emphasis = [] } = options;
  text(slide, name, value, x, y, width, height, {
    size,
    color,
    bold,
    fill,
    emphasis,
  });
}

function simpleCell(slide, name, value, x, y, width, height, options = {}) {
  const {
    fill = WHITE,
    color = BLACK,
    size = 16,
    bold = false,
    align = "center",
    lineColor = "#333333",
    emphasis = [],
  } = options;
  rect(slide, `${name}-surface`, x, y, width, height, fill, lineColor, 1);
  text(slide, `${name}-text`, value, x + 6, y + 6, width - 12, height - 12, {
    size,
    color,
    bold,
    align,
    emphasis,
  });
}

// 1. Locked company cover.
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  slide.images.add({
    blob: await sourceBytes(1),
    contentType: "image/png",
    alt: "公司锁定封面，来自源 PDF 第 1 张课件画面",
    fit: "contain",
    position: { left: 0, top: 0, width: W, height: H },
  });
  addNotes(slide, 1, ["Full-slide source PDF image reused because the company cover is locked."]);
}

// 2. Opening thesis.
{
  const slide = presentation.slides.add();
  addChrome(slide, "", "精准辨证是中医临床的基石");
  callout(
    slide,
    "opening-thesis",
    "辨证论治是中医的灵魂，而精准辨证则是临床疗效的根本保障。唯有在纷繁复杂的症状中\n抓住证候本质，才能实现理、法、方、药的一脉贯通。",
    90,
    112,
    1100,
    110,
    {
      size: 22,
      bold: false,
      emphasis: [
        { text: "辨证论治", bold: true, color: RED },
        { text: "精准辨证", bold: true, color: RED },
        { text: "理、法、方、药", bold: true, color: RED },
      ],
    },
  );
  card(slide, "opening-focus", 90, 238, 340, 250, "聚焦核心：风热证", "深入剖析风热证的核心临床表现，从发热、咽痛、舌象等维度，提炼其最具代表性的辨证要点。", { titleColor: GRAY, titleSize: 22, bodySize: 21, bodyBold: false, emphasis: [{ text: "发热、咽痛、舌象", bold: true }] });
  card(slide, "opening-compare", 470, 238, 340, 250, "关键鉴别：异于风寒", "对比风热与风寒证在寒热轻重、口渴与否、鼻涕性质的关键差异，厘清易混淆症状，避免辨证失误。", { titleColor: GRAY, titleSize: 22, bodySize: 21, bodyBold: false, emphasis: [{ text: "寒热轻重、口渴与否、鼻涕性质", bold: true }] });
  card(slide, "opening-apply", 850, 238, 340, 250, "知行合一：分型用药", "细化风热证的不同分型，结合经典方剂，讲解如何根据具体兼证灵活化裁，将辨证结果转化为精准用药方案。", { titleColor: GRAY, titleSize: 22, bodySize: 21, bodyBold: false, emphasis: [{ text: "分型", bold: true }, { text: "精准用药方案", bold: true }] });
  callout(slide, "opening-conclusion", "愿诸位练就一双辨证的“慧眼”，于细微处见真章，在临床中精准识证、果敢用药。", 90, 548, 1100, 60, {
    size: 20,
    bold: false,
    emphasis: [
      { text: "“慧眼”", bold: true },
      { text: "精准识证、果敢用药", bold: true },
    ],
  });
  addNotes(slide, 2);
}

// 3. Agenda.
{
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  await addLocalImage(slide, "agenda-building", "slide03-building.png", { left: 0, top: 0, width: 580, height: 720 }, "源 PDF 目录页中的大参林建筑图");
  text(slide, "agenda-title", "目 录", 625, 80, 400, 80, {
    size: 58,
    color: GREEN,
    bold: true,
  });
  line(slide, "agenda-rule", 625, 175, 520, 3, GREEN_2, 0);
  const agenda = [
    "一  疾病篇—风热证",
    "二  商品篇—穿心莲内酯滴丸的核心优势",
    "三  场景篇—什么时候推荐穿心莲内酯滴丸",
    "四  关怀篇—日常生活叮嘱",
    "五  权重篇—活动权重",
  ];
  agenda.forEach((item, index) => {
    text(slide, `agenda-item-${index + 1}`, item, 625, 220 + index * 70, 600, 48, {
      size: 24,
      color: "#6E7378",
      bold: true,
    });
  });
  text(slide, "agenda-internal-notice", "仅限于内部学习", 1050, 675, 170, 24, { size: 14, align: "right" });
  addNotes(slide, 3, ["PDF slide 3 left-side building photograph reused as an internal source crop."]);
}

// 4. Definition.
{
  const slide = presentation.slides.add();
  addChrome(slide, "1.1", "疾病篇——风热证的定义");
  card(
    slide,
    "definition",
    90,
    100,
    1100,
    180,
    "什么是风热证？",
    "指风热之邪侵袭人体肌表，导致卫气被遏、肺失宣肃所表现出的证候。通俗而言，即身体受到“热风”侵袭，引发发热、咽痛、口干等一系列“热”性症状，是中医外感表证中常见的证型之一。",
    {
      titleColor: GRAY,
      bodySize: 26,
      bodyBold: false,
      emphasis: [
        { text: "“热风”侵袭", bold: true },
        { text: "发热、咽痛、口干", bold: true },
      ],
    },
  );
  card(slide, "cause", 90, 300, 520, 280, "核心病因：内外合邪，热邪入侵", "外感风邪：多发于春季或气温骤升时节，风热之邪从口鼻、皮毛而入，侵犯肌表。\n\n内生积热：过食辛辣、油腻、温补之品，或情志不畅化火，致体内“火气”过旺。", {
    titleColor: GRAY,
    bodySize: 23,
    emphasis: [
      { text: "外感风邪：", bold: true },
      { text: "内生积热：", bold: true },
      { text: "辛辣、油腻、温补", bold: true },
    ],
  });
  card(slide, "pathogenesis", 650, 300, 540, 280, "关键病机：正邪交争，肺卫失和", "正邪相争：风热犯表，卫阳被遏，正邪交争于肌表则发热。\n\n津伤肺逆：热邪易灼伤津液，故见口干、口渴；肺失宣肃，气逆于上，则引发咳嗽、咽喉肿痛。", {
    titleColor: GRAY,
    bodySize: 23,
    emphasis: [
      { text: "正邪相争：", bold: true },
      { text: "津伤肺逆：", bold: true },
      { text: "口干、口渴", bold: true },
      { text: "咳嗽、咽喉肿痛", bold: true },
    ],
  });
  callout(slide, "definition-summary", "总结：风热证以“发热重、恶寒轻、咽痛、口渴、苔薄黄”为主要辨证要点。", 90, 600, 1100, 55, { size: 21 });
  addNotes(slide, 4);
}

// 5. Symptom gallery.
{
  const slide = presentation.slides.add();
  addChrome(slide, "1.2", "疾病篇——风热证的典型症状");
  const imageFrames = [
    { x: 70, fileName: "slide05-throat.png", alt: "咽喉红肿疼痛图片" },
    { x: 445, fileName: "slide05-nose.png", alt: "流黄鼻涕图片" },
    { x: 820, fileName: "slide05-sputum.png", alt: "黄色黏痰图片" },
  ];
  for (const [index, item] of imageFrames.entries()) {
    await addLocalImage(slide, `symptom-image-${index + 1}`, item.fileName, { left: item.x, top: 112, width: 320, height: 185 }, item.alt);
  }
  card(slide, "symptom-throat", 70, 308, 320, 190, "咽喉红肿疼痛", "最典型的特征之一，咽喉黏膜充血明显，吞咽时痛感加剧，是风热之邪侵犯肺卫的直接表现。", { titleColor: BLACK, titleSize: 20, bodySize: 18, bodyBold: false, emphasis: [{ text: "咽喉黏膜充血明显", bold: true }] });
  card(slide, "symptom-nose", 445, 308, 320, 190, "流黄稠涕，咳黄黏痰", "鼻腔与呼吸道分泌物颜色发黄且质地黏稠，是热邪煎灼津液所致，与风寒证清稀分泌物形成鲜明对比。", { titleColor: BLACK, titleSize: 20, bodySize: 18, bodyBold: false, emphasis: [{ text: "发黄且质地黏稠", bold: true }] });
  card(slide, "symptom-fever", 820, 308, 320, 190, "发热重，微恶风", "患者自觉身体发烫，体温较高，但怕冷感觉不明显，仅稍有怕风，是风热证在体温上的核心表现。", { titleColor: BLACK, titleSize: 20, bodySize: 18, bodyBold: false, emphasis: [{ text: "发烫，体温较高", bold: true }] });
  callout(slide, "symptom-thirst", "口干口渴，喜冷饮\n热邪耗伤津液，导致口渴，且偏好凉水。", 70, 520, 350, 92, {
    fill: GREEN,
    size: 18,
    bold: false,
    emphasis: [{ text: "口干口渴，喜冷饮", bold: true }],
  });
  callout(slide, "symptom-tongue", "舌尖红，苔薄黄\n舌尖红为热象；薄黄苔提示病邪尚在表浅。", 455, 520, 350, 92, {
    fill: GREEN,
    size: 18,
    bold: false,
    emphasis: [{ text: "舌尖红，苔薄黄", bold: true }],
  });
  await addLocalImage(slide, "symptom-tongue-image", "slide05-tongue.png", { left: 845, top: 505, width: 210, height: 120 }, "源 PDF 中的舌象图片");
  addNotes(slide, 5, [
    "Four medical symptom images are cropped from flattened PDF slide 5.",
    "These crops remain internal-source assets and should be replaced by approved high-resolution originals when available.",
  ]);
}

// 6. Wind-heat vs wind-cold.
{
  const slide = presentation.slides.add();
  addChrome(slide, "1.3", "疾病篇——风热证的鉴别");
  function comparisonPanel(x, titleValue, color, fill, leftBody, rightBody, bottomBody) {
    rect(slide, `${titleValue}-surface`, x, 105, 550, 360, WHITE, color, 2);
    rect(slide, `${titleValue}-header`, x, 105, 550, 68, fill);
    text(slide, `${titleValue}-title`, titleValue, x + 30, 120, 490, 44, { size: 27, color: GRAY, bold: true });
    text(slide, `${titleValue}-left`, leftBody, x + 22, 205, 240, 185, {
      size: 22,
      color: GRAY,
      emphasis: ["01 寒热汗出", "02 鼻痰色泽"].map((value) => ({ text: value, bold: true, color })),
    });
    line(slide, `${titleValue}-middle-rule`, x + 274, 205, 1, 185, "#C8DDE3", 0);
    text(slide, `${titleValue}-right`, rightBody, x + 295, 205, 230, 185, {
      size: 22,
      color: GRAY,
      emphasis: ["03 咽喉症状", titleValue.startsWith("风热") ? "04 口渴喜饮" : "04 口渴情况"].map((value) => ({ text: value, bold: true, color })),
    });
    text(slide, `${titleValue}-bottom`, bottomBody, x + 22, 390, 500, 65, {
      size: 22,
      color: GRAY,
      emphasis: [{ text: "05 舌脉特征", bold: true, color }],
    });
  }
  comparisonPanel(
    70,
    "风热证 · 热象显著",
    "#00B98F",
    "#D9F8EE",
    "01 寒热汗出\n发热重，恶寒轻；有汗出，体表疏松。\n\n02 鼻痰色泽\n流黄稠涕，咳痰黄黏，里热灼津。",
    "03 咽喉症状\n咽喉红肿疼痛，热邪上攻。\n\n04 口渴喜饮\n口干渴明显，偏好冷饮。",
    "05 舌脉特征  舌红、苔薄黄，脉浮数。",
  );
  comparisonPanel(
    660,
    "风寒证 · 寒象突出",
    "#2F8AFF",
    "#E8EEF6",
    "01 寒热汗出\n恶寒重，发热轻；无汗出，寒束肌表。\n\n02 鼻痰色泽\n流清稀涕，咳痰白稀，寒邪未化热。",
    "03 咽喉症状\n咽喉发痒，不红不痛，寒邪客于咽喉。\n\n04 口渴情况\n口不渴或喜热饮，体内无明显热邪。",
    "05 舌脉特征  舌淡、苔薄白，脉浮紧。",
  );
  callout(slide, "memory-1", "辨证核心口诀\n热重寒轻是风热，寒重热轻是风寒；有汗无汗要分清。", 70, 500, 350, 95, {
    fill: "#DBFAEF",
    color: GRAY,
    size: 18,
    bold: false,
    emphasis: [{ text: "辨证核心口诀", bold: true }],
  });
  callout(slide, "memory-2", "分泌物色诊口诀\n黄浊黄痰是风热，清涕白痰属风寒；红肿热痛辨咽喉。", 465, 500, 350, 95, {
    fill: "#DBFAEF",
    color: GRAY,
    size: 18,
    bold: false,
    emphasis: [{ text: "分泌物色诊口诀", bold: true }],
  });
  callout(slide, "memory-3", "津液喜恶口诀\n口渴喜凉为风热，口不渴属风寒；喜热饮者寒象真。", 860, 500, 350, 95, {
    fill: "#DBFAEF",
    color: GRAY,
    size: 18,
    bold: false,
    emphasis: [{ text: "津液喜恶口诀", bold: true }],
  });
  text(slide, "change-note", "病情演变：清涕转黄涕，应紧扣当前主症及时调整治法，不拘泥于初期寒象。", 70, 620, 1140, 42, { size: 20, color: BLACK, bold: true, fill: "#FFF200" });
  addNotes(slide, 6);
}

// 7. Treatment principles.
{
  const slide = presentation.slides.add();
  addChrome(slide, "1.4", "疾病篇——风热证的治疗：辨证用药总原则");
  card(slide, "principle-1", 70, 140, 350, 380, "01. 禁用辛温，勿助热", "核心原则：风热证为“阳热”之证，绝对禁用麻黄、桂枝等辛温发汗药。\n\n机理警示：温药入体如同“火上浇油”，会加重内热，灼伤津液，导致病情由表入里。", {
    bodySize: 23,
    bodyBold: false,
    emphasis: [
      { text: "核心原则：", bold: true },
      { text: "绝对禁用", bold: true, color: RED },
      { text: "机理警示：", bold: true },
      { text: "“火上浇油”", bold: true },
    ],
  });
  card(slide, "principle-2", 465, 140, 350, 380, "02. 分清主次，随证施方", "根据病程阶段与兼症针对性加减药物，不拘泥于一方一药。\n\n表热轻症单用辛凉解表；肺热偏重佐以清热化痰；咽喉肿痛则重加板蓝根、桔梗等解毒利咽之品。", {
    bodySize: 23,
    bodyBold: false,
    emphasis: [
      { text: "表热轻症", bold: true },
      { text: "肺热偏重", bold: true },
      { text: "咽喉肿痛", bold: true },
    ],
  });
  card(slide, "principle-3", 860, 140, 350, 380, "03. 兼顾兼证，不可偏颇", "临床多见风热夹湿等兼证，治疗时切忌只清热而不顾湿邪。\n\n在辛凉清热基础上，需酌情配伍藿香、佩兰、薏苡仁等化湿药物，使热得清解、湿得化除。", {
    bodySize: 23,
    bodyBold: false,
    emphasis: [
      { text: "风热夹湿", bold: true },
      { text: "藿香、佩兰、薏苡仁", bold: true },
    ],
  });
  callout(slide, "principle-summary", "总结：风热证治疗核心在于“辛凉解表、清热解毒”，同时严守禁忌，辨明主次兼证。", 70, 570, 1140, 58, {
    fill: "#E8F2F1",
    color: GRAY,
    size: 21,
    bold: false,
    emphasis: [
      { text: "总结：", bold: true },
      { text: "“辛凉解表、清热解毒”", bold: true },
    ],
  });
  addNotes(slide, 7);
}

// 8. Common subtypes.
{
  const slide = presentation.slides.add();
  addChrome(slide, "1.5", "疾病篇——风热证的证候细分（常见）");
  function subtypePanel(name, x, y, titleValue, clinical, treatment) {
    rect(slide, `${name}-surface`, x, y, 550, 230, WHITE, LIGHT_LINE, 1);
    rect(slide, `${name}-accent`, x, y, 6, 230, GREEN);
    text(slide, `${name}-title`, titleValue, x + 18, y + 10, 514, 44, { size: 25, color: GREEN, bold: true });
    line(slide, `${name}-rule`, x + 18, y + 56, 514, 1, "#CDE9DE", 0);
    text(slide, `${name}-clinical`, `临床表现：${clinical}`, x + 18, y + 76, 245, 135, {
      size: 23,
      color: GRAY,
      emphasis: [{ text: "临床表现：", bold: true }],
    });
    line(slide, `${name}-column-rule`, x + 274, y + 76, 1, 135, "#D5E5E7", 0);
    text(slide, `${name}-treatment`, `治则与方药：${treatment}`, x + 292, y + 76, 240, 135, {
      size: 23,
      color: GRAY,
      emphasis: [{ text: "治则与方药：", bold: true }],
    });
  }
  subtypePanel("subtype-1", 70, 110, "01. 风热感冒（表热轻症）", "发热、微恶风、咽痛、黄涕、薄黄苔、脉浮数。", "辛凉解表。方用银翘散、桑菊饮；中成药可选维C银翘片、银翘解毒片。");
  subtypePanel("subtype-2", 660, 110, "02. 风热犯肺（咳嗽为主）", "咳嗽频作、咳痰黏稠、咽痛、胸闷，或伴鼻流黄涕。", "疏风清热、宣肺止咳。方用桑菊饮；中成药如急支糖浆、川贝枇杷膏。");
  subtypePanel("subtype-3", 70, 380, "03. 风热上攻（头面热象偏重）", "头痛剧烈、面红目赤、咽喉肿痛、口舌生疮，或牙龈肿痛。", "疏风清热、清利头目；可选黄连上清片、板蓝根颗粒、穿心莲内酯滴丸。");
  subtypePanel("subtype-4", 660, 380, "04. 风热夹湿（夏季多见）", "发热、头昏沉、胸闷、肢体困重、舌苔黄腻，多在夏季暑湿时发生。", "疏风清热，兼化湿和中。方用新加香薷饮；中成药可选甘露消毒丹。");
  addNotes(slide, 8);
}

// 9. Product information.
{
  const slide = presentation.slides.add();
  addChrome(slide, "2.1", "商品篇——穿心莲内酯滴丸的产品信息");
  await addLocalImage(slide, "chuanxinlian-packshot", "slide09-packshot.png", { left: 50, top: 220, width: 250, height: 250 }, "穿心莲内酯滴丸包装，裁自源 PDF", "contain");
  rect(slide, "product-info-outline", 360, 135, 835, 440, WHITE, GREEN, 4);
  const rows = [
    ["【成  份】", "穿心莲内酯（纯度高达97%以上）；辅料为聚乙二醇、薄膜包衣预混剂。"],
    ["【性  状】", "本品为黄色的包衣滴丸，除去包衣后显类白色；味苦。"],
    ["【功能主治】", "清热解毒，抗菌消炎。用于上呼吸道感染风热证所致的咽痛。"],
    ["【规  格】", "每袋含穿心莲内酯0.15g。"],
    ["【用量用法】", "口服，一次1袋，一日3次。（建议首次服用两袋）"],
    ["【禁  忌】", "对本品过敏者禁用。"],
  ];
  rows.forEach(([label, value], index) => {
    text(slide, `product-info-label-${index + 1}`, label, 400, 170 + index * 62, 170, 38, { size: 22, bold: true, color: GRAY });
    text(slide, `product-info-value-${index + 1}`, value, 565, 170 + index * 62, 590, 48, { size: 21, color: index === 2 || index === 4 ? RED : GRAY, bold: index === 2 || index === 4 });
  });
  addNotes(slide, 9, [
    "Product packshot is cropped from flattened PDF slide 9.",
    "Replace with an authorized high-resolution packshot before production validation.",
  ]);
}

// 10. One mechanism, three advantages.
{
  const slide = presentation.slides.add();
  addChrome(slide, "2.2", "商品篇——穿心莲内酯滴丸的产品优势");
  ellipse(slide, "advantage-core", 535, 105, 210, 150, PINK);
  text(slide, "advantage-core-text", "一机理\n三优势", 555, 140, 170, 82, { size: 28, color: WHITE, bold: true, align: "center" });
  const nodes = [
    { x: 130, color: "#FF4D86", title: "机理", heading: "抑制核转录因子表达", body: "提高机体防御能力\n减轻细菌或病毒感染带来的不适症状" },
    { x: 400, color: "#45B4D4", title: "单", heading: "百分百纯植物提取", body: "单体制剂、植物化学药\n机理确切可控，降低联合用药风险" },
    { x: 680, color: "#45BEC9", title: "纯", heading: "穿心莲内酯纯度97%", body: "质量稳定，载药量高\n疗效好" },
    { x: 960, color: "#42C3A7", title: "快", heading: "滴丸剂型固体分散技术", body: "溶散时间短\n快速吸收，起效迅速" },
  ];
  line(slide, "advantage-axis", 220, 365, 830, 3, "#DDDDDD", 0);
  nodes.forEach((node, index) => {
    ellipse(slide, `advantage-node-${index + 1}`, node.x, 325, 72, 72, node.color);
    text(slide, `advantage-node-label-${index + 1}`, node.title, node.x, 343, 72, 38, { size: 22, color: WHITE, bold: true, align: "center" });
    text(slide, `advantage-heading-${index + 1}`, node.heading, node.x - 65, 425, 205, 58, { size: 19, color: PINK, bold: true, align: "center" });
    text(slide, `advantage-body-${index + 1}`, node.body, node.x - 65, 492, 205, 120, { size: 19, color: GRAY, align: "center" });
  });
  addNotes(slide, 10);
}

// 11. Core advantages summary.
{
  const slide = presentation.slides.add();
  addChrome(slide, "2.3", "商品篇——穿心莲内酯滴丸的核心优势总结");
  await addLocalImage(slide, "summary-packshot", "slide11-packshot.png", { left: 500, top: 210, width: 280, height: 260 }, "穿心莲内酯滴丸包装，裁自源 PDF", "contain");
  card(slide, "dosage-advantage", 60, 130, 400, 230, "剂型优势", "• 全国独家：全国唯一穿心莲内酯滴丸剂型\n• 起效更快：5–10分钟内全部崩解\n• 易携带：独立包装，方便携带", {
    titleSize: 26,
    bodySize: 22,
    bodyBold: false,
    emphasis: ["全国独家：", "起效更快：", "易携带："].map((value) => ({ text: value, bold: true })),
  });
  card(slide, "process-advantage", 60, 390, 440, 220, "工艺优势", "• 纯度高：穿心莲内酯纯度高达97%\n• 稳定性强：高速滴丸机，含量均匀度高\n• 安全保证：0糖0添加，纯中药制剂", {
    titleSize: 26,
    bodySize: 22,
    bodyBold: false,
    emphasis: ["纯度高：", "稳定性强：", "安全保证："].map((value) => ({ text: value, bold: true })),
  });
  card(slide, "formula-advantage", 820, 220, 390, 300, "组方优势", "• 植物单体制剂：经典老药，植物单体制剂\n• 功能全面：清热解毒＋抗菌消炎\n• 疗效显著：治疗感冒、流感、咽痛总有效率95%", {
    titleSize: 26,
    bodySize: 22,
    bodyBold: false,
    emphasis: ["植物单体制剂：", "功能全面：", "疗效显著："].map((value) => ({ text: value, bold: true })),
  });
  addNotes(slide, 11, [
    "Product packshot is cropped from flattened PDF slide 11.",
    "Replace with an authorized high-resolution packshot before production validation.",
  ]);
}

// 12. Audience scenarios.
{
  const slide = presentation.slides.add();
  addChrome(slide, "3.1", "场景篇——什么时候推荐穿心莲内酯滴丸");
  text(slide, "scenario-product-name", "＞ 穿心莲内酯滴丸", 70, 100, 430, 55, { size: 34, color: RED, bold: true });
  await addLocalImage(slide, "scenario-packshot", "slide12-packshot.png", { left: 70, top: 195, width: 260, height: 320 }, "穿心莲内酯滴丸包装，裁自源 PDF", "contain");
  await addLocalImage(slide, "scenario-child", "slide12-child.png", { left: 455, top: 140, width: 135, height: 165 }, "儿童插画，裁自源 PDF", "contain");
  await addLocalImage(slide, "scenario-adult", "slide12-adult.png", { left: 490, top: 315, width: 135, height: 160 }, "中青年插画，裁自源 PDF", "contain");
  await addLocalImage(slide, "scenario-senior", "slide12-senior.png", { left: 430, top: 505, width: 170, height: 150 }, "老年人物插画，裁自源 PDF", "contain");

  callout(slide, "audience-label-child", "儿童", 355, 225, 76, 48, { size: 25 });
  text(slide, "audience-arrow-child-1", "→", 600, 214, 78, 48, { size: 42, color: PINK, bold: true, align: "center" });
  text(slide, "audience-child-scene", "学校感冒交叉感染", 700, 215, 220, 48, { size: 23, color: BLACK, bold: true, align: "center" });
  text(slide, "audience-arrow-child-2", "→", 915, 214, 70, 48, { size: 42, color: PINK, bold: true, align: "center" });
  text(slide, "audience-child-need", "酸奶送服更安全", 995, 215, 210, 48, { size: 22, color: "#6E7378", bold: true });

  callout(slide, "audience-label-adult", "中青年", 395, 368, 104, 48, { size: 25 });
  text(slide, "audience-arrow-adult-1", "→", 625, 372, 78, 48, { size: 42, color: PINK, bold: true, align: "center" });
  const adultRows = [
    ["办公室白领", "办公室空调干燥易咽痛"],
    ["商旅人士", "出差出行劳累抵抗力低"],
    ["老师", "课堂授课易咽炎"],
    ["全职妈妈", "换季更新药箱"],
  ];
  adultRows.forEach(([person, need], index) => {
    const y = 320 + index * 43;
    text(slide, `audience-adult-person-${index + 1}`, person, 710, y, 155, 38, { size: 22, color: BLACK, bold: true, align: "center" });
    text(slide, `audience-arrow-adult-${index + 1}`, "→", 865, y - 3, 65, 42, { size: 38, color: PINK, bold: true, align: "center" });
    text(slide, `audience-adult-need-${index + 1}`, need, 935, y, 275, 38, { size: 21, color: "#777777", bold: true });
  });

  callout(slide, "audience-label-senior", "老年", 355, 550, 76, 48, { size: 25 });
  text(slide, "audience-arrow-senior-1", "→", 600, 552, 78, 48, { size: 42, color: PINK, bold: true, align: "center" });
  text(slide, "audience-senior-scene", "秋冬呼吸\n疾病高发", 705, 525, 160, 88, { size: 22, color: BLACK, bold: true, align: "center" });
  text(slide, "audience-arrow-senior-2", "→", 865, 552, 65, 42, { size: 38, color: PINK, bold: true, align: "center" });
  text(slide, "audience-senior-need", "冬日晨起锻炼易感冒\n北方暖气干燥早备药", 935, 525, 285, 88, { size: 21, color: "#777777", bold: true });
  addNotes(slide, 12, [
    "Product packshot is cropped from flattened PDF slide 12.",
    "Child, adult, and senior illustrations are cropped from flattened PDF slide 12 and reused as internal-source assets.",
    "Replace all four slide-12 crops with approved high-resolution originals when available.",
  ]);
}

// 13. Consultation framework.
{
  const slide = presentation.slides.add();
  addChrome(slide, "3.2", "场景篇——什么时候推荐穿心莲内酯滴丸");
  text(slide, "consultation-thesis", "实战销售话术：以“望闻问切”辨顾客，以专业方案做推荐", 70, 115, 1100, 48, { size: 25, color: GREEN, bold: true });
  line(slide, "consultation-rule", 90, 190, 1100, 2, GREEN, 0);
  const steps = [
    ["望 · 观气色辨需求", "观察顾客神态、面色与精神状态，初步判断体质倾向，找准沟通切入点，建立专业第一印象。"],
    ["闻 · 听诉求知痛点", "耐心倾听顾客描述身体不适与核心诉求，从话语中捕捉深层痛点，为后续辨证推荐提供依据。"],
    ["问 · 询细节定方案", "针对性询问饮食、作息、既往病史等细节，层层递进厘清“证型”，让方案更科学。"],
    ["切 · 据关键做推荐", "结合辨证结果，紧扣顾客核心需求，精准匹配产品与服务，用专业术语解读益处。"],
  ];
  steps.forEach(([heading, body], index) => {
    card(slide, `consultation-${index + 1}`, 70 + index * 290, 245, 260, 320, heading, body, { titleColor: GRAY, bodySize: 20 });
  });
  addNotes(slide, 13);
}

// 14. Scenario 1.
{
  const slide = presentation.slides.add();
  addChrome(slide, "3.3", "场景篇——什么时候推荐穿心莲内酯滴丸");
  text(slide, "scenario1-title", "场景1：顾客主诉“喉咙痛”", 80, 90, 600, 45, { size: 25, color: GREEN, bold: true });
  await addLocalImage(slide, "scenario1-photo", "slide14-throat-person.png", { left: 80, top: 175, width: 330, height: 340 }, "顾客咽痛人物照片，裁自源 PDF", "contain");
  card(slide, "scenario1-communication", 455, 175, 230, 340, "辨证沟通", "通过关键提问“是否觉得身上热”，快速判断顾客属于风热型咽喉肿痛，而非风寒。这是精准推荐用药的第一步。", {
    bodySize: 22,
    bodyBold: false,
    emphasis: [
      { text: "风热型咽喉肿痛", bold: true, color: GREEN },
      { text: "而非风寒", bold: true },
    ],
  });
  card(slide, "scenario1-product", 710, 175, 230, 340, "核心用药", "主推穿心莲内酯滴丸，其核心成分穿心莲内酯清热解毒、抗菌消炎。重点强调滴丸剂型吸收快、见效迅速。", {
    bodySize: 22,
    bodyBold: false,
    emphasis: [
      { text: "穿心莲内酯滴丸", bold: true },
      { text: "清热解毒、抗菌消炎", bold: true },
      { text: "吸收快、见效迅速", bold: true },
    ],
  });
  card(slide, "scenario1-service", 965, 175, 230, 340, "关联服务", "关联推荐熊胆薄荷含片，内服＋外用双管齐下。同时给予多饮温水、忌辛辣刺激等饮食建议。", {
    bodySize: 22,
    bodyBold: false,
    emphasis: [
      { text: "熊胆薄荷含片", bold: true },
      { text: "内服＋外用", bold: true },
    ],
  });
  callout(slide, "scenario1-summary", "服务要点：辨证精准是前提，剂型优势是卖点，关联用药是增值，健康叮嘱是保障。", 455, 555, 740, 55, { fill: MINT, color: GRAY, size: 20 });
  addNotes(slide, 14, [
    "Customer throat-pain photograph is cropped from flattened PDF slide 14.",
    "Replace with the approved original photograph if available.",
  ]);
}

// 15. Scenario 2.
{
  const slide = presentation.slides.add();
  addChrome(slide, "3.4", "场景篇——什么时候推荐穿心莲内酯滴丸");
  text(slide, "scenario2-title", "场景2：顾客主诉“感冒了，发烧，有黄痰”", 80, 90, 750, 45, { size: 25, color: GREEN, bold: true });
  card(slide, "scenario2-diagnosis", 80, 170, 340, 360, "01 症状辨析", "顾客表现为发烧38℃以上、自觉身热不恶寒、咳嗽伴黄痰。这是典型的风热感冒症状，核心病机为风热之邪犯表，肺气失和，体内有热毒积聚。", {
    bodySize: 23,
    bodyBold: false,
    emphasis: [
      { text: "发烧38℃以上", bold: true },
      { text: "风热感冒", bold: true, color: GREEN },
    ],
  });
  card(slide, "scenario2-core", 470, 170, 340, 360, "02 核心推荐方案", "推荐穿心莲内酯滴丸。它能直接清除体内热毒，从根源上解决发热、咽痛、咳黄痰等风热感冒症状；药力集中、起效快。", {
    bodySize: 23,
    bodyBold: false,
    emphasis: [
      { text: "穿心莲内酯滴丸", bold: true, color: GREEN },
      { text: "药力集中、起效快", bold: true },
    ],
  });
  card(slide, "scenario2-combo", 860, 170, 340, 360, "03 联合用药解惑", "若顾客家中有复方氨酚烷胺片，可说明：西药缓解咳嗽、流涕等症状是“治标”；穿心莲清除热毒是“治本”，二者联用。", {
    bodySize: 23,
    bodyBold: false,
    emphasis: [
      { text: "“治标”", bold: true, color: "#FF8A00" },
      { text: "“治本”", bold: true, color: GREEN },
    ],
  });
  callout(slide, "scenario2-talktrack", "关键话术：“您这是风热感冒，穿心莲内酯滴丸清除热毒是治本，复方氨酚烷胺片缓解症状是治标，一个治标一个治本，一起用效果更好。”", 80, 570, 1120, 65, { size: 20 });
  addNotes(slide, 15);
}

// 16. Daily care.
{
  const slide = presentation.slides.add();
  addChrome(slide, "4.1", "关怀篇——日常生活叮嘱");
  await addLocalImage(slide, "care-chrysanthemum", "slide16-chrysanthemum.png", { left: 70, top: 130, width: 245, height: 190 }, "菊花图片，裁自源 PDF", "contain");
  await addLocalImage(slide, "care-mungbean", "slide16-mungbean.png", { left: 335, top: 130, width: 245, height: 190 }, "绿豆汤图片，裁自源 PDF", "contain");
  callout(slide, "care-food-good", "✓ 饮食之宜 · 清热生津\n日常多喝水，可饮菊花茶、绿豆汤，适当食用梨、西瓜、苦瓜等寒凉性蔬果。", 70, 350, 245, 190, {
    fill: "#ECFFF4",
    color: GRAY,
    size: 17,
    bold: false,
    emphasis: [{ text: "✓ 饮食之宜 · 清热生津", bold: true }],
  });
  callout(slide, "care-food-bad", "✕ 饮食之忌 · 避热动火\n避免辛辣刺激、油腻煎炸食物，同时慎食羊肉、人参、桂圆等温补食材。", 335, 350, 245, 190, {
    fill: "#FFF1F1",
    color: GRAY,
    size: 17,
    bold: false,
    emphasis: [{ text: "✕ 饮食之忌 · 避热动火", bold: true }],
  });
  card(slide, "care-rest", 650, 120, 550, 145, "保证充足休息，养足精神", "建议保证7–8小时高质量睡眠，避免熬夜，让脏腑功能在夜间充分休养，促进津液恢复。", { bodySize: 21, emphasis: [{ text: "7–8小时高质量睡眠", bold: true }] });
  card(slide, "care-air", 650, 285, 550, 145, "保持室内通风，空气清新", "每日开窗通风2–3次，每次30分钟。新鲜空气有助于驱散室内浊气，保持呼吸道通畅。", { bodySize: 21, emphasis: [{ text: "2–3次，每次30分钟", bold: true }] });
  card(slide, "care-voice", 650, 450, 550, 145, "减少过度用嗓，静养咽喉", "尽量少说话，避免大声喊叫或长时间交谈，让咽喉、声带充分休息，减少外界刺激。", { bodySize: 21, emphasis: [{ text: "尽量少说话", bold: true }] });
  addNotes(slide, 16, [
    "Chrysanthemum and mung-bean soup images are cropped from flattened PDF slide 16.",
    "Replace with approved high-resolution originals if available.",
  ]);
}

// 17. Weighted product detail.
{
  const slide = presentation.slides.add();
  addChrome(slide, "5.1", "权重篇——广誉远安宫牛黄丸");
  await addLocalImage(slide, "angong-guangyuyuan", "slide17-product.png", { left: 45, top: 120, width: 465, height: 285 }, "广誉远安宫牛黄丸包装与商品图，裁自源 PDF", "contain");
  simpleCell(slide, "weighted-code-h", "编码", 45, 425, 90, 48, { fill: "#F8F8F8", bold: true });
  simpleCell(slide, "weighted-priority-h", "主推", 135, 425, 90, 48, { fill: "#F8F8F8", bold: true });
  simpleCell(slide, "weighted-spec-h", "规格", 225, 425, 160, 48, { fill: "#F8F8F8", bold: true });
  simpleCell(slide, "weighted-price-h", "零售价", 385, 425, 125, 48, { fill: "#F8F8F8", bold: true });
  simpleCell(slide, "weighted-code", "2205770", 45, 473, 90, 62, { size: 17 });
  simpleCell(slide, "weighted-priority", "A", 135, 473, 90, 62, { size: 19 });
  simpleCell(slide, "weighted-spec", "3克/丸\n（双天然）", 225, 473, 160, 62, { size: 16 });
  simpleCell(slide, "weighted-price", "880", 385, 473, 125, 62, { size: 19 });
  callout(slide, "weighted-slogan", "一句话卖点（员工宣传语）：\n安宫鼻祖，胆红素含量高于同品", 45, 555, 465, 75, { fill: WHITE, color: RED, size: 17 });
  card(slide, "weighted-selling-points", 550, 100, 660, 175, "一、核心卖点", "广誉远安宫被誉为安宫鼻祖。广誉远是较早规模化炮制安宫牛黄丸的厂家，早在光绪11年（1885年）开始规模化炮制；2014年获得“国家级非物质文化遗产”荣誉。", { titleColor: RED, titleSize: 25, bodySize: 18 });
  const tx = 585;
  const ty = 295;
  simpleCell(slide, "bilirubin-h1", "品种", tx, ty, 260, 44, { fill: GREEN_2, color: WHITE, bold: true });
  simpleCell(slide, "bilirubin-h2", "牛黄", tx + 260, ty, 120, 44, { fill: GREEN_2, color: WHITE, bold: true });
  simpleCell(slide, "bilirubin-h3", "胆红素含量", tx + 380, ty, 210, 44, { fill: GREEN_2, color: WHITE, bold: true });
  [["安宫牛黄丸（广誉远）", "天然", "46.6mg/丸"], ["北京同仁堂安宫", "天然", "40.1mg/丸"], ["安宫国家标准", "天然", "≥18.5mg/丸"]].forEach((row, index) => {
    const y = ty + 44 + index * 38;
    simpleCell(slide, `bilirubin-${index + 1}-1`, row[0], tx, y, 260, 38, { size: 16, color: index === 0 ? RED : BLACK, bold: index === 0 });
    simpleCell(slide, `bilirubin-${index + 1}-2`, row[1], tx + 260, y, 120, 38, { size: 16, color: index === 0 ? RED : BLACK, bold: index === 0 });
    simpleCell(slide, `bilirubin-${index + 1}-3`, row[2], tx + 380, y, 210, 38, { size: 16, color: index === 0 ? RED : BLACK, bold: index === 0 });
  });
  text(slide, "weighted-indications", "二、适应症：\n1. 中风或脑梗塞后遗症患者；2. 癫痫、惊厥、昏迷患者；3. 心血管疾病患者；4. 神经衰弱或失眠患者；5. 儿童高热惊厥；6. 严重感染性疾病伴高热神昏者。", 550, 470, 660, 160, {
    size: 18,
    color: GRAY,
    emphasis: [{ text: "二、适应症：", bold: true, color: RED }],
  });
  addNotes(slide, 17, [
    "The product presentation crop is reused from flattened PDF slide 17.",
    "All product data and claims are transcribed from the supplied internal courseware and require the normal internal review.",
  ]);
}

// 18. Weighted product comparison.
{
  const slide = presentation.slides.add();
  addChrome(slide, "5.2", "权重篇——白云山安宫＋宏济堂安宫");
  const x = 40;
  const y = 100;
  const widths = [150, 455, 585];
  simpleCell(slide, "compare-dim", "对比维度", x, y, widths[0], 66, { fill: "#3B8E25", color: WHITE, bold: true, size: 18 });
  simpleCell(slide, "compare-product-a", "安宫牛黄丸（白云山中一）\n8202533（人工体培）", x + widths[0], y, widths[1], 66, { fill: "#3B8E25", color: WHITE, bold: true, size: 17 });
  simpleCell(slide, "compare-product-b", "安宫牛黄丸（宏济堂）1185781（单天然）、\n1185783（人工体培）2373089（单天然包金衣）", x + widths[0] + widths[1], y, widths[2], 66, { fill: "#3B8E25", color: WHITE, bold: true, size: 16 });
  simpleCell(slide, "compare-image-label", "产品图片", x, y + 66, widths[0], 100, { bold: true });
  await addLocalImage(slide, "compare-pack-a", "slide18-product-a.png", { left: x + widths[0] + 85, top: y + 78, width: 260, height: 75 }, "白云山中一安宫产品图，裁自源 PDF", "contain");
  await addLocalImage(slide, "compare-pack-b", "slide18-product-b.png", { left: x + widths[0] + widths[1] + 45, top: y + 78, width: 485, height: 75 }, "宏济堂安宫产品图，裁自源 PDF", "contain");
  simpleCell(slide, "compare-selling-label", "核心卖点", x, y + 166, widths[0], 170, { fill: "#C7E7B7", bold: true, size: 18 });
  simpleCell(slide, "compare-selling-a", "1. 药材道地：胆红素含量是国家标准2倍；\n2. 古法手工：166年老手艺纯手工制丸；\n3. 广药白云山品牌，质量保证。", x + widths[0], y + 166, widths[1], 170, {
    fill: "#C7E7B7",
    size: 21,
    align: "left",
    emphasis: ["药材道地：", "古法手工：", "广药白云山品牌"].map((value) => ({ text: value, bold: true })),
  });
  simpleCell(slide, "compare-selling-b", "1. 系出名门，与北京同仁同宗同源，百年老号；\n2. 道地选材，自研国家一类新药麝香酮，急救效果更快更安全；\n3. 优质优价，性价比高。", x + widths[0] + widths[1], y + 166, widths[2], 170, {
    fill: "#C7E7B7",
    size: 21,
    align: "left",
    emphasis: ["系出名门", "道地选材", "优质优价"].map((value) => ({ text: value, bold: true })),
  });
  simpleCell(slide, "compare-audience-label", "适宜人群", x, y + 336, widths[0], 85, { bold: true, size: 18 });
  simpleCell(slide, "compare-audience", "1. 高血压、中风病史等心脑血管高风险人群家庭备用；\n2. 用于中风（热闭证）及高热神昏的急救。", x + widths[0], y + 336, widths[1] + widths[2], 85, { size: 19, align: "left" });
  simpleCell(slide, "compare-combo-label", "联合用药", x, y + 421, widths[0], 150, { fill: "#C7E7B7", bold: true, size: 18 });
  simpleCell(slide, "compare-combo", "1. 针对三高人群：按内部审核话术说明节气前备用逻辑；\n2. 针对急救：出现疑似急症应立即呼叫急救并遵循专业人员指导；\n3. 小儿高热：必须严格按内部审核和专业人员指导使用。\n严格辨证：仅用于“热闭”，绝对禁用于“寒闭”和“脱证”。", x + widths[0], y + 421, widths[1] + widths[2], 150, { fill: "#C7E7B7", color: RED, size: 18, align: "left" });
  addNotes(slide, 18, [
    "Product images are cropped from flattened PDF slide 18.",
    "The editable wording keeps the source structure; high-risk usage wording must be confirmed by the user's pharmacist/compliance team before production use.",
  ]);
}

for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(qaDir, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text());
}

const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(qaDir, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,image,table,notes,layout",
  maxChars: 200000,
});
await fs.writeFile(path.join(qaDir, "inspection.ndjson"), inspection.ndjson);
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPptx);
console.log(outputPptx);
