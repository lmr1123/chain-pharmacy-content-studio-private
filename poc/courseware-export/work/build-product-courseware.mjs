import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const currentFile = fileURLToPath(import.meta.url);
const workDir = path.dirname(currentFile);
const projectDir = path.resolve(workDir, "..");
const repoDir = path.resolve(projectDir, "../..");
const dataPath = path.join(projectDir, "product-courseware-green.json");
// --out / --qa：默认 settled；升级迭代改道 validation，避免误覆盖已签样金样。
function cliValue(flag) {
  const index = process.argv.indexOf(flag);
  return index >= 0 && process.argv[index + 1] ? path.resolve(process.argv[index + 1]) : null;
}
const outputPptx =
  cliValue("--out") ??
  path.join(
    repoDir,
    "production-library/templates/settled/product-courseware-green-v1/金银花露_商品培训课件_复刻验证.pptx",
  );
const qaDir =
  cliValue("--qa") ??
  path.join(
    repoDir,
    "production-library/validation/courseware/product-courseware-green-v1/qa",
  );

const data = JSON.parse(await fs.readFile(dataPath, "utf8"));
const TOTAL_PAGES = data.pages.length;

const W = 1280;
const H = 720;
// 企业内训 PPT 统一微软雅黑；导出后再 postprocess 注入 OOXML typeface
const FONT = "Microsoft YaHei";
// 品牌绿色阶（与穿心莲 courseware2 视觉升级 token 对齐）
const GREEN = data.brand.primary; // 主色 #009900
const GREEN_DEEP = "#066A2F"; // 标题/重强调/表头
const GREEN_2 = data.brand.secondary; // #45A817
const MINT = "#E9F7EE"; // 卡片/总结条浅底
const PALE = "#F4FAF5"; // 斑马纹/更浅底
// 中性色阶
const INK = "#1F2A24"; // 正文
const MUTED = "#5A6B61"; // 辅助说明
const LINE = "#D9E9DF"; // 细分隔线/边框
// 语义色
const RED = "#E60012"; // 仅禁忌/警示/卖点红字
const BLUE = "#176A91"; // 封面建筑区保留
const SOFT_YELLOW = "#FFF3C4"; // 卖点高亮（替代刺眼 #FFF200）
const WHITE = "#FFFFFF";
const BLACK = INK;
const LIGHT = PALE; // 兼容旧斑马命名

const presentation = Presentation.create({
  slideSize: { width: W, height: H },
});

