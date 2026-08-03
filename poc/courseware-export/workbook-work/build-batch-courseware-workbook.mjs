import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repoDir = "/Users/liminrong/Projects/chain-pharmacy-content-studio";
const outputDir = path.join(repoDir, "outputs/batch-courseware");
const manifestDir = path.join(outputDir, "manifests");
const qaDir = path.join(
  repoDir,
  "production-library/validation/courseware/product-courseware-green-v1/qa-batch-workbook",
);
const workbookPath = path.join(outputDir, "商品培训课件_批量导入模板.xlsx");

const COLORS = {
  green: "#009900",
  deepGreen: "#006B3C",
  lightGreen: "#E7F3E2",
  input: "#FFF4CC",
  header: "#F3F7F1",
  line: "#C7D8C2",
  white: "#FFFFFF",
  text: "#1B2E24",
  muted: "#5D6D64",
  red: "#C62828",
};

const mainRows = [
  [
    "P001",
    "是",
    "金银花露（可可康）",
    "大参林",
    "2429715",
    "A",
    "265ml",
    9.9,
    "asset://product-packshot-primary",
    "cover.company-locked-v1",
    "PPTX+PDF",
    "reference-transcription-review-required",
  ],
  [
    "DEMO002",
    "是",
    "示例商品B（仅演示结构）",
    "大参林",
    "DEMO002",
    "B",
    "示例规格",
    0,
    "asset://demo-product-b",
    "cover.company-locked-v1",
    "PPTX",
    "demo-not-for-production",
  ],
];

const introRows = [
  ["P001", 1, "主要成分", "金银花"],
  ["P001", 2, "功能主治", "清热解毒。用于小儿痱毒，暑热口渴"],
  ["P001", 3, "用法用量", "口服。一次60～120毫升，一日2～3次。"],
  ["DEMO002", 1, "商品介绍字段1", "请替换为内部审核内容"],
  ["DEMO002", 2, "商品介绍字段2", "第二个商品可以只有两条介绍"],
];

const sellingRows = [
  [
    "P001",
    1,
    "专为小儿体质设计，温和不伤胃",
    "单方金银花制剂，药性平和，清热去火不损伤婴幼儿娇嫩肠胃。",
  ],
  ["P001", 2, "药食同源，安全无添加", "无添加色素，药食同源。"],
  [
    "P001",
    3,
    "靶向解决小儿夏季常见问题",
    "精准应对痱毒、暑热口渴、小便黄、咽喉不适等夏季上火症状，一瓶多效。",
  ],
  ["DEMO002", 1, "示例卖点1", "请替换为审核后的卖点内容。"],
  ["DEMO002", 2, "示例卖点2", "不同商品的卖点数量可以不同。"],
  ["DEMO002", 3, "示例卖点3", "前三条进入01页第一张。"],
  ["DEMO002", 4, "示例卖点4", "第四条开始自动复制原布局续页。"],
  ["DEMO002", 5, "示例卖点5", "不会缩小到不可读，也不会切换新布局。"],
];

const audienceRows = [
  ["P001", 1, "夏季易生痱子的幼儿"],
  ["P001", 2, "上火症状明显的儿童"],
  ["P001", 3, "暑热烦渴、食欲不振的儿童"],
  ["DEMO002", 1, "示例适宜人群1"],
  ["DEMO002", 2, "示例适宜人群2"],
  ["DEMO002", 3, "示例适宜人群3"],
  ["DEMO002", 4, "示例适宜人群4（触发续页）"],
];

const combinationRows = [
  [
    "P001",
    1,
    "风热感冒引起的咽喉肿痛",
    "小儿咽扁颗粒",
    "asset://partner-xiaoer-yanbian",
    "小儿咽扁颗粒直击咽喉炎症，金银花露清解内热；二者联用，内外兼治。",
  ],
  [
    "P001",
    2,
    "风热感冒引起的发热、鼻塞流涕",
    "小儿氨酚黄那敏颗粒",
    "asset://partner-xiaoer-anfen",
    "一个缓解外在症状，一个清解内热，帮助快速缓解不适。",
  ],
  [
    "P001",
    3,
    "风热/肺热引起的咳嗽",
    "氨溴特罗口服溶液",
    "asset://partner-ambroxol-clenbuterol",
    "氨溴特罗化痰止咳，金银花露清肺消炎；两个搭配使用。",
  ],
  [
    "DEMO002",
    1,
    "示例应用场景",
    "示例联合商品",
    "asset://demo-partner",
    "请替换为内部药师及合规审核后的联合用药逻辑和销售话术。",
  ],
];

