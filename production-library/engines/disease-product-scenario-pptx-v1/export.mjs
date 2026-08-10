#!/usr/bin/env node
/**
 * disease-product-scenario-pptx-v1
 *
 * A data-driven, editable PPTX renderer for the approved disease → product →
 * scenario courseware framework.  Domain copy and raster assets are accepted
 * only through --data; the engine contains layout logic, not a baked theme.
 *
 * Required:
 *   --data <script.json>  --out <deck.pptx>  --qa <qa-directory>
 * Optional:
 *   --style <tokens.json> --report <report.json>
 */
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const ENGINE_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_DIR = path.resolve(ENGINE_DIR, "../../..");
const DEFAULT_STYLE = path.join(
  REPO_DIR,
  "production-library/styles/dashenlin-courseware-green-v1/tokens.json",
);
const ARTIFACT_TOOL = path.join(
  REPO_DIR,
  "production-library/engines/courseware-pptx-v1/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs",
);
const FONT_PATCH = path.join(
  REPO_DIR,
  "production-library/engines/courseware-pptx-v1/patch-pptx-font.py",
);

const GOLD_THEME_ID = "theme.product.andrographolide-drop-pills";
const GOLD_FORBIDDEN = [
  "穿心莲",
  "内酯滴丸",
  "风热证",
  "复方氨酚烷胺片",
  "安宫牛黄丸",
  "熊胆薄荷含片",
  "97%",
  "95%",
  "5–10分钟",
  "5-10分钟",
  "38℃",
];

function fail(message, code = 2) {
  console.error(`ERROR: ${message}`);
  process.exit(code);
}

function cliValue(flag) {
  const index = process.argv.indexOf(flag);
  if (index < 0) return null;
  const value = process.argv[index + 1];
  if (!value || value.startsWith("--")) fail(`${flag} requires a value`);
  return path.resolve(value);
}

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log(`disease-product-scenario-pptx-v1

Required:
  --data <script.json>  structured theme content and asset paths
  --out  <deck.pptx>    editable PowerPoint output
  --qa   <directory>    rendered slides, layouts, montage, inspection

Optional:
  --style  <tokens.json>  default: dashenlin-courseware-green-v1
  --report <report.json>  default: <qa>/generate-report.json
`);
  process.exit(0);
}

const dataPath = cliValue("--data");
const outPath = cliValue("--out");
const qaDir = cliValue("--qa");
const stylePath = cliValue("--style") ?? DEFAULT_STYLE;
if (!dataPath) fail("--data is required");
if (!outPath) fail("--out is required");
if (!qaDir) fail("--qa is required");
const reportPath = cliValue("--report") ?? path.join(qaDir, "generate-report.json");

const dataBytes = await fs.readFile(dataPath).catch((error) =>
  fail(`cannot read data file ${dataPath}: ${error.message}`),
);
const styleBytes = await fs.readFile(stylePath).catch((error) =>
  fail(`cannot read style file ${stylePath}: ${error.message}`),
);
let data;
let style;
try {
  data = JSON.parse(dataBytes.toString("utf8"));
} catch (error) {
  fail(`invalid JSON in ${dataPath}: ${error.message}`);
}
try {
  style = JSON.parse(styleBytes.toString("utf8"));
} catch (error) {
  fail(`invalid JSON in ${stylePath}: ${error.message}`);
}

function at(object, dottedPath) {
  return dottedPath.split(".").reduce((current, key) => current?.[key], object);
}

function requireString(dottedPath) {
  const value = at(data, dottedPath);
  if (typeof value !== "string" || !value.trim()) {
    fail(`data.${dottedPath} must be a non-empty string`);
  }
  return value.trim();
}

function requireArray(dottedPath, { min = 1, max = Infinity } = {}) {
  const value = at(data, dottedPath);
  if (!Array.isArray(value) || value.length < min || value.length > max) {
    fail(`data.${dottedPath} must contain ${min}..${max === Infinity ? "∞" : max} items`);
  }
  return value;
}

function requireObject(dottedPath) {
  const value = at(data, dottedPath);
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    fail(`data.${dottedPath} must be an object`);
  }
  return value;
}

if (data.schema_version !== "disease-product-scenario-script/v1") {
  fail('data.schema_version must equal "disease-product-scenario-script/v1"');
}
requireObject("meta");
requireString("meta.theme_id");
requireString("meta.organization");
requireString("meta.brand_label");
requireString("meta.internal_notice");
requireObject("pages");
requireObject("disease");
requireObject("product");
requireObject("weighted");
requireArray("agenda", { min: 3, max: 6 });
requireArray("disease.symptoms", { min: 3, max: 4 });
requireArray("disease.comparison.rows", { min: 2, max: 5 });
requireArray("disease.treatment_principles", { min: 3, max: 6 });
requireArray("disease.subtypes", { min: 2, max: 4 });
requireArray("product.information", { min: 4, max: 6 });
requireArray("product.advantages", { min: 3, max: 4 });
requireArray("product.summary.groups", { min: 2, max: 3 });
requireArray("product.audience", { min: 3, max: 3 });
requireArray("product.consultation", { min: 3, max: 4 });
requireArray("product.scenarios", { min: 1, max: 4 });
requireArray("product.daily_care", { min: 3, max: 5 });
requireArray("weighted.items", { min: 1, max: 3 });
requireArray("weighted.comparison.products", { min: 2, max: 3 });
requireArray("weighted.comparison.rows", { min: 2, max: 5 });

const isAuthorizedGold = data.meta.gold_sample === true && data.meta.theme_id === GOLD_THEME_ID;
const serializedData = JSON.stringify(data);
const inputForbiddenHits = isAuthorizedGold
  ? []
  : GOLD_FORBIDDEN.filter((token) => serializedData.includes(token));
