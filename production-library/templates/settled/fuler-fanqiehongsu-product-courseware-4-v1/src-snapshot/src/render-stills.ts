/**
 * editor-bg 底板渲染：film 工程 mode='editor-bg' → 每页 4 帧终态视频 → ffmpeg 按帧号抽帧
 * → out/scene-stills-editor-bg/{scene_id}.png。
 *
 * public/stills-editor-bg 是指向 out/scene-stills-editor-bg 的软链（2026-08-03 既有约定），
 * 渲出即同步，无需拷贝（曾在此 rm+cp 同目录互踩，勿恢复"显式拷贝"）。
 * 底板与成片同一份视觉源（layout.ts + film/pages.tsx），消灭 PIL/Revideo 双份坐标漂移。
 * 用法：npx tsx src/render-stills.ts
 */
import {execFileSync as run} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

import './ffmpeg-lavfi-patch';
import {scenes} from './content';
import {EDITOR_BG_PAGE_FRAMES} from './film/project';

const ENTRY = './src/film/project-editor-bg.tsx';
const OUT_DIR = resolve(process.cwd(), 'out', 'scene-stills-editor-bg');
const PICK = 2; // 取每页第 3 帧（editor-bg 无转场、入场直置终态，任意帧皆可，避开首帧防初始化抖动）

async function main() {
  mkdirSync(OUT_DIR, {recursive: true});

  const video = await renderVideo({
    projectFile: ENTRY,
    settings: {
      outDir: OUT_DIR,
      outFile: 'editor-bg.mp4',
      workers: 1,
      logProgress: true,
      ffmpeg: {ffmpegPath: 'ffmpeg', ffmpegLogLevel: 'error'},
    },
  });
  console.log(`editor-bg video: ${video}`);

  const list = scenes();
  const expected = list.length * EDITOR_BG_PAGE_FRAMES;
  const probe = run('ffprobe', [
    '-v', 'error',
    '-select_streams', 'v:0',
    '-show_entries', 'stream=nb_frames',
    '-of', 'csv=p=0',
    video,
  ], {encoding: 'utf8'}).trim();
  // revideo 在片尾多吐 1 帧（项目结束帧），允许 expected 或 expected+1
  if (Number(probe) !== expected && Number(probe) !== expected + 1) {
    console.error(`页边界漂移：视频 ${probe} 帧 != ${list.length} 页 × ${EDITOR_BG_PAGE_FRAMES} 帧(+1)`);
    process.exit(1);
  }

  // 单次过片按帧号抽取，输出按场景序编号
  const select = list
    .map((_, i) => `eq(n\\,${i * EDITOR_BG_PAGE_FRAMES + PICK})`)
    .join('+');
  run('ffmpeg', [
    '-y',
    '-i', video,
    '-vf', `select='${select}'`,
    '-vsync', '0',
    resolve(OUT_DIR, 'page-%02d.png'),
  ]);
  list.forEach((sc, i) => {
    const src = resolve(OUT_DIR, `page-${String(i + 1).padStart(2, '0')}.png`);
    run('mv', [src, resolve(OUT_DIR, `${sc.id}.png`)]);
  });
  console.log(`extracted ${list.length} stills → ${OUT_DIR}（public/stills-editor-bg 软链同源）`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
