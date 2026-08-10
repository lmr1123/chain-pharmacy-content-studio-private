#!/usr/bin/env node
/** Render an existing PPTX to one PNG per slide with the project artifact-tool runtime. */

import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';

const ENGINE_ROOT = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(ENGINE_ROOT, '../../..');
const args = process.argv.slice(2);

function argValue(flag, fallback = '') {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : fallback;
}

function usage() {
  return [
    'Usage:',
    '  node render-pptx.mjs --input <deck.pptx> --output-dir <dir> [--scale 1]',
  ].join('\n');
}

async function importArtifactTool() {
  const candidates = [
    path.join(ENGINE_ROOT, 'node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'),
    path.join(
      REPO,
      'production-library/engines/product-courseware-green-v1/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs',
    ),
    path.join(REPO, 'poc/courseware-export/work/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'),
  ];
  for (const candidate of candidates) {
    try {
      await fs.access(candidate);
      return await import(pathToFileURL(candidate).href);
    } catch {
      // Try the next project runtime location.
    }
  }
  try {
    const require = createRequire(path.join(ENGINE_ROOT, 'package.json'));
    const resolved = require.resolve('@oai/artifact-tool');
    return await import(pathToFileURL(resolved).href);
  } catch (error) {
    throw new Error(
      `Cannot resolve project @oai/artifact-tool. Tried:\n${candidates
        .map((candidate) => `  - ${candidate}`)
        .join('\n')}\n${error.message}`,
    );
  }
}

function slidesFromPresentation(presentation) {
  if (Array.isArray(presentation.slides?.items)) return presentation.slides.items;
  if (
    Number.isInteger(presentation.slides?.count) &&
    typeof presentation.slides.getItem === 'function'
  ) {
    return Array.from(
      {length: presentation.slides.count},
      (_, index) => presentation.slides.getItem(index),
    );
  }
  throw new Error('Could not enumerate imported presentation slides.');
}

async function saveBlob(blob, output) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  if (bytes.byteLength < 100) throw new Error(`Rendered PNG is empty: ${output}`);
  await fs.writeFile(output, bytes);
}

async function main() {
  if (args.includes('--help') || args.includes('-h')) {
    console.log(usage());
    return;
  }
  const inputArg = argValue('--input');
  const outputArg = argValue('--output-dir');
  if (!inputArg || !outputArg) throw new Error(`--input and --output-dir are required\n${usage()}`);

  const input = path.resolve(inputArg);
  const outputDir = path.resolve(outputArg);
  const scale = Number.parseFloat(argValue('--scale', '1'));
  if (!Number.isFinite(scale) || scale <= 0) throw new Error('--scale must be positive');
  await fs.access(input);
  await fs.mkdir(outputDir, {recursive: true});

  for (const entry of await fs.readdir(outputDir)) {
    if (/^slide-\d+\.png$/i.test(entry)) await fs.unlink(path.join(outputDir, entry));
  }

  const {FileBlob, PresentationFile} = await importArtifactTool();
  const presentation = await PresentationFile.importPptx(await FileBlob.load(input));
  const slides = slidesFromPresentation(presentation);
  if (!slides.length) throw new Error('Imported presentation has no slides.');

  const paths = [];
  for (let index = 0; index < slides.length; index += 1) {
    const output = path.join(outputDir, `slide-${index + 1}.png`);
    const preview = await presentation.export({
      slide: slides[index],
      format: 'png',
      scale,
    });
    await saveBlob(preview, output);
    paths.push(output);
  }

  console.log(
    JSON.stringify({
      ok: true,
      backend: 'artifact-tool',
      input,
      outputDir,
      slideCount: slides.length,
      paths,
    }),
  );
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