if (inputForbiddenHits.length) {
  fail(`non-gold input contains settled gold tokens: ${inputForbiddenHits.join(", ")}`, 3);
}

const dataDir = path.dirname(dataPath);
const assetRecords = [];
function resolveAsset(relativeOrAbsolute, owner) {
  if (typeof relativeOrAbsolute !== "string" || !relativeOrAbsolute.trim()) return null;
  const resolved = path.isAbsolute(relativeOrAbsolute)
    ? relativeOrAbsolute
    : path.resolve(dataDir, relativeOrAbsolute);
  assetRecords.push({ owner, input: relativeOrAbsolute, resolved });
  return resolved;
}

function findAssetRefs(value, owner = "data", records = []) {
  if (!value || typeof value !== "object") return records;
  if (Array.isArray(value)) {
    value.forEach((item, index) => findAssetRefs(item, `${owner}[${index}]`, records));
    return records;
  }
  for (const [key, child] of Object.entries(value)) {
    if (key === "image" && typeof child === "string" && child.trim()) {
      records.push({ owner: `${owner}.${key}`, resolved: resolveAsset(child, `${owner}.${key}`) });
    } else {
      findAssetRefs(child, `${owner}.${key}`, records);
    }
  }
  return records;
}

const discoveredAssets = findAssetRefs(data);
for (const record of discoveredAssets) {
  await fs.access(record.resolved).catch(() => fail(`missing input image ${record.owner}: ${record.resolved}`));
}

const artifactModule = await fs.access(ARTIFACT_TOOL)
  .then(() => import(pathToFileURL(ARTIFACT_TOOL).href))
  .catch((error) => fail(`cannot load @oai/artifact-tool: ${error.message}`));
const { Presentation, PresentationFile } = artifactModule;

const W = style.canvas?.width_px ?? 1280;
const H = style.canvas?.height_px ?? 720;
const FONT = style.font_family ?? "Microsoft YaHei";
const C = {
  primary: style.colors?.primary ?? "#009900",
  deep: style.colors?.primary_deep ?? "#066A2F",
  secondary: style.colors?.secondary ?? "#45A817",
  mint: style.colors?.mint ?? "#E9F7EE",
  pale: style.colors?.pale ?? "#F4FAF5",
  ink: style.colors?.ink ?? "#1F2A24",
  muted: style.colors?.muted ?? "#5A6B61",
  line: style.colors?.line ?? "#D9E9DF",
  red: style.colors?.red ?? "#E60012",
  white: style.colors?.white ?? "#FFFFFF",
  teal: style.colors?.cover_teal ?? "#006D58",
  blue: style.colors?.cover_blue ?? "#176A91",
};

const presentation = Presentation.create({ slideSize: { width: W, height: H } });
const slideRecords = [];

function shape(slide, name, geometry, left, top, width, height, options = {}) {
  return slide.shapes.add({
    geometry,
    name,
    position: { left, top, width, height },
    fill: options.fill ?? "none",
    line: {
      style: "solid",
      fill: options.line ?? "none",
      width: options.lineWidth ?? 0,
    },
    ...(geometry === "roundRect" ? { borderRadius: options.radius ?? 10 } : {}),
    ...(options.shadow ? { shadow: options.shadow } : {}),
  });
}

function rect(slide, name, left, top, width, height, fill = C.white, options = {}) {
  return shape(
    slide,
    name,
    options.radius ? "roundRect" : "rect",
    left,
    top,
    width,
    height,
    { ...options, fill },
  );
}

function ellipse(slide, name, left, top, width, height, fill, options = {}) {
  return shape(slide, name, "ellipse", left, top, width, height, { ...options, fill });
}

function text(slide, name, value, left, top, width, height, options = {}) {
  const box = shape(
    slide,
    name,
    options.radius ? "roundRect" : "textbox",
    left,
    top,
    width,
    height,
    {
      fill: options.fill ?? "none",
      line: options.line ?? "none",
      lineWidth: options.lineWidth ?? 0,
      radius: options.radius,
    },
  );
  box.text = String(value ?? "");
  box.text.style = {
    fontFamily: FONT,
    fontSize: options.size ?? 20,
    color: options.color ?? C.ink,
    bold: options.bold ?? false,
    alignment: options.align ?? "left",
    ...(options.vAlign ? { verticalAlignment: options.vAlign } : {}),
  };
  return box;
}

function rule(slide, name, left, top, width, height = 2, fill = C.line) {
  return rect(slide, name, left, top, width, height, fill);
}

function card(slide, name, left, top, width, height, options = {}) {
  return rect(slide, name, left, top, width, height, options.fill ?? C.white, {
    radius: options.radius ?? 12,
    line: options.line ?? C.line,
    lineWidth: options.lineWidth ?? 1,
    shadow: options.shadow,
  });
}

function titleBodyCard(slide, name, left, top, width, height, titleValue, bodyValue, options = {}) {
  card(slide, `${name}-card`, left, top, width, height, {
    fill: options.fill ?? C.white,
    line: options.line ?? C.line,
    radius: 12,
  });
  rect(slide, `${name}-accent`, left, top, 7, height, options.accent ?? C.primary, { radius: 3 });
  text(slide, `${name}-title`, titleValue, left + 24, top + 16, width - 44, 36, {
    size: options.titleSize ?? 19,
    bold: true,
    color: options.titleColor ?? C.deep,
  });
  text(slide, `${name}-body`, bodyValue, left + 24, top + 56, width - 44, height - 70, {
    size: options.bodySize ?? 17,
    color: options.bodyColor ?? C.ink,
  });
}

