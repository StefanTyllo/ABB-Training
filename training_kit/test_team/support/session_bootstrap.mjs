// Supplied infrastructure: validate the no-login fixture and export Playwright state.
import { parseArgs } from 'node:util';
import { mkdir, writeFile, lstat, chmod } from 'node:fs/promises';
import { resolve, relative, dirname, isAbsolute } from 'node:path';
import { chromium } from '/opt/abb/node/node_modules/playwright/index.mjs';

let values, target, state, report;
try {
  ({ values } = parseArgs({ options: Object.fromEntries(
    ['mode', 'url', 'state', 'report'].map(name => [name, { type: 'string' }])) }));
  for (const key of ['mode', 'url', 'state', 'report']) {
    if (!values[key]) throw Error('Missing required parameter');
  }
  if (!['no-login', 'login'].includes(values.mode)) throw Error('Invalid mode');
  target = new URL(values.url);
  if (!['http:', 'https:'].includes(target.protocol) || target.username || target.password || target.search) {
    throw Error('Use an HTTP(S) fixture URL without credentials or query parameters');
  }
  const within = async value => {
    const path = resolve(value), rel = relative(process.cwd(), path);
    if (!rel || rel.startsWith('..') || isAbsolute(rel)) throw Error('Output must remain in this workspace');
    for (let cursor=path; cursor!==process.cwd(); cursor=dirname(cursor)) {
      try {
        if ((await lstat(cursor)).isSymbolicLink()) throw Error('Symlink output rejected');
      } catch (error) { if (error.code !== 'ENOENT') throw error; }
    }
    return path;
  };
  state = await within(values.state); report = await within(values.report);
  if (state === report) throw Error('State and report must be separate files');
} catch {
  console.error('Required: --mode no-login|login --url HTTP_URL --state PATH --report PATH');
  process.exit(2);
}
await mkdir(dirname(report), { recursive: true });
async function save(data) {
  await writeFile(report, JSON.stringify({ ...data, authenticated: false, origin: target.origin }, null, 2)+'\n');
}
if (values.mode === 'login') {
  await save({ status: 'BLOCKED', reason: 'No reviewed login adapter is supplied for this fixture' });
  process.exit(3);
}
let browser, phase = "browser-start";
try {
  browser = await chromium.launch({ executablePath: process.env.CHROME_BINARY,
                                    headless: true, chromiumSandbox: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  phase = "navigation";
  await page.goto(target.href, { timeout: 10000 });
  phase = 'fixture-ready';
  await page.locator('#settings[aria-busy="false"]').waitFor({ timeout: 5000 });
  phase = 'dynamic-tcp';
  await page.locator('#connection').selectOption('tcp');
  await page.locator('#host:visible').waitFor({ timeout: 5000 });
  phase = 'dynamic-serial';
  await page.locator('#connection').selectOption('serial');
  await page.locator('#device:visible').waitFor({ timeout: 5000 });
  await mkdir(dirname(state), { recursive: true, mode: 0o700 });
  await context.storageState({ path: state });
  await chmod(state, 0o600);
  await save({ status: 'PASS', mode: 'no-login', state: relative(process.cwd(), state),
               browser: browser.version(), dynamicFields: true });
  console.log('PASS: no-login fixture validated; state does not authenticate Selenium');
} catch (error) {
  // Never serialize arbitrary page content, URLs, exception messages or input values.
  await save({ status: 'FAIL', phase, errorType: error.name, reason: 'Browser or fixture validation failed',
               evidence: 'No page text, cookies or input values were included in this report' });
  console.error('FAIL: fixture validation failed; see sanitized report');
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
}
