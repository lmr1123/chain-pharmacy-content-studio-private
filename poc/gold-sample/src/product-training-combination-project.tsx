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

import data from '../product-training-combination.json';
import {productName, screenOf} from './product-training-content';

const PRODUCT = productName(data as any);
const SCREEN = screenOf(data as any);
/** Content-driven: N combo lines (never invent empty 3rd row). */
const COMBO_SECTIONS: string[] =
  SCREEN.combo_sections && SCREEN.combo_sections.length > 0
    ? SCREEN.combo_sections
    : [`1、联合方案＋${PRODUCT}`];
const COMBO_COUNT = COMBO_SECTIONS.length;
const PACK_BADGE = SCREEN.pack_badge || '重新制作包装示意';
import {
  DashenlinBrandMark,
  DashenlinInternalNotice,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';

type Cue = {start: number; end: number; text: string};

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const cues = data.cues as Cue[];

function DanshenPack() {
  return (
    <Rect size={[560, 380]}>
      <Rect position={[-70, 20]} size={[390, 250]} fill={'#f5fff6'} stroke={'#20994d'} lineWidth={6} shadowColor={'rgba(39,78,54,0.24)'} shadowBlur={16}>
        <Rect position={[0, -88]} size={[390, 72]} fill={'#1f9c4d'} />
        <Txt position={[0, -88]} text={'复方丹参滴丸'} fontFamily={FONT} fontSize={43} fontWeight={900} fill={'#ffffff'} />
        <Txt position={[0, 15]} text={'无品牌包装示意'} fontFamily={FONT} fontSize={31} fontWeight={750} fill={'#1d743c'} />
        <Rect position={[0, 84]} size={[290, 28]} radius={14} fill={'#ccefd6'} />
      </Rect>
      <Rect position={[185, 55]} size={[130, 230]} radius={[30, 30, 52, 52]} fill={'#2aac58'} stroke={'#16713a'} lineWidth={6}>
        <Rect position={[0, -128]} size={[96, 48]} radius={12} fill={'#e8f6eb'} stroke={'#16713a'} lineWidth={4} />
        <Circle position={[0, 38]} size={56} fill={'#d6f5df'} />
      </Rect>
    </Rect>
  );
}

function StatinPack() {
  return (
    <Rect size={[560, 380]}>
      <Rect position={[-20, 20]} size={[470, 270]} radius={12} fill={'#ffffff'} stroke={'#4466a7'} lineWidth={6} shadowColor={'rgba(38,58,96,0.24)'} shadowBlur={16}>
        <Rect position={[-168, 0]} size={[120, 270]} fill={'#e9eefb'} />
        <Circle position={[-168, -54]} size={58} stroke={'#567ac1'} lineWidth={10} />
        <Txt position={[55, -55]} text={'他汀类药物'} fontFamily={FONT} fontSize={47} fontWeight={900} fill={'#293b69'} />
        <Txt position={[55, 18]} text={'无品牌包装示意'} fontFamily={FONT} fontSize={29} fontWeight={700} fill={'#566b92'} />
        <Rect position={[55, 80]} size={[260, 30]} radius={15} fill={'#dbe5f8'} />
      </Rect>
    </Rect>
  );
}

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

export const productTrainingCombinationScene = makeScene2D('product-training-combination', function* (view) {
  const mainTitle = createRef<Txt>();
  const sectionTitle = createRef<Txt>();
  const danshen = createRef<Rect>();
  const statin = createRef<Rect>();
  const plus = createRef<Txt>();
  const product = createRef<Img>();
  const partnerFlash = createRef<Txt>();
  const subtitle = createRef<Txt>();

  view.add(
    <>
      <Rect size={[1920, 1080]} fill={'#83cfea'} />
      <Rect position={[0, 475]} size={[1920, 130]} fill={'rgba(53,176,220,0.28)'} />
      <Audio src={data.audio.file} play />
      <DashenlinBrandMark />
      <Txt key={'editable:q10:combo:title'} ref={mainTitle} position={[0, -445]} text={'联合用药'} fontFamily={FONT} fontSize={88} fontWeight={900} fill={'#ffffff'} stroke={'#273441'} lineWidth={6} />
      <Txt key={'editable:q10:combo:section'} ref={sectionTitle} position={[0, -325]} text={COMBO_SECTIONS[0]} fontFamily={FONT} fontSize={53} fontWeight={900} fill={'#c95c49'} stroke={'#ffffff'} lineWidth={4} />
      <Rect ref={danshen} position={[-470, 90]} opacity={0} scale={0.2}><DanshenPack /></Rect>
      <Rect ref={statin} position={[-470, 90]} opacity={0} scale={0.2}><StatinPack /></Rect>
      <Txt ref={plus} position={[0, 85]} text={'＋'} fontFamily={FONT} fontSize={125} fontWeight={900} fill={'#ffe24d'} stroke={'#ffffff'} lineWidth={6} opacity={0} scale={0.2} />
      <Img key={'editable:q10:combo:product'} ref={product} src={data.assets.product} position={[450, 80]} size={[720, 405]} opacity={0} scale={0.2} />
      <Txt ref={partnerFlash} position={[-470, 90]} text={'✦'} fontFamily={FONT} fontSize={230} fontWeight={900} fill={'#ffffff'} shadowColor={'#ffffff'} shadowBlur={36} opacity={0} scale={0.2} />
      <Rect position={[450, 330]} size={[320, 52]} radius={26} fill={'rgba(255,255,255,0.94)'} stroke={'#cb484c'} lineWidth={3}>
        <Txt text={PACK_BADGE} fontFamily={FONT} fontSize={26} fontWeight={750} fill={'#b53f43'} />
      </Rect>
      <Txt
        key={'editable:q10:combo:subtitle'}
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

  function* visualTimeline() {
    // Beat 1 — first combo line (always if N>=1)
    sectionTitle().text(COMBO_SECTIONS[0]);
    yield* all(danshen().opacity(1, 0.12), danshen().scale(1, 0.46, easeOutBack));
    yield* all(plus().opacity(1, 0.1), plus().scale(1, 0.32, easeOutBack));
    yield* all(product().opacity(1, 0.12), product().scale(1, 0.48, easeOutBack));
    yield* waitFor(COMBO_COUNT > 1 ? 12.9 : 8.5);

    // Beat 2 — only when business provided a second line
    if (COMBO_COUNT > 1) {
      yield* all(
        danshen().opacity(0, 0.18),
        danshen().scale(0.7, 0.2, easeInCubic),
        partnerFlash().opacity(1, 0.1),
        partnerFlash().scale(0.86, 0.14, easeOutBack),
      );
      sectionTitle().text(COMBO_SECTIONS[1]);
      yield* all(
        statin().opacity(1, 0.12),
        statin().scale(1, 0.38, easeOutBack),
        partnerFlash().opacity(0, 0.26, easeInCubic),
        partnerFlash().scale(1.62, 0.26, easeOutCubic),
      );
      yield* waitFor(10.42);
    }

    // Extra lines (N>2): cycle section title only (shared packshot beat)
    for (let i = 2; i < COMBO_COUNT; i++) {
      sectionTitle().text(COMBO_SECTIONS[i]);
      yield* waitFor(4.2);
    }

    yield* all(
      sectionTitle().opacity(0, 0.16),
      danshen().opacity(0, 0.16),
      statin().opacity(0, 0.16),
      plus().opacity(0, 0.16),
      product().opacity(0, 0.16),
      mainTitle().opacity(0, 0.16),
    );
    mainTitle().text('总结');
    mainTitle().position([0, -100]);
    mainTitle().scale(0.78);
    yield* all(mainTitle().opacity(1, 0.12), mainTitle().scale(1, 0.22, easeOutBack));
  }

  yield* all(visualTimeline(), runSubtitles(subtitle), applyEditablePatches(view, 29));
});

export default makeProject({
  scenes: [productTrainingCombinationScene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
