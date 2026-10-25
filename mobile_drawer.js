// Keep the lock in the app window so Streamlit iframe reruns cannot orphan it.
function seherScreenAwake(host) {
  if (host.__seherScreenAwake) {
    host.__seherScreenAwake.resume();
    return host.__seherScreenAwake;
  }
  const doc = host.document;
  let lock = null, pending = false, enabled = true;
  let message = '☀️ Ekran açık tutma başlatılıyor…';
  function status() {
    const hero = doc.querySelector('.pro-hero');
    if (!hero) return;
    let label = hero.querySelector('[data-seher-awake]');
    if (!label) {
      label = doc.createElement('p');
      label.setAttribute('data-seher-awake', '');
      label.setAttribute('role', 'status');
      label.style.cssText = 'margin-top:8px;font-size:.8rem';
      hero.appendChild(label);
    }
    if (label.textContent !== message) label.textContent = message;
  }
  async function acquire() {
    if (!enabled || doc.visibilityState !== 'visible' || pending || (lock && !lock.released)) return;
    if (!host.navigator?.wakeLock?.request) {
      message = 'Ekranı açık tutma bu tarayıcıda desteklenmiyor.';
      status(); return;
    }
    pending = true;
    try {
      const sentinel = await host.navigator.wakeLock.request('screen');
      if (!enabled || doc.visibilityState !== 'visible') {
        await sentinel.release(); return;
      }
      lock = sentinel;
      sentinel.addEventListener('release', () => {
        if (lock !== sentinel) return;
        lock = null;
        message = 'Ekran açık tutma durakladı; devam etmek için ekrana dokun.';
        status();
      }, {once:true});
      message = '☀️ Çalışırken ekran açık tutuluyor';
    } catch (_) {
      message = 'Ekran açık tutulamadı. Ekrana dokun; sürerse tarayıcı/pil tasarrufu ayarlarını kontrol et.';
    } finally { pending = false; status(); }
  }
  function pause() {
    const held = lock;
    lock = null;
    if (held) held.release().catch(() => {});
  }
  const bound = new WeakSet();
  const api = {
    resume() { enabled = true; acquire(); status(); },
    bind(targetDoc) {
      if (!targetDoc || bound.has(targetDoc)) return;
      bound.add(targetDoc);
      targetDoc.addEventListener('pointerdown', () => acquire(), {passive:true});
      targetDoc.addEventListener('touchend', () => acquire(), {passive:true});
      targetDoc.addEventListener('keydown', () => acquire());
    },
    status
  };
  doc.addEventListener('visibilitychange', () => {
    if (doc.visibilityState === 'visible') acquire(); else pause();
  });
  host.addEventListener('pagehide', pause);
  host.addEventListener('pageshow', () => acquire());
  doc.addEventListener('click', event => {
    if (event.target.closest?.('.st-key-seher_pro_logout')) {
      enabled = false; pause();
    }
  }, true);
  host.__seherScreenAwake = api;
  api.resume();
  return api;
}

(() => {
  const host = window.parent, doc = host.document;
  const awake = seherScreenAwake(host);
  if (host.__seherDrawer) host.__seherDrawer.abort();
  const control = new host.AbortController();
  host.__seherDrawer = control;
  const signal = control.signal;
  const sidebar = () => doc.querySelector('[data-testid="stSidebar"]');
  function expanded() {
    const side = sidebar();
    if (!side) return false;
    if (side.hasAttribute('aria-expanded')) return side.getAttribute('aria-expanded') === 'true';
    const r = side.getBoundingClientRect();
    return r.width > 0 && r.left >= -1 && r.right > 0;
  }
  function button(container, testid) {
    const node = container.querySelector('[data-testid="'+testid+'"]');
    return node?.matches('button') ? node : node?.querySelector('button');
  }
  function toggle(open) {
    if (expanded() === open) return;
    const target = open ?
      (button(doc, 'stExpandSidebarButton') || button(doc, 'stSidebarCollapsedControl') || button(doc, 'collapsedControl')) :
      button(sidebar() || doc, 'stSidebarCollapseButton');
    target?.click();
  }
  // Touch events inside PDF iframes do not bubble to the app document. Bind
  // same-origin frames too, and rebind when Streamlit replaces their documents.
  const bound = new WeakSet();
  function bind(targetDoc, frame=null) {
    if (!targetDoc || bound.has(targetDoc)) return;
    bound.add(targetDoc);
    awake.bind(targetDoc);
    let start = null;
    const point = t => ({x:t.clientX+(frame?.getBoundingClientRect().left||0),y:t.clientY+(frame?.getBoundingClientRect().top||0)});
    function begin(e) {
      start = null;
      if (e.touches.length !== 1) return;
      if (e.target.closest?.('input,textarea,select,[role="slider"],[contenteditable="true"]')) return;
      // A zoomed PDF needs its horizontal panning gesture for reading.
      if (frame && parseInt(targetDoc.getElementById('percent')?.textContent || '100',10) > 100) return;
      const p = point(e.touches[0]), open = expanded();
      const side = sidebar();
      if ((!open && p.x <= 120) || (open && !frame && side?.contains(e.target)))
        start = {...p,open};
    }
    function move(e) {
      if (!start) return;
      if (e.touches.length !== 1) {start=null;return;}
      finish(e,e.touches[0]);
    }
    function finish(e,touch) {
      if (!start || !touch) return;
      const p = point(touch), dx = p.x-start.x, dy = p.y-start.y;
      if (Math.abs(dy)>25 && Math.abs(dy)>Math.abs(dx)) {start=null;return;}
      if (Math.abs(dx)<60 || Math.abs(dx)<Math.abs(dy)*1.6) return;
      const open = start.open;
      start=null;
      if ((!open && dx>0) || (open && dx<0)) {
        if(e.cancelable)e.preventDefault();
        toggle(!open);
      }
    }
    targetDoc.addEventListener('touchstart',begin,{passive:true,capture:true,signal});
    targetDoc.addEventListener('touchmove',move,{passive:false,capture:true,signal});
    targetDoc.addEventListener('touchend',e=>{if(!e.touches.length)finish(e,e.changedTouches[0]);start=null;},{passive:false,capture:true,signal});
    targetDoc.addEventListener('touchcancel',()=>{start=null;},{passive:true,signal});
  }
  const frames = new WeakSet();
  function scan() {
    awake.status();
    for (const frame of doc.querySelectorAll('iframe')) {
      const attach = () => {try{bind(frame.contentDocument,frame);}catch(_){}};
      if (!frames.has(frame)) {
        frames.add(frame);
        frame.addEventListener('load',attach,{signal});
      }
      attach();
    }
  }
  bind(doc);scan();
  const observer = new host.MutationObserver(scan);
  observer.observe(doc.body,{childList:true,subtree:true});
  signal.addEventListener('abort',()=>observer.disconnect(),{once:true});
})();
