import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const currentFile = fileURLToPath(import.meta.url);
const workDir = path.dirname(currentFile);
const projectDir = path.resolve(workDir, "..");
const repoDir = path.resolve(projectDir, "../..");
const data = JSON.parse(
  await fs.readFile(path.join(projectDir, "product-courseware-green.json"), "utf8"),
);

const outputPptx = path.join(
  repoDir,
  "production-library/validation/courseware/product-courseware-green-v1/金银花露_商品培训课件_品牌升级签样.pptx",
);
const qaDir = path.join(
  repoDir,
  "production-library/validation/courseware/product-courseware-green-v1/qa-brand-upgrade",
);

const W = 1280;
const H = 720;
const FONT = "PingFang SC";
const COLORS = {
  forest: "#005B37",
  brand: "#009944",
  fresh: "#65B83E",
  mint: "#E9F5EC",
  pale: "#F3F8F2",
  cream: "#F7F2E8",
  warm: "#FFFDF8",
  ink: "#17362B",
  muted: "#5C7169",
  line: "#C7DCCF",
  white: "#FFFFFF",
  gold: "#D5A72A",
  red: "#D64A3A",
};

const presentation = Presentation.create({
  slideSize: { width: W, height: H },
});

function shape(slide, name, geometry, x, y, width, height, fill, options = {}) {
  return slide.shapes.add({
    geometry,
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: {
      style: "solid",
      fill: options.line ?? "none",
      width: options.lineWidth ?? 0,
    },
    ...(options.radius ? { borderRadius: options.radius } : {}),
    ...(options.shadow ? { shadow: options.shadow } : {}),
  });
}

function box(slide, name, x, y, width, height, fill, options = {}) {
  return shape(
    slide,
    name,
    options.rounded ? "roundRect" : "rect",
    x,
    y,
    width,
    height,
    fill,
    options,
  );
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
    color = COLORS.ink,
    bold = false,
    align = "left",
    fill = "none",
    line = "none",
    lineWidth = 0,
  } = {},
) {
  const element = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  });
  element.text = value;
  element.text.style = {
    fontFamily: FONT,
    fontSize: size,
    color,
    bold,
    alignment: align,
  };
  return element;
}

