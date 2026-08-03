import {Audio, Img, Rect, Txt, View2D, makeScene2D} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeOutBack,
  makeProject,
  waitFor,
} from '@revideo/core';
import {
  ElectricCurrentOverlay,
  createElectricCurrentRefs,
  runElectricCurrent,
  traceRoundedBorder,
} from './components/premium-medical-effects';
import {
  AdviceRow,
  MedicationCard,
} from './components/reference-courseware-cards';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {ReferenceMedicalTechMaster} from './components/reference-medical-tech-master';
import {presenterLayout} from './wind-heat-production-contract';
import {unifiedAudio} from './wind-heat-audio-v2';
import data from '../health-training-medication.json';
import {
  audioFile,
  cuesOf,
  playbackDuration,
  screenOf,
} from './health-training-content';

type Cue = {start: number; end: number; text: string};
type Advice = {
  title: string;
  body: string;
  image: string;
  transparent: boolean;
};

const SCREEN = screenOf(data as any);
const DURATION = playbackDuration(data as any, 41.1);
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const WHITE = '#f7faf8';
const CYAN = '#35e5e8';
const CHAPTER = SCREEN.chapter_medication || '调理建议';
const MEDICATION_NAMES = SCREEN.medication_names || [
  '银翘解毒颗粒',
  '连花清瘟胶囊',
];

const TYPE = {
  pageTitle: 76,
  medicationTitle: 42,
  packageNote: 25,
  adviceTitle: 42,
  adviceBody: 34,
  subtitle: 52,
};

// Centralized values map directly to future drag handles and numeric controls.
const LAYOUT = {
  title: {x: 0, y: -420},
  medicationPresenter: {x: -650, y: 82, width: 600, height: 1394},
  medicationCards: {x: 375, y: 42, gap: 450},
  reminderPresenter: {x: 0, y: 278, width: 850, height: 1757},
  adviceList: {x: 0, y: 45, width: 1400, rowHeight: 148, rowGap: 18},
};

const medicationAudio = unifiedAudio('medication');
const cues: Cue[] = cuesOf(data as any, medicationAudio.cues);
const MEDICATION_AUDIO = audioFile(data as any, medicationAudio.audio);

const defaultAdvice: Advice[] = [
  {
    title: '1. 保持通风',
    body: '房间多开窗通风，保持空气流通',
    image: 'ventilation-v1.png',
    transparent: true,
  },
  {
    title: '2. 多喝温水',
    body: '少量多次补水，帮助缓解口渴和大便干',
    image: 'warm-water-v1.png',
    transparent: true,
  },
  {
    title: '3. 饮食清淡',
    body: '避免辛辣、油炸和容易上火的燥热食物',
    image: 'light-diet-badge-v2.png',
    transparent: false,
  },
  {
    title: '4. 戒烟戒酒',
    body: '暂时戒掉烟酒，不碰温补燥热类食物',
    image: 'no-smoking-alcohol-badge-v2.png',
    transparent: false,
  },
];
const adviceItems: Advice[] = (
  SCREEN.advice_items && SCREEN.advice_items.length
    ? SCREEN.advice_items.map((item) => ({
        title: item.title,
        body: item.body,
        image: item.image,
        transparent: Boolean(item.transparent),
      }))
    : defaultAdvice
) as Advice[];

const presenterAsset = (name: string) => `/wind-heat-presenter-v2/${name}`;
const asset = (name: string) => `/advice-assets/${name}`;

