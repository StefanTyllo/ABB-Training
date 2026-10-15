"""Serial, server-owning evaluation of the suite against correct and defective apps.

Usage: python automation/evaluate_variants.py --workspace PATH [--evidence-dir DIR]

For each variant (correct, no-persist, bad-boundary) in order: pick a free
loopback port, reset an owned state file, start an owned server child, poll
readiness, run guardrails.py with that server's BASE_URL and a distinct JUnit
path, parse the real JUnit, and stop the child in a finally block.  Only the
child started here is ever terminated.

Exit codes: 0 all three expected outcomes observed (status "passed");
1 an expected outcome was not met (status "failed"); 2 infrastructure
problem such as bad inputs, occupied port, failed startup or timeout
(status "blocked").
"""
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluation_lib as lib  # noqa: E402

# variant -> expected pytest return code (the engineering contract)
EXPECTED_RETURNCODE = {"correct": 0, "no-persist": 1, "bad-boundary": 1}
VARIANT_ORDER = ["correct", "no-persist", "bad-boundary"]
GUARDRAILS = Path(__file__).resolve().parent / "guardrails.py"
WATCHED_FILES = ["tests/test_settings.py", "pages/settings_page.py", "pages/base_page.py",
                 "conftest.py", "case.json", "REQUIREMENTS.md", "pytest.ini", "server.py"]


def evaluate_variant(workspace, variant, evidence_dir, ready_timeout_s, pytest_timeout_s):
    """Evaluate one variant and return its run record (status ok/blocked/error)."""
    run_dir = evidence_dir / "variants" / variant
    junit_path = run_dir / "junit.xml"
    server_log = run_dir / "server.log"
    pytest_log = run_dir / "pytest.log"
    state_path = run_dir / "state.json"
    port = lib.find_free_port()
    base_url = f"http://{lib.LOOPBACK}:{port}"
    record = {
        "variant": variant, "port": port, "base_url": base_url, "state_path": str(state_path),
        "junit_path": str(junit_path), "server_log": str(server_log), "pytest_log": str(pytest_log),
        "status": "blocked", "status_reason": "not started", "pytest_returncode": None,
        "expected_pytest_returncode": EXPECTED_RETURNCODE[variant],
        "counts": {"tests": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0},
        "failures": [], "coverage": None, "owned_server_stopped": None,
    }
    started = lib.start_server(workspace, variant, port, state_path, server_log)
    proc = started["proc"]
    try:
        if not started["ok"]:
            record["status_reason"] = f"server startup failed: {started['error']}"
            return record
        record["server_command"] = started["command"]
        ready = lib.wait_ready(base_url, ready_timeout_s, proc)
        record["readiness"] = ready
        if not ready["ready"]:
            record["status_reason"] = f"server not ready: {ready['error']}"
            return record
        result = lib.run_guardrails(workspace, base_url, junit_path, GUARDRAILS, pytest_timeout_s)
        pytest_log.parent.mkdir(parents=True, exist_ok=True)
        pytest_log.write_text(result["stdout"])
        record["pytest_returncode"] = result["returncode"]
        if result["timed_out"] or result["returncode"] in (124, 125):
            record["status_reason"] = f"suite run timed out or could not start (code {result['returncode']})"
            return record
        try:
            parsed = lib.parse_junit(junit_path)
        except lib.JUnitUnavailable as exc:
            record["status_reason"] = f"no usable JUnit report: {exc}"
            return record
        record["counts"] = parsed["counts"]
        record["failures"] = lib.classify_failures(parsed["cases"])
        record["coverage"] = lib.check_case_coverage([c["name"] for c in parsed["cases"]])
        record["status"], record["status_reason"] = "ok", "suite executed and JUnit parsed"
        return record
    finally:
        record["owned_server_stopped"] = lib.stop_server(proc)


