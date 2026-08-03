/**
 * 急性上呼吸道感染 · 疾病类健康知识培训课件
 * 复刻来源：参课真人讲解截图（已去除真人遮挡，补全被挡文案）
 * 输出：1920×1080 风格 16:9 PPTX
 */
import pptxgen from "pptxgenjs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "急性上呼吸道感染_呼吸系统疾病健康知识培训_v1.pptx");

// —— 视觉规范（对齐参课医疗蓝，无真人位）——
const C = {
  navy: "0B3D8C",
  navyDeep: "062A63",
  blue: "1E6BB8",
  blueMid: "2B7FD4",
  blueSoft: "E8F1FA",
  bluePale: "F3F7FC",
  white: "FFFFFF",
  ink: "1A2B4A",
  body: "2C3E50",
  muted: "5A6A7A",
  red: "C0392B",
  redSoft: "FDF0EE",
  line: "D0DCE8",
  tableHead: "1E5A8A",
  tableAlt: "F0F6FC",
  warnBg: "FFF8E6",
  warnBorder: "E8A317",
  cardBg: "FFFFFF",
  teal: "0D9488",
};

const FONT = "Microsoft YaHei";
const makeShadow = () => ({
  type: "outer",
  color: "000000",
  blur: 8,
  offset: 2,
  angle: 135,
  opacity: 0.1,
});

const pres = new pptxgen();
pres.defineLayout({ name: "WIDE_16x9", width: 13.333, height: 7.5 });
pres.layout = "WIDE_16x9";
pres.author = "chain-pharmacy-content-studio";
pres.title = "急性上呼吸道感染 · 呼吸系统疾病健康知识培训";
pres.subject = "疾病类培训课件 · 大参林健康顾问专业力系列";

// —— 通用组件 ——
function addContentChrome(slide, num, title) {
  slide.background = { color: C.bluePale };
  // top bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.333, h: 0.95,
    fill: { color: C.white },
    line: { color: C.line, width: 0.5 },
  });
  // number badge
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 0.22, w: 0.72, h: 0.52,
    fill: { color: C.blue },
    rectRadius: 0.06,
  });
  slide.addText(String(num).padStart(2, "0"), {
    x: 0.4, y: 0.22, w: 0.72, h: 0.52,
    fontFace: FONT, fontSize: 16, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(title, {
    x: 1.28, y: 0.22, w: 9, h: 0.52,
    fontFace: FONT, fontSize: 26, bold: true, color: C.ink,
    valign: "middle", margin: 0,
  });
  // brand corner
  slide.addText("参 课  ·  呼吸系统系列", {
    x: 10.2, y: 0.28, w: 2.8, h: 0.4,
    fontFace: FONT, fontSize: 11, color: C.muted,
    align: "right", valign: "middle", margin: 0,
  });
}

function addFooter(slide, page, total = 18) {
  slide.addText(`大参林医药集团  ·  健康顾问专业力  ·  ${page}/${total}`, {
    x: 0.4, y: 7.1, w: 12.5, h: 0.28,
    fontFace: FONT, fontSize: 10, color: C.muted, margin: 0,
  });
}

function hl(parts) {
  // parts: [{t, red?}]
  return parts.map((p, i) => ({
    text: p.t,
    options: {
      color: p.red ? C.red : C.body,
      bold: !!p.bold,
      breakLine: !!p.br,
    },
  }));
}

// ============================================================
// 01 封面
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.navyDeep };
  // decorative blocks
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.333, h: 4.2,
    fill: { color: C.navy },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 4.0, w: 13.333, h: 3.5,
    fill: { color: C.white },
  });
  // curve-ish top accent via triangle-ish bars
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 3.85, w: 13.333, h: 0.18,
    fill: { color: C.blueMid },
  });

  s.addText("大参林医药集团  ·  参课 SHENKE", {
    x: 0.8, y: 1.0, w: 11.5, h: 0.4,
    fontFace: FONT, fontSize: 16, color: "A8C8F0", align: "center", margin: 0,
  });
  s.addText("急性上呼吸道感染", {
    x: 0.8, y: 1.7, w: 11.5, h: 1.0,
    fontFace: FONT, fontSize: 48, bold: true, color: C.white,
    align: "center", margin: 0,
  });
  s.addText("呼吸系统系列  ·  疾病类健康知识培训课件", {
    x: 0.8, y: 2.85, w: 11.5, h: 0.45,
    fontFace: FONT, fontSize: 20, color: "D6E6FA", align: "center", margin: 0,
  });

  s.addText("培训目标", {
    x: 1.5, y: 4.5, w: 10, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
  });
  s.addText([
    { text: "掌握急性上呼吸道感染的定义、病因与临床表现；", options: { breakLine: true } },
    { text: "熟悉检查要点与对症用药逻辑；", options: { breakLine: true } },
    { text: "能向顾客完成专业用药指导与特殊人群关怀。", options: {} },
  ], {
    x: 1.5, y: 5.0, w: 10, h: 1.4,
    fontFace: FONT, fontSize: 15, color: C.body, paraSpaceAfter: 6,
  });
}