function notes(slide, reference) {
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n- User-provided internal courseware screenshot: ${reference}\n- Content source: product-courseware-green.json; manual transcription pending pharmacist/compliance review.\n- Visual direction: user-approved brand-preserving design upgrade.\n[/Sources]`,
  );
  slide.speakerNotes.setVisible(true);
}

function chunk(items, size) {
  const result = [];
  for (let index = 0; index < items.length; index += size) {
    result.push(items.slice(index, index + size));
  }
  return result.length ? result : [[]];
}

function splitClaim(item) {
  const separator = item.indexOf("：");
  if (separator === -1) return { title: item, body: "" };
  return {
    title: item.slice(0, separator),
    body: item.slice(separator + 1),
  };
}

function addWordmark(slide, dark = false) {
  text(
    slide,
    "brand-wordmark",
    "大参林 dashenlin",
    1010,
    27,
    205,
    34,
    {
      size: 18,
      color: dark ? COLORS.white : COLORS.brand,
      bold: true,
      align: "right",
    },
  );
}

function addFooter(slide, dark = false) {
  text(
    slide,
    "internal-notice",
    data.brand.internal_notice,
    1060,
    683,
    170,
    22,
    {
      size: 13,
      color: dark ? "#D6E9DE" : COLORS.muted,
      align: "right",
    },
  );
}

function addHeader(slide, pageNumber, eyebrow, title) {
  slide.background.fill = COLORS.warm;
  box(slide, "header-brand-rail", 0, 0, 18, H, COLORS.brand);
  text(slide, "page-number", pageNumber, 52, 25, 70, 28, {
    size: 15,
    color: COLORS.brand,
    bold: true,
  });
  text(slide, "page-eyebrow", eyebrow, 125, 25, 410, 28, {
    size: 14,
    color: COLORS.muted,
    bold: true,
  });
  addWordmark(slide);
  text(slide, "page-title", title, 52, 74, 1080, 58, {
    size: 36,
    color: COLORS.ink,
    bold: true,
  });
  box(slide, "title-accent", 52, 140, 84, 5, COLORS.brand);
  addFooter(slide);
}

function assetSlot(slide, name, label, x, y, width, height) {
  box(slide, `${name}-shadow`, x + 8, y + 10, width, height, "#D8E8DD", {
    rounded: true,
    radius: "rounded-2xl",
  });
  box(slide, `${name}-surface`, x, y, width, height, COLORS.white, {
    rounded: true,
    radius: "rounded-2xl",
    line: COLORS.line,
    lineWidth: 1,
  });
  shape(
    slide,
    `${name}-halo`,
    "ellipse",
    x + width * 0.18,
    y + height * 0.19,
    width * 0.64,
    width * 0.64,
    COLORS.mint,
  );
  text(
    slide,
    `${name}-label`,
    label,
    x + 25,
    y + height / 2 - 35,
    width - 50,
    70,
    {
      size: 18,
      color: COLORS.forest,
      bold: true,
      align: "center",
    },
  );
}

function addCover(page) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.forest;

  shape(slide, "cover-orbit-large", "ellipse", 720, 0, 560, 560, "#08754C");
  shape(slide, "cover-orbit-small", "ellipse", 870, 0, 410, 410, COLORS.brand);
  box(slide, "cover-mint-band", 0, 620, W, 100, COLORS.mint);
  box(slide, "cover-gold-mark", 76, 90, 64, 6, COLORS.gold);
  text(slide, "cover-brand", "大参林医药集团", 76, 112, 330, 42, {
    size: 22,
    color: COLORS.white,
    bold: true,
  });
  text(slide, "cover-eyebrow", "商品知识 · 内部培训课件", 76, 210, 370, 36, {
    size: 18,
    color: "#CFE8D8",
    bold: true,
  });
  text(slide, "cover-title", page.title, 76, 258, 560, 100, {
    size: 64,
    color: COLORS.white,
    bold: true,
  });
  text(
    slide,
    "cover-subtitle",
    "从商品信息到销售应用，形成统一、清晰、可复用的培训表达",
    80,
    380,
    600,
    72,
    { size: 24, color: "#E1F0E7" },
  );
  text(slide, "cover-tagline", "专业力", 82, 520, 150, 48, {
    size: 28,
    color: COLORS.forest,
    bold: true,
    align: "center",
    fill: COLORS.cream,
  });

  assetSlot(
    slide,
    "cover-product-slot",
    "商品包装高清图\n接入后自动替换",
    850,
    166,
    278,
    365,
  );
  text(
    slide,
    "cover-version",
    "品牌化高级版签样",
    875,
    552,
    230,
    34,
    { size: 15, color: "#D6E9DE", bold: true, align: "center" },
  );
  addWordmark(slide, true);
  addFooter(slide, false);
  notes(slide, page.reference);
}

function addOverviewPage(page, sellingPoints, audiences, pageIndex, pageCount) {
  const slide = presentation.slides.add();
  addHeader(
    slide,
    pageCount > 1 ? `01.${pageIndex + 1}` : "01",
    "商品介绍 / 核心卖点 / 适宜人群",
    pageIndex === 0
      ? "温和、安全、好喝，是这款产品的核心销售逻辑"
      : "核心卖点与适宜人群（续）",
  );

  assetSlot(slide, "overview-product-slot", "商品包装高清图\n待接入", 52, 182, 295, 330);
  text(slide, "overview-product-name", page.product.display_name, 52, 530, 295, 36, {
    size: 24,
    color: COLORS.forest,
    bold: true,
    align: "center",
  });

  const facts = [
    ["编码", page.product.code],
    ["规格", page.product.specification],
    ["零售价", page.product.retail_price],
  ];
  facts.forEach(([label, value], index) => {
    const x = 52 + index * 98;
    text(slide, `fact-label-${index}`, label, x, 578, 90, 22, {
      size: 13,
      color: COLORS.muted,
      align: "center",
    });
    text(slide, `fact-value-${index}`, value, x, 603, 90, 28, {
      size: index === 0 ? 15 : 18,
      color: COLORS.ink,
      bold: true,
      align: "center",
    });
  });

  const rightX = 395;
  const rightW = 820;
  text(slide, "selling-point-label", "核心卖点", rightX, 178, 150, 32, {
    size: 17,
    color: COLORS.brand,
    bold: true,
  });

  sellingPoints.forEach((item, index) => {
    const parsed = splitClaim(item);
    const y = 222 + index * 103;
    text(slide, `selling-index-${index}`, String(index + 1 + pageIndex * 3).padStart(2, "0"), rightX, y, 52, 42, {
      size: 28,
      color: COLORS.fresh,
      bold: true,
    });
    text(slide, `selling-title-${index}`, parsed.title, rightX + 72, y, 680, 32, {
      size: 20,
      color: COLORS.ink,
      bold: true,
    });
    text(slide, `selling-body-${index}`, parsed.body, rightX + 72, y + 34, 700, 54, {
      size: 16,
      color: COLORS.muted,
    });
    box(slide, `selling-rule-${index}`, rightX + 72, y + 91, rightW - 72, 1, COLORS.line);
  });

  const audienceY = 540;
  text(slide, "audience-label", "适宜人群", rightX, audienceY, 150, 30, {
    size: 17,
    color: COLORS.brand,
    bold: true,
  });
  audiences.forEach((item, index) => {
    const x = rightX + index * 265;
    box(slide, `audience-mark-${index}`, x, audienceY + 44, 8, 54, COLORS.brand);
    text(slide, `audience-item-${index}`, item.replace(/[；。]$/, ""), x + 20, audienceY + 41, 235, 60, {
      size: 17,
      color: COLORS.ink,
      bold: true,
    });
  });
  notes(slide, page.reference);
}

function addCombinationPage(page, rows, pageIndex, pageCount) {
  const slide = presentation.slides.add();
  addHeader(
    slide,
    pageCount > 1 ? `02.${pageIndex + 1}` : "02",
    "联合用药 / 场景判断 / 销售话术",
    pageIndex === 0
      ? "联合用药不是堆产品，而是围绕症状建立清晰分工"
      : "联合用药场景（续）",
  );

  text(slide, "combination-column-1", "应用场景", 56, 173, 180, 28, {
    size: 14,
    color: COLORS.muted,
    bold: true,
  });
  text(slide, "combination-column-2", "商品组合", 270, 173, 270, 28, {
    size: 14,
    color: COLORS.muted,
    bold: true,
  });
  text(slide, "combination-column-3", "销售逻辑", 610, 173, 540, 28, {
    size: 14,
    color: COLORS.muted,
    bold: true,
  });

  rows.forEach((row, index) => {
    const y = 208 + index * 151;
    box(
      slide,
      `combination-row-${index}`,
      52,
      y,
      1165,
      132,
      index === 1 ? COLORS.mint : COLORS.white,
      {
        rounded: true,
        radius: "rounded-xl",
        line: COLORS.line,
        lineWidth: 1,
      },
    );
    box(slide, `combination-accent-${index}`, 52, y, 8, 132, COLORS.brand, {
      rounded: true,
      radius: "rounded-xl",
    });
    text(slide, `combination-scenario-${index}`, row.scenario, 78, y + 28, 165, 80, {
      size: 18,
      color: COLORS.ink,
      bold: true,
    });
    text(slide, `combination-name-${index}`, row.combination, 270, y + 24, 275, 76, {
      size: 18,
      color: COLORS.forest,
      bold: true,
    });
    text(
      slide,
      `combination-asset-note-${index}`,
      "包装素材接入后自动替换",
      270,
      y + 94,
      260,
      22,
      { size: 12, color: COLORS.muted },
    );
    text(slide, `combination-talk-${index}`, row.talk_track, 610, y + 23, 570, 90, {
      size: 16,
      color: COLORS.ink,
    });
  });

  text(
    slide,
    "combination-footnote",
    "正式用药逻辑与销售话术以内部药师及合规审核稿为准",
    52,
    668,
    650,
    22,
    { size: 12, color: COLORS.muted },
  );
  notes(slide, page.reference);
}

const cover = data.pages.find((page) => page.scene_type === "courseware_cover");
const overview = data.pages.find((page) => page.scene_type === "product_overview");
const combinations = data.pages.find(
  (page) => page.scene_type === "combination_guidance",
);
if (!cover || !overview || !combinations) {
  throw new Error("Required cover, overview, or combination page is missing.");
}

addCover(cover);

const sellingSection = overview.sections.find((section) =>
  section.title.includes("核心卖点"),
);
const audienceSection = overview.sections.find((section) =>
  section.title.includes("适宜人群"),
);
const sellingChunks = chunk(sellingSection?.items ?? [], 3);
const audienceChunks = chunk(audienceSection?.items ?? [], 3);
const overviewPageCount = Math.max(sellingChunks.length, audienceChunks.length);
for (let index = 0; index < overviewPageCount; index += 1) {
  addOverviewPage(
    overview,
    sellingChunks[index] ?? [],
    audienceChunks[index] ?? [],
    index,
    overviewPageCount,
  );
}

const combinationChunks = chunk(combinations.rows, 3);
combinationChunks.forEach((rows, index) =>
  addCombinationPage(combinations, rows, index, combinationChunks.length),
);

await fs.mkdir(qaDir, { recursive: true });
await fs.mkdir(path.dirname(outputPptx), { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(
    path.join(qaDir, `${stem}.png`),
    new Uint8Array(await png.arrayBuffer()),
  );
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

console.log(
  JSON.stringify(
    {
      pptx: outputPptx,
      slides: presentation.slides.items.length,
      qaDir,
      adaptiveRules: {
        sellingPointsPerPage: 3,
        audiencesPerPage: 3,
        combinationRowsPerPage: 3,
      },
    },
    null,
    2,
  ),
);
