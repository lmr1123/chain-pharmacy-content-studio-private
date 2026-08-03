import {Audio, Img, Rect, Txt, makeScene2D} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';
import {ReferenceBottomSubtitle} from './components/reference-courseware-cards';
import {
  ElectricCurrentOverlay,
  createElectricCurrentRefs,
  runElectricCurrent,
} from './components/premium-medical-effects';
import {
  MedicalMechanismSequence,
  WindHeatAssembly,
} from './components/reference-mechanism-gap';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {ReferenceMedicalTechMaster} from './components/reference-medical-tech-master';
import {presenterLayout} from './wind-heat-production-contract';
import {unifiedAudio} from './wind-heat-audio-v2';
import data from '../health-training-mechanism.json';
import {
  audioFile,
  cuesOf,
  playbackDuration,
  screenOf,
} from './health-training-content';

type Cue = {start: number; end: number; text: string};

const SCREEN = screenOf(data as any);
const DURATION = playbackDuration(data as any, 15.84);
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const presenterAsset = (name: string) => `/wind-heat-presenter-v2/${name}`;
const CHAPTER = SCREEN.chapter_mechanism || '病因机理';

const mechanismAudio = unifiedAudio('mechanism');
const cues: Cue[] = cuesOf(data as any, mechanismAudio.cues);
const MECHANISM_AUDIO = audioFile(data as any, mechanismAudio.audio);

