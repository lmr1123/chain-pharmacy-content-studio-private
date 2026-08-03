/**
 * 可可康 × Pfizer 叙事配方 · K08 有声视听片段 v2
 *
 * 在无声运动样片基础上补齐药师旁白、动作同步音效与字幕。
 * Validation only：验证绿色视觉 + 声音语法；非完整课程、非医学审核终稿。
 */
import {Audio, Circle, Img, Line, Rect, Txt, makeScene2D} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeInOutCubic,
  easeOutBack,
  easeOutCubic,
  loop,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../kekang-pfizer-k08-audiovisual.json';

const FONT = 'PingFang SC, Source Han Sans SC, Microsoft YaHei, sans-serif';
const GREEN = '#07863f';
const GREEN_DARK = '#075a32';
const GREEN_DEEP = '#103f2d';
const MINT = '#eaf5ed';
const MINT_STRONG = '#cfe8d5';
const CREAM = '#fbfaf5';
const GOLD = '#c89532';
const INK = '#183128';
const MUTED = '#64756d';
const WHITE = '#ffffff';
const GANODERMA = '/kekang-lingzhi/v3/ganoderma-hero-v3.png';

type Ref<T> = Reference<T>;
type Cue = {start: number; end: number; text: string};
type Beats = Record<string, number>;

const cues = (data as {cues: Cue[]}).cues;
const beats = ((data as {motion_beats?: Beats}).motion_beats || {}) as Beats;
const DURATION = Number(
  (data as {playback_duration?: number}).playback_duration || 8,
);
const AUDIO =
  (data as {audio?: {file?: string}}).audio?.file ||
  '/kekang-k08-av/k08-mix-final.wav';
const TITLE =
  (data as {screen_title?: string}).screen_title ||
  '从灵芝主体，认识两类成分';
const COMPLETION =
  (data as {completion_text?: string}).completion_text ||
  '两条知识路径由同一灵芝主体展开';
const BOUNDARY =
  (data as {boundary_text?: string}).boundary_text ||
  '名称来自内部课件 · 局部运动语法验证 · 非医学审核结论';

function beat(name: string, fallback: number): number {
  const value = beats[name];
  return typeof value === 'number' ? value : fallback;
}

function IngredientCard({
  cardRef,
  markerRef,
  label,
  index,
  position,
  accent,
}: {
  cardRef: Ref<Rect>;
  markerRef: Ref<Circle>;
  label: string;
  index: string;
  position: [number, number];
  accent: string;
}) {
  return (
    <Rect
      ref={cardRef}
      position={position}
      size={[470, 184]}
      radius={92}
      fill={WHITE}
      stroke={accent}
      lineWidth={4}
      shadowColor={'rgba(16,63,45,0.16)'}
      shadowBlur={30}
      opacity={0}
      scale={0.72}
    >
      <Circle
        ref={markerRef}
        position={[-154, 0]}
        size={104}
        fill={`${accent}20`}
        scale={0.82}
      >
        <Txt
          text={index}
          fontFamily={FONT}
          fontSize={34}
          fontWeight={800}
          fill={accent}
        />
      </Circle>
      <Txt
        position={[54, 0]}
        width={260}
        text={label}
        fontFamily={FONT}
        fontSize={52}
        fontWeight={850}
        fill={INK}
      />
    </Rect>
  );
}

function* subtitleTimeline(bar: Ref<Rect>, text: Ref<Txt>) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      yield* waitFor(cue.start - cursor);
    }
    text().text(cue.text);
    bar().opacity(1);
    text().opacity(1);
    const hold = Math.max(0.05, cue.end - cue.start);
    yield* waitFor(hold);
    text().opacity(0);
    bar().opacity(0);
    cursor = cue.end;
  }
  if (cursor < DURATION) {
    yield* waitFor(DURATION - cursor);
  }
}

