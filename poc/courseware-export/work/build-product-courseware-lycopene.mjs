/**
 * 福尔番茄红素软胶囊 · 绿色商品培训课件
 * 页型复用金银花露 green 模板，布局按内容自适应（不硬凑联合推荐行数）。
 */
import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const currentFile = fileURLToPath(import.meta.url);
const workDir = path.dirname(currentFile);
const projectDir = path.resolve(workDir, "..");
const repoDir = path.resolve(projectDir, "../..");

const dataPath = path.join(projectDir, "product-courseware-lycopene.json");
const outRoot = path.join(
  repoDir,
  "production-library/validation/courseware/product-courseware-lycopene-green-v1",
);
const outputPptx = path.join(outRoot, "福尔番茄红素软胶囊_商品培训课件.pptx");
const qaDir = path.join(outRoot, "qa");

const data = JSON.parse(await fs.readFile(dataPath, "utf8"));

const W = 1280;
const H = 720;
// 企业内训 PPT 统一：微软雅黑（门店 Windows 友好）。导出后由 postprocess 注入 OOXML typeface。
const FONT = "Microsoft YaHei";
const GREEN = data.brand.primary;
const GREEN_2 = data.brand.secondary;
const PALE = data.brand.pale;
const LIGHT = "#F1F1F1";
const WHITE = "#FFFFFF";
const BLACK = "#111111";
const RED = "#E60012";
const YELLOW = "#FFF200";
const BLUE = "#176A91";

const presentation = Presentation.create({
  slideSize: { width: W, height: H },
});

function rect(slide, name, x, y, width, height, fill, line = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  });
}

function ellipse(slide, name, x, y, width, height, fill, line = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry: "ellipse",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  });
}

function text(
  slide,
  name,
  value,
  x,
  y,
  width,
  height,
  {
    size = 20,
    color = BLACK,
    bold = false,
    align = "left",
    fill = "none",
    line = "none",
    lineWidth = 0,
  } = {},
) {
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
  return shape;
}

function cell(
  slide,
  name,
  value,
  x,
  y,
  width,
  height,
  {
    fill = WHITE,
    color = BLACK,
    size = 17,
    bold = false,
    align = "center",
    line = WHITE,
    lineWidth = 1,
  } = {},
) {
  rect(slide, `${name}-surface`, x, y, width, height, fill, line, lineWidth);
  return text(slide, `${name}-text`, value, x + 8, y + 8, width - 16, height - 16, {
    size,
    color,
    bold,
    align,
  });
}

