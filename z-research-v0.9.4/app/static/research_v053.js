'use strict';
/* Z-Research v0.5.3: new chapter workflow, Ollama settings and result explanations.
   Display values come from Python-computed results; drafts are never statistical inputs. */
(function(){
 const el=id=>document.getElementById(id);
 const protect=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const C=[1,2,3,4];
 const origSwitch=switchPage;
 switchPage=function(page){
   const result=origSwitch(page);
   const labels={overview:'Research dashboard',model:'Research Model Builder',pls:'SEM-PLS Analysis',intro:'Chapter 1 · Phenomena Finder',references:'Reference Library',literature:'Chapter 2 · Literature Review',methods:'Chapter 3 · Methodology',results:'Chapter 4 · Findings Writer',settings:'AI Connection & Account'};
   el('toptitle').textContent=labels[page]||page;
   if(['intro','literature','methods','results','references'].includes(page) && state.auth?.authenticated)refreshWritingContext().catch(e=>toast(e.message));
   if(page==='intro' && state.auth?.authenticated)loadNews().catch(()=>{});
   if(page==='literature' && state.auth?.authenticated)loadLiterature().catch(()=>{});
   return result;
 };
 // Direct localhost connection from dashboard. Ollama requires no API key.
 const previousProviderChanged=el('aiProvider').onchange;
 el('aiProvider').onchange=function(...args){
   if(previousProviderChanged)previousProviderChanged.apply(this,args);
   if(this.value==='ollama'){
     el('aiModel').value='qwen3:8b';el('apiKey').value='';
     el('apiKey').disabled=true;el('apiKey').placeholder='No key needed for local Ollama';
   }else{el('apiKey').disabled=false;el('apiKey').placeholder='Your provider API secret key';}
 };
 const prevConnect=el('connectBtn').onclick;
 el('connectBtn').onclick=async function(...args){
   if(el('aiProvider').value!=='ollama')return prevConnect.apply(this,args);
   if(!state.auth?.authenticated){toast('Create or log into the local owner account first.');return}
   this.disabled=true;el('connectionMsg').textContent='Checking local Ollama on 127.0.0.1:11434…';
   try{
     const data=await jsonPost('/api/ai/connect',{provider:'ollama',api_key:'',model:el('aiModel').value.trim()||'qwen3:8b'});
     await refreshAuth();el('connectionMsg').textContent='✓ Ollama local connected · '+data.model+' · No secret key or API charges.';
     toast('Ollama connected · '+data.model);
   }catch(e){el('connectionMsg').textContent=e.message;toast(e.message)}
   finally{this.disabled=false;}
 };
 const authOld=renderAuth;
 renderAuth=function(...args){authOld(...args);const s=state.auth||{};
   if(s.provider==='ollama'){
     el('aiProvider').value='ollama';el('aiKeyInfo')?.remove();el('aiModel').value=s.model||'qwen3:8b';
     el('apiKey').disabled=true;
     if(s.provider_connected)el('connectionMsg').textContent='Connected to Ollama locally. No API key required; no token billing.';
   }else el('apiKey').disabled=false;
 };
 // Draft studio reads the same shared library and permits separate drafts for each chapter.
 let refs=[],guides=[],runs=[],history=[],news=[];
 const chosen=Object.fromEntries(C.map(n=>{let stored=[];try{stored=JSON.parse(localStorage.getItem('zr:v054:refs:'+n)||'[]');if(!Array.isArray(stored))stored=[]}catch(e){}return [n,new Set(stored)]}));
 function persistSelection(n){try{localStorage.setItem('zr:v054:refs:'+n,JSON.stringify([...chosen[n]]))}catch(e){/* private browser mode */}}
 const selectionTouched=new Set();
 function lastName(ref){
   const authors=String(ref.authors||'').trim();
   if(!authors)return 'Author unknown';
   // OpenAlex imports often start with "Given Family"; RIS may use "Family, Given".
   const first=authors.split(/;|\band\b|,\s+(?=[A-Z][a-z]+\s+[A-Z])/i)[0].trim();
   const firstSegment=first.split(',')[0].trim();
   return firstSegment.split(/\s+/).length===1?firstSegment:(firstSegment.split(/\s+/).pop()||'Author unknown');
 }
 function citeLabel(ref){
   const style=el('styleChoice')?.value||'apa';
   const auth=lastName(ref);const year=ref.year||'n.d.';
   return style==='ieee'?`[${1+refs.findIndex(x=>x.id===ref.id)}]`:`(${auth}, ${year})`;
 }
 function insertCitation(n,id){
   const ref=refs.find(x=>x.id===id);if(!ref){toast('Reference unavailable; refresh library');return}
   const editor=el('c'+n+'Text');const text=citeLabel(ref);const start=editor.selectionStart??editor.value.length,end=editor.selectionEnd??start;
   const before=editor.value.slice(0,start),after=editor.value.slice(end);
   const prefix=before&&!/\s$/.test(before)?' ':'';
   editor.value=before+prefix+text+after;
   editor.focus();editor.setSelectionRange(start+prefix.length+text.length,start+prefix.length+text.length);
   chosen[n].add(id);persistSelection(n);renderReferencePicker(n);
   status(n,'Citation inserted. Verify the bibliographic details and the source statement before submission.');
 }
 function renderReferencePicker(n){
   const search=el('c'+n+'RefFilter');const query=(search?.value||'').trim().toLowerCase();
   const entries=refs.filter(ref=>`${ref.title} ${ref.authors} ${ref.year||''}`.toLowerCase().includes(query));
   const box=el('c'+n+'RefList');if(!box)return;
   box.innerHTML=entries.length?entries.map(ref=>`<div class="zr-citation-item" draggable="true" data-ref-id="${protect(ref.id)}" title="Drag onto the editor to cite"><label class="zr-citation-include"><input type="checkbox" data-chapter-include="${protect(ref.id)}" ${chosen[n].has(ref.id)?'checked':''} aria-label="Include reference in AI context"></label><div class="zr-citation-info"><b title="${protect(ref.title)}">${protect(ref.title)}</b><small>${protect(ref.authors||'Author unknown')} · ${protect(ref.year||'n.d.')}</small></div><button class="btn light zr-cite-button" data-cite-id="${protect(ref.id)}" title="Insert citation at cursor">Cite +</button></div>`).join(''):'<div class="hint zr-empty-ref">No matching references. Add publications in Reference Library.</div>';
   box.querySelectorAll('[data-chapter-include]').forEach(ch=>ch.addEventListener('change',()=>{
     selectionTouched.add(n);ch.checked?chosen[n].add(ch.dataset.chapterInclude):chosen[n].delete(ch.dataset.chapterInclude);
     persistSelection(n);updateCiteCount(n);
   }));
   box.querySelectorAll('[data-cite-id]').forEach(btn=>btn.addEventListener('click',()=>insertCitation(n,btn.dataset.citeId)));
   box.querySelectorAll('[draggable]').forEach(item=>item.addEventListener('dragstart',e=>{
     const ref=refs.find(x=>x.id===item.dataset.refId);
     if(!ref)return;e.dataTransfer.setData('text/plain',citeLabel(ref));e.dataTransfer.setData('application/x-zresearch-reference',ref.id);
     e.dataTransfer.effectAllowed='copy';
   }));
   updateCiteCount(n);
 }
 function updateCiteCount(n){el('c'+n+'RefCount').textContent=`${chosen[n].size} selected for AI context · Click Cite or drag into draft`;}
 for(const n of C){
   el('c'+n+'RefFilter').addEventListener('input',()=>renderReferencePicker(n));
   el('c'+n+'SelectAllRefs').onclick=()=>{
     selectionTouched.add(n);const all=refs.every(r=>chosen[n].has(r.id));
     if(all)chosen[n].clear();else refs.forEach(r=>chosen[n].add(r.id));persistSelection(n);renderReferencePicker(n);
   };
   const text=el('c'+n+'Text');
   el('c'+n+'Bibliography').onclick=()=>{
     const picked=refs.filter(x=>chosen[n].has(x.id));if(!picked.length){toast('Select one or more references first');return}
     const style=el('styleChoice').value;
     const entries=picked.map(ref=>{
       const author=ref.authors||'[AUTHOR TO VERIFY]',year=ref.year||'n.d.',title=ref.title||'[TITLE TO VERIFY]',venue=ref.venue||'[VENUE TO VERIFY]';
       const doi=ref.doi?' https://doi.org/'+ref.doi:'';
       const num=refs.findIndex(x=>x.id===ref.id)+1;
       return style==='ieee'?`[${num}] ${author}, “${title},” ${venue}, ${year}.${doi}`:`${author} (${year}). ${title}. ${venue}.${doi}`;
     });
     const insertion='\n\nREFERENCES — verify and format before submission\n'+entries.join('\n');
     text.value+=insertion; text.focus();text.setSelectionRange(text.value.length,text.value.length);
     status(n,`Added ${picked.length} draft bibliography entries. Verify details and style before using.`);
   };
   text.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('application/x-zresearch-reference')){e.preventDefault();e.dataTransfer.dropEffect='copy'}});
   text.addEventListener('drop',e=>{const id=e.dataTransfer.getData('application/x-zresearch-reference');if(id){e.preventDefault();insertCitation(n,id)}});
 }

 async function refreshWritingContext(){
   if(!state.auth?.authenticated)return;
   [refs,guides,runs,history]=await Promise.all([
     api('/api/v05/references'),api('/api/v05/references/guides'),api('/api/v05/analyses'),api('/api/v05/chapters')
   ]);
   for(const chapter of C){
     const analysis=el('c'+chapter+'Analysis');const prev=analysis.value;
     analysis.innerHTML='<option value="">No saved analysis / placeholders</option>'+runs.filter(a=>!state.dataset||a.dataset_id===state.dataset).map(x=>`<option value="${protect(x.id)}">${protect(x.analysis_type)} · ${protect(x.created_at.slice(0,16))}</option>`).join('');
     if(runs.some(r=>r.id===prev))analysis.value=prev;
     else if(chapter===4&&state.lastAnalysis?.analysis_id&&runs.some(r=>r.id===state.lastAnalysis.analysis_id))analysis.value=state.lastAnalysis.analysis_id;
     const guide=el('c'+chapter+'Guide'),old=guide.value;
     guide.innerHTML='<option value="">No attached guide</option>'+guides.filter(g=>g.kind!=='news_upload').map(g=>`<option value="${protect(g.id)}">${protect(g.filename)}</option>`).join('');
     if(guides.some(g=>g.id===old))guide.value=old;
     // New references are selectable in the current chapter, but are not silently used by the writer.
     const alive=new Set(refs.map(x=>x.id));
     for(const id of chosen[chapter])if(!alive.has(id))chosen[chapter].delete(id);
     persistSelection(chapter);
     renderReferencePicker(chapter);
     const historyEl=el('c'+chapter+'History'),oldHistory=historyEl.value;
     historyEl.innerHTML='<option value="">Previous drafts for Chapter '+chapter+'</option>'+history.filter(h=>h.chapter===chapter).map(h=>`<option value="${protect(h.id)}">${protect(h.created_at.slice(0,16))} · ${protect(h.excerpt||'')}</option>`).join('');
     if(history.some(h=>h.id===oldHistory))historyEl.value=oldHistory;
   }
 }
 async function loadLiterature(){
   const root=el('litMatrix');
   if(!refs.length){root.innerHTML='<p class="hint">No publications in the shared library. Search OpenAlex and/or upload papers first.</p>';return}
   root.innerHTML='<table><thead><tr><th>Reference</th><th>Year</th><th>DOI</th><th>Evidence status</th></tr></thead><tbody>'+refs.map(r=>`<tr><td>${protect(r.title)}</td><td>${protect(r.year||'—')}</td><td>${protect(r.doi||'—')}</td><td>Bibliographic metadata · ${protect(r.scopus_status)}</td></tr>`).join('')+'</tbody></table><p class="hint">Metadata do not verify findings. Check original article text before writing a synthesis.</p>';
 }
 const savedIds={};
 function requestChapter(n){return {chapter:n,dataset_id:state.dataset||null,analysis_id:el('c'+n+'Analysis').value||null,guide_id:el('c'+n+'Guide').value||null,...stylePayload(),model_spec:(state.model.nodes.length?{nodes:state.model.nodes,edges:state.model.edges}:null),research_facts:el('c'+n+'Facts').value,instructions:el('c'+n+'Instructions').value,reference_ids:[...chosen[n]]};}
 function status(n,m){el('c'+n+'Status').textContent=m;}
 async function copyTextSafe(text){try{await navigator.clipboard.writeText(text);toast('Copied')}catch(e){toast('Clipboard blocked. Select and copy text manually.')}}
 for(const n of C){
   el('c'+n+'OpenReferences').onclick=()=>switchPage('references');
   el('c'+n+'Upload').onclick=async()=>{
     const file=el('c'+n+'RefUpload').files[0];if(!file){toast('Select a reference file first');return}
     const data=new FormData();data.append('file',file);
     try{const result=await api('/api/v05/references/upload',{method:'POST',body:data});el('c'+n+'RefStatus').textContent=`Attached ${result.filename}. Bibliographic facts remain unverified; parsed entries: ${result.imported_references}.`;await refreshWritingContext();if(n===2)await loadLiterature()}
     catch(e){el('c'+n+'RefStatus').textContent=e.message;toast(e.message)}
   };
   el('c'+n+'Preview').onclick=async()=>{
     try{if(!state.auth?.authenticated)throw Error('Log into the local account first');let p=await jsonPost('/api/v05/chapters/preview',requestChapter(n));
       el('fullPrompt').value='SYSTEM:\n'+p.system+'\n\nUSER:\n'+p.prompt;el('promptDialog').showModal();}
     catch(e){toast(e.message)}
   };
   el('c'+n+'Generate').onclick=async()=>{
     if(!state.auth?.authenticated){switchPage('settings');toast('Log into local account first');return}
     if(!state.auth.provider_connected){switchPage('settings');toast('Connect Ollama locally or a cloud AI provider first');return}
     const btn=el('c'+n+'Generate');btn.disabled=true;status(n,`Generating Chapter ${n} with ${state.auth.provider_label}… Ollama may need up to 60 minutes.`);
     try{const result=await jsonPost('/api/v05/chapters/generate',requestChapter(n));savedIds[n]=result.id;
       el('c'+n+'Text').value=result.body;status(n,'Draft generated and saved. Verify methods, estimates, literature and news claims before use.');
       await refreshWritingContext();toast('Chapter '+n+' draft created');}
     catch(e){status(n,e.message);toast(e.message)}finally{btn.disabled=false}
   };
   el('c'+n+'Save').onclick=async()=>{
     const body=el('c'+n+'Text').value;if(body.trim().length<5){toast('Write or generate chapter text first');return}
     try{
       const existing=savedIds[n];const result=existing?
         await api('/api/v05/chapters/'+encodeURIComponent(existing),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({body})}):
         await jsonPost('/api/v05/chapters/save-edited',{chapter:n,dataset_id:state.dataset||null,body});
       savedIds[n]=result.id;status(n,'✓ Current edited draft saved in local chapter history.');await refreshWritingContext();toast('Chapter saved')}
     catch(e){status(n,e.message);toast(e.message)}
   };
   el('c'+n+'Load').onclick=async()=>{
     const id=el('c'+n+'History').value;if(!id){toast('Select saved draft');return}
     try{const c=await api('/api/v05/chapters/'+encodeURIComponent(id));el('c'+n+'Text').value=c.body;savedIds[n]=id;status(n,'Loaded previously saved chapter; edits can be saved.')}catch(e){toast(e.message)}
   };
   el('c'+n+'Copy').onclick=()=>copyTextSafe(el('c'+n+'Text').value);
   el('c'+n+'Markdown').onclick=()=>{if(!el('c'+n+'Text').value.trim()){toast('No chapter text');return}downloadFile('Z_Research_Chapter_'+n+'.md',el('c'+n+'Text').value,'text/markdown')};
   el('c'+n+'Word').onclick=async()=>{
     const body=el('c'+n+'Text').value;if(body.trim().length<5){toast('No chapter text');return}
     try{
       const r=await fetch('/api/v05/chapters/export-word',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({chapter:n,body})});
       if(!r.ok){const d=await r.json();throw Error(d.detail||'Export error')}
       const u=URL.createObjectURL(await r.blob()),a=document.createElement('a');a.href=u;a.download=`Z_Research_Chapter_${n}.docx`;a.click();setTimeout(()=>URL.revokeObjectURL(u),3000);
       toast('Chapter '+n+' exported to Word');
     }catch(e){toast(e.message)}
   };
 }
 el('openLiteratureStudio').onclick=()=>switchPage('literature');
 el('litRefreshMatrix').onclick=async()=>{try{await refreshWritingContext();await loadLiterature()}catch(e){toast(e.message)}};
 // Dataset variable names generate exploratory questions and searches, not 'facts'.
 el('phenomenaFind').onclick=async()=>{
   if(!state.dataset){toast('Upload or choose a dataset from Dashboard first');return}
   if(!state.auth?.authenticated){toast('Log into local account first');return}
   el('phenomenaStatus').textContent='Inspecting dataset column names…';
   try{
     const payload=await api('/api/v05/phenomena/suggestions?dataset_id='+encodeURIComponent(state.dataset));
     el('phenomenaStatus').textContent=payload.warning;
     el('phenomenaIdeas').innerHTML=(payload.themes||[]).map(t=>`<div class="zr-theme"><b>${protect(t.theme)}</b><small>Variables: ${protect(t.variables.join(', '))}</small><div class="buttonrow"><button class="btn light" data-news-query="${protect(t.news_query)}">Find related news ↗</button><button class="btn light" data-chapter-idea="${protect(t.theme)}">Add to Chapter 1 context</button></div></div>`).join('')||'<p class="hint">No numeric variables found.</p>';
     el('phenomenaIdeas').querySelectorAll('[data-news-query]').forEach(b=>b.onclick=()=>{el('newsQuery').value=b.dataset.newsQuery;el('newsSearch').click()});
     el('phenomenaIdeas').querySelectorAll('[data-chapter-idea]').forEach(b=>b.onclick=()=>{el('c1Facts').value+=(el('c1Facts').value?'\n':'')+'Exploratory question requiring confirmation: '+b.dataset.chapterIdea;toast('Exploratory theme added to Chapter 1 context')});
   }catch(e){el('phenomenaStatus').textContent=e.message;toast(e.message)}
 };
 function openNews(){const query=el('newsQuery').value.trim();if(!query){toast('Enter keywords first');return}window.open('https://news.google.com/search?q='+encodeURIComponent(query),'_blank','noopener,noreferrer')}
 el('newsBrowser').onclick=openNews;
 el('newsSearch').onclick=async()=>{
   const q=el('newsQuery').value.trim();if(!q){toast('Enter a news search phrase');return}
   el('newsSearchResults').textContent='Searching news leads…';
   try{const o=await jsonPost('/api/v05/news/search',{query:q});
     el('newsSearchResults').innerHTML=o.results.length?o.results.slice(0,12).map(x=>`<div class="zr-ref-entry"><b>${protect(x.title)}</b><small>${protect(x.source)} · ${protect(x.published)}</small><div class="buttonrow"><a href="${protect(x.url)}" class="btn light" target="_blank" rel="noopener noreferrer">Read source ↗</a><button class="btn light" data-news-add="${protect(x.url)}" data-news-title="${protect(x.title)}" data-news-source="${protect(x.source)}" data-news-date="${protect(x.published)}">Use as evidence lead</button></div></div>`).join(''):'No results from RSS; try opening Google News directly.';
     el('newsSearchResults').querySelectorAll('[data-news-add]').forEach(b=>b.onclick=()=>{el('newsUrl').value=b.dataset.newsAdd;el('newsTitle').value=b.dataset.newsTitle;el('newsSource').value=b.dataset.newsSource;el('newsDate').value=b.dataset.newsDate;el('newsEvidenceFold').open=true;toast('News lead copied to evidence form. Verify original before saving.')});
   }catch(e){el('newsSearchResults').textContent=e.message+' Open Google News directly if feed is unavailable.'}
 };
 async function loadNews(){news=await api('/api/v05/news');const newsUploads=await api('/api/v05/news/uploads');el('newsLibrary').innerHTML=news.length?news.map(x=>`<div class="zr-ref-entry"><b>${protect(x.title)}</b><small>${protect(x.source)} · ${protect(x.published)} · ${protect(x.notes)}</small><div class="buttonrow"><a href="${protect(x.url)}" rel="noopener noreferrer" target="_blank" class="btn light">Open article ↗</a><button class="btn light" data-remove-news="${protect(x.id)}">Remove</button></div></div>`).join(''):'No news links saved.';
   if(newsUploads.length)el('newsLibrary').insertAdjacentHTML('beforeend','<h3>Uploaded article files</h3>'+newsUploads.map(f=>`<div class="zr-ref-entry"><b>${protect(f.filename)}</b><small>Uploaded text · source publication not independently verified</small></div>`).join(''));
   el('newsLibrary').querySelectorAll('[data-remove-news]').forEach(b=>b.onclick=async()=>{try{await api('/api/v05/news/'+encodeURIComponent(b.dataset.removeNews),{method:'DELETE'});await loadNews()}catch(e){toast(e.message)}});
 }
 el('newsSave').onclick=async()=>{
   try{await jsonPost('/api/v05/news',{title:el('newsTitle').value.trim(),url:el('newsUrl').value.trim(),source:el('newsSource').value.trim(),published:el('newsDate').value.trim(),notes:el('newsNotes').value.trim()});
     await loadNews();toast('News reference saved; verify full article content before citing.');}
   catch(e){toast(e.message)}
 };
 el('newsUpload').onclick=async()=>{
   const file=el('newsFile').files[0];if(!file){toast('Choose a PDF, DOCX or TXT news article');return}
   const data=new FormData();data.append('file',file);
   try{const x=await api('/api/v05/news/upload',{method:'POST',body:data});el('newsUploadMsg').textContent=`Uploaded ${x.filename} (${x.characters} text characters). Researcher must verify source/date before citing.`;await loadNews();toast('News document attached to Chapter 1')}
   catch(e){el('newsUploadMsg').textContent=e.message;toast(e.message)}
 };
 // Explain numbers to a reader; numbers and inference remain Python-owned.
 const plsOld=v5RenderPLS;
 v5RenderPLS=function(payload){plsOld(payload);const r=payload.result;
   const num=(v)=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(3):'not reported';
   let h='<h2>Interpretation of this model</h2><p class="hint">Experimental PLS-SEM: these values are associations in the uploaded sample. They are not proof of causality or population representativeness.</p>';
   h+=`<p><b>Analytical sample:</b> ${protect(r.n)} complete observations used; ${protect(r.excluded_rows)} rows excluded. These are not verified unique respondents.</p>`;
   const sorted=Object.entries(r.r_squared||{});
   if(sorted.length)h+='<h3>Explanatory power (R²)</h3><ul>'+sorted.map(([k,v])=>`<li>${protect(k)}: R² = <b>${num(v)}</b>, describing approximately ${typeof v==='number'?(100*v).toFixed(1):'unknown'}% sample variation accounted for by its modeled predictors. This is descriptive explanatory power, not model validity.</li>`).join('')+'</ul>';
   const paths=Object.entries(r.paths||{});
   if(paths.length)h+='<h3>Modeled relationships</h3><ul>'+paths.map(([k,v])=>{const b=r.bootstrap?.[k]||{};const interval=Array.isArray(b.ci95)?b.ci95:null;
     const ciMessage=interval&&interval.length===2?` Bootstrap 95% interval [${num(interval[0])}, ${num(interval[1])}]${interval[0]>0||interval[1]<0?' does not cross 0.':' crosses/includes 0.'}`:' Bootstrap interval unavailable or incomplete.';
     return `<li><b>${protect(k)}:</b> β = ${num(v)} (${v>0?'positive':v<0?'negative':'zero'} sample association).${protect(ciMessage)}</li>`;
   }).join('')+'</ul>';
   h+='<p class="hint">A path coefficient does not describe how much real-world behavior changes without considering units, measurement quality and study design. Check loadings, alpha, CR, AVE, HTMT and VIF in the tables above. Claims of significance require reliable bootstrap procedures and sufficient replications.</p>';
   el('semInterpretation').innerHTML=h;
 };
 // Supplementary descriptive / OLS / reliability stay within SEM-PLS rather than separate menu.
 const oldStats=el('runStats').onclick;
 el('runStats').onclick=async function(...args){
   await oldStats.apply(this,args);
   const type=state.analysis;
   const interpretation={descriptive:'Descriptives summarize numeric input distributions for observed variables. Mean and standard deviation alone do not establish measurement validity.',regression:'OLS coefficients reflect conditional sample associations in a linear regression, with assumptions about functional form and residuals that must be checked.',reliability:'Cronbach alpha describes internal consistency of a selected indicator set, not automatically construct validity or one-dimensionality.'};
   el('statsExplanation').textContent=interpretation[type]||'Interpret numerical outputs according to study design and measurement level.';
 };
 const out=el('statOutput');
 const p=document.createElement('p');p.id='statsExplanation';p.className='hint';p.textContent='Select a supplementary analysis to read its interpretation.';out.parentNode.append(p);
 // Existing target from v0.5.2 should jump to new Findings Writer instead of hidden Chapter Studio.
 el('openChapter4').onclick=()=>switchPage('results');
 el('goPLS').onclick=()=>switchPage('pls');
 el('goAIResults').onclick=()=>switchPage('results');
 // First auth refresh is asynchronous; this is safe and optional.
 if(state.auth?.authenticated)refreshWritingContext().catch(()=>{});
})();
