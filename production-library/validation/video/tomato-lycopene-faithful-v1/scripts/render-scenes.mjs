import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';

const require=createRequire(import.meta.url);const {chromium}=require('playwright');
const scriptDir=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(scriptDir,'..');
const projectFile=path.resolve(process.env.PROJECT_FILE||path.join(root,'project.json'));
const renderDir=path.resolve(process.env.RENDER_DIR||path.join(root,'renders'));
const project=JSON.parse(await fs.readFile(projectFile,'utf8'));
await fs.mkdir(renderDir,{recursive:true});
const executablePath='/Users/liminrong/Library/Caches/ms-playwright/chromium_headless_shell-1148/chrome-mac/headless_shell';
const browser=await chromium.launch({headless:true,executablePath,args:['--allow-file-access-from-files','--disable-web-security']});
const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
await page.addInitScript({content:`window.__PROJECT__=${JSON.stringify(project).replaceAll('</script>','<\\/script>')}`});
await page.goto(pathToFileURL(path.join(root,'web/index.html')).href,{waitUntil:'load'});await page.waitForFunction(()=>window.getProject&&window.getProject().scenes?.length>0);
const timeline=[];
for(let i=0;i<project.scenes.length;i++){
  const scene=project.scenes[i];const holds=[0.8,1.0,1.4,Math.max(1,scene.duration-3.2)];
  for(let stage=0;stage<4;stage++){
    await page.evaluate(([si,st])=>window.renderForExport(si,st),[i,stage]);await page.waitForTimeout(120);
    const name=`${String(i+1).padStart(2,'0')}-${scene.id}-stage${stage}.png`;await page.locator('#stage').screenshot({path:path.join(renderDir,name)});
    timeline.push({scene_id:scene.id,scene_index:i,stage,file:name,duration:holds[stage]});
  }
}
await browser.close();await fs.writeFile(path.join(renderDir,'timeline.json'),JSON.stringify({project_id:project.project_id,fps:project.canvas.fps,items:timeline},null,2)+'\n');
console.log(renderDir);
