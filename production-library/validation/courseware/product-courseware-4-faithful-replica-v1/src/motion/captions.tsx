/**
 * 字幕层（editor 工程与 film 工程单源）。
 * 底栏讲解字幕：近黑字 + 白描边 8 向技法（对标参考，禁止白字）。
 */
import {Txt} from '@revideo/2d';
import {waitFor} from '@revideo/core';

import type {Scene} from '../content';
import {CAPTION, FONT, OUTLINE_8, WHITE} from './primitives';

export function captionText(sc: Scene): string {
  const subs = sc.subtitles || [];
  if (subs.length) return subs[0].text || '';
  return '';
}

/**
 * 字幕切段：每段文本持续到下一段开始；相邻字幕间有空隙时插空文本段
 * （参考片句间清空，不让上一句一直挂到下一句）。
 */
export function captionSegments(sc: Scene): {dur: number; text: string}[] {
  const start = Number(sc.start);
  const end = Number(sc.end);
  const raw = sc.subtitles || [];
  if (!raw.length) {
    return [{dur: Math.max(0.1, end - start), text: ''}];
  }
  const segs: {dur: number; text: string}[] = [];
  for (let i = 0; i < raw.length; i++) {
    const t0 = i === 0 ? start : Math.max(start, Number(raw[i].t));
    const t1 = i + 1 < raw.length ? Math.min(end, Number(raw[i + 1].t)) : end;
    segs.push({
      dur: Math.max(0.05, t1 - t0),
      text: raw[i].text || '',
    });
  }
  return segs;
}

/** 底栏讲解字幕：黑字 + 白描边（对标参考，禁止白字） */
export function CaptionLayer({
  page,
  text,
  keyPrefix = 'cap',
}: {
  page: string;
  text: string;
  /** editor 用 'cap'；film 用 'film-cap' 避免编辑器误选 */
  keyPrefix?: string;
}) {
  const pos: [number, number] = [0, 988 + 28 - 540];
  const scale = 3;
  return (
    <>
      {OUTLINE_8.flatMap(([dx, dy], i) =>
        Array.from({length: scale}, (_, s) => (
          <Txt
            key={`${keyPrefix}-out-${page}-${i}-${s}`}
            text={text}
            fontFamily={FONT}
            fontSize={56}
            fontWeight={700}
            fill={WHITE}
            position={[pos[0] + dx * (s + 1), pos[1] + dy * (s + 1)]}
            textAlign="center"
            width={1700}
            textWrap={true}
          />
        )),
      )}
      <Txt
        key={keyPrefix === 'cap' ? `caption-${page}` : `${keyPrefix}-main-${page}`}
        text={text}
        fontFamily={FONT}
        fontSize={56}
        fontWeight={700}
        fill={CAPTION}
        position={pos}
        textAlign="center"
        width={1700}
        textWrap={true}
      />
    </>
  );
}

/** editor 工程字幕 key 序列（保持既有 'caption-{page}' / 'cap-out-*' 契约） */
export function* playCaptions(view: any, sc: Scene, keyPrefix = 'cap') {
  const segs = captionSegments(sc);
  const mainKey =
    keyPrefix === 'cap' ? `caption-${sc.id}` : `${keyPrefix}-main-${sc.id}`;
  const keys = [
    mainKey,
    ...OUTLINE_8.flatMap((_, i) =>
      [0, 1, 2].map(s => `${keyPrefix}-out-${sc.id}-${i}-${s}`),
    ),
  ];
  for (const seg of segs) {
    for (const key of keys) {
      const node = view.findKey(key);
      if (node && typeof node.text === 'function') {
        node.text(seg.text || '');
      }
    }
    yield* waitFor(seg.dur);
  }
}
