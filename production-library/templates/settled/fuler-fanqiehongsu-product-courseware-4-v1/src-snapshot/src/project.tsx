/**
 * 商品培训课件4 · Revideo 可编辑工程
 *
 * - 底板：scene-stills-editor-bg（签样版式、无烧录字）
 * - 可编辑层：Txt/Img，key=editable:cw4:*，字号坐标对齐 PIL
 * - **每页独立 makeScene2D**，避免非首页 opacity=0 导致插件点选失效
 * - 长文：width + textWrap
 */
import {Audio, Img, Rect, makeScene2D} from '@revideo/2d';
import {
  all,
  easeInCubic,
  easeOutBack,
  easeOutCubic,
  loop,
  makeProject,
  waitFor,
} from '@revideo/core';

import {K, T, assetSrc, scenes, type Scene} from './content';
import {applyEditablePatches} from './editor/apply-editable-patches';
import {
  BODY,
  BROWN,
  INK,
  LABEL,
  LIME,
  MUTED,
  SILK,
  WHITE,
  box,
  nodeOf,
  popIn,
  pulseArrowX,
  softPulseScale,
} from './motion/primitives';
import {
  CaptionLayer,
  captionSegments,
  captionText,
  playCaptions,
} from './motion/captions';
import {CTxt, EImg, EditableChapter, YellowLabel, bgSrc} from './ui';

/**
 * 动效语法对齐辅酶Q10 / 礼风热证业务编辑器：
 * - 节点用 opacity+scale 入场（easeOutBack）
 * - 强调循环用 loop + 位移（箭头沿指向方向）
 * - 与 applyEditablePatches / 字幕并行 yield* all(...)
 * 成片 Revideo film 工程与编辑器 Revideo 动效共享 src/motion 单源；编辑器 scrub 可播。
 */

