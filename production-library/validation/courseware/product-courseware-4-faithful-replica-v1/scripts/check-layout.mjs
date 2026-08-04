#!/usr/bin/env node
/**
 * render:film 前置版式检查：安全区 / 字号下限 / 页面覆盖。
 * 数据经 npx tsx 从 src/layout.ts + src/content.ts  dump（TS 单一来源，mjs 只做判定）。
 *
 * 判定级别：
 * - FAIL：font 字段 < 28（1080p 字号下限，计划硬性约束）；页面缺版式
 * - WARN：坐标超出画布 +40px 出血带（装饰件允许出血，只提示不阻断）
 * 重叠检测不做静态判定（元素盒高度依赖字体度量），由 qa/pair 三帧签样覆盖。
 */
import {spawnSync} from 'node:child_process';

const DUMP = `
import {scenes} from './src/content';
import {layoutFor, chainLayout} from './src/layout';
const out: Record<string, unknown> = {};
for (const sc of scenes()) out[sc.id] = layoutFor(sc.id);
console.log(JSON.stringify({pages: out, chainLayout}));
`;

const dump = spawnSync('npx', ['tsx', '-e', DUMP], {
  encoding: 'utf8',
  cwd: process.cwd(),
});
if (dump.status !== 0) {
  console.error('layout dump 失败：\n' + dump.stderr);
  process.exit(1);
}
const {pages, chainLayout} = JSON.parse(dump.stdout);

const W = 1920;
const H = 1080;
const BLEED = 40;
const FONT_MIN = 28;
const COORD_KEYS = new Set(['x', 'cx', 'x0', 'x1', 'y', 'cy', 'y0', 'y1']);

let fails = 0;
let warns = 0;

function walk(node, path) {
  if (Array.isArray(node)) {
    node.forEach((v, i) => walk(v, `${path}[${i}]`));
    return;
  }
  if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) walk(v, path ? `${path}.${k}` : k);
    return;
  }
  if (typeof node !== 'number' || !path) return;
  const key = path.split('.').pop();
  if (key === 'font' && node < FONT_MIN) {
    console.error(`FAIL ${path} = ${node} < 字号下限 ${FONT_MIN}`);
    fails++;
  }
  if (COORD_KEYS.has(key)) {
    const isX = key.includes('x');
    const [lo, hi] = isX ? [-BLEED, W + BLEED] : [-BLEED, H + BLEED];
    if (node < lo || node > hi) {
      console.warn(`WARN ${path} = ${node} 超出 ${isX ? '横向' : '纵向'}出血带 [${lo}, ${hi}]`);
      warns++;
    }
  }
}

const ids = Object.keys(pages);
for (const [id, entry] of Object.entries(pages)) {
  if (!entry || !entry.kind || !entry.spec) {
    console.error(`FAIL ${id} 缺版式（layoutFor 返回 ${JSON.stringify(entry)}）`);
    fails++;
    continue;
  }
  walk(entry.spec, id);
}
walk(chainLayout, 'chainLayout');

console.log(
  `check-layout: ${ids.length} 页 + chainLayout，${fails} FAIL / ${warns} WARN`,
);
process.exit(fails ? 1 : 0);
