"""Disposable factual checks; never inspect or modify a completed learner task."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def run_checks(offline: bool) -> dict:
    checks, versions = {}, {}
    manifest = json.loads(Path('/opt/abb/runtime/runtime.lock.json').read_text())
    def check(name, command, expected=None, blocked=False, cwd=None):
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=cwd)
            passed = run.returncode == 0 and (expected is None or expected in run.stdout)
            checks[name] = {'status': 'PASS' if passed else ('BLOCKED' if blocked else 'FAIL'),
                            'exit': run.returncode}
            return run.stdout.strip() if passed else None
        except (OSError, subprocess.TimeoutExpired) as error:
            checks[name] = {'status': 'BLOCKED' if blocked else 'FAIL', 'reason': type(error).__name__}
            return None
    versions['python'] = sys.version.split()[0]
    checks['non_root'] = {'status': 'PASS' if os.getuid() != 0 else 'FAIL'}
    for tool, expected in [('node', 'v22.23.3'), ('codex', '0.162.1'), ('copilot', '1.0.97')]:
        versions[tool] = check(tool, [tool, '--version'], expected)
    for variable in ['CHROME_BINARY', 'CHROMEDRIVER']:
        versions[variable] = check(variable, [os.environ[variable], '--version'], manifest['chrome']['version'])
    with tempfile.TemporaryDirectory(prefix='abb-doctor-') as directory:
        temp = Path(directory)
        source = temp / 'probe.c'
        source.write_text('int main(void){return 0;}\n')
        if check('compiler', ['gcc', str(source), '-o', str(temp/'probe')]) is not None:
            check('compiled_program', [str(temp/'probe')])
        check('codex_sandbox', ['codex', 'sandbox', '--', 'sh', '-c', 'printf sandbox-ok'],
              'sandbox-ok', blocked=True, cwd=temp)
        check('preparation', [sys.executable, '/opt/abb/materials/prepare_lab.py',
                              'fw1', 'demo', str(temp/'clean-work')])
        browser_script = '''import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
o=webdriver.ChromeOptions(); o.binary_location=os.environ['CHROME_BINARY']; o.add_argument('--headless=new')
with webdriver.Chrome(service=Service(os.environ['CHROMEDRIVER']),options=o) as b:
 b.get('chrome://sandbox')
 assert 'You are adequately sandboxed.' in b.find_element('tag name','body').text
'''
        check('selenium_sandbox', [sys.executable, '-c', browser_script], blocked=True)
        playwright_script = '''const {chromium}=require('/opt/abb/node/node_modules/playwright');
(async()=>{let b=await chromium.launch(require('/opt/abb/runtime/playwright.json').browser.launchOptions);
try {let p=await b.newPage();await p.goto('chrome://sandbox');
if(!(await p.locator('body').innerText()).includes('You are adequately sandboxed.'))throw Error('sandbox');
}finally{await b.close();}})().catch(()=>{process.exitCode=1});'''
        check('playwright_sandbox', ['node', '-e', playwright_script], blocked=True)
    for directory in ['/workspace/work', '/workspace/runs', '/workspace/export']:
        checks[directory] = {'status': 'PASS' if os.access(directory, os.W_OK) else 'FAIL'}
    checks['accounts'] = {'status': 'UNTESTED' if offline else 'BLOCKED',
                          'reason': 'A real opted-in provider tool call is required to verify account access'}
    statuses = [v['status'] for v in checks.values()]
    status = 'FAIL' if 'FAIL' in statuses else 'BLOCKED' if 'BLOCKED' in statuses else 'PASS'
    return {'status': status, 'checks': checks, 'versions': versions, 'workspace': '/workspace',
            'image': {'id': os.environ.get('ABB_IMAGE_ID', 'unrecorded'), 'runtime': manifest}}
