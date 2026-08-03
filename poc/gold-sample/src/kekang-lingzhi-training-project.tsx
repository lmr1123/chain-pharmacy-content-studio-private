/**
 * 可可康灵芝胶囊 · 培训视频 v4
 *
 * 结构对齐用户指定 PPTX 叙事（非「先讲成分」）：
 * 1 睡眠健康问题 → 2 三大功效 → 3 产品特点 → 4 适宜人群
 * → 5 联合用药（商品+商品=功效）→ 6 表格总结
 *
 * 动效对标风热证：多场景布局切换、行卡 stagger、滑入/弹出，非单一切小图。
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
  easeOutBack,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../kekang-lingzhi-training.json';
import {
  DashenlinBrandMark,
  DashenlinInternalNotice,
  ProductColumnBadge,
  PRODUCT_TRAINING_FONT as FONT,
} from './components/product-training-dashenlin-chrome';

type Cue = {start: number; end: number; text: string};

const cues = data.cues as Cue[];
const DURATION = Number(
  (data as {playback_duration?: number}).playback_duration ?? 70,
);
const BG = '#7ec8e8';
const WHITE = '#ffffff';
const INK = '#163642';
const ACCENT = '#0d6e8c';
const SUB_BG = 'rgba(18, 36, 48, 0.84)';
const PANEL = 'rgba(255,255,255,0.94)';
const GREEN = '#1a9a4a';
const ORANGE = '#e67e22';
const BLUE_TAG = '#3a7ebd';

const assets = data.assets as {
  sleep: string[];
  efficacy: string[];
  features: string[];
  audience: string[];
  jointIcon: string[];
  ganodermaHero: string;
};

/* —— 数字人 —— */
const PRESENTER = '/product-training-dashenlin-presenter';
const bodySrc = `${PRESENTER}/palm-mouthless.png`;
const mouthSrc = (n: string) => `${PRESENTER}/mouth-${n}.png`;
const POSE = {imgW: 334, imgH: 941};
const ANCHOR: [number, number] = [0.548, 0.391];
function bodySize(h: number): [number, number] {
  return [h * (POSE.imgW / POSE.imgH), h];
}
function mouthPos(size: [number, number]): [number, number] {
  return [(ANCHOR[0] - 0.5) * size[0], (ANCHOR[1] - 0.5) * size[1]];
}

const CX = 240; // content center (right of presenter)

function* runSubtitles(ref: Reference<Txt>, bar: Reference<Rect>) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      ref().opacity(0);
      bar().opacity(0);
      yield* waitFor(cue.start - cursor);
    }
    ref().text(cue.text);
    yield* all(bar().opacity(1, 0.05), ref().opacity(1, 0.05));
    yield* waitFor(Math.max(0, cue.end - cue.start - 0.05));
    ref().opacity(0);
    bar().opacity(0);
    cursor = cue.end;
  }
  if (cursor < DURATION) yield* waitFor(DURATION - cursor);
}

function* mouthTalk(mouths: Reference<Img>[], seconds: number) {
  let t = 0;
  const seq = [1, 2, 1, 3, 1, 0, 2, 1];
  let i = 0;
  while (t < seconds) {
    const idx = seq[i % seq.length];
    for (let m = 0; m < 4; m++) mouths[m]().opacity(m === idx ? 1 : 0);
    const step = 0.09 + (i % 3) * 0.015;
    yield* waitFor(Math.min(step, seconds - t));
    t += step;
    i++;
  }
  for (let m = 0; m < 4; m++) mouths[m]().opacity(m === 0 ? 1 : 0);
}

function* toAbs(c: {t: number}, abs: number) {
  const d = abs - c.t;
  if (d > 0.02) {
    yield* waitFor(d);
    c.t = abs;
  }
}

function* staggerIn(
  cards: Reference<Rect>[],
  labels: Reference<Txt>[],
) {
  for (let i = 0; i < cards.length; i++) {
    yield* all(
      cards[i]().opacity(1, 0.16),
      cards[i]().scale(1, 0.3, easeOutBack),
      labels[i]().opacity(1, 0.18),
    );
  }
}

function* fadeScene(...refs: Reference<any>[]) {
  yield* all(...refs.map(r => r().opacity(0, 0.18)));
}

