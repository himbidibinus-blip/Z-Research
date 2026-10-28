'use strict';
/* Z-Research v0.5 extension. Reuses v0.2 auth, dataset and SVG builder state. */
const pl5=id=>document.getElementById(id);
const v5Esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const v5num=n=>typeof n==='number'?Number(n.toPrecision(5)).toString():n==null?'—':String(n);
function v5Table(rows,cols){if(!rows?.length)return '<p class="hint">No eligible results.</p>';return '<div class="tablewrap"><table><thead><tr>'+cols.map(c=>`<th>${v5Esc(c[1])}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+cols.map(c=>`<td>${v5Esc(v5num(r[c[0]]))}</td>`).join('')+'</tr>').join('')+'</tbody></table></div>'}
function v5Pair(o){return Object.entries(o||{}).map(([k,v])=>({term:k,value:typeof v==='object'?JSON.stringify(v):v}));}
function v5RefreshSummary(){let n=state.model.nodes;pl5('plsModelSummary').textContent=`${n.length} constructs · ${state.model.edges.length} paths · ${n.reduce((s,x)=>s+(x.indicators||[]).length,0)} mapped indicators. Active dataset: ${state.data?.name||'none'}.`}
function v5Switch(page){switchPage(page);if(page==='pls')v5RefreshSummary();if(page==='references'){v5LoadRefs().catch(e=>toast(e.message));v5LoadGuides().catch(e=>toast(e.message))}if(page==='chapters'){v5LoadRuns().catch(e=>toast(e.message));v5LoadGuides().catch(e=>toast(e.message));v5LoadChapters().catch(e=>toast(e.message))}}
document.querySelectorAll('[data-page="pls"],[data-page="references"],[data-page="chapters"]').forEach(x=>x.addEventListener('click',()=>{const title={pls:'PLS-SEM Lab',references:'Reference Library',chapters:'Chapter 3 & 4 Studio'};pl5('toptitle').textContent=title[x.dataset.page]}));
pl5('goPLS').onclick=()=>v5Switch('pls');pl5('goModel').onclick=()=>v5Switch('model');pl5('openChapter4').onclick=()=>{pl5('chapterNumber').value='4';v5Switch('chapters')};
pl5('loadDemoModel').onclick=()=>{let cols=new Set(state.data?.columns||[]);let pairs=[['Social Media Marketing',['social_media_1','social_media_2','social_media_3']],['Brand Trust',['trust_1','trust_2','trust_3']],['Purchase Intention',['purchase_intention']]];if(!pairs.every(([,arr])=>arr.every(c=>cols.has(c)))){toast('Sample model requires social_media_1–3, trust_1–3, purchase_intention');return}state.model.nodes=pairs.map(([label,indicators],i)=>({id:'demo_'+i,label,type:'latent',measurement:'reflective',x:195+i*305,y:i===1?145:300,indicators}));state.model.edges=[{source:'demo_0',target:'demo_1',label:'H1'},{source:'demo_1',target:'demo_2',label:'H2'},{source:'demo_0',target:'demo_2',label:'H3'}];state.selected=null;drawModel();toast('Demo model loaded. Click Estimate current model.')};
function v5RenderPLS(a){let r=a.result;let html='<div class="pls-results"><div class="pls-metrics">'+[['Sample N',r.n],['Excluded',r.excluded_rows],['PLS iterations',r.iterations],['Bootstrap success',r.bootstraps_successful]].map(t=>`<div class="pls-metric"><strong>${v5Esc(v5num(t[1]))}</strong><small>${t[0]}</small></div>`).join('')+'</div>';
const paths=Object.entries(r.paths).map(([name,estimate])=>({path:name,estimate,...(r.bootstrap[name]||{})}));
html+='<h3>Research hypotheses</h3>'+v5Table(r.hypotheses||[],[['hypothesis','Hypothesis'],['kind','Type'],['path','Path'],['estimate','β'],['p_approx','Approx. p'],['ci95','CI 95%']]);
html+='<h3>Structural paths and bootstrap</h3>'+v5Table(paths,[['path','Hypothesis / path'],['estimate','β'],['bootstrap_se','SE'],['t_approx','Approx. t'],['p_approx','Approx. p'],['ci95','95% percentile CI'],['supported_at_5pct','CI excludes 0']]);
html+='<h3>R² and f²</h3>'+v5Table(v5Pair(r.r_squared),[['term','Endogenous construct'],['value','R²']])+v5Table(v5Pair(r.f_squared),[['term','Path'],['value','f²']]);
html+='<h3>Outer loadings and weights</h3>'+v5Table(r.outer_model,[['construct','Construct'],['indicator','Indicator'],['loading','Loading'],['weight','Weight'],['measurement','Mode']]);
html+='<h3>Reliability and convergent validity (reflective)</h3>'+v5Table(Object.entries(r.reliability_validity).map(([name,v])=>({name,...v})),[['name','Construct'],['alpha','Cronbach α'],['composite_reliability','CR'],['ave','AVE'],['single_item','Single item']]);
html+='<h3>HTMT and Fornell–Larcker</h3>'+v5Table(v5Pair(r.htmt),[['term','Pair'],['value','HTMT']])+v5Table(Object.entries(r.fornell_larcker).map(([name,v])=>({name,...v})),[['name','Pair'],['correlation','Latent corr'],['sqrt_ave_a','sqrt AVE A'],['sqrt_ave_b','sqrt AVE B']]);
html+='<h3>Inner model VIF (predictor collinearity)</h3>'+v5Table(v5Pair(r.inner_vif),[['term','Predictor path'],['value','VIF']]);
html+='<h3>Cross-loadings</h3>'+v5Table(r.cross_loadings,Object.keys(r.cross_loadings?.[0]||{}).map(k=>[k,k]));
html+='<h3>Indirect effects</h3>'+v5Table(Object.entries(r.indirect_effects).map(([name,v])=>({name,...v})),[['name','Mediation chain'],['estimate','Indirect β'],['ci95','95% CI'],['supported_at_5pct','CI excludes 0']]);
if(Object.keys(r.formative_diagnostics||{}).length)html+='<h3>Formative construct VIF</h3>'+v5Table(Object.entries(r.formative_diagnostics).flatMap(([c,v])=>Object.entries(v.indicator_vif).map(([ind,vif])=>({c,ind,vif}))),[['c','Construct'],['ind','Indicator'],['vif','VIF']]);
if(Object.keys(r.formative_bootstrap||{}).length)html+='<h3>Formative weights uncertainty</h3>'+v5Table(Object.entries(r.formative_bootstrap).map(([name,v])=>({name,...v})),[['name','Indicator'],['estimate','Weight'],['ci95','95% CI']]);
html+=`<p class="hint"><b>Method:</b> ${v5Esc(r.method)}</p><p class="hint"><b>Not implemented:</b> ${v5Esc((r.limitations||[]).join(' · '))}</p>`;
html+=(a.analysis_id?`<div class="buttonrow"><a class="btn light" href="/api/analyses/${encodeURIComponent(a.analysis_id)}/export" target="_blank">Export complete JSON</a></div>`:`<p class="hint">LIVE PREVIEW · Not saved · Click Run PLS-SEM to create an exportable analysis.</p>`)+`</div>`;pl5('plsOutput').innerHTML=html;
}
pl5('runPLS').onclick=async()=>{if(!state.auth?.authenticated){toast('Log in in AI Settings first');v5Switch('settings');return}let btn=pl5('runPLS');if(!state.dataset){toast('Select/upload a dataset');return}if(state.model.nodes.length<2 || state.model.edges.length<1){toast('Draw at least 2 constructs and a path first');return}btn.disabled=true;pl5('plsStatus').textContent='Computing PLS-SEM. This can take a minute for bootstrap runs…';try{let result=await jsonPost('/api/v05/pls/run',{dataset_id:state.dataset,nodes:state.model.nodes,edges:state.model.edges,bootstraps:Number(pl5('plsBootstraps').value),seed:Number(pl5('plsSeed').value)});state.lastAnalysis={analysis_id:result.analysis_id,kind:'pls_sem'};v5RenderPLS(result);pl5('plsStatus').textContent='Analysis complete · saved locally · experimental results require external benchmarking';toast('PLS-SEM estimation complete');}catch(e){pl5('plsStatus').textContent=e.message;toast(e.message)}finally{btn.disabled=false}};
let searchRefs=[];
let savedRefIndex=new Set();
function refIdentity(r){
 const doi=String(r.doi||'').trim().toLowerCase().replace(/^https?:\/\/(dx\.)?doi\.org\//,'').replace(/\/$/,'');
 if(doi)return 'doi:'+doi;
 return 'title:'+String(r.title||'').toLowerCase().replace(/[^a-z0-9]/g,'')+':'+String(r.year||'');
}
function updateReferenceSearchButtons(){
 document.querySelectorAll('#refResults [data-ref-add]').forEach(b=>{
  const item=searchRefs[Number(b.dataset.refAdd)];const saved=item&&savedRefIndex.has(refIdentity(item));
  b.disabled=!!saved;b.classList.toggle('zr-added',!!saved);
  b.textContent=saved?'✓ Added to library':'+ Add reference';
  b.setAttribute('aria-label',saved?'Reference already in your library':'Add reference to your library');
 });
}
pl5('refSearch').onclick=async()=>{
 const btn=pl5('refSearch');btn.disabled=true;pl5('refSearchStatus').textContent='Looking up article metadata…';
 try{
  const [data,stored]=await Promise.all([jsonPost('/api/v05/references/search',{query:pl5('refQuery').value.trim(),from_year:Number(pl5('refYear').value),count:15}),api('/api/v05/references')]);
  searchRefs=data.results;savedRefIndex=new Set(stored.map(refIdentity));
  pl5('refSearchStatus').textContent=`${searchRefs.length} works found · ${stored.length} already saved · indexing unverified`;
  pl5('refResults').innerHTML=searchRefs.map((a,i)=>`<div class="reftile zr-search-ref"><div class="zr-ref-copy"><b>${v5Esc(a.title)}</b><small>${v5Esc(a.authors)} · ${v5Esc(a.year)} · ${v5Esc(a.venue)}</small><small>DOI: ${v5Esc(a.doi||'not provided')} · <span class="pill-notverified">INDEXING NOT VERIFIED</span></small></div><button class="btn light" data-ref-add="${i}">+ Add reference</button></div>`).join('');
  updateReferenceSearchButtons();
  pl5('refResults').querySelectorAll('[data-ref-add]').forEach(b=>b.onclick=async()=>{
   if(b.disabled)return;const record=searchRefs[Number(b.dataset.refAdd)];
   b.disabled=true;b.textContent='Saving…';
   try{const outcome=await jsonPost('/api/v05/references/manual',{...record,origin:'openalex'});
    savedRefIndex.add(refIdentity(record));updateReferenceSearchButtons();
    toast(outcome.already_saved?'Already in your library':'✓ Reference saved');await v5LoadRefs();
   }catch(e){toast(e.message);b.disabled=false;updateReferenceSearchButtons()}
  });
 }catch(e){pl5('refSearchStatus').textContent=e.message;toast(e.message)}finally{btn.disabled=false}
};
async function v5LoadRefs(){
 const all=await api('/api/v05/references');savedRefIndex=new Set(all.map(refIdentity));updateReferenceSearchButtons();
 pl5('refLibrary').innerHTML=all.length?all.map(a=>`<div class="reftile zr-library-ref"><div class="zr-ref-copy"><b>${v5Esc(a.title)}</b><small>${v5Esc(a.authors)} (${v5Esc(a.year||'n.d.')}). ${v5Esc(a.venue)}.</small><small>DOI ${v5Esc(a.doi||'none')} · <span class="pill-notverified">${v5Esc(a.scopus_status)}</span></small></div><button class="btn light" data-rmref="${v5Esc(a.id)}">Remove</button></div>`).join(''):'No saved references yet.';
 pl5('refLibrary').querySelectorAll('[data-rmref]').forEach(b=>b.onclick=async()=>{
  await api('/api/v05/references/'+encodeURIComponent(b.dataset.rmref),{method:'DELETE'});
  await v5LoadRefs();toast('Reference removed');
 });
}
pl5('refUpload').onclick=async()=>{let f=pl5('refFile').files[0];if(!f){toast('Choose a reference file first');return}let d=new FormData();d.append('file',f);pl5('refUploadStatus').textContent='Extracting reference text…';try{let r=await api('/api/v05/references/upload',{method:'POST',body:d});pl5('refUploadStatus').textContent=`Saved ${r.filename} (${r.text_chars} text characters). DOI candidate: ${r.possible_doi||'none'}.`;await v5LoadGuides();toast('Reference reading guide uploaded')}catch(e){pl5('refUploadStatus').textContent=e.message;toast(e.message)}};
async function v5LoadGuides(){let guides=await api('/api/v05/references/guides');let old=pl5('chapterGuide').value;pl5('chapterGuide').innerHTML='<option value="">No reference file</option>'+guides.map(g=>`<option value="${v5Esc(g.id)}">${v5Esc(g.filename)}</option>`).join('');if(guides.some(x=>x.id===old))pl5('chapterGuide').value=old}
pl5('scopusVerify').onclick=async()=>{pl5('scopusResult').textContent='Checking serial-title API…';try{let x=await jsonPost('/api/v05/references/verify-scopus',{issn:pl5('scopusIssn').value,elsevier_api_key:pl5('scopusApiKey').value});pl5('scopusApiKey').value='';pl5('scopusResult').textContent=JSON.stringify(x,null,2)}catch(e){pl5('scopusResult').textContent=e.message}};
async function v5LoadRuns(){let x=await api('/api/v05/analyses');let old=pl5('chapterAnalysis').value;pl5('chapterAnalysis').innerHTML='<option value="">No analysis / placeholders</option>'+x.filter(a=>!state.dataset||a.dataset_id===state.dataset).map(a=>`<option value="${v5Esc(a.id)}">${v5Esc(a.analysis_type)} · ${v5Esc(a.created_at.slice(0,16))}</option>`).join('');let newAid=state.lastAnalysis?.analysis_id;if(x.some(a=>a.id===newAid))pl5('chapterAnalysis').value=newAid;else if(x.some(a=>a.id===old))pl5('chapterAnalysis').value=old}
function v5ChapterReq(){return {chapter:Number(pl5('chapterNumber').value),dataset_id:state.dataset||null,analysis_id:pl5('chapterAnalysis').value||null,guide_id:pl5('chapterGuide').value||null,...stylePayload(),research_facts:pl5('chapterFacts').value,instructions:pl5('chapterInstruction').value}}
pl5('chapterPreview').onclick=async()=>{if(!state.auth?.authenticated){toast('Log in first');return}try{let p=await jsonPost('/api/v05/chapters/preview',v5ChapterReq());pl5('fullPrompt').value='SYSTEM:\n'+p.system+'\n\nUSER:\n'+p.prompt;pl5('promptDialog').showModal()}catch(e){toast(e.message)}};
let savedChapterId='';
pl5('chapterGenerate').onclick=async()=>{if(!state.auth?.authenticated){toast('Log in first');v5Switch('settings');return}if(!state.auth.provider_connected){toast('Connect OpenAI API in Settings first');v5Switch('settings');return}let btn=pl5('chapterGenerate');btn.disabled=true;pl5('chapterStatus').textContent='Generating draft using connected AI…';try{let x=await jsonPost('/api/v05/chapters/generate',v5ChapterReq());savedChapterId=x.id;pl5('chapterText').value=x.body;pl5('chapterStatus').textContent='Draft saved · verify all claims and references';await v5LoadChapters();toast('Chapter draft generated')}catch(e){pl5('chapterStatus').textContent=e.message;toast(e.message)}finally{btn.disabled=false}};
pl5('chapterCopy').onclick=async()=>{try{await navigator.clipboard.writeText(pl5('chapterText').value);toast('Copied')}catch(e){toast('Select and copy text manually')}};
pl5('chapterMarkdown').onclick=()=>{if(!pl5('chapterText').value){toast('No content');return}downloadFile(`Chapter_${pl5('chapterNumber').value}.md`,pl5('chapterText').value,'text/markdown')};
pl5('chapterDocx').onclick=async()=>{let text=pl5('chapterText').value;if(!text){toast('Write or generate a chapter first');return}try{let r=await fetch('/api/v05/chapters/export-word',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({chapter:Number(pl5('chapterNumber').value),body:text})});if(!r.ok){let d=await r.json();throw Error(d.detail||'Export failed')}let url=URL.createObjectURL(await r.blob()),a=document.createElement('a');a.href=url;a.download=`Z_Research_Chapter_${pl5('chapterNumber').value}.docx`;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);toast('Word file exported with your latest edits')}catch(e){toast(e.message)}};
async function v5LoadChapters(){let x=await api('/api/v05/chapters');pl5('chapterHistory').innerHTML='<option value="">Select saved draft</option>'+x.map(a=>`<option value="${v5Esc(a.id)}">Chapter ${a.chapter} · ${v5Esc(a.created_at.slice(0,16))}</option>`).join('')}
pl5('chapterLoad').onclick=async()=>{try{let id=pl5('chapterHistory').value;if(!id)throw Error('Choose chapter first');let d=await api('/api/v05/chapters/'+encodeURIComponent(id));pl5('chapterText').value=d.body;savedChapterId=id;pl5('chapterNumber').value=d.chapter;toast('Draft loaded')}catch(e){toast(e.message)}};

pl5('scopusArticleSearch').onclick=async()=>{pl5('scopusArticleResults').textContent='Searching authorized Scopus API…';try{let r=await jsonPost('/api/v05/references/search-scopus',{query:pl5('scopusQuery').value.trim(),elsevier_api_key:pl5('scopusApiKey').value,count:10});pl5('scopusArticleResults').innerHTML=r.results.map((a,i)=>`<div class="reftile"><b>${v5Esc(a.title)}</b><small>${v5Esc(a.authors)} · ${v5Esc(a.year)} · ${v5Esc(a.venue)}</small><small>DOI ${v5Esc(a.doi||'not available')} · Scopus API record ${v5Esc(a.scopus_id)}</small></div>`).join('')||'No records returned';pl5('scopusApiKey').value='';toast('Scopus search complete. Add references manually after verifying metadata.')}catch(e){pl5('scopusArticleResults').textContent=e.message;toast(e.message)}};

pl5('generateBothChapters').onclick=async()=>{
 if(!state.auth?.authenticated||!state.auth.provider_connected){toast('Log in and connect OpenAI first');v5Switch('settings');return}
 if(!confirm('Generate Chapter 3 and Chapter 4 in two separate paid API requests? Chapter 4 needs an actual analysis for findings.'))return;
 let btn=pl5('generateBothChapters');btn.disabled=true;let generated=[];const original=pl5('chapterNumber').value;
 try{for(let n of [3,4]){pl5('chapterStatus').textContent=`Generating Chapter ${n} of 4…`;let input=v5ChapterReq();input.chapter=n;const result=await jsonPost('/api/v05/chapters/generate',input);generated.push(result);pl5('chapterNumber').value=String(n);pl5('chapterText').value=result.body;savedChapterId=result.id;}await v5LoadChapters();toast('Chapter 3 and Chapter 4 drafts saved. Review all claims and citations.');pl5('chapterStatus').textContent='Both drafts generated; choose each in Previous chapters.'}
 catch(e){pl5('chapterStatus').textContent=`Generated ${generated.length} chapter(s). ${e.message}`;toast(e.message);pl5('chapterNumber').value=original;}finally{btn.disabled=false}
};
