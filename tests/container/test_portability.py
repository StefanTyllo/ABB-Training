from pathlib import Path
import importlib
import json
import os
import socket
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ROOT / 'training_kit'


def test_run_root_override(monkeypatch, tmp_path):
    sys.path.insert(0, str(ROOT))
    from training_ci.runtime_paths import runs_root
    monkeypatch.setenv('ABB_RUNS_DIR', str(tmp_path / 'runs with spaces'))
    assert runs_root() == tmp_path / 'runs with spaces'
    monkeypatch.delenv('ABB_RUNS_DIR')
    assert runs_root() == ROOT / 'runs'


@pytest.mark.parametrize('lab', ['fw1', 'fw2', 'hw1', 'hw2', 't1', 't2'])
@pytest.mark.parametrize('case', ['demo', 'transfer'])
def test_clean_preparation_from_readonly_source(lab, case, tmp_path):
    output = tmp_path / 'root with spaces' / f'{lab}-{case}'
    command = [sys.executable, str(MATERIALS/'prepare_lab.py'), lab, case, str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (output/'.git').is_dir()
    assert '.auth/' in (output/'.gitignore').read_text()
    assert not (output/'automation').exists()
    if lab.startswith('hw'):
        assert not (output/'case.json').exists()
        fixture = MATERIALS/'hardware/fixtures'/lab/case
        for original in fixture.rglob('*'):
            if original.is_file():
                assert (output/original.relative_to(fixture)).read_bytes() == original.read_bytes()
    else:
        assert json.loads((output/'case.json').read_text())['case'] == case
    if lab.startswith('fw'):
        for original in (MATERIALS/'firmware'/lab).glob('*'):
            if original.is_file():
                assert (output/lab/original.name).read_bytes() == original.read_bytes()
    if lab.startswith('t'):
        for name in ['server.py', 'ui.html', 'browser_preflight.py']:
            assert (output/name).read_bytes() == (MATERIALS/'test_team/scaffold'/name).read_bytes()
    assert os.access(output, os.W_OK)
    assert all(os.access(path, os.W_OK) for path in output.rglob("*") if not path.is_symlink())
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0


def test_preview_binding_and_occupied_port(tmp_path):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    script = MATERIALS/'test_team/scaffold/server.py'
    command = [sys.executable, str(script), '--host', '0.0.0.0', '--port', str(port),
               '--state', str(tmp_path/'state.json')]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail(process.stderr.read())
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=.1):
                    break
            except OSError:
                time.sleep(.05)
        else:
            pytest.fail('Preview server did not start')
        second = subprocess.run(command, capture_output=True, text=True, timeout=10)
        assert second.returncode != 0
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_rehearsal_refuses_caller_owned_port(tmp_path):
    sys.path.insert(0, str(ROOT))
    from training_ci.run_lab import server_start
    (tmp_path/'evidence').mkdir()
    import shutil
    shutil.copy2(MATERIALS/'test_team/scaffold/server.py', tmp_path/'server.py')
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers()
        def log_message(self, *args):
            pass
    server = HTTPServer(('127.0.0.1', 8765), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    owned = None
    try:
        with pytest.raises(RuntimeError, match='occupied'):
            owned = server_start(tmp_path)
        assert thread.is_alive()
    finally:
        if owned:
            owned[0].terminate(); owned[0].wait(timeout=10); owned[1].close()
        server.shutdown(); server.server_close(); thread.join(timeout=5)
