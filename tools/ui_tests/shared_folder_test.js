// Shared Dropbox folder checks - run AFTER run_trapper_button_test.js (uses its panel_test.html).
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.argv[2] || '/home/claude/work/out';
const EXAMPLE = process.argv[3];                       // docs/shared_folder/presets.example.json
const SH = '/home/claude/work/shared_test/SmartTrapper Shared';
let pass = 0, fail = 0;
const check = (n, ok, x) => { ok ? pass++ : fail++; console.log((ok ? 'PASS ' : 'FAIL ') + n + (x ? '  ' + x : '')); };
const doc = { id: 7, title: 'p.psd', mode: 'RGBColorMode', resolution: 300, width: 300, height: 300,
  layers: ['key', 'blue', 'red', 'paper'].map((n, i) => ({ id: i + 1, name: n, kind: 'pixel', visible: true, blendMode: 'normal', opacity: 100, fillOpacity: 100 })) };
function folder(presetsText) { fs.rmSync(SH, { recursive: true, force: true }); fs.mkdirSync(SH, { recursive: true });
  if (presetsText !== undefined) fs.writeFileSync(SH + '/presets.json', presetsText); }
(async () => {
  const browser = await chromium.launch();
  async function open(saved, pick) {
    const page = await browser.newPage();
    page.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
    await page.exposeFunction('__nodeFetch', async (url, opts) => { try { const r = await fetch(url, opts); return { ok: r.ok, status: r.status, statusText: r.statusText, text: await r.text() }; } catch (e) { throw new Error('Failed to fetch'); } });
    await page.exposeFunction('__fsStat', async (p) => { try { const s = fs.statSync(p); return { exists: true, isFolder: s.isDirectory() }; } catch (e) { return { exists: false }; } });
    await page.exposeFunction('__fsRead', async (p) => fs.readFileSync(p, 'utf8'));
    await page.exposeFunction('__mkdir', async (p) => { fs.mkdirSync(p, { recursive: true }); return true; });
    await page.exposeFunction('__makeJob', async () => { const d = '/home/claude/work/TrapJobs/sf_' + Date.now(); fs.cpSync('/home/claude/work/job_ok', d, { recursive: true }); return d; });
    await page.goto('file://' + OUT + '/panel_test.html');
    await page.evaluate((s) => { localStorage.clear(); if (s) localStorage.setItem('smartTrapperSettings', JSON.stringify(s)); }, saved);
    await page.reload();
    await page.evaluate(async ({ doc, pick }) => { window.__app.activeDocument = doc; window.__pickFolder = pick;
      window.__hooks = { knockout: { ok: true, operations: 1 }, prepare: { ok: true, warnings: [] }, import: { ok: true, total: 2, placed: 2, failed: 0 },
        exportMasks: async () => ({ jobFolder: await window.__makeJob(), document: {}, inferred: {}, topLevelLayers: [], exportedMasks: [] }) };
      await window.__uxpCfg.panels['smart-trapper-panel'].create(document.getElementById('root')); }, { doc, pick });
    return page;
  }
  const st = (p) => p.evaluate(() => ({ note: document.getElementById('sharedFolderNote').textContent, shown: document.getElementById('sharedFolderDisplay').textContent,
    opts: [...document.getElementById('fileType').options].map((o) => o.value + '=' + o.textContent), sel: document.getElementById('fileType').value,
    status: document.getElementById('status').textContent, settings: window.__ctl.getSettings(), stored: JSON.parse(localStorage.getItem('smartTrapperSettings') || 'null') }));
  const ex = JSON.parse(fs.readFileSync(EXAMPLE, 'utf8'));

  // 1 not set
  let p = await open(null); let s = await st(p);
  check('not set: built-in presets, says so', /not set - using the built-in presets/.test(s.note) && /Presets: Shared folder not set/.test(s.status), s.note);
  check('not set: picker has the 4 types + Custom', s.opts.length === 5);
  // 9 pick it with the button (folder with the example presets)
  folder(JSON.stringify(ex));
  await p.evaluate((f) => { window.__pickFolder = f; }, SH); await p.click('#pickSharedFolderBtn'); await p.waitForTimeout(300); s = await st(p);
  check('picked: path shown and remembered (token saved)', s.shown === SH && s.stored.sharedFolderToken === 'tok:' + SH, s.shown);
  check('picked: presets come from the shared folder', /from the shared folder, updated 2026-10-26 by Sara/.test(s.note), s.note);
  await p.close();
  // survives a restart
  p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH, bridgeUrl: 'http://127.0.0.1:8765' }); s = await st(p);
  check('after restart: still using the shared presets', /from the shared folder/.test(s.note) && /Presets: shared presets.json/.test(s.status));
  await p.close();
  // 2 shared file differs from built-in: Standard trap 6 -> fresh install starts on 6; saved settings untouched
  const ex6 = JSON.parse(JSON.stringify(ex)); ex6.always.trapPx = 6; ex6.types[0].label = 'Illustrated (team)'; folder(JSON.stringify(ex6));
  p = await open(null); await p.evaluate(async (f) => { window.__pickFolder = f; }, SH); await p.click('#pickSharedFolderBtn'); await p.waitForTimeout(300); s = await st(p);
  check('team label shown in the picker', s.opts.some((o) => o === 'standard=Illustrated (team)'), JSON.stringify(s.opts));
  check('existing settings NOT changed by a different shared preset (shows ADJUSTED)', s.settings.trapPx === 5, 'trapPx ' + s.settings.trapPx);
  await p.close();
  p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH }); s = await st(p);
  check('saved settings kept on restart even though team Standard is trap 6', s.settings.trapPx === 5);
  await p.close();
  // a brand-new install that already knows the folder starts on the team's Standard values
  p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH, fileType: 'standard', trapPx: 5 });  // not fresh
  s = await st(p); await p.close();
  // 3 presets.json missing
  folder(undefined); p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH }); s = await st(p);
  check('presets.json missing: built-in + says so', /not in the shared folder yet/.test(s.note) && s.opts.length === 5, s.note); await p.close();
  // 4 broken JSON
  folder('{ "types": [ oops'); p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH }); s = await st(p);
  check('broken presets.json: built-in + says so', /could not be used/.test(s.note), s.note); await p.close();
  // 4b a bad value is ignored and listed, the rest used
  const exBad = JSON.parse(JSON.stringify(ex)); exBad.types[1].settings.roundTraps = 'no'; exBad.always.trapPx = 500; folder(JSON.stringify(exBad));
  p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH }); s = await st(p);
  check('bad values ignored and listed', /Ignored in presets.json/.test(s.note) && /roundTraps should be true\/false/.test(s.note) && /trapPx = 500/.test(s.note), s.note); await p.close();
  // 5 Dropbox offline / folder gone -> built-in, Run Trapper still works
  folder(JSON.stringify(ex)); fs.rmSync(SH, { recursive: true, force: true });
  p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH, bridgeUrl: 'http://127.0.0.1:8765' }); s = await st(p);
  check('offline: built-in + says so', /not reachable/.test(s.note), s.note);
  await p.evaluate(() => document.getElementById('runAllBtn').click());
  await p.waitForFunction(() => window.__alerts.length > 0 && !document.getElementById('runAllBtn').disabled, null, { timeout: 60000 });
  const alert = await p.evaluate(() => window.__alerts[0]);
  check('offline: Run Trapper still FINISHES', /^RUN TRAPPER FINISHED/.test(alert), alert.split('\n')[0]);
  s = await st(p); check('offline: run log says which presets were used', /Presets: built-in presets/.test(s.status)); await p.close();
  // 6 job.json identical: shared Standard vs boxes by hand
  folder(JSON.stringify(ex));
  p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH, fileType: 'custom' });
  await p.evaluate(() => { const e = document.getElementById('fileType'); e.value = 'geometric'; e.dispatchEvent(new Event('change')); });
  const ja = await p.evaluate((d) => window.__ctl.buildCurrentJobSpec(d).job, doc); await p.close();
  const hand = Object.assign({}, ex.always, ex.types[1].settings, { fileType: 'custom' });
  p = await open(hand); const jb = await p.evaluate((d) => window.__ctl.buildCurrentJobSpec(d).job, doc); await p.close();
  check('job.json identical: shared Geometric vs the same boxes by hand', JSON.stringify(ja) === JSON.stringify(jb));
  // 7 the REAL shared presets.json (shared_folder/presets.json in git = the Dropbox copy)
  const REAL = process.argv[4];
  if (REAL) {
    folder(fs.readFileSync(REAL, 'utf8'));
    p = await open({ sharedFolderToken: 'tok:' + SH, sharedFolderPath: SH, fileType: 'overlay', bridgeUrl: 'http://127.0.0.1:8765',
      preflightCleanup: true, roundTraps: true, closeKeyHalo: false, overlayLayers: true, smoothKeyTraps: true, bevelKeyCorners: true,
      keyTrapsFollowVisible: true, tonalInks: false, alphaThreshold: 90, edgeBiasPx: 1, keyTrapPullbackPx: 1, colorTrapPullbackPx: 0, trapPx: 5 });
    s = await st(p);
    check('real presets.json: read, nothing ignored', /from the shared folder, updated 2026-10-26 by Sara\.$/.test(s.note), s.note);
    check('real presets.json: Sara\'s MMJ settings show as Overlay, not adjusted', s.sel === 'overlay' && !/ADJUSTED/.test(await p.evaluate(() => document.getElementById('fileTypeNote').textContent)));
    check('real presets.json: labels from the file', s.opts.includes('standard=Standard poster (illustrated / organic)'), JSON.stringify(s.opts));
    await p.close();
  }
  await browser.close();
  console.log('\n' + pass + ' passed, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
