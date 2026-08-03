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
  waitFor,
} from '@revideo/core';

import timing from '../kekang-remake-v1-timing.json';

const FONT = 'PingFang SC, Noto Sans CJK SC, Microsoft YaHei, sans-serif';
const CREAM = '#fbf8f1';
const INK = '#123b30';
const GREEN_DARK = '#075d3b';

type Cue = {start: number; end: number; text: string};
type Segment = {duration_seconds: number; cues: Cue[]};
type Combination = {
  title: string;
  context: string;
  contextImage: string;
  productA: string;
  productAImage: string | null;
  tint: string;
  accent: string;
};
const k16 = timing.segments.k16 as Segment;

const COMBINATIONS: Combination[] = [
  {
    title: '谷维素片 ＋ 灵芝胶囊',
    context: '晚上睡不着、夜里容易醒',
    contextImage: '/kekang-lingzhi/v3/audience-insomnia-v3.png',
    productA: '谷维素片',
    productAImage: null,
    tint: '#f0ebfa',
    accent: '#7460a8',
  },
  {
    title: '护肝片 ＋ 灵芝胶囊',
    context: '关注肝脏健康',
    contextImage: '/kekang-lingzhi/v3/joint-liver-v3.png',
    productA: '护肝片',
    productAImage: null,
    tint: '#e5f3ea',
    accent: '#348a59',
  },
  {
    title: '转移因子口服溶液 ＋ 灵芝胶囊',
    context: '容易反复不舒服、抵抗力较弱',
    contextImage: '/kekang-lingzhi/v3/audience-low-immune-v3.png',
    productA: '转移因子口服溶液',
    productAImage: null,
    tint: '#e4f2f5',
    accent: '#267a8b',
  },
];

