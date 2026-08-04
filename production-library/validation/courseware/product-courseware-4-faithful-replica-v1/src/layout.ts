/**
 * layout.ts — 番茄课件 15 页版式单一来源。
 * 逐行抄录自 scripts/export-full-film-video.py 的 render_scene / silk_bg，
 * 坐标全部保持 PIL 原生系（1920×1080，左上原点，y 向下）：
 *   - 图片：cx/cy 为中心 + h（宽由 ASSET_DIMS 宽高比推出，复刻 paste_c）
 *   - 文字：x/y 为字形顶左（PIL draw.text 锚点）+ font 字号
 * film 工程（src/film/*）唯一消费方；editor 工程阶段 2 起逐步替换字面量。
 * 改版式只改这里，禁止在 pages.tsx 写坐标字面量。
 */
import {chainCxs} from './ui';

// ── 资产真实像素（2026-08-04 sips 实测，PIL 链路宽度计算依赖）────────────
export const ASSET_DIMS: Record<string, readonly [number, number]> = {
  'tomato.png': [732, 818],
  'arrow-red-ref.png': [900, 620],
  'prostate-diagram.png': [900, 874],
  'o2-cutout.png': [747, 826],
  'mark-red-x-hand.png': [657, 726],
  'skincare-woman.png': [802, 1013],
  'nk-cell-labeled.png': [640, 640],
  'flex-arm-cutout.png': [823, 780],
  'softgel.png': [394, 894],
  'five-tomatoes.png': [900, 895],
  'slot-time-magazine.png': [400, 580],
  'map-xinjiang.png': [900, 704],
  'slot-photo-vine-cutout.png': [1120, 720],
  'slot-photo-tomato.png': [1280, 720],
  'slot-pack-box-a.png': [420, 560],
  'slot-pack-box-b.png': [420, 560],
  'slot-pack-bottle.png': [360, 580],
  'slot-pack-lycopene.png': [420, 560],
  'slot-pack-zinc.png': [360, 480],
  'badge-hot-recommend.png': [280, 280],
  'icon-check-red.png': [180, 180],
  'icon-chevron-lime.png': [128, 128],
  'icon-chevron-white.png': [256, 256],
  'couple.png': [900, 830],
  'audience-beauty.png': [852, 880],
  'audience-weak.png': [880, 880],
};

/** 按 PIL paste_c(max_h) 语义：高缩到 maxH，宽按宽高比等比 */
export function hSize(name: string, maxH: number): [number, number] {
  const d = ASSET_DIMS[name];
  if (!d) throw new Error(`ASSET_DIMS missing: ${name}`);
  return [(maxH * d[0]) / d[1], maxH];
}

/** PIL draw.text 顶左锚点 → Revideo Txt（center pivot + textAlign 左，宽 w 不换行） */
export function textAt(x: number, y: number, w: number, fontSize: number) {
  return {
    position: [x + w / 2 - 960, y + fontSize / 2 - 540] as [number, number],
    width: w,
  };
}

/** PIL 居中文字（x=(1920-tw)/2）→ Revideo 水平居中位置 */
export function textCenterAt(y: number, fontSize: number) {
  return [0, y + fontSize / 2 - 540] as [number, number];
}

/** PIL paste_c 中心 → Revideo position */
export function imgAt(cx: number, cy: number) {
  return [cx - 960, cy - 540] as [number, number];
}

export interface ChainItemSpec {
  asset: string;
  h: number;
}
export interface ChainItemLayout extends ChainItemSpec {
  w: number;
  cx: number;
}
/** 复刻 PIL paste_chain_centered：实际宽度整体水平居中，返回每项 cx/w */
export function chainLayout(
  items: ChainItemSpec[],
  gap: number,
): ChainItemLayout[] {
  const sizes = items.map(it => hSize(it.asset, it.h));
  const cxs = chainCxs(
    sizes.map(s => s[0]),
    gap,
  );
  return items.map((it, i) => ({...it, w: sizes[i][0], cx: cxs[i]}));
}

