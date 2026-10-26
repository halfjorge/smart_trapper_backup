// Tests for "What kind of file is this?" - run AFTER run_trapper_button_test.js (uses its panel_test.html).
const { chromium } = require('playwright');
const OUT = process.argv[2] || '/home/claude/work/out';
const TYPE_VALUES = {
  standard: { fullDebug: false, preflightCleanup: true, roundTraps: true, closeKeyHalo: false, overlayLayers: false, smoothKeyTraps: true, bevelKeyCorners: true, keyTrapsFollowVisible: true, tonalInks: false, alphaThreshold: 90, edgeBiasPx: 1, keyTrapPullbackPx: 1, colorTrapPullbackPx: 0, trapPx: 5 },
};
TYPE_VALUES.geometric = Object.assign({}, TYPE_VALUES.standard, { roundTraps: false, keyTrapsFollowVisible: false });
TYPE_VALUES.overlay = Object.assign({}, TYPE_VALUES.standard, { overlayLayers: true });
TYPE_VALUES.tonal = Object.assign({}, TYPE_VALUES.standard, { tonalInks: true });
const KEYS = Object.keys(TYPE_VALUES.standard);
const doc = { id: 7, title: 'p.psd', mode: 'RGBColorMode', resolution: 300, width: 300, height: 300,
  layers: ['key', 'blue', 'red', 'paper'].map((n, i) => ({ id: i + 1, name: n, kind: 'pixel', visible: true, blendMode: 'normal', opacity: 100, fillOpacity: 100 })) };
let pass = 0, fail = 0;
function check(name, ok, extra) { if (ok) pass++; else fail++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (extra ? '  ' + extra : '')); }
const pick = (s) => Object.fromEntries(KEYS.map((k) => [k, s[k]]));
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

