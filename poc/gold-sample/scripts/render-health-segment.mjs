#!/usr/bin/env node
/**
 * Render one health-training (风热金样) segment from the current working directory.
 *
 * Usage:
 *   node scripts/render-health-segment.mjs intro out/intro.mp4
 */
import {mkdirSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {renderVideo} from '@revideo/renderer';

const SEGMENT_PROJECT = {
  intro: './src/reference-native-intro-project.tsx',
  character: './src/reference-replica-project.tsx',
  mechanism: './src/reference-mechanism-gap-project.tsx',
  symptoms: './src/reference-symptoms-project.tsx',
  treatment: './src/reference-treatment-project.tsx',
  medication: './src/reference-medication-advice-project.tsx',
  summary: './src/reference-summary-outro-project.tsx',
};

const segment = process.argv[2];
const outFileArg = process.argv[3];
if (!segment || !SEGMENT_PROJECT[segment]) {
  console.error(
    `Usage: node scripts/render-health-segment.mjs <${Object.keys(SEGMENT_PROJECT).join('|')}> <out.mp4>`,
  );
  process.exit(1);
}

const outPath = resolve(outFileArg || `out/health-${segment}.mp4`);
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