// ── 丝绸底（silk_bg 抄录：暖底 + 斜向亮褶/暗褶多边形）────────────────────
export const SILK_BG = {
  base: '#cecbc4',
  /** 白色亮褶：[(x0,0),(x0+420,0),(x0+820,1080),(x0+200,1080)] */
  lightFolds: [18, 14, 10, 8].map((a, i) => {
    const x0 = -200 + i * 180;
    return {
      alpha: a / 255,
      fill: '#ffffff',
      points: [
        [x0, 0],
        [x0 + 420, 0],
        [x0 + 820, 1080],
        [x0 + 200, 1080],
      ] as [number, number][],
    };
  }),
  /** 灰褐暗褶：[(x0,0),(x0+280,0),(x0+100,1080),(x0-180,1080)] */
  darkFolds: [12, 9, 6].map((a, i) => {
    const x0 = 400 + i * 220;
    return {
      alpha: a / 255,
      fill: '#aaa59e',
      points: [
        [x0, 0],
        [x0 + 280, 0],
        [x0 + 100, 1080],
        [x0 - 180, 1080],
      ] as [number, number][],
    };
  }),
};

/** 表头小节（paste_section_label）：白箭头 62px 持续 bounce + 棕红字白描边 */
export interface SectionSpec {
  text: string;
  chevX: number;
  chevY: number;
  chevSize: number;
  x: number;
  y: number;
  font: number;
  fill: string;
}
function section(text: string, y = 150): SectionSpec {
  return {
    text,
    chevX: 92,
    chevY: y - 4,
    chevSize: 62,
    x: 170,
    y: y + 4,
    font: 56,
    fill: '#a05040',
  };
}

/** 章节标题（chapter_title）：黄字 #ffe33c + 红描边 #ba3034，Black 88 */
export const CHAPTER = {font: 88, fill: '#ffe33c', outline: '#ba3034'};

// ── 逐页版式 ────────────────────────────────────────────────────────────

/** S00_cover / S15_end 共用（PIL 同一分支） */
export const COVER = {
  mountains: {
    fill: 'rgba(190,190,190,0.47)', // (190,190,190,120)
    points: [
      [0, 1080],
      [0, 860],
      [300, 780],
      [600, 900],
      [960, 740],
      [1400, 880],
      [1920, 800],
      [1920, 1080],
    ] as [number, number][],
  },
  pill: {
    y0: 52,
    y1: 152,
    padX: 56,
    radius: 56,
    fill: 'rgba(120,120,120,0.78)', // (120,120,120,200)
    font: 68,
    textY: 72,
    textFill: '#ffffff',
    fallback: '福尔番茄红素软胶囊',
  },
  badge: {asset: 'badge-hot-recommend.png', cx: 1720, cy: 140, h: 200},
  benefits: {
    icon: 'icon-check-red.png',
    iconSize: 76,
    iconX: 108,
    y0: 290,
    step: 108,
    textX: 210,
    textDY: 14,
    font: 52,
    fill: '#1a1a1a',
    fallback: [
      '保护前列腺，提高精子活力',
      '抗氧化，延缓衰老',
      '增强免疫力',
    ],
  },
  packs: [
    {asset: 'slot-pack-box-a.png', cx: 1120, cy: 540, h: 420},
    {asset: 'slot-pack-box-b.png', cx: 1400, cy: 540, h: 420},
    {asset: 'slot-pack-bottle.png', cx: 1660, cy: 520, h: 460},
  ],
};

export const S01 = {
  magazine: {asset: 'slot-time-magazine.png', cx: 405.5, cy: 540, h: 558},
  card: {
    x: 769,
    y: 277,
    w: 978,
    h: 520,
    radius: 48,
    fill: 'rgba(50,50,50,0.74)', // (50,50,50,188)
  },
  chevron: {asset: 'icon-chevron-lime.png', x: 820, y: 330, size: 72},
  cardTitle: {
    x: 910,
    y: 340,
    font: 42,
    fill: '#e9f200',
    fallback: '对人类健康贡献最大的10种健康食品',
  },
  rule: {x0: 820, x1: 1680, y: 420, width: 4, fill: '#e9f200'},
  list: {
    x: 860,
    y0: 460,
    step: 100,
    font: 68,
    fill: '#f2f2f2',
    rows: 3,
    fallback: ['1.番茄', '2.***', '3.***'],
  },
};

export const S02 = {
  photo: {asset: 'slot-photo-tomato.png', cx: 960, cy: 480, h: 640},
};

