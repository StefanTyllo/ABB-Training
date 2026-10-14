"""Independent, token-free assessment of each prepared Copilot submission."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
lab = sys.argv[1]
if lab not in ('fw1','fw2','hw1','hw2','t1','t2'):
    raise SystemExit('Unknown lab')
output = ROOT/'runs'/lab
output.mkdir(parents=True, exist_ok=True)
group = 'firmware' if lab.startswith('fw') else 'hardware' if lab.startswith('hw') else 'test'
snapshots_path = output/'protected-inputs.json'
snapshots = json.loads(snapshots_path.read_text()) if snapshots_path.exists() else {}
results = []
# T2 executes seven real-browser suites, including the learner variant runner.
grading_timeout = 900 if lab == 't2' else 300
for case, mode in [('demo','code'), ('transfer-md','md-only'), ('transfer-code','code')]:
    workspace = output/case
    changed = []
    for relative, expected in snapshots.get(case, {}).items():
        file = workspace/relative
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            changed.append(relative)
    command = [sys.executable, str(ROOT/f'training_ci/grade_{group}.py'), '--lab',lab,
               '--workspace',str(workspace),'--mode',mode]
    started = time.time()
    try:
        run = subprocess.run(command,capture_output=True,text=True,timeout=grading_timeout)
        returncode = run.returncode
        log = run.stdout+'\n'+run.stderr
    except subprocess.TimeoutExpired:
        returncode = 2; log = f'Independent grading timed out after {grading_timeout} seconds.'
    (output/f'{case}-independent-grader.log').write_text(log)
    print(case, log[-10000:], flush=True)
    for relative, expected in snapshots.get(case, {}).items():
        file = workspace/relative
        if (not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected) and relative not in changed:
            changed.append(relative)
    accepted = returncode == 0 and not changed and bool(snapshots.get(case))
    results.append({'case':case,'mode':mode,'accepted':accepted,'grader_exit':returncode,
                    'changed_authorities':changed,'elapsed_seconds':round(time.time()-started,2)})
(output/'assessment.json').write_text(json.dumps(results,indent=2))
lines = [f'# {lab.upper()} independent assessment', '',
         'Scripted Copilot rehearsal; not a classroom pilot or statistical comparison.', '',
         '| Submission | Result | Grader exit | Protected inputs |', '|---|---|---:|---|']
for item in results:
    lines.append(f"| {item['case']} | {'PASS' if item['accepted'] else 'FAIL'} | {item['grader_exit']} | {'unchanged' if not item['changed_authorities'] else ', '.join(item['changed_authorities'])} |")
(output/'assessment.md').write_text('\n'.join(lines)+'\n')
raise SystemExit(0 if all(x['accepted'] for x in results) else 1)
