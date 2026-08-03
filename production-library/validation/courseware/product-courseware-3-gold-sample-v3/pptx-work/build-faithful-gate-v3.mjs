import fs from "node:fs/promises";
import path from "node:path";
import {Presentation, PresentationFile} from "@oai/artifact-tool";

const ROOT = "/Users/liminrong/Projects/chain-pharmacy-content-studio/production-library/validation/courseware/product-courseware-3-gold-sample-v3";
const WORK = path.join(ROOT, "pptx-work");
const RENDER = path.join(ROOT, "pptx-render-v3");
const ALPHA = path.join(ROOT, "assets", "alpha");
const BG = path.join(ROOT, "assets", "background", "white-silk-reference-faithful-bg-v3.png");
const FINAL = path.join(ROOT, "商品培训课件3_精细复刻_PPTX门槛片段_v3.pptx");
const FONT = "Gen Jyuu Gothic";
const C = {navy: "#123A84", orange: "#F28A00", orangeDark: "#D36D00", gray: "#C9C9C9", grayDark: "#969696", white: "#FFFFFF", black: "#171717"};

async function bytes(file) {
  const b = await fs.readFile(file);
  return new Uint8Array(b.buffer, b.byteOffset, b.byteLength);
}

function shape(slide, geometry, position, fill, line = {style: "solid", fill: "none", width: 0}, name) {
  return slide.shapes.add({geometry, position, fill, line, name});
}

function text(slide, value, position, options = {}) {
  const box = shape(slide, "textbox", position, options.fill ?? "none", options.line ?? {style: "solid", fill: "none", width: 0}, options.name);
  box.text = value;
  box.text.style = {
    fontFamily: FONT,
    fontSize: options.fontSize ?? 28,
    bold: options.bold ?? true,
    color: options.color ?? C.black,
    alignment: options.alignment ?? "center",
    verticalAlignment: options.verticalAlignment ?? "middle",
  };
  return box;
}

function image(slide, blob, alt, position, name) {
  return slide.images.add({blob, contentType: "image/png", alt, fit: "contain", position, name});
}

function background(slide, bg) {
  slide.images.add({blob: bg, contentType: "image/png", alt: "原创白色珍珠丝绸背景", fit: "cover", position: {left: 0, top: 0, width: 1280, height: 720}});
}

function ribbon(slide) {
  shape(slide, "parallelogram", {left: 405, top: 54, width: 80, height: 55}, C.orangeDark, {style: "solid", fill: C.orangeDark, width: 1});
  shape(slide, "parallelogram", {left: 795, top: 54, width: 80, height: 55}, C.orangeDark, {style: "solid", fill: C.orangeDark, width: 1});
  shape(slide, "roundRect", {left: 438, top: 43, width: 404, height: 70}, C.orange, {style: "solid", fill: C.orangeDark, width: 2}, "chapter-ribbon");
  text(slide, "一、三大核心功效", {left: 468, top: 48, width: 344, height: 58}, {fontSize: 38, color: C.white, name: "chapter-title"});
}

function brand(slide) {
  text(slide, "速", {left: 1090, top: 20, width: 48, height: 44}, {fontSize: 34, color: C.navy});
  text(slide, "福", {left: 1132, top: 20, width: 48, height: 44}, {fontSize: 34, color: C.orange});
  text(slide, "达", {left: 1174, top: 20, width: 48, height: 44}, {fontSize: 34, color: C.navy});
  text(slide, "（玛巴洛沙韦）", {left: 1086, top: 62, width: 145, height: 23}, {fontSize: 13, color: C.navy});
}

