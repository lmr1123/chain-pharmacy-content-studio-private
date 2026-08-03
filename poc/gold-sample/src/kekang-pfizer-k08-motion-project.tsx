/**
 * 可可康 × Pfizer 叙事配方 · K08 两类成分局部动效样片
 *
 * Validation only. 只验证绿色视觉与“主体 → 双分支 → 结论标签”的运动语法；
 * 不包含功效、机制、治疗结果、正式旁白或商品包装。
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

const scene = makeScene2D('kekang-pfizer-k08-motion', function* (view) {
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

  view.add(
    <>
      <Audio src={'/kekang-lingzhi-motion-v1/silence-30s.wav'} play />
      <Rect size={[1920, 1080]} fill={CREAM}>
        <Circle position={[785, -420]} size={860} fill={MINT} opacity={0.72} />
        <Circle position={[-820, 470]} size={720} fill={'#f4ead1'} opacity={0.56} />
        <Line
          points={[[-960, 390], [-480, 230], [0, 300], [520, 160], [960, 250]]}
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
          text={'大参林内部培训 · K08 局部动效样片'}
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
          text={'从灵芝主体\n认识两类成分'}
          fontFamily={FONT}
          fontSize={76}
          lineHeight={94}
          fontWeight={880}
          fill={GREEN_DEEP}
          opacity={0}
        />
        <Line
          ref={titleRule}
          points={[[-780, -195], [-365, -195]]}
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
          points={[[-205, 18], [-400, -86], [-610, -86]]}
          stroke={GREEN}
          lineWidth={7}
          radius={24}
          end={0}
        />
        <Line
          ref={lineB}
          points={[[205, 112], [395, 230], [610, 230]]}
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
          text={'两条知识路径由同一灵芝主体展开'}
          fontFamily={FONT}
          fontSize={34}
          fontWeight={700}
          fill={INK}
          opacity={0}
        />
        <Txt
          ref={boundary}
          position={[0, 512]}
          text={'名称来自内部课件 · 局部运动语法验证 · 非医学审核结论'}
          fontFamily={FONT}
          fontSize={22}
          fontWeight={580}
          fill={MUTED}
          opacity={0}
        />
      </Rect>
    </>,
  );

  // 0–1.2s：标题和主体建立。
  yield* all(
    eyebrow().opacity(1, 0.5),
    title().opacity(1, 0.65),
    title().position.x(-430, 0.9, easeOutCubic),
    titleRule().end(1, 0.8, easeOutCubic),
    heroHalo().opacity(1, 0.55),
    heroHalo().scale(1, 0.9, easeOutCubic),
    heroOrbit().opacity(1, 0.7),
    heroOrbit().scale(1, 0.9, easeOutCubic),
    heroFrame().opacity(1, 0.45),
    heroFrame().scale(1, 0.85, easeOutBack),
    dotA().opacity(0.6, 0.6),
    dotB().opacity(0.65, 0.6),
    dotC().opacity(0.55, 0.6),
  );
  yield* all(
    heroCaption().opacity(1, 0.28),
    heroCaption().scale(1, 0.46, easeOutBack),
  );
  yield* waitFor(0.18);

  // 1.2–3.2s：双路径分化，标签依次进入。
  yield* all(
    lineA().end(1, 0.72, easeOutCubic),
    lineB().end(1, 0.72, easeOutCubic),
  );
  yield* all(cardA().opacity(1, 0.28), cardA().scale(1, 0.52, easeOutBack));
  yield* waitFor(0.24);
  yield* all(cardB().opacity(1, 0.28), cardB().scale(1, 0.52, easeOutBack));
  yield* waitFor(0.32);

  // 3.2–5.1s：两个知识标签轮流成为焦点。
  yield* all(
    cardA().scale(1.055, 0.36, easeInOutCubic),
    markerA().scale(1.08, 0.36, easeInOutCubic),
    cardB().opacity(0.62, 0.36),
  );
  yield* all(
    cardA().scale(1, 0.34, easeInOutCubic),
    markerA().scale(1, 0.34, easeInOutCubic),
    cardB().opacity(1, 0.34),
  );
  yield* all(
    cardB().scale(1.055, 0.36, easeInOutCubic),
    markerB().scale(1.08, 0.36, easeInOutCubic),
    cardA().opacity(0.62, 0.36),
  );
  yield* all(
    cardB().scale(1, 0.34, easeInOutCubic),
    markerB().scale(1, 0.34, easeInOutCubic),
    cardA().opacity(1, 0.34),
  );

  // 5.1–7.7s：稳定完成帧，保留细微环境运动供动态辨识。
  yield* all(
    completion().opacity(1, 0.45),
    completion().position.y(448, 0.55, easeOutCubic),
    boundary().opacity(1, 0.45),
  );
  yield* loop(2, function* (iteration) {
    const firstRotation = iteration === 0 ? 22 : 66;
    const secondRotation = iteration === 0 ? 44 : 88;
    yield* all(
      heroOrbit().rotation(firstRotation, 0.45, easeInOutCubic),
      heroHalo().scale(1.035, 0.45, easeInOutCubic),
      dotA().position.y(-165, 0.45, easeInOutCubic),
      dotB().position.y(278, 0.45, easeInOutCubic),
    );
    yield* all(
      heroOrbit().rotation(secondRotation, 0.45, easeInOutCubic),
      heroHalo().scale(1, 0.45, easeInOutCubic),
      dotA().position.y(-155, 0.45, easeInOutCubic),
      dotB().position.y(270, 0.45, easeInOutCubic),
    );
  });
  yield* waitFor(0.1);
});

export default makeProject({
  name: 'kekang-pfizer-k08-motion',
  scenes: [scene],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
