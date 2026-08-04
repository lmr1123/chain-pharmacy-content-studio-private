/**
 * 共享动效原语与视觉常量（editor 工程与 film 工程单源）。
 *
 * 动效语法红线（用户「整屏在抖」反馈锁定）：
 * - 入场单次弹出后冻结（easeOutBack / easeOutCubic）
 * - 强调循环仅限：表头白箭头 bounce、链路红箭头 X 脉冲、S01 黄绿 »
 * - 主视觉（番茄/器官/杂志/卡片/O2/NK/手臂）禁 idle/呼吸/乱转
 * - 禁多元素同相位大振幅
 */
import {all, easeOutBack, easeOutCubic, loop, waitFor} from '@revideo/core';

import {K} from '../content';

export const FONT =
  'HarmonyOS Sans SC, Source Han Sans SC, PingFang SC, Microsoft YaHei, sans-serif';
export const SILK = '#cecbc4';
export const INK = '#1a1a1a';
/** 底栏讲解字幕：对标参考近黑字（禁止白字） */
export const CAPTION = '#111111';
export const RED = '#c43c2c';
export const RED_OUTLINE = '#ba3034';
export const WHITE = '#ffffff';
export const YELLOW = '#ffe33c';
export const BROWN = '#a05040';
export const LABEL = '#9a3c2e';
export const BODY = '#8a3a28';
export const LIME = '#e9f200';
export const MUTED = '#555555';

/** 8 向描边偏移（黄字红边 / 黑字白边） */
export const OUTLINE_8: [number, number][] = [
  [-1, -1],
  [1, -1],
  [-1, 1],
  [1, 1],
  [0, -1],
  [0, 1],
  [-1, 0],
  [1, 0],
];

/** PIL top-left (x,y,w,h) → Revideo center position */
export function box(x: number, y: number, w: number, h: number) {
  return {
    position: [x + w / 2 - 960, y + h / 2 - 540] as [number, number],
    width: w,
    height: h,
  };
}

/** Revideo node by editable key（动效用） */
export function nodeOf(view: any, page: string, role: string) {
  return view.findKey(K(page, role));
}

export function* popIn(node: any, dur = 0.36) {
  if (!node) return;
  yield* all(
    node.opacity(1, Math.min(0.14, dur * 0.4), easeOutCubic),
    node.scale(1, dur, easeOutBack),
  );
}

/** 红箭头：沿指向方向（+x）脉冲，对齐培训金样「强调循环」 */
export function* pulseArrowX(node: any, baseX: number, seconds: number, amp = 14) {
  if (!node || seconds <= 0.05) return;
  const period = 0.58;
  const n = Math.max(1, Math.floor(seconds / period));
  yield* loop(n, function* () {
    yield* node.position.x(baseX + amp, period * 0.48, easeOutCubic);
    yield* node.position.x(baseX, period * 0.52, easeOutCubic);
  });
  const left = seconds - n * period;
  if (left > 0.02) yield* waitFor(left);
}

/** @deprecated 主视觉呼吸违反动效红线，S06 手臂已停用；仅保留兼容旧编排 */
export function* softPulseScale(node: any, seconds: number, amount = 0.04) {
  if (!node || seconds <= 0.05) return;
  const period = 0.9;
  const n = Math.max(1, Math.floor(seconds / period));
  yield* loop(n, function* () {
    yield* node.scale(1 + amount, period * 0.5, easeOutCubic);
    yield* node.scale(1, period * 0.5, easeOutCubic);
  });
  const left = seconds - n * period;
  if (left > 0.02) yield* waitFor(left);
}

/** 单次确认 pulse（消死区用，1→1+amount→1，只跑一次） */
export function* oncePulse(node: any, amount = 0.06, dur = 0.5) {
  if (!node) return;
  yield* node.scale(1 + amount, dur * 0.45, easeOutCubic);
  yield* node.scale(1, dur * 0.55, easeOutCubic);
}

/** 页内本地时钟：spend 消耗秒数 / remain 返回页内剩余 */
export function makeClock(dur: number) {
  let t = 0;
  const spend = function* (sec: number) {
    const s = Math.max(0, sec);
    if (s > 0.001) yield* waitFor(s);
    t += s;
  };
  const remain = () => Math.max(0.05, dur - t);
  const elapsed = () => t;
  return {spend, remain, elapsed};
}
