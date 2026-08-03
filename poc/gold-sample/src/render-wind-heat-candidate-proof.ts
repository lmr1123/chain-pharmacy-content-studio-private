import {mkdirSync, readFileSync, renameSync, rmSync} from 'node:fs';
import {basename, resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

import type {EditableLayerPatches} from './editor/apply-editable-patches';

type Candidate = {
  version: string;
  patches: EditableLayerPatches;
};

async function render() {
  const validationDir = resolve(
    process.cwd(),
    '../../production-library/validation/revideo-editability/wind-heat',
  );
  const candidatePath = resolve(validationDir, 'current-candidate.json');
  const renderOutDir = resolve(process.cwd(), 'output');
  const candidate = JSON.parse(
    readFileSync(candidatePath, 'utf8'),
  ) as Candidate;

  const patches = Object.fromEntries(
    Object.entries(candidate.patches).map(([key, patch]) => [
      key,
      {
        ...patch,
        src: patch.src?.startsWith('/__wind_heat_editor/assets/')
          ? `/@fs/${resolve(validationDir, 'assets', basename(patch.src))}`
          : patch.src,
      },
    ]),
  );

  mkdirSync(validationDir, {recursive: true});
  mkdirSync(renderOutDir, {recursive: true});

  const outFile =
    `candidate-${candidate.version}-symptoms-proof.mp4` as `${string}.mp4`;
  const file = await renderVideo({
    projectFile: './src/wind-heat-editable-project.tsx',
    variables: {editablePatches: patches},
    settings: {
      outDir: renderOutDir,
      outFile,
      workers: 1,
      logProgress: true,
      viteBasePort: 9100,
      viteConfig: {
        server: {
          fs: {allow: [process.cwd(), validationDir]},
        },
      },
      projectSettings: {
        range: [1490 / 30, 1520 / 30],
      },
      ffmpeg: {
        ffmpegPath: '/opt/homebrew/bin/ffmpeg',
        ffprobePath: '/opt/homebrew/bin/ffprobe',
        ffmpegLogLevel: 'error',
      },
    },
  });

  const destination = resolve(validationDir, outFile);
  renameSync(file, destination);
  const stem = outFile.slice(0, -4);
  for (const suffix of ['-audio.wav', '-visuals.mp4', '-0.mp4']) {
    rmSync(resolve(renderOutDir, `${stem}${suffix}`), {force: true});
  }
  console.log(`Rendered candidate proof to ${destination}`);
}

render();
