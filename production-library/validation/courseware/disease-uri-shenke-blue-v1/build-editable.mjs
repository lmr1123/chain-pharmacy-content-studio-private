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
const outName = `${data.meta.topic}_疾病健康知识培训_可编辑金样_v3.pptx`;
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
  footerLine: "D8E2EE",
  chipBg: "E3EEF8",
};

// logo-shenke*.png 为 360×110（≈3.273:1），全站按此比例摆放，禁止拉伸/裁切
const LOGO_AR = 360 / 110;
function logoW(h) { return h * LOGO_AR; }

// 柔和卡片投影（全站统一）
// 注意：pptxgenjs 会原地改写 shadow 对象（blur/angle/opacity 重复换算），必须每次返回新对象
const cardShadow = () => ({ type: "outer", color: "1A2B4A", blur: 7, offset: 2, angle: 90, opacity: 0.14 });

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

/**
 * 将单元格文案按关键词拆成 runs（对齐参课：重点药名深蓝加粗）
 * keywords 如 ["复方氨酚烷胺胶囊","奥司他韦"]
 */
/**
 * 注意事项配色：仅「禁用」类标红，慎用/指导用药用正文色
 * （避免通篇红字，对齐培训可读性）
 */
function noteRunOptions(n, baseSize = T.note) {
  const t = String(n?.text || "");
  const hardBan = /禁用/.test(t); // 含「禁用」才红
  return {
    color: hardBan ? C.red : C.body,
    bold: hardBan,
    fontSize: baseSize,
    fontFace: FONT,
  };
}

function noteBulletRuns(notes, baseSize = T.note, useSpacer = true) {
  const list = notes || [];
  const runs = [];
  list.forEach((n, i) => {
    const last = i >= list.length - 1;
    runs.push({
      text: "•  " + n.text + (last ? "" : "\n"),
      options: {
        ...noteRunOptions(n, baseSize),
        breakLine: !last && !useSpacer,
      },
    });
    // 行够高时条目间加空行；行矮时仅换行，避免撑破单元格
    if (!last && useSpacer) {
      runs.push({
        text: "\n",
        options: {
          fontSize: Math.max(7, baseSize - 5),
          breakLine: false,
          fontFace: FONT,
          color: C.body,
        },
      });
    }
  });
  return runs;
}

function emphasizeTextRuns(text, keywords = [], baseSize = T.table) {
  const src = String(text || "");
  if (!keywords.length) {
    return [{ text: src, options: { color: C.body, fontSize: baseSize, fontFace: FONT } }];
  }
  // 按关键词长度降序，避免短词抢匹配
  const keys = [...keywords].filter(Boolean).sort((a, b) => b.length - a.length);
  const runs = [];
  let i = 0;
  while (i < src.length) {
    let hit = null;
    let hitAt = -1;
    for (const k of keys) {
      const at = src.indexOf(k, i);
      if (at === i) {
        hit = k;
        hitAt = at;
        break;
      }
      if (at > i && (hitAt < 0 || at < hitAt)) {
        hit = k;
        hitAt = at;
      }
    }
    if (hit && hitAt === i) {
      runs.push({
        text: hit,
        options: {
          color: C.blueDeep,
          bold: true,
          fontSize: baseSize,
          fontFace: FONT,
        },
      });
      i += hit.length;
    } else if (hit && hitAt > i) {
      runs.push({
        text: src.slice(i, hitAt),
        options: { color: C.body, fontSize: baseSize, fontFace: FONT },
      });
      i = hitAt;
    } else {
      runs.push({
        text: src.slice(i),
        options: { color: C.body, fontSize: baseSize, fontFace: FONT },
      });
      break;
    }
  }
  return runs.length ? runs : [{ text: src, options: { color: C.body, fontSize: baseSize, fontFace: FONT } }];
}

/** 图片槽：白底+细边+轻投影，保证重绘图有统一画框 */
function addImageFrame(slide, imgPath, x, y, w, h, opts = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: C.white },
    line: { color: opts.border || C.line, width: 0.75 },
    rectRadius: 0.06,
    shadow: cardShadow(),
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

/**
 * 商品包装坑位
 * - 授权实拍：放 assets/packshots/真实文件名.png（非 pack- 前缀）
 * - 否则：形状「产品位」卡（品名可编辑 + 原生胶囊图标，不用 emoji），不伪造品牌包装
 */
