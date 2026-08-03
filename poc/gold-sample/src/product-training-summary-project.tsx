import {Audio, Rect, Txt, makeScene2D} from '@revideo/2d';
import {all, createRef, easeOutBack, makeProject, waitFor} from '@revideo/core';

import data from '../product-training-summary.json';
import {
  DASHENLIN,
  DashenlinBrandMark,
  DashenlinInternalNotice,
  DashenlinOutroPanel,
  PRODUCT_TRAINING_FONT as FONT,
} from './components/product-training-dashenlin-chrome';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {productName, screenOf} from './product-training-content';

const PRODUCT = productName(data as any);
const SCREEN = screenOf(data as any);
const SUMMARY = SCREEN.summary || {};
const SUMMARY_HEADERS = SUMMARY.headers || ['核心功效', '产品特点', '适宜人群', '联合用药'];
const SUMMARY_CELLS = SUMMARY.cells || [
  '促进能量生成',
  '抗氧化，减少\n组织细胞损伤',
  '原研工艺，锁住活性',
  '海外原料，提升品质',
  '医疗背书',
  '顽固心慌、胸闷、气短\n的心血管人群',
  '常服他汀\n出现肌肉疲劳、疼痛的人群',
  '备孕男女',
  `复方丹参滴丸＋\n${PRODUCT}`,
  `他汀＋${PRODUCT}`,
];
const SUMMARY_BRAND = SUMMARY.brand || '大参林';
const SUMMARY_SLOGAN =
  SUMMARY.slogan || `内部培训 · ${PRODUCT} 商品知识`;

function Cell(props: {x: number; y: number; w: number; h: number; text: string; header?: boolean; size?: number}) {
  const fontSize = props.size ?? 35;
  return (
    <Rect
      position={[props.x, props.y]} size={[props.w, props.h]}
      fill={props.header ? '#079985' : '#ffffff'}
      stroke={'#3c4c54'} lineWidth={2}
    >
      <Txt
        width={props.w - 18} text={props.text} textAlign={'center'}
        fontFamily={FONT} fontSize={fontSize} lineHeight={fontSize * 1.28}
        fontWeight={props.header ? 900 : 600}
        fill={props.header ? '#ffffff' : '#1c2226'}
      />
    </Rect>
  );
}

export const productTrainingSummaryScene = makeScene2D('product-training-summary', function* (view) {
  const table = createRef<Rect>();
  const title = createRef<Txt>();
  const badge = createRef<Rect>();
  const slogan = createRef<Rect>();
  const mainStage = createRef<Rect>();
  const outro = createRef<Rect>();

  view.add(
    <>
      <Rect ref={mainStage} size={[1920, 1080]} opacity={1}>
        <Rect size={[1920, 1080]} fill={'#83cfea'} />
        <Audio src={data.audio.file} play />
        <DashenlinBrandMark />
        <Txt
          key={'editable:q10:summary:title'}
          ref={title} position={[-20, -445]} text={'总结'} fontFamily={FONT}
          fontSize={88} fontWeight={900} fill={'#ffffff'} stroke={'#18252c'}
          lineWidth={7} opacity={0} scale={0.7}
        />
        <Rect key={'editable:q10:summary:badge'} ref={badge} position={[590, -425]} size={[260, 104]} rotation={-7} opacity={0} scale={0.4}>
          <Txt text={'划重点'} fontFamily={FONT} fontSize={66} fontWeight={950} fill={DASHENLIN.primary} stroke={'#075e43'} lineWidth={5} />
          <Txt position={[112, -45]} text={'✎'} fontFamily={FONT} fontSize={48} fill={'#ffca2f'} />
        </Rect>
        <Rect key={'editable:q10:summary:table'} ref={table} position={[-40, 38]} size={[1720, 620]} opacity={0} scale={0.84}>
          <Cell x={-676} y={-260} w={330} h={78} text={SUMMARY_HEADERS[0]} header />
          <Cell x={-310} y={-260} w={402} h={78} text={SUMMARY_HEADERS[1]} header />
          <Cell x={140} y={-260} w={498} h={78} text={SUMMARY_HEADERS[2]} header />
          <Cell x={594} y={-260} w={410} h={78} text={SUMMARY_HEADERS[3]} header />
          <Cell x={-676} y={-112} w={330} h={218} text={SUMMARY_CELLS[0]} size={33} />
          <Cell x={-676} y={118} w={330} h={242} text={SUMMARY_CELLS[1]} size={32} />
          <Cell x={-310} y={-112} w={402} h={218} text={SUMMARY_CELLS[2]} size={31} />
          <Cell x={-310} y={74} w={402} h={154} text={SUMMARY_CELLS[3]} size={31} />
          <Cell x={-310} y={234} w={402} h={166} text={SUMMARY_CELLS[4]} size={31} />
          <Cell x={140} y={-112} w={498} h={218} text={SUMMARY_CELLS[5]} size={31} />
          <Cell x={140} y={74} w={498} h={154} text={SUMMARY_CELLS[6]} size={29} />
          <Cell x={140} y={234} w={498} h={166} text={SUMMARY_CELLS[7]} size={31} />
          <Cell x={594} y={-112} w={410} h={218} text={SUMMARY_CELLS[8]} size={31} />
          <Cell x={594} y={152} w={410} h={384} text={SUMMARY_CELLS[9]} size={31} />
        </Rect>
        <Rect key={'editable:q10:summary:slogan'} ref={slogan} position={[-25, 425]} size={[1710, 110]} opacity={0} scale={0.86}>
          <Txt position={[-520, 0]} text={SUMMARY_BRAND} fontFamily={FONT} fontSize={72} fontWeight={950} fill={DASHENLIN.primary} stroke={'#ffffff'} lineWidth={4} />
          <Txt position={[220, 4]} text={SUMMARY_SLOGAN} fontFamily={FONT} fontSize={48} fontWeight={900} fill={'#ffffff'} stroke={'#101820'} lineWidth={5} />
        </Rect>
        <DashenlinInternalNotice />
      </Rect>
      <Rect ref={outro} size={[1920, 1080]} opacity={0}>
        <DashenlinOutroPanel />
      </Rect>
    </>,
  );

  yield* all(
    (function* () {
      yield* all(
        title().opacity(1, 0.12), title().scale(1, 0.28, easeOutBack),
        badge().opacity(1, 0.16), badge().scale(1, 0.32, easeOutBack),
      );
      yield* all(table().opacity(1, 0.16), table().scale(1, 0.36, easeOutBack));
      yield* all(slogan().opacity(1, 0.14), slogan().scale(1, 0.30, easeOutBack));
      yield* waitFor(2.2);
      yield* all(mainStage().opacity(0, 0.35), outro().opacity(1, 0.4));
      yield* waitFor(1.8);
    })(),
    applyEditablePatches(view, 6),
  );
});

export default makeProject({
  scenes: [productTrainingSummaryScene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