function SceneLayers({sc}: {sc: Scene}) {
  const page = sc.id;
  const layers: any[] = [
    <Img key={`bg-${page}`} src={bgSrc(page)} size={[1920, 1080]} zIndex={0} />,
  ];

  if (page === 'S00_cover' || page === 'S15_end') {
    layers.push(
      <CTxt
        page={page}
        role="title_pill"
        text={T(page, 'title_pill', sc.title_pill || '福尔番茄红素软胶囊')}
        x={480}
        y={52}
        w={960}
        h={100}
        fontSize={68}
        fill={WHITE}
        fontWeight={800}
        align="center"
      />,
    );
    const benefits = sc.benefits || [
      '保护前列腺，提高精子活力',
      '抗氧化，延缓衰老',
      '增强免疫力',
    ];
    benefits.forEach((b, i) => {
      const yy = 290 + i * 108;
      layers.push(
        <CTxt
          page={page}
          role={`benefit.${i + 1}`}
          text={T(page, `benefit.${i + 1}`, b)}
          x={210}
          y={yy + 14}
          w={700}
          h={70}
          fontSize={52}
          fill={INK}
          fontWeight={600}
          align="left"
        />,
      );
    });
    layers.push(
      <Img
        key={K(page, 'pack_a')}
        src={assetSrc('slot-pack-box-a.png')}
        position={box(910, 330, 420, 420).position}
        size={[420, 420]}
        opacity={0}
        scale={0.82}
      />,
      <Img
        key={K(page, 'pack_b')}
        src={assetSrc('slot-pack-box-b.png')}
        position={box(1190, 330, 420, 420).position}
        size={[420, 420]}
        opacity={0}
        scale={0.82}
      />,
      <Img
        key={K(page, 'pack_bottle')}
        src={assetSrc('slot-pack-bottle.png')}
        position={box(1430, 290, 460, 460).position}
        size={[460, 460]}
        opacity={0}
        scale={0.82}
      />,
    );
  }

  if (page === 'S01_time_list') {
    // 入场动效节点：初始 scale/opacity 由 playSceneMotion 弹出
    layers.push(
      <EImg
        page={page}
        role="magazine"
        src={assetSrc('slot-time-magazine.png')}
        cx={211 + 389 / 2}
        cy={261 + 558 / 2}
        w={389}
        h={558}
        opacity={0}
        scale={0.78}
      />,
      <Img
        key={K(page, 'card_chevron')}
        src={assetSrc('icon-chevron-lime.png')}
        position={[820 + 36 - 960, 330 + 36 - 540]}
        size={[72, 72]}
        opacity={0}
        scale={0.7}
      />,
      <CTxt
        page={page}
        role="card_title"
        text={T(
          page,
          'card_title',
          sc.card_title || '对人类健康贡献最大的10种健康食品',
        )}
        x={910}
        y={330}
        w={780}
        h={80}
        fontSize={42}
        fill={LIME}
        fontWeight={600}
        align="left"
      />,
    );
    (sc.list || ['1.番茄', '2.***', '3.***']).forEach((line, i) => {
      layers.push(
        <CTxt
          page={page}
          role={`list.${i + 1}`}
          text={T(page, `list.${i + 1}`, line)}
          x={860}
          y={460 + i * 100}
          w={800}
          h={90}
          fontSize={68}
          fill={'#f2f2f2'}
          fontWeight={600}
          align="left"
        />,
      );
    });
  }

  // S02 broll — was missing all editable layers (only baked bg)
  if (page === 'S02_broll') {
    layers.push(
      <EImg
        page={page}
        role="photo"
        src={assetSrc('slot-photo-tomato.png')}
        cx={960}
        cy={480}
        size={640}
      />,
    );
  }

  if (
    [
      'S04_benefit_1',
      'S05_benefit_2',
      'S06_benefit_3',
      'S07_origin',
      'S08_material',
      'S09_content',
    ].includes(page)
  ) {
    const chapterDefault = ['S04_benefit_1', 'S05_benefit_2', 'S06_benefit_3'].includes(
      page,
    )
      ? '一、三大核心功效'
      : '二、产品特点';
    layers.push(
      <EditableChapter
        page={page}
        text={T(page, 'chapter', sc.chapter || chapterDefault)}
        y={40}
      />,
    );
    const sectionDefault: Record<string, string> = {
      S04_benefit_1: '1、保护前列腺、提高精子活力',
      S05_benefit_2: '2、抗氧化，延缓衰老',
      S06_benefit_3: '3、增强免疫力',
      S07_origin: '1、产地好',
      S08_material: '2、原料优',
      S09_content: '3、含量高',
    };
    layers.push(
      <CTxt
        page={page}
        role="section"
        text={T(page, 'section', sc.section || sectionDefault[page] || '')}
        x={170}
        y={154}
        w={1500}
        h={70}
        fontSize={56}
        fill={BROWN}
        fontWeight={800}
        align="left"
      />,
    );
  }

  // Benefit chains — 初始隐藏，由 playSceneMotion 序贯弹出（对齐 Q10）
  if (page === 'S04_benefit_1') {
    layers.push(
      <EImg
        page={page}
        role="tomato"
        src={assetSrc('tomato.png')}
        cx={602}
        cy={580}
        size={360}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="arrow"
        src={assetSrc('arrow-red.png')}
        cx={916}
        cy={580}
        size={110}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="prostate"
        src={assetSrc('prostate-diagram.png')}
        cx={1273}
        cy={580}
        size={400}
        opacity={0}
        scale={0.72}
      />,
      <Img
        key={K(page, 'section_chevron')}
        src={assetSrc('icon-chevron-white.png')}
        position={[92 + 31 - 960, 150 + 31 - 540]}
        size={[62, 62]}
        opacity={0}
      />,
    );
  }
  if (page === 'S05_benefit_2') {
    const cxs = [484, 724, 966, 1207, 1442];
    layers.push(
      <EImg
        page={page}
        role="tomato"
        src={assetSrc('tomato.png')}
        cx={cxs[0]}
        cy={580}
        size={260}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="arrow1"
        src={assetSrc('arrow-red.png')}
        cx={cxs[1]}
        cy={580}
        size={96}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="o2"
        src={assetSrc('o2-cutout.png')}
        cx={cxs[2]}
        cy={580}
        size={260}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="mark_x"
        src={assetSrc('mark-red-x-hand.png')}
        cx={cxs[2]}
        cy={580}
        size={250}
        opacity={0}
        scale={0.55}
      />,
      <EImg
        page={page}
        role="arrow2"
        src={assetSrc('arrow-red.png')}
        cx={cxs[3]}
        cy={580}
        size={96}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="woman"
        src={assetSrc('skincare-woman.png')}
        cx={cxs[4]}
        cy={580}
        size={280}
        opacity={0}
        scale={0.72}
      />,
      <Img
        key={K(page, 'section_chevron')}
        src={assetSrc('icon-chevron-white.png')}
        position={[92 + 31 - 960, 150 + 31 - 540]}
        size={[62, 62]}
        opacity={0}
      />,
    );
  }
  if (page === 'S06_benefit_3') {
    const cxs = [424, 664, 929, 1194, 1466];
    layers.push(
      <EImg
        page={page}
        role="tomato"
        src={assetSrc('tomato.png')}
        cx={cxs[0]}
        cy={580}
        size={260}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="arrow1"
        src={assetSrc('arrow-red.png')}
        cx={cxs[1]}
        cy={580}
        size={96}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="nk"
        src={assetSrc('nk-cell-labeled.png')}
        cx={cxs[2]}
        cy={580}
        size={300}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="arrow2"
        src={assetSrc('arrow-red.png')}
        cx={cxs[3]}
        cy={580}
        size={96}
        opacity={0}
        scale={0.72}
      />,
      <EImg
        page={page}
        role="arm"
        src={assetSrc('flex-arm-cutout.png')}
        cx={cxs[4]}
        cy={580}
        size={300}
        opacity={0}
        scale={0.72}
      />,
      <Img
        key={K(page, 'section_chevron')}
        src={assetSrc('icon-chevron-white.png')}
        position={[92 + 31 - 960, 150 + 31 - 540]}
        size={[62, 62]}
        opacity={0}
      />,
    );
  }

  if (page === 'S07_origin') {
    layers.push(
      <CTxt
        page={page}
        role="map_caption"
        text={T(page, 'map_caption', sc.map_caption || '中国分省地图—新疆维吾尔自治区')}
        x={360}
        y={240}
        w={1200}
        h={50}
        fontSize={36}
        fill={MUTED}
        fontWeight={500}
        align="center"
      />,
      <EImg
        page={page}
        role="map"
        src={assetSrc('map-xinjiang.png')}
        cx={960}
        cy={580}
        size={460}
      />,
    );
  }

  if (page === 'S08_material') {
    layers.push(
      <EImg
        page={page}
        role="vine"
        src={assetSrc('slot-photo-vine.png')}
        cx={960}
        cy={560}
        size={520}
      />,
    );
  }

  if (page === 'S09_content') {
    const cxs = [650, 910, 1220];
    layers.push(
      <EImg page={page} role="softgel" src={assetSrc('softgel.png')} cx={cxs[0]} cy={560} size={280} />,
      <CTxt
        page={page}
        role="eq"
        text={T(page, 'eq', '=')}
        x={cxs[1] - 70}
        y={470}
        w={140}
        h={140}
        fontSize={140}
        fill={'#e8c020'}
        fontWeight={900}
        align="center"
      />,
      <EImg
        page={page}
        role="five_tomatoes"
        src={assetSrc('five-tomatoes.png')}
        cx={cxs[2]}
        cy={560}
        size={380}
      />,
    );
  }

  if (page === 'S10_audience') {
    // Only once — was duplicated with S04–S10 chapter block (Duplicated node key crash)
    layers.push(
      <EditableChapter page={page} text={T(page, 'chapter', sc.chapter || '三、适宜人群')} y={40} />,
    );
    const iconFiles = [
      'prostate-diagram.png',
      'couple.png',
      'audience-beauty.png',
      'audience-weak.png',
    ];
    const items = sc.items || [
      {label: '前列腺患病'},
      {label: '备孕男士和女士'},
      {label: '爱美人士'},
      {label: '身体虚弱人群'},
    ];
    const margin = 100;
    const colW = (1920 - 2 * margin) / Math.max(items.length, 1);
    items.forEach((it, i) => {
      const cx = margin + colW * (i + 0.5);
      layers.push(
        <EImg
          page={page}
          role={`icon.${i + 1}`}
          src={assetSrc(iconFiles[i] || 'tomato.png')}
          cx={cx}
          cy={500}
          size={300}
        />,
        <YellowLabel
          page={page}
          role={`label.${i + 1}`}
          text={T(page, `label.${i + 1}`, it.label)}
          cx={cx}
          y={680}
          w={340}
          fontSize={42}
        />,
      );
    });
  }

  if (page === 'S11_summary') {
    layers.push(
      <EditableChapter
        page={page}
        text={T(page, 'chapter', sc.chapter || '五、福尔番茄红素三大核心功效')}
        y={22}
      />,
      <CTxt
        page={page}
        role="side_left"
        text={T(page, 'side_left', sc.side_left || '不适宜人群：少年儿童、孕妇、乳母')}
        x={20}
        y={180}
        w={48}
        h={720}
        fontSize={28}
        fill={MUTED}
        fontWeight={600}
        align="center"
      />,
      <CTxt
        page={page}
        role="side_right"
        text={T(
          page,
          'side_right',
          sc.side_right || '每日1次，每次1粒，建议固定随餐服用，避免漏服',
        )}
        x={1850}
        y={160}
        w={48}
        h={760}
        fontSize={28}
        fill={MUTED}
        fontWeight={600}
        align="center"
      />,
    );
    const rows = sc.rows || [];
    const table = {left: 148, top: 138, bot: 980, left_w: 420};
    const fh = (table.bot - table.top) / Math.max(rows.length, 1);
    rows.forEach((row, i) => {
      const y0 = table.top + i * fh;
      layers.push(
        <CTxt
          page={page}
          role={`row.${i + 1}.label`}
          text={T(page, `row.${i + 1}.label`, row.label)}
          x={table.left + 88}
          y={y0 + 50}
          w={300}
          h={fh - 100}
          fontSize={48}
          fill={LABEL}
          fontWeight={900}
          align="left"
        />,
        <CTxt
          page={page}
          role={`row.${i + 1}.body`}
          text={T(page, `row.${i + 1}.body`, row.body)}
          x={table.left + table.left_w + 32}
          y={y0 + 40}
          w={1100}
          h={fh - 80}
          fontSize={40}
          fill={BODY}
          fontWeight={500}
          align="left"
        />,
      );
    });
  }

  if (page === 'S12_related_1' || page === 'S13_related_2') {
    layers.push(
      <EditableChapter
        page={page}
        text={T(page, 'chapter', sc.chapter || '四、关联用药')}
        y={36}
      />,
    );
    const nav = sc.nav || ['', ''];
    const active = sc.active_nav ?? (page === 'S12_related_1' ? 0 : 1);
    const xs = [100, 1000];
    const widths = [860, 820];
    nav.slice(0, 2).forEach((label, i) => {
      layers.push(
        <CTxt
          page={page}
          role={`nav.${i + 1}`}
          text={T(page, `nav.${i + 1}`, label)}
          x={xs[i] + 64}
          y={166}
          w={widths[i] - 90}
          h={40}
          fontSize={26}
          fill={i === active ? WHITE : MUTED}
          fontWeight={800}
          align="left"
        />,
      );
    });
    layers.push(
      <CTxt
        page={page}
        role="note"
        text={T(page, 'note', sc.note || '')}
        x={160}
        y={240}
        w={1600}
        h={70}
        fontSize={36}
        fill={'#3a2a28'}
        fontWeight={900}
        align="center"
      />,
      <Img
        key={K(page, 'pack_left')}
        src={assetSrc(sc.left_pack || 'slot-pack-lycopene.png')}
        position={box(320, 420, 400, 400).position}
        size={[400, 400]}
        opacity={0}
        scale={0.82}
      />,
      <Img
        key={K(page, 'pack_right')}
        src={assetSrc(sc.right_pack || 'slot-pack-zinc.png')}
        position={box(1140, 440, 360, 360).position}
        size={[360, 360]}
        opacity={0}
        scale={0.82}
      />,
      <CTxt
        page={page}
        role="left_label"
        text={T(page, 'left_label', sc.left_label || '')}
        x={320}
        y={870}
        w={400}
        h={40}
        fontSize={32}
        fill={'#6a3a30'}
        fontWeight={700}
        align="center"
      />,
      <CTxt
        page={page}
        role="right_label"
        text={T(page, 'right_label', sc.right_label || '')}
        x={1140}
        y={870}
        w={360}
        h={40}
        fontSize={32}
        fill={'#6a3a30'}
        fontWeight={700}
        align="center"
      />,
    );
  }

  // product intro: vine + packs (PIL centers)
  if (page === 'S03_product_intro') {
    layers.push(
      <EImg
        page={page}
        role="vine"
        src={assetSrc('slot-photo-vine-cutout.png')}
        cx={400}
        cy={500}
        size={440}
        opacity={0}
        scale={0.8}
      />,
      <EImg
        page={page}
        role="pack_a"
        src={assetSrc('slot-pack-box-a.png')}
        cx={1000}
        cy={520}
        size={440}
        opacity={0}
        scale={0.8}
      />,
      <EImg
        page={page}
        role="pack_b"
        src={assetSrc('slot-pack-box-b.png')}
        cx={1280}
        cy={520}
        size={440}
        opacity={0}
        scale={0.8}
      />,
      <EImg
        page={page}
        role="pack_bottle"
        src={assetSrc('slot-pack-bottle.png')}
        cx={1560}
        cy={500}
        size={480}
        opacity={0}
        scale={0.8}
      />,
    );
  }

  return <Rect size={[1920, 1080]}>{layers}</Rect>;
}

