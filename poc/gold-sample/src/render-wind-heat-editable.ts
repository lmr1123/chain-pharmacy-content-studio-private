import {mkdirSync, renameSync, rmSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const validationDir = resolve(
    process.cwd(),
    '../../production-library/validation/revideo-editability/wind-heat-v2',
  );
  const renderOutDir = resolve(process.cwd(), '.render-work');
  mkdirSync(validationDir, {recursive: true});
  mkdirSync(renderOutDir, {recursive: true});

  const file = await renderVideo({
    projectFile: './src/wind-heat-editable-project.tsx',
    settings: {
      outDir: renderOutDir,
      outFile: 'wind-heat-full-editable-v2.mp4',
      workers: 1,
      logProgress: true,
      projectSettings: {
        range: [0, 5435 / 30],
      },
      ffmpeg: {
        ffmpegPath: '/opt/homebrew/bin/ffmpeg',
        ffprobePath: '/opt/homebrew/bin/ffprobe',
        ffmpegLogLevel: 'error',
      },
    },
  });

  const destination = resolve(
    validationDir,
    'wind-heat-full-editable-v2.mp4',
  );
  renameSync(file, destination);
  for (const suffix of ['-audio.wav', '-visuals.mp4', '-0.mp4']) {
    rmSync(
      resolve(renderOutDir, `wind-heat-full-editable-v2${suffix}`),
      {force: true},
    );
  }
  rmSync(renderOutDir, {recursive: true, force: true});
  console.log(`Rendered video to ${destination}`);
}

render();
