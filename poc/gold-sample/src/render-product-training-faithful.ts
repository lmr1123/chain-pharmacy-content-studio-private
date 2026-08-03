import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(process.cwd(), '../../production-library/validation/video');
  mkdirSync(outDir, {recursive: true});

  const file = await renderVideo({
    projectFile: './src/product-training-faithful-project.tsx',
    settings: {
      outDir,
      outFile: 'product-training-faithful-replica.mp4',
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