// ============================================================
// 02 目录
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bluePale };
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 5.2, h: 7.5,
    fill: { color: C.navy },
  });
  s.addText("目录", {
    x: 0.6, y: 2.8, w: 4, h: 0.7,
    fontFace: FONT, fontSize: 40, bold: true, color: C.white, margin: 0,
  });
  s.addText("CONTENTS", {
    x: 0.6, y: 3.5, w: 4, h: 0.4,
    fontFace: FONT, fontSize: 14, color: "8AB4E8", charSpacing: 4, margin: 0,
  });
  s.addText("呼吸系统 · 急性上呼吸道感染", {
    x: 0.6, y: 6.6, w: 4, h: 0.35,
    fontFace: FONT, fontSize: 12, color: "8AB4E8", margin: 0,
  });

  const items = [
    ["01", "疾病概览", "定义 · 流行特点 · 病因诱因"],
    ["02", "临床表现", "普通感冒 · 咽炎喉炎 · 疱疹性咽峡炎"],
    ["03", "检查方法", "体征 · 病原 · 实验室鉴别"],
    ["04", "治疗用药", "一般 · 局部 · 全身 · 对症与注意"],
    ["05", "专业关怀", "生活方式 · 特殊人群 · 防护"],
  ];
  items.forEach((it, i) => {
    const y = 1.1 + i * 1.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 5.8, y, w: 6.8, h: 0.9,
      fill: { color: C.white },
      shadow: makeShadow(),
      rectRadius: 0.08,
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 5.95, y: y + 0.18, w: 0.7, h: 0.54,
      fill: { color: C.blue },
      rectRadius: 0.06,
    });
    s.addText(it[0], {
      x: 5.95, y: y + 0.18, w: 0.7, h: 0.54,
      fontFace: FONT, fontSize: 16, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(it[1], {
      x: 6.9, y: y + 0.12, w: 5.3, h: 0.4,
      fontFace: FONT, fontSize: 18, bold: true, color: C.ink, margin: 0,
    });
    s.addText(it[2], {
      x: 6.9, y: y + 0.48, w: 5.3, h: 0.3,
      fontFace: FONT, fontSize: 12, color: C.muted, margin: 0,
    });
  });
}

// ============================================================
// 03 01 疾病概览
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 1, "疾病概览");
  addFooter(s, 3);

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.2, w: 3.2, h: 0.48,
    fill: { color: C.blue },
    rectRadius: 0.06,
  });
  s.addText("急性上呼吸道感染", {
    x: 0.4, y: 1.2, w: 3.2, h: 0.48,
    fontFace: FONT, fontSize: 14, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.9, w: 12.5, h: 2.0,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 1.9, w: 0.12, h: 2.0,
    fill: { color: C.blueMid },
  });
  s.addText([
    { text: "鼻腔、咽或喉部急性炎症", options: { bold: true, color: C.red } },
    { text: "的概称，是呼吸道最常见的一种传染疾病。", options: { color: C.body, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "本病全年皆可发病，", options: { color: C.body } },
    { text: "冬春季节多发", options: { bold: true, color: C.red } },
    { text: "，多为散发，但常在气候突变时流行。", options: { color: C.body } },
  ], {
    x: 0.8, y: 2.1, w: 11.8, h: 1.6,
    fontFace: FONT, fontSize: 16, valign: "middle",
  });

  // 病因
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 4.2, w: 12.5, h: 2.6,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addShape(pres.shapes.OVAL, {
    x: 0.7, y: 4.45, w: 0.42, h: 0.42,
    fill: { color: C.blueSoft },
  });
  s.addText("病", {
    x: 0.7, y: 4.45, w: 0.42, h: 0.42,
    fontFace: FONT, fontSize: 12, bold: true, color: C.blue,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText("病因", {
    x: 1.3, y: 4.45, w: 2, h: 0.42,
    fontFace: FONT, fontSize: 18, bold: true, color: C.ink, valign: "middle", margin: 0,
  });
  s.addText([
    { text: "大约 70% 是由", options: { color: C.body } },
    { text: "病毒", options: { bold: true, color: C.red } },
    { text: "引起，少数由细菌所致。还因淋雨、受凉、气候改变、过度劳累等导致呼吸道防御功能下降，病原体繁殖而诱发本病。", options: { color: C.body } },
  ], {
    x: 0.8, y: 5.1, w: 11.8, h: 1.4,
    fontFace: FONT, fontSize: 15,
  });
}

// ============================================================
// 04 02 临床表现
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 2, "临床表现");
  addFooter(s, 4);

  const blocks = [
    {
      t: "普通感冒",
      body: "常见疾病起病，应注意询问有无打喷嚏、鼻塞、流水样鼻涕等鼻咽部卡他症状，有无咽痛、咽痒、声哑等。一般无明显畏寒、高热等全身症状。",
    },
    {
      t: "病毒性咽炎、喉炎",
      body: "患者有咽喉部发痒和烧灼感，注意询问有无发热，有无声音嘶哑、讲话困难、咳嗽时疼痛等。",
    },
    {
      t: "疱疹性咽峡炎",
      body: "患者有明显的咽痛、发热。",
    },
  ];
  blocks.forEach((b, i) => {
    const y = 1.2 + i * 1.45;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y, w: 12.5, h: 1.3,
      fill: { color: C.white },
      shadow: makeShadow(),
      rectRadius: 0.08,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y, w: 0.12, h: 1.3,
      fill: { color: i === 2 ? C.red : C.blue },
    });
    s.addText(b.t, {
      x: 0.8, y: y + 0.12, w: 11.8, h: 0.35,
      fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
    });
    s.addText(b.body, {
      x: 0.8, y: y + 0.5, w: 11.8, h: 0.65,
      fontFace: FONT, fontSize: 14, color: C.body, margin: 0,
    });
  });

  // 诱因提示
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 5.65, w: 12.5, h: 1.15,
    fill: { color: C.warnBg },
    line: { color: C.warnBorder, width: 1 },
    rectRadius: 0.08,
  });
  s.addText([
    { text: "⚠  询问诱因  ", options: { bold: true, color: C.red } },
    { text: "有无受凉、淋雨、过度劳累等诱发因素。", options: { color: C.body } },
  ], {
    x: 0.7, y: 5.85, w: 12, h: 0.75,
    fontFace: FONT, fontSize: 15, valign: "middle",
  });
}

