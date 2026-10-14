#!/usr/bin/env python3
"""Run the workspace pytest suite and report it honestly.

Usage: python automation/guardrails.py --workspace PATH --junit PATH [--timeout S]

pytest is run as `sys.executable -m pytest tests -q -ra --junitxml=JUNIT` with
cwd = workspace and BASE_URL inherited unchanged (the caller owns the server).
Exit status: pytest's own status is preserved, except
  124  pytest timed out (BLOCKED)
  125  pytest could not be launched (BLOCKED)
  4    pytest exited 0 but the run is INCOMPLETE (skips / missing coverage)
Tests, expected values and application files are never modified.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from automation import helpers  # noqa: E402

EXIT_TIMEOUT, EXIT_LAUNCH_FAILED, EXIT_INCOMPLETE = 124, 125, 4


def run_pytest(workspace, junit_path, timeout_s):
    """Run pytest; return (returncode, output_text, timed_out). Output is echoed."""
    command = [sys.executable, "-m", "pytest", "tests", "-q", "-ra", f"--junitxml={junit_path}"]
    print(f"[guardrails] command: {command} (cwd={workspace})", flush=True)
    try:
        completed = subprocess.run(command, cwd=workspace, capture_output=True, text=True,
                                   timeout=timeout_s, env=os.environ.copy())
    except subprocess.TimeoutExpired as exc:
        partial = (exc.stdout or b"")
        partial = partial.decode(errors="replace") if isinstance(partial, bytes) else partial
        return None, partial, True
    except OSError as exc:
        return None, f"launch failure: {exc}", False
    output = completed.stdout + completed.stderr
    sys.stdout.write(output)
    return completed.returncode, output, False


def main(argv=None):
    """CLI entry point; returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--junit", required=True)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--summary", help="summary JSON (default: <junit stem>-summary.json beside JUnit)")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    junit = Path(args.junit).resolve()
    summary_path = Path(args.summary) if args.summary else junit.with_name(junit.stem + "-summary.json")
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8765")
    if not (workspace / "tests").is_dir():
        print(f"[guardrails] BLOCKED: {workspace} has no tests directory")
        return EXIT_LAUNCH_FAILED
    junit.parent.mkdir(parents=True, exist_ok=True)
    junit.unlink(missing_ok=True)  # a stale report must never be mistaken for this run

    returncode, output, timed_out = run_pytest(workspace, junit, args.timeout)
    report = None
    if junit.exists():
        try:
            report = helpers.parse_junit(junit)
        except helpers.ReportError as exc:
            print(f"[guardrails] {exc}")
    status, reason = helpers.classify_outcome(returncode, report, output, timed_out)
    if returncode is None and not timed_out:
        status, reason = helpers.BLOCKED, "pytest could not be launched"

    browser = helpers.probe_browser(headed=os.environ.get("HEADED") == "1",
                                    binary=os.environ.get("CHROME_BINARY") or None,
                                    driver_path=os.environ.get("CHROMEDRIVER") or None)
    print(f"[guardrails] browser: {browser}")
    helpers.write_summary(summary_path, status, reason, report, browser=browser, url=base_url,
                          artifacts={"junit": str(junit), "workspace": str(workspace),
                                     "pytest_returncode": returncode})
    counts = report and {k: report[k] for k in ("collected", "passed", "failed", "skipped", "errors")}
    kind = {helpers.BLOCKED: "infrastructure problem (not a UI assertion result)",
            helpers.FAILED: "UI/assertion failure (the product or a test is wrong)",
            helpers.INCOMPLETE: "incomplete coverage (not acceptance)",
            helpers.PASSED: "all executed tests passed"}[status]
    print(f"[guardrails] expected: pytest exit 0 with no skips/errors at {base_url}")
    print(f"[guardrails] observed: status={status} pytest_exit={returncode} counts={counts}")
    print(f"[guardrails] reason: {reason} -> {kind}")
    print(f"[guardrails] evidence: {junit} , {summary_path}")

    if timed_out:
        return EXIT_TIMEOUT
    if returncode is None:
        return EXIT_LAUNCH_FAILED
    if returncode == 0 and status != helpers.PASSED:
        return EXIT_INCOMPLETE
    return returncode


if __name__ == "__main__":
    sys.exit(main())
