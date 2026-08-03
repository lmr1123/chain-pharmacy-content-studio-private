import {Audio, Img, Rect, Txt, View2D, makeScene2D} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeOutBack,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {ReferenceMedicalTechMaster} from './components/reference-medical-tech-master';
import {presenterLayout} from './wind-heat-production-contract';
import {unifiedAudio} from './wind-heat-audio-v2';

type Cue = {start: number; end: number; text: string};
type Herb = {name: string; image: string; lines: [string, string]};

const DURATION = 41.94;
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const WHITE = '#f7faf8';
const CYAN = '#35e5e8';
const PANEL = 'rgba(24, 42, 55, 0.96)';

const TYPE = {
  pageTitle: 76,
  cardTitle: 58,
  cardBody: 42,
  dosage: 58,
  subtitle: 52,
  coreHeading: 58,
  coreBody: 48,
};

const LAYOUT = {
  title: {x: 0, y: -420},
  corePanel: {x: -325, y: 8, width: 1090, height: 510},
  corePresenter: {x: 650, y: 80, width: 770, height: 1568},
  herbCards: {x: 0, y: 38, width: 1330, height: 690, gap: 34},
  recipePresenter: {x: -660, y: 84, width: 600, height: 1394},
  recipeCards: {x: 300, y: -150, scale: 0.57},
  recipeDosage: {x: 355, y: 110},
  recipeTea: {x: 470, y: 340, width: 570, height: 380},
};

const legacyCues: Cue[] = [
  {start: 0, end: 2.274, text: '就是把身体里的风散出去'},
  {start: 2.35, end: 3.825, text: '把热清掉'},
  {start: 3.901, end: 6.049, text: '不舒服的感觉自然就缓解了'},
  {start: 6.126, end: 7.866, text: '日常生活中有这几样'},
  {start: 7.942, end: 9.768, text: '用来调理特别方便'},
  {start: 9.844, end: 10.544, text: '记好了'},
  {start: 10.621, end: 12.59, text: '一、桑叶'},
  {start: 12.666, end: 13.522, text: '能散风热'},
  {start: 13.598, end: 14.879, text: '还能滋润肺部'},
  {start: 14.955, end: 16.124, text: '缓解咳嗽'},
  {start: 16.2, end: 17.803, text: '二、菊花'},
  {start: 17.879, end: 19.448, text: '不仅能散风热'},
  {start: 19.524, end: 20.998, text: '还能清热解毒'},
  {start: 21.075, end: 22.764, text: '平时泡着喝也舒服'},
  {start: 22.84, end: 24.304, text: '三、薄荷'},
  {start: 24.381, end: 26.064, text: '散风热的效果特别快'},
  {start: 26.14, end: 27.593, text: '还能清头目'},
  {start: 27.669, end: 28.979, text: '缓解喉咙痛'},
  {start: 29.056, end: 30.704, text: '平常在家时'},
  {start: 30.78, end: 34.579, text: '用桑叶、菊花、薄荷各3—5克'},
  {start: 34.655, end: 36.385, text: '泡一杯水喝'},
  {start: 36.462, end: 38.881, text: '就是简单又管用的桑菊薄荷饮'},
  {start: 38.957, end: 40.2, text: '喝1—2天'},
  {start: 40.276, end: 41.94, text: '就能感觉到舒服不少'},
];
const treatmentAudio = unifiedAudio('treatment');
const cues: Cue[] = treatmentAudio.cues;

const herbs: Herb[] = [
  {
    name: '桑叶',
    image: 'mulberry-leaf-v1.png',
    lines: ['散风热、润肺', '缓解咳嗽'],
  },
  {
    name: '菊花',
    image: 'chrysanthemum-v1.png',
    lines: ['散风热、清热解毒', '泡饮清润舒适'],
  },
  {
    name: '薄荷',
    image: 'mint-v1.png',
    lines: ['疏散风热、清头目', '缓解咽喉不适'],
  },
];

const presenterAsset = (name: string) => `/wind-heat-presenter-v2/${name}`;
const treatment = (name: string) => `/treatment-assets/${name}`;

function addTitle(parent: View2D | Rect, text: string, id: string) {
  parent.add(
    <Rect
      key={`editable:treatment:title:${id}:root`}
      position={[LAYOUT.title.x, LAYOUT.title.y]}
      size={[960, 100]}
    >
      <Rect position={[-395, 12]} size={20} radius={10} fill={'#fff0a8'} />
      <Rect position={[-365, -15]} size={30} radius={15} fill={'#bd386f'} />
      <Txt
        key={`editable:treatment:title:${id}:text`}
        text={text}
        fontFamily={FONT}
        fontSize={TYPE.pageTitle}
        fontWeight={650}
        fill={WHITE}
      />
      <Rect
        position={[390, -17]}
        size={[92, 40]}
        radius={20}
        rotation={-36}
        fill={'#f3f6f4'}
        stroke={'#d6e0e4'}
        lineWidth={2}
      >
        <Rect position={[26, 0]} size={36} radius={18} fill={'#77a9da'} />
      </Rect>
      <Rect
        position={[390, 30]}
        size={[92, 40]}
        radius={20}
        fill={'#f3f6f4'}
        stroke={'#d6e0e4'}
        lineWidth={2}
      >
        <Rect position={[26, 0]} size={36} radius={18} fill={'#df6c6c'} />
      </Rect>
    </Rect>,
  );
}

