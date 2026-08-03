/**
 * K03 失眠状态 — other-model remake (independent source)
 *
 * Semantic chain (must be readable without audio):
 *   S01 入睡困难: full bedroom + awake face + one eye cue + clock advances
 *   S02 多次夜醒: same bedroom; 1:00 → 3:00 → 5:00 appear in order with clock
 *   S03 次日疲倦: night→dawn; time history de-emphasized; red state falls to fatigue
 *
 * Audio: contract mix only (/contract-audio/k03-mix-final.wav) — no re-TTS.
 */
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

import timing from './timing.json';

const FONT = 'PingFang SC, Noto Sans CJK SC, Microsoft YaHei, sans-serif';
const CREAM = '#fbf8f1';
const INK = '#123b30';
const GREEN_DARK = '#075d3b';
const GOLD = '#d59a28';
const NIGHT = '#132a52';
const PURPLE = '#7460a8';
const RED = '#ef6b68';
const FATIGUE_RED = '#a9413e';

const k03 = timing.k03;
const CUES = k03.cues;

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

export const k03Scene = makeScene2D('k03-other-model', function* (view) {
  const sceneImg = createRef<Img>();
  const nightWash = createRef<Rect>();
  const dawnGlow = createRef<Circle>();
  const subtitle = createRef<Txt>();
  const hour = createRef<Line>();
  const minute = createRef<Line>();
  const eyePulse = createRef<Circle>();
  const timePath = createRef<Line>();
  const timeDots = [0, 1, 2].map(() => createRef<Circle>());
  const fatigue = [0, 1, 2].map(() => createRef<Circle>());
  const fatigueTxt = createRef<Txt>();
  const clockFace = createRef<Circle>();

  // Wake-time positions along bedding (teaching path, not decorative dots)
  const wakePos: [number, number][] = [
    [120, 100],
    [400, 85],
    [660, 55],
  ];

  view.add(
    <>
      {/*
        Official contract mix (same MD5 as remake-comparison-v1/audio/k03-mix-final.wav).
        Served from gold-sample public for revideo asset resolution; not re-TTS.
      */}
      <Audio src={'/kekang-remake-v1/k03-mix-final.wav'} play />
      <Rect size={[1920, 1080]} fill={CREAM}>
        <Img
          ref={sceneImg}
          src={'/kekang-remake-v1/k03-sleep-wide.png'}
          size={[1920, 1080]}
          scale={1.04}
          opacity={0}
        />
        {/* Night wash: strong at start, fades for dawn in S03 */}
        <Rect ref={nightWash} size={[1920, 1080]} fill={NIGHT} opacity={0.38} />
        <Circle
          ref={dawnGlow}
          position={[650, -120]}
          size={720}
          fill={'#ffd985'}
          opacity={0}
        />

        {/* Scene question — not chapter chrome / MEDICAL chip */}
        <Rect
          position={[-600, -420]}
          size={[650, 118]}
          radius={28}
          fill={'rgba(251,248,241,0.92)'}
          shadowColor={'rgba(16,63,45,0.13)'}
          shadowBlur={24}
        >
          <Txt
            text={'一夜清醒，如何变成次日疲倦？'}
            fontFamily={FONT}
            fontSize={46}
            fontWeight={850}
            fill={INK}
          />
        </Rect>

        {/* Persistent clock — advances every state */}
        <Rect
          position={[690, -265]}
          size={[270, 270]}
          radius={135}
          fill={'rgba(251,248,241,0.94)'}
          shadowColor={'rgba(0,0,0,0.18)'}
          shadowBlur={30}
        >
          <Circle
            ref={clockFace}
            size={220}
            fill={'#fffdf8'}
            stroke={GREEN_DARK}
            lineWidth={8}
          />
          <Line
            ref={hour}
            points={[
              [0, 0],
              [0, -55],
            ]}
            stroke={GREEN_DARK}
            lineWidth={10}
            lineCap={'round'}
          />
          <Line
            ref={minute}
            points={[
              [0, 0],
              [65, 0],
            ]}
            stroke={GOLD}
            lineWidth={8}
            lineCap={'round'}
          />
          <Circle size={18} fill={GREEN_DARK} />
        </Rect>

        {/* S01: one restrained eye cue for "awake / hard to fall asleep" */}
        <Circle
          ref={eyePulse}
          position={[-300, 18]}
          size={180}
          stroke={RED}
          lineWidth={7}
          opacity={0}
        />

        {/* S02: time history path drawn along bedding */}
        <Line
          ref={timePath}
          points={[
            [-20, 120],
            [240, 70],
            [480, 110],
            [700, 45],
          ]}
          stroke={'rgba(255,255,255,0.78)'}
          lineWidth={5}
          lineDash={[12, 12]}
          end={0}
        />

        {[0, 1, 2].map((i) => (
          <Circle
            key={`wake-${i}`}
            ref={timeDots[i]}
            position={wakePos[i]}
            size={104}
            fill={i === 2 ? '#f7d47e' : '#f7f2ff'}
            stroke={i === 2 ? GOLD : PURPLE}
            lineWidth={5}
            opacity={0}
            scale={0.65}
          >
            <Txt
              text={['1:00', '3:00', '5:00'][i]}
              fontFamily={FONT}
              fontSize={28}
              fontWeight={800}
              fill={i === 2 ? INK : NIGHT}
            />
          </Circle>
        ))}

        {/* S03: red state points fall from wake history → fatigue result */}
        {[0, 1, 2].map((i) => (
          <Circle
            key={`fat-${i}`}
            ref={fatigue[i]}
            position={[wakePos[i][0] * 0.55 + 280, wakePos[i][1] + 40]}
            size={34 - i * 5}
            fill={RED}
            opacity={0}
          />
        ))}
        <Txt
          ref={fatigueTxt}
          position={[520, 290]}
          text={'精神状态下降'}
          fontFamily={FONT}
          fontSize={38}
          fontWeight={840}
          fill={FATIGUE_RED}
          opacity={0}
        />

        {subtitleNode(subtitle)}

        <Txt
          position={[-800, 510]}
          text={'other-model remake · K03'}
          fontFamily={FONT}
          fontSize={22}
          fontWeight={700}
          fill={'rgba(255,255,255,0.78)'}
        />
      </Rect>
    </>,
  );

  // Absolute timeline (seconds). Every cue boundary is hard-locked.
  let t = 0;
  const advanceTo = function* (target: number) {
    const d = target - t;
    if (d > 0.001) {
      yield* waitFor(d);
      t = target;
    } else {
      t = Math.max(t, target);
    }
  };

  // ─── S01  0.06–2.799  入睡困难 ─────────────────────────────────
  // start: night bedroom, person awake, clock visible
  // action: establish bedroom; one eye ring; clock advances
  // end: still awake, time is already slipping
  yield* waitFor(0.001);
  subtitle().text(CUES[0].text);
  yield* advanceTo(CUES[0].start);

  // Establish bedroom + eye cue + clock in ~1.9s (fits inside 2.74s window)
  yield* all(
    sceneImg().opacity(1, 0.65, easeOutCubic),
    sceneImg().scale(1.0, 0.9, easeOutCubic),
    eyePulse().opacity(0.92, 0.4),
    eyePulse().scale(1.14, 0.7, easeOutCubic),
  );
  t += 0.9;
  yield* all(
    eyePulse().scale(1.0, 0.5, easeInOutCubic),
    eyePulse().opacity(0.5, 0.5),
    hour().rotation(28, 0.65, easeInOutCubic),
    minute().rotation(165, 0.65, easeInOutCubic),
  );
  t += 0.65;
  // Hold final S01 state; clear eye before S02 so wake history is clean
  yield* advanceTo(CUES[0].end - 0.2);
  yield* eyePulse().opacity(0, 0.2);
  t = CUES[0].end;

  // ─── S02  2.799–6.633  多次夜醒 ────────────────────────────────
  // start: same bedroom + clock (no page change)
  // action: clock keeps moving; 1:00, 3:00, 5:00 form in order with path
  // end: three wake times remain as one night's history
  subtitle().text(CUES[1].text);

  // Sequential wake markers (~0.9s spacing) + continuous clock (~3.5s)
  // Window length = 3.834s
  yield* all(
    hour().rotation(195, 3.4, easeInOutCubic),
    minute().rotation(780, 3.4, easeInOutCubic),
    timePath().end(1, 2.5, easeOutCubic),
    sequence(
      0.75,
      all(
        timeDots[0]().opacity(1, 0.28),
        timeDots[0]().scale(1, 0.4, easeOutBack),
      ),
      all(
        timeDots[1]().opacity(1, 0.28),
        timeDots[1]().scale(1, 0.4, easeOutBack),
      ),
      all(
        timeDots[2]().opacity(1, 0.28),
        timeDots[2]().scale(1, 0.4, easeOutBack),
      ),
    ),
  );
  t += 3.4;
  yield* advanceTo(CUES[1].end);

  // ─── S03  6.633–10.468  次日疲倦 ───────────────────────────────
  // start: night + time history + awake person from S02
  // action: night softens, dawn rises; history stays weak; red falls to fatigue
  // end: same person at dawn; night history faint; fatigue is the result
  subtitle().text(CUES[2].text);

  // Dawn + de-weight history + fatigue appear (~2.0s)
  yield* all(
    nightWash().opacity(0.05, 1.9, easeInOutCubic),
    dawnGlow().opacity(0.38, 1.6, easeOutCubic),
    sceneImg().scale(1.07, 1.9, easeInOutCubic),
    sceneImg().position([-60, 28], 1.9, easeInOutCubic),
    timePath().opacity(0.16, 1.0),
    ...timeDots.map((d) => d().opacity(0.2, 1.0)),
    fatigueTxt().opacity(1, 0.55),
    sequence(0.18, ...fatigue.map((d) => d().opacity(0.95, 0.3))),
  );
  t += 1.9;
  // Red state drops = spirit declines (~1.0s)
  yield* all(
    ...fatigue.map((d, i) =>
      d().position.y(300 + i * 42, 0.95, easeInOutCubic),
    ),
    fatigueTxt().position.y(318, 0.95, easeInOutCubic),
    hour().rotation(210, 0.9, easeInOutCubic),
    minute().rotation(860, 0.9, easeInOutCubic),
  );
  t += 0.95;
  yield* advanceTo(CUES[2].end);

  // ─── HOLD  10.468–11.733  keep final state through audio tail ──
  yield* advanceTo(k03.duration_seconds);
});
