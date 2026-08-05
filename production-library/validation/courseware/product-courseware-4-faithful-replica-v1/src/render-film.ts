/**
 * 权威成片渲染：Revideo film 工程 visuals → ffmpeg 后合旁白 → loudnorm → ffprobe/blackdetect 校验。
 *
 * - 旁白权威轨：web/working-narration.mp3（156.62s，与 scenes[].end 总和一致）
 * - 默认全片入口 ./src/film/project.tsx；CW4_ENTRY 可切签样子集（如 ./src/film/project-preview.tsx）
 * - 全片渲染后硬校验：时长 ±0.1s / 30fps / 1920×1080 / 无黑帧，任一不合格非零退出
 * - 子集入口只出 visuals（不含旁白、不做时长校验），供签样门禁对照用
 *
 * 用法：
 *   npx tsx src/render-film.ts
 *   CW4_ENTRY=./src/film/project-preview.tsx npx tsx src/render-film.ts
 *   CW4_WORKERS=2 npx tsx src/render-film.ts
 */
import {execFileSync, spawnSync} from 'node:child_process';
import {copyFileSync, existsSync, mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

import './ffmpeg-lavfi-patch';
import {scenes, totalDuration} from './content';

const ENTRY = process.env.CW4_ENTRY ?? './src/film/project.tsx';
const FULL = /film\/project\.tsx$/.test(ENTRY);
const OUT_DIR = resolve(process.cwd(), 'out');
const NARRATION = resolve(process.cwd(), 'web/working-narration.mp3');
const WORKERS = Number(process.env.CW4_WORKERS ?? 1);

const VISUALS = FULL
  ? '番茄红素_商品培训课件4_film_v2-visuals.mp4'
  : 'cw4-film-preview-visuals.mp4';
const FINAL = '番茄红素_商品培训课件4_film_v2.mp4';

function ffprobeJson(file: string, entries: string): any {
  const out = execFileSync(
    'ffprobe',
    ['-v', 'error', '-show_entries', entries, '-of', 'json', file],
    {encoding: 'utf8'},
  );
  return JSON.parse(out);
}

function assertFullFilm(file: string, expected: number) {
  const info = ffprobeJson(file, 'format=duration:stream=codec_name,width,height,avg_frame_rate');
  const duration = Number(info.format.duration);
  const v = info.streams.find((s: any) => s.codec_name === 'h264') ?? info.streams[0];
  const [fn, fd] = String(v.avg_frame_rate).split('/').map(Number);
  const fps = fd ? fn / fd : fn;
  const problems: string[] = [];
  if (Math.abs(duration - expected) > 0.1)
    problems.push(`duration ${duration.toFixed(3)}s != ${expected.toFixed(3)}s±0.1`);
  if (Math.round(fps) !== 30) problems.push(`fps ${v.avg_frame_rate} != 30`);
  if (v.width !== 1920 || v.height !== 1080)
    problems.push(`size ${v.width}x${v.height} != 1920x1080`);

  const bd = spawnSync(
    'ffmpeg',
    ['-i', file, '-vf', 'blackdetect=d=0.1:pix_th=0.10', '-an', '-f', 'null', '-'],
    {encoding: 'utf8'},
  );
  const hits = (bd.stderr || '')
    .split('\n')
    .filter((l: string) => l.includes('blackdetect:'));
  if (hits.length) problems.push(`blackdetect hits:\n${hits.join('\n')}`);

  if (problems.length) {
    console.error('成片校验失败：\n' + problems.join('\n'));
    process.exit(1);
  }
  console.log(
    `成片校验通过：${duration.toFixed(3)}s / ${v.avg_frame_rate}fps / ${v.width}x${v.height} / 无黑帧`,
  );
}

async function main() {
  mkdirSync(OUT_DIR, {recursive: true});

  const visuals = await renderVideo({
    projectFile: ENTRY,
    settings: {
      outDir: OUT_DIR,
      outFile: VISUALS,
      workers: WORKERS,
      logProgress: true,
      ffmpeg: {ffmpegPath: 'ffmpeg', ffmpegLogLevel: 'error'},
    },
  });
  console.log(`visuals rendered: ${visuals}`);

  if (!FULL) {
    console.log('子集入口：仅出 visuals（无旁白），供签样对照。');
    return;
  }

  const expected = totalDuration();

  // visuals 时长硬校验：防未记账动画的秒级漂移（v2 基线曾 +1~3s/页被 -t 截断掩盖）。
  // 容差 = 帧量化下限：页时长非 30fps 帧整数倍，revideo 逐页取整，全片累计 ≤ 页数/fps。
  const tol = scenes().length / 30;
  const vdur = Number(
    ffprobeJson(visuals, 'format=duration').format.duration,
  );
  if (Math.abs(vdur - expected) > tol) {
    console.error(
      `visuals 时长 ${vdur.toFixed(3)}s != 旁白轨 ${expected.toFixed(3)}s±${tol.toFixed(2)}：` +
        '页编排有未记账动画（motion.ts 必须经 clk.spend/play 记账），拒绝合成。',
    );
    process.exit(1);
  }
  console.log(`visuals 时长校验通过：${vdur.toFixed(3)}s（帧量化差 ${(vdur - expected).toFixed(3)}s，容差 ±${tol.toFixed(2)}s）`);

  const final = resolve(OUT_DIR, FINAL);
  execFileSync('ffmpeg', [
    '-y',
    '-i', visuals,
    '-i', NARRATION,
    '-c:v', 'copy',
    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-t', expected.toFixed(3),
    final,
  ]);
  console.log(`audio merged (loudnorm -16 LUFS): ${final}`);

  assertFullFilm(final, expected);

  const exportDir = process.env.CW4_EXPORT_DIR;
  if (exportDir && existsSync(final)) {
    const target = resolve(exportDir, '商品培训课件4_当前作品.mp4');
    copyFileSync(final, target);
    console.log('copied to', target);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