function addSubtitle(view: View2D) {
  const ref = createRef<Txt>();
  view.add(
    <Txt
      key={'editable:treatment:subtitle'}
      ref={ref}
      position={[0, 435]}
      width={1580}
      textAlign={'center'}
      fontFamily={FONT}
      fontSize={TYPE.subtitle}
      fontWeight={800}
      fill={'#ffffff'}
      stroke={'rgba(0,0,0,0.98)'}
      lineWidth={2}
      shadowColor={'rgba(0,0,0,0.9)'}
      shadowBlur={6}
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
    yield* ref().opacity(1, 0.04);
    yield* waitFor(Math.max(0, cue.end - cue.start - 0.04));
    ref().opacity(0);
    cursor = cue.end;
  }
}

function mouthLayer(
  refs: Reference<Img>[],
  presenterSize: readonly [number, number],
  anchor: readonly [number, number],
) {
  const [width, height] = presenterSize;
  const position: [number, number] = [
    (anchor[0] - 0.5) * width,
    (anchor[1] - 0.5) * height,
  ];
  return ['closed', 'small', 'o', 'wide'].map((name, index) => (
    <Img
      ref={refs[index]}
      src={presenterAsset(
        name === 'closed'
          ? 'mouth-closed-vector.svg'
          : `mouth-${name}-vector.svg`,
      )}
      position={position}
      size={
        index === 0
          ? [width * 0.115, width * 0.072]
          : [width * 0.124, width * 0.083]
      }
      opacity={index === 0 ? 1 : 0}
    />
  ));
}

function HerbCards({
  refs,
  compact = false,
  layerPrefix = 'editable:treatment:herb',
}: {
  refs: Reference<Rect>[];
  compact?: boolean;
  layerPrefix?: string;
}) {
  const cardWidth = 420;
  const cardHeight = compact ? 500 : 670;
  const headingY = compact ? -195 : -280;
  const imageY = compact ? 22 : -42;
  return (
    <>
      {herbs.map((herb, index) => (
        <Rect
          key={`${layerPrefix}:${index}:root`}
          ref={refs[index]}
          position={[(index - 1) * (cardWidth + LAYOUT.herbCards.gap), 0]}
          size={[cardWidth, cardHeight]}
          fill={PANEL}
          stroke={'#58acb5'}
          lineWidth={5}
          radius={8}
          shadowColor={'rgba(47,232,234,0.16)'}
          shadowBlur={16}
          scale={compact ? 1 : 0.92}
        >
          <Rect
            position={[0, headingY]}
            size={[210, 74]}
            radius={14}
            fill={'#149da5'}
          >
            <Txt
              key={`${layerPrefix}:${index}:name`}
              text={herb.name}
              fontFamily={FONT}
              fontSize={TYPE.cardTitle}
              fontWeight={650}
              fill={WHITE}
            />
          </Rect>
          <Img
            key={`${layerPrefix}:${index}:asset`}
            src={treatment(herb.image)}
            position={[0, imageY]}
            size={[358, 360]}
            radius={12}
          />
          {!compact && (
            <>
              <Txt
                key={`${layerPrefix}:${index}:line:0`}
                position={[0, 198]}
                width={360}
                text={herb.lines[0]}
                fontFamily={FONT}
                fontSize={TYPE.cardBody}
                fontWeight={580}
                fill={CYAN}
              />
              <Txt
                key={`${layerPrefix}:${index}:line:1`}
                position={[0, 260]}
                width={360}
                text={herb.lines[1]}
                fontFamily={FONT}
                fontSize={TYPE.cardBody}
                fontWeight={580}
                fill={WHITE}
              />
            </>
          )}
        </Rect>
      ))}
    </>
  );
}

