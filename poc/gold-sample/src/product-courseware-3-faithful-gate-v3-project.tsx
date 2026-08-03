import {Audio, Circle, Img, Rect, Txt, makeScene2D} from '@revideo/2d';
import {Reference, all, createRef, easeInOutCubic, easeOutBack, easeOutCubic, makeProject, waitFor} from '@revideo/core';

type RectRef = Reference<Rect>;
const FONT = 'Gen Jyuu Gothic, Source Han Sans SC, sans-serif';
const DURATION = 27.44;
const NAVY = '#123A84';
const ORANGE = '#F28A00';
const ORANGE_DARK = '#D36D00';
const GRAY = '#C9C9C9';
const GRAY_DARK = '#969696';
const WHITE = '#FFFFFF';

function Brand() {
  return <Rect position={[822, -478]} size={[260, 105]}>
    <Txt text={'速'} position={[-70, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={NAVY} />
    <Txt text={'福'} position={[0, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={ORANGE} />
    <Txt text={'达'} position={[70, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={NAVY} />
    <Txt text={'（玛巴洛沙韦）'} position={[0, 35]} fontFamily={FONT} fontSize={20} fontWeight={900} fill={NAVY} />
  </Rect>;
}

function Ribbon() {
  return <Rect position={[0, -425]} size={[700, 110]}>
    <Rect position={[-315, 7]} size={[120, 82]} skew={[-15, 0]} fill={ORANGE_DARK} />
    <Rect position={[315, 7]} size={[120, 82]} skew={[-15, 0]} fill={ORANGE_DARK} />
    <Rect size={[606, 105]} radius={18} fill={ORANGE} stroke={ORANGE_DARK} lineWidth={4}>
      <Txt text={'一、三大核心功效'} fontFamily={FONT} fontSize={57} fontWeight={900} fill={WHITE} />
    </Rect>
  </Rect>;
}

function NavItem({root, number, label, position, width}: {root: RectRef; number: string; label: string; position: [number, number]; width: number}) {
  return <Rect ref={root} position={position} size={[width, 87]} radius={42} fill={GRAY} stroke={'#BEBEBE'} lineWidth={2}>
    <Circle position={[-width / 2 + 45, 0]} size={69} fill={WHITE} stroke={'#BEBEBE'} lineWidth={3}>
      <Txt text={number} fontFamily={FONT} fontSize={41} fontWeight={900} fill={GRAY_DARK} />
    </Circle>
    <Txt position={[31, 0]} width={width - 92} text={label} textAlign={'center'} fontFamily={FONT} fontSize={number === '3' ? 40 : 43} fontWeight={900} fill={WHITE} />
  </Rect>;
}

const scene = makeScene2D('product-courseware-3-faithful-gate-v3', function* (view) {
  const background = createRef<Img>();
  const navGroup = createRef<Rect>();
  const nav = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const r06 = createRef<Rect>();
  const packs = createRef<Img>();
  const aGroup = createRef<Rect>();
  const bGroup = createRef<Rect>();
  const capsule = createRef<Img>();
  const bubble = createRef<Rect>();
  const r07 = createRef<Rect>();
  const board = createRef<Rect>();
  const blocker = createRef<Img>();
  const cell = createRef<Img>();
  const grayPath = createRef<Img>();
  const r07LeftText = createRef<Txt>();
  const r07MidText = createRef<Txt>();
  const r07RightText = createRef<Txt>();
  const r08 = createRef<Rect>();
  const patient = createRef<Img>();
  const shield = createRef<Img>();
  const virusA = createRef<Img>();
  const virusB = createRef<Img>();
  const caption = createRef<Txt>();

  view.add(<>
    <Img ref={background} src={'/product-courseware-3-v3/white-silk-reference-faithful-bg-v3.png'} size={[1920, 1080]} />
    <Audio src={'/product-courseware-3-v3/reference-audio-14.83-42.27-v3.wav'} play />
    <Ribbon />
    <Brand />

    <Rect ref={navGroup} size={[1920, 1080]} opacity={0}>
      <NavItem root={nav[0]} number={'1'} label={'专治甲流乙流'} position={[-556.5, -294]} width={423} />
      <NavItem root={nav[1]} number={'2'} label={'全程1次，1天退热'} position={[-67.5, -294]} width={483} />
      <NavItem root={nav[2]} number={'3'} label={'治疗自己，保护身边人'} position={[493.5, -294]} width={567} />
    </Rect>

    <Rect ref={r06} size={[1920, 1080]} opacity={0}>
      <Img ref={packs} src={'/product-courseware-3-v3/r06-package-cluster-alpha.png'} position={[-67.5, 180]} size={[885, 498]} opacity={0} scale={0.68} />
      <Rect ref={aGroup} position={[-510, 48]} opacity={0} scale={0.35} rotation={-9}>
        <Img src={'/product-courseware-3-v3/r06-burst-navy-alpha.png'} size={[210, 156]} />
        <Txt text={'甲'} fontFamily={FONT} fontSize={55} fontWeight={900} fill={WHITE} />
      </Rect>
      <Rect ref={bGroup} position={[-71, -128]} opacity={0} scale={0.35} rotation={10}>
        <Img src={'/product-courseware-3-v3/r06-burst-orange-alpha.png'} size={[218, 165]} />
        <Txt text={'乙'} fontFamily={FONT} fontSize={56} fontWeight={900} fill={WHITE} />
      </Rect>
      <Img ref={capsule} src={'/product-courseware-3-v3/r06-capsule-icon-alpha.png'} position={[210, 173]} size={[150, 150]} opacity={0} scale={0.35} />
      <Rect ref={bubble} position={[760, 118]} size={[450, 450]} opacity={0} scale={0.43} rotation={13}>
        <Img src={'/product-courseware-3-v3/r06-speech-bubble-alpha.png'} size={[450, 450]} />
        <Txt text={'专治\n甲流乙流'} position={[4, -6]} width={330} height={228} textAlign={'center'} fontFamily={FONT} fontSize={63} fontWeight={900} lineHeight={78} fill={WHITE} />
      </Rect>
    </Rect>

    <Rect ref={r07} size={[1920, 1080]} opacity={0}>
      <Rect ref={board} position={[0, 120]} size={[1764, 615]} radius={30} fill={'#FFFFFF'} stroke={'#E8E8E8'} lineWidth={2} opacity={0} />
      <Txt ref={r07LeftText} text={'全程只需口服1次'} position={[-640, -145]} width={530} fontFamily={FONT} fontSize={46} fontWeight={900} fill={ORANGE} opacity={0} />
      <Txt ref={r07MidText} text={'早期阻断病毒复制\n遏制新病毒生成'} position={[0, -135]} width={520} textAlign={'center'} fontFamily={FONT} fontSize={40} fontWeight={900} fill={ORANGE} opacity={0} />
      <Txt ref={r07RightText} text={'传统药物：1天2次\n连续服用5天'} position={[640, -135]} width={500} textAlign={'center'} fontFamily={FONT} fontSize={38} fontWeight={900} fill={GRAY_DARK} opacity={0} />
      <Img ref={blocker} src={'/product-courseware-3-v3/r07-orange-blocker-alpha.png'} position={[-600, 150]} size={[645, 375]} opacity={0} scale={0.65} />
      <Img ref={cell} src={'/product-courseware-3-v3/r07-infected-cell-alpha.png'} position={[0, 160]} size={[533, 533]} opacity={0} scale={0.65} />
      <Img ref={grayPath} src={'/product-courseware-3-v3/r07-gray-path-alpha.png'} position={[600, 165]} size={[660, 353]} opacity={0} scale={0.65} />
      <Rect position={[-600, 330]} size={[345, 86]} radius={18} fill={ORANGE} stroke={ORANGE_DARK} lineWidth={2}>
        <Txt text={'玛巴洛沙韦'} fontFamily={FONT} fontSize={43} fontWeight={900} fill={WHITE} />
      </Rect>
      <Rect position={[600, 330]} size={[315, 86]} radius={18} fill={GRAY_DARK} stroke={'#777777'} lineWidth={2}>
        <Txt text={'奥司他韦'} fontFamily={FONT} fontSize={43} fontWeight={900} fill={WHITE} />
      </Rect>
    </Rect>

    <Rect ref={r08} size={[1920, 1080]} opacity={0}>
      <Img ref={patient} src={'/product-courseware-3-v3/r08-patient-alpha.png'} position={[-520, 120]} size={[458, 608]} opacity={0} />
      <Img ref={virusA} src={'/product-courseware-3-v3/r06-burst-navy-alpha.png'} position={[-120, 65]} size={[135, 105]} opacity={0} scale={0.4} />
      <Img ref={virusB} src={'/product-courseware-3-v3/r06-burst-orange-alpha.png'} position={[0, 180]} size={[110, 84]} opacity={0} scale={0.4} />
      <Img ref={shield} src={'/product-courseware-3-v3/r08-family-shield-alpha.png'} position={[500, 105]} size={[750, 630]} opacity={0} />
    </Rect>

    <Txt ref={caption} position={[0, 487]} width={1550} textAlign={'center'} fontFamily={FONT} fontSize={46} fontWeight={500} fill={'#171717'} opacity={1} />
  </>);

  const activate = (index: number) => nav.forEach((item, itemIndex) => item().fill(itemIndex === index ? ORANGE : GRAY));

  function* pages() {
    yield* waitFor(2.00);
    navGroup().opacity(1); r06().opacity(1); activate(0);
    yield* waitFor(2.07);
    r06().opacity(0); r07().opacity(1); activate(1);
    yield* waitFor(16.17);
    r07().opacity(0); r08().opacity(1); activate(2);
    yield* waitFor(7.20);
  }

  function* r06Motion() {
    yield* waitFor(2.00);
    yield* all(packs().opacity(1, 0.12), packs().scale(1, 0.30, easeOutBack), packs().position.y(81, 0.30, easeOutCubic));
    yield* all(aGroup().opacity(1, 0.08), aGroup().scale(1, 0.18, easeOutBack), aGroup().rotation(0, 0.18, easeOutCubic));
    yield* all(bGroup().opacity(1, 0.08), bGroup().scale(1, 0.18, easeOutBack), bGroup().rotation(0, 0.18, easeOutCubic));
    yield* all(capsule().opacity(1, 0.08), capsule().scale(1, 0.16, easeOutBack));
    yield* all(bubble().opacity(1, 0.08), bubble().position.x(465, 0.34, easeOutCubic), bubble().position.y(42, 0.34, easeOutCubic), bubble().scale(1, 0.34, easeOutBack), bubble().rotation(-4, 0.34, easeOutBack));
    yield* bubble().rotation(0, 0.12, easeOutCubic);
    yield* waitFor(24.02);
  }

  function* r07Motion() {
    yield* waitFor(4.07);
    yield* board().opacity(1, 0.16);
    yield* all(cell().opacity(1, 0.12), cell().scale(1, 0.34, easeOutBack), r07MidText().opacity(1, 0.18));
    yield* waitFor(1.25);
    yield* all(blocker().opacity(1, 0.14), blocker().scale(1, 0.34, easeOutBack), blocker().position.x(-600, 0.34, easeOutCubic), r07LeftText().opacity(1, 0.18));
    yield* waitFor(2.15);
    yield* cell().scale(1.035, 0.34, easeInOutCubic);
    yield* cell().scale(1, 0.34, easeInOutCubic);
    yield* waitFor(5.40);
    yield* all(grayPath().opacity(1, 0.14), grayPath().scale(1, 0.36, easeOutBack), r07RightText().opacity(1, 0.18));
    yield* waitFor(5.49);
  }

  function* r08Motion() {
    yield* waitFor(20.24);
    patient().position.x(-760); shield().position.x(780);
    yield* all(patient().opacity(1, 0.15), patient().position.x(-520, 0.42, easeOutCubic), shield().opacity(1, 0.15), shield().position.x(500, 0.46, easeOutCubic));
    yield* waitFor(0.35);
    yield* all(virusA().opacity(1, 0.10), virusA().scale(1, 0.20, easeOutBack));
    yield* waitFor(0.25);
    yield* all(virusB().opacity(1, 0.10), virusB().scale(1, 0.20, easeOutBack));
    yield* shield().scale(1.025, 0.45, easeInOutCubic);
    yield* shield().scale(1, 0.45, easeInOutCubic);
    yield* waitFor(4.84);
  }

  function* captions() {
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

  function* bgMotion() {
    yield* all(background().scale(1.025, DURATION, easeInOutCubic), background().position.x(-10, DURATION, easeOutCubic));
  }

  yield* all(pages(), r06Motion(), r07Motion(), r08Motion(), captions(), bgMotion());
});

export default makeProject({scenes: [scene], settings: {shared: {size: {x: 1920, y: 1080}}}});
