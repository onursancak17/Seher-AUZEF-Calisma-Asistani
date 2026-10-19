"""Seher AUZEF launcher: verified study bundle + mobile full-screen PDF reader.

The original application, questions, PDF content and saved-test logic are untouched.
This launcher replaces only the PDF page UI at runtime.
"""
from __future__ import annotations

import base64
import os
import runpy
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'uygulama_paketi.zip'
RUNTIME = ROOT / '.runtime'
STAMP = RUNTIME / '.archive_stamp'

if not ARCHIVE.is_file():
    raise RuntimeError('uygulama_paketi.zip bulunamadı. GitHub deposuna yüklenmesi gerekiyor.')

current_stamp = f'{ARCHIVE.stat().st_size}:{ARCHIVE.stat().st_mtime_ns}'
if not (RUNTIME / 'app.py').is_file() or not STAMP.is_file() or STAMP.read_text() != current_stamp:
    RUNTIME.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, 'r') as bundle:
        root = RUNTIME.resolve()
        for item in bundle.infolist():
            if not (RUNTIME / item.filename).resolve().is_relative_to(root):
                raise RuntimeError('Paket içinde geçersiz dosya yolu bulundu.')
        bundle.extractall(RUNTIME)
    STAMP.write_text(current_stamp, encoding='utf-8')

sys.path.insert(0, str(RUNTIME))
os.chdir(RUNTIME)
# Import the existing app without executing its main() yet, so we can safely
# override just show_pdf(), leaving all test logic and authentication as-is.
app = runpy.run_path(str(RUNTIME / 'app.py'), run_name='seher_pdf_ui_v3')
import streamlit as st
import streamlit.components.v1 as components

