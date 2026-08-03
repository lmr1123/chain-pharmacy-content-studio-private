import {Img, Rect, Txt} from '@revideo/2d';
import {Reference} from '@revideo/core';

const FONT = 'PingFang SC, Microsoft YaHei, sans-serif';
const CYAN = '#39edf0';

export type WindHeatAssemblyRefs = {
  root: Reference<Rect>;
  wind: Reference<Rect>;
  plus: Reference<Txt>;
  heat: Reference<Rect>;
  body: Reference<Rect>;
  bodyGlow: Reference<Rect>;
  scanLine: Reference<Rect>;
};

export function WindHeatAssembly({
  refs,
  layerPrefix = 'editable:mechanism:assembly',
}: {
  refs: WindHeatAssemblyRefs;
  layerPrefix?: string;
}) {
  return (
    <Rect
      key={`${layerPrefix}:root`}
      ref={refs.root}
      position={[-275, 10]}
      size={[1040, 690]}
    >
      <Rect
        key={`${layerPrefix}:wind`}
        ref={refs.wind}
        position={[-385, -25]}
        opacity={0}
        scale={0.72}
      >
        <Txt
          key={`${layerPrefix}:wind-symbol`}
          text={'≋'}
          fontFamily={FONT}
          fontSize={210}
          fontWeight={700}
          fill={'#65bff5'}
          shadowColor={'rgba(71,197,255,0.75)'}
          shadowBlur={32}
        />
      </Rect>
      <Txt
        key={`${layerPrefix}:plus`}
        ref={refs.plus}
        position={[-205, -24]}
        text={'+'}
        fontFamily={FONT}
        fontSize={112}
        fontWeight={500}
        fill={'#f5fbfa'}
        opacity={0}
      />
      <Rect
        ref={refs.bodyGlow}
        position={[25, 15]}
        size={[400, 690]}
        radius={200}
        fill={'rgba(37,215,226,0.10)'}
        shadowColor={'#2ef0f0'}
        shadowBlur={90}
        opacity={0}
      />
      <Rect
        key={`${layerPrefix}:body`}
        ref={refs.body}
        position={[25, -5]}
        opacity={0}
        scale={0.82}
      >
        <Img
          key={`${layerPrefix}:body-asset`}
          src={'/mechanism-assets/wind-heat-dynamic-v1/full-body.png'}
          size={[455, 750]}
          shadowColor={CYAN}
          shadowBlur={28}
        />
        <Rect
          ref={refs.scanLine}
          position={[0, -300]}
          size={[320, 5]}
          radius={3}
          fill={'rgba(209,255,255,0.92)'}
          shadowColor={'#55ffff'}
          shadowBlur={24}
          opacity={0}
        />
      </Rect>
      <Rect
        key={`${layerPrefix}:heat`}
        ref={refs.heat}
        position={[310, -25]}
        opacity={0}
        scale={0.72}
      >
        <Txt
          key={`${layerPrefix}:heat-symbol`}
          text={'🔥'}
          fontFamily={FONT}
          fontSize={150}
          shadowColor={'rgba(255,118,30,0.78)'}
          shadowBlur={34}
        />
      </Rect>
    </Rect>
  );
}

export type MedicalMechanismSequenceRefs = {
  root: Reference<Rect>;
  lungScene: Reference<Rect>;
  lungImage: Reference<Img>;
  lungGlow: Reference<Rect>;
  smokeLayer: Reference<Rect>;
  mistA: Reference<Img>;
  mistB: Reference<Img>;
  throatScene: Reference<Rect>;
  throatGlow: Reference<Rect>;
  larynxScene: Reference<Rect>;
  larynxGlow: Reference<Rect>;
  airflow: Reference<Rect>;
  surfaceTag: Reference<Rect>;
};

