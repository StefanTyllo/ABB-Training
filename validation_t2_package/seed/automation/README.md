# T2 automation (stage 4)

Standard library only; run from the workspace root (`runs/t2/demo`) with the training venv (Python 3.12, Selenium, pytest, Chrome).

| File | Role |
| --- | --- |
| `automation/guardrails.py` | Common entry point. Runs `python -m pytest tests -q -ra --junitxml=JUNIT` in the workspace, inheriting `BASE_URL`. Keeps pytest's exit code; prints PASS / ASSERTION FAILURE / INFRASTRUCTURE FAILURE. |
| `automation/evaluate_variants.py` | Serial runner: starts its own server per variant (correct, no-persist, bad-boundary) on a free loopback port with clean owned state, runs guardrails, parses JUnit, stops the child in `finally`. |
| `automation/evaluation_lib.py` | Helpers: `validate_inputs`, `collect_artifact_digests`, `find_free_port`, `start_server`, `wait_ready`, `stop_server`, `parse_junit`, `classify_failures`, `check_case_coverage`, `compare_runs`, `summarize_detection`, `write_report`. |
| `automation/tests/` | Checks and altered fixtures (JUnit variants, throwaway workspaces). |

## Commands
```bash
# 1. Checks of the automation itself (defect gate, valid input, failure branches)
python -m pytest automation/tests -q

# 2. Suite against one externally owned server (the caller owns BASE_URL)
BASE_URL=http://127.0.0.1:8765 python automation/guardrails.py --workspace . --junit evidence/guardrails/junit.xml

# 3. Full three-variant evaluation (stop any server you do not need first; it uses its own ports)
python automation/evaluate_variants.py --workspace .
```
Options: `guardrails.py --timeout S` (default 600); `evaluate_variants.py --evidence-dir DIR --ready-timeout S --pytest-timeout S`.

## Exit codes
- `guardrails.py`: pytest's code (0 pass, 1 test failures, 2-5 pytest error); 124 timeout; 125 workspace unusable / pytest cannot launch.
- `evaluate_variants.py`: 0 `passed` (correct rc 0; no-persist and bad-boundary rc 1 with relevant assertion failures, no skips/errors); 1 `failed`; 2 `blocked` (bad inputs, occupied port, startup failure, timeout, missing JUnit).

## Evidence written
`evidence/variant-evaluation.json` (fresh every run: `status`, `variants` with `pytest_returncode`, counts, JUnit/log/state paths, readiness, failures with class `assertion`/`incidental`, `verdicts`, `review_required`, file digests, `not_run`) and `evidence/variants/<variant>/{junit.xml,pytest.log,server.log,state.json}`. Stage 1-3 evidence is never touched.

## Limits
A verdict `detected` is provisional: `review_required` lists each detecting assertion (requirement ID, observed, expected, phase) for human review. Expected/observed extraction and the before/after-reload phase come from pytest message text and test names, so they may be null or heuristic. Whether a defect truly violates a requirement stays a human decision.
