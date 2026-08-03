import {mkdirSync, renameSync, rmSync, writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

import {renderVideo} from '@revideo/renderer';

import type {EditableLayerPatches} from './editor/apply-editable-patches';

const proofCases = [
  {scene: 'intro', time: 2.5, key: 'editable:intro:title:main'},
  {
    scene: 'character',
    time: 10,
    key: 'editable:character:symptom-card:0:text',
  },
  {
    scene: 'mechanism',
    time: 33,
    key: 'editable:mechanism:assembly:body-asset',
  },
  {
    scene: 'symptoms',
    time: 50,
    key: 'editable:symptoms:asset:①-0',
  },
  {
    scene: 'treatment',
    time: 104,
    key: 'editable:treatment:recipe:dosage',
  },
  {
    scene: 'medication',
    time: 114,
    key: 'editable:medication:card:银翘解毒颗粒:title',
  },
  {
    scene: 'summary',
    time: 165,
    key: 'editable:summary:matrix:item:0:body',
  },
] as const;

const patches: EditableLayerPatches = {
  'editable:intro:title:main': {
    text: '风热证（可编辑）',
    fill: '#fff2a6',
  },
  'editable:character:symptom-card:0:text': {
    text: '喉咙肿痛 ✓',
    fill: '#fff2a6',
  },
  'editable:mechanism:assembly:body-asset': {
    transform: {x: 42, scale: 0.9, rotation: 3},
  },
  'editable:symptoms:asset:①-0': {
    src: '/production-symptoms/cough.png',
  },
  'editable:treatment:recipe:dosage': {
    text: '各 3—5 克（可改）',
    fill: '#fff2a6',
  },
  'editable:medication:card:银翘解毒颗粒:title': {
    text: '药品名称可替换',
    fontSize: 34,
  },
  'editable:summary:matrix:item:0:body': {
    text: '风 + 热｜内容可编辑',
    fill: '#fff2a6',
  },
};

async function render() {
  const validationDir = resolve(
    process.cwd(),
    '../../production-library/validation/revideo-editability/wind-heat-v2',
  );
  const workDir = resolve(process.cwd(), '.render-proof-work');
  mkdirSync(validationDir, {recursive: true});
  mkdirSync(workDir, {recursive: true});
  const clips: string[] = [];

  for (const [index, proof] of proofCases.entries()) {
    const outFile = `proof-${index}-${proof.scene}.mp4` as `${string}.mp4`;
    const file = await renderVideo({
      projectFile: './src/wind-heat-editable-project.tsx',
      variables: {editablePatches: patches},
      settings: {
        outDir: workDir,
        outFile,
        workers: 1,
        logProgress: false,
        viteBasePort: 9200 + index * 10,
        projectSettings: {
          range: [proof.time, proof.time + 29 / 30],
        },
        ffmpeg: {
          ffmpegPath: '/opt/homebrew/bin/ffmpeg',
          ffprobePath: '/opt/homebrew/bin/ffprobe',
          ffmpegLogLevel: 'error',
        },
      },
    });
    const clip = resolve(workDir, outFile);
    if (file !== clip) renameSync(file, clip);
    clips.push(clip);
  }

  const concat = clips.flatMap(file => ['-i', file]);
  const streams = clips.map((_, index) => `[${index}:v][${index}:a]`).join('');
  const destination = resolve(validationDir, 'editability-proof-7-scenes.mp4');
  const result = spawnSync(
    '/opt/homebrew/bin/ffmpeg',
    [
      '-y',
      ...concat,
      '-filter_complex',
      `${streams}concat=n=${clips.length}:v=1:a=1[v][a]`,
      '-map',
      '[v]',
      '-map',
      '[a]',
      '-c:v',
      'libx264',
      '-crf',
      '18',
      '-pix_fmt',
      'yuv420p',
      '-c:a',
      'aac',
      '-b:a',
      '192k',
      destination,
    ],
    {stdio: 'inherit'},
  );
  if (result.status !== 0) process.exit(result.status ?? 1);

  writeFileSync(
    resolve(validationDir, 'editability-proof-manifest.json'),
    `${JSON.stringify(
      {
        projectId: 'health.wind-heat.editable-v2',
        status: 'rendered',
        cases: proofCases,
        patches,
        output: 'editability-proof-7-scenes.mp4',
        note: 'Validation-only changes; the settled template is not modified.',
      },
      null,
      2,
    )}\n`,
  );
  rmSync(workDir, {recursive: true, force: true});
  console.log(`Rendered editability proof to ${destination}`);
}

render();
