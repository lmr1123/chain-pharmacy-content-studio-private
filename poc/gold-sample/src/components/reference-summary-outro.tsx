import {Circle, Img, Line, Rect, Txt} from '@revideo/2d';
import {Reference, all, easeOutCubic, waitFor} from '@revideo/core';

export type SummaryItem = {
  title: string;
  body: string;
};

export type SummaryMatrixRefs = {
  panel: Reference<Rect>;
  labelsLayer: Reference<Rect>;
  bodiesLayer: Reference<Rect>;
};

export function SummaryMatrix({
  refs,
  items,
  fontFamily,
  layout = '2x2',
  layerPrefix = 'editable:summary:matrix',
}: {
  refs: SummaryMatrixRefs;
  items: SummaryItem[];
  fontFamily: string;
  layout?: '2x2' | '1x4';
  layerPrefix?: string;
}) {
  const panelWidth = 1390;
  const panelHeight = 620;
  const columns = layout === '2x2' ? 2 : 4;
  const rows = layout === '2x2' ? 2 : 1;
  const cellWidth = panelWidth / columns;
  const cellHeight = panelHeight / rows;

  return (
    <Rect
      key={`${layerPrefix}:root`}
      ref={refs.panel}
      position={[0, 45]}
      size={[panelWidth, panelHeight]}
      fill={'rgba(18,38,55,0.97)'}
      stroke={'#199ba5'}
      lineWidth={5}
      opacity={0}
      scale={0.94}
      shadowColor={'rgba(35,226,230,0.22)'}
      shadowBlur={24}
    >
      <Rect
        size={[panelWidth - 22, panelHeight - 22]}
        stroke={'rgba(54,224,229,0.28)'}
        lineWidth={2}
      />
      <Rect position={[-panelWidth / 2 + 14, 0]} size={[28, 270]} fill={'#1bb3ba'} />
      <Rect position={[panelWidth / 2 - 14, 0]} size={[28, 270]} fill={'#1bb3ba'} />
      <Rect position={[0, -panelHeight / 2 + 15]} size={[360, 30]} fill={'#159ba5'} />
      <Rect position={[0, panelHeight / 2 - 15]} size={[150, 30]} fill={'#159ba5'} />
      {columns > 1 &&
        Array.from({length: columns - 1}, (_, index) => (
          <Rect
            position={[
              -panelWidth / 2 + cellWidth * (index + 1),
              0,
            ]}
            size={[2, panelHeight - 80]}
            fill={'rgba(75,132,153,0.45)'}
          />
        ))}
      {rows > 1 &&
        Array.from({length: rows - 1}, (_, index) => (
          <Rect
            position={[
              0,
              -panelHeight / 2 + cellHeight * (index + 1),
            ]}
            size={[panelWidth - 120, 2]}
            fill={'rgba(75,132,153,0.45)'}
          />
        ))}
      <Rect ref={refs.labelsLayer} size={[panelWidth, panelHeight]} opacity={0}>
        {items.map((item, index) => {
          const column = index % columns;
          const row = Math.floor(index / columns);
          const x = -panelWidth / 2 + cellWidth * (column + 0.5);
          const y = -panelHeight / 2 + cellHeight * (row + 0.5);
          return (
            <Rect
              key={`${layerPrefix}:item:${index}:label`}
              position={[x, y - cellHeight * 0.27]}
              size={[260, 68]}
              radius={11}
              fill={'#238f98'}
            >
              <Txt
                key={`${layerPrefix}:item:${index}:title`}
                text={item.title}
                fontFamily={fontFamily}
                fontSize={46}
                fontWeight={650}
                fill={'#f7faf8'}
              />
            </Rect>
          );
        })}
      </Rect>
      <Rect ref={refs.bodiesLayer} size={[panelWidth, panelHeight]}>
        {items.map((item, index) => {
        const column = index % columns;
        const row = Math.floor(index / columns);
        const x = -panelWidth / 2 + cellWidth * (column + 0.5);
        const y = -panelHeight / 2 + cellHeight * (row + 0.5);
        return (
          <Txt
            key={`${layerPrefix}:item:${index}:body`}
            position={[x, y + cellHeight * 0.12]}
            width={cellWidth - 135}
            text={item.body}
            textAlign={'left'}
            textWrap
            lineHeight={57}
            fontFamily={fontFamily}
            fontSize={35}
            fontWeight={550}
            fill={'#2ee5e8'}
          />
        );
      })}
      </Rect>
      <Line
        position={[-585, 265]}
        points={[[0, 0], [42, 36], [92, 36]]}
        stroke={'#25bac2'}
        lineWidth={5}
      />
      <Circle position={[620, 250]} size={12} stroke={'#25bac2'} lineWidth={3} />
      <Line
        position={[595, 250]}
        points={[[0, 0], [-85, 0], [-85, -48]]}
        stroke={'#25bac2'}
        lineWidth={3}
      />
    </Rect>
  );
}

export type SummaryArrowRefs = {
  track: Reference<Line>;
  glow: Reference<Rect>;
};

export function SummaryTopCurrentArrow({
  refs,
}: {
  refs: SummaryArrowRefs;
}) {
  return (
    <>
      <Line
        ref={refs.track}
        position={[555, -285]}
        points={[[0, 0], [118, 0]]}
        stroke={'#159da7'}
        lineWidth={8}
        endArrow
        arrowSize={28}
      />
      <Rect
        ref={refs.glow}
        position={[610, -285]}
        size={[42, 7]}
        radius={4}
        fill={'#d9ffff'}
        shadowColor={'#4feaf3'}
        shadowBlur={24}
        opacity={0.25}
      />
    </>
  );
}

