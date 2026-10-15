"""Common guardrails entry point: run the learner suite against BASE_URL.

Usage: python automation/guardrails.py --workspace PATH --junit PATH [--timeout S]

Runs ``python -m pytest tests -q -ra --junitxml=JUNIT`` in the workspace,
inheriting BASE_URL unchanged (the caller owns the server).  The pytest exit
status and output are preserved.  The human-readable verdict separates
infrastructure failure (blocked) from assertion failure (a test result).

Exit codes: pytest's own code (0 pass, 1 test failures, 2-5 pytest errors);
124 on timeout; 125 when the workspace is unusable or pytest cannot launch.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluation_lib import JUnitUnavailable, classify_failures, parse_junit  # noqa: E402

EXIT_TIMEOUT = 124
EXIT_BLOCKED = 125
PYTEST_NO_TESTS = 5


def build_command(junit_path):
    """Argument-list command (no shell) required by the CI contract."""
    return [sys.executable, "-m", "pytest", "tests", "-q", "-ra", f"--junitxml={junit_path}"]


def describe_outcome(returncode, junit_path):
    """Classify the finished run and return a log line explaining expected vs observed."""
    try:
        parsed = parse_junit(junit_path)
    except JUnitUnavailable as exc:
        return f"INFRASTRUCTURE FAILURE: pytest exit {returncode} and no usable JUnit ({exc})"
    counts = parsed["counts"]
    summary = (f"tests={counts['tests']} passed={counts['passed']} failed={counts['failed']} "
               f"errors={counts['error']} skipped={counts['skipped']}")
    if returncode == 0:
        return f"PASS: expected all tests to pass, observed {summary}"
    failures = classify_failures(parsed["cases"])
    incidental = [f for f in failures if f["class"] == "incidental"]
    if incidental or returncode != 1:
        names = ", ".join(f["name"] for f in incidental) or "pytest usage/collection problem"
        return (f"INFRASTRUCTURE FAILURE: expected assertion results only, observed non-assertion "
                f"errors in [{names}] (pytest exit {returncode}); {summary}")
    names = ", ".join(f["name"] for f in failures)
    return f"ASSERTION FAILURE: {len(failures)} test(s) failed an assertion: {names}; {summary}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--junit", required=True)
    parser.add_argument("--timeout", type=float, default=600.0, help="finite pytest timeout in seconds")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    junit_path = Path(args.junit).resolve()
    if not workspace.is_dir() or not (workspace / "tests").is_dir():
        print(f"INFRASTRUCTURE FAILURE: workspace or tests directory missing: {workspace}")
        return EXIT_BLOCKED
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    junit_path.unlink(missing_ok=True)  # a stale report must never be mistaken for this run

    command = build_command(junit_path)
    print(f"guardrails: cwd={workspace} command={command}", flush=True)
    try:
        completed = subprocess.run(command, cwd=str(workspace), timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"INFRASTRUCTURE FAILURE: pytest exceeded {args.timeout}s timeout")
        return EXIT_TIMEOUT
    except OSError as exc:
        print(f"INFRASTRUCTURE FAILURE: cannot launch pytest: {exc}")
        return EXIT_BLOCKED

    print(f"guardrails: pytest exit code {completed.returncode}")
    print(f"guardrails: {describe_outcome(completed.returncode, junit_path)}")
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