/** 无品牌包装示意卡 */
function PackCard({
  title,
  color,
  position,
  cardRef,
}: {
  title: string;
  color: string;
  position: [number, number];
  cardRef: Reference<Rect>;
}) {
  return (
    <Rect
      ref={cardRef}
      position={position}
      size={[200, 240]}
      radius={16}
      fill={WHITE}
      stroke={color}
      lineWidth={5}
      shadowColor={'rgba(20,50,70,0.16)'}
      shadowBlur={12}
      opacity={0}
      scale={0.85}
    >
      <Rect position={[0, -70]} size={[200, 70]} fill={color} radius={[16, 16, 0, 0]} />
      <Txt
        position={[0, -70]}
        text={title}
        fontFamily={FONT}
        fontSize={26}
        fontWeight={850}
        fill={WHITE}
      />
      <Circle position={[0, 40]} size={72} fill={`${color}33`} stroke={color} lineWidth={4} />
      <Txt
        position={[0, 40]}
        text={'药'}
        fontFamily={FONT}
        fontSize={28}
        fontWeight={800}
        fill={color}
      />
      <Txt
        position={[0, 100]}
        text={'示意包装'}
        fontFamily={FONT}
        fontSize={18}
        fontWeight={600}
        fill={'#7a8a94'}
      />
    </Rect>
  );
}