function rect(slide, name, x, y, width, height, fill, line = "none", lineWidth = 0, opts = {}) {
  const { radius = 0, shadow } = opts;
  return slide.shapes.add({
    geometry: radius > 0 ? "roundRect" : "rect",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
    ...(radius > 0 ? { borderRadius: radius } : {}),
    ...(shadow ? { shadow } : {}),
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
    vAlign,
    fill = "none",
    line = "none",
    lineWidth = 0,
    radius = 0,
  } = {},
) {
  const shape = slide.shapes.add({
    geometry: radius > 0 ? "roundRect" : "textbox",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
    ...(radius > 0 ? { borderRadius: radius } : {}),
  });
  shape.text = value;
  shape.text.style = {
    fontFamily: FONT,
    fontSize: size,
    color,
    bold,
    alignment: align,
    ...(vAlign ? { verticalAlignment: vAlign } : {}),
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
    line = LINE,
    lineWidth = 1,
  } = {},
) {
  rect(slide, `${name}-surface`, x, y, width, height, fill, line, lineWidth);
  return text(slide, `${name}-text`, value, x + 8, y, width - 16, height, {
    size,
    color,
    bold,
    align,
    vAlign: "middle",
  });
}

function addNotes(slide, reference) {
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n- User-provided internal reference screenshot: ${reference}\n- Content status: manual transcription; pharmacist/compliance review required.\n[/Sources]`,
  );
  slide.speakerNotes.setVisible(true);
}

function addFooter(slide, { showIndex = false } = {}) {
  const pageNo = presentation.slides.items.length;
  text(slide, "internal-notice", data.brand.internal_notice, 1010, 688, 160, 22, {
    size: 12,
    color: MUTED,
    align: "right",
  });
  if (showIndex) {
    text(
      slide,
      "page-index",
      `${String(pageNo).padStart(2, "0")} / ${String(TOTAL_PAGES).padStart(2, "0")}`,
      1180,
      688,
      64,
      22,
      { size: 12, color: MUTED, align: "right" },
    );
  }
}

function addPageChrome(slide, page) {
  slide.background.fill = WHITE;
  if (page.page_number) {
    rect(slide, "page-number-block", 32, 18, 64, 42, GREEN_DEEP, "none", 0, { radius: 10 });
    text(slide, "page-number", page.page_number, 32, 18, 64, 42, {
      size: 21,
      color: WHITE,
      bold: true,
      align: "center",
      vAlign: "middle",
    });
  }
  text(slide, "page-title", page.title, 114, 14, 900, 50, {
    size: 27,
    color: INK,
    bold: true,
    vAlign: "middle",
  });
  rect(slide, "chrome-hairline", 32, 73, 1216, 1, LINE);
  rect(slide, "chrome-rule-accent", 114, 70, 72, 5, GREEN, "none", 0, { radius: 2 });
  text(slide, "brand-wordmark", data.brand.display_name || "大参林 dashenlin", 1080, 18, 164, 40, {
    size: 14,
    color: GREEN_2,
    bold: true,
    align: "right",
  });
  addFooter(slide, { showIndex: true });
}

function assetSlot(slide, name, label, x, y, width, height, fill = MINT) {
  rect(slide, `${name}-surface`, x, y, width, height, fill, LINE, 1, { radius: 10 });
  text(slide, `${name}-label`, label, x + 10, y + height / 2 - 25, width - 20, 50, {
    size: 15,
    color: MUTED,
    bold: true,
    align: "center",
    vAlign: "middle",
  });
}

/** 薄荷底 + 绿左条 callout（总结条/卖点条） */
function callout(slide, name, value, x, y, width, height, options = {}) {
  const { fill, color = WHITE, size = 18, bold = true } = options;
  const mintMode = fill === undefined;
  const surface = mintMode ? MINT : fill;
  const textColor = mintMode ? INK : color;
  rect(slide, `${name}-surface`, x, y, width, height, surface, "none", 0, { radius: 10 });
  if (mintMode) {
    rect(slide, `${name}-accent`, x + 8, y + 10, 4, height - 20, GREEN, "none", 0, { radius: 2 });
  }
  const insetX = mintMode ? 24 : 14;
  text(slide, name, value, x + insetX, y, width - insetX - 14, height, {
    size,
    color: textColor,
    bold,
    vAlign: "middle",
  });
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
  text(slide, "cover-title", page.title, 400, 250, 480, 105, {
    size: 64,
    color: WHITE,
    bold: true,
    align: "center",
  });
  text(slide, "cover-tagline", page.tagline, 550, 542, 180, 40, {
    size: 22,
    color: WHITE,
    bold: true,
    align: "center",
    fill: GREEN_DEEP,
    radius: 8,
    vAlign: "middle",
  });
  addFooter(slide, { showIndex: true });
  addNotes(slide, page.reference);
}

function addOverview(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  assetSlot(slide, "primary-packshot", "商品包装高清图\n待接入", 145, 92, 205, 260);
  text(slide, "product-name", page.product.display_name, 130, 365, 240, 34, {
    size: 22,
    color: RED,
    bold: true,
    align: "center",
    vAlign: "middle",
  });

  const tableX = 38;
  const tableY = 420;
  const widths = [120, 82, 153, 112];
  const headers = ["编码", "主推", "规格", "零售价"];
  let cursorX = tableX;
  headers.forEach((header, index) => {
    cell(slide, `product-table-head-${index}`, header, cursorX, tableY, widths[index], 48, {
      fill: GREEN_DEEP,
      color: WHITE,
      size: 18,
      bold: true,
      line: LINE,
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
    cell(
      slide,
      `product-table-value-${index}`,
      value,
      cursorX,
      tableY + 48,
      widths[index],
      56,
      { size: index === 0 ? 16 : 19, fill: index % 2 === 0 ? WHITE : PALE, line: LINE },
    );
    cursorX += widths[index];
  });

  callout(
    slide,
    "selling-point",
    `一句话卖点：${page.product.one_line_selling_point}`,
    38,
    544,
    467,
    120,
    { fill: SOFT_YELLOW, color: INK, size: 20, bold: true },
  );

  const sectionX = 525;
  const sectionW = 710;
  let y = 102;
  const sectionHeights = [136, 250, 175];
  page.sections.forEach((section, sectionIndex) => {
    text(
      slide,
      `section-title-${sectionIndex}`,
      section.title,
      sectionX,
      y,
      170,
      34,
      {
        size: 20,
        color: WHITE,
        bold: true,
        align: "center",
        fill: GREEN_DEEP,
        radius: 8,
        vAlign: "middle",
      },
    );
    y += 39;
    section.items.forEach((item, itemIndex) => {
      const itemHeight = sectionIndex === 1 ? 61 : 36;
      text(
        slide,
        `section-${sectionIndex}-item-${itemIndex}`,
        `${itemIndex + 1}、${item}`,
        sectionX,
        y,
        sectionW,
        itemHeight,
        {
          size: sectionIndex === 1 ? 17 : 18,
          color: INK,
          bold: sectionIndex === 1,
          vAlign: "middle",
        },
      );
      y += itemHeight;
    });
    y = 102 + sectionHeights.slice(0, sectionIndex + 1).reduce((a, b) => a + b, 0);
  });
  addNotes(slide, page.reference);
}

/**
 * 联合用药页（内容驱动行数）：
 * | 应用场景 | 联合用药 | 联合商品图(每行) | 本品图(纵向合并) | 销售话术 |
 * 每行搭档包装独立成列；本品在旁侧合并列贯穿全部行，保证「每一行都与本品关联」。
 */
function addCombination(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  const x = 28;
  const y = 96;
  const headerH = 58;
  const rowCount = page.rows.length;
  if (rowCount < 1) throw new Error("combination_guidance requires at least 1 row");

  // 五列：场景 | 联合用药 | 联合商品图 | 本品(合并) | 话术
  const widths = [150, 175, 230, 200, 465];
  const headers = page.columns?.length === 5
    ? page.columns
    : [
        "应用场景（适宜人群）",
        "联合用药",
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
      fill: GREEN_DEEP,
      color: WHITE,
      size: index <= 1 ? 15 : 16,
      bold: true,
      line: LINE,
    });
    cx += widths[index];
  });

  const bodyTop = y + headerH;
  const bodyH = rowHeights.reduce((a, b) => a + b, 0);
  const primaryLabel =
    page.primary_pack_label ||
    page.primary_product_label ||
    "本品包装图\n待接入";

  let cy = bodyTop;
  page.rows.forEach((row, rowIndex) => {
    const h = rowHeights[rowIndex];
    const fill = rowIndex % 2 === 1 ? PALE : WHITE;
    const talkSize = (row.talk_track || "").length > 95 ? 14 : 15;

    cell(slide, `combination-scenario-${rowIndex}`, row.scenario, x, cy, widths[0], h, {
      fill,
      size: 15,
      bold: true,
      align: "left",
      line: LINE,
    });
    cell(
      slide,
      `combination-name-${rowIndex}`,
      row.combination,
      x + widths[0],
      cy,
      widths[1],
      h,
      { fill, size: 15, bold: true, align: "left", line: LINE },
    );

    // 每行：联合商品图（独立列）
    rect(
      slide,
      `combination-partner-surface-${rowIndex}`,
      x + widths[0] + widths[1],
      cy,
      widths[2],
      h,
      fill,
      LINE,
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
      MINT,
    );

    // 行分隔线仍画在本品列背景上（合并列本体在循环外绘制）
    cell(
      slide,
      `combination-talk-${rowIndex}`,
      row.talk_track,
      x + widths[0] + widths[1] + widths[2] + widths[3],
      cy,
      widths[4],
      h,
      { fill, size: talkSize, align: "left", line: LINE },
    );
    cy += h;
  });

  // 本品合并列：整块背景 + 居中包装槽 + 红色「+」示意关联
  const primaryX = x + widths[0] + widths[1] + widths[2];
  rect(
    slide,
    "combination-primary-merge-surface",
    primaryX,
    bodyTop,
    widths[3],
    bodyH,
    MINT,
    LINE,
    1,
  );
  // 左侧细竖线分隔，强调「每行搭档 + 共用本品」
  rect(slide, "combination-primary-divider", primaryX, bodyTop, 3, bodyH, GREEN);

  text(
    slide,
    "combination-plus",
    "+",
    primaryX + 8,
    bodyTop + bodyH / 2 - 28,
    40,
    56,
    { size: 40, color: RED, bold: true, align: "center", vAlign: "middle" },
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
    WHITE,
  );

  addNotes(slide, page.reference);
}

function addBenchmark(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  const x = 45;
  const y = 105;
  const widths = [180, 530, 490];
  const rowHeights = [62, 190, 72, 72, 72, 90];
  let cx = x;
  page.columns.forEach((header, index) => {
    cell(slide, `benchmark-head-${index}`, header, cx, y, widths[index], rowHeights[0], {
      fill: GREEN_DEEP,
      color: WHITE,
      size: 18,
      bold: true,
      line: LINE,
    });
    cx += widths[index];
  });

  let cy = y + rowHeights[0];
  page.rows.forEach((row, rowIndex) => {
    const h = rowHeights[rowIndex + 1];
    const zebra = rowIndex % 2 === 1 ? PALE : WHITE;
    cell(slide, `benchmark-label-${rowIndex}`, row.label, x, cy, widths[0], h, {
      fill: MINT,
      bold: true,
      size: 17,
      line: LINE,
    });
    if (row.label === "产品展示") {
      rect(slide, "benchmark-product-left-cell", x + widths[0], cy, widths[1], h, WHITE, LINE, 1);
      rect(
        slide,
        "benchmark-product-right-cell",
        x + widths[0] + widths[1],
        cy,
        widths[2],
        h,
        WHITE,
        LINE,
        1,
      );
      assetSlot(
        slide,
        "benchmark-primary-packshot",
        "可可康包装图\n待接入",
        x + widths[0] + 195,
        cy + 18,
        140,
        h - 36,
      );
      assetSlot(
        slide,
        "benchmark-competitor-packshot",
        "竞品包装图\n待接入",
        x + widths[0] + widths[1] + 175,
        cy + 18,
        140,
        h - 36,
        PALE,
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
        {
          fill: zebra,
          size: 17,
          bold: row.label === "共有优势",
          line: LINE,
        },
      );
    } else {
      cell(
        slide,
        `benchmark-left-${rowIndex}`,
        row.values[0],
        x + widths[0],
        cy,
        widths[1],
        h,
        {
          fill: zebra,
          size: 17,
          color: row.label === "卖点差异" ? RED : BLACK,
          bold: row.label === "卖点差异",
          line: LINE,
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
        { fill: zebra, size: 17, line: LINE },
      );
    }
    cy += h;
  });
  addNotes(slide, page.reference);
}

function addPrecautions(page) {
  const slide = presentation.slides.add();
  addPageChrome(slide, page);

  text(slide, "precautions-label", "注意事项：", 58, 126, 130, 38, {
    size: 20,
    color: WHITE,
    bold: true,
    align: "center",
    fill: GREEN_DEEP,
    radius: 8,
    vAlign: "middle",
  });
  let y = 185;
  page.items.forEach((item, index) => {
    const h = index === 3 || index === 4 ? 105 : 65;
    text(slide, `precaution-item-${index}`, `${index + 1}、${item}`, 58, y, 565, h, {
      size: 19,
      color: INK,
      vAlign: "middle",
    });
    y += h;
  });

  const gridX = 670;
  const gridY = 105;
  const gridW = 540;
  const gridH = 535;
  const gap = 10;
  const cellW = (gridW - gap) / 2;
  const cellH = (gridH - gap) / 2;
  page.illustration_slots.forEach((slot, index) => {
    const col = index % 2;
    const row = Math.floor(index / 2);
    const sx = gridX + col * (cellW + gap);
    const sy = gridY + row * (cellH + gap);
    rect(slide, `precaution-card-${index}`, sx, sy, cellW, cellH, MINT, LINE, 1, { radius: 12 });
    rect(slide, `precaution-card-accent-${index}`, sx + 10, sy + 16, 4, 24, GREEN, "none", 0, {
      radius: 2,
    });
    text(slide, `precaution-card-title-${index}`, slot.title, sx + 24, sy + 14, cellW - 40, 38, {
      size: 20,
      color: GREEN_DEEP,
      bold: true,
      vAlign: "middle",
    });
    assetSlot(
      slide,
      `precaution-asset-${index}`,
      `原创插图槽位\n${slot.title}`,
      sx + 28,
      sy + 64,
      cellW - 56,
      cellH - 86,
      index % 2 === 0 ? WHITE : SOFT_YELLOW,
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

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPptx);

// 注入微软雅黑 typeface（artifact-tool 默认不写字体）
const post = spawnSync(
  "python3",
  [path.join(workDir, "postprocess-product-courseware-pptx.py"), outputPptx],
  { encoding: "utf8" },
);
if (post.status !== 0) {
  console.error(post.stdout);
  console.error(post.stderr);
  throw new Error(`postprocess failed with status ${post.status}`);
}

console.log(JSON.stringify({
  pptx: outputPptx,
  slides: presentation.slides.items.length,
  qaDir,
  visual_tokens: "courseware2-upgrade-v2 (GREEN_DEEP/MINT/PALE/INK/MUTED/LINE)",
  combination_layout: "partner-per-row + primary-merged-column",
  postprocess: post.stdout.trim(),
}, null, 2));
