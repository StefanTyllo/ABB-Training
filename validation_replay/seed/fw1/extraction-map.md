# Extraction map: FW1 restore link by one justified configuration change

Stage 3 design only. No reusable automation exists yet (stage 4). Source: `workflow.md` (one observed happy path; branches marked UNTESTED stay unproven until stage 4 checks).
Facts verified in this workspace: `fw1/expected.json` is keyed by case name (`demo`, `transfer`), and each entry holds `device_id`, `firmware`, `baud`. The device is currently repaired (baud 19200, probe ok), so `evidence/baseline.json` is the only record of the original state and must never be regenerated.

Dispositions: **D** = deterministic code, **M** = model judgment, **H** = human decision.

## Step review

| # | Step (category) | Purpose | Inputs | Operation | Expected output | Failure condition | Disposition |
|---|---|---|---|---|---|---|---|
| 1 | Validate inputs (validation) | Stop before any device command if the workspace is unusable | `--workspace`; `fw1/device.py`, `device/state.json`, `fw1/expected.json`, `case.json`, `evidence/` | Resolve paths from the workspace, check existence, check evidence dir creatable and writable. Never run `init` | Resolved path set | Any required item missing/unwritable gives BLOCKED, no writes. Missing `case.json` is only a note | D |
| 2 | Collect observations (collection) | Capture current state read-only | Tool path, state dir | Run `read --field identity/firmware/config/faults`, `logs`, `probe` with `--workdir`; keep stdout verbatim, return code, timestamp, argv | Six raw records | Nonzero exit, empty or non-JSON stdout: capture incomplete (never a baseline) | D |
| 3 | Parse (parsing) | Turn raw stdout into values without altering the raw text | Raw records | `json.loads` each; check shape (`device_id` str, `version` str, `baud` int, faults list, logs list, probe has `ok` bool and `status`) | Parsed values | Wrong shape or missing key gives INVALID/BLOCKED | D |
| 4 | Save baseline (reporting) | Preserve pre-change evidence once | Five parsed primitives plus raw stdout | If `baseline.json` exists, leave it untouched (byte-identical). Else write keys `identity, firmware, config, faults, logs` holding the unmodified primitive JSON. Probe goes to the session record, not the baseline | `evidence/baseline.json` | Incomplete capture: do not write. No baseline and device already healthy/repaired: ERROR (do not fabricate history) | D |
| 5 | Select reference (comparison) | Derive target from observed identity | Parsed identity, firmware, `expected.json` | Find the entry whose `device_id` equals the observed id (not the case key, not the nearest). Require firmware equality. Output `target_baud` | Matched entry, `target_baud` | Zero or several matches, firmware mismatch, `baud` not int in 1200..115200: BLOCKED | D |
| 6 | Form hypothesis (judgment) | Decide whether evidence supports a baud fault and not a software or other fault | Baseline, probe, config, reference | Check support: LINK_TIMEOUT active in faults, probe `ok:false`, `config.baud != target_baud`, firmware matches. Explain why the old log entry is history | Hypothesis with cited evidence | Unfamiliar fault, or baud already equals target while the link fails: stop, different investigation | Mechanical pre-conditions D (`hypothesis_preconditions`); interpretation and explanation M; unfamiliar fault H |
| 7 | Healthy check (validation) | Avoid needless write | Probe, faults | `ok:true` and `faults == []` means no repair | `NOOP` | None. A healthy device with no baseline is ERROR (step 4) | D |
| 8 | Stale-baseline check (comparison) | Ensure state hasn't drifted since baseline | `baseline.config`, fresh `config` | Re-read config, compare for equality before writing | Equal | Differs: BLOCKED, ask for a new capture, no write | D |
| 9 | Apply change (operation) | Make exactly one configuration write | Target baud, tool | `set --parameter baud --value <target>`; parse `{parameter, old, new}`; only if steps 1-8 pass and no change has been recorded this run | `{"parameter":"baud","old":9600,"new":<target>}` | Nonzero exit: state unchanged, report, one retry at most after re-reading. A second write attempt: refuse | D (gated); whether to proceed on an ambiguous case H |
| 10 | Verify recovery (calculation/comparison) | Show recovery from fresh evidence | Fresh config, faults, logs, probe; baseline | Re-capture. Check `config.baud == target`, `faults == []`, probe `ok:true`, logs start with baseline logs and end with exactly one `baud changed: <old> -> <target>` | Per-check PASS/FAIL list | Any check fails: report FAIL, no further write | D |
| 11 | Explain recovery (judgment) | Argue which observations demonstrate recovery and why historic log is not an active fault | Check list, before/after values | Write rationale | Prose | None automatable | M |
| 12 | Record (reporting) | Auditable session record | All records, statuses | Write `evidence/session.md` (commands, outputs, statuses, denied ops) and a machine summary. Never edit `baseline.json` | Report | Write failure: report error | D for the facts table; M for the narrative |
| 13 | Idempotent rerun | A repeat run changes nothing | Existing baseline, current state | If baseline exists and the device is healthy at target: verify only, no write, no baseline rewrite | Same exit and bytes | Any write or baseline change is a defect | D |
| 14 | Unknown/unexpected outcomes | Probe still failing after write; wrong value written | Verify result | Report visibly, no auto-retry or second write | FAIL report | Hiding or softening a failure | H (decides any corrective `set`) |