const scene = makeScene2D('kekang-lingzhi-training', function* (view) {
  const mainTitle = createRef<Txt>();
  const sectionHint = createRef<Txt>();
  const subtitle = createRef<Txt>();
  const subBar = createRef<Rect>();

  const pSize = bodySize(760);
  const mPos = mouthPos(pSize);
  const closed: [number, number] = [pSize[0] * 0.115, pSize[0] * 0.072];
  const open: [number, number] = [pSize[0] * 0.124, pSize[0] * 0.083];
  const mSizes: [number, number][] = [
    closed,
    open,
    [open[0] * 0.92, open[1] * 1.06],
    [open[0] * 1.1, open[1] * 0.95],
  ];
  const presenter = createRef<Rect>();
  const mouths = [0, 1, 2, 3].map(() => createRef<Img>());

  // Scene groups
  const scSleep = createRef<Rect>();
  const scEff = createRef<Rect>();
  const scFeat = createRef<Rect>();
  const scAud = createRef<Rect>();
  const scJoint = createRef<Rect>();
  const scTable = createRef<Rect>();

  // Sleep: 3 symptom cards
  const sleepCards = [0, 1, 2].map(() => createRef<Rect>());
  const sleepLabs = [0, 1, 2].map(() => createRef<Txt>());
  const SLEEP_L = ['入睡慢', '夜间易醒', '白天疲倦'];
  const SLEEP_POS: [number, number][] = [
    [CX - 280, 20],
    [CX + 20, 20],
    [CX + 320, 20],
  ];

  // Efficacy
  const effCards = [0, 1, 2].map(() => createRef<Rect>());
  const effLabs = [0, 1, 2].map(() => createRef<Txt>());
  const EFF_L = ['宁心安神助睡眠', '保肝护肝抗衰老', '提升免疫少生病'];
  const EFF_POS: [number, number][] = [
    [CX - 300, 30],
    [CX + 20, 30],
    [CX + 340, 30],
  ];

  // Features: hero + 3 rows sliding
  const featHero = createRef<Img>();
  const featRows = [0, 1, 2].map(() => createRef<Rect>());
  const FEAT_T = ['优质产地含量高', '专利工艺吸收好', '大品牌值得信赖'];
  const FEAT_B = [
    '大别山赤灵芝 · 多糖含量高',
    '双重提取 · 胶囊锁营养',
    '中山可可康 · 国家 GMP',
  ];

  // Audience
  const audCards = [0, 1, 2].map(() => createRef<Rect>());
  const audLabs = [0, 1, 2].map(() => createRef<Txt>());
  const AUD_L = ['经常失眠', '常喝酒伤肝', '免疫力差'];

  // Joint formula (one at a time)
  const jointRoot = [0, 1, 2].map(() => createRef<Rect>());
  const jointPackA = [0, 1, 2].map(() => createRef<Rect>());
  const jointPackB = [0, 1, 2].map(() => createRef<Rect>());
  const jointPlus = [0, 1, 2].map(() => createRef<Txt>());
  const jointEq = [0, 1, 2].map(() => createRef<Txt>());
  const jointResult = [0, 1, 2].map(() => createRef<Rect>());
  const jointIcon = [0, 1, 2].map(() => createRef<Img>());
  const jointTag = [0, 1, 2].map(() => createRef<Rect>());
  const JOINT = [
    {
      tag: '失眠',
      a: '谷维素片',
      aColor: '#5b8fd9',
      b: '灵芝胶囊',
      result: '营养神经 + 镇静助眠',
      tip: '改善失眠更稳',
    },
    {
      tag: '肝功能异常',
      a: '护肝片',
      aColor: '#3aa06a',
      b: '灵芝胶囊',
      result: '降酶疏肝 + 保肝解毒',
      tip: '保肝护肝',
    },
    {
      tag: '免疫力低下',
      a: '转移因子',
      aColor: '#d17a3a',
      b: '灵芝胶囊',
      result: '调节免疫 + 提升杀伤力',
      tip: '提高免疫力',
    },
  ];

  // Table rows
  const tableRows = [0, 1, 2, 3, 4].map(() => createRef<Rect>());
  const TABLE = [
    ['有效成分', '灵芝多糖、灵芝三萜'],
    ['三大功效', '安神助眠 · 保肝 · 提升免疫'],
    ['产品特点', '产地高含量 · 双重提取 · GMP'],
    ['适宜人群', '失眠 · 伤肝 · 免疫力差'],
    ['服用建议', '1 个月一周期 · 连服 2—3 个月'],
  ];

  view.add(
    <>
      <Rect size={[1920, 1080]} fill={BG} />
      {Array.from({length: 5}, (_, r) =>
        Array.from({length: 9}, (_, c) => (
          <Rect
            key={`g${r}${c}`}
            position={[-840 + c * 200, -400 + r * 180]}
            size={[40, 40]}
            radius={8}
            fill={'rgba(255,255,255,0.035)'}
          />
        )),
      )}
      <Audio src={data.audio.file} play />
      <DashenlinBrandMark position={[-790, -450]} />
      <ProductColumnBadge text={'可可康灵芝胶囊'} position={[-720, -355]} />
      <DashenlinInternalNotice />

      <Txt
        ref={mainTitle}
        position={[CX, -400]}
        text={'睡眠健康问题'}
        fontFamily={FONT}
        fontSize={58}
        fontWeight={800}
        fill={WHITE}
        shadowColor={'rgba(12,40,60,0.35)'}
        shadowBlur={10}
        shadowOffset={[0, 3]}
        opacity={0}
      />
      <Txt
        ref={sectionHint}
        position={[CX, -335]}
        text={'从顾客痛点出发'}
        fontFamily={FONT}
        fontSize={26}
        fontWeight={600}
        fill={ACCENT}
        opacity={0}
      />

      {/* 数字人 */}
      <Rect ref={presenter} position={[-620, 95]} size={pSize} opacity={0}>
        <Img src={bodySrc} size={pSize} />
        <Rect
          position={mPos}
          size={[closed[0] * 1.15, closed[1] * 1.2]}
          radius={closed[1] * 0.6}
          fill={'#fce8d5'}
        />
        {(['closed', 'small', 'o', 'wide'] as const).map((n, i) => (
          <Img
            key={n}
            ref={mouths[i]}
            src={mouthSrc(n)}
            position={mPos}
            size={mSizes[i]}
            opacity={i === 0 ? 1 : 0}
          />
        ))}
      </Rect>

      {/* —— 1 睡眠健康问题：三症状行卡 stagger —— */}
      <Rect ref={scSleep} size={[1920, 1080]} opacity={1}>
        {assets.sleep.map((src, i) => (
          <Rect
            key={`sl-${i}`}
            ref={sleepCards[i]}
            position={[SLEEP_POS[i][0], SLEEP_POS[i][1] + 24]}
            size={[250, 320]}
            radius={22}
            fill={PANEL}
            shadowColor={'rgba(20,50,70,0.16)'}
            shadowBlur={14}
            opacity={0}
            scale={0.88}
          >
            <Img src={src} position={[0, -30]} size={[210, 210]} radius={16} />
            <Txt
              ref={sleepLabs[i]}
              position={[0, 120]}
              text={SLEEP_L[i]}
              fontFamily={FONT}
              fontSize={28}
              fontWeight={800}
              fill={INK}
              opacity={0}
            />
          </Rect>
        ))}
      </Rect>

      {/* —— 2 三大功效 —— */}
      <Rect ref={scEff} size={[1920, 1080]} opacity={0}>
        {assets.efficacy.map((src, i) => (
          <Rect
            key={`ef-${i}`}
            ref={effCards[i]}
            position={[EFF_POS[i][0], EFF_POS[i][1] + 20]}
            size={[270, 340]}
            radius={22}
            fill={PANEL}
            shadowColor={'rgba(20,50,70,0.16)'}
            shadowBlur={14}
            opacity={0}
            scale={0.88}
          >
            <Circle
              position={[0, -90]}
              size={48}
              fill={i === 0 ? BLUE_TAG : i === 1 ? GREEN : ORANGE}
            >
              <Txt
                text={`${i + 1}`}
                fontFamily={FONT}
                fontSize={24}
                fontWeight={900}
                fill={WHITE}
              />
            </Circle>
            <Img src={src} position={[0, -10]} size={[200, 200]} radius={14} />
            <Txt
              ref={effLabs[i]}
              position={[0, 130]}
              width={240}
              textAlign={'center'}
              text={EFF_L[i]}
              fontFamily={FONT}
              fontSize={24}
              fontWeight={800}
              fill={INK}
              opacity={0}
            />
          </Rect>
        ))}
      </Rect>

      {/* —— 3 产品特点：左主视觉 + 右三行滑入 —— */}
      <Rect ref={scFeat} size={[1920, 1080]} opacity={0}>
        <Img
          ref={featHero}
          src={assets.ganodermaHero}
          position={[CX - 280, 30]}
          size={[340, 340]}
          radius={24}
          opacity={0}
          scale={0.9}
          shadowColor={'rgba(20,50,70,0.18)'}
          shadowBlur={14}
        />
        {FEAT_T.map((t, i) => (
          <Rect
            key={`fr-${i}`}
            ref={featRows[i]}
            position={[CX + 420, -120 + i * 140]}
            size={[520, 110]}
            radius={18}
            fill={PANEL}
            opacity={0}
            shadowColor={'rgba(20,50,70,0.14)'}
            shadowBlur={10}
          >
            <Rect
              position={[-240, 0]}
              size={[14, 110]}
              fill={i === 0 ? GREEN : i === 1 ? BLUE_TAG : ORANGE}
              radius={[18, 0, 0, 18]}
            />
            <Img
              src={assets.features[i]}
              position={[-160, 0]}
              size={[72, 72]}
              radius={12}
            />
            <Txt
              position={[40, -22]}
              text={t}
              fontFamily={FONT}
              fontSize={30}
              fontWeight={850}
              fill={ACCENT}
            />
            <Txt
              position={[60, 28]}
              width={360}
              text={FEAT_B[i]}
              fontFamily={FONT}
              fontSize={22}
              fontWeight={600}
              fill={'#556'}
            />
          </Rect>
        ))}
      </Rect>

      {/* —— 4 适宜人群 —— */}
      <Rect ref={scAud} size={[1920, 1080]} opacity={0}>
        {assets.audience.map((src, i) => (
          <Rect
            key={`au-${i}`}
            ref={audCards[i]}
            position={[SLEEP_POS[i][0], SLEEP_POS[i][1] + 20]}
            size={[250, 320]}
            radius={22}
            fill={PANEL}
            shadowColor={'rgba(20,50,70,0.16)'}
            shadowBlur={14}
            opacity={0}
            scale={0.88}
          >
            <Img src={src} position={[0, -30]} size={[210, 210]} radius={16} />
            <Txt
              ref={audLabs[i]}
              position={[0, 120]}
              text={AUD_L[i]}
              fontFamily={FONT}
              fontSize={28}
              fontWeight={800}
              fill={ACCENT}
              opacity={0}
            />
          </Rect>
        ))}
      </Rect>

      {/* —— 5 联合用药：场景 | A + B = 功效 + 小插图 —— */}
      <Rect ref={scJoint} size={[1920, 1080]} opacity={0}>
        {JOINT.map((j, i) => (
          <Rect
            key={`j-${i}`}
            ref={jointRoot[i]}
            position={[CX + 40, 20]}
            size={[1100, 520]}
            opacity={0}
          >
            {/* 场景标签 */}
            <Rect
              ref={jointTag[i]}
              position={[-420, -160]}
              size={[200, 120]}
              radius={14}
              fill={BLUE_TAG}
            >
              <Txt
                text={j.tag}
                fontFamily={FONT}
                fontSize={32}
                fontWeight={900}
                fill={WHITE}
              />
            </Rect>
            {/* A + B 包装示意 */}
            <PackCard
              title={j.a}
              color={j.aColor}
              position={[-200, 20]}
              cardRef={jointPackA[i]}
            />
            <Txt
              ref={jointPlus[i]}
              position={[20, 20]}
              text={'+'}
              fontFamily={FONT}
              fontSize={72}
              fontWeight={900}
              fill={GREEN}
              opacity={0}
            />
            <PackCard
              title={j.b}
              color={'#c45c26'}
              position={[240, 20]}
              cardRef={jointPackB[i]}
            />
            <Txt
              ref={jointEq[i]}
              position={[420, 20]}
              text={'='}
              fontFamily={FONT}
              fontSize={64}
              fontWeight={900}
              fill={ORANGE}
              opacity={0}
            />
            {/* 结果功效条 + 小插图 */}
            <Rect
              ref={jointResult[i]}
              position={[20, 200]}
              size={[700, 88]}
              radius={16}
              fill={'#e8f6ef'}
              stroke={GREEN}
              lineWidth={3}
              opacity={0}
            >
              <Txt
                text={j.result}
                fontFamily={FONT}
                fontSize={28}
                fontWeight={800}
                fill={GREEN}
              />
            </Rect>
            <Img
              ref={jointIcon[i]}
              src={assets.jointIcon[i]}
              position={[420, -100]}
              size={[180, 180]}
              radius={18}
              opacity={0}
              scale={0.85}
              shadowColor={'rgba(20,50,70,0.14)'}
              shadowBlur={10}
            />
          </Rect>
        ))}
      </Rect>

      {/* —— 6 表格总结：行级联 —— */}
      <Rect ref={scTable} size={[1920, 1080]} opacity={0}>
        <Rect
          position={[CX, 10]}
          size={[900, 560]}
          radius={20}
          fill={PANEL}
          shadowColor={'rgba(20,50,70,0.14)'}
          shadowBlur={16}
        >
          {TABLE.map((row, i) => (
            <Rect
              key={`tr-${i}`}
              ref={tableRows[i]}
              position={[0, -200 + i * 90]}
              size={[860, 76]}
              radius={12}
              fill={i % 2 === 0 ? '#f4fafc' : WHITE}
              opacity={0}
              x={40}
            >
              <Rect
                position={[-320, 0]}
                size={[180, 76]}
                fill={i === 4 ? GREEN : ACCENT}
                radius={[12, 0, 0, 12]}
              >
                <Txt
                  text={row[0]}
                  fontFamily={FONT}
                  fontSize={24}
                  fontWeight={800}
                  fill={WHITE}
                />
              </Rect>
              <Txt
                position={[80, 0]}
                width={560}
                textAlign={'left'}
                text={row[1]}
                fontFamily={FONT}
                fontSize={26}
                fontWeight={700}
                fill={INK}
              />
            </Rect>
          ))}
        </Rect>
      </Rect>

      {/* 字幕胶囊 */}
      <Rect
        ref={subBar}
        position={[0, 458]}
        size={[1520, 72]}
        radius={36}
        fill={SUB_BG}
        opacity={0}
      />
      <Txt
        ref={subtitle}
        position={[0, 458]}
        width={1440}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={32}
        fontWeight={650}
        fill={'#f7fafc'}
        opacity={0}
      />
    </>,
  );

  function* setTitle(t: string, h = '') {
    mainTitle().text(t);
    sectionHint().text(h);
    yield* all(
      mainTitle().opacity(1, 0.12),
      sectionHint().opacity(h ? 1 : 0, 0.12),
    );
  }

  function* showJoint(i: number) {
    jointRoot[i]().opacity(1);
    yield* all(
      jointPackA[i]().opacity(1, 0.18),
      jointPackA[i]().scale(1, 0.28, easeOutBack),
    );
    yield* jointPlus[i]().opacity(1, 0.1);
    yield* all(
      jointPackB[i]().opacity(1, 0.18),
      jointPackB[i]().scale(1, 0.28, easeOutBack),
    );
    yield* jointEq[i]().opacity(1, 0.1);
    yield* all(
      jointResult[i]().opacity(1, 0.2),
      jointIcon[i]().opacity(1, 0.2),
      jointIcon[i]().scale(1, 0.28, easeOutBack),
    );
  }

  function* visualTimeline() {
    const c = {t: 0};

    // 入场
    yield* all(
      presenter().opacity(1, 0.3),
      setTitle('睡眠健康问题', '从顾客痛点出发'),
    );
    c.t = 0.35;

    // 1 睡眠症状卡（cue1 起）
    yield* toAbs(c, Math.max(0.4, (cues[1]?.start ?? 1.7) - 0.05));
    yield* staggerIn(sleepCards, sleepLabs);
    c.t += 1.0;

    // 2 功效（cue5「先记住三大核心功效」）
    yield* toAbs(c, Math.max(c.t + 0.1, (cues[5]?.start ?? 16.5) - 0.12));
    yield* fadeScene(scSleep);
    scEff().opacity(1);
    yield* setTitle('三大核心功效', '门店讲解三条主轴');
    yield* staggerIn(effCards, effLabs);
    c.t += 1.1;

    // 3 特点（cue9）
    yield* toAbs(c, Math.max(c.t + 0.1, (cues[9]?.start ?? 31.2) - 0.12));
    yield* fadeScene(scEff);
    scFeat().opacity(1);
    yield* setTitle('产品特点', '三句话讲清楚');
    yield* all(
      featHero().opacity(1, 0.25),
      featHero().scale(1, 0.35, easeOutBack),
    );
    for (let i = 0; i < 3; i++) {
      const row = featRows[i];
      row().position([CX + 520, -120 + i * 140]);
      yield* all(
        row().opacity(1, 0.18),
        row().position([CX + 280, -120 + i * 140], 0.32, easeOutCubic),
      );
    }
    c.t += 1.4;

    // 4 人群（cue10）
    yield* toAbs(c, Math.max(c.t + 0.1, (cues[10]?.start ?? 37.4) - 0.1));
    yield* fadeScene(scFeat);
    scAud().opacity(1);
    yield* setTitle('适宜人群', '三类顾客对得上');
    yield* staggerIn(audCards, audLabs);
    c.t += 1.0;

    // 5 联合用药（cue11 公式 + cue12–14 三套）
    yield* toAbs(c, Math.max(c.t + 0.1, (cues[11]?.start ?? 41.7) - 0.1));
    yield* fadeScene(scAud);
    scJoint().opacity(1);
    yield* setTitle('联合用药', '商品 + 商品 = 解决功效');
    // 公式段先出第一套，避免空场
    yield* showJoint(0);
    c.t += 1.1;

    for (let i = 1; i < 3; i++) {
      const start = cues[12 + i]?.start ?? 49.9 + (i - 1) * 4.5;
      yield* toAbs(c, Math.max(c.t + 0.05, start - 0.08));
      yield* jointRoot[i - 1]().opacity(0, 0.16);
      yield* showJoint(i);
      c.t += 1.1;
    }

    // 6 表格（cue15）
    yield* toAbs(c, Math.max(c.t + 0.1, (cues[15]?.start ?? 59.2) - 0.1));
    yield* fadeScene(scJoint, jointRoot[2]);
    scTable().opacity(1);
    yield* setTitle('快速复盘', '表格总结');
    for (let i = 0; i < tableRows.length; i++) {
      yield* all(
        tableRows[i]().opacity(1, 0.14),
        tableRows[i]().position([0, -200 + i * 90], 0.22, easeOutCubic),
      );
    }
    c.t += 1.2;
    yield* toAbs(c, DURATION);
  }

  yield* all(
    runSubtitles(subtitle, subBar),
    visualTimeline(),
    mouthTalk(mouths, Math.max(1, DURATION - 0.3)),
  );
});

export default makeProject({
  name: 'kekang-lingzhi-training',
  scenes: [scene],
  settings: {
    shared: {size: {x: 1920, y: 1080}},
    rendering: {fps: 30},
  },
});
