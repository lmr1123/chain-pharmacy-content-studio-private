/**
 * 可可康灵芝胶囊 v7 · 最终交付标准签样片
 *
 * 代表段：数字人开场 → 三类人群同页顺序聚焦 → 三大功效回收。
 * 本工程直接复用于后续整片，不是静帧录屏或无声动效示例。
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
  Reference,
  all,
  createRef,
  easeInOutCubic,
  easeOutBack,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../kekang-lingzhi-v7-signoff.json';

type Cue = {start: number; end: number; text: string};
type ImgRef = Reference<Img>;
type RectRef = Reference<Rect>;

const cues = data.cues as Cue[];
const DURATION = Number(data.playback_duration);
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';

const GREEN = '#078b3a';
const GREEN_DARK = '#075b32';
const GREEN_DEEP = '#043f29';
const MINT = '#e7f3e9';
const CREAM = '#fbf8ed';
const GOLD = '#efc95d';
const INK = '#14241b';
const MUTED = '#607067';
const WHITE = '#ffffff';

const PRESENTER = '/product-training-dashenlin-presenter';
const presenterBody = `${PRESENTER}/palm-mouthless.png`;
const presenterMouth = (name: string) => `${PRESENTER}/mouth-${name}.png`;
const PRESENTER_META = {width: 334, height: 941};
const MOUTH_ANCHOR: [number, number] = [0.548, 0.391];

const packshot = '/kekang-lingzhi/packshot.png';
const ganoderma = '/kekang-lingzhi/v3/ganoderma-hero-v3.png';
const audienceAssets = [
  '/kekang-lingzhi/v7-signoff/audience-young-woman-insomnia-v7.png',
  '/kekang-lingzhi/v7-signoff/audience-middle-man-alcohol-v7.png',
  '/kekang-lingzhi/v7-signoff/audience-elder-woman-seasonal-v7.png',
] as const;

function bodySize(height: number): [number, number] {
  return [height * (PRESENTER_META.width / PRESENTER_META.height), height];
}

function mouthPosition(size: [number, number]): [number, number] {
  return [
    (MOUTH_ANCHOR[0] - 0.5) * size[0],
    (MOUTH_ANCHOR[1] - 0.5) * size[1],
  ];
}

function Presenter({
  root,
  mouths,
  position,
  height,
}: {
  root: RectRef;
  mouths: ImgRef[];
  position: [number, number];
  height: number;
}) {
  const size = bodySize(height);
  const [width] = size;
  const mouthPos = mouthPosition(size);
  const closed: [number, number] = [width * 0.115, width * 0.072];
  const open: [number, number] = [width * 0.124, width * 0.083];
  const mouthSizes: [number, number][] = [
    closed,
    open,
    [open[0] * 0.92, open[1] * 1.06],
    [open[0] * 1.1, open[1] * 0.95],
  ];

  return (
    <Rect ref={root} position={position} size={size}>
      <Img src={presenterBody} size={size} />
      <Rect
        position={mouthPos}
        size={[closed[0] * 1.15, closed[1] * 1.2]}
        radius={closed[1] * 0.55}
        fill={'#fce8d5'}
      />
      {(['closed', 'small', 'o', 'wide'] as const).map((name, index) => (
        <Img
          ref={mouths[index]}
          key={name}
          src={presenterMouth(name)}
          position={mouthPos}
          size={mouthSizes[index]}
          opacity={index === 0 ? 1 : 0}
        />
      ))}
    </Rect>
  );
}

function AudienceCard({
  root,
  focusLabel,
  position,
  image,
  number,
  title,
  steps,
  result,
  accent,
}: {
  root: RectRef;
  focusLabel: RectRef;
  position: [number, number];
  image: string;
  number: string;
  title: string;
  steps: string;
  result: string;
  accent: string;
}) {
  return (
    <Rect
      ref={root}
      position={position}
      size={[460, 740]}
      radius={34}
      fill={'rgba(255,255,255,0.96)'}
      stroke={'rgba(7,91,50,0.22)'}
      lineWidth={3}
      shadowColor={'rgba(26,83,48,0.14)'}
      shadowBlur={24}
      opacity={0}
      scale={0.84}
      clip
    >
      <Img
        src={image}
        position={[0, -120]}
        size={[460, 460]}
      />
      <Circle
        position={[-184, -318]}
        size={58}
        fill={GREEN}
        stroke={WHITE}
        lineWidth={4}
      >
        <Txt
          text={number}
          fontFamily={FONT}
          fontSize={23}
          fontWeight={850}
          fill={WHITE}
        />
      </Circle>
      <Rect
        ref={focusLabel}
        position={[128, -318]}
        size={[154, 44]}
        radius={22}
        fill={GREEN}
        opacity={0}
      >
        <Txt
          text={'当前讲解'}
          fontFamily={FONT}
          fontSize={18}
          fontWeight={800}
          fill={WHITE}
        />
      </Rect>
      <Rect
        position={[0, 207]}
        size={[460, 326]}
        fill={'rgba(255,255,255,0.98)'}
      >
        <Rect
          position={[-203, -92]}
          size={[10, 92]}
          radius={5}
          fill={accent}
        />
        <Txt
          position={[0, -102]}
          width={390}
          text={title}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={34}
          fontWeight={850}
          fill={GREEN_DARK}
        />
        <Txt
          position={[0, -34]}
          width={390}
          text={steps}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={23}
          lineHeight={36}
          fontWeight={560}
          fill={MUTED}
        />
        <Rect
          position={[0, 110]}
          size={[410, 60]}
          radius={16}
          fill={GREEN_DARK}
        >
          <Txt
            text={result}
            fontFamily={FONT}
            fontSize={23}
            fontWeight={820}
            fill={WHITE}
          />
        </Rect>
      </Rect>
    </Rect>
  );
}

function* runSubtitles(text: Reference<Txt>, bar: RectRef) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      text().opacity(0);
      bar().opacity(0);
      yield* waitFor(cue.start - cursor);
    }
    text().text(cue.text);
    yield* all(
      bar().opacity(1, 0.06),
      text().opacity(1, 0.06),
    );
    yield* waitFor(Math.max(0, cue.end - cue.start - 0.06));
    text().opacity(0);
    bar().opacity(0);
    cursor = cue.end;
  }
  if (cursor < DURATION) yield* waitFor(DURATION - cursor);
}

function* mouthTimeline(mouths: ImgRef[]) {
  const start = cues[0]?.start ?? 0;
  const end = cues.at(-1)?.end ?? DURATION;
  if (start > 0) yield* waitFor(start);
  let elapsed = start;
  let index = 0;
  const pattern = [1, 3, 1, 2, 1, 0, 2, 1, 3, 1];
  while (elapsed < end) {
    const active = pattern[index % pattern.length];
    mouths.forEach((mouth, mouthIndex) =>
      mouth().opacity(mouthIndex === active ? 1 : 0),
    );
    const step = Math.min(0.13 + (index % 3) * 0.025, end - elapsed);
    yield* waitFor(step);
    elapsed += step;
    index += 1;
  }
  mouths.forEach((mouth, mouthIndex) =>
    mouth().opacity(mouthIndex === 0 ? 1 : 0),
  );
  if (elapsed < DURATION) yield* waitFor(DURATION - elapsed);
}

const scene = makeScene2D('kekang-lingzhi-v7-signoff', function* (view) {
  const ambientA = createRef<Circle>();
  const ambientB = createRef<Circle>();
  const trail = createRef<Circle>();
  const presenter = createRef<Rect>();
  const mouths = [0, 1, 2, 3].map(() => createRef<Img>());

  const opening = createRef<Rect>();
  const speech = createRef<Rect>();
  const heroProduct = createRef<Rect>();
  const stage = createRef<Rect>();
  const title = createRef<Txt>();
  const progress = createRef<Line>();
  const cards = [0, 1, 2].map(() => createRef<Rect>());
  const focusLabels = [0, 1, 2].map(() => createRef<Rect>());
  const summary = createRef<Rect>();
  const summaryProduct = createRef<Img>();
  const subtitleBar = createRef<Rect>();
  const subtitle = createRef<Txt>();

  view.add(
    <>
      <Audio src={data.audio.file} play volume={1} />

      <Rect size={[1920, 1080]} fill={CREAM}>
        <Rect
          size={[1920, 1080]}
          fill={'#e7f3e9'}
          opacity={0.9}
        />
        <Circle
          ref={ambientA}
          position={[-720, -340]}
          size={650}
          fill={'rgba(255,224,130,0.30)'}
        />
        <Circle
          ref={ambientB}
          position={[720, 340]}
          size={760}
          fill={'rgba(92,188,124,0.16)'}
        />
        <Circle
          ref={trail}
          position={[600, -40]}
          size={720}
          stroke={'rgba(7,139,58,0.16)'}
          lineWidth={4}
          lineDash={[18, 18]}
        />
        {[
          [-840, -420, 22, GOLD],
          [-540, -450, 14, GREEN],
          [790, -390, 18, GREEN],
          [850, 400, 28, GOLD],
          [430, -450, 12, GREEN],
        ].map(([x, y, size, fill], index) => (
          <Circle
            key={String(index)}
            position={[x as number, y as number]}
            size={size as number}
            fill={fill as string}
            opacity={0.55}
          />
        ))}
      </Rect>

      <Txt
        position={[-715, -480]}
        text={'大参林 · 内部商品知识培训'}
        fontFamily={FONT}
        fontSize={25}
        fontWeight={750}
        fill={GREEN_DARK}
      />
      <Rect
        position={[735, -470]}
        size={[320, 56]}
        radius={28}
        fill={'rgba(255,255,255,0.80)'}
        stroke={'rgba(7,91,50,0.25)'}
        lineWidth={2}
      >
        <Txt
          text={'可可康灵芝胶囊 · 签样片'}
          fontFamily={FONT}
          fontSize={20}
          fontWeight={760}
          fill={GREEN_DARK}
        />
      </Rect>

      <Rect ref={opening} size={[1920, 1080]}>
        <Rect
          ref={speech}
          position={[-150, -155]}
          size={[650, 320]}
          radius={[34, 34, 34, 8]}
          fill={'rgba(255,253,244,0.98)'}
          stroke={GOLD}
          lineWidth={3}
          shadowColor={'rgba(36,87,52,0.14)'}
          shadowBlur={30}
          opacity={0}
          scale={0.9}
        >
          <Txt
            position={[0, -104]}
            width={560}
            text={'讲师开场 · 建立学习问题'}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={24}
            fontWeight={820}
            fill={GREEN}
          />
          <Txt
            position={[0, 15]}
            width={560}
            text={'一粒灵芝胶囊，\n应该从哪些层面真正认识？'}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={48}
            lineHeight={64}
            fontWeight={900}
            fill={INK}
          />
        </Rect>
        <Rect
          ref={heroProduct}
          position={[545, 45]}
          size={[650, 760]}
          opacity={0}
          scale={0.82}
        >
          <Circle
            position={[0, 0]}
            size={650}
            fill={'rgba(255,249,219,0.92)'}
            stroke={'rgba(239,201,93,0.48)'}
            lineWidth={5}
          />
          <Img
            src={ganoderma}
            position={[-10, -10]}
            size={[620, 620]}
            opacity={0.72}
          />
          <Img
            src={packshot}
            position={[35, 30]}
            size={[300, 420]}
          />
        </Rect>
      </Rect>

      <Rect ref={stage} size={[1920, 1080]} opacity={0}>
        <Txt
          ref={title}
          position={[130, -418]}
          width={1500}
          text={'三类典型成人状态，在同一舞台依次聚焦'}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={50}
          fontWeight={900}
          fill={GREEN_DARK}
          opacity={0}
        />
        <Txt
          position={[130, -363]}
          width={1500}
          text={'先看状态发生，再解释产品方向'}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={23}
          fontWeight={620}
          fill={MUTED}
        />
        <Line
          ref={progress}
          points={[[-560, -325], [840, -325]]}
          stroke={GREEN}
          lineWidth={7}
          radius={4}
          end={0}
        />
        <AudienceCard
          root={cards[0]}
          focusLabel={focusLabels[0]}
          position={[-420, 35]}
          image={audienceAssets[0]}
          number={'01'}
          title={'年轻女性 · 失眠'}
          steps={'难入睡 → 夜醒 → 次日疲倦'}
          result={'宁心安神助睡眠'}
          accent={'#5962ad'}
        />
        <AudienceCard
          root={cards[1]}
          focusLabel={focusLabels[1]}
          position={[75, 35]}
          image={audienceAssets[1]}
          number={'02'}
          title={'中年男性 · 饮酒'}
          steps={'饮酒累积 → 肝脏负担 → 防护建立'}
          result={'保肝护肝抗衰老'}
          accent={'#a84d3c'}
        />
        <AudienceCard
          root={cards[2]}
          focusLabel={focusLabels[2]}
          position={[570, 35]}
          image={audienceAssets[2]}
          number={'03'}
          title={'老年女性 · 季节刺激'}
          steps={'冷暖变化 → 反复不适 → 免疫盾牌'}
          result={'提升免疫少生病'}
          accent={'#218c7d'}
        />
      </Rect>

      <Rect
        ref={summary}
        position={[150, 370]}
        size={[1380, 88]}
        radius={44}
        fill={GREEN_DEEP}
        stroke={'rgba(255,255,255,0.9)'}
        lineWidth={3}
        shadowColor={'rgba(7,91,50,0.30)'}
        shadowBlur={30}
        opacity={0}
        scale={0.92}
      >
        <Img
          ref={summaryProduct}
          src={packshot}
          position={[-575, -22]}
          size={[110, 160]}
          opacity={0}
        />
        <Txt
          position={[45, 0]}
          width={1160}
          text={'安神助眠  ·  保肝抗衰  ·  提升免疫'}
          fontFamily={FONT}
          fontSize={37}
          fontWeight={880}
          fill={WHITE}
        />
      </Rect>

      <Presenter
        root={presenter}
        mouths={mouths}
        position={[-650, 75]}
        height={900}
      />

      <Rect
        ref={subtitleBar}
        position={[70, 458]}
        size={[1660, 86]}
        radius={24}
        fill={'rgba(18,36,48,0.86)'}
        opacity={0}
      />
      <Txt
        ref={subtitle}
        position={[70, 458]}
        width={1570}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={40}
        fontWeight={760}
        fill={WHITE}
        opacity={0}
      />
    </>,
  );

  function* ambientTimeline() {
    function* floatA() {
      let elapsed = 0;
      let forward = true;
      while (elapsed < DURATION) {
        const step = Math.min(3.2, DURATION - elapsed);
        yield* ambientA().position(
          forward ? [-690, -360] : [-720, -340],
          step,
          easeInOutCubic,
        );
        elapsed += step;
        forward = !forward;
      }
    }
    function* floatB() {
      let elapsed = 0;
      let forward = true;
      while (elapsed < DURATION) {
        const step = Math.min(3.8, DURATION - elapsed);
        yield* ambientB().position(
          forward ? [690, 320] : [720, 340],
          step,
          easeInOutCubic,
        );
        elapsed += step;
        forward = !forward;
      }
    }
    yield* all(
      floatA(),
      floatB(),
      trail().rotation(360 * (DURATION / 24), DURATION),
    );
  }

  function* focusCard(active: number) {
    yield* all(
      ...cards.map((card, index) =>
        all(
          card().scale(index === active ? 1.035 : 0.965, 0.36, easeOutCubic),
          card().opacity(index === active ? 1 : 0.62, 0.3),
          card().lineWidth(index === active ? 7 : 3, 0.3),
          card().stroke(
            index === active ? 'rgba(19,153,72,0.82)' : 'rgba(7,91,50,0.22)',
            0.3,
          ),
          card().shadowColor(
            index === active ? 'rgba(19,153,72,0.46)' : 'rgba(26,83,48,0.10)',
            0.3,
          ),
          card().shadowBlur(index === active ? 42 : 18, 0.3),
          focusLabels[index]().opacity(index === active ? 1 : 0, 0.22),
        ),
      ),
    );
  }

  function* visualTimeline() {
    const at = (index: number, fallback: number) =>
      cues[index]?.start ?? fallback;
    const cursor = {time: 0};
    function* waitUntil(target: number) {
      const delta = target - cursor.time;
      if (delta > 0) {
        yield* waitFor(delta);
        cursor.time = target;
      }
    }

    presenter().opacity(0);
    presenter().scale(0.92);
    yield* all(
      presenter().opacity(1, 0.45),
      presenter().scale(1, 0.7, easeOutBack),
      speech().opacity(1, 0.35),
      speech().scale(1, 0.55, easeOutBack),
      heroProduct().opacity(1, 0.5),
      heroProduct().scale(1, 0.75, easeOutBack),
    );
    cursor.time = 0.75;

    yield* waitUntil(at(1, 4));
    yield* all(
      opening().opacity(0, 0.42),
      stage().opacity(1, 0.42),
      presenter().position([-790, 95], 0.55, easeInOutCubic),
      presenter().scale(0.78, 0.55, easeInOutCubic),
      title().opacity(1, 0.36),
      progress().end(1, 0.7, easeOutCubic),
    );
    cursor.time += 0.7;
    for (let index = 0; index < cards.length; index += 1) {
      yield* all(
        cards[index]().opacity(index === 0 ? 1 : 0.62, 0.18),
        cards[index]().scale(index === 0 ? 1.035 : 0.965, 0.32, easeOutBack),
      );
      cursor.time += 0.32;
    }

    yield* waitUntil(at(2, 6));
    yield* focusCard(0);
    cursor.time += 0.36;

    yield* waitUntil(at(4, 14));
    yield* focusCard(1);
    cursor.time += 0.36;

    yield* waitUntil(at(6, 23));
    yield* focusCard(2);
    cursor.time += 0.36;

    yield* waitUntil(at(7, 28));
    yield* all(
      ...cards.map(card =>
        all(
          card().opacity(0.84, 0.3),
          card().scale(0.97, 0.3),
          card().lineWidth(4, 0.3),
          card().stroke('rgba(7,139,58,0.45)', 0.3),
          card().shadowBlur(22, 0.3),
        ),
      ),
      ...focusLabels.map(label => label().opacity(0, 0.2)),
      summary().opacity(1, 0.35),
      summary().scale(1, 0.48, easeOutBack),
      summaryProduct().opacity(1, 0.35),
    );
    cursor.time += 0.48;

    yield* waitUntil(at(8, 33));
    yield* all(
      title().text('从人群状态，建立产品知识的第一步', 0.28),
      summary().shadowBlur(48, 0.28),
      summary().scale(1.025, 0.28),
    );
    cursor.time += 0.28;
    yield* summary().scale(1, 0.35, easeOutCubic);
    cursor.time += 0.35;
    yield* waitFor(Math.max(0, DURATION - cursor.time));
  }

  yield* all(
    ambientTimeline(),
    visualTimeline(),
    runSubtitles(subtitle, subtitleBar),
    mouthTimeline(mouths),
  );
});

export default makeProject({
  name: 'kekang-lingzhi-v7-signoff',
  scenes: [scene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
    },
    rendering: {
      fps: 30,
    },
  },
});
