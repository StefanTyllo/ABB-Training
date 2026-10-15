"""Deterministic helpers for the T2 test-effectiveness evaluation.

Engineering intent: everything mechanical (ports, owned child servers,
readiness polling, JUnit parsing, failure classification, verdict gating,
report writing) lives here.  Judging whether a defect is a true requirement
violation, and whether a detecting assertion is the *right* one, stays with
a human reviewer; every detection produced here is marked ``needs_review``.

Only the standard library is used.  Nothing here edits tests, expected
values or application files.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

LOOPBACK = "127.0.0.1"

# Exception types that mean "the suite asserted something false".
ASSERTION_TYPES = {"AssertionError"}

# Variant -> test-name family that must contain a relevant assertion failure.
EXPECTED_FAMILY = {
    "no-persist": "save_reload",
    "bad-boundary": "port_boundary",
}

# Required-case matrix from the task card: name fragments and port parameters.
REQUIRED_CASES = {
    "names": ["save_reload", "port_boundary", "invalid_save"],
    "port_params": ["1", "65535", "0", "65536", "abc"],
}
MINIMUM_EXECUTED = 8

# Requirement IDs by test-name family (the oracle is REQUIREMENTS.md).
REQUIREMENT_BY_FAMILY = {
    "save_reload": "SAVE-01",
    "invalid_save": "SAVE-01",
    "port_boundary": "VAL-01",
}


class JUnitUnavailable(Exception):
    """Raised when a JUnit report is missing or malformed (never fabricated)."""


def sha256_of(path):
    """Return the SHA-256 hex digest of a file, or None when it is absent."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def validate_inputs(workspace, requirements="REQUIREMENTS.md", case="case.json", evidence_dir=None):
    """Check the workspace oracle files; return ``{ok, problems, case}``.

    A non-empty ``problems`` list means the run is blocked.  Only the
    evidence directory is ever created.
    """
    problems = []
    workspace = Path(workspace)
    case_data = {}
    if not workspace.is_dir():
        return {"ok": False, "problems": [f"workspace is not a directory: {workspace}"], "case": case_data}
    for label, name in (("requirements", requirements), ("case", case), ("server", "server.py")):
        if not (workspace / name).is_file():
            problems.append(f"{label} file missing or unreadable: {workspace / name}")
    if not (workspace / "tests").is_dir():
        problems.append(f"tests directory missing in {workspace}")
    if (workspace / case).is_file():
        try:
            case_data = json.loads((workspace / case).read_text())
            missing = [k for k in ("lab", "case", "connection", "host", "port") if k not in case_data]
            if missing:
                problems.append(f"case file lacks keys: {missing}")
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"case file is not valid JSON: {exc}")
    if evidence_dir is not None:
        try:
            Path(evidence_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            problems.append(f"evidence directory not creatable: {exc}")
    return {"ok": not problems, "problems": problems, "case": case_data}


def collect_artifact_digests(workspace, relative_paths):
    """Map each relative path to its SHA-256 digest (None if missing)."""
    return {rel: sha256_of(Path(workspace) / rel) for rel in relative_paths}


def find_free_port(host=LOOPBACK):
    """Ask the OS for a currently free port.  Callers must still handle a later bind failure."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def port_is_free(port, host=LOOPBACK):
    """True when nothing accepts connections on host:port (probe only; never kills)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) != 0


def probe_url(url, timeout_s=2.0):
    """Read-only health probe, e.g. to show a root-owned server still answers."""
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, OSError, ValueError):
        return False


