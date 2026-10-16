"""Scoped agent launch and documented device/secret-file authentication."""
import json
import os
from pathlib import Path
import subprocess
import tomllib
from .paths import ROOT, RUNTIME, NODE_MODULES, node_command, provider_command

TOKEN_KEYS = ['OPENAI_API_KEY', 'CODEX_API_KEY', 'CODEX_ACCESS_TOKEN',
              'COPILOT_GITHUB_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN']
HOMES = {name: ROOT / '.auth' / name for name in ('codex', 'copilot')}


class ProviderBlocked(RuntimeError):
    pass


def provider_environment(provider: str) -> dict[str, str]:
    if provider not in HOMES:
        raise ValueError('Unknown provider')
    env = {k: v for k, v in os.environ.items()
           if k not in TOKEN_KEYS + ['CODEX_HOME', 'COPILOT_HOME', 'COPILOT_ALLOW_ALL']
           and not k.startswith(('COPILOT_PROVIDER_', 'CODEX_UNSAFE_'))}
    env['CODEX_HOME' if provider == 'codex' else 'COPILOT_HOME'] = str(HOMES[provider])
    env['COPILOT_AUTO_UPDATE'] = 'false'
    return env


def configure_mcp(workspace: Path) -> dict:
    workspace = workspace.resolve(strict=True)
    config_dir = workspace/'.abb'
    if config_dir.is_symlink():
        raise ValueError('MCP configuration must remain inside this workspace')
    config_dir.mkdir(exist_ok=True)
    for name in ['playwright.json', 'copilot-mcp.json']:
        if (config_dir/name).is_symlink():
            raise ValueError('MCP configuration file must not be a symlink')
    state = workspace/'.auth/state.json'
    if not state.resolve().is_relative_to(workspace):
        raise ValueError('MCP state must remain inside this workspace')
    browser = json.loads((RUNTIME / 'playwright.json').read_text())
    browser['browser']['isolated'] = True
    if os.environ.get('CHROME_BINARY'):
        browser['browser']['launchOptions']['executablePath'] = os.environ['CHROME_BINARY']
    (config_dir/'playwright.json').write_text(json.dumps(browser, indent=2)+'\n')
    args = [str(NODE_MODULES / '@playwright/mcp/cli.js'), '--config',
            str(config_dir/'playwright.json'), '--isolated', '--sandbox',
            '--output-dir', str(workspace/'evidence/mcp')]
    if (workspace/'.auth/state.json').is_file():
        args += ['--storage-state', str(workspace/'.auth/state.json')]
    server = {'type': 'local', 'command': node_command(), 'args': args,
              'cwd': str(workspace), 'tools': ['*'], 'env': {k: '' for k in TOKEN_KEYS}}
    copilot = json.loads((RUNTIME / 'copilot-mcp.json').read_text())
    copilot['mcpServers']['playwright'] = server
    (config_dir/'copilot-mcp.json').write_text(json.dumps(copilot, indent=2)+'\n')
    return {'args': args, 'copilot': str(config_dir/'copilot-mcp.json')}


def _import_secret(provider: str, env: dict) -> bool:
    secret = Path(os.environ.get('ABB_SECRETS_DIR', str(ROOT / '.auth' / 'secrets'))) / ('codex_api_key' if provider == 'codex' else 'copilot_token')
    if not secret.is_file():
        return False
    value = secret.read_text().strip()
    if not value or '\n' in value:
        raise ProviderBlocked('Runtime secret must contain one nonempty token line')
    command = [provider_command(provider), 'login', '--with-api-key' if provider == 'codex' else '--with-token']
    try:
        result = subprocess.run(command, input=value+'\n', capture_output=True, text=True,
                                env=env, timeout=60)
    except subprocess.TimeoutExpired as error:
        raise ProviderBlocked('Provider secret-file login timed out') from error
    if result.returncode:
        raise ProviderBlocked('Provider rejected secret-file login; inspect account policy and token scope')
    return True


def login(provider: str) -> int:
    env = provider_environment(provider)
    HOMES[provider].mkdir(parents=True, exist_ok=True)
    try:
        if _import_secret(provider, env):
            return 0
    except ProviderBlocked as error:
        print('BLOCKED: '+str(error))
        return 3
    command = [provider_command(provider), 'login', '--device-auth' if provider == 'codex' else '--device-code']
    return subprocess.run(command, env=env).returncode


def credentials_present(provider: str) -> bool:
    path = HOMES[provider]/('auth.json' if provider == 'codex' else 'config.json')
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    if provider == 'codex':
        return bool(data.get('OPENAI_API_KEY') or data.get('tokens'))
    return bool(data.get('github_token') or data.get('logged_in_users'))


def prepare_agent_process(provider: str, workspace: Path) -> tuple[list[str], dict[str, str]]:
    from .launcher import workspace_path
    workspace = workspace_path(str(workspace))
    env = provider_environment(provider)
    _import_secret(provider, env)
    if not credentials_present(provider):
        raise ProviderBlocked(f'No {provider} login is available; run abb login {provider}')
    mcp = configure_mcp(workspace)
    if provider == 'codex':
        base = tomllib.loads((RUNTIME / 'codex.toml').read_text())
        command = [provider_command('codex')]
        for key, value in base.items():
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    command += ['-c', key+'.'+nested_key+'='+json.dumps(nested_value)]
            else:
                command += ['-c', key+'='+json.dumps(value)]
        command += ['-c', 'mcp_servers.playwright.command='+json.dumps(node_command()),
                    '-c', 'mcp_servers.playwright.args='+json.dumps(mcp['args'])]
    else:
        command = [provider_command('copilot'), '--no-auto-update', '--additional-mcp-config', '@'+mcp['copilot']]
    version = subprocess.run([provider_command(provider), '--version'], env=env, capture_output=True, text=True, timeout=15)
    record = {'provider': provider, 'cli': version.stdout.strip(), 'workspace': str(workspace),
              'model_requested': 'gpt-6.1-sol' if provider == 'codex' else 'account default',
              'effort_requested': 'medium' if provider == 'codex' else 'account default',
              'account_tool_call': 'UNTESTED'}
    (workspace/'evidence/agent-launch.json').write_text(json.dumps(record, indent=2)+'\n')
    return command, env
