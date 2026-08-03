/**
 * 参课 · 疾病健康知识培训 · 可编辑金样 v2
 *
 * 交付级标准：
 * 1) 插图为重绘生成（assets/），非视频截图裁切
 * 2) 字体/字号/行距/留白统一字阶，对齐参课版式
 * 3) 商品包装为命名坑位（placeholders），业务替换授权原图
 *
 * 复用：改 content/*.content.json → node build-editable.mjs
 */
import pptxgen from "pptxgenjs";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const contentPath =
  process.argv[2] ||
  path.join(__dirname, "content/急性上呼吸道感染.content.json");
const data = JSON.parse(fs.readFileSync(contentPath, "utf8"));
const assetsDir = path.join(__dirname, "assets");
const placeholdersDir = path.join(assetsDir, "placeholders");
const outName = `${data.meta.topic}_疾病健康知识培训_可编辑金样_v2.pptx`;
const OUT = path.join(__dirname, outName);

// —— 参课色（从截图采样，不另起 UI）——
const C = {
  bg: "F4F7FC",
  white: "FFFFFF",
  ink: "1A2B4A",
  body: "2C3E50",
  muted: "5A6A7A",
  blue: "1E6BB8",
  blueDeep: "1A4F8C",
  blueBadge: "2B6CB0",
  blueLine: "3A7BC8",
  tableHead: "1E5A8A",
  tableAlt: "EEF4FA",
  red: "C0392B",
  line: "C8D6E6",
  quoteBorder: "5B9BD5",
  cardBorder: "A8C5E2",
  navy: "0A3A7A",
  navyDeep: "062A63",
  purple: "6B5B95",
  slotBg: "EAF2FA",
  slotBorder: "5A9BD5",
};

// 字阶：门店培训投影可读（偏大、偏密，避免稀拉拉）
const FONT = "Microsoft YaHei";
const T = {
  coverTitle: 44,
  coverSub: 26,
  section: 30,
  h2: 20,
  h3: 18,
  body: 18,
  bodySm: 17,
  table: 16,
  note: 15,
  caption: 13,
  badge: 18,
  tag: 20,
};

const W = 13.333;
const H = 7.5;

function asset(name) {
  if (!name) return null;
  for (const base of [assetsDir, placeholdersDir]) {
    const p = path.join(base, name);
    if (fs.existsSync(p)) return p;
  }
  // also try placeholders/pack- prefix
  const pack = path.join(placeholdersDir, name.startsWith("pack-") ? name : `pack-${name}.png`);
  if (fs.existsSync(pack)) return pack;
  return null;
}

function partsToRuns(parts, baseSize = T.body) {
  return (parts || []).map((p) => ({
    text: p.text,
    options: {
      color: p.emphasize ? C.red : C.body,
      bold: !!(p.emphasize || p.bold),
      fontSize: baseSize,
      fontFace: FONT,
    },
  }));
}

/** 图片槽：白底+细边，保证重绘图有统一画框 */
function addImageFrame(slide, imgPath, x, y, w, h, opts = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: C.white },
    line: { color: opts.border || C.line, width: 0.75 },
    rectRadius: 0.06,
  });
  if (imgPath) {
    const pad = opts.pad ?? 0.06;
    slide.addImage({
      path: imgPath,
      x: x + pad,
      y: y + pad,
      w: w - pad * 2,
      h: h - pad * 2,
      sizing: { type: "contain", w: w - pad * 2, h: h - pad * 2 },
    });
  }
}