function tableCell(slide, name, value, left, top, width, height, options = {}) {
  rect(slide, `${name}-bg`, left, top, width, height, options.fill ?? C.white, {
    line: options.line ?? C.line,
    lineWidth: 1,
  });
  text(slide, `${name}-text`, value, left + 8, top + 6, width - 16, height - 12, {
    size: options.size ?? 16,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    align: options.align ?? "center",
    vAlign: "middle",
  });
}

function pageSourceRefs(page) {
  return Array.isArray(page?.source_refs) ? page.source_refs : [];
}

function addNotes(slide, page, images = []) {
  const common = Array.isArray(data.meta.source_notes) ? data.meta.source_notes : [];
  const pageRefs = pageSourceRefs(page);
  const lines = ["[Sources]"];
  for (const item of [...common, ...pageRefs]) lines.push(`- ${item}`);
  for (const imagePath of images.filter(Boolean)) {
    lines.push(`- Input image: ${path.relative(REPO_DIR, imagePath)}`);
  }
  if (lines.length === 1) lines.push("- Source reference was not supplied in the input package.");
  lines.push("[/Sources]");
  slide.speakerNotes.textFrame.setText(lines.join("\n"));
  slide.speakerNotes.setVisible(true);
}

function addChrome(slide, section, titleValue) {
  slide.background.fill = C.white;
  const pageNumber = presentation.slides.items.length;
  if (section) {
    rect(slide, "chrome-section-bg", 32, 18, 68, 42, C.deep, { radius: 10 });
    text(slide, "chrome-section", section, 32, 18, 68, 42, {
      size: 20,
      color: C.white,
      bold: true,
      align: "center",
      vAlign: "middle",
    });
  }
  text(slide, "chrome-title", titleValue, 118, 15, 830, 48, {
    size: 27,
    bold: true,
    color: C.ink,
    vAlign: "middle",
  });
  text(slide, "chrome-brand", data.meta.brand_label, 1000, 19, 245, 38, {
    size: 14,
    bold: true,
    color: C.secondary,
    align: "right",
  });
  rule(slide, "chrome-line", 32, 73, 1216, 1, C.line);
  rect(slide, "chrome-accent", 118, 70, 74, 5, C.primary, { radius: 2 });
  text(slide, "chrome-notice", data.meta.internal_notice, 860, 688, 300, 20, {
    size: 11,
    color: C.muted,
    align: "right",
  });
  text(slide, "chrome-index", String(pageNumber).padStart(2, "0"), 1174, 688, 70, 20, {
    size: 12,
    color: C.muted,
    align: "right",
  });
}

function newSlide(type, page, section = null) {
  const slide = presentation.slides.add();
  if (type !== "cover") addChrome(slide, page.section ?? section, page.title);
  slideRecords.push({
    index: presentation.slides.items.length,
    type,
    title: page.title,
  });
  return slide;
}

function imageMime(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  if (ext === ".svg") return "image/svg+xml";
  return "image/png";
}

async function addImage(slide, name, inputPath, frame, alt, fit = "contain") {
  if (!inputPath) return null;
  const resolved = resolveAsset(inputPath, name);
  const blob = await fs.readFile(resolved);
  slide.images.add({
    blob,
    contentType: imageMime(resolved),
    alt: alt || name,
    fit,
    position: frame,
  });
  return resolved;
}

function bulletList(slide, name, items, left, top, width, rowHeight, options = {}) {
  items.forEach((item, index) => {
    const y = top + index * rowHeight;
    ellipse(slide, `${name}-${index + 1}-dot`, left, y + 10, 14, 14, options.dot ?? C.primary);
    text(slide, `${name}-${index + 1}-text`, item, left + 28, y, width - 28, rowHeight - 2, {
      size: options.size ?? 18,
      color: options.color ?? C.ink,
      bold: options.bold ?? false,
      vAlign: "middle",
    });
  });
}

// 1. Cover: native shapes + optional bounded input image; never a flattened old slide.
{
  const page = data.pages.cover;
  const slide = newSlide("cover", page);
  slide.background.fill = C.white;
  rect(slide, "cover-left-field", 0, 0, 760, H, C.teal);
  rect(slide, "cover-right-field", 760, 0, 520, H, C.blue);
  ellipse(slide, "cover-orbit-1", 805, 45, 450, 450, "none", { line: "#FFFFFF55", lineWidth: 3 });
  ellipse(slide, "cover-orbit-2", 900, 115, 330, 330, "none", { line: "#FFFFFF44", lineWidth: 2 });
  rect(slide, "cover-eyebrow-rule", 72, 86, 72, 7, C.white, { radius: 3 });
  text(slide, "cover-brand", data.meta.organization, 72, 110, 560, 42, {
    size: 18,
    bold: true,
    color: C.white,
  });
  text(slide, "cover-eyebrow", page.eyebrow, 72, 206, 590, 38, {
    size: 17,
    color: "#DFF6EC",
    bold: true,
  });
  text(slide, "cover-title", page.title, 72, 252, 620, 120, {
    size: 40,
    bold: true,
    color: C.white,
    vAlign: "middle",
  });
  text(slide, "cover-subtitle", page.subtitle, 74, 382, 575, 78, {
    size: 21,
    color: C.white,
  });
  text(slide, "cover-prepared", page.prepared_line, 74, 594, 580, 36, {
    size: 14,
    color: "#DFF6EC",
  });
  text(slide, "cover-notice", data.meta.internal_notice, 74, 640, 580, 30, {
    size: 12,
    color: "#DFF6EC",
  });
  const coverImage = await addImage(
    slide,
    "cover-input-illustration",
    page.image,
    { left: 850, top: 170, width: 330, height: 365 },
    page.image_alt,
    "contain",
  );
  text(slide, "cover-product-label", data.product.name, 835, 565, 360, 45, {
    size: 20,
    bold: true,
    color: C.white,
    align: "center",
  });
  addNotes(slide, page, [coverImage]);
}

