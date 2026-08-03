import {Audio, Rect, Txt, makeScene2D} from '@revideo/2d';
import {
  all,
  createRef,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';
import {
  ElectricCurrentOverlay,
  createElectricCurrentRefs,
  runElectricCurrent,
} from './components/premium-medical-effects';
import {ReferenceMedicalTechMaster} from './components/reference-medical-tech-master';
import {applyEditablePatches} from './editor/apply-editable-patches';
import data from '../health-training-intro.json';
import {
  audioFile,
  diseaseName,
  playbackDuration,
  screenOf,
} from './health-training-content';

const DISEASE = diseaseName(data as any);
const SCREEN = screenOf(data as any);
const DURATION = playbackDuration(data as any, 136 / 30);
const AUDIO = audioFile(data as any, '/wind-heat-audio-v2/intro-silence.wav');
const EYEBROW = SCREEN.eyebrow || '中医基础知识';
const TAGLINE = SCREEN.tagline || '营运培训 · 专业赋能';
const CHAPTER = SCREEN.chapter_intro || '基础认知';
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';

function* referenceNativeIntro(view: Parameters<Parameters<typeof makeScene2D>[1]>[0], canonical = false) {
  const title = createRef<Rect>();
  const titleText = createRef<Txt>();
  const ghostCyan = createRef<Txt>();
  const ghostMagenta = createRef<Txt>();
  const rule = createRef<Rect>();
  const scan = createRef<Rect>();
  const electric = createElectricCurrentRefs();

  view.add(
    <>
      <Audio src={AUDIO} play />
      <ReferenceMedicalTechMaster
        activeChapter={CHAPTER}
        layerPrefix={'intro'}
      />
      <ElectricCurrentOverlay refs={electric} />
      <Rect
        key={'editable:intro:group:title'}
        ref={title}
        position={[0, -10]}
        opacity={0}
        scale={0.92}
      >
        <Txt
          key={'editable:intro:title:eyebrow'}
          position={[0, -92]}
          text={EYEBROW}
          fontFamily={FONT}
          fontSize={44}
          fontWeight={500}
          letterSpacing={12}
          fill={'rgba(204, 244, 245, 0.82)'}
        />
        <Txt
          key={'editable:intro:title:ghost-cyan'}
          ref={ghostCyan}
          position={[-7, 20]}
          text={DISEASE}
          fontFamily={FONT}
          fontSize={126}
          fontWeight={720}
          letterSpacing={18}
          fill={'#45eff4'}
          opacity={0}
        />
        <Txt
          key={'editable:intro:title:ghost-magenta'}
          ref={ghostMagenta}
          position={[7, 20]}
          text={DISEASE}
          fontFamily={FONT}
          fontSize={126}
          fontWeight={720}
          letterSpacing={18}
          fill={'#f34b91'}
          opacity={0}
        />
        <Txt
          key={'editable:intro:title:main'}
          ref={titleText}
          position={[0, 20]}
          text={DISEASE}
          fontFamily={FONT}
          fontSize={126}
          fontWeight={720}
          letterSpacing={18}
          fill={'#f7faf8'}
          shadowColor={'rgba(66, 224, 228, 0.42)'}
          shadowBlur={24}
        />
        <Rect
          ref={scan}
          position={[0, -80]}
          size={[760, 5]}
          fill={'rgba(213,255,255,0.72)'}
          shadowColor={'#5effff'}
          shadowBlur={22}
          opacity={0}
        />
        <Rect
          ref={rule}
          position={[0, 112]}
          size={[0, 4]}
          radius={2}
          fill={'#55e5e8'}
          shadowColor={'#55e5e8'}
          shadowBlur={18}
        />
        <Txt
          position={[0, 166]}
          text={TAGLINE}
          fontFamily={FONT}
          fontSize={32}
          letterSpacing={8}
          fill={'rgba(224, 246, 246, 0.68)'}
        />
      </Rect>
    </>,
  );

  function* glitchTimeline() {
    yield* waitFor(0.36);
    scan().opacity(0.74);
    yield* scan().position([0, 120], 0.48);
    scan().opacity(0);
    yield* waitFor(0.18);
    ghostCyan().opacity(0.58);
    ghostMagenta().opacity(0.46);
    titleText().opacity(0.72);
    title().position([8, -10]);
    yield* waitFor(0.055);
    title().position([-10, -10]);
    ghostCyan().position([11, 20]);
    ghostMagenta().position([-9, 20]);
    yield* waitFor(0.055);
    title().position([4, -10]);
    titleText().opacity(1);
    yield* waitFor(0.045);
    title().position([0, -10]);
    ghostCyan().opacity(0);
    ghostMagenta().opacity(0);
    yield* waitFor(0.62);
    ghostCyan().opacity(0.42);
    ghostMagenta().opacity(0.34);
    titleText().opacity(0.62);
    title().position([-6, -10]);
    yield* waitFor(0.045);
    title().position([7, -10]);
    titleText().opacity(1);
    yield* waitFor(0.045);
    title().position([0, -10]);
    ghostCyan().opacity(0);
    ghostMagenta().opacity(0);
    yield* waitFor(DURATION - 2.04);
  }

  yield* all(
    title().opacity(1, 0.5),
    title().scale(1, 0.64, easeOutCubic),
    rule().size([620, 4], 0.72, easeOutCubic),
    runElectricCurrent(electric, DURATION),
    glitchTimeline(),
    applyEditablePatches(view, DURATION),
  );
  if (!canonical) {
    yield* waitFor(DURATION - 0.72);
  }
}

export const referenceNativeIntroScene = makeScene2D(
  'reference-native-intro',
  function* (view) {
    yield* referenceNativeIntro(view);
  },
);

export const referenceNativeIntroCanonicalScene = makeScene2D(
  'reference-native-intro-canonical',
  function* (view) {
    yield* referenceNativeIntro(view, true);
  },
);

export default makeProject({
  scenes: [referenceNativeIntroScene],
  settings: {
    shared: {size: {x: 1920, y: 1080}, background: '#020a15'},
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