function* motionTimeline(refs: {
  mintBlob: Ref<Circle>;
  goldBlob: Ref<Circle>;
  eyebrow: Ref<Txt>;
  title: Ref<Txt>;
  titleRule: Ref<Line>;
  heroHalo: Ref<Circle>;
  heroOrbit: Ref<Circle>;
  heroFrame: Ref<Rect>;
  heroCaption: Ref<Rect>;
  lineA: Ref<Line>;
  lineB: Ref<Line>;
  cardA: Ref<Rect>;
  cardB: Ref<Rect>;
  markerA: Ref<Circle>;
  markerB: Ref<Circle>;
  completion: Ref<Txt>;
  boundary: Ref<Txt>;
  dotA: Ref<Circle>;
  dotB: Ref<Circle>;
  dotC: Ref<Circle>;
}) {
  const {
    mintBlob,
    goldBlob,
    eyebrow,
    title,
    titleRule,
    heroHalo,
    heroOrbit,
    heroFrame,
    heroCaption,
    lineA,
    lineB,
    cardA,
    cardB,
    markerA,
    markerB,
    completion,
    boundary,
    dotA,
    dotB,
    dotC,
  } = refs;

  const tEnv = beat('env_start', 0);
  const tHero = beat('title_hero_start', 0.12);
  const tOrbit = beat('orbit_lines_start', 1.25);
  const tPathA = beat('path_a_start', 3.16);
  const tLabelA = beat('label_a_start', 3.28);
  const tPathB = beat('path_b_start', 4.12);
  const tLabelB = beat('label_b_start', 4.24);
  const tFocusA = beat('focus_a_start', 5.43);
  const tFocusB = beat('focus_b_start', 6.16);
  const tCompletion = beat('completion_start', 6.86);
  const tEnd = beat('end', DURATION);

  let now = 0;
  const waitUntil = function* (target: number) {
    const delta = target - now;
    if (delta > 0.001) {
      yield* waitFor(delta);
      now = target;
    }
  };

  // Environment soft in
  yield* waitUntil(tEnv);
  yield* all(mintBlob().opacity(0.72, 0.28), goldBlob().opacity(0.56, 0.28));
  now += 0.28;

  // Title + hero enter quickly so first phrase has a stable subject
  yield* waitUntil(tHero);
  yield* all(
    eyebrow().opacity(1, 0.35),
    title().opacity(1, 0.45),
    title().position.x(-430, 0.55, easeOutCubic),
    titleRule().end(1, 0.5, easeOutCubic),
    heroHalo().opacity(1, 0.4),
    heroHalo().scale(1, 0.55, easeOutCubic),
    heroOrbit().opacity(1, 0.5),
    heroOrbit().scale(1, 0.55, easeOutCubic),
    heroFrame().opacity(1, 0.3),
    heroFrame().scale(1, 0.55, easeOutBack),
    dotA().opacity(0.6, 0.4),
    dotB().opacity(0.65, 0.4),
    dotC().opacity(0.55, 0.4),
  );
  now += 0.55;
  yield* all(
    heroCaption().opacity(1, 0.22),
    heroCaption().scale(1, 0.28, easeOutBack),
  );
  now += 0.28;

  // Soft orbit while second phrase runs
  yield* waitUntil(tOrbit);
  {
    const orbitDur = Math.max(0.35, Math.min(0.9, tPathA - now - 0.05));
    yield* heroOrbit().rotation(14, orbitDur, easeInOutCubic);
    now += orbitDur;
  }

  // Left path + 01: draw and land the card inside the 灵芝多糖 cue
  yield* waitUntil(tPathA);
  yield* lineA().end(1, 0.28, easeOutCubic);
  now += 0.28;
  yield* waitUntil(Math.max(now, tLabelA));
  yield* all(cardA().opacity(1, 0.22), cardA().scale(1, 0.32, easeOutBack));
  now += 0.32;

  // Right path + 02
  yield* waitUntil(tPathB);
  yield* lineB().end(1, 0.28, easeOutCubic);
  now += 0.28;
  yield* waitUntil(Math.max(now, tLabelB));
  yield* all(cardB().opacity(1, 0.22), cardB().scale(1, 0.32, easeOutBack));
  now += 0.32;

  // Focus 01 then 02
  yield* waitUntil(tFocusA);
  yield* all(
    cardA().scale(1.05, 0.3, easeInOutCubic),
    markerA().scale(1.08, 0.3, easeInOutCubic),
    cardB().opacity(0.64, 0.3),
  );
  now += 0.3;
  yield* all(
    cardA().scale(1, 0.26, easeInOutCubic),
    markerA().scale(1, 0.26, easeInOutCubic),
    cardB().opacity(1, 0.26),
  );
  now += 0.26;

  yield* waitUntil(tFocusB);
  yield* all(
    cardB().scale(1.05, 0.3, easeInOutCubic),
    markerB().scale(1.08, 0.3, easeInOutCubic),
    cardA().opacity(0.64, 0.3),
  );
  now += 0.3;
  yield* all(
    cardB().scale(1, 0.26, easeInOutCubic),
    markerB().scale(1, 0.26, easeInOutCubic),
    cardA().opacity(1, 0.26),
  );
  now += 0.26;

  // Completion hold (above subtitle band)
  yield* waitUntil(tCompletion);
  completion().position([0, 400]);
  boundary().position([0, 448]);
  yield* all(
    completion().opacity(1, 0.35),
    completion().position.y(390, 0.4, easeOutCubic),
    boundary().opacity(1, 0.35),
  );
  now += 0.4;

  const remain = Math.max(0.12, tEnd - now);
  if (remain >= 0.85) {
    yield* loop(1, function* () {
      yield* all(
        heroOrbit().rotation(36, 0.38, easeInOutCubic),
        heroHalo().scale(1.03, 0.38, easeInOutCubic),
        dotA().position.y(-165, 0.38, easeInOutCubic),
        dotB().position.y(278, 0.38, easeInOutCubic),
      );
      yield* all(
        heroOrbit().rotation(52, 0.38, easeInOutCubic),
        heroHalo().scale(1, 0.38, easeInOutCubic),
        dotA().position.y(-155, 0.38, easeInOutCubic),
        dotB().position.y(270, 0.38, easeInOutCubic),
      );
    });
    now += 0.76;
  }
  if (now < tEnd) {
    yield* waitFor(tEnd - now);
  }
}

