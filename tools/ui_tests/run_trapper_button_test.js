// Stand-in Photoshop for the combined "Run Trapper" button.
// Real: panel markup + styles, runAllSteps, every check, Run Trapper's (engine) code talking to the REAL
// helper (real_bridge.py) and REAL engine, settings, alerts.  Stand-ins: Photoshop itself (doc/layers),
// and the Photoshop-only parts of the steps (knockout, snapshot, mask export, prepare, import) which
// just record that they were called and return what the real ones return.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const MAIN = process.argv[2], CSS = process.argv[3], OUTDIR = process.argv[4] || '/home/claude/work/out';
fs.mkdirSync(OUTDIR, { recursive: true });
let src = fs.readFileSync(MAIN, 'utf8');
function swap(oldHead, newHead) {
  const n = src.split(oldHead).length - 1;
  if (n !== 1) throw new Error('transform anchor x' + n + ': ' + oldHead);
  src = src.replace(oldHead, newHead);
}
swap('async function runManualProgressiveKnockout() {',
  'async function runManualProgressiveKnockout() { return await window.__hook("knockout"); }\n  async function __real_knockout() {');
swap('async function createOriginalFlattenedSnapshot(',
  'async function createOriginalFlattenedSnapshot(d) { return await window.__hook("snapshot"); }\n  async function __real_snapshot(');
swap('async function exportMasksToJobFolderForRun(',
  'async function exportMasksToJobFolderForRun(p) { const r = await window.__hook("exportMasks"); currentJobFolderEntry = await tryBindFolderEntryFromPath(r.jobFolder); els.jobFolderDisplay.textContent = r.jobFolder; return r; }\n  async function __real_export(');
swap('async function prepareImportStructure() {',
  'async function prepareImportStructure() { return await window.__hook("prepare"); }\n  async function __real_prepare() {');
swap('async function importTraps() {',
  'async function importTraps() { return await window.__hook("import"); }\n  async function __real_import() {');

const STUB = `
window.__alerts = []; window.__calls = [];
window.setInterval = () => 0;
window.fetch = async (url, opts) => { const r = await window.__nodeFetch(String(url), opts ? { method: opts.method, body: opts.body } : {});
  return { ok: r.ok, status: r.status, statusText: r.statusText, text: async () => r.text }; };
function __fileEntry(p) { return { isFile: true, isFolder: false, name: p.split('/').pop(), nativePath: p, read: async () => window.__fsRead(p) }; }
function __folderEntry(p) { return { isFile: false, isFolder: true, name: p.split('/').pop(), nativePath: p,
  getEntry: async (n) => { const q = p + '/' + n; const s = await window.__fsStat(q); if (!s.exists) throw new Error('not found ' + q); return s.isFolder ? __folderEntry(q) : __fileEntry(q); } }; }
const __lfs = { getEntryWithUrl: async (u) => { const p = String(u).replace(/^file:/, ''); const s = await window.__fsStat(p);
  if (!s.exists) throw new Error('no ' + p); return s.isFolder ? __folderEntry(p) : __fileEntry(p); } };
window.__app = { activeDocument: null, showAlert: async (m) => { window.__alerts.push(String(m)); } };
window.require = (m) => {
  if (m === 'uxp') return { entrypoints: { setup: (cfg) => { window.__uxpCfg = cfg; } }, storage: { localFileSystem: __lfs, formats: {} } };
  if (m === 'photoshop') return { app: window.__app, core: { executeAsModal: async (f) => f({}) }, constants: {}, action: { batchPlay: async () => [{}] } };
  throw new Error('module ' + m);
};
window.__hook = async (name) => { window.__calls.push(name); const h = window.__hooks[name]; return typeof h === 'function' ? await h() : h; };
`;
const html = `<!doctype html><html><head><meta charset="utf-8"><style>${fs.readFileSync(CSS, 'utf8')}</style></head>
<body style="width:360px;background:#323232;margin:0"><div id="root"></div><script>${STUB}</script><script>${src}</script></body></html>`;
fs.writeFileSync(OUTDIR + '/panel_test.html', html);

const TEMPLATES = { ok: process.env.JOB_OK || '/home/claude/work/job_ok', zero: process.env.JOB_ZERO || '/home/claude/work/job_zero', broken: '/home/claude/work/job_broken' };
const JOBS = '/home/claude/work/TrapJobs';

function layer(id, name, extra) { return Object.assign({ id, name, kind: 'pixel', visible: true, blendMode: 'normal', opacity: 100, fillOpacity: 100 }, extra || {}); }
function poster(extra) { return Object.assign({ id: 7, title: 'test_poster.psd', mode: 'RGBColorMode', resolution: 300,
  width: 300, height: 300, layers: [layer(1, 'key'), layer(2, 'blue'), layer(3, 'red'), layer(4, 'paper')] }, extra || {}); }

