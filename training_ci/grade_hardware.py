#!/usr/bin/env python3
"""Externally grade a generated hardware guardrail against trusted fixture checks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


CASE_BY_BOARD = {
    "hw1": {"SENSE-ALPHA": "demo", "SENSE-BETA": "transfer"},
    "hw2": {"DIVIDER-ALPHA": "demo", "DIVIDER-BETA": "transfer"},
}
EXPECTED_ENGINEERING_EXIT = {
    ("hw1", "demo"): 0,
    ("hw1", "transfer"): 2,
    ("hw2", "demo"): 0,
    ("hw2", "transfer"): 1,
}


def run_recorded(command, workspace, records, label):
    """Keep actual process evidence, including expected nonzero engineering exits."""
    record = {"label": label, "command": [str(part) for part in command], "cwd": str(workspace)}
    try:
        result = subprocess.run(record["command"], cwd=workspace, capture_output=True,
                                text=True, timeout=120, check=False)
        record.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                      timed_out=False)
    except subprocess.TimeoutExpired as exc:
        def decoded(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
        record.update(returncode=None, stdout=decoded(exc.stdout), stderr=decoded(exc.stderr),
                      timed_out=True)
    except OSError as exc:
        record.update(returncode=None, stdout="", stderr=str(exc), timed_out=False)
    records.append(record)
    return record["returncode"]


def artifact_snapshot(workspace, lab):
    """The stable task outputs exclude appendable execution logs under evidence/."""
    derived = "netlist.json" if lab == "hw1" else "calibration.json"
    return {name: hashlib.sha256((workspace / name).read_bytes()).hexdigest()
            for name in ("report.json", f"derived/{derived}")}


def find_checker():
    root = Path(__file__).resolve().parent.parent
    for directory in ("training_kit", "materials"):
        candidate = root / directory / "hardware/instructor/check.py"
        if candidate.is_file():
            return candidate
    raise ValueError("trusted instructor checker missing under training_kit/ or materials/")


def grade(lab, workspace, mode="code"):
    evidence = {"schema_version": 1, "lab": lab, "mode": mode, "workspace": str(workspace),
                "accepted": False, "errors": [], "processes": []}
    try:
        checker = find_checker()
        if checker.is_relative_to(workspace):
            raise ValueError("trusted instructor checker must be outside the participant workspace")
        source_path = workspace / "source" / ("approval.json" if lab == "hw1" else "circuit.json")
        board = json.loads(source_path.read_text(encoding="utf-8"))["board_id"]
        case = CASE_BY_BOARD[lab].get(board)
        if case is None:
            raise ValueError(f"unknown fixture board identity: {board!r}")
        expected_exit = EXPECTED_ENGINEERING_EXIT[(lab, case)]
        evidence.update(case=case, board_id=board, expected_engineering_exit=expected_exit)
        check_command = [sys.executable, checker, "--lab", lab, "--case", case,
                         "--workspace", workspace]
        if mode == "md-only":
            checker_exit = run_recorded(check_command, workspace, evidence["processes"], "instructor_check_md_only")
            if checker_exit != 0:
                evidence["errors"].append("independent instructor check did not accept the MD-only assessment")
            else:
                evidence["artifact_snapshots"] = [artifact_snapshot(workspace, lab)]
                evidence["accepted"] = True
            return evidence
        helper = workspace / "automation/guardrails.py"
        if not helper.is_file() or helper.is_symlink():
            raise ValueError("expected regular file automation/guardrails.py is missing or is a symlink")
        command = [sys.executable, helper, "--workspace", workspace]
        snapshots = []
        for iteration in (1, 2):
            actual_exit = run_recorded(command, workspace, evidence["processes"], f"guardrails_run_{iteration}")
            if actual_exit != expected_exit:
                evidence["errors"].append(f"run {iteration}: engineering exit {actual_exit!r}; expected {expected_exit}")
            checker_exit = run_recorded(check_command, workspace, evidence["processes"], f"instructor_check_{iteration}")
            if checker_exit != 0:
                evidence["errors"].append(f"run {iteration}: independent instructor check did not accept the assessment")
            if evidence["errors"]:
                break
            snapshots.append(artifact_snapshot(workspace, lab))
        evidence["artifact_snapshots"] = snapshots
        if len(snapshots) == 2 and snapshots[0] != snapshots[1]:
            evidence["errors"].append("report.json or derived artifact changed on the second run; outputs must be idempotent")
        evidence["accepted"] = not evidence["errors"] and len(snapshots) == 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        evidence["errors"].append(str(exc))
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", required=True, choices=("hw1", "hw2"))
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--mode", choices=("md-only", "code"), default="code")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        parser.error("workspace must be an existing prepared directory")
    evidence = grade(args.lab, workspace, args.mode)
    destination = workspace / "evidence/grade_hardware.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("HARDWARE TRAINING CHECK " + ("ACCEPTED" if evidence["accepted"] else "FAILED"))
    for error in evidence["errors"]:
        print(f"- {error}")
    print(f"Process evidence: {destination}")
    raise SystemExit(0 if evidence["accepted"] else 1)


if __name__ == "__main__":
    main()
