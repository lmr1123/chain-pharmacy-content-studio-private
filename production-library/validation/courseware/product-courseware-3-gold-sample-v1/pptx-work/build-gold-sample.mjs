import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/Users/liminrong/Projects/chain-pharmacy-content-studio/production-library/validation/courseware/product-courseware-3-gold-sample-v1";
const WORK = path.join(ROOT, "pptx-work");
const RENDER = path.join(ROOT, "pptx-render");
const FINAL = path.join(ROOT, "商品培训课件3_金样复刻_PPTX小样_v1.pptx");
const ASSETS = path.join(ROOT, "assets");

const C = {
  navy: "#123C78",
  navy2: "#22579B",
  orange: "#E98200",
  orange2: "#F4A437",
  coral: "#E65D6F",
  pink: "#FCE8EC",
  gray: "#777E88",
  lightGray: "#E9EDF2",
  ink: "#182A43",
  white: "#FFFFFF"
};

async function bytes(file) {
  const b = await fs.readFile(file);
  return new Uint8Array(b.buffer, b.byteOffset, b.byteLength);
}

function addShape(slide, geometry, position, fill, line = { style: "solid", fill: "none", width: 0 }, name) {
  return slide.shapes.add({ geometry, position, fill, line, name });
}

function addText(slide, text, position, opts = {}) {
  const box = addShape(slide, "textbox", position, opts.fill ?? "none", opts.line ?? { style: "solid", fill: "none", width: 0 }, opts.name);
  box.text = text;
  box.text.style = {
    fontFamily: "PingFang SC",
    fontSize: opts.fontSize ?? 24,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    alignment: opts.alignment ?? "left",
    verticalAlignment: opts.verticalAlignment ?? "middle"
  };
  return box;
}

async function addBackground(slide, bgBytes) {
  slide.images.add({
    blob: bgBytes,
    contentType: "image/png",
    alt: "原创白色丝绸医疗课件背景",
    fit: "cover",
    position: { left: 0, top: 0, width: 1280, height: 720 }
  });
  addShape(slide, "rect", { left: 0, top: 0, width: 1280, height: 720 }, "#FFFFFF/12");
}

function addChrome(slide, active) {
  addShape(slide, "roundRect", { left: 420, top: 28, width: 440, height: 58 }, C.orange, { style: "solid", fill: C.orange2, width: 1 }, "chapter-ribbon");
  addText(slide, "一、三大核心功效", { left: 455, top: 36, width: 370, height: 42 }, { fontSize: 30, bold: true, color: C.white, alignment: "center", name: "chapter-title" });

  const nav = ["专治甲流、乙流", "全程1次，1天退热", "治疗自己，保护身边人"];
  const widths = [285, 300, 330];
  let left = 176;
  nav.forEach((label, index) => {
    const isActive = index + 1 === active;
    addShape(slide, "roundRect", { left, top: 99, width: widths[index], height: 42 }, isActive ? C.orange : "#D4D7DB", { style: "solid", fill: isActive ? C.orange2 : "#C6CBD1", width: 1 }, `nav-${index + 1}`);
    addShape(slide, "ellipse", { left: left + 9, top: 105, width: 30, height: 30 }, C.white, { style: "solid", fill: isActive ? C.orange : "#B0B5BC", width: 1 }, `nav-number-${index + 1}`);
    addText(slide, String(index + 1), { left: left + 13, top: 107, width: 22, height: 26 }, { fontSize: 17, bold: true, color: isActive ? C.orange : C.gray, alignment: "center" });
    addText(slide, label, { left: left + 44, top: 104, width: widths[index] - 52, height: 30 }, { fontSize: 18, bold: true, color: isActive ? C.white : C.white, alignment: "center", name: `nav-label-${index + 1}` });
    left += widths[index] + 12;
  });
  addText(slide, "模板示例", { left: 1138, top: 28, width: 92, height: 28 }, { fontSize: 14, color: "#7E8DA1", alignment: "right", name: "sample-label" });
  addText(slide, "仅用于金样复刻验证 · 包装与医学内容待业务审核", { left: 74, top: 675, width: 520, height: 24 }, { fontSize: 13, color: "#8A95A3", name: "review-footer" });
}

