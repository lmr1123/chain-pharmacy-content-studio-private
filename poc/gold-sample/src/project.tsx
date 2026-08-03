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

import storyboard from '../storyboard.json';
import timing from '../audio/timing.json';

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
  blue: '#27a9ff',
  coral: '#ff755b',
  amber: '#ffb347',
  text: '#f5fbff',
  muted: '#a7c3d5',
  panel: 'rgba(7, 27, 44, 0.88)',
  panelSoft: 'rgba(11, 42, 61, 0.78)',
  line: 'rgba(70, 224, 226, 0.42)',
};

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const sceneById = Object.fromEntries(
  storyboard.scenes.map((scene) => [scene.id, scene]),
) as Record<string, (typeof storyboard.scenes)[number]>;
const timingById = timing as Record<string, SceneTiming>;

const asset = (name: string) => `/assets/${name}`;
const audio = (id: string) => `/audio/${id}.m4a`;

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

function addChrome(view: View2D, activeChapter: string) {
  view.add(
    <>
      <Circle
        position={[-865, -482]}
        size={38}
        stroke={COLORS.teal}
        lineWidth={3}
      />
      <Circle position={[-865, -482]} size={12} fill={COLORS.teal} />
      <Txt
        position={[-700, -482]}
        width={280}
        textAlign={'left'}
        fontFamily={FONT}
        fontSize={28}
        fontWeight={600}
        fill={COLORS.text}
      >
        内部健康课堂
      </Txt>
      <Txt
        position={[755, -482]}
        width={300}
        textAlign={'right'}
        fontFamily={FONT}
        fontSize={20}
        letterSpacing={4}
        fill={'rgba(189,226,239,0.58)'}
      >
        KNOWLEDGE STUDIO
      </Txt>
    </>,
  );

  const chapters = storyboard.chapters;
  const itemWidth = 350;
  const startX = -525;

  chapters.forEach((chapter, index) => {
    const active = chapter === activeChapter;
    view.add(
      <Rect
        position={[startX + itemWidth * index, 505]}
        size={[itemWidth - 18, 54]}
        radius={12}
        fill={active ? 'rgba(31,207,211,0.2)' : 'rgba(4,17,31,0.62)'}
        stroke={active ? COLORS.teal : 'rgba(88,138,159,0.24)'}
        lineWidth={active ? 2 : 1}
      >
        <Txt
          fontFamily={FONT}
          fontSize={22}
          fontWeight={active ? 700 : 400}
          fill={active ? COLORS.tealSoft : 'rgba(191,214,224,0.62)'}
        >
          {chapter}
        </Txt>
      </Rect>,
    );
  });
}

function addSubtitle(view: View2D) {
  const textRef = createRef<Txt>();
  view.add(
    <>
      <Rect
        position={[0, 430]}
        size={[1540, 66]}
        radius={18}
        fill={'rgba(0,7,15,0.74)'}
        stroke={'rgba(59,220,224,0.2)'}
        lineWidth={1}
      />
      <Txt
        ref={textRef}
        position={[0, 430]}
        width={1460}
        textWrap={true}
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
    yield* ref().opacity(1, 0.1);
    const readable = Math.max(0.05, cue.end - cue.start - 0.1);
    yield* waitFor(readable);
    cursor = cue.end;
  }
  if (duration > cursor) {
    yield* waitFor(duration - cursor);
  }
}

function* runTalking(
  neutral: Reference<Img>,
  talking: Reference<Img>,
  duration: number,
) {
  let elapsed = 0;
  while (elapsed < duration) {
    neutral().opacity(1);
    talking().opacity(0);
    yield* waitFor(0.13);
    elapsed += 0.13;
    neutral().opacity(0);
    talking().opacity(1);
    yield* waitFor(0.18);
    elapsed += 0.18;
  }
}

function addSceneAudio(view: View2D, id: string) {
  view.add(<Audio src={audio(id)} play={true} />);
}

function addSectionTitle(
  view: View2D,
  text: string,
  eyebrow: string,
  position: [number, number] = [0, -372],
) {
  const ref = createRef<Rect>();
  view.add(
    <Rect
      ref={ref}
      position={position}
      opacity={0}
      scale={0.94}
      layout
      direction={'column'}
      gap={8}
      alignItems={'center'}
    >
      <Txt
        fontFamily={FONT}
        fontSize={21}
        fontWeight={600}
        letterSpacing={5}
        fill={COLORS.teal}
      >
        {eyebrow}
      </Txt>
      <Txt
        fontFamily={FONT}
        fontSize={54}
        fontWeight={760}
        fill={COLORS.text}
      >
        {text}
      </Txt>
    </Rect>,
  );
  return ref;
}

