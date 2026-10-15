"""Public container launcher. All process arguments remain separate argv items."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

WORK = Path('/workspace/work')
EXPORT = Path('/workspace/export')
LABS = ['fw1', 'fw2', 'hw1', 'hw2', 't1', 't2']


def workspace_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = Path('/workspace') / candidate
    candidate = candidate.resolve(strict=True)
    if not candidate.is_relative_to(WORK) or candidate == WORK or not candidate.is_dir():
        raise ValueError('Workspace must be a prepared directory under /workspace/work')
    if not (candidate / 'evidence').is_dir():
        raise ValueError('Workspace is not prepared: evidence directory is missing')
    return candidate


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog='abb')
    commands = parser.add_subparsers(dest='command', required=True)
    doctor = commands.add_parser('doctor')
    doctor.add_argument('--offline', action='store_true')
    prepare = commands.add_parser('prepare')
    prepare.add_argument('lab', choices=LABS)
    prepare.add_argument('case', choices=['demo', 'transfer'])
    prepare.add_argument('--name')
    shell = commands.add_parser('shell')
    shell.add_argument('--workspace', required=True)
    export = commands.add_parser('export')
    export.add_argument('--output', default='/workspace/export/learner-work.zip')
    login = commands.add_parser('login')
    login.add_argument('provider', choices=['codex', 'copilot'])
    agent = commands.add_parser('agent')
    agent.add_argument('provider', choices=['codex', 'copilot'])
    agent.add_argument('--workspace', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'doctor':
            from doctor import run_checks
            report = run_checks(args.offline)
            print(json.dumps(report, indent=2))
            print('Readiness: ' + report['status'], file=sys.stderr)
            return {'PASS': 0, 'FAIL': 1, 'BLOCKED': 3}[report['status']]
        if args.command == 'prepare':
            name = args.name or f'{args.lab}-{args.case}'
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _.\-]{0,79}', name):
                raise ValueError('Invalid workspace name; use a single directory name')
            target = WORK / name
            if target.exists() or target.is_symlink():
                raise ValueError('Workspace already exists; resume it or choose a fresh name')
            result = subprocess.run([sys.executable, '/opt/abb/materials/prepare_lab.py',
                                     args.lab, args.case, str(target)])
            return result.returncode
        if args.command == 'export':
            from export import export_workspace
            output = Path(args.output).resolve()
            if not output.is_relative_to(EXPORT):
                raise ValueError('Export output must be under /workspace/export')
            print(json.dumps(export_workspace(WORK, output)))
            return 0
        if args.command == 'shell':
            os.chdir(workspace_path(args.workspace))
            os.execvp('bash', ['bash'])
        if args.command in {'login', 'agent'}:
            try:
                import auth
            except ImportError:
                print('BLOCKED: provider setup is not installed', file=sys.stderr)
                return 3
            if args.command == 'login':
                return auth.login(args.provider)
            workspace = workspace_path(args.workspace)
            command, env = auth.prepare_agent_process(args.provider, workspace)
            return subprocess.run(command, cwd=workspace, env=env).returncode
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
