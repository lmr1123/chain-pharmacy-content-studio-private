/**
 * 大参林商品培训视频共用母版角标（从厂商案例模板剥离品牌）。
 * 一项目只锁本风格包的品牌身份：Logo、内部培训声明、栏目签。
 */
import {Circle, Img, Rect, Txt} from '@revideo/2d';

export const PRODUCT_TRAINING_FONT =
  'PingFang SC, Microsoft YaHei, sans-serif';

/** 大参林课件绿（与 style-pack.dashenlin-courseware-green 对齐，用于角标/声明） */
export const DASHENLIN = {
  primary: '#009900',
  secondary: '#45A817',
  pale: '#C9E7BE',
  notice: '#2d6a2d',
  ink: '#111111',
  white: '#ffffff',
  productBlue: '#43a9e4',
};

const LOGO = '/product-training-brand/dashenlin-logo.png';

/** 右侧竖条：仅供内部培训 */
export function DashenlinInternalNotice(props?: {
  fill?: string;
  position?: [number, number];
}) {
  const fill = props?.fill ?? DASHENLIN.notice;
  const position = props?.position ?? ([937, 0] as [number, number]);
  return (
    <Rect
      position={position}
      size={[55, 950]}
      fill={fill}
      shadowColor={'rgba(20,60,20,0.22)'}
      shadowBlur={8}
    >
      <Txt
        text={'仅\n供\n内\n部\n培\n训\n学\n习\n，\n未\n经\n允\n许\n禁\n止\n对\n外\n使\n用'}
        width={45}
        height={890}
        fontFamily={PRODUCT_TRAINING_FONT}
        fontSize={26}
        fontWeight={650}
        lineHeight={34}
        fill={DASHENLIN.white}
      />
    </Rect>
  );
}

/** 左上：大参林 Logo + 中文名 */
export function DashenlinBrandMark(props?: {
  position?: [number, number];
  showWordmark?: boolean;
}) {
  const position = props?.position ?? ([-790, -438] as [number, number]);
  const showWordmark = props?.showWordmark ?? true;
  return (
    <Rect position={position} size={[showWordmark ? 320 : 200, 100]}>
      <Img
        src={LOGO}
        position={showWordmark ? [-88, 0] : [0, 0]}
        size={[168, 66]}
      />
      {showWordmark ? (
        <Txt
          position={[78, 2]}
          text={'大参林'}
          fontFamily={PRODUCT_TRAINING_FONT}
          fontSize={42}
          fontWeight={900}
          fill={DASHENLIN.primary}
        />
      ) : null}
    </Rect>
  );
}

/** 左上产品栏目签（辅酶Q10 等） */
export function ProductColumnBadge(props: {
  text: string;
  position?: [number, number];
  fill?: string;
}) {
  const position = props.position ?? ([-780, -472] as [number, number]);
  const fill = props.fill ?? DASHENLIN.primary;
  return (
    <Rect
      position={position}
      size={[Math.max(265, props.text.length * 48), 86]}
      radius={25}
      fill={fill}
      shadowColor={'rgba(0,80,0,0.22)'}
      shadowBlur={9}
    >
      <Txt
        text={props.text}
        fontFamily={PRODUCT_TRAINING_FONT}
        fontSize={44}
        fontWeight={800}
        fill={DASHENLIN.white}
      />
    </Rect>
  );
}

/**
 * 品牌总览页头：Logo + 大参林医药集团（替换厂商 CGE/远大/能气朗 多 Logo 行）
 */
export function DashenlinBrandHeader() {
  return (
    <>
      <DashenlinBrandMark position={[-780, -438]} />
      <Rect position={[-280, -438]} size={[360, 98]}>
        <Txt
          position={[0, -14]}
          text={'大参林医药集团'}
          fontFamily={PRODUCT_TRAINING_FONT}
          fontSize={40}
          fontWeight={800}
          fill={DASHENLIN.primary}
        />
        <Txt
          position={[0, 30]}
          text={'DASHENLIN · 内部商品培训'}
          fontFamily={PRODUCT_TRAINING_FONT}
          fontSize={20}
          fontWeight={700}
          fill={'#2f6b2f'}
        />
      </Rect>
      <Rect position={[160, -438]} size={[300, 98]}>
        <Txt
          position={[0, -12]}
          text={'辅酶 Q10'}
          fontFamily={PRODUCT_TRAINING_FONT}
          fontSize={44}
          fontWeight={850}
          fill={'#173b4a'}
        />
        <Txt
          position={[0, 32]}
          text={'商品知识培训'}
          fontFamily={PRODUCT_TRAINING_FONT}
          fontSize={24}
          fontWeight={700}
          fill={'#3d5a66'}
        />
      </Rect>
    </>
  );
}

/** 封底 / 片尾品牌页内容（可嵌在总结段末或独立镜头） */
export function DashenlinOutroPanel(props?: {subtitle?: string}) {
  const subtitle =
    props?.subtitle ?? '辅酶 Q10 商品知识 · 仅供内部培训学习';
  return (
    <Rect size={[1920, 1080]}>
      <Rect size={[1920, 1080]} fill={DASHENLIN.primary} />
      <Circle
        position={[-620, -280]}
        size={720}
        fill={'rgba(255,255,255,0.08)'}
      />
      <Circle
        position={[680, 320]}
        size={640}
        fill={'rgba(255,255,255,0.07)'}
      />
      <Img src={LOGO} position={[0, -120]} size={[420, 165]} />
      <Txt
        position={[0, 80]}
        text={'大参林医药集团'}
        fontFamily={PRODUCT_TRAINING_FONT}
        fontSize={64}
        fontWeight={900}
        fill={DASHENLIN.white}
      />
      <Txt
        position={[0, 170]}
        text={subtitle}
        fontFamily={PRODUCT_TRAINING_FONT}
        fontSize={36}
        fontWeight={650}
        fill={DASHENLIN.pale}
      />
      <Txt
        position={[0, 280]}
        text={'未经允许禁止对外使用'}
        fontFamily={PRODUCT_TRAINING_FONT}
        fontSize={28}
        fontWeight={600}
        fill={'rgba(255,255,255,0.85)'}
      />
    </Rect>
  );
}