function addPackshotSlot(slide, label, x, y, w, h, fileHint) {
  // 实拍优先：packshots/ 目录或非 pack- 前缀
  let realImg = null;
  if (fileHint) {
    const cand = asset(fileHint);
    if (cand && !path.basename(cand).startsWith("pack-")) realImg = cand;
  }
  if (!realImg) {
    const byLabel = path.join(assetsDir, "packshots", `${label}.png`);
    if (fs.existsSync(byLabel)) realImg = byLabel;
  }

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h,
    fill: { color: C.white },
    line: { color: C.cardBorder, width: 1.1 },
    rectRadius: 0.06,
    shadow: cardShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: 0.07,
    fill: { color: C.blueDeep },
  });

  if (realImg) {
    const pad = 0.1;
    slide.addImage({
      path: realImg,
      x: x + pad,
      y: y + 0.14,
      w: w - pad * 2,
      h: h - 0.42,
      sizing: { type: "contain", w: w - pad * 2, h: h - 0.42 },
    });
    slide.addText(label, {
      x: x + 0.06, y: y + h - 0.26, w: w - 0.12, h: 0.22,
      fontFace: FONT, fontSize: 11, bold: true, color: C.blueDeep,
      align: "center", margin: 0,
    });
    return;
  }

  // 产品位（设计感占位，非灰默认框）：虚线槽 + 原生胶囊图标 + 品名/提示分层不压线
  const compact = h < 1.0; // 一页通小坑位
  const labelH = compact ? 0.26 : 0.3;
  const hintH = compact ? 0.16 : 0.2;
  const slotTop = y + 0.13;
  const slotBottom = y + h - labelH - hintH - 0.06;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x + 0.16, y: slotTop, w: w - 0.32, h: slotBottom - slotTop,
    fill: { color: "F0F6FC" },
    line: { color: C.slotBorder, width: 1, dashType: "dash" },
    rectRadius: 0.05,
  });

  // 原生形状胶囊图标：旋转的圆角矩形，左半蓝右半白
  const capW = compact ? 0.42 : 0.56;
  const capH = compact ? 0.18 : 0.24;
  const capX = x + w / 2 - capW / 2;
  const capY = slotTop + (slotBottom - slotTop) / 2 - capH / 2;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: capX, y: capY, w: capW, h: capH,
    fill: { color: C.white },
    line: { color: C.blueBadge, width: 1.25 },
    rectRadius: capH / 2,
    rotate: 330,
  });
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: capX, y: capY, w: capW / 2, h: capH,
    fill: { color: C.blueBadge },
    rectRadius: capH / 2,
    rotate: 330,
  });

  slide.addText(label, {
    x: x + 0.06, y: y + h - labelH - hintH - 0.03, w: w - 0.12, h: labelH,
    fontFace: FONT, fontSize: compact ? 10.5 : 13, bold: true, color: C.ink,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText("授权包装图替换位", {
    x: x + 0.06, y: y + h - hintH - 0.03, w: w - 0.12, h: hintH,
    fontFace: FONT, fontSize: compact ? 7.5 : 9, color: C.muted,
    align: "center", valign: "middle", margin: 0,
  });
}

/** 页脚：集团·参课·系列 + 内部学习提示 + 页码（全站统一；opts.left=false 时省略左侧品牌行，用于深色底图页） */
function addFooter(slide, pageIdx, opts = {}) {
  const total = data.slides.length;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 7.12, w: W - 0.9, h: 0.012,
    fill: { color: C.footerLine },
  });
  if (opts.left !== false) {
    slide.addText(`${data.meta.brand || "大参林医药集团"}  ·  参课  ·  ${data.meta.series || ""}`, {
      x: 0.45, y: 7.17, w: 7.5, h: 0.24,
      fontFace: FONT, fontSize: 9.5, color: C.muted, margin: 0, valign: "middle",
    });
  }
  slide.addText(`仅限内部学习  ·  ${pageIdx} / ${total}`, {
    x: 8.9, y: 7.17, w: 3.99, h: 0.24,
    fontFace: FONT, fontSize: 9.5, color: C.muted, align: "right", margin: 0, valign: "middle",
  });
}

/** 参课内容页 chrome：蓝方章 + 章节名 + 右上角 Logo + 页脚 */
function addShenkeChrome(slide, num, title, pageIdx) {
  slide.background = { color: C.bg };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.92,
    fill: { color: C.white },
    line: { color: C.line, width: 0.5 },
  });
  // 页眉底部深蓝细条，加强结构
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.92, w: W, h: 0.035,
    fill: { color: C.blueDeep },
  });

  // 蓝方章号（微圆角 + 投影）
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 0.2, w: 0.68, h: 0.52,
    fill: { color: C.blueBadge },
    rectRadius: 0.05,
    shadow: cardShadow(),
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
    const lh = 0.5;
    slide.addImage({ path: logo, x: 12.85 - logoW(lh), y: 0.23, w: logoW(lh), h: lh });
  } else {
    slide.addText("参课 SHENKE", {
      x: 10.7, y: 0.3, w: 2.3, h: 0.35,
      fontFace: FONT, fontSize: 12, color: C.blue, align: "right", margin: 0,
    });
  }
  if (pageIdx) addFooter(slide, pageIdx);
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
pres.title = `${data.meta.topic} · 疾病健康知识培训（可编辑金样 v3）`;
pres.subject = data.template_id;

