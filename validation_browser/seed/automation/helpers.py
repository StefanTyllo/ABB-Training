"""Reusable helpers extracted from workflow.md (see extraction-map.md).

Nothing here holds case values or requirement expectations: those come from
case.json / REQUIREMENTS.md and live in the tests. Helpers only collect, parse,
count, compare and report.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

PASSED, FAILED, BLOCKED, INCOMPLETE = "PASSED", "FAILED", "BLOCKED", "INCOMPLETE"
REQUIRED_CASE_KEYS = ("connection", "host", "port", "auth", "password", "device")
REQUIRED_TEST_FRAGMENTS = ("connection_visibility", "auth_visibility", "save_reload")
FORM_FIELD_IDS = ("connection", "device", "host", "port", "auth", "password", "save", "status")

# Error text that means the environment broke, not that the product misbehaved.
INFRASTRUCTURE_PATTERNS = re.compile(
    r"ConnectionRefusedError|URLError|Connection refused|Max retries exceeded|"
    r"NewConnectionError|SessionNotCreatedException|NoSuchDriverException|"
    r"chrome not reachable|cannot find Chrome binary|Unable to obtain driver|"
    r"unknown error: (?:cannot|Chrome failed)|net::ERR_CONNECTION|ERR_NAME_NOT_RESOLVED",
    re.IGNORECASE,
)
# Built by concatenation so this module does not flag itself when scanned.
FORBIDDEN_PATTERNS = {
    "fixed sleep": re.compile(r"\b(?:time\.)?sl" r"eep\s*\("),
    "skip/xfail": re.compile(r"pytest\.(?:sk" r"ip|xf" r"ail|importor" r"skip)|mark\.(?:sk" r"ip|xf" r"ail)"),
}


class CaseError(Exception):
    """case.json is missing, unparseable or lacks a required key."""


class ReportError(Exception):
    """A JUnit report is missing or invalid; counts are never guessed."""


class BrowserStartupError(Exception):
    """Chrome/driver could not be created (infrastructure, not an assertion)."""


def utc_now():
    """Current UTC time as an ISO string for evidence records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_case(path):
    """Return the case dict from `path`, raising CaseError naming the problem."""
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise CaseError(f"cannot read case file {path}: {exc}") from exc
    missing = [key for key in REQUIRED_CASE_KEYS if key not in data]
    if missing:
        raise CaseError(f"case file {path} lacks keys {missing}")
    return data


def check_app_ready(base_url, timeout_s=10.0, interval_s=0.25):
    """Poll `base_url` until it answers HTTP 200, within a finite deadline.

    Returns {"ready", "url", "detail"} and never raises on connection errors.
    The only pause is the bounded retry interval between probes (not a UI wait).
    """
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            with urllib.request.urlopen(base_url, timeout=2) as response:
                return {"ready": response.status == 200, "url": base_url,
                        "detail": f"HTTP {response.status}"}
        except (urllib.error.URLError, OSError, ValueError) as exc:
            detail = f"{type(exc).__name__}: {exc}"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"ready": False, "url": base_url, "detail": detail}
        threading.Event().wait(min(interval_s, remaining))


def start_browser(headed=False, binary=None, driver_path=None):
    """Create Chrome; return (driver, identity). Failure -> BrowserStartupError."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        options = webdriver.ChromeOptions()
        if not headed:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,900")
        if binary:
            options.binary_location = binary
        service = Service(driver_path) if driver_path else Service()
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as exc:  # any creation failure is infrastructure
        raise BrowserStartupError(f"{type(exc).__name__}: {exc}") from exc
    caps = driver.capabilities
    return driver, {"browser": caps.get("browserName"), "version": caps.get("browserVersion")}


def parse_junit(path):
    """Count outcomes in a JUnit file. Raises ReportError if absent/invalid."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ReportError(f"cannot parse JUnit report {path}: {exc}") from exc
    cases = []
    for element in root.iter("testcase"):
        outcome, message = "passed", ""
        for tag, label in (("failure", "failed"), ("error", "errors"), ("skipped", "skipped")):
            child = element.find(tag)
            if child is not None:
                outcome = label
                message = (child.get("message") or "") + "\n" + (child.text or "")
                break
        cases.append({"name": element.get("name", ""), "classname": element.get("classname", ""),
                      "outcome": outcome, "message": message.strip()})
    counts = {key: sum(1 for c in cases if c["outcome"] == key)
              for key in ("passed", "failed", "skipped", "errors")}
    return {"collected": len(cases), **counts, "cases": cases}


def required_names_present(report, required=REQUIRED_TEST_FRAGMENTS):
    """Count executed (not skipped) cases whose name contains each fragment."""
    return {fragment: sum(1 for c in report["cases"]
                          if fragment in c["name"] and c["outcome"] != "skipped")
            for fragment in required}


