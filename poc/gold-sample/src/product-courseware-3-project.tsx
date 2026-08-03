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
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../product-courseware-3.json';

type Cue = {start: number; end: number; text: string};
type RectRef = Reference<Rect>;
type TxtRef = Reference<Txt>;
type ImgRef = Reference<Img>;
type CircleRef = Reference<Circle>;

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const DURATION = Number(data.duration);
const cues = data.cues as Cue[];

const NAVY = '#123c78';
const NAVY2 = '#22579b';
const ORANGE = '#e98200';
const ORANGE2 = '#f4a437';
const CORAL = '#e65d6f';
const PINK = '#fce8ec';
const INK = '#182a43';
const MUTED = '#617389';
const WHITE = '#ffffff';
const GRAY = '#cfd4da';

function NavItem({
  root,
  number,
  text,
  x,
  width,
}: {
  root: RectRef;
  number: string;
  text: string;
  x: number;
  width: number;
}) {
  return (
    <Rect
      ref={root}
      position={[x, -366]}
      size={[width, 66]}
      radius={32}
      fill={GRAY}
      stroke={'rgba(110,120,132,0.22)'}
      lineWidth={2}
    >
      <Circle
        position={[-width / 2 + 33, 0]}
        size={46}
        fill={WHITE}
        stroke={'rgba(120,130,142,0.5)'}
        lineWidth={2}
      >
        <Txt
          text={number}
          fontFamily={FONT}
          fontSize={24}
          fontWeight={850}
          fill={ORANGE}
        />
      </Circle>
      <Txt
        position={[20, 0]}
        width={width - 78}
        text={text}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={27}
        fontWeight={820}
        fill={WHITE}
      />
    </Rect>
  );
}

function* setActiveNav(nav: RectRef[], active: number) {
  yield* all(
    ...nav.map((item, index) =>
      all(
        item().fill(index === active ? ORANGE : GRAY, 0.22),
        item().scale(index === active ? 1.035 : 1, 0.22, easeOutCubic),
      ),
    ),
  );
}

function* runSubtitles(text: TxtRef, bar: RectRef) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      text().opacity(0);
      bar().opacity(0);
      yield* waitFor(cue.start - cursor);
    }
    text().text(cue.text);
    yield* all(bar().opacity(0.94, 0.06), text().opacity(1, 0.06));
    yield* waitFor(Math.max(0, cue.end - cue.start - 0.06));
    text().opacity(0);
    bar().opacity(0);
    cursor = cue.end;
  }
  if (cursor < DURATION) yield* waitFor(DURATION - cursor);
}