export const referenceTreatmentScene = makeScene2D('reference-treatment', function* (view) {
  view.add(
    <Audio
      src={treatmentAudio.audio}
      play
      volume={1}
    />,
  );
  view.add(
    <>
      <ReferenceMedicalTechMaster
        activeChapter={'调理建议'}
        layerPrefix={'treatment'}
      />
    </>,
  );

  const coreScene = createRef<Rect>();
  const herbsScene = createRef<Rect>();
  const recipeScene = createRef<Rect>();
  const largeCards = herbs.map(() => createRef<Rect>());
  const smallCards = herbs.map(() => createRef<Rect>());
  const coreMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const recipeMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const tea = createRef<Rect>();
  const drinkTag = createRef<Rect>();
  const corePresenterLayout = presenterLayout('megaphone', 'sideRight');
  const recipePresenterLayout = presenterLayout('point', 'sideLeft');

  view.add(
    <>
      <Rect
        key={'editable:treatment:group:core'}
        ref={coreScene}
        size={[1920, 1080]}
      >
        <Rect size={[1920, 1080]} />
        <Rect
          position={[
            LAYOUT.corePanel.x,
            LAYOUT.corePanel.y,
          ]}
          size={[
            LAYOUT.corePanel.width,
            LAYOUT.corePanel.height,
          ]}
          fill={PANEL}
          stroke={'#55adb6'}
          lineWidth={5}
          shadowColor={'rgba(47,232,234,0.2)'}
          shadowBlur={18}
        >
          <Rect
            position={[-330, -170]}
            size={[330, 92]}
            radius={12}
            fill={'#159ca4'}
          >
            <Txt
              key={'editable:treatment:core:title'}
              text={'疏风清热'}
              fontFamily={FONT}
              fontSize={TYPE.coreHeading}
              fontWeight={650}
              fill={WHITE}
            />
          </Rect>
          <Rect
            position={[-435, 15]}
            size={28}
            radius={14}
            stroke={CYAN}
            lineWidth={5}
          />
          <Txt
            key={'editable:treatment:core:body:0'}
            position={[-5, 15]}
            width={820}
            text={'把身体里的风散出去，把热清掉'}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={TYPE.coreBody}
            fontWeight={560}
            fill={CYAN}
          />
          <Rect
            position={[-435, 125]}
            size={28}
            radius={14}
            stroke={CYAN}
            lineWidth={5}
          />
          <Txt
            key={'editable:treatment:core:body:1'}
            position={[-5, 125]}
            width={820}
            text={'让发热、咽痛、咳嗽等不适逐渐缓解'}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={TYPE.coreBody}
            fontWeight={560}
            fill={CYAN}
          />
        </Rect>
        <Rect
          key={'editable:treatment:presenter:core-megaphone'}
          position={corePresenterLayout.position}
          size={corePresenterLayout.size}
        >
          <Img
            key={'editable:treatment:presenter:core-megaphone-asset'}
            src={corePresenterLayout.asset}
            size={corePresenterLayout.size}
          />
          {mouthLayer(
            coreMouths,
            corePresenterLayout.size,
            corePresenterLayout.mouthAnchor,
          )}
        </Rect>
      </Rect>

      <Rect
        key={'editable:treatment:group:herb-cards'}
        ref={herbsScene}
        size={[1920, 1080]}
        opacity={0}
      >
        <Rect size={[1920, 1080]} />
        <Rect
          position={[
            LAYOUT.herbCards.x,
            LAYOUT.herbCards.y,
          ]}
          size={[
            LAYOUT.herbCards.width,
            LAYOUT.herbCards.height,
          ]}
        >
          <HerbCards
            refs={largeCards}
            layerPrefix={'editable:treatment:herb-large'}
          />
        </Rect>
      </Rect>

      <Rect
        key={'editable:treatment:group:recipe'}
        ref={recipeScene}
        size={[1920, 1080]}
        opacity={0}
      >
        <Rect size={[1920, 1080]} />
        <Rect
          key={'editable:treatment:presenter:recipe-point'}
          position={recipePresenterLayout.position}
          size={recipePresenterLayout.size}
        >
          <Img
            key={'editable:treatment:presenter:recipe-point-asset'}
            src={recipePresenterLayout.asset}
            size={recipePresenterLayout.size}
          />
          {mouthLayer(
            recipeMouths,
            recipePresenterLayout.size,
            recipePresenterLayout.mouthAnchor,
          )}
        </Rect>
        <Rect
          position={[
            LAYOUT.recipeCards.x,
            LAYOUT.recipeCards.y,
          ]}
          scale={LAYOUT.recipeCards.scale}
        >
          <HerbCards
            refs={smallCards}
            compact
            layerPrefix={'editable:treatment:herb-recipe'}
          />
        </Rect>
        <Rect
          position={[
            LAYOUT.recipeDosage.x,
            LAYOUT.recipeDosage.y,
          ]}
          size={[620, 108]}
          radius={18}
          fill={'rgba(18, 157, 165, 0.95)'}
          stroke={'#77e6e8'}
          lineWidth={4}
        >
          <Txt
            key={'editable:treatment:recipe:dosage'}
            text={'桑叶 · 菊花 · 薄荷  各3—5克'}
            fontFamily={FONT}
            fontSize={TYPE.dosage}
            fontWeight={700}
            fill={WHITE}
          />
        </Rect>
        <Rect
          key={'editable:treatment:asset:tea'}
          ref={tea}
          position={[
            LAYOUT.recipeTea.x,
            LAYOUT.recipeTea.y + 60,
          ]}
          opacity={0}
          scale={0.84}
        >
          <Img
            key={'editable:treatment:recipe:tea-asset'}
            src={treatment('sangju-mint-tea-v1.png')}
            size={[
              LAYOUT.recipeTea.width,
              LAYOUT.recipeTea.height,
            ]}
          />
          <Txt
            key={'editable:treatment:recipe:drink-tag-text'}
            position={[-45, -215]}
            text={'〰'}
            fontFamily={FONT}
            fontSize={92}
            fill={'rgba(220,255,255,0.75)'}
            rotation={-80}
          />
          <Txt
            position={[55, -225]}
            text={'〰'}
            fontFamily={FONT}
            fontSize={78}
            fill={'rgba(220,255,255,0.56)'}
            rotation={-80}
          />
        </Rect>
        <Rect
          key={'editable:treatment:group:drink-tag'}
          ref={drinkTag}
          position={[600, 210]}
          size={[300, 100]}
          radius={50}
          fill={'#fff1a7'}
          stroke={'#d8bf67'}
          lineWidth={4}
          opacity={0}
          scale={0.7}
        >
          <Txt
            text={'喝1—2天'}
            fontFamily={FONT}
            fontSize={56}
            fontWeight={800}
            fill={'#253743'}
          />
        </Rect>
      </Rect>
    </>,
  );

  addTitle(coreScene(), '调理核心', 'core');
  addTitle(herbsScene(), '常用食材', 'herbs');
  addTitle(recipeScene(), '常用食材', 'recipe');
  const subtitle = addSubtitle(view);
  const allMouths = [...coreMouths, ...recipeMouths];
  const setMouth = (active: number) => {
    for (const ref of allMouths) ref().opacity(0);
    for (const refs of [coreMouths, recipeMouths]) refs[active]().opacity(1);
  };

  function* visualTimeline() {
    yield* waitFor(6.4);
    coreScene().opacity(0);
    herbsScene().opacity(1);
    yield* all(
      ...largeCards.map((card, index) =>
        card().scale(1, 0.22 + index * 0.05, easeOutBack),
      ),
    );
    yield* waitFor(4.78);
    largeCards[0]().shadowColor('rgba(47,232,234,0.75)');
    largeCards[0]().shadowBlur(34);
    largeCards[0]().lineWidth(9);
    yield* waitFor(5.34);
    largeCards[0]().shadowColor('rgba(47,232,234,0.16)');
    largeCards[0]().shadowBlur(16);
    largeCards[0]().lineWidth(5);
    largeCards[1]().shadowColor('rgba(47,232,234,0.75)');
    largeCards[1]().shadowBlur(34);
    largeCards[1]().lineWidth(9);
    yield* waitFor(6.42);
    largeCards[1]().shadowColor('rgba(47,232,234,0.16)');
    largeCards[1]().shadowBlur(16);
    largeCards[1]().lineWidth(5);
    largeCards[2]().shadowColor('rgba(47,232,234,0.75)');
    largeCards[2]().shadowBlur(34);
    largeCards[2]().lineWidth(9);
    yield* waitFor(6.06);
    herbsScene().opacity(0);
    recipeScene().opacity(1);
    yield* waitFor(4.9);
    yield* all(
      tea().opacity(1, 0.22),
      tea().position(
        [LAYOUT.recipeTea.x, LAYOUT.recipeTea.y],
        0.38,
        easeOutCubic,
      ),
      tea().scale(1, 0.38, easeOutBack),
    );
    yield* waitFor(3.96);
    yield* all(
      drinkTag().opacity(1, 0.18),
      drinkTag().scale(1, 0.3, easeOutBack),
    );
    yield* waitFor(3.08);
  }

  function* mouthTimeline() {
    const pattern = [1, 3, 1, 2, 0, 1, 3, 1];
    let elapsed = 0;
    let index = 0;
    while (elapsed < DURATION) {
      const speaking = elapsed < 6.4 || elapsed >= 29.32;
      setMouth(speaking ? pattern[index % pattern.length] : 0);
      const step = Math.min(0.14, DURATION - elapsed);
      yield* waitFor(step);
      elapsed += step;
      index += 1;
    }
    setMouth(0);
  }

  yield* all(
    visualTimeline(),
    mouthTimeline(),
    runSubtitles(subtitle),
    applyEditablePatches(view, DURATION),
  );
});

export default makeProject({
  scenes: [referenceTreatmentScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#020a15',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