def classify_outcome(returncode, report, log_text="", timed_out=False, required=REQUIRED_TEST_FRAGMENTS):
    """Return (status, reason). Ambiguity resolves to BLOCKED, never PASSED.

    BLOCKED: timeout, no report, or errors showing the app/browser was
    unavailable. FAILED: a genuine assertion/test failure. INCOMPLETE: green
    run that skipped tests, collected nothing, or lacks a required test family.
    """
    if timed_out:
        return BLOCKED, "pytest exceeded the time limit"
    if report is None:
        return BLOCKED, "no JUnit report was produced; cannot count results"
    infra = [c for c in report["cases"] if c["outcome"] in ("errors", "failed")
             and INFRASTRUCTURE_PATTERNS.search(c["message"])]
    if infra:
        return BLOCKED, f"infrastructure error in {len(infra)} case(s), first: {infra[0]['name']}"
    if report["collected"] == 0 and INFRASTRUCTURE_PATTERNS.search(log_text):
        return BLOCKED, "infrastructure error during collection"
    if report["errors"]:
        return BLOCKED, f"{report['errors']} setup/teardown error(s) not attributable to an assertion"
    if report["failed"]:
        return FAILED, f"{report['failed']} assertion failure(s), pytest exit {returncode}"
    if report["collected"] == 0:
        return INCOMPLETE, "no tests were collected"
    if report["skipped"]:
        return INCOMPLETE, f"{report['skipped']} test(s) skipped; skips are not coverage"
    missing = [k for k, n in required_names_present(report, required).items() if n == 0]
    if missing:
        return INCOMPLETE, f"no executed test for required family: {missing}"
    if returncode != 0:
        return BLOCKED, f"pytest exit {returncode} without a recorded failure"
    return PASSED, f"{report['passed']} passed, none skipped"


def scan_forbidden(paths):
    """List fixed sleeps and skip/xfail markers in the given Python files."""
    hits = []
    for path in map(Path, paths):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#", 1)[0]
            for label, pattern in FORBIDDEN_PATTERNS.items():
                if pattern.search(code):
                    hits.append({"file": str(path), "line": number, "kind": label, "text": line.strip()})
    return hits


def compare_runs(reports):
    """Compare per-test outcomes across repeated runs; stable means identical."""
    differences = []
    baseline = {c["name"]: c["outcome"] for c in reports[0]["cases"]} if reports else {}
    for index, report in enumerate(reports[1:], 2):
        current = {c["name"]: c["outcome"] for c in report["cases"]}
        for name in sorted(set(baseline) | set(current)):
            if baseline.get(name) != current.get(name):
                differences.append({"run": index, "test": name,
                                    "first": baseline.get(name), "this": current.get(name)})
    return {"stable": not differences, "differences": differences}


def snapshot_visibility(driver, ids=FORM_FIELD_IDS):
    """Non-waiting {id: displayed, or None if absent} for the given element ids."""
    from selenium.webdriver.common.by import By
    state = {}
    for element_id in ids:
        found = driver.find_elements(By.ID, element_id)
        state[element_id] = found[0].is_displayed() if found else None
    return state


def capture_failure_evidence(driver, out_dir, label, error=None):
    """Save screenshot + text context. Capture problems are recorded, not raised."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", label)
    png, txt = out / f"{safe}.png", out / f"{safe}.txt"
    lines = [f"label: {label}", f"captured_at: {utc_now()}"]
    if error is not None:
        lines.append(f"error: {type(error).__name__}: {error}")
    for name, getter in (
        ("url", lambda: driver.current_url),
        ("title", lambda: driver.title),
        ("aria-busy", lambda: driver.find_element("id", "settings").get_attribute("aria-busy")),
        ("visibility", lambda: json.dumps(snapshot_visibility(driver))),
        ("screenshot", lambda: str(png) if driver.save_screenshot(str(png)) else "not saved"),
    ):
        try:
            lines.append(f"{name}: {getter()}")
        except Exception as exc:
            lines.append(f"{name}: capture failed ({type(exc).__name__}: {exc})")
    txt.write_text("\n".join(lines) + "\n")
    return {"screenshot": str(png) if png.exists() else None, "context": str(txt)}


def hash_files(paths):
    """SHA-256 map for files (baseline for protected-file checks)."""
    return {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}


def verify_protected(baseline_hashes):
    """Return paths whose current hash differs from (or is missing vs) baseline."""
    changed = []
    for path, digest in baseline_hashes.items():
        try:
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                changed.append(path)
        except OSError:
            changed.append(path)
    return changed


def write_summary(path, status, reason, report, browser, url, artifacts):
    """Write machine-readable JSON containing only real, passed-in values."""
    if report is None and status != BLOCKED:
        raise ValueError("counts are required unless the run is BLOCKED")
    payload = {"generated_at": utc_now(), "status": status, "reason": reason,
               "url": url, "browser": browser, "counts": None, "cases": [],
               "artifacts": artifacts}
    if report is not None:
        payload["counts"] = {k: report[k] for k in ("collected", "passed", "failed", "skipped", "errors")}
        payload["cases"] = [{"name": c["name"], "outcome": c["outcome"]} for c in report["cases"]]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return payload
