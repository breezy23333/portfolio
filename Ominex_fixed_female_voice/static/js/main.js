/* ====================== OMINEX main.js (clean consolidated) ====================== */
function escapeHTML(s = "") {
  return String(s).replace(/[&<>"']/g, c => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]
  ));
}
function linkify(text = "") {
  const safe = escapeHTML(text);
  return safe
    .replace(/https?:\/\/\S+/g, u => `<a href="${u}" target="_blank" rel="noopener">${u}</a>`)
    .replace(/\n/g, "<br>");
}
/* ------------------------------ DOM refs ------------------------------ */
const $id   = (id) => document.getElementById(id);
const chat  = $id('chat');
const input = $id('input');
const sendBtn = $id('send');
const statusEl = $id('status') || document.querySelector('.status');
const moodEl   = $id('mood');
const avatar   = $id('avatar');

// Optional controls (wire them if present)
const voiceToggleEl = $id('voiceToggle') || $id('ttsToggle');
const testVoiceEl   = $id('testVoice')   || $id('testVoiceBtn');
const micBtnDom     = $id('micBtn');

console.log('[OMINEX] main.js loaded');

let voiceUnlocked = false;

function unlockVoice(callback) {
  if (voiceUnlocked) return;
  const overlay = document.createElement('div');
  overlay.style.position = 'fixed';
  overlay.style.inset = '0';
  overlay.style.zIndex = '99999';
  overlay.style.cursor = 'pointer';
  overlay.style.background = 'transparent';

  overlay.addEventListener('click', () => {
    voiceUnlocked = true;
    speechSynthesis.getVoices(); // unlock audio
    overlay.remove();
    if (callback) callback();
  });

  document.body.appendChild(overlay);
}


/* --------------------------- Small helpers --------------------------- */
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function setStatus(t){ if (statusEl) statusEl.textContent = t; }
function setMood(m){
  if (!moodEl) return;
  moodEl.textContent = 'Mood: ' + m;
  moodEl.className = 'badge ' + (m === 'Positive' ? 'badge-positive' :
                                 m === 'Concerned' ? 'badge-concerned' : 'badge-neutral');
}
function getCurrentMood(){
  return (moodEl?.textContent || 'Neutral').split(':').pop().trim() || 'Neutral';
}

function sanitize(text=''){
  return text.replace(/[&<>"']/g, (m)=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
}
function linkify(text=''){
  const urlRegex = /(https?:\/\/[^\s)]+)(?=\)|\s|$)/g;
  return text.replace(urlRegex, u => `<a href="${u}" target="_blank" rel="noopener noreferrer">${u}</a>`);
}

function add(role, text){
  if (!chat) { console.error('No #chat element'); return; }

  const row = document.createElement('div');
  row.className = 'msg ' + role;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  const safe = sanitize(text || '');
  const decoded = decodeHTML(safe);

  bubble.innerHTML = linkify(decoded).replace(/\n/g,'<br>');

  row.appendChild(bubble);
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
  return row;
}


function decodeHTML(str) {
  const txt = document.createElement('textarea');
  txt.innerHTML = str;
  return txt.value;
}


