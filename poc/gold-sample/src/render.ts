import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(process.cwd(), '../../production-library/validation/video');
  mkdirSync(outDir, {recursive: true});
  const range = process.env.PHARMACY_RENDER_RANGE
    ?.split(',')
    .map(Number) as [number, number] | undefined;

  const file = await renderVideo({
    projectFile: './src/project.tsx',
    settings: {
      outDir,
      outFile: range
        ? `preview-${range[0]}-${range[1]}.mp4`
        : 'wind-heat-gold-sample.mp4',
      workers: 1,
      logProgress: true,
      projectSettings: range ? {range} : undefined,
      ffmpeg: {
        ffmpegPath: 'ffmpeg',
        ffmpegLogLevel: 'error',
      },
    },
  });

  console.log(`Rendered video to ${file}`);
}

render();