// What the real Photoshop-only steps return (shapes copied from the patched main.js).
const OK = { knockout: { ok: true, operations: 3 }, snapshot: undefined, prepare: { ok: true, wrapped: 2, skipped: 0, warnings: [] },
  import: { ok: true, total: 3, placed: 3, failed: 0 } };

const scenarios = [
  { name: 'A normal file, everything works', doc: poster(), job: 'ok' },
  { name: 'B Tonal inks ticked -> knockout skipped', doc: poster(), job: 'ok', ticks: ['tonalInks'] },
  { name: 'C no document open', doc: null, job: 'ok' },
  { name: 'D file already trapped (COLOR__ groups)', doc: poster({ layers: [layer(1, 'key'), layer(2, 'COLOR__blue', { kind: 'group' }), layer(3, 'COLOR__red', { kind: 'group' }), layer(4, 'paper')] }), job: 'ok' },
  { name: 'E helper not running', doc: poster(), job: 'ok', bridge: 'http://127.0.0.1:8799' },
  { name: 'F overlay layer, overlay box OFF', doc: poster({ layers: [layer(1, 'key'), layer(2, 'blue', { blendMode: 'multiply' }), layer(3, 'red'), layer(4, 'paper')] }), job: 'ok' },
  { name: 'G overlay layer, overlay box ON', doc: poster({ layers: [layer(1, 'key'), layer(2, 'blue', { blendMode: 'multiply' }), layer(3, 'red'), layer(4, 'paper')] }), job: 'ok', ticks: ['overlayLayers'] },
  { name: 'H 600 ppi file', doc: poster({ resolution: 600 }), job: 'ok' },
  { name: 'I CMYK file', doc: poster({ mode: 'CMYKColorMode' }), job: 'ok' },
  { name: 'J trap width 0', doc: poster(), job: 'ok', fields: { trapPx: '0' } },
  { name: 'K knockout fails part-way', doc: poster(), job: 'ok', hooks: { knockout: { ok: false, reason: 'Error: progressive knockout clear failed for blue -> red' } } },
  { name: 'L engine fails (broken job)', doc: poster(), job: 'broken' },
  { name: 'M engine makes 0 traps', doc: poster(), job: 'zero' },
  { name: 'N prepare: one colour gets no CLEAN layer', doc: poster(), job: 'ok', hooks: { prepare: { ok: true, wrapped: 2, skipped: 0, warnings: ["No CLEAN layer for 'blue ': clean mask file not found"] } } },
  { name: 'O import: 1 trap layer fails', doc: poster(), job: 'ok', hooks: { import: { ok: true, total: 3, placed: 2, failed: 1 } } },
  { name: 'P a step throws unexpectedly', doc: poster(), job: 'ok', hooks: { prepare: '__throw__' } },
  { name: 'Q only 2 layers', doc: poster({ layers: [layer(1, 'key'), layer(4, 'paper')] }), job: 'ok' },
];

