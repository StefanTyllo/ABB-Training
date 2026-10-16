"""Local CLI integration, containment and export behavior."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from training_runtime import launcher
from training_runtime.auth import configure_mcp
from training_runtime.export import export_workspace
from training_runtime.paths import ROOT


def test_prepare_all_cases_and_preserve_existing_work(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, 'WORK', tmp_path)
    for lab in launcher.LABS:
        for case in ('demo', 'transfer'):
            name = f'{lab}-{case} with spaces'
            assert launcher.main(['prepare', lab, case, '--name', name]) == 0
            marker = tmp_path/name/'evidence/marker'
            marker.write_text('original')
            assert launcher.main(['prepare', lab, case, '--name', name]) == 2
            assert marker.read_text() == 'original'


def test_workspace_path_refuses_escape_and_symlinks(monkeypatch, tmp_path):
    work = tmp_path/'work'
    work.mkdir()
    monkeypatch.setattr(launcher, 'WORK', work)
    outside = tmp_path/'outside'
    (outside/'evidence').mkdir(parents=True)
    (work/'escape').symlink_to(outside, target_is_directory=True)
    for path in (outside, work/'escape', work):
        with pytest.raises(ValueError):
            launcher.workspace_path(str(path))
    assert launcher.main(['prepare', 'fw1', 'demo', '--name', '../escape']) == 2


def test_export_omits_credentials_and_preserves_existing_archive(tmp_path):
    work = tmp_path/'work'
    work.mkdir()
    (work/'result.txt').write_text('evidence')
    for relative in ('.env', '.auth/state.json', '.git/config', '.venv/settings', 'node_modules/secret'):
        path = work/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('SYNTHETIC_SECRET')
    (work/'leak').symlink_to(work/'.env')
    archive = tmp_path/'export.zip'
    export_workspace(work, archive)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.namelist() == ['result.txt']
    with pytest.raises(FileExistsError):
        export_workspace(work, archive)


def test_mcp_paths_are_local_and_state_is_scoped(tmp_path):
    (tmp_path/'evidence').mkdir()
    config = configure_mcp(tmp_path)
    server = json.loads(Path(config['copilot']).read_text())['mcpServers']['playwright']
    assert Path(server['args'][0]).is_relative_to(ROOT)
    assert '--sandbox' in server['args']
    assert server['cwd'] == str(tmp_path)
    browser = json.loads((tmp_path/'.abb/playwright.json').read_text())
    assert '/opt/abb' not in json.dumps(browser)


def test_module_entrypoint_works_outside_repository(tmp_path):
    result = subprocess.run([sys.executable, '-m', 'training_runtime', '--help'],
                            cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert 'prepare' in result.stdout


def test_collection_uses_same_secret_filter(tmp_path):
    from training_runtime.collect import collect_evidence
    root = tmp_path/'runs'
    (root/'fw1/evidence').mkdir(parents=True)
    (root/'fw1/evidence/result.txt').write_text('actual result')
    (root/'fw1/.auth').mkdir()
    (root/'fw1/.auth/state.json').write_text('SYNTHETIC_SECRET')
    output = tmp_path/'collected'
    collect_evidence(root, output)
    assert (output/'fw1/evidence/result.txt').read_text() == 'actual result'
    assert not (output/'fw1/.auth').exists()


def test_provider_homes_and_child_tokens_are_scoped(monkeypatch):
    from training_runtime.auth import HOMES, TOKEN_KEYS, provider_environment
    for token in TOKEN_KEYS:
        monkeypatch.setenv(token, 'SYNTHETIC_SECRET')
    for provider in ('codex', 'copilot'):
        env = provider_environment(provider)
        assert not any(token in env for token in TOKEN_KEYS)
        assert HOMES[provider] == ROOT/'.auth'/provider
        assert env['CODEX_HOME' if provider == 'codex' else 'COPILOT_HOME'] == str(HOMES[provider])