const benchmarkRows = [
  ["P001", 1, "金银花露（小葵花露-葵花药业）", "功效主治", "清热解毒。用于小儿痱毒，暑热口渴"],
  ["P001", 2, "金银花露（小葵花露-葵花药业）", "共有优势", "清甜好喝不抗拒，防漏瓶盖不浪费"],
  ["P001", 3, "金银花露（小葵花露-葵花药业）", "零售价", "13.3元（250ml）"],
  ["P001", 4, "金银花露（小葵花露-葵花药业）", "卖点差异", "性价比高；毛利率高"],
  ["DEMO002", 1, "示例竞品", "示例维度", "请替换为审核后的对标内容"],
];

const precautionRows = [
  ["P001", 1, "服药时饮食宜清淡。"],
  ["P001", 2, "服用本药时，不宜同时服滋补性中成药。"],
  ["P001", 3, "脾虚大便溏者慎服。"],
  ["P001", 4, "服用3天后症状无改善，或出现其他严重症状时应停药并就诊。"],
  ["P001", 5, "对本品过敏者禁用，过敏体质者慎用。"],
  ["DEMO002", 1, "示例注意事项1"],
  ["DEMO002", 2, "示例注意事项2"],
];

const assetRows = [
  ["cover.company-locked-v1", "GLOBAL", "公司封面PPTX", "待提供原始PPTX路径", "是", "待接入", "封面布局锁定，不得重建"],
  ["asset://product-packshot-primary", "P001", "商品包装", "待提供高清原图路径", "是", "待接入", "01页及02页商品展示"],
  ["asset://partner-xiaoer-yanbian", "P001", "联合商品包装", "待提供高清原图路径", "是", "待接入", "02页第1行"],
  ["asset://partner-xiaoer-anfen", "P001", "联合商品包装", "待提供高清原图路径", "是", "待接入", "02页第2行"],
  ["asset://partner-ambroxol-clenbuterol", "P001", "联合商品包装", "待提供高清原图路径", "是", "待接入", "02页第3行"],
  ["asset://demo-product-b", "DEMO002", "商品包装", "示例路径", "是", "示例", "仅演示结构"],
  ["asset://demo-partner", "DEMO002", "联合商品包装", "示例路径", "是", "示例", "仅演示结构"],
];

function styleHeader(range) {
  range.format = {
    fill: COLORS.green,
    font: { bold: true, color: COLORS.white },
    verticalAlignment: "center",
    horizontalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: COLORS.line },
  };
  range.format.rowHeight = 34;
}

function styleInputBody(range) {
  range.format = {
    fill: COLORS.input,
    font: { color: COLORS.text },
    verticalAlignment: "top",
    horizontalAlignment: "left",
    wrapText: true,
    borders: {
      insideHorizontal: { style: "thin", color: COLORS.line },
      bottom: { style: "thin", color: COLORS.line },
    },
  };
}

function addDataSheet(workbook, name, headers, rows, widths, tableName) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  const endCol = String.fromCharCode(64 + headers.length);
  sheet.getRange(`A1:${endCol}${rows.length + 1}`).values = [headers, ...rows];
  styleHeader(sheet.getRange(`A1:${endCol}1`));
  styleInputBody(sheet.getRange(`A2:${endCol}${rows.length + 1}`));
  widths.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, rows.length + 1, 1).format.columnWidth = width;
  });
  sheet.getRange(`A2:${endCol}${rows.length + 1}`).format.autofitRows();
  const table = sheet.tables.add(`A1:${endCol}${rows.length + 1}`, true, tableName);
  table.style = "TableStyleMedium4";
  table.showBandedColumns = false;
  return sheet;
}

const workbook = Workbook.create();

