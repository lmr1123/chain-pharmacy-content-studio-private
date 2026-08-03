import {Audio, Img, Rect, Txt, makeScene2D} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  makeProject,
  waitFor,
} from '@revideo/core';
import {
  AdviceRow,
  ReferenceBottomSubtitle,
} from './components/reference-courseware-cards';
import {
  ElectricCurrentOverlay,
  createElectricCurrentRefs,
  runElectricCurrent,
} from './components/premium-medical-effects';
import {
  SummaryMatrix,
  SummaryTopCurrentArrow,
  TrainingBrandOutro,
  revealSummaryMatrix,
  revealTrainingOutro,
  runSummaryTopArrow,
} from './components/reference-summary-outro';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {ReferenceMedicalTechMaster} from './components/reference-medical-tech-master';
import {unifiedAudio} from './wind-heat-audio-v2';

type Cue = {start: number; end: number; text: string};

const DURATION = 27.99;
const OUTRO_START = 25.0;
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const adviceAsset = (name: string) => `/advice-assets/${name}`;

const legacyCues: Cue[] = [
  {start: 0.00, end: 0.94, text: '最后'},
  {start: 0.94, end: 2.64, text: '给大家划个重点'},
  {start: 2.64, end: 4.96, text: '记不住的可以多看两遍'},
  {start: 4.96, end: 5.80, text: '病因'},
  {start: 5.80, end: 7.60, text: '风加热一起入侵'},
  {start: 7.60, end: 8.66, text: '肺气不顺'},
  {start: 8.66, end: 9.48, text: '症状'},
  {start: 9.48, end: 10.20, text: '发热'},
  {start: 10.20, end: 11.00, text: '口渴'},
  {start: 11.00, end: 11.88, text: '喉咙痛'},
  {start: 11.88, end: 12.74, text: '咳黄痰'},
  {start: 12.74, end: 13.62, text: '流黄涕'},
  {start: 13.62, end: 14.36, text: '心烦'},
  {start: 14.36, end: 15.12, text: '调理'},
  {start: 15.12, end: 16.32, text: '疏风清热'},
  {start: 16.32, end: 17.24, text: '用桑叶'},
  {start: 17.24, end: 17.98, text: '菊花'},
  {start: 17.98, end: 18.68, text: '薄荷'},
  {start: 18.68, end: 19.70, text: '清淡饮食'},
  {start: 19.70, end: 20.52, text: '多喝水'},
  {start: 20.52, end: 21.26, text: '禁忌'},
  {start: 21.26, end: 22.40, text: '辛辣刺激'},
  {start: 22.40, end: 23.16, text: '烟酒'},
  {start: 23.16, end: 24.54, text: '温补燥热食物'},
];
const summaryAudio = unifiedAudio('summary');
const cues: Cue[] = summaryAudio.cues;

const summaryItems = [
  {title: '病因', body: '风 + 热一起入侵，肺气不顺'},
  {title: '症状', body: '发热口渴、喉咙痛、咳黄痰、流黄涕、心烦'},
  {title: '调理', body: '疏风清热，用桑叶、菊花、薄荷，清淡饮食多喝水'},
  {title: '禁忌', body: '辛辣刺激、烟酒、温补燥热食物'},
];

const adviceItems = [
  ['1. 保持通风', '房间多开窗通风，保持空气流通', 'ventilation-v1.png', true],
  ['2. 多喝温水', '少量多次补水，帮助缓解口渴和大便干', 'warm-water-v1.png', true],
  ['3. 饮食清淡', '避免辛辣、油炸和容易上火的燥热食物', 'light-diet-badge-v2.png', false],
  ['4. 戒烟戒酒', '暂时戒掉烟酒，不碰温补燥热类食物', 'no-smoking-alcohol-badge-v2.png', false],
] as const;

