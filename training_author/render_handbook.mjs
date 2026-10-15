import { chromium } from '/opt/abb/node/node_modules/playwright/index.mjs';
import { pathToFileURL } from 'node:url';
const [input, output] = process.argv.slice(2);
if (!input || !output) throw Error('Expected HTML input and PDF output paths');
const browser = await chromium.launch({ executablePath: process.env.CHROME_BINARY,
                                        headless: true, chromiumSandbox: true });
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(input).href);
  await page.pdf({ path: output, format: 'A4', printBackground: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#555">ABB workflow training · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    margin: { top: '16mm', bottom: '18mm', left: '16mm', right: '16mm' } });
} finally { await browser.close(); }