// 2. Opening thesis.
{
  const page = data.pages.opening;
  const slide = newSlide("opening", page);
  text(slide, "opening-kicker", page.kicker, 70, 108, 1140, 40, {
    size: 18,
    color: C.primary,
    bold: true,
    align: "center",
  });
  text(slide, "opening-headline", page.headline, 120, 150, 1040, 92, {
    size: 34,
    color: C.deep,
    bold: true,
    align: "center",
    vAlign: "middle",
  });
  const pillars = requireArray("pages.opening.pillars", { min: 3, max: 3 });
  pillars.forEach((pillar, index) => {
    const x = 65 + index * 405;
    card(slide, `opening-pillar-${index + 1}`, x, 285, 370, 190, {
      fill: index === 1 ? C.mint : C.white,
      line: index === 1 ? C.primary : C.line,
    });
    ellipse(slide, `opening-pillar-${index + 1}-number-bg`, x + 26, 310, 46, 46, C.primary);
    text(slide, `opening-pillar-${index + 1}-number`, String(index + 1), x + 26, 310, 46, 46, {
      size: 20,
      bold: true,
      color: C.white,
      align: "center",
      vAlign: "middle",
    });
    text(slide, `opening-pillar-${index + 1}-title`, pillar.title, x + 90, 303, 250, 55, {
      size: 20,
      bold: true,
      color: C.deep,
      vAlign: "middle",
    });
    text(slide, `opening-pillar-${index + 1}-body`, pillar.body, x + 22, 371, 326, 88, {
      size: 16,
      color: C.ink,
      align: "center",
      vAlign: "middle",
    });
  });
  text(slide, "opening-quote", page.quote, 190, 530, 900, 72, {
    size: 20,
    color: C.deep,
    bold: true,
    align: "center",
    vAlign: "middle",
    fill: C.pale,
    line: C.line,
    lineWidth: 1,
    radius: 14,
  });
  addNotes(slide, page);
}

// 3. Agenda.
{
  const page = data.pages.agenda;
  const slide = newSlide("agenda", page);
  const items = data.agenda;
  const colWidth = 560;
  const rowHeight = 150;
  items.forEach((item, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const x = 70 + col * 600;
    const y = 105 + row * rowHeight;
    card(slide, `agenda-${index + 1}`, x, y, colWidth, 118, {
      fill: index % 3 === 1 ? C.mint : C.white,
      line: C.line,
    });
    text(slide, `agenda-${index + 1}-number`, item.number, x + 22, y + 20, 64, 68, {
      size: 30,
      bold: true,
      color: C.primary,
      align: "center",
      vAlign: "middle",
    });
    text(slide, `agenda-${index + 1}-title`, item.title, x + 105, y + 18, 420, 42, {
      size: 21,
      bold: true,
      color: C.deep,
    });
    text(slide, `agenda-${index + 1}-subtitle`, item.subtitle, x + 105, y + 61, 420, 38, {
      size: 16,
      color: C.muted,
    });
  });
  addNotes(slide, page);
}

// 4. Disease definition.
{
  const page = data.pages.disease_definition;
  const slide = newSlide("disease-definition", page);
  const diseaseImage = await addImage(
    slide,
    "disease-definition-input-image",
    page.image,
    { left: 65, top: 120, width: 400, height: 410 },
    page.image_alt,
    "contain",
  );
  text(slide, "disease-definition-name", data.disease.name, 515, 118, 680, 62, {
    size: 31,
    bold: true,
    color: C.deep,
  });
  text(slide, "disease-definition-copy", data.disease.definition, 515, 194, 680, 142, {
    size: 21,
    color: C.ink,
    fill: C.pale,
    line: C.line,
    lineWidth: 1,
    radius: 14,
  });
  const tags = requireArray("disease.definition_tags", { min: 3, max: 5 });
  tags.forEach((tag, index) => {
    const x = 515 + (index % 2) * 340;
    const y = 370 + Math.floor(index / 2) * 82;
    text(slide, `disease-definition-tag-${index + 1}`, tag, x, y, 305, 58, {
      size: 18,
      bold: true,
      color: C.deep,
      align: "center",
      vAlign: "middle",
      fill: C.mint,
      line: C.line,
      lineWidth: 1,
      radius: 12,
    });
  });
  addNotes(slide, page, [diseaseImage]);
}

// 5. Symptoms.
{
  const page = data.pages.symptoms;
  const slide = newSlide("symptoms", page);
  const images = [];
  for (const [index, symptom] of data.disease.symptoms.entries()) {
    const x = 55 + index * 300;
    card(slide, `symptom-${index + 1}`, x, 115, 275, 500, {
      fill: index % 2 ? C.pale : C.white,
      line: C.line,
    });
    images.push(
      await addImage(
        slide,
        `symptom-${index + 1}-input-image`,
        symptom.image,
        { left: x + 40, top: 145, width: 195, height: 190 },
        symptom.image_alt,
        "contain",
      ),
    );
    text(slide, `symptom-${index + 1}-name`, symptom.name, x + 28, 356, 219, 52, {
      size: 21,
      bold: true,
      color: C.deep,
      align: "center",
      vAlign: "middle",
    });
    text(slide, `symptom-${index + 1}-description`, symptom.description, x + 28, 420, 219, 150, {
      size: 17,
      color: C.ink,
      align: "center",
    });
  }
  addNotes(slide, page, images);
}

