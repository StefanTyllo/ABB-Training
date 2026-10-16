"""Run one CI phase; provider auth exists only in its rehearsal process."""
import argparse
import subprocess
import sys

from .auth import ProviderBlocked, _import_secret, provider_environment


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', choices=['copilot', 'codex'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('A command is required after --')
    env = None
    if args.provider:
        env = provider_environment(args.provider)
        try:
            if not _import_secret(args.provider, env):
                raise ProviderBlocked('Selected provider runtime secret is missing')
        except ProviderBlocked as error:
            print('BLOCKED: '+str(error), file=sys.stderr)
            return 3
    try:
        return subprocess.run(command, env=env).returncode
    except OSError as error:
        print(type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
