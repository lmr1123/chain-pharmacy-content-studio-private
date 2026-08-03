import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(process.cwd(), '../../production-library/validation/courseware/product-courseware-3-gold-sample-v3');
  mkdirSync(outDir, {recursive: true});
  const file = await renderVideo({
    projectFile: './src/product-courseware-3-next-segments-v6-project.tsx',
    settings: {
      outDir,
      outFile: '商品培训课件3_精细复刻_动画视频继续片段_v6.mp4',
      workers: 1,
      logProgress: true,
      ffmpeg: {ffmpegPath: 'ffmpeg', ffmpegLogLevel: 'error'},
    },
  });
  console.log(`Rendered video to ${file}`);
}

render();