// ============================================================
// 05 03 检查方法
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 3, "检查方法");
  addFooter(s, 5);

  // left: 体征
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.2, w: 6.1, h: 5.5,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addText("体格检查要点", {
    x: 0.7, y: 1.4, w: 5.5, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: C.ink, margin: 0,
  });
  s.addText([
    { text: "鼻腔粘膜及咽部充血；", options: { bullet: true, breakLine: true } },
    { text: "可有扁桃体肿大、充血，甚至化脓；有时咽部、扁桃体表面可有灰白色疱疹及浅表溃疡；", options: { bullet: true, breakLine: true } },
    { text: "病毒感染：实验室检查白细胞正常或偏低；细菌感染：则白细胞升高。", options: { bullet: true } },
  ], {
    x: 0.7, y: 2.0, w: 5.5, h: 3.2,
    fontFace: FONT, fontSize: 14, color: C.body, paraSpaceAfter: 10,
  });
  s.addText("参考：正常 / 红肿扁桃体对比观察", {
    x: 0.7, y: 5.9, w: 5.5, h: 0.4,
    fontFace: FONT, fontSize: 12, color: C.muted, italic: true, margin: 0,
  });

  // right: 病原
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.8, y: 1.2, w: 6.1, h: 5.5,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addText("常见病原体（补全）", {
    x: 7.1, y: 1.4, w: 5.5, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: C.ink, margin: 0,
  });

  const pathogens = [
    ["病毒", "鼻病毒、呼吸道合胞病毒、冠状病毒、柯萨奇病毒和腺病毒等"],
    ["细菌", "A 族溶血性链球菌、肺炎链球菌、流感嗜血杆菌、葡萄球菌、酿脓链球菌、卡他莫拉菌等"],
    ["其他", "肺炎支原体、衣原体"],
  ];
  pathogens.forEach((p, i) => {
    const y = 2.0 + i * 1.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 7.1, y, w: 1.1, h: 0.38,
      fill: { color: i === 0 ? C.blue : i === 1 ? C.teal : "7C3AED" },
      rectRadius: 0.05,
    });
    s.addText(p[0], {
      x: 7.1, y, w: 1.1, h: 0.38,
      fontFace: FONT, fontSize: 13, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(p[1], {
      x: 8.35, y, w: 4.2, h: 1.15,
      fontFace: FONT, fontSize: 13, color: C.body, margin: 0,
    });
  });
}

// ============================================================
// 06 04 一般治疗
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 一般治疗");
  addFooter(s, 6);

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.25, w: 2.0, h: 0.45,
    fill: { color: C.blueSoft },
    rectRadius: 0.05,
  });
  s.addText("一般治疗", {
    x: 0.4, y: 1.25, w: 2.0, h: 0.45,
    fontFace: FONT, fontSize: 14, bold: true, color: C.blue,
    align: "center", valign: "middle", margin: 0,
  });

  const tips = [
    ["饮食营养", "饮食清淡，营养均衡，增加维生素和微量元素的摄取。"],
    ["补水休息", "多饮开水，注意通便，注意休息。"],
    ["环境温湿", "保持室内合适的温度和湿度。"],
    ["发热处理", "如有发热，还应注意退热。"],
  ];
  tips.forEach((t, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.4 + col * 6.4;
    const y = 2.0 + row * 2.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 6.1, h: 1.95,
      fill: { color: C.white },
      shadow: makeShadow(),
      rectRadius: 0.1,
    });
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.3, y: y + 0.35, w: 0.7, h: 0.7,
      fill: { color: C.blueSoft },
    });
    s.addText(String(i + 1), {
      x: x + 0.3, y: y + 0.35, w: 0.7, h: 0.7,
      fontFace: FONT, fontSize: 18, bold: true, color: C.blue,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(t[0], {
      x: x + 1.2, y: y + 0.35, w: 4.5, h: 0.4,
      fontFace: FONT, fontSize: 18, bold: true, color: C.ink, margin: 0,
    });
    s.addText(t[1], {
      x: x + 1.2, y: y + 0.9, w: 4.5, h: 0.75,
      fontFace: FONT, fontSize: 14, color: C.body, margin: 0,
    });
  });
}

