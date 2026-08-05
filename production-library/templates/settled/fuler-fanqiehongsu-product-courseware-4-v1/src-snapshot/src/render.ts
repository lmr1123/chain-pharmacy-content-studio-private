/**
 * Headless video render via Revideo.
 * Prefer PIL export for signed still fidelity; this path is for editor/export chain.
 */
import {mkdirSync, copyFileSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

async function render() {
  const outDir = resolve(process.cwd(), 'out');
  mkdirSync(outDir, {recursive: true});
  const outFile = '商品培训课件4_Revideo编辑器导出_v1.mp4';

  const file = await renderVideo({
    projectFile: './src/project.tsx',
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

  // If export dir env set (editor pipeline), copy there
  const exportDir = process.env.CW4_EXPORT_DIR;
  if (exportDir && existsSync(file)) {
    const target = resolve(exportDir, '商品培训课件4_当前作品.mp4');
    copyFileSync(file, target);
    console.log('copied to', target);
  }
}

render().catch(err => {
  console.error(err);
  process.exit(1);
});
