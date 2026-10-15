"""Checks for the automation helpers: defect, valid-input and failure branches.

Pure-parsing checks use altered fixtures from automation/tests/fixtures.
Browser checks use the supplied `page` fixture and need the app at BASE_URL.
Run from the workspace root: python -m pytest automation/tests -q -rA
"""
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from automation import helpers

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
WORKSPACE = HERE.parent.parent


def classify_fixture(name, returncode):
    """Parse a fixture JUnit file and classify it as guardrails would."""
    report = helpers.parse_junit(FIXTURES / name)
    return report, helpers.classify_outcome(returncode, report)


def test_valid_junit_is_passed_with_real_counts():
    report, (status, reason) = classify_fixture("junit_pass.xml", 0)
    print(f"expected PASSED/4 passed; observed {status} ({reason}) counts={report['passed']}")
    assert (report["collected"], report["passed"], report["skipped"]) == (4, 4, 0)
    assert status == helpers.PASSED


def test_skipped_required_test_is_incomplete_not_coverage():
    report, (status, reason) = classify_fixture("junit_skipped_required.xml", 0)
    print(f"expected INCOMPLETE; observed {status} ({reason})")
    assert report["skipped"] == 1
    assert status == helpers.INCOMPLETE
    assert helpers.required_names_present(report)["save_reload"] == 1


def test_assertion_failure_is_failed_not_blocked():
    _, (status, reason) = classify_fixture("junit_assertion_failure.xml", 1)
    print(f"expected FAILED; observed {status} ({reason})")
    assert status == helpers.FAILED


def test_startup_error_is_blocked_not_failed():
    _, (status, reason) = classify_fixture("junit_startup_error.xml", 1)
    print(f"expected BLOCKED; observed {status} ({reason})")
    assert status == helpers.BLOCKED


def test_missing_or_timed_out_run_is_blocked():
    assert helpers.classify_outcome(1, None)[0] == helpers.BLOCKED
    assert helpers.classify_outcome(None, helpers.parse_junit(FIXTURES / "junit_pass.xml"),
                                    timed_out=True)[0] == helpers.BLOCKED
    with pytest.raises(helpers.ReportError):
        helpers.parse_junit(FIXTURES / "does_not_exist.xml")


def test_case_loader_valid_alternate_and_missing_keys():
    alternate = helpers.load_case(FIXTURES / "case_alternate.json")
    assert alternate["device"] == "COM9"
    with pytest.raises(helpers.CaseError, match="lacks keys"):
        helpers.load_case(FIXTURES / "case_missing_keys.json")
    with pytest.raises(helpers.CaseError):
        helpers.load_case(FIXTURES / "nope.json")


def test_no_fixed_sleep_or_skip_in_framework():
    clean = [WORKSPACE / "pages" / "settings_page.py", WORKSPACE / "tests" / "test_settings.py",
             *sorted((WORKSPACE / "automation").glob("*.py"))]
    assert helpers.scan_forbidden(clean) == []
    hits = helpers.scan_forbidden([FIXTURES / "sleepy_test.py.txt"])
    print(f"expected 1 fixed-sleep hit in altered fixture; observed {hits}")
    assert [h["kind"] for h in hits] == ["fixed sleep"]


def test_compare_runs_reports_instability():
    stable = helpers.parse_junit(FIXTURES / "junit_pass.xml")
    flaky = helpers.parse_junit(FIXTURES / "junit_skipped_required.xml")
    assert helpers.compare_runs([stable, stable])["stable"]
    result = helpers.compare_runs([stable, flaky])
    assert not result["stable"] and result["differences"][0]["this"] == "skipped"


def test_protected_files_detect_change(tmp_path):
    target = tmp_path / "guarded.txt"
    target.write_text("original")
    baseline = helpers.hash_files([target])
    assert helpers.verify_protected(baseline) == []
    target.write_text("altered")
    assert helpers.verify_protected(baseline) == [str(target)]


def test_wrong_url_is_reported_unavailable():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        dead_url = f"http://127.0.0.1:{probe.getsockname()[1]}"
    result = helpers.check_app_ready(dead_url, timeout_s=1)
    print(f"expected ready=False; observed {result}")
    assert result["ready"] is False and "Error" in result["detail"]


def test_guardrails_wrong_url_reports_blocked(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        dead_url = f"http://127.0.0.1:{probe.getsockname()[1]}"
    junit = tmp_path / "wrong-url.xml"
    env = {**os.environ, "BASE_URL": dead_url}
    run = subprocess.run([sys.executable, str(WORKSPACE / "automation" / "guardrails.py"),
                          "--workspace", str(WORKSPACE), "--junit", str(junit), "--timeout", "120"],
                         capture_output=True, text=True, env=env, timeout=180)
    summary = json.loads((tmp_path / "wrong-url-summary.json").read_text())
    print(run.stdout[-800:])
    assert run.returncode != 0
    assert summary["status"] == helpers.BLOCKED
    assert summary["counts"]["passed"] == 0


def test_known_good_interaction_with_alternate_case(page):
    case = helpers.load_case(FIXTURES / "case_alternate.json")
    page.choose_connection(case["connection"])
    page.fill("device", case["device"])
    page.choose_auth(case["auth"])
    page.fill("password", case["password"])
    assert page.save() == "Saved"
    page.reload()
    visibility = helpers.snapshot_visibility(page.driver)
    print(f"observed visibility after reload: {visibility}")
    assert page.value("device") == case["device"]
    assert page.value("password") == case["password"]
    assert visibility["device"] is True and visibility["host"] is False


def test_missing_element_produces_useful_failure_evidence(page, tmp_path):
    with pytest.raises(TimeoutException) as caught:
        WebDriverWait(page.driver, 1).until(lambda d: d.find_element("id", "no-such-field"))
    paths = helpers.capture_failure_evidence(page.driver, tmp_path, "missing-element", caught.value)
    context = Path(paths["context"]).read_text()
    print(context)
    assert Path(paths["screenshot"]).stat().st_size > 0
    assert "url: http" in context and "aria-busy: false" in context
    assert "TimeoutException" in context and '"device": true' in context
