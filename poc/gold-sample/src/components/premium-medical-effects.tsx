import {Rect} from '@revideo/2d';
import {Reference, all, createRef} from '@revideo/core';

export type ElectricCurrentRefs = {
  top: Reference<Rect>;
  bottom: Reference<Rect>;
  left: Reference<Rect>;
  right: Reference<Rect>;
};

export function createElectricCurrentRefs(): ElectricCurrentRefs {
  return {
    top: createRef<Rect>(),
    bottom: createRef<Rect>(),
    left: createRef<Rect>(),
    right: createRef<Rect>(),
  };
}

export function ElectricCurrentOverlay({
  refs,
  color = '#d9ffff',
  glow = '#4feaf3',
  layerPrefix = 'editable:motion:electric',
}: {
  refs: ElectricCurrentRefs;
  color?: string;
  glow?: string;
  layerPrefix?: string;
}) {
  return (
    <>
      <Rect
        key={`${layerPrefix}:top`}
        ref={refs.top}
        position={[-700, -505]}
        size={[190, 6]}
        radius={3}
        fill={color}
        shadowColor={glow}
        shadowBlur={30}
        opacity={0.15}
      />
      <Rect
        key={`${layerPrefix}:bottom`}
        ref={refs.bottom}
        position={[700, 505]}
        size={[190, 6]}
        radius={3}
        fill={color}
        shadowColor={glow}
        shadowBlur={30}
        opacity={0.15}
      />
      <Rect
        key={`${layerPrefix}:left`}
        ref={refs.left}
        position={[-905, 350]}
        size={[6, 150]}
        radius={3}
        fill={color}
        shadowColor={glow}
        shadowBlur={30}
        opacity={0.12}
      />
      <Rect
        key={`${layerPrefix}:right`}
        ref={refs.right}
        position={[905, -350]}
        size={[6, 150]}
        radius={3}
        fill={color}
        shadowColor={glow}
        shadowBlur={30}
        opacity={0.12}
      />
    </>
  );
}

export function RoundedTraceSegment({
  ref,
  length = 150,
  color = '#f7ffff',
  glow = '#73f8ff',
}: {
  ref: Reference<Rect>;
  length?: number;
  color?: string;
  glow?: string;
}) {
  return (
    <Rect
      ref={ref}
      size={[length, 8]}
      radius={4}
      fill={color}
      shadowColor={glow}
      shadowBlur={28}
      opacity={0}
    />
  );
}

export function* traceRoundedBorder(
  ref: Reference<Rect>,
  width: number,
  height: number,
  duration: number,
  cycles = 2,
) {
  const edge = duration / (cycles * 4);
  const x = width / 2 - 76;
  const y = height / 2 - 5;
  ref().opacity(1);
  for (let cycle = 0; cycle < cycles; cycle += 1) {
    ref().size([150, 8]);
    ref().position([-x, -y]);
    yield* ref().position([x, -y], edge);
    ref().size([8, 82]);
    ref().position([width / 2 - 5, -height / 2 + 44]);
    yield* ref().position([width / 2 - 5, height / 2 - 44], edge);
    ref().size([150, 8]);
    ref().position([x, y]);
    yield* ref().position([-x, y], edge);
    ref().size([8, 82]);
    ref().position([-width / 2 + 5, height / 2 - 44]);
    yield* ref().position([-width / 2 + 5, -height / 2 + 44], edge);
  }
  ref().opacity(0);
}

export function* runElectricCurrent(
  refs: ElectricCurrentRefs,
  duration: number,
  halfPeriod = 1.2,
) {
  let elapsed = 0;
  while (elapsed < duration) {
    const step = Math.min(halfPeriod, duration - elapsed);
    refs.top().position([-700, -505]);
    refs.bottom().position([700, 505]);
    refs.left().position([-905, 350]);
    refs.right().position([905, -350]);
    yield* all(
      refs.top().position([0, -505], step),
      refs.bottom().position([0, 505], step),
      refs.left().position([-905, 0], step),
      refs.right().position([905, 0], step),
      refs.top().opacity(0.9, step),
      refs.bottom().opacity(0.75, step),
      refs.left().opacity(0.65, step),
      refs.right().opacity(0.65, step),
    );
    elapsed += step;
    if (elapsed >= duration) break;
    const secondStep = Math.min(halfPeriod, duration - elapsed);
    yield* all(
      refs.top().position([700, -505], secondStep),
      refs.bottom().position([-700, 505], secondStep),
      refs.left().position([-905, -350], secondStep),
      refs.right().position([905, 350], secondStep),
      refs.top().opacity(0.15, secondStep),
      refs.bottom().opacity(0.15, secondStep),
      refs.left().opacity(0.12, secondStep),
      refs.right().opacity(0.12, secondStep),
    );
    elapsed += secondStep;
  }
}