// 6. Comparison table.
{
  const page = data.pages.comparison;
  const slide = newSlide("disease-comparison", page);
  const columns = requireArray("disease.comparison.columns", { min: 3, max: 4 });
  const rows = data.disease.comparison.rows;
  for (const row of rows) {
    if (!Array.isArray(row) || row.length !== columns.length) fail("each disease.comparison row must match columns");
  }
  const x = 55;
  const y = 112;
  const tableWidth = 1170;
  const columnWidths = columns.map((_, index) => (index === 0 ? 210 : (tableWidth - 210) / (columns.length - 1)));
  let cursorX = x;
  columns.forEach((column, index) => {
    tableCell(slide, `disease-compare-head-${index + 1}`, column, cursorX, y, columnWidths[index], 58, {
      fill: C.deep,
      color: C.white,
      bold: true,
      size: 18,
    });
    cursorX += columnWidths[index];
  });
  const rowHeight = Math.min(88, 430 / rows.length);
  rows.forEach((row, rowIndex) => {
    cursorX = x;
    row.forEach((value, colIndex) => {
      tableCell(
        slide,
        `disease-compare-${rowIndex + 1}-${colIndex + 1}`,
        value,
        cursorX,
        y + 58 + rowIndex * rowHeight,
        columnWidths[colIndex],
        rowHeight,
        {
          fill: rowIndex % 2 ? C.pale : C.white,
          bold: colIndex === 0,
          align: colIndex === 0 ? "center" : "left",
          size: 16,
        },
      );
      cursorX += columnWidths[colIndex];
    });
  });
  if (page.footer) {
    text(slide, "disease-comparison-footer", page.footer, 120, 605, 1040, 52, {
      size: 17,
      bold: true,
      color: C.deep,
      align: "center",
      vAlign: "middle",
      fill: C.mint,
      radius: 12,
    });
  }
  addNotes(slide, page);
}

// 7. Treatment principles.
{
  const page = data.pages.treatment;
  const slide = newSlide("treatment-principles", page);
  const items = data.disease.treatment_principles;
  items.forEach((item, index) => {
    const col = index % 3;
    const row = Math.floor(index / 3);
    const x = 55 + col * 405;
    const y = 115 + row * 245;
    titleBodyCard(slide, `treatment-${index + 1}`, x, y, 370, 210, item.title, item.body, {
      fill: row % 2 ? C.pale : C.white,
      titleSize: 20,
      bodySize: 17,
    });
  });
  addNotes(slide, page);
}

// 8. Subtypes.
{
  const page = data.pages.subtypes;
  const slide = newSlide("subtypes", page);
  const items = data.disease.subtypes;
  items.forEach((item, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const x = 65 + col * 600;
    const y = 112 + row * 250;
    card(slide, `subtype-${index + 1}`, x, y, 550, 215, {
      fill: index % 2 ? C.pale : C.white,
      line: C.line,
    });
    text(slide, `subtype-${index + 1}-name`, item.name, x + 24, y + 20, 500, 42, {
      size: 21,
      bold: true,
      color: C.deep,
    });
    text(slide, `subtype-${index + 1}-features-label`, item.features_label, x + 24, y + 78, 100, 30, {
      size: 16,
      bold: true,
      color: C.primary,
    });
    text(slide, `subtype-${index + 1}-features`, item.features, x + 145, y + 75, 375, 55, {
      size: 16,
      color: C.ink,
    });
    text(slide, `subtype-${index + 1}-approach-label`, item.approach_label, x + 24, y + 143, 100, 30, {
      size: 16,
      bold: true,
      color: C.primary,
    });
    text(slide, `subtype-${index + 1}-approach`, item.approach, x + 145, y + 140, 375, 55, {
      size: 16,
      color: C.ink,
    });
  });
  addNotes(slide, page);
}

// 9. Product information.
{
  const page = data.pages.product_info;
  const slide = newSlide("product-info", page);
  const productImage = await addImage(
    slide,
    "product-info-input-image",
    data.product.image,
    { left: 60, top: 125, width: 400, height: 360 },
    data.product.image_alt,
    "contain",
  );
  text(slide, "product-info-name", data.product.name, 60, 515, 400, 58, {
    size: 25,
    bold: true,
    color: C.deep,
    align: "center",
    vAlign: "middle",
  });
  const fields = data.product.information;
  fields.forEach((field, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const x = 510 + col * 355;
    const y = 118 + row * 158;
    card(slide, `product-info-${index + 1}`, x, y, 325, 132, {
      fill: row % 2 ? C.pale : C.white,
      line: C.line,
    });
    text(slide, `product-info-${index + 1}-label`, field.label, x + 20, y + 16, 285, 30, {
      size: 15,
      bold: true,
      color: C.primary,
    });
    text(slide, `product-info-${index + 1}-value`, field.value, x + 20, y + 52, 285, 62, {
      size: 18,
      bold: field.emphasis === true,
      color: C.ink,
      vAlign: "middle",
    });
  });
  const badges = Array.isArray(data.product.badges) ? data.product.badges : [];
  badges.slice(0, 3).forEach((badge, index) => {
    text(slide, `product-badge-${index + 1}`, badge, 510 + index * 235, 610, 205, 42, {
      size: 15,
      bold: true,
      color: C.deep,
      align: "center",
      vAlign: "middle",
      fill: C.mint,
      radius: 10,
    });
  });
  addNotes(slide, page, [productImage]);
}