export function MedicalMechanismSequence({
  refs,
  layerPrefix = 'editable:mechanism:sequence',
}: {
  refs: MedicalMechanismSequenceRefs;
  layerPrefix?: string;
}) {
  return (
    <Rect
      key={`${layerPrefix}:root`}
      ref={refs.root}
      position={[320, 60]}
      size={[980, 580]}
      radius={26}
      fill={'rgba(16,34,48,0.94)'}
      stroke={'#4cb9c2'}
      lineWidth={4}
      shadowColor={'rgba(57,237,240,0.22)'}
      shadowBlur={24}
      opacity={0}
    >
      <Rect ref={refs.lungScene} size={[940, 540]} opacity={0}>
        <Rect ref={refs.smokeLayer} size={[900, 506]} opacity={0.88}>
          <Img
            key={`${layerPrefix}:mist-a`}
            ref={refs.mistA}
            src={'/mechanism-assets/wind-heat-dynamic-v1/volumetric-mist-a.png'}
            size={[900, 506]}
            opacity={0.82}
          />
          <Img
            key={`${layerPrefix}:mist-b`}
            ref={refs.mistB}
            src={'/mechanism-assets/wind-heat-dynamic-v1/volumetric-mist-b.png'}
            size={[900, 506]}
            opacity={0.12}
          />
        </Rect>
        <Rect
          ref={refs.lungGlow}
          position={[65, 10]}
          size={[390, 270]}
          radius={135}
          fill={'rgba(255,63,91,0.15)'}
          shadowColor={'#ff4568'}
          shadowBlur={75}
          opacity={0.35}
        />
        <Img
          key={`${layerPrefix}:lung`}
          ref={refs.lungImage}
          src={'/mechanism-assets/wind-heat-dynamic-v1/lung.png'}
          position={[50, 15]}
          size={[820, 585]}
        />
      </Rect>
      <Rect ref={refs.throatScene} size={[940, 540]} opacity={0}>
        <Img
          key={`${layerPrefix}:throat`}
          src={'/mechanism-assets/wind-heat-dynamic-v1/throat-clean.png'}
          position={[40, 45]}
          size={[760, 660]}
        />
        <Rect
          ref={refs.throatGlow}
          position={[43, 2]}
          size={110}
          radius={55}
          fill={'rgba(255,52,75,0.30)'}
          shadowColor={'#ff375f'}
          shadowBlur={45}
          opacity={0.38}
        />
      </Rect>
      <Rect ref={refs.larynxScene} size={[940, 540]} opacity={0}>
        <Img
          key={`${layerPrefix}:larynx`}
          src={'/mechanism-assets/wind-heat-dynamic-v1/larynx-clean.png'}
          position={[35, 25]}
          size={[825, 650]}
        />
        <Rect
          ref={refs.larynxGlow}
          position={[-95, 55]}
          size={145}
          radius={73}
          fill={'rgba(255,55,79,0.26)'}
          shadowColor={'#ff365f'}
          shadowBlur={52}
          opacity={0.38}
        />
        <Rect ref={refs.airflow} position={[-145, -60]} opacity={0}>
          {[
            [0, 0],
            [55, 35],
            [95, 82],
            [112, 140],
            [118, 198],
          ].map(([x, y], index) => (
            <Rect
              position={[x, y]}
              size={12 + index * 2}
              radius={8}
              fill={'#fff1d2'}
              shadowColor={'#ffdc83'}
              shadowBlur={18}
            />
          ))}
        </Rect>
      </Rect>
      <Rect
        ref={refs.surfaceTag}
        position={[-185, -335]}
        size={[280, 82]}
        radius={41}
        fill={'#176b86'}
        stroke={'#70ecf0'}
        lineWidth={3}
        opacity={0}
      >
        <Txt
          key={`${layerPrefix}:surface-tag-text`}
          text={'体表受邪'}
          fontFamily={FONT}
          fontSize={44}
          fontWeight={650}
          fill={'#f5ffff'}
        />
      </Rect>
    </Rect>
  );
}