export const k16RelationScene = makeScene2D('k16-relation', function* (view) {
  const stageBack = createRef<Rect>();
  const combinationTitle = createRef<Txt>();
  const titleRule = createRef<Line>();
  const contextGroup = createRef<Rect>();
  const contextImage = createRef<Img>();
  const contextText = createRef<Txt>();
  const leftShowcase = createRef<Rect>();
  const leftSlot = createRef<Rect>();
  const leftProductImage = createRef<Img>();
  const leftSlotLineA = createRef<Line>();
  const leftSlotLineB = createRef<Line>();
  const leftName = createRef<Txt>();
  const rightShowcase = createRef<Rect>();
  const rightPackshot = createRef<Img>();
  const plus = createRef<Txt>();
  const linkLine = createRef<Line>();
  const subtitle = createRef<Txt>();

  view.add(
    <>
      <Audio src={'/kekang-remake-v1/k16-mix-final.wav'} play />
      <Rect size={[1920, 1080]} fill={CREAM}>
        <Circle position={[-850, 520]} size={760} fill={'#f1e8d4'} opacity={0.62} />
        <Circle position={[870, -480]} size={820} fill={'#dff1e7'} opacity={0.7} />
        <Txt
          position={[-690, -440]}
          text={'联合用药组合'}
          fontFamily={FONT}
          fontSize={52}
          fontWeight={880}
          fill={INK}
        />
        <Rect position={[770, -472]} size={[190, 58]} radius={29} fill={'rgba(7,93,59,0.88)'}>
          <Txt text={'模板示例'} fontFamily={FONT} fontSize={26} fontWeight={760} fill={'#ffffff'} />
        </Rect>

        <Rect
          ref={stageBack}
          position={[0, 42]}
          size={[1640, 670]}
          radius={74}
          fill={COMBINATIONS[0].tint}
          stroke={'rgba(7,93,59,0.14)'}
          lineWidth={4}
          shadowColor={'rgba(18,59,48,0.13)'}
          shadowBlur={34}
        >
          <Txt
            ref={combinationTitle}
            position={[0, -270]}
            width={1240}
            text={COMBINATIONS[0].title}
            textAlign={'center'}
            fontFamily={FONT}
            fontSize={48}
            fontWeight={900}
            fill={INK}
            opacity={0}
          />
          <Line
            ref={titleRule}
            points={[[-300, -218], [300, -218]]}
            stroke={COMBINATIONS[0].accent}
            lineWidth={7}
            lineCap={'round'}
            start={0.5}
            end={0.5}
          />

          <Rect
            ref={contextGroup}
            position={[-620, -235]}
            size={[300, 96]}
            radius={48}
            fill={'rgba(255,255,255,0.9)'}
            stroke={'rgba(18,59,48,0.12)'}
            lineWidth={3}
            opacity={0}
          >
            <Img
              ref={contextImage}
              position={[-101, 0]}
              src={COMBINATIONS[0].contextImage}
              size={[78, 78]}
              radius={39}
            />
            <Txt
              ref={contextText}
              position={[42, 0]}
              width={190}
              text={COMBINATIONS[0].context}
              textAlign={'center'}
              fontFamily={FONT}
              fontSize={24}
              fontWeight={760}
              fill={INK}
            />
          </Rect>

          <Circle position={[-380, 45]} size={450} fill={'rgba(255,255,255,0.46)'} />
          <Circle position={[380, 45]} size={450} fill={'rgba(255,255,255,0.46)'} />

          <Rect
            ref={leftShowcase}
            position={[-380, 55]}
            size={[520, 430]}
            radius={56}
            fill={'rgba(255,255,255,0.72)'}
            shadowColor={'rgba(18,59,48,0.14)'}
            shadowBlur={28}
            opacity={0}
            scale={0.82}
          >
            <Rect
              ref={leftSlot}
              position={[0, -35]}
              size={[250, 290]}
              radius={28}
              fill={'rgba(255,255,255,0.82)'}
              stroke={COMBINATIONS[0].accent}
              lineWidth={5}
              lineDash={[18, 14]}
            >
              <Circle position={[55, -72]} size={34} fill={COMBINATIONS[0].accent} opacity={0.34} />
              <Line
                ref={leftSlotLineA}
                points={[[-82, 82], [-22, 16], [26, 60], [82, -6]]}
                stroke={COMBINATIONS[0].accent}
                lineWidth={8}
                lineCap={'round'}
              />
              <Line
                ref={leftSlotLineB}
                points={[[-82, 82], [82, 82]]}
                stroke={COMBINATIONS[0].accent}
                lineWidth={8}
                lineCap={'round'}
              />
            </Rect>
            <Img
              ref={leftProductImage}
              position={[0, -35]}
              src={'/kekang-lingzhi/packshot.png'}
              size={[228, 342]}
              radius={12}
              opacity={0}
            />
            <Txt
              ref={leftName}
              position={[0, 165]}
              width={460}
              text={COMBINATIONS[0].productA}
              textAlign={'center'}
              fontFamily={FONT}
              fontSize={38}
              fontWeight={900}
              fill={INK}
            />
          </Rect>

          <Rect
            ref={rightShowcase}
            position={[380, 55]}
            size={[520, 430]}
            radius={56}
            fill={'rgba(255,255,255,0.72)'}
            shadowColor={'rgba(18,59,48,0.14)'}
            shadowBlur={28}
            opacity={0}
            scale={0.82}
          >
            <Img
              ref={rightPackshot}
              position={[0, -34]}
              src={'/kekang-lingzhi/packshot.png'}
              size={[228, 342]}
              radius={12}
            />
            <Txt
              position={[0, 165]}
              width={460}
              text={'灵芝胶囊'}
              textAlign={'center'}
              fontFamily={FONT}
              fontSize={38}
              fontWeight={900}
              fill={INK}
            />
          </Rect>

          <Line
            ref={linkLine}
            points={[[-112, 45], [-42, 45], [42, 45], [112, 45]]}
            stroke={COMBINATIONS[0].accent}
            lineWidth={8}
            lineCap={'round'}
            start={0.5}
            end={0.5}
            opacity={0}
          />
          <Circle position={[0, 45]} size={128} fill={'#fffdf8'} shadowColor={'rgba(18,59,48,0.18)'} shadowBlur={20} />
          <Txt
            ref={plus}
            position={[0, 39]}
            text={'＋'}
            fontFamily={FONT}
            fontSize={96}
            fontWeight={900}
            fill={COMBINATIONS[0].accent}
            opacity={0}
            scale={0.4}
          />
        </Rect>

        <Rect
          position={[0, 458]}
          size={[1500, 76]}
          radius={24}
          fill={'rgba(9,45,35,0.88)'}
          shadowColor={'rgba(0,0,0,0.16)'}
          shadowBlur={18}
        >
          <Txt ref={subtitle} width={1400} text={''} textAlign={'center'} fontFamily={FONT} fontSize={34} fontWeight={720} fill={'#ffffff'} />
        </Rect>
      </Rect>
    </>,
  );

  for (let index = 0; index < COMBINATIONS.length; index += 1) {
    const combination = COMBINATIONS[index];
    const sceneCue = k16.cues[index * 2];
    const pairCue = k16.cues[index * 2 + 1];

    stageBack().fill(combination.tint);
    combinationTitle().text(combination.title);
    combinationTitle().fontSize(index === 2 ? 40 : 48);
    combinationTitle().position.y(-270);
    combinationTitle().opacity(0);
    titleRule().stroke(combination.accent);
    titleRule().start(0.5);
    titleRule().end(0.5);
    contextImage().src(combination.contextImage);
    contextText().text(combination.context);
    contextText().fontSize(index === 2 ? 20 : 24);
    contextGroup().opacity(0);
    contextGroup().position.x(-700);
    leftSlot().stroke(combination.accent);
    leftSlot().opacity(combination.productAImage ? 0 : 1);
    leftSlotLineA().stroke(combination.accent);
    leftSlotLineB().stroke(combination.accent);
    leftProductImage().src(combination.productAImage ?? '/kekang-lingzhi/packshot.png');
    leftProductImage().opacity(combination.productAImage ? 1 : 0);
    leftName().text(combination.productA);
    leftName().fontSize(index === 2 ? 31 : 38);
    leftShowcase().opacity(0);
    leftShowcase().scale(0.82);
    leftShowcase().position.x(-560);
    rightShowcase().opacity(0);
    rightShowcase().scale(0.82);
    rightShowcase().position.x(560);
    plus().fill(combination.accent);
    plus().opacity(0);
    plus().scale(0.4);
    linkLine().stroke(combination.accent);
    linkLine().opacity(0);
    linkLine().start(0.5);
    linkLine().end(0.5);

    subtitle().text(sceneCue.text);
    yield* all(
      combinationTitle().opacity(1, 0.42),
      combinationTitle().position.y(-258, 0.62, easeOutCubic),
      titleRule().start(0, 0.7, easeOutCubic),
      titleRule().end(1, 0.7, easeOutCubic),
      contextGroup().opacity(1, 0.42),
      contextGroup().position.x(-620, 0.62, easeOutCubic),
    );
    yield* waitFor(Math.max(0, sceneCue.end - sceneCue.start - 0.7));

    subtitle().text(pairCue.text);
    yield* all(
      leftShowcase().opacity(1, 0.32),
      leftShowcase().scale(1, 0.72, easeOutBack),
      leftShowcase().position.x(-380, 0.72, easeOutCubic),
      rightShowcase().opacity(1, 0.32),
      rightShowcase().scale(1, 0.72, easeOutBack),
      rightShowcase().position.x(380, 0.72, easeOutCubic),
      plus().opacity(1, 0.32),
      plus().scale(1, 0.65, easeOutBack),
      linkLine().opacity(0.62, 0.25),
      linkLine().start(0, 0.72, easeOutCubic),
      linkLine().end(1, 0.72, easeOutCubic),
    );
    const exitDuration = index < COMBINATIONS.length - 1 ? 0.42 : 0;
    yield* waitFor(Math.max(0, pairCue.end - pairCue.start - 0.72 - exitDuration));

    if (index < COMBINATIONS.length - 1) {
      yield* all(
        leftShowcase().position.x(-800, 0.42, easeInOutCubic),
        leftShowcase().opacity(0, 0.32),
        rightShowcase().position.x(800, 0.42, easeInOutCubic),
        rightShowcase().opacity(0, 0.32),
        combinationTitle().position.y(-330, 0.38, easeInOutCubic),
        combinationTitle().opacity(0, 0.3),
        contextGroup().position.x(-800, 0.38, easeInOutCubic),
        contextGroup().opacity(0, 0.28),
        plus().scale(0.35, 0.32, easeInOutCubic),
        plus().opacity(0, 0.25),
        linkLine().opacity(0, 0.25),
      );
    }
  }

  yield* waitFor(Math.max(0, k16.duration_seconds - k16.cues[k16.cues.length - 1].end));
});
