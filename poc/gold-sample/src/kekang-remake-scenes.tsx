import {
  Audio,
  Circle,
  Img,
  Line,
  Rect,
  Txt,
  makeScene2D,
} from '@revideo/2d';
import {
  all,
  createRef,
  easeInOutCubic,
  easeOutBack,
  easeOutCubic,
  sequence,
  waitFor,
} from '@revideo/core';

import timing from '../kekang-remake-v1-timing.json';

const FONT = 'PingFang SC, Noto Sans CJK SC, Microsoft YaHei, sans-serif';
const CREAM = '#fbf8f1';
const INK = '#123b30';
const GREEN = '#0f8b52';
const GREEN_DARK = '#075d3b';
const MINT = '#dff1e7';
const GOLD = '#d59a28';
const NIGHT = '#132a52';
const PURPLE = '#7460a8';

type Cue = {start: number; end: number; text: string};
type Segment = {duration_seconds: number; cues: Cue[]};
const k03 = timing.segments.k03 as Segment;
const k13 = timing.segments.k13 as Segment;

function subtitleNode(ref: ReturnType<typeof createRef<Txt>>) {
  return (
    <Rect
      position={[0, 458]}
      size={[1500, 76]}
      radius={24}
      fill={'rgba(9,45,35,0.84)'}
      shadowColor={'rgba(0,0,0,0.16)'}
      shadowBlur={18}
    >
      <Txt
        ref={ref}
        width={1400}
        text={''}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={34}
        fontWeight={720}
        fill={'#ffffff'}
      />
    </Rect>
  );
}

