import {Audio, Circle, Img, Line, Rect, Txt, makeScene2D} from '@revideo/2d';
import {
  Reference, all, createRef, easeInCubic, easeOutBack, easeOutCubic,
  loop, makeProject, waitFor,
} from '@revideo/core';

import data from '../product-training-opening.json';
import {
  DashenlinBrandMark,
  DashenlinInternalNotice,
  ProductColumnBadge,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';

const OPENING_DURATION = 19;

type Cue = {start: number; end: number; text: string};
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const cues = data.cues as Cue[];

function Pattern() {
  return (
    <>
      <Txt position={[-690, -320]} text={'╬  ╬'} fontFamily={FONT} fontSize={112} fill={'rgba(22,112,210,0.22)'} />
      <Txt position={[-360, -85]} text={'╬'} fontFamily={FONT} fontSize={150} fill={'rgba(22,112,210,0.22)'} />
      <Txt position={[30, -350]} text={'╬  ╬'} fontFamily={FONT} fontSize={118} fill={'rgba(22,112,210,0.22)'} />
      <Txt position={[520, -70]} text={'╬'} fontFamily={FONT} fontSize={150} fill={'rgba(22,112,210,0.22)'} />
      <Txt position={[-700, 260]} text={'╬'} fontFamily={FONT} fontSize={130} fill={'rgba(22,112,210,0.22)'} />
      <Txt position={[-110, 290]} text={'╬  ╬'} fontFamily={FONT} fontSize={115} fill={'rgba(22,112,210,0.22)'} />
      <Txt position={[610, 300]} text={'╬'} fontFamily={FONT} fontSize={130} fill={'rgba(22,112,210,0.22)'} />
    </>
  );
}

function OfficeBackdrop() {
  return (
    <Rect size={[1500, 760]}>
      <Rect position={[540, 20]} size={[210, 36]} fill={'#ffffff'} />
      <Rect position={[540, -18]} size={[165, 34]} fill={'#ec4d62'} />
      <Rect position={[535, -56]} size={[140, 34]} fill={'#1c3151'} />
      <Rect position={[525, -94]} size={[188, 34]} fill={'#ffffff'} />
      <Circle position={[-610, -190]} size={130} fill={'#ffffff'} stroke={'#17203a'} lineWidth={7}>
        <Line points={[[0, 0], [0, -44]]} stroke={'#17203a'} lineWidth={7} />
        <Line points={[[0, 0], [35, 14]]} stroke={'#17203a'} lineWidth={7} />
      </Circle>
      <Rect position={[380, -210]} size={[440, 100]} radius={8} fill={'#ffffff'} stroke={'#d5d9e2'} lineWidth={5}>
        <Rect position={[0, 20]} size={[360, 18]} fill={'#d9d2d5'} />
        <Rect position={[-150, -22]} size={[40, 9]} fill={'#17203a'} />
      </Rect>
    </Rect>
  );
}

function Meter(props: {x: number; label: string; color: string; fillRef: Reference<Rect>}) {
  return (
    <Rect position={[props.x, 20]} size={[240, 720]}>
      <Rect size={[92, 590]} radius={46} fill={'#ffffff'} />
      <Rect ref={props.fillRef} position={[0, 170]} size={[58, 210]} radius={29} fill={props.color} />
      <Txt position={[0, 360]} text={props.label} fontFamily={FONT} fontSize={44} fontWeight={850} fill={'#ffffff'} />
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

export const productTrainingOpeningScene = makeScene2D('product-training-opening', function* (view) {
  const openingPattern = createRef<Rect>();
  const officeBackdrop = createRef<Rect>();
  const officeWorking = createRef<Img>();
  const officeTired = createRef<Img>();
  const heart = createRef<Rect>();
  const heartIcon = createRef<Img>();
  const callout = createRef<Rect>();
  const age = createRef<Rect>();
  const ageFill = createRef<Rect>();
  const q10Fill = createRef<Rect>();
  const ageYoung = createRef<Img>();
  const ageSenior = createRef<Img>();
  const ageElder = createRef<Img>();
  const ageElderGlasses = createRef<Img>();
  const subtitle = createRef<Txt>();

  view.add(
    <>
      <Rect size={[1920, 1080]} fill={'#2f9cf0'} />
      <Rect ref={openingPattern} size={[1920, 1080]}><Pattern /></Rect>
      <Audio src={data.audio.file} play />
      <Rect key={'editable:q10:opening:product-badge'} position={[-820, -475]} size={[230, 72]} radius={28} fill={'#ff7b46'}>
        <Txt key={'editable:q10:opening:product-badge:text'} text={'辅酶Q10'} fontFamily={FONT} fontSize={42} fontWeight={850} fill={'#ffffff'} />
      </Rect>
      <Rect ref={officeBackdrop} position={[0, 0]}><OfficeBackdrop /></Rect>
      <Img key={'editable:q10:opening:office-working'} ref={officeWorking} src={data.assets.officeWorking} position={[0, 45]} size={[1480, 987]} opacity={0} scale={0.72} />
      <Img key={'editable:q10:opening:office-tired'} ref={officeTired} src={data.assets.officeTired} position={[0, 45]} size={[1480, 987]} opacity={0} scale={0.72} />
      <Rect key={'editable:q10:opening:group:heart'} ref={heart} position={[-130, -25]} size={[900, 770]} opacity={0} scale={0.4}>
        <Circle size={560} fill={'#1769a9'} />
        <Img key={'editable:q10:opening:heart-icon'} ref={heartIcon} src={data.assets.heart} size={[520, 310]} />
        <Circle position={[-260, -115]} size={28} fill={'#ff9800'} />
        <Circle position={[245, -75]} size={34} fill={'#ff9800'} />
        <Circle position={[-240, 190]} size={24} fill={'#ff9800'} />
        <Circle position={[190, 230]} size={30} fill={'#ff9800'} />
        <Rect key={'editable:q10:opening:callout'} ref={callout} position={[590, 105]} size={[390, 90]} radius={20} fill={'rgba(255,255,255,0.45)'} opacity={0}>
          <Txt key={'editable:q10:opening:callout:text'} text={'辅酶Q10'} fontFamily={FONT} fontSize={48} fontWeight={850} fill={'#ffffff'} />
        </Rect>
        <Line points={[[250, 170], [390, 15], [520, 15]]} stroke={'#ffffff'} lineWidth={8} />
      </Rect>
      <Rect key={'editable:q10:opening:group:age'} ref={age} position={[0, -10]} size={[1500, 850]} opacity={0} scale={0.7}>
        <Meter x={-600} label={'年龄'} color={'#f0823e'} fillRef={ageFill} />
        <Img key={'editable:q10:opening:age-young'} ref={ageYoung} src={data.assets.ageYoung} size={[470, 705]} opacity={1} />
        <Img key={'editable:q10:opening:age-senior'} ref={ageSenior} src={data.assets.ageSenior} size={[470, 705]} opacity={0} />
        <Img key={'editable:q10:opening:age-elder'} ref={ageElder} src={data.assets.ageElder} size={[470, 705]} opacity={0} />
        <Img key={'editable:q10:opening:age-elder-glasses'} ref={ageElderGlasses} src={data.assets.ageElderGlasses} size={[470, 705]} opacity={0} />
        <Meter x={600} label={'辅酶Q10'} color={'#39c65e'} fillRef={q10Fill} />
        <Txt position={[-730, 135]} text={'↑'} fontFamily={FONT} fontSize={100} fontWeight={900} fill={'#ffe343'} />
        <Txt position={[730, 150]} text={'↓'} fontFamily={FONT} fontSize={100} fontWeight={900} fill={'#ffe343'} />
      </Rect>
      <Txt
        key={'editable:q10:opening:subtitle'}
        ref={subtitle} position={[-35, 452]} width={1660} textAlign={'center'}
        fontFamily={FONT} fontSize={58} fontWeight={900} fill={'#ffe733'}
        stroke={'rgba(24,36,55,0.98)'} lineWidth={3.5} opacity={0}
      />
      <Rect key={'editable:q10:opening:brand'}>
        <DashenlinBrandMark position={[-800, -468]} />
      </Rect>
      <ProductColumnBadge text={'辅酶Q10'} position={[-520, -472]} />
      <DashenlinInternalNotice />
    </>,
  );

  function* visuals() {
    yield* all(officeWorking().opacity(1, 0.16), officeWorking().scale(1, 0.55, easeOutBack));
    yield* loop(3, function* () {
      yield* officeWorking().position.y(39, 0.42, easeOutCubic);
      yield* officeWorking().position.y(45, 0.42, easeOutCubic);
    });
    yield* all(officeWorking().opacity(0, 0.24), officeTired().opacity(1, 0.24), officeTired().scale(1, 0.24, easeOutCubic));
    yield* waitFor(3.75);
    yield* all(
      officeTired().opacity(0, 0.22),
      officeTired().scale(1.28, 0.32, easeInCubic),
      officeBackdrop().opacity(0, 0.22),
      openingPattern().opacity(0, 0.22),
    );
    yield* all(heart().opacity(1, 0.14), heart().scale(1, 0.44, easeOutBack));
    yield* callout().opacity(1, 0.22);
    yield* loop(3, function* () {
      yield* heartIcon().scale(1.08, 0.34, easeOutCubic);
      yield* heartIcon().scale(1, 0.34, easeOutCubic);
    });
    yield* waitFor(3.40);
    yield* all(heart().opacity(0, 0.18), heart().position.x(-850, 0.35, easeInCubic));
    yield* all(age().opacity(1, 0.14), age().scale(1, 0.42, easeOutBack));
    function* meterTimeline() {
      yield* all(
        ageFill().position.y(-30, 4.70, easeOutCubic),
        ageFill().size.y(610, 4.70, easeOutCubic),
        q10Fill().position.y(255, 4.70, easeOutCubic),
        q10Fill().size.y(80, 4.70, easeOutCubic),
      );
    }
    function* ageTimeline() {
      yield* waitFor(0.78);
      yield* all(ageYoung().opacity(0, 0.28), ageSenior().opacity(1, 0.28));
      yield* waitFor(1.05);
      yield* all(ageSenior().opacity(0, 0.28), ageElder().opacity(1, 0.28));
      yield* waitFor(1.05);
      yield* all(ageElder().opacity(0, 0.24), ageElderGlasses().opacity(1, 0.24));
      yield* waitFor(1.02);
    }
    yield* all(meterTimeline(), ageTimeline());
  }

  yield* all(
    visuals(),
    runSubtitles(subtitle),
    applyEditablePatches(view, OPENING_DURATION),
  );
});

export default makeProject({
  scenes: [productTrainingOpeningScene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
