/**
 * 可可康灵芝胶囊 · 产品知识中心动效短样 v2
 *
 * 验证内容：产品认识 → 两类成分 → 青年/中年/老年多人群 →
 * 睡眠/肝脏/免疫三条知识路径汇聚。
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
  loop,
  makeProject,
  waitFor,
} from '@revideo/core';

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const GREEN = '#078b3a';
const GREEN_DARK = '#075b32';
const GREEN_DEEP = '#043f29';
const MINT = '#e5f3e8';
const CREAM = '#fbfaf4';
const GOLD = '#d9ae50';
const WHITE = '#ffffff';
const INK = '#14241b';
const MUTED = '#607067';

const packshot = '/kekang-lingzhi/packshot.png';
const ganoderma = '/kekang-lingzhi/v3/ganoderma-hero-v3.png';
const young =
  '/product-training-opening-characters/age-reference-young-v2.png';
const middle =
  '/kekang-lingzhi/product-centered-v2/middle-age-man-v1.png';
const elder =
  '/product-training-opening-characters/age-reference-elder-glasses-v2.png';

type Ref<T> = Reference<T>;

function KnowledgeChip({
  chipRef,
  label,
  position,
  fill,
}: {
  chipRef: Ref<Rect>;
  label: string;
  position: [number, number];
  fill: string;
}) {
  return (
    <Rect
      ref={chipRef}
      position={position}
      size={[390, 104]}
      radius={52}
      fill={fill}
      shadowColor={'rgba(4,63,41,0.18)'}
      shadowBlur={24}
      opacity={0}
      scale={0.72}
    >
      <Txt
        text={label}
        fontFamily={FONT}
        fontSize={42}
        fontWeight={800}
        fill={WHITE}
      />
    </Rect>
  );
}

function PersonStage({
  stageRef,
  imageRef,
  haloRef,
  image,
  label,
  concern,
  position,
  accent,
}: {
  stageRef: Ref<Rect>;
  imageRef: Ref<Img>;
  haloRef: Ref<Circle>;
  image: string;
  label: string;
  concern: string;
  position: [number, number];
  accent: string;
}) {
  return (
    <Rect
      ref={stageRef}
      position={position}
      size={[480, 720]}
      radius={54}
      fill={'rgba(255,255,255,0.90)'}
      stroke={'rgba(7,139,58,0.16)'}
      lineWidth={3}
      shadowColor={'rgba(4,63,41,0.13)'}
      shadowBlur={34}
      opacity={0}
      scale={0.82}
      clip
    >
      <Circle
        ref={haloRef}
        position={[0, -70]}
        size={390}
        fill={accent}
        opacity={0.22}
        scale={0.78}
      />
      <Img
        ref={imageRef}
        src={image}
        position={[0, -12]}
        size={[340, 510]}
      />
      <Rect
        position={[0, 276]}
        size={[480, 168]}
        fill={GREEN_DEEP}
      >
        <Txt
          position={[0, -30]}
          text={label}
          fontFamily={FONT}
          fontSize={42}
          fontWeight={820}
          fill={WHITE}
        />
        <Txt
          position={[0, 32]}
          text={concern}
          fontFamily={FONT}
          fontSize={28}
          fontWeight={650}
          fill={'rgba(255,255,255,0.78)'}
        />
      </Rect>
    </Rect>
  );
}

const scene = makeScene2D(
  'kekang-lingzhi-product-centered-sample',
  function* (view) {
    const intro = createRef<Rect>();
    const brand = createRef<Txt>();
    const heroGlow = createRef<Circle>();
    const ganodermaImage = createRef<Img>();
    const product = createRef<Img>();
    const productTitle = createRef<Txt>();
    const productSub = createRef<Txt>();
    const polyChip = createRef<Rect>();
    const triChip = createRef<Rect>();
    const ingredientLineA = createRef<Line>();
    const ingredientLineB = createRef<Line>();

    const audience = createRef<Rect>();
    const audienceTitle = createRef<Txt>();
    const audienceSub = createRef<Txt>();
    const youngStage = createRef<Rect>();
    const middleStage = createRef<Rect>();
    const elderStage = createRef<Rect>();
    const youngImage = createRef<Img>();
    const middleImage = createRef<Img>();
    const elderImage = createRef<Img>();
    const youngHalo = createRef<Circle>();
    const middleHalo = createRef<Circle>();
    const elderHalo = createRef<Circle>();

    const converge = createRef<Rect>();
    const convergeProduct = createRef<Img>();
    const convergeGlow = createRef<Circle>();
    const pathA = createRef<Line>();
    const pathB = createRef<Line>();
    const pathC = createRef<Line>();
    const sleepChip = createRef<Rect>();
    const liverChip = createRef<Rect>();
    const immuneChip = createRef<Rect>();
    const finalLine = createRef<Rect>();
    const finalText = createRef<Txt>();
    const boundary = createRef<Txt>();

    view.add(
      <>
        <Audio src={'/kekang-lingzhi-motion-v1/silence-30s.wav'} play />

        <Rect ref={intro} size={[1920, 1080]} fill={CREAM}>
          <Rect
            size={[1920, 1080]}
            fill={'#edf6ef'}
          />
          <Txt
            ref={brand}
            position={[-710, -474]}
            text={'大参林  ·  内部商品知识培训'}
            fontFamily={FONT}
            fontSize={28}
            fontWeight={720}
            fill={GREEN_DARK}
            opacity={0}
          />
          <Circle
            ref={heroGlow}
            position={[432, 4]}
            size={720}
            fill={'rgba(217,174,80,0.22)'}
            opacity={0}
            scale={0.55}
          />
          <Img
            ref={ganodermaImage}
            src={ganoderma}
            position={[410, 18]}
            size={[700, 700]}
            opacity={0}
            scale={0.72}
          />
          <Img
            ref={product}
            src={packshot}
            position={[495, 55]}
            size={[370, 450]}
            opacity={0}
            scale={0.74}
          />
          <Txt
            ref={productTitle}
            position={[-520, -110]}
            width={780}
            text={'可可康灵芝胶囊'}
            fontFamily={FONT}
            fontSize={82}
            fontWeight={880}
            fill={GREEN_DEEP}
            opacity={0}
          />
          <Txt
            ref={productSub}
            position={[-570, 20]}
            width={680}
            text={'从灵芝与核心有效成分\n认识这款产品'}
            fontFamily={FONT}
            fontSize={42}
            lineHeight={64}
            fontWeight={650}
            fill={MUTED}
            opacity={0}
          />
          <Line
            ref={ingredientLineA}
            points={[[250, -50], [-40, -240], [-350, -240]]}
            stroke={GREEN}
            lineWidth={6}
            radius={16}
            end={0}
          />
          <Line
            ref={ingredientLineB}
            points={[[250, 85], [-40, 270], [-350, 270]]}
            stroke={GOLD}
            lineWidth={6}
            radius={16}
            end={0}
          />
          <KnowledgeChip
            chipRef={polyChip}
            label={'灵芝多糖'}
            position={[-510, -240]}
            fill={GREEN}
          />
          <KnowledgeChip
            chipRef={triChip}
            label={'灵芝三萜'}
            position={[-510, 270]}
            fill={'#b6882f'}
          />
        </Rect>

        <Rect ref={audience} size={[1920, 1080]} fill={CREAM} opacity={0}>
          <Rect
            size={[1920, 1080]}
            fill={'#f1f7f1'}
          />
          <Txt
            ref={audienceTitle}
            position={[0, -458]}
            text={'不同生活阶段，都可能关注这些健康方向'}
            fontFamily={FONT}
            fontSize={58}
            fontWeight={850}
            fill={GREEN_DEEP}
            opacity={0}
          />
          <Txt
            ref={audienceSub}
            position={[0, -388]}
            text={'年龄用于画面演绎；适应人群仍以具体情况为准'}
            fontFamily={FONT}
            fontSize={30}
            fontWeight={620}
            fill={MUTED}
            opacity={0}
          />
          <PersonStage
            stageRef={youngStage}
            imageRef={youngImage}
            haloRef={youngHalo}
            image={young}
            label={'青年'}
            concern={'经常失眠'}
            position={[-550, 80]}
            accent={'#776cc8'}
          />
          <PersonStage
            stageRef={middleStage}
            imageRef={middleImage}
            haloRef={middleHalo}
            image={middle}
            label={'中年'}
            concern={'常喝酒伤肝／肝功能差'}
            position={[0, 80]}
            accent={'#e1a648'}
          />
          <PersonStage
            stageRef={elderStage}
            imageRef={elderImage}
            haloRef={elderHalo}
            image={elder}
            label={'老年'}
            concern={'免疫力低下'}
            position={[550, 80]}
            accent={'#4aa9ba'}
          />
        </Rect>

        <Rect ref={converge} size={[1920, 1080]} fill={CREAM} opacity={0}>
          <Rect
            size={[1920, 1080]}
            fill={'#e7f2e9'}
          />
          <Txt
            position={[-708, -470]}
            text={'产品三大核心功效'}
            fontFamily={FONT}
            fontSize={30}
            fontWeight={760}
            fill={GREEN_DARK}
          />
          <Circle
            ref={convergeGlow}
            position={[0, 20]}
            size={650}
            fill={'rgba(7,139,58,0.13)'}
            opacity={0}
            scale={0.55}
          />
          <Img
            ref={convergeProduct}
            src={packshot}
            position={[0, 24]}
            size={[330, 400]}
            opacity={0}
            scale={0.65}
          />
          <Line
            ref={pathA}
            points={[[-620, -260], [-350, -130], [-168, -45]]}
            stroke={'#776cc8'}
            lineWidth={9}
            radius={24}
            end={0}
          />
          <Line
            ref={pathB}
            points={[[-620, 260], [-350, 145], [-168, 70]]}
            stroke={'#d49a37'}
            lineWidth={9}
            radius={24}
            end={0}
          />
          <Line
            ref={pathC}
            points={[[620, 0], [350, 0], [168, 15]]}
            stroke={'#3f9faf'}
            lineWidth={9}
            radius={24}
            end={0}
          />
          <KnowledgeChip
            chipRef={sleepChip}
            label={'安神助眠'}
            position={[-660, -300]}
            fill={'#675bb6'}
          />
          <KnowledgeChip
            chipRef={liverChip}
            label={'保肝抗衰'}
            position={[-660, 300]}
            fill={'#b88127'}
          />
          <KnowledgeChip
            chipRef={immuneChip}
            label={'提升免疫'}
            position={[660, 0]}
            fill={'#2d8c9c'}
          />
          <Rect
            ref={finalLine}
            position={[0, 422]}
            size={[1500, 124]}
            radius={62}
            fill={GREEN_DEEP}
            opacity={0}
            scale={0.92}
          >
            <Txt
              ref={finalText}
              text={'从产品出发，认识成分、功效与适应人群'}
              fontFamily={FONT}
              fontSize={50}
              fontWeight={820}
              fill={WHITE}
              opacity={0}
            />
          </Rect>
          <Txt
            ref={boundary}
            position={[0, 505]}
            text={'内部培训候选 · 年龄层为视觉覆盖，不新增医学适用范围'}
            fontFamily={FONT}
            fontSize={24}
            fontWeight={590}
            fill={MUTED}
            opacity={0}
          />
        </Rect>
      </>,
    );

    // A · 产品认识：主体进入 → 灵芝空间 → 双成分从产品分化
    yield* all(
      brand().opacity(1, 0.45),
      productTitle().opacity(1, 0.65),
      productTitle().position.x(-470, 0.9, easeOutCubic),
      productSub().opacity(1, 0.6),
      heroGlow().opacity(1, 0.7),
      heroGlow().scale(1, 0.9, easeOutCubic),
      ganodermaImage().opacity(0.88, 0.8),
      ganodermaImage().scale(1, 1.0, easeOutBack),
    );
    yield* all(
      product().opacity(1, 0.35),
      product().scale(1, 0.65, easeOutBack),
      ganodermaImage().position.x(360, 1.0, easeInOutCubic),
      ganodermaImage().opacity(0.38, 0.9),
    );
    yield* waitFor(0.5);
    yield* all(
      ingredientLineA().end(1, 0.75, easeOutCubic),
      ingredientLineB().end(1, 0.75, easeOutCubic),
    );
    yield* all(
      polyChip().opacity(1, 0.28),
      polyChip().scale(1, 0.52, easeOutBack),
    );
    yield* waitFor(0.32);
    yield* all(
      triChip().opacity(1, 0.28),
      triChip().scale(1, 0.52, easeOutBack),
    );
    yield* waitFor(1.45);

    // B · 多人群：三个生活阶段依次成为主体，而不是静态三栏同时出现。
    yield* all(intro().opacity(0, 0.5), audience().opacity(1, 0.5));
    yield* all(
      audienceTitle().opacity(1, 0.5),
      audienceTitle().position.y(-438, 0.65, easeOutCubic),
      audienceSub().opacity(1, 0.55),
    );
    yield* all(
      youngStage().opacity(1, 0.28),
      youngStage().scale(1, 0.62, easeOutBack),
      youngStage().position.x(-520, 0.7, easeOutCubic),
      youngHalo().scale(1, 0.7, easeOutCubic),
    );
    yield* loop(2, function* () {
      yield* youngImage().position.y(-22, 0.45, easeInOutCubic);
      yield* youngImage().position.y(-12, 0.45, easeInOutCubic);
    });
    yield* all(
      youngStage().scale(0.93, 0.4, easeOutCubic),
      youngStage().opacity(0.68, 0.4),
      middleStage().opacity(1, 0.28),
      middleStage().scale(1, 0.62, easeOutBack),
      middleHalo().scale(1, 0.7, easeOutCubic),
    );
    yield* loop(2, function* () {
      yield* middleHalo().opacity(0.34, 0.38, easeInOutCubic);
      yield* middleHalo().opacity(0.2, 0.38, easeInOutCubic);
    });
    yield* all(
      middleStage().scale(0.93, 0.4, easeOutCubic),
      middleStage().opacity(0.68, 0.4),
      elderStage().opacity(1, 0.28),
      elderStage().scale(1, 0.62, easeOutBack),
      elderHalo().scale(1, 0.7, easeOutCubic),
    );
    yield* loop(2, function* () {
      yield* elderHalo().scale(1.06, 0.42, easeInOutCubic);
      yield* elderHalo().scale(1, 0.42, easeInOutCubic);
    });
    yield* all(
      youngStage().opacity(1, 0.38),
      youngStage().scale(1, 0.38),
      middleStage().opacity(1, 0.38),
      middleStage().scale(1, 0.38),
    );
    yield* waitFor(1.0);

    // C · 三条知识路径汇聚回产品，强调本片主体仍然是产品。
    yield* all(audience().opacity(0, 0.5), converge().opacity(1, 0.5));
    yield* all(
      convergeGlow().opacity(1, 0.5),
      convergeGlow().scale(1, 0.75, easeOutCubic),
      convergeProduct().opacity(1, 0.35),
      convergeProduct().scale(1, 0.65, easeOutBack),
    );
    yield* all(
      sleepChip().opacity(1, 0.25),
      sleepChip().scale(1, 0.5, easeOutBack),
      pathA().end(1, 0.75, easeOutCubic),
    );
    yield* waitFor(0.3);
    yield* all(
      liverChip().opacity(1, 0.25),
      liverChip().scale(1, 0.5, easeOutBack),
      pathB().end(1, 0.75, easeOutCubic),
    );
    yield* waitFor(0.3);
    yield* all(
      immuneChip().opacity(1, 0.25),
      immuneChip().scale(1, 0.5, easeOutBack),
      pathC().end(1, 0.75, easeOutCubic),
    );
    yield* waitFor(1.1);
    yield* all(
      convergeGlow().scale(1.08, 0.55, easeInOutCubic),
      finalLine().opacity(1, 0.35),
      finalLine().scale(1, 0.52, easeOutBack),
      finalText().opacity(1, 0.35),
      boundary().opacity(1, 0.4),
    );
    yield* waitFor(2.2);
  },
);

export default makeProject({
  name: 'kekang-lingzhi-product-centered-sample',
  scenes: [scene],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
