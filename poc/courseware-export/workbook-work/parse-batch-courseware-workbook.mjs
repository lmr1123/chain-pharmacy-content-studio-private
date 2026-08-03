import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const repoDir = "/Users/liminrong/Projects/chain-pharmacy-content-studio";
const inputPath = path.resolve(
  process.argv[2] ??
    path.join(repoDir, "outputs/batch-courseware/商品培训课件_批量导入模板.xlsx"),
);
const outputDir = path.resolve(
  process.argv[3] ?? path.join(repoDir, "outputs/batch-courseware/generated"),
);
const manifestDir = path.join(outputDir, "manifests");

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));

function sheetRecords(sheetName) {
  const sheet = workbook.worksheets.getItem(sheetName);
  if (!sheet) {
    throw new Error(`缺少工作表：${sheetName}`);
  }
  const values = sheet.getUsedRange(true)?.values ?? [];
  if (values.length === 0) {
    return [];
  }
  const headers = values[0].map((value) => String(value ?? "").trim());
  return values
    .slice(1)
    .filter((row) => row.some((value) => value !== null && value !== ""))
    .map((row) =>
      Object.fromEntries(headers.map((header, index) => [header, row[index] ?? null])),
    );
}

const products = sheetRecords("商品主表").filter(
  (row) => String(row["生成开关"]).trim() === "是",
);
const productIds = products.map((row) => String(row.product_id ?? "").trim());
if (productIds.some((id) => !id)) {
  throw new Error("商品主表存在空 product_id。");
}
if (new Set(productIds).size !== productIds.length) {
  throw new Error("商品主表的 product_id 必须唯一。");
}

const childSheets = {
  introduction: sheetRecords("商品介绍"),
  selling_points: sheetRecords("核心卖点"),
  audiences: sheetRecords("适宜人群"),
  combinations: sheetRecords("联合用药"),
  benchmarks: sheetRecords("品种对标"),
  precautions: sheetRecords("注意事项"),
  assets: sheetRecords("素材表"),
};

await fs.mkdir(manifestDir, { recursive: true });
const index = [];

for (const product of products) {
  const productId = String(product.product_id).trim();
  const related = Object.fromEntries(
    Object.entries(childSheets).map(([key, records]) => [
      key,
      records
        .filter(
          (record) =>
            String(record.product_id).trim() === productId ||
            (key === "assets" && String(record.product_id).trim() === "GLOBAL"),
        )
        .sort((a, b) => Number(a["顺序"] ?? 0) - Number(b["顺序"] ?? 0)),
    ]),
  );

  const missingSections = [
    ["商品介绍", related.introduction.length],
    ["核心卖点", related.selling_points.length],
    ["适宜人群", related.audiences.length],
    ["联合用药", related.combinations.length],
  ]
    .filter(([, count]) => count === 0)
    .map(([name]) => name);
  if (missingSections.length > 0) {
    throw new Error(`${productId} 缺少必需内容：${missingSections.join("、")}`);
  }

  const pageRules = {
    cover: {
      mode: "locked-source-slide",
      source_template_id: product["封面模板ID"],
    },
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
  const manifestPath = path.join(manifestDir, `${productId}.json`);
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  index.push({
    product_id: productId,
    product_name: product["商品名称"],
    page01_count: pageRules.page01.page_count,
    page02_count: pageRules.page02.page_count,
    manifest: path.relative(outputDir, manifestPath),
  });
}

const indexPath = path.join(outputDir, "批量生成索引.json");
await fs.writeFile(
  indexPath,
  `${JSON.stringify({ source: inputPath, products: index }, null, 2)}\n`,
);

console.log(
  JSON.stringify(
    {
      source: inputPath,
      output: outputDir,
      products: index,
    },
    null,
    2,
  ),
);
