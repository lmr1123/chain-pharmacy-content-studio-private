import {Audio, Img, Rect, Txt, View2D, makeScene2D} from '@revideo/2d';
import {
  Reference,
  all,
  chain,
  createRef,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {ReferenceMedicalTechMaster} from './components/reference-medical-tech-master';
import {presenterLayout} from './wind-heat-production-contract';
import {unifiedAudio} from './wind-heat-audio-v2';
import data from '../health-training-symptoms.json';
import {
  audioFile,
  cuesOf,
  diseaseName,
  playbackDuration,
  screenOf,
} from './health-training-content';

type Cue = {
  start: number;
  end: number;
  text: string;
};

type SymptomItem = {
  image: string;
  label: string;
};

type SymptomGroup = {
  number: string;
  title: string;
  summaryLines: [string, string];
  items: SymptomItem[];
};

const DISEASE = diseaseName(data as any);
const SCREEN = screenOf(data as any);
const DURATION = playbackDuration(data as any, 27.5);
const CANONICAL_DURATION = 790 / 30;
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const WHITE = '#f6f7f5';
const CYAN = '#2fe8ea';
const PANEL = 'rgba(29, 42, 54, 0.96)';

const TYPOGRAPHY = {
  pageTitle: 72,
  cardHeading: 52,
  cardBody: 44,
  imageLabel: 38,
  subtitle: 52,
  treatmentTitle: 76,
  treatmentCore: 58,
  treatmentBody: 50,
};

const DEFAULT_LAYOUT = {
  title: {x: 0, y: -418, width: 1050},
  cards: {
    x: 0,
    y: 20,
    width: 1280,
    height: 730,
    rowHeight: 230,
    rowGap: 22,
  },
  introPresenter: {x: 0, y: 275, width: 650, height: 1510},
  splitPresenter: {x: -690, y: 96, width: 600, height: 1394},
  splitCards: {x: 335, y: 45, scale: 0.78},
  treatmentPresenter: {x: 660, y: 80, width: 760, height: 1548},
  treatmentPanel: {x: -350, y: 5, width: 1080, height: 500},
};

const MOUTH_RIG = {
  point: {anchor: [0.526, 0.415] as [number, number]},
  megaphone: {anchor: [0.526, 0.421] as [number, number]},
};

const symptomsAudio = unifiedAudio('symptoms');
const cues: Cue[] = cuesOf(data as any, symptomsAudio.cues);
const SYMPTOMS_AUDIO = audioFile(data as any, symptomsAudio.audio);
const CHAPTER = SCREEN.chapter_symptoms || '典型症状';
const SYMPTOMS_TITLE =
  SCREEN.symptoms_title || `${DISEASE}的典型症状`;
const CORE_HEADING = SCREEN.core_heading || '调理核心';
const CORE_TREATMENT = SCREEN.core_treatment || '疏风清热';
const CORE_BODY_1 = SCREEN.core_body_1 || '围绕风邪与热邪进行调理';
const CORE_BODY_2 = SCREEN.core_body_2 || '缓解发热、口渴、咽痛、';
const CORE_BODY_3 = SCREEN.core_body_3 || '痰黄等表现';

const defaultGroups: SymptomGroup[] = [
  {
    number: '①',
    title: '全身症状',
    summaryLines: ['发热、口渴、嘴巴干', '心里烦躁'],
    items: [
      {image: 'fever.png', label: '发热'},
      {image: 'thirst.png', label: '口渴'},
      {image: 'dry-mouth.png', label: '嘴巴干'},
      {image: 'irritable.png', label: '心里烦躁'},
    ],
  },
  {
    number: '②',
    title: '呼吸道症状',
    summaryLines: ['喉咙肿痛、咳嗽', '痰黄、黄稠鼻涕'],
    items: [
      {image: 'sore-throat.png', label: '喉咙肿痛'},
      {image: 'cough.png', label: '咳嗽'},
      {image: 'yellow-phlegm.png', label: '痰黄'},
      {image: 'yellow-nasal.png', label: '鼻涕黄稠'},
    ],
  },
  {
    number: '③',
    title: '其他症状',
    summaryLines: ['舌头偏红、舌苔发黄', '大便干结'],
    items: [
      {image: 'red-tongue.png', label: '舌头红'},
      {image: 'yellow-coat.png', label: '舌苔黄'},
      {image: 'dry-stool.png', label: '大便干结'},
    ],
  },
];
const groups: SymptomGroup[] = (
  SCREEN.symptom_groups && SCREEN.symptom_groups.length
    ? SCREEN.symptom_groups
    : defaultGroups
) as SymptomGroup[];

const presenterAsset = (name: string) => `/wind-heat-presenter-v2/${name}`;
const symptom = (name: string) => `/production-symptoms/${name}`;

function addSubtitle(view: View2D) {
  const ref = createRef<Txt>();
  view.add(
    <Txt
      key={'editable:symptoms:subtitle'}
      ref={ref}
      position={[0, 433]}
      width={1540}
      textAlign={'center'}
      fontFamily={FONT}
      fontSize={TYPOGRAPHY.subtitle}
      fontWeight={800}
      fill={'#ffffff'}
      stroke={'rgba(0,0,0,0.96)'}
      lineWidth={2}
      shadowColor={'rgba(0,0,0,0.9)'}
      shadowBlur={5}
      opacity={0}
    />,
  );
  return ref;
}

function* runSubtitles(ref: Reference<Txt>, duration = DURATION) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start >= duration) break;
    const cueEnd = Math.min(duration, cue.end);
    if (cue.start > cursor) {
      ref().opacity(0);
      yield* waitFor(cue.start - cursor);
    }
    ref().text(cue.text);
    const fadeDuration = Math.min(0.05, cueEnd - cue.start);
    yield* ref().opacity(1, fadeDuration);
    yield* waitFor(Math.max(0, cueEnd - cue.start - fadeDuration));
    ref().opacity(0);
    cursor = cueEnd;
  }
  yield* waitFor(Math.max(0, duration - cursor));
}

