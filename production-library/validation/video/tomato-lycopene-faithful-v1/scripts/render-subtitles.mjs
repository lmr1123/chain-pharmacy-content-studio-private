import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

const require=createRequire(import.meta.url);const {chromium}=require('playwright');
const scriptDir=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(scriptDir,'..');
const srtFile=path.join(root,'audio/narration.srt');const outputDir=path.join(root,'renders/subtitles');
const seconds=(stamp)=>{const [h,m,rest]=stamp.split(':');const [s,ms]=rest.split(',');return +h*3600 + +m*60 + +s + +ms/1000};
const blocks=(await fs.readFile(srtFile,'utf8')).trim().split(/\n\s*\n/).map(block=>{
  const lines=block.trim().split('\n');const [start,end]=lines[1].split(/\s+-->\s+/);return {start:seconds(start),end:seconds(end),text:lines.slice(2).join(' ')};
});
await fs.mkdir(outputDir,{recursive:true});
const executablePath='/Users/liminrong/Library/Caches/ms-playwright/chromium_headless_shell-1148/chrome-mac/headless_shell';
const browser=await chromium.launch({headless:true,executablePath});const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
for(let i=0;i<blocks.length;i++){
  const cue=blocks[i];
  await page.setContent(`<!doctype html><meta charset="utf-8"><style>*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;background:transparent;overflow:hidden}.wrap{position:absolute;left:100px;right:100px;bottom:30px;text-align:center}.caption{display:inline;color:#211d1f;font-family:"HarmonyOS Sans SC","PingFang SC","Microsoft YaHei",sans-serif;font-size:38px;font-weight:650;line-height:1.38;letter-spacing:.02em;text-shadow:-2px -2px 0 #fff,2px -2px 0 #fff,-2px 2px 0 #fff,2px 2px 0 #fff,0 3px 8px rgba(255,255,255,.95)}</style><div class="wrap"><span class="caption"></span></div>`);
  await page.locator('.caption').evaluate((node,text)=>node.textContent=text,cue.text);
  const file=`${String(i+1).padStart(3,'0')}.png`;await page.screenshot({path:path.join(outputDir,file),omitBackground:true});cue.file=file;
}
await page.setContent('<!doctype html><style>html,body{margin:0;width:1920px;height:1080px;background:transparent}</style>');
await page.screenshot({path:path.join(outputDir,'blank.png'),omitBackground:true});
await browser.close();await fs.writeFile(path.join(outputDir,'manifest.json'),JSON.stringify({cues:blocks},null,2)+'\n');console.log(`${blocks.length} subtitle layers`);
