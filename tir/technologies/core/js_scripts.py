inspector_js = """
(function(){
  if (window.__inspectorInstalled) return 'already';
  window.__inspectorInstalled = true;

  const state = window.__activityState = {
    // contadores
    pending: { xhr:0, fetch:0, transitions:0, animations:0 },
    totals:  { xhr:0, fetch:0, transitions:0, animations:0 },
    events: [],
    mutations: 0,
    mutationLog: [],
    lastChange: Date.now()
  };

  // --- captura de eventos básicos (opcional, mas útil p/ log) ---
  const capture = [
    'click','change','input','submit','keydown','keyup',
    'pointerdown','pointerup','mousedown','mouseup',
    'touchstart','touchend',
    'transitionstart','transitionend',
    'animationstart','animationend'
  ];
  capture.forEach(t=>{
    document.addEventListener(t, e=>{
      state.events.push({ type:t, time:Date.now(), target: e.target?.tagName });
      state.lastChange = Date.now();
      if (t==='transitionstart') { state.pending.transitions++; state.totals.transitions++; }
      if (t==='transitionend')   { state.pending.transitions = Math.max(0, state.pending.transitions-1); }
      if (t==='animationstart')  { state.pending.animations++;  state.totals.animations++; }
      if (t==='animationend')    { state.pending.animations = Math.max(0, state.pending.animations-1); }
    }, true);
  });

  // --- MutationObserver (DOM alterada) ---
  const mo = new MutationObserver(muts => {
    state.mutations += muts.length;
    state.lastChange = Date.now();

    muts.forEach(m => {
      const entry = { time: Date.now(), type: m.type };

      if (m.type === "childList") {
        entry.added   = Array.from(m.addedNodes).map(n => n.outerHTML || n.nodeName);
        entry.removed = Array.from(m.removedNodes).map(n => n.outerHTML || n.nodeName);
      }

      if (m.type === "attributes") {
        entry.attribute = m.attributeName;
        entry.oldValue  = m.oldValue;
        entry.newValue  = m.target.getAttribute(m.attributeName);
      }

      if (m.type === "characterData") {
        entry.oldValue = m.oldValue;
        entry.newValue = m.target.data;
      }

      state.mutationLog.push(entry);
      if (state.mutationLog.length > 200) {
        state.mutationLog = state.mutationLog.slice(-200);
      }
    });
  });

  mo.observe(document.documentElement, { 
    childList: true, subtree: true, 
    attributes: true, attributeOldValue: true,
    characterData: true, characterDataOldValue: true
  });

  // --- fetch tracking ---
  if (window.fetch) {
    const _fetch = window.fetch;
    window.fetch = function(...args){
      state.pending.fetch++; state.totals.fetch++; state.lastChange = Date.now();
      return _fetch.apply(this,args).finally(()=>{
        state.pending.fetch = Math.max(0, state.pending.fetch-1);
        state.lastChange = Date.now();
      });
    };
  }

  // --- XHR tracking ---
  const _open = XMLHttpRequest.prototype.open;
  const _send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(...args){ this.__tracked=true; return _open.apply(this,args); };
  XMLHttpRequest.prototype.send = function(...args){
    if (this.__tracked){
      state.pending.xhr++; state.totals.xhr++; state.lastChange = Date.now();
      this.addEventListener('loadend', ()=>{
        state.pending.xhr = Math.max(0, state.pending.xhr-1);
        state.lastChange = Date.now();
      }, { once:true });
    }
    return _send.apply(this,args);
  };

  // --- função wait_until_idle ---
  window.__waitForIdle = function(timeout=7000, quiet=500){
    return new Promise(resolve=>{
      const start = Date.now();
      (function tick(){
        const p = state.pending;
        const busy = (p.xhr+p.fetch+p.transitions+p.animations) > 0;
        const since = Date.now() - state.lastChange;
        if (!busy && since >= quiet) return resolve({ since, state });
        if (Date.now() - start > timeout) return resolve({ timeout:true, since, state });
        setTimeout(tick, 50);
      })();
    });
  };

  return 'installed';
})();

"""