'use strict';
/* Z-Research UI enhancements layered on the original MVP API and analysis functions. */
(function(){
 const byId=id=>document.getElementById(id);
 const clean=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const navigate=page=>{if(['pls','references','chapters'].includes(page)&&typeof v5Switch==='function')v5Switch(page);else switchPage(page);};
 document.querySelectorAll('[data-jump]').forEach(el=>el.addEventListener('click',()=>navigate(el.dataset.jump)));
 const btn=byId('loadSampleBtn');
 if(btn)btn.addEventListener('click',async()=>{
   const old=btn.textContent;btn.disabled=true;btn.textContent='Loading sample…';
   try{
     const res=await fetch('/static/sample_survey.csv');
     if(!res.ok)throw Error('Demo file unavailable');
     const blob=await res.blob();const form=new FormData();form.append('file',new File([blob],'Z_Research_Demo_Survey.csv',{type:'text/csv'}));
     const result=await api('/api/datasets',{method:'POST',body:form});
     await refreshDatasets();state.dataset=result.id;byId('datasetSelect').value=result.id;await loadPreview();
     byId('uploadStatus').textContent='Demo survey loaded: '+result.rows+' synthetic observations. Not real respondents.';
     toast('Demo data ready. Try the Model Builder and PLS-SEM Lab.');
   }catch(e){toast(e.message)}finally{btn.disabled=false;btn.textContent=old}
 });
 function updateModelPreview(){
   const nodes=state.model.nodes,edges=state.model.edges, m=byId('metricModels'),caption=byId('dashboardModelCaption'),svg=byId('dashboardModelSvg');
   if(m)m.textContent=nodes.length;
   if(!svg||!caption)return;
   if(nodes.length===0){caption.textContent='Example model · not computed results';return}
   caption.textContent=nodes.length+' constructs · '+edges.length+' structural paths · current model';
   const width=560,height=225;
   const xs=nodes.map(n=>n.x), ys=nodes.map(n=>n.y);let minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
   const positions=new Map(nodes.map((n,i)=>[n.id,{x:75+(maxX===minX?i/(Math.max(1,nodes.length-1)):(n.x-minX)/(maxX-minX))*410,y:58+(maxY===minY?0.5:(n.y-minY)/(maxY-minY))*115,label:n.label}]));
   const connections=edges.map(e=>{const a=positions.get(e.source),b=positions.get(e.target);if(!a||!b)return '';const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy)||1,x1=a.x+dx*36/len,y1=a.y+dy*36/len,x2=b.x-dx*39/len,y2=b.y-dy*39/len;return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="#7c87c8" stroke-width="2" fill="none" marker-end="url(#dasharrow)"/><text x="${(x1+x2)/2}" y="${(y1+y2)/2-8}" font-size="11" fill="#665caa" font-weight="700" text-anchor="middle">${clean(e.label||'')}</text>`}).join('');
   const circles=nodes.map(n=>{let p=positions.get(n.id);return `<circle cx="${p.x}" cy="${p.y}" r="37" fill="#e9eaff" stroke="#766aea" stroke-width="2"/><text x="${p.x}" y="${p.y+3}" font-size="11" fill="#283775" text-anchor="middle" font-weight="750">${clean((p.label||'').slice(0,12))}</text>`}).join('');
   svg.innerHTML='<defs><marker id="dasharrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="#6477c4"/></marker></defs>'+connections+circles;
 }
 const previousDraw=drawModel;
 drawModel=function(...args){const output=previousDraw(...args);updateModelPreview();return output};
 document.querySelectorAll('.navitem').forEach(item=>item.addEventListener('click',()=>{if(item.dataset.page==='overview')updateModelPreview()}));
 const oldRefresh=refreshDatasets;
 refreshDatasets=async function(...args){const output=await oldRefresh(...args);updateModelPreview();return output};
 updateModelPreview();
})();