function addNotes(slide, slideNo) {
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n- 用户提供参考视频：/Users/liminrong/Downloads/商品培训课件3/商品培训课件3.mp4，参考片段 00:14.84–00:44.04。\n- 页面 ${slideNo} 的可见文案来自参考片观察与转录，未引入外部医学结论；正式使用前须业务与医学审核。\n- 背景与插画为本项目原创生成资产；包装为 series.medication.generic-packshot-v1 的无品牌示意。`
  );
  slide.speakerNotes.setVisible(false);
}

async function build() {
  await fs.mkdir(RENDER, { recursive: true });
  const bg = await bytes(path.join(ASSETS, "white-silk-medical-bg-v1.png"));
  const family = await bytes(path.join(ASSETS, "family-shield-v1.png"));
  const pack = await bytes(path.join(ASSETS, "generic-packshot-v1.png"));
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // B01 — chapter and first benefit
  {
    const slide = presentation.slides.add();
    await addBackground(slide, bg);
    addChrome(slide, 1);
    addText(slide, "针对甲流、乙流的抗流感治疗路径", { left: 105, top: 188, width: 650, height: 62 }, { fontSize: 38, bold: true, color: C.navy, name: "slide1-headline" });
    addText(slide, "先识别流感类型，再进入完整疗程说明", { left: 108, top: 253, width: 590, height: 38 }, { fontSize: 22, color: "#5B6D82", name: "slide1-subhead" });

    addShape(slide, "ellipse", { left: 130, top: 345, width: 150, height: 150 }, "#FFF4E7", { style: "solid", fill: C.orange2, width: 3 }, "influenza-a-circle");
    addText(slide, "甲流", { left: 155, top: 380, width: 100, height: 45 }, { fontSize: 31, bold: true, color: C.orange, alignment: "center" });
    addText(slide, "A 型流感", { left: 155, top: 425, width: 100, height: 30 }, { fontSize: 16, color: C.gray, alignment: "center" });
    addShape(slide, "ellipse", { left: 315, top: 345, width: 150, height: 150 }, "#EEF4FD", { style: "solid", fill: C.navy2, width: 3 }, "influenza-b-circle");
    addText(slide, "乙流", { left: 340, top: 380, width: 100, height: 45 }, { fontSize: 31, bold: true, color: C.navy, alignment: "center" });
    addText(slide, "B 型流感", { left: 340, top: 425, width: 100, height: 30 }, { fontSize: 16, color: C.gray, alignment: "center" });

    addShape(slide, "ellipse", { left: 790, top: 194, width: 370, height: 370 }, "#FFFFFF/72", { style: "solid", fill: "#F4C56E", width: 4 }, "packshot-halo");
    slide.images.add({ blob: pack, contentType: "image/png", alt: "无品牌胶囊包装示意，可替换", fit: "contain", position: { left: 860, top: 250, width: 230, height: 245 } });
    addShape(slide, "roundRect", { left: 895, top: 510, width: 160, height: 34 }, C.orange, { style: "solid", fill: C.orange2, width: 1 }, "packshot-label");
    addText(slide, "包装示意 · 可替换", { left: 905, top: 514, width: 140, height: 26 }, { fontSize: 15, bold: true, color: C.white, alignment: "center" });
    addNotes(slide, 1);
  }

  // B02 — one dose / one day
  {
    const slide = presentation.slides.add();
    await addBackground(slide, bg);
    addChrome(slide, 2);
    addText(slide, "全程一次，一天退热", { left: 92, top: 180, width: 620, height: 64 }, { fontSize: 42, bold: true, color: C.navy, name: "slide2-headline" });
    addText(slide, "全程仅需口服 1 次，早期阻断病毒复制。", { left: 95, top: 250, width: 610, height: 42 }, { fontSize: 24, color: "#465C75", name: "slide2-body" });

    addShape(slide, "ellipse", { left: 118, top: 338, width: 250, height: 250 }, "#FFF8EF", { style: "solid", fill: C.orange, width: 5 }, "dose-clock");
    addText(slide, "1", { left: 166, top: 365, width: 150, height: 120 }, { fontSize: 92, bold: true, color: C.orange, alignment: "center" });
    addText(slide, "全程口服", { left: 170, top: 485, width: 142, height: 34 }, { fontSize: 22, bold: true, color: C.navy, alignment: "center" });
    addText(slide, "次", { left: 248, top: 418, width: 72, height: 55 }, { fontSize: 34, bold: true, color: C.navy, alignment: "center" });

    addShape(slide, "rightArrow", { left: 405, top: 418, width: 190, height: 76 }, C.orange, { style: "solid", fill: C.orange2, width: 1 }, "treatment-arrow");
    addText(slide, "早期阻断", { left: 426, top: 434, width: 126, height: 40 }, { fontSize: 22, bold: true, color: C.white, alignment: "center" });

    addShape(slide, "ellipse", { left: 730, top: 205, width: 395, height: 395 }, "#FFFFFF/76", { style: "solid", fill: "#F2C87C", width: 3 }, "slide2-pack-halo");
    slide.images.add({ blob: pack, contentType: "image/png", alt: "无品牌胶囊包装示意，可替换", fit: "contain", position: { left: 822, top: 270, width: 210, height: 220 } });
    addText(slide, "1 天", { left: 810, top: 475, width: 235, height: 72 }, { fontSize: 54, bold: true, color: C.orange, alignment: "center", name: "one-day" });
    addText(slide, "快速退热", { left: 824, top: 540, width: 210, height: 38 }, { fontSize: 25, bold: true, color: C.navy, alignment: "center" });
    addNotes(slide, 2);
  }

  // B03 — editable mechanism comparison
  {
    const slide = presentation.slides.add();
    await addBackground(slide, bg);
    addChrome(slide, 2);
    addText(slide, "从源头遏制新病毒生成", { left: 86, top: 167, width: 700, height: 58 }, { fontSize: 39, bold: true, color: C.navy, name: "slide3-headline" });
    addText(slide, "一个机制图，讲清两条不同的抗病毒路径", { left: 88, top: 225, width: 570, height: 34 }, { fontSize: 21, color: "#5D6E82" });
    addShape(slide, "roundRect", { left: 70, top: 280, width: 1140, height: 340 }, C.white, { style: "solid", fill: "#D9E0E8", width: 1 }, "mechanism-surface");

    addShape(slide, "roundRect", { left: 103, top: 398, width: 190, height: 68 }, C.orange, { style: "solid", fill: C.orange2, width: 1 }, "new-path-label");
    addText(slide, "早期阻断路径", { left: 116, top: 412, width: 164, height: 40 }, { fontSize: 22, bold: true, color: C.white, alignment: "center" });

    const cell = addShape(slide, "ellipse", { left: 427, top: 318, width: 315, height: 260 }, C.pink, { style: "solid", fill: C.coral, width: 4 }, "infected-cell");
    addText(slide, "感染细胞", { left: 505, top: 425, width: 160, height: 36 }, { fontSize: 22, bold: true, color: C.navy, alignment: "center" });
    const virusPos = [
      [472, 360], [545, 350], [620, 366], [497, 500], [610, 490]
    ];
    virusPos.forEach(([x, y], i) => {
      addShape(slide, "star12", { left: x, top: y, width: 38, height: 38 }, C.coral, { style: "solid", fill: "#C94E5F", width: 1 }, `virus-${i + 1}`);
      addShape(slide, "ellipse", { left: x + 12, top: y + 12, width: 14, height: 14 }, "#FFFFFF/70", { style: "solid", fill: "#FFFFFF/20", width: 1 }, `virus-core-${i + 1}`);
    });
    addShape(slide, "downArrow", { left: 560, top: 280, width: 52, height: 95 }, C.orange, { style: "solid", fill: C.orange2, width: 1 }, "block-arrow");
    addText(slide, "阻断复制", { left: 497, top: 286, width: 116, height: 28 }, { fontSize: 18, bold: true, color: C.orange, alignment: "center" });

    addShape(slide, "rightArrow", { left: 748, top: 406, width: 116, height: 54 }, "#AEB5BD", { style: "solid", fill: "#969DA6", width: 1 }, "release-arrow");
    addShape(slide, "roundRect", { left: 884, top: 388, width: 210, height: 72 }, "#8D9299", { style: "solid", fill: "#757B83", width: 1 }, "traditional-label");
    addText(slide, "传统释放阻断路径", { left: 897, top: 403, width: 184, height: 42 }, { fontSize: 20, bold: true, color: C.white, alignment: "center" });
    addText(slide, "对比重点：阻断复制源头，而不是等病毒复制后再限制释放", { left: 158, top: 578, width: 956, height: 34 }, { fontSize: 20, bold: true, color: C.navy, alignment: "center", name: "comparison-takeaway" });
    addNotes(slide, 3);
  }

  // B04 — protect family
  {
    const slide = presentation.slides.add();
    await addBackground(slide, bg);
    addChrome(slide, 3);
    addText(slide, "治疗自己，保护身边人", { left: 84, top: 188, width: 560, height: 64 }, { fontSize: 41, bold: true, color: C.navy, name: "slide4-headline" });
    addText(slide, "早期阻断流感传播，降低传染给家人的风险。", { left: 88, top: 258, width: 555, height: 66 }, { fontSize: 24, color: "#465C75", name: "slide4-body" });
    addShape(slide, "roundRect", { left: 88, top: 364, width: 430, height: 130 }, "#FFF5E9", { style: "solid", fill: "#F6C27A", width: 2 }, "impact-callout");
    addText(slide, "本人尽早治疗", { left: 116, top: 386, width: 220, height: 34 }, { fontSize: 25, bold: true, color: C.orange });
    addText(slide, "→ 传播链更早被截断", { left: 116, top: 427, width: 320, height: 38 }, { fontSize: 22, bold: true, color: C.navy });
    slide.images.add({
      blob: family,
      contentType: "image/png",
      alt: "康复成人与受到盾牌保护的多代家庭原创插画",
      fit: "contain",
      position: { left: 630, top: 170, width: 540, height: 470 },
      geometry: "roundRect",
      borderRadius: "rounded-2xl"
    });
    addNotes(slide, 4);
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 2 });
    await fs.writeFile(path.join(RENDER, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(RENDER, `${stem}.layout.json`), await layout.text());
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(RENDER, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const snapshot = await presentation.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 20000 });
  await fs.writeFile(path.join(WORK, "inspect.ndjson"), snapshot.ndjson);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL);
  console.log(FINAL);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
