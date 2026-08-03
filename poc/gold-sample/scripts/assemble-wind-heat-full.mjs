import {mkdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';

const outDir = resolve(process.cwd(), '../../production-library/validation/video');
mkdirSync(outDir, {recursive: true});

const sources = [
  'reference-native-intro.mp4',
  'reference-character-action-replica.mp4',
  'reference-mechanism-gap-replica.mp4',
  'reference-typical-symptoms-replica.mp4',
  'reference-treatment-replica.mp4',
  'reference-medication-advice-replica.mp4',
  'reference-summary-outro-replica.mp4',
];

const inputArgs = sources.flatMap((name) => ['-i', resolve(outDir, name)]);
inputArgs.push(
  '-f',
  'lavfi',
  '-t',
  String(92 / 30),
  '-i',
  'anullsrc=channel_layout=stereo:sample_rate=48000',
);

const filters = [
  '[0:v]trim=start_frame=0:end_frame=136,setpts=PTS-STARTPTS[vtitle]',
  '[1:v]trim=start_frame=136:end_frame=840,setpts=PTS-STARTPTS[vcharacter]',
  '[vtitle][vcharacter]concat=n=2:v=1:a=0[v0]',
  '[7:a]apad,atrim=start_sample=0:end_sample=147200,asetpts=PTS-STARTPTS[as0]',
  '[1:a]apad,atrim=start_sample=0:end_sample=1196800,asetpts=PTS-STARTPTS[ac0]',
  '[as0][ac0]concat=n=2:v=0:a=1[a0]',
];
const laterFrames = [475, 790, 1258, 1233, 840];
laterFrames.forEach((frames, offset) => {
  const inputIndex = offset + 2;
  const outputIndex = offset + 1;
  filters.push(
    `[${inputIndex}:v]trim=start_frame=0:end_frame=${frames},setpts=PTS-STARTPTS[v${outputIndex}]`,
  );
  const samples = frames * 1600;
  filters.push(
    `[${inputIndex}:a]apad,atrim=start_sample=0:end_sample=${samples},asetpts=PTS-STARTPTS[a${outputIndex}]`,
  );
});
filters.push(
  '[v0][a0][v1][a1][v2][a2][v3][a3][v4][a4][v5][a5]concat=n=6:v=1:a=1[vbase][aout]',
);
filters.push(
  "[vbase]drawbox=x='mod(t*520\\,1740)':y=22:w=180:h=4:color=0xd7ffff@0.36:t=fill," +
    "drawbox=x='1740-mod(t*430\\,1740)':y=1054:w=180:h=4:color=0x77eef4@0.28:t=fill," +
    "drawbox=x=18:y='mod(t*360\\,940)+70':w=4:h=150:color=0x9df9ff@0.24:t=fill," +
    "drawbox=x=1898:y='940-mod(t*330\\,940)+70':w=4:h=150:color=0x67e5ee@0.22:t=fill[vout]",
);

const output = resolve(
  process.cwd(),
  '../../production-library/templates/settled/health-video-reference-tech-v1/wind-heat-reference-full-181s.mp4',
);
const result = spawnSync(
  'ffmpeg',
  [
    '-y',
    ...inputArgs,
    '-filter_complex',
    filters.join(';'),
    '-map',
    '[vout]',
    '-map',
    '[aout]',
    '-r',
    '30',
    '-frames:v',
    '5436',
    '-c:v',
    'libx264',
    '-preset',
    'medium',
    '-crf',
    '18',
    '-pix_fmt',
    'yuv420p',
    '-c:a',
    'aac',
    '-b:a',
    '192k',
    '-ar',
    '48000',
    '-movflags',
    '+faststart',
    output,
  ],
  {stdio: 'inherit'},
);

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}
console.log(`Assembled ${output} from 5436 frame-locked source frames.`);
