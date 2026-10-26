const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 360, height: 1600 }, deviceScaleFactor: 2 });
  await p.exposeFunction('__nodeFetch', async () => ({ ok: false, status: 0, statusText: '', text: '' }));
  await p.exposeFunction('__fsStat', async () => ({ exists: false })); await p.exposeFunction('__fsRead', async () => '');
  await p.goto('file:///home/claude/work/out_shared/panel_test.html');
  await p.addStyleTag({ content: 'input[type=text],select{background:#1e1e1e!important;color:#f0f0f0!important;border:1px solid #555!important;padding:4px 6px!important;font-size:13px!important}' });
  await p.evaluate(async () => { localStorage.clear(); window.__app.activeDocument = null; window.__hooks = {};
    await window.__uxpCfg.panels['smart-trapper-panel'].create(document.getElementById('root'));
    document.getElementById('status').textContent = 'Ready.'; });
  const box = async (sel) => (await p.$(sel)).boundingBox();
  const panels = await p.$$('.panel');
  await panels[0].screenshot({ path: 'shot_settings.png' });
  await panels[1].screenshot({ path: 'shot_actions.png' });
  const f = await p.$('#fileType'); const fb = await f.boundingBox();
  await p.screenshot({ path: 'shot_picker.png', clip: { x: 0, y: 0, width: 360, height: fb.y + 90 } });
  await b.close();
})();