function mouthLayer(
  refs: Reference<Img>[],
  size: readonly [number, number],
  anchor: readonly [number, number],
) {
  const [width, height] = size;
  const position: [number, number] = [
    (anchor[0] - 0.5) * width,
    (anchor[1] - 0.5) * height,
  ];
  const closedWidth = width * 0.115;
  const openWidth = width * 0.124;
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

export const referenceMechanismGapScene = makeScene2D('reference-mechanism-gap', function* (view) {
  view.add(
    <Audio
      src={MECHANISM_AUDIO}
      play
      volume={1}
    />,
  );

  const intro = createRef<Rect>();
  const assemblyScene = createRef<Rect>();
  const panelScene = createRef<Rect>();
  const subtitle = createRef<Txt>();
  const assemblyRefs = {
    root: createRef<Rect>(),
    wind: createRef<Rect>(),
    plus: createRef<Txt>(),
    heat: createRef<Rect>(),
    body: createRef<Rect>(),
    bodyGlow: createRef<Rect>(),
    scanLine: createRef<Rect>(),
  };
  const panelRefs = {
    root: createRef<Rect>(),
    lungScene: createRef<Rect>(),
    lungImage: createRef<Img>(),
    lungGlow: createRef<Rect>(),
    smokeLayer: createRef<Rect>(),
    mistA: createRef<Img>(),
    mistB: createRef<Img>(),
    throatScene: createRef<Rect>(),
    throatGlow: createRef<Rect>(),
    larynxScene: createRef<Rect>(),
    larynxGlow: createRef<Rect>(),
    airflow: createRef<Rect>(),
    surfaceTag: createRef<Rect>(),
  };
  const introMouths = Array.from({length: 4}, () => createRef<Img>());
  const megaphoneMouths = Array.from({length: 4}, () => createRef<Img>());
  const pointMouths = Array.from({length: 4}, () => createRef<Img>());
  const electric = createElectricCurrentRefs();
  const introPresenter = presenterLayout('openArms', 'heroCenter');
  const megaphonePresenter = presenterLayout('megaphone', 'sideRight');
  const pointPresenter = presenterLayout('point', 'sideLeft');

  view.add(
    <>
      <ReferenceMedicalTechMaster
        activeChapter={CHAPTER}
        layerPrefix={'mechanism'}
      />
      <ElectricCurrentOverlay refs={electric} />

      <Rect ref={intro} size={[1920, 1080]}>
        <Rect
          key={'editable:mechanism:group:intro-presenter'}
          position={introPresenter.position}
          size={introPresenter.size}
        >
          <Img
            key={'editable:mechanism:presenter:open-arms'}
            src={introPresenter.asset}
            size={introPresenter.size}
          />
          {mouthLayer(
            introMouths,
            introPresenter.size,
            introPresenter.mouthAnchor,
          )}
        </Rect>
      </Rect>

      <Rect ref={assemblyScene} size={[1920, 1080]} opacity={0}>
        <Rect key={'editable:mechanism:group:wind-heat-assembly'}>
          <WindHeatAssembly refs={assemblyRefs} />
        </Rect>
        <Rect
          key={'editable:mechanism:group:megaphone-presenter'}
          position={megaphonePresenter.position}
          size={megaphonePresenter.size}
        >
          <Img
            key={'editable:mechanism:presenter:megaphone'}
            src={megaphonePresenter.asset}
            size={megaphonePresenter.size}
          />
          {mouthLayer(
            megaphoneMouths,
            megaphonePresenter.size,
            megaphonePresenter.mouthAnchor,
          )}
        </Rect>
      </Rect>

      <Rect ref={panelScene} size={[1920, 1080]} opacity={0}>
        <Rect
          key={'editable:mechanism:group:point-presenter'}
          position={pointPresenter.position}
          size={pointPresenter.size}
        >
          <Img
            key={'editable:mechanism:presenter:point'}
            src={pointPresenter.asset}
            size={pointPresenter.size}
          />
          {mouthLayer(
            pointMouths,
            pointPresenter.size,
            pointPresenter.mouthAnchor,
          )}
        </Rect>
        <Rect key={'editable:mechanism:group:medical-sequence'}>
          <MedicalMechanismSequence refs={panelRefs} />
        </Rect>
      </Rect>
      <ReferenceBottomSubtitle ref={subtitle} fontFamily={FONT} />
    </>,
  );

  const allMouths = [...introMouths, ...megaphoneMouths, ...pointMouths];
  const setMouth = (active: number) => {
    allMouths.forEach((ref) => ref().opacity(0));
    for (const group of [introMouths, megaphoneMouths, pointMouths]) {
      group[active]().opacity(1);
    }
  };

  function* visuals() {
    yield* waitFor(0.45);
    intro().opacity(0);
    assemblyScene().opacity(1);
    yield* all(
      assemblyRefs.wind().opacity(1, 0.18),
      assemblyRefs.wind().scale(1, 0.28, easeOutCubic),
    );
    yield* waitFor(0.18);
    yield* assemblyRefs.plus().opacity(1, 0.14);
    yield* all(
      assemblyRefs.heat().opacity(1, 0.18),
      assemblyRefs.heat().scale(1, 0.28, easeOutCubic),
    );
    yield* waitFor(0.2);
    yield* all(
      assemblyRefs.body().opacity(1, 0.36),
      assemblyRefs.body().scale(1, 0.42, easeOutCubic),
      assemblyRefs.bodyGlow().opacity(0.78, 0.42),
    );
    yield* waitFor(7.83);
    assemblyScene().opacity(0);
    panelScene().opacity(1);
    panelRefs.surfaceTag().scale(1.05);
    yield* all(
      panelRefs.root().opacity(1, 0.18),
      panelRefs.lungScene().opacity(1, 0.18),
      panelRefs.surfaceTag().opacity(1, 0.18),
      panelRefs.surfaceTag().scale(1, 0.22, easeOutCubic),
    );
    yield* waitFor(1.74);
    panelRefs.lungScene().opacity(0);
    panelRefs.surfaceTag().opacity(0);
    panelRefs.throatScene().opacity(1);
    yield* waitFor(1.12);
    panelRefs.throatScene().opacity(0);
    panelRefs.larynxScene().opacity(1);
    yield* waitFor(2.98);
  }

  function* pathogenMotion() {
    yield* waitFor(1.2);
    let elapsed = 1.2;
    let inward = true;
    while (elapsed < 9.78) {
      const step = Math.min(0.55, 9.78 - elapsed);
      yield* all(
        assemblyRefs.wind().position(
          [inward ? -325 : -385, -25],
          step,
        ),
        assemblyRefs.heat().position(
          [inward ? 250 : 310, -25],
          step,
        ),
        assemblyRefs.heat().scale(inward ? 1.08 : 1, step),
      );
      elapsed += step;
      inward = !inward;
    }
    yield* waitFor(DURATION - elapsed);
  }

  function* bodyScanAndPulse() {
    yield* waitFor(1.7);
    let elapsed = 1.7;
    let expanded = true;
    while (elapsed < 9.78) {
      assemblyRefs.scanLine().position([0, -300]);
      assemblyRefs.scanLine().opacity(0);
      const scanStep = Math.min(0.82, 9.78 - elapsed);
      yield* all(
        assemblyRefs.scanLine().opacity(0.9, 0.12),
        assemblyRefs.scanLine().position([0, 300], scanStep),
        assemblyRefs.body().scale(expanded ? 1.018 : 1, scanStep),
        assemblyRefs.bodyGlow().opacity(expanded ? 0.9 : 0.5, scanStep),
      );
      elapsed += scanStep;
      assemblyRefs.scanLine().opacity(0);
      expanded = !expanded;
      if (elapsed < 9.78) {
        const pause = Math.min(0.26, 9.78 - elapsed);
        yield* waitFor(pause);
        elapsed += pause;
      }
    }
    yield* waitFor(DURATION - elapsed);
  }

  function* internalMechanismMotion() {
    yield* waitFor(9.78);
    let elapsed = 9.78;
    let expanded = true;
    while (elapsed < 11.74) {
      const step = Math.min(0.38, 11.74 - elapsed);
      yield* all(
        panelRefs.lungImage().scale(expanded ? 1.025 : 1, step),
        panelRefs.lungGlow().scale(expanded ? 1.12 : 0.96, step),
        panelRefs.lungGlow().opacity(expanded ? 0.78 : 0.35, step),
        panelRefs.smokeLayer().position(
          [expanded ? -7 : 7, expanded ? -5 : 5],
          step,
        ),
        panelRefs.smokeLayer().scale(expanded ? 1.025 : 1, step),
        panelRefs.mistA().opacity(expanded ? 0.38 : 0.82, step),
        panelRefs.mistA().position(
          [expanded ? -5 : 4, expanded ? -8 : 4],
          step,
        ),
        panelRefs.mistB().opacity(expanded ? 0.72 : 0.16, step),
        panelRefs.mistB().position(
          [expanded ? 5 : -4, expanded ? 5 : -8],
          step,
        ),
      );
      elapsed += step;
      expanded = !expanded;
    }

    while (elapsed < 12.86) {
      const step = Math.min(0.28, 12.86 - elapsed);
      yield* all(
        panelRefs.throatGlow().scale(expanded ? 1.18 : 0.88, step),
        panelRefs.throatGlow().opacity(expanded ? 0.82 : 0.35, step),
      );
      elapsed += step;
      expanded = !expanded;
    }

    panelRefs.airflow().opacity(1);
    while (elapsed < DURATION) {
      panelRefs.airflow().position([-145, -75]);
      const step = Math.min(0.62, DURATION - elapsed);
      yield* all(
        panelRefs.airflow().position([-25, 60], step),
        panelRefs.airflow().opacity(0.15, step),
        panelRefs.larynxGlow().scale(expanded ? 1.16 : 0.9, step),
        panelRefs.larynxGlow().opacity(expanded ? 0.82 : 0.34, step),
      );
      elapsed += step;
      panelRefs.airflow().opacity(1);
      expanded = !expanded;
    }
  }

  function* mouths() {
    let elapsed = 0;
    let index = 0;
    const pattern = [1, 3, 1, 2, 0, 1, 3, 1];
    while (elapsed < DURATION - 0.12) {
      setMouth(pattern[index % pattern.length]);
      const step = Math.min(0.14, DURATION - 0.12 - elapsed);
      yield* waitFor(step);
      elapsed += step;
      index += 1;
    }
    setMouth(0);
    yield* waitFor(DURATION - elapsed);
  }

  yield* all(
    visuals(),
    pathogenMotion(),
    bodyScanAndPulse(),
    internalMechanismMotion(),
    mouths(),
    runSubtitles(subtitle),
    runElectricCurrent(electric, DURATION),
    applyEditablePatches(view, DURATION),
  );
});

export default makeProject({
  scenes: [referenceMechanismGapScene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#020a15',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