function addTitle(parent: Rect, text: string) {
  parent.add(
    <Rect
      key={`editable:summary:title:${text}:root`}
      position={[0, -420]}
      size={[1080, 100]}
    >
      <Rect position={[-440, 12]} size={20} radius={10} fill={'#fff0a8'} />
      <Rect position={[-410, -15]} size={30} radius={15} fill={'#bd386f'} />
      <Txt
        key={`editable:summary:title:${text}:text`}
        text={text}
        fontFamily={FONT}
        fontSize={76}
        fontWeight={650}
        fill={'#f7faf8'}
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
  yield* waitFor(DURATION - cursor);
}

export const referenceSummaryOutroScene = makeScene2D('reference-summary-outro', function* (view) {
  view.add(
    <Audio
      src={summaryAudio.audio}
      play
      volume={1}
    />,
  );
  view.add(
    <>
      <ReferenceMedicalTechMaster
        activeChapter={'重点总结'}
        layerPrefix={'summary'}
      />
    </>,
  );

  const advice = createRef<Rect>();
  const summary = createRef<Rect>();
  const dimmer = createRef<Rect>();
  const subtitle = createRef<Txt>();
  const matrixRefs = {
    panel: createRef<Rect>(),
    labelsLayer: createRef<Rect>(),
    bodiesLayer: createRef<Rect>(),
  };
  const arrowRefs = {
    track: createRef<any>(),
    glow: createRef<Rect>(),
  };
  const bodyMasks = summaryItems.map(() => createRef<Rect>());
  const outroRefs = {
    root: createRef<Rect>(),
    handwriting: createRef<any>(),
    light: createRef<any>(),
    subtitle: createRef<Txt>(),
  };
  const electric = createElectricCurrentRefs();

  view.add(
    <>
      <ElectricCurrentOverlay refs={electric} />
      <Rect
        key={'editable:summary:group:advice'}
        ref={advice}
        size={[1920, 1080]}
      >
        <Rect position={[0, 45]} size={[1400, 700]}>
          {adviceItems.map(([title, body, image, transparent], index) => (
            <AdviceRow
              ref={createRef<Rect>()}
              scanRef={createRef<Rect>()}
              position={[0, -249 + index * 166]}
              item={{
                title,
                body,
                imageSrc: adviceAsset(image),
                transparent,
              }}
              width={1400}
              height={148}
              fontFamily={FONT}
              titleFontSize={42}
              bodyFontSize={34}
            />
          ))}
        </Rect>
      </Rect>
      <Rect
        ref={dimmer}
        size={[1920, 1080]}
        fill={'rgba(0,4,10,0.48)'}
        opacity={0}
      />
      <Rect
        key={'editable:summary:group:summary'}
        ref={summary}
        size={[1920, 1080]}
        opacity={0}
      >
        <SummaryMatrix
          refs={matrixRefs}
          items={summaryItems}
          fontFamily={FONT}
        />
        {[
          [-348, -70],
          [348, -70],
          [-348, 240],
          [348, 240],
        ].map((position, index) => (
          <Rect
            ref={bodyMasks[index]}
            position={position as [number, number]}
            size={[590, 145]}
            fill={'#102537'}
          />
        ))}
        <SummaryTopCurrentArrow refs={arrowRefs} />
      </Rect>
      <TrainingBrandOutro refs={outroRefs} fontFamily={FONT} />
      <ReferenceBottomSubtitle
        ref={subtitle}
        fontFamily={FONT}
        layerId={'editable:summary:subtitle'}
      />
    </>,
  );

  addTitle(advice(), '生活禁忌与建议');
  addTitle(summary(), '风热证总结');

  function* visuals() {
    yield* dimmer().opacity(1, 0.22);
    yield* waitFor(0.72);
    advice().opacity(0);
    dimmer().opacity(0);
    summary().opacity(1);
    yield* revealSummaryMatrix(matrixRefs);
    yield* all(...bodyMasks.map((mask) => mask().opacity(0, 0.28)));
    yield* waitFor(Math.max(0, OUTRO_START - 2.04));
    summary().opacity(0);
    yield* revealTrainingOutro(outroRefs, DURATION - OUTRO_START);
  }

  yield* all(
    visuals(),
    runSubtitles(subtitle),
    runElectricCurrent(electric, DURATION),
    runSummaryTopArrow(arrowRefs, OUTRO_START),
    applyEditablePatches(view, DURATION),
  );
});

export default makeProject({
  scenes: [referenceSummaryOutroScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#020a15',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