function escapeHTML(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function linkify(text) {
  const safe = escapeHTML(text);
  return safe.replace(/https?:\/\/\S+/g, (url) => `<a href="${url}" target="_blank" rel="noopener">${url}</a>`);
}
/* ----------------------- Typing indicator ----------------------- */
let typingEl = null;
function showTyping(){
  if (typingEl) return;
  typingEl = document.createElement('div');
  typingEl.className = 'typing';
  typingEl.innerHTML = 'OMINEX is thinking&nbsp;<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
  chat.appendChild(typingEl);
  chat.scrollTop = chat.scrollHeight;
  if (avatar){ avatar.classList.add('active'); }
}
function hideTyping(){
  if (typingEl){ typingEl.remove(); typingEl = null; }
  if (avatar){ avatar.classList.remove('active'); }
}

/* --------------------- Backend connectivity --------------------- */
async function backendIsUp(){
  try {
    const r = await fetch("https://ominex-backend-sxeg.onrender.com/api/ping", { cache:'no-store' });
    return r.ok;
  } catch {
    return false;
  }
}

async function updateStatus(){
  const ok = await backendIsUp();
  setStatus(ok ? 'Backend: connected' : 'Backend: disconnected');
}
updateStatus();
setInterval(updateStatus, 4000);

/* ------------------------------ TTS ------------------------------ */
const TTS = {
  enabled: JSON.parse(localStorage.getItem('ominexVoice') || 'true'),
  rate: 1.0, pitch: 1.03, voice: null
};
const synth = window.speechSynthesis;

function preferredVoice(){
  if (!synth) return null;
  const vs = synth.getVoices() || [];
  if (!vs.length) return null;
  const preferNames = [
    'Microsoft Aria Online (Natural) - English (United States)',
    'Microsoft Jenny Online (Natural) - English (United States)',
    'Microsoft Sonia Online (Natural) - English (Great Britain)',
    'Google UK English Female','Google US English'
  ];
  return vs.find(v => preferNames.includes(v.name))
      || vs.find(v => (v.lang||'').toLowerCase().startsWith('en') && /Female|Aria|Jenny|Sonia|Neural|Online/i.test(v.name))
      || vs.find(v => (v.lang||'').toLowerCase().startsWith('en'))
      || vs[0];
}
function ensureVoice(){ if (!synth) return null; if (!TTS.voice) TTS.voice = preferredVoice(); return TTS.voice; }

function speak(text) {
  const synth = window.speechSynthesis;
  if (!synth) return;

  const msg = text?.trim();
  if (!msg) return;

  const voices = synth.getVoices();
  if (!voices.length) {
    console.warn("No voices yet");
    return;
  }

  const voice = voices.find(v => v.lang.startsWith("en")) || voices[0];

  const u = new SpeechSynthesisUtterance(msg);
  u.voice = voice;
  u.lang = voice.lang;
  u.volume = 1;
  u.rate = 1;
  u.pitch = 1;

  synth.speak(u);
}

// warm voices after first user gesture (Chrome quirk)
window.addEventListener('click', () => { try { speechSynthesis.getVoices(); } catch {} }, { once:true });

// Toggle + Test (if controls exist)
if (voiceToggleEl){
  voiceToggleEl.checked = !!TTS.enabled;
  voiceToggleEl.addEventListener('change', () => {
    TTS.enabled = voiceToggleEl.checked;
    localStorage.setItem('ominexVoice', JSON.stringify(TTS.enabled));
    if (!TTS.enabled) try { synth?.cancel(); } catch {}
  });
}
if (testVoiceEl){ testVoiceEl.addEventListener('click', () => speak("Hello, I'm OMINEX. Voice is ready.")); }

/* -------------------------- Send flow -------------------------- */
async function postChat(payload){
  const r = await fetch(
    "https://ominex-backend-sxeg.onrender.com/api/demo",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }
  );
  if (!r.ok) throw new Error("Demo API unreachable");
  return await r.json();
}

async function sendMessage(text){
  if (!text) return;
  if (/^wiki\s+/i.test(text)) text = text.replace(/^wiki\s+/i, 'search ');
  add('user', text);
  if (input) input.value = '';
  showTyping();

  const t0 = performance.now();
  let data;
  try {
    const payload = { text, message: text, mood: getCurrentMood() };
    data = await postChat(payload);
  } catch (e) {
    console.error('[OMINEX] chat error', e);
    hideTyping(); add('bot', 'I could not reach the server.'); setStatus('Backend: error');
    return;
  }

  const elapsed = performance.now() - t0;
  const minDelay = 350 + Math.random()*350;
  if (elapsed < minDelay) await sleep(minDelay - elapsed);

  hideTyping();

  const reply = data?.reply || '';
  const mood  = data?.mood  || 'Neutral';
  setMood(mood);
  add('bot', reply);

  const say = (data?.speak && data.speak.trim()) ? data.speak : reply;
  const isHelper = /You can say things like/i.test(reply);
  if (TTS.enabled && say && !isHelper) requestAnimationFrame(()=> speak(say));

  if (data?.error){ add('bot', `Debug: ${data.error}`); console.error('[OMINEX] backend error:', data.error); }
}
window.sendMessage = sendMessage; // allow other code to trigger it

