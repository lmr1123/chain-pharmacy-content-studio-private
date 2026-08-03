import {Line, Rect, Txt} from '@revideo/2d';

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';

export function ReferenceMedicalTechMaster({
  activeChapter = '中医基础知识',
  pageTitle,
  layerPrefix = 'master',
  brandText = '连锁药店 · 营运培训',
  internalNotice = '内部学习资料  请勿外传',
}: {
  activeChapter?: string;
  pageTitle?: string;
  layerPrefix?: string;
  brandText?: string;
  internalNotice?: string;
}) {
  return (
    <Rect
      key={`editable:${layerPrefix}:master:background`}
      size={[1920, 1080]}
      fill={'#020a15'}
    >
      <Rect
        key={`editable:${layerPrefix}:master:frame`}
        size={[1800, 970]}
        fill={'rgba(3, 14, 27, 0.78)'}
        stroke={'rgba(72, 205, 211, 0.48)'}
        lineWidth={2}
        radius={22}
      />
      {Array.from({length: 9}, (_, index) => (
        <Line
          key={`${layerPrefix}:grid-v-${index}`}
          points={[
            [-720 + index * 180, -420],
            [-720 + index * 180, 390],
          ]}
          stroke={'rgba(58, 185, 194, 0.055)'}
          lineWidth={1}
        />
      ))}
      {Array.from({length: 5}, (_, index) => (
        <Line
          key={`${layerPrefix}:grid-h-${index}`}
          points={[
            [-840, -320 + index * 160],
            [840, -320 + index * 160],
          ]}
          stroke={'rgba(58, 185, 194, 0.05)'}
          lineWidth={1}
        />
      ))}
      <Rect
        key={`editable:${layerPrefix}:master:brand`}
        position={[-710, -466]}
        size={[390, 62]}
        radius={8}
        fill={'rgba(31, 111, 126, 0.48)'}
        stroke={'rgba(83, 220, 220, 0.45)'}
        lineWidth={1}
      >
        <Txt
          key={`editable:${layerPrefix}:master:brand-text`}
          text={brandText}
          fontFamily={FONT}
          fontSize={30}
          fontWeight={600}
          fill={'#dffafa'}
        />
      </Rect>
      <Txt
        key={`editable:${layerPrefix}:master:notice`}
        position={[690, -466]}
        text={internalNotice}
        fontFamily={FONT}
        fontSize={25}
        fill={'rgba(225, 246, 246, 0.72)'}
      />
      {pageTitle ? (
        <Txt
          key={`editable:${layerPrefix}:master:page-title`}
          position={[0, -410]}
          text={pageTitle}
          fontFamily={FONT}
          fontSize={64}
          fontWeight={650}
          fill={'#f7faf8'}
        />
      ) : null}
      <Rect
        key={`editable:${layerPrefix}:master:navigation`}
        position={[0, 472]}
        size={[1800, 58]}
        fill={'rgba(4, 20, 34, 0.94)'}
        stroke={'rgba(72, 205, 211, 0.22)'}
        lineWidth={1}
      >
        {['基础认知', '病因机理', '典型症状', '调理建议', '重点总结'].map(
          (label, index) => (
            <Rect
              key={`editable:${layerPrefix}:master:chapter:${index}`}
              position={[-650 + index * 325, 0]}
              size={[260, 44]}
              radius={6}
              fill={
                label === activeChapter
                  ? 'rgba(67, 190, 198, 0.30)'
                  : 'rgba(255,255,255,0.015)'
              }
            >
              <Txt
                key={`editable:${layerPrefix}:master:chapter-text:${index}`}
                text={label}
                fontFamily={FONT}
                fontSize={24}
                fill={
                  label === activeChapter
                    ? '#eaffff'
                    : 'rgba(220,238,240,0.52)'
                }
              />
            </Rect>
          ),
        )}
      </Rect>
      <Line
        points={[
          [-860, -405],
          [-780, -405],
          [-740, -445],
        ]}
        stroke={'#48ccd3'}
        lineWidth={3}
        opacity={0.72}
      />
      <Line
        points={[
          [860, 405],
          [780, 405],
          [740, 445],
        ]}
        stroke={'#48ccd3'}
        lineWidth={3}
        opacity={0.72}
      />
    </Rect>
  );
}
