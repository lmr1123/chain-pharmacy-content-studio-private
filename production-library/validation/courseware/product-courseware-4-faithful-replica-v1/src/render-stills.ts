/**
 * editor-bg 底板渲染：film 工程 mode='editor-bg' → 每页 0.12s 终态视频 → ffmpeg 逐页抽帧
 * → out/scene-stills-editor-bg/ → 显式同步 public/stills-editor-bg/（编辑器实际读取位置）。
 *
 * 底板与成片同一份视觉源（layout.ts + film/pages.tsx），消灭 PIL/Revideo 双份坐标漂移。
 * 用法：npx tsx src/render-stills.ts
 */
import {execFileSync as run} from 'node:child_process';
import {copyFileSync, mkdirSync, readdirSync, rmSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

import './ffmpeg-lavfi-patch';
import {scenes} from './content';

const ENTRY = './src/film/project-editor-bg.tsx';
const OUT_DIR = resolve(process.cwd(), 'out', 'scene-stills-editor-bg');
const PUBLIC_DIR = resolve(process.cwd(), 'public', 'stills-editor-bg');
const PAGE_DUR = 0.12; // 与 film/project.tsx editor-bg 分支一致

async function main() {
  mkdirSync(OUT_DIR, {recursive: true});
  mkdirSync(PUBLIC_DIR, {recursive: true});

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
  list.forEach((sc, i) => {
    const at = (i * PAGE_DUR + PAGE_DUR / 2).toFixed(3);
    const png = resolve(OUT_DIR, `${sc.id}.png`);
    run('ffmpeg', [
      '-y',
      '-ss', at,
      '-i', video,
      '-frames:v', '1',
      png,
    ]);
  });
  console.log(`extracted ${list.length} stills → ${OUT_DIR}`);

  // 显式同步：先清后拷，防止删页后残留旧底板
  for (const f of readdirSync(PUBLIC_DIR)) {
    if (f.endsWith('.png')) rmSync(resolve(PUBLIC_DIR, f));
  }
  for (const sc of list) {
    copyFileSync(
      resolve(OUT_DIR, `${sc.id}.png`),
      resolve(PUBLIC_DIR, `${sc.id}.png`),
    );
  }
  console.log(`synced ${list.length} stills → ${PUBLIC_DIR}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
