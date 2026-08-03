(function(){
  const rootPath='../';
  let project=null,current=0,selected=null,history=[],historyIndex=-1;
  const $=s=>document.querySelector(s);
  const clone=v=>JSON.parse(JSON.stringify(v));
  const assetUrl=key=>{
    const src=project.assets[key]?.src||'';
    if(!src)return '';
    if(src.startsWith('data:')||src.startsWith('http')||src.startsWith('file:'))return src;
    return rootPath+src;
  };
  async function load(){
    project=window.__PROJECT__?clone(window.__PROJECT__):await fetch(rootPath+'project.json').then(r=>r.json());
    const saved=localStorage.getItem(project.project_id);if(saved&&!window.__PROJECT__)project=JSON.parse(saved);
    project.patches=project.patches||{};pushHistory();renderAll();fit();
  }
  function pushHistory(){history=history.slice(0,historyIndex+1);history.push(clone(project));historyIndex=history.length-1;updateStatus('未保存调整');}
  function restore(index){if(index<0||index>=history.length)return;historyIndex=index;project=clone(history[index]);renderAll();}
  function updateStatus(t){const el=$('#saveStatus');if(el)el.textContent=t;}
  function renderAll(){renderList();renderScene();renderInspector();}
  function renderList(){const box=$('#sceneList');if(!box)return;box.innerHTML='';project.scenes.forEach((s,i)=>{const item=document.createElement('div');item.className='scene-item'+(i===current?' active':'');item.innerHTML=`<strong>${String(i+1).padStart(2,'0')}·${s.title}</strong><small>${s.source_class} · ${s.duration}秒</small>`;item.onclick=()=>{current=i;selected=null;renderAll()};box.appendChild(item)})}
  function layer(id,cls,html){const p=project.patches[id]||{};const style=`transform:translate(${p.x||0}px,${p.y||0}px) scale(${p.scale||1});transform-origin:center`;return `<div class="layer ${cls}" data-layer="${id}" style="${style}"><i class="layer-handle"></i>${html}<i class="resize-handle"></i></div>`}
  function editable(field,value){return `<span contenteditable="true" data-field="${field}">${value||''}</span>`}
  function renderScene(stage=3){const s=project.scenes[current],stageEl=$('#stage');if(!stageEl)return;stageEl.className=`stage stage-stage-${stage}`;
    let content='';
    if(s.groups)content=`<div class="group-list">${s.groups.map((g,i)=>`<div class="group"><strong contenteditable="true" data-group="${i}" data-key="name">${g.name}</strong><span contenteditable="true" data-group="${i}" data-key="copy">${g.copy}</span></div>`).join('')}</div>`;
    else if(s.summary)content=`<div class="summary">${s.summary.map((r,i)=>`<div class="label" contenteditable="true" data-summary="${i}" data-key="label">${r.label}</div><div contenteditable="true" data-summary="${i}" data-key="value">${r.value}</div>`).join('')}</div>`;
    else content=`<div class="bullet-list">${(s.bullets||[]).map((b,i)=>`<div class="bullet" contenteditable="true" data-bullet="${i}">${b}</div>`).join('')}</div>`;
    const img=s.image?assetUrl(s.image):'';
    stageEl.innerHTML=`
      ${layer(s.id+':title','scene-title',editable('title',s.title))}
      ${layer(s.id+':headline','scene-headline',editable('headline',s.headline))}
      ${layer(s.id+':image','visual',img?`<img data-image-key="${s.image}" src="${img}">`:'<div></div>')}
      ${layer(s.id+':content','content',content)}
      <div class="subtitle">${s.narration}</div><div class="origin-badge">内部商品知识培训</div>`;
    bindScene();applySelection();
  }
  function bindScene(){const s=project.scenes[current];document.querySelectorAll('[contenteditable]').forEach(el=>el.addEventListener('blur',()=>{if(el.dataset.field!==undefined)s[el.dataset.field]=el.textContent.trim();if(el.dataset.bullet!==undefined)s.bullets[+el.dataset.bullet]=el.textContent.trim();if(el.dataset.group!==undefined)s.groups[+el.dataset.group][el.dataset.key]=el.textContent.trim();if(el.dataset.summary!==undefined)s.summary[+el.dataset.summary][el.dataset.key]=el.textContent.trim();pushHistory();renderInspector()}));
    document.querySelectorAll('.layer').forEach(el=>{el.addEventListener('click',e=>{if(e.target.closest('[contenteditable]'))return;e.stopPropagation();selected=el.dataset.layer;applySelection()});const move=el.querySelector('.layer-handle'),resize=el.querySelector('.resize-handle');dragHandle(move,el,false);dragHandle(resize,el,true)});$('#stage').onclick=e=>{if(e.target.id==='stage'){selected=null;applySelection()}};
  }
  function dragHandle(handle,el,isResize){handle.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();const id=el.dataset.layer,p=project.patches[id]||(project.patches[id]={x:0,y:0,scale:1});const sx=e.clientX,sy=e.clientY,bx=p.x||0,by=p.y||0,bs=p.scale||1;handle.setPointerCapture(e.pointerId);handle.onpointermove=ev=>{if(isResize)p.scale=Math.max(.35,Math.min(2.4,bs+(ev.clientX-sx)/320));else{p.x=bx+(ev.clientX-sx)/currentScale();p.y=by+(ev.clientY-sy)/currentScale()}el.style.transform=`translate(${p.x||0}px,${p.y||0}px) scale(${p.scale||1})`};handle.onpointerup=()=>{handle.onpointermove=null;pushHistory()}})}
  function applySelection(){document.querySelectorAll('.layer').forEach(el=>el.classList.toggle('selected',el.dataset.layer===selected))}
  function renderInspector(){const s=project.scenes[current];if(!$('#projectTitle'))return;$('#projectTitle').value=project.title;$('#sourceClass').value=s.source_class;$('#durationInput').value=s.duration;$('#narrationInput').value=s.narration}
  function fit(){const vp=$('#stageViewport'),st=$('#stage');if(!vp||!st)return;st.style.transform=`scale(${vp.clientWidth/1920})`}
  function currentScale(){const vp=$('#stageViewport');return vp?vp.clientWidth/1920:1}
  function bindUi(){window.addEventListener('resize',fit);$('#undoBtn').onclick=()=>restore(historyIndex-1);$('#redoBtn').onclick=()=>restore(historyIndex+1);$('#projectTitle').onchange=e=>{project.title=e.target.value;pushHistory();renderList()};$('#durationInput').onchange=e=>{project.scenes[current].duration=+e.target.value;pushHistory();renderList()};$('#narrationInput').onchange=e=>{project.scenes[current].narration=e.target.value;pushHistory();renderScene()};$('#replaceBtn').onclick=()=>{if(!selected||!selected.endsWith(':image'))return alert('请先选中当前场景的图片');$('#imagePicker').click()};$('#imagePicker').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{const s=project.scenes[current];project.assets[s.image].src=r.result;pushHistory();renderScene()};r.readAsDataURL(f)};$('#downloadJsonBtn').onclick=()=>download('tomato-lycopene-project.json',JSON.stringify(project,null,2),'application/json');$('#exportPptxBtn').onclick=()=>serverExport('pptx');$('#exportMp4Btn').onclick=()=>serverExport('mp4')}
  function download(name,data,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data],{type}));a.download=name;a.click();URL.revokeObjectURL(a.href)}
  async function serverExport(format){if(location.protocol==='file:')return alert('请先运行 scripts/server.mjs，再从本地编辑器导出。');updateStatus('正在导出 '+format.toUpperCase());const r=await fetch('/api/export/'+format,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(project)});const j=await r.json();if(!r.ok)throw new Error(j.error||'导出失败');updateStatus('导出完成');location.href=j.download}
  window.renderForExport=(sceneIndex,stage=3)=>{current=sceneIndex;selected=null;document.body.classList.add('export-mode');renderScene(stage);const st=$('#stage');st.style.transform='none';return {scene:project.scenes[current].id,stage}};
  window.getProject=()=>clone(project);
  bindUi();load().catch(e=>{document.body.innerHTML='<pre>'+e.stack+'</pre>'});
})();