_PDF_READER_HTML = r'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5,user-scalable=yes"/>
<style>
  * {box-sizing:border-box}html,body{margin:0;height:100%;overflow:hidden;background:#f2eff4;font-family:system-ui,-apple-system,sans-serif;color:#282032}
  #wrap {display:flex;flex-direction:column;height:100%;min-height:300px}
  #toolbar {display:flex;gap:6px;align-items:center;justify-content:center;flex-wrap:wrap;padding:8px 6px;background:#fff;border-bottom:1px solid #d8cdd9;flex-shrink:0}
  button{background:#f4ecf3;border:1px solid #cdbdcd;border-radius:9px;min-height:40px;padding:6px 10px;font-size:15px;color:#392539;font-weight:650;cursor:pointer;touch-action:manipulation}
  button.main{background:#865678;color:#fff;border-color:#865678}
  button:disabled{opacity:.4;cursor:not-allowed}
  #page{font-size:13px;white-space:nowrap;min-width:67px;text-align:center}
  #percent{font-size:13px;white-space:nowrap;min-width:48px;text-align:center}
  #viewport{flex:1;overflow:auto;overscroll-behavior:contain;text-align:center;touch-action:pan-x pan-y;-webkit-overflow-scrolling:touch}
  #paper{display:inline-block;position:relative;margin:12px auto 35px;box-shadow:0 3px 12px #0002;background:white;line-height:0;max-width:none}
  canvas{display:block;background:white;touch-action:pan-x pan-y}
  #status{padding:3px 8px;background:#fff;border-top:1px solid #ddd;font-size:12px;text-align:center;flex-shrink:0}
  html:fullscreen, html:-webkit-full-screen {width:100vw;height:100dvh;background:#f2eff4}
  html:fullscreen #wrap, html:-webkit-full-screen #wrap{height:100dvh}
  @media(max-width:480px){#toolbar{gap:4px;padding:6px 3px}button{font-size:14px;min-height:42px;padding:5px 8px}#page{min-width:61px}}
</style></head><body>
<div id="wrap">
 <div id="toolbar" role="toolbar" aria-label="PDF okuma araçları">
  <button id="full" class="main" title="Tam ekran aç veya kapat">⛶ Tam ekran</button>
  <button id="prev" title="Önceki sayfa">‹</button><span id="page">1 / …</span>
  <button id="next" title="Sonraki sayfa">›</button>
  <button id="out" title="Uzaklaştır">−</button><span id="percent">100%</span>
  <button id="in" title="Yakınlaştır">+</button><button id="fit" title="Sayfa genişliğine sığdır">Sığdır</button>
 </div>
 <div id="viewport"><div id="paper"><canvas id="canvas" title="Tam ekran okumak için dokun"></canvas></div></div>
 <div id="status">⛶ Tam ekrana bas · İki parmakla yakınlaştır · ‹ › sayfa değiştir</div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
(function(){
'use strict';
const base64PDF = '__PDF_BASE64__';
const $ = id => document.getElementById(id);
const canvas = $('canvas'), paper = $('paper'), viewport = $('viewport');
let pdf = null, current = 1, zoom = 1, renderTask = null, renderVersion = 0;
let initialPinch = 0, pinchZoom = 1, currentFactor = 1, lastGesture = 0;
function note(s){$('status').textContent=s;}
function clamp(n,min,max){return Math.max(min,Math.min(max,n));}
function fingerDistance(t){return Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY);}
function refreshButtons(){
 $('page').textContent = pdf ? current+' / '+pdf.numPages : '…';
 $('percent').textContent=Math.round(zoom*100)+'%';
 $('prev').disabled=!pdf||current<=1;
 $('next').disabled=!pdf||current>=pdf.numPages;
}
async function render(){
 if(!pdf)return;
 const myVersion=++renderVersion;
 if(renderTask){try{renderTask.cancel()}catch(e){} renderTask=null;}
 try{
   const pg=await pdf.getPage(current);
   if(myVersion!==renderVersion)return;
   const atOne=pg.getViewport({scale:1});
   const fit=Math.max(.2,(viewport.clientWidth-24)/atOne.width);
   const visual=pg.getViewport({scale:fit*zoom});
   const dpr=Math.min(window.devicePixelRatio||1,2);
   canvas.width=Math.round(visual.width*dpr);
   canvas.height=Math.round(visual.height*dpr);
   canvas.style.width=visual.width+'px';
   canvas.style.height=visual.height+'px';
   paper.style.width=visual.width+'px';paper.style.height=visual.height+'px';
   paper.style.transform='';
   const ctx=canvas.getContext('2d',{alpha:false});
   renderTask=pg.render({canvasContext:ctx,viewport:visual,transform:dpr!==1?[dpr,0,0,dpr,0,0]:undefined});
   await renderTask.promise;
   if(myVersion!==renderVersion)return;
   refreshButtons();note('⛶ Tam ekran · İki parmakla yakınlaştır · ‹ › sayfa değiştir');
 }catch(e){if(e && e.name==='RenderingCancelledException')return;note('Sayfa görüntülenemedi: '+String(e.message||e));}
}
function go(delta){if(!pdf)return;const n=clamp(current+delta,1,pdf.numPages);if(n===current)return;current=n;viewport.scrollTop=0;viewport.scrollLeft=0;render();}
function changeZoom(z){zoom=clamp(z,.65,4.0);refreshButtons();render();}
async function fullscreen(){
 try{
  if(document.fullscreenElement || document.webkitFullscreenElement){
   if(document.exitFullscreen)await document.exitFullscreen();else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
  } else if(document.documentElement.requestFullscreen){await document.documentElement.requestFullscreen();}
  else if(document.documentElement.webkitRequestFullscreen){document.documentElement.webkitRequestFullscreen();}
  else note('Tarayıcı tam ekranı engelliyor. PDF indir düğmesini kullanabilirsin.');
 } catch(e){note('Bu tarayıcı tam ekrana izin vermedi; yakınlaştırma tuşlarını kullanabilirsin.');}
 setTimeout(render,150);
}
$('full').addEventListener('click',fullscreen);
$('prev').addEventListener('click',()=>go(-1));$('next').addEventListener('click',()=>go(1));
$('in').addEventListener('click',()=>changeZoom(zoom+.25));
$('out').addEventListener('click',()=>changeZoom(zoom-.25));
$('fit').addEventListener('click',()=>changeZoom(1));
canvas.addEventListener('click',()=>{if(Date.now()-lastGesture>600)fullscreen();});
viewport.addEventListener('touchstart',e=>{
 if(e.touches.length===2){initialPinch=fingerDistance(e.touches);pinchZoom=zoom;currentFactor=1;lastGesture=Date.now();}
},{passive:true});
viewport.addEventListener('touchmove',e=>{
 if(e.touches.length===2 && initialPinch){
  e.preventDefault();currentFactor=clamp(fingerDistance(e.touches)/initialPinch,.5,4);
  paper.style.transform='scale('+currentFactor+')';
  paper.style.transformOrigin='center top';
  lastGesture=Date.now();
 }
},{passive:false});
viewport.addEventListener('touchend',e=>{
 if(initialPinch && e.touches.length<2){
  initialPinch=0;lastGesture=Date.now();const target=pinchZoom*currentFactor;
  currentFactor=1;paper.style.transform='';changeZoom(target);
 }
},{passive:true});
window.addEventListener('resize',()=>{if(pdf)render();});
document.addEventListener('fullscreenchange',()=>{setTimeout(render,100);$('full').textContent=document.fullscreenElement?'✕ Kapat':'⛶ Tam ekran';});
window.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')go(-1);if(e.key==='ArrowRight')go(1);if(e.key==='Escape' && document.fullscreenElement)document.exitFullscreen();});
async function start(){
 if(!window.pdfjsLib){note('Okuyucu yüklenemedi. Alttaki klasik görünümü veya PDF indirmeyi kullan.');return;}
 try{
  window.pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  const decoded=atob(base64PDF),data=new Uint8Array(decoded.length);
  for(let i=0;i<decoded.length;i++)data[i]=decoded.charCodeAt(i);
  pdf=await window.pdfjsLib.getDocument({data:data}).promise;
  await render();
 }catch(e){note('PDF açılamadı: '+String(e.message||e));}
}
start();
})();
</script></body></html>'''


def show_mobile_pdf():
    slug = st.session_state['course']
    course = app['COURSE_BY_ID'][slug]
    path = app['get_pdf_path'](slug)
    st.subheader(f"{course['icon']} {course['name']} — PDF")
    st.caption('Belgeye veya ⛶ Tam ekran düğmesine dokun. İki parmağınla büyütüp küçültebilir, + / − düğmelerini de kullanabilirsin.')
    # All course PDFs are small enough to send to a native interactive reader.
    pdf_encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    components.html(_PDF_READER_HTML.replace('__PDF_BASE64__',pdf_encoded), height=660, scrolling=False)
    with path.open('rb') as pdf_file:
        st.download_button('📥 PDF’yi telefona indir / başka uygulamada aç',pdf_file,file_name=f'Seher_{slug}_tam_rehber.pdf',mime='application/pdf',use_container_width=True)
    with st.expander('📄 Eski sayfa sayfa okuyucu (yedek)'):
        app['show_pdf']()


# The original show_pdf function retains the old working interface and is only
# called if the user expands the fallback. All unrelated original functions stay.
app['show_pdf'].__globals__['show_pdf'] = show_mobile_pdf
app['main']()