/** 业务编辑器内可播放动效（对齐 Q10 / 礼风热证） */
function* playSceneMotion(view: any, sc: Scene) {
  const page = sc.id;
  const dur = Math.max(0.1, Number(sc.end) - Number(sc.start));
  let t = 0;

  const spend = function* (sec: number) {
    const s = Math.max(0, sec);
    if (s > 0.001) yield* waitFor(s);
    t += s;
  };
  const remain = () => Math.max(0.05, dur - t);

  // 章节 / 小节标题轻弹
  const chapter = nodeOf(view, page, 'chapter');
  if (chapter && typeof chapter.scale === 'function') {
    try {
      chapter.scale(0.86);
      yield* all(
        chapter.opacity ? chapter.opacity(1, 0.1) : waitFor(0),
        chapter.scale(1, 0.28, easeOutBack),
      );
      t += 0.28;
    } catch {
      /* ignore */
    }
  }

  if (page === 'S01_time_list') {
    const mag = nodeOf(view, page, 'magazine');
    const chev = nodeOf(view, page, 'card_chevron');
    const title = nodeOf(view, page, 'card_title');
    yield* spend(0.08);
    if (mag) yield* popIn(mag, 0.42);
    yield* spend(0.12);
    if (chev) yield* popIn(chev, 0.32);
    if (title && typeof title.opacity === 'function') {
      title.opacity(0);
      yield* title.opacity(1, 0.16, easeOutCubic);
    }
    for (let i = 1; i <= 3; i++) {
      const row = nodeOf(view, page, `list.${i}`);
      if (row && typeof row.opacity === 'function') {
        row.opacity(0);
        if (typeof row.position?.y === 'function') {
          const y0 = row.position.y();
          row.position.y(y0 + 28);
          yield* all(
            row.opacity(1, 0.12, easeOutCubic),
            row.position.y(y0, 0.28, easeOutCubic),
          );
        } else {
          yield* row.opacity(1, 0.16, easeOutCubic);
        }
      }
      yield* spend(0.1);
    }
    // 黄绿 » 轻上下循环（表头强调）
    if (chev && typeof chev.position?.y === 'function') {
      const y0 = chev.position.y();
      yield* loop(Math.max(1, Math.floor(remain() / 0.7)), function* () {
        yield* chev.position.y(y0 - 7, 0.34, easeOutCubic);
        yield* chev.position.y(y0, 0.36, easeOutCubic);
      });
    } else {
      yield* spend(remain());
    }
    return;
  }

  if (page === 'S04_benefit_1') {
    const chev = nodeOf(view, page, 'section_chevron');
    const tomato = nodeOf(view, page, 'tomato');
    const arrow = nodeOf(view, page, 'arrow');
    const prostate = nodeOf(view, page, 'prostate');
    if (chev) yield* popIn(chev, 0.28);
    yield* spend(0.35);
    if (tomato) yield* popIn(tomato, 0.4);
    yield* spend(0.45);
    if (arrow) yield* popIn(arrow, 0.32);
    yield* spend(0.35);
    if (prostate) yield* popIn(prostate, 0.4);
    // 箭头向右脉冲 + 表头 chevron 轻跳
    const ax = arrow && typeof arrow.position?.x === 'function' ? arrow.position.x() : 0;
    const cy0 =
      chev && typeof chev.position?.y === 'function' ? chev.position.y() : null;
    yield* all(
      pulseArrowX(arrow, ax, remain(), 14),
      cy0 != null
        ? loop(Math.max(1, Math.floor(remain() / 0.7)), function* () {
            yield* chev.position.y(cy0 - 8, 0.34, easeOutCubic);
            yield* chev.position.y(cy0, 0.36, easeOutCubic);
          })
        : waitFor(remain()),
    );
    return;
  }

  if (page === 'S05_benefit_2') {
    const chev = nodeOf(view, page, 'section_chevron');
    const tomato = nodeOf(view, page, 'tomato');
    const a1 = nodeOf(view, page, 'arrow1');
    const o2 = nodeOf(view, page, 'o2');
    const markX = nodeOf(view, page, 'mark_x');
    const a2 = nodeOf(view, page, 'arrow2');
    const woman = nodeOf(view, page, 'woman');
    if (chev) yield* popIn(chev, 0.28);
    yield* spend(0.5);
    if (tomato) yield* popIn(tomato, 0.38);
    yield* spend(0.35);
    if (a1) yield* popIn(a1, 0.3);
    if (o2) yield* popIn(o2, 0.38);
    yield* spend(1.6);
    // 手绘叉弹出
    if (markX) {
      if (typeof markX.rotation === 'function') markX.rotation(-6);
      yield* popIn(markX, 0.32);
    }
    yield* spend(3.8);
    // 第二箭 + 护肤女；叉淡出
    if (a2) yield* popIn(a2, 0.3);
    if (woman) yield* popIn(woman, 0.4);
    if (markX && typeof markX.opacity === 'function') {
      yield* markX.opacity(0, 0.28, easeInCubic);
    }
    const ax1 = a1 && typeof a1.position?.x === 'function' ? a1.position.x() : 0;
    const ax2 = a2 && typeof a2.position?.x === 'function' ? a2.position.x() : 0;
    const cy0 =
      chev && typeof chev.position?.y === 'function' ? chev.position.y() : null;
    yield* all(
      pulseArrowX(a1, ax1, remain(), 14),
      pulseArrowX(a2, ax2, remain(), 14),
      cy0 != null
        ? loop(Math.max(1, Math.floor(remain() / 0.7)), function* () {
            yield* chev.position.y(cy0 - 8, 0.34, easeOutCubic);
            yield* chev.position.y(cy0, 0.36, easeOutCubic);
          })
        : waitFor(remain()),
    );
    return;
  }

  if (page === 'S06_benefit_3') {
    const chev = nodeOf(view, page, 'section_chevron');
    const tomato = nodeOf(view, page, 'tomato');
    const a1 = nodeOf(view, page, 'arrow1');
    const nk = nodeOf(view, page, 'nk');
    const a2 = nodeOf(view, page, 'arrow2');
    const arm = nodeOf(view, page, 'arm');
    if (chev) yield* popIn(chev, 0.28);
    yield* spend(0.4);
    if (tomato) yield* popIn(tomato, 0.38);
    yield* spend(0.35);
    if (a1) yield* popIn(a1, 0.3);
    if (nk) yield* popIn(nk, 0.42);
    yield* spend(3.2);
    if (a2) yield* popIn(a2, 0.3);
    if (arm) yield* popIn(arm, 0.42);
    const ax1 = a1 && typeof a1.position?.x === 'function' ? a1.position.x() : 0;
    const ax2 = a2 && typeof a2.position?.x === 'function' ? a2.position.x() : 0;
    const cy0 =
      chev && typeof chev.position?.y === 'function' ? chev.position.y() : null;
    yield* all(
      pulseArrowX(a1, ax1, remain(), 14),
      pulseArrowX(a2, ax2, remain(), 14),
      softPulseScale(arm, remain(), 0.04),
      cy0 != null
        ? loop(Math.max(1, Math.floor(remain() / 0.7)), function* () {
            yield* chev.position.y(cy0 - 8, 0.34, easeOutCubic);
            yield* chev.position.y(cy0, 0.36, easeOutCubic);
          })
        : waitFor(remain()),
    );
    return;
  }

  // 其它页：主视觉轻弹 + hold（更丰富但不抢戏）
  if (page === 'S00_cover' || page === 'S15_end') {
    for (const role of ['pack_a', 'pack_b', 'pack_bottle']) {
      const n = nodeOf(view, page, role);
      if (n) {
        if (typeof n.scale === 'function') n.scale(0.82);
        if (typeof n.opacity === 'function') n.opacity(0);
        yield* popIn(n, 0.34);
        yield* spend(0.08);
      }
    }
    yield* spend(remain());
    return;
  }
  if (page === 'S02_broll') {
    const photo = nodeOf(view, page, 'photo');
    if (photo) {
      if (typeof photo.scale === 'function') photo.scale(0.88);
      if (typeof photo.opacity === 'function') photo.opacity(0);
      yield* popIn(photo, 0.45);
    }
    yield* spend(remain());
    return;
  }
  if (page === 'S03_product_intro') {
    for (const role of ['vine', 'pack_a', 'pack_b', 'pack_bottle']) {
      const n = nodeOf(view, page, role);
      if (n) {
        if (typeof n.scale === 'function') n.scale(0.8);
        if (typeof n.opacity === 'function') n.opacity(0);
        yield* popIn(n, 0.34);
        yield* spend(0.06);
      }
    }
    yield* spend(remain());
    return;
  }
  if (page === 'S07_origin') {
    const map = nodeOf(view, page, 'map');
    if (map) {
      if (typeof map.scale === 'function') map.scale(0.75);
      if (typeof map.opacity === 'function') map.opacity(0);
      yield* popIn(map, 0.45);
    }
    yield* spend(remain());
    return;
  }
  if (page === 'S09_content') {
    for (const role of ['softgel', 'eq', 'five_tomatoes']) {
      const n = nodeOf(view, page, role);
      if (n) {
        if (typeof n.scale === 'function') n.scale(0.75);
        if (typeof n.opacity === 'function') n.opacity(0);
        yield* popIn(n, 0.34);
        yield* spend(0.1);
      }
    }
    yield* spend(remain());
    return;
  }
  if (page === 'S10_audience') {
    for (let i = 1; i <= 4; i++) {
      const icon = nodeOf(view, page, `icon.${i}`);
      const label = nodeOf(view, page, `label.${i}`);
      if (icon) {
        if (typeof icon.scale === 'function') icon.scale(0.7);
        if (typeof icon.opacity === 'function') icon.opacity(0);
        yield* popIn(icon, 0.32);
      }
      if (label && typeof label.opacity === 'function') {
        label.opacity(0);
        yield* label.opacity(1, 0.14, easeOutCubic);
      }
      yield* spend(0.12);
    }
    yield* spend(remain());
    return;
  }
  if (page === 'S12_related_1' || page === 'S13_related_2') {
    for (const role of ['pack_left', 'pack_right', 'note']) {
      const n = nodeOf(view, page, role);
      if (n) {
        if (typeof n.scale === 'function') n.scale(0.82);
        if (typeof n.opacity === 'function') n.opacity(0);
        yield* popIn(n, 0.34);
        yield* spend(0.1);
      }
    }
    yield* spend(remain());
    return;
  }

  yield* spend(remain());
}

function makePageScene(sc: Scene) {
  const dur = Math.max(0.1, Number(sc.end) - Number(sc.start));
  const firstCap = captionSegments(sc)[0]?.text || captionText(sc);
  // Absolute start on the full reference narration timeline (sec)
  const audioOffset = Math.max(0, Number(sc.start) || 0);
  return makeScene2D(sc.id, function* (view) {
    view.fill(SILK);
    // 每页挂载完整参考旁白轨，time=场景绝对起点，scrub/切场景时继续跟口播
    view.add(
      <Audio
        key={`narration-${sc.id}`}
        src={'/narration.mp3'}
        play={true}
        volume={1}
        time={audioOffset}
      />,
    );
    view.add(<SceneLayers sc={sc} />);
    view.add(<CaptionLayer page={sc.id} text={firstCap} />);
    // 对齐 Q10：动效 + 字幕 + 可编辑补丁 并行
    yield* all(
      playSceneMotion(view, sc),
      playCaptions(view, sc),
      applyEditablePatches(view, dur),
    );
  });
}

const list = scenes();
const pageScenes = list.map(sc => makePageScene(sc));

export default makeProject({
  name: 'product-courseware-4-faithful-replica-v1',
  scenes: pageScenes,
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: SILK,
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
