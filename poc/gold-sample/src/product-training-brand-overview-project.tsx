import {
  Audio,
  Circle,
  Img,
  Rect,
  Txt,
  makeScene2D,
} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeOutBack,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../product-training-brand-overview.json';
import {
  DashenlinBrandHeader,
  DashenlinInternalNotice,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';

type Cue = {start: number; end: number; text: string};

const DURATION = Number(
  (data as {playback_duration?: number; referenceRange?: {duration?: number}})
    .playback_duration ??
    (data as {referenceRange?: {duration?: number}}).referenceRange?.duration ??
    13.04,
);
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const cues = data.cues as Cue[];

function* runSubtitles(ref: Reference<Txt>) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      ref().opacity(0);
      yield* waitFor(cue.start - cursor);
    }
    ref().text(cue.text);
    yield* ref().opacity(1, 0.035);
    yield* waitFor(Math.max(0, cue.end - cue.start - 0.035));
    ref().opacity(0);
    cursor = cue.end;
  }
}

export const productTrainingBrandOverviewScene = makeScene2D('product-training-brand-overview', function* (view) {
  const product = createRef<Img>();
  const productBadge = createRef<Rect>();
  const labels = [0, 1, 2].map(() => createRef<Rect>());
  const subtitle = createRef<Txt>();
  const transitionTitle = createRef<Txt>();

  view.add(
    <>
      <Rect size={[1920, 1080]} fill={'#83cfea'} />
      <Rect
        position={[0, 475]}
        size={[1920, 130]}
        fill={'rgba(53,176,220,0.28)'}
      />
      <Audio src={data.audio.file} play />
      <DashenlinBrandHeader />
      <Img
        key={'editable:q10:brand:product'}
        ref={product}
        src={data.assets.product}
        position={[-80, 0]}
        size={[1100, 619]}
        opacity={0}
        scale={0.2}
        rotation={-5}
      />
      <Rect
        key={'editable:q10:brand:product-badge'}
        ref={productBadge}
        position={[-80, 350]}
        size={[320, 54]}
        radius={27}
        fill={'rgba(255,255,255,0.95)'}
        stroke={'#cf4245'}
        lineWidth={3}
        opacity={0}
      >
        <Txt
          key={'editable:q10:brand:product-badge:text'}
          text={'重新制作包装示意'}
          fontFamily={FONT}
          fontSize={27}
          fontWeight={750}
          fill={'#b64043'}
        />
      </Rect>
      {['90粒大包装', '原研工艺', '海外原料'].map((text, index) => (
        <Rect
          key={`editable:q10:brand:label:${index}`}
          ref={labels[index]}
          position={[445, -95 + index * 145]}
          size={[510, 100]}
          opacity={0}
          scale={0.45}
        >
          <Txt
            key={`editable:q10:brand:label:${index}:shadow`}
            position={[7, 7]}
            text={text}
            fontFamily={FONT}
            fontSize={60}
            fontWeight={900}
            fill={'#56bb5b'}
          />
          <Txt
            text={text}
            fontFamily={FONT}
            fontSize={60}
            fontWeight={900}
            fill={'#ffffff'}
            stroke={'#ee761c'}
            lineWidth={5}
          />
        </Rect>
      ))}
      <Txt
        key={'editable:q10:brand:transition-title'}
        ref={transitionTitle}
        position={[0, -100]}
        text={'两大核心功效'}
        fontFamily={FONT}
        fontSize={86}
        fontWeight={900}
        fill={'#ffffff'}
        stroke={'#273441'}
        lineWidth={5}
        opacity={0}
      />
      <Txt
        key={'editable:q10:brand:subtitle'}
        ref={subtitle}
        position={[-40, 455]}
        width={1640}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={60}
        fontWeight={900}
        fill={'#ffe733'}
        stroke={'rgba(24,36,55,0.98)'}
        lineWidth={3.5}
        shadowColor={'rgba(0,0,0,0.28)'}
        shadowBlur={4}
        opacity={0}
      />
      <DashenlinInternalNotice />
    </>,
  );

  function* visualTimeline() {
    yield* all(
      product().opacity(1, 0.16),
      product().scale(1, 0.72, easeOutBack),
      product().rotation(0, 0.72, easeOutCubic),
    );
    yield* productBadge().opacity(1, 0.14);
    for (const label of labels) {
      yield* all(
        label().opacity(1, 0.12),
        label().scale(1, 0.28, easeOutBack),
      );
      yield* label().rotation(2.5, 0.08, easeOutCubic);
      yield* label().rotation(0, 0.08, easeOutCubic);
      yield* waitFor(0.08);
    }
    yield* waitFor(9.9);
    yield* all(
      product().opacity(0, 0.18),
      productBadge().opacity(0, 0.18),
      ...labels.map(label => label().opacity(0, 0.18)),
    );
    yield* transitionTitle().opacity(1, 0.22);
    yield* waitFor(0.2);
  }

  yield* all(visualTimeline(), runSubtitles(subtitle), applyEditablePatches(view, DURATION + 1));
});

export default makeProject({
  scenes: [productTrainingBrandOverviewScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#83cfea',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
