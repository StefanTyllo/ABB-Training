#!/usr/bin/env python3
"""Controlled FW1 experiment: at most one justified baud change, then verify.

Engineering intent: the device may only be written when (1) a valid baseline
exists for the same device, (2) the reference entry was selected from the
observed identity, (3) the fault evidence supports a baud hypothesis, and
(4) the current configuration still equals the baseline (not stale).  Any unmet
gate returns BLOCKED with no write.  A healthy device already at target is
verified only (idempotent rerun).  The target baud is never an argument: it
comes from the matched expected.json entry.

Exit codes: 0 OK/NOOP, 1 FAIL/ERROR, 2 BLOCKED/INVALID.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capture_state as cs  # noqa: E402

ALLOWED_PARAMETER = "baud"


def hypothesis_preconditions(baseline, probe, target_baud):
    """Mechanical evidence checks for a baud fault; interpretation stays human."""
    current_baud = baseline["config"]["baud"]
    checks = {
        "link_timeout_in_baseline_faults": "LINK_TIMEOUT" in baseline["faults"],
        "probe_failing": probe.get("ok") is False,
        "baud_differs_from_target": current_baud != target_baud,
    }
    status = "SUPPORTED" if all(checks.values()) else "NOT_SUPPORTED"
    return {"status": status, "checks": checks}


def check_baseline_current(baseline, current_config):
    """Compare fresh config with baseline config before any write."""
    same = baseline["config"] == current_config
    result = {"status": "OK" if same else "BLOCKED",
              "baseline_baud": baseline["config"].get("baud"),
              "current_baud": current_config.get("baud")}
    if not same:
        result["reason"] = "stale baseline: configuration changed since baseline; new capture needed"
    return result


def apply_baud(paths, target_baud, old_baud, already_written):
    """Run exactly one ``set --parameter baud`` after re-checking all gates."""
    if already_written:
        return {"status": "BLOCKED", "reason": "a write was already made this run"}
    if isinstance(target_baud, bool) or not isinstance(target_baud, int) \
            or not cs.MIN_BAUD <= target_baud <= cs.MAX_BAUD:
        return {"status": "BLOCKED", "reason": f"baud {target_baud!r} outside {cs.MIN_BAUD}..{cs.MAX_BAUD}"}
    args = ["set", "--parameter", ALLOWED_PARAMETER, "--value", str(target_baud)]
    record = cs.run_primitive(paths, args)
    cs.log(f"[apply] expected set {old_baud} -> {target_baud}; observed rc={record['returncode']} "
           f"stdout={record['stdout_raw'].strip()!r}")
    if not record["valid"]:
        return {"status": "ERROR", "reason": "set failed; state assumed unchanged", "record": record}
    return {"status": "OK", "old": old_baud, "new": target_baud, "record": record}


def compare_before_after(baseline, after, target_baud):
    """Per-check PASS/FAIL list comparing the fresh capture with the baseline."""
    old_logs = baseline["logs"]
    new_logs = after["logs"]
    old_baud = baseline["config"]["baud"]
    expected_entry = f"baud changed: {old_baud} -> {target_baud}"
    checks = [
        ("baud_is_target", target_baud, after["config"].get("baud")),
        ("faults_empty", [], after["faults"]),
        ("probe_ok", True, after["probe"].get("ok")),
        ("original_logs_preserved", old_logs, new_logs[:len(old_logs)]),
        ("exactly_one_change_entry", [expected_entry], new_logs[len(old_logs):]),
        ("identity_unchanged", baseline["identity"], after["identity"]),
        ("firmware_unchanged", baseline["firmware"], after["firmware"]),
    ]
    rows = [{"name": n, "expected": e, "actual": a, "pass": e == a} for n, e, a in checks]
    for row in rows:
        cs.log(f"[verify] {row['name']}: expected {row['expected']!r}; observed {row['actual']!r} "
               f"-> {'PASS' if row['pass'] else 'FAIL'}")
    return {"status": "OK" if all(r["pass"] for r in rows) else "FAIL", "checks": rows}


def parsed_values(capture):
    """Flatten a capture to {name: parsed JSON}."""
    return {n: r["parsed"] for n, r in capture["records"].items()}


def run_experiment(workspace):
    """Run the gated experiment and return a result dict with ``status``."""
    run = {"started_utc": cs.utc_now(), "workspace": str(workspace), "steps": [], "wrote_device": False}

    def finish(status, reason=None, **extra):
        run.update(status=status, reason=reason, finished_utc=cs.utc_now(), **extra)
        cs.log(f"[experiment] result {status}" + (f": {reason}" if reason else ""))
        return run

    resolved = cs.resolve_paths(workspace)
    if resolved["status"] != "OK":
        return finish("BLOCKED", resolved["reason"])
    paths = resolved["paths"]

    before = cs.capture_state(paths)
    problems = cs.validate_capture(before)
    if problems["status"] != "OK":
        return finish("BLOCKED", f"capture unusable: {problems['problems']}")
    now = parsed_values(before)

    loaded = cs.load_baseline(paths)
    if loaded["status"] != "OK":
        return finish("BLOCKED", f"valid baseline required: {loaded['reason']}")
    baseline = loaded["baseline"]
    if baseline["identity"] != now["identity"]:
        return finish("BLOCKED", f"baseline is for {baseline['identity']}, device is {now['identity']}")

    reference = cs.select_reference(paths["reference"], now["identity"], now["firmware"])
    run["reference"] = reference
    if reference["status"] != "OK":
        return finish("BLOCKED", reference["reason"])
    target = reference["target_baud"]
    cs.log(f"[reference] device {now['identity']['device_id']} -> entry {reference['entry_key']!r} target_baud={target}")

    healthy = now["probe"]["ok"] and not now["faults"]
    if healthy:
        cs.log("[experiment] device healthy: verify only, no write")
        verdict = compare_before_after(baseline, now, target)
        return finish("NOOP" if verdict["status"] == "OK" else "FAIL",
                      None if verdict["status"] == "OK" else "healthy device does not match baseline/target",
                      verification=verdict)

    hypothesis = hypothesis_preconditions(baseline, now["probe"], target)
    run["hypothesis"] = hypothesis
    cs.log(f"[hypothesis] expected all baud-fault checks true; observed {hypothesis['checks']}")
    if hypothesis["status"] != "SUPPORTED":
        return finish("BLOCKED", "baud hypothesis not supported; different investigation needed")

    stale = check_baseline_current(baseline, now["config"])
    cs.log(f"[stale-check] baseline baud {stale['baseline_baud']} vs current {stale['current_baud']}")
    if stale["status"] != "OK":
        return finish("BLOCKED", stale["reason"])

    change = apply_baud(paths, target, now["config"]["baud"], run["wrote_device"])
    run["change"] = {k: v for k, v in change.items() if k != "record"}
    if change["status"] == "OK":
        run["wrote_device"] = True
    else:
        return finish(change["status"], change["reason"])

    after = cs.capture_state(paths)
    if cs.validate_capture(after)["status"] != "OK":
        return finish("FAIL", "post-change capture unusable", verification=None)
    verdict = compare_before_after(baseline, parsed_values(after), target)
    return finish("OK" if verdict["status"] == "OK" else "FAIL",
                  None if verdict["status"] == "OK" else "verification failed after the single write",
                  verification=verdict)


def main(argv=None):
    """CLI entry point; prints the result JSON and returns the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", required=True, help="absolute workspace path")
    args = parser.parse_args(argv)
    result = run_experiment(args.workspace)
    print(json.dumps(result))
    return cs.EXIT_CODES.get(result["status"], 1)


if __name__ == "__main__":
    sys.exit(main())