/** 商品包装命名坑位：无授权原图时显示可替换卡（品名写在卡内，不叠字） */
function addPackshotSlot(slide, label, x, y, w, h, fileHint) {
  const img =
    (fileHint && asset(fileHint)) ||
    asset(`pack-${label}.png`) ||
    asset(`placeholders/pack-${label}.png`);

  if (img) {
    // 预生成命名卡：整卡贴入，不额外叠字
    slide.addImage({
      path: img,
      x, y, w, h,
      sizing: { type: "contain", w, h },
    });
    return;
  }

  // 纯形状坑位（无预生成图时）
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: C.slotBg },
    line: { color: C.slotBorder, width: 1.25, dashType: "dash" },
    rectRadius: 0.06,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: x + 0.06, y: y + 0.06, w: w - 0.12, h: 0.3,
    fill: { color: C.tableHead },
  });
  slide.addText("PACKSHOT · 替换位", {
    x: x + 0.06, y: y + 0.06, w: w - 0.12, h: 0.3,
    fontFace: FONT, fontSize: 10, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(label, {
    x: x + 0.1, y: y + h * 0.36, w: w - 0.2, h: 0.4,
    fontFace: FONT, fontSize: 13, bold: true, color: C.ink,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText("业务替换授权包装原图", {
    x: x + 0.1, y: y + h - 0.38, w: w - 0.2, h: 0.26,
    fontFace: FONT, fontSize: 10, color: C.muted,
    align: "center", margin: 0,
  });
}

/** 参课内容页 chrome：蓝方章 + 章节名 + 右上角 Logo */
function addShenkeChrome(slide, num, title) {
  slide.background = { color: C.bg };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.92,
    fill: { color: C.white },
    line: { color: C.line, width: 0.5 },
  });

  // 蓝方章号（直角，对齐截图）
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 0.2, w: 0.68, h: 0.52,
    fill: { color: C.blueBadge },
  });
  slide.addText(String(num).padStart(2, "0"), {
    x: 0.4, y: 0.2, w: 0.68, h: 0.52,
    fontFace: FONT, fontSize: 20, bold: true, color: C.white,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(title, {
    x: 1.2, y: 0.2, w: 9.0, h: 0.52,
    fontFace: FONT, fontSize: T.section, bold: true, color: C.ink,
    valign: "middle", margin: 0,
  });

  const logo = asset("logo-shenke.png");
  if (logo) {
    slide.addImage({ path: logo, x: 11.5, y: 0.16, w: 1.55, h: 0.58 });
  } else {
    slide.addText("参课 SHENKE", {
      x: 10.7, y: 0.3, w: 2.3, h: 0.35,
      fontFace: FONT, fontSize: 12, color: C.blue, align: "right", margin: 0,
    });
  }
}

/** 角标标签：一般治疗 / 全身用药 / 局部用药（L 形在字外） */
function addCornerTag(slide, tag, x = 0.5, y = 1.12) {
  const tw = Math.max(2.0, tag.length * 0.45 + 0.6);
  // L 形角标：竖条 + 横条
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h: 0.5, fill: { color: C.blueLine },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.38, h: 0.06, fill: { color: C.blueLine },
  });
  // 文字从 L 右侧明显留白
  slide.addText(tag, {
    x: x + 0.35, y: y - 0.02, w: tw, h: 0.5,
    fontFace: FONT, fontSize: T.tag, bold: true, color: C.ink,
    valign: "middle", margin: 0,
  });
}

/** 虚线角框正文（高度按内容收紧，避免大块空白） */
function addDashedBodyBox(slide, textOrParts, y = 5.05, h = 2.05) {
  const x = 0.45, w = 12.4;
  const c = C.blueLine;
  const L = 0.28;
  const thick = 0.055;
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: L, h: thick, fill: { color: c } });
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: thick, h: L, fill: { color: c } });
  slide.addShape(pres.shapes.RECTANGLE, { x: x + w - L, y, w: L, h: thick, fill: { color: c } });
  slide.addShape(pres.shapes.RECTANGLE, { x: x + w - thick, y, w: thick, h: L, fill: { color: c } });
  slide.addShape(pres.shapes.RECTANGLE, { x, y: y + h - thick, w: L, h: thick, fill: { color: c } });
  slide.addShape(pres.shapes.RECTANGLE, { x, y: y + h - L, w: thick, h: L, fill: { color: c } });
  slide.addShape(pres.shapes.RECTANGLE, { x: x + w - L, y: y + h - thick, w: L, h: thick, fill: { color: c } });
  slide.addShape(pres.shapes.RECTANGLE, { x: x + w - thick, y: y + h - L, w: thick, h: L, fill: { color: c } });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x + 0.06, y: y + 0.06, w: w - 0.12, h: h - 0.12,
    fill: { color: C.white },
    line: { color: "D0E0F0", width: 1, dashType: "dash" },
    rectRadius: 0.04,
  });

  const runs = Array.isArray(textOrParts)
    ? [
        { text: "□  ", options: { color: C.body, fontSize: T.body, fontFace: FONT } },
        ...partsToRuns(textOrParts, T.body),
      ]
    : [
        {
          text: "□  " + textOrParts,
          options: { color: C.body, fontSize: T.body, fontFace: FONT },
        },
      ];

  slide.addText(runs, {
    x: x + 0.28, y: y + 0.2, w: w - 0.56, h: h - 0.38,
    fontFace: FONT, fontSize: T.body, color: C.body,
    valign: "middle", align: "left",
    paraSpaceAfter: 6,
  });
}