export function* revealSummaryMatrix(refs: SummaryMatrixRefs) {
  yield* all(
    refs.panel().opacity(1, 0.22),
    refs.panel().scale(1, 0.36, easeOutCubic),
  );
  refs.labelsLayer().opacity(1);
  yield* waitFor(0.46);
}

export function* runSummaryTopArrow(
  refs: SummaryArrowRefs,
  duration: number,
) {
  yield* waitFor(0.02);
  let elapsed = 0;
  while (elapsed < duration) {
    refs.glow().position([610, -285]);
    const forward = Math.min(0.68, duration - elapsed);
    yield* all(
      refs.glow().position([675, -285], forward),
      refs.glow().opacity(0.95, forward),
    );
    elapsed += forward;
    if (elapsed >= duration) break;
    const reset = Math.min(0.32, duration - elapsed);
    yield* refs.glow().opacity(0.18, reset);
    elapsed += reset;
  }
}

export type TrainingOutroRefs = {
  root: Reference<Rect>;
  handwriting: Reference<Line>;
  light: Reference<Circle>;
  subtitle: Reference<Txt>;
};

export function TrainingBrandOutro({
  refs,
  fontFamily,
  logoSrc,
}: {
  refs: TrainingOutroRefs;
  fontFamily: string;
  logoSrc?: string;
}) {
  const particles = [
    [-690, -130, 5], [-575, -80, 3], [-455, -160, 4], [-330, -110, 3],
    [390, -125, 4], [515, -75, 3], [640, -145, 5], [735, -100, 3],
  ] as const;
  return (
    <Rect
      key={'editable:summary:outro:root'}
      ref={refs.root}
      size={[1920, 1080]}
      opacity={0}
      fill={'#020b16'}
    >
      <Rect
        size={[1920, 1080]}
        fill={'rgba(3,19,29,0.72)'}
        shadowColor={'rgba(16,89,94,0.35)'}
        shadowBlur={80}
      />
      {particles.map(([x, y, size]) => (
        <Circle
          position={[x, y]}
          size={size}
          fill={'rgba(218,244,246,0.68)'}
          shadowColor={'#d9ffff'}
          shadowBlur={12}
        />
      ))}
      <Line
        position={[0, -20]}
        points={[
          [-960, 0], [-620, 0], [-500, -35], [-430, 120], [-350, -12],
          [-260, -12], [-210, -70], [-165, 55], [-120, 0], [960, 0],
        ]}
        stroke={'rgba(77,122,126,0.18)'}
        lineWidth={6}
      />
      <Rect position={[-760, -360]} size={[160, 160]} rotation={30} stroke={'rgba(47,105,113,0.12)'} lineWidth={3} />
      <Rect position={[760, 330]} size={[150, 150]} rotation={30} stroke={'rgba(47,105,113,0.12)'} lineWidth={3} />
      <Rect
        key={'editable:summary:outro:logo-slot'}
        position={[0, -135]}
        size={[320, 190]}
        radius={24}
        stroke={'rgba(134,184,50,0.72)'}
        lineWidth={3}
      >
        {logoSrc ? (
          <Img
            key={'editable:summary:outro:logo'}
            src={logoSrc}
            size={[280, 150]}
          />
        ) : (
          <Txt
            key={'editable:summary:outro:logo-placeholder'}
            text={'授权品牌 Logo'}
            fontFamily={fontFamily}
            fontSize={34}
            fontWeight={600}
            fill={'rgba(223,246,218,0.78)'}
          />
        )}
      </Rect>
      <Txt
        key={'editable:summary:outro:brand-name'}
        position={[0, 5]}
        text={'连锁药店培训'}
        fontFamily={fontFamily}
        fontSize={43}
        fontWeight={500}
        fill={'#86b832'}
      />
      <Txt
        key={'editable:summary:outro:headline'}
        position={[0, 87]}
        text={'营运培训   专业赋能'}
        fontFamily={fontFamily}
        fontSize={64}
        fontWeight={560}
        letterSpacing={8}
        fill={'#f7faf8'}
      />
      <Line
        ref={refs.handwriting}
        position={[0, 165]}
        points={[
          [-500, 22], [-300, 0], [-85, -12], [0, 2], [-38, 30],
          [95, 8], [320, 3], [520, 15],
        ]}
        stroke={'#f6fbfb'}
        lineWidth={4}
        end={0}
      />
      <Circle
        ref={refs.light}
        position={[-500, 187]}
        size={18}
        fill={'#ffe24b'}
        shadowColor={'#ffd31f'}
        shadowBlur={30}
        opacity={0}
      />
      <Txt
        key={'editable:summary:outro:credit'}
        ref={refs.subtitle}
        position={[0, 295]}
        text={'—  营运中心 - 营运培训部出品  —'}
        fontFamily={fontFamily}
        fontSize={38}
        fontWeight={350}
        letterSpacing={8}
        fill={'rgba(230,239,240,0.72)'}
        opacity={0}
      />
      <Txt
        key={'editable:summary:outro:authorization-note'}
        position={[0, 390]}
        text={'品牌 Logo 槽位｜仅接受公司授权透明原图'}
        fontFamily={fontFamily}
        fontSize={20}
        fill={'rgba(222,232,234,0.42)'}
      />
    </Rect>
  );
}

export function* revealTrainingOutro(
  refs: TrainingOutroRefs,
  duration: number,
) {
  refs.root().opacity(1);
  yield* waitFor(0.18);
  yield* all(
    refs.handwriting().end(1, 1.05, easeOutCubic),
    refs.light().opacity(1, 0.12),
    refs.light().position([520, 187], 1.05, easeOutCubic),
  );
  yield* refs.light().opacity(0.45, 0.2);
  yield* refs.subtitle().opacity(1, 0.42);
  yield* waitFor(Math.max(0, duration - 1.85));
}
