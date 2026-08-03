import fs from "node:fs/promises";
import path from "node:path";
import {Presentation, PresentationFile} from "@oai/artifact-tool";

const ROOT = "/Users/liminrong/Projects/chain-pharmacy-content-studio/production-library/validation/courseware/product-courseware-3-gold-sample-v2";
const WORK = path.join(ROOT, "pptx-work");
const RENDER = path.join(ROOT, "pptx-render");
const ASSETS = path.join(ROOT, "assets");
const FINAL = path.join(ROOT, "商品培训课件3_参考忠实复刻_PPTX门槛片段_v2.pptx");

const C = {
  navy: "#142E76",
  orange: "#ED8A00",
  orangeDark: "#C96E00",
  gray: "#C8C8C8",
  grayDark: "#8C8C8C",
  coral: "#E93E5E",
  pink: "#FAD6DF",
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
    fontFamily: "PingFang SC",
    fontSize: options.fontSize ?? 24,
    bold: options.bold ?? false,
    color: options.color ?? C.black,
    alignment: options.alignment ?? "center",
    verticalAlignment: options.verticalAlignment ?? "middle",
  };
  return box;
}

async function background(slide, bg) {
  slide.images.add({blob: bg, contentType: "image/png", alt: "白色丝绸课件背景", fit: "cover", position: {left: 0, top: 0, width: 1280, height: 720}});
  shape(slide, "rect", {left: 0, top: 0, width: 1280, height: 720}, "#FFFFFF/08");
}

function brand(slide) {
  text(slide, "速", {left: 1094, top: 22, width: 50, height: 45}, {fontSize: 33, bold: true, color: C.navy});
  text(slide, "福", {left: 1138, top: 22, width: 50, height: 45}, {fontSize: 33, bold: true, color: C.orange});
  text(slide, "达", {left: 1182, top: 22, width: 50, height: 45}, {fontSize: 33, bold: true, color: C.navy});
  text(slide, "（玛巴洛沙韦）", {left: 1094, top: 65, width: 138, height: 20}, {fontSize: 11, bold: true, color: C.navy});
}

function ribbon(slide) {
  shape(slide, "parallelogram", {left: 410, top: 67, width: 64, height: 53}, C.orangeDark, {style: "solid", fill: C.orangeDark, width: 1});
  shape(slide, "parallelogram", {left: 806, top: 67, width: 64, height: 53}, C.orangeDark, {style: "solid", fill: C.orangeDark, width: 1});
  shape(slide, "roundRect", {left: 440, top: 54, width: 400, height: 73}, C.orange, {style: "solid", fill: C.orangeDark, width: 3}, "chapter-ribbon");
  text(slide, "一、三大核心功效", {left: 468, top: 63, width: 344, height: 52}, {fontSize: 34, bold: true, color: C.white, name: "chapter-title"});
}

function nav(slide, active) {
  const items = [
    {left: 128, width: 282, label: "专治甲流乙流"},
    {left: 431, width: 322, label: "全程1次，1天退热"},
    {left: 782, width: 378, label: "治疗自己，保护身边人"},
  ];
  items.forEach((item, index) => {
    const on = active === index + 1;
    shape(slide, "roundRect", {left: item.left, top: 158, width: item.width, height: 60}, on ? C.orange : C.gray, {style: "solid", fill: on ? "#D97900" : "#BEBEBE", width: 1}, `nav-${index + 1}`);
    shape(slide, "ellipse", {left: item.left + 8, top: 164, width: 48, height: 48}, C.white, {style: "solid", fill: on ? C.orange : "#B6B6B6", width: 2});
    text(slide, String(index + 1), {left: item.left + 14, top: 169, width: 36, height: 36}, {fontSize: 25, bold: true, color: on ? C.orange : C.grayDark});
    text(slide, item.label, {left: item.left + 58, top: 165, width: item.width - 66, height: 46}, {fontSize: 25, bold: true, color: C.white});
  });
}

function chrome(slide, active = null) {
  ribbon(slide);
  if (active) nav(slide, active);
  brand(slide);
}

