"""Checks for the T2 automation: defect detection gate, valid input, failure branches.

Fixtures are altered copies kept under automation/tests/fixtures; the real
application, suite and requirements are never modified.  Run with:
    python -m pytest automation/tests -q
"""
import json
import socket
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import evaluation_lib as lib  # noqa: E402
import evaluate_variants as ev  # noqa: E402
import guardrails  # noqa: E402

FIXTURES = HERE / "fixtures"
GUARDRAILS = HERE.parent / "guardrails.py"


def run_record(junit_name, returncode, status="ok"):
    """Build a run record from a fixture JUnit, mirroring evaluate_variant output."""
    parsed = lib.parse_junit(FIXTURES / junit_name)
    return {"status": status, "status_reason": "fixture", "pytest_returncode": returncode,
            "counts": parsed["counts"], "failures": lib.classify_failures(parsed["cases"])}


def make_workspace(tmp_path, test_fixture, server_fixture=None):
    """Create a throwaway workspace whose tests/ come from a .txt fixture."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_fixture.py").write_text((FIXTURES / test_fixture).read_text())
    for name in ("REQUIREMENTS.md",):
        (tmp_path / name).write_text("fixture")
    (tmp_path / "case.json").write_text(json.dumps(
        {"lab": "t2", "case": "x", "connection": "tcp", "host": "h", "port": "1"}))
    server = (FIXTURES / server_fixture).read_text() if server_fixture else "pass\n"
    (tmp_path / "server.py").write_text(server)
    return tmp_path


# ---- valid input: correct app ------------------------------------------------
def test_parse_junit_counts_valid_input():
    parsed = lib.parse_junit(FIXTURES / "junit_correct.xml")
    assert parsed["counts"] == {"passed": 3, "failed": 0, "error": 0, "skipped": 0, "tests": 3}


def test_case_coverage_reports_missing_boundaries():
    names = [c["name"] for c in lib.parse_junit(FIXTURES / "junit_correct.xml")["cases"]]
    coverage = lib.check_case_coverage(names)
    assert "port=65535" in coverage["missing"]
    assert any("at least 8" in m for m in coverage["missing"])


# ---- the defect: persistence failure is an assertion in the right family ----
def test_defect_assertion_detected_for_save_reload():
    correct = run_record("junit_correct.xml", 0)
    defect = run_record("junit_defect_assertion.xml", 1)
    verdict = lib.compare_runs(correct, defect, "save_reload")
    assert verdict["verdict"] == "detected", verdict
    review = lib.summarize_detection(defect["failures"][0])
    assert (review["requirement_id"], review["observed"], review["expected"]) == ("SAVE-01", "'serial'", "'tcp'")
    assert review["needs_review"] is True


def test_defect_passing_suite_is_survived():
    correct = run_record("junit_correct.xml", 0)
    assert lib.compare_runs(correct, correct, "save_reload")["verdict"] == "survived"


# ---- failure branches ---------------------------------------------------------
def test_timeout_skip_and_setup_error_are_not_detection():
    correct = run_record("junit_correct.xml", 0)
    defect = run_record("junit_defect_timeout.xml", 1)
    assert {f["class"] for f in defect["failures"]} == {"incidental"}
    assert lib.compare_runs(correct, defect, "save_reload")["verdict"] == "not_credited"


def test_failing_correct_run_gets_no_credit():
    failing_correct = run_record("junit_defect_assertion.xml", 1)
    defect = run_record("junit_defect_assertion.xml", 1)
    assert lib.compare_runs(failing_correct, defect, "save_reload")["verdict"] == "not_credited"


def test_required_skip_rejected_on_correct_run():
    skipped = run_record("junit_defect_timeout.xml", 0)
    defect = run_record("junit_defect_assertion.xml", 1)
    assert lib.compare_runs(skipped, defect, "save_reload")["verdict"] == "not_credited"


def test_blocked_run_is_blocked_not_detected():
    correct = run_record("junit_correct.xml", 0)
    blocked = {"status": "blocked", "status_reason": "port occupied", "pytest_returncode": None,
               "counts": {}, "failures": []}
    assert lib.compare_runs(correct, blocked, "save_reload")["verdict"] == "blocked"


def test_wrong_family_assertion_is_not_credited():
    correct = run_record("junit_correct.xml", 0)
    defect = run_record("junit_defect_assertion.xml", 1)
    assert lib.compare_runs(correct, defect, "port_boundary")["verdict"] == "not_credited"


def test_malformed_junit_raises_instead_of_inventing_counts(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("<testsuites><oops")
    with pytest.raises(lib.JUnitUnavailable):
        lib.parse_junit(bad)
    with pytest.raises(lib.JUnitUnavailable):
        lib.parse_junit(tmp_path / "missing.xml")


def test_occupied_port_is_reported_and_occupant_survives(tmp_path):
    ws = make_workspace(tmp_path, "ws_passes.txt")
    with socket.socket() as occupant:
        occupant.bind((lib.LOOPBACK, 0))
        occupant.listen(1)
        port = occupant.getsockname()[1]
        started = lib.start_server(ws, "correct", port, tmp_path / "s.json", tmp_path / "log.txt")
        assert started["ok"] is False and "occupied" in started["error"]
        assert occupant.fileno() != -1  # occupant untouched


def test_failed_startup_is_blocked(tmp_path):
    ws = make_workspace(tmp_path, "ws_passes.txt", "server_exits_immediately.txt")
    record = ev.evaluate_variant(ws, "correct", tmp_path / "evidence", ready_timeout_s=5, pytest_timeout_s=30)
    assert record["status"] == "blocked" and "not ready" in record["status_reason"]
    assert record["owned_server_stopped"]["stopped"] is True


# ---- guardrails: pytest status preserved, infra vs assertion distinguished ---
@pytest.mark.parametrize("fixture,expected_rc,expected_text", [
    ("ws_passes.txt", 0, "PASS"),
    ("ws_assertion_fails.txt", 1, "ASSERTION FAILURE"),
    ("ws_infra_error.txt", 1, "INFRASTRUCTURE FAILURE"),
])
def test_guardrails_preserves_status_and_labels(tmp_path, capsys, fixture, expected_rc, expected_text):
    ws = make_workspace(tmp_path, fixture)
    junit = tmp_path / "out" / "r.xml"
    assert guardrails.main(["--workspace", str(ws), "--junit", str(junit)]) == expected_rc
    assert expected_text in capsys.readouterr().out
    assert junit.is_file()


def test_guardrails_missing_workspace_is_blocked_without_junit(tmp_path, capsys):
    junit = tmp_path / "r.xml"
    assert guardrails.main(["--workspace", str(tmp_path / "nope"), "--junit", str(junit)]) == guardrails.EXIT_BLOCKED
    assert not junit.exists()
    assert "INFRASTRUCTURE FAILURE" in capsys.readouterr().out