// ============================================================
// 07 04 局部用药
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 局部用药");
  addFooter(s, 7);

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.25, w: 2.0, h: 0.45,
    fill: { color: C.blueSoft },
    rectRadius: 0.05,
  });
  s.addText("局部用药", {
    x: 0.4, y: 1.25, w: 2.0, h: 0.45,
    fontFace: FONT, fontSize: 14, bold: true, color: C.blue,
    align: "center", valign: "middle", margin: 0,
  });

  const locals = [
    { t: "鼻塞严重", d: "可短期使用减充血剂或医用高渗海水；伴有过敏的局部用抗组胺和糖皮质激素喷鼻。" },
    { t: "咽痛", d: "可用局部雾化药物缓解症状。" },
    { t: "耳痛 / 耳流脓", d: "局部治疗可采用 1% 酚甘油滴耳剂；3% 双氧水清洗加局部采用非耳毒性抗菌药物滴耳剂等。" },
  ];
  locals.forEach((l, i) => {
    const y = 2.0 + i * 1.5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y, w: 12.5, h: 1.35,
      fill: { color: C.white },
      shadow: makeShadow(),
      rectRadius: 0.08,
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.65, y: y + 0.4, w: 2.2, h: 0.55,
      fill: { color: C.blue },
      rectRadius: 0.06,
    });
    s.addText(l.t, {
      x: 0.65, y: y + 0.4, w: 2.2, h: 0.55,
      fontFace: FONT, fontSize: 14, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(l.d, {
      x: 3.1, y: y + 0.3, w: 9.5, h: 0.8,
      fontFace: FONT, fontSize: 15, color: C.body, valign: "middle", margin: 0,
    });
  });
}

// ============================================================
// 08 04 全身用药
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 全身用药");
  addFooter(s, 8);

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.25, w: 2.0, h: 0.45,
    fill: { color: C.blueSoft },
    rectRadius: 0.05,
  });
  s.addText("全身用药", {
    x: 0.4, y: 1.25, w: 2.0, h: 0.45,
    fontFace: FONT, fontSize: 14, bold: true, color: C.blue,
    align: "center", valign: "middle", margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 2.0, w: 12.5, h: 2.4,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.1,
  });
  s.addText([
    { text: "反复上呼吸道感染急性期应以", options: { color: C.body } },
    { text: "抗感染治疗", options: { bold: true, color: C.red } },
    { text: "为主。", options: { color: C.body, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "细菌感染者", options: { bold: true, color: C.ink } },
    { text: "应使用青霉素类如", options: { color: C.body } },
    { text: "阿莫西林", options: { bold: true, color: C.red } },
    { text: "等抗菌药物。", options: { color: C.body, breakLine: true } },
    { text: "病毒感染者", options: { bold: true, color: C.ink } },
    { text: "酌情使用抗病毒药物。", options: { color: C.body } },
  ], {
    x: 0.9, y: 2.35, w: 11.5, h: 1.8,
    fontFace: FONT, fontSize: 18, valign: "middle",
  });

  // three pillars
  const pillars = [
    ["抗感染", "急性期核心原则\n避免延误病情"],
    ["抗菌药", "细菌感染：青霉素类\n如阿莫西林等"],
    ["抗病毒", "病毒感染：酌情使用\n抗病毒药物"],
  ];
  pillars.forEach((p, i) => {
    const x = 0.4 + i * 4.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 4.7, w: 4.0, h: 1.9,
      fill: { color: C.white },
      shadow: makeShadow(),
      rectRadius: 0.1,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 4.7, w: 4.0, h: 0.12,
      fill: { color: C.blue },
    });
    s.addText(p[0], {
      x: x + 0.2, y: 5.0, w: 3.6, h: 0.45,
      fontFace: FONT, fontSize: 18, bold: true, color: C.blue,
      align: "center", margin: 0,
    });
    s.addText(p[1], {
      x: x + 0.2, y: 5.5, w: 3.6, h: 0.9,
      fontFace: FONT, fontSize: 13, color: C.body,
      align: "center", margin: 0,
    });
  });
}

// ============================================================
// 09 04 对症用药表
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 对症选药");
  addFooter(s, 9);

  const rows = [
    [
      { text: "临床症状", options: { fill: { color: C.tableHead }, color: C.white, bold: true, align: "center" } },
      { text: "对症用药", options: { fill: { color: C.tableHead }, color: C.white, bold: true, align: "center" } },
    ],
    ["流鼻涕、打喷嚏", "氯雷他定"],
    ["鼻塞", "盐酸伪麻黄碱"],
    ["发热、头痛", "精氨酸布洛芬颗粒、对乙酰氨基酚、复方氨酚烷胺胶囊"],
    ["咳嗽", "右美沙芬、氨溴索"],
    ["咽喉及扁桃体红肿、疼痛", "冬凌草糖浆、利咽解毒颗粒、清咽滴丸"],
    ["病毒感染", "抗病毒口服液、奥司他韦（1 岁以下慎用）"],
    ["细菌感染", "阿莫西林（3 个月以下慎用）、头孢拉定、罗红霉素"],
    ["免疫力低下", "复合维生素、维生素 C"],
  ];

  const tableData = rows.map((r, i) => {
    if (i === 0) return r;
    const fill = i % 2 === 0 ? C.tableAlt : C.white;
    return [
      { text: r[0], options: { fill: { color: fill }, color: C.ink, bold: true, align: "center" } },
      { text: r[1], options: { fill: { color: fill }, color: C.body, align: "left" } },
    ];
  });

  s.addTable(tableData, {
    x: 0.4, y: 1.25, w: 12.5, h: 5.5,
    colW: [3.5, 9.0],
    border: [{ pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }],
    fontFace: FONT,
    fontSize: 13,
    valign: "middle",
  });
}

