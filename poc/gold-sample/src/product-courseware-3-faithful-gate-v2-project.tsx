import {Audio, Circle, Img, Rect, Txt, makeScene2D} from '@revideo/2d';
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

type RectRef = Reference<Rect>;

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const DURATION = 27.44;
const NAVY = '#142e76';
const ORANGE = '#ed8a00';
const ORANGE_DARK = '#c96e00';
const GRAY = '#c8c8c8';
const GRAY_DARK = '#8c8c8c';
const WHITE = '#ffffff';
const CORAL = '#e93e5e';
const PINK = '#fad6df';

function Virus({position, size = 56, fill = CORAL}: {position: [number, number]; size?: number; fill?: string}) {
  return (
    <Circle position={position} size={size} fill={fill}>
      {[0, 45, 90, 135].map(angle => (
        <Rect rotation={angle} size={[size * 1.33, 5]} radius={3} fill={fill} />
      ))}
      <Circle size={size * 0.34} fill={fill} />
    </Circle>
  );
}

function Brand() {
  return (
    <Rect position={[820, -482]} size={[260, 100]}>
      <Txt text={'速'} position={[-78, -10]} fontFamily={FONT} fontSize={55} fontWeight={900} fill={NAVY} />
      <Txt text={'福'} position={[0, -10]} fontFamily={FONT} fontSize={55} fontWeight={900} fill={ORANGE} />
      <Txt text={'达'} position={[78, -10]} fontFamily={FONT} fontSize={55} fontWeight={900} fill={NAVY} />
      <Txt text={'（玛巴洛沙韦）'} position={[0, 38]} fontFamily={FONT} fontSize={18} fontWeight={750} fill={NAVY} />
    </Rect>
  );
}

function Ribbon() {
  return (
    <Rect position={[0, -430]} size={[700, 112]}>
      <Rect position={[-330, 6]} size={[100, 78]} skew={[-15, 0]} fill={ORANGE_DARK} />
      <Rect position={[330, 6]} size={[100, 78]} skew={[-15, 0]} fill={ORANGE_DARK} />
      <Rect size={[620, 108]} radius={18} fill={ORANGE} stroke={ORANGE_DARK} lineWidth={5}>
        <Txt text={'一、三大核心功效'} fontFamily={FONT} fontSize={52} fontWeight={900} fill={WHITE} />
      </Rect>
    </Rect>
  );
}

function NavItem({root, number, label, position, width}: {root: RectRef; number: string; label: string; position: [number, number]; width: number}) {
  return (
    <Rect ref={root} position={position} size={[width, 90]} radius={42} fill={GRAY}>
      <Circle position={[-width / 2 + 46, 0]} size={72} fill={WHITE} stroke={'#b6b6b6'} lineWidth={3}>
        <Txt text={number} fontFamily={FONT} fontSize={37} fontWeight={900} fill={GRAY_DARK} />
      </Circle>
      <Txt position={[32, 0]} width={width - 105} text={label} textAlign={'center'} fontFamily={FONT} fontSize={37} fontWeight={900} fill={WHITE} />
    </Rect>
  );
}

