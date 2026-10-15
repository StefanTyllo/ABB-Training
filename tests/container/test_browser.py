from pathlib import Path
import json
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fixture_ui(tmp_path):
    workspace = tmp_path/'t1'
    result = subprocess.run([sys.executable, str(ROOT/'training_kit/prepare_lab.py'),
                             't1', 'demo', str(workspace)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    server = subprocess.Popen([sys.executable, 'server.py', '--port', str(port)],
                              cwd=workspace, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    url = f'http://127.0.0.1:{port}'
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(url, timeout=.1).close(); break
            except OSError:
                time.sleep(.05)
        else:
            pytest.fail('Fixture failed to start')
        yield workspace, url
    finally:
        server.terminate(); server.wait(timeout=10)


def bootstrap(workspace, *args):
    return subprocess.run(['node', str(workspace/'tools/session_bootstrap.mjs'), *args],
                          cwd=workspace, capture_output=True, text=True, timeout=30)


def test_supplied_bootstrap_validates_and_exports_state(fixture_ui):
    workspace, url = fixture_ui
    result = bootstrap(workspace, '--mode', 'no-login', '--url', url,
                       '--state', '.auth/state.json', '--report', 'evidence/bootstrap.json')
    assert result.returncode == 0, result.stderr
    report = json.loads((workspace/'evidence/bootstrap.json').read_text())
    assert report['status'] == 'PASS'
    assert report['authenticated'] is False
    assert json.loads((workspace/'.auth/state.json').read_text())['cookies'] == []
    assert not (workspace/'automation').exists()


def test_login_without_adapter_is_blocked(fixture_ui):
    workspace, url = fixture_ui
    result = bootstrap(workspace, '--mode', 'login', '--url', url,
                       '--state', '.auth/state.json', '--report', 'evidence/login.json')
    assert result.returncode == 3
    assert json.loads((workspace/'evidence/login.json').read_text())['status'] == 'BLOCKED'
    assert not (workspace/'.auth/state.json').exists()


def test_bootstrap_parameters_and_url_are_validated(fixture_ui):
    workspace, _ = fixture_ui
    assert bootstrap(workspace).returncode == 2
    result = bootstrap(workspace, '--mode', 'no-login', '--url', 'file:///etc/passwd',
                       '--state', '.auth/state.json', '--report', 'evidence/bad.json')
    assert result.returncode == 2
    assert not (workspace/'.auth/state.json').exists()


def test_actual_mcp_restores_state_and_interacts_with_dynamic_fields(fixture_ui):
    workspace, url = fixture_ui
    result = bootstrap(workspace, '--mode', 'no-login', '--url', url,
                       '--state', '.auth/state.json', '--report', 'evidence/bootstrap.json')
    assert result.returncode == 0, result.stderr
    state = workspace/'.auth/state.json'
    data = json.loads(state.read_text())
    data['origins'] = [{'origin': url, 'localStorage': [
        {'name': 'abb_container_marker', 'value': 'container-state-restored'}]}]
    state.write_text(json.dumps(data))
    sys.path.insert(0, '/opt/abb/runtime')
    from auth import configure_mcp
    config = configure_mcp(workspace)
    import selectors
    stderr = (workspace/'evidence/mcp-stdio.log').open('w')
    process = subprocess.Popen(['/opt/abb/node/bin/node', *config['args']], cwd=workspace,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                               text=True, bufsize=1)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    request_id = 0
    def request(method, params):
        nonlocal request_id
        request_id += 1
        process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': request_id,
                                        'method': method, 'params': params})+'\n')
        process.stdin.flush()
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            assert selector.select(timeout=30), 'MCP response timed out'
            line = process.stdout.readline()
            assert line, 'MCP exited without a response'
            response = json.loads(line)
            if response.get('id') == request_id:
                assert 'error' not in response, response
                return response['result']
        pytest.fail('MCP response deadline exceeded')
    def call(name, arguments):
        result = request('tools/call', {'name': name, 'arguments': arguments})
        assert not result.get('isError'), result
        return '\n'.join(c.get('text', '') for c in result.get('content', []))
    try:
        request('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                               'clientInfo': {'name': 'abb-offline-probe', 'version': '1'}})
        process.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'})+'\n')
        process.stdin.flush()
        request('tools/list', {})
        sandbox = call('browser_navigate', {'url': 'chrome://sandbox'})
        if 'You are adequately sandboxed.' not in sandbox:
            sandbox = '\n'.join(path.read_text() for path in (workspace/'evidence/mcp').glob('page-*.yml'))
        assert 'You are adequately sandboxed.' in sandbox
        call('browser_navigate', {'url': url})
        result = call('browser_evaluate', {'function': '''async () => {
          const field = document.querySelector('#connection');
          field.value='tcp'; field.dispatchEvent(new Event('change', {bubbles:true}));
          await new Promise(resolve => setTimeout(resolve, 500));
          return {fieldVisible: !document.querySelector('#tcp-fields').hidden,
                  marker: localStorage.getItem('abb_container_marker')};
        }'''})
        import re
        assert re.search(r'"fieldVisible":\s*true', result), result
        assert 'container-state-restored' in result, result
        call('browser_close', {})
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()
        selector.close(); stderr.close()


def test_element_failure_produces_sanitized_evidence(fixture_ui):
    workspace, url = fixture_ui
    result = bootstrap(workspace, '--mode', 'no-login', '--url', url+'/missing',
                       '--state', '.auth/state.json', '--report', 'evidence/missing.json')
    assert result.returncode == 1
    report = json.loads((workspace/'evidence/missing.json').read_text())
    assert report['status'] == 'FAIL'
    assert report['phase'] == 'fixture-ready'
    assert report['errorType'] == 'TimeoutError'
    assert 'password' not in json.dumps(report).lower()


def test_bootstrap_refuses_symlink_output(fixture_ui):
    workspace, url = fixture_ui
    outside = workspace.parent/'outside-state'
    outside.mkdir()
    (workspace/'.auth').symlink_to(outside, target_is_directory=True)
    result = bootstrap(workspace, '--mode', 'no-login', '--url', url,
                       '--state', '.auth/state.json', '--report', 'evidence/rejected.json')
    assert result.returncode == 2
    assert not (outside/'state.json').exists()