export const S03 = {
  items: [
    {asset: 'slot-photo-vine-cutout.png', cx: 400, cy: 500, h: 440},
    {asset: 'slot-pack-box-a.png', cx: 1000, cy: 520, h: 440},
    {asset: 'slot-pack-box-b.png', cx: 1280, cy: 520, h: 440},
    {asset: 'slot-pack-bottle.png', cx: 1560, cy: 500, h: 480},
  ],
};

export const S04 = {
  chapterY: 40,
  chapterFallback: '一、三大核心功效',
  section: section('1、保护前列腺、提高精子活力'),
  chain: {
    cy: 580,
    gap: 56,
    items: [
      {asset: 'tomato.png', h: 360},
      {asset: 'arrow-red-ref.png', h: 110},
      {asset: 'prostate-diagram.png', h: 400},
    ] as ChainItemSpec[],
  },
};

export const S05 = {
  chapterY: 40,
  chapterFallback: '一、三大核心功效',
  section: section('2、抗氧化，延缓衰老'),
  chain: {
    cy: 580,
    gap: 40,
    items: [
      {asset: 'tomato.png', h: 260},
      {asset: 'arrow-red-ref.png', h: 110},
      {asset: 'o2-cutout.png', h: 260},
      {asset: 'arrow-red-ref.png', h: 110},
      {asset: 'skincare-woman.png', h: 280},
    ] as ChainItemSpec[],
  },
  /** 手绘红叉：中心压在 O2 上，略倾斜 */
  redX: {asset: 'mark-red-x-hand.png', h: 250, rot: -6},
};

export const S06 = {
  chapterY: 40,
  chapterFallback: '一、三大核心功效',
  section: section('3、增强免疫力'),
  chain: {
    cy: 580,
    gap: 40,
    items: [
      {asset: 'tomato.png', h: 260},
      {asset: 'arrow-red-ref.png', h: 110},
      {asset: 'nk-cell-labeled.png', h: 300},
      {asset: 'arrow-red-ref.png', h: 110},
      {asset: 'flex-arm-cutout.png', h: 300},
    ] as ChainItemSpec[],
  },
};

export const S07 = {
  chapterY: 40,
  chapterFallback: '二、产品特点',
  section: section('1、产地好'),
  mapCaption: {
    y: 240,
    font: 36,
    fill: '#555555',
    fallback: '中国分省地图—新疆维吾尔自治区',
  },
  map: {asset: 'map-xinjiang.png', cx: 960, cy: 580, h: 460},
};

export const S08 = {
  chapterY: 40,
  chapterFallback: '二、产品特点',
  section: section('2、原料优'),
  photo: {asset: 'slot-photo-vine-cutout.png', cx: 960, cy: 560, h: 520},
};

export const S09 = {
  chapterY: 40,
  chapterFallback: '二、产品特点',
  section: section('3、含量高'),
  /** PIL 直接把名义槽宽 [300,140,400] 传给 chain_centers */
  slots: {widths: [300, 140, 400], gap: 40, cy: 560},
  softgel: {asset: 'softgel.png', h: 280},
  eq: {y: 470, font: 140, fill: '#e8c020'},
  five: {asset: 'five-tomatoes.png', h: 380},
};

export const S10 = {
  chapterY: 40,
  chapterFallback: '三、适宜人群',
  marginX: 100,
  cols: 4,
  iconCy: 500,
  iconH: 300,
  labelY: 680,
  labelFont: 42,
  labelFill: '#ffe33c',
  labelOutline: '#ba3034',
  items: [
    {asset: 'prostate-diagram.png', label: '前列腺患病'},
    {asset: 'couple.png', label: '备孕男士和女士'},
    {asset: 'audience-beauty.png', label: '爱美人士'},
    {asset: 'audience-weak.png', label: '身体虚弱人群'},
  ],
};

