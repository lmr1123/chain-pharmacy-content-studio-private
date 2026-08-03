import fs from "node:fs/promises";
import path from "node:path";
import {Presentation, PresentationFile} from "@oai/artifact-tool";

const ROOT = "/Users/liminrong/Projects/chain-pharmacy-content-studio/production-library/validation/courseware/product-courseware-3-gold-sample-v3";
const WORK = path.join(ROOT, "pptx-work-v5");
const RENDER = path.join(ROOT, "pptx-render-v5-next");
const OLD_ALPHA = path.join(ROOT, "assets", "alpha");
const V5_ALPHA = path.join(ROOT, "assets", "v5-alpha");
const BG = path.join(ROOT, "assets", "background", "white-silk-reference-faithful-bg-v3.png");
const FINAL = path.join(ROOT, "商品培训课件3_精细复刻_PPTX继续片段_v5.pptx");
const FONT = "Gen Jyuu Gothic";
const C = {navy: "#123A84", orange: "#F28A00", orangeDark: "#D36D00", cream: "#FFF4E5", gray: "#C9C9C9", grayDark: "#969696", white: "#FFFFFF", black: "#171717"};

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

function ribbon(slide, title) {
  shape(slide, "parallelogram", {left: 405, top: 54, width: 80, height: 55}, C.orangeDark, {style: "solid", fill: C.orangeDark, width: 1});
  shape(slide, "parallelogram", {left: 795, top: 54, width: 80, height: 55}, C.orangeDark, {style: "solid", fill: C.orangeDark, width: 1});
  shape(slide, "roundRect", {left: 438, top: 43, width: 404, height: 70}, C.orange, {style: "solid", fill: C.orangeDark, width: 2}, "chapter-ribbon");
  text(slide, title, {left: 468, top: 48, width: 344, height: 58}, {fontSize: 38, color: C.white, name: "chapter-title"});
}

function brand(slide) {
  text(slide, "速", {left: 1090, top: 20, width: 48, height: 44}, {fontSize: 34, color: C.navy});
  text(slide, "福", {left: 1132, top: 20, width: 48, height: 44}, {fontSize: 34, color: C.orange});
  text(slide, "达", {left: 1174, top: 20, width: 48, height: 44}, {fontSize: 34, color: C.navy});
  text(slide, "（玛巴洛沙韦）", {left: 1086, top: 62, width: 145, height: 23}, {fontSize: 13, color: C.navy});
}

function productNav(slide, active) {
  const items = [
    {left: 55, width: 346, label: "成人儿童安全性均良好", size: 24},
    {left: 416, width: 494, label: "片剂、干混悬剂双剂型选择", size: 23},
    {left: 925, width: 250, label: "原研品牌", size: 25},
  ];
  items.forEach((item, index) => {
    const on = active === index + 1;
    shape(slide, "roundRect", {left: item.left, top: 135, width: item.width, height: 54}, on ? C.orange : C.gray, {style: "solid", fill: on ? C.orangeDark : "#BEBEBE", width: 1}, `product-nav-${index + 1}`);
    shape(slide, "ellipse", {left: item.left + 6, top: 140, width: 44, height: 44}, C.white, {style: "solid", fill: on ? C.orangeDark : "#BEBEBE", width: 2});
    text(slide, String(index + 1), {left: item.left + 10, top: 144, width: 36, height: 36}, {fontSize: 25, color: on ? C.orange : C.grayDark});
    text(slide, item.label, {left: item.left + 50, top: 139, width: item.width - 56, height: 44}, {fontSize: item.size, color: C.white});
  });
}

function notes(slide, referenceTime, detail) {
  slide.speakerNotes.textFrame.setText(`[Sources]\n- 用户提供参考视频：/Users/liminrong/Downloads/商品培训课件3/商品培训课件3.mp4，参考时段 ${referenceTime}。\n- 用户新录音：/Users/liminrong/Downloads/商品培训课件3/商品培训课件3.mp3。\n- ${detail}\n- 人物、片剂和药瓶为内置 imagegen 生成的无品牌透明插画；品牌包装与 Logo 等待业务授权资产后原位替换，未裁取参考视频像素。`);
  slide.speakerNotes.setVisible(false);
}