(async () => {
  const browser = await chromium.launch();
  const results = [];
  for (const sc of scenarios.concat([{ name: 'R double-click while running', doc: poster(), job: 'ok', double: true }])) {
    const page = await browser.newPage({ viewport: { width: 380, height: 1500 } });
    page.on('pageerror', (e) => console.log('PAGE ERROR', sc.name, e.message));
    await page.exposeFunction('__nodeFetch', async (url, opts) => {
      try { const r = await fetch(url, opts); return { ok: r.ok, status: r.status, statusText: r.statusText, text: await r.text() }; }
      catch (e) { throw new Error('Failed to fetch: ' + e.message); } });
    await page.exposeFunction('__fsStat', async (p) => { try { const s = fs.statSync(p); return { exists: true, isFolder: s.isDirectory() }; } catch (e) { return { exists: false }; } });
    await page.exposeFunction('__fsRead', async (p) => fs.readFileSync(p, 'utf8'));
    await page.exposeFunction('__makeJob', async (t) => { const d = JOBS + '/test_poster__UXP__' + Date.now() + Math.floor(Math.random() * 1000);
      fs.mkdirSync(d, { recursive: true }); fs.cpSync(TEMPLATES[t], d, { recursive: true }); return d; });
    await page.goto('file://' + OUTDIR + '/panel_test.html');
    await page.evaluate(async ({ sc, OK }) => {
      window.__app.activeDocument = sc.doc;
      const hooks = Object.assign({}, OK, sc.hooks || {});
      if (hooks.prepare === '__throw__') hooks.prepare = () => { throw new Error('Photoshop said: the command is not currently available'); };
      hooks.exportMasks = async () => ({ jobFolder: await window.__makeJob(sc.job), document: { title: sc.doc && sc.doc.title }, inferred: {}, topLevelLayers: [], exportedMasks: [] });
      window.__hooks = hooks;
      const root = document.getElementById('root');
      await window.__uxpCfg.panels['smart-trapper-panel'].create(root);
      (sc.ticks || []).forEach((id) => { const b = document.getElementById(id); b.checked = true; b.dispatchEvent(new Event('change')); });
      Object.entries(sc.fields || {}).forEach(([id, v]) => { const b = document.getElementById(id); b.value = v; b.dispatchEvent(new Event('change')); });
    }, { sc, OK });
    if (sc.bridge) {
      // point the panel at a port where nothing is listening (as if the helper was never started)
      await page.evaluate((u) => { localStorage.setItem('smartTrapperSettings', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('smartTrapperSettings') || '{}'), { bridgeUrl: u }))); }, sc.bridge);
      await page.reload();
      await page.evaluate(async ({ sc, OK }) => {
        window.__app.activeDocument = sc.doc;
        window.__hooks = Object.assign({}, OK, { exportMasks: async () => ({ jobFolder: await window.__makeJob(sc.job), document: {}, inferred: {}, topLevelLayers: [], exportedMasks: [] }) });
        await window.__uxpCfg.panels['smart-trapper-panel'].create(document.getElementById('root'));
      }, { sc, OK });
    }
    if (sc.name.startsWith('A')) await page.screenshot({ path: OUTDIR + '/panel_before_run.png', fullPage: true });
    await page.evaluate((dbl) => { const b = document.getElementById('runAllBtn'); b.click(); if (dbl) b.click(); }, !!sc.double);
    await page.waitForFunction(() => window.__alerts.length > 0 && !document.getElementById('runAllBtn').disabled, null, { timeout: 60000 });
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => ({ calls: window.__calls.slice(), alerts: window.__alerts.slice(),
      progress: document.getElementById('runProgressLabel').textContent, status: document.getElementById('status').textContent }));
    if (sc.name.startsWith('A')) await page.screenshot({ path: OUTDIR + '/panel_after_run.png', fullPage: true });
    if (sc.name.startsWith('E')) await page.screenshot({ path: OUTDIR + '/panel_helper_not_running.png', fullPage: true });
    results.push({ name: sc.name, ...r });
    await page.close();
  }
  // individual buttons still behave as before (Sara's copy)
  const page = await browser.newPage({ viewport: { width: 380, height: 1500 } });
  await page.exposeFunction('__nodeFetch', async (url, opts) => { const r = await fetch(url, opts); return { ok: r.ok, status: r.status, statusText: r.statusText, text: await r.text() }; });
  await page.exposeFunction('__fsStat', async (p) => { try { const s = fs.statSync(p); return { exists: true, isFolder: s.isDirectory() }; } catch (e) { return { exists: false }; } });
  await page.exposeFunction('__fsRead', async (p) => fs.readFileSync(p, 'utf8'));
  await page.exposeFunction('__makeJob', async (t) => { const d = JOBS + '/indiv_' + Date.now(); fs.mkdirSync(d, { recursive: true }); fs.cpSync(TEMPLATES[t], d, { recursive: true }); return d; });
  await page.goto('file://' + OUTDIR + '/panel_test.html');
  const indiv = await page.evaluate(async ({ doc, OK }) => {
    window.__app.activeDocument = doc;
    window.__hooks = Object.assign({}, OK, { exportMasks: async () => ({ jobFolder: await window.__makeJob('ok'), document: {}, inferred: {}, topLevelLayers: [], exportedMasks: [] }) });
    await window.__uxpCfg.panels['smart-trapper-panel'].create(document.getElementById('root'));
    const out = [];
    for (const id of ['manualKnockoutBtn', 'runBtn', 'prepareImportBtn', 'importTrapsBtn']) {
      const n = window.__alerts.length; document.getElementById(id).click();
      while (window.__alerts.length === n) await new Promise((r) => setTimeout(r, 50));
      out.push(id + ' -> called ' + window.__calls[window.__calls.length - 1] + ', alert "' + window.__alerts[window.__alerts.length - 1] + '"');
    }
    out.push('engine-only status: ' + (document.getElementById('status').textContent.match(/Traps made by the engine: \d+/) || ['?'])[0]);
    return out;
  }, { doc: poster(), OK });
  await browser.close();
  fs.writeFileSync(OUTDIR + '/results.json', JSON.stringify({ results, indiv }, null, 2));
  for (const r of results) {
    console.log('\n### ' + r.name + '\n  steps called: ' + (r.calls.join(' -> ') || '(none)') + '\n  progress: ' + r.progress + '\n  alerts: ' + r.alerts.length +
      '\n  ' + r.alerts[0].split('\n').join('\n  '));
  }
  console.log('\n### Individual buttons (Sara\'s copy)\n  ' + indiv.join('\n  '));
})().catch((e) => { console.error(e); process.exit(1); });
