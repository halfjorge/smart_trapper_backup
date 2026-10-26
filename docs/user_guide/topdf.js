const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file:///home/claude/work/guide/guide.html'); await p.waitForTimeout(500);
  await p.pdf({ path: '/home/claude/work/guide/Smart_Trapper_Guide.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true, headerTemplate: '<span></span>', footerTemplate: '<div style="font-size:8px;color:#999;width:100%;text-align:center;font-family:sans-serif">Smart Trapper guide - page <span class="pageNumber"></span> of <span class="totalPages"></span></div>' });
  await b.close(); })();