def start_server(workspace, variant, port, state_path, log_path):
    """Start an owned server child; return ``{ok, proc, pid, error, command}``.

    The state file lives in a directory this runner owns, so removing a stale
    copy is a safe clean reset.  An occupied port is reported, never cleared
    by killing the occupant.
    """
    state_path, log_path = Path(state_path), Path(log_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not port_is_free(port):
        return {"ok": False, "proc": None, "pid": None, "command": None,
                "error": f"port {port} is already occupied"}
    state_path.unlink(missing_ok=True)
    command = [sys.executable, "server.py", "--variant", variant, "--port", str(port), "--state", str(state_path)]
    log_handle = open(log_path, "w")
    try:
        proc = subprocess.Popen(command, cwd=str(workspace), stdout=log_handle, stderr=subprocess.STDOUT)
    except OSError as exc:
        log_handle.close()
        return {"ok": False, "proc": None, "pid": None, "command": command, "error": f"cannot launch server: {exc}"}
    proc.log_handle = log_handle  # closed by stop_server
    return {"ok": True, "proc": proc, "pid": proc.pid, "command": command, "error": None}


def wait_ready(base_url, timeout_s, proc=None, interval_s=0.2):
    """Poll ``base_url`` until it answers, the owned process dies, or time runs out."""
    started = time.monotonic()
    last_error = "not polled"
    while time.monotonic() - started < timeout_s:
        if proc is not None and proc.poll() is not None:
            return {"ready": False, "elapsed_s": round(time.monotonic() - started, 3),
                    "error": f"server exited early with code {proc.returncode}"}
        try:
            with urllib.request.urlopen(base_url + "/", timeout=1.0) as response:
                if response.status == 200:
                    return {"ready": True, "elapsed_s": round(time.monotonic() - started, 3), "error": None}
        except (urllib.error.URLError, OSError) as exc:
            last_error = str(exc)
        time.sleep(interval_s)  # bounded readiness poll of our own server, not a UI wait
    return {"ready": False, "elapsed_s": round(time.monotonic() - started, 3),
            "error": f"timeout after {timeout_s}s: {last_error}"}


def stop_server(proc, grace_s=5.0):
    """Terminate only the owned child handle; kill after the grace period."""
    if proc is None:
        return {"stopped": True, "forced": False}
    forced = False
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=grace_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            forced = True
            proc.wait(timeout=grace_s)
    handle = getattr(proc, "log_handle", None)
    if handle is not None:
        handle.close()
    return {"stopped": proc.poll() is not None, "forced": forced}


def parse_junit(junit_path):
    """Parse a real JUnit file into counts and per-case records.

    Raises JUnitUnavailable if the file is missing or malformed.
    """
    try:
        root = ET.parse(str(junit_path)).getroot()
    except (OSError, ET.ParseError) as exc:
        raise JUnitUnavailable(f"{junit_path}: {exc}") from exc
    cases = []
    for element in root.iter("testcase"):
        record = {"name": element.get("name", ""), "status": "passed", "message": None, "exc_type": None}
        for tag, status in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
            child = element.find(tag)
            if child is not None:
                message = child.get("message")
                # pytest's JUnit omits ``type``; the exception name prefixes the message.
                prefix = re.match(r"([A-Za-z_][\w.]*(?:Error|Exception)):", message or "")
                exc_type = child.get("type") or (prefix.group(1).split(".")[-1] if prefix else None)
                record.update(status=status, message=message, exc_type=exc_type)
                break
        cases.append(record)
    counts = {status: sum(1 for c in cases if c["status"] == status)
              for status in ("passed", "failed", "error", "skipped")}
    counts["tests"] = len(cases)
    return {"counts": counts, "cases": cases}


def requirement_for(test_name):
    """Requirement ID implied by the test-name family, or None."""
    for family, requirement in REQUIREMENT_BY_FAMILY.items():
        if family in test_name:
            return requirement
    return None


def classify_failures(cases):
    """Tag each failed/errored case ``assertion`` or ``incidental``.

    Unknown exception types default to incidental, never to detection.
    """
    classified = []
    for case in cases:
        if case["status"] not in ("failed", "error"):
            continue
        is_assertion = case["status"] == "failed" and (case.get("exc_type") or "") in ASSERTION_TYPES
        classified.append({**case, "class": "assertion" if is_assertion else "incidental",
                           "requirement_id": requirement_for(case["name"])})
    return classified


def check_case_coverage(case_names, required=REQUIRED_CASES, minimum=MINIMUM_EXECUTED):
    """Report which required name fragments and port parameters are present."""
    present, missing = [], []
    for fragment in required["names"]:
        (present if any(fragment in n for n in case_names) else missing).append(fragment)
    for value in required["port_params"]:
        found = any("port_boundary" in n and re.search(rf"[\[-]{re.escape(value)}[\]-]", n) for n in case_names)
        (present if found else missing).append(f"port={value}")
    if len(case_names) < minimum:
        missing.append(f"at least {minimum} tests (found {len(case_names)})")
    return {"present": present, "missing": missing, "executed_count": len(case_names)}


def summarize_detection(failure):
    """Review-sheet entry for one detecting failure; underivable fields are None."""
    message = failure.get("message") or ""
    match = re.search(r"assert\s+(.+?)\s*==\s*(.+?)(?:\n|$)", message)
    name = failure["name"]
    after_reload = any(t in name for t in ("save_reload", "invalid_save", "accepts_valid"))
    return {
        "test": name,
        "requirement_id": failure.get("requirement_id"),
        "observed": match.group(1) if match else None,
        "expected": match.group(2) if match else None,
        "phase": "after_reload" if after_reload else "before_reload",
        "phase_is_heuristic": True,
        "message": message[:300],
        "needs_review": True,
    }


def compare_runs(correct, defect, expected_family):
    """Gate a defect run against the correct run.

    Verdicts: detected, survived, not_credited, blocked.  Provisional until a
    human reviews the detecting assertion.
    """
    if correct["status"] == "blocked" or defect["status"] == "blocked":
        why = "; ".join(r["status_reason"] for r in (correct, defect) if r["status"] == "blocked")
        return {"verdict": "blocked", "reasons": [f"infrastructure failure: {why}"]}
    c, d = correct["counts"], defect["counts"]
    if correct["pytest_returncode"] != 0 or c["failed"] or c["error"] or c["skipped"]:
        return {"verdict": "not_credited", "reasons": ["correct app did not pass cleanly with 0 skips/errors"]}
    if defect["pytest_returncode"] == 0 and not (d["failed"] or d["error"]):
        return {"verdict": "survived", "reasons": ["defective variant passed the suite: coverage gap"]}
    if d["skipped"] or d["error"]:
        return {"verdict": "not_credited", "reasons": [f"defect run has {d['skipped']} skips and {d['error']} errors"]}
    incidental = [f for f in defect["failures"] if f["class"] == "incidental"]
    if incidental:
        return {"verdict": "not_credited", "reasons": [f"{len(incidental)} incidental (non-assertion) failure(s)"]}
    relevant = [f for f in defect["failures"] if f["class"] == "assertion" and expected_family in f["name"]]
    if not relevant:
        return {"verdict": "not_credited", "reasons": [f"no assertion failure in '{expected_family}' family"]}
    return {"verdict": "detected", "reasons": [f"{len(relevant)} assertion failure(s) in '{expected_family}' family"]}


def run_guardrails(workspace, base_url, junit_path, guardrails_path, timeout_s):
    """Run guardrails.py as a child with BASE_URL set; keep its real return code."""
    env = dict(os.environ, BASE_URL=base_url)
    command = [sys.executable, str(guardrails_path), "--workspace", str(workspace),
               "--junit", str(junit_path), "--timeout", str(timeout_s)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, env=env, timeout=timeout_s + 30)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return {"returncode": None, "stdout": output, "timed_out": True}
    return {"returncode": completed.returncode, "stdout": completed.stdout + completed.stderr, "timed_out": False}


def write_report(report, out_path):
    """Write a fresh JSON report (never merges with stale content)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    return out_path
