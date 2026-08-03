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
  chain,
  createRef,
  makeProject,
  waitFor,
} from '@revideo/core';

import storyboard from '../review-storyboard.json';
import timing from '../review-audio/timing.json';

type Cue = {
  start: number;
  end: number;
  text: string;
};

type SceneTiming = {
  duration: number;
  cues: Cue[];
};

const COLORS = {
  bg: '#04111f',
  teal: '#2de2e6',
  tealSoft: '#69f0e8',
  coral: '#ff755b',
  text: '#f5fbff',
  muted: '#a7c3d5',
  panel: 'rgba(7, 27, 44, 0.9)',
};

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const sceneById = Object.fromEntries(
  storyboard.scenes.map((scene) => [scene.id, scene]),
) as Record<string, (typeof storyboard.scenes)[number]>;
const timingById = timing as Record<string, SceneTiming>;

const asset = (name: string) => `/assets/${name}`;
const audio = (id: string) => `/review-audio/${id}.m4a`;

function addBackground(view: View2D, opacity = 1) {
  const ref = createRef<Img>();
  view.add(
    <Img
      ref={ref}
      src={asset('medical-tech-background.png')}
      size={[1920, 1080]}
      opacity={opacity}
    />,
  );
  return ref;
}

function addSubtitle(view: View2D) {
  const textRef = createRef<Txt>();
  view.add(
    <>
      <Rect
        position={[0, 432]}
        size={[1540, 66]}
        radius={18}
        fill={'rgba(0,7,15,0.78)'}
        stroke={'rgba(59,220,224,0.2)'}
        lineWidth={1}
      />
      <Txt
        ref={textRef}
        position={[0, 432]}
        width={1460}
        textWrap
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={32}
        fontWeight={500}
        fill={COLORS.text}
        opacity={0}
        shadowColor={'rgba(0,0,0,0.9)'}
        shadowBlur={8}
      />
    </>,
  );
  return textRef;
}

function* runSubtitles(
  ref: Reference<Txt>,
  cues: Cue[],
  duration: number,
) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      yield* waitFor(cue.start - cursor);
    }
    ref().text(cue.text);
    yield* ref().opacity(1, 0.08);
    yield* waitFor(Math.max(0.04, cue.end - cue.start - 0.08));
    cursor = cue.end;
  }
  if (duration > cursor) {
    yield* waitFor(duration - cursor);
  }
}

function addAudio(view: View2D, id: string) {
  view.add(<Audio src={audio(id)} play />);
}