function addTitle(parent: View2D | Rect, text: string) {
  parent.add(
    <Rect
      key={`editable:medication:title:${text}:root`}
      position={[LAYOUT.title.x, LAYOUT.title.y]}
      size={[1080, 100]}
    >
      <Rect position={[-440, 12]} size={20} radius={10} fill={'#fff0a8'} />
      <Rect position={[-410, -15]} size={30} radius={15} fill={'#bd386f'} />
      <Txt
        key={`editable:medication:title:${text}:text`}
        text={text}
        fontFamily={FONT}
        fontSize={TYPE.pageTitle}
        fontWeight={650}
        fill={WHITE}
      />
      <Rect
        position={[445, -17]}
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
        position={[445, 30]}
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
      key={'editable:medication:subtitle'}
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

export const referenceMedicationAdviceScene = makeScene2D('reference-medication-advice', function* (view) {
  view.add(
    <Audio
      src={MEDICATION_AUDIO}
      play
      volume={1}
    />,
  );
  view.add(
    <>
      <ReferenceMedicalTechMaster
        activeChapter={CHAPTER}
        layerPrefix={'medication'}
      />
    </>,
  );

  const medicationScene = createRef<Rect>();
  const reminderScene = createRef<Rect>();
  const adviceScene = createRef<Rect>();
  const cardOne = createRef<Rect>();
  const cardTwo = createRef<Rect>();
  const cardScans = [createRef<Rect>(), createRef<Rect>()];
  const adviceRows = adviceItems.map(() => createRef<Rect>());
  const adviceScans = adviceItems.map(() => createRef<Rect>());
  const electricCurrent = createElectricCurrentRefs();
  const medicationMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const reminderMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const medicationPresenterLayout = presenterLayout('point', 'sideLeft');
  const reminderPresenterLayout = presenterLayout('openArms', 'heroCenter');

  view.add(
    <>
      <ElectricCurrentOverlay refs={electricCurrent} />
      <Rect
        key={'editable:medication:group:medication'}
        ref={medicationScene}
        size={[1920, 1080]}
      >
        <Rect
          key={'editable:medication:presenter:point'}
          position={medicationPresenterLayout.position}
          size={medicationPresenterLayout.size}
        >
          <Img
            key={'editable:medication:presenter:point-asset'}
            src={medicationPresenterLayout.asset}
            size={medicationPresenterLayout.size}
          />
          {mouthLayer(
            medicationMouths,
            medicationPresenterLayout.size,
            medicationPresenterLayout.mouthAnchor,
          )}
        </Rect>
        <Rect
          key={'editable:medication:group:card-one'}
          position={[
            LAYOUT.medicationCards.x - LAYOUT.medicationCards.gap / 2,
            LAYOUT.medicationCards.y,
          ]}
        >
          <MedicationCard
            ref={cardOne}
            scanRef={cardScans[0]}
            name={MEDICATION_NAMES[0] || '银翘解毒颗粒'}
            imageSrc={asset('granule-package-v1.png')}
            packageSize={[800, 450]}
            fontFamily={FONT}
            titleFontSize={TYPE.medicationTitle}
            noteFontSize={TYPE.packageNote}
          />
        </Rect>
        <Rect
          position={[
            LAYOUT.medicationCards.x + LAYOUT.medicationCards.gap / 2,
            LAYOUT.medicationCards.y,
          ]}
          opacity={0}
          scale={0.92}
          key={'editable:medication:group:card-two'}
          ref={cardTwo}
        >
          <MedicationCard
            ref={createRef<Rect>()}
            scanRef={cardScans[1]}
            name={MEDICATION_NAMES[1] || '连花清瘟胶囊'}
            imageSrc={asset('capsule-carton-v1.png')}
            packageSize={[520, 292]}
            fontFamily={FONT}
            titleFontSize={TYPE.medicationTitle}
            noteFontSize={TYPE.packageNote}
          />
        </Rect>
      </Rect>

      <Rect
        key={'editable:medication:group:reminder'}
        ref={reminderScene}
        size={[1920, 1080]}
        opacity={0}
      >
        <Rect
          key={'editable:medication:presenter:open-arms'}
          position={reminderPresenterLayout.position}
          size={reminderPresenterLayout.size}
        >
          <Img
            key={'editable:medication:presenter:open-arms-asset'}
            src={reminderPresenterLayout.asset}
            size={reminderPresenterLayout.size}
          />
          {mouthLayer(
            reminderMouths,
            reminderPresenterLayout.size,
            reminderPresenterLayout.mouthAnchor,
          )}
        </Rect>
      </Rect>

      <Rect
        key={'editable:medication:group:advice'}
        ref={adviceScene}
        size={[1920, 1080]}
        opacity={0}
      >
        <Rect
          position={[LAYOUT.adviceList.x, LAYOUT.adviceList.y]}
          size={[LAYOUT.adviceList.width, 700]}
        >
          {adviceItems.map((item, index) => {
            const y =
              -249 +
              index *
                (LAYOUT.adviceList.rowHeight + LAYOUT.adviceList.rowGap);
            return (
              <AdviceRow
                ref={adviceRows[index]}
                scanRef={adviceScans[index]}
                position={[0, y]}
                item={{...item, imageSrc: asset(item.image)}}
                width={LAYOUT.adviceList.width}
                height={LAYOUT.adviceList.rowHeight}
                fontFamily={FONT}
                titleFontSize={TYPE.adviceTitle}
                bodyFontSize={TYPE.adviceBody}
              />
            );
          })}
        </Rect>
      </Rect>
    </>,
  );

  addTitle(medicationScene(), '药物调理');
  addTitle(adviceScene(), '生活禁忌与建议');
  const subtitle = addSubtitle(view);
  const allMouths = [...medicationMouths, ...reminderMouths];
  const setMouth = (active: number) => {
    for (const ref of allMouths) ref().opacity(0);
    for (const refs of [medicationMouths, reminderMouths]) {
      refs[active]().opacity(1);
    }
  };
  const setHighlight = (active: number) => {
    adviceRows.forEach((row, index) => {
      row().stroke(index === active ? '#f7faf8' : '#4daab4');
      row().lineWidth(index === active ? 7 : 4);
      row().fill(
        index === active
          ? 'rgba(58,68,78,0.98)'
          : 'rgba(18,42,55,0.94)',
      );
      row().shadowColor(
        index === active
          ? 'rgba(247,250,248,0.35)'
          : 'rgba(47,232,234,0.12)',
      );
      row().shadowBlur(index === active ? 22 : 12);
    });
  };

  function* visualTimeline() {
    yield* traceRoundedBorder(cardScans[0], 420, 620, 2.626);
    yield* all(
      cardTwo().opacity(1, 0.18),
      cardTwo().scale(1, 0.3, easeOutBack),
      traceRoundedBorder(cardScans[1], 420, 620, 3.547),
    );
    medicationScene().opacity(0);
    reminderScene().opacity(1);
    yield* waitFor(5.264);
    reminderScene().opacity(0);
    adviceScene().opacity(1);
    setHighlight(0);
    yield* traceRoundedBorder(adviceScans[0], 1400, 148, 7.061);
    setHighlight(1);
    yield* traceRoundedBorder(adviceScans[1], 1400, 148, 7.492);
    setHighlight(2);
    yield* traceRoundedBorder(adviceScans[2], 1400, 148, 8.961);
    setHighlight(3);
    yield* traceRoundedBorder(adviceScans[3], 1400, 148, 6.149);
  }

  function* mouthTimeline() {
    const pattern = [1, 2, 1, 3, 1, 0, 1, 2, 1];
    const steps = [0.2, 0.18, 0.23, 0.17, 0.24, 0.21];
    let elapsed = 0;
    let index = 0;
    while (elapsed < 11.437) {
      setMouth(pattern[index % pattern.length]);
      const step = Math.min(
        steps[index % steps.length],
        11.437 - elapsed,
      );
      yield* waitFor(step);
      elapsed += step;
      index += 1;
    }
    setMouth(0);
    yield* waitFor(DURATION - elapsed);
  }

  yield* all(
    visualTimeline(),
    runElectricCurrent(electricCurrent, DURATION),
    mouthTimeline(),
    runSubtitles(subtitle),
    applyEditablePatches(view, DURATION),
  );
});

export default makeProject({
  scenes: [referenceMedicationAdviceScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#020a15',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
