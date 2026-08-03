import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const scriptDir=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(scriptDir,'..');
const projectFile=path.resolve(process.env.PROJECT_FILE||path.join(root,'project.json'));
const outputFile=path.resolve(process.env.OUTPUT_FILE||path.join(root,'福尔麦金利番茄红素软胶囊_可编辑课件.pptx'));
const project=JSON.parse(await fs.readFile(projectFile,'utf8'));
const W=1920,H=1080;
const deck=Presentation.create({slideSize:{width:W,height:H}});
const theme=project.theme;

function text(slide,name,value,pos,size,color=theme.ink,bold=false,align='left'){
  const shape=slide.shapes.add({geometry:'textbox',name,position:pos,fill:'none',line:{style:'solid',fill:'none',width:0}});
  shape.text=value;shape.text.style={fontFamily:theme.font_family,fontSize:size,color,bold,alignment:align,verticalAlignment:'middle'};return shape;
}
function rect(slide,name,pos,fill,lineFill='none',lineWidth=0,radius='rounded-xl'){
  return slide.shapes.add({geometry:'roundRect',name,position:pos,fill,line:{style:'solid',fill:lineFill,width:lineWidth},borderRadius:radius});
}
async function image(slide,name,src,pos){
  const full=path.resolve(root,src);const bytes=await fs.readFile(full);const ab=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
  return slide.images.add({name,blob:ab,contentType:'image/png',alt:name,fit:'contain',position:pos});
}
function background(slide){
  slide.background.fill=theme.background;
  slide.shapes.add({geometry:'ellipse',name:'silk-highlight',position:{left:-180,top:-220,width:1320,height:760},fill:{color:'#ffffff',transparency:28},line:{style:'solid',fill:'none',width:0}});
  slide.shapes.add({geometry:'ellipse',name:'silk-shadow',position:{left:1050,top:650,width:1180,height:620},fill:{color:'#d9d4cd',transparency:55},line:{style:'solid',fill:'none',width:0}});
}
function addTitle(slide,scene){
  text(slide,`${scene.id}:title-outline`,scene.title,{left:240,top:36,width:1440,height:86},60,theme.accent,true,'center');
  text(slide,`${scene.id}:title`,scene.title,{left:240,top:36,width:1440,height:86},55,theme.title,true,'center');
  text(slide,`${scene.id}:headline`,scene.headline,{left:126,top:140,width:1668,height:84},39,theme.accent,true,'left');
  text(slide,`${scene.id}:internal`,'内部商品知识培训',{left:1765,top:60,width:38,height:300},18,theme.muted,false,'center').rotation=90;
}
function addBullets(slide,scene){
  const items=scene.bullets||[];const two=items.length>2;const cols=two?2:1;const colW=two?800:1620;const rowH=items.length>2?72:88;
  items.forEach((item,i)=>{const col=i%cols,row=Math.floor(i/cols),left=135+col*(colW+46),top=760+row*rowH;text(slide,`${scene.id}:bullet:${i}`,'✔',{left,top,width:36,height:52},28,theme.accent,true,'center');text(slide,`${scene.id}:bullet-text:${i}`,item,{left:left+42,top,width:colW-42,height:62},25,theme.ink,true,'left')});
}
function addGroups(slide,scene){
  const gap=20,w=528;scene.groups.forEach((g,i)=>{const left=128+i*(w+gap);rect(slide,`${scene.id}:group-bg:${i}`,{left,top:690,width:w,height:250},'#fffdfb','#d7aaa8',3);text(slide,`${scene.id}:group-name:${i}`,g.name,{left:left+20,top:712,width:w-40,height:62},23,theme.accent,true,'left');text(slide,`${scene.id}:group-copy:${i}`,g.copy,{left:left+20,top:780,width:w-40,height:138},20,theme.ink,false,'left')});
}
function addSummary(slide,scene){
  const left=260,top=368,labelW=380,valueW=1020,rowH=122;scene.summary.forEach((r,i)=>{rect(slide,`${scene.id}:summary-label-bg:${i}`,{left,top:top+i*rowH,width:labelW,height:rowH-4},'#fff8f3','#c6aaa4',2,'rounded-sm');rect(slide,`${scene.id}:summary-value-bg:${i}`,{left:left+labelW+4,top:top+i*rowH,width:valueW,height:rowH-4},'#fffdfb','#c6aaa4',2,'rounded-sm');text(slide,`${scene.id}:summary-label:${i}`,r.label,{left:left+24,top:top+i*rowH+18,width:labelW-48,height:78},27,theme.accent,true,'left');text(slide,`${scene.id}:summary-value:${i}`,r.value,{left:left+labelW+28,top:top+i*rowH+18,width:valueW-48,height:78},25,theme.ink,false,'left')});
}
for(const scene of project.scenes){
  const slide=deck.slides.add();background(slide);addTitle(slide,scene);
  if(scene.image){const a=project.assets[scene.image];if(a?.src)await image(slide,`${scene.id}:image`,a.src,scene.summary?{left:1340,top:170,width:420,height:210}:{left:300,top:240,width:1320,height:500});}
  if(scene.groups)addGroups(slide,scene);else if(scene.summary)addSummary(slide,scene);else addBullets(slide,scene);
  text(slide,`${scene.id}:footer`,scene.narration,{left:150,top:970,width:1620,height:74},22,'#211d1f',true,'center');
  slide.speakerNotes.textFrame.setText(`[Sources]\n- Business reference: ${project.reference.video}\n- Business script and quality-control edits: project.json\n- Scene source class: ${scene.source_class}\n- Generated illustration provenance: qa/asset-provenance.json`);
}
await fs.mkdir(path.dirname(outputFile),{recursive:true});
const pptx=await PresentationFile.exportPptx(deck);await pptx.save(outputFile);
console.log(outputFile);
