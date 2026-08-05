/**
 * 速福达®玛巴洛沙韦 · 商品培训课件3 独立金样 v2.1
 * v2.1：整课克隆旁白（voice.sufuda-courseware-pharmacist-v1 / v5-smooth），
 * 评估克隆音色与语速上限；时长约 93s。原声备份 narration-rerecord-original-v2.wav。
 */
import {
  Audio,
  Circle,
  Img,
  Layout,
  Line,
  Rect,
  Txt,
  makeScene2D,
} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeInCubic,
  easeInOutCubic,
  easeOutBack,
  easeOutCubic,
  linear,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../storyboard.json';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {A as assetOf, K, T, tokens} from './content';

type Cap = {start: number; end: number; text: string};
type R = Reference<Rect>;
type T = Reference<Txt>;
type I = Reference<Img>;

const FONT =
  'HarmonyOS Sans SC, Source Han Sans SC, Source Han Sans CN, PingFang SC, Microsoft YaHei, sans-serif';
const DURATION = Number(data.duration);
const captions = data.captions as Cap[];
const storyAssets = data.assets as Record<string, string>;
const A: Record<string, string> = new Proxy(
  {},
  {
    get(_t, prop: string) {
      try {
        return assetOf(prop);
      } catch {
        return storyAssets[prop];
      }
    },
  },
) as Record<string, string>;

// 设计 token 单源：content-model.json tokens（色值 + fs_* 字号），键缺失时回退常量
const tk = tokens();
const ORANGE = tk.orange ?? '#e98200';
const ORANGE2 = tk.orange2 ?? '#f4a437';
const NAVY = tk.navy ?? '#123c78';
const NAVY2 = tk.navy2 ?? '#22579b';
const WHITE = tk.white ?? '#ffffff';
const GRAY = tk.gray ?? '#b8c0cb';
const MUTED = tk.muted ?? '#5a6a7d';
const INK = tk.ink ?? '#182a43';
const ROW_BG = tk.row_bg ?? '#fff3e0';
const ROW_BG2 = tk.row_bg2 ?? '#ffe8c8';

const fs = (key: string, dflt: number) => Number(tk[key] ?? dflt);
const TS = {
  coverTitle: fs('fs_cover_title', 84),
  coverSub: fs('fs_cover_sub', 36),
  coverCheck: fs('fs_cover_check', 40),
  chapter: fs('fs_chapter', 48),
  nav: fs('fs_nav', 28),
  navNum: fs('fs_nav_num', 24),
  cardTitle: fs('fs_card_title', 36),
  cardBody: fs('fs_card_body', 30),
  heroNum: fs('fs_hero_num', 72),
  bubble: fs('fs_bubble', 46),
  caption: fs('fs_caption', 40),
};

function* setNav(items: R[], active: number) {
  yield* all(
    ...items.map((item, i) =>
      all(
        item().fill(i === active ? ORANGE : GRAY, 0.12),
        item().scale(i === active ? 1.04 : 1, 0.12, easeOutCubic),
      ),
    ),
  );
}

function NavPill({
  root,
  n,
  text,
  x,
  w,
}: {
  root: R;
  n: string;
  text: string;
  x: number;
  w: number;
}) {
  return (
    <Rect ref={root} position={[x, -348]} size={[w, 64]} radius={32} fill={GRAY} opacity={0}>
      <Circle position={[-w / 2 + 30, 0]} size={46} fill={WHITE}>
        <Txt text={n} fontFamily={FONT} fontSize={TS.navNum} fontWeight={900} fill={ORANGE} />
      </Circle>
      <Txt
        position={[12, 0]}
        width={w - 72}
        text={text}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={TS.nav}
        fontWeight={900}
        fill={WHITE}
      />
    </Rect>
  );
}

function LogoMark(props: {layerKey?: string} = {}) {
  return (
    <Img
      key={props.layerKey}
      src={A.logo}
      position={[790, -478]}
      size={[300, 86]}
      opacity={0.95}
    />
  );
}

function ChapterRibbon({text}: {text: string}) {
  return (
    <>
      <Img src={'/assets/ribbon-chapter-shell-v1.png'} position={[0, -458]} size={[720, 100]} />
      <Txt
        position={[0, -458]}
        text={text}
        fontFamily={FONT}
        fontSize={TS.chapter}
        fontWeight={900}
        fill={WHITE}
      />
    </>
  );
}

function* runCaptions(bar: R, text: T) {
  let cursor = 0;
  for (const c of captions) {
    if (c.start > cursor) {
      text().opacity(0);
      bar().opacity(0);
      yield* waitFor(c.start - cursor);
    }
    text().text(c.text);
    yield* all(bar().opacity(1, 0.08), text().opacity(1, 0.08));
    // clamp 到 DURATION：末条 caption end(93.513) 超出旁白轨，会把场景拖过 93.228
    yield* waitFor(Math.max(0, Math.min(c.end, DURATION) - c.start - 0.08));
    cursor = c.end;
  }
  if (cursor < DURATION) {
    text().opacity(0);
    bar().opacity(0);
    yield* waitFor(DURATION - cursor);
  }
}

