import {mkdirSync, writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

const root = resolve(process.cwd(), '../..');
const analysisAudio = resolve(
  root,
  'poc/reference-replica/reference-analysis/audio',
);
const publicAudio = resolve(process.cwd(), 'public/reference-audio');
const workDir = resolve(analysisAudio, 'semantic-uniform-v2');
mkdirSync(workDir, {recursive: true});

const configs = {
  symptoms: {
    sourceDir: 'qwen-clone-symptoms-segments',
    target: 27.5,
    output: 'qwen-cloned-symptoms-semantic-v2.wav',
    timing: 'qwen-cloned-symptoms-semantic-v2-timing.json',
    tail: 0.35,
    minimumDurations: {
      '一看就懂': 1.3,
      '大便干结': 1.3,
      '基本就是风热证没跑了': 2.6,
    },
    texts: [
      '它有三个典型信号',
      '记好这几点',
      '一看就懂',
      '一、发热、口渴、嘴巴干',
      '心里烦躁',
      '二、喉咙肿痛、咳嗽、痰黄',
      '鼻涕又黄又稠',
      '三、舌头偏红',
      '舌苔微微发黄',
      '大便干结',
      '只要你出现这些情况',
      '基本就是风热证没跑了',
      '对付风热证',
      '记住一个核心',
      '疏风清热',
    ],
  },
  treatment: {
    sourceDir: 'qwen-clone-treatment-segments',
    target: 41.94,
    output: 'qwen-cloned-treatment-semantic-v2.wav',
    timing: 'qwen-cloned-treatment-semantic-v2-timing.json',
    tail: 0,
    forceTempo: 1.18,
    minimumDurations: {'记好了': 0.7, '一、桑叶': 1.5},
    texts: [
      '就是把身体里的风散出去',
      '把热清掉',
      '不舒服的感觉自然就缓解了',
      '日常生活中有这几样',
      '用来调理特别方便',
      '记好了',
      '一、桑叶',
      '能散风热',
      '还能滋润肺部',
      '缓解咳嗽',
      '二、菊花',
      '不仅能散风热',
      '还能清热解毒',
      '平时泡着喝也舒服',
      '三、薄荷',
      '散风热的效果特别快',
      '还能清头目',
      '缓解喉咙痛',
      '平常在家时',
      '用桑叶、菊花、薄荷各三至五克',
      '泡一杯水喝',
      '就是简单又管用的桑菊薄荷饮',
      '喝一至两天',
      '就能感觉到舒服不少',
    ],
  },
};

function run(command, args) {
  const result = spawnSync(command, args, {stdio: 'inherit'});
  if (result.status !== 0) process.exit(result.status ?? 1);
}

function duration(path) {
  const result = spawnSync(
    'ffprobe',
    [
      '-v',
      'error',
      '-show_entries',
      'format=duration',
      '-of',
      'default=nw=1:nk=1',
      path,
    ],
    {encoding: 'utf8'},
  );
  if (result.status !== 0) process.exit(result.status ?? 1);
  return Number(result.stdout.trim());
}

const mode = process.argv[2];
const config = configs[mode];
if (!config) {
  console.error('Usage: node scripts/rebuild-semantic-narration.mjs symptoms|treatment');
  process.exit(2);
}

const sourceDir = resolve(analysisAudio, config.sourceDir);
const modeDir = resolve(workDir, mode);
mkdirSync(modeDir, {recursive: true});
const trimmed = config.texts.map((_, index) => {
  const input = resolve(sourceDir, `${String(index).padStart(2, '0')}-raw.wav`);
  const output = resolve(modeDir, `${String(index).padStart(2, '0')}-trimmed.wav`);
  run('ffmpeg', [
    '-y',
    '-v',
    'error',
    '-i',
    input,
    '-af',
    'silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,areverse,afade=t=in:d=0.012,areverse,afade=t=in:d=0.012,areverse',
    '-ar',
    '24000',
    '-ac',
    '1',
    output,
  ]);
  return output;
});

const minimumGap = 0.05;
const tail = config.tail;
const rawDurations = trimmed.map(duration);
const rawSpeechDuration = rawDurations.reduce((sum, value) => sum + value, 0);
const fastestNeededTempo =
  rawSpeechDuration /
  (config.target - minimumGap * (trimmed.length - 1) - tail);
const uniformTempo =
  config.forceTempo ?? Math.min(1.18, Math.max(1, fastestNeededTempo));
if (fastestNeededTempo > 1.185) {
  throw new Error(
    `${mode} requires ${fastestNeededTempo.toFixed(3)}x, above the 1.18x production gate`,
  );
}
const fittedDurations = rawDurations.map((rawDuration, index) =>
  Math.max(
    rawDuration / uniformTempo,
    config.minimumDurations[config.texts[index]] ?? 0,
  ),
);
const gap =
  (config.target -
    tail -
    fittedDurations.reduce((sum, value) => sum + value, 0)) /
  (trimmed.length - 1);
if (gap < minimumGap - 0.002) {
  throw new Error(
    `${mode} cannot satisfy phrase duration and gap gates (gap=${gap.toFixed(3)}s)`,
  );
}

const inputs = trimmed.flatMap((path) => ['-i', path]);
const filters = [];
const concatInputs = [];
const timing = [];
let cursor = 0;
trimmed.forEach((_, index) => {
  const fittedDuration = fittedDurations[index];
  const cueTempo = rawDurations[index] / fittedDuration;
  filters.push(
    `[${index}:a]atempo=${cueTempo.toFixed(8)},aresample=24000[a${index}]`,
  );
  concatInputs.push(`[a${index}]`);
  timing.push({
    index,
    text: config.texts[index],
    start: Number(cursor.toFixed(3)),
    end: Number((cursor + fittedDuration).toFixed(3)),
  });
  cursor += fittedDuration;
  if (index < trimmed.length - 1) {
    filters.push(
      `anullsrc=channel_layout=mono:sample_rate=24000,atrim=duration=${gap}[g${index}]`,
    );
    concatInputs.push(`[g${index}]`);
    cursor += gap;
  }
});
filters.push(
  `${concatInputs.join('')}concat=n=${concatInputs.length}:v=0:a=1,apad,atrim=duration=${config.target},highpass=f=65,lowpass=f=12000,adeclick=w=55:o=75:a=2:t=2,loudnorm=I=-16:LRA=6:TP=-1.5[out]`,
);

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
  resolve(publicAudio, config.output),
]);

writeFileSync(
  resolve(publicAudio, config.timing),
  `${JSON.stringify(
    {
      duration: config.target,
      uniformTempo,
      maxAllowedTempo: 1.18,
      gapSeconds: gap,
      cues: timing,
      minimumDurations: config.minimumDurations,
    },
    null,
    2,
  )}\n`,
);
console.log(
  `${mode}: uniform tempo ${uniformTempo.toFixed(3)}x, output ${config.output}`,
);