function nav(slide, active) {
  const items = [
    {left: 128, width: 282, label: "专治甲流乙流"},
    {left: 434, width: 322, label: "全程1次，1天退热"},
    {left: 780, width: 378, label: "治疗自己，保护身边人"},
  ];
  items.forEach((item, index) => {
    const on = active === index + 1;
    shape(slide, "roundRect", {left: item.left, top: 135, width: item.width, height: 58}, on ? C.orange : C.gray, {style: "solid", fill: on ? C.orangeDark : "#BEBEBE", width: 1}, `nav-${index + 1}`);
    shape(slide, "ellipse", {left: item.left + 7, top: 141, width: 46, height: 46}, C.white, {style: "solid", fill: on ? C.orangeDark : "#BEBEBE", width: 2});
    text(slide, String(index + 1), {left: item.left + 11, top: 145, width: 38, height: 38}, {fontSize: 27, color: on ? C.orange : C.grayDark});
    text(slide, item.label, {left: item.left + 54, top: 140, width: item.width - 60, height: 48}, {fontSize: index === 2 ? 27 : 29, color: C.white});
  });
}

function chrome(slide, active) {
  ribbon(slide);
  brand(slide);
  if (active) nav(slide, active);
}

function notes(slide, time, detail) {
  slide.speakerNotes.textFrame.setText(`[Sources]\n- 用户提供参考视频：/Users/liminrong/Downloads/商品培训课件3/商品培训课件3.mp4，参考时段 ${time}。\n- ${detail}\n- 品牌位为可编辑文字；包装为原创无品牌透明插画，等待业务授权真包装后原位替换；未裁取参考视频品牌像素。`);
  slide.speakerNotes.setVisible(false);
}