const r01 = makeScene2D('review-tech-title', function* (view) {
  const id = 'r01';
  const data = sceneById[id];
  const duration = timingById[id].duration + 0.5;
  const bg = addBackground(view, 0);
  addAudio(view, id);
  const subtitle = addSubtitle(view);

  const eyebrow = createRef<Txt>();
  const title = createRef<Txt>();
  const sub = createRef<Txt>();
  const line = createRef<Line>();
  const ring1 = createRef<Circle>();
  const ring2 = createRef<Circle>();

  view.add(
    <>
      <Circle
        ref={ring1}
        position={[465, 10]}
        size={360}
        stroke={'rgba(38,222,228,0.55)'}
        lineWidth={4}
        startAngle={-80}
        endAngle={185}
        opacity={0}
        scale={0.72}
      />
      <Circle
        ref={ring2}
        position={[465, 10]}
        size={292}
        stroke={'rgba(255,117,91,0.65)'}
        lineWidth={10}
        startAngle={20}
        endAngle={84}
        opacity={0}
      />
      <Txt
        ref={eyebrow}
        position={[-360, -145]}
        width={740}
        textAlign={'left'}
        fontFamily={FONT}
        fontSize={30}
        fontWeight={600}
        letterSpacing={7}
        fill={COLORS.tealSoft}
        opacity={0}
      >
        {data.screenCopy.eyebrow}
      </Txt>
      <Txt
        ref={title}
        position={[-355, 5]}
        width={760}
        textAlign={'left'}
        fontFamily={FONT}
        fontSize={142}
        fontWeight={800}
        letterSpacing={10}
        fill={COLORS.text}
        opacity={0}
        scale={0.82}
        shadowColor={'rgba(34,221,227,0.45)'}
        shadowBlur={28}
      >
        {data.screenCopy.title}
      </Txt>
      <Line
        ref={line}
        points={[
          [-720, 130],
          [80, 130],
        ]}
        stroke={COLORS.teal}
        lineWidth={4}
        end={0}
      />
      <Txt
        ref={sub}
        position={[-360, 200]}
        width={740}
        textAlign={'left'}
        fontFamily={FONT}
        fontSize={31}
        letterSpacing={3}
        fill={COLORS.muted}
        opacity={0}
      >
        {data.screenCopy.sub}
      </Txt>
      <Txt
        position={[760, 440]}
        width={330}
        textAlign={'right'}
        fontFamily={FONT}
        fontSize={18}
        letterSpacing={3}
        fill={'rgba(157,201,215,0.55)'}
      >
        VISUAL APPROVAL · 30 SEC
      </Txt>
    </>,
  );

  function* visuals() {
    yield* all(bg().opacity(1, 0.4), ring1().opacity(1, 0.45));
    yield* all(
      ring1().scale(1, 0.55),
      ring1().rotation(38, 1.1),
      ring2().opacity(1, 0.45),
      eyebrow().opacity(1, 0.35),
    );
    yield* all(title().opacity(1, 0.45), title().scale(1, 0.45));
    yield* all(line().end(1, 0.55), sub().opacity(1, 0.55));
    yield* waitFor(Math.max(0, duration - 2.45));
  }

  yield* all(
    visuals(),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

const r02 = makeScene2D('review-expressive-presenter', function* (view) {
  const id = 'r02';
  const data = sceneById[id] as any;
  const duration = timingById[id].duration + 0.55;
  addBackground(view, 0.96);
  addAudio(view, id);
  const subtitle = addSubtitle(view);

  const presenter = createRef<Rect>();
  const neutral = createRef<Img>();
  const talking = createRef<Img>();
  const blink = createRef<Img>();
  const concerned = createRef<Img>();
  const pointing = createRef<Img>();
  const pointingTalking = createRef<Img>();
  const title = createRef<Rect>();
  const lead = createRef<Txt>();
  const cards = data.screenCopy.cards.map(() => createRef<Rect>());

  view.add(
    <>
      <Circle
        position={[-610, 80]}
        size={620}
        stroke={'rgba(45,226,230,0.2)'}
        lineWidth={3}
      />
      <Circle
        position={[-610, 80]}
        size={510}
        stroke={'rgba(255,117,91,0.12)'}
        lineWidth={8}
        startAngle={20}
        endAngle={120}
      />
      <Rect
        ref={presenter}
        position={[-610, 56]}
        size={[430, 860]}
        opacity={0}
        scale={0.94}
      >
        <Img
          ref={neutral}
          src={asset('pharmacist-review-neutral.png')}
          size={[380, 860]}
          opacity={0}
        />
        <Img
          ref={talking}
          src={asset('pharmacist-review-talking.png')}
          size={[380, 860]}
          opacity={0}
        />
        <Img
          ref={blink}
          src={asset('pharmacist-review-blink.png')}
          size={[380, 860]}
          opacity={0}
        />
        <Img
          ref={concerned}
          src={asset('pharmacist-review-concerned.png')}
          size={[380, 860]}
          opacity={0}
        />
        <Img
          ref={pointing}
          src={asset('pharmacist-review-pointing.png')}
          size={[380, 860]}
          opacity={0}
        />
        <Img
          ref={pointingTalking}
          src={asset('pharmacist-review-pointing-talking.png')}
          size={[380, 860]}
          opacity={0}
        />
      </Rect>
      <Rect
        ref={title}
        position={[270, -390]}
        opacity={0}
        scale={0.95}
        layout
        direction={'column'}
        gap={7}
        alignItems={'center'}
      >
        <Txt
          fontFamily={FONT}
          fontSize={21}
          fontWeight={600}
          letterSpacing={5}
          fill={COLORS.teal}
        >
          {data.screenCopy.eyebrow}
        </Txt>
        <Txt
          fontFamily={FONT}
          fontSize={56}
          fontWeight={760}
          fill={COLORS.text}
        >
          {data.screenCopy.title}
        </Txt>
      </Rect>
      <Txt
        ref={lead}
        position={[270, -270]}
        width={1050}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={28}
        letterSpacing={5}
        fill={COLORS.muted}
        opacity={0}
      >
        {data.screenCopy.lead}
      </Txt>
      {data.screenCopy.cards.map(
        (
          card: {heading: string; body: string},
          index: number,
        ) => (
          <Rect
            ref={cards[index]}
            position={[305, -105 + index * 160]}
            size={[980, 126]}
            radius={28}
            fill={COLORS.panel}
            stroke={index === 1 ? COLORS.coral : COLORS.teal}
            lineWidth={2}
            opacity={0}
            scale={0.94}
            shadowColor={'rgba(0,0,0,0.45)'}
            shadowBlur={20}
          >
            <Rect
              position={[-410, 0]}
              size={[72, 72]}
              radius={22}
              fill={index === 1 ? COLORS.coral : COLORS.teal}
            >
              <Txt
                fontFamily={FONT}
                fontSize={24}
                fontWeight={800}
                fill={COLORS.bg}
              >
                {`0${index + 1}`}
              </Txt>
            </Rect>
            <Txt
              position={[-255, 0]}
              width={240}
              textAlign={'left'}
              fontFamily={FONT}
              fontSize={34}
              fontWeight={760}
              fill={COLORS.text}
            >
              {card.heading}
            </Txt>
            <Txt
              position={[195, 0]}
              width={540}
              textAlign={'left'}
              fontFamily={FONT}
              fontSize={25}
              fill={COLORS.muted}
            >
              {card.body}
            </Txt>
          </Rect>
        ),
      )}
      <Txt
        position={[305, 356]}
        width={980}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={20}
        letterSpacing={2}
        fill={'rgba(186,218,229,0.58)'}
      >
        {data.screenCopy.footer}
      </Txt>
    </>,
  );

  const stateRefs = [
    neutral,
    talking,
    blink,
    concerned,
    pointing,
    pointingTalking,
  ];

  const showState = (active: Reference<Img>) => {
    for (const ref of stateRefs) {
      ref().opacity(ref === active ? 1 : 0);
    }
  };

  function* runPresenterStates() {
    const blinkAt = [2.3, 5.8, 11.3, 20.5];
    const step = 0.14;
    let elapsed = 0;

    while (elapsed < duration) {
      const isBlink = blinkAt.some(
        (time) => Math.abs(time - elapsed) < step * 0.75,
      );
      const mouthOpen = Math.floor(elapsed / 0.18) % 2 === 1;

      if (isBlink) {
        showState(blink);
      } else if (elapsed >= 7.0 && elapsed < 8.2) {
        showState(concerned);
      } else if (elapsed >= 14.0 && elapsed < 19.0) {
        showState(mouthOpen ? pointingTalking : pointing);
      } else {
        showState(mouthOpen ? talking : neutral);
      }

      yield* waitFor(step);
      elapsed += step;
    }

    showState(neutral);
  }

  function* visuals() {
    yield* all(
      presenter().opacity(1, 0.45),
      presenter().scale(1, 0.55),
      title().opacity(1, 0.4),
      title().scale(1, 0.4),
    );
    yield* lead().opacity(1, 0.35);
    yield* chain(
      ...cards.map((card: Reference<Rect>) =>
        all(card().opacity(1, 0.38), card().scale(1, 0.38)),
      ),
    );
    yield* waitFor(Math.max(0, duration - 2.15));
  }

  yield* all(
    visuals(),
    runPresenterStates(),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

export default makeProject({
  scenes: [r01, r02],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: COLORS.bg,
    },
    rendering: {
      fps: 30,
    },
    preview: {
      fps: 30,
    },
  },
});