const scene = makeScene2D('sufuda-product-courseware-3', function* (view) {
  const cover = createRef<Rect>();
  const flu = createRef<Rect>();
  const chRibbon = createRef<Rect>();
  const chTitle = createRef<Txt>();
  const benefitShell = createRef<Rect>();
  const navB = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const b1 = createRef<Rect>();
  const b1Bubble = createRef<Rect>();
  const b1Jia = createRef<Rect>();
  const b1Yi = createRef<Rect>();
  const b2 = createRef<Rect>();
  const b3 = createRef<Rect>();
  const featShell = createRef<Rect>();
  const navF = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const f1 = createRef<Rect>();
  const f2 = createRef<Rect>();
  const f3 = createRef<Rect>();
  const audShell = createRef<Rect>();
  const a1 = createRef<Rect>();
  const a2 = createRef<Rect>();
  const comboShell = createRef<Rect>();
  const navC = [createRef<Rect>(), createRef<Rect>()];
  const c1 = createRef<Rect>();
  const c2 = createRef<Rect>();
  const summary = createRef<Rect>();

  const fluCard1 = createRef<Rect>();
  const fluCard2 = createRef<Rect>();
  const fluCard3 = createRef<Rect>();
  const flu48 = createRef<Rect>();
  const flu48Rule = createRef<Line>();
  const coverChecks = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const coverPack = createRef<Img>();

  // 章节过场（chRibbon 层内 ribbon 图 + 标题做方向性扫入扫出）
  const chRibbonImg = createRef<Img>();

  const dose1 = createRef<Rect>();
  const dose24 = createRef<Rect>();
  const cellImg = createRef<Img>();
  const osel = createRef<Rect>();
  const mechLeft = createRef<Txt>();
  const mechRight = createRef<Txt>();
  const virusOrbit = [0, 1, 2, 3, 4, 5].map(() => createRef<Img>());
  const b2Divider = createRef<Line>();

  const patient = createRef<Img>();
  const family = createRef<Img>();
  const b3ShadowP = createRef<Circle>();
  const b3ShadowF = createRef<Circle>();

  const packHero = createRef<Img>();
  const f1Baby = createRef<Img>();
  const f1Ring = createRef<Circle>();
  const f1Shield = createRef<Img>();
  const f1LabelL = createRef<Txt>();
  const f1LabelR = createRef<Txt>();
  const tabBubble = createRef<Rect>();
  const strawBubble = createRef<Rect>();
  const tabLine = createRef<Line>();
  const strawLine = createRef<Line>();
  const granPanel = createRef<Rect>();
  const tabPanel = createRef<Rect>();

  const f3r1 = createRef<Rect>();
  const f3r2 = createRef<Rect>();
  const f3r3 = createRef<Rect>();
  const f3r4 = createRef<Rect>();

  const ageBubble = createRef<Rect>();
  const a1Person = createRef<Img>();
  const a1Shadow = createRef<Circle>();
  const audHeadline = createRef<Txt>();
  const cardElder = createRef<Rect>();
  const cardChild = createRef<Rect>();
  const cardChronic = createRef<Rect>();

  const plus1 = createRef<Txt>();
  const plus2 = createRef<Txt>();
  const comboNote1 = createRef<Txt>();
  const comboNote2 = createRef<Txt>();
  const comboStage1 = createRef<Rect>();
  const comboStage2 = createRef<Rect>();
  const comboLine1 = createRef<Line>();
  const comboLine2 = createRef<Line>();
  const comboRule1 = createRef<Line>();
  const comboRule2 = createRef<Line>();
  const comboSweep1 = createRef<Rect>();
  const comboSweep2 = createRef<Rect>();

  // 总结表级联：eyebrow/表头/3 数据行
  const smHand = createRef<Img>();
  const smEyebrow = createRef<Txt>();
  const smHead = createRef<Rect>();
  const smE1 = createRef<Txt>();
  const smE2 = createRef<Txt>();
  const smE3 = createRef<Txt>();
  const smF1 = createRef<Txt>();
  const smF2 = createRef<Txt>();
  const smF3 = createRef<Txt>();
  const smA1 = createRef<Txt>();
  const smC1 = createRef<Txt>();

  const capBar = createRef<Rect>();
  const capTxt = createRef<Txt>();

  // combo note 下划线半宽 ≈ 字数 × 36px 字号的 0.47 倍
  const comboRuleHalf1 = T('combo_1', 'note').length * 17;
  const comboRuleHalf2 = T('combo_2', 'note').length * 17;

  view.add(
    <>
      <Img src={A.background} size={[1920, 1080]} />
      <Audio src={data.audio.file} play />

      {/* ===== COVER: left-aligned checks ===== */}
      <Rect ref={cover} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <Txt
          position={[0, -320]}
          text={T('cover', 'title')} key={K('cover', 'title')}
          fontFamily={FONT}
          fontSize={TS.coverTitle}
          fontWeight={900}
          fill={NAVY2}
        />
        <Rect position={[0, -220]} size={[780, 64]} radius={12} fill={ORANGE}>
          <Txt
            text={T('cover', 'tagline')} key={K('cover', 'tagline')}
            fontFamily={FONT}
            fontSize={TS.coverSub}
            fontWeight={900}
            fill={WHITE}
          />
        </Rect>
        {/* left column checks — left-aligned, equal spacing */}
        {[
          {ref: coverChecks[0], y: -40, role: 'check1' as const},
          {ref: coverChecks[1], y: 50, role: 'check2' as const},
          {ref: coverChecks[2], y: 140, role: 'check3' as const},
        ].map(({ref, y, role}) => (
          <Rect key={role} ref={ref} position={[-520, y]} size={[560, 70]} opacity={0} scale={0.9}>
            <Circle position={[-230, 0]} size={46} fill={ORANGE}>
              <Txt text={'✓'} fontFamily={FONT} fontSize={28} fontWeight={900} fill={WHITE} />
            </Circle>
            <Txt
              key={K('cover', role)}
              position={[20, 0]}
              width={460}
              textAlign={'left'}
              text={T('cover', role)}
              fontFamily={FONT}
              fontSize={TS.coverCheck}
              fontWeight={900}
              fill={INK}
            />
          </Rect>
        ))}
        <Img key={K('cover', 'pack')} ref={coverPack} src={A.packGroup} position={[400, 90]} size={[820, 560]} opacity={0} scale={0.85} />
        <Txt
          position={[780, 490]}
          text={T('cover', 'pack_note')} key={K('cover', 'pack_note')}
          fontFamily={FONT}
          fontSize={16}
          fill={MUTED}
        />
      </Rect>

      {/* ===== FLU CONTEXT ===== */}
      <Rect ref={flu} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <Rect
          ref={fluCard1}
          position={[-520, -20]}
          size={[420, 640]}
          radius={28}
          fill={WHITE}
          shadowColor={'rgba(30,50,80,0.12)'}
          shadowBlur={28}
          opacity={0}
          scale={0.9}
        >
          <Img key={K('flu', 'card1_icon_a')} src={A.icon365} position={[0, -190]} size={[200, 200]} />
          <Txt
            position={[0, -40]}
            width={360}
            textAlign={'center'}
            text={T('flu', 'card1_title')} key={K('flu', 'card1_title')}
            fontFamily={FONT}
            fontSize={TS.cardTitle}
            fontWeight={900}
            fill={NAVY}
          />
          <Img key={K('flu', 'card1_icon_b')} src={A.iconTree} position={[0, 100]} size={[200, 200]} />
          <Txt
            position={[0, 240]}
            width={360}
            textAlign={'center'}
            text={T('flu', 'card1_body')} key={K('flu', 'card1_body')}
            fontFamily={FONT}
            fontSize={TS.cardBody}
            fontWeight={800}
            fill={NAVY2}
          />
        </Rect>
        <Rect
          ref={fluCard2}
          position={[0, -20]}
          size={[420, 640]}
          radius={28}
          fill={WHITE}
          shadowColor={'rgba(30,50,80,0.12)'}
          shadowBlur={28}
          opacity={0}
          scale={0.9}
        >
          <Img key={K('flu', 'card2_icon_a')} src={A.iconVirus} position={[0, -210]} size={[120, 120]} />
          <Txt position={[0, -110]} text={T('flu', 'card2_t1')} key={K('flu', 'card2_t1')} fontFamily={FONT} fontSize={TS.cardTitle} fontWeight={900} fill={NAVY} />
          <Img key={K('flu', 'card2_icon_b')} src={A.iconLungs} position={[0, -10]} size={[110, 110]} />
          <Txt position={[0, 80]} text={T('flu', 'card2_t2')} key={K('flu', 'card2_t2')} fontFamily={FONT} fontSize={TS.cardTitle} fontWeight={900} fill={NAVY} />
          <Img key={K('flu', 'card2_icon_c')} src={A.iconWarn} position={[0, 170]} size={[100, 100]} />
          <Txt position={[0, 255]} text={T('flu', 'card2_t3')} key={K('flu', 'card2_t3')} fontFamily={FONT} fontSize={TS.cardTitle} fontWeight={900} fill={NAVY} />
        </Rect>
        <Rect
          ref={fluCard3}
          position={[520, -20]}
          size={[420, 640]}
          radius={28}
          fill={WHITE}
          shadowColor={'rgba(30,50,80,0.12)'}
          shadowBlur={28}
          opacity={0}
          scale={0.9}
        >
          <Img key={K('flu', 'card3_icon')} src={A.iconChina} position={[0, -180]} size={[190, 160]} />
          <Txt
            position={[0, -20]}
            width={360}
            textAlign={'center'}
            text={T('flu', 'card3_num')} key={K('flu', 'card3_num')}
            fontFamily={FONT}
            fontSize={TS.heroNum}
            fontWeight={900}
            fill={ORANGE}
          />
          {/* wrap long line */}
          <Txt
            position={[0, 90]}
            width={340}
            textAlign={'center'}
            text={T('flu', 'card3_body')} key={K('flu', 'card3_body')}
            fontFamily={FONT}
            fontSize={TS.cardBody}
            fontWeight={800}
            fill={NAVY}
          />
        </Rect>
        <Rect ref={flu48} position={[0, 400]} size={[1000, 78]} radius={16} fill={'rgba(255,255,255,0.92)'} opacity={0}>
          <Txt
            text={T('flu', 'footer')} key={K('flu', 'footer')}
            fontFamily={FONT}
            fontSize={TS.cardTitle}
            fontWeight={900}
            fill={NAVY}
          />
          {/* 黄金48h 下划线：入场后扫入一次 */}
          <Line
            ref={flu48Rule}
            points={[
              [-270, 28],
              [270, 28],
            ]}
            stroke={ORANGE}
            lineWidth={5}
            radius={2.5}
            end={0}
          />
        </Rect>
      </Rect>

      {/* chapter only */}
      <Rect ref={chRibbon} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <Img ref={chRibbonImg} src={'/assets/ribbon-chapter-shell-v1.png'} position={[0, 0]} size={[780, 110]} />
        <Txt ref={chTitle} text={''} fontFamily={FONT} fontSize={52} fontWeight={900} fill={WHITE} />
      </Rect>

      {/* ===== BENEFITS ===== */}
      <Rect ref={benefitShell} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <ChapterRibbon text={T('benefit_1', 'chapter')} />
        <NavPill root={navB[0]} n={'1'} text={T('benefit_1', 'nav1')} x={-500} w={380} />
        <NavPill root={navB[1]} n={'2'} text={T('benefit_1', 'nav2')} x={0} w={420} />
        <NavPill root={navB[2]} n={'3'} text={T('benefit_1', 'nav3')} x={520} w={460} />

        <Rect ref={b1} size={[1920, 1080]} opacity={0}>
          <Img key={K('benefit_1', 'pack')} src={A.packGroup} position={[0, 50]} size={[700, 480]} />
          <Rect ref={b1Jia} position={[-430, -20]} size={[200, 200]} opacity={0} scale={0.4} rotation={-18}>
            <Img key={K('benefit_1', 'badge_jia')} src={A.badgeJia} size={[200, 200]} />
            <Txt position={[0, 8]} text={T('benefit_1', 'badge_jia_label')} key={K('benefit_1', 'badge_jia_label')} fontFamily={FONT} fontSize={64} fontWeight={900} fill={NAVY2} />
          </Rect>
          <Rect ref={b1Yi} position={[-220, 120]} size={[170, 170]} opacity={0} scale={0.4} rotation={12}>
            <Img key={K('benefit_1', 'badge_yi')} src={A.badgeYi} size={[170, 170]} />
            <Txt position={[0, 6]} text={T('benefit_1', 'badge_yi_label')} key={K('benefit_1', 'badge_yi_label')} fontFamily={FONT} fontSize={56} fontWeight={900} fill={ORANGE} />
          </Rect>
          {/* bubble text WHITE for contrast on orange bubble */}
          <Rect ref={b1Bubble} position={[430, -10]} size={[420, 340]} opacity={0} scale={0.35} rotation={-14}>
            <Img key={K('benefit_1', 'bubble')} src={A.bubbleSpeech} size={[420, 340]} />
            <Txt
              position={[0, -10]}
              width={280}
              textAlign={'center'}
              text={T('benefit_1', 'bubble_text')} key={K('benefit_1', 'bubble_text')}
              fontFamily={FONT}
              fontSize={TS.bubble}
              fontWeight={900}
              fill={WHITE}
              shadowColor={'rgba(120,60,0,0.35)'}
              shadowBlur={6}
              shadowOffset={[0, 2]}
            />
          </Rect>
        </Rect>

        {/* B2 mechanism + animated viruses */}
        <Rect ref={b2} size={[1920, 1080]} opacity={0}>
          <Rect
            position={[0, 40]}
            size={[1680, 620]}
            radius={28}
            fill={'rgba(255,255,255,0.96)'}
            shadowColor={'rgba(30,50,80,0.10)'}
            shadowBlur={24}
          />
          {/* 左右对比中央分隔线：对照药 reveal 时扫入 */}
          <Line
            ref={b2Divider}
            points={[
              [380, -140],
              [380, 220],
            ]}
            stroke={'#d8dee6'}
            lineWidth={3}
            end={0}
          />
          <Rect ref={dose1} position={[-620, -80]} size={[240, 76]} radius={38} fill={ORANGE} opacity={0} scale={0.8}>
            <Txt text={T('benefit_2', 'dose1')} key={K('benefit_2', 'dose1')} fontFamily={FONT} fontSize={32} fontWeight={900} fill={WHITE} />
          </Rect>
          <Rect position={[-620, 20]} size={[280, 76]} radius={18} fill={ORANGE}>
            <Txt text={T('benefit_2', 'drug_a')} key={K('benefit_2', 'drug_a')} fontFamily={FONT} fontSize={34} fontWeight={900} fill={WHITE} />
          </Rect>
          <Rect ref={dose24} position={[-620, 140]} size={[280, 76]} radius={38} fill={ORANGE2} opacity={0} scale={0.8}>
            <Txt text={T('benefit_2', 'dose24')} key={K('benefit_2', 'dose24')} fontFamily={FONT} fontSize={28} fontWeight={900} fill={WHITE} />
          </Rect>
          <Img ref={cellImg} key={K('benefit_2', 'cell')} src={A.cell} position={[40, 40]} size={[560, 400]} opacity={0} scale={0.85} />
          {/* orbiting viruses for motion */}
          {[
            [-80, -40],
            [40, -90],
            [160, -30],
            [140, 90],
            [20, 120],
            [-90, 70],
          ].map(([x, y], i) => (
            <Img
              key={`v${i}`}
              ref={virusOrbit[i]}
              src={'/assets/icon-virus-v1.png'}
              position={[x, y]}
              size={[56, 56]}
              opacity={0}
            />
          ))}
          <Txt
            ref={mechLeft}
            position={[40, -200]}
            width={520}
            textAlign={'center'}
            text={T('benefit_2', 'mech_left')} key={K('benefit_2', 'mech_left')}
            fontFamily={FONT}
            fontSize={32}
            fontWeight={900}
            fill={ORANGE}
            opacity={0}
          />
          <Rect ref={osel} position={[560, 20]} size={[280, 84]} radius={18} fill={'#8e949c'} opacity={0}>
            <Txt text={T('benefit_2', 'drug_b')} key={K('benefit_2', 'drug_b')} fontFamily={FONT} fontSize={36} fontWeight={900} fill={WHITE} />
          </Rect>
          <Txt
            ref={mechRight}
            position={[560, 140]}
            width={320}
            textAlign={'center'}
            text={T('benefit_2', 'mech_right')} key={K('benefit_2', 'mech_right')}
            fontFamily={FONT}
            fontSize={28}
            fontWeight={800}
            fill={MUTED}
            opacity={0}
          />
        </Rect>

        <Rect ref={b3} size={[1920, 1080]} opacity={0}>
          {/* 地影：主图入场后淡入，z 序在主图之下 */}
          <Circle ref={b3ShadowP} position={[-420, 302]} size={[260, 30]} fill={'rgba(24,42,67,0.16)'} opacity={0} />
          <Circle ref={b3ShadowF} position={[280, 312]} size={[420, 36]} fill={'rgba(24,42,67,0.16)'} opacity={0} />
          <Img ref={patient} key={K('benefit_3', 'patient')} src={A.patient} position={[-420, 40]} size={[320, 520]} opacity={0} scale={0.9} />
          <Img ref={family} key={K('benefit_3', 'family')} src={A.family} position={[280, 20]} size={[580, 580]} opacity={0} scale={0.85} />
          <Txt position={[-420, 340]} text={T('benefit_3', 'patient_label')} key={K('benefit_3', 'patient_label')} fontFamily={FONT} fontSize={32} fontWeight={900} fill={NAVY} />
          <Txt position={[280, 340]} text={T('benefit_3', 'family_label')} key={K('benefit_3', 'family_label')} fontFamily={FONT} fontSize={32} fontWeight={900} fill={NAVY} />
        </Rect>
      </Rect>

      {/* ===== FEATURES ===== */}
      <Rect ref={featShell} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <ChapterRibbon text={T('feature_1', 'chapter')} />
        <NavPill root={navF[0]} n={'1'} text={T('feature_1', 'nav1')} x={-520} w={440} />
        <NavPill root={navF[1]} n={'2'} text={T('feature_1', 'nav2')} x={20} w={480} />
        <NavPill root={navF[2]} n={'3'} text={T('feature_1', 'nav3')} x={500} w={300} />

        {/* F1 safety — larger product */}
        <Rect ref={f1} size={[1920, 1080]} opacity={0}>
          <Img ref={f1Baby} key={K('feature_1', 'icon_baby')} src={A.iconBaby} position={[-560, 0]} size={[180, 180]} opacity={0} />
          <Txt ref={f1LabelL} position={[-560, 140]} text={T('feature_1', 'label_left')} key={K('feature_1', 'label_left')} fontFamily={FONT} fontSize={44} fontWeight={900} fill={NAVY} opacity={0} />
          <Circle
            ref={f1Ring}
            position={[0, 30]}
            size={[620, 620]}
            fill={WHITE}
            stroke={ORANGE2}
            lineWidth={8}
            shadowColor={'rgba(30,50,80,0.14)'}
            shadowBlur={28}
            opacity={0}
            scale={0.85}
          >
            <Img
              ref={packHero}
              key={K('feature_1', 'pack')}
              src={A.packGroup}
              position={[0, 0]}
              size={[520, 380]}
            />
          </Circle>
          <Img ref={f1Shield} key={K('feature_1', 'icon_shield')} src={A.iconShield} position={[560, 0]} size={[160, 160]} opacity={0} />
          <Txt ref={f1LabelR} position={[560, 140]} text={T('feature_1', 'label_right')} key={K('feature_1', 'label_right')} fontFamily={FONT} fontSize={40} fontWeight={900} fill={NAVY} opacity={0} />
        </Rect>

        {/* F2 dual form — 正式交互：中包装常驻 → 左片剂卡片+角标 → 右干混悬+草莓气泡+体重文案 */}
        <Rect ref={f2} size={[1920, 1080]} opacity={0}>
          {/* left tablet card — product photo + dose meta + corner callout */}
          <Rect
            ref={tabPanel}
            position={[-500, 20]}
            size={[400, 520]}
            radius={24}
            fill={WHITE}
            shadowColor={'rgba(30,50,80,0.14)'}
            shadowBlur={26}
            opacity={0}
            scale={0.9}
          >
            <Img key={K('feature_2', 'tablets')} src={A.tablets} position={[0, -50]} size={[320, 320]} />
            {/* dose rows matching reference labels */}
            <Rect position={[-90, 150]} size={[150, 72]} radius={12} fill={'#f7f9fc'}>
              <Txt
                width={140}
                textAlign={'center'}
                text={T('feature_2', 'dose_20')} key={K('feature_2', 'dose_20')}
                fontFamily={FONT}
                fontSize={20}
                fontWeight={800}
                fill={NAVY}
              />
            </Rect>
            <Rect position={[90, 150]} size={[150, 72]} radius={12} fill={'#f7f9fc'}>
              <Txt
                width={140}
                textAlign={'center'}
                text={T('feature_2', 'dose_40')} key={K('feature_2', 'dose_40')}
                fontFamily={FONT}
                fontSize={20}
                fontWeight={800}
                fill={NAVY}
              />
            </Rect>
          </Rect>
          {/* tablet callout — top-left of left card, pops with tablet line */}
          <Rect
            ref={tabBubble}
            position={[-620, -210]}
            size={[200, 96]}
            radius={16}
            fill={ORANGE}
            opacity={0}
            scale={0.6}
            shadowColor={'rgba(180,90,0,0.22)'}
            shadowBlur={14}
          >
            <Txt
              width={180}
              textAlign={'center'}
              text={T('feature_2', 'tab_bubble')} key={K('feature_2', 'tab_bubble')}
              fontFamily={FONT}
              fontSize={26}
              fontWeight={900}
              fill={WHITE}
            />
          </Rect>
          {/* center pack hero — always on when F2 visible；业务可换授权包装图 */}
          <Circle
            position={[0, 20]}
            size={[440, 440]}
            fill={WHITE}
            stroke={ORANGE2}
            lineWidth={8}
            shadowColor={'rgba(30,50,80,0.14)'}
            shadowBlur={28}
          >
            <Img key={K('feature_2', 'pack')} src={A.packGroup} size={[360, 270]} />
          </Circle>
          <Line
            ref={tabLine}
            points={[
              [-290, 20],
              [-220, 20],
            ]}
            stroke={ORANGE}
            lineWidth={5}
            endArrow
            opacity={0}
          />
          {/* right granule card */}
          <Rect
            ref={granPanel}
            position={[500, 20]}
            size={[400, 520]}
            radius={24}
            fill={WHITE}
            shadowColor={'rgba(30,50,80,0.14)'}
            shadowBlur={26}
            opacity={0}
            scale={0.9}
          >
            <Img key={K('feature_2', 'granule')} src={A.granule} position={[0, -40]} size={[320, 320]} />
            <Txt
              position={[0, 180]}
              width={340}
              textAlign={'center'}
              text={T('feature_2', 'granule_label')} key={K('feature_2', 'granule_label')}
              fontFamily={FONT}
              fontSize={24}
              fontWeight={900}
              fill={NAVY}
            />
          </Rect>
          <Line
            ref={strawLine}
            points={[
              [220, 20],
              [290, 20],
            ]}
            stroke={ORANGE}
            lineWidth={5}
            endArrow
            opacity={0}
          />
          {/* strawberry flavor bubble — top-right of right card */}
          <Rect
            ref={strawBubble}
            position={[620, -210]}
            size={[230, 88]}
            radius={44}
            fill={ORANGE}
            opacity={0}
            scale={0.5}
            shadowColor={'rgba(180,90,0,0.22)'}
            shadowBlur={14}
          >
            <Img src={A.iconStrawberry} position={[-72, 0]} size={[44, 44]} />
            <Txt
              key={K('feature_2', 'strawberry')}
              position={[28, 0]}
              text={T('feature_2', 'strawberry')}
              fontFamily={FONT}
              fontSize={28}
              fontWeight={900}
              fill={WHITE}
            />
          </Rect>
        </Rect>

        {/* F3 brand evidence — deeper taller rows */}
        <Rect ref={f3} size={[1920, 1080]} opacity={0}>
          <Rect ref={f3r1} position={[0, -170]} size={[1500, 110]} radius={20} fill={ROW_BG2} opacity={0} scale={0.95}>
            <Img key={K('feature_3', 'icon_flag')} src={A.iconFlag} position={[-640, 0]} size={[72, 72]} />
            <Txt
              position={[40, 0]}
              width={1280}
              text={T('feature_3', 'row1')} key={K('feature_3', 'row1')}
              fontFamily={FONT}
              fontSize={34}
              fontWeight={900}
              fill={NAVY}
            />
          </Rect>
          <Rect ref={f3r2} position={[-360, 0]} size={[680, 120]} radius={20} fill={ROW_BG2} opacity={0} scale={0.95}>
            <Img key={K('feature_3', 'icon_70')} src={A.icon70} position={[-250, 0]} size={[80, 80]} />
            <Txt position={[50, 0]} text={T('feature_3', 'row2')} key={K('feature_3', 'row2')} fontFamily={FONT} fontSize={34} fontWeight={900} fill={NAVY} />
          </Rect>
          <Rect ref={f3r3} position={[360, 0]} size={[680, 120]} radius={20} fill={ROW_BG2} opacity={0} scale={0.95}>
            <Img key={K('feature_3', 'icon_thumb')} src={A.iconThumb} position={[-250, 0]} size={[72, 72]} />
            <Txt
              position={[40, 0]}
              text={T('feature_3', 'row3')} key={K('feature_3', 'row3')}
              fontFamily={FONT}
              fontSize={32}
              fontWeight={900}
              fill={NAVY}
            />
          </Rect>
          <Rect ref={f3r4} position={[0, 170]} size={[1000, 120]} radius={20} fill={ROW_BG2} opacity={0} scale={0.95}>
            <Img key={K('feature_3', 'icon_award')} src={A.iconAward} position={[-380, 0]} size={[80, 80]} />
            <Txt
              position={[40, 0]}
              text={T('feature_3', 'row4')} key={K('feature_3', 'row4')}
              fontFamily={FONT}
              fontSize={36}
              fontWeight={900}
              fill={NAVY}
            />
          </Rect>
        </Rect>
      </Rect>

      {/* ===== AUDIENCE ===== */}
      <Rect ref={audShell} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <ChapterRibbon text={T('audience', 'chapter')} />
        {/* A1: 参考式人物线稿 + 实心橙气泡（非医生工牌） */}
        <Rect ref={a1} size={[1920, 1080]} opacity={0}>
          {/* 地影：人物入场后淡入，z 序在人物之下 */}
          <Circle ref={a1Shadow} position={[-360, 284]} size={[280, 32]} fill={'rgba(24,42,67,0.16)'} opacity={0} />
          <Img
            ref={a1Person}
            key={K('audience', 'person')} src={A.personOutline}
            position={[-360, 40]}
            size={[360, 480]}
          />
          <Rect
            ref={ageBubble}
            position={[320, 20]}
            size={[560, 420]}
            radius={280}
            fill={ORANGE}
            opacity={0}
            scale={0.35}
            rotation={-8}
            shadowColor={'rgba(180,90,0,0.25)'}
            shadowBlur={20}
          >
            <Txt
              position={[0, -70]}
              text={T('audience', 'age')} key={K('audience', 'age')}
              fontFamily={FONT}
              fontSize={78}
              fontWeight={900}
              fill={WHITE}
            />
            <Txt
              position={[0, 55]}
              width={400}
              textAlign={'center'}
              text={T('audience', 'age_body')} key={K('audience', 'age_body')}
              fontFamily={FONT}
              fontSize={28}
              fontWeight={800}
              fill={WHITE}
            />
          </Rect>
        </Rect>
        <Rect ref={a2} size={[1920, 1080]} opacity={0}>
          <Txt
            ref={audHeadline}
            position={[0, -300]}
            width={1680}
            textAlign={'center'}
            text={T('audience', 'headline')} key={K('audience', 'headline')}
            fontFamily={FONT}
            fontSize={30}
            fontWeight={900}
            fill={NAVY}
            opacity={0}
          />
          <Rect
            ref={cardElder}
            position={[-480, 60]}
            size={[400, 520]}
            radius={24}
            fill={WHITE}
            shadowColor={'rgba(30,50,80,0.12)'}
            shadowBlur={22}
            opacity={0}
            scale={0.9}
          >
            <Img key={K('audience', 'elder_img')} src={A.charElder} position={[0, -40]} size={[260, 360]} />
            <Txt position={[0, 200]} text={T('audience', 'elder_label')} key={K('audience', 'elder_label')} fontFamily={FONT} fontSize={32} fontWeight={900} fill={NAVY} />
          </Rect>
          <Rect
            ref={cardChild}
            position={[0, 60]}
            size={[400, 520]}
            radius={24}
            fill={WHITE}
            shadowColor={'rgba(30,50,80,0.12)'}
            shadowBlur={22}
            opacity={0}
            scale={0.9}
          >
            <Img key={K('audience', 'child_img')} src={A.charChild} position={[0, -40]} size={[260, 360]} />
            <Txt position={[0, 200]} text={T('audience', 'child_label')} key={K('audience', 'child_label')} fontFamily={FONT} fontSize={32} fontWeight={900} fill={NAVY} />
          </Rect>
          <Rect
            ref={cardChronic}
            position={[480, 60]}
            size={[400, 520]}
            radius={24}
            fill={WHITE}
            shadowColor={'rgba(30,50,80,0.12)'}
            shadowBlur={22}
            opacity={0}
            scale={0.9}
          >
            <Img key={K('audience', 'chronic_img')} src={A.charChronic} position={[0, -50]} size={[340, 300]} />
            <Txt
              position={[0, 200]}
              width={360}
              textAlign={'center'}
              text={T('audience', 'chronic_label')} key={K('audience', 'chronic_label')}
              fontFamily={FONT}
              fontSize={30}
              fontWeight={900}
              fill={NAVY}
            />
          </Rect>
        </Rect>
      </Rect>

      {/* ===== COMBO ===== */}
      <Rect ref={comboShell} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <ChapterRibbon text={T('combo_1', 'chapter')} />
        <NavPill root={navC[0]} n={'1'} text={T('combo_1', 'nav1')} x={-360} w={580} />
        <NavPill root={navC[1]} n={'2'} text={T('combo_1', 'nav2')} x={380} w={660} />

        <Rect ref={c1} size={[1920, 1080]} opacity={0}>
          {/* efficacy ABOVE products */}
          <Txt
            ref={comboNote1}
            position={[0, -200]}
            width={1400}
            textAlign={'center'}
            text={T('combo_1', 'note')} key={K('combo_1', 'note')}
            fontFamily={FONT}
            fontSize={36}
            fontWeight={900}
            fill={NAVY}
            opacity={0}
          />
          {/* note 下划线：note 入场后扫入 */}
          <Line
            ref={comboRule1}
            points={[
              [-comboRuleHalf1, -162],
              [comboRuleHalf1, -162],
            ]}
            stroke={ORANGE}
            lineWidth={4}
            radius={2}
            end={0}
          />
          <Rect ref={comboStage1} position={[0, 80]} size={[1600, 480]} radius={28} fill={'rgba(255,255,255,0.96)'}>
            {/* 包装：clip 层内高光扫过一次 */}
            <Layout clip position={[-360, 0]} size={[560, 400]}>
              <Img key={K('combo_1', 'pack')} src={A.packGroup} size={[560, 400]} />
              <Rect ref={comboSweep1} position={[-700, 0]} size={[110, 560]} rotation={18} fill={'rgba(255,255,255,0.55)'} />
            </Layout>
            {/* plus 弹入后连线 draw（z 序在 plus 之下） */}
            <Line
              ref={comboLine1}
              points={[
                [-70, 0],
                [150, 0],
              ]}
              stroke={ORANGE2}
              lineWidth={4}
              end={0}
            />
            <Txt ref={plus1} position={[0, 0]} text={'+'} fontFamily={FONT} fontSize={110} fontWeight={900} fill={ORANGE} opacity={0} scale={0.5} />
            <Img key={K('combo_1', 'other')} src={A.boxFever} position={[360, 0]} size={[400, 280]} />
          </Rect>
        </Rect>
        <Rect ref={c2} size={[1920, 1080]} opacity={0}>
          <Txt
            ref={comboNote2}
            position={[0, -200]}
            width={1400}
            textAlign={'center'}
            text={T('combo_2', 'note')} key={K('combo_2', 'note')}
            fontFamily={FONT}
            fontSize={36}
            fontWeight={900}
            fill={NAVY}
            opacity={0}
          />
          <Line
            ref={comboRule2}
            points={[
              [-comboRuleHalf2, -162],
              [comboRuleHalf2, -162],
            ]}
            stroke={ORANGE}
            lineWidth={4}
            radius={2}
            end={0}
          />
          <Rect ref={comboStage2} position={[0, 80]} size={[1600, 480]} radius={28} fill={'rgba(255,255,255,0.96)'}>
            <Layout clip position={[-360, 0]} size={[560, 400]}>
              <Img key={K('combo_2', 'pack')} src={A.packGroup} size={[560, 400]} />
              <Rect ref={comboSweep2} position={[-700, 0]} size={[110, 560]} rotation={18} fill={'rgba(255,255,255,0.55)'} />
            </Layout>
            <Line
              ref={comboLine2}
              points={[
                [-70, 0],
                [150, 0],
              ]}
              stroke={ORANGE2}
              lineWidth={4}
              end={0}
            />
            <Txt ref={plus2} position={[0, 0]} text={'+'} fontFamily={FONT} fontSize={110} fontWeight={900} fill={ORANGE} opacity={0} scale={0.5} />
            <Img key={K('combo_2', 'other')} src={A.boxChronic} position={[360, 0]} size={[400, 280]} />
          </Rect>
        </Rect>
      </Rect>

      {/* ===== SUMMARY ===== */}
      <Rect ref={summary} size={[1920, 1080]} opacity={0}>
        <LogoMark />
        <Img ref={smHand} key={K('summary', 'icon_hand')} src={A.iconHand} position={[-780, -430]} size={[100, 100]} opacity={0} />
        <Txt ref={smEyebrow} position={[-680, -430]} text={T('summary', 'eyebrow')} key={K('summary', 'eyebrow')} fontFamily={FONT} fontSize={32} fontWeight={900} fill={ORANGE} opacity={0} />
        <ChapterRibbon text={T('summary', 'chapter')} />
        <Rect ref={smHead} position={[0, -300]} size={[1680, 70]} fill={ORANGE} opacity={0}>
          {(['col_h1', 'col_h2', 'col_h3', 'col_h4'] as const).map((role, i) => (
            <Txt
              key={K('summary', role)}
              position={[-630 + i * 420, 0]}
              text={T('summary', role)}
              fontFamily={FONT}
              fontSize={34}
              fontWeight={900}
              fill={WHITE}
            />
          ))}
        </Rect>
        <Rect position={[0, 40]} size={[1680, 620]} fill={'rgba(255,255,255,0.96)'} stroke={'#e8edf2'} lineWidth={2}>
          <Line points={[[-420, -310], [-420, 310]]} stroke={'#e8edf2'} lineWidth={2} />
          <Line points={[[0, -310], [0, 310]]} stroke={'#e8edf2'} lineWidth={2} />
          <Line points={[[420, -310], [420, 310]]} stroke={'#e8edf2'} lineWidth={2} />
          <Line points={[[-840, -100], [840, -100]]} stroke={'#e8edf2'} lineWidth={2} />
          <Line points={[[-840, 100], [840, 100]]} stroke={'#e8edf2'} lineWidth={2} />
          <Txt ref={smE1} key={K('summary', 'e1')} position={[-630, -200]} width={380} textAlign={'center'} text={T('summary', 'e1')} fontFamily={FONT} fontSize={30} fontWeight={900} fill={ORANGE} opacity={0} />
          <Txt ref={smE2} key={K('summary', 'e2')} position={[-630, 0]} width={380} textAlign={'center'} text={T('summary', 'e2')} fontFamily={FONT} fontSize={30} fontWeight={900} fill={ORANGE} opacity={0} />
          <Txt ref={smE3} key={K('summary', 'e3')} position={[-630, 200]} width={380} textAlign={'center'} text={T('summary', 'e3')} fontFamily={FONT} fontSize={28} fontWeight={900} fill={ORANGE} opacity={0} />
          <Txt ref={smF1} position={[-210, -200]} width={380} textAlign={'center'} text={T('summary', 'f1')} key={K('summary', 'f1')} fontFamily={FONT} fontSize={26} fontWeight={800} fill={NAVY} opacity={0} />
          <Txt ref={smF2} position={[-210, 0]} width={380} textAlign={'center'} text={T('summary', 'f2')} key={K('summary', 'f2')} fontFamily={FONT} fontSize={26} fontWeight={800} fill={NAVY} opacity={0} />
          <Txt ref={smF3} position={[-210, 200]} width={380} textAlign={'center'} text={T('summary', 'f3')} key={K('summary', 'f3')} fontFamily={FONT} fontSize={26} fontWeight={800} fill={NAVY} opacity={0} />
          {/* 适宜人群列：参考式多行，避免溢出 */}
          <Txt
            ref={smA1}
            key={K('summary', 'a1')}
            position={[210, -10]}
            width={360}
            textAlign={'center'}
            text={T('summary', 'a1')}
            fontFamily={FONT}
            fontSize={20}
            fontWeight={800}
            fill={ORANGE}
            lineHeight={28}
            opacity={0}
          />
          <Txt
            ref={smC1}
            position={[630, 0]}
            width={360}
            textAlign={'center'}
            text={T('summary', 'c1')} key={K('summary', 'c1')}
            fontFamily={FONT}
            fontSize={22}
            fontWeight={800}
            fill={NAVY}
            lineHeight={30}
            opacity={0}
          />
        </Rect>
      </Rect>

      <Rect ref={capBar} position={[0, 468]} size={[1700, 64]} opacity={0}>
        <Txt
          ref={capTxt}
          width={1600}
          textAlign={'center'}
          fontFamily={FONT}
          fontSize={TS.caption}
          fontWeight={900}
          fill={INK}
          opacity={0}
        />
      </Rect>
    </>,
  );

  // B2 病毒椭圆轨道：各异 rx/ry、相位错 1/6 圈，围绕 cell(40,40)；cell 主视觉保持静止
  const ORBITS = [
    {rx: 210, ry: 95},
    {rx: 250, ry: 120},
    {rx: 290, ry: 105},
    {rx: 320, ry: 140},
    {rx: 230, ry: 150},
    {rx: 270, ry: 85},
  ].map((o, i) => ({...o, cx: 40, cy: 40, phase: (i * Math.PI) / 3}));

  // 8 段关键帧线性逼近椭圆；seconds 内整圈摊派（不悬挂 loop，避免吃掉后续 until 锚点）
  function* orbitAll(seconds: number) {
    const laps = Math.max(1, Math.floor(seconds / 6));
    const step = seconds / (laps * 8);
    for (let s = 1; s <= laps * 8; s++) {
      yield* all(
        ...virusOrbit.map((v, i) => {
          const p = ORBITS[i];
          const a = p.phase + (s / 8) * Math.PI * 2;
          return all(
            v().position.x(p.cx + p.rx * Math.cos(a), step, linear),
            v().position.y(p.cy + p.ry * Math.sin(a), step, linear),
          );
        }),
      );
    }
  }

  function* visuals() {
    let clock = 0;
    function* until(target: number) {
      const gap = target - clock;
      if (gap > 0.001) yield* waitFor(gap);
      clock = Math.max(clock, target);
    }
    function* anim(seconds: number, task: any) {
      yield* all(task, waitFor(seconds));
      clock += seconds;
    }

    // 定向滑出：opacity + x∓50（dir -1 左 / +1 右），时长沿用原锚点空档
    function slideOut(sec: number, dir: number, ...refs: R[]) {
      return all(
        ...refs.map(r =>
          all(r().opacity(0, sec), r().position.x(50 * dir, sec, easeInCubic)),
        ),
      );
    }

    // 章节过场：ribbon + 标题自左扫入 / 向右扫出（LogoMark 不参与）
    function* chapterShow(title: string) {
      chTitle().text(title);
      chRibbon().opacity(1);
      chRibbonImg().position.x(-60);
      chRibbonImg().opacity(0);
      chTitle().position.x(-60);
      chTitle().opacity(0);
      yield* all(
        chRibbonImg().position.x(0, 0.32, easeOutCubic),
        chRibbonImg().opacity(1, 0.22),
        chTitle().position.x(0, 0.32, easeOutCubic),
        chTitle().opacity(1, 0.22),
      );
    }

    function* chapterHide() {
      yield* all(
        chRibbonImg().position.x(60, 0.26, easeInCubic),
        chRibbonImg().opacity(0, 0.26),
        chTitle().position.x(60, 0.26, easeInCubic),
        chTitle().opacity(0, 0.26),
      );
      chRibbon().opacity(0);
      chRibbonImg().position.x(0);
      chRibbonImg().opacity(1);
      chTitle().position.x(0);
      chTitle().opacity(1);
    }

    // B2 页锚点序列：与轨道并行，直至 29.55
    function* b2Anchors() {
      yield* until(19.5);
      yield* anim(0.2, all(dose24().opacity(1, 0.16), dose24().scale(1, 0.2, easeOutBack)));
      yield* until(21.5);
      yield* anim(
        0.35,
        all(
          osel().opacity(1, 0.18),
          mechRight().opacity(1, 0.18),
          b2Divider().end(1, 0.35, easeInOutCubic),
        ),
      );
      yield* until(29.55);
    }

    // 短封面后进入流感（克隆轨 0.06s 起口播）
    cover().opacity(1);
    yield* anim(
      0.22,
      all(
        coverChecks[0]().opacity(1, 0.14),
        coverChecks[0]().scale(1, 0.18, easeOutBack),
        coverPack().opacity(1, 0.18),
        coverPack().scale(1, 0.22, easeOutBack),
      ),
    );
    yield* anim(0.16, all(coverChecks[1]().opacity(1, 0.12), coverChecks[1]().scale(1, 0.16, easeOutBack)));
    yield* anim(0.16, all(coverChecks[2]().opacity(1, 0.12), coverChecks[2]().scale(1, 0.16, easeOutBack)));
    yield* until(0.45);
    yield* anim(0.1, slideOut(0.1, -1, cover));

    // flu 0.5–10.9
    flu().opacity(1);
    yield* anim(0.24, all(fluCard1().opacity(1, 0.2), fluCard1().scale(1, 0.24, easeOutBack)));
    yield* until(2.0);
    yield* anim(0.24, all(fluCard2().opacity(1, 0.2), fluCard2().scale(1, 0.24, easeOutBack)));
    yield* until(3.5);
    yield* anim(0.24, all(fluCard3().opacity(1, 0.2), fluCard3().scale(1, 0.24, easeOutBack)));
    yield* until(5.5);
    yield* anim(0.2, flu48().opacity(1, 0.2));
    // 死区填充：48h 下划线扫入 + 横幅单次 pulse
    yield* anim(0.45, flu48Rule().end(1, 0.45, easeInOutCubic));
    yield* anim(0.22, flu48().scale(1.06, 0.22, easeOutCubic));
    yield* anim(0.28, flu48().scale(1, 0.28, easeInOutCubic));
    yield* until(10.85);
    yield* anim(0.12, slideOut(0.12, 1, flu));

    // 章节 + B1 专治甲乙流 10.97–13.86
    yield* anim(0.32, chapterShow('一、三大核心功效'));
    yield* until(12.35);
    yield* anim(0.26, chapterHide());

    benefitShell().opacity(1);
    navB.forEach(n => n().opacity(1));
    yield* anim(0.12, all(setNav(navB, 0), b1().opacity(1, 0.12)));
    yield* anim(
      0.26,
      all(
        b1Jia().opacity(1, 0.18),
        b1Jia().scale(1, 0.26, easeOutBack),
        b1Jia().rotation(-8, 0.26, easeOutBack),
        b1Yi().opacity(1, 0.18),
        b1Yi().scale(1, 0.26, easeOutBack),
        b1Yi().rotation(6, 0.26, easeOutBack),
      ),
    );
    yield* anim(
      0.3,
      all(
        b1Bubble().opacity(1, 0.16),
        b1Bubble().scale(1, 0.3, easeOutBack),
        b1Bubble().rotation(-6, 0.3, easeOutBack),
      ),
    );
    yield* until(13.85);
    yield* anim(0.1, slideOut(0.1, -1, b1));

    // B2 14.0–29.6：病毒左右对撞入场 → 椭圆轨道至页末
    virusOrbit.forEach((v, i) => {
      const p = ORBITS[i];
      v().position([i % 2 === 0 ? -1000 : 1000, p.cy + p.ry * Math.sin(p.phase)]);
      v().opacity(0);
      v().scale(1);
      v().rotation(0);
    });
    yield* anim(0.12, all(setNav(navB, 1), b2().opacity(1, 0.12)));
    yield* anim(0.22, all(dose1().opacity(1, 0.18), dose1().scale(1, 0.22, easeOutBack)));
    yield* anim(
      0.28,
      all(cellImg().opacity(1, 0.2), cellImg().scale(1, 0.24, easeOutBack), mechLeft().opacity(1, 0.2)),
    );
    yield* anim(
      0.4,
      all(
        ...virusOrbit.map((v, i) => {
          const p = ORBITS[i];
          return all(
            v().position.x(p.cx + p.rx * Math.cos(p.phase), 0.4, easeOutCubic),
            v().position.y(p.cy + p.ry * Math.sin(p.phase), 0.4, easeOutCubic),
            v().opacity(0.95, 0.25),
          );
        }),
      ),
    );
    yield* all(b2Anchors(), orbitAll(29.55 - clock));
    yield* anim(0.1, slideOut(0.1, 1, b2));

    // B3 29.6–37.0
    yield* anim(0.12, all(setNav(navB, 2), b3().opacity(1, 0.12)));
    yield* anim(
      0.28,
      all(
        patient().opacity(1, 0.2),
        patient().scale(1, 0.24, easeOutBack),
        family().opacity(1, 0.24),
        family().scale(1, 0.28, easeOutBack),
      ),
    );
    // 地影淡入 + 单次确认 pulse
    yield* anim(0.2, all(b3ShadowP().opacity(1, 0.2), b3ShadowF().opacity(1, 0.2)));
    yield* anim(0.2, all(patient().scale(1.04, 0.2, easeOutCubic), family().scale(1.04, 0.2, easeOutCubic)));
    yield* anim(0.3, all(patient().scale(1, 0.3, easeInOutCubic), family().scale(1, 0.3, easeInOutCubic)));
    yield* until(36.9);
    yield* anim(0.1, slideOut(0.1, -1, benefitShell));

    // 产品特点章 + F1 安全 37.0–42.65
    yield* anim(0.32, chapterShow('二、产品特点'));
    yield* until(38.0);
    yield* anim(0.26, chapterHide());
    featShell().opacity(1);
    navF.forEach(n => n().opacity(1));
    f1Baby().position.x(-640);
    f1Shield().position.x(640);
    yield* anim(0.12, all(setNav(navF, 0), f1().opacity(1, 0.12)));
    // F1 完整入场：左 icon 滑入 → 圆环 pop → 右 icon 滑入 → 双向 nudge 12px
    yield* anim(
      0.3,
      all(f1Baby().position.x(-560, 0.3, easeOutCubic), f1Baby().opacity(1, 0.25), f1LabelL().opacity(1, 0.3)),
    );
    yield* anim(0.35, all(f1Ring().opacity(1, 0.2), f1Ring().scale(1, 0.35, easeOutBack)));
    yield* anim(
      0.3,
      all(f1Shield().position.x(560, 0.3, easeOutCubic), f1Shield().opacity(1, 0.25), f1LabelR().opacity(1, 0.3)),
    );
    yield* anim(0.2, all(f1Baby().position.x(-548, 0.2, easeInOutCubic), f1Shield().position.x(548, 0.2, easeInOutCubic)));
    yield* anim(0.24, all(f1Baby().position.x(-560, 0.24, easeInOutCubic), f1Shield().position.x(560, 0.24, easeInOutCubic)));
    yield* until(42.55);
    yield* anim(0.1, slideOut(0.1, 1, f1));

    // F2 双剂型 42.65–51.43
    yield* anim(0.12, all(setNav(navF, 1), f2().opacity(1, 0.12)));
    yield* until(43.2);
    yield* anim(
      0.3,
      all(
        tabPanel().opacity(1, 0.24),
        tabPanel().scale(1, 0.28, easeOutBack),
        granPanel().opacity(0.55, 0.24),
        granPanel().scale(0.96, 0.28, easeOutCubic),
      ),
    );
    yield* until(45.1);
    yield* anim(
      0.28,
      all(
        tabPanel().scale(1.04, 0.24, easeOutBack),
        tabLine().opacity(1, 0.18),
        tabBubble().opacity(1, 0.2),
        tabBubble().scale(1, 0.28, easeOutBack),
        granPanel().opacity(0.45, 0.18),
      ),
    );
    yield* until(46.8);
    yield* anim(
      0.28,
      all(
        tabPanel().scale(1, 0.18),
        granPanel().opacity(1, 0.22),
        granPanel().scale(1.04, 0.26, easeOutBack),
        strawLine().opacity(1, 0.18),
        strawBubble().opacity(1, 0.22),
        strawBubble().scale(1, 0.28, easeOutBack),
      ),
    );
    yield* until(48.5);
    yield* anim(0.18, all(granPanel().scale(1, 0.16), strawBubble().scale(1.05, 0.16, easeOutBack)));
    yield* until(51.35);
    yield* anim(0.1, slideOut(0.1, -1, f2));

    // F3 原研 51.43–62.4
    yield* anim(0.12, all(setNav(navF, 2), f3().opacity(1, 0.12)));
    yield* anim(0.22, all(f3r1().opacity(1, 0.18), f3r1().scale(1, 0.22, easeOutBack)));
    yield* until(55.5);
    yield* anim(0.18, all(f3r2().opacity(1, 0.16), f3r2().scale(1, 0.18, easeOutBack)));
    yield* until(57.2);
    yield* anim(0.18, all(f3r3().opacity(1, 0.16), f3r3().scale(1, 0.18, easeOutBack)));
    yield* until(59.5);
    yield* anim(0.22, all(f3r4().opacity(1, 0.18), f3r4().scale(1, 0.22, easeOutBack)));
    yield* until(62.3);
    yield* anim(0.1, slideOut(0.1, 1, featShell));

    // 适宜人群 62.4–68.36 A1；68.36–74.95 A2
    yield* anim(0.32, chapterShow('三、适宜人群'));
    yield* until(63.4);
    yield* anim(0.26, chapterHide());
    audShell().opacity(1);
    yield* anim(0.12, a1().opacity(1, 0.12));
    yield* anim(
      0.32,
      all(
        ageBubble().opacity(1, 0.2),
        ageBubble().scale(1, 0.3, easeOutBack),
        ageBubble().rotation(-4, 0.3, easeOutBack),
      ),
    );
    // 地影淡入 + 人物单次确认 pulse
    yield* anim(0.2, a1Shadow().opacity(1, 0.2));
    yield* anim(0.2, a1Person().scale(1.04, 0.2, easeOutCubic));
    yield* anim(0.3, a1Person().scale(1, 0.3, easeInOutCubic));
    yield* until(68.25);
    yield* anim(0.1, slideOut(0.1, -1, a1));

    a2().opacity(1);
    yield* anim(0.2, audHeadline().opacity(1, 0.2));
    yield* anim(0.22, all(cardElder().opacity(1, 0.18), cardElder().scale(1, 0.22, easeOutBack)));
    yield* until(70.7);
    yield* anim(0.22, all(cardChild().opacity(1, 0.18), cardChild().scale(1, 0.22, easeOutBack)));
    yield* until(72.3);
    yield* anim(0.22, all(cardChronic().opacity(1, 0.18), cardChronic().scale(1, 0.22, easeOutBack)));
    yield* until(74.85);
    yield* anim(0.1, slideOut(0.1, 1, audShell));

    // 联合用药 75.0–82.95 / 83.0–89.85
    yield* anim(0.32, chapterShow('三、联合用药'));
    yield* until(75.95);
    yield* anim(0.26, chapterHide());
    comboShell().opacity(1);
    navC.forEach(n => n().opacity(1));
    yield* anim(0.12, all(setNav(navC, 0), c1().opacity(1, 0.12)));
    yield* anim(0.18, comboNote1().opacity(1, 0.18));
    yield* anim(0.22, all(plus1().opacity(1, 0.16), plus1().scale(1, 0.22, easeOutBack)));
    // plus 后：连线 draw → note 下划线扫入 → 包装高光扫过
    yield* anim(0.35, comboLine1().end(1, 0.35, easeInOutCubic));
    yield* anim(0.3, comboRule1().end(1, 0.3, easeInOutCubic));
    yield* anim(0.65, comboSweep1().position.x(700, 0.65, easeInOutCubic));
    yield* until(82.85);
    yield* anim(0.1, slideOut(0.1, -1, c1));

    yield* anim(0.12, all(setNav(navC, 1), c2().opacity(1, 0.12)));
    yield* anim(0.18, comboNote2().opacity(1, 0.18));
    yield* anim(0.22, all(plus2().opacity(1, 0.16), plus2().scale(1, 0.22, easeOutBack)));
    yield* anim(0.35, comboLine2().end(1, 0.35, easeInOutCubic));
    yield* anim(0.3, comboRule2().end(1, 0.3, easeInOutCubic));
    yield* anim(0.65, comboSweep2().position.x(700, 0.65, easeInOutCubic));
    yield* until(89.75);
    yield* anim(0.1, slideOut(0.1, 1, comboShell));

    // 总结 89.85–93.2：整页框架 → eyebrow → 表头 → 3 数据行级联 → 92.4 收束
    yield* anim(0.32, chapterShow('总结'));
    yield* until(90.15);
    yield* anim(0.26, chapterHide());
    smHead().position.y(-282);
    const smRow1: Array<[T, number]> = [
      [smE1, -200],
      [smF1, -200],
    ];
    const smRow2: Array<[T, number]> = [
      [smE2, 0],
      [smF2, 0],
      [smA1, -10],
    ];
    const smRow3: Array<[T, number]> = [
      [smE3, 200],
      [smF3, 200],
      [smC1, 0],
    ];
    [smRow1, smRow2, smRow3].forEach(row => row.forEach(([r, y]) => r().position.y(y + 18)));
    yield* anim(0.18, summary().opacity(1, 0.18));
    yield* anim(0.25, all(smHand().opacity(1, 0.2), smEyebrow().opacity(1, 0.2)));
    yield* anim(0.25, all(smHead().opacity(1, 0.2), smHead().position.y(-300, 0.25, easeOutCubic)));
    for (const row of [smRow1, smRow2, smRow3]) {
      yield* anim(
        0.22,
        all(...row.map(([r, y]) => all(r().opacity(1, 0.18), r().position.y(y, 0.22, easeOutCubic)))),
      );
    }
    yield* until(92.4);
    yield* anim(
      0.4,
      all(summary().scale(0.995, 0.4, easeInOutCubic), summary().opacity(0.92, 0.4, easeInOutCubic)),
    );
    yield* until(DURATION);
  }

  yield* all(
    visuals(),
    runCaptions(capBar, capTxt),
    applyEditablePatches(view, DURATION),
  );
});

export default makeProject({
  scenes: [scene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
    },
  },
});