def judge(records):
    """Apply the three expected outcomes; return (status, problems, verdicts)."""
    problems, verdicts = [], {}
    by_name = {r["variant"]: r for r in records}
    blocked = [r for r in records if r["status"] != "ok"]
    for r in blocked:
        problems.append(f"{r['variant']}: blocked - {r['status_reason']}")
    if blocked:
        return "blocked", problems, verdicts
    correct = by_name["correct"]
    cc = correct["counts"]
    if correct["pytest_returncode"] != 0 or cc["failed"] or cc["error"] or cc["skipped"]:
        problems.append(f"correct: expected rc 0 with no failures/skips/errors, observed rc "
                        f"{correct['pytest_returncode']} counts {cc}")
    if correct["coverage"] and correct["coverage"]["missing"]:
        problems.append(f"correct: required cases missing: {correct['coverage']['missing']}")
    for variant, family in lib.EXPECTED_FAMILY.items():
        verdict = lib.compare_runs(correct, by_name[variant], family)
        verdicts[variant] = verdict
        if verdict["verdict"] != "detected":
            problems.append(f"{variant}: expected 'detected', observed '{verdict['verdict']}' "
                            f"({'; '.join(verdict['reasons'])})")
        if by_name[variant]["pytest_returncode"] != EXPECTED_RETURNCODE[variant]:
            problems.append(f"{variant}: expected rc {EXPECTED_RETURNCODE[variant]}, "
                            f"observed {by_name[variant]['pytest_returncode']}")
    return ("failed" if problems else "passed"), problems, verdicts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--evidence-dir", default=None, help="default: WORKSPACE/evidence")
    parser.add_argument("--ready-timeout", type=float, default=20.0)
    parser.add_argument("--pytest-timeout", type=float, default=300.0)
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    evidence_dir = Path(args.evidence_dir).resolve() if args.evidence_dir else workspace / "evidence"
    report_path = evidence_dir / "variant-evaluation.json"
    report = {"status": "blocked", "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "workspace": str(workspace), "problems": [], "variants": {}, "verdicts": {},
              "review_required": [], "digests": {}, "not_run": []}

    checked = lib.validate_inputs(workspace, evidence_dir=evidence_dir)
    if not checked["ok"]:
        report["problems"] = checked["problems"]
        lib.write_report(report, report_path)
        print(f"BLOCKED: expected a usable workspace, observed {checked['problems']}")
        return 2
    report["digests"] = lib.collect_artifact_digests(workspace, WATCHED_FILES)

    records = []
    for variant in VARIANT_ORDER:
        print(f"== variant {variant}: starting owned server", flush=True)
        record = evaluate_variant(workspace, variant, evidence_dir, args.ready_timeout, args.pytest_timeout)
        records.append(record)
        report["variants"][variant] = record
        print(f"   status={record['status']} reason={record['status_reason']} "
              f"rc={record['pytest_returncode']} (expected {record['expected_pytest_returncode']}) "
              f"counts={record['counts']}", flush=True)
        if record["status"] != "ok":
            break  # serial gate: no later variant earns credit without a usable run

    report["not_run"] = [v for v in VARIANT_ORDER if v not in report["variants"]]
    status, problems, verdicts = judge(records) if not report["not_run"] else (
        "blocked", [f"{r['variant']}: blocked - {r['status_reason']}" for r in records if r["status"] != "ok"], {})
    report.update(status=status, problems=problems, verdicts=verdicts)
    for variant, verdict in verdicts.items():
        if verdict["verdict"] == "detected":
            family = lib.EXPECTED_FAMILY[variant]
            report["review_required"].extend(
                lib.summarize_detection(f) for f in report["variants"][variant]["failures"]
                if f["class"] == "assertion" and family in f["name"])
    lib.write_report(report, report_path)

    for problem in problems:
        print(f"PROBLEM: {problem}")
    print(f"RESULT: {status.upper()} - report {report_path}")
    return {"passed": 0, "failed": 1, "blocked": 2}[status]


if __name__ == "__main__":
    sys.exit(main())
