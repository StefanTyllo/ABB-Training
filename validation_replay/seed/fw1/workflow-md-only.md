# Workflow: restore a simulated device link by one justified configuration change

Derived from one observed run (a single happy path). Steps marked **UNTESTED** were not exercised in that run; treat them as intended behavior to verify, not proven behavior.

## Named inputs (validate before any device command)
| Input | Meaning | Missing/invalid behavior |
|---|---|---|
| `WORKSPACE` | Absolute workspace root; resolve every other path from it, never from the caller's cwd | BLOCKED |
| `TOOL` | `<WORKSPACE>/fw1/device.py` | BLOCKED |
| `STATE_DIR` | `<WORKSPACE>/device`, must contain `state.json` | BLOCKED; never run `init` (it refuses existing state and would fabricate a device) |
| `REFERENCE` | `<WORKSPACE>/fw1/expected.json`, read-only fixed authority | BLOCKED |
| `CASE` | `<WORKSPACE>/case.json`, read-only metadata | Not needed to select the reference; if absent, continue and note it |
| `EVIDENCE_DIR` | `<WORKSPACE>/evidence`, must be writable | BLOCKED if it cannot be created or written |

BLOCKED means: stop, make no device write, and report which input failed. Do not substitute a default or a value from another case.
Call the tool as `python TOOL --workdir STATE_DIR <primitive>`. Each primitive prints one JSON value to stdout; failures print to stderr and exit nonzero.

## Authority rules (invariants)
- The device identity observed now selects the reference entry. Never use identity, baud or firmware remembered from another case or the training text.
- Do not edit `state.json`, the simulator, the reference, or case metadata. Mutate only with `set`.
- The fault register is the current state. Logs are append-only history and may keep the original incident after recovery.
- A probe may exit 0 while failing. Judge it from its JSON (`ok`, `status`), not the exit code.
- The baseline is written once, before the first mutation, and is never overwritten or reformatted.

## Steps
1. **Validate inputs** (table above). Any failure: BLOCKED.
2. **Capture the observations, no writes.** Run `read --field identity`, `read --field firmware`, `read --field config`, `read --field faults`, `logs`, `probe`. If any call fails or does not return valid JSON, the capture is incomplete: stop and report; do not save it as a baseline.
3. **Save the baseline** to `EVIDENCE_DIR/baseline.json` with keys `identity`, `firmware`, `config`, `faults`, `logs`, each holding the unmodified output of its primitive. Record the probe result in the session log. If a baseline file already exists, keep it untouched. If none exists and the device is already repaired, report an error: do not fabricate history.
4. **Select the reference from the observed identity.** Look up the observed device id in `REFERENCE`. Unknown id, or observed firmware different from the entry's firmware: BLOCKED; investigate and never guess or pick the nearest entry. Take `target_baud` only from the matched entry.
5. **Form the hypothesis (engineering judgement, not automatable).** Support for a configuration fault: an active fault in the register, a failed probe, and `config.baud != target_baud` with matching firmware. Absent a software error, this points to configuration rather than simulator repair. Stop without writing if the fault is not one you can tie to baud, or if the baud already equals `target_baud` while the link fails. That needs a different investigation.
6. **Healthy start.** Probe `ok:true` and empty fault register: nothing to repair, no write.
7. **Confirm the baseline is current.** Re-read `config`; it must still equal `baseline.config`. If it differs, the baseline is stale: BLOCKED, request a new capture. Do not write.
8. **Make one change:** `set --parameter baud --value <target_baud>` (accepted range 1200..115200 inclusive). Save the old/new JSON it returns. Make at most one change per run.
9. **Verify with fresh reads:** `read --field config`, `read --field faults`, `logs`, `probe`. Compare to baseline.
10. **Record** commands, outputs, rationale, and any denied or failed operation in `EVIDENCE_DIR/session.md`. Report failures and BLOCKED outcomes as they are. Do not soften them.

## Branches and recovery
| Situation | Behavior | Status |
|---|---|---|
| Missing/nonexistent state dir or input | BLOCKED, no writes | UNTESTED |
| A baseline read fails | Incomplete, no write | UNTESTED |
| Unknown identity or firmware mismatch | BLOCKED | UNTESTED |
| Config differs from baseline before writing | BLOCKED, new capture needed | UNTESTED |
| Device already healthy | No write | UNTESTED |
| `set` rejected (nonzero exit) | State is unchanged. Re-read config, check value and range, retry once at most | UNTESTED |
| Probe still fails after the write | Make no further change. Capture observations and re-examine the hypothesis and reference match. Report failure | UNTESTED |
| Wrong value written | Baseline keeps the original, logs keep every change. Correct with one documented `set` and explain | UNTESTED |
| Writing extra evidence under a subdirectory was denied by the environment | No device state changed. Save only the required files | Observed |

Only the single successful path (steps 1-5, 7-10) was observed.

## Completion criteria
- Baseline saved before the write, holding the original config, active fault, history and identity/firmware.
- Reference entry matched to the observed identity.
- Exactly one recorded `set`, whose log entry reads `baud changed: <baseline baud> -> <target_baud>`. Earlier log entries are preserved.
- Current `config.baud == target_baud`, faults are `[]`, probe is `ok:true`.
- Reasoning given for why an old log entry is history and not an active fault.
- Rerunning leaves the baseline and device state unchanged and makes no further write.
