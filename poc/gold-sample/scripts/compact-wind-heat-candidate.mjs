import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, '..');
const repositoryRoot = path.resolve(projectRoot, '../..');
const validationDir = path.resolve(
  repositoryRoot,
  'production-library/validation/revideo-editability/wind-heat',
);
const assetsDir = path.resolve(validationDir, 'assets');
const currentFile = path.resolve(validationDir, 'current-candidate.json');

const candidate = JSON.parse(fs.readFileSync(currentFile, 'utf8'));
fs.mkdirSync(assetsDir, {recursive: true});

for (const patch of Object.values(candidate.patches ?? {})) {
  if (typeof patch.src !== 'string' || !patch.src.startsWith('data:image/')) {
    continue;
  }
  const match = patch.src.match(/^data:image\/(png|jpeg|webp);base64,(.+)$/);
  if (!match) continue;
  const extension = match[1] === 'jpeg' ? 'jpg' : match[1];
  const contents = Buffer.from(match[2], 'base64');
  const hash = crypto.createHash('sha256').update(contents).digest('hex');
  const filename = `${hash}.${extension}`;
  const assetFile = path.resolve(assetsDir, filename);
  if (!fs.existsSync(assetFile)) fs.writeFileSync(assetFile, contents);
  patch.src = `/__wind_heat_editor/assets/${filename}`;
}

const now = new Date();
candidate.version = now
  .toISOString()
  .replace(/[-:]/g, '')
  .replace(/\..+/, 'Z');
candidate.saved_at = now.toISOString();
candidate.compacted_from = '20260730T135110Z';

const serialized = `${JSON.stringify(candidate, null, 2)}\n`;
fs.writeFileSync(currentFile, serialized);
fs.writeFileSync(
  path.resolve(validationDir, `candidate-${candidate.version}.json`),
  serialized,
);
console.log(candidate.version);
