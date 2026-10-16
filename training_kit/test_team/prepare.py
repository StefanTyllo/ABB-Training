"""Create an isolated learner exercise, never overwrite an existing directory."""
import argparse
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--lab", choices=("t1", "t2"), required=True)
parser.add_argument("--case", choices=("demo", "transfer"), required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("Output already exists; choose a fresh directory")
root = Path(__file__).resolve().parent
shutil.copytree(root / "scaffold", args.output, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
# Copies belong to the learner; original starter files remain in training_kit/.
for copied in [args.output, *args.output.rglob("*")]:
    if not copied.is_symlink():
        copied.chmod(copied.stat().st_mode | 0o200)
(args.output / "tests").mkdir(exist_ok=True)
shutil.copyfile(root / (args.lab + "_test.py.txt"), args.output / "tests" / "test_settings.py")
shutil.copyfile(root / "REQUIREMENTS.md", args.output / "REQUIREMENTS.md")
data = dict(lab=args.lab, case=args.case, connection="tcp", host="lab.example.test", port="1502", auth="password", password="practice-only", device="COM7")
if args.case == "transfer":
    data.update(connection="serial" if args.lab == "t1" else "tcp", port="65535", device="COM9", password="transfer-only")
(args.output / "case.json").write_text(json.dumps(data, indent=2) + "\n")
print(f"Prepared {args.lab}/{args.case}: {args.output.resolve()}")

if args.lab == "t1":
    (args.output / "tools").mkdir(exist_ok=True)
    shutil.copyfile(root / "support/session_bootstrap.mjs", args.output / "tools/session_bootstrap.mjs")
