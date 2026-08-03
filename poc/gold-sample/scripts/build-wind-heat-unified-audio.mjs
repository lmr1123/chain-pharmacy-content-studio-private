import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

const projectRoot = process.cwd();
const repoRoot = resolve(projectRoot, '../..');
const analysisRoot = resolve(
  repoRoot,
  'poc/reference-replica/reference-analysis/audio',
);
const publicRoot = resolve(projectRoot, 'public/wind-heat-audio-v2');
const validationRoot = resolve(
  repoRoot,
  'production-library/validation/revideo-editability/wind-heat-v2/audio',
);
const dataRoot = resolve(projectRoot, 'src/data');
const workRoot = resolve(validationRoot, 'work');
for (const directory of [publicRoot, validationRoot, dataRoot, workRoot]) {
  mkdirSync(directory, {recursive: true});
}

const TEMPO = 1.16;
const CROSSFADE = 0.035;
const scenes = [
  {
    id: 'character',
    sourceDir: 'qwen-clone-segments',
    sourceFile: 'src/reference-replica-project.tsx',
    speechDuration: 28.1,
    sceneDuration: 28.1,
    mapping: 'one-to-one',
  },
  {
    id: 'mechanism',
    sourceDir: 'qwen-clone-mechanism-gap-v1',
    sourceFile: 'src/reference-mechanism-gap-project.tsx',
    oldTiming: 'qwen-cloned-mechanism-gap-v1-timing.json',
    speechDuration: 15.84,
    sceneDuration: 15.84,
    mapping: 'old-blocks',
  },
  {
    id: 'symptoms',
    sourceDir: 'qwen-clone-symptoms-segments',
    sourceFile: 'src/reference-symptoms-project.tsx',
    speechDuration: 27.5,
    sceneDuration: 790 / 30,
    mapping: 'one-to-one',
  },
  {
    id: 'treatment',
    sourceDir: 'qwen-clone-treatment-segments',
    sourceFile: 'src/reference-treatment-project.tsx',
    speechDuration: 41.94,
    sceneDuration: 1258 / 30,
    mapping: 'one-to-one',
  },
  {
    id: 'medication',
    sourceDir: 'qwen-clone-medication-advice-smooth-v2',
    sourceFile: 'src/reference-medication-advice-project.tsx',
    oldTiming: 'qwen-cloned-medication-advice-smooth-v2-timing.json',
    speechDuration: 41.1,
    sceneDuration: 1233 / 30,
    mapping: 'old-blocks',
  },
  {
    id: 'summary',
    sourceDir: 'qwen-clone-summary-outro-v1',
    sourceFile: 'src/reference-summary-outro-project.tsx',
    oldTiming: 'qwen-cloned-summary-outro-v1-timing.json',
    speechDuration: 24.54,
    sceneDuration: 28,
    mapping: 'old-blocks',
  },
];

function run(command, args, capture = false) {
  const result = spawnSync(command, args, {
    encoding: capture ? 'utf8' : undefined,
    stdio: capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
  });
  if (result.status !== 0) {
    throw new Error(
      `${command} failed: ${capture ? result.stderr : result.status}`,
    );
  }
  return capture ? result.stdout : '';
}

function duration(file) {
  return Number(
    run(
      'ffprobe',
      [
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=nw=1:nk=1',
        file,
      ],
      true,
    ).trim(),
  );
}

function parseCues(sourceFile) {
  const source = readFileSync(resolve(projectRoot, sourceFile), 'utf8');
  const cues = [];
  const pattern =
    /\{\s*start:\s*([\d.]+),\s*end:\s*([\d.]+),\s*text:\s*'([^']+)'\s*,?\s*\}/g;
  for (const match of source.matchAll(pattern)) {
    cues.push({
      start: Number(match[1]),
      end: Number(match[2]),
      text: match[3],
    });
  }
  if (!cues.length) throw new Error(`No cues parsed from ${sourceFile}`);
  return cues;
}

function rawFiles(sourceDir) {
  const directory = resolve(analysisRoot, sourceDir);
  const result = run(
    'find',
    [directory, '-maxdepth', '1', '-name', '*-raw.wav', '-print'],
    true,
  )
    .trim()
    .split('\n')
    .filter(Boolean)
    .sort();
  if (!result.length) throw new Error(`No raw blocks in ${directory}`);
  return result;
}