// 10. Product advantages.
{
  const page = data.pages.advantages;
  const slide = newSlide("product-advantages", page);
  data.product.advantages.forEach((item, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const x = 65 + col * 600;
    const y = 115 + row * 245;
    card(slide, `advantage-${index + 1}`, x, y, 550, 210, {
      fill: index % 3 === 1 ? C.mint : C.white,
      line: C.line,
    });
    ellipse(slide, `advantage-${index + 1}-number-bg`, x + 24, y + 26, 52, 52, C.primary);
    text(slide, `advantage-${index + 1}-number`, String(index + 1), x + 24, y + 26, 52, 52, {
      size: 21,
      bold: true,
      color: C.white,
      align: "center",
      vAlign: "middle",
    });
    text(slide, `advantage-${index + 1}-title`, item.title, x + 96, y + 25, 420, 52, {
      size: 21,
      bold: true,
      color: C.deep,
      vAlign: "middle",
    });
    text(slide, `advantage-${index + 1}-body`, item.body, x + 28, y + 96, 494, 88, {
      size: 17,
      color: C.ink,
    });
  });
  addNotes(slide, page);
}

// 11. Product summary.
{
  const page = data.pages.product_summary;
  const slide = newSlide("product-summary", page);
  text(slide, "product-summary-headline", data.product.summary.headline, 120, 102, 1040, 72, {
    size: 27,
    bold: true,
    color: C.deep,
    align: "center",
    vAlign: "middle",
    fill: C.mint,
    radius: 14,
  });
  const groups = data.product.summary.groups;
  const groupWidth = groups.length === 2 ? 540 : 365;
  const startX = groups.length === 2 ? 80 : 55;
  groups.forEach((group, index) => {
    if (!Array.isArray(group.items) || group.items.length < 1 || group.items.length > 4) {
      fail(`product.summary.groups[${index}].items must contain 1..4 items`);
    }
    const x = startX + index * (groupWidth + 35);
    card(slide, `summary-group-${index + 1}`, x, 215, groupWidth, 355, {
      fill: index === 1 ? C.pale : C.white,
      line: C.line,
    });
    text(slide, `summary-group-${index + 1}-title`, group.title, x + 24, 238, groupWidth - 48, 48, {
      size: 21,
      bold: true,
      color: C.deep,
      align: "center",
      vAlign: "middle",
    });
    bulletList(slide, `summary-group-${index + 1}-items`, group.items, x + 32, 310, groupWidth - 64, 62, {
      size: 17,
    });
  });
  addNotes(slide, page);
}

// 12. Audience.
{
  const page = data.pages.audience;
  const slide = newSlide("audience", page);
  const images = [];
  for (const [index, item] of data.product.audience.entries()) {
    const x = 65 + index * 405;
    card(slide, `audience-${index + 1}`, x, 115, 370, 500, {
      fill: index === 1 ? C.pale : C.white,
      line: C.line,
    });
    images.push(
      await addImage(
        slide,
        `audience-${index + 1}-input-image`,
        item.image,
        { left: x + 60, top: 145, width: 250, height: 225 },
        item.image_alt,
        "contain",
      ),
    );
    text(slide, `audience-${index + 1}-title`, item.title, x + 30, 390, 310, 55, {
      size: 21,
      bold: true,
      color: C.deep,
      align: "center",
      vAlign: "middle",
    });
    text(slide, `audience-${index + 1}-body`, item.body, x + 30, 465, 310, 112, {
      size: 17,
      color: C.ink,
      align: "center",
    });
  }
  addNotes(slide, page, images);
}

// 13. Consultation framework.
{
  const page = data.pages.consultation;
  const slide = newSlide("consultation", page);
  const items = data.product.consultation;
  items.forEach((item, index) => {
    const y = 112 + index * 128;
    ellipse(slide, `consultation-${index + 1}-step-bg`, 75, y + 17, 78, 78, C.primary);
    text(slide, `consultation-${index + 1}-step`, item.step, 75, y + 17, 78, 78, {
      size: 22,
      bold: true,
      color: C.white,
      align: "center",
      vAlign: "middle",
    });
    card(slide, `consultation-${index + 1}-card`, 185, y, 1020, 112, {
      fill: index % 2 ? C.pale : C.white,
      line: C.line,
    });
    text(slide, `consultation-${index + 1}-title`, item.title, 215, y + 16, 260, 34, {
      size: 19,
      bold: true,
      color: C.deep,
    });
    text(slide, `consultation-${index + 1}-question`, item.question, 215, y + 53, 950, 44, {
      size: 18,
      color: C.ink,
      vAlign: "middle",
    });
  });
  addNotes(slide, page);
}