async function build() {
  await fs.mkdir(RENDER, {recursive: true});
  const [bg, packs, burstA, burstB, capsule, bubble, cell, blocker, grayPath, patient, shield] = await Promise.all([
    bytes(BG),
    bytes(path.join(ALPHA, "r06-package-cluster-alpha.png")),
    bytes(path.join(ALPHA, "r06-burst-navy-alpha.png")),
    bytes(path.join(ALPHA, "r06-burst-orange-alpha.png")),
    bytes(path.join(ALPHA, "r06-capsule-icon-alpha.png")),
    bytes(path.join(ALPHA, "r06-speech-bubble-alpha.png")),
    bytes(path.join(ALPHA, "r07-infected-cell-alpha.png")),
    bytes(path.join(ALPHA, "r07-orange-blocker-alpha.png")),
    bytes(path.join(ALPHA, "r07-gray-path-alpha.png")),
    bytes(path.join(ALPHA, "r08-patient-alpha.png")),
    bytes(path.join(ALPHA, "r08-family-shield-alpha.png")),
  ]);
  const deck = Presentation.create({slideSize: {width: 1280, height: 720}});

  {
    const slide = deck.slides.add();
    background(slide, bg);
    ribbon(slide);
    brand(slide);
    text(slide, "一、三大核心功效", {left: 410, top: 650, width: 460, height: 42}, {fontSize: 28, bold: false});
    notes(slide, "00:14.83–00:16.83", "章节条按参考由小到大建立，画面保持稀疏。 ");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg);
    chrome(slide, 1);
    image(slide, packs, "无品牌白色药品包装组合透明插画", {left: 300, top: 248, width: 590, height: 332}, "r06-package-cluster");
    image(slide, burstA, "深蓝色甲流爆裂标记透明插画", {left: 230, top: 340, width: 140, height: 104}, "r06-a-burst");
    text(slide, "甲", {left: 269, top: 365, width: 58, height: 52}, {fontSize: 36, color: C.white});
    image(slide, burstB, "橙色乙流爆裂标记透明插画", {left: 520, top: 220, width: 145, height: 110}, "r06-b-burst");
    text(slide, "乙", {left: 560, top: 244, width: 60, height: 55}, {fontSize: 37, color: C.white});
    image(slide, capsule, "橙色胶囊徽章透明插画", {left: 730, top: 425, width: 100, height: 100}, "r06-capsule");
    image(slide, bubble, "橙色聊天气泡透明插画", {left: 800, top: 238, width: 300, height: 300}, "r06-bubble");
    text(slide, "专治\n甲流乙流", {left: 835, top: 295, width: 220, height: 150}, {fontSize: 42, color: C.white});
    text(slide, "1：专治甲流乙流", {left: 370, top: 650, width: 540, height: 45}, {fontSize: 31, bold: false});
    notes(slide, "00:16.83–00:18.90", "商品和图标按用户反馈整体放大；甲乙和气泡文字保留独立可编辑层。 ");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg);
    chrome(slide, 2);
    shape(slide, "roundRect", {left: 52, top: 218, width: 1176, height: 410}, "#FFFFFF/92", {style: "solid", fill: "#E8E8E8", width: 1}, "mechanism-stage");
    image(slide, blocker, "橙色胶囊阻断病毒复制透明插画", {left: 70, top: 326, width: 430, height: 250}, "r07-blocker");
    image(slide, cell, "含病毒的粉红细胞透明插画", {left: 438, top: 284, width: 355, height: 355}, "r07-cell");
    image(slide, grayPath, "灰色胶囊与病毒释放路径透明插画", {left: 755, top: 340, width: 440, height: 235}, "r07-gray-path");
    text(slide, "全程只需口服1次", {left: 72, top: 236, width: 350, height: 48}, {fontSize: 30, color: C.orange});
    text(slide, "早期阻断病毒复制\n遏制新病毒生成", {left: 445, top: 230, width: 340, height: 72}, {fontSize: 26, color: C.orange});
    text(slide, "传统药物：1天2次\n连续服用5天", {left: 837, top: 235, width: 330, height: 70}, {fontSize: 25, color: C.grayDark});
    shape(slide, "roundRect", {left: 120, top: 545, width: 230, height: 58}, C.orange, {style: "solid", fill: C.orangeDark, width: 1});
    text(slide, "玛巴洛沙韦", {left: 140, top: 550, width: 190, height: 48}, {fontSize: 28, color: C.white});
    shape(slide, "roundRect", {left: 900, top: 545, width: 210, height: 58}, C.grayDark, {style: "solid", fill: "#777777", width: 1});
    text(slide, "奥司他韦", {left: 918, top: 550, width: 174, height: 48}, {fontSize: 28, color: C.white});
    text(slide, "2：全程1次，1天快速退热", {left: 310, top: 650, width: 660, height: 45}, {fontSize: 30, bold: false});
    notes(slide, "00:18.90–00:35.07", "机制页改为三组透明位图插画层：橙色阻断、感染细胞、灰色释放路径；文字和用药次数保持可编辑。 ");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg);
    chrome(slide, 3);
    image(slide, patient, "戴口罩的流感患者透明人物插画", {left: 155, top: 230, width: 305, height: 405}, "r08-patient");
    image(slide, burstA, "患者与家庭之间的病毒颗粒透明插画", {left: 485, top: 345, width: 90, height: 70}, "r08-virus-1");
    image(slide, burstB, "患者与家庭之间的病毒颗粒透明插画", {left: 545, top: 425, width: 72, height: 56}, "r08-virus-2");
    image(slide, shield, "蓝色盾牌内多代家庭透明插画", {left: 600, top: 220, width: 500, height: 420}, "r08-family-shield");
    text(slide, "治疗自己，保护身边人", {left: 400, top: 645, width: 480, height: 48}, {fontSize: 31, bold: false});
    notes(slide, "00:35.07–00:42.27", "患者、病毒和家庭盾牌均为透明 PNG 分层，无白色矩形底；视频中患者与盾牌从两侧分别入场。 ");
  }

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await deck.export({slide, format: "png", scale: 2});
    await fs.writeFile(path.join(RENDER, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({format: "layout"});
    await fs.writeFile(path.join(RENDER, `${stem}.layout.json`), await layout.text());
  }
  const montage = await deck.export({format: "webp", montage: true, scale: 1});
  await fs.writeFile(path.join(RENDER, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const inspect = await deck.inspect({kind: "slide,textbox,shape,image,notes", maxChars: 40000});
  await fs.writeFile(path.join(WORK, "inspect.ndjson"), inspect.ndjson);
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(FINAL);
  console.log(FINAL);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
