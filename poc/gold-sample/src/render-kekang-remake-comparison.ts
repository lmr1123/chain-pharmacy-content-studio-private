import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {renderVideo} from '@revideo/renderer';

async function renderOne(projectFile: string, outFile: string) {
  const outDir = resolve(process.cwd(), '../../production-library/validation/courseware');
  mkdirSync(outDir, {recursive: true});
  return renderVideo({
    projectFile,
    settings: {
      outDir,
      outFile: outFile as `${string}.mp4`,
      workers: 1,
      logProgress: true,
      ffmpeg: {ffmpegPath: 'ffmpeg', ffmpegLogLevel: 'error'},
    },
  });
}

async function main() {
  const base = '../reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/remake-comparison-v1';
  const jobs = {
    k03: ['./src/kekang-k03-remake-project.tsx', `${base}/k03-after.mp4`],
    k13: ['./src/kekang-k13-remake-project.tsx', `${base}/k13-after.mp4`],
    k16: ['./src/kekang-k16-relation-project.tsx', `${base}/k16-after.mp4`],
  } as const;
  const selected = process.argv[2];
  const entries = selected
    ? Object.entries(jobs).filter(([key]) => key === selected)
    : Object.entries(jobs);
  if (entries.length === 0) throw new Error(`Unknown segment: ${selected}`);
  for (const [, [projectFile, outFile]] of entries) {
    console.log(await renderOne(projectFile, outFile));
  }
}

main();