// 14+. One page per input scenario; dialogue is never templated in the engine.
for (const [scenarioIndex, scenario] of data.product.scenarios.entries()) {
  if (
    !scenario.page_title ||
    !scenario.title ||
    !Array.isArray(scenario.dialogues) ||
    scenario.dialogues.length < 2 ||
    scenario.dialogues.length > 5
  ) {
    fail(`product.scenarios[${scenarioIndex}] requires page_title, title and 2..5 dialogues`);
  }
  const page = {
    title: scenario.page_title,
    section: scenario.section,
    source_refs: scenario.source_refs,
  };
  const slide = newSlide("scenario", page);
  text(slide, `scenario-${scenarioIndex + 1}-title`, scenario.title, 65, 105, 650, 54, {
    size: 25,
    bold: true,
    color: C.deep,
  });
  titleBodyCard(slide, `scenario-${scenarioIndex + 1}-profile`, 65, 180, 520, 150, scenario.profile_label, scenario.profile, {
    fill: C.pale,
    bodySize: 17,
  });
  titleBodyCard(slide, `scenario-${scenarioIndex + 1}-needs`, 65, 350, 520, 145, scenario.needs_label, scenario.needs, {
    fill: C.white,
    bodySize: 17,
  });
  text(slide, `scenario-${scenarioIndex + 1}-recommendation-label`, scenario.recommendation_label, 65, 520, 520, 34, {
    size: 17,
    bold: true,
    color: C.primary,
  });
  text(slide, `scenario-${scenarioIndex + 1}-recommendation`, scenario.recommendation, 65, 556, 520, 80, {
    size: 17,
    color: C.ink,
    fill: C.mint,
    radius: 10,
  });
  scenario.dialogues.forEach((dialogue, index) => {
    const y = 120 + index * 103;
    const staff = dialogue.role === "staff";
    const x = staff ? 650 : 720;
    text(slide, `scenario-${scenarioIndex + 1}-dialogue-${index + 1}-speaker`, dialogue.speaker, x, y, 150, 28, {
      size: 14,
      bold: true,
      color: staff ? C.primary : C.blue,
    });
    text(slide, `scenario-${scenarioIndex + 1}-dialogue-${index + 1}-text`, dialogue.text, x, y + 30, staff ? 520 : 455, 62, {
      size: 17,
      color: C.ink,
      fill: staff ? C.mint : "#EEF5FA",
      line: staff ? C.line : "#D9E5ED",
      lineWidth: 1,
      radius: 12,
      vAlign: "middle",
    });
  });
  addNotes(slide, page);
}

// Daily care.
{
  const page = data.pages.daily_care;
  const slide = newSlide("daily-care", page);
  const images = [];
  const careColumns = data.product.daily_care.length === 4 ? 2 : 3;
  const careWidth = careColumns === 2 ? 550 : 370;
  const careStep = careColumns === 2 ? 600 : 405;
  for (const [index, item] of data.product.daily_care.entries()) {
    const col = index % careColumns;
    const row = Math.floor(index / careColumns);
    const x = 55 + col * careStep;
    const y = 112 + row * 260;
    card(slide, `daily-care-${index + 1}`, x, y, careWidth, 225, {
      fill: index % 2 ? C.pale : C.white,
      line: C.line,
    });
    images.push(
      await addImage(
        slide,
        `daily-care-${index + 1}-input-image`,
        item.image,
        { left: x + 22, top: y + 27, width: 110, height: 110 },
        item.image_alt,
        "contain",
      ),
    );
    text(slide, `daily-care-${index + 1}-title`, item.title, x + 148, y + 28, careWidth - 172, 60, {
      size: 18,
      bold: true,
      color: C.deep,
      vAlign: "middle",
    });
    text(slide, `daily-care-${index + 1}-body`, item.body, x + 25, y + 146, careWidth - 50, 60, {
      size: 16,
      color: C.ink,
      align: "center",
    });
  }
  addNotes(slide, page, images);
}

// One weighted detail page per input item.
for (const [itemIndex, item] of data.weighted.items.entries()) {
  if (!item.page_title || !item.name) fail(`weighted.items[${itemIndex}] requires page_title and name`);
  const page = { title: item.page_title, section: item.section, source_refs: item.source_refs };
  const slide = newSlide("weighted-detail", page);
  const productImage = await addImage(
    slide,
    `weighted-${itemIndex + 1}-input-image`,
    item.image,
    { left: 55, top: 110, width: 420, height: 265 },
    item.image_alt,
    "contain",
  );
  text(slide, `weighted-${itemIndex + 1}-name`, item.name, 55, 385, 420, 48, {
    size: 23,
    bold: true,
    color: C.deep,
    align: "center",
  });
  const fields = Array.isArray(item.fields) ? item.fields : [];
  if (fields.length < 1 || fields.length > 4) {
    fail(`weighted.items[${itemIndex}].fields must contain 1..4 items`);
  }
  if (!Array.isArray(item.selling_points) || item.selling_points.length < 1 || item.selling_points.length > 4) {
    fail(`weighted.items[${itemIndex}].selling_points must contain 1..4 items`);
  }
  fields.forEach((field, index) => {
    const width = 420 / Math.max(fields.length, 1);
    tableCell(slide, `weighted-${itemIndex + 1}-field-${index + 1}-label`, field.label, 55 + index * width, 452, width, 40, {
      fill: C.deep,
      color: C.white,
      bold: true,
      size: 14,
    });
    tableCell(slide, `weighted-${itemIndex + 1}-field-${index + 1}-value`, field.value, 55 + index * width, 492, width, 60, {
      fill: C.white,
      size: 15,
    });
  });
  text(slide, `weighted-${itemIndex + 1}-slogan`, item.slogan, 55, 575, 420, 67, {
    size: 17,
    bold: true,
    color: C.red,
    align: "center",
    vAlign: "middle",
    fill: C.pale,
    radius: 10,
  });
  titleBodyCard(
    slide,
    `weighted-${itemIndex + 1}-selling`,
    520,
    110,
    705,
    220,
    item.selling_points_label,
    item.selling_points.join("\n"),
    { titleColor: C.red, bodySize: 18, fill: C.white },
  );
  const table = item.table;
  if (table?.headers?.length && table?.rows?.length) {
    if (table.headers.length < 2 || table.headers.length > 4 || table.rows.length > 3) {
      fail(`weighted.items[${itemIndex}].table must have 2..4 columns and at most 3 rows`);
    }
    table.rows.forEach((row, rowIndex) => {
      if (!Array.isArray(row) || row.length !== table.headers.length) {
        fail(`weighted.items[${itemIndex}].table.rows[${rowIndex}] must match headers`);
      }
    });
    const columnWidth = 650 / table.headers.length;
    table.headers.forEach((header, index) =>
      tableCell(slide, `weighted-${itemIndex + 1}-table-head-${index + 1}`, header, 548 + index * columnWidth, 355, columnWidth, 42, {
        fill: C.deep,
        color: C.white,
        bold: true,
        size: 15,
      }),
    );
    table.rows.forEach((row, rowIndex) =>
      row.forEach((value, colIndex) =>
        tableCell(
          slide,
          `weighted-${itemIndex + 1}-table-${rowIndex + 1}-${colIndex + 1}`,
          value,
          548 + colIndex * columnWidth,
          397 + rowIndex * 40,
          columnWidth,
          40,
          { fill: rowIndex % 2 ? C.pale : C.white, size: 14 },
        ),
      ),
    );
  }
  text(slide, `weighted-${itemIndex + 1}-suitable-label`, item.suitable_for_label, 520, 535, 170, 34, {
    size: 17,
    bold: true,
    color: C.primary,
  });
  text(slide, `weighted-${itemIndex + 1}-suitable`, item.suitable_for, 520, 570, 705, 72, {
    size: 17,
    color: C.ink,
    fill: C.mint,
    radius: 10,
  });
  addNotes(slide, page, [productImage]);
}