const s01 = makeScene2D('s01-tech-title', function* (view) {
  const id = 's01';
  const data = sceneById[id];
  const duration = timingById[id].duration + 0.45;
  const bg = addBackground(view, 0);
  addSceneAudio(view, id);

  const ring1 = createRef<Circle>();
  const ring2 = createRef<Circle>();
  const title = createRef<Txt>();
  const eyebrow = createRef<Txt>();
  const sub = createRef<Txt>();
  const line = createRef<Line>();
  const subtitle = addSubtitle(view);

  view.add(
    <>
      <Circle
        ref={ring1}
        position={[465, 10]}
        size={360}
        stroke={'rgba(38,222,228,0.52)'}
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
        stroke={'rgba(255,117,91,0.62)'}
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
        GOLD SAMPLE · 01
      </Txt>
    </>,
  );

  function* visuals() {
    yield* all(bg().opacity(1, 0.45), ring1().opacity(1, 0.5));
    yield* all(
      ring1().scale(1, 0.65),
      ring1().rotation(38, 1.2),
      ring2().opacity(1, 0.5),
      eyebrow().opacity(1, 0.45),
    );
    yield* all(title().opacity(1, 0.55), title().scale(1, 0.55));
    yield* all(line().end(1, 0.65), sub().opacity(1, 0.65));
    yield* waitFor(Math.max(0, duration - 2.95));
  }

  yield* all(
    visuals(),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

const s02 = makeScene2D('s02-presenter-hook', function* (view) {
  const id = 's02';
  const data = sceneById[id];
  const duration = timingById[id].duration + 0.45;
  const bg = addBackground(view, 0.92);
  addChrome(view, data.chapter);
  addSceneAudio(view, id);
  const title = addSectionTitle(view, data.screenCopy.title, 'TYPICAL SIGNALS');
  const subtitle = addSubtitle(view);

  const neutral = createRef<Img>();
  const talking = createRef<Img>();
  const hero = createRef<Rect>();
  const tagRefs = data.screenCopy.tags.map(() => createRef<Rect>());

  view.add(
    <>
      <Img
        ref={neutral}
        src={asset('pharmacist-neutral.png')}
        position={[-650, 46]}
        size={[320, 720]}
        opacity={0}
      />
      <Img
        ref={talking}
        src={asset('pharmacist-talking.png')}
        position={[-650, 46]}
        size={[320, 720]}
        opacity={0}
      />
      <Rect
        ref={hero}
        position={[330, 48]}
        size={[1040, 575]}
        radius={34}
        clip
        stroke={'rgba(56,223,227,0.55)'}
        lineWidth={2}
        opacity={0}
        scale={0.96}
        shadowColor={'rgba(0,0,0,0.55)'}
        shadowBlur={24}
      >
        <Img src={asset('symptom-triptych.png')} size={[1040, 585]} />
        <Rect
          size={[1040, 585]}
          fill={'rgba(0,14,26,0.16)'}
        />
      </Rect>
      {data.screenCopy.tags.map((tag, index) => {
        const positions: [number, number][] = [
          [70, -155],
          [410, -155],
          [735, -155],
          [250, 200],
          [600, 200],
        ];
        return (
          <Rect
            ref={tagRefs[index]}
            position={positions[index]}
            size={[270, 66]}
            radius={18}
            fill={'rgba(2,18,31,0.86)'}
            stroke={index < 3 ? COLORS.teal : COLORS.coral}
            lineWidth={2}
            opacity={0}
            scale={0.84}
          >
            <Txt
              fontFamily={FONT}
              fontSize={27}
              fontWeight={650}
              fill={COLORS.text}
            >
              {tag}
            </Txt>
          </Rect>
        );
      })}
    </>,
  );

  function* visuals() {
    yield* all(
      title().opacity(1, 0.4),
      title().scale(1, 0.4),
      neutral().opacity(1, 0.45),
      hero().opacity(1, 0.5),
      hero().scale(1, 0.5),
    );
    yield* chain(
      ...tagRefs.map((ref) =>
        all(ref().opacity(1, 0.24), ref().scale(1, 0.24)),
      ),
    );
    yield* waitFor(Math.max(0, duration - 2.1));
  }

  yield* all(
    visuals(),
    runTalking(neutral, talking, duration),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

const s03 = makeScene2D('s03-mechanism-flow', function* (view) {
  const id = 's03';
  const data = sceneById[id];
  const duration = timingById[id].duration + 0.45;
  addSceneAudio(view, id);
  const background = createRef<Img>();
  view.add(
    <>
      <Img
        ref={background}
        src={asset('mechanism-body.png')}
        size={[1920, 1080]}
        opacity={0}
        scale={1.04}
      />
      <Rect size={[1920, 1080]} fill={'rgba(0,8,18,0.1)'} />
    </>,
  );
  addChrome(view, data.chapter);
  const title = addSectionTitle(
    view,
    data.screenCopy.title,
    'MECHANISM',
    [0, -400],
  );
  const subtitle = addSubtitle(view);
  const wind = createRef<Rect>();
  const heat = createRef<Rect>();
  const pulse = createRef<Circle>();
  const nodeRefs = data.screenCopy.nodes.map(() => createRef<Rect>());

  view.add(
    <>
      <Rect
        ref={wind}
        position={[-650, -60]}
        size={[240, 88]}
        radius={44}
        fill={'rgba(9,82,132,0.78)'}
        stroke={COLORS.blue}
        lineWidth={3}
        opacity={0}
        scale={0.75}
      >
        <Txt
          fontFamily={FONT}
          fontSize={40}
          fontWeight={760}
          fill={COLORS.text}
        >
          风邪
        </Txt>
      </Rect>
      <Rect
        ref={heat}
        position={[650, -60]}
        size={[240, 88]}
        radius={44}
        fill={'rgba(118,44,25,0.76)'}
        stroke={COLORS.coral}
        lineWidth={3}
        opacity={0}
        scale={0.75}
      >
        <Txt
          fontFamily={FONT}
          fontSize={40}
          fontWeight={760}
          fill={COLORS.text}
        >
          热邪
        </Txt>
      </Rect>
      <Circle
        ref={pulse}
        position={[0, -35]}
        size={178}
        stroke={'rgba(255,255,255,0.75)'}
        lineWidth={5}
        opacity={0}
        scale={0.5}
      />
      {data.screenCopy.nodes.map((node, index) => (
        <Rect
          ref={nodeRefs[index]}
          position={[-520 + index * 260, 315]}
          size={[220, 68]}
          radius={18}
          fill={'rgba(3,19,32,0.84)'}
          stroke={
            index < 2
              ? index === 0
                ? COLORS.blue
                : COLORS.coral
              : COLORS.teal
          }
          lineWidth={2}
          opacity={0}
        >
          <Txt
            fontFamily={FONT}
            fontSize={25}
            fontWeight={650}
            fill={COLORS.text}
          >
            {node}
          </Txt>
        </Rect>
      ))}
    </>,
  );

  function* visuals() {
    yield* all(
      background().opacity(1, 0.65),
      background().scale(1, 1.2),
      title().opacity(1, 0.45),
      title().scale(1, 0.45),
    );
    yield* all(
      wind().opacity(1, 0.4),
      wind().scale(1, 0.4),
      heat().opacity(1, 0.4),
      heat().scale(1, 0.4),
    );
    yield* all(pulse().opacity(0.8, 0.4), pulse().scale(1.3, 0.9));
    yield* chain(
      ...nodeRefs.map((ref) => ref().opacity(1, 0.22)),
    );
    yield* waitFor(Math.max(0, duration - 2.8));
  }

  yield* all(
    visuals(),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

const s04 = makeScene2D('s04-three-signals', function* (view) {
  const id = 's04';
  const data = sceneById[id];
  const duration = timingById[id].duration + 0.45;
  addBackground(view, 0.96);
  addChrome(view, data.chapter);
  addSceneAudio(view, id);
  const title = addSectionTitle(view, data.screenCopy.title, 'THREE SIGNALS');
  const subtitle = addSubtitle(view);
  const cardRefs = data.screenCopy.cards.map(() => createRef<Rect>());
  const images = [
    'symptom-fever.png',
    'symptom-cough.png',
    'symptom-throat.png',
  ];

  view.add(
    <>
      {data.screenCopy.cards.map((card, index) => (
        <Rect
          ref={cardRefs[index]}
          position={[-560 + index * 560, 55]}
          size={[490, 620]}
          radius={34}
          clip
          fill={COLORS.panel}
          stroke={index === 1 ? COLORS.coral : COLORS.teal}
          lineWidth={2}
          opacity={0}
          scale={0.9}
          shadowColor={'rgba(0,0,0,0.55)'}
          shadowBlur={24}
        >
          <Rect
            position={[0, -110]}
            size={[490, 400]}
            clip
          >
            <Img
              src={asset(images[index])}
              size={[490, 828]}
              position={[0, index === 1 ? 40 : 0]}
            />
            <Rect
              size={[490, 400]}
              fill={'rgba(0,11,21,0.08)'}
            />
          </Rect>
          <Rect
            position={[-178, -245]}
            size={[92, 46]}
            radius={23}
            fill={index === 1 ? COLORS.coral : COLORS.teal}
          >
            <Txt
              fontFamily={FONT}
              fontSize={23}
              fontWeight={800}
              fill={COLORS.bg}
            >
              {card.number}
            </Txt>
          </Rect>
          <Txt
            position={[0, 170]}
            width={410}
            fontFamily={FONT}
            fontSize={34}
            fontWeight={750}
            fill={COLORS.text}
          >
            {card.heading}
          </Txt>
          <Txt
            position={[0, 235]}
            width={410}
            textWrap={true}
            fontFamily={FONT}
            fontSize={25}
            lineHeight={40}
            fill={COLORS.muted}
          >
            {card.body}
          </Txt>
        </Rect>
      ))}
    </>,
  );

  function* visuals() {
    yield* all(title().opacity(1, 0.4), title().scale(1, 0.4));
    yield* chain(
      ...cardRefs.map((ref) =>
        all(ref().opacity(1, 0.38), ref().scale(1, 0.38)),
      ),
    );
    yield* waitFor(Math.max(0, duration - 1.8));
  }

  yield* all(
    visuals(),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

const s05 = makeScene2D('s05-botanicals', function* (view) {
  const id = 's05';
  const data = sceneById[id] as any;
  const botanicalItems = data.screenCopy.items as Array<{
    heading: string;
    sub: string;
  }>;
  const duration = timingById[id].duration + 0.45;
  addBackground(view, 0.97);
  addChrome(view, data.chapter);
  addSceneAudio(view, id);
  const title = addSectionTitle(view, data.screenCopy.title, 'DAILY SUPPORT');
  const subtitle = addSubtitle(view);
  const neutral = createRef<Img>();
  const talking = createRef<Img>();
  const cardRefs = botanicalItems.map(() => createRef<Rect>());
  const images = [
    'botanical-mulberry.png',
    'botanical-chrysanthemum.png',
    'botanical-mint.png',
  ];
  const note = createRef<Rect>();

  view.add(
    <>
      <Img
        ref={neutral}
        src={asset('pharmacist-pointing.png')}
        position={[-725, 85]}
        size={[297, 670]}
        opacity={0}
      />
      <Img
        ref={talking}
        src={asset('pharmacist-pointing-talking.png')}
        position={[-725, 85]}
        size={[297, 670]}
        opacity={0}
      />
      {botanicalItems.map((item, index) => (
        <Rect
          ref={cardRefs[index]}
          position={[-285 + index * 410, 20]}
          size={[350, 535]}
          radius={30}
          clip
          fill={COLORS.panel}
          stroke={'rgba(69,229,219,0.54)'}
          lineWidth={2}
          opacity={0}
          scale={0.88}
        >
          <Rect position={[0, -80]} size={[350, 375]} clip>
            <Img src={asset(images[index])} size={[350, 591]} />
          </Rect>
          <Txt
            position={[0, 154]}
            width={290}
            fontFamily={FONT}
            fontSize={36}
            fontWeight={760}
            fill={COLORS.text}
          >
            {item.heading}
          </Txt>
          <Rect
            position={[0, 214]}
            size={[138, 42]}
            radius={21}
            fill={'rgba(45,226,230,0.16)'}
            stroke={COLORS.teal}
            lineWidth={1}
          >
            <Txt
              fontFamily={FONT}
              fontSize={21}
              fontWeight={650}
              fill={COLORS.tealSoft}
            >
              {item.sub}
            </Txt>
          </Rect>
        </Rect>
      ))}
      <Rect
        ref={note}
        position={[330, 335]}
        size={[980, 70]}
        radius={22}
        fill={'rgba(6,25,40,0.9)'}
        stroke={COLORS.teal}
        lineWidth={2}
        opacity={0}
      >
        <Txt
          fontFamily={FONT}
          fontSize={28}
          fontWeight={650}
          letterSpacing={3}
          fill={COLORS.text}
        >
          {data.screenCopy.note}
        </Txt>
      </Rect>
    </>,
  );

  function* visuals() {
    yield* all(
      title().opacity(1, 0.4),
      title().scale(1, 0.4),
      neutral().opacity(1, 0.45),
    );
    yield* chain(
      ...cardRefs.map((ref) =>
        all(ref().opacity(1, 0.35), ref().scale(1, 0.35)),
      ),
    );
    yield* note().opacity(1, 0.45);
    yield* waitFor(Math.max(0, duration - 2.2));
  }

  yield* all(
    visuals(),
    runTalking(neutral, talking, duration),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

const s06 = makeScene2D('s06-summary', function* (view) {
  const id = 's06';
  const data = sceneById[id] as any;
  const summaryItems = data.screenCopy.items as Array<{
    heading: string;
    body: string;
  }>;
  const duration = timingById[id].duration + 0.6;
  addBackground(view, 1);
  addChrome(view, data.chapter);
  addSceneAudio(view, id);
  const title = addSectionTitle(view, data.screenCopy.title, 'SUMMARY');
  const subtitle = addSubtitle(view);
  const neutral = createRef<Img>();
  const talking = createRef<Img>();
  const itemRefs = summaryItems.map(() => createRef<Rect>());
  const footer = createRef<Txt>();

  view.add(
    <>
      <Img
        ref={neutral}
        src={asset('pharmacist-neutral.png')}
        position={[710, 75]}
        size={[302, 680]}
        opacity={0}
      />
      <Img
        ref={talking}
        src={asset('pharmacist-talking.png')}
        position={[710, 75]}
        size={[302, 680]}
        opacity={0}
      />
      {summaryItems.map((item, index) => {
        const positions: [number, number][] = [
          [-520, -90],
          [-80, -90],
          [-520, 185],
          [-80, 185],
        ];
        const accent = index === 1 ? COLORS.coral : COLORS.teal;
        return (
          <Rect
            ref={itemRefs[index]}
            position={positions[index]}
            size={[390, 215]}
            radius={30}
            fill={COLORS.panelSoft}
            stroke={accent}
            lineWidth={2}
            opacity={0}
            scale={0.9}
          >
            <Rect
              position={[-145, -74]}
              size={[74, 34]}
              radius={17}
              fill={accent}
            >
              <Txt
                fontFamily={FONT}
                fontSize={18}
                fontWeight={800}
                fill={COLORS.bg}
              >
                {`0${index + 1}`}
              </Txt>
            </Rect>
            <Txt
              position={[0, -30]}
              width={330}
              fontFamily={FONT}
              fontSize={34}
              fontWeight={760}
              fill={COLORS.text}
            >
              {item.heading}
            </Txt>
            <Txt
              position={[0, 50]}
              width={330}
              textWrap={true}
              fontFamily={FONT}
              fontSize={25}
              lineHeight={38}
              fill={COLORS.muted}
            >
              {item.body}
            </Txt>
          </Rect>
        );
      })}
      <Txt
        ref={footer}
        position={[-300, 338]}
        width={870}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={22}
        letterSpacing={2}
        fill={'rgba(186,218,229,0.62)'}
        opacity={0}
      >
        {data.screenCopy.footer}
      </Txt>
    </>,
  );

  function* visuals() {
    yield* all(
      title().opacity(1, 0.4),
      title().scale(1, 0.4),
      neutral().opacity(1, 0.45),
    );
    yield* chain(
      ...itemRefs.map((ref) =>
        all(ref().opacity(1, 0.3), ref().scale(1, 0.3)),
      ),
    );
    yield* footer().opacity(1, 0.4);
    yield* waitFor(Math.max(0, duration - 2.15));
  }

  yield* all(
    visuals(),
    runTalking(neutral, talking, duration),
    runSubtitles(subtitle, timingById[id].cues, duration),
  );
});

export default makeProject({
  scenes: [s01, s02, s03, s04, s05, s06],
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