// ============================================================
// 10 注意事项 1：阿莫西林/头孢/罗红/抗病毒/奥司他韦
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 注意事项（1）");
  addFooter(s, 10);

  const drugs = [
    {
      name: "阿莫西林胶囊",
      notes: [
        { t: "对青霉素过敏及皮肤试验阳性患者禁用", red: true },
        { t: "孕妇、哺乳期妇女慎用", red: false },
      ],
    },
    {
      name: "头孢拉定胶囊",
      notes: [
        { t: "对头孢菌素过敏者及有青霉素过敏性休克者禁用", red: true },
        { t: "孕妇、哺乳期妇女慎用，儿童慎用", red: true },
      ],
    },
    {
      name: "罗红霉素胶囊",
      notes: [
        { t: "对本品、红霉素或其他大环内酯类药物过敏者禁用", red: false },
        { t: "肝功能不全者禁用，肾功能不全者慎用", red: true },
        { t: "孕妇及哺乳期妇女慎用", red: false },
      ],
    },
    {
      name: "抗病毒口服液",
      notes: [
        { t: "孕妇、哺乳期妇女禁用", red: true },
        { t: "脾胃虚寒泄泻者慎服", red: true },
      ],
    },
    {
      name: "奥司他韦",
      notes: [
        { t: "1 岁以下儿童慎用", red: true },
      ],
    },
  ];

  const tableRows = [
    [
      { text: "药品", options: { fill: { color: C.tableHead }, color: C.white, bold: true, align: "center" } },
      { text: "注意事项", options: { fill: { color: C.tableHead }, color: C.white, bold: true, align: "center" } },
    ],
  ];
  drugs.forEach((d, i) => {
    const fill = i % 2 === 0 ? C.white : C.tableAlt;
    const noteText = d.notes.map((n) => `• ${n.t}`).join("\n");
    // For red highlights we use plain text; red called out in note content with 禁用/慎用
    tableRows.push([
      { text: d.name, options: { fill: { color: fill }, color: C.blue, bold: true, align: "center", valign: "middle" } },
      { text: noteText, options: { fill: { color: fill }, color: C.body, align: "left", valign: "middle" } },
    ]);
  });

  s.addTable(tableRows, {
    x: 0.4, y: 1.25, w: 12.5, h: 5.5,
    colW: [2.8, 9.7],
    border: [{ pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }],
    fontFace: FONT,
    fontSize: 12,
    valign: "middle",
  });
}

// ============================================================
// 11 注意事项 2：氯雷他定 / 复方氨酚烷胺 / 伪麻
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 注意事项（2）");
  addFooter(s, 11);

  // 氯雷他定
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.2, w: 12.5, h: 2.7,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 1.2, w: 0.12, h: 2.7,
    fill: { color: C.blue },
  });
  s.addText("氯雷他定", {
    x: 0.8, y: 1.35, w: 11.8, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
  });
  s.addText([
    { text: "不推荐 6 岁以下、6 岁以上但体重 ≤30 公斤的儿童使用", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "妊娠期及哺乳期妇女慎用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "肝功能不全的患者在医生指导下使用", options: { bullet: true, color: C.body } },
  ], {
    x: 0.8, y: 1.85, w: 11.8, h: 1.8,
    fontFace: FONT, fontSize: 14, paraSpaceAfter: 6,
  });

  // 复方氨酚烷胺胶囊
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 4.1, w: 12.5, h: 2.55,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 4.1, w: 0.12, h: 2.55,
    fill: { color: C.red },
  });
  s.addText("复方氨酚烷胺胶囊", {
    x: 0.8, y: 4.25, w: 11.8, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
  });
  s.addText([
    { text: "严重肝肾功能不全者禁用", options: { bullet: true, color: C.red } },
    { text: "；肝、肾功能不全者慎用", options: { color: C.red, breakLine: true } },
    { text: "用药不超过 7 天", options: { bullet: true, color: C.red } },
    { text: "，症状未缓解，请咨询医师或药师", options: { color: C.body, breakLine: true } },
    { text: "不能同时服用成份相似的其他抗感冒药", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "服用本品期间", options: { bullet: true, color: C.body } },
    { text: "不得饮酒", options: { color: C.red } },
    { text: "或含有酒精的饮料", options: { color: C.body, breakLine: true } },
    { text: "心脏病、高血压、甲状腺疾病、糖尿病等患者应在医师指导下使用", options: { bullet: true, color: C.body } },
  ], {
    x: 0.8, y: 4.7, w: 11.8, h: 1.8,
    fontFace: FONT, fontSize: 13, paraSpaceAfter: 3,
  });
}