function addNotes(slide, reference) {
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n- Content: business-approved manuscript (content-first layout)\n- Style: product-courseware-green-v1 (dashenlin)\n- Reference id: ${reference}\n- Compliance review required before external use.\n[/Sources]`,
  );
  slide.speakerNotes.setVisible(true);
}

function addBrand(slide, x = 1080, y = 18) {
  text(slide, "brand-wordmark", "大参林 dashenlin", x, y, 165, 42, {
    size: 18,
    color: GREEN_2,
    bold: true,
    align: "right",
  });
}

function addFooter(slide) {
  text(slide, "internal-notice", data.brand.internal_notice, 1080, 688, 170, 22, {
    size: 14,
    align: "right",
  });
}

function addPageChrome(slide, page) {
  slide.background.fill = WHITE;
  rect(slide, "header-shadow-line", 0, 69, W, 3, "#D9E8D4");
  rect(slide, "header-green-line", 95, 69, W - 95, 4, GREEN);
  rect(slide, "page-number-block", 30, 0, 70, 83, GREEN);
  text(slide, "page-number", page.page_number, 22, 19, 86, 48, {
    size: 28,
    color: WHITE,
    align: "center",
  });
  text(slide, "page-title", page.title, 110, 16, 740, 48, {
    size: 30,
    bold: true,
  });
  addBrand(slide);
  addFooter(slide);
}

function assetSlot(slide, name, label, x, y, width, height, fill = "#D9EEF4") {
  rect(slide, `${name}-surface`, x, y, width, height, fill, "#8ABFC8", 1);
  text(slide, `${name}-label`, label, x + 10, y + height / 2 - 25, width - 20, 50, {
    size: 16,
    color: "#315C62",
    bold: true,
    align: "center",
  });
}

/** 封面标题字号：按字数自适应，避免长品名溢出 */
function coverTitleSize(title) {
  const n = [...title].length;
  if (n <= 4) return 64;
  if (n <= 6) return 52;
  if (n <= 9) return 42;
  if (n <= 12) return 36;
  return 30;
}

function addCover(page) {
  const slide = presentation.slides.add();
  slide.background.fill = WHITE;
  rect(slide, "cover-color-field", 0, 0, W, 440, "#006D58");
  rect(slide, "cover-blue-field", 560, 0, 720, 440, BLUE);
  rect(slide, "cover-green-overlay", 0, 0, 460, 440, GREEN);
  for (let i = 0; i < 10; i += 1) {
    rect(
      slide,
      `cover-building-band-${i + 1}`,
      690 + i * 50,
      55 + (i % 3) * 18,
      26,
      330 - (i % 4) * 26,
      i % 2 === 0 ? "#5A98B1" : "#2D7898",
    );
  }
  rect(slide, "cover-white-bottom", 0, 500, W, H - 500, WHITE);
  ellipse(slide, "cover-white-curve", 0, 330, W, 340, WHITE);
  rect(slide, "cover-frame-top", 200, 120, 880, 4, "#82D400");
  rect(slide, "cover-frame-left", 200, 120, 4, 440, "#82D400");
  rect(slide, "cover-frame-right", 1076, 120, 4, 440, "#2E5FA4");
  rect(slide, "cover-frame-bottom", 200, 556, 880, 4, "#2E5FA4");
  text(slide, "cover-brand", data.brand.display_name, 236, 136, 190, 52, {
    size: 20,
    color: WHITE,
    bold: true,
  });
  text(slide, "cover-organization", page.organization, 490, 195, 300, 44, {
    size: 24,
    color: WHITE,
    bold: true,
    align: "center",
  });
  rect(slide, "cover-rule-left", 305, 215, 175, 2, WHITE);
  rect(slide, "cover-rule-right", 800, 215, 175, 2, WHITE);

  const titleSize = coverTitleSize(page.title);
  text(slide, "cover-title", page.title, 240, 245, 800, 120, {
    size: titleSize,
    color: WHITE,
    bold: true,
    align: "center",
  });
  text(slide, "cover-tagline", page.tagline, 550, 542, 180, 40, {
    size: 22,
    color: WHITE,
    bold: true,
    align: "center",
    fill: "#00775C",
  });
  addFooter(slide);
  addNotes(slide, page.reference);
}

/**
 * 右侧三板块高度按条目数与字数分配，避免固定 3 段高度硬塞。
 */
function planOverviewSections(sections) {
  const top = 102;
  const bottom = 680;
  const titleH = 39;
  const usable = bottom - top;
  const titleTotal = sections.length * titleH;
  const bodyBudget = usable - titleTotal;

  const weights = sections.map((section, sectionIndex) => {
    const itemCount = Math.max(section.items.length, 1);
    const charWeight = section.items.reduce((sum, item) => sum + Math.min(item.length, 80), 0) / 40;
    // 核心卖点段（通常第 2 段）略加重
    const boost = sectionIndex === 1 ? 1.25 : 1;
    return (itemCount + charWeight) * boost;
  });
  const weightSum = weights.reduce((a, b) => a + b, 0) || 1;

  let allocated = weights.map((w) => Math.floor((w / weightSum) * bodyBudget));
  // 修正取整误差
  let remainder = bodyBudget - allocated.reduce((a, b) => a + b, 0);
  for (let i = 0; remainder > 0; i = (i + 1) % allocated.length) {
    allocated[i] += 1;
    remainder -= 1;
  }

  return sections.map((section, index) => {
    const bodyH = allocated[index];
    const itemH = Math.max(28, Math.floor(bodyH / Math.max(section.items.length, 1)));
    const fontSize = itemH < 34 ? 15 : itemH < 42 ? 16 : section.title.includes("核心") ? 16 : 17;
    return { section, bodyH, itemH, fontSize, titleH };
  });
}

function addOverview(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  assetSlot(slide, "primary-packshot", "商品包装高清图\n待接入", 145, 82, 205, 270);
  text(slide, "product-name", page.product.display_name, 110, 360, 280, 42, {
    size: 20,
    color: RED,
    bold: true,
    align: "center",
  });

  const tableX = 38;
  const tableY = 420;
  const widths = [120, 82, 153, 112];
  const headers = ["编码", "主推", "规格", "零售价"];
  let cursorX = tableX;
  headers.forEach((header, index) => {
    cell(slide, `product-table-head-${index}`, header, cursorX, tableY, widths[index], 48, {
      size: 19,
      bold: true,
      line: BLACK,
    });
    cursorX += widths[index];
  });
  cursorX = tableX;
  [
    page.product.code,
    page.product.priority,
    page.product.specification,
    page.product.retail_price,
  ].forEach((value, index) => {
    cell(slide, `product-table-value-${index}`, value, cursorX, tableY + 48, widths[index], 56, {
      size: index === 0 ? 16 : 19,
      line: BLACK,
    });
    cursorX += widths[index];
  });

  rect(slide, "selling-point-highlight", 38, 544, 467, 120, YELLOW);
  text(
    slide,
    "selling-point",
    `一句话卖点：${page.product.one_line_selling_point}`,
    48,
    565,
    445,
    80,
    { size: 20, bold: true },
  );

  const sectionX = 525;
  const sectionW = 710;
  const plan = planOverviewSections(page.sections);
  let y = 102;
  plan.forEach(({ section, itemH, fontSize, titleH }, sectionIndex) => {
    text(
      slide,
      `section-title-${sectionIndex}`,
      section.title,
      sectionX,
      y,
      170,
      34,
      { size: 20, color: WHITE, bold: true, align: "center", fill: GREEN },
    );
    y += titleH;
    section.items.forEach((item, itemIndex) => {
      text(
        slide,
        `section-${sectionIndex}-item-${itemIndex}`,
        `${itemIndex + 1}、${item}`,
        sectionX,
        y,
        sectionW,
        itemH,
        { size: fontSize, bold: sectionIndex === 1 },
      );
      y += itemH;
    });
  });
  addNotes(slide, page.reference);
}

/**
 * 联合推荐（与金银花露母版一致）：
 * 联合商品图按行独立；本品图纵向合并，每一行都与本品关联。
 */
function addCombination(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  const x = 28;
  const y = 96;
  const headerH = 58;
  const rowCount = page.rows.length;
  if (rowCount < 1) throw new Error("combination_guidance requires at least 1 row");

  const widths = [150, 175, 230, 200, 465];
  const headers = page.columns?.length === 5
    ? page.columns
    : [
        "应用场景（适宜人群）",
        "联合推荐",
        "联合商品图",
        page.primary_column_title || "本品图",
        "销售话术",
      ];

  const usable = 680 - y - headerH;
  const baseH = Math.floor(usable / rowCount);
  const rowHeights = Array.from({ length: rowCount }, () => baseH);
  let rem = usable - baseH * rowCount;
  for (let i = 0; rem > 0; i += 1, rem -= 1) rowHeights[i] += 1;

  let cx = x;
  headers.forEach((header, index) => {
    cell(slide, `combination-head-${index}`, header, cx, y, widths[index], headerH, {
      fill: GREEN,
      color: WHITE,
      size: index <= 1 ? 16 : 17,
      bold: true,
      line: WHITE,
    });
    cx += widths[index];
  });

  const bodyTop = y + headerH;
  const bodyH = rowHeights.reduce((a, b) => a + b, 0);
  const primaryLabel = page.primary_pack_label || "本品包装图\n待接入";

  let cy = bodyTop;
  page.rows.forEach((row, rowIndex) => {
    const h = rowHeights[rowIndex];
    const fill = rowIndex % 2 === 1 ? PALE : LIGHT;
    const talkSize = (row.talk_track || "").length > 95 ? 14 : 15;

    cell(slide, `combination-scenario-${rowIndex}`, row.scenario, x, cy, widths[0], h, {
      fill,
      size: 15,
      bold: true,
      align: "left",
    });
    cell(
      slide,
      `combination-name-${rowIndex}`,
      row.combination,
      x + widths[0],
      cy,
      widths[1],
      h,
      { fill, size: 15, bold: true, align: "left" },
    );

    rect(
      slide,
      `combination-partner-surface-${rowIndex}`,
      x + widths[0] + widths[1],
      cy,
      widths[2],
      h,
      fill,
      WHITE,
      1,
    );
    const partnerSlotH = Math.min(h - 28, 150);
    assetSlot(
      slide,
      `partner-slot-${rowIndex}`,
      `${row.partner}\n包装图待接入`,
      x + widths[0] + widths[1] + 20,
      cy + (h - partnerSlotH) / 2,
      widths[2] - 40,
      partnerSlotH,
      "#F7FAF4",
    );

    cell(
      slide,
      `combination-talk-${rowIndex}`,
      row.talk_track,
      x + widths[0] + widths[1] + widths[2] + widths[3],
      cy,
      widths[4],
      h,
      { fill, size: talkSize, align: "left" },
    );
    cy += h;
  });

  const primaryX = x + widths[0] + widths[1] + widths[2];
  rect(
    slide,
    "combination-primary-merge-surface",
    primaryX,
    bodyTop,
    widths[3],
    bodyH,
    PALE,
    WHITE,
    1,
  );
  rect(slide, "combination-primary-divider", primaryX, bodyTop, 3, bodyH, GREEN);
  text(
    slide,
    "combination-plus",
    "+",
    primaryX + 8,
    bodyTop + bodyH / 2 - 28,
    40,
    56,
    { size: 40, color: RED, bold: true, align: "center" },
  );
  const primarySlotW = 130;
  const primarySlotH = Math.min(bodyH - 48, 280);
  assetSlot(
    slide,
    "combination-primary-product",
    primaryLabel,
    primaryX + (widths[3] - primarySlotW) / 2 + 10,
    bodyTop + (bodyH - primarySlotH) / 2,
    primarySlotW,
    primarySlotH,
    "#D9EEF4",
  );

  addNotes(slide, page.reference);
}

function addBenchmark(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  const x = 45;
  const y = 105;
  const widths = [160, 540, 500];
  const headerH = 56;
  const bodyRows = page.rows;
  const usable = 680 - y - headerH;
  // 产品展示行更高，其余均分
  const showcaseBoost = 90;
  const otherCount = Math.max(bodyRows.length - 1, 1);
  const otherBase = Math.floor((usable - showcaseBoost) / bodyRows.length);
  const rowHeights = bodyRows.map((row, i) =>
    row.label === "产品展示" ? otherBase + showcaseBoost : otherBase,
  );
  let rem = usable - rowHeights.reduce((a, b) => a + b, 0);
  for (let i = 0; rem !== 0; i = (i + 1) % rowHeights.length) {
    const step = rem > 0 ? 1 : -1;
    rowHeights[i] += step;
    rem -= step;
  }

  let cx = x;
  page.columns.forEach((header, index) => {
    cell(slide, `benchmark-head-${index}`, header, cx, y, widths[index], headerH, {
      fill: GREEN,
      color: WHITE,
      size: 16,
      bold: true,
      line: BLACK,
    });
    cx += widths[index];
  });

  const primaryLabel = page.primary_pack_label || "本品包装图\n待接入";
  const competitorLabel = page.competitor_pack_label || "竞品包装图\n待接入";

  let cy = y + headerH;
  bodyRows.forEach((row, rowIndex) => {
    const h = rowHeights[rowIndex];
    cell(slide, `benchmark-label-${rowIndex}`, row.label, x, cy, widths[0], h, {
      bold: true,
      size: 16,
      line: BLACK,
    });
    if (row.label === "产品展示") {
      rect(slide, "benchmark-product-left-cell", x + widths[0], cy, widths[1], h, WHITE, BLACK, 1);
      rect(
        slide,
        "benchmark-product-right-cell",
        x + widths[0] + widths[1],
        cy,
        widths[2],
        h,
        WHITE,
        BLACK,
        1,
      );
      assetSlot(
        slide,
        "benchmark-primary-packshot",
        primaryLabel,
        x + widths[0] + 195,
        cy + 16,
        140,
        h - 32,
      );
      assetSlot(
        slide,
        "benchmark-competitor-packshot",
        competitorLabel,
        x + widths[0] + widths[1] + 175,
        cy + 16,
        140,
        h - 32,
        "#E9F1E8",
      );
    } else if (row.merge) {
      cell(
        slide,
        `benchmark-merged-${rowIndex}`,
        row.value,
        x + widths[0],
        cy,
        widths[1] + widths[2],
        h,
        { size: 16, bold: row.label === "共有优势", line: BLACK },
      );
    } else {
      const leftSize = (row.values[0] || "").length > 40 ? 14 : 16;
      const rightSize = (row.values[1] || "").length > 40 ? 14 : 16;
      cell(
        slide,
        `benchmark-left-${rowIndex}`,
        row.values[0],
        x + widths[0],
        cy,
        widths[1],
        h,
        {
          size: leftSize,
          color: row.label === "卖点差异" ? RED : BLACK,
          bold: row.label === "卖点差异",
          line: BLACK,
        },
      );
      cell(
        slide,
        `benchmark-right-${rowIndex}`,
        row.values[1],
        x + widths[0] + widths[1],
        cy,
        widths[2],
        h,
        { size: rightSize, line: BLACK },
      );
    }
    cy += h;
  });
  addNotes(slide, page.reference);
}

function addPrecautions(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  text(slide, "precautions-label", "注意事项：", 58, 100, 130, 36, {
    size: 20,
    color: WHITE,
    bold: true,
    align: "center",
    fill: GREEN,
  });

  const items = page.items;
  const listTop = 150;
  const listBottom = 680;
  const listBudget = listBottom - listTop;
  const itemH = Math.floor(listBudget / items.length);
  const fontSize = itemH < 55 ? 15 : itemH < 70 ? 17 : 19;

  items.forEach((item, index) => {
    text(
      slide,
      `precaution-item-${index}`,
      `${index + 1}、${item}`,
      58,
      listTop + index * itemH,
      575,
      itemH - 4,
      { size: fontSize },
    );
  });

  const gridX = 670;
  const gridY = 105;
  const gridW = 540;
  const gridH = 535;
  const gap = 6;
  const cellW = (gridW - gap) / 2;
  const cellH = (gridH - gap) / 2;
  page.illustration_slots.forEach((slot, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const sx = gridX + col * (cellW + gap);
    const sy = gridY + row * (cellH + gap);
    rect(slide, `precaution-card-${index}`, sx, sy, cellW, cellH, "#F5FBEC", GREEN, 3);
    text(
      slide,
      `precaution-card-title-${index}`,
      `！ ${slot.title}`,
      sx + 20,
      sy + 22,
      cellW - 40,
      38,
      { size: 20, bold: true, align: "center" },
    );
    assetSlot(
      slide,
      `precaution-asset-${index}`,
      `原创插图槽位\n${slot.title}`,
      sx + 35,
      sy + 76,
      cellW - 70,
      cellH - 105,
      index % 2 === 0 ? "#DDF6E9" : "#FFF4DB",
    );
  });
  addNotes(slide, page.reference);
}

const builders = {
  courseware_cover: addCover,
  product_overview: addOverview,
  combination_guidance: addCombination,
  product_benchmark: addBenchmark,
  precautions: addPrecautions,
};

for (const page of data.pages) {
  const builder = builders[page.scene_type];
  if (!builder) throw new Error(`Unsupported scene_type: ${page.scene_type}`);
  builder(page);
}

await fs.mkdir(qaDir, { recursive: true });
await fs.mkdir(path.dirname(outputPptx), { recursive: true });

for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(qaDir, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text());
}

const montage = await presentation.export({
  format: "webp",
  montage: true,
  scale: 1,
});
await fs.writeFile(
  path.join(qaDir, "deck-montage.webp"),
  new Uint8Array(await montage.arrayBuffer()),
);

const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,notes",
  maxChars: 30000,
});
await fs.writeFile(path.join(qaDir, "inspection.ndjson"), inspection.ndjson);

// 同步内容 JSON 到 validation 目录，便于后续改稿
await fs.copyFile(dataPath, path.join(outRoot, "content.json"));

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPptx);

// 后处理：注入中文字体 + 嵌入注意事项示例图
const post = spawnSync(
  "python3",
  [
    path.join(workDir, "postprocess-product-courseware-pptx.py"),
    outputPptx,
    "--assets-dir",
    path.join(outRoot, "assets/precautions"),
  ],
  { encoding: "utf8" },
);
if (post.status !== 0) {
  console.error(post.stdout);
  console.error(post.stderr);
  throw new Error(`postprocess failed with status ${post.status}`);
}

console.log(
  JSON.stringify(
    {
      pptx: outputPptx,
      slides: presentation.slides.items.length,
      combination_rows: data.pages.find((p) => p.scene_type === "combination_guidance")?.rows
        ?.length,
      qaDir,
      content: path.join(outRoot, "content.json"),
      postprocess: post.stdout.trim(),
    },
    null,
    2,
  ),
);
