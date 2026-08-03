#!/usr/bin/env node
/**
 * Render one product-training segment from the current working directory
 * (expects product-training-*.json + src/ + public/ + node_modules).
 *
 * Usage:
 *   node scripts/render-product-segment.mjs opening out/opening.mp4
 */
import {mkdirSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {renderVideo} from '@revideo/renderer';

const SEGMENT_PROJECT = {
  opening: './src/product-training-opening-project.tsx',
  brand: './src/product-training-brand-overview-project.tsx',
  faithful: './src/product-training-faithful-project.tsx',
  efficacy: './src/product-training-efficacy-project.tsx',
  features: './src/product-training-features-project.tsx',
  audience: './src/product-training-audience-project.tsx',
  combination: './src/product-training-combination-project.tsx',
  summary: './src/product-training-summary-project.tsx',
};

const segment = process.argv[2];
const outFileArg = process.argv[3];
if (!segment || !SEGMENT_PROJECT[segment]) {
  console.error(
    `Usage: node scripts/render-product-segment.mjs <${Object.keys(SEGMENT_PROJECT).join('|')}> <out.mp4>`,
  );
  process.exit(1);
}

const outPath = resolve(outFileArg || `out/product-${segment}.mp4`);
const outDir = dirname(outPath);
const outFile = outPath.split('/').pop();
mkdirSync(outDir, {recursive: true});

const ffmpegPath = process.env.FFMPEG_PATH || '/opt/homebrew/bin/ffmpeg';
const ffprobePath = process.env.FFPROBE_PATH || '/opt/homebrew/bin/ffprobe';

const file = await renderVideo({
  projectFile: SEGMENT_PROJECT[segment],
  settings: {
    outDir,
    outFile,
    workers: 1,
    logProgress: true,
    ffmpeg: {
      ffmpegPath,
      ffprobePath,
      ffmpegLogLevel: 'error',
    },
  },
});
console.log(JSON.stringify({ok: true, segment, file, ffmpegPath}));