// ============================================================
// 12 注意事项 3：对乙酰氨基酚 / 布洛芬
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 注意事项（3）");
  addFooter(s, 12);

  // left: 对乙酰氨基酚
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 1.2, w: 6.2, h: 5.5,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 1.2, w: 6.2, h: 0.55,
    fill: { color: C.tableHead },
  });
  s.addText("对乙酰氨基酚", {
    x: 0.35, y: 1.2, w: 6.2, h: 0.55,
    fontFace: FONT, fontSize: 16, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "严重肝肾功能不全者禁用，过敏者禁用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "对阿司匹林过敏者慎用，肝肾功能不全者慎用，孕妇及哺乳期妇女慎用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "应尽量避免合并使用含有对乙酰氨基酚或其他解热镇痛药的药品", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "口服一日最大量不超过 2 克", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "用于解热连续使用不超过 3 天，用于止痛不超过 5 天", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "服用期间不得饮酒或含有酒精的饮料", options: { bullet: true, color: C.red } },
  ], {
    x: 0.55, y: 1.95, w: 5.8, h: 4.5,
    fontFace: FONT, fontSize: 13, paraSpaceAfter: 8,
  });

  // right: 布洛芬颗粒
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.75, y: 1.2, w: 6.2, h: 5.5,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.75, y: 1.2, w: 6.2, h: 0.55,
    fill: { color: C.tableHead },
  });
  s.addText("布洛芬颗粒", {
    x: 6.75, y: 1.2, w: 6.2, h: 0.55,
    fontFace: FONT, fontSize: 16, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "消化性溃疡、重度血液异常、重度肝/肾病、重度心功能不全、重度高血压患者禁用；对成分过敏及对其他非甾体抗炎药过敏者禁用；阿司匹林哮喘或有既往史者禁用；", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "孕妇及哺乳期妇女禁用", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "老年人和儿童（6 个月以下）慎用药，尽可能将用量控制在所需的最小限度内", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "如出现胃肠道出血或溃疡、胸痛、气短、无力、言语含糊等情况，应停药并咨询医师", options: { bullet: true, color: C.body } },
  ], {
    x: 6.95, y: 1.95, w: 5.8, h: 4.5,
    fontFace: FONT, fontSize: 12.5, paraSpaceAfter: 8,
  });
}

// ============================================================
// 13 注意事项 4：右美沙芬 / 氨溴索
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 注意事项（4）");
  addFooter(s, 13);

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.2, w: 12.5, h: 3.15,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addText("右美沙芬", {
    x: 0.7, y: 1.35, w: 12, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
  });
  s.addText([
    { text: "妊娠 3 个月内妇女，有精神病史者及哺乳期妇女禁用", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "肝肾功能不全者禁用", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "2 周岁以下儿童使用时请咨询医师", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "不得与单胺氧化酶抑制剂及抗抑郁药并用", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "用药不得超过 7 天，如症状未缓解，应向医师或药师咨询", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "服药期间不得驾驶机、车、船，从事高空作业、机械作业及操作精密仪器", options: { bullet: true, color: C.body } },
  ], {
    x: 0.7, y: 1.85, w: 12, h: 2.3,
    fontFace: FONT, fontSize: 13, paraSpaceAfter: 4,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 4.55, w: 12.5, h: 2.15,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addText("氨溴索", {
    x: 0.7, y: 4.7, w: 12, h: 0.35,
    fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
  });
  s.addText([
    { text: "孕妇、哺乳期妇女慎用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "6 岁以下儿童应在医师指导下使用", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "肝肾功能不全者应在医师指导下使用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "应避免与中枢镇咳药（右美沙芬）同时使用，以免稀化的痰液堵塞气道", options: { bullet: true, color: C.red } },
  ], {
    x: 0.7, y: 5.15, w: 12, h: 1.4,
    fontFace: FONT, fontSize: 13, paraSpaceAfter: 4,
  });
}

// ============================================================
// 14 注意事项 5：利咽解毒颗粒 / 清咽滴丸
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 4, "治疗用药 · 注意事项（5）");
  addFooter(s, 14);

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.2, w: 12.5, h: 3.2,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addText("利咽解毒颗粒", {
    x: 0.7, y: 1.35, w: 12, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
  });
  s.addText([
    { text: "声嘶、咽痛初起，兼见恶寒发热、鼻流清涕等外感风寒者不适用", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "有高血压、心脏病、肝病、糖尿病、肾病等慢性病严重者应在医师指导下服用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "儿童、孕妇、哺乳期妇女、年老体弱、脾虚便溏者应在医师指导下服用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "扁桃体有化脓或发热体温超过 38.5℃ 的患者应医院就诊", options: { bullet: true, color: C.red, breakLine: true } },
    { text: "服药 3 天症状无缓解，应去医院就诊", options: { bullet: true, color: C.body } },
  ], {
    x: 0.7, y: 1.9, w: 12, h: 2.3,
    fontFace: FONT, fontSize: 13, paraSpaceAfter: 5,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 4.6, w: 12.5, h: 2.1,
    fill: { color: C.white },
    shadow: makeShadow(),
    rectRadius: 0.08,
  });
  s.addText("清咽滴丸", {
    x: 0.7, y: 4.75, w: 12, h: 0.35,
    fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0,
  });
  s.addText([
    { text: "孕妇慎用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "不宜在服药期间同时服用温补性中成药", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "按照用法用量服用，儿童应在医师指导下服用", options: { bullet: true, color: C.body, breakLine: true } },
    { text: "服药 3 天后症状无改善，或出现其他症状，应医院就诊", options: { bullet: true, color: C.body } },
  ], {
    x: 0.7, y: 5.2, w: 12, h: 1.35,
    fontFace: FONT, fontSize: 13, paraSpaceAfter: 4,
  });
}

