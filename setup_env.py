"""Create .venv and install local training tools; optional browser/agent support."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agents', action='store_true', help='Install locked Node CLIs and Playwright Chromium')
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error('Python 3.11 or newer is required')
    target = ROOT / '.venv'
    python = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(target)
    subprocess.run([str(python), '-m', 'pip', 'install', '--require-hashes', '-r', str(ROOT/'requirements.lock')], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '--no-deps', '-e', str(ROOT)], check=True)
    if args.agents:
        npm = shutil.which('npm')
        node = shutil.which('node')
        if not npm or not node:
            parser.error('Install Node.js 22+ with npm, then rerun --agents')
        subprocess.run([npm, 'ci', '--no-audit', '--no-fund'], cwd=ROOT/'training_runtime', check=True)
        subprocess.run([node, str(ROOT/'training_runtime/node_modules/playwright/cli.js'), 'install', 'chromium'], check=True)
        browser = subprocess.run([node, '-e', "process.stdout.write(require('playwright').chromium.executablePath())"],
                                 cwd=ROOT/'training_runtime', check=True, capture_output=True, text=True).stdout
        (target/'browser.json').write_text(json.dumps({'executablePath': browser})+'\n')
    for name in ('work', 'runs', 'export'):
        (ROOT/name).mkdir(exist_ok=True)
    print(r'Ready. Activate .venv: .venv\Scripts\Activate.ps1 (PowerShell) or source .venv/bin/activate (Bash).')
    print('Then run: abb doctor --offline')


if __name__ == '__main__':
    main()