(async () => {
  const browser = await chromium.launch();
  async function openPanel(saved) {
    const page = await browser.newPage({ viewport: { width: 380, height: 1500 } });
    await page.exposeFunction('__nodeFetch', async () => ({ ok: false, status: 0, statusText: '', text: '' }));
    await page.exposeFunction('__fsStat', async () => ({ exists: false }));
    await page.exposeFunction('__fsRead', async () => '');
    await page.goto('file://' + OUT + '/panel_test.html');
    await page.evaluate((saved) => { localStorage.clear(); if (saved) localStorage.setItem('smartTrapperSettings', JSON.stringify(saved)); }, saved);
    await page.reload();
    await page.evaluate(async (doc) => { window.__app.activeDocument = doc; window.__hooks = {};
      await window.__uxpCfg.panels['smart-trapper-panel'].create(document.getElementById('root')); }, doc);
    return page;
  }
  const state = (page) => page.evaluate(() => ({ sel: document.getElementById('fileType').value, note: document.getElementById('fileTypeNote').textContent,
    reset: document.getElementById('fileTypeResetBtn').style.display !== 'none', resetText: document.getElementById('fileTypeResetBtn').textContent,
    settings: window.__ctl.getSettings(), stored: JSON.parse(localStorage.getItem('smartTrapperSettings') || 'null') }));
  const choose = (page, id) => page.evaluate((id) => { const s = document.getElementById('fileType'); s.value = id; s.dispatchEvent(new Event('change')); }, id);

  // 1 fresh install
  let page = await openPanel(null); let st = await state(page);
  check('fresh install starts on Standard poster', st.sel === 'standard');
  check('fresh install boxes = Standard values', eq(pick(st.settings), TYPE_VALUES.standard));
  check('note shows the type description, no reset button', /Illustrated \/ organic/.test(st.note) && !st.reset, JSON.stringify(st.note));
  await page.screenshot({ path: OUT + '/picker_fresh.png', clip: { x: 0, y: 0, width: 380, height: 260 } });

  // 2 each type fills the boxes and is remembered
  for (const id of ['geometric', 'overlay', 'tonal', 'standard']) {
    await choose(page, id); st = await state(page);
    check('pick ' + id + ': boxes = its values', eq(pick(st.settings), TYPE_VALUES[id]));
    check('pick ' + id + ': saved (survives Reload)', st.stored && st.stored.fileType === id && eq(pick(st.stored), TYPE_VALUES[id]));
  }
  // 3 bridge URL / folders untouched by picking
  check('picking keeps bridge URL', st.settings.bridgeUrl === 'http://127.0.0.1:8765');

  // 4 adjust after picking, then put back
  await choose(page, 'geometric');
  await page.evaluate(() => { const b = document.getElementById('trapPx'); b.value = '6'; b.dispatchEvent(new Event('change'));
    const c = document.getElementById('roundTraps'); c.checked = true; c.dispatchEvent(new Event('change')); });
  st = await state(page);
  check('adjusted: type still Geometric', st.sel === 'geometric');
  check('adjusted: note lists the changes', /ADJUSTED from Geometric/.test(st.note) && /Trap width 6 \(usual 5\)/.test(st.note) && /Round traps on \(usual off\)/.test(st.note), JSON.stringify(st.note));
  check('adjusted: reset button shown', st.reset && /Put back Geometric/.test(st.resetText));
  check('adjusted values are kept (and saved)', st.settings.trapPx === 6 && st.settings.roundTraps === true && st.stored.trapPx === 6);
  await page.screenshot({ path: OUT + '/picker_adjusted.png', clip: { x: 0, y: 0, width: 380, height: 330 } });
  // reload keeps the adjustment
  await page.reload(); await page.evaluate(async (doc) => { window.__app.activeDocument = doc; window.__hooks = {};
    await window.__uxpCfg.panels['smart-trapper-panel'].create(document.getElementById('root')); }, doc);
  st = await state(page);
  check('after Reload: still Geometric + adjusted values', st.sel === 'geometric' && st.settings.trapPx === 6 && /ADJUSTED/.test(st.note));
  await page.click('#fileTypeResetBtn'); st = await state(page);
  check('put back: Geometric values again, note normal', eq(pick(st.settings), TYPE_VALUES.geometric) && !st.reset);
  // clicking a checkbox's text (toggles in code) also updates the note
  await page.evaluate(() => document.querySelector('.check-text[data-for="closeKeyHalo"]').click()); st = await state(page);
  check('clicking a setting name updates the note', /Close key halo on \(usual off\)/.test(st.note));

  // 5 Custom changes nothing
  const before = pick(st.settings); await choose(page, 'custom'); st = await state(page);
  check('Custom: values unchanged', eq(pick(st.settings), before) && /Your own settings/.test(st.note));
  await page.close();

  // 6 Sara's existing saved settings (saved before the picker existed) are never replaced
  const saraObey = Object.assign({ bridgeUrl: 'http://127.0.0.1:8765', jobFolder: 'C:\\Users\\Valued Customer\\Desktop\\TrapJobs', logFolder: 'C:\\x' }, TYPE_VALUES.geometric);
  page = await openPanel(saraObey); st = await state(page);
  check('Sara Obey settings: shown as Geometric, values unchanged', st.sel === 'geometric' && eq(pick(st.settings), pick(saraObey)));
  await page.close();
  const sara1009 = Object.assign({}, saraObey, TYPE_VALUES.standard, { alphaThreshold: 89 });
  const saraMMJ = Object.assign({ bridgeUrl: 'http://127.0.0.1:8765' }, TYPE_VALUES.overlay);
  page = await openPanel(sara1009); st = await state(page);
  check('Sara alpha-89 settings: shown as Custom, values unchanged', st.sel === 'custom' && eq(pick(st.settings), pick(sara1009)));
  await page.close();
  page = await openPanel(saraMMJ); st = await state(page);
  check('Sara MMJ run-2 settings: shown as Overlay / Multiply, values unchanged', st.sel === 'overlay' && eq(pick(st.settings), pick(saraMMJ)));
  await page.close();
  const oldNoTonal = Object.assign({}, saraObey); delete oldNoTonal.tonalInks; delete oldNoTonal.keyTrapsFollowVisible;
  page = await openPanel(oldNoTonal); st = await state(page);
  check('very old saved settings (missing newer boxes): those stay off as before', st.settings.tonalInks === false && st.settings.keyTrapsFollowVisible === false);
  await page.close();

  // 7 the engine gets the same job settings whether a type is picked or the boxes are ticked by hand
  for (const id of ['standard', 'geometric', 'overlay', 'tonal']) {
    const a = await openPanel(null); await choose(a, id);
    const ja = await a.evaluate((doc) => { const j = window.__ctl.buildCurrentJobSpec(doc).job; return j; }, doc); await a.close();
    const b = await openPanel(Object.assign({ bridgeUrl: 'http://127.0.0.1:8765' }, TYPE_VALUES[id], { fileType: 'custom' }));
    const jb = await b.evaluate((doc) => window.__ctl.buildCurrentJobSpec(doc).job, doc); await b.close();
    check('job.json identical: picker "' + id + '" vs boxes by hand', eq(ja, jb), JSON.stringify(Object.keys(ja)).includes('fileType') ? 'fileType leaked!' : '');
    if (id === 'geometric') console.log('   job.json settings (geometric): ' + JSON.stringify(Object.fromEntries(Object.entries(ja).filter(([k]) => !['colors', 'files', 'docName', 'widthPx', 'heightPx', 'resolution', 'keyLayerName', 'paperLayerName'].includes(k)))));
  }
  await browser.close();
  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