// wire UI
if (sendBtn){
  sendBtn.setAttribute('type','button');
  sendBtn.addEventListener('click', (e)=>{ e.preventDefault(); sendMessage((input?.value||'').trim()); });
}
if (input){
  input.addEventListener('keydown', (e)=>{
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage((input.value||'').trim()); }
  });
}

/* ----------------------- Push-to-talk (STT) ----------------------- */
(function setupSTT(){
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Rec) { if (micBtnDom) micBtnDom.title = 'SpeechRecognition not supported'; return; }

  const rec = new Rec();
  rec.lang = 'en-US'; rec.continuous = false; rec.interimResults = false;
  rec.onresult = (e) => {
    const t = e.results?.[0]?.[0]?.transcript || '';
    if (t) sendMessage(t);
  };

  function start(){ try { rec.start(); micBtn?.classList?.add('is-listening'); } catch {} }
  function stop (){ try { rec.stop();  micBtn?.classList?.remove('is-listening'); } catch {} }

  // use existing mic if present; otherwise inject one next to Send
  let micBtn = micBtnDom;
  if (!micBtn && sendBtn && sendBtn.parentElement){
    micBtn = document.createElement('button');
    micBtn.id = 'micBtn';
    micBtn.className = 'ominex-inline-btn ominex-mic';
    micBtn.title = 'Hold to talk';
    micBtn.textContent = '🎤';
    sendBtn.parentElement.insertBefore(micBtn, sendBtn.nextSibling);
  }
  if (!micBtn) return;

  // hold-to-talk
  micBtn.addEventListener('mousedown', start);
  micBtn.addEventListener('touchstart', (e)=>{ e.preventDefault(); start(); }, { passive:false });
  ['mouseup','mouseleave','touchend','touchcancel','blur'].forEach(ev => micBtn.addEventListener(ev, stop));
})();

