"""Collect CI evidence through the same sanitizer used for learner exports."""
import argparse
from pathlib import Path
import tempfile
import zipfile

from export import export_workspace


def collect_evidence(root: Path, output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError('Evidence output must be fresh')
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError('Evidence collection output must be outside the run root')
    with tempfile.TemporaryDirectory(prefix='abb-ci-export-') as temporary:
        archive = Path(temporary)/'evidence.zip'
        export_workspace(root, archive)
        output.mkdir(parents=True, mode=0o700)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path('/workspace/runs'))
    parser.add_argument('--output', type=Path, default=Path('/tmp/abb-evidence'))
    args = parser.parse_args()
    collect_evidence(args.root, args.output)
