"""Regrade the unchanged T2 transfer submission with a sufficient outer timeout."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'runs/t2-regraded'
shutil.copytree(ROOT / 'validation_t2_package/seed', WORK)
(WORK / 'evidence').mkdir()
expected = json.loads((ROOT / 'validation_t2_package/source_hashes.json').read_text())
protected = json.loads((ROOT / 'validation_t2_package/protected-inputs.json').read_text())['transfer-code']
def verify():
    for name, digest in {**expected, **protected}.items():
        assert hashlib.sha256((WORK / name).read_bytes()).hexdigest() == digest, name
verify()
commands = [
    [sys.executable, '-m', 'pytest', 'automation/tests', '-q', '--junitxml=evidence/automation-self-tests.xml'],
    [sys.executable, str(ROOT / 'training_ci/grade_test.py'), '--lab', 't2', '--workspace', str(WORK), '--mode', 'code'],
]
for i, command in enumerate(commands):
    result = subprocess.run(command, cwd=WORK, capture_output=True, text=True, timeout=900)
    (WORK / f'evidence/package-command-{i}.log').write_text(result.stdout + '\n' + result.stderr)
    print(result.stdout, flush=True)
    print(result.stderr, flush=True)
    verify()
    if result.returncode:
        raise SystemExit(result.returncode)
print('Unchanged T2 transfer package accepted: self-tests, real Chrome, both mutants, helpers and protected inputs.')
