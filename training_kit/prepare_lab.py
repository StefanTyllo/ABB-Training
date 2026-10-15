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
    task_card = root / 'task_cards' / (args.lab + '.md')
    if not task_card.is_file():
        parser.error('Bundled task card is missing; re-extract the current starter materials.')
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
    shutil.copy2(task_card, output/'task-card.md')
    (output/'evidence').mkdir(exist_ok=True)
    print('Prepared workspace:',output)
    print('Read task-card.md and the PDF shared prompts before starting GitHub Copilot CLI.')

if __name__=='__main__':
    main()
