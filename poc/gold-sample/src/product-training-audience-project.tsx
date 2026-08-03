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
  easeInCubic,
  easeOutBack,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../product-training-audience.json';
import {
  DashenlinBrandMark,
  DashenlinInternalNotice,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';

type Cue = {start: number; end: number; text: string};

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const cues = data.cues as Cue[];
const PAIR_POSITIONS: [number, number][] = [[-430, 95], [120, 95]];

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

export const productTrainingAudienceScene = makeScene2D('product-training-audience', function* (view) {
  const mainTitle = createRef<Txt>();
  const subtitle = createRef<Txt>();
  const images = [0, 1, 2, 3, 4, 5].map(() => createRef<Img>());
  const flashes = [0, 1, 2, 3, 4, 5].map(() => createRef<Txt>());
  const keywordGroups = [0, 1, 2].map(() => createRef<Rect>());

  const sources = [
    ...data.assets.heart,
    ...data.assets.muscle,
    ...data.assets.fertility,
  ];

  view.add(
    <>
      <Rect size={[1920, 1080]} fill={'#83cfea'} />
      <Rect position={[0, 475]} size={[1920, 130]} fill={'rgba(53,176,220,0.28)'} />
      <Audio src={data.audio.file} play />
      <DashenlinBrandMark />
      <Txt key={'editable:q10:audience:title'} ref={mainTitle} position={[0, -425]} text={'适宜人群'} fontFamily={FONT} fontSize={96} fontWeight={900} fill={'#ffffff'} stroke={'#273441'} lineWidth={6} />
      {sources.map((src, index) => (
        <Img
          key={`editable:q10:audience:image:${index}`}
          ref={images[index]}
          src={src}
          position={PAIR_POSITIONS[index % 2]}
          size={index < 2 ? [590, 590] : [470, 470]}
          opacity={0}
          scale={0.08}
          shadowColor={'rgba(33,78,98,0.24)'}
          shadowBlur={14}
        />
      ))}
      {sources.map((_, index) => (
        <Txt
          ref={flashes[index]}
          position={PAIR_POSITIONS[index % 2]}
          text={'✦'}
          fontFamily={FONT}
          fontSize={200}
          fontWeight={900}
          fill={'#ffffff'}
          opacity={0}
          scale={0.2}
          shadowColor={'#ffffff'}
          shadowBlur={34}
        />
      ))}
      <Rect ref={keywordGroups[0]} position={[650, 70]} size={[360, 440]} opacity={0}>
        {['顽固心慌', '胸闷', '气短'].map((text, index) => (
          <Txt position={[0, -130 + index * 130]} text={text} fontFamily={FONT} fontSize={58} fontWeight={900} fill={'#d09a42'} stroke={'#694415'} lineWidth={2.5} shadowColor={'rgba(255,255,255,0.75)'} shadowBlur={8} />
        ))}
      </Rect>
      <Rect ref={keywordGroups[1]} position={[650, 70]} size={[360, 440]} opacity={0}>
        {['肌肉疲劳', '疼痛'].map((text, index) => (
          <Txt position={[0, -75 + index * 150]} text={text} fontFamily={FONT} fontSize={60} fontWeight={900} fill={'#d09a42'} stroke={'#694415'} lineWidth={2.5} shadowColor={'rgba(255,255,255,0.75)'} shadowBlur={8} />
        ))}
      </Rect>
      <Rect ref={keywordGroups[2]} position={[650, 60]} size={[300, 470]} opacity={0}>
        {['备', '孕', '男', '女'].map((text, index) => (
          <Txt position={[0, -180 + index * 120]} text={text} fontFamily={FONT} fontSize={72} fontWeight={900} fill={'#d09a42'} stroke={'#694415'} lineWidth={2.5} shadowColor={'rgba(255,255,255,0.75)'} shadowBlur={8} />
        ))}
      </Rect>
      <Txt
        key={'editable:q10:audience:subtitle'}
        ref={subtitle}
        position={[-40, 455]}
        width={1640}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={58}
        fontWeight={900}
        fill={'#ffe733'}
        stroke={'rgba(24,36,55,0.98)'}
        lineWidth={3.5}
        opacity={0}
      />
      <DashenlinInternalNotice />
    </>,
  );

  function* reveal(index: number) {
    yield* all(flashes[index]().opacity(1, 0.08), flashes[index]().scale(0.82, 0.12, easeOutBack));
    yield* all(
      images[index]().opacity(1, 0.1),
      images[index]().scale(1, 0.32, easeOutBack),
      flashes[index]().opacity(0, 0.22, easeInCubic),
      flashes[index]().scale(1.6, 0.22, easeOutCubic),
    );
  }

  function* hideGroup(group: number) {
    yield* all(
      images[group * 2]().opacity(0, 0.14),
      images[group * 2 + 1]().opacity(0, 0.14),
      keywordGroups[group]().opacity(0, 0.14),
    );
  }

  function* visualTimeline() {
    yield* waitFor(0.34);
    yield* reveal(0);
    yield* waitFor(0.36);
    yield* reveal(1);
    yield* keywordGroups[0]().opacity(1, 0.22);
    yield* waitFor(1.86);
    yield* hideGroup(0);

    yield* reveal(2);
    yield* waitFor(0.34);
    yield* reveal(3);
    yield* keywordGroups[1]().opacity(1, 0.22);
    yield* waitFor(1.48);
    yield* hideGroup(1);

    yield* reveal(4);
    yield* waitFor(0.24);
    yield* reveal(5);
    yield* keywordGroups[2]().opacity(1, 0.18);
    yield* waitFor(0.40);
    yield* all(
      images[4]().opacity(0, 0.14),
      images[5]().opacity(0, 0.14),
      keywordGroups[2]().opacity(0, 0.14),
      mainTitle().opacity(0, 0.14),
    );
    mainTitle().text('联合用药');
    mainTitle().position([0, -100]);
    mainTitle().scale(0.78);
    yield* all(mainTitle().opacity(1, 0.12), mainTitle().scale(1, 0.22, easeOutBack));
  }

  yield* all(visualTimeline(), runSubtitles(subtitle), applyEditablePatches(view, 11));
});

export default makeProject({
  scenes: [productTrainingAudienceScene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
