'use strict';
/* Brand asset is the user's existing logo. Keep old mark until exact image is uploaded. */
(function(){
 const img=document.getElementById('customBrandLogo');
 const chooser=document.getElementById('brandLogoFile');
 const status=document.getElementById('brandLogoStatus');
 const button=document.getElementById('brandLogoUpload');
 function showLogo(){
   const probe=new Image();const src='/api/v05/branding/logo?view='+Date.now();
   probe.onload=()=>{img.src=src;img.hidden=false};
   probe.onerror=()=>{img.hidden=true};
   probe.src=src;
 }
 showLogo();
 button?.addEventListener('click',async()=>{
   const file=chooser?.files?.[0];if(!file){status.textContent='Select your original logo image first.';return}
   button.disabled=true;status.textContent='Uploading logo…';
   try{
     const data=new FormData();data.append('file',file);
     const r=await api('/api/v05/branding/logo',{method:'POST',body:data});
     status.textContent='✓ Original logo saved; sidebar updated.';
     showLogo();toast('Logo Z-Research updated');
   }catch(e){status.textContent=e.message;toast(e.message)}finally{button.disabled=false}
 });
})();