const scene = makeScene2D('kekang-pfizer-k08-audiovisual', function* (view) {
  const title = createRef<Txt>();
  const eyebrow = createRef<Txt>();
  const titleRule = createRef<Line>();
  const heroHalo = createRef<Circle>();
  const heroOrbit = createRef<Circle>();
  const heroFrame = createRef<Rect>();
  const heroImage = createRef<Img>();
  const heroCaption = createRef<Rect>();
  const lineA = createRef<Line>();
  const lineB = createRef<Line>();
  const cardA = createRef<Rect>();
  const cardB = createRef<Rect>();
  const markerA = createRef<Circle>();
  const markerB = createRef<Circle>();
  const completion = createRef<Txt>();
  const boundary = createRef<Txt>();
  const dotA = createRef<Circle>();
  const dotB = createRef<Circle>();
  const dotC = createRef<Circle>();
  const subtitleBar = createRef<Rect>();
  const subtitle = createRef<Txt>();
  const mintBlob = createRef<Circle>();
  const goldBlob = createRef<Circle>();

  view.add(
    <>
      <Audio src={AUDIO} play volume={1} />
      <Rect size={[1920, 1080]} fill={CREAM}>
        <Circle
          ref={mintBlob}
          position={[785, -420]}
          size={860}
          fill={MINT}
          opacity={0}
        />
        <Circle
          ref={goldBlob}
          position={[-820, 470]}
          size={720}
          fill={'#f4ead1'}
          opacity={0}
        />
        <Line
          points={[
            [-960, 390],
            [-480, 230],
            [0, 300],
            [520, 160],
            [960, 250],
          ]}
          stroke={'rgba(7,134,63,0.08)'}
          lineWidth={64}
          radius={80}
        />

        <Circle ref={dotA} position={[-760, -155]} size={18} fill={GREEN} opacity={0} />
        <Circle ref={dotB} position={[720, 270]} size={14} fill={GOLD} opacity={0} />
        <Circle ref={dotC} position={[820, -110]} size={22} fill={GREEN} opacity={0} />

        <Txt
          ref={eyebrow}
          position={[-650, -454]}
          text={'大参林内部培训 · K08 有声视听样片'}
          fontFamily={FONT}
          fontSize={28}
          fontWeight={720}
          fill={GREEN_DARK}
          opacity={0}
        />
        <Txt
          ref={title}
          position={[-470, -350]}
          width={820}
          text={TITLE.replace('，', '\n')}
          fontFamily={FONT}
          fontSize={72}
          lineHeight={90}
          fontWeight={880}
          fill={GREEN_DEEP}
          opacity={0}
        />
        <Line
          ref={titleRule}
          points={[
            [-780, -195],
            [-365, -195],
          ]}
          stroke={GREEN}
          lineWidth={8}
          end={0}
        />

        <Circle
          ref={heroHalo}
          position={[0, 66]}
          size={488}
          fill={MINT_STRONG}
          opacity={0}
          scale={0.45}
        />
        <Circle
          ref={heroOrbit}
          position={[0, 66]}
          size={590}
          stroke={'rgba(7,134,63,0.34)'}
          lineWidth={4}
          lineDash={[16, 18]}
          opacity={0}
          scale={0.78}
        />
        <Rect
          ref={heroFrame}
          position={[0, 66]}
          size={[382, 382]}
          radius={191}
          fill={WHITE}
          stroke={WHITE}
          lineWidth={16}
          shadowColor={'rgba(16,63,45,0.18)'}
          shadowBlur={38}
          clip
          opacity={0}
          scale={0.62}
        >
          <Img ref={heroImage} src={GANODERMA} size={[382, 382]} scale={1.08} />
        </Rect>
        <Rect
          ref={heroCaption}
          position={[0, 302]}
          size={[240, 74]}
          radius={37}
          fill={GREEN_DEEP}
          opacity={0}
          scale={0.78}
        >
          <Txt
            text={'灵芝主体'}
            fontFamily={FONT}
            fontSize={32}
            fontWeight={760}
            fill={WHITE}
          />
        </Rect>

        <Line
          ref={lineA}
          points={[
            [-205, 18],
            [-400, -86],
            [-610, -86],
          ]}
          stroke={GREEN}
          lineWidth={7}
          radius={24}
          end={0}
        />
        <Line
          ref={lineB}
          points={[
            [205, 112],
            [395, 230],
            [610, 230],
          ]}
          stroke={GOLD}
          lineWidth={7}
          radius={24}
          end={0}
        />
        <IngredientCard
          cardRef={cardA}
          markerRef={markerA}
          label={'灵芝多糖'}
          index={'01'}
          position={[-660, -86]}
          accent={GREEN}
        />
        <IngredientCard
          cardRef={cardB}
          markerRef={markerB}
          label={'灵芝三萜'}
          index={'02'}
          position={[660, 230]}
          accent={GOLD}
        />

        <Txt
          ref={completion}
          position={[0, 458]}
          text={COMPLETION}
          fontFamily={FONT}
          fontSize={34}
          fontWeight={700}
          fill={INK}
          opacity={0}
        />
        <Txt
          ref={boundary}
          position={[0, 512]}
          text={BOUNDARY}
          fontFamily={FONT}
          fontSize={22}
          fontWeight={580}
          fill={MUTED}
          opacity={0}
        />

        <Rect
          ref={subtitleBar}
          position={[0, 470]}
          size={[920, 64]}
          radius={18}
          fill={'rgba(16,63,45,0.78)'}
          opacity={0}
        />
        <Txt
          ref={subtitle}
          position={[0, 470]}
          width={860}
          text={''}
          fontFamily={FONT}
          fontSize={44}
          fontWeight={720}
          fill={WHITE}
          textAlign={'center'}
          opacity={0}
        />
      </Rect>
    </>,
  );

  yield* all(
    motionTimeline({
      mintBlob,
      goldBlob,
      eyebrow,
      title,
      titleRule,
      heroHalo,
      heroOrbit,
      heroFrame,
      heroCaption,
      lineA,
      lineB,
      cardA,
      cardB,
      markerA,
      markerB,
      completion,
      boundary,
      dotA,
      dotB,
      dotC,
    }),
    subtitleTimeline(subtitleBar, subtitle),
  );
});

export default makeProject({
  name: 'kekang-pfizer-k08-audiovisual',
  scenes: [scene],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
