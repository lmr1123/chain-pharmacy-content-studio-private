import {existsSync, readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

const projectRoot = process.cwd();
const repoRoot = resolve(projectRoot, '../..');
const validationRoot = resolve(
  repoRoot,
  'production-library/validation/revideo-editability/wind-heat-v2',
);
mkdirSync(validationRoot, {recursive: true});

function run(command, args, capture = false) {
  const result = spawnSync(command, args, {
    cwd: projectRoot,
    encoding: 'utf8',
    stdio: capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
  });
  return {
    ok: result.status === 0,
    status: result.status,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
  };
}

function probe(file) {
  const result = run(
    'ffprobe',
    [
      '-v',
      'error',
      '-show_entries',
      'format=duration:stream=sample_rate,channels',
      '-of',
      'json',
      file,
    ],
    true,
  );
  if (!result.ok) throw new Error(result.stderr);
  return JSON.parse(result.stdout);
}

function loudness(file) {
  const result = run(
    'ffmpeg',
    [
      '-hide_banner',
      '-nostats',
      '-i',
      file,
      '-af',
      'loudnorm=I=-16:LRA=6:TP=-1.5:print_format=json',
      '-f',
      'null',
      '-',
    ],
    true,
  );
  const match = result.stderr.match(/\{\s*"input_i"[\s\S]*?\}/);
  if (!match) throw new Error(`No loudness JSON for ${file}`);
  return JSON.parse(match[0]);
}

const failures = [];
const checks = [];
const typecheck = run('npm', ['run', 'typecheck'], true);
checks.push({id: 'typecheck', status: typecheck.ok ? 'passed' : 'failed'});
if (!typecheck.ok) failures.push(typecheck.stderr || typecheck.stdout);

const provenance = run(
  'node',
  ['scripts/qa-wind-heat-provenance.mjs'],
  true,
);
checks.push({
  id: 'reference-pixel-provenance',
  status: provenance.ok ? 'passed' : 'failed',
});
if (!provenance.ok) failures.push(provenance.stdout || provenance.stderr);

const audit = JSON.parse(
  readFileSync(resolve(validationRoot, 'element-audit.json'), 'utf8'),
);
const elements = audit.elements ?? audit.items ?? [];
const layerIds = elements.map(item => item.layer_id);
const scenes = new Set(elements.map(item => item.scene_id));
const uniqueLayerIds = new Set(layerIds);
const auditPassed =
  scenes.size === 7 &&
  elements.length >= 60 &&
  layerIds.length === uniqueLayerIds.size;
checks.push({
  id: 'element-audit-schema',
  status: auditPassed ? 'passed' : 'failed',
  sceneCount: scenes.size,
  elementCount: elements.length,
  uniqueLayerIdCount: uniqueLayerIds.size,
});
if (!auditPassed) failures.push('Element audit is incomplete or has duplicate IDs.');

const editableSources = [
  'src/reference-native-intro-project.tsx',
  'src/reference-replica-project.tsx',
  'src/reference-mechanism-gap-project.tsx',
  'src/reference-symptoms-project.tsx',
  'src/reference-treatment-project.tsx',
  'src/reference-medication-advice-project.tsx',
  'src/reference-summary-outro-project.tsx',
  'src/components/reference-courseware-cards.tsx',
  'src/components/reference-mechanism-gap.tsx',
  'src/components/reference-medical-tech-master.tsx',
  'src/components/reference-summary-outro.tsx',
];
const editableCount = editableSources.reduce((sum, file) => {
  const source = readFileSync(resolve(projectRoot, file), 'utf8');
  return sum + (source.match(/editable:/g)?.length ?? 0);
}, 0);
const editorSource = readFileSync(
  resolve(projectRoot, 'src/editor/apply-editable-patches.ts'),
  'utf8',
);
const editorCapabilities = ['text', 'src', 'fontSize', 'fill', 'rotation', 'opacity'];
const missingCapabilities = editorCapabilities.filter(
  capability => !editorSource.includes(capability),
);
const editabilityPassed = editableCount >= 80 && !missingCapabilities.length;
checks.push({
  id: 'editability-contract',
  status: editabilityPassed ? 'passed' : 'failed',
  editableTokenCount: editableCount,
  requiredCapabilities: editorCapabilities,
  missingCapabilities,
});
if (!editabilityPassed) {
  failures.push(
    `Editability coverage insufficient (${editableCount}) or capabilities missing: ${missingCapabilities.join(', ')}`,
  );
}

const mouthRoot = resolve(projectRoot, 'public/wind-heat-presenter-v2');
const mouthFiles = ['closed', 'small', 'o', 'wide'].map(
  state => `mouth-${state}-vector.svg`,
);
const mouthSources = mouthFiles.map(file => ({
  file,
  source: readFileSync(resolve(mouthRoot, file), 'utf8'),
}));
const legacyDarkColors = [
  '#6f3f3b', '#653938', '#6d3a38', '#583a39', '#523536', '#563638',
  '#9b716b', '#a06c68', '#a36f6a', '#a8736e', '#936661', '#91635f', '#8f615d',
];
const legacyDarkHits = mouthSources.flatMap(({file, source}) =>
  legacyDarkColors.filter(color => source.toLowerCase().includes(color)).map(color => ({file, color})),
);
const strokeWidths = mouthSources.flatMap(({source}) =>
  [...source.matchAll(/stroke-width="([\d.]+)"/g)].map(match => Number(match[1])),
);
const mouthManifest = JSON.parse(
  readFileSync(resolve(mouthRoot, 'manifest.json'), 'utf8'),
);
const mouthContactSheet = resolve(validationRoot, 'mouth-soft-palette-contact-sheet.png');
const mouthPalettePassed =
  legacyDarkHits.length === 0 &&
  strokeWidths.every(width => width <= 1.35) &&
  mouthSources[0].source.includes('<path') &&
  mouthManifest.mouth_palette?.version === 'soft-pink-v3' &&
  existsSync(mouthContactSheet);
checks.push({
  id: 'presenter-mouth-palette',
  status: mouthPalettePassed ? 'passed' : 'failed',
  paletteVersion: mouthManifest.mouth_palette?.version,
  states: mouthFiles,
  maxStrokeWidth: Math.max(...strokeWidths),
  legacyDarkHits,
  closedMouthPresent: mouthSources[0].source.includes('<path'),
  contactSheet: 'mouth-soft-palette-contact-sheet.png',
});
if (!mouthPalettePassed) {
  failures.push('Presenter mouth palette or visual QA evidence regressed.');
}

const timing = JSON.parse(
  readFileSync(resolve(projectRoot, 'src/data/wind-heat-audio-v2.json'), 'utf8'),
);
const audioChecks = [];
for (const [sceneId, contract] of Object.entries(timing.scenes)) {
  const file = resolve(projectRoot, 'public', contract.audio.slice(1));
  const metadata = probe(file);
  const analysis = loudness(file);
  const stream = metadata.streams[0];
  const actualDuration = Number(metadata.format.duration);
  const integratedLufs = Number(analysis.input_i);
  const truePeakDbfs = Number(analysis.input_tp);
  const passed =
    Math.abs(actualDuration - contract.sceneDuration) <= 0.03 &&
    Number(stream.sample_rate) === 24000 &&
    stream.channels === 1 &&
    Math.abs(integratedLufs - -16) <= 0.7 &&
    truePeakDbfs <= -1;
  audioChecks.push({
    sceneId,
    passed,
    duration: actualDuration,
    targetDuration: contract.sceneDuration,
    sampleRate: Number(stream.sample_rate),
    channels: stream.channels,
    integratedLufs,
    truePeakDbfs,
    tempo: contract.tempo,
  });
  if (!passed) failures.push(`Audio QA failed for ${sceneId}.`);
}
checks.push({
  id: 'unified-audio',
  status: audioChecks.every(item => item.passed) ? 'passed' : 'failed',
  scenes: audioChecks,
});

const fullVideo = resolve(validationRoot, 'wind-heat-full-editable-v2.mp4');
if (existsSync(fullVideo)) {
  const metadataResult = run(
    'ffprobe',
    [
      '-v',
      'error',
      '-show_streams',
      '-show_format',
      '-of',
      'json',
      fullVideo,
    ],
    true,
  );
  const metadata = JSON.parse(metadataResult.stdout);
  const video = metadata.streams.find(stream => stream.codec_type === 'video');
  const audio = metadata.streams.find(stream => stream.codec_type === 'audio');
  const decode = run('ffmpeg', ['-v', 'error', '-i', fullVideo, '-f', 'null', '-'], true);
  const black = run(
    'ffmpeg',
    [
      '-hide_banner',
      '-nostats',
      '-i',
      fullVideo,
      '-vf',
      'blackdetect=d=0.5:pix_th=0.02',
      '-an',
      '-f',
      'null',
      '-',
    ],
    true,
  );
  const blackSegments = black.stderr.match(/black_start:/g)?.length ?? 0;
  const passed =
    metadataResult.ok &&
    decode.ok &&
    Number(metadata.format.duration) === 181.2 &&
    video?.codec_name === 'h264' &&
    Number(video?.width) === 1920 &&
    Number(video?.height) === 1080 &&
    video?.r_frame_rate === '30/1' &&
    Number(video?.nb_frames) === 5436 &&
    audio?.codec_name === 'aac' &&
    Number(audio?.sample_rate) === 48000 &&
    Number(audio?.channels) === 2 &&
    blackSegments === 0;
  checks.push({
    id: 'full-render',
    status: passed ? 'passed' : 'failed',
    file: 'wind-heat-full-editable-v2.mp4',
    sha256: createHash('sha256').update(readFileSync(fullVideo)).digest('hex'),
    duration: Number(metadata.format.duration),
    resolution: `${video?.width}x${video?.height}`,
    fps: video?.r_frame_rate,
    frames: Number(video?.nb_frames),
    videoCodec: video?.codec_name,
    audioCodec: audio?.codec_name,
    fullDecode: decode.ok,
    sustainedBlackSegments: blackSegments,
  });
  if (!passed) failures.push('Full 181.2 second render QA failed.');
} else {
  checks.push({id: 'full-render', status: 'not-run'});
  failures.push('Full v2 render is missing.');
}

const proofVideo = resolve(validationRoot, 'editability-proof-7-scenes.mp4');
const proofManifest = resolve(validationRoot, 'editability-proof-manifest.json');
if (existsSync(proofVideo) && existsSync(proofManifest)) {
  const proof = JSON.parse(readFileSync(proofManifest, 'utf8'));
  const metadataResult = run(
    'ffprobe',
    ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', proofVideo],
    true,
  );
  const metadata = JSON.parse(metadataResult.stdout);
  const video = metadata.streams.find(stream => stream.codec_type === 'video');
  const passed =
    metadataResult.ok &&
    proof.cases.length === 7 &&
    Number(video?.nb_frames) === 210 &&
    Number(metadata.format.duration) >= 7;
  checks.push({
    id: 'seven-scene-editability-proof',
    status: passed ? 'passed' : 'failed',
    cases: proof.cases,
    frames: Number(video?.nb_frames),
    duration: Number(metadata.format.duration),
    contactSheet: 'editability-proof-contact-sheet.jpg',
  });
  if (!passed) failures.push('Seven-scene editability proof QA failed.');
} else {
  checks.push({id: 'seven-scene-editability-proof', status: 'not-run'});
  failures.push('Seven-scene editability proof is missing.');
}

const report = {
  projectId: 'health.wind-heat.editable-v2',
  templateId: 'template.health-reference-tech-v1',
  stylePackId: 'style-pack.reference-medical-tech-v1',
  checkedAt: new Date().toISOString(),
  status: failures.length ? 'failed' : 'passed',
  checks,
  failures,
};
writeFileSync(
  resolve(validationRoot, 'qa-report-v2.json'),
  `${JSON.stringify(report, null, 2)}\n`,
);
console.log(JSON.stringify(report, null, 2));
process.exit(failures.length ? 1 : 0);
