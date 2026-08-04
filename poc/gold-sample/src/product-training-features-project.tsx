import {
  Audio,
  Circle,
  Img,
  Rect,
  Txt,
  makeScene2D,
} from '@revideo/2d';
import {
  Reference,
  all,
  createRef,
  easeInCubic,
  easeOutBack,
  easeOutCubic,
  makeProject,
  waitFor,
} from '@revideo/core';

import data from '../product-training-features.json';
import {productName, screenOf} from './product-training-content';

const PRODUCT = productName(data as any);
const SCREEN = screenOf(data as any);
/** Content-driven: only cycle titles that business provided. */
const FEATURE_SECTIONS: string[] =
  SCREEN.feature_sections && SCREEN.feature_sections.length > 0
    ? SCREEN.feature_sections
    : [
        '1、原研工艺，锁住活性',
        '2、海外原料，提升品质',
        '3、医疗背书',
      ];
const FEATURE_COUNT = FEATURE_SECTIONS.length;
import {
  DashenlinBrandMark,
  DashenlinInternalNotice,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';

type Cue = {start: number; end: number; text: string};

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const cues = data.cues as Cue[];

function DocumentCard() {
  return (
    <Rect
      size={[390, 430]}
      radius={12}
      fill={'#ffffff'}
      stroke={'#d2d8dc'}
      lineWidth={3}
      shadowColor={'rgba(35,75,92,0.2)'}
      shadowBlur={15}
    >
      <Txt position={[0, -162]} text={'原研工艺文件'} fontFamily={FONT} fontSize={31} fontWeight={800} fill={'#222f3a'} />
      <Txt position={[0, -122]} text={'INTERNAL RECREATION'} fontFamily={FONT} fontSize={13} fontWeight={700} fill={'#7b8991'} />
      {[0, 1, 2, 3, 4, 5, 6].map(index => (
        <Rect
          position={[-38 + (index % 2) * 24, -68 + index * 40]}
          size={[260 - (index % 3) * 38, 7]}
          radius={4}
          fill={index === 2 ? '#de6a58' : '#aeb9be'}
        />
      ))}
      <Circle position={[122, 150]} size={72} stroke={'#d15b4f'} lineWidth={5}>
        <Txt text={'研'} fontFamily={FONT} fontSize={31} fontWeight={800} fill={'#d15b4f'} />
      </Circle>
      <Txt position={[0, 190]} text={'资料结构重制示意'} fontFamily={FONT} fontSize={19} fontWeight={650} fill={'#76878f'} />
    </Rect>
  );
}

function LockArtwork() {
  return (
    <Rect size={[390, 430]} radius={16} fill={'#d8edf4'} shadowColor={'rgba(35,75,92,0.2)'} shadowBlur={15}>
      <Circle position={[0, -68]} size={205} stroke={'#293b4c'} lineWidth={38} />
      <Rect position={[0, 70]} size={[230, 230]} radius={35} fill={'#1788c5'} stroke={'#293b4c'} lineWidth={12}>
        <Circle position={[0, -28]} size={50} fill={'#f8ce52'} />
        <Rect position={[0, 48]} size={[28, 110]} radius={14} fill={'#f8ce52'} />
      </Rect>
      <Rect size={[325, 350]} stroke={'rgba(219,66,66,0.5)'} lineWidth={8} radius={28} />
    </Rect>
  );
}

function CapsuleArtwork() {
  return (
    <Rect size={[390, 430]} radius={16} fill={'#e9f5fa'} shadowColor={'rgba(35,75,92,0.2)'} shadowBlur={15}>
      {[0, 1, 2, 3].map(index => (
        <Rect
          position={[0, -125 + index * 80]}
          size={[180, 82]}
          radius={41}
          fill={index % 2 === 0 ? '#7bc7ee' : '#d4eef8'}
          stroke={'#4797ca'}
          lineWidth={5}
        >
          <Rect position={[-44, 0]} size={[6, 58]} fill={'rgba(255,255,255,0.72)'} radius={3} />
          <Circle position={[25, -10]} size={18} fill={'#f8a33a'} />
          <Circle position={[50, 12]} size={13} fill={'#f3ca4d'} />
        </Rect>
      ))}
      {[0, 1, 2, 3, 4].map(index => (
        <Circle position={[108 + index * 16, -35 + index * 32]} size={12} fill={'#f19535'} />
      ))}
    </Rect>
  );
}

function RawMaterialPanel() {
  return (
    <Rect size={[1220, 390]} radius={34} fill={'#ffffff'} stroke={'#2f9ecb'} lineWidth={4} shadowColor={'rgba(28,85,112,0.24)'} shadowBlur={20}>
      <Rect position={[-390, 0]} size={[440, 390]} radius={[34, 0, 0, 34]} fill={'#138bc7'}>
        <Txt position={[0, -85]} text={'纯度高 · 更安全'} fontFamily={FONT} fontSize={51} fontWeight={850} fill={'#ffffff'} />
        <Txt position={[0, 5]} width={340} text={'甄选海外原料\n纯度高 · 杂质少'} textAlign={'center'} fontFamily={FONT} fontSize={31} lineHeight={48} fontWeight={650} fill={'#dff5ff'} />
        <Circle position={[86, 94]} size={34} fill={'#d6f6ff'} />
        <Circle position={[120, 65]} size={15} fill={'#8be0ef'} />
      </Rect>
      <Rect position={[220, 0]} size={[730, 330]} fill={'#f7fbfc'} stroke={'#c3d4da'} lineWidth={2}>
        {[0, 1, 2, 3, 4].map(index => (
          <Rect position={[0, -132 + index * 66]} size={[700, 2]} fill={'#aebcc2'} />
        ))}
        {[-250, -80, 100, 280].map(x => (
          <Rect position={[x, 0]} size={[2, 320]} fill={'#aebcc2'} />
        ))}
        <Txt position={[-165, -98]} text={'原料'} fontFamily={FONT} fontSize={24} fontWeight={800} fill={'#344955'} />
        <Txt position={[190, -98]} text={'纯度    杂质    稳定性'} fontFamily={FONT} fontSize={24} fontWeight={800} fill={'#344955'} />
        {['重制样本 A', '重制样本 B', '重制样本 C'].map((text, index) => (
          <Txt position={[-165, -32 + index * 66]} text={text} fontFamily={FONT} fontSize={21} fill={'#536c78'} />
        ))}
        <Txt position={[190, -32]} text={'高       少       稳定'} fontFamily={FONT} fontSize={21} fontWeight={750} fill={'#dc554d'} />
        <Txt position={[190, 34]} text={'—        —        —'} fontFamily={FONT} fontSize={21} fill={'#647984'} />
        <Txt position={[190, 100]} text={'—        —        —'} fontFamily={FONT} fontSize={21} fill={'#647984'} />
      </Rect>
    </Rect>
  );
}

function MedicalPanel() {
  return (
    <Rect size={[1500, 500]} fill={'rgba(255,255,255,0.05)'}>
      <Img src={data.assets.product} position={[-535, 30]} size={[520, 300]} />
      <Rect position={[20, 0]} size={[520, 430]} fill={'#ffffff'} stroke={'#d3dadd'} lineWidth={3}>
        <Txt position={[0, -165]} text={'辅酶 Q10 内部资料示意'} fontFamily={FONT} fontSize={30} fontWeight={800} fill={'#273b47'} />
        {[0, 1, 2, 3, 4, 5, 6].map(index => (
          <Rect position={[0, -110 + index * 44]} size={[420 - (index % 3) * 55, 7]} radius={4} fill={index === 3 ? '#d65f52' : '#aeb9be'} />
        ))}
      </Rect>
      <Rect position={[530, 0]} size={[430, 430]} fill={'#ffffff'} stroke={'#d3dadd'} lineWidth={3}>
        <Txt position={[0, -165]} text={'临床资料重制页'} fontFamily={FONT} fontSize={29} fontWeight={800} fill={'#273b47'} />
        {[0, 1, 2, 3, 4, 5, 6].map(index => (
          <Rect position={[0, -110 + index * 44]} size={[330 - (index % 2) * 70, 7]} radius={4} fill={index === 2 ? '#d65f52' : '#aeb9be'} />
        ))}
      </Rect>
    </Rect>
  );
}

function Magnifier() {
  return (
    <Rect size={[480, 540]} rotation={-42}>
      <Circle position={[0, -90]} size={310} fill={'rgba(255,255,255,0.15)'} stroke={'#252d32'} lineWidth={32} shadowColor={'rgba(0,0,0,0.28)'} shadowBlur={18}>
        <Circle size={265} stroke={'rgba(255,255,255,0.75)'} lineWidth={12} />
        <Txt text={'内部资料'} fontFamily={FONT} fontSize={47} fontWeight={900} fill={'#201f20'} stroke={'#ffffff'} lineWidth={2} />
      </Circle>
      <Rect position={[0, 160]} size={[72, 270]} radius={34} fill={'#252d32'} stroke={'#686f74'} lineWidth={8} />
    </Rect>
  );
}

function* runSubtitles(ref: Reference<Txt>) {
  let cursor = 0;
  for (const cue of cues) {
    if (cue.start > cursor) {
      ref().opacity(0);
      yield* waitFor(cue.start - cursor);
    }
    ref().text(cue.text);
    yield* ref().opacity(1, 0.035);
    yield* waitFor(Math.max(0, cue.end - cue.start - 0.035));
    ref().opacity(0);
    cursor = cue.end;
  }
}

export const productTrainingFeaturesScene = makeScene2D('product-training-features', function* (view) {
  const mainTitle = createRef<Txt>();
  const sectionTitle = createRef<Txt>();
  const doc = createRef<Rect>();
  const lock = createRef<Rect>();
  const capsule = createRef<Rect>();
  const rawPanel = createRef<Rect>();
  const medicalPanel = createRef<Rect>();
  const magnifier = createRef<Rect>();
  const subtitle = createRef<Txt>();

  view.add(
    <>
      <Rect size={[1920, 1080]} fill={'#83cfea'} />
      <Rect position={[0, 475]} size={[1920, 130]} fill={'rgba(53,176,220,0.28)'} />
      <Audio src={data.audio.file} play />
      <DashenlinBrandMark />
      <Txt key={'editable:q10:features:title'} ref={mainTitle} position={[0, -445]} text={'产品特点'} fontFamily={FONT} fontSize={88} fontWeight={900} fill={'#ffffff'} stroke={'#273441'} lineWidth={6} />
      <Txt key={'editable:q10:features:section'} ref={sectionTitle} position={[0, -325]} text={FEATURE_SECTIONS[0]} fontFamily={FONT} fontSize={54} fontWeight={900} fill={'#c95c49'} stroke={'#ffffff'} lineWidth={4} />
      <Rect key={'editable:q10:features:doc'} ref={doc} position={[-500, 90]} opacity={0} scale={0.08}><DocumentCard /></Rect>
      <Rect key={'editable:q10:features:lock'} ref={lock} position={[0, 90]} opacity={0} scale={0.08}><LockArtwork /></Rect>
      <Rect key={'editable:q10:features:capsule'} ref={capsule} position={[500, 90]} opacity={0} scale={0.08}><CapsuleArtwork /></Rect>
      <Rect key={'editable:q10:features:raw'} ref={rawPanel} position={[0, 90]} opacity={0} scale={0.08}><RawMaterialPanel /></Rect>
      <Rect key={'editable:q10:features:medical'} ref={medicalPanel} position={[0, 90]} opacity={0} scale={0.08}><MedicalPanel /></Rect>
      <Rect ref={magnifier} position={[-570, 80]} opacity={0} scale={0.2}><Magnifier /></Rect>
      <Txt
        key={'editable:q10:features:subtitle'}
        ref={subtitle}
        position={[-40, 455]}
        width={1640}
        textAlign={'center'}
        fontFamily={FONT}
        fontSize={58}
        fontWeight={900}
        fill={'#ffe733'}
        stroke={'rgba(24,36,55,0.98)'}
        lineWidth={3.5}
        shadowColor={'rgba(0,0,0,0.28)'}
        shadowBlur={4}
        opacity={0}
      />
      <DashenlinInternalNotice />
    </>,
  );

  function* pop(ref: Reference<Rect>) {
    yield* all(ref().opacity(1, 0.1), ref().scale(1, 0.38, easeOutBack));
  }

  function* visualTimeline() {
    yield* waitFor(0.72);
    yield* pop(doc);
    yield* waitFor(2.92);
    yield* pop(lock);
    yield* waitFor(2.42);
    yield* pop(capsule);
    yield* waitFor(2.00);

    yield* all(
      doc().opacity(0, 0.16),
      lock().opacity(0, 0.16),
      capsule().opacity(0, 0.16),
    );
    if (FEATURE_COUNT > 1) {
      sectionTitle().text(FEATURE_SECTIONS[1]);
    }
    yield* pop(rawPanel);
    yield* waitFor(FEATURE_COUNT > 1 ? 7.18 : 3.5);

    yield* all(rawPanel().opacity(0, 0.16), rawPanel().scale(0.82, 0.18, easeInCubic));
    if (FEATURE_COUNT > 2) {
      sectionTitle().text(FEATURE_SECTIONS[2]);
    }
    yield* all(
      medicalPanel().opacity(1, 0.1),
      medicalPanel().scale(1, 0.36, easeOutBack),
      magnifier().opacity(1, 0.12),
      magnifier().scale(1, 0.42, easeOutBack),
    );
    yield* all(
      magnifier().position([-520, 55], 1.2, easeOutCubic),
      magnifier().rotation(-3, 1.2, easeOutCubic),
    );
    yield* waitFor(2.2);
    yield* all(
      magnifier().position([-475, 75], 1.1, easeOutCubic),
      magnifier().rotation(2, 1.1, easeOutCubic),
    );
    yield* waitFor(2.60);

    yield* all(
      mainTitle().opacity(0, 0.16),
      sectionTitle().opacity(0, 0.16),
      medicalPanel().opacity(0, 0.16),
      magnifier().opacity(0, 0.16),
    );
    mainTitle().text('适宜人群');
    mainTitle().position([0, -100]);
    mainTitle().scale(0.78);
    yield* all(mainTitle().opacity(1, 0.12), mainTitle().scale(1, 0.22, easeOutBack));
  }

  yield* all(visualTimeline(), runSubtitles(subtitle), applyEditablePatches(view, 30));
});

export default makeProject({
  scenes: [productTrainingFeaturesScene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
