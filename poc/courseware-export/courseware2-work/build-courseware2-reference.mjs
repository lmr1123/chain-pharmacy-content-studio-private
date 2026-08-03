import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const currentFile = fileURLToPath(import.meta.url);
const workDir = path.dirname(currentFile);
const repoDir = path.resolve(workDir, "../../..");
const config = JSON.parse(
  await fs.readFile(path.join(workDir, "courseware2-template.json"), "utf8"),
);

const outputDir = path.join(
  repoDir,
  "production-library/validation/courseware/disease-product-scenario-v1/courseware2-replication",
);
const qaDir = path.join(
  repoDir,
  "production-library/validation/courseware/disease-product-scenario-v1/qa-reference",
);
const outputPptx = path.join(
  repoDir,
  "production-library",
  "validation",
  "courseware",
  "disease-product-scenario-v1",
  "穿心莲内酯滴丸_商品培训课件2_PDF高保真基线.pptx",
);

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(path.dirname(outputPptx), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const presentation = Presentation.create({
  slideSize: { width: 1280, height: 720 },
});

for (const item of config.slides) {
  const sourceName = `slide-${String(item.slide - 1).padStart(3, "0")}.png`;
  const sourcePath = path.join(workDir, "source-slides", sourceName);
  const bytes = await fs.readFile(sourcePath);
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt: `源 PDF 第 ${item.slide} 张课件画面：${item.title}`,
    fit: "contain",
    position: { left: 0, top: 0, width: 1280, height: 720 },
  });
  slide.speakerNotes.textFrame.setText(
    [
      "[Sources]",
      `- User-provided internal PDF: ${config.source_pdf}`,
      `- Extracted flattened slide image: ${sourcePath}`,
      `- Source slide: ${item.slide}`,
      "- Reuse mode: full-slide flattened image; visual reference baseline, not an editable production page.",
      "[/Sources]",
    ].join("\n"),
  );
  slide.speakerNotes.setVisible(true);

  const stem = `slide-${String(item.slide).padStart(2, "0")}`;
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

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPptx);

const inspection = await presentation.inspect({
  kind: "slide,image,notes,layout",
  maxChars: 100000,
});
await fs.writeFile(path.join(qaDir, "inspection.ndjson"), inspection.ndjson);

console.log(outputPptx);
