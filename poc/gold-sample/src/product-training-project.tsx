import {Audio, Circle, Img, Rect, Txt, View2D, makeScene2D} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeOutBack,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../product-training-signoff.json';

type Cue = {
  start: number;
  end: number;
  text: string;
};

const DURATION = 30;
const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const COLORS = {
  bg: '#dff4f7',
  ink: '#173b4a',
  muted: '#5b7882',
  teal: '#138d96',
  tealSoft: '#d8f2f0',
  coral: '#e76155',
  coralSoft: '#ffe8e3',
  white: '#ffffff',
  line: 'rgba(23, 87, 99, 0.18)',
};

const cues = data.cues as Cue[];

function addBackground(view: View2D) {
  view.add(
    <>
      <Rect size={[1920, 1080]} fill={COLORS.bg} />
      <Circle
        position={[780, -390]}
        size={820}
        fill={'rgba(255,255,255,0.28)'}
      />
      <Circle
        position={[-840, 390]}
        size={610}
        stroke={'rgba(19,141,150,0.12)'}
        lineWidth={70}
      />
      <Rect
        position={[0, 488]}
        size={[1920, 104]}
        fill={'rgba(255,255,255,0.68)'}
        stroke={COLORS.line}
        lineWidth={1}
      />
    </>,
  );
}

function addChrome(view: View2D) {
  view.add(
    <>
      <Rect
        position={[-760, -470]}
        size={[330, 58]}
        radius={29}
        fill={COLORS.ink}
      >
        <Circle position={[-130, 0]} size={16} fill={COLORS.coral} />
        <Txt
          position={[12, 0]}
          width={250}
          text={data.brand.name}
          textAlign={'left'}
          fontFamily={FONT}
          fontSize={26}
          fontWeight={700}
          fill={COLORS.white}
        />
      </Rect>
      <Txt
        position={[725, -470]}
        width={390}
        text={`${data.brand.badge}  ·  30 SEC`}
        textAlign={'right'}
        fontFamily={FONT}
        fontSize={24}
        fontWeight={650}
        letterSpacing={2}
        fill={COLORS.muted}
      />
      <Txt
        position={[0, 492]}
        width={1660}
        text={data.disclaimer.text}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={22}
        fontWeight={500}
        fill={COLORS.muted}
      />
    </>,
  );
}

function addSubtitle(view: View2D) {
  const ref = createRef<Txt>();
  view.add(
    <>
      <Rect
        position={[0, 414]}
        size={[1540, 70]}
        radius={22}
        fill={'rgba(20,55,68,0.92)'}
        shadowColor={'rgba(17,54,66,0.2)'}
        shadowBlur={16}
      />
      <Txt
        ref={ref}
        position={[0, 414]}
        width={1440}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={38}
        fontWeight={650}
        fill={COLORS.white}
        opacity={0}
      />
    </>,
  );
  return ref;
}

function* runSubtitles(ref: Reference<Txt>) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      ref().opacity(0);
      yield* waitFor(cue.start - cursor);
    }
    ref().text(cue.text);
    yield* ref().opacity(1, 0.05);
    yield* waitFor(Math.max(0, cue.end - cue.start - 0.05));
    cursor = cue.end;
  }
  ref().opacity(0);
}