function mouthLayer(
  refs: Reference<Img>[],
  presenterSize: readonly [number, number],
  anchor: readonly [number, number],
) {
  const [presenterWidth, presenterHeight] = presenterSize;
  const position: [number, number] = [
    (anchor[0] - 0.5) * presenterWidth,
    (anchor[1] - 0.5) * presenterHeight,
  ];
  const closedWidth = presenterWidth * 0.115;
  const openWidth = presenterWidth * 0.124;
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
          ? [closedWidth, closedWidth * 0.625]
          : [openWidth, openWidth * 0.673]
      }
      opacity={index === 0 ? 1 : 0}
    />
  ));
}

function* referenceSymptoms(view: View2D, duration = DURATION) {
  const layout = DEFAULT_LAYOUT;
  const introPresenterLayout = presenterLayout('point', 'heroCenter');
  const pointPresenterLayout = presenterLayout('point', 'sideLeft');
  const treatmentPresenterLayout = presenterLayout('megaphone', 'sideRight');

  view.add(
    <Audio
      src={SYMPTOMS_AUDIO}
      play
      volume={1}
    />,
  );

  const intro = createRef<Rect>();
  const cardsScene = createRef<Rect>();
  const cards = createRef<Rect>();
  const rows = groups.map(() => createRef<Rect>());
  const pointPresenter = createRef<Rect>();
  const treatment = createRef<Rect>();
  const introMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const pointMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const treatmentMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );

  view.add(
    <>
      <ReferenceMedicalTechMaster
        activeChapter={CHAPTER}
        layerPrefix={'symptoms'}
      />

      <Rect ref={intro} size={[1920, 1080]}>
        <Rect
          position={[0, 360]}
          size={[820, 820]}
          scale={[1, 0.2]}
          radius={410}
          stroke={'rgba(71, 194, 203, 0.3)'}
          lineWidth={4}
        />
        <Rect
          key={'editable:symptoms:group:intro-presenter'}
          position={introPresenterLayout.position}
          size={introPresenterLayout.size}
        >
          <Img
            key={'editable:symptoms:presenter:intro-point'}
            src={introPresenterLayout.asset}
            size={introPresenterLayout.size}
          />
          {mouthLayer(
            introMouths,
            introPresenterLayout.size,
            introPresenterLayout.mouthAnchor,
          )}
        </Rect>
      </Rect>

      <Rect ref={cardsScene} size={[1920, 1080]} opacity={0}>
        <Rect
          position={[layout.title.x, layout.title.y]}
          size={[layout.title.width, 92]}
        >
          <Rect
            position={[-420, -10]}
            size={18}
            radius={9}
            fill={'#fff2a6'}
          />
          <Rect
            position={[-392, -25]}
            size={24}
            radius={12}
            fill={'#bd386f'}
          />
          <Txt
            key={'editable:symptoms:title'}
            text={SYMPTOMS_TITLE}
            fontFamily={FONT}
            fontSize={TYPOGRAPHY.pageTitle}
            fontWeight={620}
            fill={WHITE}
          />
          <Rect
            position={[420, -13]}
            size={[82, 34]}
            radius={17}
            rotation={-36}
            fill={'#f4f7f5'}
            stroke={'#d7e0e4'}
            lineWidth={2}
          >
            <Rect
              position={[23, 0]}
              size={30}
              radius={15}
              fill={'#78a9d9'}
            />
          </Rect>
          <Rect
            position={[420, 24]}
            size={[82, 34]}
            radius={17}
            fill={'#f4f7f5'}
            stroke={'#d7e0e4'}
            lineWidth={2}
          >
            <Rect
              position={[23, 0]}
              size={30}
              radius={15}
              fill={'#df6b6b'}
            />
          </Rect>
        </Rect>

        <Rect
          key={'editable:symptoms:group:symptom-cards'}
          ref={cards}
          position={[layout.cards.x, layout.cards.y]}
          size={[layout.cards.width, layout.cards.height]}
        >
          {groups.map((group, groupIndex) => {
            const y =
              (groupIndex - 1) *
              (layout.cards.rowHeight + layout.cards.rowGap);
            const itemStart =
              group.items.length === 4 ? 650 : 710;
            const itemGap =
              group.items.length === 4 ? 172 : 195;
            return (
              <Rect
                key={`editable:symptoms:group:${groupIndex}:root`}
                ref={rows[groupIndex]}
                position={[0, y]}
                size={[layout.cards.width, layout.cards.rowHeight]}
                fill={PANEL}
                stroke={'#55aeb6'}
                lineWidth={4}
                opacity={0}
                scale={0.92}
                shadowColor={'rgba(49,225,225,0.18)'}
                shadowBlur={14}
              >
                <Rect
                  position={[-637, 0]}
                  size={[36, 150]}
                  fill={'#4ba4ad'}
                />
                <Txt
                  key={`editable:symptoms:group:${groupIndex}:heading`}
                  position={[-365, -60]}
                  width={480}
                  text={`${group.number} ${group.title}：`}
                  textAlign={'left'}
                  fontFamily={FONT}
                  fontSize={TYPOGRAPHY.cardHeading}
                  fontWeight={520}
                  fill={WHITE}
                />
                {group.summaryLines.map((line, lineIndex) => (
                  <Txt
                    key={`editable:symptoms:group:${groupIndex}:summary:${lineIndex}`}
                    position={[-365, 22 + lineIndex * 56]}
                    width={520}
                    text={line}
                    textAlign={'left'}
                    fontFamily={FONT}
                    fontSize={TYPOGRAPHY.cardBody}
                    fontWeight={520}
                    fill={CYAN}
                  />
                ))}
                {group.items.map((item, itemIndex) => (
                  <Rect
                    key={`editable:symptoms:item:${groupIndex}:${itemIndex}:root`}
                    position={[
                      -layout.cards.width / 2 +
                        itemStart +
                        itemIndex * itemGap,
                      0,
                    ]}
                    size={[164, 210]}
                  >
                    <Img
                      key={`editable:symptoms:asset:${group.number}-${itemIndex}`}
                      src={symptom(item.image)}
                      position={[0, -17]}
                      size={[164, 166]}
                      radius={8}
                    />
                    <Txt
                      key={`editable:symptoms:item:${groupIndex}:${itemIndex}:label`}
                      position={[0, 89]}
                      width={184}
                      text={item.label}
                      fontFamily={FONT}
                      fontSize={TYPOGRAPHY.imageLabel}
                      fontWeight={540}
                      fill={WHITE}
                    />
                  </Rect>
                ))}
              </Rect>
            );
          })}
        </Rect>

        <Rect
          key={'editable:symptoms:group:point-presenter'}
          ref={pointPresenter}
          position={pointPresenterLayout.position}
          size={pointPresenterLayout.size}
          opacity={0}
        >
          <Rect
            position={[0, 330]}
            size={[480, 480]}
            scale={[1, 0.22]}
            radius={240}
            stroke={'rgba(71, 194, 203, 0.3)'}
            lineWidth={3}
          />
          <Img
            key={'editable:symptoms:presenter:side-point'}
            src={pointPresenterLayout.asset}
            size={pointPresenterLayout.size}
          />
          {mouthLayer(
            pointMouths,
            pointPresenterLayout.size,
            pointPresenterLayout.mouthAnchor,
          )}
        </Rect>
      </Rect>

      <Rect
        key={'editable:symptoms:group:treatment-transition'}
        ref={treatment}
        size={[1920, 1080]}
        opacity={0}
      >
        <Rect position={[-350, -415]} size={[760, 100]}>
          <Rect
            position={[-330, 14]}
            size={22}
            radius={11}
            fill={'#fff2a6'}
          />
          <Rect
            position={[-298, -9]}
            size={30}
            radius={15}
            fill={'#bd386f'}
          />
          <Txt
            key={'editable:symptoms:treatment:title'}
            text={CORE_HEADING}
            fontFamily={FONT}
            fontSize={TYPOGRAPHY.treatmentTitle}
            fontWeight={620}
            fill={WHITE}
          />
          <Rect
            position={[315, -15]}
            size={[90, 38]}
            radius={19}
            rotation={-36}
            fill={'#f4f7f5'}
            stroke={'#d7e0e4'}
            lineWidth={2}
          >
            <Rect
              position={[25, 0]}
              size={34}
              radius={17}
              fill={'#78a9d9'}
            />
          </Rect>
          <Rect
            position={[315, 28]}
            size={[90, 38]}
            radius={19}
            fill={'#f4f7f5'}
            stroke={'#d7e0e4'}
            lineWidth={2}
          >
            <Rect
              position={[25, 0]}
              size={34}
              radius={17}
              fill={'#df6b6b'}
            />
          </Rect>
        </Rect>
        <Rect
          position={[
            layout.treatmentPanel.x,
            layout.treatmentPanel.y,
          ]}
          size={[
            layout.treatmentPanel.width,
            layout.treatmentPanel.height,
          ]}
          fill={'rgba(23, 39, 52, 0.95)'}
          stroke={'#53adb6'}
          lineWidth={4}
          shadowColor={'rgba(47,232,234,0.2)'}
          shadowBlur={18}
        >
          <Rect
            position={[-330, -165]}
            size={[330, 92]}
            radius={12}
            fill={'#159ca4'}
          >
            <Txt
              key={'editable:symptoms:treatment:core'}
              text={CORE_TREATMENT}
              fontFamily={FONT}
              fontSize={TYPOGRAPHY.treatmentCore}
              fontWeight={620}
              fill={'#f2ffff'}
            />
          </Rect>
          <Rect
            position={[-425, 30]}
            size={28}
            radius={14}
            stroke={CYAN}
            lineWidth={5}
          />
          <Txt
            key={'editable:symptoms:treatment:body:0'}
            position={[-5, 30]}
            width={800}
            text={CORE_BODY_1}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={TYPOGRAPHY.treatmentBody}
            fill={CYAN}
          />
          <Rect
            position={[-425, 127]}
            size={28}
            radius={14}
            stroke={CYAN}
            lineWidth={5}
          />
          <Txt
            key={'editable:symptoms:treatment:body:1'}
            position={[-5, 112]}
            width={800}
            text={CORE_BODY_2}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={TYPOGRAPHY.treatmentBody}
            fill={CYAN}
          />
          <Txt
            key={'editable:symptoms:treatment:body:2'}
            position={[-5, 180]}
            width={800}
            text={CORE_BODY_3}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={TYPOGRAPHY.treatmentBody}
            fill={CYAN}
          />
        </Rect>
        <Rect
          key={'editable:symptoms:presenter:treatment-megaphone'}
          position={treatmentPresenterLayout.position}
          size={treatmentPresenterLayout.size}
        >
          <Img
            key={'editable:symptoms:presenter:treatment-megaphone-asset'}
            src={treatmentPresenterLayout.asset}
            size={treatmentPresenterLayout.size}
          />
          {mouthLayer(
            treatmentMouths,
            treatmentPresenterLayout.size,
            treatmentPresenterLayout.mouthAnchor,
          )}
        </Rect>
      </Rect>
    </>,
  );

  const subtitle = addSubtitle(view);
  const allMouths = [...introMouths, ...pointMouths, ...treatmentMouths];
  const setMouth = (active: number) => {
    for (const ref of allMouths) {
      ref().opacity(0);
    }
    for (const mouths of [introMouths, pointMouths, treatmentMouths]) {
      mouths[active]().opacity(1);
    }
  };

  function* visualTimeline() {
    yield* waitFor(4.18);
    yield* all(intro().opacity(0, 0.22), cardsScene().opacity(1, 0.22));
    yield* chain(
      ...rows.map((row) =>
        all(
          row().opacity(1, 0.18),
          row().scale(1, 0.24, easeOutCubic),
        ),
      ),
    );

    rows[0]().shadowColor('rgba(47,232,234,0.62)');
    rows[0]().shadowBlur(26);
    yield* waitFor(3.86);
    rows[0]().shadowColor('rgba(49,225,225,0.18)');
    rows[0]().shadowBlur(14);
    rows[1]().shadowColor('rgba(47,232,234,0.62)');
    rows[1]().shadowBlur(26);

    yield* waitFor(4.92);
    rows[1]().shadowColor('rgba(49,225,225,0.18)');
    rows[1]().shadowBlur(14);
    rows[2]().shadowColor('rgba(47,232,234,0.62)');
    rows[2]().shadowBlur(26);

    yield* waitFor(4.56);
    rows[2]().shadowColor('rgba(49,225,225,0.18)');
    rows[2]().shadowBlur(14);

    yield* waitFor(1.42);
    pointPresenter().opacity(1);
    cards().position([layout.splitCards.x, layout.splitCards.y]);
    cards().scale(layout.splitCards.scale);

    yield* waitFor(2.12);
    cardsScene().opacity(0);
    treatment().opacity(1);

    yield* waitFor(Math.max(0, Math.min(5.28, duration - 22)));
  }

  function* mouthTimeline() {
    let elapsed = 0;
    let index = 0;
    const pattern = [1, 3, 1, 2, 0, 1, 3, 1];
    while (elapsed < Math.min(26.1, duration)) {
      setMouth(pattern[index % pattern.length]);
      const step = Math.min(0.14, Math.min(26.1, duration) - elapsed);
      yield* waitFor(step);
      elapsed += step;
      index += 1;
    }
    setMouth(0);
    yield* waitFor(Math.max(0, duration - elapsed));
  }

  yield* all(
    visualTimeline(),
    mouthTimeline(),
    runSubtitles(subtitle, duration),
    applyEditablePatches(view, duration),
  );
}

export const referenceSymptomsScene = makeScene2D(
  'reference-typical-symptoms',
  function* (view) {
    yield* referenceSymptoms(view);
  },
);

export const referenceSymptomsCanonicalScene = makeScene2D(
  'reference-typical-symptoms-canonical',
  function* (view) {
    yield* referenceSymptoms(view, CANONICAL_DURATION);
  },
);

export default makeProject({
  scenes: [referenceSymptomsScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#020a15',
    },
    rendering: {
      fps: 30,
    },
    preview: {
      fps: 30,
    },
  },
});
