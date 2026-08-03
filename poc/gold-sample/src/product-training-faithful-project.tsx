import {
  Audio,
  Circle,
  Img,
  Line,
  Rect,
  Txt,
  View2D,
  makeScene2D,
} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeOutBack,
  easeOutCubic,
  linear,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../product-training-faithful.json';
import {
  DashenlinInternalNotice,
  ProductColumnBadge,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';

type Cue = {start: number; end: number; text: string};
type MouthRig = {
  normalizedMouthAnchor: [number, number];
  closedWidthRatio: number;
  openWidthRatio: number;
};
type ProductRotatingRays = {
  center: [number, number];
  haloSize: number;
  rayCount: number;
  rayColors: string[];
  revealDelay: number;
  revealDuration: number;
  rotationDegrees: number;
};

const DURATION =
  Number(
    (data as {playback_duration?: number; referenceRange?: {duration?: number}})
      .playback_duration ??
      (data as {referenceRange?: {duration?: number}}).referenceRange?.duration ??
      29.06,
  );
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const BLUE = '#43a9e4';
const DEEP_BLUE = '#1178bd';
const YELLOW = '#ffe733';
const PINK = '#e75491';
const ORANGE = '#f08b31';
const WHITE = '#ffffff';
const cues = data.cues as Cue[];
const PRODUCT_EFFECT = data.effects
  .productRotatingRays as unknown as ProductRotatingRays;
const PRODUCT_RAYS = Array.from(
  {length: PRODUCT_EFFECT.rayCount},
  (_, index) => ({
    angle: index * (360 / PRODUCT_EFFECT.rayCount),
    color: PRODUCT_EFFECT.rayColors[index % PRODUCT_EFFECT.rayColors.length],
    outerHalf: index % 2 === 0 ? 140 : 52,
    length: 1500,
  }),
);

/**
 * 大参林药师数字人（与 reference-replica 同 IP 同图）。
 * 口型布局对齐 reference-treatment / medication-advice 的 mouthLayer：
 * 归一化锚点 × 显示宽高，禁止手填像素 my 猜位置。
 *
 * 锚点由 mouthless 与有嘴原图差分得到（嘴洞中心）：
 *   palm 334×941 → (183, 368) → [0.548, 0.391]
 *   point 405×941 → (214, 393) → [0.528, 0.418]
 * 与 MOUTH_RIG.point [0.526, 0.415] 一致量级。
 */
const DASHENLIN_PRESENTER = '/product-training-dashenlin-presenter';
const asset = (name: string) =>
  name.startsWith('/') ? name : `/product-training-faithful/${name}`;
const presenterBody = (pose: 'palm' | 'point') =>
  `${DASHENLIN_PRESENTER}/${pose === 'palm' ? 'palm' : 'point'}-mouthless.png`;
const presenterMouth = (name: string) =>
  `${DASHENLIN_PRESENTER}/mouth-${name}.png`;

const POSE_META = {
  palm: {imgW: 334, imgH: 941},
  point: {imgW: 405, imgH: 941},
} as const;

/** 姿势 → 归一化嘴锚点（相对全身 PNG 宽高，0–1） */
const MOUTH_RIG = {
  palm: {anchor: [0.548, 0.391] as [number, number]},
  point: {anchor: [0.528, 0.418] as [number, number]},
} as const;

/** 身体保持源图宽高比，口型用同一显示尺寸做归一化映射 */
function bodyDisplaySize(
  pose: 'palm' | 'point',
  height: number,
): [number, number] {
  const m = POSE_META[pose];
  return [height * (m.imgW / m.imgH), height];
}

/** 与 reference-treatment mouthLayer 相同：position = (anchor-0.5)*size */
function mouthPosition(
  displaySize: [number, number],
  anchor: [number, number],
): [number, number] {
  const [width, height] = displaySize;
  return [(anchor[0] - 0.5) * width, (anchor[1] - 0.5) * height];
}

function addBackground(view: View2D) {
  view.add(
    <>
      <Rect size={[1920, 1080]} fill={BLUE} />
      {Array.from({length: 10}, (_, row) =>
        Array.from({length: 18}, (_, column) => (
          <Rect
            key={`${row}-${column}`}
            position={[-900 + column * 110, -495 + row * 110]}
            size={[76, 76]}
            radius={13}
            fill={
              (row + column) % 3 === 0
                ? 'rgba(255,255,255,0.035)'
                : 'rgba(13,114,183,0.035)'
            }
            rotation={(row + column) % 2 === 0 ? 8 : -8}
          />
        )),
      )}
      <Circle
        position={[-720, -20]}
        size={920}
        fill={'rgba(255,255,255,0.035)'}
      />
    </>,
  );
}

function addFixedChrome(view: View2D) {
  view.add(
    <>
      <ProductColumnBadge text={'辅酶Q10'} />
      <DashenlinInternalNotice />
    </>,
  );
}

function addSubtitle(view: View2D) {
  const ref = createRef<Txt>();
  view.add(
    <Txt
      ref={ref}
      position={[-40, 455]}
      width={1640}
      textAlign={'center'}
      fontFamily={FONT}
      fontSize={60}
      fontWeight={900}
      fill={YELLOW}
      stroke={'rgba(24,36,55,0.98)'}
      lineWidth={3.5}
      shadowColor={'rgba(0,0,0,0.28)'}
      shadowBlur={4}
      opacity={0}
    />,
  );
  return ref;
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
  if (cursor < DURATION) yield* waitFor(DURATION - cursor);
}

/**
 * 对齐 reference-treatment / medication-advice 的 mouthLayer。
 * 口型尺寸按身体显示宽度比例，与角色缩放联动。
 */
function mouthLayers(
  id: string,
  refs: Reference<Img>[],
  pose: 'palm' | 'point',
  displaySize: [number, number],
) {
  const [width] = displaySize;
  const position = mouthPosition(displaySize, MOUTH_RIG[pose].anchor);
  const closedSize: [number, number] = [width * 0.115, width * 0.072];
  const openSize: [number, number] = [width * 0.124, width * 0.083];
  const sizes: [number, number][] = [
    closedSize,
    openSize,
    [openSize[0] * 0.92, openSize[1] * 1.06],
    [openSize[0] * 1.1, openSize[1] * 0.95],
  ];
  // 肤色盖层：盖住 mouthless 残留缝隙；必须与口型同锚点
  const coverSize: [number, number] = [
    closedSize[0] * 1.15,
    closedSize[1] * 1.2,
  ];
  return (
    <>
      <Rect
        key={`${id}-mouth-cover`}
        position={position}
        size={coverSize}
        radius={coverSize[1] * 0.5}
        fill={'#fce8d5'}
      />
      {(['closed', 'small', 'o', 'wide'] as const).map((name, index) => (
        <Img
          key={`${id}-mouth-${name}`}
          ref={refs[index]}
          src={presenterMouth(name)}
          position={position}
          size={sizes[index]}
          opacity={index === 0 ? 1 : 0}
        />
      ))}
    </>
  );
}

function Presenter({
  id,
  containerRef,
  pose,
  position,
  height,
  mouths,
}: {
  id: string;
  containerRef: Reference<Rect>;
  pose: 'palm' | 'point';
  position: [number, number];
  /** 仅指定高度，宽度按源图比例，口型用同一显示尺寸映射 */
  height: number;
  mouths: Reference<Img>[];
}) {
  const size = bodyDisplaySize(pose, height);
  return (
    <Rect
      key={`editable:q10:faithful:presenter:${id}`}
      ref={containerRef}
      position={position}
      size={size}
    >
      <Img
        key={`editable:q10:faithful:presenter:${id}:body`}
        src={presenterBody(pose)}
        size={size}
      />
      {mouthLayers(id, mouths, pose, size)}
    </Rect>
  );
}

function SymptomCard({
  cardRef,
  circleRef,
  imageRef,
  labelRef,
  symbolRef,
  position,
  image,
  label,
  circleFill,
  kind,
}: {
  cardRef: Reference<Rect>;
  circleRef: Reference<Circle>;
  imageRef: Reference<Img>;
  labelRef: Reference<Txt>;
  symbolRef: Reference<Txt>;
  position: [number, number];
  image: string;
  label: string;
  circleFill: string;
  kind: 'fatigue' | 'breath' | 'chest';
}) {
  const symbolConfig = {
    fatigue: {
      text: '✦ 〰',
      position: [-78, -112] as [number, number],
      fontSize: 49,
      fill: '#d9a858',
    },
    breath: {
      text: '≈',
      position: [-110, -8] as [number, number],
      fontSize: 88,
      fill: '#dfa77c',
    },
    chest: {
      text: '⚡',
      position: [108, 72] as [number, number],
      fontSize: 72,
      fill: '#f0bb35',
    },
  }[kind];

  return (
    <Rect
      key={`editable:q10:faithful:symptom-card:${kind}`}
      ref={cardRef}
      position={position}
      size={[390, 430]}
    >
      <Circle
        ref={circleRef}
        position={[0, -22]}
        size={320}
        fill={circleFill}
        clip
        scale={0}
        opacity={0}
      >
        <Img
          key={`editable:q10:faithful:symptom-image:${kind}`}
          ref={imageRef}
          src={image}
          size={[480, 720]}
          position={[0, 250]}
          opacity={0}
        />
        <Txt
          ref={symbolRef}
          text={symbolConfig.text}
          position={symbolConfig.position}
          fontFamily={FONT}
          fontSize={symbolConfig.fontSize}
          fontWeight={800}
          fill={symbolConfig.fill}
          opacity={0}
        />
      </Circle>
      <Txt
        key={`editable:q10:faithful:symptom-label:${kind}`}
        ref={labelRef}
        position={[0, 172]}
        text={label}
        fontFamily={FONT}
        fontSize={42}
        fontWeight={650}
        fill={'#333333'}
        opacity={0}
      />
    </Rect>
  );
}

function RelationNode({
  ref,
  position,
  text,
  size = [300, 104],
  fill = WHITE,
}: {
  ref: Reference<Rect>;
  position: [number, number];
  text: string;
  size?: [number, number];
  fill?: string;
}) {
  return (
    <Rect
      ref={ref}
      position={position}
      size={size}
      radius={18}
      fill={fill}
      shadowColor={'rgba(20,88,132,0.16)'}
      shadowBlur={9}
      opacity={0}
      scale={0.86}
    >
      <Txt
        text={text}
        width={size[0] - 30}
        fontFamily={FONT}
        fontSize={34}
        fontWeight={800}
        fill={fill === WHITE ? '#315773' : WHITE}
        textAlign={'center'}
      />
    </Rect>
  );
}

export const productTrainingFaithfulScene = makeScene2D('product-training-faithful', function* (view) {
  addBackground(view);
  view.add(<Audio src={data.audio.file} play />);

  const meterScene = createRef<Rect>();
  const neutralScene = createRef<Rect>();
  const palmScene = createRef<Rect>();
  const symptomScene = createRef<Rect>();
  const relationScene = createRef<Rect>();
  const productScene = createRef<Rect>();

  const neutralMouths = [0, 1, 2, 3].map(() => createRef<Img>());
  const palmMouths = [0, 1, 2, 3].map(() => createRef<Img>());
  const smallMouths = [0, 1, 2, 3].map(() => createRef<Img>());
  const relationMouths = [0, 1, 2, 3].map(() => createRef<Img>());
  const presenterNeutral = createRef<Rect>();
  const presenterPalm = createRef<Rect>();
  const presenterSmall = createRef<Rect>();
  const presenterRelation = createRef<Rect>();

  const meterNeedle = createRef<Line>();
  const symptomCards = [0, 1, 2].map(() => createRef<Rect>());
  const symptomCircles = [0, 1, 2].map(() => createRef<Circle>());
  const symptomImages = [0, 1, 2].map(() => createRef<Img>());
  const symptomLabels = [0, 1, 2].map(() => createRef<Txt>());
  const symptomSymbols = [0, 1, 2].map(() => createRef<Txt>());
  const relationCenter = createRef<Rect>();
  const relationTop = createRef<Rect>();
  const relationLeft = createRef<Rect>();
  const relationRight = createRef<Rect>();
  const product = createRef<Img>();
  const productBadge = createRef<Rect>();
  const productOuterGlow = createRef<Circle>();
  const productInnerGlow = createRef<Circle>();
  const rays = PRODUCT_RAYS.map(() => createRef<Line>());

  view.add(
    <>
      <Rect ref={meterScene} size={[1920, 1080]}>
        <Txt
          key={'editable:q10:faithful:meter-title'}
          position={[-50, -315]}
          text={'心肌细胞能量水平'}
          fontFamily={FONT}
          fontSize={70}
          fontWeight={900}
          fill={WHITE}
          stroke={'#185f92'}
          lineWidth={4}
        />
        <Circle
          position={[-50, 55]}
          size={510}
          fill={'rgba(255,255,255,0.18)'}
          stroke={WHITE}
          lineWidth={22}
        />
        <Circle position={[-50, 55]} size={80} fill={ORANGE} stroke={WHITE} lineWidth={8} />
        <Line
          ref={meterNeedle}
          position={[-50, 55]}
          points={[[0, 0], [0, -195]]}
          lineWidth={18}
          stroke={ORANGE}
          endArrow
          rotation={58}
        />
        <Txt
          key={'editable:q10:faithful:meter-caption'}
          position={[-55, 345]}
          text={'缺乏 → 能量生产下降'}
          fontFamily={FONT}
          fontSize={55}
          fontWeight={850}
          fill={YELLOW}
          stroke={'#22577b'}
          lineWidth={4}
        />
      </Rect>

      <Rect ref={neutralScene} size={[1920, 1080]} opacity={0}>
        <Presenter
          id="neutral"
          containerRef={presenterNeutral}
          pose={'point'}
          position={[-25, 120]}
          height={980}
          mouths={neutralMouths}
        />
      </Rect>

      <Rect ref={palmScene} size={[1920, 1080]} opacity={0}>
        <Presenter
          id="palm"
          containerRef={presenterPalm}
          pose={'palm'}
          position={[-15, 120]}
          height={980}
          mouths={palmMouths}
        />
      </Rect>

      <Rect ref={symptomScene} size={[1920, 1080]} opacity={0}>
        <Rect
          position={[-210, -15]}
          size={[1460, 820]}
          fill={WHITE}
        >
          <Rect position={[0, -410]} size={[1460, 24]} fill={DEEP_BLUE} />
          <Rect position={[0, 410]} size={[1460, 24]} fill={DEEP_BLUE} />
          <Rect
            position={[-490, -315]}
            size={[450, 84]}
            radius={20}
            fill={'#ef5350'}
          >
            <Txt
              key={'editable:q10:faithful:symptom-badge'}
              text={'引发系列症状'}
              fontFamily={FONT}
              fontSize={53}
              fontWeight={650}
              fill={WHITE}
            />
          </Rect>
          <Txt
            key={'editable:q10:faithful:symptom-lead'}
            position={[295, -315]}
            text={'缺乏辅酶 Q10 可能引发'}
            fontFamily={FONT}
            fontSize={38}
            fontWeight={650}
            fill={'#48687a'}
          />
          <SymptomCard
            cardRef={symptomCards[0]}
            circleRef={symptomCircles[0]}
            imageRef={symptomImages[0]}
            labelRef={symptomLabels[0]}
            symbolRef={symptomSymbols[0]}
            position={[-455, 55]}
            image={data.assets.symptoms[0].file}
            label={'疲劳乏力'}
            circleFill={'#ffe6a2'}
            kind={'fatigue'}
          />
          <SymptomCard
            cardRef={symptomCards[1]}
            circleRef={symptomCircles[1]}
            imageRef={symptomImages[1]}
            labelRef={symptomLabels[1]}
            symbolRef={symptomSymbols[1]}
            position={[-15, 55]}
            image={data.assets.symptoms[1].file}
            label={'心慌气短'}
            circleFill={'#bce8bf'}
            kind={'breath'}
          />
          <SymptomCard
            cardRef={symptomCards[2]}
            circleRef={symptomCircles[2]}
            imageRef={symptomImages[2]}
            labelRef={symptomLabels[2]}
            symbolRef={symptomSymbols[2]}
            position={[425, 55]}
            image={data.assets.symptoms[2].file}
            label={'胸闷心悸'}
            circleFill={'#a9dfed'}
            kind={'chest'}
          />
        </Rect>
        <Presenter
          id="small"
          containerRef={presenterSmall}
          pose={'palm'}
          position={[720, 80]}
          height={720}
          mouths={smallMouths}
        />
      </Rect>

      <Rect ref={relationScene} size={[1920, 1080]} opacity={0}>
        <Rect position={[-210, -15]} size={[1460, 820]} fill={WHITE}>
          <Rect position={[0, -410]} size={[1460, 24]} fill={DEEP_BLUE} />
          <Rect position={[0, 410]} size={[1460, 24]} fill={DEEP_BLUE} />
        </Rect>
        {Array.from({length: 5}, (_, index) => (
          <Circle
            position={[-230, -35 - index * 25]}
            size={6}
            fill={'#a6a6a6'}
          />
        ))}
        {Array.from({length: 6}, (_, index) => (
          <Circle
            position={[-345 - index * 27, 100 + index * 24]}
            size={6}
            fill={'#a6a6a6'}
          />
        ))}
        {Array.from({length: 6}, (_, index) => (
          <Circle
            position={[-115 + index * 27, 100 + index * 24]}
            size={6}
            fill={'#a6a6a6'}
          />
        ))}
        <RelationNode
          ref={relationCenter}
          position={[-230, 35]}
          text={'辅酶 Q10'}
          size={[330, 128]}
          fill={'#ef5350'}
        />
        <RelationNode
          ref={relationTop}
          position={[-230, -175]}
          text={'慢性心力衰竭'}
          fill={'#eea03a'}
        />
        <RelationNode
          ref={relationLeft}
          position={[-525, 235]}
          text={'心肌炎'}
          fill={'#efbd43'}
        />
        <RelationNode
          ref={relationRight}
          position={[65, 235]}
          text={'心绞痛'}
          fill={'#9cc83d'}
        />
        <Presenter
          id="relation"
          containerRef={presenterRelation}
          pose={'palm'}
          position={[720, 80]}
          height={720}
          mouths={relationMouths}
        />
      </Rect>

      <Rect ref={productScene} size={[1920, 1080]} opacity={0}>
        <Circle
          ref={productOuterGlow}
          position={PRODUCT_EFFECT.center}
          size={PRODUCT_EFFECT.haloSize}
          fill={'rgba(189,239,220,0.2)'}
          shadowColor={'rgba(210,248,226,0.9)'}
          shadowBlur={110}
          opacity={0}
          scale={0.72}
        />
        <Circle
          ref={productInnerGlow}
          position={PRODUCT_EFFECT.center}
          size={560}
          fill={'rgba(255,255,224,0.22)'}
          shadowColor={'rgba(255,255,220,0.88)'}
          shadowBlur={90}
          opacity={0}
          scale={0.72}
        />
        {PRODUCT_RAYS.map((rayConfig, index) => (
          <Line
            ref={rays[index]}
            position={PRODUCT_EFFECT.center}
            points={[
              [-5, 0],
              [5, 0],
              [rayConfig.outerHalf, rayConfig.length],
              [-rayConfig.outerHalf, rayConfig.length],
            ]}
            closed
            fill={rayConfig.color}
            rotation={rayConfig.angle}
            opacity={0}
            scale={0}
          />
        ))}
        <Img
          key={'editable:q10:faithful:product'} ref={product}
          src={asset('q10-reference-approx-v1.png')}
          position={[-30, 15]}
          size={[1280, 721]}
          scale={0}
          opacity={0}
        />
        <Rect
          ref={productBadge}
          position={[-22, 336]}
          size={[320, 54]}
          radius={27}
          fill={'rgba(255,255,255,0.95)'}
          stroke={'#cf4245'}
          lineWidth={3}
          opacity={0}
        >
          <Txt
            text={'重新制作包装示意'}
            fontFamily={FONT}
            fontSize={27}
            fontWeight={750}
            fill={'#b64043'}
          />
        </Rect>
      </Rect>
    </>,
  );

  addFixedChrome(view);
  const subtitle = addSubtitle(view);

  const allMouths = [
    neutralMouths,
    palmMouths,
    smallMouths,
    relationMouths,
  ];
  const setMouth = (active: number) => {
    for (const group of allMouths) {
      group.forEach((mouth, index) => mouth().opacity(index === active ? 1 : 0));
    }
  };

  function* revealSymptom(index: number) {
    yield* all(
      symptomCircles[index]().opacity(1, 0.08),
      symptomCircles[index]().scale(1, 0.32, easeOutBack),
      symptomLabels[index]().opacity(1, 0.18),
    );
    symptomImages[index]().opacity(1);
    yield* symptomImages[index]().y(0, 0.4, easeOutCubic);
  }

  function* fatiguePerformance() {
    yield* waitFor(7.82);
    symptomSymbols[0]().opacity(0.72);
    for (let cycle = 0; cycle < 5; cycle += 1) {
      yield* all(
        symptomImages[0]().rotation(-2.8, 0.28, easeOutCubic),
        symptomImages[0]().x(-4, 0.28, easeOutCubic),
        symptomSymbols[0]().rotation(-8, 0.28, easeOutCubic),
        symptomSymbols[0]().opacity(0.35, 0.28),
      );
      yield* all(
        symptomImages[0]().rotation(2.8, 0.28, easeOutCubic),
        symptomImages[0]().x(4, 0.28, easeOutCubic),
        symptomSymbols[0]().rotation(8, 0.28, easeOutCubic),
        symptomSymbols[0]().opacity(0.9, 0.28),
      );
      yield* all(
        symptomImages[0]().rotation(0, 0.14, easeOutCubic),
        symptomImages[0]().x(0, 0.14, easeOutCubic),
      );
    }
  }

  function* breathPerformance() {
    yield* waitFor(8.72);
    for (let cycle = 0; cycle < 4; cycle += 1) {
      symptomSymbols[1]().x(-94);
      symptomSymbols[1]().scale(0.72);
      symptomSymbols[1]().opacity(0.18);
      yield* all(
        symptomImages[1]().y(-6, 0.3, easeOutCubic),
        symptomSymbols[1]().x(-126, 0.6, linear),
        symptomSymbols[1]().scale(1.18, 0.6, easeOutCubic),
        symptomSymbols[1]().opacity(0.88, 0.22),
      );
      yield* all(
        symptomImages[1]().y(4, 0.3, easeOutCubic),
        symptomSymbols[1]().opacity(0, 0.3),
      );
    }
  }

  function* chestPerformance() {
    yield* waitFor(9.62);
    for (let cycle = 0; cycle < 4; cycle += 1) {
      yield* all(
        symptomImages[2]().scale(1.025, 0.25, easeOutCubic),
        symptomImages[2]().y(4, 0.25, easeOutCubic),
        symptomSymbols[2]().opacity(0.95, 0.12),
        symptomSymbols[2]().scale(1.18, 0.25, easeOutBack),
      );
      yield* all(
        symptomImages[2]().scale(1, 0.25, easeOutCubic),
        symptomImages[2]().y(0, 0.25, easeOutCubic),
        symptomSymbols[2]().opacity(0.28, 0.25),
        symptomSymbols[2]().scale(0.86, 0.25, easeOutCubic),
      );
    }
  }

  function* visualTimeline() {
    yield* meterNeedle().rotation(104, 0.55, easeOutCubic);
    yield* meterScene().opacity(0, 0.15);
    meterScene().opacity(0);
    neutralScene().opacity(1);
    yield* waitFor(2.7);

    neutralScene().opacity(0);
    palmScene().opacity(1);
    yield* presenterPalm().scale(1.025, 0.14, easeOutBack);
    yield* waitFor(2.66);

    palmScene().opacity(0);
    symptomScene().opacity(1);
    yield* waitFor(0.9);
    yield* revealSymptom(0);
    yield* waitFor(0.18);
    yield* revealSymptom(1);
    yield* waitFor(0.18);
    yield* revealSymptom(2);
    yield* waitFor(2.1);
    for (const card of symptomCards) {
      yield* all(
        card().y(-440, 0.26, easeOutCubic),
        card().scale(0.22, 0.26, easeOutCubic),
        card().opacity(0, 0.2),
      );
    }

    symptomScene().opacity(0);
    relationScene().opacity(1);
    relationCenter().position([-790, 35]);
    relationTop().position([-230, -520]);
    relationLeft().position([-790, 235]);
    relationRight().position([540, 235]);
    yield* all(
      relationCenter().opacity(1, 0.12),
      relationCenter().scale(1, 0.3, easeOutBack),
      relationCenter().position([-230, 35], 0.3, easeOutCubic),
    );
    yield* waitFor(0.04);
    yield* all(
      relationTop().opacity(1, 0.12),
      relationTop().scale(1, 0.28, easeOutBack),
      relationTop().position([-230, -175], 0.28, easeOutCubic),
    );
    yield* waitFor(0.04);
    yield* all(
      relationLeft().opacity(1, 0.12),
      relationLeft().scale(1, 0.28, easeOutBack),
      relationLeft().position([-525, 235], 0.28, easeOutCubic),
    );
    yield* waitFor(0.04);
    yield* all(
      relationRight().opacity(1, 0.12),
      relationRight().scale(1, 0.28, easeOutBack),
      relationRight().position([65, 235], 0.28, easeOutCubic),
    );
    yield* waitFor(6.08);

    relationScene().opacity(0);
    productScene().opacity(1);
    yield* all(
      product().opacity(1, 0.12),
      product().scale(1, 0.45, easeOutBack),
    );
    yield* productBadge().opacity(1, 0.15);
    yield* waitFor(
      Math.max(0, PRODUCT_EFFECT.revealDelay - 0.45 - 0.15),
    );
    yield* all(
      productOuterGlow().opacity(0.92, 0.24),
      productOuterGlow().scale(1, 0.32, easeOutCubic),
      productInnerGlow().opacity(0.32, 0.2),
      productInnerGlow().scale(1, 0.32, easeOutCubic),
      ...rays.map((ray, index) =>
        all(
          ray().opacity(index % 2 === 0 ? 0.9 : 0.72, 0.18),
          ray().scale(
            1,
            PRODUCT_EFFECT.revealDuration,
            easeOutBack,
          ),
          ray().rotation(
            PRODUCT_RAYS[index].angle + PRODUCT_EFFECT.rotationDegrees,
            8.58,
            linear,
          ),
        ),
      ),
    );
  }

  function* mouthTimeline() {
    const pattern = [2, 3, 2, 1, 2, 0, 2, 3, 2, 1];
    const durations = [0.18, 0.21, 0.17, 0.23, 0.2, 0.19];
    let elapsed = 0;
    let index = 0;
    while (elapsed < 19.55) {
      setMouth(pattern[index % pattern.length]);
      const step = Math.min(durations[index % durations.length], 19.55 - elapsed);
      yield* waitFor(step);
      elapsed += step;
      index += 1;
    }
    setMouth(0);
    yield* waitFor(DURATION - elapsed);
  }

  yield* all(
    visualTimeline(),
    fatiguePerformance(),
    breathPerformance(),
    chestPerformance(),
    mouthTimeline(),
    runSubtitles(subtitle),
    applyEditablePatches(view, DURATION),
  );
});

export default makeProject({
  scenes: [productTrainingFaithfulScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: BLUE,
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
