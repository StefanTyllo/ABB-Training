"""Run in the candidate image, offline, as its ordinary non-root user."""
import os
from pathlib import Path
import re
import subprocess


def run(*args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, timeout=60, **kwargs)


def test_codex_sandbox_shell(tmp_path):
    assert os.getuid() != 0
    result = run("codex", "sandbox", "--", "sh", "-c",
                 "printf sandbox-ok", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "sandbox-ok"


def test_pinned_browser_driver_pair():
    browser = run(os.environ["CHROME_BINARY"], "--version")
    driver = run(os.environ["CHROMEDRIVER"], "--version")
    assert browser.returncode == driver.returncode == 0
    assert re.search(r"\d+\.\d+\.\d+\.\d+", browser.stdout)[0] == re.search(
        r"\d+\.\d+\.\d+\.\d+", driver.stdout)[0]


def test_real_chrome_sandbox():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    assert os.getuid() != 0
    options = webdriver.ChromeOptions()
    options.binary_location = os.environ["CHROME_BINARY"]
    options.add_argument("--headless=new")
    with webdriver.Chrome(service=Service(os.environ["CHROMEDRIVER"]), options=options) as browser:
        browser.get("data:text/html,<button onclick=\"setTimeout(()=>{document.body.innerHTML='<input id=late>'},100)\">Add</button>")
        browser.find_element(By.TAG_NAME, "button").click()
        field = WebDriverWait(browser, 5).until(lambda b: b.find_element(By.ID, "late"))
        field.send_keys("sandboxed")
        assert field.get_attribute("value") == "sandboxed"
        browser.get("chrome://sandbox")
        status = browser.find_element(By.TAG_NAME, "body").text
        assert re.search(r"Layer 1 Sandbox\s+Namespace", status), status
        assert re.search(r"PID namespaces\s+Yes", status), status
        assert re.search(r"Network namespaces\s+Yes", status), status
        assert re.search(r"Seccomp-BPF sandbox\s+Yes", status), status


def test_offline_toolchain(tmp_path):
    assert os.getuid() != 0
    source = tmp_path / "probe.c"
    source.write_text('#include <stdio.h>\nint main(void){puts("compiler-ok");return 0;}\n')
    binary = tmp_path / "probe"
    compiled = run("gcc", str(source), "-o", str(binary))
    assert compiled.returncode == 0, compiled.stderr
    assert run(str(binary)).stdout == "compiler-ok\n"
    assert run("node", "--version").stdout.strip() == "v22.23.3"
    assert run("copilot", "--version").returncode == 0
    assert run("codex", "--version").stdout.strip() == "codex-cli 0.162.1"


def test_playwright_sandbox():
    script = """
const {chromium} = require('/opt/abb/node/node_modules/playwright');
const config = require('/opt/abb/runtime/playwright.json');
(async () => {
  const browser = await chromium.launch(config.browser.launchOptions);
  try {
    const page = await browser.newPage();
    await page.goto('chrome://sandbox');
    const status = await page.locator('body').innerText();
    if (!status.includes('You are adequately sandboxed.')) throw Error(status);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode=1; });
"""
    result = run("node", "-e", script)
    assert result.returncode == 0, result.stderr


def test_image_owned_materials_and_os_lock():
    assert not os.access('/opt/abb/materials', os.W_OK)
    assert not os.access('/opt/abb/repo', os.W_OK)
    assert not os.access('/opt/abb/materials/firmware/fw1/expected.json', os.W_OK)
    assert os.access('/workspace/work', os.W_OK)
    for relative in ['firmware/instructor', 'hardware/instructor', 'hardware/tests', 'test_team/author_checks']:
        assert not Path('/opt/abb/materials', relative).exists()
    installed = run('dpkg-query', '-W')
    assert installed.returncode == 0
    assert installed.stdout == Path('/opt/abb/repo/docker/os-packages.lock').read_text()


def test_retained_fixture_checks_in_disposable_writable_copy(tmp_path):
    import shutil
    root = tmp_path/'materials'
    shutil.copytree('/opt/abb/repo/training_kit', root)
    for path in [root, *root.rglob('*')]:
        if not path.is_symlink():
            path.chmod(path.stat().st_mode | 0o200)
    import sys
    for relative in ['hardware/tests/test_starters.py', 'firmware/instructor/smoke.py',
                     'test_team/author_checks/check_server.py']:
        result = run(sys.executable, str(root/relative))
        assert result.returncode == 0, result.stdout+result.stderr
