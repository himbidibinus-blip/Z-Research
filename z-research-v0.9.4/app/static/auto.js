'use strict';
/* v0.5.2: provider adapters, dataset-driven construct roles, editable hypotheses,
   audited numeric input editing, debounced live PLS preview. No AI-generated statistics. */
(function(){
 const A=id=>document.getElementById(id);
 const defaults={openai:'gpt-5-mini',gemini:'gemini-2.5-flash',anthropic:'claude-sonnet-4-5',openrouter:'openai/gpt-4o-mini',groq:'llama-3.3-70b-versatile',deepseek:'deepseek-chat',mistral:'mistral-small-latest',together:'meta-llama/Llama-3.3-70B-Instruct-Turbo',custom:''};
 const names={openai:'OpenAI',gemini:'Google Gemini',anthropic:'Anthropic Claude',openrouter:'OpenRouter',groq:'Groq',deepseek:'DeepSeek',mistral:'Mistral',together:'Together',custom:'Custom API'};
 A('aiProvider').onchange=()=>{const p=A('aiProvider').value;A('aiModel').value=defaults[p];A('customEndpointWrap').style.display=p==='custom'?'block':'none'};
 A('connectBtn').onclick=async()=>{if(!state.auth?.authenticated){toast('Log in to the local Z-Research account first');return}const p=A('aiProvider').value;try{
   A('connectBtn').disabled=true;A('connectionMsg').textContent=`Checking ${names[p]} credential…`;
   const r=await jsonPost('/api/ai/connect',{provider:p,api_key:A('apiKey').value.trim(),model:A('aiModel').value.trim(),base_url:A('aiBaseUrl').value.trim()});
   A('apiKey').value='';await refreshAuth();A('connectionMsg').textContent=`${names[p]} · ${r.model}. ${r.notice}`;
   toast(`${names[p]} connected · ${r.model}${r.verified_key?' (credential accepted)':' (unverified custom endpoint)'}`);
 }catch(e){A('connectionMsg').textContent=e.message;toast(e.message)}finally{A('connectBtn').disabled=false}};
 const oldRenderAuth=renderAuth;
 renderAuth=function(...args){oldRenderAuth(...args);let s=state.auth||{};if(s.provider&&defaults[s.provider]!==undefined){A('aiProvider').value=s.provider;A('customEndpointWrap').style.display=s.provider==='custom'?'block':'none'}
   if(s.provider_connected){A('providerSide').textContent=`● ${s.provider_label||names[s.provider]} connected`;A('metricAi').textContent=s.provider_label||names[s.provider];A('connectionMsg').textContent=`Connected: ${s.provider_label||names[s.provider]} · ${s.model}. Key is held in server RAM only.`}
   else A('connectionMsg').textContent='Select an AI provider and enter its own API key. ChatGPT Plus is not an API subscription.';
 };
 // Provider-independent guards in AI Writer + Chapter Studio.
 requireProvider=function(){if(!requireLogin())return false;if(!state.auth.provider_connected){switchPage('settings');toast('Connect a supported AI provider in Settings first');return false}return true};
 A('disconnectBtn').onclick=async()=>{try{await jsonPost('/api/ai/disconnect',{});await refreshAuth();toast('AI provider disconnected')}catch(e){toast(e.message)}};
 // Dataset construct inference: names like trust_1 / trust_2 grouped; scientific roles NOT inferred.
 let available=[],datasetSeen=null;
 function inferConstructs(data){
   let cols=data?.columns||[];let previews=data?.preview||[];let groups=new Map();
   for(const col of cols){let vals=previews.map(r=>r[col]).filter(v=>v!==null&&v!==undefined&&v!=='');
     if(data?.numeric_columns){if(!data.numeric_columns.includes(col))continue;}else if(!vals.length||vals.some(v=>!Number.isFinite(Number(v))))continue;
     if(/^(id|row_?id|timestamp|created_at|record_?no|response_?id)$/i.test(col))continue;
     const m=col.match(/^(.+?)[_\- ](?:item[_\- ]?)?(\d{1,3})$/i);
     let name=m?m[1].replace(/[_-]+/g,' ').trim():col.replace(/[_-]+/g,' ').trim();
     const key=name.toLowerCase();if(!groups.has(key))groups.set(key,{key,label:name,indicators:[]});groups.get(key).indicators.push(col);
   }
   return [...groups.values()].sort((a,b)=>a.label.localeCompare(b.label)).slice(0,40);
 }
 const roleIds=['autoIV','autoDV','autoMediator','autoModerator'];
 function selectedValues(id){const el=A(id);return [...el.selectedOptions].map(o=>o.value).filter(Boolean)}
 function loadRoleGroups(force=false){if(!force&&state.dataset===datasetSeen)return;datasetSeen=state.dataset;
   available=inferConstructs(state.data);const opts=available.map(g=>`<option value="${esc(g.key)}">${esc(g.label)} (${g.indicators.length})</option>`).join('');
   for(const id of roleIds){A(id).innerHTML=(id==='autoDV'?'<option value="">Select Y</option>':'')+opts;}
   A('autoModelMessage').textContent=available.length?`${available.length} possible numeric constructs detected. Grouping uses column names, not theoretical assumptions. Select X and Y.`:'No eligible numeric columns detected. Upload a numerical dataset first.';
 }
 function createModel(){
   const iv=selectedValues('autoIV'),dv=A('autoDV').value,med=selectedValues('autoMediator'),mod=selectedValues('autoModerator');
   if(!iv.length||!dv){A('autoModelMessage').textContent='Select at least one X and one Y to auto-generate.';return false}
   const all=[...iv,dv,...med,...mod];if(new Set(all).size!==all.length){A('autoModelMessage').textContent='Construct roles must be distinct; remove duplicate assignments.';return false}
   const ordered=[...iv,...med,...mod,dv];if(ordered.length>24){toast('Maximum 24 constructs');return false}
   const byKey=new Map(available.map(g=>[g.key,g]));if(ordered.some(k=>!byKey.has(k)))return false;
   const byId=new Map();const nodes=ordered.map((k,i)=>{
     const a=byKey.get(k),id='auto_'+i;byId.set(k,id);
     const role=iv.includes(k)?'iv':med.includes(k)?'mediator':mod.includes(k)?'moderator':'dv';
     const x=role==='iv'?160:role==='dv'?820:role==='mediator'?455:465;
     const list=role==='iv'?iv:role==='mediator'?med:role==='moderator'?mod:[dv];
     const j=list.indexOf(k);const y=135+(j+0.5)*Math.min(360/Math.max(1,list.length),150)+(role==='moderator'?180:0);
     return {id,label:a.label,type:'latent',measurement:'reflective',x,y:Math.min(550,y),role,indicators:a.indicators};
   });
   const edges=[];const seen=new Set();const connect=(source,target,kind='direct',moderator=null)=>{
     if(source===target)return;const key=[source,target,kind,moderator].join('|');if(seen.has(key))return;seen.add(key);
     edges.push({source:byId.get(source),target:byId.get(target),kind,moderator:moderator?byId.get(moderator):undefined,label:'H'+(edges.length+1)});
   };
   for(const x of iv){connect(x,dv);for(const m of med)connect(x,m)}
   for(const m of med)connect(m,dv);
   for(const w of mod){connect(w,dv);for(const x of iv)connect(x,dv,'moderation',w)}
   state.model={nodes,edges};state.selected=null;selectNode(null);
   A('autoModelMessage').textContent=`Generated ${nodes.length} constructs, ${edges.length} hypotheses. Adjust theory and indicator mapping before interpreting results.`;
   renderHypotheses();scheduleLive();return true;
 }
 A('autoBuild').onclick=()=>{if(createModel())toast('Model & hypotheses generated automatically')};
 A('clearRoles').onclick=()=>{for(const id of roleIds)for(const option of A(id).options)option.selected=false;A('autoModelMessage').textContent='Role selections cleared; current model retained.'};
 for(const id of roleIds)A(id).addEventListener('change',()=>{if(selectedValues('autoIV').length&&A('autoDV').value)createModel()});
 // Editable hypothesis paths; editing edges does not alter the theory role selections.
 function options(sel){return state.model.nodes.map(n=>`<option value="${esc(n.id)}" ${sel===n.id?'selected':''}>${esc(n.label)}</option>`).join('')}
 function renderHypotheses(){const root=A('hypothesisEditor');
   if(!state.model.edges.length){root.innerHTML='<p class="hint">No hypotheses. Choose roles or add a manual path.</p>';return}
   root.innerHTML=state.model.edges.map((edge,i)=>`<div class="hypothesis-row" data-index="${i}"><div class="minirow"><input aria-label="Hypothesis name" data-key="label" value="${esc(edge.label||'H'+(i+1))}"/><select aria-label="From construct" data-key="source">${options(edge.source)}</select><span>→</span><select aria-label="To construct" data-key="target">${options(edge.target)}</select></div><div class="minirow"><select data-key="kind"><option value="direct" ${edge.kind!=='moderation'?'selected':''}>Direct</option><option value="moderation" ${edge.kind==='moderation'?'selected':''}>Interaction</option></select>${edge.kind==='moderation'?`<select data-key="moderator" aria-label="Moderator">${options(edge.moderator)}</select>`:''}<button class="btn danger" data-delete="${i}" title="Delete hypothesis">Remove</button></div></div>`).join('');
   root.querySelectorAll('[data-key]').forEach(el=>el.addEventListener('change',()=>{
     const idx=Number(el.closest('[data-index]').dataset.index),edge=state.model.edges[idx];if(!edge)return;
     edge[el.dataset.key]=el.value;if(el.dataset.key==='kind'&&el.value==='moderation'){edge.moderator=state.model.nodes.find(n=>n.id!==edge.source&&n.id!==edge.target)?.id||''}
     if(edge.kind!=='moderation')delete edge.moderator;
     drawModel();renderHypotheses();scheduleLive();
   }));
   root.querySelectorAll('[data-delete]').forEach(b=>b.onclick=()=>{state.model.edges.splice(Number(b.dataset.delete),1);drawModel();renderHypotheses();scheduleLive()});
 }
 const originalDraw=drawModel;
 drawModel=function(...args){let r=originalDraw(...args);renderHypotheses();scheduleLive();return r};
 A('edgeModerator').innerHTML='<option value="">Choose moderator</option>';
 A('edgeKind').onchange=()=>{A('edgeModerator').disabled=A('edgeKind').value!=='moderation'};A('edgeKind').onchange();
 const origNodeSelects=updateNodeSelects;
 updateNodeSelects=function(...args){const r=origNodeSelects(...args);const el=A('edgeModerator'),v=el.value;el.innerHTML='<option value="">Choose moderator</option>'+state.model.nodes.map(n=>`<option value="${esc(n.id)}">${esc(n.label)}</option>`).join('');el.value=v;return r};
 A('addEdge').onclick=()=>{const source=A('edgeFrom').value,target=A('edgeTo').value,kind=A('edgeKind').value,moderator=A('edgeModerator').value,label=A('edgeLabel').value.trim()||`H${state.model.edges.length+1}`;
   if(!source||!target||source===target){toast('Choose two distinct constructs');return}
   if(kind==='moderation'&&(!moderator||[source,target].includes(moderator))){toast('Choose a third construct as moderator');return}
   if(state.model.edges.some(e=>e.source===source&&e.target===target&&(e.kind||'direct')===kind&&(kind!=='moderation'||e.moderator===moderator))){toast('Hypothesis path already exists');return}
   state.model.edges.push({source,target,kind,moderator:kind==='moderation'?moderator:undefined,label});A('edgeLabel').value=`H${state.model.edges.length+1}`;drawModel();toast('Hypothesis created');
 };
 // Special drawing layer for interaction hypothesis annotation while preserving the original chart.
 const nativeRender=drawModel;
 drawModel=function(...args){const r=nativeRender(...args);const svg=A('modelSvg');for(const e of state.model.edges){if(e.kind!=='moderation')continue;
   const a=state.model.nodes.find(n=>n.id===e.source),b=state.model.nodes.find(n=>n.id===e.target),m=state.model.nodes.find(n=>n.id===e.moderator);
   if(!a||!b||!m)continue;const k=document.createElementNS('http://www.w3.org/2000/svg','text');k.setAttribute('x',String((a.x+b.x+m.x)/3));k.setAttribute('y',String((a.y+b.y+m.y)/3-18));k.setAttribute('font-size','13');k.setAttribute('font-weight','bold');k.setAttribute('fill','#835ad3');k.textContent=`${e.label}: ${m.label} ×`;svg.append(k)}return r};
 // Live preview uses 40 replications; manual Run PLS-SEM uses user-selected bootstrap setting.
 let liveTimer=null,revision=0,lastFingerprint='',liveWorking=false;
 function fingerprint(){return JSON.stringify([state.dataset,state.model.nodes.map(n=>[n.id,n.label,n.type,n.measurement,n.indicators]),state.model.edges.map(e=>[e.source,e.target,e.kind,e.moderator,e.label])]);}
 function scheduleLive(force=false){if(!A('autoRecompute').checked)return;let fp=fingerprint();if(!force&&fp===lastFingerprint)return;lastFingerprint=fp;clearTimeout(liveTimer);const current=++revision;
   if(!state.dataset||state.model.nodes.length<2||!state.model.edges.length)return;
   state.lastAnalysis=null;A('plsStatus').textContent='Model changed · preparing live recomputation…';
   liveTimer=setTimeout(async()=>{
     if(!state.auth?.authenticated){A('plsStatus').textContent='Log in locally to activate live PLS analysis (no AI key needed).';return}
     try{
       A('plsStatus').textContent='Live recalculation in progress · 40 provisional bootstrap replications…';
       let result=await jsonPost('/api/v05/pls/preview',{dataset_id:state.dataset,nodes:state.model.nodes,edges:state.model.edges,bootstraps:40,seed:Number(A('plsSeed').value)||42});
       if(current!==revision)return;
       v5RenderPLS(result);
       A('plsStatus').textContent='✓ Live preview updated (40 bootstraps). Provisional estimates not saved; use Run PLS-SEM to save full analysis.';
       // A previous persisted run no longer matches this model; keep it out of Chapter 4.
       state.lastAnalysis=null;
     }catch(e){if(current!==revision)return;A('plsStatus').textContent='Live preview: '+e.message}
   },850);
 }
 A('autoRecompute').onchange=()=>{if(A('autoRecompute').checked)scheduleLive(true);else{clearTimeout(liveTimer);revision++;A('plsStatus').textContent='Auto recalculation paused; click Run PLS-SEM to recompute manually.'}};
 A('plsSeed').addEventListener('change',()=>scheduleLive(true));
 A('runPLS').addEventListener('click',()=>{clearTimeout(liveTimer);revision++},{capture:true});
 // Auto-apply mapped indicator edits as user leaves a field.
 for(const id of ['selectedName','selectedIndicators','selectedMeasurement']){
   A(id).addEventListener('change',()=>{if(state.selected)updateNode()});
 }
 // Repaint selectors when datasets reload / switch / upload.
 const oldLoad=loadPreview;
 loadPreview=async function(...args){const v=await oldLoad(...args);loadRoleGroups();await loadEditableRows(0);scheduleLive(true);return v};
 const oldAuth=refreshAuth;
 refreshAuth=async function(...args){const v=await oldAuth(...args);if(state.auth?.authenticated)scheduleLive(true);return v};
 // Audited dataset value editing with pagination.
 let rowOffset=0,editTotal=0,editedColumns=[];
 async function loadEditableRows(offset=rowOffset){rowOffset=Math.max(0,offset);if(!state.dataset){A('numericEditor').innerHTML='<p class="hint">Select a dataset first.</p>';return}
   if(!state.auth?.authenticated){A('numericEditor').innerHTML='<p class="hint">Log in to edit numeric dataset values.</p>';return}
   try{const data=await api(`/api/v05/datasets/${encodeURIComponent(state.dataset)}/rows?offset=${rowOffset}&limit=10`);
      editTotal=data.total;editedColumns=data.columns.filter(c=>state.model.nodes.some(n=>(n.indicators||[]).includes(c)));
      if(!editedColumns.length)editedColumns=data.columns.slice(0,12);else editedColumns=editedColumns.slice(0,24);
      A('dataPageIndicator').textContent=`Rows ${data.total?rowOffset+1:0}–${Math.min(data.total,rowOffset+data.rows.length)} / ${data.total}`;
      A('dataPrev').disabled=rowOffset===0;A('dataNext').disabled=rowOffset+10>=editTotal;
      const head='<table><thead><tr><th>Row</th>'+editedColumns.map(c=>`<th>${esc(c)}</th>`).join('')+'</tr></thead>';
      const rows=data.rows.map((r,i)=>'<tr><td>'+String(rowOffset+i+1)+'</td>'+editedColumns.map(c=>`<td><input class="dataset-input" aria-label="${esc(c)} row ${rowOffset+i+1}" data-row="${rowOffset+i}" data-col="${esc(c)}" type="number" step="any" value="${r[c]==null?'':esc(r[c])}"/></td>`).join('')+'</tr>').join('');
      A('numericEditor').innerHTML=head+'<tbody>'+rows+'</tbody></table>';
      A('numericEditor').querySelectorAll('[data-col]').forEach(inp=>inp.onchange=async()=>{
        const value=inp.value.trim()===''?null:Number(inp.value);if(value!==null&&!Number.isFinite(value)){toast('Enter a valid number');return}
        inp.disabled=true;try{await jsonPost(`/api/v05/datasets/${encodeURIComponent(state.dataset)}/edit-cell`,{row:Number(inp.dataset.row),column:inp.dataset.col,value});
          A('dataEditNotice').textContent=`Saved row ${Number(inp.dataset.row)+1}, ${inp.dataset.col}. Original CSV backed up. Recalculating…`;
          await oldLoad();scheduleLive(true);
        }catch(e){A('dataEditNotice').textContent=e.message;toast(e.message)}finally{inp.disabled=false}
      });
   }catch(e){A('numericEditor').textContent=e.message}
 }
 A('dataPrev').onclick=()=>loadEditableRows(Math.max(0,rowOffset-10));A('dataNext').onclick=()=>loadEditableRows(Math.min(editTotal-1,rowOffset+10));A('dataReload').onclick=()=>loadEditableRows();
 const oldSwitch=switchPage;
 switchPage=function(p){const r=oldSwitch(p);if(p==='pls')loadEditableRows().catch(e=>toast(e.message));if(p==='model')loadRoleGroups();return r};
 // Existing loaded model, when any change is applied manually, triggers live estimation.
 loadRoleGroups();renderHypotheses();
})();
