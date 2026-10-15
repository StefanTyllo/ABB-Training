from pathlib import Path
import json
import subprocess
import sys
import uuid

import pytest


def auth_module():
    assert Path('/opt/abb/runtime/auth.py').exists(), 'Agent support is not installed'
    sys.path.insert(0, '/opt/abb/runtime')
    import auth
    return auth


def test_provider_environment_excludes_tokens_and_bypass(monkeypatch):
    auth = auth_module()
    for key in ['OPENAI_API_KEY', 'COPILOT_GITHUB_TOKEN', 'GITHUB_TOKEN', 'COPILOT_ALLOW_ALL']:
        monkeypatch.setenv(key, 'SYNTHETIC-SENTINEL')
    for provider in ['codex', 'copilot']:
        env = auth.provider_environment(provider)
        assert 'SYNTHETIC-SENTINEL' not in json.dumps(env)
        assert env['COPILOT_AUTO_UPDATE'] == 'false'
        assert env.get('CODEX_HOME') == ('/home/learner/.codex' if provider == 'codex' else None)
        assert env.get('COPILOT_HOME') == ('/home/learner/.copilot' if provider == 'copilot' else None)


def test_workspace_mcp_configuration_is_scoped(tmp_path):
    auth = auth_module()
    first, second = tmp_path/'first', tmp_path/'second'
    first.mkdir(); second.mkdir()
    one = auth.configure_mcp(first)
    two = auth.configure_mcp(second)
    assert one != two
    config = json.loads((first/'.abb/playwright.json').read_text())
    assert config['browser']['launchOptions']['chromiumSandbox'] is True
    assert config['browser']['launchOptions']['executablePath'].startswith('/opt/abb/browser/')
    assert str(second) not in json.dumps(config)
    assert not (first/'automation').exists()


def test_absent_credentials_report_blocked_without_secrets():
    name = 'abb-test-auth-' + uuid.uuid4().hex
    prepared = subprocess.run(['abb', 'prepare', 'fw1', 'demo', '--name', name], capture_output=True, text=True)
    assert prepared.returncode == 0, prepared.stderr
    try:
        for provider in ['codex', 'copilot']:
            result = subprocess.run(['abb', 'agent', provider, '--workspace', 'work/'+name],
                                    capture_output=True, text=True, timeout=15)
            assert result.returncode == 3
            assert 'BLOCKED' in result.stderr
        wrong = subprocess.run(['abb', 'agent', 'codex', '--workspace', '/tmp'],
                               capture_output=True, text=True, timeout=15)
        assert wrong.returncode == 2
    finally:
        import shutil
        shutil.rmtree(Path('/workspace/work', name))
