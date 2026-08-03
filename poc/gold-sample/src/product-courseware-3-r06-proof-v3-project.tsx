import {Audio, Circle, Img, Rect, Txt, makeScene2D} from '@revideo/2d';
import {all, createRef, easeOutBack, easeOutCubic, makeProject, waitFor} from '@revideo/core';

const FONT = 'Gen Jyuu Gothic, Source Han Sans SC, sans-serif';
const NAVY = '#123A84';
const ORANGE = '#F28A00';
const ORANGE_DARK = '#D36D00';
const GRAY = '#C9C9C9';
const GRAY_DARK = '#969696';
const WHITE = '#FFFFFF';

function Brand() {
  return (
    <Rect position={[822, -478]} size={[260, 105]}>
      <Txt text={'速'} position={[-70, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={NAVY} />
      <Txt text={'福'} position={[0, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={ORANGE} />
      <Txt text={'达'} position={[70, -15]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={NAVY} />
      <Txt text={'（玛巴洛沙韦）'} position={[0, 35]} fontFamily={FONT} fontSize={20} fontWeight={900} fill={NAVY} />
    </Rect>
  );
}

function Ribbon() {
  return (
    <Rect position={[0, -425]} size={[700, 110]}>
      <Rect position={[-315, 7]} size={[120, 82]} skew={[-15, 0]} fill={ORANGE_DARK} />
      <Rect position={[315, 7]} size={[120, 82]} skew={[-15, 0]} fill={ORANGE_DARK} />
      <Rect size={[606, 105]} radius={18} fill={ORANGE} stroke={ORANGE_DARK} lineWidth={4}>
        <Txt text={'一、三大核心功效'} fontFamily={FONT} fontSize={57} fontWeight={900} fill={WHITE} />
      </Rect>
    </Rect>
  );
}

function NavItem({number, label, position, width, active}: {number: string; label: string; position: [number, number]; width: number; active: boolean}) {
  return (
    <Rect position={position} size={[width, 87]} radius={42} fill={active ? ORANGE : GRAY} stroke={active ? ORANGE_DARK : '#BEBEBE'} lineWidth={2}>
      <Circle position={[-width / 2 + 45, 0]} size={69} fill={WHITE} stroke={active ? ORANGE_DARK : '#BEBEBE'} lineWidth={3}>
        <Txt text={number} fontFamily={FONT} fontSize={41} fontWeight={900} fill={active ? ORANGE : GRAY_DARK} />
      </Circle>
      <Txt position={[31, 0]} width={width - 92} text={label} textAlign={'center'} fontFamily={FONT} fontSize={number === '3' ? 40 : 43} fontWeight={900} fill={WHITE} />
    </Rect>
  );
}

const scene = makeScene2D('product-courseware-3-r06-proof-v3', function* (view) {
  const nav = createRef<Rect>();
  const packs = createRef<Img>();
  const aGroup = createRef<Rect>();
  const bGroup = createRef<Rect>();
  const capsule = createRef<Img>();
  const bubble = createRef<Rect>();
  const caption = createRef<Txt>();

  view.add(
    <>
      <Img src={'/product-courseware-3-v3/white-silk-reference-faithful-bg-v3.png'} size={[1920, 1080]} />
      <Audio src={'/product-courseware-3-v3/r06-reference-audio-v3.wav'} play />
      <Ribbon />
      <Brand />

      <Rect ref={nav} size={[1920, 1080]} opacity={0}>
        <NavItem number={'1'} label={'专治甲流乙流'} position={[-556.5, -294]} width={423} active />
        <NavItem number={'2'} label={'全程1次，1天退热'} position={[-67.5, -294]} width={483} active={false} />
        <NavItem number={'3'} label={'治疗自己，保护身边人'} position={[493.5, -294]} width={567} active={false} />
      </Rect>

      <Img
        ref={packs}
        src={'/product-courseware-3-v3/r06-package-cluster-alpha.png'}
        position={[-67.5, 180]}
        size={[885, 498]}
        opacity={0}
        scale={0.68}
      />

      <Rect ref={aGroup} position={[-510, 48]} opacity={0} scale={0.35} rotation={-9}>
        <Img src={'/product-courseware-3-v3/r06-burst-navy-alpha.png'} size={[210, 156]} />
        <Txt text={'甲'} fontFamily={FONT} fontSize={55} fontWeight={900} fill={WHITE} />
      </Rect>
      <Rect ref={bGroup} position={[-71, -128]} opacity={0} scale={0.35} rotation={10}>
        <Img src={'/product-courseware-3-v3/r06-burst-orange-alpha.png'} size={[218, 165]} />
        <Txt text={'乙'} fontFamily={FONT} fontSize={56} fontWeight={900} fill={WHITE} />
      </Rect>
      <Img
        ref={capsule}
        src={'/product-courseware-3-v3/r06-capsule-icon-alpha.png'}
        position={[210, 173]}
        size={[150, 150]}
        opacity={0}
        scale={0.35}
      />

      <Rect ref={bubble} position={[760, 118]} size={[450, 450]} opacity={0} scale={0.43} rotation={13}>
        <Img src={'/product-courseware-3-v3/r06-speech-bubble-alpha.png'} size={[450, 450]} />
        <Txt
          text={'专治\n甲流乙流'}
          position={[4, -6]}
          width={330}
          height={228}
          textAlign={'center'}
          fontFamily={FONT}
          fontSize={63}
          fontWeight={900}
          lineHeight={78}
          fill={WHITE}
        />
      </Rect>

      <Txt ref={caption} text={'1：专治甲流乙流'} position={[0, 473]} width={810} textAlign={'center'} fontFamily={FONT} fontSize={47} fontWeight={500} fill={'#171717'} opacity={0} />
    </>,
  );

  yield* nav().opacity(1, 0.12, easeOutCubic);
  yield* all(
    packs().opacity(1, 0.14),
    packs().scale(1, 0.34, easeOutBack),
    packs().position.y(83, 0.34, easeOutCubic),
  );
  yield* all(aGroup().opacity(1, 0.09), aGroup().scale(1, 0.22, easeOutBack), aGroup().rotation(0, 0.22, easeOutCubic));
  yield* waitFor(0.08);
  yield* all(bGroup().opacity(1, 0.09), bGroup().scale(1, 0.22, easeOutBack), bGroup().rotation(0, 0.22, easeOutCubic));
  yield* waitFor(0.07);
  yield* all(capsule().opacity(1, 0.08), capsule().scale(1, 0.19, easeOutBack));
  yield* waitFor(0.06);
  yield* all(
    bubble().opacity(1, 0.10),
    bubble().position.x(468, 0.42, easeOutCubic),
    bubble().position.y(42, 0.42, easeOutCubic),
    bubble().scale(1, 0.42, easeOutBack),
    bubble().rotation(-4, 0.42, easeOutBack),
    caption().opacity(1, 0.22),
  );
  yield* bubble().rotation(0, 0.16, easeOutCubic);
  yield* waitFor(0.94);
});

export default makeProject({
  scenes: [scene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