export const k03RemakeScene = makeScene2D('k03-remake', function* (view) {
  const world = createRef<Rect>();
  const sceneImg = createRef<Img>();
  const daySceneImg = createRef<Img>();
  const nightWash = createRef<Rect>();
  const dawnGlow = createRef<Circle>();
  const subtitle = createRef<Txt>();
  const clock = createRef<Circle>();
  const hour = createRef<Line>();
  const minute = createRef<Line>();
  const eyePulse = createRef<Circle>();
  const timePath = createRef<Line>();
  const timeDots = [0, 1, 2].map(() => createRef<Circle>());
  const timeTxt = [0, 1, 2].map(() => createRef<Txt>());
  const fatigue = [0, 1, 2].map(() => createRef<Circle>());
  const fatigueTxt = createRef<Txt>();

  view.add(
    <>
      <Audio src={'/kekang-remake-v1/k03-mix-final.wav'} play />
      <Rect ref={world} size={[1920, 1080]} fill={CREAM}>
        <Img
          ref={sceneImg}
          src={'/kekang-remake-v1/k03-sleep-wide.png'}
          size={[1920, 1080]}
          scale={1.04}
          opacity={0}
        />
        <Img
          ref={daySceneImg}
          src={'/kekang-remake-v1/k03-day-fatigue-v2.png'}
          size={[1920, 1080]}
          scale={1.04}
          opacity={0}
        />
        <Rect ref={nightWash} size={[1920, 1080]} fill={NIGHT} opacity={0.36} />
        <Circle ref={dawnGlow} position={[650, -120]} size={680} fill={'#ffd985'} opacity={0} />
        <Rect
          position={[-600, -420]}
          size={[650, 118]}
          radius={28}
          fill={'rgba(251,248,241,0.92)'}
          shadowColor={'rgba(16,63,45,0.13)'}
          shadowBlur={24}
        >
          <Txt
            text={'夜里反复醒，第二天容易疲倦'}
            fontFamily={FONT}
            fontSize={43}
            fontWeight={850}
            fill={INK}
          />
        </Rect>
        <Rect
          position={[690, -265]}
          size={[270, 270]}
          radius={135}
          fill={'rgba(251,248,241,0.94)'}
          shadowColor={'rgba(0,0,0,0.18)'}
          shadowBlur={30}
        >
          <Circle ref={clock} size={220} fill={'#fffdf8'} stroke={GREEN_DARK} lineWidth={8} />
          <Line ref={hour} points={[[0, 0], [0, -55]]} stroke={GREEN_DARK} lineWidth={10} lineCap={'round'} />
          <Line ref={minute} points={[[0, 0], [65, 0]]} stroke={GOLD} lineWidth={8} lineCap={'round'} />
          <Circle size={18} fill={GREEN_DARK} />
        </Rect>
        <Circle
          ref={eyePulse}
          position={[-300, 18]}
          size={180}
          stroke={'#ef6b68'}
          lineWidth={7}
          opacity={0}
        />
        <Line
          ref={timePath}
          points={[[-20, 120], [240, 70], [480, 110], [700, 45]]}
          stroke={'rgba(255,255,255,0.78)'}
          lineWidth={5}
          lineDash={[12, 12]}
          end={0}
        />
        {[0, 1, 2].map((i) => (
          <Circle
            key={`time-${i}`}
            ref={timeDots[i]}
            position={([[120, 100], [400, 85], [660, 55]][i] as [number, number])}
            size={104}
            fill={i === 2 ? '#f7d47e' : '#f7f2ff'}
            stroke={i === 2 ? GOLD : PURPLE}
            lineWidth={5}
            opacity={0}
            scale={0.65}
          >
            <Txt
              ref={timeTxt[i]}
              text={['1:00', '3:00', '5:00'][i]}
              fontFamily={FONT}
              fontSize={28}
              fontWeight={800}
              fill={i === 2 ? INK : NIGHT}
            />
          </Circle>
        ))}
        {[0, 1, 2].map((i) => (
          <Circle
            key={`fatigue-${i}`}
            ref={fatigue[i]}
            position={[350 + i * 95, 230 + i * 30]}
            size={34 - i * 5}
            fill={'#ef6b68'}
            opacity={0}
          />
        ))}
        <Txt
          ref={fatigueTxt}
          position={[520, 290]}
          text={'白天还是很疲倦'}
          fontFamily={FONT}
          fontSize={38}
          fontWeight={840}
          fill={'#a9413e'}
          opacity={0}
        />
        {subtitleNode(subtitle)}
        <Rect position={[770, -472]} size={[190, 58]} radius={29} fill={'rgba(7,93,59,0.88)'}>
          <Txt text={'模板示例'} fontFamily={FONT} fontSize={26} fontWeight={760} fill={'#ffffff'} />
        </Rect>
      </Rect>
    </>,
  );

  subtitle().text(k03.cues[0].text);
  yield* all(
    sceneImg().opacity(1, 0.75),
    sceneImg().scale(1.0, 1.1, easeOutCubic),
    eyePulse().opacity(0.9, 0.5),
    eyePulse().scale(1.18, 0.8, easeOutCubic),
  );
  yield* all(
    eyePulse().scale(0.9, 0.65, easeInOutCubic),
    hour().rotation(24, 0.65, easeInOutCubic),
    minute().rotation(150, 0.65, easeInOutCubic),
  );
  yield* waitFor(Math.max(0, k03.cues[0].end - 2.05));

  subtitle().text(k03.cues[1].text);
  eyePulse().opacity(0);
  yield* all(
    timePath().end(1, 1.35, easeOutCubic),
    hour().rotation(190, 2.8, easeInOutCubic),
    minute().rotation(720, 2.8, easeInOutCubic),
    sequence(
      0.62,
      ...timeDots.map((dot) => all(dot().opacity(1, 0.3), dot().scale(1, 0.48, easeOutBack))),
    ),
  );
  yield* waitFor(Math.max(0, k03.cues[1].end - k03.cues[1].start - 2.8));

  subtitle().text(k03.cues[2].text);
  yield* all(
    nightWash().opacity(0.05, 1.15, easeInOutCubic),
    dawnGlow().opacity(0.34, 1.15, easeOutCubic),
    sceneImg().scale(1.05, 1.15, easeInOutCubic),
    timePath().opacity(0.18, 0.9),
    ...timeDots.map((dot) => dot().opacity(0.2, 0.9)),
  );
  yield* all(
    sceneImg().opacity(0, 1.0, easeInOutCubic),
    daySceneImg().opacity(1, 1.0, easeInOutCubic),
    daySceneImg().scale(1, 1.0, easeOutCubic),
    nightWash().opacity(0, 0.75),
    dawnGlow().opacity(0, 0.75),
    fatigueTxt().opacity(1, 0.65),
    sequence(0.18, ...fatigue.map((dot) => dot().opacity(0.9, 0.3))),
  );
  yield* all(
    daySceneImg().position([-22, 8], 0.75, easeInOutCubic),
    ...fatigue.map((dot, i) => dot().position.y(300 + i * 45, 0.75, easeInOutCubic)),
    fatigueTxt().position.y(320, 0.75, easeInOutCubic),
  );
  yield* waitFor(Math.max(0, k03.duration_seconds - k03.cues[2].start - 2.9));
  // Keep the final state on screen long enough for the mastered narration tail.
  yield* waitFor(0.4);
});