// ============================================================
// 15 05 专业关怀 · 生活方式
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 5, "专业关怀 · 生活方式与防护");
  addFooter(s, 15);

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.2, w: 12.5, h: 1.3,
    fill: { color: C.blueSoft },
    rectRadius: 0.08,
  });
  s.addText([
    { text: "急性期须积极采取抗感染治疗", options: { bold: true, color: C.red } },
    { text: "，以免耽误病情；病情稳定后注意增强和改善自身免疫功能，减少再次感染的机率。", options: { color: C.body } },
  ], {
    x: 0.7, y: 1.4, w: 12, h: 0.9,
    fontFace: FONT, fontSize: 15, valign: "middle",
  });

  const cares = [
    ["饮食与休息", "饮食清淡，营养均衡，多休息、多饮水；男士戒烟，女士避免接触二手烟。"],
    ["环境与隔离", "生活环境保持整洁通风，尽量避免去人群聚集的场所，减少与病原体的接触（不聚众）。"],
    ["增强体质", "经常锻炼，增强体质，提高自身免疫力。"],
  ];
  cares.forEach((c, i) => {
    const x = 0.4 + i * 4.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 2.8, w: 4.05, h: 3.7,
      fill: { color: C.white },
      shadow: makeShadow(),
      rectRadius: 0.1,
    });
    s.addShape(pres.shapes.OVAL, {
      x: x + 1.45, y: 3.15, w: 1.15, h: 1.15,
      fill: { color: C.blueSoft },
    });
    s.addText(String(i + 1), {
      x: x + 1.45, y: 3.15, w: 1.15, h: 1.15,
      fontFace: FONT, fontSize: 28, bold: true, color: C.blue,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(c[0], {
      x: x + 0.25, y: 4.5, w: 3.55, h: 0.45,
      fontFace: FONT, fontSize: 16, bold: true, color: C.ink,
      align: "center", margin: 0,
    });
    s.addText(c[1], {
      x: x + 0.3, y: 5.1, w: 3.45, h: 1.15,
      fontFace: FONT, fontSize: 13, color: C.body,
      align: "center", margin: 0,
    });
  });
}

// ============================================================
// 16 05 专业关怀 · 特殊人群
// ============================================================
{
  const s = pres.addSlide();
  addContentChrome(s, 5, "专业关怀 · 特殊人群与防控");
  addFooter(s, 16);

  const cards = [
    {
      t: "疫苗预防",
      d: "儿童、老人可以常规接种流感疫苗，同时并合用其他的预防手段。",
      accent: C.blue,
    },
    {
      t: "特殊人群用药",
      d: "1 岁以下幼儿慎用感冒药；孕妇、哺乳期妇女慎用感冒药，以免影响胎儿婴儿。",
      accent: C.red,
    },
    {
      t: "隔离防护",
      d: "具有一定的传染性，提醒患者密切接触的家人注意隔离防护，避免交叉感染。勤开窗、多通风。",
      accent: C.teal,
    },
  ];
  cards.forEach((c, i) => {
    const y = 1.3 + i * 1.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y, w: 12.5, h: 1.55,
      fill: { color: C.white },
      shadow: makeShadow(),
      rectRadius: 0.1,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y, w: 0.14, h: 1.55,
      fill: { color: c.accent },
    });
    s.addText(c.t, {
      x: 0.9, y: y + 0.25, w: 11.7, h: 0.4,
      fontFace: FONT, fontSize: 18, bold: true, color: C.ink, margin: 0,
    });
    s.addText(c.d, {
      x: 0.9, y: y + 0.75, w: 11.7, h: 0.55,
      fontFace: FONT, fontSize: 15, color: C.body, margin: 0,
    });
  });
}

