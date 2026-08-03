import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(
    process.cwd(),
    '../../production-library/validation/courseware',
  );
  mkdirSync(outDir, {recursive: true});

  const file = await renderVideo({
    projectFile: './src/kekang-pfizer-k08-motion-project.tsx',
    settings: {
      outDir,
      outFile:
        '../reference-analysis/kekang-pfizer-framework-v1/animation-k08-v1/kekang-k08-two-ingredients-motion-v1.mp4',
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
