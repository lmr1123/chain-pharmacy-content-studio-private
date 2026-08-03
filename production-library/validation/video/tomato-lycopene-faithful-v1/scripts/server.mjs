import http from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const scriptDir=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(scriptDir,'..');const port=Number(process.env.PORT||9014);const exportRoot=path.join(root,'exports');
await fsp.mkdir(exportRoot,{recursive:true});
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation','.mp4':'video/mp4'};
function json(res,status,value){res.writeHead(status,{'content-type':'application/json; charset=utf-8'});res.end(JSON.stringify(value))}
async function body(req){const chunks=[];for await(const c of req)chunks.push(c);return JSON.parse(Buffer.concat(chunks).toString('utf8'))}
function run(script,env){const r=spawnSync(process.execPath,[path.join(scriptDir,script)],{cwd:root,env:{...process.env,...env},encoding:'utf8'});if(r.status!==0)throw new Error((r.stderr||r.stdout||'export failed').slice(-4000))}
const server=http.createServer(async(req,res)=>{try{
  if(req.method==='POST'&&req.url?.startsWith('/api/export/')){const format=req.url.split('/').pop();if(!['pptx','mp4'].includes(format))return json(res,400,{error:'unsupported'});const project=await body(req);const stamp=new Date().toISOString().replace(/[-:.]/g,'').replace('Z','');const dir=path.join(exportRoot,stamp+'-'+format);await fsp.mkdir(dir,{recursive:true});const snapshot=path.join(dir,'project.json');await fsp.writeFile(snapshot,JSON.stringify(project,null,2)+'\n');const out=path.join(dir,format==='pptx'?'番茄红素_当前作品.pptx':'番茄红素_当前作品.mp4');if(format==='pptx')run('build-pptx.mjs',{PROJECT_FILE:snapshot,OUTPUT_FILE:out});else{const renders=path.join(dir,'renders');run('render-scenes.mjs',{PROJECT_FILE:snapshot,RENDER_DIR:renders});run('build-video.mjs',{PROJECT_FILE:snapshot,RENDER_DIR:renders,OUTPUT_FILE:out,AUDIO_FILE:path.join(root,'audio/narration-normalized.wav')})}return json(res,200,{ok:true,download:`/exports/${path.basename(dir)}/${path.basename(out)}`})}
  let rel=req.url==='/'?'web/index.html':decodeURIComponent((req.url||'').replace(/^\//,''));const target=path.resolve(root,rel);if(!target.startsWith(root)||!fs.existsSync(target)||fs.statSync(target).isDirectory()){res.writeHead(404);return res.end('Not found')}res.writeHead(200,{'content-type':mime[path.extname(target)]||'application/octet-stream'});fs.createReadStream(target).pipe(res);
}catch(e){json(res,500,{error:String(e.message||e)})}});
server.listen(port,'127.0.0.1',()=>console.log(`http://127.0.0.1:${port}/`));
