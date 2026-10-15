#!/usr/bin/env python3
"""Common guardrails entry point for the FW1 lab.

Usage: python3 automation/guardrails.py --workspace /absolute/path

Order of operations (engineering intent: evidence before change):
1. Resolve paths from --workspace and capture the current state read-only.
2. If no baseline exists and the device is still faulted, save the baseline
   (first and only time) BEFORE any write.  If no baseline exists and the device
   is already healthy, fail: history is never fabricated.
3. Run the gated experiment (one change at most, or verify-only when healthy).
4. Confirm the baseline bytes never changed and write
   evidence/guardrails-result.json (machine-readable; safe to overwrite).

Exit codes: 0 verified OK/NOOP, 1 FAIL/ERROR, 2 BLOCKED/INVALID.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capture_state as cs  # noqa: E402
import experiment as ex  # noqa: E402


def run_guardrails(workspace):
    """Return the combined result dict for a workspace."""
    result = {"started_utc": cs.utc_now(), "workspace": str(Path(workspace).resolve())}
    resolved = cs.resolve_paths(workspace)
    if resolved["status"] != "OK":
        result.update(status="BLOCKED", reason=resolved["reason"])
        return result, None
    paths = resolved["paths"]

    baseline_hash_before = cs.sha256_of(paths["baseline"]) if paths["baseline"].exists() else None
    if baseline_hash_before is None:
        capture = cs.capture_state(paths)
        saved = cs.write_baseline(paths, capture)
        result["baseline_step"] = saved
        if saved["status"] != "WRITTEN":
            result.update(status=saved["status"], reason=saved.get("reason"))
            return result, paths
    else:
        cs.log("[guardrails] baseline already present; preserving it")

    experiment = ex.run_experiment(workspace)
    result["experiment"] = {k: v for k, v in experiment.items() if k != "steps"}
    result.update(status=experiment["status"], reason=experiment.get("reason"))

    if baseline_hash_before is not None:
        after = cs.sha256_of(paths["baseline"])
        result["baseline_preserved"] = after == baseline_hash_before
        cs.log(f"[guardrails] baseline sha256 expected {baseline_hash_before}; observed {after}")
        if after != baseline_hash_before:
            result.update(status="FAIL", reason="baseline bytes changed")
    result["finished_utc"] = cs.utc_now()
    return result, paths


def main(argv=None):
    """CLI wrapper: run, persist the result, return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", required=True, help="absolute workspace path")
    args = parser.parse_args(argv)
    result, paths = run_guardrails(args.workspace)
    if paths is not None:
        out = paths["evidence_dir"] / "guardrails-result.json"
        out.write_text(json.dumps(result, indent=2) + "\n")
        cs.log(f"[guardrails] wrote {out}")
    print(json.dumps({"status": result["status"], "reason": result.get("reason")}))
    return cs.EXIT_CODES.get(result["status"], 1)


if __name__ == "__main__":
    sys.exit(main())
