/**
 * film 15 页装配：每页 = SilkFolds + chrome 形状 + editable 内容。
 * 坐标/字号一律取自 ../layout.ts（PIL 抄录单一来源），禁止在此写字面量坐标。
 * pre 入场预置仅 film 模式生效；editor-bg 模式所有元素直置终态。
 */
import {Circle, Img, Layout, Line, Node} from '@revideo/2d';

import {T, type Scene} from '../content';
import {
  CHAPTER,
  COVER,
  RELATED,
  S01,
  S02,
  S03,
  S04,
  S05,
  S06,
  S07,
  S08,
  S09,
  S10,
  S11,
  chainLayout,
  hSize,
  layoutFor,
} from '../layout';
import {INK, RED, WHITE} from '../motion/primitives';
import {chainCxs} from '../ui';
import {
  ChromeRect,
  FImg,
  FTxt,
  FilmChapter,
  FilmSection,
  OutlineTxt,
  Poly,
  SilkFolds,
  chromeKey,
  type FilmMode,
} from './parts';

const POP = {opacity: 0, scale: 0.82};
const CHAIN = {opacity: 0, scale: 0.92, dy: 22};
const CHAIN_NO_RISE = {opacity: 0, scale: 0.92, dy: 0};

function CoverPage({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const L = COVER;
  const pill = T(page, 'title_pill', sc.title_pill || L.pill.fallback);
  const pillW = [...pill].length * L.pill.font + L.pill.padX * 2;
  const benefits = sc.benefits || L.benefits.fallback;
  const pre = mode === 'film' ? POP : {};
  return (
    <>
      <Poly k={chromeKey(page, 'mountains')} points={L.mountains.points} fill={L.mountains.fill} />
      <ChromeRect
        page={page}
        role="pill"
        x={960 - pillW / 2}
        y={L.pill.y0}
        w={pillW}
        h={L.pill.y1 - L.pill.y0}
        radius={L.pill.radius}
        fill={L.pill.fill}
      />
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="title_pill"
        text={pill}
        cx={960}
        cy={L.pill.textY + L.pill.font / 2}
        width={pillW}
        fontSize={L.pill.font}
        weight={700}
        fill={L.pill.textFill}
        align="center"
      />
      <FImg mode={mode} layer="chrome" page={page} role="badge" asset={L.badge.asset} cx={L.badge.cx} cy={L.badge.cy} h={L.badge.h} />
      {benefits.map((line, i) => {
        const yy = L.benefits.y0 + i * L.benefits.step;
        return (
          <Node key={`film:grp:${page}:benefit-${i}`}>
            <FImg
              mode={mode}
              layer="chrome"
              page={page}
              role={`benefit_check.${i + 1}`}
              asset={L.benefits.icon}
              cx={L.benefits.iconX + L.benefits.iconSize / 2}
              cy={yy + L.benefits.iconSize / 2}
              h={L.benefits.iconSize}
            />
            <FTxt
              mode={mode}
              layer="editable"
              page={page}
              role={`benefit.${i + 1}`}
              text={T(page, `benefit.${i + 1}`, line)}
              cx={L.benefits.textX + 350}
              cy={yy + L.benefits.textDY + L.benefits.font / 2}
              width={700}
              fontSize={L.benefits.font}
              weight={500}
              fill={INK}
              align="left"
            />
          </Node>
        );
      })}
      {L.packs.map((p, i) => (
        <FImg
          mode={mode}
          layer="editable"
          page={page}
          role={['pack_a', 'pack_b', 'pack_bottle'][i]}
          asset={p.asset}
          cx={p.cx}
          cy={p.cy}
          h={p.h}
          pre={pre}
        />
      ))}
    </>
  );
}

function S01Page({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const pre = mode === 'film';
  const card = S01.card;
  const list = sc.list || S01.list.fallback;
  return (
    <>
      <FImg
        mode={mode}
        layer="editable"
        page={page}
        role="magazine"
        asset={S01.magazine.asset}
        cx={S01.magazine.cx}
        cy={S01.magazine.cy}
        h={S01.magazine.h}
        pre={pre ? {opacity: 0, scale: 0.88, dy: 36} : {}}
      />
      <ChromeRect
        page={page}
        role="card"
        x={card.x}
        y={card.y}
        w={card.w}
        h={card.h}
        radius={card.radius}
        fill={card.fill}
        pre={pre ? {opacity: 0, scale: 0.92, dy: 28} : {}}
      />
      <Line
        key={chromeKey(page, 'rule')}
        points={[
          [S01.rule.x0 - 960, S01.rule.y - 540],
          [S01.rule.x1 - 960, S01.rule.y - 540],
        ]}
        stroke={S01.rule.fill}
        lineWidth={S01.rule.width}
        opacity={pre ? 0 : 1}
      />
      <FImg
        mode={mode}
        layer="chrome"
        page={page}
        role="card_chevron"
        asset={S01.chevron.asset}
        cx={S01.chevron.x + S01.chevron.size / 2}
        cy={S01.chevron.y + S01.chevron.size / 2}
        h={S01.chevron.size}
        pre={pre ? POP : {}}
      />
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="card_title"
        text={T(page, 'card_title', sc.card_title || S01.cardTitle.fallback)}
        cx={S01.cardTitle.x + 380}
        cy={S01.cardTitle.y + S01.cardTitle.font / 2}
        width={760}
        fontSize={S01.cardTitle.font}
        weight={400}
        fill={S01.cardTitle.fill}
        align="left"
        pre={pre ? {opacity: 0} : {}}
      />
      {list.slice(0, S01.list.rows).map((line, i) => (
        <FTxt
          mode={mode}
          layer="editable"
          page={page}
          role={`list.${i + 1}`}
          text={T(page, `list.${i + 1}`, line)}
          cx={S01.list.x + 400}
          cy={S01.list.y0 + i * S01.list.step + S01.list.font / 2}
          width={800}
          fontSize={S01.list.font}
          weight={500}
          fill={S01.list.fill}
          align="left"
          pre={pre ? {opacity: 0, dy: 28} : {}}
        />
      ))}
    </>
  );
}

/** S04/S05/S06 链路页通用装配；返回的 redX 仅 S05 用 */
function ChainPage({
  sc,
  mode,
  spec,
  roles,
  redX,
}: {
  sc: Scene;
  mode: FilmMode;
  spec: typeof S04 | typeof S05 | typeof S06;
  roles: string[];
  redX?: {asset: string; h: number; rot: number; atIndex: number; role: string};
}) {
  const page = sc.id;
  const pre = mode === 'film';
  const items = chainLayout(spec.chain.items, spec.chain.gap);
  return (
    <>
      <FilmChapter
        mode={mode}
        page={page}
        text={T(page, 'chapter', sc.chapter || spec.chapterFallback)}
        y={spec.chapterY}
        pre={pre ? {opacity: 0, scale: 0.86} : {}}
      />
      <FilmSection mode={mode} page={page} spec={spec.section} chevPre={pre ? POP : {}} />
      {items.map((it, i) => (
        <FImg
          mode={mode}
          layer="editable"
          page={page}
          role={roles[i]}
          asset={it.asset}
          cx={it.cx}
          cy={spec.chain.cy}
          h={it.h}
          pre={pre ? (it.asset.startsWith('arrow') ? CHAIN_NO_RISE : CHAIN) : {}}
        />
      ))}
      {redX &&
        (() => {
          const o2 = items[redX.atIndex];
          return (
            <FImg
              mode={mode}
              layer="editable"
              page={page}
              role={redX.role}
              asset={redX.asset}
              cx={o2.cx}
              cy={spec.chain.cy}
              h={redX.h}
              rotation={redX.rot}
              pre={pre ? {opacity: 0, scale: 0.88} : {}}
            />
          );
        })()}
    </>
  );
}

function S07Page({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const pre = mode === 'film';
  const chapterText = T(page, 'chapter', sc.chapter || S07.chapterFallback);
  // 推镜头层：同图 ×2.2，中心与底图对齐；clip 窗口（layout S07.zoom）避开章节/表头/字幕
  const [zw, zh] = hSize(S07.map.asset, S07.map.h);
  const clipCy = (S07.zoom.clipY0 + S07.zoom.clipY1) / 2;
  // 章节装饰线：章节标题下沿，宽度随字数（PIL 无此元素，仅 film 叠加）
  const ruleW = [...chapterText].length * CHAPTER.font;
  const ruleY = S07.chapterY + CHAPTER.font + 12;
  return (
    <>
      <FilmChapter
        mode={mode}
        page={page}
        text={chapterText}
        y={S07.chapterY}
        pre={pre ? {opacity: 0, scale: 0.86} : {}}
      />
      <FilmSection mode={mode} page={page} spec={S07.section} chevPre={pre ? POP : {}} />
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="map_caption"
        text={T(page, 'map_caption', sc.map_caption || S07.mapCaption.fallback)}
        cx={960}
        cy={S07.mapCaption.y + S07.mapCaption.font / 2}
        width={900}
        fontSize={S07.mapCaption.font}
        weight={500}
        fill={S07.mapCaption.fill}
        align="center"
        pre={pre ? {opacity: 0} : {}}
      />
      <FImg
        mode={mode}
        layer="editable"
        page={page}
        role="map"
        asset={S07.map.asset}
        cx={S07.map.cx}
        cy={S07.map.cy}
        h={S07.map.h}
        pre={pre ? CHAIN : {}}
      />
      {mode === 'film' && (
        <Layout
          key={`film:decor:${page}:map-zoom`}
          position={[0, clipCy - 540]}
          size={[1920, S07.zoom.clipY1 - S07.zoom.clipY0]}
          clip={true}
          opacity={0}
          layout={false}
        >
          <Img
            src={`/assets/${S07.map.asset}`}
            position={[S07.map.cx - 960, S07.map.cy - clipCy]}
            size={[zw, zh]}
            scale={S07.zoom.scale}
          />
        </Layout>
      )}
      {mode === 'film' && (
        <Line
          key={`film:decor:${page}:chapter-rule`}
          points={[
            [-ruleW / 2, ruleY - 540],
            [ruleW / 2, ruleY - 540],
          ]}
          stroke={CHAPTER.outline}
          lineWidth={6}
          end={0}
        />
      )}
    </>
  );
}

function S08Page({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const pre = mode === 'film';
  return (
    <>
      <FilmChapter
        mode={mode}
        page={page}
        text={T(page, 'chapter', sc.chapter || S08.chapterFallback)}
        y={S08.chapterY}
        pre={pre ? {opacity: 0, scale: 0.86} : {}}
      />
      <FilmSection mode={mode} page={page} spec={S08.section} chevPre={pre ? POP : {}} />
      <FImg
        mode={mode}
        layer="editable"
        page={page}
        role="vine"
        asset={S08.photo.asset}
        cx={S08.photo.cx}
        cy={S08.photo.cy}
        h={S08.photo.h}
        pre={pre ? CHAIN : {}}
      />
    </>
  );
}

function S09Page({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const pre = mode === 'film';
  const cxs = chainCxs(S09.slots.widths, S09.slots.gap);
  return (
    <>
      <FilmChapter
        mode={mode}
        page={page}
        text={T(page, 'chapter', sc.chapter || S09.chapterFallback)}
        y={S09.chapterY}
        pre={pre ? {opacity: 0, scale: 0.86} : {}}
      />
      <FilmSection mode={mode} page={page} spec={S09.section} chevPre={pre ? POP : {}} />
      <FImg
        mode={mode}
        layer="editable"
        page={page}
        role="softgel"
        asset={S09.softgel.asset}
        cx={cxs[0]}
        cy={S09.slots.cy}
        h={S09.softgel.h}
        pre={pre ? CHAIN : {}}
      />
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="eq"
        text="="
        cx={cxs[1]}
        cy={S09.eq.y + S09.eq.font / 2}
        width={200}
        fontSize={S09.eq.font}
        weight={900}
        fill={S09.eq.fill}
        align="center"
        pre={pre ? POP : {}}
      />
      <FImg
        mode={mode}
        layer="editable"
        page={page}
        role="five_tomatoes"
        asset={S09.five.asset}
        cx={cxs[2]}
        cy={S09.slots.cy}
        h={S09.five.h}
        pre={pre ? CHAIN : {}}
      />
    </>
  );
}

function S10Page({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const pre = mode === 'film';
  const colW = (1920 - 2 * S10.marginX) / S10.cols;
  const items = sc.items?.length
    ? S10.items.map((it, i) => ({asset: it.asset, label: sc.items![i]?.label ?? it.label}))
    : S10.items;
  return (
    <>
      <FilmChapter
        mode={mode}
        page={page}
        text={T(page, 'chapter', sc.chapter || S10.chapterFallback)}
        y={S10.chapterY}
        pre={pre ? {opacity: 0, scale: 0.86} : {}}
      />
      {items.map((it, i) => {
        const cx = S10.marginX + colW * (i + 0.5);
        return (
          <Node key={`film:grp:${page}:aud-${i}`}>
            <FImg
              mode={mode}
              layer="editable"
              page={page}
              role={`icon.${i + 1}`}
              asset={it.asset}
              cx={cx}
              cy={S10.iconCy}
              h={S10.iconH}
              pre={pre ? CHAIN : {}}
            />
            {/* PIL omit_text 也烧录人群标签 → chrome（描边副本随主层） */}
            <OutlineTxt
              mode={mode}
              layer="chrome"
              page={page}
              role={`label.${i + 1}`}
              text={T(page, `label.${i + 1}`, it.label)}
              cx={cx}
              cy={S10.labelY + S10.labelFont / 2}
              width={340}
              fontSize={S10.labelFont}
              weight={900}
              fill={S10.labelFill}
              outline={S10.labelOutline}
              steps={4}
              pre={pre ? POP : {}}
            />
          </Node>
        );
      })}
    </>
  );
}

function S11Page({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const pre = mode === 'film';
  const t = S11.table;
  const rows = sc.rows?.length ? sc.rows : S11.rowsFallback;
  const fh = (t.y1 - t.y0) / rows.length;
  const vertical = (s: string) => [...s].join('\n');
  return (
    <>
      <FilmChapter
        mode={mode}
        page={page}
        text={T(page, 'chapter', sc.chapter || S11.chapterFallback)}
        y={S11.chapterY}
        pre={pre ? {opacity: 0, scale: 0.86} : {}}
      />
      {/* 表格线（chrome） */}
      <ChromeRect
        page={page}
        role="table"
        x={t.x0}
        y={t.y0}
        w={t.x1 - t.x0}
        h={t.y1 - t.y0}
        fill={'rgba(0,0,0,0)'}
        stroke={t.stroke}
        strokeW={t.strokeW}
      />
      {rows.slice(0, -1).map((_, i) => (
        <Line
          key={chromeKey(page, `rowline-${i}`)}
          points={[
            [t.x0 - 960, t.y0 + (i + 1) * fh - 540],
            [t.x1 - 960, t.y0 + (i + 1) * fh - 540],
          ]}
          stroke={t.stroke}
          lineWidth={2}
        />
      ))}
      <Line
        key={chromeKey(page, 'colline')}
        points={[
          [t.x0 + t.leftW - 960, t.y0 - 540],
          [t.x0 + t.leftW - 960, t.y1 - 540],
        ]}
        stroke={t.stroke}
        lineWidth={2}
      />
      {rows.map((row, i) => {
        const y0 = t.y0 + i * fh;
        const labLines = row.label.split('\n').length;
        const blockH = labLines * S11.label.lh;
        return (
          <Node key={`film:grp:${page}:row-${i}`}>
            <FImg
              mode={mode}
              layer="chrome"
              page={page}
              role={`row_chev.${i + 1}`}
              asset={S11.chevron.asset}
              cx={t.x0 + S11.chevron.dx + S11.chevron.size / 2}
              cy={y0 + fh / 2}
              h={S11.chevron.size}
              pre={pre ? POP : {}}
            />
            {/* 左列 width=340+textWrap：消解单行长标签溢出压右栏（现行 bug） */}
            <OutlineTxt
              mode={mode}
              layer="editable"
              page={page}
              role={`row.${i + 1}.label`}
              text={T(page, `row.${i + 1}.label`, row.label)}
              cx={t.x0 + S11.label.xOff + 170}
              cy={y0 + fh / 2}
              width={340}
              fontSize={S11.label.font}
              weight={900}
              fill={S11.label.fill}
              outline={S11.label.outline}
              steps={S11.label.outlineW}
              align="left"
              lineHeight={S11.label.lh}
              wrap={true}
              pre={pre ? {opacity: 0, dy: 18} : {}}
            />
            <OutlineTxt
              mode={mode}
              layer="editable"
              page={page}
              role={`row.${i + 1}.body`}
              text={T(page, `row.${i + 1}.body`, row.body)}
              cx={t.x0 + t.leftW + S11.body.xOff + (t.x1 - t.x0 - t.leftW - S11.body.xOff - 24) / 2}
              cy={y0 + fh / 2}
              width={t.x1 - t.x0 - t.leftW - S11.body.xOff - 24}
              fontSize={S11.body.font}
              weight={500}
              fill={S11.body.fill}
              outline={S11.body.outline}
              steps={S11.body.outlineW}
              align="left"
              lineHeight={S11.body.lh}
              wrap={true}
              pre={pre ? {opacity: 0, dy: 18} : {}}
            />
          </Node>
        );
      })}
      {/* 左右竖排说明 */}
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="side_left"
        text={vertical(T(page, 'side_left', sc.side_left || S11.side.leftFallback))}
        cx={S11.side.leftX + 20}
        cy={S11.side.leftY + 270}
        width={40}
        fontSize={S11.side.font}
        weight={500}
        fill={S11.side.fill}
        align="center"
        lineHeight={S11.side.step}
      />
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="side_right"
        text={vertical(T(page, 'side_right', sc.side_right || S11.side.rightFallback))}
        cx={S11.side.rightX + 20}
        cy={S11.side.rightY + 360}
        width={40}
        fontSize={S11.side.font}
        weight={500}
        fill={S11.side.fill}
        align="center"
        lineHeight={S11.side.step}
      />
    </>
  );
}

function RelatedPage({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const page = sc.id;
  const pre = mode === 'film';
  const L = RELATED;
  const nav = sc.nav || L.nav.fallback;
  const active = sc.active_nav ?? (page === 'S12_related_1' ? 0 : 1);
  const card = L.card;
  return (
    <>
      <FilmChapter
        mode={mode}
        page={page}
        text={T(page, 'chapter', sc.chapter || L.chapterFallback)}
        y={L.chapterY}
        pre={pre ? {opacity: 0, scale: 0.86} : {}}
      />
      {nav.slice(0, 2).map((label, i) => {
        const px = L.nav.xs[i];
        const pw = L.nav.widths[i];
        const isActive = i === active;
        return (
          <Node key={`film:grp:${page}:nav-${i}`}>
            <ChromeRect
              page={page}
              role={`nav_pill.${i + 1}`}
              x={px}
              y={L.nav.y}
              w={pw}
              h={L.nav.h}
              radius={30}
              fill={isActive ? L.nav.active : L.nav.inactive}
            />
            <Circle
              key={chromeKey(page, `nav_dot.${i + 1}`)}
              position={[px + L.nav.circleDX - 960, L.nav.y + L.nav.h / 2 - 540]}
              size={L.nav.r * 2}
              fill={isActive ? WHITE : RED}
            />
            <FTxt
              mode={mode}
              layer="editable"
              page={page}
              role={`nav_num.${i + 1}`}
              text={`${i + 1}`}
              cx={px + L.nav.circleDX}
              cy={L.nav.y + L.nav.h / 2}
              width={L.nav.r * 2}
              fontSize={L.nav.numFont}
              weight={900}
              fill={isActive ? RED : WHITE}
              align="center"
            />
            <FTxt
              mode={mode}
              layer="editable"
              page={page}
              role={`nav.${i + 1}`}
              text={T(page, `nav.${i + 1}`, label)}
              cx={px + L.nav.labelDX + (pw - 90) / 2}
              cy={L.nav.y + L.nav.labelDY + L.nav.font / 2}
              width={pw - 90}
              fontSize={L.nav.font}
              weight={700}
              fill={isActive ? L.nav.activeText : L.nav.inactiveText}
              align="left"
              pre={pre ? {opacity: 0} : {}}
            />
          </Node>
        );
      })}
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="note"
        text={T(page, 'note', sc.note || '')}
        cx={960}
        cy={L.note.y + L.note.font / 2}
        width={1600}
        fontSize={L.note.font}
        weight={900}
        fill={L.note.fill}
        align="center"
        pre={pre ? {opacity: 0} : {}}
      />
      <ChromeRect
        page={page}
        role="card"
        x={card.x0}
        y={card.y0}
        w={card.x1 - card.x0}
        h={card.y1 - card.y0}
        radius={card.radius}
        fill={card.fill}
        pre={pre ? {opacity: 0, scale: 0.94, dy: 16} : {}}
      />
      <FImg
        mode={mode}
        layer="editable"
        page={page}
        role="pack_left"
        asset={sc.left_pack || L.left.packFallback}
        cx={L.left.cx}
        cy={L.left.cy}
        h={L.left.h}
        pre={pre ? POP : {}}
      />
      <FImg
        mode={mode}
        layer="editable"
        page={page}
        role="pack_right"
        asset={sc.right_pack || L.right.packFallback}
        cx={L.right.cx}
        cy={L.right.cy}
        h={L.right.h}
        pre={pre ? POP : {}}
      />
      <FTxt
        mode={mode}
        layer="chrome"
        page={page}
        role="plus"
        text="+"
        cx={960}
        cy={L.plus.y + L.plus.font / 2}
        width={160}
        fontSize={L.plus.font}
        weight={900}
        fill={L.plus.fill}
        align="center"
        pre={pre ? POP : {}}
      />
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="left_label"
        text={T(page, 'left_label', sc.left_label || L.left.labelFallback)}
        cx={L.left.cx}
        cy={L.left.labelY + L.left.font / 2}
        width={400}
        fontSize={L.left.font}
        weight={700}
        fill={L.left.fill}
        align="center"
        pre={pre ? {opacity: 0} : {}}
      />
      <FTxt
        mode={mode}
        layer="editable"
        page={page}
        role="right_label"
        text={T(page, 'right_label', sc.right_label || L.right.labelFallback)}
        cx={L.right.cx}
        cy={L.right.labelY + L.right.font / 2}
        width={360}
        fontSize={L.right.font}
        weight={700}
        fill={L.right.fill}
        align="center"
        pre={pre ? {opacity: 0} : {}}
      />
    </>
  );
}

function SimplePhotoPage({
  sc,
  mode,
  spec,
  role,
}: {
  sc: Scene;
  mode: FilmMode;
  spec: {asset: string; cx: number; cy: number; h: number};
  role: string;
}) {
  return (
    <FImg
      mode={mode}
      layer="editable"
      page={sc.id}
      role={role}
      asset={spec.asset}
      cx={spec.cx}
      cy={spec.cy}
      h={spec.h}
      pre={mode === 'film' ? CHAIN : {}}
    />
  );
}

export function FilmPage({sc, mode}: {sc: Scene; mode: FilmMode}) {
  const {kind} = layoutFor(sc.id);
  return (
    <>
      <SilkFolds />
      {kind === 'cover' && <CoverPage sc={sc} mode={mode} />}
      {kind === 's01' && <S01Page sc={sc} mode={mode} />}
      {kind === 's02' && (
        <SimplePhotoPage sc={sc} mode={mode} spec={{asset: S02.photo.asset, cx: S02.photo.cx, cy: S02.photo.cy, h: S02.photo.h}} role="photo" />
      )}
      {kind === 's03' &&
        S03.items.map((it, i) => (
          <FImg
            mode={mode}
            layer="editable"
            page={sc.id}
            role={['vine', 'pack_a', 'pack_b', 'pack_bottle'][i]}
            asset={it.asset}
            cx={it.cx}
            cy={it.cy}
            h={it.h}
            pre={mode === 'film' ? POP : {}}
          />
        ))}
      {kind === 's04' && (
        <ChainPage sc={sc} mode={mode} spec={S04} roles={['tomato', 'arrow', 'prostate']} />
      )}
      {kind === 's05' && (
        <ChainPage
          sc={sc}
          mode={mode}
          spec={S05}
          roles={['tomato', 'arrow1', 'o2', 'arrow2', 'woman']}
          redX={{asset: S05.redX.asset, h: S05.redX.h, rot: S05.redX.rot, atIndex: 2, role: 'mark_x'}}
        />
      )}
      {kind === 's06' && (
        <ChainPage sc={sc} mode={mode} spec={S06} roles={['tomato', 'arrow1', 'nk', 'arrow2', 'arm']} />
      )}
      {kind === 's07' && <S07Page sc={sc} mode={mode} />}
      {kind === 's08' && <S08Page sc={sc} mode={mode} />}
      {kind === 's09' && <S09Page sc={sc} mode={mode} />}
      {kind === 's10' && <S10Page sc={sc} mode={mode} />}
      {kind === 's11' && <S11Page sc={sc} mode={mode} />}
      {kind === 'related' && <RelatedPage sc={sc} mode={mode} />}
    </>
  );
}