function mapCues(scene, cues, blocks) {
  if (scene.mapping === 'one-to-one') {
    if (cues.length !== blocks.length) {
      throw new Error(
        `${scene.id}: ${cues.length} cues != ${blocks.length} blocks`,
      );
    }
    return cues.map((cue, index) => ({
      ...cue,
      start: blocks[index].start,
      end: blocks[index].end,
    }));
  }

  const old = JSON.parse(
    readFileSync(
      resolve(projectRoot, 'public/reference-audio', scene.oldTiming),
      'utf8',
    ),
  ).blocks;
  if (old.length !== blocks.length) {
    throw new Error(`${scene.id}: old/new semantic block count differs`);
  }
  return cues.map(cue => {
    const midpoint = (cue.start + cue.end) / 2;
    let index = old.findIndex(
      block => midpoint >= block.start && midpoint <= block.end,
    );
    if (index < 0) {
      index = old.reduce(
        (best, block, candidate) =>
          Math.abs(midpoint - (block.start + block.end) / 2) <
          Math.abs(midpoint - (old[best].start + old[best].end) / 2)
            ? candidate
            : best,
        0,
      );
    }
    const oldBlock = old[index];
    const newBlock = blocks[index];
    const scale =
      (newBlock.end - newBlock.start) / (oldBlock.end - oldBlock.start);
    return {
      text: cue.text,
      start: Math.max(
        newBlock.start,
        newBlock.start + (cue.start - oldBlock.start) * scale,
      ),
      end: Math.min(
        newBlock.end,
        newBlock.start + (cue.end - oldBlock.start) * scale,
      ),
    };
  });
}

const timing = {};
for (const scene of scenes) {
  const sources = rawFiles(scene.sourceDir);
  const sceneWork = resolve(workRoot, scene.id);
  mkdirSync(sceneWork, {recursive: true});
  const processed = sources.map((source, index) => {
    const output = resolve(
      sceneWork,
      `${String(index).padStart(2, '0')}-tempo.wav`,
    );
    run('ffmpeg', [
      '-y',
      '-v',
      'error',
      '-i',
      source,
      '-af',
      `silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,areverse,atempo=${TEMPO},afade=t=in:d=0.012,areverse,afade=t=in:d=0.012,areverse`,
      '-ar',
      '24000',
      '-ac',
      '1',
      output,
    ]);
    return output;
  });
  const durations = processed.map(duration);
  const gap =
    (scene.speechDuration -
      durations.reduce((sum, value) => sum + value, 0)) /
    Math.max(1, processed.length - 1);
  if (gap < 0.05) {
    throw new Error(
      `${scene.id}: uniform ${TEMPO}x does not fit; gap=${gap.toFixed(3)}s`,
    );
  }

  const inputs = processed.flatMap(file => ['-i', file]);
  const filters = [];
  processed.forEach((_, index) => {
    const pad = index < processed.length - 1 ? gap + CROSSFADE : 0;
    const output = `b${index}`;
    filters.push(
      `[${index}:a]apad=pad_dur=${pad.toFixed(8)},atrim=duration=${(
        durations[index] + pad
      ).toFixed(8)}[${output}]`,
    );
  });
  let current = 'b0';
  for (let index = 1; index < processed.length; index++) {
    const next = index === processed.length - 1 ? 'joined' : `j${index}`;
    filters.push(
      `[${current}][b${index}]acrossfade=d=${CROSSFADE}:c1=tri:c2=tri[${next}]`,
    );
    current = next;
  }
  filters.push(
    `[${current}]apad,atrim=duration=${scene.sceneDuration},highpass=f=65,lowpass=f=12000,adeclick=w=55:o=75:a=2:t=2,loudnorm=I=-16:LRA=6:TP=-1.5[out]`,
  );
  const output = resolve(publicRoot, `${scene.id}.wav`);
  run('ffmpeg', [
    '-y',
    '-v',
    'error',
    ...inputs,
    '-filter_complex',
    filters.join(';'),
    '-map',
    '[out]',
    '-ar',
    '24000',
    '-ac',
    '1',
    output,
  ]);

  let cursor = 0;
  const blocks = durations.map((blockDuration, index) => {
    const block = {
      index,
      start: cursor,
      end: cursor + blockDuration,
    };
    cursor = block.end + (index < durations.length - 1 ? gap : 0);
    return block;
  });
  const cues = mapCues(scene, parseCues(scene.sourceFile), blocks).map(cue => ({
    ...cue,
    start: Number(cue.start.toFixed(3)),
    end: Number(cue.end.toFixed(3)),
  }));
  timing[scene.id] = {
    audio: `/wind-heat-audio-v2/${scene.id}.wav`,
    tempo: TEMPO,
    crossfadeSeconds: CROSSFADE,
    gapSeconds: Number(gap.toFixed(6)),
    speechDuration: scene.speechDuration,
    sceneDuration: scene.sceneDuration,
    blocks,
    cues,
  };
}

const manifest = {
  projectId: 'health.wind-heat.editable-v2',
  voiceId: 'voice.reference-pharmacist-qwen-v1',
  generatedBy: 'scripts/build-wind-heat-unified-audio.mjs',
  tempo: TEMPO,
  maxTempo: 1.18,
  crossfadeSeconds: CROSSFADE,
  targetLufs: -16,
  truePeakDbfs: -1.5,
  sampleRate: 24000,
  scenes: timing,
};
const serialized = `${JSON.stringify(manifest, null, 2)}\n`;
writeFileSync(resolve(dataRoot, 'wind-heat-audio-v2.json'), serialized);
writeFileSync(resolve(validationRoot, 'timing-manifest.json'), serialized);
console.log('Built unified wind-heat narration for 6 spoken scenes.');
