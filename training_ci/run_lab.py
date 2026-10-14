"""Run a bounded, scripted rehearsal of the handbook using real Copilot tools.

The four prompts reproduce the teaching stages, but CI is not a learner pilot.
Independent graders execute afterwards without an authentication token.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LABS = ('fw1', 'fw2', 'hw1', 'hw2', 't1', 't2')
ALLOWED_SHELL = ('python', 'python3', 'gcc', './fw2/parser', 'cat', 'ls', 'pwd', 'mkdir', 'sed', 'head', 'rg')


def fingerprint(workspace):
    """Record supplied authorities and adapters; candidate edits are excluded."""
    protected = {}
    for path in workspace.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(workspace)
        parts = relative.parts
        if parts[0] in ('device', 'derived', 'evidence', 'automation'):
            continue
        if str(relative) in ('fw2/parser.c', 'pages/settings_page.py', 'tests/test_settings.py'):
            continue
        if '__pycache__' in parts or path.suffix == '.pyc':
            continue
        protected[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return protected


def check_protected(workspace, expected):
    for relative, digest in expected.items():
        path = workspace / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Authoritative starter changed: {relative}')


def card(lab):
    sections = (ROOT / 'training_author/guide.md').read_text().split('<!-- PAGE -->')
    return '\n'.join(s for s in sections if s.strip().startswith('# ' + lab.upper() + ' '))


def agent(workspace, stage, instructions):
    evidence = workspace / 'evidence'
    prompt = f'''You are performing a scripted CI rehearsal of the ABB training lab.
Your working directory is {workspace}. Stay in this workspace. Do not read instructor files,
external graders, other workspaces, or CI orchestration. They are independent assessment.
Read task-card.md, CI_CONTRACT.md, and the local requirements/report contract.
Use actual terminal tools; do not claim unexecuted results. Do not print environment variables
or credentials. Preserve source authorities and supplied adapters. Expected engineering failure
or blocked results must remain visible. This is a scripted rehearsal, not a human learner pilot.
{instructions}
'''
    (evidence / f'{stage}-prompt.txt').write_text(prompt)
    command = ['copilot', '-p', prompt, '--no-ask-user', '-s',
               '--share=' + str(evidence / f'{stage}-transcript.md'),
               '--allow-tool=read', '--allow-tool=write']
    command += ['--allow-tool=shell(' + tool + ':*)' for tool in ALLOWED_SHELL]
    started = time.time()
    with (evidence / f'{stage}-response.txt').open('w') as stream:
        result = subprocess.run(command, cwd=workspace, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    metadata = {'stage': stage, 'returncode': result.returncode, 'elapsed_seconds': round(time.time()-started, 2)}
    (evidence / f'{stage}-execution.json').write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata), flush=True)
    if result.returncode:
        print((evidence / f'{stage}-response.txt').read_text()[-6000:])
        raise RuntimeError('Copilot execution failed: ' + stage)


def server_start(workspace):
    stream = (workspace / 'evidence/server.log').open('w')
    process = subprocess.Popen([sys.executable, 'server.py', '--variant', 'correct', '--port', '8765',
                                '--state', 'state.json'], cwd=workspace, stdout=stream, stderr=stream)
    for _ in range(50):
        if process.poll() is not None:
            raise RuntimeError('Application server exited')
        try:
            urllib.request.urlopen('http://127.0.0.1:8765', timeout=1).close()
            return process, stream
        except OSError:
            time.sleep(.1)
    process.terminate()
    stream.close()
    raise RuntimeError('Application readiness timeout')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lab', choices=LABS)
    args = parser.parse_args()
    lab = args.lab
    output = ROOT / 'runs' / lab
    output.mkdir(parents=True, exist_ok=True)
    contract_name = 'firmware' if lab.startswith('fw') else 'hardware' if lab.startswith('hw') else 'test'
    snapshots = {}
    for case_name, case in [('demo', 'demo'), ('transfer-md', 'transfer'), ('transfer-code', 'transfer')]:
        workspace = output / case_name
        subprocess.run([sys.executable, str(ROOT/'training_kit/prepare_lab.py'), lab, case, str(workspace)], check=True)
        (workspace / 'task-card.md').write_text(card(lab))
        shutil.copy2(ROOT / f'training_ci/{contract_name}_contract.md', workspace / 'CI_CONTRACT.md')
        snapshots[case_name] = fingerprint(workspace)
    (output / 'protected-inputs.json').write_text(json.dumps(snapshots, indent=2))
    version = subprocess.run(['copilot', '--version'], capture_output=True, text=True, check=True)
    (output / 'environment.json').write_text(json.dumps({'copilot':version.stdout.strip(), 'python':sys.version,
        'runner_os':os.getenv('RUNNER_OS'), 'commit':os.getenv('GITHUB_SHA'), 'lab':lab,
        'model':'CLI default; inspect transcript for model identity', 'method':'scripted CI rehearsal'}, indent=2))
    demo = output / 'demo'
    app = server_start(demo) if lab.startswith('t') else None
    try:
        agent(demo, 'stage1', '''STAGE 1: Execute the task-card demonstration one operation at a time.
CI cannot provide interactive explanations. Use each decision point in the task card as the scripted
facilitator rationale: state why, execute, inspect the actual result, then proceed. Record every command,
observation, and rationale in evidence/session.md. Complete the task and its stated checks. For browser
labs the correct server is already running at http://127.0.0.1:8765; do not stop it.
For variant evaluation or helper lifecycle checks start your own server on another free port,
set BASE_URL for that subprocess, and stop only your own child process.
Use existing low-level tools. Do not create reusable automation yet. Finally reconstruct the actual process
as workflow.md with prerequisites, ordered steps, branches, evidence, recovery and completion criteria.''')
        check_protected(demo, snapshots['demo'])
        if (demo/'automation').exists():
            raise RuntimeError('Reusable automation created before extraction stage')
        agent(demo, 'stage2', '''STAGE 2: Review evidence/session.md and workflow.md. Abstract the observed
process for reuse. Replace incident-specific IDs, paths, versions and values with named validated inputs.
Preserve genuine engineering invariants and authority rules. Specify missing-input behavior and untested
branches. Remove duplicate instructions. Save workflow.md and an identical workflow-md-only.md checkpoint.
Do not create automation or change the completed task artifacts.''')
        checkpoint = (demo/'workflow-md-only.md').read_bytes()
        agent(demo, 'stage3', '''STAGE 3: Review each workflow step. Write extraction-map.md with purpose,
inputs, operation, expected output, failure condition, and disposition (deterministic code, model judgment,
human decision). Prioritize collection, parsing, calculation, comparison, validation, reporting. Give every
proposed function an input/output contract. Do not implement reusable automation until stage 4.''')
        agent(demo, 'stage4', '''STAGE 4: Implement the deterministic operations in extraction-map.md under
automation/, using CI_CONTRACT.md for the common guardrails entry point. Follow every Stage 4 requirement in
task-card.md. Use descriptive names, docstrings, engineering-intent comments, explicit intermediate values,
and actionable expected/observed logs. Produce real machine-readable evidence and meaningful exit codes.
Add checks for the defect, valid input and failure branch; altered fixtures belong under automation/tests.
Run and inspect those checks. Do not overwrite the original stage1 baseline/session evidence. The already
completed task may require idempotent verification. Preserve workflow-md-only.md. Update workflow.md to call
the helpers and explain results, and document exact commands in automation/README.md. Do not access graders.''')
        if (demo/'workflow-md-only.md').read_bytes() != checkpoint:
            raise RuntimeError('MD-only workflow checkpoint changed during implementation')
        for relative in ('workflow.md','workflow-md-only.md','extraction-map.md','automation/README.md',
                         'automation/guardrails.py','evidence/session.md'):
            if not (demo/relative).is_file() or not (demo/relative).stat().st_size:
                raise RuntimeError('Required learning artifact missing: '+relative)
        check_protected(demo, snapshots['demo'])
    finally:
        if app:
            app[0].terminate(); app[0].wait(timeout=10); app[1].close()
    for mode in ('md', 'code'):
        workspace = output / ('transfer-' + mode)
        shutil.copy2(demo/('workflow-md-only.md' if mode=='md' else 'workflow.md'), workspace/'workflow.md')
        if mode == 'code':
            shutil.copytree(demo/'automation', workspace/'automation', ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        app = server_start(workspace) if lab.startswith('t') else None
        try:
            agent(workspace, 'replay', f'''FRESH TRANSFER ({'Markdown only' if mode=='md' else 'Markdown plus code'}):
Read workflow.md and execute its process using this workspace's actual inputs. Record commands, observations,
failures and decisions in evidence/session.md. Do not copy demo outputs or implementation. Fresh parser/POM/
tests still need the task-specific repair or extension. {'Invoke the supplied automation and retain its actual feedback.' if mode=='code' else 'No reusable helper is supplied; follow the Markdown workflow.'}
For browser labs the correct server is already running on port 8765. Do not stop it.
Use another free port for your own variant servers and pass BASE_URL to their tests. Complete the task or
faithfully report a required blocked/fail engineering assessment. Do not invent missing source authority.''')
            check_protected(workspace, snapshots['transfer-'+mode])
        finally:
            if app:
                app[0].terminate(); app[0].wait(timeout=10); app[1].close()
    print('All Copilot stages executed. Independent grading is a separate token-free step.', flush=True)

if __name__ == '__main__':
    main()