export const S11 = {
  chapterY: 22,
  chapterFallback: '五、福尔番茄红素三大核心功效',
  table: {
    x0: 148,
    y0: 138,
    x1: 1772,
    y1: 980,
    leftW: 420,
    stroke: '#6a6a6a',
    strokeW: 3,
    rows: 3,
  },
  chevron: {asset: 'icon-chevron-lime.png', size: 52, dx: 22},
  label: {
    xOff: 88,
    font: 48,
    lh: 58,
    fill: '#9a3c2e',
    outline: '#ffffff',
    outlineW: 3,
  },
  body: {
    xOff: 32,
    padRight: 56,
    font: 40,
    lh: 54,
    fill: '#8a3a28',
    outline: '#ffffff',
    outlineW: 2,
  },
  side: {
    font: 30,
    fill: '#4a4a4a',
    step: 36,
    leftX: 42,
    leftY: 200,
    rightX: 1810,
    rightY: 180,
    leftFallback: '不适宜人群：少年儿童、孕妇、乳母',
    rightFallback: '每日1次，每次1粒，建议固定随餐服用，避免漏服',
  },
  rowsFallback: [
    {
      label: '保护前列腺、\n提高精子活力',
      body: '番茄红素具有抗氧化与调节细胞生长代谢的功能，能活化前列腺细胞，抑制致癌物的产生，保护前列腺，提高精子活力',
    },
    {
      label: '抗氧化，\n延缓衰老',
      body: '番茄红素可通过物理和化学方式猝灭单线态氧或捕捉过氧化自由基，抗氧化能力是维E的100倍，从而达到延缓衰老的作用',
    },
    {
      label: '增强免疫力',
      body: '番茄红素可活化免疫细胞，保护吞噬细胞免受自身的氧化损伤，促进淋巴细胞增殖，从而增强免疫力',
    },
  ],
};

/** S12_related_1 / S13_related_2 共用 */
export const RELATED = {
  chapterY: 36,
  chapterFallback: '四、关联用药',
  nav: {
    y: 150,
    h: 62,
    widths: [860, 820],
    xs: [100, 1000],
    font: 28, // PIL 原作 26，按 1080p 字号下限约束（导航 28-32）上调
    numFont: 24,
    active: '#c43c2c',
    inactive: '#d8d4cc',
    activeText: '#ffffff',
    inactiveText: '#555555',
    labelDX: 64,
    labelDY: 16,
    circleDX: 34,
    r: 16,
    fallback: [
      '番茄红素+锌/硒（备孕与男性健康）',
      '番茄红素+维生素E（抗氧化协同）',
    ],
  },
  note: {y: 250, font: 36, fill: '#3a2a28'},
  card: {
    x0: 120,
    y0: 330,
    x1: 1800,
    y1: 980,
    radius: 36,
    fill: 'rgba(255,255,255,0.94)', // (255,255,255,240)
  },
  left: {
    cx: 520,
    cy: 620,
    h: 400,
    labelY: 870,
    font: 32,
    fill: '#6a3a30',
    packFallback: 'slot-pack-lycopene.png',
    labelFallback: '福尔番茄红素软胶囊',
  },
  right: {
    cx: 1320,
    cy: 620,
    h: 360,
    labelY: 870,
    font: 32,
    fill: '#6a3a30',
    packFallback: 'slot-pack-zinc.png',
    labelFallback: '关联品',
  },
  plus: {y: 540, font: 120, fill: '#c43c2c'},
};

/** 页面 id → 版式（S00/S15 共用 COVER；S12/S13 共用 RELATED） */
export function layoutFor(sceneId: string) {
  switch (sceneId) {
    case 'S00_cover':
    case 'S15_end':
      return {kind: 'cover' as const, spec: COVER};
    case 'S01_time_list':
      return {kind: 's01' as const, spec: S01};
    case 'S02_broll':
      return {kind: 's02' as const, spec: S02};
    case 'S03_product_intro':
      return {kind: 's03' as const, spec: S03};
    case 'S04_benefit_1':
      return {kind: 's04' as const, spec: S04};
    case 'S05_benefit_2':
      return {kind: 's05' as const, spec: S05};
    case 'S06_benefit_3':
      return {kind: 's06' as const, spec: S06};
    case 'S07_origin':
      return {kind: 's07' as const, spec: S07};
    case 'S08_material':
      return {kind: 's08' as const, spec: S08};
    case 'S09_content':
      return {kind: 's09' as const, spec: S09};
    case 'S10_audience':
      return {kind: 's10' as const, spec: S10};
    case 'S11_summary':
      return {kind: 's11' as const, spec: S11};
    case 'S12_related_1':
    case 'S13_related_2':
      return {kind: 'related' as const, spec: RELATED};
    default:
      throw new Error(`no layout for scene ${sceneId}`);
  }
}
