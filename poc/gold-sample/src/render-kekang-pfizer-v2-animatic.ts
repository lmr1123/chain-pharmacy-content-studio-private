import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(
    process.cwd(),
    '../../production-library/validation/courseware',
  );
  mkdirSync(outDir, {recursive: true});
  mkdirSync(
    resolve(
      process.cwd(),
      '../../production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/renders',
    ),
    {recursive: true},
  );

  const file = await renderVideo({
    projectFile: './src/kekang-pfizer-v2-animatic-project.tsx',
    settings: {
      outDir,
      outFile:
        '../reference-analysis/kekang-pfizer-framework-v1/production-v2/renders/kekang-green-microshot-animatic-v2.mp4',
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