async function build() {
  await fs.mkdir(RENDER, {recursive: true});
  const [bg, packs, tablets, bottles, elder, child, chronic] = await Promise.all([
    bytes(BG),
    bytes(path.join(OLD_ALPHA, "r06-package-cluster-alpha.png")),
    bytes(path.join(V5_ALPHA, "tablets-alpha.png")),
    bytes(path.join(V5_ALPHA, "suspension-bottles-alpha.png")),
    bytes(path.join(V5_ALPHA, "elder-alpha.png")),
    bytes(path.join(V5_ALPHA, "child-alpha.png")),
    bytes(path.join(V5_ALPHA, "chronic-group-alpha.png")),
  ]);
  const deck = Presentation.create({slideSize: {width: 1280, height: 720}});

  {
    const slide = deck.slides.add();
    background(slide, bg); ribbon(slide, "二、产品特点"); brand(slide);
    text(slide, "二、产品特点", {left: 430, top: 648, width: 420, height: 44}, {fontSize: 29, bold: false});
    notes(slide, "00:40.68–00:44.04", "章节条由小到大建立；生产视频按新录音 00:40.74 的语义节点重定时。");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg); ribbon(slide, "二、产品特点"); brand(slide); productNav(slide, 1);
    shape(slide, "ellipse", {left: 365, top: 210, width: 550, height: 390}, "none", {style: "solid", fill: "#F5A326", width: 3}, "safety-ring");
    image(slide, packs, "无品牌包装组合透明插画", {left: 420, top: 270, width: 440, height: 248}, "safety-package-slot");
    shape(slide, "ellipse", {left: 115, top: 305, width: 135, height: 135}, C.cream, {style: "solid", fill: C.orange, width: 3});
    text(slide, "儿童", {left: 135, top: 324, width: 95, height: 38}, {fontSize: 24, color: C.navy});
    text(slide, "呕吐率低", {left: 72, top: 430, width: 220, height: 52}, {fontSize: 33, color: C.navy});
    shape(slide, "hexagon", {left: 1030, top: 325, width: 105, height: 115}, "none", {style: "solid", fill: C.orange, width: 5});
    text(slide, "✓", {left: 1050, top: 343, width: 65, height: 70}, {fontSize: 54, color: C.orange});
    text(slide, "安全性良好", {left: 425, top: 575, width: 430, height: 50}, {fontSize: 32});
    text(slide, "1：成人儿童安全性均良好", {left: 340, top: 650, width: 600, height: 42}, {fontSize: 28, bold: false});
    notes(slide, "00:44.04–00:49.24", "中央包装在橙色圆环内，左侧儿童呕吐率低，右侧安全盾牌；文字均保持可编辑。");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg); ribbon(slide, "二、产品特点"); brand(slide); productNav(slide, 2);
    shape(slide, "roundRect", {left: 42, top: 230, width: 330, height: 360}, "#FFFFFF/84", {style: "solid", fill: C.navy, width: 3}, "tablet-stage");
    shape(slide, "ellipse", {left: 395, top: 235, width: 490, height: 350}, "none", {style: "solid", fill: C.orange, width: 3}, "dosage-center-ring");
    shape(slide, "roundRect", {left: 908, top: 230, width: 330, height: 360}, "#FFFFFF/84", {style: "solid", fill: C.navy, width: 3}, "suspension-stage");
    image(slide, tablets, "四种无品牌白色片剂与刻度尺透明插画", {left: 70, top: 270, width: 275, height: 220}, "tablets-layer");
    image(slide, packs, "无品牌包装组合透明插画", {left: 435, top: 305, width: 410, height: 230}, "dosage-package-slot");
    image(slide, bottles, "无品牌干混悬剂药瓶透明插画", {left: 960, top: 258, width: 225, height: 300}, "suspension-layer");
    shape(slide, "line", {left: 370, top: 408, width: 70, height: 0}, "none", {style: "solid", fill: C.orange, width: 4});
    shape(slide, "line", {left: 840, top: 408, width: 70, height: 0}, "none", {style: "solid", fill: C.orange, width: 4});
    text(slide, "片剂无味，药小易吞", {left: 52, top: 545, width: 310, height: 44}, {fontSize: 25, color: C.navy});
    text(slide, "草莓口味｜可按体重精准给药", {left: 918, top: 540, width: 310, height: 54}, {fontSize: 23, color: C.navy});
    text(slide, "2：片剂、干混悬剂双剂型选择", {left: 300, top: 650, width: 680, height: 42}, {fontSize: 28, bold: false});
    notes(slide, "00:49.24–01:00.32", "片剂、包装、干混悬剂瓶为三组独立透明层；业务授权包装到位后替换中央与右侧槽位。");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg); ribbon(slide, "二、产品特点"); brand(slide); productNav(slide, 3);
    const rows = [
      {top: 235, icon: "⚑", title: "来自第一代流感药奥司他韦厂家", sub: "全球制药企业罗氏"},
      {top: 350, icon: "70+", title: "70+ 国家和地区获批上市", sub: "覆盖全球多个市场"},
      {top: 465, icon: "✓", title: "中国卫健委与 WHO 一致推荐", sub: "14 项国内外权威指南纳入"},
    ];
    rows.forEach((row, index) => {
      shape(slide, "roundRect", {left: 175, top: row.top, width: 930, height: 86}, C.cream, {style: "solid", fill: "#F4D7AC", width: 1}, `brand-evidence-${index + 1}`);
      text(slide, row.icon, {left: 198, top: row.top + 12, width: 88, height: 62}, {fontSize: index === 1 ? 27 : 39, color: C.orange});
      text(slide, row.title, {left: 300, top: row.top + 8, width: 735, height: 40}, {fontSize: 27, color: C.navy, alignment: "left"});
      text(slide, row.sub, {left: 300, top: row.top + 44, width: 735, height: 30}, {fontSize: 19, color: C.grayDark, alignment: "left", bold: false});
    });
    text(slide, "3：原研品牌", {left: 465, top: 650, width: 350, height: 42}, {fontSize: 29, bold: false});
    notes(slide, "01:00.32–01:11.92", "参考为三条证据卡累积；未使用或伪造罗氏 Logo，品牌事实文字按用户参考保留为可编辑层。");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg); ribbon(slide, "三、适宜人群"); brand(slide);
    image(slide, child, "5岁以上儿童透明人物插画", {left: 260, top: 245, width: 240, height: 360}, "audience-child-intro");
    shape(slide, "ellipse", {left: 610, top: 250, width: 300, height: 300}, C.orange, {style: "solid", fill: C.orangeDark, width: 2}, "age-five-badge");
    text(slide, "≥ 5岁", {left: 645, top: 310, width: 230, height: 90}, {fontSize: 62, color: C.white});
    text(slide, "既往健康或存在流感并发症高风险的\n单纯性甲型或乙型流感患者", {left: 625, top: 405, width: 270, height: 95}, {fontSize: 22, color: C.white});
    text(slide, "三、适宜人群", {left: 440, top: 650, width: 400, height: 42}, {fontSize: 29, bold: false});
    notes(slide, "01:11.92–01:17.36", "先建立5岁以上门槛与适用范围；人物为透明位图，文字独立可编辑。");
  }

  {
    const slide = deck.slides.add();
    background(slide, bg); ribbon(slide, "三、适宜人群"); brand(slide);
    text(slide, "5岁及以上的既往健康或存在流感并发症高风险的单纯性甲型或乙型流感患者", {left: 125, top: 138, width: 1030, height: 54}, {fontSize: 27, color: C.navy});
    const cards = [
      {left: 55, width: 330, img: elder, pos: {left: 116, top: 235, width: 205, height: 310}, label: "老年人（≥65岁）", name: "audience-elder"},
      {left: 430, width: 330, img: child, pos: {left: 490, top: 235, width: 210, height: 310}, label: "学龄期儿童\n（5岁及以上）", name: "audience-child"},
      {left: 805, width: 420, img: chronic, pos: {left: 825, top: 260, width: 380, height: 270}, label: "自身有基础性疾病的慢病患者", name: "audience-chronic"},
    ];
    cards.forEach((card) => {
      shape(slide, "roundRect", {left: card.left, top: 215, width: card.width, height: 405}, "#FFFFFF/88", {style: "solid", fill: "#E5E7EB", width: 1}, `${card.name}-card`);
      image(slide, card.img, card.label, card.pos, card.name);
      text(slide, card.label, {left: card.left + 15, top: 548, width: card.width - 30, height: 58}, {fontSize: card.name === "audience-chronic" ? 22 : 24, color: C.navy});
    });
    text(slide, "特别关注：老年人、学龄期儿童及慢病患者", {left: 285, top: 650, width: 710, height: 42}, {fontSize: 28, bold: false});
    notes(slide, "01:17.36–01:22.96", "老人、儿童和慢病患者三组人物按参考逐个出现；无白底，人物标签可编辑。");
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
  const inspect = await deck.inspect({kind: "slide,textbox,shape,image,notes", maxChars: 50000});
  await fs.writeFile(path.join(WORK, "inspect.ndjson"), inspect.ndjson);
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(FINAL);
  console.log(FINAL);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
