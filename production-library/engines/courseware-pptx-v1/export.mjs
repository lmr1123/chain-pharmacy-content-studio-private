#!/usr/bin/env node
/**
 * courseware-pptx-v1 — generic editable PPTX engine
 *
 * Flags:
 *   --model   content-model.json
 *   --style   style pack tokens.json
 *   --recipes optional recipes dir or map json (M3; reserved)
 *   --out     output .pptx
 *   --assets  assets root (default: dirname of model)
 *   --prefix  element id prefix (default: editable:cw4)
 *
 * artifact-tool is resolved from repo root absolute path (not relative to this file alone).
 *
 * Usage:
 *   node production-library/engines/courseware-pptx-v1/export.mjs \
 *     --model production-library/validation/courseware/product-courseware-4-faithful-replica-v1/content-model.json \
 *     --style production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json \
 *     --out /tmp/cw-engine-gold.pptx \
 *     --assets production-library/validation/courseware/product-courseware-4-faithful-replica-v1
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {loadStylePack} from './lib/tokens.mjs';
import {createContext} from './lib/context.mjs';
import {loadRecipes, resolveSceneRecipe} from './lib/recipes.mjs';
import {builders, notes} from './scenes/builders.mjs';
import {chromeBg} from './components/chrome_bg.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = __dirname;
/** production-library/engines/courseware-pptx-v1 → repo root = ../../../ */
const REPO = path.resolve(ENGINE_ROOT, '../../..');
const DEFAULT_RECIPES = path.join(
  REPO,
  'production-library/page-types/product-training/recipes',
);

const args = process.argv.slice(2);
function argValue(flag, fallback) {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : fallback;
}
function hasFlag(flag) {
  return args.includes(flag);
}

if (hasFlag('--help') || hasFlag('-h')) {
  console.log(`courseware-pptx-v1 export

Required:
  --model <content-model.json>
  --style <tokens.json>
  --out   <out.pptx>

Optional:
  --assets <dir>     default: dirname(model)
  --recipes <path>   recipes dir (default: page-types/product-training/recipes)
  --prefix <id>      default: editable:cw4
  --snapshot <json>  editor patches snapshot
`);
  process.exit(0);
}

const modelPath = path.resolve(argValue('--model', ''));
const stylePath = path.resolve(
  argValue(
    '--style',
    path.join(REPO, 'production-library/styles/courseware-4-silk-yellow-red-v1/tokens.json'),
  ),
);
const outPath = path.resolve(argValue('--out', path.join(ENGINE_ROOT, 'out', 'export.pptx')));
const assetsRoot = path.resolve(
  argValue('--assets', modelPath ? path.dirname(modelPath) : ENGINE_ROOT),
);
const recipesPath = path.resolve(argValue('--recipes', DEFAULT_RECIPES));
const eidPrefix = argValue('--prefix', 'editable:cw4');
const snapshotPath = argValue('--snapshot', '');

if (!modelPath) {
  console.error('ERROR: --model is required');
  process.exit(2);
}

// ── artifact-tool: absolute resolve from repo root (formal engines first) ──
const ARTIFACT_CANDIDATES = [
  path.join(ENGINE_ROOT, 'node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'),
  path.join(
    REPO,
    'production-library/engines/product-courseware-green-v1/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs',
  ),
  path.join(REPO, 'poc/courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'),
  path.join(
    REPO,
    'production-library/validation/courseware/product-courseware-4-faithful-replica-v1/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs',
  ),
];

async function importArtifactTool() {
  for (const p of ARTIFACT_CANDIDATES) {
    try {
      await fs.access(p);
      return import(pathToFileURL(p).href);
    } catch {
      /* try next */
    }
  }
  // last resort: require from known work dir
  try {
    const require = createRequire(
      path.join(REPO, 'poc/courseware-export/work/package.json'),
    );
    const resolved = require.resolve('@oai/artifact-tool');
    return import(pathToFileURL(resolved).href);
  } catch (e) {
    throw new Error(
      `Cannot resolve @oai/artifact-tool from repo root ${REPO}. Tried:\n` +
        ARTIFACT_CANDIDATES.map((c) => `  - ${c}`).join('\n') +
        `\n${e.message}`,
    );
  }
}

