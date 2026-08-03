import fs from 'node:fs/promises';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const scriptDir=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(scriptDir,'..');const subtitleDir=path.join(root,'renders/subtitles');
const {cues}=JSON.parse(await fs.readFile(path.join(subtitleDir,'manifest.json'),'utf8'));const timing=JSON.parse(await fs.readFile(path.join(root,'audio/timing.json'),'utf8'));
const entries=[];let cursor=0;const quote=p=>`'${p.replaceAll("'","'\\''")}'`;
for(const cue of cues){if(cue.start>cursor+.001)entries.push({file:'blank.png',duration:cue.start-cursor});entries.push({file:cue.file,duration:cue.end-cue.start});cursor=cue.end;}
if(timing.total_duration>cursor+.001)entries.push({file:'blank.png',duration:timing.total_duration-cursor});
let body='ffconcat version 1.0\n';for(const entry of entries)body+=`file ${quote(path.join(subtitleDir,entry.file))}\nduration ${entry.duration.toFixed(4)}\n`;body+=`file ${quote(path.join(subtitleDir,entries.at(-1).file))}\n`;
const list=path.join(subtitleDir,'track.ffconcat');const output=path.join(subtitleDir,'subtitle-track.mov');await fs.writeFile(list,body);
const result=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',list,'-vf','fps=30,format=argb','-c:v','qtrle','-pix_fmt','argb',output],{encoding:'utf8',maxBuffer:8*1024*1024});if(result.status!==0)throw new Error(result.stderr||`ffmpeg failed ${result.status}`);console.log(output);
