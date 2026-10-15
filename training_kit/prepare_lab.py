"""Copy one clean lab case; never overwrite previous participant work.

Run from the directory containing materials/ and work/:
    python materials/prepare_lab.py fw1 demo work/fw1-demo
This only prepares inputs. Participants create the reusable automation themselves.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lab', choices=['fw1', 'fw2', 'hw1', 'hw2', 't1', 't2'])
    parser.add_argument('case', choices=['demo', 'transfer'])
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = args.output.resolve()
    if output.exists():
        parser.error('Output exists; choose a fresh directory to preserve prior work.')
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.lab.startswith('fw'):
        output.mkdir()
        shutil.copytree(root / 'firmware' / args.lab, output / args.lab,
                        ignore=shutil.ignore_patterns('__pycache__', 'parser'))
        shutil.copy2(root / 'firmware' / 'requirements.md', output / 'requirements.md')
        (output / 'case.json').write_text(json.dumps({'lab':args.lab, 'case':args.case})+'\n')
        if args.lab == 'fw1':
            subprocess.run([sys.executable, str(output/'fw1/device.py'),
                            '--workdir', str(output/'device'), 'init', '--case', args.case],check=True)
    else:
        group = 'hardware' if args.lab.startswith('hw') else 'test_team'
        subprocess.run([sys.executable, str(root/group/'prepare.py'), '--lab',args.lab,
                        '--case',args.case,'--output',str(output)],check=True)
    if args.lab.startswith('hw'):
        shutil.copy2(root/'hardware/REPORT_CONTRACT.md', output/'REPORT_CONTRACT.md')
    # Copies belong to the learner; image-owned source stays read-only.
    for copied in [output, *output.rglob("*")]:
        if not copied.is_symlink():
            copied.chmod(copied.stat().st_mode | 0o200)
    subprocess.run(['git', 'init', '--quiet', '--initial-branch=main', str(output)], check=True)
    ignore = output / '.gitignore'
    previous = ignore.read_text() if ignore.exists() else ''
    ignore.write_text(previous + '\n.env\n.env.*\n.auth/\n.codex/\n.copilot/\n__pycache__/\n.pytest_cache/\n')
    (output/'evidence').mkdir(exist_ok=True)
    print('Prepared workspace:',output)
    print('Read the PDF lab card before starting the agent.')

if __name__=='__main__':
    main()