const scene = makeScene2D('product-courseware-3-faithful-gate-v2', function* (view) {
  const background = createRef<Img>();
  const navGroup = createRef<Rect>();
  const nav = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const benefit1 = createRef<Rect>();
  const mechanism = createRef<Rect>();
  const family = createRef<Rect>();
  const packages = createRef<Rect>();
  const aMark = createRef<Rect>();
  const bMark = createRef<Rect>();
  const benefitBubble = createRef<Circle>();
  const cell = createRef<Circle>();
  const viruses = [0, 1, 2, 3, 4].map(() => createRef<Circle>());
  const oral = createRef<Rect>();
  const drug1 = createRef<Rect>();
  const orangeArrow = createRef<Rect>();
  const grayPath = createRef<Rect>();
  const drug2 = createRef<Rect>();
  const familyImg = createRef<Img>();
  const caption = createRef<Txt>();

  view.add(
    <>
      <Img ref={background} src={'/product-courseware-3-v2/white-silk-medical-bg-v2.png'} size={[1920, 1080]} scale={1.01} />
      <Audio src={'/product-courseware-3-v2/reference-audio-14.83-42.27-v2.wav'} play />
      <Ribbon />
      <Brand />

      <Rect ref={navGroup} size={[1920, 1080]} opacity={0}>
        <NavItem root={nav[0]} number={'1'} label={'专治甲流乙流'} position={[-544, -255]} width={423} />
        <NavItem root={nav[1]} number={'2'} label={'全程1次，1天退热'} position={[-100, -255]} width={483} />
        <NavItem root={nav[2]} number={'3'} label={'治疗自己，保护身边人'} position={[496, -255]} width={567} />
      </Rect>

      <Rect ref={benefit1} size={[1920, 1080]} opacity={0}>
        <Rect ref={packages} position={[30, 110]} size={[700, 430]} scale={0.72} opacity={0}>
          <Rect position={[-130, -45]} size={[500, 120]} fill={WHITE} stroke={'#d6d6d6'} lineWidth={2}>
            <Rect position={[0, 32]} size={[460, 18]} fill={ORANGE} />
            <Txt text={'产品包装占位'} fontFamily={FONT} fontSize={21} fill={'#777777'} />
          </Rect>
          <Rect position={[-105, 72]} size={[470, 126]} fill={WHITE} stroke={'#d6d6d6'} lineWidth={2}>
            <Rect position={[0, 35]} size={[430, 18]} fill={ORANGE} />
            <Txt text={'产品包装占位'} fontFamily={FONT} fontSize={21} fill={'#777777'} />
          </Rect>
          <Rect position={[310, 0]} size={[165, 315]} fill={WHITE} stroke={'#d6d6d6'} lineWidth={2}>
            <Rect position={[-68, 0]} size={[14, 275]} fill={'#e4d313'} />
            <Txt text={'包装\n占位'} fontFamily={FONT} fontSize={19} fill={'#777777'} />
          </Rect>
        </Rect>
        <Rect ref={aMark} position={[-650, 85]} opacity={0} scale={0.4}>
          <Virus position={[0, 0]} size={92} fill={NAVY} />
          <Txt text={'甲'} fontFamily={FONT} fontSize={42} fontWeight={900} fill={WHITE} />
        </Rect>
        <Rect ref={bMark} position={[-160, -60]} opacity={0} scale={0.4}>
          <Virus position={[0, 0]} size={96} fill={ORANGE} />
          <Txt text={'乙'} fontFamily={FONT} fontSize={42} fontWeight={900} fill={WHITE} />
        </Rect>
        <Circle ref={benefitBubble} position={[600, 45]} size={315} fill={'#f3b451'} opacity={0} scale={0.5}>
          <Txt text={'专治\n甲流乙流'} textAlign={'center'} fontFamily={FONT} fontSize={52} fontWeight={900} fill={WHITE} />
        </Circle>
      </Rect>

      <Rect ref={mechanism} size={[1920, 1080]} opacity={0}>
        <Rect position={[0, 115]} size={[1704, 582]} radius={34} fill={WHITE} stroke={'#eeeeee'} lineWidth={2} />
        <Rect ref={oral} position={[-650, -10]} opacity={0}>
          <Txt text={'① 口服1次'} fontFamily={FONT} fontSize={40} fontWeight={900} fill={ORANGE} />
        </Rect>
        <Rect ref={drug1} position={[-610, 150]} size={[380, 118]} radius={22} fill={ORANGE} stroke={ORANGE_DARK} lineWidth={2} opacity={0} scale={0.75}>
          <Txt text={'玛巴洛沙韦'} fontFamily={FONT} fontSize={47} fontWeight={900} fill={WHITE} />
        </Rect>
        <Txt position={[-615, 300]} text={'-24h  1天快速退热'} fontFamily={FONT} fontSize={32} fontWeight={900} fill={ORANGE} />
        <Circle ref={cell} position={[0, 130]} size={[450, 375]} fill={PINK} stroke={'#c63a57'} lineWidth={7} opacity={0} scale={0.7}>
          {[
            [-135, -40], [-15, -110], [105, -60], [-35, 100], [105, 105],
          ].map(([x, y], index) => (
            <Circle ref={viruses[index]} position={[x, y]} size={66} opacity={0} scale={0.25}>
              <Virus position={[0, 0]} size={66} />
            </Circle>
          ))}
        </Circle>
        <Rect ref={orangeArrow} position={[-55, -95]} opacity={0}>
          <Txt position={[-130, -18]} width={260} text={'早期阻断病毒复制，\n遏制新病毒生成'} textAlign={'center'} fontFamily={FONT} fontSize={28} fontWeight={900} fill={ORANGE} />
          <Rect position={[0, 75]} size={[60, 170]} fill={ORANGE} />
          <Txt position={[0, 165]} text={'↓'} fontFamily={FONT} fontSize={90} fontWeight={900} fill={ORANGE} />
          <Txt position={[0, 238]} text={'×'} fontFamily={FONT} fontSize={62} fontWeight={900} fill={ORANGE} />
        </Rect>
        <Rect ref={grayPath} position={[520, 135]} opacity={0}>
          <Txt position={[-135, -175]} text={'↓'} fontFamily={FONT} fontSize={120} fontWeight={900} fill={GRAY_DARK} />
          <Txt position={[-135, -55]} text={'×  →'} fontFamily={FONT} fontSize={70} fontWeight={900} fill={GRAY_DARK} />
          <Virus position={[60, -20]} size={75} fill={'#f6dde2'} />
          <Virus position={[120, 80]} size={75} fill={'#f6dde2'} />
        </Rect>
        <Rect ref={drug2} position={[675, 150]} size={[310, 118]} radius={22} fill={GRAY_DARK} opacity={0} scale={0.75}>
          <Txt text={'奥司他韦'} fontFamily={FONT} fontSize={47} fontWeight={900} fill={WHITE} />
        </Rect>
        <Txt position={[680, 300]} text={'2次/天 × 5天'} fontFamily={FONT} fontSize={31} fontWeight={900} fill={GRAY_DARK} />
      </Rect>

      <Rect ref={family} size={[1920, 1080]} opacity={0}>
        <Img ref={familyImg} src={'/product-courseware-3-v2/family-shield-flat-v2.png'} position={[0, 95]} size={[1185, 665]} opacity={0} scale={0.82} />
      </Rect>

      <Txt ref={caption} position={[0, 487]} width={1550} textAlign={'center'} fontFamily={FONT} fontSize={43} fontWeight={500} fill={'#171717'} opacity={0} />
    </>,
  );

  function activate(index: number) {
    nav.forEach((item, itemIndex) => item().fill(itemIndex === index ? ORANGE : GRAY));
  }

  function* pageTimeline() {
    yield* waitFor(2.00);
    navGroup().opacity(1);
    benefit1().opacity(1);
    activate(0);
    yield* waitFor(2.07);
    benefit1().opacity(0);
    mechanism().opacity(1);
    activate(1);
    yield* waitFor(16.17);
    mechanism().opacity(0);
    family().opacity(1);
    activate(2);
    yield* waitFor(7.20);
  }

  function* benefitMotion() {
    yield* waitFor(2.00);
    yield* all(
      packages().opacity(1, 0.16), packages().scale(1, 0.30, easeOutBack),
      aMark().opacity(1, 0.12), aMark().scale(1, 0.24, easeOutBack),
      bMark().opacity(1, 0.12), bMark().scale(1, 0.24, easeOutBack),
      benefitBubble().opacity(1, 0.12), benefitBubble().scale(1, 0.24, easeOutBack),
    );
    yield* waitFor(25.14);
  }

  function* mechanismMotion() {
    yield* waitFor(4.07);
    yield* all(cell().opacity(1, 0.16), cell().scale(1, 0.30, easeOutBack));
    yield* waitFor(1.20);
    yield* all(oral().opacity(1, 0.12), drug1().opacity(1, 0.12), drug1().scale(1, 0.25, easeOutBack));
    yield* waitFor(1.70);
    yield* all(...viruses.flatMap(item => [item().opacity(1, 0.08), item().scale(1, 0.18, easeOutBack)]));
    yield* waitFor(1.30);
    yield* orangeArrow().opacity(1, 0.18);
    yield* waitFor(4.80);
    yield* all(
      grayPath().opacity(1, 0.18),
      drug2().opacity(1, 0.18), drug2().scale(1, 0.30, easeOutBack),
    );
    yield* waitFor(13.16);
  }

  function* familyMotion() {
    yield* waitFor(20.24);
    yield* all(familyImg().opacity(1, 0.16), familyImg().scale(1, 0.36, easeOutBack));
    yield* waitFor(2.74);
    yield* familyImg().scale(1.025, 0.50, easeInOutCubic);
    yield* familyImg().scale(1, 0.50, easeInOutCubic);
    yield* waitFor(3.10);
  }

  function* captions() {
    caption().opacity(1);
    caption().text('一、三大核心功效');
    yield* waitFor(2.00);
    caption().text('1：专治甲流乙流');
    yield* waitFor(2.07);
    caption().text('2：全程1次');
    yield* waitFor(1.53);
    caption().text('全程只需口服1次');
    yield* waitFor(1.90);
    caption().text('且早期阻断病毒复制');
    yield* waitFor(2.50);
    caption().text('遏制新病毒生成，一天快速退热');
    yield* waitFor(2.80);
    caption().text('传统药物奥司他韦不阻止病毒复制');
    yield* waitFor(2.80);
    caption().text('而是阻止已复制的病毒释放，减少体内扩散');
    yield* waitFor(2.60);
    caption().text('且需1天2次，连续吃5天');
    yield* waitFor(2.04);
    caption().text('3：治疗自己，保护身边人');
    yield* waitFor(2.36);
    caption().text('仅需患者本人服用，即可早期阻断流感传播');
    yield* waitFor(2.80);
    caption().text('大大降低传染给家人的风险');
    yield* waitFor(2.04);
  }

  function* backgroundMotion() {
    yield* all(
      background().scale(1.035, DURATION, easeInOutCubic),
      background().position.x(-12, DURATION, easeOutCubic),
    );
  }

  yield* all(pageTimeline(), benefitMotion(), mechanismMotion(), familyMotion(), captions(), backgroundMotion());
});

export default makeProject({
  scenes: [scene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
