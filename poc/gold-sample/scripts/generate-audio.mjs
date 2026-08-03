import {
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

const root = resolve(import.meta.dirname, '..');
const audioDir = resolve(
  root,
  process.env.PHARMACY_AUDIO_DIR ?? 'audio',
);
const storyboardFile =
  process.env.PHARMACY_STORYBOARD ?? 'storyboard.json';
const storyboard = JSON.parse(
  readFileSync(resolve(root, storyboardFile), 'utf8'),
);

mkdirSync(audioDir, {recursive: true});

const run = (command, args, label) => {
  const result = spawnSync(command, args, {encoding: 'utf8'});
  if (result.status !== 0) {
    throw new Error(`${label}: ${result.stderr || result.stdout}`);
  }
  return result.stdout;
};

const probeDuration = (path) =>
  Number(
    run(
      'ffprobe',
      [
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        path,
      ],
      `ffprobe failed for ${path}`,
    ).trim(),
  );

const splitNarration = (text) =>
  text
    .split(/(?<=[。！？；])/)
    .map((part) => part.trim())
    .filter(Boolean);

const formatTimestamp = (seconds) => {
  const milliseconds = Math.round(seconds * 1000);
  const hours = Math.floor(milliseconds / 3_600_000);
  const minutes = Math.floor((milliseconds % 3_600_000) / 60_000);
  const secs = Math.floor((milliseconds % 60_000) / 1000);
  const ms = milliseconds % 1000;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(
    2,
    '0',
  )}:${String(secs).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
};

const timing = {};

for (const scene of storyboard.scenes) {
  const sceneWorkDir = resolve(audioDir, '.work', scene.id);
  mkdirSync(sceneWorkDir, {recursive: true});

  const mediaPath = resolve(audioDir, `${scene.id}.m4a`);
  const subtitlePath = resolve(audioDir, `${scene.id}.srt`);
  const cues = [];
  const concatLines = [];
  let cursor = 0;

  const parts = splitNarration(scene.narration);
  for (const [index, text] of parts.entries()) {
    const partId = String(index + 1).padStart(2, '0');
    const aiffPath = resolve(sceneWorkDir, `${partId}.aiff`);
    const wavPath = resolve(sceneWorkDir, `${partId}.wav`);

    run(
      'say',
      [
        '-v',
        'Tingting',
        '-r',
        '190',
        '-o',
        aiffPath,
        text,
      ],
      `Local TTS failed for ${scene.id}/${partId}`,
    );
    run(
      'ffmpeg',
      [
        '-y',
        '-i',
        aiffPath,
        '-ar',
        '44100',
        '-ac',
        '1',
        '-c:a',
        'pcm_s16le',
        wavPath,
        '-loglevel',
        'error',
      ],
      `Audio conversion failed for ${scene.id}/${partId}`,
    );

    const duration = probeDuration(wavPath);
    cues.push({start: cursor, end: cursor + duration, text});
    cursor += duration;
    concatLines.push(`file '${wavPath.replaceAll("'", "'\\''")}'`);

    if (index < parts.length - 1) {
      const silencePath = resolve(sceneWorkDir, `${partId}-silence.wav`);
      run(
        'ffmpeg',
        [
          '-y',
          '-f',
          'lavfi',
          '-i',
          'anullsrc=r=44100:cl=mono',
          '-t',
          '0.12',
          '-c:a',
          'pcm_s16le',
          silencePath,
          '-loglevel',
          'error',
        ],
        `Silence generation failed for ${scene.id}/${partId}`,
      );
      concatLines.push(`file '${silencePath.replaceAll("'", "'\\''")}'`);
      cursor += 0.12;
    }
  }

  const concatPath = resolve(sceneWorkDir, 'concat.txt');
  writeFileSync(concatPath, `${concatLines.join('\n')}\n`);
  run(
    'ffmpeg',
    [
      '-y',
      '-f',
      'concat',
      '-safe',
      '0',
      '-i',
      concatPath,
      '-c:a',
      'aac',
      '-b:a',
      '192k',
      mediaPath,
      '-loglevel',
      'error',
    ],
    `Scene audio assembly failed for ${scene.id}`,
  );

  const srt = cues
    .map(
      (cue, index) =>
        `${index + 1}\n${formatTimestamp(cue.start)} --> ${formatTimestamp(
          cue.end,
        )}\n${cue.text}\n`,
    )
    .join('\n');
  writeFileSync(subtitlePath, srt);

  timing[scene.id] = {
    duration: probeDuration(mediaPath),
    cues,
  };

  rmSync(sceneWorkDir, {recursive: true, force: true});
}

writeFileSync(
  resolve(audioDir, 'timing.json'),
  `${JSON.stringify(timing, null, 2)}\n`,
);

const total = Object.values(timing).reduce(
  (sum, scene) => sum + scene.duration,
  0,
);

console.log(`Generated ${storyboard.scenes.length} scenes, ${total.toFixed(2)}s`);
