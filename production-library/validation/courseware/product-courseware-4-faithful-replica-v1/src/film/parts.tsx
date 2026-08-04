/**
 * film 基础构件：丝绸底、章节、表头、描边文字、图/文节点工厂。
 * 可见性契约（editor-bg = PIL omit_text 精确复刻）：
 *   chrome   两模式都渲染；editable 仅 film。
 *   描边副本 key 用 film:decor:*，可见性跟随主层。
 */
import {Img, Line, Node, Rect, Txt} from '@revideo/2d';

import {K} from '../content';
import {CHAPTER, SILK_BG, hSize, imgAt, type SectionSpec} from '../layout';
import {FONT, OUTLINE_8, box} from '../motion/primitives';

export type FilmMode = 'film' | 'editor-bg';
export type Layer = 'chrome' | 'editable';

export const vis = (mode: FilmMode, layer: Layer) =>
  mode === 'film' || layer === 'chrome';

export const chromeKey = (page: string, role: string) =>
  `film:chrome:${page}:${role}`;
export const wrapKey = (page: string, role: string) =>
  `film:wrap:${page}:${role}`;

const toRev = ([x, y]: [number, number]): [number, number] => [
  x - 960,
  y - 540,
];

function hexRgba(hex: string, alpha: number): string {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha.toFixed(3)})`;
}

/** 章节描边 7 向偏移（PIL chapter_title） */
const CHAPTER_OUT: [number, number][] = [
  [-4, -4],
  [4, -4],
  [-4, 4],
  [4, 4],
  [0, 4],
  [-3, 0],
  [3, 0],
];

/** 丝绸底褶皱纹（chrome，两模式都画） */
export function SilkFolds() {
  return (
    <>
      {SILK_BG.lightFolds.map((f, i) => (
        <Line
          key={`silk-light-${i}`}
          points={f.points.map(toRev)}
          closed={true}
          fill={hexRgba(f.fill, f.alpha)}
        />
      ))}
      {SILK_BG.darkFolds.map((f, i) => (
        <Line
          key={`silk-dark-${i}`}
          points={f.points.map(toRev)}
          closed={true}
          fill={hexRgba(f.fill, f.alpha)}
        />
      ))}
    </>
  );
}

/** PIL 多边形（远山等） */
export function Poly({
  k,
  points,
  fill,
}: {
  k: string;
  points: [number, number][];
  fill: string;
}) {
  return <Line key={k} points={points.map(toRev)} closed={true} fill={fill} />;
}

/**
 * 描边文字：主层 + 8 向 × steps 描边副本，整体包一层 wrapper（pivot=文字中心，
 * 动效 pop wrapper 不影响子节点坐标）。wrapper key = wrapKey(page, role)。
 */
export function OutlineTxt({
  mode,
  layer,
  page,
  role,
  text,
  cx,
  cy,
  width,
  fontSize,
  weight,
  fill,
  outline,
  steps,
  align = 'center',
  lineHeight,
  pre,
}: {
  mode: FilmMode;
  layer: Layer;
  page: string;
  role: string;
  text: string;
  cx: number;
  cy: number;
  width: number;
  fontSize: number;
  weight: number;
  fill: string;
  outline: string;
  steps: number;
  align?: 'left' | 'center' | 'right';
  lineHeight?: number;
  /** 入场预置（仅 film）：opacity/scale/dy */
  pre?: {opacity?: number; scale?: number; dy?: number};
}) {
  if (!vis(mode, layer)) return null;
  const p = pre ?? {};
  const pos: [number, number] = [
    cx - 960,
    cy - 540 + (p.dy ?? 0),
  ];
  return (
    <Node
      key={wrapKey(page, role)}
      position={pos}
      opacity={p.opacity ?? 1}
      scale={p.scale ?? 1}
    >
      {OUTLINE_8.flatMap(([dx, dy], i) =>
        Array.from({length: steps}, (_, s) => (
          <Txt
            key={`film:decor:${page}:${role}-out-${i}-${s}`}
            text={text}
            fontFamily={FONT}
            fontSize={fontSize}
            fontWeight={weight}
            fill={outline}
            position={[dx * (s + 1), dy * (s + 1)]}
            textAlign={align}
            width={width}
            lineHeight={lineHeight}
          />
        )),
      )}
      <Txt
        key={layer === 'editable' ? K(page, role) : chromeKey(page, role)}
        text={text}
        fontFamily={FONT}
        fontSize={fontSize}
        fontWeight={weight}
        fill={fill}
        position={[0, 0]}
        textAlign={align}
        width={width}
        lineHeight={lineHeight}
      />
    </Node>
  );
}

/** 章节标题：黄字 + 红描边 7 向（editable；wrapper key = wrapKey(page,'chapter')） */
export function FilmChapter({
  mode,
  page,
  text,
  y,
  pre,
}: {
  mode: FilmMode;
  page: string;
  text: string;
  y: number;
  pre?: {opacity?: number; scale?: number};
}) {
  if (!vis(mode, 'editable')) return null;
  const cy = y + CHAPTER.font / 2 - 540;
  return (
    <Node
      key={wrapKey(page, 'chapter')}
      position={[0, cy]}
      opacity={pre?.opacity ?? 1}
      scale={pre?.scale ?? 1}
    >
      {CHAPTER_OUT.map(([dx, dy], i) => (
        <Txt
          key={`film:decor:${page}:chapter-out-${i}`}
          text={text}
          fontFamily={FONT}
          fontSize={CHAPTER.font}
          fontWeight={900}
          fill={CHAPTER.outline}
          position={[dx, dy]}
          textAlign="center"
        />
      ))}
      <Txt
        key={K(page, 'chapter')}
        text={text}
        fontFamily={FONT}
        fontSize={CHAPTER.font}
        fontWeight={900}
        fill={CHAPTER.fill}
        position={[0, 0]}
        textAlign="center"
      />
    </Node>
  );
}

/** 表头小节：白箭头（chrome，K(page,'section_chevron')）+ 棕红字白描边（editable） */
export function FilmSection({
  mode,
  page,
  spec,
  chevPre,
}: {
  mode: FilmMode;
  page: string;
  spec: SectionSpec;
  chevPre?: {opacity?: number; scale?: number};
}) {
  const chevW = spec.chevSize;
  return (
    <>
      <Img
        key={K(page, 'section_chevron')}
        src={`/assets/icon-chevron-white.png`}
        position={[
          spec.chevX + chevW / 2 - 960,
          spec.chevY + chevW / 2 - 540,
        ]}
        size={[chevW, chevW]}
        opacity={chevPre?.opacity ?? 1}
        scale={chevPre?.scale ?? 1}
      />
      <OutlineTxt
        mode={mode}
        layer="editable"
        page={page}
        role="section"
        text={spec.text}
        cx={spec.x + 760}
        cy={spec.y + spec.font / 2}
        width={1520}
        fontSize={spec.font}
        weight={700}
        fill={spec.fill}
        outline="#ffffff"
        steps={2}
        align="left"
      />
    </>
  );
}

/** 图片节点（cx/cy PIL 中心；h 定高宽随比例；pre 入场预置） */
export function FImg({
  mode,
  layer,
  page,
  role,
  asset,
  cx,
  cy,
  h,
  rotation,
  pre,
}: {
  mode: FilmMode;
  layer: Layer;
  page: string;
  role: string;
  asset: string;
  cx: number;
  cy: number;
  h: number;
  rotation?: number;
  pre?: {opacity?: number; scale?: number; dy?: number};
}) {
  if (!vis(mode, layer)) return null;
  const [w, hh] = hSize(asset, h);
  const p = pre ?? {};
  const pos = imgAt(cx, cy + (p.dy ?? 0));
  return (
    <Img
      key={layer === 'editable' ? K(page, role) : chromeKey(page, role)}
      src={`/assets/${asset}`}
      position={pos}
      size={[w, hh]}
      rotation={rotation ?? 0}
      opacity={p.opacity ?? 1}
      scale={p.scale ?? 1}
    />
  );
}

/** 纯文字节点（无描边；left/center 对齐；pre 入场预置） */
export function FTxt({
  mode,
  layer,
  page,
  role,
  text,
  cx,
  cy,
  width,
  fontSize,
  weight,
  fill,
  align = 'left',
  lineHeight,
  pre,
}: {
  mode: FilmMode;
  layer: Layer;
  page: string;
  role: string;
  text: string;
  cx: number;
  cy: number;
  width: number;
  fontSize: number;
  weight: number;
  fill: string;
  align?: 'left' | 'center' | 'right';
  lineHeight?: number;
  pre?: {opacity?: number; scale?: number; dy?: number};
}) {
  if (!vis(mode, layer)) return null;
  const p = pre ?? {};
  return (
    <Txt
      key={layer === 'editable' ? K(page, role) : chromeKey(page, role)}
      text={text}
      fontFamily={FONT}
      fontSize={fontSize}
      fontWeight={weight}
      fill={fill}
      position={[cx - 960, cy - 540 + (p.dy ?? 0)]}
      textAlign={align}
      width={width}
      lineHeight={lineHeight}
      opacity={p.opacity ?? 1}
      scale={p.scale ?? 1}
    />
  );
}

/** chrome 圆角矩形（卡片/胶囊/导航 pill） */
export function ChromeRect({
  page,
  role,
  x,
  y,
  w,
  h,
  radius,
  fill,
  stroke,
  strokeW,
  pre,
}: {
  page: string;
  role: string;
  x: number;
  y: number;
  w: number;
  h: number;
  radius?: number;
  fill?: string;
  stroke?: string;
  strokeW?: number;
  pre?: {opacity?: number; scale?: number; dy?: number};
}) {
  const p = pre ?? {};
  const b = box(x, y + (p.dy ?? 0), w, h);
  return (
    <Rect
      key={chromeKey(page, role)}
      position={b.position}
      size={[w, h]}
      radius={radius ?? 0}
      fill={fill}
      stroke={stroke}
      lineWidth={strokeW}
      opacity={p.opacity ?? 1}
      scale={p.scale ?? 1}
    />
  );
}
