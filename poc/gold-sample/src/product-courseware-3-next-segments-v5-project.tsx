import {Audio, Circle, Img, Rect, Txt, makeScene2D} from '@revideo/2d';
import {Reference, all, createRef, easeInOutCubic, easeOutBack, easeOutCubic, makeProject, waitFor} from '@revideo/core';

type RectRef = Reference<Rect>;
const FONT = 'Gen Jyuu Gothic, Source Han Sans SC, sans-serif';
const DURATION = 40.12;
const NAVY = '#123A84';
const ORANGE = '#F28A00';
const ORANGE_DARK = '#D36D00';
const GRAY = '#C9C9C9';
const GRAY_DARK = '#969696';
const WHITE = '#FFFFFF';
const CREAM = '#FFF4E5';

function Brand() {
  return <Rect position={[822, -478]} size={[260, 105]}>
    <Txt text={'速'} position={[-70, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={NAVY} />
    <Txt text={'福'} position={[0, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={ORANGE} />
    <Txt text={'达'} position={[70, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={NAVY} />
    <Txt text={'（玛巴洛沙韦）'} position={[0, 35]} fontFamily={FONT} fontSize={20} fontWeight={900} fill={NAVY} />
  </Rect>;
}

function Ribbon({title}: {title: Reference<Txt>}) {
  return <Rect position={[0, -425]} size={[700, 110]}>
    <Rect position={[-315, 7]} size={[120, 82]} skew={[-15, 0]} fill={ORANGE_DARK} />
    <Rect position={[315, 7]} size={[120, 82]} skew={[-15, 0]} fill={ORANGE_DARK} />
    <Rect size={[606, 105]} radius={18} fill={ORANGE} stroke={ORANGE_DARK} lineWidth={4}>
      <Txt ref={title} text={'二、产品特点'} fontFamily={FONT} fontSize={57} fontWeight={900} fill={WHITE} />
    </Rect>
  </Rect>;
}

function NavItem({root, number, label, position, width, fontSize}: {root: RectRef; number: string; label: string; position: [number, number]; width: number; fontSize: number}) {
  return <Rect ref={root} position={position} size={[width, 82]} radius={40} fill={GRAY} stroke={'#BEBEBE'} lineWidth={2}>
    <Circle position={[-width / 2 + 43, 0]} size={66} fill={WHITE} stroke={'#BEBEBE'} lineWidth={3}>
      <Txt text={number} fontFamily={FONT} fontSize={39} fontWeight={900} fill={GRAY_DARK} />
    </Circle>
    <Txt position={[29, 0]} width={width - 88} text={label} textAlign={'center'} fontFamily={FONT} fontSize={fontSize} fontWeight={900} fill={WHITE} />
  </Rect>;
}

const scene = makeScene2D('product-courseware-3-next-segments-v5', function* (view) {
  const background = createRef<Img>();
  const chapterTitle = createRef<Txt>();
  const ribbonGroup = createRef<Rect>();
  const navGroup = createRef<Rect>();
  const nav = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const safety = createRef<Rect>();
  const safetyRing = createRef<Circle>();
  const safetyPack = createRef<Img>();
  const lowRate = createRef<Rect>();
  const shield = createRef<Rect>();
  const dosage = createRef<Rect>();
  const dosagePack = createRef<Img>();
  const tablets = createRef<Img>();
  const bottles = createRef<Img>();
  const tabletStage = createRef<Rect>();
  const bottleStage = createRef<Rect>();
  const brandScene = createRef<Rect>();
  const brandRows = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const audienceIntro = createRef<Rect>();
  const introChild = createRef<Img>();
  const ageBadge = createRef<Circle>();
  const audienceFinal = createRef<Rect>();
  const audienceCards = [createRef<Rect>(), createRef<Rect>(), createRef<Rect>()];
  const elder = createRef<Img>();
  const child = createRef<Img>();
  const chronic = createRef<Img>();
  const caption = createRef<Txt>();

  view.add(<>
    <Img ref={background} src={'/product-courseware-3-v5/white-silk-bg-v5.png'} size={[1920, 1080]} />
    <Audio src={'/product-courseware-3-v5/next-segments-audio-v5.wav'} play />
    <Rect ref={ribbonGroup}><Ribbon title={chapterTitle} /></Rect>
    <Brand />

    <Rect ref={navGroup} size={[1920, 1080]} opacity={0}>
      <NavItem root={nav[0]} number={'1'} label={'成人儿童安全性均良好'} position={[-600, -294]} width={510} fontSize={34} />
      <NavItem root={nav[1]} number={'2'} label={'片剂、干混悬剂双剂型选择'} position={[5, -294]} width={650} fontSize={32} />
      <NavItem root={nav[2]} number={'3'} label={'原研品牌'} position={[600, -294]} width={390} fontSize={36} />
    </Rect>

    <Rect ref={safety} size={[1920, 1080]} opacity={0}>
      <Circle ref={safetyRing} position={[0, 130]} size={[850, 610]} fill={'#FFFFFF00'} stroke={ORANGE} lineWidth={5} opacity={0} scale={0.72} />
      <Img ref={safetyPack} src={'/product-courseware-3-v5/package-cluster-alpha.png'} position={[0, 140]} size={[660, 372]} opacity={0} scale={0.72} />
      <Rect ref={lowRate} position={[-680, 130]} size={[315, 260]} opacity={0}>
        <Circle position={[0, -45]} size={140} fill={CREAM} stroke={ORANGE} lineWidth={5}>
          <Txt text={'儿童'} fontFamily={FONT} fontSize={38} fontWeight={900} fill={NAVY} />
        </Circle>
        <Txt text={'呕吐率低'} position={[0, 80]} width={310} fontFamily={FONT} fontSize={51} fontWeight={900} fill={NAVY} />
      </Rect>
      <Rect ref={shield} position={[690, 120]} size={[220, 240]} opacity={0}>
        <Rect size={[170, 190]} radius={32} stroke={ORANGE} lineWidth={9} fill={'#FFFFFF00'} rotation={45} />
        <Txt text={'✓'} fontFamily={FONT} fontSize={92} fontWeight={900} fill={ORANGE} />
      </Rect>
      <Txt text={'安全性良好'} position={[0, 425]} width={620} fontFamily={FONT} fontSize={50} fontWeight={900} fill={'#171717'} />
    </Rect>

    <Rect ref={dosage} size={[1920, 1080]} opacity={0}>
      <Rect ref={tabletStage} position={[-650, 140]} size={[500, 545]} radius={24} fill={'#FFFFFFE8'} stroke={NAVY} lineWidth={5} opacity={0}>
        <Img ref={tablets} src={'/product-courseware-3-v5/tablets-alpha.png'} position={[0, -35]} size={[420, 280]} opacity={0} scale={0.65} />
        <Txt text={'片剂无味，药小易吞'} position={[0, 210]} width={470} fontFamily={FONT} fontSize={38} fontWeight={900} fill={NAVY} />
      </Rect>
      <Circle position={[0, 130]} size={[700, 540]} fill={'#FFFFFF00'} stroke={ORANGE} lineWidth={5} />
      <Img ref={dosagePack} src={'/product-courseware-3-v5/package-cluster-alpha.png'} position={[0, 140]} size={[620, 350]} opacity={0} scale={0.70} />
      <Rect position={[-388, 145]} size={[95, 5]} fill={ORANGE} />
      <Rect position={[388, 145]} size={[95, 5]} fill={ORANGE} />
      <Rect ref={bottleStage} position={[650, 140]} size={[500, 545]} radius={24} fill={'#FFFFFFE8'} stroke={NAVY} lineWidth={5} opacity={0}>
        <Img ref={bottles} src={'/product-courseware-3-v5/suspension-bottles-alpha.png'} position={[0, -35]} size={[310, 410]} opacity={0} scale={0.65} />
        <Txt text={'草莓口味｜可按体重精准给药'} position={[0, 210]} width={470} fontFamily={FONT} fontSize={34} fontWeight={900} fill={NAVY} />
      </Rect>
    </Rect>

    <Rect ref={brandScene} size={[1920, 1080]} opacity={0}>
      <Rect ref={brandRows[0]} position={[0, -30]} size={[1450, 145]} radius={22} fill={CREAM} stroke={'#F4D7AC'} lineWidth={2} opacity={0}>
        <Txt text={'⚑'} position={[-620, 0]} fontFamily={FONT} fontSize={64} fontWeight={900} fill={ORANGE} />
        <Txt text={'来自第一代流感药奥司他韦厂家'} position={[-60, -25]} width={1040} textAlign={'left'} fontFamily={FONT} fontSize={43} fontWeight={900} fill={NAVY} />
        <Txt text={'全球制药企业罗氏'} position={[-60, 35]} width={1040} textAlign={'left'} fontFamily={FONT} fontSize={29} fontWeight={500} fill={GRAY_DARK} />
      </Rect>
      <Rect ref={brandRows[1]} position={[0, 150]} size={[1450, 145]} radius={22} fill={CREAM} stroke={'#F4D7AC'} lineWidth={2} opacity={0}>
        <Txt text={'70+'} position={[-610, 0]} fontFamily={FONT} fontSize={48} fontWeight={900} fill={ORANGE} />
        <Txt text={'70+ 国家和地区获批上市'} position={[-60, -25]} width={1040} textAlign={'left'} fontFamily={FONT} fontSize={43} fontWeight={900} fill={NAVY} />
        <Txt text={'覆盖全球多个市场'} position={[-60, 35]} width={1040} textAlign={'left'} fontFamily={FONT} fontSize={29} fontWeight={500} fill={GRAY_DARK} />
      </Rect>
      <Rect ref={brandRows[2]} position={[0, 330]} size={[1450, 145]} radius={22} fill={CREAM} stroke={'#F4D7AC'} lineWidth={2} opacity={0}>
        <Txt text={'✓'} position={[-620, 0]} fontFamily={FONT} fontSize={70} fontWeight={900} fill={ORANGE} />
        <Txt text={'中国卫健委与 WHO 一致推荐'} position={[-60, -25]} width={1040} textAlign={'left'} fontFamily={FONT} fontSize={43} fontWeight={900} fill={NAVY} />
        <Txt text={'14 项国内外权威指南纳入'} position={[-60, 35]} width={1040} textAlign={'left'} fontFamily={FONT} fontSize={29} fontWeight={500} fill={GRAY_DARK} />
      </Rect>
    </Rect>

    <Rect ref={audienceIntro} size={[1920, 1080]} opacity={0}>
      <Img ref={introChild} src={'/product-courseware-3-v5/child-alpha.png'} position={[-430, 150]} size={[360, 540]} opacity={0} />
      <Circle ref={ageBadge} position={[270, 120]} size={500} fill={ORANGE} stroke={ORANGE_DARK} lineWidth={4} opacity={0} scale={0.70}>
        <Txt text={'≥ 5岁'} position={[0, -85]} fontFamily={FONT} fontSize={104} fontWeight={900} fill={WHITE} />
        <Txt text={'既往健康或存在流感并发症高风险的\n单纯性甲型或乙型流感患者'} position={[0, 75]} width={425} textAlign={'center'} fontFamily={FONT} fontSize={37} fontWeight={900} lineHeight={52} fill={WHITE} />
      </Circle>
    </Rect>

    <Rect ref={audienceFinal} size={[1920, 1080]} opacity={0}>
      <Txt text={'5岁及以上的既往健康或存在流感并发症高风险的单纯性甲型或乙型流感患者'} position={[0, -245]} width={1660} textAlign={'center'} fontFamily={FONT} fontSize={40} fontWeight={900} fill={NAVY} />
      <Rect ref={audienceCards[0]} position={[-620, 145]} size={[510, 570]} radius={25} fill={'#FFFFFFE8'} stroke={'#E5E7EB'} lineWidth={2} opacity={0}>
        <Img ref={elder} src={'/product-courseware-3-v5/elder-alpha.png'} position={[0, -40]} size={[290, 435]} />
        <Txt text={'老年人（≥65岁）'} position={[0, 225]} width={460} fontFamily={FONT} fontSize={36} fontWeight={900} fill={NAVY} />
      </Rect>
      <Rect ref={audienceCards[1]} position={[0, 145]} size={[510, 570]} radius={25} fill={'#FFFFFFE8'} stroke={'#E5E7EB'} lineWidth={2} opacity={0}>
        <Img ref={child} src={'/product-courseware-3-v5/child-alpha.png'} position={[0, -40]} size={[300, 440]} />
        <Txt text={'学龄期儿童\n（5岁及以上）'} position={[0, 218]} width={460} fontFamily={FONT} fontSize={34} fontWeight={900} lineHeight={42} fill={NAVY} />
      </Rect>
      <Rect ref={audienceCards[2]} position={[620, 145]} size={[610, 570]} radius={25} fill={'#FFFFFFE8'} stroke={'#E5E7EB'} lineWidth={2} opacity={0}>
        <Img ref={chronic} src={'/product-courseware-3-v5/chronic-group-alpha.png'} position={[0, -35]} size={[520, 390]} />
        <Txt text={'自身有基础性疾病的慢病患者'} position={[0, 225]} width={570} fontFamily={FONT} fontSize={34} fontWeight={900} fill={NAVY} />
      </Rect>
    </Rect>

    <Txt ref={caption} position={[0, 487]} width={1650} textAlign={'center'} fontFamily={FONT} fontSize={46} fontWeight={500} fill={'#171717'} />
  </>);

  const activate = (index: number) => nav.forEach((item, itemIndex) => item().fill(itemIndex === index ? ORANGE : GRAY));

  function* pageStates() {
    chapterTitle().text('二、产品特点');
    yield* waitFor(1.50);
    navGroup().opacity(1); safety().opacity(1); activate(0);
    yield* waitFor(5.48);
    safety().opacity(0); dosage().opacity(1); activate(1);
    yield* waitFor(9.56);
    dosage().opacity(0); brandScene().opacity(1); activate(2);
    yield* waitFor(11.66);
    navGroup().opacity(0); brandScene().opacity(0); chapterTitle().text('三、适宜人群'); audienceIntro().opacity(1);
    yield* waitFor(6.70);
    audienceIntro().opacity(0); audienceFinal().opacity(1);
    yield* waitFor(5.22);
  }

  function* safetyMotion() {
    yield* waitFor(1.50);
    yield* all(safetyRing().opacity(1, 0.14), safetyRing().scale(1, 0.34, easeOutBack), safetyPack().opacity(1, 0.12), safetyPack().scale(1, 0.34, easeOutBack));
    yield* waitFor(1.95);
    yield* all(lowRate().opacity(1, 0.16), lowRate().position.x(-650, 0.30, easeOutCubic));
    yield* waitFor(0.55);
    yield* all(shield().opacity(1, 0.16), shield().scale(1.04, 0.24, easeOutBack));
    yield* waitFor(2.14);
  }

  function* dosageMotion() {
    yield* waitFor(6.98);
    yield* all(dosagePack().opacity(1, 0.14), dosagePack().scale(1, 0.34, easeOutBack));
    yield* waitFor(1.12);
    yield* tabletStage().opacity(1, 0.16);
    yield* all(tablets().opacity(1, 0.12), tablets().scale(1, 0.32, easeOutBack));
    yield* waitFor(2.90);
    yield* bottleStage().opacity(1, 0.16);
    yield* all(bottles().opacity(1, 0.12), bottles().scale(1, 0.32, easeOutBack));
    yield* waitFor(5.96);
  }

  function* brandMotion() {
    yield* waitFor(17.80);
    yield* all(brandRows[0]().opacity(1, 0.16), brandRows[0]().position.x(0, 0.34, easeOutCubic));
    yield* waitFor(3.90);
    yield* all(brandRows[1]().opacity(1, 0.16), brandRows[1]().scale(1.01, 0.30, easeOutBack));
    yield* waitFor(1.40);
    yield* all(brandRows[2]().opacity(1, 0.16), brandRows[2]().scale(1.01, 0.30, easeOutBack));
    yield* waitFor(4.16);
  }

  function* audienceMotion() {
    yield* waitFor(28.20);
    introChild().position.x(-560);
    yield* all(introChild().opacity(1, 0.16), introChild().position.x(-430, 0.42, easeOutCubic), ageBadge().opacity(1, 0.16), ageBadge().scale(1, 0.38, easeOutBack));
    yield* waitFor(6.28);
    yield* all(audienceCards[0]().opacity(1, 0.16), audienceCards[0]().position.y(145, 0.30, easeOutCubic));
    yield* waitFor(0.35);
    yield* all(audienceCards[1]().opacity(1, 0.16), audienceCards[1]().position.y(145, 0.30, easeOutCubic));
    yield* waitFor(0.35);
    yield* all(audienceCards[2]().opacity(1, 0.16), audienceCards[2]().position.y(145, 0.30, easeOutCubic));
    yield* waitFor(3.62);
  }

  function* captions() {
    caption().text('二、产品特点');
    yield* waitFor(1.50);
    caption().text('1：成人儿童安全性均良好');
    yield* waitFor(2.60);
    caption().text('儿童服用呕吐率低，安全性良好');
    yield* waitFor(2.88);
    caption().text('2：片剂、干混悬剂双剂型选择');
    yield* waitFor(3.36);
    caption().text('片剂无味，药小易吞');
    yield* waitFor(1.36);
    caption().text('干混悬剂草莓口味');
    yield* waitFor(2.18);
    caption().text('小体重孩子可按体重精准给药，喂药更轻松');
    yield* waitFor(2.66);
    caption().text('3：原研品牌');
    yield* waitFor(1.26);
    caption().text('来自第一代流感药奥司他韦厂家，全球制药企业罗氏');
    yield* waitFor(4.24);
    caption().text('70+ 国家和地区获批上市');
    yield* waitFor(1.70);
    caption().text('中国卫健委与 WHO 一致推荐，14项国内外权威指南纳入');
    yield* waitFor(4.46);
    caption().text('三、适宜人群');
    yield* waitFor(1.32);
    caption().text('5岁及以上的既往健康或存在流感并发症高风险的单纯性甲型或乙型流感患者');
    yield* waitFor(5.38);
    caption().text('特别是老年人、学龄期儿童及自身有基础性疾病的慢病患者');
    yield* waitFor(5.22);
  }

  function* bgMotion() {
    yield* all(background().scale(1.025, DURATION, easeInOutCubic), background().position.x(-10, DURATION, easeOutCubic));
  }

  yield* all(pageStates(), safetyMotion(), dosageMotion(), brandMotion(), audienceMotion(), captions(), bgMotion());
});

export default makeProject({scenes: [scene], settings: {shared: {size: {x: 1920, y: 1080}}}});