const scene = makeScene2D('product-courseware-3', function* (view) {
  const background = createRef<Img>();
  const chrome = createRef<Rect>();
  const nav = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const page1 = createRef<Rect>();
  const page2 = createRef<Rect>();
  const page3 = createRef<Rect>();
  const page4 = createRef<Rect>();
  const pack1 = createRef<Img>();
  const pack2 = createRef<Img>();
  const dose = createRef<Circle>();
  const routeArrow = createRef<Rect>();
  const oneDay = createRef<Txt>();
  const cell = createRef<Circle>();
  const blockArrow = createRef<Rect>();
  const releaseArrow = createRef<Line>();
  const traditional = createRef<Rect>();
  const family = createRef<Img>();
  const familyCallout = createRef<Rect>();
  const subtitleBar = createRef<Rect>();
  const subtitle = createRef<Txt>();
  const virus = [0, 1, 2, 3, 4].map(() => createRef<Circle>());

  view.add(
    <>
      <Img
        ref={background}
        src={data.assets.background}
        size={[1920, 1080]}
        scale={1.015}
      />
      <Audio src={data.audio.file} play />

      <Rect ref={chrome} size={[1920, 1080]} opacity={0}>
        <Rect
          position={[0, -478]}
          size={[660, 82]}
          radius={24}
          fill={ORANGE}
          stroke={ORANGE2}
          lineWidth={2}
          shadowColor={'rgba(105,75,20,0.18)'}
          shadowBlur={18}
        >
          <Txt
            text={'一、三大核心功效'}
            fontFamily={FONT}
            fontSize={44}
            fontWeight={900}
            fill={WHITE}
          />
        </Rect>
        <NavItem root={nav[0]} number={'1'} text={'专治甲流、乙流'} x={-560} width={430} />
        <NavItem root={nav[1]} number={'2'} text={'全程1次，1天退热'} x={-70} width={450} />
        <NavItem root={nav[2]} number={'3'} text={'治疗自己，保护身边人'} x={470} width={520} />
        <Txt
          position={[830, -490]}
          text={'模板示例'}
          fontFamily={FONT}
          fontSize={20}
          fontWeight={580}
          fill={'#7f8fa2'}
        />
      </Rect>

      <Rect ref={page1} size={[1920, 1080]} opacity={0}>
        <Txt
          position={[-460, -190]}
          width={980}
          text={'针对甲流、乙流的抗流感治疗路径'}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={56}
          fontWeight={900}
          fill={NAVY}
        />
        <Txt
          position={[-480, -118]}
          width={940}
          text={'先识别流感类型，再进入完整疗程说明'}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={31}
          fontWeight={540}
          fill={MUTED}
        />
        <Circle position={[-680, 100]} size={220} fill={'#fff4e7'} stroke={ORANGE2} lineWidth={5}>
          <Txt text={'甲流'} fontFamily={FONT} fontSize={48} fontWeight={900} fill={ORANGE} />
          <Txt position={[0, 52]} text={'A 型流感'} fontFamily={FONT} fontSize={23} fontWeight={560} fill={MUTED} />
        </Circle>
        <Circle position={[-400, 100]} size={220} fill={'#eef4fd'} stroke={NAVY2} lineWidth={5}>
          <Txt text={'乙流'} fontFamily={FONT} fontSize={48} fontWeight={900} fill={NAVY} />
          <Txt position={[0, 52]} text={'B 型流感'} fontFamily={FONT} fontSize={23} fontWeight={560} fill={MUTED} />
        </Circle>
        <Circle position={[520, 30]} size={500} fill={'rgba(255,255,255,0.72)'} stroke={'#f2c870'} lineWidth={6} />
        <Img ref={pack1} src={data.assets.packshot} position={[520, -10]} size={[310, 310]} opacity={0} scale={0.3} />
        <Rect position={[520, 240]} size={[240, 46]} radius={22} fill={ORANGE}>
          <Txt text={'包装示意 · 可替换'} fontFamily={FONT} fontSize={21} fontWeight={800} fill={WHITE} />
        </Rect>
      </Rect>

      <Rect ref={page2} size={[1920, 1080]} opacity={0}>
        <Txt position={[-475, -190]} width={900} text={'全程一次，一天退热'} textAlign={'left'} fontFamily={FONT} fontSize={64} fontWeight={900} fill={NAVY} />
        <Txt position={[-480, -110]} width={900} text={'全程仅需口服 1 次，早期阻断病毒复制。'} textAlign={'left'} fontFamily={FONT} fontSize={33} fontWeight={540} fill={MUTED} />
        <Circle ref={dose} position={[-620, 125]} size={330} fill={'#fff8ef'} stroke={ORANGE} lineWidth={7} opacity={0} scale={0.6}>
          <Txt position={[-8, -25]} text={'1'} fontFamily={FONT} fontSize={122} fontWeight={900} fill={ORANGE} />
          <Txt position={[70, -8]} text={'次'} fontFamily={FONT} fontSize={46} fontWeight={900} fill={NAVY} />
          <Txt position={[0, 85]} text={'全程口服'} fontFamily={FONT} fontSize={31} fontWeight={820} fill={NAVY} />
        </Circle>
        <Rect ref={routeArrow} position={[-225, 135]} size={[250, 82]} radius={18} fill={ORANGE} opacity={0} scale={0.6}>
          <Txt text={'早期阻断  →'} fontFamily={FONT} fontSize={31} fontWeight={860} fill={WHITE} />
        </Rect>
        <Circle position={[505, 30]} size={510} fill={'rgba(255,255,255,0.74)'} stroke={'#f2c870'} lineWidth={5} />
        <Img ref={pack2} src={data.assets.packshot} position={[505, -55]} size={[290, 290]} opacity={0} scale={0.45} />
        <Txt ref={oneDay} position={[505, 170]} text={'1 天'} fontFamily={FONT} fontSize={94} fontWeight={900} fill={ORANGE} opacity={0} scale={0.6} />
        <Txt position={[505, 245]} text={'快速退热'} fontFamily={FONT} fontSize={40} fontWeight={850} fill={NAVY} />
      </Rect>

      <Rect ref={page3} size={[1920, 1080]} opacity={0}>
        <Txt position={[-455, -198]} width={980} text={'从源头遏制新病毒生成'} textAlign={'left'} fontFamily={FONT} fontSize={58} fontWeight={900} fill={NAVY} />
        <Txt position={[-455, -132]} width={860} text={'一个机制图，讲清两条不同的抗病毒路径'} textAlign={'left'} fontFamily={FONT} fontSize={31} fontWeight={540} fill={MUTED} />
        <Rect position={[0, 125]} size={[1720, 480]} radius={30} fill={'rgba(255,255,255,0.94)'} stroke={'#d9e0e8'} lineWidth={2} shadowColor={'rgba(30,60,95,0.10)'} shadowBlur={22} />
        <Rect position={[-700, 125]} size={[265, 92]} radius={20} fill={ORANGE}>
          <Txt text={'早期阻断路径'} fontFamily={FONT} fontSize={34} fontWeight={900} fill={WHITE} />
        </Rect>
        <Circle ref={cell} position={[-50, 120]} size={390} fill={PINK} stroke={CORAL} lineWidth={7} scale={0.75} opacity={0}>
          <Txt text={'感染细胞'} fontFamily={FONT} fontSize={38} fontWeight={880} fill={NAVY} />
          {[
            [-95, -82], [0, -105], [102, -65], [-80, 100], [90, 88],
          ].map(([x, y], index) => (
            <Circle ref={virus[index]} key={`virus-${index}`} position={[x, y]} size={42} fill={CORAL} stroke={'#ca4c60'} lineWidth={4} scale={0.25} opacity={0} />
          ))}
        </Circle>
        <Rect ref={blockArrow} position={[-50, -85]} size={[72, 132]} radius={10} fill={ORANGE} opacity={0}>
          <Txt position={[-82, -78]} width={180} text={'阻断复制'} textAlign={'center'} fontFamily={FONT} fontSize={29} fontWeight={900} fill={ORANGE} />
        </Rect>
        <Line ref={releaseArrow} points={[[170, 122], [430, 122]]} stroke={'#aeb5bd'} lineWidth={20} endArrow opacity={0} />
        <Rect ref={traditional} position={[610, 122]} size={[330, 98]} radius={22} fill={'#8e949c'} opacity={0}>
          <Txt text={'传统释放阻断路径'} fontFamily={FONT} fontSize={31} fontWeight={850} fill={WHITE} />
        </Rect>
        <Txt position={[0, 345]} width={1500} text={'对比重点：阻断复制源头，而不是等病毒复制后再限制释放'} textAlign={'center'} fontFamily={FONT} fontSize={31} fontWeight={850} fill={NAVY} />
      </Rect>

      <Rect ref={page4} size={[1920, 1080]} opacity={0}>
        <Txt position={[-500, -190]} width={820} text={'治疗自己，保护身边人'} textAlign={'left'} fontFamily={FONT} fontSize={62} fontWeight={900} fill={NAVY} />
        <Txt position={[-500, -105]} width={820} text={'早期阻断流感传播，降低传染给家人的风险。'} textAlign={'left'} fontFamily={FONT} fontSize={34} fontWeight={540} fill={MUTED} />
        <Rect ref={familyCallout} position={[-560, 150]} size={[560, 190]} radius={28} fill={'#fff5e9'} stroke={'#f3bb70'} lineWidth={4} opacity={0} scale={0.82}>
          <Txt position={[-40, -40]} text={'本人尽早治疗'} fontFamily={FONT} fontSize={39} fontWeight={900} fill={ORANGE} />
          <Txt position={[5, 45]} text={'→ 传播链更早被截断'} fontFamily={FONT} fontSize={32} fontWeight={860} fill={NAVY} />
        </Rect>
        <Rect position={[510, 80]} size={[700, 650]} radius={36} fill={'rgba(255,255,255,0.86)'} shadowColor={'rgba(30,60,95,0.12)'} shadowBlur={28} />
        <Img ref={family} src={data.assets.family} position={[510, 80]} size={[650, 650]} opacity={0} scale={0.72} />
      </Rect>

      <Rect ref={subtitleBar} position={[0, 454]} size={[1680, 100]} radius={20} fill={'rgba(16,34,62,0.90)'} opacity={0}>
        <Txt ref={subtitle} width={1560} textAlign={'center'} fontFamily={FONT} fontSize={42} fontWeight={830} fill={WHITE} opacity={0} />
      </Rect>
      <Txt position={[-660, 510]} text={'金样复刻验证 · 包装与医学内容待业务审核'} fontFamily={FONT} fontSize={18} fontWeight={540} fill={'#8a95a3'} />
    </>,
  );

  function* visualTimeline() {
    yield* all(chrome().opacity(1, 0.36), chrome().position.y(0, 0.36, easeOutCubic));
    yield* setActiveNav(nav, 0);
    yield* all(page1().opacity(1, 0.32), page1().scale(1, 0.32, easeOutCubic));
    yield* all(pack1().opacity(1, 0.24), pack1().scale(1, 0.48, easeOutBack));
    yield* waitFor(2.65);

    yield* all(page1().opacity(0, 0.24), page1().position.x(-90, 0.24, easeInOutCubic));
    yield* setActiveNav(nav, 1);
    yield* page2().opacity(1, 0.28);
    yield* all(dose().opacity(1, 0.18), dose().scale(1, 0.38, easeOutBack));
    yield* all(routeArrow().opacity(1, 0.16), routeArrow().scale(1, 0.28, easeOutBack));
    yield* all(pack2().opacity(1, 0.18), pack2().scale(1, 0.34, easeOutBack));
    yield* all(oneDay().opacity(1, 0.14), oneDay().scale(1, 0.30, easeOutBack));
    yield* waitFor(4.55);

    yield* all(page2().opacity(0, 0.24), page2().position.x(-90, 0.24, easeInOutCubic));
    yield* page3().opacity(1, 0.26);
    yield* all(cell().opacity(1, 0.16), cell().scale(1, 0.32, easeOutBack));
    for (let index = 0; index < virus.length; index += 1) {
      yield* all(virus[index]().opacity(1, 0.08), virus[index]().scale(1, 0.16, easeOutBack));
    }
    yield* all(blockArrow().opacity(1, 0.16), blockArrow().position.y(-20, 0.30, easeOutBack));
    yield* waitFor(2.35);
    yield* all(releaseArrow().opacity(1, 0.22), traditional().opacity(1, 0.28));
    yield* all(
      ...virus.map((item, index) => item().scale(index % 2 === 0 ? 1.16 : 0.88, 0.55, easeInOutCubic)),
    );
    yield* all(...virus.map(item => item().scale(1, 0.55, easeInOutCubic)));
    yield* waitFor(4.45);

    yield* all(page3().opacity(0, 0.26), page3().position.x(-90, 0.26, easeInOutCubic));
    yield* setActiveNav(nav, 2);
    yield* page4().opacity(1, 0.28);
    yield* all(family().opacity(1, 0.22), family().scale(1, 0.46, easeOutBack));
    yield* all(familyCallout().opacity(1, 0.18), familyCallout().scale(1, 0.34, easeOutBack));
    yield* waitFor(5.70);
    yield* family().scale(1.025, 0.42, easeInOutCubic);
    yield* family().scale(1, 0.42, easeInOutCubic);
    yield* waitFor(0.38);
  }

  function* backgroundMotion() {
    yield* all(
      background().scale(1.045, DURATION, easeInOutCubic),
      background().position.x(-18, DURATION, easeInOutCubic),
    );
  }

  yield* all(visualTimeline(), runSubtitles(subtitle, subtitleBar), backgroundMotion());
});

export default makeProject({
  scenes: [scene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
    },
  },
});
