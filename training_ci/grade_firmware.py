"""Independent firmware lab checks; never repairs participant sources."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TRUSTED = ROOT / "training_kit" / "firmware"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def command(argv, cwd, timeout=60):
    result = subprocess.run(list(map(str, argv)), cwd=cwd, text=True,
                            capture_output=True, timeout=timeout)
    require(result.returncode == 0,
            f"Command failed ({result.returncode}): {argv[0]}\n"
            f"{result.stdout[-3000:]}{result.stderr[-3000:]}")
    return result.stdout


def read_json(path):
    return json.loads(path.read_text())


def unchanged(path, original):
    require(path.read_bytes() == original, f"Must preserve {path}")


def check_fw1(workspace, case):
    spec = read_json(TRUSTED / "fw1/expected.json")[case]
    for name in ("device.py", "expected.json"):
        unchanged(workspace / "fw1" / name, (TRUSTED / "fw1" / name).read_bytes())
    device = [sys.executable, TRUSTED / "fw1/device.py", "--workdir", workspace / "device"]
    def primitive(*args):
        return json.loads(command(device + list(args), workspace))
    baseline = read_json(workspace / "evidence/baseline.json")
    expected_baseline = {
        "identity": {"device_id": spec["device_id"]},
        "firmware": {"version": spec["firmware"]},
        "config": {"baud": 9600}, "faults": ["LINK_TIMEOUT"],
        "logs": ["boot: link timeout"],
    }
    for key, value in expected_baseline.items():
        require(baseline.get(key) == value, f"Baseline {key} must contain original primitive output")
    state = read_json(workspace / "device/state.json")
    require(state["case"] == case, "State case differs from case.json")
    require(primitive("read", "--field", "identity") == baseline["identity"], "Identity changed")
    require(primitive("read", "--field", "firmware") == baseline["firmware"], "Firmware changed")
    require(primitive("read", "--field", "config") == {"baud": spec["baud"]}, "Wrong final baud")
    require(primitive("read", "--field", "faults") == [], "Faults remain")
    require(primitive("probe") == {"ok": True, "status": "reply"}, "Probe failed")
    require(primitive("logs") == baseline["logs"] + [f"baud changed: 9600 -> {spec['baud']}"],
            "Expected exactly one intended baud change after original logs")
    return [workspace / "device/state.json", workspace / "evidence/baseline.json"]


def check_fw2(workspace, case):
    del case
    for name in ("main.c", "parser.h"):
        unchanged(workspace / "fw2" / name, (TRUSTED / "fw2" / name).read_bytes())
    with tempfile.TemporaryDirectory(prefix="firmware-grade-", dir=workspace / "evidence") as folder:
        temp = Path(folder)
        # Use an isolated source copy with the trusted public interface.
        for name in ("main.c", "parser.h"):
            (temp / name).write_bytes((TRUSTED / "fw2" / name).read_bytes())
        (temp / "parser.c").write_bytes((workspace / "fw2/parser.c").read_bytes())
        exe = temp / "parser"
        command(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", temp / "parser.c",
                 temp / "main.c", "-o", exe], workspace)
        result = json.loads(command([sys.executable, TRUSTED / "instructor/smoke.py", exe], workspace))
        require(result["cases"] == 50 and not result["failures"], "External parser grader failed")
    return [workspace / "fw2/parser.c", workspace / "fw2/parser.h", workspace / "fw2/main.c"]


def grade(lab, workspace, mode):
    metadata_path = workspace / "case.json"
    metadata_bytes = metadata_path.read_bytes()
    metadata = json.loads(metadata_bytes)
    require(metadata.get("lab") == lab, "Lab differs from case.json")
    require(metadata.get("case") in ("demo", "transfer"), "Unknown case")
    require((workspace / "workflow.md").read_text().strip(), "workflow.md must not be empty")
    checker = check_fw1 if lab == "fw1" else check_fw2
    if mode == "md-only":
        checker(workspace, metadata["case"])
        return {"lab": lab, "case": metadata["case"], "mode": mode, "passed": True,
                "checks": ["independent result"]}
    automation = workspace / "automation/guardrails.py"
    require(automation.is_file(), "Missing automation/guardrails.py")
    baseline_path = workspace / "evidence/baseline.json"
    prior_baseline = baseline_path.read_bytes() if baseline_path.exists() else None
    if lab == "fw1" and prior_baseline is None:
        require(read_json(workspace / "device/state.json")["baud"] == 9600,
                "Already changed device has no original baseline; do not reconstruct history")
    invocation = [sys.executable, automation, "--workspace", workspace]
    command(invocation, ROOT)
    unchanged(metadata_path, metadata_bytes)
    if prior_baseline is not None:
        unchanged(baseline_path, prior_baseline)
    preserved = {path: path.read_bytes() for path in checker(workspace, metadata["case"])}
    command(invocation, ROOT)
    unchanged(metadata_path, metadata_bytes)
    for path, original in preserved.items():
        unchanged(path, original)
    checker(workspace, metadata["case"])
    return {"lab": lab, "case": metadata["case"], "mode": mode, "passed": True,
            "checks": ["automation success", "independent result", "idempotent replay"]}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--lab", choices=("fw1", "fw2"), required=True)
    cli.add_argument("--workspace", type=Path, required=True)
    cli.add_argument("--mode", choices=("md-only", "code"), default="code")
    args = cli.parse_args()
    try:
        result = grade(args.lab, args.workspace.resolve(), args.mode)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        result = {"lab": args.lab, "mode": args.mode, "passed": False, "error": str(error)}
    report = args.workspace.resolve() / "evidence/grade_firmware.json"
    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + "\n")
    except OSError as error:
        result = {"lab": args.lab, "mode": args.mode, "passed": False,
                  "error": f"Could not save grader artifact: {error}"}
    print(json.dumps(result))
    print(f"{'PASS' if result['passed'] else 'FAIL'} {args.lab} ({args.mode}): {report}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
