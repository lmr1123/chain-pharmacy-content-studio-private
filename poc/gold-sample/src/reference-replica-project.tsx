import {
  Audio,
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
  chain,
  createRef,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {ReferenceMedicalTechMaster} from './components/reference-medical-tech-master';
import {
  presenterLayout,
  presenterMouthLayout,
} from './wind-heat-production-contract';
import {unifiedAudio} from './wind-heat-audio-v2';
import data from '../health-training-character.json';
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

const DISEASE = diseaseName(data as any);
const SCREEN = screenOf(data as any);
const DURATION = playbackDuration(data as any, 28.1);
const CANONICAL_START = 136 / 30;
const CANONICAL_END = 840 / 30;
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const CYAN = '#56b9c2';
const TEXT = '#f6f7f5';
const PANEL = 'rgba(4, 14, 26, 0.94)';

const characterAudio = unifiedAudio('character');
const cues: Cue[] = cuesOf(data as any, characterAudio.cues);
const CHARACTER_AUDIO = audioFile(data as any, characterAudio.audio);
const CHAPTER = SCREEN.chapter_character || '基础认知';
const CHARACTER_CARDS =
  SCREEN.character_cards ||
  ['喉咙肿痛', '身体发烫', '咳嗽痰黄', '口渴嘴干', '鼻涕黄稠', '心里烦躁'];
const MECHANISM_TITLE =
  SCREEN.mechanism_title || `${DISEASE}怎么找上门？`;
const EQUATION_LEFT = SCREEN.equation_left || '💨  风邪';
const EQUATION_RIGHT = SCREEN.equation_right || '🔥  热邪';
const EQUATION_RESULT = SCREEN.equation_result || '入侵身体';

const presenterAsset = (name: string) => `/wind-heat-presenter-v2/${name}`;

function addSubtitle(view: View2D) {
  const ref = createRef<Txt>();
  view.add(
    <Txt
      key={'editable:character:subtitle'}
      ref={ref}
      position={[0, 433]}
      width={1540}
      textAlign={'center'}
      fontFamily={FONT}
      fontSize={40}
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

function* runSubtitles(
  ref: Reference<Txt>,
  startAt = 0,
  endAt = DURATION,
) {
  let cursor = startAt;
  for (const cue of cues) {
    if (cue.end <= startAt || cue.start >= endAt) continue;
    const cueStart = Math.max(startAt, cue.start);
    const cueEnd = Math.min(endAt, cue.end);
    if (cueStart > cursor) {
      ref().opacity(0);
      yield* waitFor(cueStart - cursor);
    }
    ref().text(cue.text);
    const fadeDuration = Math.min(0.06, cueEnd - cueStart);
    yield* ref().opacity(1, fadeDuration);
    yield* waitFor(Math.max(0, cueEnd - cueStart - fadeDuration));
    ref().opacity(0);
    cursor = cueEnd;
  }
  yield* waitFor(Math.max(0, endAt - cursor));
}

function* referenceCharacterAction(view: View2D, startAt = 0, endAt = DURATION) {
  const duration = endAt - startAt;
  const trimmed = startAt > 0;
  view.add(
    <Audio
      src={CHARACTER_AUDIO}
      time={startAt}
      play
      volume={1}
    />,
  );

  const title = createRef<Rect>();
  const titleFrame = createRef<Rect>();
  const main = createRef<Rect>();
  const presenter = createRef<Rect>();
  const palm = createRef<Img>();
  const arms = createRef<Img>();
  const palmMouthCover = createRef<Rect>();
  const armsMouthCover = createRef<Rect>();
  const palmMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const armsMouths = ['closed', 'small', 'o', 'wide'].map(() =>
    createRef<Img>(),
  );
  const activeChapter = createRef<Rect>();
  const palmLayout = presenterLayout('palm', 'sideLeft');
  const armsLayout = presenterLayout('openArms', 'heroCenter');
  const palmMouthLayout = presenterMouthLayout('palm', palmLayout.size);
  const armsMouthLayout = presenterMouthLayout('openArms', armsLayout.size);
  const symptomCards = CHARACTER_CARDS.map(() => createRef<Rect>());
  const nodeTitle = createRef<Txt>();
  const equation = createRef<Rect>();
  const arrow = createRef<Line>();

  view.add(
    <>
      <Rect
        key={'editable:character:group:title'}
        ref={title}
        size={[1920, 1080]}
        opacity={trimmed ? 0 : 1}
      >
        <Rect
          key={'editable:character:asset:title-frame'}
          ref={titleFrame}
          size={[1920, 1080]}
          scale={1.015}
        >
          <ReferenceMedicalTechMaster
            activeChapter={CHAPTER}
            layerPrefix={'character-title'}
          />
          <Txt
            key={'editable:character:title:text'}
            text={DISEASE}
            fontFamily={FONT}
            fontSize={112}
            fontWeight={700}
            fill={'#f7faf8'}
          />
        </Rect>
        <Rect
          position={[0, 446]}
          size={[900, 82]}
          fill={'rgba(3, 16, 30, 0.96)'}
          radius={10}
        />
        <Rect
          position={[0, -28]}
          size={[1920, 9]}
          fill={'rgba(113,245,236,0.22)'}
          shadowColor={'rgba(75,231,225,0.55)'}
          shadowBlur={16}
        />
      </Rect>

      <Rect ref={main} size={[1920, 1080]} opacity={trimmed ? 1 : 0}>
        <ReferenceMedicalTechMaster
          activeChapter={CHAPTER}
          layerPrefix={'character'}
        />
        <Rect
          ref={activeChapter}
          position={[-650, 443]}
          size={[220, 5]}
          fill={'rgba(75, 231, 225, 0.72)'}
        />

          <Rect
            key={'editable:character:group:presenter'}
            ref={presenter}
          position={palmLayout.position}
          size={palmLayout.size}
          opacity={trimmed ? 0.45 : 0}
          >
          <Rect
            position={[0, 365]}
            size={[620, 620]}
            scale={[1, 0.22]}
            radius={310}
            stroke={'rgba(72, 185, 196, 0.28)'}
            lineWidth={4}
          />
          <Rect
            position={[0, 365]}
            size={[470, 470]}
            scale={[1, 0.22]}
            radius={235}
            stroke={'rgba(94, 220, 218, 0.18)'}
            lineWidth={3}
          />
          <Img
            key={'editable:character:presenter:palm'}
            ref={palm}
            src={palmLayout.asset}
            size={palmLayout.size}
            opacity={1}
          />
          <Rect
            ref={palmMouthCover}
            position={palmMouthLayout.position}
            size={palmMouthLayout.openSize}
            radius={31}
            fill={'#fdf5e9'}
            opacity={0}
          />
          {['closed', 'small', 'o', 'wide'].map((name, index) => (
            <Img
              key={`editable:character:presenter:palm-mouth:${name}`}
              ref={palmMouths[index]}
              src={presenterAsset(
                name === 'closed'
                  ? 'mouth-closed-vector.svg'
                  : `mouth-${name}-vector.svg`,
              )}
              position={palmMouthLayout.position}
              size={
                index === 0
                  ? palmMouthLayout.closedSize
                  : palmMouthLayout.openSize
              }
              opacity={index === 0 ? 1 : 0}
            />
          ))}
          <Img
            key={'editable:character:presenter:open-arms'}
            ref={arms}
            src={armsLayout.asset}
            size={armsLayout.size}
            opacity={0}
          />
          <Rect
            ref={armsMouthCover}
            position={armsMouthLayout.position}
            size={armsMouthLayout.openSize}
            radius={29}
            fill={'#fdf5e9'}
            opacity={0}
          />
          {['closed', 'small', 'o', 'wide'].map((name, index) => (
            <Img
              key={`editable:character:presenter:open-arms-mouth:${name}`}
              ref={armsMouths[index]}
              src={presenterAsset(
                name === 'closed'
                  ? 'mouth-closed-vector.svg'
                  : `mouth-${name}-vector.svg`,
              )}
              position={armsMouthLayout.position}
              size={
                index === 0
                  ? armsMouthLayout.closedSize
                  : armsMouthLayout.openSize
              }
              opacity={0}
            />
          ))}

        </Rect>

        {CHARACTER_CARDS.map((label, index) => {
          const col = index % 2;
          const row = Math.floor(index / 2);
          return (
            <Rect
              key={`editable:character:symptom-card:${index}:root`}
              ref={symptomCards[index]}
              position={[260 + col * 380, -210 + row * 174]}
              size={[395, 116]}
              fill={PANEL}
              stroke={CYAN}
              lineWidth={2}
              opacity={0}
              scale={0.92}
              shadowColor={'rgba(59, 188, 198, 0.24)'}
              shadowBlur={12}
            >
              <Line
                position={[-174, -49]}
                points={[
                  [0, 0],
                  [48, 0],
                ]}
                stroke={'#7cd6de'}
                lineWidth={5}
              />
              <Line
                position={[174, 49]}
                points={[
                  [-48, 0],
                  [0, 0],
                ]}
                stroke={'#7cd6de'}
                lineWidth={5}
              />
              <Txt
                key={`editable:character:symptom-card:${index}:text`}
                text={label}
                fontFamily={FONT}
                fontSize={51}
                fontWeight={430}
                fill={TEXT}
              />
            </Rect>
          );
        })}

        <Txt
          key={'editable:character:text:mechanism-title'}
          ref={nodeTitle}
          position={[0, -430]}
          text={MECHANISM_TITLE}
          fontFamily={FONT}
          fontSize={58}
          fontWeight={650}
          fill={TEXT}
          opacity={0}
        />
        <Rect
          key={'editable:character:group:equation'}
          ref={equation}
          position={[0, -190]}
          size={[1720, 150]}
          opacity={0}
          scale={0.9}
        >
          <Rect
            position={[-700, 0]}
            size={[220, 112]}
            radius={18}
            fill={'rgba(23, 50, 69, 0.94)'}
            stroke={'#4aa7bf'}
            lineWidth={2}
          >
            <Txt
              key={'editable:character:equation:wind'}
              text={EQUATION_LEFT}
              fontFamily={FONT}
              fontSize={42}
              fill={'#8dcff2'}
            />
          </Rect>
          <Txt
            key={'editable:character:equation:plus'}
            position={[-550, 0]}
            text={'＋'}
            fontFamily={FONT}
            fontSize={62}
            fill={TEXT}
          />
          <Rect
            position={[-390, 0]}
            size={[220, 112]}
            radius={18}
            fill={'rgba(69, 39, 29, 0.94)'}
            stroke={'#ef8057'}
            lineWidth={2}
          >
            <Txt
              key={'editable:character:equation:heat'}
              text={EQUATION_RIGHT}
              fontFamily={FONT}
              fontSize={42}
              fill={'#ff9c72'}
            />
          </Rect>
          <Line
            ref={arrow}
            position={[-245, 0]}
            points={[
              [-62, 0],
              [0, 0],
            ]}
            stroke={'#5cc5cb'}
            lineWidth={6}
            endArrow
            arrowSize={18}
            end={0}
          />
          <Txt
            key={'editable:character:equation:result'}
            position={[520, 0]}
            text={EQUATION_RESULT}
            fontFamily={FONT}
            fontSize={44}
            fontWeight={620}
            fill={'#7de0dc'}
          />
        </Rect>
      </Rect>
    </>,
  );
  const subtitle = addSubtitle(view);

  const allMouths = [...palmMouths, ...armsMouths];
  const setMouth = (pose: 'palm' | 'arms', active: number) => {
    for (const ref of allMouths) {
      ref().opacity(0);
    }
    const target = pose === 'palm' ? palmMouths : armsMouths;
    target[active]().opacity(1);
  };

  function* titleMotion() {
    if (trimmed) {
      yield* waitFor(duration);
      return;
    }
    yield* waitFor(0.42);
    yield* titleFrame().position([10, 0], 0.05);
    yield* titleFrame().position([-8, 0], 0.05);
    yield* titleFrame().position([5, 0], 0.05);
    yield* titleFrame().position([0, 0], 0.05);
    yield* waitFor(3.66);
    yield* all(title().opacity(0, 0.26), main().opacity(1, 0.26));
  }

  function* visualTimeline() {
    if (trimmed) {
      presenter().position([-715, 16]);
      const remainingEntrance = Math.max(0, 4.94 - startAt);
      yield* all(
        presenter().opacity(1, Math.min(0.19, remainingEntrance)),
        presenter().position(
          [-650, 12],
          remainingEntrance,
          easeOutCubic,
        ),
      );
    } else {
      yield* waitFor(4.38);
      presenter().position([-820, 22]);
      yield* all(
        presenter().opacity(1, 0.34),
        presenter().position([-650, 12], 0.56, easeOutCubic),
      );
    }

    yield* waitFor(2.58);
    yield* chain(
      ...symptomCards.map((card) =>
        all(card().opacity(1, 0.22), card().scale(1, 0.28, easeOutCubic)),
      ),
    );

    yield* waitFor(10.12);
    yield* all(
      ...symptomCards.map((card) => card().opacity(0, 0.28)),
    );

    yield* waitFor(1.68);
    palm().opacity(0);
    setMouth('palm', 0);
    palmMouthCover().opacity(0);
    arms().opacity(1);
    armsMouthCover().opacity(0);
    setMouth('arms', 0);
    presenter().position(armsLayout.position);
    activeChapter().position([-325, 443]);

    yield* all(
      nodeTitle().opacity(1, 0.36),
      equation().opacity(1, 0.42),
      equation().scale(1, 0.42, easeOutCubic),
    );
    yield* arrow().end(1, 0.34);
    yield* waitFor(4.3);
  }

  function* mouthTimeline() {
    const mouthStart = Math.max(startAt, 4.56);
    yield* waitFor(mouthStart - startAt);
    let elapsed = mouthStart;
    let pose: 'palm' | 'arms' = 'palm';
    let index = 0;
    const pattern = [1, 3, 1, 2, 0, 1, 3, 1];

    while (elapsed < endAt) {
      if (elapsed >= 21.28) {
        pose = 'arms';
      }
      setMouth(pose, pattern[index % pattern.length]);
      const mouthStep = Math.min(0.14, endAt - elapsed);
      yield* waitFor(mouthStep);
      elapsed += mouthStep;
      index += 1;
    }
    setMouth('arms', 0);
  }

  yield* all(
    titleMotion(),
    visualTimeline(),
    mouthTimeline(),
    runSubtitles(subtitle, startAt, endAt),
    applyEditablePatches(view, endAt - startAt),
  );
}

export const referenceCharacterActionScene = makeScene2D(
  'reference-character-action',
  function* (view) {
    yield* referenceCharacterAction(view);
  },
);

export const referenceCharacterBodyScene = makeScene2D(
  'reference-character-body',
  function* (view) {
    yield* referenceCharacterAction(view, CANONICAL_START, CANONICAL_END);
  },
);

export default makeProject({
  scenes: [referenceCharacterActionScene],
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
