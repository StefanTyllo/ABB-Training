#!/usr/bin/env python3
"""Copy one synthetic starter; never solve or overwrite a participant workspace."""
import argparse
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", choices=("hw1", "hw2"), required=True)
    parser.add_argument("--case", choices=("demo", "transfer"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.output.exists() or args.output.is_symlink():
        parser.error(f"output already exists; choose a fresh directory: {args.output}")
    source = root / "fixtures" / args.lab / args.case
    shutil.copytree(source, args.output)
    # Copies belong to the learner; original starter files remain in training_kit/.
    for copied in [args.output, *args.output.rglob("*")]:
        if not copied.is_symlink():
            copied.chmod(copied.stat().st_mode | 0o200)
    if args.lab == "hw2":
        (args.output / "tools").mkdir()
        shutil.copy2(root / "tools/generate_calibration.py", args.output / "tools/generate_calibration.py")
    print(f"Prepared {args.lab}/{args.case} at {args.output}")


if __name__ == "__main__":
    main()