const instructions = workbook.worksheets.add("使用说明");
instructions.showGridLines = false;
instructions.getRange("A1:F2").merge();
instructions.getRange("A1").values = [["商品培训课件批量导入模板"]];
instructions.getRange("A1:F2").format = {
  fill: COLORS.deepGreen,
  font: { color: COLORS.white, bold: true, size: 20 },
  verticalAlignment: "center",
  horizontalAlignment: "left",
};
instructions.getRange("A4:B11").values = [
  ["使用顺序", "说明"],
  ["1", "先在“商品主表”增加商品，一行一个商品，product_id 必须唯一。"],
  ["2", "商品介绍、核心卖点、适宜人群、联合用药等均在对应子表中一行写一条，通过 product_id 关联。"],
  ["3", "不要把多个卖点或多类人群塞进同一个单元格；条目数量不同是允许的。"],
  ["4", "01页固定保留商品介绍、核心卖点、适宜人群；卖点或人群超过3项时复制原版式续页。"],
  ["5", "02页固定保留应用场景、联合用药、产品图片展示、销售话术；超过3行时复制原版式续页。"],
  ["6", "公司封面布局锁定。精确生成前必须提供原始公司PPTX，生成器复制源页面，不重新设计。"],
  ["7", "黄色单元格为输入区；正式药品内容必须使用内部药师及合规审核稿。"],
];
styleHeader(instructions.getRange("A4:B4"));
instructions.getRange("A5:B11").format = {
  fill: COLORS.header,
  font: { color: COLORS.text },
  wrapText: true,
  verticalAlignment: "top",
  borders: { preset: "all", style: "thin", color: COLORS.line },
};
instructions.getRange("A:A").format.columnWidth = 12;
instructions.getRange("B:B").format.columnWidth = 90;
instructions.getRange("A5:B11").format.autofitRows();
instructions.getRange("D4:F9").values = [
  ["固定页面", "容量规则", "超量处理"],
  ["封面", "1页", "复制公司源页面，只替换允许字段"],
  ["01 商品页", "卖点≤3、人群≤3", "生成01-2、01-3续页"],
  ["02 联合用药", "每页≤3行", "生成02-2、02-3续页"],
  ["03 品种对标", "按参考表格容量", "复制03页续页"],
  ["04 注意事项", "每页≤5条", "复制04页续页"],
];
styleHeader(instructions.getRange("D4:F4"));
instructions.getRange("D5:F9").format = {
  fill: COLORS.lightGreen,
  font: { color: COLORS.text },
  wrapText: true,
  verticalAlignment: "top",
  borders: { preset: "all", style: "thin", color: COLORS.line },
};
instructions.getRange("D:D").format.columnWidth = 22;
instructions.getRange("E:E").format.columnWidth = 24;
instructions.getRange("F:F").format.columnWidth = 34;
instructions.freezePanes.freezeRows(2);

const main = addDataSheet(
  workbook,
  "商品主表",
  [
    "product_id",
    "生成开关",
    "商品名称",
    "品牌名称",
    "商品编码",
    "主推",
    "规格",
    "零售价",
    "商品主图asset_id",
    "封面模板ID",
    "输出格式",
    "审核版本",
  ],
  mainRows,
  [16, 12, 30, 18, 16, 10, 15, 12, 30, 28, 15, 34],
  "ProductsTable",
);
main.getRange("B2:B200").dataValidation = {
  rule: { type: "list", values: ["是", "否"] },
};
main.getRange("K2:K200").dataValidation = {
  rule: { type: "list", values: ["PPTX", "PDF", "PPTX+PDF"] },
};
main.getRange("H2:H200").format.numberFormat = '0.0"元"';

addDataSheet(
  workbook,
  "商品介绍",
  ["product_id", "顺序", "字段名称", "内容"],
  introRows,
  [16, 10, 26, 75],
  "IntroductionTable",
);
addDataSheet(
  workbook,
  "核心卖点",
  ["product_id", "顺序", "卖点标题", "卖点内容"],
  sellingRows,
  [16, 10, 38, 82],
  "SellingPointsTable",
);
addDataSheet(
  workbook,
  "适宜人群",
  ["product_id", "顺序", "人群描述"],
  audienceRows,
  [16, 10, 80],
  "AudiencesTable",
);
addDataSheet(
  workbook,
  "联合用药",
  ["product_id", "顺序", "应用场景", "联合商品", "联合商品asset_id", "销售话术"],
  combinationRows,
  [16, 10, 34, 30, 32, 82],
  "CombinationsTable",
);
addDataSheet(
  workbook,
  "品种对标",
  ["product_id", "顺序", "竞品名称", "对比维度", "对比内容"],
  benchmarkRows,
  [16, 10, 40, 24, 72],
  "BenchmarksTable",
);
addDataSheet(
  workbook,
  "注意事项",
  ["product_id", "顺序", "注意事项"],
  precautionRows,
  [16, 10, 90],
  "PrecautionsTable",
);
const assets = addDataSheet(
  workbook,
  "素材表",
  ["asset_id", "product_id", "素材类型", "文件路径", "是否必需", "状态", "用途"],
  assetRows,
  [36, 16, 24, 48, 14, 14, 44],
  "AssetsTable",
);
assets.getRange("E2:E200").dataValidation = {
  rule: { type: "list", values: ["是", "否"] },
};
assets.getRange("F2:F200").dataValidation = {
  rule: { type: "list", values: ["已就绪", "待接入", "示例"] },
};