/** 小标题底色条（培训课件用，替代裸下划线） */
function addTitleChip(slide, title, x, y, w = 7.5) {
  const chipH = 0.42;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h: chipH,
    fill: { color: "E3EEF8" },
    rectRadius: 0.04,
  });
  // 左侧色条
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.1, h: chipH,
    fill: { color: C.blueDeep },
  });
  slide.addText(title, {
    x: x + 0.22, y, w: w - 0.35, h: chipH,
    fontFace: FONT, fontSize: T.h2, bold: true, color: C.blueDeep,
    valign: "middle", margin: 0,
  });
  return chipH;
}

const pres = new pptxgen();
pres.defineLayout({ name: "HD", width: W, height: H });
pres.layout = "HD";
pres.author = "chain-pharmacy-content-studio";
pres.title = `${data.meta.topic} · 疾病健康知识培训（可编辑金样 v2）`;
pres.subject = data.template_id;

for (const s of data.slides) {
  const slide = pres.addSlide();
  const st = s.scene_type;

  // ========== COVER ==========
  if (st === "cover_branded") {
    slide.background = { color: C.navyDeep };
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: W, h: 4.4, fill: { color: "0B4A9C" },
    });
    // 建筑感竖条
    for (let i = 0; i < 10; i++) {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.5 + i * 1.3, y: 0.2, w: 0.75, h: 3.7,
        fill: { color: "1A6BC4", transparency: 50 + (i % 3) * 10 },
      });
    }
    slide.addShape(pres.shapes.OVAL, {
      x: -2.2, y: 3.5, w: 18.5, h: 5.6,
      fill: { color: C.white },
    });
    // 标题框
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 1.5, y: 1.45, w: 10.3, h: 3.45,
      fill: { color: "0A3A7A", transparency: 30 },
      line: { color: "5BA3E0", width: 1.5 },
      rectRadius: 0.08,
    });

    const logoC = asset("logo-shenke-cover.png") || asset("logo-shenke.png");
    if (logoC) {
      slide.addImage({ path: logoC, x: 1.9, y: 1.65, w: 2.5, h: 0.72 });
    }
    slide.addText(data.meta.brand || "大参林医药集团", {
      x: 4.8, y: 1.82, w: 6.5, h: 0.4,
      fontFace: FONT, fontSize: 15, color: "D0E6FF", align: "center", margin: 0,
    });

    slide.addText(s.title, {
      x: 1.8, y: 2.55, w: 9.7, h: 1.2,
      fontFace: FONT, fontSize: T.coverTitle, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(s.subtitle || data.meta.series, {
      x: 1.8, y: 3.9, w: 9.7, h: 0.55,
      fontFace: FONT, fontSize: T.coverSub, bold: true, color: C.navyDeep,
      align: "center", margin: 0,
    });

    // 讲者信息条（可编辑，无真人）
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 8.5, y: 6.3, w: 4.5, h: 0.95,
      fill: { color: C.white },
      rectRadius: 0.04,
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 8.5, y: 6.3, w: 0.16, h: 0.95, fill: { color: C.blue },
    });
    slide.addText(data.meta.presenter_title || "", {
      x: 8.85, y: 6.35, w: 4.0, h: 0.4,
      fontFace: FONT, fontSize: 14, bold: true, color: C.ink, margin: 0,
    });
    slide.addText(data.meta.presenter_sub || "", {
      x: 8.85, y: 6.75, w: 4.0, h: 0.4,
      fontFace: FONT, fontSize: 12, color: C.muted, margin: 0,
    });
    continue;
  }

  // ========== AGENDA ==========
  if (st === "agenda") {
    slide.background = { color: C.white };
    const building = asset("agenda-building.png");
    if (building) {
      slide.addImage({
        path: building, x: 0, y: 0, w: 6.2, h: H,
        sizing: { type: "cover", w: 6.2, h: H },
      });
    } else {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0, y: 0, w: 6.2, h: H, fill: { color: "D6E6F5" },
      });
    }
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 5.7, y: 0, w: 7.7, h: H, fill: { color: C.white },
    });
    const logo = asset("logo-shenke.png");
    if (logo) slide.addImage({ path: logo, x: 11.45, y: 0.28, w: 1.55, h: 0.55 });

    slide.addText(s.title, {
      x: 6.9, y: 0.95, w: 5.4, h: 0.7,
      fontFace: FONT, fontSize: 38, bold: true, color: C.blueDeep,
      align: "center", margin: 0,
    });

    (s.items || []).forEach((it, i) => {
      const y = 1.9 + i * 0.95;
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.05, y, w: 5.0, h: 0.8,
        fill: { color: i % 2 === 0 ? "F0F5FB" : "E8F0F8" },
        rectRadius: 0.06,
      });
      slide.addText([
        { text: `${it.num}  `, options: { color: C.blue, bold: true, fontSize: 22 } },
        { text: it.label, options: { color: C.ink, bold: true, fontSize: 22 } },
      ], {
        x: 7.3, y, w: 4.5, h: 0.8,
        fontFace: FONT, valign: "middle", margin: 0,
      });
    });
    continue;
  }

  // ========== DEFINITION + ETIOLOGY ==========
  if (st === "definition_etiology") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    // 病名徽章
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y: 1.12, w: 4.6, h: 0.55,
      fill: { color: "E3EEF8" },
      line: { color: C.blueLine, width: 1.5 },
      rectRadius: 0.04,
    });
    slide.addText(s.badge, {
      x: 0.45, y: 1.12, w: 4.6, h: 0.55,
      fontFace: FONT, fontSize: T.badge, bold: true, color: C.ink,
      align: "center", valign: "middle", margin: 0,
    });

    // 定义框：高度贴合正文，不留大片白
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y: 1.85, w: 12.4, h: 2.0,
      fill: { color: C.white },
      line: { color: C.quoteBorder, width: 1.75 },
      rectRadius: 0.06,
    });
    slide.addText("“", {
      x: 0.6, y: 1.9, w: 0.55, h: 0.55,
      fontFace: FONT, fontSize: 40, bold: true, color: C.quoteBorder, margin: 0,
    });
    slide.addText(partsToRuns(s.definition_parts, T.body), {
      x: 1.25, y: 2.0, w: 11.3, h: 1.65,
      fontFace: FONT, fontSize: T.body, color: C.body, valign: "middle",
    });

    // 病因：底色标题条 + 正文卡铺满下半屏
    addTitleChip(slide, s.etiology_title || "病因", 0.45, 4.1, 2.4);
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y: 4.65, w: 12.4, h: 2.45,
      fill: { color: C.white },
      line: { color: C.line, width: 1 },
      rectRadius: 0.05,
    });
    slide.addText(partsToRuns(s.etiology_parts, T.body), {
      x: 0.7, y: 4.85, w: 11.9, h: 2.05,
      fontFace: FONT, fontSize: T.body, color: C.body, valign: "middle",
    });
    continue;
  }

  // ========== CLINICAL ==========
  if (st === "clinical_blocks") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    const blocks = s.blocks || [];
    // 左栏三卡等高：底色标题条 + 正文；短文垂直居中，避免压到底栏
    const gap = 0.1;
    const n = Math.max(blocks.length, 1);
    const startY = 1.12;
    const endY = 6.12; // 提示条上方
    const blockH = (endY - startY - gap * (n - 1)) / n;
    let y = startY;
    blocks.forEach((b) => {
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.4, y, w: 7.7, h: blockH,
        fill: { color: C.white },
        line: { color: C.cardBorder, width: 1 },
        rectRadius: 0.06,
      });
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.4, y, w: 7.7, h: 0.42,
        fill: { color: "E3EEF8" },
        rectRadius: 0.06,
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.4, y: y + 0.28, w: 7.7, h: 0.16,
        fill: { color: "E3EEF8" },
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.4, y, w: 0.12, h: 0.42,
        fill: { color: C.blueDeep },
      });
      slide.addText(b.title, {
        x: 0.65, y, w: 7.2, h: 0.42,
        fontFace: FONT, fontSize: T.h2, bold: true, color: C.blueDeep,
        valign: "middle", margin: 0,
      });
      // 短正文居中，长正文顶对齐，减少「稀拉拉」感
      const short = (b.body || "").length < 45;
      slide.addText(b.body, {
        x: 0.6, y: y + 0.5, w: 7.3, h: blockH - 0.58,
        fontFace: FONT, fontSize: T.bodySm, color: C.body,
        valign: short ? "middle" : "top",
      });
      y += blockH + gap;
    });

    // 右栏插图（止于提示条上方，不压字）
    const throat = asset("clinical-throat-anatomy.png");
    const oral = asset("clinical-oral.png");
    if (throat) addImageFrame(slide, throat, 8.3, 1.12, 4.55, 2.4);
    if (oral) addImageFrame(slide, oral, 8.3, 3.65, 4.55, 2.4);

    // 询问诱因：整宽提示条（去掉无逻辑悬浮小图标）
    if (s.warning) {
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.4, y: 6.25, w: 12.5, h: 0.95,
        fill: { color: "FFF8E8" },
        line: { color: "F0D090", width: 1.25 },
        rectRadius: 0.05,
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.4, y: 6.25, w: 0.12, h: 0.95,
        fill: { color: "E8A317" },
      });
      slide.addText([
        {
          text: "⚠  " + s.warning.label + "：",
          options: { bold: true, color: C.ink, fontSize: T.bodySm },
        },
        {
          text: s.warning.body,
          options: { color: C.body, fontSize: T.bodySm },
        },
      ], {
        x: 0.7, y: 6.32, w: 12.0, h: 0.8,
        fontFace: FONT, valign: "middle", margin: 0,
      });
    }
    continue;
  }

  // ========== EXAM ==========
  if (st === "exam_two_column") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    // 左：体征说明卡
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y: 1.12, w: 6.2, h: 3.25,
      fill: { color: C.white },
      line: { color: C.cardBorder, width: 1 },
      rectRadius: 0.06,
    });
    addTitleChip(slide, "体格 / 实验室检查", 0.55, 1.25, 4.2);
    const leftRuns = (s.left_bullets || []).map((t, i, arr) => ({
      text: t,
      options: {
        bullet: { code: "25B6" },
        color: C.body,
        breakLine: i < arr.length - 1,
        fontSize: T.bodySm,
        fontFace: FONT,
      },
    }));
    slide.addText(leftRuns, {
      x: 0.65, y: 1.8, w: 5.7, h: 2.4,
      fontFace: FONT, fontSize: T.bodySm, color: C.body, valign: "top",
      paraSpaceAfter: 10,
    });

    const tonsils = asset("exam-tonsils.png");
    if (tonsils) addImageFrame(slide, tonsils, 0.4, 4.5, 6.2, 2.6);

    // 右：病原分型
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 6.85, y: 1.12, w: 6.05, h: 5.98,
      fill: { color: C.white },
      line: { color: C.cardBorder, width: 1 },
      rectRadius: 0.06,
    });
    addTitleChip(slide, "常见病原体", 7.0, 1.25, 3.6);
    const virus = asset("exam-virus-cartoon.png");
    if (virus) {
      slide.addImage({
        path: virus, x: 10.2, y: 1.2, w: 2.4, h: 1.7,
        sizing: { type: "contain", w: 2.4, h: 1.7 },
      });
    }

    let py = 3.1;
    (s.pathogens || []).forEach((p) => {
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.05, y: py, w: 5.65, h: 1.15,
        fill: { color: "F4F8FC" },
        rectRadius: 0.05,
      });
      slide.addText([
        { text: p.label + "\n", options: { bold: true, color: C.blueDeep, fontSize: T.h3 } },
        { text: p.body, options: { color: C.body, fontSize: T.bodySm } },
      ], {
        x: 7.25, y: py + 0.1, w: 5.25, h: 0.95,
        fontFace: FONT, valign: "middle",
      });
      py += 1.28;
    });
    continue;
  }

  // ========== TREATMENT ILLUSTRATION ==========
  if (st === "treatment_illustration") {
    addShenkeChrome(slide, s.section_num, s.section_title);
    addCornerTag(slide, s.tag || "");

    const images = s.images || [];
    const layout =
      s.images_layout ||
      (images.length === 1 ? "single_wide" : images.length === 3 ? "triple" : "double");

    // 插图区上移放大，正文框收紧，消灭大片空白
    if (layout === "single_wide" && images[0]) {
      const p = asset(images[0]);
      if (p) addImageFrame(slide, p, 2.0, 1.65, 9.3, 3.15);
    } else if (layout === "triple") {
      images.slice(0, 3).forEach((name, i) => {
        const p = asset(name);
        if (p) addImageFrame(slide, p, 0.5 + i * 4.2, 1.6, 4.0, 3.15);
      });
    } else {
      images.slice(0, 2).forEach((name, i) => {
        const p = asset(name);
        if (p) addImageFrame(slide, p, 0.55 + i * 6.35, 1.6, 6.1, 3.15);
      });
    }

    if (s.body_parts) addDashedBodyBox(slide, s.body_parts, 5.0, 2.1);
    else if (s.body) addDashedBodyBox(slide, s.body, 5.0, 2.1);
    continue;
  }

  // ========== TWO COL TABLE + PACKSHOT SLOTS ==========
  if (st === "two_col_table") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    const headers = s.headers || ["临床症状", "对症用药"];
    const tableRows = [
      headers.map((h) => ({
        text: h,
        options: {
          bold: true, color: C.white, align: "center", valign: "middle",
          fill: { color: C.tableHead }, fontSize: T.table,
        },
      })),
      ...(s.rows || []).map((r, ri) =>
        r.map((cell, ci) => ({
          text: cell,
          options: {
            color: C.body,
            align: ci === 0 ? "center" : "left",
            valign: "middle",
            bold: ci === 0,
            fill: { color: ri % 2 === 0 ? C.white : C.tableAlt },
            fontSize: T.table,
          },
        })),
      ),
    ];

    slide.addTable(tableRows, {
      x: 0.35, y: 1.15, w: 8.55, h: 5.95,
      colW: [2.7, 5.85],
      border: [{ pt: 0.6, color: C.line }],
      fontFace: FONT,
      fontSize: T.table,
    });

    // 右侧：命名商品坑位（业务替换授权包装）
    const slots =
      s.packshot_slots || [
        { label: "复方氨酚烷胺胶囊", file: "pack-复方氨酚烷胺胶囊.png" },
        { label: "冬凌草糖浆", file: "pack-冬凌草糖浆.png" },
        { label: "磷酸奥司他韦颗粒", file: "pack-磷酸奥司他韦颗粒.png" },
        { label: "阿莫西林胶囊", file: "pack-阿莫西林胶囊.png" },
      ];
    const slotH = 1.35;
    const slotGap = 0.1;
    const slotTop = 1.15;
    slots.slice(0, 4).forEach((slot, i) => {
      const y = slotTop + i * (slotH + slotGap);
      addPackshotSlot(slide, slot.label, 9.15, y, 3.75, slotH, slot.file);
    });
    continue;
  }

  // ========== DRUG PRECAUTIONS TABLE ==========
  if (st === "drug_precautions_table") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    const headers = s.headers || ["药品", "注意事项"];
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.55, y: 1.18, w: 12.2, h: 0.5,
      fill: { color: C.tableHead },
    });
    slide.addText(headers[0], {
      x: 0.55, y: 1.18, w: 2.3, h: 0.5,
      fontFace: FONT, fontSize: 17, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(headers[1], {
      x: 2.85, y: 1.18, w: 9.9, h: 0.5,
      fontFace: FONT, fontSize: 17, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });

    const rows = s.rows || [];
    const bodyH = 5.55;
    const rowH = Math.min(1.5, bodyH / Math.max(rows.length, 1));
    rows.forEach((row, ri) => {
      const y = 1.68 + ri * rowH;
      const bg = ri % 2 === 0 ? C.white : C.tableAlt;
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.55, y, w: 12.2, h: rowH,
        fill: { color: bg },
        line: { color: C.line, width: 0.5 },
      });
      slide.addText(row.drug, {
        x: 0.6, y, w: 2.2, h: rowH,
        fontFace: FONT, fontSize: 16, bold: true, color: C.ink,
        align: "center", valign: "middle", margin: 0,
      });
      const noteRuns = (row.notes || []).map((n, i, arr) => ({
        text: "• " + n.text + (i < arr.length - 1 ? "\n" : ""),
        options: {
          color: n.risk ? C.red : C.body,
          bold: !!n.risk,
          fontSize: T.note,
          fontFace: FONT,
        },
      }));
      slide.addText(noteRuns.length ? noteRuns : [{ text: "", options: {} }], {
        x: 2.95, y: y + 0.08, w: 9.6, h: rowH - 0.14,
        fontFace: FONT, fontSize: T.note, color: C.body, valign: "middle",
      });
    });
    continue;
  }

  // ========== DUAL DRUG COLUMNS ==========
  if (st === "drug_precautions_dual") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    const headers = s.headers || ["药品", "药A", "药B"];
    const hx = [0.45, 1.85, 7.55];
    const hw = [1.4, 5.7, 5.35];
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y: 1.18, w: 12.45, h: 0.52, fill: { color: C.tableHead },
    });
    headers.forEach((h, i) => {
      slide.addText(h, {
        x: hx[i], y: 1.18, w: hw[i], h: 0.52,
        fontFace: FONT, fontSize: 17, bold: true, color: C.white,
        align: "center", valign: "middle", margin: 0,
      });
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.45, y: 1.7, w: 12.45, h: 5.35,
      fill: { color: C.white },
      line: { color: C.line, width: 0.75 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 1.85, y: 1.7, w: 0.02, h: 5.35, fill: { color: C.line },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 7.55, y: 1.7, w: 0.02, h: 5.35, fill: { color: C.line },
    });
    slide.addText("注意\n事项", {
      x: 0.5, y: 3.5, w: 1.3, h: 1.2,
      fontFace: FONT, fontSize: 16, bold: true, color: C.ink,
      align: "center", valign: "middle", margin: 0,
    });

    const leftRuns = (s.left_notes || []).map((n, i, arr) => ({
      text: "• " + n.text + (i < arr.length - 1 ? "\n" : ""),
      options: {
        color: n.risk ? C.red : C.body,
        bold: !!n.risk,
        fontSize: T.note,
        fontFace: FONT,
      },
    }));
    const rightRuns = (s.right_notes || []).map((n, i, arr) => ({
      text: "• " + n.text + (i < arr.length - 1 ? "\n" : ""),
      options: {
        color: n.risk ? C.red : C.body,
        bold: !!n.risk,
        fontSize: T.note,
        fontFace: FONT,
      },
    }));
    slide.addText(leftRuns, {
      x: 2.05, y: 1.9, w: 5.3, h: 4.95,
      fontFace: FONT, fontSize: T.note, color: C.body, valign: "top",
    });
    slide.addText(rightRuns, {
      x: 7.75, y: 1.9, w: 4.95, h: 4.95,
      fontFace: FONT, fontSize: T.note, color: C.body, valign: "top",
    });
    continue;
  }

  // ========== CARE THREE CARDS ==========
  if (st === "care_three_cards") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    // 横幅收紧 + 字加大
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y: 1.1, w: 12.5, h: 1.05,
      fill: { color: "EAF2FA" },
      line: { color: C.cardBorder, width: 1 },
      rectRadius: 0.06,
    });
    slide.addText(partsToRuns(s.banner_parts, T.body), {
      x: 0.65, y: 1.18, w: 12.0, h: 0.9,
      fontFace: FONT, fontSize: T.body, color: C.body, valign: "middle",
    });

    // 三列：图 + 文同一卡，底部贴齐，少留白
    (s.cards || []).forEach((card, i) => {
      const x = 0.4 + i * 4.25;
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x, y: 2.35, w: 4.1, h: 4.75,
        fill: { color: C.white },
        line: { color: C.cardBorder, width: 1.25 },
        rectRadius: 0.08,
      });
      const imgName = (s.images || [])[i];
      const p = asset(imgName);
      if (p) {
        slide.addImage({
          path: p,
          x: x + 0.3, y: 2.55, w: 3.5, h: 2.55,
          sizing: { type: "contain", w: 3.5, h: 2.55 },
        });
      }
      slide.addShape(pres.shapes.RECTANGLE, {
        x: x + 0.25, y: 5.2, w: 3.6, h: 0.04,
        fill: { color: "E3EEF8" },
      });
      slide.addText(
        partsToRuns(card.parts || [{ text: card.body || "", emphasize: false }], T.bodySm),
        {
          x: x + 0.28, y: 5.35, w: 3.55, h: 1.55,
          fontFace: FONT, fontSize: T.bodySm, color: C.body, valign: "top",
        },
      );
    });
    continue;
  }

  // ========== CARE SPECIAL ==========
  if (st === "care_special") {
    addShenkeChrome(slide, s.section_num, s.section_title);

    // 三列整卡：上文下图，密度更高
    (s.cards || []).forEach((card, i) => {
      const x = 0.4 + i * 4.25;
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x, y: 1.15, w: 4.1, h: 5.95,
        fill: { color: C.white },
        line: { color: C.cardBorder, width: 1.5 },
        rectRadius: 0.08,
      });
      // 标题色条
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y: 1.15, w: 4.1, h: 0.12,
        fill: { color: C.blueDeep },
      });
      slide.addText(partsToRuns(card.parts, T.bodySm), {
        x: x + 0.22, y: 1.45, w: 3.65, h: 2.2,
        fontFace: FONT, fontSize: T.bodySm, color: C.body, valign: "top",
      });
      const imgName = (s.images || [])[i];
      const p = asset(imgName);
      if (p) {
        slide.addImage({
          path: p,
          x: x + 0.25, y: 3.85, w: 3.6, h: 2.95,
          sizing: { type: "contain", w: 3.6, h: 2.95 },
        });
      }
    });
    continue;
  }

  // ========== OUTRO ==========
  if (st === "outro") {
    slide.background = { color: "0A4A9C" };
    for (let i = 0; i < 12; i++) {
      slide.addShape(pres.shapes.OVAL, {
        x: 0.3 + (i % 6) * 2.1, y: 0.4 + Math.floor(i / 6) * 3.2,
        w: 1.8, h: 1.2,
        fill: { color: "1A6BC4", transparency: 70 },
      });
    }
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 2.7, y: 1.55, w: 7.9, h: 3.5,
      fill: { color: "0B5AB5", transparency: 18 },
      line: { color: "5EC8F0", width: 3 },
      rectRadius: 0.1,
    });

    const logo = asset("logo-shenke.png");
    if (logo) slide.addImage({ path: logo, x: 11.45, y: 0.28, w: 1.55, h: 0.55 });

    slide.addText(s.title || "专业服务\n助力健康", {
      x: 2.9, y: 1.95, w: 7.5, h: 2.7,
      fontFace: FONT, fontSize: 46, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });

    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 8.4, y: 5.85, w: 4.6, h: 1.3,
      fill: { color: C.white },
      rectRadius: 0.05,
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 8.4, y: 5.85, w: 4.6, h: 0.4, fill: { color: C.blue },
    });
    slide.addText(s.name || data.meta.presenter_name || "", {
      x: 8.4, y: 5.85, w: 4.6, h: 0.4,
      fontFace: FONT, fontSize: 15, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(s.title_line || "", {
      x: 8.6, y: 6.35, w: 4.25, h: 0.32,
      fontFace: FONT, fontSize: 14, bold: true, color: C.ink, margin: 0,
    });
    slide.addText(s.sub_line || "", {
      x: 8.6, y: 6.7, w: 4.25, h: 0.35,
      fontFace: FONT, fontSize: 12, color: C.muted, margin: 0,
    });
    continue;
  }

  // ========== ONE PAGE SUMMARY ==========
  if (st === "one_page_summary") {
    slide.background = { color: C.white };
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.22, y: 0.18, w: W - 0.44, h: H - 0.36,
      fill: { color: C.white },
      line: { color: C.blueDeep, width: 3 },
    });

    const seriesLogo = asset("summary-series-logo.png");
    if (seriesLogo) {
      slide.addImage({ path: seriesLogo, x: 0.42, y: 0.32, w: 2.2, h: 0.45 });
    }
    slide.addText(s.series_label || "健康顾问专业力系列", {
      x: 2.7, y: 0.38, w: 4.2, h: 0.35,
      fontFace: FONT, fontSize: 13, color: C.muted, margin: 0,
    });

    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 0.9, w: 12.3, h: 0.58,
      fill: { color: C.blueDeep },
      rectRadius: 0.06,
    });
    slide.addText(s.header, {
      x: 0.5, y: 0.9, w: 12.3, h: 0.58,
      fontFace: FONT, fontSize: 20, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });

    function sideLabel(y, label) {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.5, y, w: 0.2, h: 0.4, fill: { color: "8EB8E0" },
      });
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.78, y, w: 1.7, h: 0.4,
        fill: { color: C.blueDeep }, rectRadius: 0.04,
      });
      slide.addText(label, {
        x: 0.78, y, w: 1.7, h: 0.4,
        fontFace: FONT, fontSize: 13, bold: true, color: C.white,
        align: "center", valign: "middle", margin: 0,
      });
    }

    sideLabel(1.7, "疾病概览");
    slide.addText(s.overview, {
      x: 2.7, y: 1.7, w: 10.0, h: 0.85,
      fontFace: FONT, fontSize: T.bodySm, color: C.body, valign: "top",
    });

    sideLabel(2.7, "临床表现");
    slide.addText((s.clinical || []).join("\n"), {
      x: 2.7, y: 2.7, w: 10.0, h: 1.45,
      fontFace: FONT, fontSize: 13, color: C.body, valign: "top",
    });

    sideLabel(4.3, "治疗用药");
    const mt = s.med_table || { headers: [], rows: [] };
    const medRows = [
      mt.headers.map((h) => ({
        text: h,
        options: {
          bold: true, color: C.white, align: "center",
          fill: { color: C.tableHead },
        },
      })),
      ...mt.rows.map((r, i) =>
        r.map((c) => ({
          text: c,
          options: {
            color: C.body, align: "center", valign: "middle",
            fill: { color: i % 2 ? C.tableAlt : C.white },
            fontSize: 12,
          },
        })),
      ),
    ];
    slide.addTable(medRows, {
      x: 2.7, y: 4.3, w: 7.0, h: 1.55,
      colW: [1.45, 1.7, 3.85],
      border: [{ pt: 0.5, color: C.line }],
      fontFace: FONT,
      fontSize: 12,
    });

    // 总结页包装坑位
    addPackshotSlot(
      slide,
      "主/辅/关联用药包装",
      9.95,
      4.25,
      2.85,
      1.55,
      "pack-summary-group.png",
    );

    sideLabel(6.1, "专业关怀");
    slide.addText((s.care || []).join("\n"), {
      x: 2.7, y: 6.1, w: 8.6, h: 1.1,
      fontFace: FONT, fontSize: 12, color: C.body, valign: "top",
    });
    continue;
  }

  // fallback
  addShenkeChrome(slide, s.section_num || "00", s.section_title || s.id || "页面");
  slide.addText("未识别 scene_type: " + st, {
    x: 1, y: 3, w: 10, h: 1,
    fontFace: FONT, fontSize: 16, color: C.red,
  });
}

await pres.writeFile({ fileName: OUT });
console.log("Wrote", OUT);
console.log("Slides:", data.slides.length);
console.log("v2: redrawn assets + typography scale + named packshot slots");
