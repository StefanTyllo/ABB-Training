"""Author entry point for the locked virtual environment handbook renderer."""
import argparse
from pathlib import Path
from build_handbook import build_handbook

ROOT = Path(__file__).resolve().parents[1]


def sync_cards():
    guide = (ROOT/'training_author/guide.md').read_text()
    for lab in ('fw1', 'fw2', 'hw1', 'hw2', 't1', 't2'):
        card = '\n'.join(part for part in guide.split('<!-- PAGE -->')
                         if part.strip().startswith('# '+lab.upper()+' '))
        if not card:
            raise ValueError('Missing complete task card: '+lab)
        (ROOT/f'training_kit/task_cards/{lab}.md').write_text(card)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Fresh PDF output path')
    parser.add_argument('--sync-cards', action='store_true', help='Update task cards in a writable author checkout')
    args = parser.parse_args()
    if args.sync_cards:
        sync_cards()
    print(build_handbook(ROOT/'training_author/guide.md', args.output, ROOT/'training_kit'))
