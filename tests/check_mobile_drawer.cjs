const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('mobile_drawer.js','utf8');
let open=false,opens=0,closes=0,observed=false;
function eventDoc(){const listeners={};return {listeners,addEventListener:(n,f)=>listeners[n]=f}}
const doc=eventDoc(),pdf=eventDoc();
const side={hasAttribute:()=>true,getAttribute:()=>String(open),contains:t=>t.side,
 querySelector:s=>s.includes('stSidebarCollapseButton')?closeBtn:null};
const openBtn={matches:s=>s==='button',click(){open=true;opens++}};
const closeBtn={matches:s=>s==='button',click(){open=false;closes++}};
let zoom='100%';pdf.getElementById=id=>({textContent:zoom});
const frame={contentDocument:pdf,getBoundingClientRect:()=>({left:10,top:200}),addEventListener(){}};
doc.querySelector=s=>s.includes('stSidebar"]')?side:s.includes('stExpandSidebarButton')?openBtn:null;
doc.querySelectorAll=()=>[frame];doc.body={};
const host={document:doc,AbortController,MutationObserver:class{constructor(f){this.fn=f}observe(){observed=true}disconnect(){}}};
vm.runInNewContext(source,{window:{parent:host}});
const target=(side=false)=>({side,closest:()=>null});
function touch(d,type,x,y,side=false,count=1){let prevented=false;
const touches=Array.from({length:count},()=>({clientX:x,clientY:y}));
d.listeners[type]({target:target(side),touches:type==='touchend'?[]:touches,changedTouches:touches,cancelable:true,preventDefault(){prevented=true}});return prevented;
}
assert(observed);
touch(doc,'touchstart',90,100);assert(touch(doc,'touchmove',165,105));assert(open);assert.equal(opens,1);
touch(doc,'touchend',165,105);assert(open);assert.equal(opens,1);
touch(doc,'touchstart',150,100,true);touch(doc,'touchend',70,105,true);assert(!open);assert.equal(closes,1);
touch(doc,'touchstart',80,100);touch(doc,'touchmove',85,220);touch(doc,'touchend',180,220);assert(!open);
touch(doc,'touchstart',80,100,false,2);touch(doc,'touchend',180,100);assert(!open);
touch(doc,'touchstart',180,100);touch(doc,'touchend',280,100);assert(!open);
touch(pdf,'touchstart',60,100);touch(pdf,'touchend',150,100);assert(open);
open=false;zoom='150%';touch(pdf,'touchstart',60,100);touch(pdf,'touchend',150,100);assert(!open);
touch(doc,'touchstart',80,100);doc.listeners.touchcancel();touch(doc,'touchend',180,100);assert(!open);
console.log('Drawer: modern native control, wider swipe zone, move/end, latch, PDF iframe, zoom, scroll, pinch, cancel PASS');