export const k13RemakeScene = makeScene2D('k13-remake', function* (view) {
  const subtitle = createRef<Txt>();
  const ganoderma = createRef<Img>();
  const rawLabel = createRef<Txt>();
  const pipeA = createRef<Line>();
  const pipeB = createRef<Line>();
  const liquidA = createRef<Rect>();
  const liquidB = createRef<Rect>();
  const vesselA = createRef<Rect>();
  const vesselB = createRef<Rect>();
  const token = createRef<Circle>();
  const particles = [0, 1, 2, 3, 4].map(() => createRef<Circle>());
  const bubblesA = [0, 1, 2].map(() => createRef<Circle>());
  const bubblesB = [0, 1, 2].map(() => createRef<Circle>());
  const capsules = [0, 1, 2].map(() => createRef<Rect>());
  const stageLabel = createRef<Txt>();

  view.add(
    <>
      <Audio src={'/kekang-remake-v1/k13-mix-final.wav'} play />
      <Rect size={[1920, 1080]} fill={CREAM}>
        <Circle position={[-810, 460]} size={720} fill={'#f2ead7'} opacity={0.6} />
        <Circle position={[820, -450]} size={780} fill={MINT} opacity={0.64} />
        <Txt
          position={[-290, -430]}
          text={'双重提取工艺'}
          width={1250}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={48}
          fontWeight={860}
          fill={INK}
        />
        <Rect position={[-700, 20]} size={[300, 360]} radius={150} fill={'#fffdf8'} shadowColor={'rgba(16,63,45,.14)'} shadowBlur={24}>
          <Img ref={ganoderma} src={'/kekang-lingzhi/v3/ganoderma-hero-v3.png'} size={[280, 280]} opacity={0} scale={0.72} />
        </Rect>
        <Txt ref={rawLabel} position={[-700, 245]} text={'灵芝原料'} fontFamily={FONT} fontSize={32} fontWeight={820} fill={GREEN_DARK} opacity={0} />
        <Line ref={pipeA} points={[[-540, 20], [-400, 20], [-320, 80]]} stroke={GREEN} lineWidth={14} radius={20} end={0} />
        <Line ref={pipeB} points={[[0, 80], [130, 80], [250, 80]]} stroke={GREEN} lineWidth={14} radius={20} end={0} />
        <Rect ref={vesselA} position={[-150, 80]} size={[320, 390]} radius={54} fill={'rgba(255,255,255,.8)'} stroke={GREEN_DARK} lineWidth={10} opacity={0} scale={0.82}>
          <Rect ref={liquidA} position={[0, 105]} size={[280, 120]} radius={[0, 0, 40, 40]} fill={'#d18a2c'} opacity={0.88} />
          {[0, 1, 2].map((i) => <Circle key={`ba${i}`} ref={bubblesA[i]} position={[-80 + i * 75, 90 - i * 35]} size={24 + i * 5} fill={'#f7c66a'} opacity={0} />)}
          <Txt position={[0, -145]} text={'第一次提取'} fontFamily={FONT} fontSize={34} fontWeight={840} fill={INK} />
        </Rect>
        <Rect ref={vesselB} position={[420, 80]} size={[320, 390]} radius={54} fill={'rgba(255,255,255,.8)'} stroke={GREEN_DARK} lineWidth={10} opacity={0} scale={0.82}>
          <Rect ref={liquidB} position={[0, 125]} size={[280, 80]} radius={[0, 0, 40, 40]} fill={'#a96021'} opacity={0.92} />
          {[0, 1, 2].map((i) => <Circle key={`bb${i}`} ref={bubblesB[i]} position={[-75 + i * 70, 110 - i * 30]} size={22 + i * 4} fill={'#f1b452'} opacity={0} />)}
          <Txt position={[0, -145]} text={'第二次浓缩'} fontFamily={FONT} fontSize={34} fontWeight={840} fill={INK} />
        </Rect>
        <Circle ref={token} position={[-520, 20]} size={62} fill={GOLD} stroke={'#8d4f18'} lineWidth={6} opacity={0} />
        {[0, 1, 2, 3, 4].map((i) => <Circle key={`p${i}`} ref={particles[i]} position={[-720 + (i % 3) * 44, -20 + Math.floor(i / 3) * 50]} size={24 + (i % 2) * 8} fill={i % 2 ? '#be6f27' : '#e0a33c'} opacity={0} />)}
        {[0, 1, 2].map((i) => <Rect key={`cap${i}`} ref={capsules[i]} position={[700 + i * 90, 90 + (i % 2) * 60]} size={[110, 48]} radius={24} fill={i % 2 ? '#d98926' : '#eead44'} stroke={'#8d4f18'} lineWidth={5} opacity={0} scale={0.6} rotation={i % 2 ? -18 : 15}><Line points={[[0,-23],[0,23]]} stroke={'#8d4f18'} lineWidth={4} /></Rect>)}
        <Txt ref={stageLabel} position={[120, 340]} text={'原料进入第一次提取'} fontFamily={FONT} fontSize={38} fontWeight={850} fill={GREEN_DARK} opacity={0} />
        {subtitleNode(subtitle)}
        <Rect position={[770, -472]} size={[190, 58]} radius={29} fill={'rgba(7,93,59,0.88)'}>
          <Txt text={'模板示例'} fontFamily={FONT} fontSize={26} fontWeight={760} fill={'#ffffff'} />
        </Rect>
      </Rect>
    </>,
  );

  subtitle().text(k13.cues[0].text);
  stageLabel().opacity(1);
  yield* all(
    ganoderma().opacity(1, 0.55),
    ganoderma().scale(1, 0.8, easeOutBack),
    rawLabel().opacity(1, 0.5),
    vesselA().opacity(1, 0.55),
    vesselA().scale(1, 0.8, easeOutBack),
    pipeA().end(1, 1.0, easeOutCubic),
    sequence(0.12, ...particles.map((p) => p().opacity(1, 0.3))),
  );
  yield* all(
    ...particles.map((p, i) => p().position([-260 + (i % 2) * 45, 60 + i * 18], 1.15, easeInOutCubic)),
    token().opacity(1, 0.25),
    token().position([-150, 70], 1.15, easeInOutCubic),
    sequence(0.2, ...bubblesA.map((b) => b().opacity(0.9, 0.3))),
  );
  yield* waitFor(Math.max(0, k13.cues[0].end - 2.15));

  subtitle().text(k13.cues[1].text);
  stageLabel().text('第一次提取完成，进入第二次浓缩');
  yield* all(
    pipeB().end(1, 0.8, easeOutCubic),
    vesselB().opacity(1, 0.55),
    vesselB().scale(1, 0.8, easeOutBack),
    token().position([420, 70], 1.5, easeInOutCubic),
    liquidA().opacity(0.35, 1.2),
  );
  yield* all(
    liquidB().size.y(150, 1.0, easeOutCubic),
    liquidB().position.y(90, 1.0, easeOutCubic),
    sequence(0.18, ...bubblesB.map((b) => b().opacity(0.9, 0.3))),
  );
  yield* waitFor(Math.max(0, k13.cues[1].end - k13.cues[1].start - 2.5));

  subtitle().text(k13.cues[2].text);
  stageLabel().text('两次提取完成，制成胶囊');
  yield* all(
    liquidB().size.y(72, 1.2, easeInOutCubic),
    liquidB().position.y(128, 1.2, easeInOutCubic),
    token().opacity(0, 0.5),
    sequence(0.24, ...capsules.map((cap) => all(cap().opacity(1, 0.35), cap().scale(1, 0.5, easeOutBack)))),
  );
  yield* all(
    ...capsules.map((cap, i) => cap().position.x(720 + i * 95, 0.8, easeInOutCubic)),
    ...bubblesB.map((b) => b().opacity(0.2, 0.8)),
  );
  yield* waitFor(Math.max(0, k13.duration_seconds - k13.cues[2].start - 2.0));
});