const checks = workbook.worksheets.add("生成检查");
checks.showGridLines = false;
checks.freezePanes.freezeRows(1);
checks.getRange("A1:K3").values = [
  [
    "product_id",
    "商品名称",
    "商品介绍条数",
    "核心卖点条数",
    "适宜人群条数",
    "联合用药条数",
    "预计01页数",
    "预计02页数",
    "缺少必需素材",
    "结构校验",
    "素材状态",
  ],
  ["P001", null, null, null, null, null, null, null, null, null, null],
  ["DEMO002", null, null, null, null, null, null, null, null, null, null],
];
styleHeader(checks.getRange("A1:K1"));
checks.getRange("A2:A3").format = {
  fill: COLORS.input,
  font: { color: COLORS.text, bold: true },
};
checks.getRange("B2:K3").format = {
  fill: COLORS.header,
  font: { color: COLORS.text },
  wrapText: true,
  borders: { preset: "all", style: "thin", color: COLORS.line },
};

for (let row = 2; row <= 3; row += 1) {
  checks.getRange(`B${row}`).formulas = [[`=IFERROR(INDEX('商品主表'!$C$2:$C$200,MATCH(A${row},'商品主表'!$A$2:$A$200,0)),"")`]];
  checks.getRange(`C${row}`).formulas = [[`=COUNTIF('商品介绍'!$A$2:$A$200,A${row})`]];
  checks.getRange(`D${row}`).formulas = [[`=COUNTIF('核心卖点'!$A$2:$A$200,A${row})`]];
  checks.getRange(`E${row}`).formulas = [[`=COUNTIF('适宜人群'!$A$2:$A$200,A${row})`]];
  checks.getRange(`F${row}`).formulas = [[`=COUNTIF('联合用药'!$A$2:$A$200,A${row})`]];
  checks.getRange(`G${row}`).formulas = [[`=MAX(1,CEILING(MAX(D${row}/3,E${row}/3),1))`]];
  checks.getRange(`H${row}`).formulas = [[`=MAX(1,CEILING(F${row}/3,1))`]];
  checks.getRange(`I${row}`).formulas = [[`=COUNTIFS('素材表'!$B$2:$B$200,A${row},'素材表'!$E$2:$E$200,"是",'素材表'!$F$2:$F$200,"待接入")+COUNTIFS('素材表'!$B$2:$B$200,"GLOBAL",'素材表'!$E$2:$E$200,"是",'素材表'!$F$2:$F$200,"待接入")`]];
  checks.getRange(`J${row}`).formulas = [[`=IF(C${row}=0,"缺少商品介绍",IF(D${row}=0,"缺少核心卖点",IF(E${row}=0,"缺少适宜人群","结构可生成")))`]];
  checks.getRange(`K${row}`).formulas = [[`=IF(I${row}=0,"素材已就绪","有必需素材待接入")`]];
}
["A", "C", "D", "E", "F", "G", "H", "I"].forEach((col) => {
  checks.getRange(`${col}:${col}`).format.columnWidth = 16;
});
checks.getRange("B:B").format.columnWidth = 34;
checks.getRange("J:K").format.columnWidth = 24;
checks.getRange("J2:J3").conditionalFormats.add("containsText", {
  text: "结构可生成",
  format: { fill: "#D9EAD3", font: { color: COLORS.deepGreen, bold: true } },
});
checks.getRange("K2:K3").conditionalFormats.add("containsText", {
  text: "待接入",
  format: { fill: "#FCE8E6", font: { color: COLORS.red, bold: true } },
});

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(manifestDir, { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

for (const sheet of workbook.worksheets.items) {
  const used = sheet.getUsedRange();
  if (used) {
    used.format.autofitRows();
  }
  const preview = await workbook.render({
    sheetName: sheet.name,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(
    path.join(qaDir, `${String(workbook.worksheets.items.indexOf(sheet) + 1).padStart(2, "0")}-${sheet.name}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const workbookFile = await SpreadsheetFile.exportXlsx(workbook);
await workbookFile.save(workbookPath);

const imported = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));

function sheetRecords(sheetName) {
  const sheet = imported.worksheets.getItem(sheetName);
  const values = sheet.getUsedRange(true).values;
  const headers = values[0].map((value) => String(value ?? ""));
  return values
    .slice(1)
    .filter((row) => row.some((value) => value !== null && value !== ""))
    .map((row) =>
      Object.fromEntries(headers.map((header, index) => [header, row[index] ?? null])),
    );
}

const productRows = sheetRecords("商品主表").filter(
  (row) => row["生成开关"] === "是",
);
const childSheets = {
  introduction: sheetRecords("商品介绍"),
  selling_points: sheetRecords("核心卖点"),
  audiences: sheetRecords("适宜人群"),
  combinations: sheetRecords("联合用药"),
  benchmarks: sheetRecords("品种对标"),
  precautions: sheetRecords("注意事项"),
  assets: sheetRecords("素材表"),
};

const index = [];
for (const product of productRows) {
  const productId = String(product.product_id);
  const related = Object.fromEntries(
    Object.entries(childSheets).map(([key, records]) => [
      key,
      records
        .filter(
          (record) =>
            String(record.product_id) === productId ||
            (key === "assets" && String(record.product_id) === "GLOBAL"),
        )
        .sort((a, b) => Number(a["顺序"] ?? 0) - Number(b["顺序"] ?? 0)),
    ]),
  );
  const pageRules = {
    cover: { mode: "locked-source-slide", source_template_id: product["封面模板ID"] },
    page01: {
      layout: "source-page-01",
      required_sections: ["商品介绍", "核心卖点", "适宜人群"],
      items_per_page: 3,
      page_count: Math.max(
        1,
        Math.ceil(
          Math.max(related.selling_points.length, related.audiences.length) / 3,
        ),
      ),
    },
    page02: {
      layout: "source-page-02",
      required_columns: ["应用场景", "联合用药", "产品图片展示", "销售话术"],
      rows_per_page: 3,
      page_count: Math.max(1, Math.ceil(related.combinations.length / 3)),
    },
  };
  const manifest = {
    project_id: `courseware.${productId}`,
    product_id: productId,
    template_id: "template.product-courseware-dashenlin-green-v1",
    style_pack_id: "style-pack.dashenlin-courseware-green-v1",
    layout_policy: "preserve-source-layout",
    content_lock: product["审核版本"],
    output_format: product["输出格式"],
    product,
    ...related,
    page_rules: pageRules,
    blocker:
      "精确PPTX生成仍需公司原始PPTX；当前已完成Excel分组、可变模块和续页清单。",
  };
  const file = path.join(manifestDir, `${productId}.json`);
  await fs.writeFile(file, `${JSON.stringify(manifest, null, 2)}\n`);
  index.push({
    product_id: productId,
    product_name: product["商品名称"],
    page01_count: pageRules.page01.page_count,
    page02_count: pageRules.page02.page_count,
    manifest: path.relative(repoDir, file),
  });
}
await fs.writeFile(
  path.join(outputDir, "批量生成索引.json"),
  `${JSON.stringify({ products: index }, null, 2)}\n`,
);

const checkInspection = await imported.inspect({
  kind: "table",
  range: "生成检查!A1:K3",
  include: "values,formulas",
  tableMaxRows: 5,
  tableMaxCols: 12,
  maxChars: 12000,
});
await fs.writeFile(path.join(qaDir, "generation-check.ndjson"), checkInspection.ndjson);

const errorInspection = await imported.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
  maxChars: 8000,
});
await fs.writeFile(path.join(qaDir, "formula-errors.ndjson"), errorInspection.ndjson);

console.log(
  JSON.stringify(
    {
      workbook: workbookPath,
      sheets: imported.worksheets.items.map((sheet) => sheet.name),
      manifests: index,
      qaDir,
    },
    null,
    2,
  ),
);
