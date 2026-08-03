/**
 * Independent render entry for other-model-remake-attempt-v1.
 *
 * Revideo resolves audio as: path.join(outDir, '../public', assetSrc)
 * so outDir must be under production-library/validation/courseware
 * (sibling of validation/public which holds kekang-remake-v1 assets).
 *
 * Scene source of truth lives in this attempt directory; gold-sample only
 * provides the thin project bridge + node_modules + public media host.
 *
 *   node src/render.mjs k03
 *   node src/render.mjs k13
 */
import {mkdirSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {renderVideo} from '@revideo/renderer';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ATTEMPT_ROOT = resolve(__dirname, '..');
const REPO = resolve(ATTEMPT_ROOT, '../../../../../../../');
const GOLD_SAMPLE = resolve(REPO, 'poc/gold-sample');
// outDir sibling of validation/public → audio resolve works
const OUT_DIR = resolve(REPO, 'production-library/validation/courseware');
// relative from OUT_DIR to attempt root
const OUT_REL =
  '../reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/other-model-remake-attempt-v1';

const target = (process.argv[2] || 'k03').toLowerCase();

const projects = {
  k03: {
    projectFile: './src/other-model-k03-project.tsx',
    outFile: `${OUT_REL}/k03-remake.mp4`,
  },
  k13: {
    projectFile: './src/other-model-k13-project.tsx',
    outFile: `${OUT_REL}/k13-remake.mp4`,
  },
};

const cfg = projects[target];
if (!cfg) {
  console.error(`Unknown target "${target}". Use k03 or k13.`);
  process.exit(1);
}

mkdirSync(ATTEMPT_ROOT, {recursive: true});
mkdirSync(OUT_DIR, {recursive: true});

// gold-sample cwd so relative projectFile and vite public resolve
process.chdir(GOLD_SAMPLE);

console.log('cwd:', process.cwd());
console.log('project:', cfg.projectFile);
console.log('outDir:', OUT_DIR);
console.log('outFile:', cfg.outFile);

const result = await renderVideo({
  projectFile: cfg.projectFile,
  settings: {
    outDir: OUT_DIR,
    outFile: cfg.outFile,
    workers: 1,
    logProgress: true,
    ffmpeg: {ffmpegPath: 'ffmpeg', ffmpegLogLevel: 'error'},
  },
});

console.log('Rendered:', result);