function notes(slide, referenceTime, details) {
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n- 用户提供参考视频：/Users/liminrong/Downloads/商品培训课件3/商品培训课件3.mp4，参考时刻 ${referenceTime}。\n- 本页按参考视频的版式比例、可见文案与素材角色重建；${details}\n- 品牌 Logo 与真包装尚未授权：品牌位置以可编辑文字保留，包装为无品牌矢量占位，不裁取参考视频像素。`,
  );
  slide.speakerNotes.setVisible(false);
}

function packageGroup(slide) {
  // Three editable, deliberately unbranded package silhouettes matching the reference role and proportions.
  shape(slide, "rect", {left: 438, top: 345, width: 330, height: 80}, C.white, {style: "solid", fill: "#D6D6D6", width: 1}, "packshot-horizontal-back");
  shape(slide, "rect", {left: 453, top: 416, width: 315, height: 84}, C.white, {style: "solid", fill: "#D6D6D6", width: 1}, "packshot-horizontal-front");
  shape(slide, "rect", {left: 777, top: 326, width: 112, height: 210}, C.white, {style: "solid", fill: "#D6D6D6", width: 1}, "packshot-vertical");
  shape(slide, "rect", {left: 460, top: 389, width: 292, height: 13}, C.orange, {style: "solid", fill: C.orange, width: 0});
  shape(slide, "rect", {left: 475, top: 460, width: 277, height: 13}, C.orange, {style: "solid", fill: C.orange, width: 0});
  shape(slide, "rect", {left: 782, top: 338, width: 9, height: 184}, "#E4D313", {style: "solid", fill: "#E4D313", width: 0});
  text(slide, "产品包装占位", {left: 510, top: 350, width: 190, height: 30}, {fontSize: 14, color: "#777777"});
  text(slide, "产品包装占位", {left: 505, top: 423, width: 190, height: 30}, {fontSize: 14, color: "#777777"});
  text(slide, "包装\n占位", {left: 800, top: 394, width: 70, height: 64}, {fontSize: 13, color: "#777777"});
}

function virus(slide, left, top, size = 42, fill = C.coral, name) {
  shape(slide, "star12", {left, top, width: size, height: size}, fill, {style: "solid", fill, width: 1}, name);
  shape(slide, "ellipse", {left: left + size * 0.34, top: top + size * 0.34, width: size * 0.32, height: size * 0.32}, fill, {style: "solid", fill, width: 0});
}

async function build() {
  await fs.mkdir(RENDER, {recursive: true});
  const bg = await bytes(path.join(ASSETS, "white-silk-medical-bg-v2.png"));
  const family = await bytes(path.join(ASSETS, "family-shield-flat-v2.png"));
  const deck = Presentation.create({slideSize: {width: 1280, height: 720}});

  // R05 — chapter transition, intentionally sparse like the reference.
  {
    const slide = deck.slides.add();
    await background(slide, bg);
    ribbon(slide);
    brand(slide);
    notes(slide, "00:14.83–00:16.83", "章节转场仅保留标题条和固定品牌位，不增加导航或说明文字。 ");
  }

  // R06 — benefit 1 final state.
  {
    const slide = deck.slides.add();
    await background(slide, bg);
    chrome(slide, 1);
    packageGroup(slide);
    virus(slide, 318, 372, 64, C.navy, "influenza-a");
    text(slide, "甲", {left: 326, top: 381, width: 48, height: 46}, {fontSize: 28, bold: true, color: C.white});
    virus(slide, 590, 258, 68, C.orange, "influenza-b");
    text(slide, "乙", {left: 599, top: 269, width: 50, height: 44}, {fontSize: 28, bold: true, color: C.white});
    shape(slide, "ellipse", {left: 850, top: 250, width: 210, height: 210}, "#F3B451/80", {style: "solid", fill: "#F3B451/30", width: 0});
    text(slide, "专治\n甲流乙流", {left: 884, top: 283, width: 142, height: 120}, {fontSize: 34, bold: true, color: C.white});
    notes(slide, "00:18.90", "保留中央包装组、甲／乙病毒标记与右侧圆形功效结论；包装只以无品牌可替换对象占位。 ");
  }

  // R07 — mechanism final state.
  {
    const slide = deck.slides.add();
    await background(slide, bg);
    chrome(slide, 2);
    shape(slide, "roundRect", {left: 72, top: 240, width: 1136, height: 388}, C.white, {style: "solid", fill: "#EEEEEE", width: 1}, "mechanism-board");
    text(slide, "① 口服1次", {left: 105, top: 300, width: 185, height: 48}, {fontSize: 26, bold: true, color: C.orange});
    shape(slide, "roundRect", {left: 176, top: 393, width: 255, height: 78}, C.orange, {style: "solid", fill: C.orangeDark, width: 1});
    text(slide, "玛巴洛沙韦", {left: 194, top: 405, width: 220, height: 54}, {fontSize: 30, bold: true, color: C.white});
    text(slide, "-24h  1天快速退热", {left: 116, top: 502, width: 300, height: 44}, {fontSize: 21, bold: true, color: C.orange});

    shape(slide, "ellipse", {left: 460, top: 330, width: 300, height: 250}, C.pink, {style: "solid", fill: "#C63A57", width: 4}, "infected-cell");
    [[500, 415], [600, 370], [675, 395], [585, 470], [675, 480]].forEach(([x, y], i) => virus(slide, x, y, 45, C.coral, `virus-${i + 1}`));
    shape(slide, "downArrow", {left: 555, top: 265, width: 48, height: 120}, C.orange, {style: "solid", fill: C.orange, width: 1});
    text(slide, "早期阻断病毒复制，\n遏制新病毒生成", {left: 420, top: 273, width: 185, height: 70}, {fontSize: 18, bold: true, color: C.orange});
    text(slide, "×", {left: 558, top: 375, width: 50, height: 52}, {fontSize: 40, bold: true, color: C.orange});

    shape(slide, "downArrow", {left: 760, top: 300, width: 44, height: 130}, C.grayDark, {style: "solid", fill: C.grayDark, width: 1});
    text(slide, "×", {left: 760, top: 406, width: 50, height: 50}, {fontSize: 37, bold: true, color: C.grayDark});
    shape(slide, "rightArrow", {left: 798, top: 423, width: 85, height: 38}, C.grayDark, {style: "solid", fill: C.grayDark, width: 1});
    virus(slide, 875, 403, 54, "#F6DDE2", "released-virus-1");
    virus(slide, 920, 466, 54, "#F6DDE2", "released-virus-2");
    shape(slide, "roundRect", {left: 954, top: 392, width: 205, height: 78}, C.grayDark, {style: "solid", fill: "#777777", width: 1});
    text(slide, "奥司他韦", {left: 972, top: 404, width: 170, height: 54}, {fontSize: 30, bold: true, color: C.white});
    text(slide, "2次/天 × 5天", {left: 968, top: 502, width: 180, height: 42}, {fontSize: 20, bold: true, color: C.grayDark});
    text(slide, "传统药物奥司他韦不阻止病毒复制", {left: 330, top: 645, width: 620, height: 46}, {fontSize: 28, color: C.black});
    notes(slide, "00:29.00", "机制板按参考终态重建为可编辑图形；药物名、次数和底部字幕均来自参考画面。 ");
  }

  // R08 — protection of family.
  {
    const slide = deck.slides.add();
    await background(slide, bg);
    chrome(slide, 3);
    slide.images.add({blob: family, contentType: "image/png", alt: "戴口罩患者、病毒颗粒与盾牌内多代家庭的原创扁平插画", fit: "contain", position: {left: 245, top: 216, width: 790, height: 420}});
    text(slide, "大大降低传染给家人的风险", {left: 390, top: 645, width: 500, height: 46}, {fontSize: 28, color: C.black});
    notes(slide, "00:40.50", "人物数量、左右关系、口罩、病毒颗粒和蓝色盾牌均与参考素材角色一致；插画为原创重绘。 ");
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
