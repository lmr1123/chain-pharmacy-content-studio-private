import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const scriptDir=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(scriptDir,'..');
const projectFile=path.resolve(process.env.PROJECT_FILE||path.join(root,'project.json'));
const renderDir=path.resolve(process.env.RENDER_DIR||path.join(root,'renders'));
const outputFile=path.resolve(process.env.OUTPUT_FILE||path.join(root,'福尔麦金利番茄红素软胶囊_完整复刻.mp4'));
const defaultAudio=fs.existsSync(path.join(root,'audio/narration-normalized.wav'))?path.join(root,'audio/narration-normalized.wav'):path.join(root,'audio/narration.wav');
const audioFile=path.resolve(process.env.AUDIO_FILE||defaultAudio);const subtitleTrack=path.join(root,'renders/subtitles/subtitle-track.mov');
const project=JSON.parse(await fsp.readFile(projectFile,'utf8'));const timeline=JSON.parse(await fsp.readFile(path.join(renderDir,'timeline.json'),'utf8')).items;
const segmentDir=path.join(renderDir,'segments');await fsp.mkdir(segmentDir,{recursive:true});const transition=.28;const segments=[];
function run(args){const r=spawnSync('ffmpeg',['-hide_banner','-loglevel','error',...args],{encoding:'utf8',maxBuffer:32*1024*1024});if(r.status!==0)throw new Error(`ffmpeg failed: ${r.status}\n${r.stderr||r.stdout||''}`)}
for(let si=0;si<project.scenes.length;si++){
  console.log(`render scene ${si+1}/${project.scenes.length}`);
  const items=timeline.filter(x=>x.scene_index===si);const out=path.join(segmentDir,`${String(si+1).padStart(2,'0')}.mp4`);const args=['-y'];
  for(const it of items)args.push('-loop','1','-t',String(it.duration+transition),'-i',path.join(renderDir,it.file));
  let filters=[];items.forEach((it,i)=>filters.push(`[${i}:v]scale=1920:1080,format=yuv420p,fps=30[v${i}]`));let prev='v0',offset=items[0].duration;
  for(let i=1;i<items.length;i++){const next=`x${i}`;filters.push(`[${prev}][v${i}]xfade=transition=fade:duration=${transition}:offset=${Math.max(.1,offset).toFixed(3)}[${next}]`);prev=next;offset+=items[i].duration;}
  args.push('-filter_complex',filters.join(';'),'-map',`[${prev}]`,'-t',String(items.reduce((a,b)=>a+b.duration,0)),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30','-an',out);run(args);segments.push(out);
}
const concatFile=path.join(segmentDir,'concat.txt');await fsp.writeFile(concatFile,segments.map(p=>`file '${p.replaceAll("'","'\\''")}'`).join('\n')+'\n');const silent=path.join(segmentDir,'silent.mp4');run(['-y','-f','concat','-safe','0','-i',concatFile,'-c','copy',silent]);
await fsp.mkdir(path.dirname(outputFile),{recursive:true});
if(fs.existsSync(audioFile)&&fs.existsSync(subtitleTrack)){run(['-y','-i',silent,'-i',audioFile,'-i',subtitleTrack,'-filter_complex','[0:v][2:v]overlay=0:0:shortest=1[v]','-map','[v]','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-shortest','-movflags','+faststart',outputFile]);}
else if(fs.existsSync(audioFile))run(['-y','-i',silent,'-i',audioFile,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-shortest','-movflags','+faststart',outputFile]);
else run(['-y','-i',silent,'-c','copy','-movflags','+faststart',outputFile]);
console.log(outputFile);
