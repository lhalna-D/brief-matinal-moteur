// Usage : node pdf.js page.html sortie.pdf
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [, , src, out] = process.argv;
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + path.resolve(src));
  await p.waitForTimeout(300);
  await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:7px;color:#898781;width:100%;text-align:center;font-family:Carlito,sans-serif">Brief Matinal · page <span class="pageNumber"></span>/<span class="totalPages"></span></div>' });
  await b.close();
  console.log('PDF :', out);
})();