for (const [pageNo, s] of data.slides.entries()) {
  const pageIdx = pageNo + 1;
  const slide = pres.addSlide();
  const st = s.scene_type;

  // ========== COVER ==========
  if (st === "cover_branded") {
    slide.background = { color: C.navyDeep };
    // 上部主色带
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: W, h: 4.55, fill: { color: C.navy },
    });
    // 建筑感竖条（更少更宽，透明度分层）
    for (let i = 0; i < 7; i++) {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.65 + i * 1.85, y: 0, w: 1.05, h: 3.1 + (i % 3) * 0.55,
        fill: { color: "1A6BC4", transparency: 62 + (i % 3) * 8 },
      });
    }
    // 弧边：浅蓝新月 + 白色主弧
    slide.addShape(pres.shapes.OVAL, {
      x: -2.4, y: 3.28, w: 18.9, h: 5.9,
      fill: { color: "4A90D9", transparency: 35 },
    });
    slide.addShape(pres.shapes.OVAL, {
      x: -2.2, y: 3.62, w: 18.5, h: 5.9,
      fill: { color: C.white },
    });

    // 白色版 logo（完整比例）+ 集团名
    const logoC = asset("logo-shenke-cover.png") || asset("logo-shenke.png");
    if (logoC) {
      const lh = 0.6;
      slide.addImage({ path: logoC, x: 0.7, y: 0.5, w: logoW(lh), h: lh });
    }
    slide.addText(data.meta.brand || "大参林医药集团", {
      x: 8.9, y: 0.62, w: 3.75, h: 0.38,
      fontFace: FONT, fontSize: 14, color: "C9DFF5", align: "right", margin: 0,
    });

    // 顶部小标签
    slide.addText("健康知识培训课程  ·  HEALTH TRAINING", {
      x: 1.5, y: 1.78, w: 10.33, h: 0.32,
      fontFace: FONT, fontSize: 12, color: "9CC4E8", align: "center",
      charSpacing: 3, margin: 0,
    });
    // 主标题
    slide.addText(s.title, {
      x: 1.2, y: 2.18, w: 10.93, h: 1.15,
      fontFace: FONT, fontSize: 50, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    // 副标题白 pill（跨弧边设计）
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 5.07, y: 3.5, w: 3.2, h: 0.64,
      fill: { color: C.white },
      rectRadius: 0.32,
      shadow: cardShadow(),
    });
    slide.addText(s.subtitle || data.meta.series, {
      x: 5.07, y: 3.5, w: 3.2, h: 0.64,
      fontFace: FONT, fontSize: 22, bold: true, color: C.navyDeep,
      align: "center", valign: "middle", margin: 0,
    });

    // 底部白区：左内训提示，右讲者信息卡
    slide.addText(data.meta.internal_notice || "仅限内部学习", {
      x: 0.7, y: 6.88, w: 5.5, h: 0.3,
      fontFace: FONT, fontSize: 10, color: C.muted, margin: 0,
    });
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 8.35, y: 5.72, w: 4.55, h: 1.28,
      fill: { color: "F0F6FC" },
      line: { color: C.line, width: 0.75 },
      rectRadius: 0.05,
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 8.35, y: 5.72, w: 0.14, h: 1.28, fill: { color: C.blue },
    });
    slide.addText([
      { text: (data.meta.presenter_name || "") + "　", options: { bold: true, fontSize: 15, color: C.ink } },
      { text: data.meta.presenter_title || "", options: { fontSize: 12.5, color: C.body } },
    ], {
      x: 8.72, y: 5.9, w: 4.05, h: 0.4,
      fontFace: FONT, margin: 0, valign: "middle",
    });
    slide.addText(data.meta.presenter_sub || "", {
      x: 8.72, y: 6.34, w: 4.05, h: 0.4,
      fontFace: FONT, fontSize: 11.5, color: C.muted, margin: 0, valign: "middle",
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
    // 图右深蓝竖线分隔
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 6.2, y: 0, w: 0.045, h: H, fill: { color: C.blueDeep },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 6.24, y: 0, w: W - 6.24, h: H, fill: { color: C.white },
    });
    const logo = asset("logo-shenke.png");
    if (logo) {
      const lh = 0.5;
      slide.addImage({ path: logo, x: 12.75 - logoW(lh), y: 0.3, w: logoW(lh), h: lh });
    }

    slide.addText(s.title, {
      x: 6.9, y: 0.98, w: 5.4, h: 0.68,
      fontFace: FONT, fontSize: 38, bold: true, color: C.blueDeep,
      align: "center", margin: 0,
    });
    slide.addText("CONTENTS", {
      x: 6.9, y: 1.66, w: 5.4, h: 0.3,
      fontFace: FONT, fontSize: 12, color: C.muted,
      align: "center", charSpacing: 4, margin: 0,
    });

    (s.items || []).forEach((it, i) => {
      const y = 2.12 + i * 0.94;
      // 白卡 + 投影
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.0, y, w: 5.15, h: 0.78,
        fill: { color: C.white },
        line: { color: C.line, width: 1 },
        rectRadius: 0.06,
        shadow: cardShadow(),
      });
      // 编号深蓝块
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.0, y, w: 0.78, h: 0.78,
        fill: { color: C.blueDeep },
        rectRadius: 0.06,
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 7.39, y, w: 0.39, h: 0.78,
        fill: { color: C.blueDeep },
      });
      slide.addText(it.num, {
        x: 7.0, y, w: 0.78, h: 0.78,
        fontFace: FONT, fontSize: 20, bold: true, color: C.white,
        align: "center", valign: "middle", margin: 0,
      });
      slide.addText(it.label, {
        x: 8.05, y, w: 3.95, h: 0.78,
        fontFace: FONT, fontSize: 20, bold: true, color: C.ink,
        valign: "middle", margin: 0,
      });
    });
    addFooter(slide, pageIdx, { left: false }); // 左半幅为深色建筑图，省略左侧品牌行
    continue;
  }

  // ========== DEFINITION + ETIOLOGY ==========
  if (st === "definition_etiology") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

    // 病名徽章：深蓝实心 pill
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y: 1.14, w: 4.6, h: 0.56,
      fill: { color: C.blueDeep },
      rectRadius: 0.06,
      shadow: cardShadow(),
    });
    slide.addText(s.badge, {
      x: 0.45, y: 1.14, w: 4.6, h: 0.56,
      fontFace: FONT, fontSize: T.badge, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });

    // 左文右图，避免整页纯字单调
    const illus = asset("overview-uri-illustration.png");
    const defW = illus ? 7.9 : 12.4;

    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y: 1.9, w: defW, h: 2.35,
      fill: { color: C.white },
      line: { color: C.quoteBorder, width: 1.75 },
      rectRadius: 0.06,
      shadow: cardShadow(),
    });
    slide.addText("“", {
      x: 0.6, y: 2.0, w: 0.55, h: 0.55,
      fontFace: FONT, fontSize: 40, bold: true, color: C.quoteBorder, margin: 0,
    });
    slide.addText(partsToRuns(s.definition_parts, T.body), {
      x: 1.2, y: 2.1, w: defW - 1.0, h: 1.95,
      fontFace: FONT, fontSize: T.body, color: C.body, valign: "middle",
    });

    if (illus) {
      addImageFrame(slide, illus, 8.55, 1.9, 4.3, 2.35, { pad: 0.08 });
    }

    // 病因
    addTitleChip(slide, s.etiology_title || "病因", 0.45, 4.5, 2.4);
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y: 5.05, w: 12.4, h: 1.95,
      fill: { color: C.white },
      line: { color: C.line, width: 1 },
      rectRadius: 0.05,
      shadow: cardShadow(),
    });
    slide.addText(partsToRuns(s.etiology_parts, T.body), {
      x: 0.7, y: 5.2, w: 11.9, h: 1.65,
      fontFace: FONT, fontSize: T.body, color: C.body, valign: "middle",
    });
    continue;
  }

  // ========== CLINICAL ==========
  if (st === "clinical_blocks") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

    const blocks = s.blocks || [];
    // 左栏三卡等高：底色标题条 + 正文；短文垂直居中，避免压到底栏
    const gap = 0.12;
    const n = Math.max(blocks.length, 1);
    const startY = 1.14;
    const endY = 6.0; // 提示条上方
    const blockH = (endY - startY - gap * (n - 1)) / n;
    let y = startY;
    blocks.forEach((b) => {
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.4, y, w: 7.7, h: blockH,
        fill: { color: C.white },
        line: { color: C.cardBorder, width: 1 },
        rectRadius: 0.06,
        shadow: cardShadow(),
      });
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.4, y, w: 7.7, h: 0.42,
        fill: { color: C.chipBg },
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
    if (throat) addImageFrame(slide, throat, 8.3, 1.14, 4.55, 2.36);
    if (oral) addImageFrame(slide, oral, 8.3, 3.62, 4.55, 2.36);

    // 询问诱因：整宽提示条（去掉无逻辑悬浮小图标）
    if (s.warning) {
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.4, y: 6.14, w: 12.5, h: 0.88,
        fill: { color: "FFF8E8" },
        line: { color: "F0D090", width: 1.25 },
        rectRadius: 0.05,
        shadow: cardShadow(),
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0.4, y: 6.14, w: 0.12, h: 0.88,
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
        x: 0.7, y: 6.2, w: 12.0, h: 0.76,
        fontFace: FONT, valign: "middle", margin: 0,
      });
    }
    continue;
  }

  // ========== EXAM ==========
  if (st === "exam_two_column") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

    // 左：体征说明卡
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.4, y: 1.14, w: 6.2, h: 3.2,
      fill: { color: C.white },
      line: { color: C.cardBorder, width: 1 },
      rectRadius: 0.06,
      shadow: cardShadow(),
    });
    addTitleChip(slide, "体格 / 实验室检查", 0.55, 1.28, 4.2);
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
    if (tonsils) addImageFrame(slide, tonsils, 0.4, 4.5, 6.2, 2.5);

    // 右：病原分型
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 6.85, y: 1.14, w: 6.05, h: 5.86,
      fill: { color: C.white },
      line: { color: C.cardBorder, width: 1 },
      rectRadius: 0.06,
      shadow: cardShadow(),
    });
    addTitleChip(slide, "常见病原体", 7.0, 1.28, 3.6);
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
        line: { color: "DCE8F4", width: 0.75 },
        rectRadius: 0.05,
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 7.05, y: py + 0.18, w: 0.06, h: 0.79,
        fill: { color: C.blueLine },
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
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);
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

    if (s.body_parts) addDashedBodyBox(slide, s.body_parts, 4.95, 2.05);
    else if (s.body) addDashedBodyBox(slide, s.body, 4.95, 2.05);
    continue;
  }

  // ========== TWO COL TABLE + PACKSHOT SLOTS ==========
  if (st === "two_col_table") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

    const headers = s.headers || ["临床症状", "对症用药"];
    const empMap = s.emphasize_in_rows || {};
    const rows = s.rows || [];
    const headH = 0.55;
    const tableX = 0.35;
    const tableY = 1.12;
    const tableW = 8.55;
    const col0W = 2.75;
    const col1W = tableW - col0W;
    const bodyH = 5.9;
    const dataRowH = (bodyH - headH) / Math.max(rows.length, 1);

    // 外框
    slide.addShape(pres.shapes.RECTANGLE, {
      x: tableX, y: tableY, w: tableW, h: bodyH,
      fill: { color: C.white },
      line: { color: C.tableHead, width: 1.5 },
    });
    // 表头
    slide.addShape(pres.shapes.RECTANGLE, {
      x: tableX, y: tableY, w: tableW, h: headH,
      fill: { color: C.tableHead },
    });
    slide.addText(headers[0], {
      x: tableX, y: tableY, w: col0W, h: headH,
      fontFace: FONT, fontSize: 17, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(headers[1], {
      x: tableX + col0W, y: tableY, w: col1W, h: headH,
      fontFace: FONT, fontSize: 17, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    // 中缝
    slide.addShape(pres.shapes.RECTANGLE, {
      x: tableX + col0W - 0.01, y: tableY, w: 0.02, h: bodyH,
      fill: { color: "8EB8D0" },
    });

    rows.forEach((r, ri) => {
      const y = tableY + headH + ri * dataRowH;
      // 左列（症状）：浅蓝底 + 加粗
      slide.addShape(pres.shapes.RECTANGLE, {
        x: tableX, y, w: col0W, h: dataRowH,
        fill: { color: ri % 2 === 0 ? "F5F9FC" : "EAF2F8" },
      });
      // 右列（药品）
      slide.addShape(pres.shapes.RECTANGLE, {
        x: tableX + col0W, y, w: col1W, h: dataRowH,
        fill: { color: ri % 2 === 0 ? C.white : C.tableAlt },
      });
      // 行底线
      slide.addShape(pres.shapes.RECTANGLE, {
        x: tableX, y: y + dataRowH - 0.012, w: tableW, h: 0.012,
        fill: { color: C.line },
      });
      slide.addText(r[0] || "", {
        x: tableX + 0.08, y, w: col0W - 0.16, h: dataRowH,
        fontFace: FONT, fontSize: 16, bold: true, color: C.ink,
        align: "center", valign: "middle", margin: 0,
      });
      // 重点药名深蓝加粗（参课截图）
      const keys = empMap[String(ri)] || empMap[ri] || [];
      slide.addText(emphasizeTextRuns(r[1] || "", keys, 16), {
        x: tableX + col0W + 0.16, y: y + 0.04, w: col1W - 0.3, h: dataRowH - 0.08,
        fontFace: FONT, fontSize: 16, color: C.body,
        align: "left", valign: "middle", margin: 0,
      });
    });

    // 右侧产品包装位
    const slots =
      s.packshot_slots || [
        { label: "复方氨酚烷胺胶囊", file: "pack-复方氨酚烷胺胶囊.png" },
        { label: "冬凌草糖浆", file: "pack-冬凌草糖浆.png" },
        { label: "磷酸奥司他韦颗粒", file: "pack-磷酸奥司他韦颗粒.png" },
        { label: "阿莫西林胶囊", file: "pack-阿莫西林胶囊.png" },
      ];
    const slotH = 1.38;
    const slotGap = 0.1;
    const slotTop = 1.12;
    slots.slice(0, 4).forEach((slot, i) => {
      const y = slotTop + i * (slotH + slotGap);
      addPackshotSlot(slide, slot.label, 9.15, y, 3.75, slotH, slot.file);
    });
    continue;
  }

  // ========== DRUG PRECAUTIONS TABLE ==========
  if (st === "drug_precautions_table") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

    const headers = s.headers || ["药品", "注意事项"];
    const headH = 0.5;
    const tableX = 0.45;
    const tableY = 1.15;
    const tableW = 12.4;
    const col0W = 2.35;
    const rows = s.rows || [];
    const n = Math.max(rows.length, 1);
    // 底边距：保证不超出页脚上方
    const maxBottom = 7.05;
    const bodyH = maxBottom - (tableY + headH);
    // 行少时略疏、行多时压入可用高度（绝不撑出页面）
    const preferred =
      n <= 2 ? 2.35 : n <= 3 ? 1.75 : n <= 4 ? 1.35 : 1.05;
    const rowH = Math.min(preferred, bodyH / n);
    const usedH = rowH * n;
    // 表头与首行紧贴，左右列同一 y/h，保证对齐
    const startY = tableY + headH;
    const tableH = headH + usedH;

    // 外框（表头+数据一体）
    slide.addShape(pres.shapes.RECTANGLE, {
      x: tableX, y: tableY, w: tableW, h: tableH,
      fill: { color: C.white },
      line: { color: C.tableHead, width: 1.25 },
    });
    // 表头
    slide.addShape(pres.shapes.RECTANGLE, {
      x: tableX, y: tableY, w: tableW, h: headH,
      fill: { color: C.tableHead },
    });
    slide.addText(headers[0], {
      x: tableX, y: tableY, w: col0W, h: headH,
      fontFace: FONT, fontSize: 17, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(headers[1], {
      x: tableX + col0W, y: tableY, w: tableW - col0W, h: headH,
      fontFace: FONT, fontSize: 17, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    // 中缝（整表等高）
    slide.addShape(pres.shapes.RECTANGLE, {
      x: tableX + col0W - 0.01, y: tableY, w: 0.02, h: tableH,
      fill: { color: "8EB8D0" },
    });

    // 字号：行矮时略收，避免溢出
    const noteSize = rowH >= 1.8 ? 15 : rowH >= 1.2 ? 14 : 13;
    const useSpacer = rowH >= 1.5; // 行够高才插空行

    rows.forEach((row, ri) => {
      const y = startY + ri * rowH;
      const bgL = ri % 2 === 0 ? "F5F9FC" : "EAF2F8";
      const bgR = ri % 2 === 0 ? C.white : C.tableAlt;
      // 左右列同 y、同 h
      slide.addShape(pres.shapes.RECTANGLE, {
        x: tableX, y, w: col0W, h: rowH, fill: { color: bgL },
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x: tableX + col0W, y, w: tableW - col0W, h: rowH, fill: { color: bgR },
      });
      if (ri < n - 1) {
        slide.addShape(pres.shapes.RECTANGLE, {
          x: tableX, y: y + rowH - 0.012, w: tableW, h: 0.012, fill: { color: C.line },
        });
      }
      slide.addText(String(row.drug || "").replace(/\n/g, "\n"), {
        x: tableX + 0.06, y, w: col0W - 0.12, h: rowH,
        fontFace: FONT, fontSize: 15, bold: true, color: C.ink,
        align: "center", valign: "middle", margin: 0,
      });
      const padY = Math.min(0.14, rowH * 0.1);
      slide.addText(noteBulletRuns(row.notes, noteSize, useSpacer), {
        x: tableX + col0W + 0.18, y: y + padY,
        w: tableW - col0W - 0.36, h: rowH - padY * 2,
        fontFace: FONT, fontSize: noteSize, color: C.body, valign: "middle",
      });
    });
    continue;
  }

  // ========== DUAL DRUG COLUMNS ==========
  if (st === "drug_precautions_dual") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

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
      x: 0.45, y: 1.7, w: 12.45, h: 5.28,
      fill: { color: C.white },
      line: { color: C.line, width: 0.75 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 1.85, y: 1.7, w: 0.02, h: 5.28, fill: { color: C.line },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 7.55, y: 1.7, w: 0.02, h: 5.28, fill: { color: C.line },
    });
    slide.addText("注意\n事项", {
      x: 0.5, y: 3.5, w: 1.3, h: 1.2,
      fontFace: FONT, fontSize: 16, bold: true, color: C.ink,
      align: "center", valign: "middle", margin: 0,
    });

    const leftRuns = noteBulletRuns(s.left_notes, 14);
    const rightRuns = noteBulletRuns(s.right_notes, 14);
    slide.addText(leftRuns, {
      x: 2.05, y: 1.95, w: 5.3, h: 4.85,
      fontFace: FONT, fontSize: 14, color: C.body, valign: "top",
    });
    slide.addText(rightRuns, {
      x: 7.75, y: 1.95, w: 4.95, h: 4.85,
      fontFace: FONT, fontSize: 14, color: C.body, valign: "top",
    });
    continue;
  }

  // ========== CARE THREE CARDS ==========
  if (st === "care_three_cards") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

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
        x, y: 2.35, w: 4.1, h: 4.62,
        fill: { color: C.white },
        line: { color: C.cardBorder, width: 1.25 },
        rectRadius: 0.08,
        shadow: cardShadow(),
      });
      const imgName = (s.images || [])[i];
      const p = asset(imgName);
      if (p) {
        slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
          x: x + 0.18, y: 2.53, w: 3.74, h: 2.62,
          fill: { color: "F7FAFD" },
          rectRadius: 0.05,
        });
        slide.addImage({
          path: p,
          x: x + 0.3, y: 2.58, w: 3.5, h: 2.52,
          sizing: { type: "contain", w: 3.5, h: 2.52 },
        });
      }
      slide.addShape(pres.shapes.RECTANGLE, {
        x: x + 0.25, y: 5.28, w: 3.6, h: 0.03,
        fill: { color: C.chipBg },
      });
      slide.addText(
        partsToRuns(card.parts || [{ text: card.body || "", emphasize: false }], T.bodySm),
        {
          x: x + 0.28, y: 5.42, w: 3.55, h: 1.42,
          fontFace: FONT, fontSize: T.bodySm, color: C.body, valign: "top",
        },
      );
    });
    continue;
  }

  // ========== CARE SPECIAL ==========
  if (st === "care_special") {
    addShenkeChrome(slide, s.section_num, s.section_title, pageIdx);

    // 三列整卡：上文下图，密度更高
    (s.cards || []).forEach((card, i) => {
      const x = 0.4 + i * 4.25;
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x, y: 1.15, w: 4.1, h: 5.85,
        fill: { color: C.white },
        line: { color: C.cardBorder, width: 1.5 },
        rectRadius: 0.08,
        shadow: cardShadow(),
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
    slide.background = { color: C.navy };
    for (let i = 0; i < 12; i++) {
      slide.addShape(pres.shapes.OVAL, {
        x: 0.3 + (i % 6) * 2.1, y: 0.4 + Math.floor(i / 6) * 3.2,
        w: 1.8, h: 1.2,
        fill: { color: "1A6BC4", transparency: 88 },
      });
    }
    // 底部白弧，与封面呼应
    slide.addShape(pres.shapes.OVAL, {
      x: -2.4, y: 5.95, w: 18.9, h: 4.6,
      fill: { color: "4A90D9", transparency: 35 },
    });
    slide.addShape(pres.shapes.OVAL, {
      x: -2.2, y: 6.28, w: 18.5, h: 4.6,
      fill: { color: C.white },
    });

    const logo = asset("logo-shenke-cover.png") || asset("logo-shenke.png");
    if (logo) {
      const lh = 0.5;
      slide.addImage({ path: logo, x: 12.75 - logoW(lh), y: 0.3, w: logoW(lh), h: lh });
    }

    slide.addText(s.title || "专业服务\n助力健康", {
      x: 1.9, y: 2.0, w: 9.5, h: 2.3,
      fontFace: FONT, fontSize: 46, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    // 标题下短 accent 条
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 6.17, y: 4.62, w: 1.0, h: 0.07,
      fill: { color: "7FB6E8" },
      rectRadius: 0.035,
    });

    // 讲者信息卡（白区上，与封面同款）
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 8.35, y: 5.82, w: 4.55, h: 1.28,
      fill: { color: "F0F6FC" },
      line: { color: C.line, width: 0.75 },
      rectRadius: 0.05,
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 8.35, y: 5.82, w: 0.14, h: 1.28, fill: { color: C.blue },
    });
    slide.addText(s.name || data.meta.presenter_name || "", {
      x: 8.72, y: 5.94, w: 4.05, h: 0.36,
      fontFace: FONT, fontSize: 14, bold: true, color: C.ink, margin: 0, valign: "middle",
    });
    slide.addText(s.title_line || "", {
      x: 8.72, y: 6.32, w: 4.05, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: C.body, margin: 0, valign: "middle",
    });
    slide.addText(s.sub_line || "", {
      x: 8.72, y: 6.64, w: 4.05, h: 0.3,
      fontFace: FONT, fontSize: 11.5, color: C.muted, margin: 0, valign: "middle",
    });
    continue;
  }

  // ========== ONE PAGE SUMMARY（方案A：16:9 画布内居中竖版手机比例 ~0.73）==========
  if (st === "one_page_summary") {
    // 两侧浅底 = 手机预览边距
    slide.background = { color: "E8EEF5" };

    // 竖版内容框：宽/高 ≈ 0.73（对齐 ref-18）
    const ph = 7.2;
    const pw = ph * 0.73; // ≈ 5.256
    const px = (W - pw) / 2;
    const py = (H - ph) / 2;

    // 外阴影感（底层略偏）
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: px + 0.05, y: py + 0.06, w: pw, h: ph,
      fill: { color: "C5D0DE" },
      rectRadius: 0.06,
    });
    // 主白卡
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: px, y: py, w: pw, h: ph,
      fill: { color: C.white },
      line: { color: C.blueDeep, width: 1.75 },
      rectRadius: 0.05,
    });

    // 内边距坐标（相对竖框）
    const ix = px + 0.18;
    const iw = pw - 0.36;
    let iy = py + 0.16;

    // 顶栏：系列
    const seriesLogo = asset("summary-series-logo.png");
    if (seriesLogo) {
      slide.addImage({
        path: seriesLogo, x: ix, y: iy, w: 1.06, h: 0.31,
        sizing: { type: "contain", w: 1.06, h: 0.31 },
      });
    }
    slide.addText(s.series_label || "健康顾问专业力系列", {
      x: ix + 1.12, y: iy, w: iw - 1.15, h: 0.32,
      fontFace: FONT, fontSize: 11, color: C.muted, valign: "middle", margin: 0,
    });
    iy += 0.42;

    // 深蓝标题条
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: ix, y: iy, w: iw, h: 0.48,
      fill: { color: C.blueDeep },
      rectRadius: 0.04,
    });
    slide.addText(s.header || "呼吸系统课程  急性上呼吸道感染", {
      x: ix, y: iy, w: iw, h: 0.48,
      fontFace: FONT, fontSize: 14, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    iy += 0.58;

    // 区块标签 + 正文
    function portraitBlock(label, bodyLines, blockH, opts = {}) {
      const tagW = 1.15;
      const tagH = 0.34;
      // 浅蓝方块装饰
      slide.addShape(pres.shapes.RECTANGLE, {
        x: ix, y: iy + 0.04, w: 0.14, h: 0.14,
        fill: { color: "8EB8E0" },
      });
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: ix + 0.22, y: iy, w: tagW, h: tagH,
        fill: { color: C.blueDeep },
        rectRadius: 0.03,
      });
      slide.addText(label, {
        x: ix + 0.22, y: iy, w: tagW, h: tagH,
        fontFace: FONT, fontSize: 11, bold: true, color: C.white,
        align: "center", valign: "middle", margin: 0,
      });
      const textX = ix + 0.22 + tagW + 0.12;
      const textW = iw - tagW - 0.34;
      if (typeof bodyLines === "string") {
        slide.addText(bodyLines, {
          x: textX, y: iy, w: textW, h: blockH,
          fontFace: FONT, fontSize: opts.fontSize || 11, color: C.body,
          valign: "top", margin: 0,
        });
      } else if (Array.isArray(bodyLines)) {
        slide.addText(bodyLines.join("\n"), {
          x: textX, y: iy, w: textW, h: blockH,
          fontFace: FONT, fontSize: opts.fontSize || 11, color: C.body,
          valign: "top", margin: 0,
        });
      }
      iy += blockH + 0.1;
    }

    portraitBlock("疾病概览", s.overview || "", 0.62, { fontSize: 11 });
    portraitBlock("临床表现", s.clinical || [], 1.05, { fontSize: 10.5 });

    // 治疗用药：标签 + 小表 + 包装三坑位
    {
      const tagW = 1.15;
      const tagH = 0.32;
      slide.addShape(pres.shapes.RECTANGLE, {
        x: ix, y: iy + 0.04, w: 0.14, h: 0.14,
        fill: { color: "8EB8E0" },
      });
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: ix + 0.22, y: iy, w: tagW, h: tagH,
        fill: { color: C.blueDeep },
        rectRadius: 0.03,
      });
      slide.addText("治疗用药", {
        x: ix + 0.22, y: iy, w: tagW, h: tagH,
        fontFace: FONT, fontSize: 11, bold: true, color: C.white,
        align: "center", valign: "middle", margin: 0,
      });
      iy += 0.38;

      const mt = s.med_table || { headers: [], rows: [] };
      const medRows = [
        (mt.headers || []).map((h) => ({
          text: h,
          options: {
            bold: true, color: C.white, align: "center", valign: "middle",
            fill: { color: C.tableHead }, fontSize: 10,
          },
        })),
        ...(mt.rows || []).map((r, i) =>
          r.map((c) => ({
            text: c,
            options: {
              color: C.body, align: "center", valign: "middle",
              fill: { color: i % 2 ? C.tableAlt : C.white },
              fontSize: 10,
            },
          })),
        ),
      ];
      const tableH = 1.05;
      slide.addTable(medRows, {
        x: ix + 0.1, y: iy, w: iw - 0.2, h: tableH,
        colW: [(iw - 0.2) * 0.2, (iw - 0.2) * 0.22, (iw - 0.2) * 0.58],
        border: [{ pt: 0.5, color: C.line }],
        fontFace: FONT,
        fontSize: 10,
      });
      iy += tableH + 0.1;

      // 三个包装坑位横排
      const packLabels = ["阿莫西林胶囊", "冬凌草糖浆", "维生素C"];
      const pW = (iw - 0.2) / 3;
      packLabels.forEach((lab, i) => {
        addPackshotSlot(slide, lab, ix + 0.1 + i * pW, iy, pW - 0.08, 0.82, null);
      });
      iy += 0.95;
    }

    // 专业关怀：标签行 + 全文（预留底部，不压边）
    {
      const tagW = 1.15;
      const tagH = 0.32;
      const bottomLimit = py + ph - 0.18;
      slide.addShape(pres.shapes.RECTANGLE, {
        x: ix, y: iy + 0.04, w: 0.14, h: 0.14,
        fill: { color: "8EB8E0" },
      });
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: ix + 0.22, y: iy, w: tagW, h: tagH,
        fill: { color: C.blueDeep },
        rectRadius: 0.03,
      });
      slide.addText("专业关怀", {
        x: ix + 0.22, y: iy, w: tagW, h: tagH,
        fontFace: FONT, fontSize: 11, bold: true, color: C.white,
        align: "center", valign: "middle", margin: 0,
      });
      iy += 0.38;

      const careH = Math.max(1.0, bottomLimit - iy);
      // 不用截图裁切小医生（易带残字/残标）；关怀正文铺满
      slide.addText((s.care || []).join("\n"), {
        x: ix + 0.12,
        y: iy,
        w: iw - 0.15,
        h: careH,
        fontFace: FONT, fontSize: 11, color: C.body, valign: "top", margin: 0,
      });
    }

    // 画布两侧提示（培训：可手机转发）
    slide.addText("手机竖版一页通 · 可截图转发", {
      x: 0.2, y: H - 0.35, w: 3.5, h: 0.25,
      fontFace: FONT, fontSize: 10, color: "8A9AAB", margin: 0,
    });
    continue;
  }

  // fallback
  addShenkeChrome(slide, s.section_num || "00", s.section_title || s.id || "页面", pageIdx);
  slide.addText("未识别 scene_type: " + st, {
    x: 1, y: 3, w: 10, h: 1,
    fontFace: FONT, fontSize: 16, color: C.red,
  });
}

await pres.writeFile({ fileName: OUT });
console.log("Wrote", OUT);
console.log("Slides:", data.slides.length);
console.log("v2: redrawn assets + typography scale + named packshot slots");