Status vocabulary for every function result: `OK`, `NOOP`, `BLOCKED` (precondition unmet, no write), `INVALID` (malformed observation), `FAIL` (change made but verification failed), `ERROR`. A caller must be able to see BLOCKED/FAIL; none is converted to success.

## Proposed functions and contracts

All return a `dict` with `status` plus the fields listed. None prints secrets or reads environment variables. Functions marked *read-only* never call `set`.

| Function | Input | Output | Errors / blocked |
|---|---|---|---|
| `resolve_paths(workspace: str) -> Paths` | Workspace path (absolute or relative; made absolute) | `tool, state_dir, state_file, reference, case_file, evidence_dir, baseline, session_md` | `BLOCKED` naming the missing path; state_dir without `state.json` is BLOCKED; no `init` |
| `run_primitive(paths, args: list[str]) -> Record` *(read-only unless args start with `set`)* | Paths; primitive args after `--workdir` | `{argv, returncode, stdout_raw, stderr, timestamp_utc, parsed}`; `parsed` is `json.loads(stdout)` | Nonzero return, empty stdout, bad JSON: `INVALID`, raw kept. Timeout limit applied |
| `capture_state(paths) -> Capture` *(read-only)* | Paths | `{complete: bool, records: {identity, firmware, config, faults, logs, probe}, timestamp_utc, input_identity}` | `complete=False` if any of six fails; the failing record is listed |
| `validate_capture(capture) -> Result` | Capture | `{status, problems: [str]}` shape check from step 3 | `INVALID` with problems |
| `write_baseline(paths, capture) -> Result` | Complete capture | `{status: "WRITTEN"/"EXISTS", path, sha256}`; five keys with raw primitive JSON only | Incomplete capture: `BLOCKED`. Existing file untouched (open with exclusive create `x`; never rewrite). Repaired device without baseline: `ERROR` |
| `load_baseline(paths) -> Result` | Paths | Baseline dict with five keys | Missing/invalid keys: `INVALID`; missing: `ERROR` |
| `select_reference(reference_path, identity, firmware) -> Result` | `expected.json`; observed `{device_id}` and `{version}` | `{status, entry_key, target_baud, firmware}` | No/duplicate id match, firmware mismatch, bad baud: `BLOCKED`. An unknown id must never fall back to `case.json` or default |
| `hypothesis_preconditions(baseline, probe, target_baud) -> Result` | Baseline faults/config, probe record, target | `{status: "SUPPORTED"/"NOT_SUPPORTED"/"NOOP", checks: {...}}`. Does not interpret | `NOT_SUPPORTED` when baud equals target but link fails, or fault is not `LINK_TIMEOUT`: halt for human/model review |
| `check_baseline_current(baseline, current_config) -> Result` | Baseline dict, fresh `config` | `{status: "OK"/"BLOCKED", baseline_baud, current_baud}` | `BLOCKED: stale baseline, new capture needed` |
| `apply_baud(paths, target_baud, old_baud, already_written: bool) -> Result` | Gate inputs | `{status, command, old, new}` parsed from `set` | Refuse unless the gates pass (`BLOCKED`); value outside 1200..115200 is refused before running; `set` nonzero: `ERROR`, state unchanged; second write refused |
| `compare_before_after(baseline, after, target_baud, probe) -> Result` | Baseline, after-captured config/faults/logs, probe | `{status, checks: [{name, expected, actual, pass}]}` for baud, empty faults, probe ok, log prefix preserved, exactly one `baud changed: <old> -> <target>` entry | `FAIL` listing failing checks |
| `write_session_report(paths, run_record) -> Result` | Ordered records, statuses, checks | `evidence/session.md` facts section (idempotent append of a labelled run, never touching baseline) | Write error: `ERROR` |
| `run(workspace) -> int` | Workspace | Exit 0 only on verified OK/idempotent NOOP; 1 on BLOCKED/INVALID/FAIL/ERROR | Orchestrates the above in order; reruns write nothing |

## Boundary notes
- Input identity, firmware, and baud come from current evidence plus `expected.json`, never from the demo (`SIM-017`/`19200`) or the transfer text. Tests must use values that differ from the demo.
- Stays with reasoning (M/H): choosing the hypothesis, handling unfamiliar faults, explaining why the historical log differs from an active fault, deciding any corrective write after a wrong or failed change.
- Stage 4 checks to implement against disposable prepared cases: valid capture; nonexistent state dir gives BLOCKED; unknown identity cannot select a reference; no baseline rejects the experiment; stale baseline rejected; correct change restores the probe; rerun is byte-identical.
- Known gaps (UNTESTED in `workflow.md`): every branch other than the happy path, and the logs-prefix check, remain unproven until stage 4.
