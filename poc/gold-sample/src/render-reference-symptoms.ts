import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(process.cwd(), '../../production-library/validation/video');
  mkdirSync(outDir, {recursive: true});

  const requestedOut = process.env.PHARMACY_RENDER_OUT;
  const outFile = (
    requestedOut?.endsWith('.mp4')
      ? requestedOut
      : 'reference-typical-symptoms-replica.mp4'
  ) as `${string}.mp4`;

  const file = await renderVideo({
    projectFile: './src/reference-symptoms-project.tsx',
    settings: {
      outDir,
      outFile,
      workers: 1,
      logProgress: true,
      ffmpeg: {
        ffmpegPath: 'ffmpeg',
        ffmpegLogLevel: 'error',
      },
    },
  });

  console.log(`Rendered video to ${file}`);
}

render();