// ============================================================
// 17 一页纸总结
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bluePale };
  // outer frame
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.25, y: 0.25, w: 12.83, h: 7.0,
    fill: { color: C.white },
    line: { color: C.navy, width: 2.5 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.25, y: 0.25, w: 12.83, h: 0.7,
    fill: { color: C.navy },
  });
  s.addText("呼吸系统课程  ·  急性上呼吸道感染  ·  一页总结", {
    x: 0.4, y: 0.35, w: 12.5, h: 0.5,
    fontFace: FONT, fontSize: 18, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });

  // 疾病概览
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.15, w: 1.8, h: 0.4,
    fill: { color: C.blue },
    rectRadius: 0.04,
  });
  s.addText("疾病概览", {
    x: 0.5, y: 1.15, w: 1.8, h: 0.4,
    fontFace: FONT, fontSize: 12, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText("急性上呼吸道感染是鼻腔、咽或喉部急性炎症的概称，是呼吸道最常见的一种传染疾病。", {
    x: 2.5, y: 1.15, w: 10.2, h: 0.55,
    fontFace: FONT, fontSize: 12, color: C.body, margin: 0,
  });

  // 临床表现
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.85, w: 1.8, h: 0.4,
    fill: { color: C.blue },
    rectRadius: 0.04,
  });
  s.addText("临床表现", {
    x: 0.5, y: 1.85, w: 1.8, h: 0.4,
    fontFace: FONT, fontSize: 12, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "1. 普通感冒：打喷嚏、鼻塞、流水样鼻涕等鼻咽部卡他症状，有无咽痛、咽痒、声哑等。", options: { breakLine: true } },
    { text: "2. 病毒性咽炎、喉炎：咽喉部发痒和烧灼感，声音嘶哑，讲话困难，咳嗽时疼痛等。", options: { breakLine: true } },
    { text: "3. 疱疹性咽峡炎：明显的咽痛、发热。", options: {} },
  ], {
    x: 2.5, y: 1.8, w: 10.2, h: 1.15,
    fontFace: FONT, fontSize: 11.5, color: C.body,
  });

  // 治疗用药 table
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 3.15, w: 1.8, h: 0.4,
    fill: { color: C.blue },
    rectRadius: 0.04,
  });
  s.addText("治疗用药", {
    x: 0.5, y: 3.15, w: 1.8, h: 0.4,
    fontFace: FONT, fontSize: 12, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });

  s.addTable([
    [
      { text: "类别", options: { fill: { color: C.tableHead }, color: C.white, bold: true, align: "center" } },
      { text: "功能", options: { fill: { color: C.tableHead }, color: C.white, bold: true, align: "center" } },
      { text: "具体用药", options: { fill: { color: C.tableHead }, color: C.white, bold: true, align: "center" } },
    ],
    [
      { text: "主药", options: { bold: true, color: C.ink, align: "center", fill: { color: C.tableAlt } } },
      { text: "消炎杀菌", options: { color: C.body, align: "center", fill: { color: C.tableAlt } } },
      { text: "阿莫西林、头孢拉定、罗红霉素", options: { color: C.body, fill: { color: C.tableAlt } } },
    ],
    [
      { text: "辅药", options: { bold: true, color: C.ink, align: "center" } },
      { text: "缓解症状", options: { color: C.body, align: "center" } },
      { text: "冬凌草糖浆、利咽解毒颗粒、清咽滴丸", options: { color: C.body } },
    ],
    [
      { text: "关联用药", options: { bold: true, color: C.ink, align: "center", fill: { color: C.tableAlt } } },
      { text: "增强体质", options: { color: C.body, align: "center", fill: { color: C.tableAlt } } },
      { text: "复合维生素、维生素 C", options: { color: C.body, fill: { color: C.tableAlt } } },
    ],
  ], {
    x: 2.5, y: 3.15, w: 10.2, h: 1.7,
    colW: [1.8, 2.0, 6.4],
    border: [{ pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }, { pt: 0.5, color: C.line }],
    fontFace: FONT,
    fontSize: 12,
    valign: "middle",
  });

  // 专业关怀
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 5.1, w: 1.8, h: 0.4,
    fill: { color: C.blue },
    rectRadius: 0.04,
  });
  s.addText("专业关怀", {
    x: 0.5, y: 5.1, w: 1.8, h: 0.4,
    fontFace: FONT, fontSize: 12, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "1. 注意隔离防护，避免交叉感染。", options: { breakLine: true } },
    { text: "2. 1 岁以下幼儿慎用感冒药；孕妇、哺乳期妇女慎用感冒药，以免影响胎儿婴儿。", options: { breakLine: true } },
    { text: "3. 经常锻炼，增强体质，提高自身免疫力。", options: { breakLine: true } },
    { text: "4. 饮食清淡，营养均衡，多休息、多饮水。", options: { breakLine: true } },
    { text: "5. 生活环境保持整洁通风。", options: {} },
  ], {
    x: 2.5, y: 5.05, w: 10.2, h: 1.9,
    fontFace: FONT, fontSize: 12, color: C.body,
  });
}

// ============================================================
// 18 结束页
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.navyDeep };
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.333, h: 7.5,
    fill: { color: C.navy },
  });
  s.addText("专业服务  ·  助力健康", {
    x: 0.8, y: 2.4, w: 11.7, h: 1.0,
    fontFace: FONT, fontSize: 42, bold: true, color: C.white,
    align: "center", margin: 0,
  });
  s.addText("大参林医药集团  ·  健康顾问专业力系列", {
    x: 0.8, y: 3.6, w: 11.7, h: 0.5,
    fontFace: FONT, fontSize: 18, color: "A8C8F0",
    align: "center", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.5, y: 4.3, w: 2.3, h: 0.06,
    fill: { color: C.blueMid },
  });
  s.addText("急性上呼吸道感染  ·  呼吸系统疾病健康知识培训", {
    x: 0.8, y: 4.7, w: 11.7, h: 0.4,
    fontFace: FONT, fontSize: 14, color: "8AB4E8",
    align: "center", margin: 0,
  });
  s.addText("本课件仅供内部培训使用，用药须遵医嘱与说明书", {
    x: 0.8, y: 6.5, w: 11.7, h: 0.35,
    fontFace: FONT, fontSize: 12, color: "6A8AB0",
    align: "center", margin: 0,
  });
}

await pres.writeFile({ fileName: OUT });
console.log("Wrote:", OUT);