/* ---------------------- Memory Viewer (local) ---------------------- */
(function memoryViewer(){
  const STORE_KEY = 'ominexHistory';
  const save = (arr) => localStorage.setItem(STORE_KEY, JSON.stringify(arr.slice(-500)));
  const load = () => { try { return JSON.parse(localStorage.getItem(STORE_KEY) || '[]'); } catch { return []; } };
  const log  = (role, text) => { if (!text) return; const arr = load(); arr.push({ t: Date.now(), role, text }); save(arr); };

  // Observe chat for new .msg nodes
  if (chat){
    new MutationObserver(muts => {
      for (const m of muts) for (const n of m.addedNodes){
        if (!(n instanceof HTMLElement)) continue;
        if (!n.classList.contains('msg')) continue;
        const role = n.classList.contains('user') ? 'user' : (n.classList.contains('bot') ? 'bot' : 'unknown');
        const text = n.textContent?.trim();
        log(role, text);
      }
    }).observe(chat, { childList: true });
  }

  // Add Mem button (after mic if exists, else after send)
  const after = document.getElementById('micBtn') || sendBtn;
  if (!after || !after.parentElement) return;
  const memBtn = document.createElement('button');
  memBtn.id = 'memBtn';
  memBtn.className = 'ominex-inline-btn';
  memBtn.title = 'View memory (local)';
  memBtn.textContent = '🧠 Mem';
  after.parentElement.insertBefore(memBtn, after.nextSibling);

  // Modal UI
  memBtn.addEventListener('click', () => {
    const data = load();
    const overlay = document.createElement('div');
    overlay.className = 'ominex-modal-backdrop';
    overlay.addEventListener('click', (e)=>{ if (e.target === overlay) overlay.remove(); });

    const modal = document.createElement('div'); modal.className = 'ominex-modal';
    const head = document.createElement('header');
    head.innerHTML = `<strong>Memory (local)</strong>
      <div class="ominex-toolbar">
        <button class="ominex-inline-btn" id="memExport">Export JSON</button>
        <button class="ominex-inline-btn" id="memClear">Clear</button>
        <button class="ominex-inline-btn" id="memClose">Close</button>
      </div>`;
    const body = document.createElement('div'); body.className = 'body ominex-tiny';
    const pretty = data.map(it => `[${new Date(it.t).toLocaleString()}] ${it.role.toUpperCase()}: ${it.text}`).join('\n');
    body.innerHTML = `<pre>${pretty || 'No messages captured yet.'}</pre>`;

    modal.appendChild(head); modal.appendChild(body);
    overlay.appendChild(modal); document.body.appendChild(overlay);

    document.getElementById('memClose').onclick  = () => overlay.remove();
    document.getElementById('memClear').onclick  = () => { save([]); overlay.remove(); };
    document.getElementById('memExport').onclick = () => {
      const blob = new Blob([ JSON.stringify(load(), null, 2) ], { type:'application/json' });
      const url  = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `ominex_memory_${Date.now()}.json`; a.click();
      URL.revokeObjectURL(url);
    };
  });

  // Inject minimal styles for mic/mem/modal if your CSS doesn’t have them
  const style = document.createElement('style');
  style.textContent = `
    .ominex-inline-btn{ padding:10px 12px; border-radius:12px; border:1px solid rgba(148,163,184,.25);
      background:#1a2334; color:#e6edf3; font-weight:600; cursor:pointer; margin-left:8px }
    .ominex-inline-btn:hover{ filter:brightness(1.05) }
    .ominex-mic.is-listening{ box-shadow:0 0 0 2px rgba(124,140,255,.25) inset, 0 0 20px rgba(124,140,255,.35) }
    .ominex-modal-backdrop{ position:fixed; inset:0; background:rgba(0,0,0,.45); backdrop-filter:saturate(1.2) blur(2px);
      display:flex; align-items:center; justify-content:center; z-index:9999 }
    .ominex-modal{ width:min(760px,94vw); max-height:76vh; overflow:auto; background:#0f172a; color:#e6edf3;
      border:1px solid rgba(255,255,255,.08); border-radius:14px; box-shadow:0 20px 40px rgba(0,0,0,.45) }
    .ominex-modal header{ display:flex; justify-content:space-between; align-items:center; padding:12px 14px;
      border-bottom:1px solid rgba(255,255,255,.06) }
    .ominex-modal .body{ padding:12px 14px }
    .ominex-modal pre{ white-space:pre-wrap; word-wrap:break-word; background:#0b1324; border:1px solid rgba(255,255,255,.06);
      border-radius:10px; padding:10px; margin:0 }
    .ominex-toolbar{ display:flex; gap:8px }
    .ominex-tiny{ font-size:12px; opacity:.8 }
  `;
  document.head.appendChild(style);
})();

