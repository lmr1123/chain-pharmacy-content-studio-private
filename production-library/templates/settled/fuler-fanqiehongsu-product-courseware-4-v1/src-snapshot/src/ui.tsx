/**
 * 共享可视化组件（editor 工程与 film 工程单源）。
 * CTxt/EImg/EditableChapter/YellowLabel：可编辑层组件，key=editable:cw4:*
 */
import {Img, Txt} from '@revideo/2d';

import {K, assetSrc} from './content';
import {FONT, OUTLINE_8, RED_OUTLINE, WHITE, YELLOW, box} from './motion/primitives';

export {assetSrc};

export function bgSrc(pageId: string) {
  return `/stills-editor-bg/${pageId}.png`;
}

/**
 * Center-anchored editable text with width+wrap.
 * position is center of the layout box.
 */
export function CTxt({
  page,
  role,
  text,
  x,
  y,
  w,
  h,
  fontSize,
  fill,
  fontWeight = 700,
  align = 'left',
  keyNs,
}: {
  page: string;
  role: string;
  text: string;
  x: number;
  y: number;
  w: number;
  h: number;
  fontSize: number;
  fill: string;
  fontWeight?: number;
  align?: 'left' | 'center' | 'right';
  /** 覆盖默认 editable key（film 装饰文案用） */
  keyNs?: string;
}) {
  const b = box(x, y, w, h);
  return (
    <Txt
      key={keyNs ?? K(page, role)}
      text={text}
      fontFamily={FONT}
      fontSize={fontSize}
      fontWeight={fontWeight}
      fill={fill}
      position={b.position}
      width={w}
      textAlign={align}
      textWrap={true}
    />
  );
}

/** Editable image. (cx,cy)=center in 1920×1080; size = display box. */
export function EImg({
  page,
  role,
  src,
  cx,
  cy,
  size,
  w,
  h,
  opacity = 1,
  scale = 1,
  keyNs,
}: {
  page: string;
  role: string;
  src: string;
  cx: number;
  cy: number;
  size?: number;
  w?: number;
  h?: number;
  opacity?: number;
  scale?: number;
  keyNs?: string;
}) {
  const ww = w ?? size ?? 200;
  const hh = h ?? size ?? 200;
  return (
    <Img
      key={keyNs ?? K(page, role)}
      src={src}
      position={[cx - 960, cy - 540]}
      size={[ww, hh]}
      opacity={opacity}
      scale={scale}
    />
  );
}

/** Editable text with wrap (default wrap on when width set)
 *  @deprecated 现无调用方（保留备查）；新代码用 CTxt
 */
export function ETxt({
  page,
  role,
  text,
  x,
  y,
  w,
  h,
  fontSize,
  fill,
  fontWeight = 700,
  align = 'left',
}: {
  page: string;
  role: string;
  text: string;
  x: number;
  y: number;
  w: number;
  h: number;
  fontSize: number;
  fill: string;
  fontWeight?: number;
  align?: 'left' | 'center' | 'right';
}) {
  const b = box(x, y, w, h);
  return (
    <Txt
      key={K(page, role)}
      text={text}
      fontFamily={FONT}
      fontSize={fontSize}
      fontWeight={fontWeight}
      fill={fill}
      position={b.position}
      width={w}
      height={h}
      textAlign={align}
      textWrap={true}
      offset={[-1, -1]}
    />
  );
}

/** Centered horizontal chain centers (match PIL paste_chain_centered).
 *  现无调用方（保留）：film 链路页排版可用 */
export function chainCxs(sizes: number[], gap = 48): number[] {
  if (!sizes.length) return [];
  const total = sizes.reduce((a, b) => a + b, 0) + gap * (sizes.length - 1);
  let x = (1920 - total) / 2;
  return sizes.map(w => {
    const cx = x + w / 2;
    x += w + gap;
    return cx;
  });
}

/** 章节标题：黄字 + 红描边（7 向偏移技法，对标参考） */
export function EditableChapter({
  page,
  text,
  y = 40,
}: {
  page: string;
  text: string;
  y?: number;
}) {
  // PIL chapter_title: x=(1920-tw)/2 → visual center at canvas x=960 → Revideo x=0
  const cy = y + 44 - 540;
  return (
    <>
      {[
        [-4, -4],
        [4, -4],
        [-4, 4],
        [4, 4],
        [0, 4],
        [-3, 0],
        [3, 0],
      ].map(([dx, dy], i) => (
        <Txt
          key={`out-${page}-${i}`}
          text={text}
          fontFamily={FONT}
          fontSize={88}
          fontWeight={900}
          fill={RED_OUTLINE}
          position={[dx, cy + dy]}
          textAlign="center"
        />
      ))}
      <Txt
        key={K(page, 'chapter')}
        text={text}
        fontFamily={FONT}
        fontSize={88}
        fontWeight={900}
        fill={YELLOW}
        position={[0, cy]}
        textAlign="center"
      />
    </>
  );
}

/** 黄字 + 红描边（适宜人群标签等，对标参考） */
export function YellowLabel({
  page,
  role,
  text,
  cx,
  y,
  w = 320,
  fontSize = 42,
}: {
  page: string;
  role: string;
  text: string;
  cx: number;
  y: number;
  w?: number;
  fontSize?: number;
}) {
  const pos: [number, number] = [cx - 960, y + fontSize / 2 - 540];
  const scale = 3;
  return (
    <>
      {OUTLINE_8.flatMap(([dx, dy], i) =>
        Array.from({length: scale}, (_, s) => (
          <Txt
            key={`yl-out-${page}-${role}-${i}-${s}`}
            text={text}
            fontFamily={FONT}
            fontSize={fontSize}
            fontWeight={900}
            fill={RED_OUTLINE}
            position={[pos[0] + dx * (s + 1), pos[1] + dy * (s + 1)]}
            textAlign="center"
            width={w}
          />
        )),
      )}
      <Txt
        key={K(page, role)}
        text={text}
        fontFamily={FONT}
        fontSize={fontSize}
        fontWeight={900}
        fill={YELLOW}
        position={pos}
        textAlign="center"
        width={w}
      />
    </>
  );
}
