"""Disposable checks of the active local environment."""
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .paths import ROOT, WORK, EXPORT, NODE_MODULES, provider_command


def run_checks(offline: bool) -> dict:
    checks = {}
    versions = {'python': sys.version.split()[0]}
    checks['virtual_environment'] = {'status': 'PASS' if sys.prefix != sys.base_prefix else 'FAIL'}
    for package in ('pytest', 'selenium', 'pypdf', 'PyYAML', 'markdown-it-py'):
        try:
            versions[package] = importlib.metadata.version(package)
            checks[package] = {'status': 'PASS'}
        except importlib.metadata.PackageNotFoundError:
            checks[package] = {'status': 'FAIL', 'reason': 'Rerun setup_env.py'}
    for tool in ('git', 'gcc', 'node', 'codex', 'copilot'):
        executable = provider_command(tool) if tool in ('codex', 'copilot') else shutil.which(tool)
        present = bool(executable and (Path(executable).is_file() or shutil.which(executable)))
        checks[tool] = {'status': 'PASS' if present else 'BLOCKED',
                        'reason': 'Available' if present else 'Install this host tool; Node agents can be installed with setup_env.py --agents'}
    with tempfile.TemporaryDirectory(prefix='abb-doctor-') as directory:
        temp = Path(directory)
        result = subprocess.run([sys.executable, str(ROOT/'training_kit/prepare_lab.py'),
                                 'fw1', 'demo', str(temp/'workspace')], capture_output=True, text=True)
        checks['preparation'] = {'status': 'PASS' if result.returncode == 0 else 'FAIL', 'exit': result.returncode}
        if shutil.which('gcc'):
            source = temp/'probe.c'
            source.write_text('int main(void){return 0;}\n')
            binary = temp / ('probe.exe' if os.name == 'nt' else 'probe')
            built = subprocess.run(['gcc', str(source), '-o', str(binary)], capture_output=True)
            ok = built.returncode == 0 and subprocess.run([str(binary)]).returncode == 0
            checks['compiler'] = {'status': 'PASS' if ok else 'FAIL'}
    for directory in (WORK, ROOT/'runs', EXPORT):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            checks[directory.name] = {'status': 'PASS' if os.access(directory, os.W_OK) else 'FAIL'}
        except OSError:
            checks[directory.name] = {'status': 'FAIL'}
    # Avoid network downloads during offline checks. Browser acceptance is explicit.
    checks['browser'] = {'status': 'UNTESTED', 'reason': 'Run browser_preflight.py in a prepared T1/T2 workspace with its server running'}
    checks['accounts'] = {'status': 'UNTESTED' if offline else 'BLOCKED',
                          'reason': 'A real provider tool call is required to verify account access'}
    statuses = [item['status'] for item in checks.values()]
    status = 'FAIL' if 'FAIL' in statuses else 'BLOCKED' if 'BLOCKED' in statuses else 'PASS'
    return {'status': status, 'checks': checks, 'versions': versions, 'workspace': str(ROOT)}