const {Presentation, PresentationFile} = await importArtifactTool();

const model = JSON.parse(await fs.readFile(modelPath, 'utf8'));
const style = await loadStylePack(stylePath);
const patches = snapshotPath
  ? JSON.parse(await fs.readFile(path.resolve(snapshotPath), 'utf8')).patches ?? {}
  : {};

// M3: recipes drive scene.type → page_type → builder impl
const recipeBundle = await loadRecipes(recipesPath);

const ctx = createContext({
  model,
  style,
  assetsRoot,
  repoRoot: REPO,
  patches,
  eidPrefix,
  modelPath,
});
ctx.pathRelative = path.relative.bind(path);
ctx.recipes = recipeBundle;

const presentation = Presentation.create({slideSize: {width: ctx.W, height: ctx.H}});
const scenes = model.scenes || [];
const pageIds = [];
const unknownTypes = [];
const recipeTrace = [];

for (const sc of scenes) {
  const slide = presentation.slides.add();
  const resolved = resolveSceneRecipe(recipeBundle, sc);
  const implName = resolved.impl || sc.type;
  const builder = builders[implName] || builders[sc.type];

  recipeTrace.push({
    id: sc.id,
    scene_type: sc.type || null,
    page_type: resolved.page_type || null,
    impl: implName || null,
    recipe_ok: !!resolved.ok,
    variant: resolved.variant || null,
  });

  if (!builder) {
    unknownTypes.push(sc.type || sc.id);
    chromeBg(ctx, slide);
    ctx.text(slide, ctx.eid(sc.id, 'fallback'), sc.id, ctx.centerBox(0, 0, 800, 80), {
      fontSize: ctx.TS.chapter,
      color: ctx.C.ink,
    });
  } else {
    sc._recipe = resolved;
    await builder(ctx, slide, sc);
  }
  notes(ctx, slide, sc);
  pageIds.push(sc.id);
}

await fs.mkdir(path.dirname(outPath), {recursive: true});
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outPath);

const patchScript = path.join(ENGINE_ROOT, 'patch-pptx-font.py');
const patch = spawnSync('python3', [patchScript, outPath, ctx.font], {encoding: 'utf8'});
if (patch.status !== 0) {
  console.warn('font patch failed:', patch.stderr || patch.stdout);
} else if (patch.stdout) {
  console.log(patch.stdout.trim());
}

const inspect = {
  ok: true,
  engine: 'courseware-pptx-v1',
  out: outPath,
  slides: pageIds.length,
  page_ids: pageIds,
  model: path.relative(REPO, modelPath),
  style: style.id,
  style_path: path.relative(REPO, stylePath),
  assets: path.relative(REPO, assetsRoot),
  recipes_dir: path.relative(REPO, recipesPath),
  recipes_loaded: Object.keys(recipeBundle.recipes).length,
  scene_types_mapped: Object.keys(recipeBundle.byScene).length,
  recipe_trace: recipeTrace,
  patches: Object.keys(patches).length,
  project_id: model.project_id,
  font: ctx.font,
  layout: 'video-design-coords-scaled-1280x720',
  image_fit: 'native-aspect-contain-box',
  element_id_prefix: eidPrefix,
  font_patched: patch.status === 0,
  unknown_types: unknownTypes,
  artifact_tool: 'repo-absolute',
};
const inspectPath = outPath + '.inspect.json';
await fs.writeFile(inspectPath, JSON.stringify(inspect, null, 2) + '\n');
console.log(JSON.stringify(inspect, null, 2));
if (unknownTypes.length) {
  console.warn('WARN unknown scene types (fallback slides):', unknownTypes);
  process.exitCode = 0; // still produced pptx
}
