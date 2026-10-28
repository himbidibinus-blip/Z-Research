/* Z-Research local citation formatter: intentionally limited to APA in-text and IEEE numeric.
   Parse author strings conservatively; CSL-level edge cases still require human review. */
(function(root,factory){const exported=factory();if(typeof module==='object'&&module.exports)module.exports=exported;root.ZRCitation=exported;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const clean=x=>String(x??'').trim();
function parseAuthors(raw){
  let t=clean(raw);
  if(!t)return [];
  const byName=t.split(/\s*;\s*|\s+and\s+/i).map(clean).filter(Boolean);
  let names=byName;
  if(names.length===1){
    if(/^\{[^{}]+\}$/.test(t))return [{family:t.slice(1,-1),given:'',organization:true}];
    let segments=t.split(/\s*,\s*/).filter(Boolean);
    if(segments.length>=4 && segments.length%2===0 && segments.every(Boolean)){
      names=[];for(let i=0;i<segments.length;i+=2)names.push(segments[i]+', '+segments[i+1]);
    } else if(segments.length===2){
      // Two single tokens typically indicate BibTeX-style "Surname, Given".
      // Multiple words in both segments suggest OpenAlex full names "John Smith, Jane Doe".
      names=(segments[0].split(/\s+/).length>=2 && segments[1].split(/\s+/).length>=2)?segments:[t];
    } else if(segments.length>=3){names=segments;}
  }
  return names.map(name=>{
    name=clean(name);if(/^\{[^{}]+\}$/.test(name))return {family:name.slice(1,-1),given:'',organization:true};
    if(!name.includes(',') && /^(?:World |United |European |American |International )/.test(name)&&/(Organization|Association|Institute|Commission|University|Nations|Bank|Council)$/i.test(name))return {family:name,given:'',organization:true};
    if(name.includes(',')){const a=name.split(/\s*,\s*/);return {family:clean(a[0]),given:clean(a.slice(1).join(' '))};}
    const parts=name.split(/\s+/);if(parts.length===1)return {family:name,given:''};
    let family=parts.pop();while(parts.length && /^(de|del|da|di|van|von|der|la|le|bin|al)$/i.test(parts[parts.length-1]))family=parts.pop()+' '+family;
    return {family,given:parts.join(' ')};
  });
}
function authorNames(ref){
  if(Array.isArray(ref.author_parts) && ref.author_parts.length)return ref.author_parts;
  return parseAuthors(ref.authors);
}
function citeAPA(ref){
  const authors=authorNames(ref).map(a=>a.family).filter(Boolean);
  const year=ref.year||'n.d.';
  if(!authors.length)return `(${clean(ref.title).slice(0,45)||'Unknown'}, ${year})`;
  let text=authors[0];if(authors.length===2)text+=` & ${authors[1]}`;else if(authors.length>2)text+=' et al.';
  return `(${text}, ${year})`;
}
function ieeeNumber(ref,order){const i=order.indexOf(ref.id);if(i<0)throw new Error('Reference must be selected before citation');return `[${i+1}]`;}
function cite(ref,style,order=[]){return style==='ieee'?ieeeNumber(ref,order):citeAPA(ref);}
function initials(given){return given.split(/[\s-]+/).filter(Boolean).map(x=>x[0].toUpperCase()+'.').join(' ');}
function bibliography(ref,style,order=[]){
  const names=authorNames(ref).map(a=>a.organization?a.family:style==='ieee'?[initials(a.given),a.family].filter(Boolean).join(' '):[a.family,initials(a.given)].filter(Boolean).join(', '));
  const url=clean(ref.doi)?'https://doi.org/'+clean(ref.doi).replace(/^https?:\/\/(?:dx\.)?doi\.org\//i,''):clean(ref.url);
  if(style==='ieee')return `${ieeeNumber(ref,order)} ${names.join(', ')||'Unknown author'}, "${clean(ref.title)}," ${clean(ref.venue)}, ${ref.year||'n.d.'}. ${url}`.trim();
  return `${names.join(', ')||'Unknown author'} (${ref.year||'n.d.'}). ${clean(ref.title)}. ${clean(ref.venue)}. ${url}`.trim();
}
const TOKEN=/\[@ref:([A-Za-z0-9_-]{1,128})\]/g;
const BIBLIO='[@bibliography]';
function token(id){if(!/^[A-Za-z0-9_-]{1,128}$/.test(String(id)))throw new Error('Invalid reference ID');return `[@ref:${id}]`;}
function citedIds(body){return [...new Set([...String(body||'').matchAll(TOKEN)].map(m=>m[1]))];}
function renderDocument(body,style,refs=[]){
  const source=String(body||'');
  const list=citedIds(source); // first occurrence, never checkbox insertion order
  const positions=new Map(list.map((id,i)=>[id,i+1]));
  const byId=new Map(refs.map(ref=>[ref.id,ref]));
  const missing=list.filter(id=>!byId.has(id));
  const unlinked=list.filter(id=>!byId.has(id));
  const rendered=source.replace(TOKEN,(_token,id)=>byId.has(id)?cite(byId.get(id),style,list):`[MISSING SOURCE: ${id}]`);
  const bibliographyText=list.filter(id=>byId.has(id)).map(id=>bibliography(byId.get(id),style,list)).join('\n');
  const text=rendered.includes(BIBLIO)?rendered.replaceAll(BIBLIO,'References\n'+bibliographyText):rendered.trimEnd()+(bibliographyText?'\n\nReferences\n'+bibliographyText:'');
  // Legacy numeric citations cannot be safely mapped from bare [n] to IDs.
  const legacyNumeric=/\[(?:\d+)(?:\s*[-,]\s*\d+)*\]/.test(source.replace(TOKEN,''));
  return {text,order:list,missing,unlinked,legacyNumeric,bibliography:bibliographyText};
}
return {parseAuthors, cite, bibliography, citeAPA,token,citedIds,renderDocument};
});
