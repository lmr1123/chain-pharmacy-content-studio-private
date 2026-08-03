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
    projectFile: './src/kekang-lingzhi-motion-sample-project.tsx',
    settings: {
      outDir,
      outFile:
        'kekang-lingzhi-video-keyframes-v1/kekang-lingzhi-motion-sample-v1.mp4',
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
