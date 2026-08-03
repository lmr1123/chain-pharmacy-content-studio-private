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

import data from '../product-training-efficacy.json';
import {
  DashenlinBrandMark,
  DashenlinInternalNotice,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';

type Cue = {start: number; end: number; text: string};

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const cues = data.cues as Cue[];
const CARD_POSITIONS: [number, number][] = [
  [-510, 90],
  [0, 90],
  [510, 90],
];

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

export const productTrainingEfficacyScene = makeScene2D('product-training-efficacy', function* (view) {
  const mainTitle = createRef<Txt>();
  const sectionTitle = createRef<Txt>();
  const board = createRef<Rect>();
  const subtitle = createRef<Txt>();
  const energyCards = [0, 1, 2].map(() => createRef<Img>());
  const energyFlashes = [0, 1, 2].map(() => createRef<Txt>());
  const antioxidantCards = [0, 1, 2].map(() => createRef<Img>());
  const antioxidantFlashes = [0, 1, 2].map(() => createRef<Txt>());

  view.add(
    <>
      <Rect size={[1920, 1080]} fill={'#83cfea'} />
      <Rect position={[0, 475]} size={[1920, 130]} fill={'rgba(53,176,220,0.28)'} />
      <Audio src={data.audio.file} play />
      <DashenlinBrandMark />
      <Txt
        key={'editable:q10:efficacy:title'}
        ref={mainTitle}
        position={[0, -445]}
        text={'两大核心功效'}
        fontFamily={FONT}
        fontSize={88}
        fontWeight={900}
        fill={'#ffffff'}
        stroke={'#273441'}
        lineWidth={6}
        shadowColor={'rgba(255,255,255,0.7)'}
        shadowBlur={12}
      />
      <Txt
        key={'editable:q10:efficacy:section'}
        ref={sectionTitle}
        position={[0, -325]}
        text={'1.促进能量生成'}
        fontFamily={FONT}
        fontSize={56}
        fontWeight={900}
        fill={'#c95c49'}
        stroke={'#ffffff'}
        lineWidth={4}
      />
      <Rect
        ref={board}
        position={[-20, 110]}
        size={[1580, 530]}
        fill={'rgba(255,255,255,0.055)'}
        shadowColor={'rgba(36,104,135,0.24)'}
        shadowBlur={26}
      />
      {data.assets.energy.map((src, index) => (
        <Img
          key={`editable:q10:efficacy:energy:${index}`}
          ref={energyCards[index]}
          src={src}
          position={CARD_POSITIONS[index]}
          size={[410, 410]}
          opacity={0}
          scale={0.08}
          shadowColor={'rgba(30,67,89,0.22)'}
          shadowBlur={10}
        />
      ))}
      {data.assets.energy.map((_, index) => (
        <Txt
          ref={energyFlashes[index]}
          position={CARD_POSITIONS[index]}
          text={'✦'}
          fontFamily={FONT}
          fontSize={190}
          fontWeight={900}
          fill={'#ffffff'}
          opacity={0}
          scale={0.2}
          shadowColor={'#ffffff'}
          shadowBlur={32}
        />
      ))}
      {data.assets.antioxidant.map((src, index) => (
        <Img
          key={`editable:q10:efficacy:antioxidant:${index}`}
          ref={antioxidantCards[index]}
          src={src}
          position={CARD_POSITIONS[index]}
          size={[410, 410]}
          opacity={0}
          scale={0.08}
          shadowColor={'rgba(30,67,89,0.22)'}
          shadowBlur={10}
        />
      ))}
      {data.assets.antioxidant.map((_, index) => (
        <Txt
          ref={antioxidantFlashes[index]}
          position={CARD_POSITIONS[index]}
          text={'✦'}
          fontFamily={FONT}
          fontSize={190}
          fontWeight={900}
          fill={'#ffffff'}
          opacity={0}
          scale={0.2}
          shadowColor={'#ffffff'}
          shadowBlur={32}
        />
      ))}
      <Txt
        key={'editable:q10:efficacy:subtitle'}
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
        shadowColor={'rgba(0,0,0,0.28)'}
        shadowBlur={4}
        opacity={0}
      />
      <DashenlinInternalNotice />
    </>,
  );

  function* revealEvidence(card: Reference<Img>, flash: Reference<Txt>) {
    yield* all(
      flash().opacity(1, 0.08, easeOutCubic),
      flash().scale(0.82, 0.12, easeOutBack),
    );
    yield* all(
      card().opacity(1, 0.12),
      card().scale(1, 0.34, easeOutBack),
      flash().opacity(0, 0.24, easeInCubic),
      flash().scale(1.65, 0.24, easeOutCubic),
    );
  }

  function* hidePage(cards: Reference<Img>[]) {
    yield* all(
      ...cards.map((card, index) =>
        all(
          card().opacity(0, 0.16 + index * 0.02),
          card().scale(0.84, 0.18 + index * 0.02, easeInCubic),
        ),
      ),
    );
  }

  function* visualTimeline() {
    yield* waitFor(1.90);
    yield* revealEvidence(energyCards[0], energyFlashes[0]);
    yield* waitFor(2.67);
    yield* revealEvidence(energyCards[1], energyFlashes[1]);
    yield* waitFor(3.31);
    yield* revealEvidence(energyCards[2], energyFlashes[2]);
    yield* waitFor(4.00);

    yield* hidePage(energyCards);
    sectionTitle().text('2.抗氧化，减少组织细胞损伤');
    yield* sectionTitle().scale(1.06, 0.10, easeOutCubic);
    yield* sectionTitle().scale(1, 0.10, easeOutCubic);
    yield* waitFor(1.14);

    yield* revealEvidence(antioxidantCards[0], antioxidantFlashes[0]);
    yield* waitFor(2.46);
    yield* revealEvidence(antioxidantCards[1], antioxidantFlashes[1]);
    yield* waitFor(3.76);
    yield* revealEvidence(antioxidantCards[2], antioxidantFlashes[2]);
    yield* waitFor(4.96);

    yield* all(
      mainTitle().opacity(0, 0.16),
      sectionTitle().opacity(0, 0.16),
      board().opacity(0, 0.16),
      ...antioxidantCards.map(card => card().opacity(0, 0.16)),
    );
    mainTitle().text('产品特点');
    mainTitle().position([0, -100]);
    mainTitle().scale(0.78);
    yield* all(
      mainTitle().opacity(1, 0.12),
      mainTitle().scale(1, 0.22, easeOutBack),
    );
  }

  yield* all(visualTimeline(), runSubtitles(subtitle), applyEditablePatches(view, 33));
});

export default makeProject({
  scenes: [productTrainingEfficacyScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
    },
  },
});
