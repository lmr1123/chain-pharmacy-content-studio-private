/**
 * 可可康灵芝胶囊 · 场景演绎动效短样 v1
 *
 * 目标：验证“情境出现 → 问题聚焦 → 关系建立 → 结论强化”的视频语法，
 * 不把静态 PPT 页面直接做入场动画。
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

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const GREEN = '#078b3a';
const GREEN_DARK = '#075b32';
const GREEN_DEEP = '#043f29';
const MINT = '#e5f3e8';
const CREAM = '#fbfaf4';
const INK = '#14241b';
const MUTED = '#617168';
const WHITE = '#ffffff';

const sleepIllustration =
  '/kekang-lingzhi-motion-v1/sleep-problem-illustration-candidate-v1.png';

type Ref<T> = Reference<T>;

function SignalChip({
  label,
  position,
  chipRef,
  dotRef,
}: {
  label: string;
  position: [number, number];
  chipRef: Ref<Rect>;
  dotRef: Ref<Circle>;
}) {
  return (
    <Rect
      ref={chipRef}
      position={position}
      size={[320, 92]}
      radius={46}
      fill={'rgba(255,255,255,0.94)'}
      stroke={'rgba(7,139,58,0.38)'}
      lineWidth={3}
      shadowColor={'rgba(5,49,31,0.20)'}
      shadowBlur={24}
      opacity={0}
      scale={0.76}
    >
      <Circle
        ref={dotRef}
        position={[-116, 0]}
        size={24}
        fill={GREEN}
        opacity={0.75}
      />
      <Txt
        position={[20, 0]}
        text={label}
        fontFamily={FONT}
        fontSize={42}
        fontWeight={780}
        fill={GREEN_DARK}
      />
    </Rect>
  );
}

function ProductSlot({
  name,
  slotRef,
  position,
}: {
  name: string;
  slotRef: Ref<Rect>;
  position: [number, number];
}) {
  return (
    <Rect
      ref={slotRef}
      position={position}
      size={[370, 440]}
      radius={34}
      fill={WHITE}
      stroke={'rgba(7,139,58,0.50)'}
      lineWidth={4}
      shadowColor={'rgba(5,49,31,0.16)'}
      shadowBlur={30}
      opacity={0}
      scale={0.72}
    >
      <Rect
        position={[0, -155]}
        size={[370, 88]}
        radius={[34, 34, 0, 0]}
        fill={GREEN_DARK}
      />
      <Txt
        position={[0, -155]}
        text={name}
        fontFamily={FONT}
        fontSize={40}
        fontWeight={820}
        fill={WHITE}
      />
      <Rect
        position={[0, 28]}
        size={[242, 190]}
        radius={22}
        fill={'rgba(229,243,232,0.64)'}
        stroke={'rgba(7,139,58,0.52)'}
        lineWidth={3}
        lineDash={[14, 10]}
      />
      <Txt
        position={[0, 12]}
        text={'授权包装图'}
        fontFamily={FONT}
        fontSize={33}
        fontWeight={760}
        fill={GREEN_DARK}
      />
      <Txt
        position={[0, 132]}
        text={'待业务替换'}
        fontFamily={FONT}
        fontSize={26}
        fontWeight={620}
        fill={MUTED}
      />
    </Rect>
  );
}

const scene = makeScene2D('kekang-lingzhi-motion-sample', function* (view) {
  const sleepScene = createRef<Rect>();
  const sleepImage = createRef<Img>();
  const nightTint = createRef<Rect>();
  const question = createRef<Txt>();
  const openingLead = createRef<Txt>();
  const cornerBrand = createRef<Txt>();
  const signalChips = [0, 1, 2].map(() => createRef<Rect>());
  const signalDots = [0, 1, 2].map(() => createRef<Circle>());
  const focusLine = createRef<Line>();
  const sleepConclusion = createRef<Rect>();
  const sleepConclusionText = createRef<Txt>();

  const jointScene = createRef<Rect>();
  const contextFrame = createRef<Rect>();
  const contextImage = createRef<Img>();
  const contextTag = createRef<Rect>();
  const productA = createRef<Rect>();
  const productB = createRef<Rect>();
  const plusCircle = createRef<Circle>();
  const plusText = createRef<Txt>();
  const relationLine = createRef<Line>();
  const outcome = createRef<Rect>();
  const outcomeTitle = createRef<Txt>();
  const outcomeBody = createRef<Txt>();
  const finalStatement = createRef<Rect>();
  const finalStatementText = createRef<Txt>();

  view.add(
    <>
      <Audio src={'/kekang-lingzhi-motion-v1/silence-30s.wav'} play />
      <Rect ref={sleepScene} size={[1920, 1080]} fill={CREAM}>
        <Img
          ref={sleepImage}
          src={sleepIllustration}
          size={[1920, 1080]}
          scale={1.04}
        />
        <Rect
          ref={nightTint}
          size={[1920, 1080]}
          fill={'rgba(3,25,42,0.28)'}
        />
        <Txt
          ref={cornerBrand}
          position={[-716, -470]}
          text={'大参林  ·  内部商品培训'}
          fontFamily={FONT}
          fontSize={28}
          fontWeight={720}
          fill={'rgba(255,255,255,0.90)'}
          opacity={0}
        />
        <Txt
          ref={question}
          position={[-385, 304]}
          width={1010}
          text={'顾客说：“最近总是睡不好……”'}
          fontFamily={FONT}
          fontSize={70}
          lineHeight={94}
          fontWeight={820}
          fill={WHITE}
          shadowColor={'rgba(0,0,0,0.38)'}
          shadowBlur={20}
          opacity={0}
        />
        <Txt
          ref={openingLead}
          position={[-480, 420]}
          width={820}
          text={'不要急着讲产品，先看见顾客的真实状态'}
          fontFamily={FONT}
          fontSize={36}
          fontWeight={650}
          fill={'rgba(255,255,255,0.92)'}
          opacity={0}
        />
        <Line
          ref={focusLine}
          points={[[-330, 382], [72, 382]]}
          stroke={'#7fe09d'}
          lineWidth={6}
          end={0}
        />
        <SignalChip
          label={'入睡慢'}
          position={[590, -250]}
          chipRef={signalChips[0]}
          dotRef={signalDots[0]}
        />
        <SignalChip
          label={'夜间易醒'}
          position={[680, -78]}
          chipRef={signalChips[1]}
          dotRef={signalDots[1]}
        />
        <SignalChip
          label={'早醒疲倦'}
          position={[590, 94]}
          chipRef={signalChips[2]}
          dotRef={signalDots[2]}
        />
        <Rect
          ref={sleepConclusion}
          position={[0, 392]}
          size={[1220, 132]}
          radius={66}
          fill={'rgba(4,63,41,0.94)'}
          opacity={0}
          scale={0.92}
        >
          <Txt
            ref={sleepConclusionText}
            text={'先问清睡眠表现，再进入商品沟通'}
            fontFamily={FONT}
            fontSize={52}
            fontWeight={800}
            fill={WHITE}
            opacity={0}
          />
        </Rect>
      </Rect>

      <Rect
        ref={jointScene}
        size={[1920, 1080]}
        fill={CREAM}
        opacity={0}
      >
        <Txt
          position={[-716, -470]}
          text={'大参林  ·  联合用药演绎'}
          fontFamily={FONT}
          fontSize={28}
          fontWeight={720}
          fill={GREEN_DARK}
        />
        <Rect
          ref={contextFrame}
          position={[-640, -15]}
          size={[470, 690]}
          radius={54}
          clip
          fill={MINT}
          opacity={0}
          scale={0.92}
        >
          <Img
            ref={contextImage}
            src={sleepIllustration}
            size={[1160, 652]}
            position={[-140, -80]}
          />
          <Rect
            position={[0, 260]}
            size={[470, 170]}
            fill={'rgba(4,63,41,0.93)'}
          />
          <Txt
            position={[0, 235]}
            text={'失眠顾客'}
            fontFamily={FONT}
            fontSize={48}
            fontWeight={820}
            fill={WHITE}
          />
          <Txt
            position={[0, 300]}
            text={'入睡困难 · 易醒 · 早醒'}
            fontFamily={FONT}
            fontSize={28}
            fontWeight={640}
            fill={'rgba(255,255,255,0.88)'}
          />
        </Rect>
        <Rect
          ref={contextTag}
          position={[-640, -405]}
          size={[320, 62]}
          radius={31}
          fill={GREEN}
          opacity={0}
          scale={0.72}
        >
          <Txt
            text={'先判断顾客问题'}
            fontFamily={FONT}
            fontSize={29}
            fontWeight={760}
            fill={WHITE}
          />
        </Rect>
        <ProductSlot
          name={'谷维素片'}
          slotRef={productA}
          position={[-170, -68]}
        />
        <ProductSlot
          name={'灵芝胶囊'}
          slotRef={productB}
          position={[310, -68]}
        />
        <Circle
          ref={plusCircle}
          position={[70, -68]}
          size={112}
          fill={GREEN}
          opacity={0}
          scale={0.4}
        >
          <Txt
            ref={plusText}
            text={'＋'}
            fontFamily={FONT}
            fontSize={66}
            fontWeight={760}
            fill={WHITE}
            opacity={0}
          />
        </Circle>
        <Line
          ref={relationLine}
          points={[[70, 186], [70, 266], [560, 266]]}
          stroke={GREEN}
          lineWidth={7}
          radius={18}
          end={0}
        />
        <Rect
          ref={outcome}
          position={[600, 266]}
          size={[580, 230]}
          radius={42}
          fill={GREEN_DARK}
          opacity={0}
          scale={0.78}
        >
          <Txt
            ref={outcomeTitle}
            position={[0, -48]}
            text={'组合逻辑'}
            fontFamily={FONT}
            fontSize={31}
            fontWeight={720}
            fill={'#8ee6a8'}
            opacity={0}
          />
          <Txt
            ref={outcomeBody}
            position={[0, 34]}
            text={'营养神经  ＋  镇静助眠'}
            fontFamily={FONT}
            fontSize={42}
            fontWeight={820}
            fill={WHITE}
            opacity={0}
          />
        </Rect>
        <Rect
          ref={finalStatement}
          position={[0, 420]}
          size={[1460, 126]}
          radius={63}
          fill={GREEN_DEEP}
          opacity={0}
          scale={0.94}
        >
          <Txt
            ref={finalStatementText}
            text={'联合用药的价值，不是产品堆叠，而是作用互补'}
            fontFamily={FONT}
            fontSize={50}
            fontWeight={800}
            fill={WHITE}
            opacity={0}
          />
        </Rect>
      </Rect>
    </>,
  );

  // A · 睡眠问题：情境出现 → 问题聚焦 → 三个信号 → 结论强化
  yield* all(
    cornerBrand().opacity(1, 0.5),
    question().opacity(1, 0.7),
    nightTint().opacity(0.16, 0.8),
    sleepImage().scale(1.08, 2.8, easeInOutCubic),
    sleepImage().position([-46, 18], 2.8, easeInOutCubic),
  );
  yield* all(
    openingLead().opacity(1, 0.45),
    focusLine().end(1, 0.65),
  );
  yield* waitFor(0.5);

  for (let index = 0; index < signalChips.length; index += 1) {
    yield* all(
      signalChips[index]().opacity(1, 0.22),
      signalChips[index]().scale(1, 0.46, easeOutBack),
      signalDots[index]().scale(1.28, 0.25, easeOutCubic),
    );
    yield* signalDots[index]().scale(1, 0.18, easeOutCubic);
    yield* waitFor(0.24);
  }
  yield* waitFor(1.0);
  yield* all(
    question().opacity(0, 0.35),
    openingLead().opacity(0, 0.35),
    focusLine().opacity(0, 0.35),
    ...signalChips.map(chip => chip().position.x(chip().position.x() - 50, 0.45, easeOutCubic)),
    sleepConclusion().opacity(1, 0.35),
    sleepConclusion().scale(1, 0.5, easeOutBack),
    sleepConclusionText().opacity(1, 0.35),
  );
  yield* waitFor(1.8);

  // B · 联合用药：顾客情境 → 两个商品槽 → 建立关系 → 结论强化
  yield* all(
    sleepScene().opacity(0, 0.45),
    jointScene().opacity(1, 0.45),
  );
  yield* all(
    contextFrame().opacity(1, 0.35),
    contextFrame().scale(1, 0.55, easeOutBack),
    contextTag().opacity(1, 0.3),
    contextTag().scale(1, 0.48, easeOutBack),
  );
  yield* waitFor(0.5);
  yield* all(
    productA().opacity(1, 0.28),
    productA().scale(1, 0.55, easeOutBack),
  );
  yield* waitFor(0.4);
  yield* all(
    plusCircle().opacity(1, 0.2),
    plusCircle().scale(1, 0.42, easeOutBack),
    plusText().opacity(1, 0.2),
  );
  yield* waitFor(0.28);
  yield* all(
    productB().opacity(1, 0.28),
    productB().scale(1, 0.55, easeOutBack),
  );
  yield* waitFor(0.72);
  yield* relationLine().end(1, 0.7, easeOutCubic);
  yield* all(
    outcome().opacity(1, 0.3),
    outcome().scale(1, 0.52, easeOutBack),
    outcomeTitle().opacity(1, 0.28),
    outcomeBody().opacity(1, 0.38),
  );
  yield* waitFor(1.6);
  yield* all(
    contextFrame().opacity(0.18, 0.42),
    contextTag().opacity(0, 0.3),
    productA().opacity(0.18, 0.42),
    productB().opacity(0.18, 0.42),
    plusCircle().opacity(0.18, 0.42),
    plusText().opacity(0.18, 0.42),
    relationLine().opacity(0.18, 0.42),
    outcome().opacity(0.18, 0.42),
    outcomeTitle().opacity(0, 0.28),
    outcomeBody().opacity(0, 0.28),
    finalStatement().opacity(1, 0.35),
    finalStatement().scale(1, 0.52, easeOutBack),
    finalStatementText().opacity(1, 0.4),
  );
  yield* waitFor(2.4);
});

export default makeProject({
  name: 'kekang-lingzhi-motion-sample',
  scenes: [scene],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
