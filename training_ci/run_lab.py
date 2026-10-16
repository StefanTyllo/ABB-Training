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
import socket
import subprocess
import sys
import time
import urllib.request
import tempfile

from context_delivery import prepare_context

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from training_ci.runtime_paths import runs_root
LABS = ('fw1', 'fw2', 'hw1', 'hw2', 't1', 't2')
ALLOWED_SHELL = ('python', 'python3', 'gcc', './fw2/parser', 'cat', 'ls', 'pwd', 'mkdir', 'sed', 'head', 'rg', 'node', 'npm', 'npx', 'git')


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


def copilot_command(workspace, stage, lab, prompt):
    """Keep programmatic Copilot context explicit, without changing user settings."""
    command = ['copilot', '-p', prompt, '--no-ask-user', '-s',
               '--no-auto-update', '--no-custom-instructions', '--disable-builtin-mcps',
               '--dynamic-retrieval', 'skills=off',
               '--share=' + str(workspace/'evidence'/f'{stage}-transcript.md'),
               '--allow-tool=read', '--allow-tool=write']
    command += ['--allow-tool=shell(' + tool + ':*)' for tool in ALLOWED_SHELL]
    if os.getenv('COPILOT_MODEL'):
        command += ['--model', os.environ['COPILOT_MODEL']]
    if os.getenv('COPILOT_REASONING_EFFORT'):
        command += ['--reasoning-effort', os.environ['COPILOT_REASONING_EFFORT']]
    if lab.startswith('t'):
        from training_runtime.auth import configure_mcp
        config = configure_mcp(workspace)
        command += ['--additional-mcp-config', Path(config['copilot']).read_text(), '--allow-tool=playwright']
    return command


def authenticate_profile(env):
    """Import the selected runtime secret into this invocation's private profile."""
    from training_runtime.auth import _import_secret
    _import_secret('copilot', env)


def agent(workspace, stage, lab):
    prompt, delivery = prepare_context(workspace, lab, stage)
    command = copilot_command(workspace, stage, lab, prompt)
    started = time.time()
    metadata = {'stage': stage, 'agent': 'GitHub Copilot CLI', 'timeout_seconds': 600,
                'model': os.getenv('COPILOT_MODEL') or 'CLI default; inspect transcript',
                'reasoning_effort': os.getenv('COPILOT_REASONING_EFFORT') or 'CLI default',
                'context_sha256': delivery['context_sha256'], 'timed_out': False,
                'profile': 'ephemeral; custom instructions and skill retrieval disabled'}
    # The Actions token is inherited only by the Copilot step. Never persist it
    # into a profile or metadata; the independent grader is a separate step.
    with tempfile.TemporaryDirectory(prefix='abb-copilot-') as profile:
        env = dict(os.environ, COPILOT_HOME=profile)
        env.pop('COPILOT_CUSTOM_INSTRUCTIONS_DIRS', None)
        authenticate_profile(env)
        with (workspace/'evidence'/f'{stage}-response.txt').open('w') as stream:
            try:
                result = subprocess.run(command, cwd=workspace, env=env, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=600)
                metadata['returncode'] = result.returncode
            except subprocess.TimeoutExpired:
                metadata.update(returncode=124, timed_out=True)
                stream.write('\nCopilot stage exceeded the unchanged 600-second harness limit.\n')
    metadata['elapsed_seconds'] = round(time.time()-started, 2)
    (workspace/'evidence'/f'{stage}-execution.json').write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata), flush=True)
    if metadata['returncode']:
        raise RuntimeError('Copilot execution failed: ' + stage)

def server_start(workspace):
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(('127.0.0.1', 8765))
        except OSError as error:
            raise RuntimeError('Application port 8765 is occupied; stop its owner first') from error
    stream = (workspace / 'evidence/server.log').open('w')
    process = subprocess.Popen([sys.executable, 'server.py', '--variant', 'correct', '--port', '8765',
                                '--state', 'state.json'], cwd=workspace, stdout=stream, stderr=stream)
    for _ in range(50):
        if process.poll() is not None:
            stream.close()
            raise RuntimeError('Application server exited; inspect evidence/server.log')
        try:
            urllib.request.urlopen('http://127.0.0.1:8765', timeout=1).close()
            return process, stream
        except OSError:
            time.sleep(.1)
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill(); process.wait()
    stream.close()
    raise RuntimeError('Application readiness timeout')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lab', choices=LABS)
    args = parser.parse_args()
    lab = args.lab
    output = runs_root() / lab
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
    version = subprocess.run(['copilot', '--no-auto-update', '--version'], capture_output=True, text=True, check=True)
    (output / 'environment.json').write_text(json.dumps({'copilot':version.stdout.strip(), 'python':sys.version,
        'runner_os':os.getenv('RUNNER_OS'), 'commit':os.getenv('GITHUB_SHA'), 'lab':lab,
        'model':os.getenv('COPILOT_MODEL') or 'CLI default; inspect transcript for model identity',
        'reasoning_effort':os.getenv('COPILOT_REASONING_EFFORT') or 'CLI default', 'method':'scripted CI rehearsal'}, indent=2))
    demo = output / 'demo'
    app = server_start(demo) if lab.startswith('t') else None
    try:
        agent(demo, 'stage1', lab)
        check_protected(demo, snapshots['demo'])
        if (demo/'automation').exists():
            raise RuntimeError('Reusable automation created before extraction stage')
        agent(demo, 'stage2', lab)
        checkpoint = (demo/'workflow-md-only.md').read_bytes()
        agent(demo, 'stage3', lab)
        agent(demo, 'stage4', lab)
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
            agent(workspace, 'replay-' + mode, lab)
            check_protected(workspace, snapshots['transfer-'+mode])
        finally:
            if app:
                app[0].terminate(); app[0].wait(timeout=10); app[1].close()
    print('All Copilot stages executed. Independent grading is a separate token-free step.', flush=True)

if __name__ == '__main__':
    main()
