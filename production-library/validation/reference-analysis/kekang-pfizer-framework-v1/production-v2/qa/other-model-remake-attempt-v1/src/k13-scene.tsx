/**
 * K13 双重提取工艺 — other-model remake (independent source)
 *
 * Semantic chain (must be readable without audio):
 *   S01 第一次提取: 灵芝原料颗粒实际进入第一罐；罐内液体/气泡变化
 *   S02 转移浓缩: 提取物沿管路进入第二罐；第二罐液位与颜色变化；两罐并存
 *   S03 证据收口: 浓缩收束、无品牌胶囊输出；证据门禁最后出现
 *
 * Audio: contract mix only — no re-TTS.
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
const GREEN = '#0f8b52';
const GREEN_DARK = '#075d3b';
const MINT = '#dff1e7';
const GOLD = '#d59a28';

const k13 = timing.k13;
const CUES = k13.cues;

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

export const k13Scene = makeScene2D('k13-other-model', function* (view) {
  const subtitle = createRef<Txt>();
  const ganoderma = createRef<Img>();
  const rawLabel = createRef<Txt>();
  const pipeA = createRef<Line>();
  const pipeB = createRef<Line>();
  const liquidA = createRef<Rect>();
  const liquidB = createRef<Rect>();
  const vesselA = createRef<Rect>();
  const vesselB = createRef<Rect>();
  const transfer = createRef<Circle>();
  const particles = [0, 1, 2, 3, 4].map(() => createRef<Circle>());
  const bubblesA = [0, 1, 2].map(() => createRef<Circle>());
  const bubblesB = [0, 1, 2].map(() => createRef<Circle>());
  const capsules = [0, 1, 2].map(() => createRef<Rect>());
  const evidence = createRef<Rect>();
  const stageLabel = createRef<Txt>();

  view.add(
    <>
      <Audio src={'/kekang-remake-v1/k13-mix-final.wav'} play />
      <Rect size={[1920, 1080]} fill={CREAM}>
        <Circle position={[-810, 460]} size={720} fill={'#f2ead7'} opacity={0.6} />
        <Circle position={[820, -450]} size={780} fill={MINT} opacity={0.64} />

        <Txt
          position={[-290, -430]}
          text={'双重提取，不是两个节点，而是两次材料变化'}
          width={1250}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={48}
          fontWeight={860}
          fill={INK}
        />

        {/* Raw material */}
        <Rect
          position={[-700, 20]}
          size={[300, 360]}
          radius={150}
          fill={'#fffdf8'}
          shadowColor={'rgba(16,63,45,.14)'}
          shadowBlur={24}
        >
          <Img
            ref={ganoderma}
            src={'/kekang-lingzhi/v3/ganoderma-hero-v3.png'}
            size={[280, 280]}
            opacity={0}
            scale={0.72}
          />
        </Rect>
        <Txt
          ref={rawLabel}
          position={[-700, 245]}
          text={'灵芝原料'}
          fontFamily={FONT}
          fontSize={32}
          fontWeight={820}
          fill={GREEN_DARK}
          opacity={0}
        />

        <Line
          ref={pipeA}
          points={[
            [-540, 20],
            [-400, 20],
            [-320, 80],
          ]}
          stroke={GREEN}
          lineWidth={14}
          radius={20}
          end={0}
        />
        <Line
          ref={pipeB}
          points={[
            [0, 80],
            [130, 80],
            [250, 80],
          ]}
          stroke={GREEN}
          lineWidth={14}
          radius={20}
          end={0}
        />

        {/* Vessel A — first extraction */}
        <Rect
          ref={vesselA}
          position={[-150, 80]}
          size={[320, 390]}
          radius={54}
          fill={'rgba(255,255,255,.8)'}
          stroke={GREEN_DARK}
          lineWidth={10}
          opacity={0}
          scale={0.82}
        >
          {/* liquid starts low; rises when material enters */}
          <Rect
            ref={liquidA}
            position={[0, 145]}
            size={[280, 40]}
            radius={[0, 0, 40, 40]}
            fill={'#d18a2c'}
            opacity={0}
          />
          {[0, 1, 2].map((i) => (
            <Circle
              key={`ba${i}`}
              ref={bubblesA[i]}
              position={[-80 + i * 75, 90 - i * 35]}
              size={24 + i * 5}
              fill={'#f7c66a'}
              opacity={0}
            />
          ))}
          <Txt
            position={[0, -145]}
            text={'第一次提取'}
            fontFamily={FONT}
            fontSize={34}
            fontWeight={840}
            fill={INK}
          />
        </Rect>

        {/* Vessel B — second concentration */}
        <Rect
          ref={vesselB}
          position={[420, 80]}
          size={[320, 390]}
          radius={54}
          fill={'rgba(255,255,255,.8)'}
          stroke={GREEN_DARK}
          lineWidth={10}
          opacity={0}
          scale={0.82}
        >
          <Rect
            ref={liquidB}
            position={[0, 155]}
            size={[280, 20]}
            radius={[0, 0, 40, 40]}
            fill={'#a96021'}
            opacity={0}
          />
          {[0, 1, 2].map((i) => (
            <Circle
              key={`bb${i}`}
              ref={bubblesB[i]}
              position={[-75 + i * 70, 110 - i * 30]}
              size={22 + i * 4}
              fill={'#f1b452'}
              opacity={0}
            />
          ))}
          <Txt
            position={[0, -145]}
            text={'第二次浓缩'}
            fontFamily={FONT}
            fontSize={34}
            fontWeight={840}
            fill={INK}
          />
        </Rect>

        {/* Transfer blob — material moving through pipe (not a decorative path-dot alone) */}
        <Circle
          ref={transfer}
          position={[-520, 20]}
          size={62}
          fill={GOLD}
          stroke={'#8d4f18'}
          lineWidth={6}
          opacity={0}
        />

        {/* Raw particles that physically travel into vessel A */}
        {[0, 1, 2, 3, 4].map((i) => (
          <Circle
            key={`p${i}`}
            ref={particles[i]}
            position={[-720 + (i % 3) * 44, -20 + Math.floor(i / 3) * 50]}
            size={24 + (i % 2) * 8}
            fill={i % 2 ? '#be6f27' : '#e0a33c'}
            opacity={0}
          />
        ))}

        {/* Unbranded capsule output */}
        {[0, 1, 2].map((i) => (
          <Rect
            key={`cap${i}`}
            ref={capsules[i]}
            position={[700 + i * 90, 90 + (i % 2) * 60]}
            size={[110, 48]}
            radius={24}
            fill={i % 2 ? '#d98926' : '#eead44'}
            stroke={'#8d4f18'}
            lineWidth={5}
            opacity={0}
            scale={0.6}
            rotation={i % 2 ? -18 : 15}
          >
            <Line points={[[0, -23], [0, 23]]} stroke={'#8d4f18'} lineWidth={4} />
          </Rect>
        ))}

        {/* Evidence gate — only after process result exists */}
        <Rect
          ref={evidence}
          position={[690, -250]}
          size={[340, 78]}
          radius={39}
          fill={'#fff5e8'}
          stroke={'#a94b24'}
          lineWidth={4}
          opacity={0}
        >
          <Txt
            text={'证据通过后用于正式培训'}
            fontFamily={FONT}
            fontSize={25}
            fontWeight={760}
            fill={'#943f20'}
          />
        </Rect>

        <Txt
          ref={stageLabel}
          position={[120, 340]}
          text={'原料进入第一次提取'}
          fontFamily={FONT}
          fontSize={38}
          fontWeight={850}
          fill={GREEN_DARK}
          opacity={0}
        />

        {subtitleNode(subtitle)}

        <Txt
          position={[-800, 510]}
          text={'other-model remake · K13'}
          fontFamily={FONT}
          fontSize={22}
          fontWeight={700}
          fill={'rgba(18,59,48,0.55)'}
        />
      </Rect>
    </>,
  );

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

  // ─── S01  0.06–2.869  原料进入第一次提取 ─────────────────────
  yield* waitFor(0.001);
  subtitle().text(CUES[0].text);
  stageLabel().text('原料进入第一次提取');
  stageLabel().opacity(1);
  yield* advanceTo(CUES[0].start);

  // Fast establish: empty vessel ready to receive (not a slow fade as the action)
  yield* all(
    ganoderma().opacity(1, 0.35),
    ganoderma().scale(1, 0.5, easeOutBack),
    rawLabel().opacity(1, 0.3),
    vesselA().opacity(1, 0.35),
    vesselA().scale(1, 0.45, easeOutBack),
    pipeA().end(1, 0.55, easeOutCubic),
    sequence(0.08, ...particles.map((p) => p().opacity(1, 0.2))),
  );
  t += 0.55;

  // Semantic action: particles travel into vessel A; liquid rises; bubbles start
  yield* all(
    ...particles.map((p, i) =>
      p().position([-200 + (i % 2) * 40, 70 + i * 16], 1.15, easeInOutCubic),
    ),
    transfer().opacity(1, 0.18),
    transfer().position([-150, 70], 1.15, easeInOutCubic),
    liquidA().opacity(0.92, 0.45),
    liquidA().size.y(150, 1.15, easeOutCubic),
    liquidA().position.y(90, 1.15, easeOutCubic),
    sequence(0.14, ...bubblesA.map((b) => b().opacity(0.92, 0.28))),
  );
  t += 1.15;
  yield* advanceTo(CUES[0].end);

  // ─── S02  2.869–6.732  提取物转移并浓缩 ───────────────────────
  subtitle().text(CUES[1].text);
  stageLabel().text('第一次提取完成，进入第二次浓缩');

  // Second vessel appears empty; material begins transfer from A
  yield* all(
    pipeB().end(1, 0.55, easeOutCubic),
    vesselB().opacity(1, 0.4),
    vesselB().scale(1, 0.5, easeOutBack),
  );
  t += 0.55;

  // Transfer blob moves A→B; A liquid de-weighted (still retained as history)
  yield* all(
    transfer().position([420, 70], 1.25, easeInOutCubic),
    liquidA().opacity(0.3, 1.1),
    ...particles.map((p, i) => p().opacity(0.32 + (i % 3) * 0.08, 0.9)),
  );
  t += 1.25;

  // B liquid rises + darkens + bubbles — material state change, not label flash
  yield* all(
    liquidB().opacity(0.96, 0.3),
    liquidB().size.y(170, 1.1, easeOutCubic),
    liquidB().position.y(78, 1.1, easeOutCubic),
    liquidB().fill('#8a4a16', 1.0),
    sequence(0.14, ...bubblesB.map((b) => b().opacity(0.92, 0.26))),
  );
  t += 1.1;
  yield* advanceTo(CUES[1].end);

  // ─── S03  6.732–11.473  浓缩完成并受证据约束 ─────────────────
  subtitle().text(CUES[2].text);
  stageLabel().text('浓缩完成，形成稳定输出');

  // 1) Concentrate settles first (level contracts, color deepens)
  yield* all(
    liquidB().size.y(68, 1.2, easeInOutCubic),
    liquidB().position.y(130, 1.2, easeInOutCubic),
    liquidB().fill('#6e3a12', 1.1),
    transfer().opacity(0, 0.4),
    ...bubblesB.map((b) => b().opacity(0.12, 0.7)),
  );
  t += 1.2;

  // 2) Unbranded capsules form as process output
  // sequence delay 0.2 × 2 + anim 0.42 ≈ 0.82s total
  yield* sequence(
    0.2,
    ...capsules.map((cap) =>
      all(cap().opacity(1, 0.3), cap().scale(1, 0.42, easeOutBack)),
    ),
  );
  t += 0.82;
  yield* all(
    ...capsules.map((cap, i) =>
      cap().position.x(720 + i * 95, 0.7, easeInOutCubic),
    ),
  );
  t += 0.7;

  // 3) Evidence gate only after result is visible
  yield* evidence().opacity(1, 0.55);
  t += 0.55;
  yield* advanceTo(CUES[2].end);

  // ─── HOLD  through audio tail ────────────────────────────────
  yield* advanceTo(k13.duration_seconds);
});
