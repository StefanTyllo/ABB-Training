"""Exercise the public launcher, real preparation and sanitized ZIP export."""
from pathlib import Path
import subprocess
import uuid
import zipfile


def abb(*args):
    return subprocess.run(['abb', *map(str, args)], text=True, capture_output=True, timeout=30)


def test_prepare_preserves_existing_workspace():
    name = 'abb-test-' + uuid.uuid4().hex
    workspace = Path('/workspace/work', name)
    try:
        first = abb('prepare', 'fw1', 'demo', '--name', name)
        assert first.returncode == 0, first.stderr
        marker = workspace / 'evidence' / 'original.txt'
        marker.write_text('preserve-this')
        second = abb('prepare', 'fw1', 'demo', '--name', name)
        assert second.returncode != 0
        assert marker.read_text() == 'preserve-this'
    finally:
        import shutil
        shutil.rmtree(workspace, ignore_errors=True)


def test_prepare_refuses_path_escape():
    result = abb('prepare', 'fw1', 'demo', '--name', '../escape')
    assert result.returncode != 0
    assert 'workspace name' in result.stderr.lower()
    assert not Path('/workspace/escape').exists()


def test_export_excludes_secrets_and_symlinks(tmp_path):
    import sys
    sys.path.insert(0, '/opt/abb/runtime')
    from export import export_workspace

    root = tmp_path / 'work with spaces'
    root.mkdir()
    (root / 'code.py').write_text('print("hello")')
    (root / 'evidence').mkdir()
    (root / 'evidence/result.json').write_text('{"status":"FAIL"}')
    for relative in ['.env', '.env.local', '.auth/state.json', '.codex/auth.json',
                     '.copilot/config.json', '__pycache__/cached.pyc', '.git/config']:
        path = root / relative
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text('SYNTHETIC-SECRET-DO-NOT-EXPORT')
    (root / 'link').symlink_to(root / '.env')
    output = tmp_path / 'export with spaces.zip'
    result = export_workspace(root, output)
    assert result['status'] == 'PASS'
    with zipfile.ZipFile(output) as archive:
        assert sorted(archive.namelist()) == ['code.py', 'evidence/result.json']
        assert b'SYNTHETIC-SECRET' not in b''.join(archive.read(n) for n in archive.namelist())


def test_doctor_offline_distinguishes_accounts():
    import json
    result = abb('doctor', '--offline')
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report['status'] == 'PASS'
    assert report['checks']['accounts']['status'] == 'UNTESTED'
