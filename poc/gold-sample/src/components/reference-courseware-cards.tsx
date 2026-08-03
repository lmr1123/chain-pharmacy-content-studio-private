import {Img, Rect, Txt} from '@revideo/2d';
import {Reference} from '@revideo/core';
import {RoundedTraceSegment} from './premium-medical-effects';

const WHITE = '#f7faf8';
const PANEL = 'rgba(22, 42, 55, 0.96)';

export type AdviceCardItem = {
  title: string;
  body: string;
  imageSrc: string;
  transparent: boolean;
};

export function ReferenceBottomSubtitle({
  ref,
  fontFamily,
  fontSize = 52,
  layerId = 'editable:shared:subtitle',
}: {
  ref: Reference<Txt>;
  fontFamily: string;
  fontSize?: number;
  layerId?: string;
}) {
  return (
    <Txt
      key={layerId}
      ref={ref}
      position={[0, 435]}
      width={1580}
      textAlign={'center'}
      fontFamily={fontFamily}
      fontSize={fontSize}
      fontWeight={800}
      fill={'#ffffff'}
      stroke={'rgba(0,0,0,0.98)'}
      lineWidth={2}
      shadowColor={'rgba(0,0,0,0.9)'}
      shadowBlur={6}
      opacity={0}
    />
  );
}

export function MedicationCard({
  ref,
  scanRef,
  name,
  imageSrc,
  packageSize,
  fontFamily,
  titleFontSize = 42,
  noteFontSize = 25,
}: {
  ref: Reference<Rect>;
  scanRef: Reference<Rect>;
  name: string;
  imageSrc: string;
  packageSize: [number, number];
  fontFamily: string;
  titleFontSize?: number;
  noteFontSize?: number;
}) {
  const layerPrefix = `editable:medication:card:${name}`;
  return (
    <Rect
      key={`${layerPrefix}:root`}
      ref={ref}
      size={[420, 620]}
      fill={PANEL}
      stroke={'#55adb6'}
      lineWidth={5}
      radius={28}
      shadowColor={'rgba(47,232,234,0.2)'}
      shadowBlur={20}
    >
      <Rect
        size={[402, 602]}
        radius={23}
        stroke={'rgba(95,224,232,0.24)'}
        lineWidth={2}
      />
      <Rect
        position={[0, -270]}
        size={[360, 70]}
        radius={12}
        fill={'#159ca4'}
      >
        <Txt
          key={`${layerPrefix}:title`}
          text={name}
          fontFamily={fontFamily}
          fontSize={titleFontSize}
          fontWeight={680}
          fill={WHITE}
        />
      </Rect>
      <Img
        key={`${layerPrefix}:asset`}
        src={imageSrc}
        position={[0, 15]}
        size={packageSize}
      />
      <Rect
        position={[0, 270]}
        size={[160, 44]}
        radius={22}
        fill={'rgba(255,241,167,0.95)'}
      >
        <Txt
          key={`${layerPrefix}:note`}
          text={'包装示意'}
          fontFamily={fontFamily}
          fontSize={noteFontSize}
          fontWeight={700}
          fill={'#253743'}
        />
      </Rect>
      <RoundedTraceSegment ref={scanRef} />
    </Rect>
  );
}

export function AdviceRow({
  ref,
  scanRef,
  item,
  position = [0, 0],
  width,
  height,
  fontFamily,
  titleFontSize = 42,
  bodyFontSize = 34,
}: {
  ref: Reference<Rect>;
  scanRef: Reference<Rect>;
  item: AdviceCardItem;
  position?: [number, number];
  width: number;
  height: number;
  fontFamily: string;
  titleFontSize?: number;
  bodyFontSize?: number;
}) {
  const layerPrefix = `editable:advice:row:${item.title}`;
  return (
    <Rect
      key={`${layerPrefix}:root`}
      ref={ref}
      position={position}
      size={[width, height]}
      fill={'rgba(18,42,55,0.94)'}
      stroke={'#4daab4'}
      lineWidth={4}
      radius={24}
      shadowColor={'rgba(47,232,234,0.12)'}
      shadowBlur={12}
    >
      <Rect
        size={[width - 18, height - 18]}
        radius={18}
        stroke={'rgba(95,224,232,0.2)'}
        lineWidth={2}
      />
      <Img
        key={`${layerPrefix}:asset`}
        src={item.imageSrc}
        position={[-620, 0]}
        size={item.transparent ? [120, 110] : [116, 116]}
        radius={item.transparent ? 0 : 58}
      />
      <Rect
        position={[-360, 0]}
        size={[300, 82]}
        radius={14}
        fill={'#159ca4'}
      >
        <Txt
          key={`${layerPrefix}:title`}
          text={item.title}
          fontFamily={fontFamily}
          fontSize={titleFontSize}
          fontWeight={680}
          fill={WHITE}
        />
      </Rect>
      <Txt
        key={`${layerPrefix}:body`}
        position={[245, 0]}
        width={850}
        text={item.body}
        textAlign={'left'}
        fontFamily={fontFamily}
        fontSize={bodyFontSize}
        fontWeight={520}
        fill={WHITE}
      />
      <RoundedTraceSegment ref={scanRef} length={170} />
    </Rect>
  );
}