// Final weighted comparison page.
{
  const page = data.pages.weighted_comparison;
  const comparison = data.weighted.comparison;
  const slide = newSlide("weighted-comparison", page);
  const products = comparison.products;
  const x = 45;
  const y = 110;
  const labelWidth = 180;
  const productWidth = (1190 - labelWidth) / products.length;
  tableCell(slide, "weighted-compare-dimension", comparison.dimension_label, x, y, labelWidth, 72, {
    fill: C.deep,
    color: C.white,
    bold: true,
    size: 17,
  });
  products.forEach((product, index) => {
    tableCell(slide, `weighted-compare-product-${index + 1}`, product.name, x + labelWidth + index * productWidth, y, productWidth, 72, {
      fill: C.deep,
      color: C.white,
      bold: true,
      size: 17,
    });
  });
  const rowHeight = Math.min(100, 470 / comparison.rows.length);
  comparison.rows.forEach((row, rowIndex) => {
    if (!Array.isArray(row.values) || row.values.length !== products.length) {
      fail(`weighted.comparison.rows[${rowIndex}].values must match products`);
    }
    tableCell(slide, `weighted-compare-row-${rowIndex + 1}-label`, row.dimension, x, y + 72 + rowIndex * rowHeight, labelWidth, rowHeight, {
      fill: C.mint,
      bold: true,
      size: 16,
    });
    row.values.forEach((value, productIndex) => {
      tableCell(
        slide,
        `weighted-compare-row-${rowIndex + 1}-value-${productIndex + 1}`,
        value,
        x + labelWidth + productIndex * productWidth,
        y + 72 + rowIndex * rowHeight,
        productWidth,
        rowHeight,
        {
          fill: rowIndex % 2 ? C.pale : C.white,
          size: 16,
          align: "left",
        },
      );
    });
  });
  if (comparison.footer) {
    text(slide, "weighted-comparison-footer", comparison.footer, 110, 615, 1060, 46, {
      size: 16,
      color: C.deep,
      bold: true,
      align: "center",
      vAlign: "middle",
      fill: C.mint,
      radius: 10,
    });
  }
  addNotes(slide, page);
}

await fs.mkdir(path.dirname(outPath), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

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
  maxChars: 500000,
});
await fs.writeFile(path.join(qaDir, "inspection.ndjson"), inspection.ndjson);

const outputForbiddenHits = isAuthorizedGold
  ? []
  : GOLD_FORBIDDEN.filter((token) => inspection.ndjson.includes(token));
if (outputForbiddenHits.length) {
  fail(`non-gold rendered deck contains settled gold tokens: ${outputForbiddenHits.join(", ")}`, 4);
}

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outPath);
const fontPatch = spawnSync("python3", [FONT_PATCH, outPath, FONT], { encoding: "utf8" });
if (fontPatch.status !== 0) {
  fail(`font patch failed: ${fontPatch.stderr || fontPatch.stdout}`, 5);
}

const inspectionRows = inspection.ndjson
  .split("\n")
  .filter(Boolean)
  .map((line) => JSON.parse(line));
const report = {
  schema_version: "disease-product-scenario-generation-report/v1",
  ok: true,
  engine: "disease-product-scenario-pptx-v1",
  input: path.relative(REPO_DIR, dataPath),
  input_sha256: crypto.createHash("sha256").update(dataBytes).digest("hex"),
  theme_id: data.meta.theme_id,
  gold_sample: isAuthorizedGold,
  style_pack_id: style.style_pack_id,
  style: path.relative(REPO_DIR, stylePath),
  output: outPath,
  qa_dir: qaDir,
  page_count: presentation.slides.items.length,
  pages: slideRecords,
  editable_textboxes: inspectionRows.filter((row) => row.kind === "textbox").length,
  input_images: discoveredAssets.length,
  rendered_images: inspectionRows.filter((row) => row.kind === "image").length,
  forbidden_input_hits: inputForbiddenHits,
  forbidden_output_hits: outputForbiddenHits,
  cover_source: "editable-native-layout",
  font: FONT,
  font_patched: true,
  qa: {
    slide_pngs: presentation.slides.items.length,
    slide_layouts: presentation.slides.items.length,
    montage: "deck-montage.webp",
    inspection: "inspection.ndjson",
  },
};
await fs.mkdir(path.dirname(reportPath), { recursive: true });
await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));
