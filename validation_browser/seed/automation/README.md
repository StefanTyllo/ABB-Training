# automation/ — T1 execution and evidence helpers

Run everything from the workspace root (`runs/t1/demo`) with the app already running at `BASE_URL` (default `http://127.0.0.1:8765`). This code does not start or stop the server and never edits tests, expected values or app files.

| File | Purpose |
|---|---|
| `helpers.py` | `load_case`, `check_app_ready`, `start_browser`, `parse_junit`, `classify_outcome`, `required_names_present`, `scan_forbidden`, `compare_runs`, `snapshot_visibility`, `capture_failure_evidence`, `hash_files`/`verify_protected`, `write_summary` |
| `guardrails.py` | Runs the suite and classifies the result |
| `tests/test_automation.py`, `tests/fixtures/` | Checks of the helpers using altered fixtures (skipped test, assertion failure, startup error, sleep, other case values) |

## Commands
```bash
# Suite run with machine-readable evidence (JUnit + <junit stem>-summary.json)
python automation/guardrails.py --workspace . --junit evidence/stage4-run1-junit.xml

# Optional: --timeout SECONDS (default 600), --summary PATH

# Wrong URL must be BLOCKED (nonzero exit, status BLOCKED, errors not "failures")
BASE_URL=http://127.0.0.1:9 python automation/guardrails.py --workspace . --junit evidence/stage4-wrongurl-junit.xml

# Checks of the automation itself (defect, valid input, failure branch; needs the app)
python -m pytest automation/tests -q -rA
```

## Exit codes of guardrails.py
pytest's status is preserved, except: `124` timeout (BLOCKED), `125` pytest could not be launched (BLOCKED), `4` pytest exited 0 but the run is INCOMPLETE (skips, nothing collected, or a required test family missing).

## Statuses
- `PASSED`: all executed, none skipped, required families (`connection_visibility`, `auth_visibility`, `save_reload`) ran.
- `FAILED`: assertion failure: read the failing case and screenshots.
- `BLOCKED`: infrastructure (unreachable app, browser/driver start, timeout, setup errors). Not a pass, not a product failure.
- `INCOMPLETE`: green but skips/missing coverage. A skipped required test is never coverage.

## Evidence written
`evidence/stage4-run{1,2}-junit.xml|-summary.json|.log`, `stage4-wrongurl-*`, `stage4-automation-junit.xml|.log`. Stage 1 files (`session.md`, `stage1-*`) are not modified. `capture_failure_evidence(driver, dir, label)` writes a screenshot plus a text file with URL, title, `aria-busy`, per-field visibility and the error.

## Limits
Classifying infrastructure errors uses text patterns in the JUnit messages; unknown cases resolve to BLOCKED. VAL-01 and invalid-save behavior are not covered by the T1 demo suite. Headed mode and variant servers are not exercised here.
