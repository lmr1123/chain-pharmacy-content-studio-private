import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(process.cwd(), 'out');
  mkdirSync(outDir, {recursive: true});

  const file = await renderVideo({
    projectFile: './src/project.tsx',
    settings: {
      outDir,
      outFile: '速福达_商品培训课件3_独立金样_v2.mp4',
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

render().catch(err => {
  console.error(err);
  process.exit(1);
});
