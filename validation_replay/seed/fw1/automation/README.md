# FW1 automation

All helpers live under `automation/` and take the workspace via `--workspace` (absolute path); nothing is resolved from the caller's cwd. Exit codes: `0` OK/NOOP, `1` FAIL/ERROR, `2` BLOCKED/INVALID.

| File | Role |
|---|---|
| `guardrails.py` | Common entry point: baseline (once, before any write) -> gated experiment -> baseline-preserved check. Writes `evidence/guardrails-result.json`. |
| `capture_state.py` | Read-only capture of identity, firmware, config, faults, logs, probe (raw stdout, rc, UTC timestamp, input identity). Also holds shared helpers. |
| `experiment.py` | One gated `set --parameter baud` using the target from the identity-matched `fw1/expected.json` entry; verify before/after. |
| `tests/` | Checks on disposable workspaces; altered fixtures in `tests/fixtures/`. |

## Commands (run from the workspace root)

```bash
# Common entry point (idempotent; safe to repeat)
python3 automation/guardrails.py --workspace "$PWD"

# Capture only, read-only; add --save-baseline to save evidence/baseline.json
# (only if absent and the device is still faulted)
python3 automation/capture_state.py --workspace "$PWD" [--save-baseline] [--output capture.json]

# Controlled experiment (needs a valid baseline for the same device)
python3 automation/experiment.py --workspace "$PWD"

# Checks (each builds its own disposable workspace; demo state is not touched)
python3 -m unittest discover -v automation/tests
```

## Behavior
- Missing workspace/state dir/tool/reference: `BLOCKED`, no write.
- Capture with any failed read is never saved as baseline.
- Unknown identity or firmware mismatch cannot select a reference: `BLOCKED`.
- No baseline: experiment `BLOCKED`. Baseline missing on an already healthy device: `ERROR` (history is not fabricated).
- Config differs from baseline before a write: `BLOCKED` (stale; capture again).
- At most one `set` per run. Healthy device at target: verify only (`NOOP`); baseline and `device/state.json` stay byte-identical.
- Verification: baud == target, faults empty, probe ok, original logs preserved, exactly one `baud changed: <old> -> <target>` entry. Any failed check is `FAIL`.
- Interpretation of the fault, unfamiliar faults, and explaining why historic logs are not an active fault stay with the engineer.
