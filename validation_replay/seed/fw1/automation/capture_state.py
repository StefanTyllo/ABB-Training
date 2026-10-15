#!/usr/bin/env python3
"""Capture FW1 device state and hold the shared helpers for the automation.

Engineering intent: every observation is taken through the existing low-level
tool (fw1/device.py) so the raw result is preserved verbatim.  A capture that is
missing any required read is never allowed to become a baseline.  All paths are
resolved from the workspace argument, never from the caller's cwd, and no
identity, firmware or baud value is hard-coded: they come from current evidence
and fw1/expected.json.

Exit codes (CLI): 0 OK, 1 FAIL/ERROR, 2 BLOCKED/INVALID.
"""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

MIN_BAUD, MAX_BAUD = 1200, 115200
TIMEOUT_S = 30

# Baseline key -> primitive arguments (placed after --workdir).
BASELINE_PRIMITIVES = {
    "identity": ["read", "--field", "identity"],
    "firmware": ["read", "--field", "firmware"],
    "config": ["read", "--field", "config"],
    "faults": ["read", "--field", "faults"],
    "logs": ["logs"],
}
ALL_PRIMITIVES = dict(BASELINE_PRIMITIVES, probe=["probe"])

EXIT_CODES = {"OK": 0, "NOOP": 0, "WRITTEN": 0, "EXISTS": 0, "SUPPORTED": 0,
              "FAIL": 1, "ERROR": 1, "BLOCKED": 2, "INVALID": 2,
              "NOT_SUPPORTED": 2}


def log(message):
    """Print an action/result line; stdout is the human-readable run log."""
    print(message, flush=True)


def utc_now():
    """Return an ISO-8601 UTC timestamp used to date each record."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_of(path):
    """Return the SHA-256 hex digest of a file, for byte-identity evidence."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_paths(workspace):
    """Resolve every input/output path from the workspace.

    Returns a dict with status OK and the paths, or BLOCKED naming the first
    missing required item.  Never runs ``init``.
    """
    root = Path(workspace).expanduser().resolve()
    paths = {
        "workspace": root,
        "tool": root / "fw1" / "device.py",
        "state_dir": root / "device",
        "state_file": root / "device" / "state.json",
        "reference": root / "fw1" / "expected.json",
        "case_file": root / "case.json",
        "evidence_dir": root / "evidence",
        "baseline": root / "evidence" / "baseline.json",
    }
    for key in ("workspace", "tool", "state_dir", "state_file", "reference"):
        if not paths[key].exists():
            log(f"[resolve] expected {key} at {paths[key]}; observed: missing -> BLOCKED")
            return {"status": "BLOCKED", "reason": f"missing {key}: {paths[key]}"}
    try:
        paths["evidence_dir"].mkdir(exist_ok=True)
        probe_file = paths["evidence_dir"] / ".write-check"
        probe_file.write_text("ok")
        probe_file.unlink()
    except OSError as exc:
        log(f"[resolve] evidence dir not writable: {exc} -> BLOCKED")
        return {"status": "BLOCKED", "reason": f"evidence dir not writable: {exc}"}
    if not paths["case_file"].exists():
        log("[resolve] note: case.json absent; not needed for reference selection")
    log(f"[resolve] expected all inputs present; observed: OK under {root}")
    return {"status": "OK", "paths": paths}


def run_primitive(paths, args):
    """Run one device primitive and keep the raw stdout, rc and timestamp.

    ``parsed`` is json.loads(stdout) or None.  An unusable result has
    ``valid`` False; the raw text is kept for the evidence trail.
    """
    argv = [sys.executable, str(paths["tool"]), "--workdir", str(paths["state_dir"])] + args
    record = {"argv": argv, "timestamp_utc": utc_now(), "returncode": None,
              "stdout_raw": "", "stderr": "", "parsed": None, "valid": False}
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        record["stderr"] = f"{type(exc).__name__}: {exc}"
        return record
    record.update(returncode=done.returncode, stdout_raw=done.stdout, stderr=done.stderr)
    if done.returncode == 0 and done.stdout.strip():
        try:
            record["parsed"] = json.loads(done.stdout)
            record["valid"] = True
        except json.JSONDecodeError:
            record["stderr"] += " stdout was not valid JSON"
    return record


def capture_state(paths):
    """Read all six observations without writing to the device.

    ``complete`` is True only when every read returned valid JSON.
    """
    records, failed = {}, []
    for name, args in ALL_PRIMITIVES.items():
        rec = run_primitive(paths, args)
        records[name] = rec
        log(f"[capture] {name}: expected rc=0 + JSON; observed rc={rec['returncode']} "
            f"stdout={rec['stdout_raw'].strip()[:80]!r}")
        if not rec["valid"]:
            failed.append(name)
    identity = (records["identity"]["parsed"] or {}) if records["identity"]["valid"] else {}
    return {"complete": not failed, "failed_reads": failed, "records": records,
            "timestamp_utc": utc_now(),
            "input_identity": {"workspace": str(paths["workspace"]),
                               "device_id": identity.get("device_id")}}


