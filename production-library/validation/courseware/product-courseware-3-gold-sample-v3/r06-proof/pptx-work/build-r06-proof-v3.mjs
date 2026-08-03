import fs from "node:fs/promises";
import path from "node:path";
import {Presentation, PresentationFile} from "@oai/artifact-tool";

const ROOT = "/Users/liminrong/Projects/chain-pharmacy-content-studio/production-library/validation/courseware/product-courseware-3-gold-sample-v3";
const PROOF = path.join(ROOT, "r06-proof");
const WORK = path.join(PROOF, "pptx-work");
const RENDER = path.join(PROOF, "pptx-render");
const ALPHA = path.join(ROOT, "assets", "alpha");
const BG = path.join(ROOT, "assets", "background", "white-silk-reference-faithful-bg-v3.png");
const FINAL = path.join(PROOF, "商品培训课件3_R06精细复刻_PPTX证明_v3.pptx");

const FONT = "Gen Jyuu Gothic";
const C = {
  navy: "#123A84",
  orange: "#F28A00",
  orangeDark: "#D36D00",
  gray: "#C9C9C9",
  grayDark: "#969696",
  white: "#FFFFFF",
  black: "#171717",
};

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
  return slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    fit: "contain",
    position,
    name,
  });
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

function nav(slide) {
  // Equal 24 px perceived gaps after outline/shadow: 128–410, 434–756, 780–1158.
  const items = [
    {left: 128, width: 282, label: "专治甲流乙流", active: true},
    {left: 434, width: 322, label: "全程1次，1天退热", active: false},
    {left: 780, width: 378, label: "治疗自己，保护身边人", active: false},
  ];
  items.forEach((item, index) => {
    const fill = item.active ? C.orange : C.gray;
    const stroke = item.active ? C.orangeDark : "#BEBEBE";
    shape(slide, "roundRect", {left: item.left, top: 135, width: item.width, height: 58}, fill, {style: "solid", fill: stroke, width: 1}, `nav-${index + 1}`);
    shape(slide, "ellipse", {left: item.left + 7, top: 141, width: 46, height: 46}, C.white, {style: "solid", fill: stroke, width: 2}, `nav-number-${index + 1}`);
    text(slide, String(index + 1), {left: item.left + 11, top: 145, width: 38, height: 38}, {fontSize: 27, color: item.active ? C.orange : C.grayDark});
    text(slide, item.label, {left: item.left + 54, top: 140, width: item.width - 60, height: 48}, {fontSize: index === 2 ? 27 : 29, color: C.white, name: `nav-label-${index + 1}`});
  });
}

async function build() {
  await fs.mkdir(RENDER, {recursive: true});
  const [bg, packs, burstA, burstB, capsule, bubble] = await Promise.all([
    bytes(BG),
    bytes(path.join(ALPHA, "r06-package-cluster-alpha.png")),
    bytes(path.join(ALPHA, "r06-burst-navy-alpha.png")),
    bytes(path.join(ALPHA, "r06-burst-orange-alpha.png")),
    bytes(path.join(ALPHA, "r06-capsule-icon-alpha.png")),
    bytes(path.join(ALPHA, "r06-speech-bubble-alpha.png")),
  ]);

  const deck = Presentation.create({slideSize: {width: 1280, height: 720}});
  const slide = deck.slides.add();
  slide.images.add({blob: bg, contentType: "image/png", alt: "原创白色珍珠丝绸背景", fit: "cover", position: {left: 0, top: 0, width: 1280, height: 720}});
  ribbon(slide);
  brand(slide);
  nav(slide);

  image(slide, packs, "无品牌白色药品包装组合透明插画", {left: 300, top: 248, width: 590, height: 332}, "package-cluster");
  image(slide, burstA, "深蓝色甲流爆裂标记透明插画", {left: 230, top: 340, width: 140, height: 104}, "influenza-a-burst");
  text(slide, "甲", {left: 269, top: 365, width: 58, height: 52}, {fontSize: 36, color: C.white, name: "influenza-a-text"});
  image(slide, burstB, "橙色乙流爆裂标记透明插画", {left: 520, top: 220, width: 145, height: 110}, "influenza-b-burst");
  text(slide, "乙", {left: 560, top: 244, width: 60, height: 55}, {fontSize: 37, color: C.white, name: "influenza-b-text"});
  image(slide, capsule, "橙色胶囊徽章透明插画", {left: 730, top: 425, width: 100, height: 100}, "capsule-badge");
  image(slide, bubble, "橙色两段式聊天气泡透明插画", {left: 800, top: 238, width: 300, height: 300}, "benefit-speech-bubble");
  text(slide, "专治\n甲流乙流", {left: 835, top: 295, width: 220, height: 150}, {fontSize: 42, color: C.white, name: "benefit-editable-text"});

  text(slide, "1：专治甲流乙流", {left: 370, top: 650, width: 540, height: 45}, {fontSize: 31, bold: false, color: C.black, name: "caption"});
  slide.speakerNotes.textFrame.setText(
    "[Sources]\n- 用户提供参考视频：/Users/liminrong/Downloads/商品培训课件3/商品培训课件3.mp4，参考时段 00:16.83–00:18.90。\n- 本页按参考镜头的标题、导航、包装组、甲/乙标记、胶囊徽章、聊天气泡与字幕层级重建。\n- 包装为原创无品牌透明插画，品牌位为可编辑文字；未裁取参考视频的品牌包装或 Logo 像素。\n- 字体统一为 Gen Jyuu Gothic；三段导航可见间距均为 24 px；气泡底图和文字分层。",
  );
  slide.speakerNotes.setVisible(false);

  const png = await deck.export({slide, format: "png", scale: 2});
  await fs.writeFile(path.join(RENDER, "r06-proof-final.png"), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({format: "layout"});
  await fs.writeFile(path.join(RENDER, "r06-proof-final.layout.json"), await layout.text());
  const inspect = await deck.inspect({kind: "slide,textbox,shape,image,notes", maxChars: 30000});
  await fs.writeFile(path.join(WORK, "inspect.ndjson"), inspect.ndjson);
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(FINAL);
  console.log(FINAL);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