const scene = makeScene2D('product-training-signoff', function* (view) {
  addBackground(view);
  view.add(
    <Audio
      src={'/product-training-audio/product-training-signoff-30s.wav'}
      play
      volume={1}
    />,
  );

  const hero = createRef<Rect>();
  const heroCopy = createRef<Rect>();
  const product = createRef<Img>();
  const heroBadges = data.product.badges.map(() => createRef<Rect>());
  const efficacy = createRef<Rect>();
  const efficacyTitle = createRef<Rect>();
  const mechanismCards = data.efficacy.mechanism.map(() =>
    createRef<Rect>(),
  );
  const features = createRef<Rect>();
  const featureTitle = createRef<Rect>();
  const featureCards = data.features.map(() => createRef<Rect>());

  view.add(
    <>
      <Rect ref={hero} size={[1920, 1080]} opacity={1}>
        <Rect
          ref={heroCopy}
          position={[-455, -12]}
          size={[780, 610]}
          radius={38}
          fill={'rgba(255,255,255,0.78)'}
          stroke={COLORS.line}
          lineWidth={2}
          shadowColor={'rgba(26,85,96,0.12)'}
          shadowBlur={28}
        >
          <Rect
            position={[-270, -242]}
            size={[190, 48]}
            radius={24}
            fill={COLORS.coralSoft}
          >
            <Txt
              text={'商品英雄页'}
              fontFamily={FONT}
              fontSize={24}
              fontWeight={700}
              fill={COLORS.coral}
            />
          </Rect>
          <Txt
            position={[-8, -142]}
            width={650}
            text={data.product.displayName}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={84}
            fontWeight={800}
            fill={COLORS.ink}
          />
          <Txt
            position={[-8, -62]}
            width={650}
            text={`${data.product.genericName}  ·  ${data.product.specification}`}
            textAlign={'left'}
            fontFamily={FONT}
            fontSize={31}
            fontWeight={500}
            fill={COLORS.muted}
          />
          {data.product.badges.map((badge, index) => (
            <Rect
              ref={heroBadges[index]}
              position={[-132 + index * 190, 92]}
              size={[174, 106]}
              radius={20}
              fill={index === 1 ? COLORS.coralSoft : COLORS.tealSoft}
              stroke={
                index === 1
                  ? 'rgba(231,97,85,0.22)'
                  : 'rgba(19,141,150,0.22)'
              }
              lineWidth={2}
              scale={0.84}
              opacity={0}
            >
              <Txt
                width={140}
                text={badge}
                textWrap={true}
                textAlign={'center'}
                fontFamily={FONT}
                fontSize={25}
                fontWeight={650}
                lineHeight={35}
                fill={index === 1 ? COLORS.coral : COLORS.teal}
              />
            </Rect>
          ))}
        </Rect>
        <Rect
          position={[525, -5]}
          size={[760, 650]}
          radius={50}
          fill={'rgba(255,255,255,0.5)'}
          stroke={'rgba(255,255,255,0.9)'}
          lineWidth={2}
        >
          <Circle
            position={[0, 44]}
            size={540}
            fill={'rgba(231,97,85,0.08)'}
          />
          <Img
            ref={product}
            src={data.product.packshot}
            position={[0, 32]}
            size={[720, 406]}
            opacity={0}
            scale={0.88}
          />
          <Rect
            position={[0, 280]}
            size={[260, 48]}
            radius={24}
            fill={COLORS.ink}
          >
            <Txt
              text={'通用包装示意'}
              fontFamily={FONT}
              fontSize={24}
              fontWeight={700}
              fill={COLORS.white}
            />
          </Rect>
        </Rect>
      </Rect>

      <Rect ref={efficacy} size={[1920, 1080]} opacity={0}>
        <Rect
          ref={efficacyTitle}
          position={[0, -325]}
          size={[1150, 150]}
          opacity={0}
        >
          <Txt
            position={[0, -32]}
            text={data.efficacy.title}
            fontFamily={FONT}
            fontSize={38}
            fontWeight={650}
            fill={COLORS.teal}
          />
          <Txt
            position={[0, 40]}
            text={data.efficacy.headline}
            fontFamily={FONT}
            fontSize={72}
            fontWeight={800}
            fill={COLORS.ink}
          />
        </Rect>
        <Rect
          position={[0, 5]}
          size={[1580, 470]}
          radius={40}
          fill={'rgba(255,255,255,0.78)'}
          stroke={COLORS.line}
          lineWidth={2}
          shadowColor={'rgba(26,85,96,0.1)'}
          shadowBlur={24}
        >
          {data.efficacy.mechanism.map((item, index) => (
            <Rect
              ref={mechanismCards[index]}
              position={[-490 + index * 490, -10]}
              size={[390, 320]}
              radius={30}
              fill={index === 1 ? COLORS.coralSoft : COLORS.tealSoft}
              stroke={
                index === 1
                  ? 'rgba(231,97,85,0.24)'
                  : 'rgba(19,141,150,0.24)'
              }
              lineWidth={2}
              opacity={0}
              scale={0.84}
            >
              <Circle
                position={[0, -72]}
                size={116}
                fill={index === 1 ? COLORS.coral : COLORS.teal}
              >
                <Txt
                  text={index === 1 ? 'ATP' : `0${index + 1}`}
                  fontFamily={FONT}
                  fontSize={index === 1 ? 30 : 34}
                  fontWeight={800}
                  fill={COLORS.white}
                />
              </Circle>
              <Txt
                position={[0, 38]}
                text={item}
                fontFamily={FONT}
                fontSize={42}
                fontWeight={750}
                fill={COLORS.ink}
              />
              <Txt
                position={[0, 100]}
                width={310}
                text={
                  index === 0
                    ? '结构化输入'
                    : index === 1
                      ? '机制节点'
                      : '审核结论'
                }
                fontFamily={FONT}
                fontSize={25}
                fontWeight={500}
                fill={COLORS.muted}
              />
            </Rect>
          ))}
        </Rect>
        <Rect
          position={[0, 285]}
          size={[780, 54]}
          radius={27}
          fill={COLORS.ink}
        >
          <Txt
            text={data.efficacy.note}
            fontFamily={FONT}
            fontSize={24}
            fontWeight={600}
            fill={COLORS.white}
          />
        </Rect>
      </Rect>

      <Rect ref={features} size={[1920, 1080]} opacity={0}>
        <Rect
          ref={featureTitle}
          position={[0, -330]}
          size={[1200, 140]}
          opacity={0}
        >
          <Txt
            position={[0, -28]}
            text={'产品特点与证据'}
            fontFamily={FONT}
            fontSize={68}
            fontWeight={800}
            fill={COLORS.ink}
          />
          <Txt
            position={[0, 48]}
            text={'每张证据卡都保留来源、版本与审核状态'}
            fontFamily={FONT}
            fontSize={29}
            fontWeight={500}
            fill={COLORS.muted}
          />
        </Rect>
        {data.features.map((feature, index) => (
          <Rect
            ref={featureCards[index]}
            position={[-510 + index * 510, 30]}
            size={[450, 470]}
            radius={34}
            fill={'rgba(255,255,255,0.84)'}
            stroke={index === 1 ? COLORS.coral : COLORS.teal}
            lineWidth={3}
            shadowColor={'rgba(26,85,96,0.12)'}
            shadowBlur={26}
            opacity={0}
            scale={0.84}
          >
            <Rect
              position={[-142, -168]}
              size={[94, 54]}
              radius={27}
              fill={index === 1 ? COLORS.coral : COLORS.teal}
            >
              <Txt
                text={feature.number}
                fontFamily={FONT}
                fontSize={27}
                fontWeight={800}
                fill={COLORS.white}
              />
            </Rect>
            <Txt
              position={[0, -64]}
              text={feature.title}
              fontFamily={FONT}
              fontSize={46}
              fontWeight={780}
              fill={COLORS.ink}
            />
            <Txt
              position={[0, 28]}
              width={340}
              text={feature.description}
              textWrap={true}
              textAlign={'center'}
              fontFamily={FONT}
              fontSize={29}
              lineHeight={42}
              fontWeight={500}
              fill={COLORS.muted}
            />
            <Rect
              position={[0, 150]}
              size={[330, 68]}
              radius={18}
              fill={index === 1 ? COLORS.coralSoft : COLORS.tealSoft}
            >
              <Txt
                text={'来源  ·  版本  ·  已审核'}
                fontFamily={FONT}
                fontSize={23}
                fontWeight={650}
                fill={index === 1 ? COLORS.coral : COLORS.teal}
              />
            </Rect>
          </Rect>
        ))}
      </Rect>
    </>,
  );

  addChrome(view);
  const subtitle = addSubtitle(view);

  function* visualTimeline() {
    yield* all(
      heroCopy().position([-455, -12], 0.55, easeOutCubic),
      product().opacity(1, 0.4),
      product().scale(1, 0.55, easeOutBack),
    );
    for (const badge of heroBadges) {
      yield* all(
        badge().opacity(1, 0.16),
        badge().scale(1, 0.28, easeOutBack),
      );
    }
    yield* waitFor(7.71);
    yield* all(hero().opacity(0, 0.3), efficacy().opacity(1, 0.3));

    yield* efficacyTitle().opacity(1, 0.28);
    for (const card of mechanismCards) {
      yield* all(
        card().opacity(1, 0.16),
        card().scale(1, 0.28, easeOutBack),
      );
      yield* waitFor(0.08);
    }
    yield* waitFor(8.34);
    yield* all(efficacy().opacity(0, 0.3), features().opacity(1, 0.3));

    yield* featureTitle().opacity(1, 0.28);
    for (const card of featureCards) {
      yield* all(
        card().opacity(1, 0.18),
        card().scale(1, 0.3, easeOutBack),
      );
      yield* waitFor(0.1);
    }
    yield* waitFor(9.12);
  }

  yield* all(visualTimeline(), runSubtitles(subtitle));
});

export default makeProject({
  scenes: [scene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: COLORS.bg,
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
