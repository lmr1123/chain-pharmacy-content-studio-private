/**
 * 可可康绿色金样 production-v2 · 58 微镜头结构 Animatic
 *
 * 严格按 handoff-v2/microshot-timeline.json 顺序与时长实现。
 * 章节不是页面：每个微镜头有独立 entry / performance / exit 与非文字层运动。
 * 静音结构验证；正式旁白仅允许 production_ready 镜头（K08 三镜）。
 */
import {
  Audio,
  Circle,
  Img,
  Line,
  Rect,
  Txt,
  makeScene2D,
} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeInOutCubic,
  easeOutBack,
  easeOutCubic,
  easeInCubic,
  makeProject,
  waitFor,
} from '@revideo/core';

import timeline from './kekang-v2/microshot-timeline.json';
import {gateLabel, isBlocked, nodeLabels} from './kekang-v2/labels';
import type {Microshot, SharedVisualState} from './kekang-v2/types';
import {
  AUDIENCE,
  CREAM,
  FONT,
  GANODERMA,
  GOLD,
  GREEN,
  GREEN_DARK,
  GREEN_DEEP,
  INK,
  LOGO_CANDIDATE,
  MINT,
  MINT_STRONG,
  MUTED,
  SILENCE,
  WARN,
  WARN_BG,
  WHITE,
} from './kekang-v2/theme';

type R<T> = Reference<T>;

const microshots: Microshot[] = (timeline as {chapters: {microshots: Microshot[]}[]}).chapters.flatMap(
  (c) => c.microshots,
);
const TOTAL = microshots.reduce((s, m) => s + m.duration_seconds, 0);

type PersonKind = 'young' | 'middle' | 'elder' | null;

function personKindFor(shot: Microshot): PersonKind {
  const id = shot.id;
  const sub = shot.subtitle + shot.focal_subject + shot.visual_action;
  if (id.startsWith('K02-S01') || id.startsWith('K03') || sub.includes('失眠') || sub.includes('夜'))
    return 'young';
  if (id.startsWith('K02-S02') || id.startsWith('K04') || sub.includes('饮酒') || sub.includes('肝'))
    return 'middle';
  if (id.startsWith('K02-S03') || id.startsWith('K05') || sub.includes('免疫') || sub.includes('季节'))
    return 'elder';
  if (id.startsWith('K16-S01') || id.startsWith('K16-S02')) return 'young';
  if (id.startsWith('K16-S03') || id.startsWith('K16-S04')) return 'middle';
  if (id.startsWith('K16-S05') || id.startsWith('K16-S06')) return 'elder';
  return null;
}

