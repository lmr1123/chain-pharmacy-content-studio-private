import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

import {renderVideo} from '@revideo/renderer';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, '..');
const snapshotFile = path.resolve(process.argv[2] ?? '');

if (!process.argv[2] || !fs.existsSync(snapshotFile)) {
  throw new Error('Missing current-project snapshot.');
}

const exportDir = path.dirname(snapshotFile);
const snapshot = JSON.parse(fs.readFileSync(snapshotFile, 'utf8'));
const workRoot = path.resolve(projectRoot, '.export-video-work');
const workDir = path.resolve(
  workRoot,
  snapshot.export_id ?? 'current-project',
);
const outputName = '风热证_当前作品.mp4';
const outputFile = path.resolve(exportDir, outputName);
const requestedRange = process.env.WIND_HEAT_EXPORT_TEST_RANGE
  ?.split(',')
  .map(value => Number(value.trim()));
const renderRange =
  requestedRange?.length === 2 &&
  requestedRange.every(Number.isFinite)
    ? [requestedRange[0] / 30, requestedRange[1] / 30]
    : [0, 5435 / 30];

const patches = Object.fromEntries(
  Object.entries(snapshot.patches ?? {}).map(([key, patch]) => {
    if (typeof patch.src !== 'string' || !patch.src.startsWith('assets/')) {
      return [key, patch];
    }
    return [
      key,
      {
        ...patch,
        src: `/@fs/${path.resolve(exportDir, patch.src)}`,
      },
    ];
  }),
);

fs.mkdirSync(workRoot, {recursive: true});
const workPublic = path.resolve(workRoot, 'public');
if (!fs.existsSync(workPublic)) {
  fs.symlinkSync(path.resolve(projectRoot, 'public'), workPublic, 'dir');
}
fs.mkdirSync(workDir, {recursive: true});

try {
  const renderedFile = await renderVideo({
    projectFile: './src/wind-heat-editable-project.tsx',
    variables: {editablePatches: patches},
    settings: {
      outDir: workDir,
      outFile: outputName,
      workers: 1,
      logProgress: true,
      viteBasePort: 9400,
      viteConfig: {
        server: {
          fs: {allow: [projectRoot, exportDir]},
        },
      },
      projectSettings: {
        range: renderRange,
      },
      ffmpeg: {
        ffmpegPath: '/opt/homebrew/bin/ffmpeg',
        ffprobePath: '/opt/homebrew/bin/ffprobe',
        ffmpegLogLevel: 'error',
      },
    },
  });

  if (path.resolve(renderedFile) !== outputFile) {
    fs.renameSync(renderedFile, outputFile);
  }
  console.log(JSON.stringify({ok: true, output: outputName}));
} finally {
  fs.rmSync(workDir, {recursive: true, force: true});
}