/* ================== OMINEX: Ledger + Alerts + Backtest UI ================== */
(function () {
  const sendBtn = document.getElementById('send');
  const after = document.getElementById('memBtn') || document.getElementById('micBtn') || sendBtn;
  if (!after || !after.parentElement) return;

  // Add buttons
  const mkBtn = (id, text, title) => {
    const b = document.createElement('button');
    b.id = id; b.className = 'ominex-inline-btn'; b.textContent = text; b.title = title; return b;
  };
  const ledgerBtn = mkBtn('ledgerBtn','📒 Ledger','Paper-trade ledger');
  const alertBtn  = mkBtn('alertBtn','⏰ Alerts','Price alerts');
  const copyBtn   = mkBtn('copyPlanBtn','📋 Copy','Copy last bot message');
  after.parentElement.insertBefore(ledgerBtn, after.nextSibling);
  ledgerBtn.after(alertBtn); alertBtn.after(copyBtn);

  // Helpers
  const modalCSS = `
    .ominex-modal-backdrop{ position:fixed; inset:0; background:rgba(0,0,0,.45); display:flex; align-items:center; justify-content:center; z-index:9999 }
    .ominex-modal{ width:min(880px,94vw); max-height:80vh; overflow:auto; background:#0f172a; color:#e6edf3;
      border:1px solid rgba(255,255,255,.08); border-radius:14px; box-shadow:0 20px 40px rgba(0,0,0,.45) }
    .ominex-modal header{ display:flex; justify-content:space-between; align-items:center; padding:12px 14px; border-bottom:1px solid rgba(255,255,255,.06) }
    .ominex-modal .body{ padding:12px 14px }
    table.ominex{ width:100%; border-collapse:collapse; font-size:14px }
    table.ominex th, table.ominex td{ border-bottom:1px solid rgba(255,255,255,.08); padding:8px 6px; text-align:left }
  `;
  if (!document.getElementById('ominex_modal_css')){
    const st = document.createElement('style'); st.id='ominex_modal_css'; st.textContent = modalCSS; document.head.appendChild(st);
  }
  function modal(title, innerHTML){
    const ov = document.createElement('div'); ov.className='ominex-modal-backdrop';
    const m = document.createElement('div'); m.className='ominex-modal';
    const h = document.createElement('header'); h.innerHTML = `<strong>${title}</strong><div class="ominex-toolbar">
      <button class="ominex-inline-btn" id="mdlClose">Close</button></div>`;
    const body = document.createElement('div'); body.className='body'; body.innerHTML = innerHTML;
    m.appendChild(h); m.appendChild(body); ov.appendChild(m); document.body.appendChild(ov);
    ov.addEventListener('click', (e)=>{ if(e.target===ov) ov.remove(); });
    document.getElementById('mdlClose').onclick = ()=> ov.remove();
    return { ov, body };
  }

  // ----- Ledger -----
  ledgerBtn.onclick = async () => {
    const r = await fetch('/api/trade/ledger'); const js = await r.json();
    const rows = [...js.open, ...js.closed].map(t =>
      `<tr><td>${t.id}</td><td>${t.symbol}</td><td>${t.status}</td>
       <td>${t.entry?.toFixed?.(2) ?? '-'}</td><td>${t.stop?.toFixed?.(2) ?? '-'}</td>
       <td>${t.exit?.toFixed?.(2) ?? '-'}</td><td>${t.R==null?'':t.R.toFixed(2)}</td></tr>`).join('');
    const { body } = modal('Ledger',
      `<div style="display:flex;gap:8px;margin-bottom:8px">
        <div class="ominex-inline-btn" id="ldgRefresh">Refresh</div>
        <div class="ominex-inline-btn" id="ldgExport">Export JSON</div>
      </div>
      <div style="margin-bottom:8px">Closed: ${js.count} | Win: ${js.winrate}% | AvgR: ${js.avgR} | TotalR: ${js.total_R}</div>
      <table class="ominex"><thead><tr><th>ID</th><th>Symbol</th><th>Status</th><th>Entry</th><th>Stop</th><th>Exit</th><th>R</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="7">No trades yet.</td></tr>'}</tbody></table>`);
    body.querySelector('#ldgRefresh').onclick = ()=> { document.getElementById('mdlClose').click(); ledgerBtn.click(); };
    body.querySelector('#ldgExport').onclick  = ()=> {
      fetch('/api/trade/ledger').then(r=>r.json()).then(d=>{
        const blob = new Blob([JSON.stringify(d,null,2)], {type:'application/json'});
        const u = URL.createObjectURL(blob); const a = document.createElement('a');
        a.href=u; a.download=`ominex_ledger_${Date.now()}.json`; a.click(); URL.revokeObjectURL(u);
      });
    };
  };

  // ----- Alerts -----
  alertBtn.onclick = async () => {
    const list = await fetch('/api/trade/alerts').then(r=>r.json());
    const { body } = modal('Alerts',
      `<form id="alertForm" style="display:flex;gap:8px;margin-bottom:8px">
         <input id="alSym" placeholder="Symbol e.g. STX40.JO" required style="flex:1;padding:8px;border-radius:10px;border:1px solid rgba(255,255,255,.08);background:#0b1324;color:#e6edf3">
         <input id="alLvl" type="number" step="0.01" placeholder="Level" required style="width:140px;padding:8px;border-radius:10px;border:1px solid rgba(255,255,255,.08);background:#0b1324;color:#e6edf3">
         <select id="alDir" style="padding:8px;border-radius:10px;background:#0b1324;color:#e6edf3">
            <option value="above">Above</option><option value="below">Below</option></select>
         <button class="ominex-inline-btn" type="submit">Add</button>
       </form>
       <div id="alList"></div>`);
    const render = (arr)=> body.querySelector('#alList').innerHTML =
      `<table class="ominex"><thead><tr><th>ID</th><th>Symbol</th><th>Direction</th><th>Level</th><th>Triggered</th></tr></thead>
        <tbody>${(arr||[]).map(a=>`<tr><td>${a.id}</td><td>${a.symbol}</td><td>${a.direction}</td><td>${a.level}</td><td>${a.triggered?'Yes':'No'}</td></tr>`).join('')}</tbody></table>`;
    render(list.alerts);
    body.querySelector('#alertForm').onsubmit = async (e) => {
      e.preventDefault();
      const payload = { symbol: body.querySelector('#alSym').value.trim(),
                        level: parseFloat(body.querySelector('#alLvl').value),
                        direction: body.querySelector('#alDir').value };
      const r = await fetch('/api/trade/alert', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const j = await r.json(); const l = await fetch('/api/trade/alerts').then(x=>x.json()); render(l.alerts);
    };
  };

  // Poll alerts every 60s — write to chat when something fires
  setInterval(async () => {
    try {
      const r = await fetch('/api/trade/alerts/check'); const j = await r.json();
      (j.triggered||[]).forEach(a => {
        const msg = `⏰ Alert: ${a.symbol} ${a.direction} ${a.level} (last ${a.price?.toFixed?.(2)})`;
        if (typeof add === 'function') add('bot', msg);
        if (window.TTS?.enabled) window.requestAnimationFrame(()=> window.speak?.(msg));
      });
    } catch {}
  }, 60000);

let introSpoken = false;

function speakIntroOnce(text) {
  if (introSpoken || !TTS.enabled) return;

  const unlock = () => {
    introSpoken = true;
    speechSynthesis.getVoices(); // unlock audio
    speak(text);
    document.removeEventListener('click', unlock);
    document.removeEventListener('keydown', unlock);
  };

  document.addEventListener('click', unlock, { once: true });
  document.addEventListener('keydown', unlock, { once: true });
}


  // ----- Copy last bot message -----
  copyBtn.onclick = () => {
    const bubbles = [...document.querySelectorAll('#chat .msg.bot .bubble')];
    const last = bubbles[bubbles.length-1]; if (!last) return;
    const text = last.innerText || '';
    navigator.clipboard?.writeText(text);
    if (typeof add === 'function') add('bot','Copied ✅');
  };
})();

/* ------------------------------- Boot ------------------------------- */
setMood('Neutral');

const introText = `I am OMINEX — an intelligent interface designed to assist, analyze, and communicate with clarity.

I was created by Luvo Maphela as an experimental AI system focused on human-centric interaction, clean design, and controlled intelligence.

This environment is a demonstration interface, showcasing how I speak, respond, and present information.

Real-time cognition and external systems are currently disabled.

You may interact freely.`;

add('bot', introText);
speakIntroOnce(introText);


/* ====== OMINEX Learn UI (topics + tick + query) ====== */
(function(){
  const sendBtn = document.getElementById('send');
  const after = document.getElementById('copyPlanBtn') || document.getElementById('ledgerBtn') || sendBtn;
  if (!after || !after.parentElement) return;

  const btn = document.createElement('button');
  btn.id = 'learnBtn'; btn.className = 'ominex-inline-btn'; btn.textContent = '🕸️ Learn';
  after.parentElement.insertBefore(btn, after.nextSibling);

  function modal(title, html){
    const ov = document.createElement('div'); ov.className='ominex-modal-backdrop';
    const m  = document.createElement('div'); m.className='ominex-modal';
    m.innerHTML = `<header style="display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border-bottom:1px solid rgba(255,255,255,.06)">
      <strong>${title}</strong><button class="ominex-inline-btn" id="xClose">Close</button></header>
      <div class="body" style="padding:12px 14px">${html}</div>`;
    ov.appendChild(m); document.body.appendChild(ov);
    ov.addEventListener('click', (e)=>{ if(e.target===ov) ov.remove(); });
    m.querySelector('#xClose').onclick = ()=> ov.remove();
    return {ov, body: m.querySelector('.body')};
  }

  btn.onclick = async ()=>{
    const stats = await fetch('/api/learn/topics').then(r=>r.json());
    const { body } = modal('Autonomous Learner',
      `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
        <input id="topicIn" placeholder="Add topic e.g. 'JSE ETFs'" style="flex:1;padding:8px;border-radius:10px;border:1px solid rgba(255,255,255,.08);background:#0b1324;color:#e6edf3">
        <button id="addTopic" class="ominex-inline-btn">Add</button>
        <button id="tickNow" class="ominex-inline-btn">Learn now</button>
      </div>
      <div id="topicList" style="margin-bottom:10px"></div>
      <div style="display:flex;gap:8px;margin-top:6px">
        <input id="qIn" placeholder="Ask what OMINEX learned…" style="flex:1;padding:8px;border-radius:10px;border:1px solid rgba(255,255,255,.08);background:#0b1324;color:#e6edf3">
        <button id="askQ" class="ominex-inline-btn">Ask</button>
      </div>
      <div id="ans" style="margin-top:10px;font-size:14px;opacity:.9"></div>
      <div id="stats" class="ominex-tiny" style="margin-top:8px;opacity:.75"></div>`);

    const render = async ()=>{
      const js = await fetch('/api/learn/topics').then(r=>r.json());
      body.querySelector('#topicList').innerHTML =
        `<strong>Topics:</strong> ${(js.topics||[]).map(t=>`<span class="badge badge-neutral" style="margin-right:6px">${t}</span>`).join('') || '—'}
         `;
      body.querySelector('#stats').textContent =
        `Sources: ${js.stats.sources} | Chunks: ${js.stats.chunks}`;
    };
    render();

    body.querySelector('#addTopic').onclick = async ()=>{
      const t = body.querySelector('#topicIn').value.trim();
      if(!t) return;
      await fetch('/api/learn/topics',{method:'POST',headers:{'Content-Type':'application/json'}, body: JSON.stringify({topic:t})});
      body.querySelector('#topicIn').value = ''; render();
    };
    body.querySelector('#tickNow').onclick = async ()=>{
      const r = await fetch('/api/learn/tick',{method:'POST',headers:{'Content-Type':'application/json'}, body: JSON.stringify({max_per_topic:2})}).then(r=>r.json());
      const msg = 'Learned: ' + Object.entries(r.summary||{}).map(([k,v])=>`${k} (+${v.length})`).join(', ');
      body.querySelector('#ans').textContent = msg;
      render();
    };
    body.querySelector('#askQ').onclick = async ()=>{
      const q = body.querySelector('#qIn').value.trim(); if(!q) return;
      const j = await fetch('/api/learn/query',{method:'POST',headers:{'Content-Type':'application/json'}, body: JSON.stringify({q})}).then(r=>r.json());
      const links = (j.matches||[]).map(m=>`<div style="margin-top:6px"><a href="${m.url}" target="_blank">${m.title||m.url}</a> <span class="ominex-tiny">(${m.score})</span></div>`).join('');
      body.querySelector('#ans').innerHTML = `<div style="white-space:pre-wrap">${(j.answer||'').slice(0,1200)}</div>${links}`;
    };
  };
})();

// Make layout account for the dock
document.body.classList.add('with-dock');

/* ---------- MATRIX RAIN BACKGROUND ---------- */
(function initMatrix(){
  const c = document.getElementById('bg-matrix');
  if (!c) return;
  const ctx = c.getContext('2d');
  const chars = 'アカサタナハマヤラワ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const state = { fontSize: 16, drops: [] };

  function resize(){
    c.width = innerWidth; c.height = innerHeight;
    const cols = Math.floor(c.width / state.fontSize);
    state.drops = Array(cols).fill(1);
  }
  addEventListener('resize', resize); resize();

  (function draw(){
    ctx.fillStyle = 'rgba(0,0,0,0.08)'; ctx.fillRect(0,0,c.width,c.height);
    ctx.fillStyle = '#22ff88'; ctx.shadowColor = '#00ff88'; ctx.shadowBlur = 8;
    ctx.font = state.fontSize + 'px monospace';
    for (let i = 0; i < state.drops.length; i++) {
      const ch = chars[(Math.random()*chars.length)|0];
      const x = i * state.fontSize, y = state.drops[i] * state.fontSize;
      ctx.fillText(ch, x, y);
      if (y > c.height && Math.random() > 0.975) state.drops[i] = 0;
      state.drops[i]++;
    }
    requestAnimationFrame(draw);
  })();
})();

(function initThemes(){
  const layers = {
    matrix: document.getElementById('bg-matrix'),
    grid:   document.getElementById('bg-grid'),
    holo:   document.getElementById('bg-holo')
  };
  const setTheme = (t) => {
    localStorage.setItem('ominexTheme', t);
    ['matrix','grid','holo'].forEach(name => {
      layers[name]?.classList.toggle('hidden', name !== t);
    });
  };
  document.getElementById('themeMatrix')?.addEventListener('click', () => setTheme('matrix'));
  document.getElementById('themeGrid')?.addEventListener('click',   () => setTheme('grid'));
  document.getElementById('themeHolo')?.addEventListener('click',   () => setTheme('holo'));
  setTheme(localStorage.getItem('ominexTheme') || 'matrix');
})();


async function fetchNews(q = "") {
  const el = document.getElementById("chat");
  const res = await fetch(`/api/news?q=${encodeURIComponent(q)}`);
  const data = await res.json();
  const items = data.items || [];
  const block = document.createElement("div");
  block.className = "msg bot";
  block.innerHTML = `
    <div class="bubble">
      <strong>News ${q ? "— " + q : "— Top"}</strong><br/>
      <ul style="margin:6px 0;padding-left:18px;">
        ${items.slice(0,6).map(it => `
          <li>
            <a href="${it.url}" target="_blank" rel="noopener">${it.title}</a>
            ${it.source ? ` — <em>${it.source}</em>` : "" }
          </li>`).join("")}
      </ul>
    </div>`;
  el.appendChild(block);
  el.scrollTop = el.scrollHeight;
}
// Example: fetchNews();  or  fetchNews("Bitcoin")

document.addEventListener("click", () => {
  speechSynthesis.getVoices();
  speak("OMINEX voice system online");
}, { once: true });