def validate_capture(capture):
    """Check shape of parsed observations; return status and a problem list."""
    problems = [f"read failed: {n}" for n in capture["failed_reads"]]
    if not problems:
        p = {n: r["parsed"] for n, r in capture["records"].items()}
        checks = [
            (isinstance(p["identity"], dict) and isinstance(p["identity"].get("device_id"), str), "identity.device_id must be str"),
            (isinstance(p["firmware"], dict) and isinstance(p["firmware"].get("version"), str), "firmware.version must be str"),
            (isinstance(p["config"], dict) and isinstance(p["config"].get("baud"), int), "config.baud must be int"),
            (isinstance(p["faults"], list), "faults must be a list"),
            (isinstance(p["logs"], list), "logs must be a list"),
            (isinstance(p["probe"], dict) and isinstance(p["probe"].get("ok"), bool) and "status" in p["probe"], "probe needs bool ok and status"),
        ]
        problems = [msg for ok, msg in checks if not ok]
    return {"status": "OK" if not problems else "INVALID", "problems": problems}


def write_baseline(paths, capture):
    """Write evidence/baseline.json once, using exclusive create.

    The file holds the five primitives' JSON values (probe excluded).
    An existing baseline is never touched.  A device that is already healthy
    with no baseline is an ERROR: history must not be fabricated.
    """
    baseline = paths["baseline"]
    if baseline.exists():
        log(f"[baseline] exists, left untouched sha256={sha256_of(baseline)}")
        return {"status": "EXISTS", "path": str(baseline), "sha256": sha256_of(baseline)}
    if not capture["complete"] or validate_capture(capture)["status"] != "OK":
        return {"status": "BLOCKED", "reason": "capture incomplete or invalid; not saved as baseline"}
    parsed = {n: capture["records"][n]["parsed"] for n in ALL_PRIMITIVES}
    if parsed["probe"]["ok"] and not parsed["faults"]:
        return {"status": "ERROR", "reason": "device already healthy and no baseline exists; refusing to fabricate history"}
    document = {n: parsed[n] for n in BASELINE_PRIMITIVES}
    with open(baseline, "x") as handle:
        handle.write(json.dumps(document) + "\n")
    log(f"[baseline] written {baseline}")
    return {"status": "WRITTEN", "path": str(baseline), "sha256": sha256_of(baseline)}


def load_baseline(paths):
    """Load and check the baseline; ERROR if missing, INVALID if malformed."""
    if not paths["baseline"].exists():
        return {"status": "ERROR", "reason": "no baseline; run capture on the unrepaired device first"}
    try:
        data = json.loads(paths["baseline"].read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "INVALID", "reason": f"unreadable baseline: {exc}"}
    missing = [k for k in BASELINE_PRIMITIVES if k not in data]
    if missing:
        return {"status": "INVALID", "reason": f"baseline missing keys {missing}"}
    return {"status": "OK", "baseline": data}


def select_reference(reference_path, identity, firmware):
    """Pick the expected entry whose device_id equals the observed id.

    Never falls back to case.json or a default: unknown ids are BLOCKED.
    """
    try:
        reference = json.loads(Path(reference_path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "BLOCKED", "reason": f"reference unreadable: {exc}"}
    matches = [(k, v) for k, v in reference.items()
               if isinstance(v, dict) and v.get("device_id") == identity.get("device_id")]
    if len(matches) != 1:
        return {"status": "BLOCKED", "reason": f"{len(matches)} reference entries match device_id "
                                               f"{identity.get('device_id')!r}"}
    key, entry = matches[0]
    if entry.get("firmware") != firmware.get("version"):
        return {"status": "BLOCKED", "reason": f"firmware mismatch: reference {entry.get('firmware')!r} "
                                               f"observed {firmware.get('version')!r}"}
    baud = entry.get("baud")
    if isinstance(baud, bool) or not isinstance(baud, int) or not MIN_BAUD <= baud <= MAX_BAUD:
        return {"status": "BLOCKED", "reason": f"reference baud {baud!r} not an int in {MIN_BAUD}..{MAX_BAUD}"}
    return {"status": "OK", "entry_key": key, "target_baud": baud, "firmware": entry["firmware"]}


def main(argv=None):
    """CLI: capture state read-only; write the baseline only with --save-baseline."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", required=True, help="absolute workspace path")
    parser.add_argument("--save-baseline", action="store_true",
                        help="save evidence/baseline.json (only if absent and device is faulted)")
    parser.add_argument("--output", help="optional path for the capture JSON")
    args = parser.parse_args(argv)

    resolved = resolve_paths(args.workspace)
    if resolved["status"] != "OK":
        print(json.dumps(resolved))
        return EXIT_CODES[resolved["status"]]
    paths = resolved["paths"]
    capture = capture_state(paths)
    result = {"status": "OK" if capture["complete"] else "BLOCKED", "capture": capture,
              "validation": validate_capture(capture)}
    if args.save_baseline:
        result["baseline"] = write_baseline(paths, capture)
        result["status"] = result["baseline"]["status"]
    elif result["validation"]["status"] != "OK":
        result["status"] = "INVALID" if capture["complete"] else "BLOCKED"
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "capture"}))
    return EXIT_CODES.get(result["status"], 1)


if __name__ == "__main__":
    sys.exit(main())