const scene = makeScene2D('kekang-pfizer-v2-animatic', function* (view) {
  // Layer pool
  const stage = createRef<Rect>();
  const mintBlob = createRef<Circle>();
  const goldBlob = createRef<Circle>();
  const envWave = createRef<Line>();
  const heroHalo = createRef<Circle>();
  const heroOrbit = createRef<Circle>();
  const heroFrame = createRef<Rect>();
  const heroImg = createRef<Img>();
  const heroSlot = createRef<Rect>();
  const pathA = createRef<Line>();
  const pathB = createRef<Line>();
  const pathArc = createRef<Line>();
  const processPath = createRef<Line>();
  const token = createRef<Circle>();
  const focusRing = createRef<Circle>();
  const lockBadge = createRef<Rect>();
  const shotIdTxt = createRef<Txt>();
  const titleTxt = createRef<Txt>();
  const focusTxt = createRef<Txt>();
  const subtitleBar = createRef<Rect>();
  const subtitleTxt = createRef<Txt>();
  const gateChip = createRef<Rect>();
  const gateTxt = createRef<Txt>();
  const progress = createRef<Line>();
  const logo = createRef<Img>();
  const personYoung = createRef<Img>();
  const personMiddle = createRef<Img>();
  const personElder = createRef<Img>();
  const calendar = [0, 1, 2].map(() => createRef<Rect>());
  const calTxt = [0, 1, 2].map(() => createRef<Txt>());
  const nodes = [0, 1, 2, 3, 4, 5].map(() => createRef<Rect>());
  const nodeTxt = [0, 1, 2, 3, 4, 5].map(() => createRef<Txt>());
  const pairA = createRef<Rect>();
  const pairB = createRef<Rect>();
  const pairATxt = createRef<Txt>();
  const pairBTxt = createRef<Txt>();
  const relation = createRef<Circle>();
  const evidenceBox = createRef<Rect>();
  const evidenceTxt = createRef<Txt>();

  view.add(
    <>
      <Audio src={SILENCE} play />
      <Rect ref={stage} size={[1920, 1080]} fill={CREAM} scale={1}>
        <Circle ref={mintBlob} position={[800, -420]} size={860} fill={MINT} opacity={0.7} />
        <Circle ref={goldBlob} position={[-840, 460]} size={720} fill={'#f4ead1'} opacity={0.5} />
        <Line
          ref={envWave}
          points={[
            [-960, 390],
            [-400, 250],
            [100, 310],
            [520, 180],
            [960, 260],
          ]}
          stroke={'rgba(7,134,63,0.10)'}
          lineWidth={56}
          radius={80}
        />

        <Txt
          position={[-640, -492]}
          text={'大参林内部培训 · production-v2 微镜头结构 Animatic'}
          fontFamily={FONT}
          fontSize={24}
          fontWeight={720}
          fill={GREEN_DARK}
        />
        <Txt
          ref={shotIdTxt}
          position={[780, -492]}
          text={'K01-S01'}
          fontFamily={FONT}
          fontSize={24}
          fontWeight={780}
          fill={MUTED}
        />

        <Circle ref={heroHalo} position={[0, 40]} size={420} fill={MINT_STRONG} opacity={0} scale={0.6} />
        <Circle
          ref={heroOrbit}
          position={[0, 40]}
          size={500}
          stroke={'rgba(7,134,63,0.35)'}
          lineWidth={4}
          lineDash={[14, 16]}
          opacity={0}
          scale={0.85}
        />
        <Rect
          ref={heroFrame}
          position={[0, 40]}
          size={[300, 300]}
          radius={150}
          fill={WHITE}
          stroke={WHITE}
          lineWidth={12}
          clip
          opacity={0}
          scale={0.72}
          shadowColor={'rgba(16,63,45,0.16)'}
          shadowBlur={28}
        >
          <Img ref={heroImg} src={GANODERMA} size={[300, 300]} scale={1.06} />
        </Rect>
        <Rect
          ref={heroSlot}
          position={[0, 40]}
          size={[260, 320]}
          radius={28}
          fill={'rgba(255,255,255,0.55)'}
          stroke={GREEN}
          lineWidth={3}
          lineDash={[10, 10]}
          opacity={0}
        >
          <Txt text={'授权包装空槽'} fontFamily={FONT} fontSize={28} fontWeight={700} fill={MUTED} />
        </Rect>

        <Img
          ref={personYoung}
          src={AUDIENCE.young}
          position={[-420, 40]}
          size={[280, 420]}
          opacity={0}
          scale={0.9}
        />
        <Img
          ref={personMiddle}
          src={AUDIENCE.middle}
          position={[-420, 40]}
          size={[280, 420]}
          opacity={0}
          scale={0.9}
        />
        <Img
          ref={personElder}
          src={AUDIENCE.elder}
          position={[-420, 40]}
          size={[280, 420]}
          opacity={0}
          scale={0.9}
        />

        <Line
          ref={pathA}
          points={[
            [-140, 20],
            [-360, -90],
            [-560, -90],
          ]}
          stroke={GREEN}
          lineWidth={7}
          radius={20}
          end={0}
        />
        <Line
          ref={pathB}
          points={[
            [140, 80],
            [360, 200],
            [560, 200],
          ]}
          stroke={GOLD}
          lineWidth={7}
          radius={20}
          end={0}
        />
        <Line
          ref={pathArc}
          points={[
            [-520, 160],
            [-200, -40],
            [200, -40],
            [520, 160],
          ]}
          stroke={'rgba(7,134,63,0.45)'}
          lineWidth={5}
          radius={40}
          lineDash={[12, 12]}
          end={0}
        />
        <Line
          ref={processPath}
          points={[
            [-620, 120],
            [-240, -40],
            [160, -40],
            [560, 120],
          ]}
          stroke={GREEN}
          lineWidth={6}
          radius={28}
          end={0}
        />
        <Circle ref={token} position={[-620, 120]} size={36} fill={GOLD} opacity={0} />
        <Circle
          ref={focusRing}
          position={[0, 40]}
          size={120}
          stroke={GREEN}
          lineWidth={5}
          opacity={0}
        />

        {[0, 1, 2, 3, 4, 5].map((i) => (
          <Rect
            key={`n${i}`}
            ref={nodes[i]}
            position={[-500 + i * 200, 260]}
            size={[180, 96]}
            radius={48}
            fill={WHITE}
            stroke={GREEN}
            lineWidth={3}
            opacity={0}
            scale={0.8}
            shadowColor={'rgba(16,63,45,0.12)'}
            shadowBlur={16}
          >
            <Txt
              ref={nodeTxt[i]}
              width={150}
              text={''}
              fontFamily={FONT}
              fontSize={24}
              fontWeight={760}
              fill={INK}
              textAlign={'center'}
            />
          </Rect>
        ))}

        {[0, 1, 2].map((i) => (
          <Rect
            key={`c${i}`}
            ref={calendar[i]}
            position={[-280 + i * 280, 80]}
            size={[220, 240]}
            radius={24}
            fill={WHITE}
            stroke={GREEN}
            lineWidth={4}
            opacity={0}
            scale={0.85}
          >
            <Txt
              ref={calTxt[i]}
              position={[0, -70]}
              text={`${i + 1} 月`}
              fontFamily={FONT}
              fontSize={40}
              fontWeight={820}
              fill={GREEN_DEEP}
            />
            <Txt
              position={[0, 40]}
              text={'月历推进'}
              fontFamily={FONT}
              fontSize={22}
              fontWeight={650}
              fill={MUTED}
            />
          </Rect>
        ))}

        <Rect
          ref={pairA}
          position={[-360, 120]}
          size={[260, 160]}
          radius={24}
          fill={WHITE}
          stroke={GREEN}
          lineWidth={3}
          lineDash={[8, 8]}
          opacity={0}
        >
          <Txt ref={pairATxt} text={'商品 A 空槽'} fontFamily={FONT} fontSize={28} fontWeight={740} fill={MUTED} />
        </Rect>
        <Rect
          ref={pairB}
          position={[360, 120]}
          size={[260, 160]}
          radius={24}
          fill={WHITE}
          stroke={GOLD}
          lineWidth={3}
          lineDash={[8, 8]}
          opacity={0}
        >
          <Txt ref={pairBTxt} text={'商品 B 空槽'} fontFamily={FONT} fontSize={28} fontWeight={740} fill={MUTED} />
        </Rect>
        <Circle
          ref={relation}
          position={[0, 120]}
          size={72}
          fill={MINT_STRONG}
          stroke={GREEN}
          lineWidth={3}
          opacity={0}
        />
        <Txt
          position={[0, 120]}
          text={'+'}
          fontFamily={FONT}
          fontSize={36}
          fontWeight={800}
          fill={GREEN_DEEP}
          opacity={0}
        />

        <Rect
          ref={evidenceBox}
          position={[420, -40]}
          size={[280, 120]}
          radius={18}
          fill={WHITE}
          stroke={GOLD}
          lineWidth={4}
          opacity={0}
          scale={0.9}
        >
          <Txt ref={evidenceTxt} text={'证据位'} fontFamily={FONT} fontSize={30} fontWeight={780} fill={INK} />
        </Rect>

        <Rect
          ref={lockBadge}
          position={[0, -180]}
          size={[220, 56]}
          radius={28}
          fill={WARN_BG}
          stroke={WARN}
          lineWidth={3}
          opacity={0}
        >
          <Txt text={'待审核锁定'} fontFamily={FONT} fontSize={24} fontWeight={780} fill={WARN} />
        </Rect>

        <Txt
          ref={titleTxt}
          position={[-520, -360]}
          width={900}
          textAlign={'left'}
          text={''}
          fontFamily={FONT}
          fontSize={52}
          fontWeight={860}
          fill={GREEN_DEEP}
          opacity={0}
        />
        <Txt
          ref={focusTxt}
          position={[-520, -290]}
          width={900}
          textAlign={'left'}
          text={''}
          fontFamily={FONT}
          fontSize={28}
          fontWeight={620}
          fill={MUTED}
          opacity={0}
        />

        <Rect
          ref={gateChip}
          position={[760, -340]}
          size={[280, 52]}
          radius={26}
          fill={WARN_BG}
          stroke={WARN}
          lineWidth={3}
          opacity={0}
        >
          <Txt ref={gateTxt} text={'BLOCKED'} fontFamily={FONT} fontSize={24} fontWeight={800} fill={WARN} />
        </Rect>

        <Img ref={logo} src={LOGO_CANDIDATE} position={[780, 430]} size={[160, 48]} opacity={0} />

        <Rect
          ref={subtitleBar}
          position={[0, 470]}
          size={[880, 58]}
          radius={16}
          fill={'rgba(16,63,45,0.78)'}
          opacity={0}
        />
        <Txt
          ref={subtitleTxt}
          position={[0, 470]}
          width={820}
          text={''}
          fontFamily={FONT}
          fontSize={36}
          fontWeight={720}
          fill={WHITE}
          textAlign={'center'}
          opacity={0}
        />

        <Rect position={[0, 520]} size={[1600, 8]} radius={4} fill={'rgba(16,63,45,0.08)'} />
        <Line
          ref={progress}
          points={[
            [-800, 520],
            [800, 520],
          ]}
          stroke={GREEN}
          lineWidth={8}
          end={0}
          lineCap={'round'}
        />
      </Rect>
    </>,
  );

  const hideAllNodes = () => {
    for (let i = 0; i < 6; i++) {
      nodes[i]().opacity(0);
      nodes[i]().scale(0.8);
    }
  };
  const hidePairs = () => {
    pairA().opacity(0);
    pairB().opacity(0);
    relation().opacity(0);
  };
  const hideCal = () => {
    for (let i = 0; i < 3; i++) calendar[i]().opacity(0);
  };

  let elapsed = 0;
  const state: SharedVisualState = {
    accent: GREEN,
    heroX: 0,
    heroY: 40,
    heroScale: 1,
    pathProgress: 0,
  };

  for (let si = 0; si < microshots.length; si++) {
    const shot = microshots[si];
    const d = shot.duration_seconds;
    const tEntry = d * 0.28;
    const tPerf = d * 0.48;
    const tExit = d * 0.24;
    const blocked = isBlocked(shot);
    const labels = nodeLabels(shot.subtitle, 6);
    const recipe = shot.recipe_id;
    const pKind = personKindFor(shot);
    const personRef = () =>
      pKind === 'middle'
        ? personMiddle()
        : pKind === 'elder'
          ? personElder()
          : personYoung();

    // chrome
    shotIdTxt().text(`${shot.id} · ${si + 1}/${microshots.length}`);
    titleTxt().text(shot.focal_subject);
    focusTxt().text(shot.visual_action.slice(0, 42));
    subtitleTxt().text(shot.subtitle);
    gateTxt().text(blocked ? gateLabel(shot) : 'READY');
    gateTxt().fill(blocked ? WARN : GREEN);
    gateChip().stroke(blocked ? WARN : GREEN);
    gateChip().fill(blocked ? WARN_BG : MINT);
    lockBadge().opacity(0);

    // reset common
    hideAllNodes();
    hidePairs();
    hideCal();
    pathA().end(0);
    pathB().end(0);
    pathArc().end(0);
    processPath().end(0);
    token().opacity(0);
    personYoung().opacity(0);
    personMiddle().opacity(0);
    personElder().opacity(0);
    heroFrame().opacity(0);
    heroSlot().opacity(0);
    heroHalo().opacity(0);
    heroOrbit().opacity(0);
    evidenceBox().opacity(0);
    logo().opacity(0);
    focusRing().opacity(0);
    titleTxt().opacity(0);
    focusTxt().opacity(0);
    subtitleBar().opacity(0);
    subtitleTxt().opacity(0);
    gateChip().opacity(0);

    // camera mild reset
    stage().scale(1);
    stage().position([0, 0]);

    // place nodes from labels
    const nCount = Math.min(6, Math.max(2, labels.length));
    const spacing = nCount <= 3 ? 300 : nCount <= 4 ? 240 : 200;
    const startX = -((nCount - 1) * spacing) / 2;
    for (let i = 0; i < nCount; i++) {
      nodeTxt[i]().text(labels[i] || `节点 ${i + 1}`);
      nodes[i]().position([startX + i * spacing, 250]);
      nodes[i]().stroke(i === 1 && recipe.includes('R04') ? GOLD : GREEN);
    }

    // ENTRY (chrome + recipe share tEntry exactly via parallel all + one recipe block)
    const chromeIn = all(
      titleTxt().opacity(1, Math.min(0.28, tEntry * 0.45)),
      focusTxt().opacity(1, Math.min(0.28, tEntry * 0.45)),
      gateChip().opacity(1, Math.min(0.22, tEntry * 0.35)),
      subtitleBar().opacity(1, Math.min(0.2, tEntry * 0.3)),
      subtitleTxt().opacity(1, Math.min(0.2, tEntry * 0.3)),
      mintBlob().opacity(0.7, Math.min(0.22, tEntry * 0.35)),
      goldBlob().opacity(0.5, Math.min(0.22, tEntry * 0.35)),
    );

    if (recipe.startsWith('R01')) {
      // hero reveal
      const useSlot = !shot.production_ready && shot.asset_ids.some((a) => a.includes('packshot') || a.includes('logo'));
      if (useSlot && shot.id !== 'K01-S01') {
        heroSlot().position([state.heroX, state.heroY]);
        yield* all(
          chromeIn,
          heroSlot().opacity(1, tEntry * 0.55),
          heroSlot().scale(1, tEntry * 0.7, easeOutBack),
          heroHalo().opacity(0.9, tEntry * 0.45),
          heroHalo().scale(1, tEntry * 0.65, easeOutCubic),
        );
      } else {
        heroFrame().position([state.heroX, state.heroY]);
        heroHalo().position([state.heroX, state.heroY]);
        heroOrbit().position([state.heroX, state.heroY]);
        heroFrame().scale(0.72);
        yield* all(
          chromeIn,
          heroHalo().opacity(1, tEntry * 0.45),
          heroHalo().scale(1, tEntry * 0.7, easeOutCubic),
          heroOrbit().opacity(1, tEntry * 0.5),
          heroOrbit().scale(1, tEntry * 0.7, easeOutCubic),
          heroFrame().opacity(1, tEntry * 0.4),
          heroFrame().scale(1, tEntry * 0.75, easeOutBack),
        );
      }
    } else if (recipe.startsWith('R02')) {
      personRef().position([-380, 30]);
      personRef().scale(0.88);
      personRef().size([280, 420]);
      focusRing().position([-340, -80]);
      yield* all(
        chromeIn,
        personRef().opacity(1, tEntry * 0.6),
        personRef().position.x(-340, tEntry * 0.85, easeOutCubic),
        personRef().scale(1, tEntry * 0.75, easeOutBack),
        focusRing().opacity(0.85, tEntry * 0.5),
        focusRing().scale(1.1, tEntry * 0.65, easeOutCubic),
      );
    } else if (recipe.startsWith('R03')) {
      pathArc().end(0);
      // Show nodes with stagger but total time capped to tEntry via single timeline budget
      const nodeIn = Math.min(0.28, tEntry * 0.35);
      yield* all(
        chromeIn,
        pathArc().end(1, tEntry * 0.75, easeOutCubic),
        ...Array.from({length: nCount}, (_, i) => nodes[i]().opacity(1, nodeIn)),
        ...Array.from({length: nCount}, (_, i) => nodes[i]().scale(1, Math.min(0.4, tEntry * 0.55), easeOutBack)),
      );
    } else if (recipe.startsWith('R04')) {
      heroFrame().position([0, 40]);
      heroHalo().position([0, 40]);
      heroOrbit().position([0, 40]);
      const showA = shot.sequence_in_chapter >= 2;
      const showB = shot.sequence_in_chapter >= 3;
      if (showA) pathA().end(0);
      if (showB) { pathA().end(1); pathB().end(0); }
      yield* all(
        chromeIn,
        heroHalo().opacity(1, tEntry * 0.5),
        heroHalo().scale(1, tEntry * 0.7, easeOutCubic),
        heroOrbit().opacity(1, tEntry * 0.55),
        heroOrbit().scale(1, tEntry * 0.7, easeOutCubic),
        heroFrame().opacity(1, tEntry * 0.45),
        heroFrame().scale(1, tEntry * 0.75, easeOutBack),
        ...(showA && !showB ? [pathA().end(1, tEntry * 0.85, easeOutCubic)] : []),
        ...(showB ? [pathB().end(1, tEntry * 0.85, easeOutCubic)] : []),
      );
    } else if (recipe.startsWith('R05')) {
      focusRing().position([-200, 0]);
      token().position([-140, 20]);
      yield* all(
        chromeIn,
        pathA().end(1, tEntry * 0.85, easeOutCubic),
        focusRing().opacity(0.9, tEntry * 0.5),
        token().opacity(1, tEntry * 0.4),
        ...(blocked ? [lockBadge().opacity(1, tEntry * 0.4)] : []),
      );
    } else if (recipe.startsWith('R06')) {
      heroSlot().position([-200, 20]);
      evidenceTxt().text(labels[0] || '证据位');
      yield* all(
        chromeIn,
        heroSlot().opacity(0.95, tEntry * 0.55),
        heroSlot().scale(1, tEntry * 0.7, easeOutBack),
        evidenceBox().opacity(1, tEntry * 0.55),
        evidenceBox().scale(1, tEntry * 0.7, easeOutBack),
        ...(blocked ? [lockBadge().opacity(1, tEntry * 0.4)] : []),
      );
    } else if (recipe.startsWith('R07')) {
      const stages = Math.min(4, nCount);
      for (let i = 0; i < stages; i++) {
        nodes[i]().position([-480 + i * 300, 40]);
      }
      token().position([-620, 120]);
      yield* all(
        chromeIn,
        processPath().end(1, tEntry * 0.85, easeOutCubic),
        token().opacity(1, tEntry * 0.4),
        ...Array.from({length: stages}, (_, i) => nodes[i]().opacity(1, tEntry * 0.45)),
        ...Array.from({length: stages}, (_, i) => nodes[i]().scale(1, tEntry * 0.6, easeOutBack)),
      );
    } else if (recipe.startsWith('R08')) {
      if (pKind) {
        personRef().position([0, -60]);
        personRef().size([200, 300]);
      }
      yield* all(
        chromeIn,
        ...(pKind ? [personRef().opacity(0.95, tEntry * 0.5)] : []),
        pairA().opacity(1, tEntry * 0.55),
        pairA().position.x(-320, tEntry * 0.7, easeOutCubic),
        pairB().opacity(1, tEntry * 0.55),
        pairB().position.x(320, tEntry * 0.7, easeOutCubic),
        ...(blocked ? [lockBadge().opacity(1, tEntry * 0.4)] : []),
      );
    } else if (recipe.startsWith('R09')) {
      yield* all(
        chromeIn,
        ...[0, 1, 2].map((i) => calendar[i]().opacity(1, tEntry * 0.45)),
        ...[0, 1, 2].map((i) => calendar[i]().scale(1, tEntry * 0.65, easeOutBack)),
      );
    } else if (recipe.startsWith('R10')) {
      for (let i = 0; i < nCount; i++) {
        const ang = (Math.PI * 2 * i) / nCount - Math.PI / 2;
        nodes[i]().position([Math.cos(ang) * 340, Math.sin(ang) * 200 + 40]);
      }
      heroFrame().position([0, 40]);
      yield* all(
        chromeIn,
        pathArc().end(1, tEntry * 0.8, easeOutCubic),
        ...Array.from({length: nCount}, (_, i) => nodes[i]().opacity(1, tEntry * 0.45)),
        ...Array.from({length: nCount}, (_, i) => nodes[i]().scale(1, tEntry * 0.6, easeOutBack)),
        heroFrame().opacity(1, tEntry * 0.5),
        heroFrame().scale(0.85, tEntry * 0.65, easeOutBack),
        heroHalo().opacity(0.9, tEntry * 0.45),
      );
    } else {
      yield* all(
        chromeIn,
        focusRing().opacity(1, tEntry * 0.6),
        focusRing().scale(1.2, tEntry * 0.75, easeOutCubic),
      );
    }

    // PERFORMANCE — non-text motion required
    const perfSteps = Math.max(2, Math.floor(tPerf / 0.45));
    for (let p = 0; p < perfSteps; p++) {
      const step = tPerf / perfSteps;
      if (recipe.startsWith('R01') || recipe.startsWith('R04')) {
        yield* all(
          heroOrbit().rotation(heroOrbit().rotation() + 18, step, easeInOutCubic),
          heroHalo().scale(1 + (p % 2 === 0 ? 0.03 : 0), step, easeInOutCubic),
        );
        if (recipe.startsWith('R04') && nCount >= 2 && (shot.sequence_in_chapter >= 2 || pathA().end() > 0.5)) {
          // ensure path labels exist as nodes at path ends
          if (nodes[0]().opacity() < 0.5) {
            nodes[0]().position([-560, -90]);
            nodes[1]().position([560, 200]);
            nodeTxt[0]().text(labels[0] || '01');
            nodeTxt[1]().text(labels[1] || '02');
            yield* all(
              nodes[0]().opacity(1, step * 0.4),
              nodes[0]().scale(1, step * 0.5, easeOutBack),
            );
          }
          if (pathB().end() > 0.5 && nodes[1]().opacity() < 0.5) {
            yield* all(
              nodes[1]().opacity(1, step * 0.4),
              nodes[1]().scale(1, step * 0.5, easeOutBack),
            );
          }
          if (nodes[0]().opacity() > 0.5 && nodes[1]().opacity() > 0.5) {
            const focus = p % 2;
            yield* all(
              nodes[focus]().scale(1.05, step * 0.55, easeInOutCubic),
              nodes[1 - focus]().opacity(0.68, step * 0.55),
              nodes[1 - focus]().scale(1, step * 0.55),
            );
            nodes[focus]().scale(1);
            nodes[1 - focus]().opacity(1);
          }
        }
      } else if (recipe.startsWith('R02')) {
        yield* all(
          personRef().position.y(30 + (p % 2 === 0 ? -8 : 8), step, easeInOutCubic),
          focusRing().scale(1 + (p % 2) * 0.08, step, easeInOutCubic),
          goldBlob().opacity(0.45 + (p % 2) * 0.1, step),
        );
      } else if (recipe.startsWith('R03') || recipe.startsWith('R10')) {
        const focus = p % nCount;
        for (let i = 0; i < nCount; i++) {
          const active = i === focus;
          nodes[i]().opacity(active ? 1 : 0.68);
          nodes[i]().scale(active ? 1.05 : 1);
        }
        yield* waitFor(step);
      } else if (recipe.startsWith('R05')) {
        const x = -140 + (p / Math.max(1, perfSteps - 1)) * 280;
        yield* all(
          token().position([x, 20 - Math.sin(p) * 20], step, easeInOutCubic),
          focusRing().position([x, 0], step, easeInOutCubic),
          lockBadge().opacity(blocked ? 0.7 + (p % 2) * 0.3 : 0, step * 0.5),
        );
      } else if (recipe.startsWith('R06')) {
        yield* all(
          evidenceBox().scale(1 + (p % 2) * 0.04, step, easeInOutCubic),
          evidenceBox().position.y(-40 + (p % 2) * 12, step, easeInOutCubic),
          heroSlot().scale(1 + (p % 2) * 0.02, step, easeInOutCubic),
        );
      } else if (recipe.startsWith('R07')) {
        const pts = [
          [-620, 120],
          [-240, -40],
          [160, -40],
          [560, 120],
        ] as [number, number][];
        const idx = Math.min(pts.length - 1, Math.floor((p / perfSteps) * pts.length));
        yield* all(
          token().position(pts[idx], step, easeInOutCubic),
          nodes[Math.min(nCount - 1, idx)]().scale(1.05, step, easeInOutCubic),
        );
        nodes[Math.min(nCount - 1, idx)]().scale(1);
      } else if (recipe.startsWith('R08')) {
        if (p === 0) {
          yield* relation().opacity(1, step * 0.6);
          yield* relation().scale(1.1, step * 0.5, easeOutBack);
        } else {
          yield* all(
            relation().scale(1 + (p % 2) * 0.06, step, easeInOutCubic),
            pairA().opacity(0.85 + (p % 2) * 0.15, step),
            pairB().opacity(0.85 + (p % 2) * 0.15, step),
          );
        }
      } else if (recipe.startsWith('R09')) {
        const focus = Math.min(2, p % 3);
        for (let i = 0; i < 3; i++) {
          calendar[i]().scale(i === focus ? 1.06 : 0.92);
          calendar[i]().opacity(i === focus ? 1 : 0.7);
        }
        yield* waitFor(step);
      } else {
        yield* all(
          focusRing().scale(1.1 + (p % 2) * 0.1, step, easeInOutCubic),
          mintBlob().position.x(800 + (p % 2) * 20, step),
        );
      }

      // mild camera push for recipes that request it
      if (shot.camera_motion.includes('push') && p === 0) {
        stage().scale(1.015);
      }
    }

    // EXIT — hand off to next, never full-page fade only
    if (recipe.startsWith('R01') || recipe.startsWith('R04')) {
      state.heroX = shot.transition_to.startsWith('K08') || shot.id.startsWith('K08') ? 0 : 280;
      state.heroY = 40;
      yield* all(
        heroFrame().position([state.heroX, state.heroY], tExit, easeInOutCubic),
        heroHalo().position([state.heroX, state.heroY], tExit, easeInOutCubic),
        heroOrbit().position([state.heroX, state.heroY], tExit, easeInOutCubic),
        heroFrame().scale(0.72, tExit, easeInCubic),
        titleTxt().opacity(0.2, tExit * 0.6),
        ...[0, 1, 2, 3, 4, 5].map((i) => nodes[i]().opacity(Math.min(nodes[i]().opacity(), 0.35), tExit * 0.7)),
      );
    } else if (recipe.startsWith('R02')) {
      yield* all(
        personRef().position.x(personRef().position.x() + 120, tExit, easeInCubic),
        personRef().opacity(0.25, tExit),
        focusRing().opacity(0, tExit * 0.8),
        titleTxt().opacity(0.2, tExit * 0.5),
      );
    } else if (recipe.startsWith('R03')) {
      // converge toward center
      yield* all(
        ...Array.from({length: nCount}, (_, i) =>
          nodes[i]().position([0, 120], tExit, easeInOutCubic),
        ),
        ...Array.from({length: nCount}, (_, i) => nodes[i]().scale(0.55, tExit, easeInCubic)),
        pathArc().end(0.2, tExit, easeInCubic),
      );
      yield* all(...Array.from({length: nCount}, (_, i) => nodes[i]().opacity(0, 0.12)));
    } else if (recipe.startsWith('R05')) {
      yield* all(
        token().position([state.heroX, state.heroY], tExit, easeInOutCubic),
        pathA().end(0.35, tExit, easeInCubic),
        lockBadge().opacity(0, tExit * 0.6),
      );
    } else if (recipe.startsWith('R06')) {
      yield* all(
        evidenceBox().position([0, 40], tExit, easeInOutCubic),
        evidenceBox().scale(0.55, tExit, easeInCubic),
        heroSlot().opacity(0.35, tExit),
      );
    } else if (recipe.startsWith('R07')) {
      yield* all(
        token().position([560, 120], tExit * 0.7, easeInOutCubic),
        processPath().end(0.4, tExit, easeInCubic),
        ...Array.from({length: nCount}, (_, i) => nodes[i]().opacity(0.3, tExit)),
      );
    } else if (recipe.startsWith('R08')) {
      yield* all(
        pairA().position.y(pairA().position.y() + 40, tExit, easeInCubic),
        pairB().position.y(pairB().position.y() + 40, tExit, easeInCubic),
        pairA().opacity(0.25, tExit),
        pairB().opacity(0.25, tExit),
        relation().opacity(0.3, tExit),
        personYoung().opacity(0.2, tExit),
        personMiddle().opacity(0.2, tExit),
        personElder().opacity(0.2, tExit),
      );
    } else if (recipe.startsWith('R09')) {
      yield* all(
        ...[0, 1, 2].map((i) => calendar[i]().position.y(80 + 30, tExit, easeInCubic)),
        ...[0, 1, 2].map((i) => calendar[i]().opacity(0.25, tExit)),
      );
    } else if (recipe.startsWith('R10')) {
      yield* all(
        ...Array.from({length: nCount}, (_, i) =>
          nodes[i]().position([0, 40], tExit, easeInOutCubic),
        ),
        ...Array.from({length: nCount}, (_, i) => nodes[i]().scale(0.4, tExit, easeInCubic)),
        pathArc().end(0.15, tExit, easeInCubic),
      );
      if (shot.id === 'K18-S04') {
        logo().opacity(0.85);
        yield* waitFor(Math.min(0.8, tExit));
      }
    } else {
      yield* all(focusRing().opacity(0, tExit), titleTxt().opacity(0.2, tExit));
    }

    yield* all(
      subtitleBar().opacity(0, 0.12),
      subtitleTxt().opacity(0, 0.12),
      gateChip().opacity(0.35, 0.12),
    );

    elapsed += d;
    yield* progress().end(elapsed / TOTAL, 0.12, easeOutCubic);
    stage().scale(1);
  }

  // end hold
  titleTxt().text('58 微镜头结构 Animatic 完成');
  focusTxt().text('正式旁白与授权资产齐备后，按相同微镜头结构替换，不重做页式章节');
  subtitleTxt().text('production-v2 · 非完整金样');
  yield* all(
    titleTxt().opacity(1, 0.3),
    focusTxt().opacity(1, 0.3),
    subtitleBar().opacity(1, 0.25),
    subtitleTxt().opacity(1, 0.25),
    heroFrame().opacity(1, 0.3),
    heroFrame().position([0, 40], 0.3),
    heroFrame().scale(1, 0.35, easeOutBack),
  );
  yield* waitFor(0.6);
});

export default makeProject({
  name: 'kekang-pfizer-v2-animatic',
  scenes: [scene],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
