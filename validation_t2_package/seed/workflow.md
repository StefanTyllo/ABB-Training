# Workflow: evaluate whether a UI test suite detects defects

Reusable for any web app with an independent requirements document, a Page Object (POM) suite and known or unknown defective variants. Angle-bracket names are inputs, not literals.

## Inputs (validate before any action)
| Input | Validation | If missing or invalid |
| --- | --- | --- |
| `WORKSPACE` | Existing directory; all work stays inside it | Stop, blocked |
| `REQUIREMENTS_FILE` | Readable; is the only oracle for expected behavior | Stop, blocked. Never infer expectations from app source or output |
| `CASE_FILE` | Readable valid JSON; supplies case values | Stop, blocked. Never invent case values |
| `REQUIRED_CASES` | List of valid, invalid and boundary values plus persistence and invalid-save-preserves-baseline cases, from the task card and requirements | Ask the task owner. If unanswerable, derive only from requirements and record that as an assumption |
| `CORRECT_BASE_URL` | Reachable loopback URL of the correct app; owner known | Start own correct instance if a server command is given. Else blocked |
| `SERVER_CMD`, `VARIANT_LABELS`, `STATE_PATH_ROOT`, `PORT_POLICY` | Command template accepts variant, port and state path. Ports are free loopback ports. State files are new and owned | Without a server command, evaluate only against supplied URLs and record that variants were not controlled |
| `EVIDENCE_DIR` | Writable | Create it. If that fails, blocked |
| `IMMUTABLE_FILES` | Source app, base page, fixtures, case data, requirements, test config | Never edit them. Edit only the permitted POM and test files |

The suite must read the server address from the `BASE_URL` environment variable so one suite can target any server.

## Invariants (never relax)
1. Requirements are the oracle. Do not read the fault-switch implementation or copy actual output into expected values.
2. The suite must pass the correct app first. A failing correct run gives no detection credit. The suite or environment is wrong, or the result is blocked.
3. Detection counts only when a variant fails on an assertion that ties to a requirement. Timeouts, hidden-element lookups, crashes, startup errors and driver errors are not detection.
4. The same cases and expectations run on every variant. No skips, xfail, variant-based branching, fixed sleeps, fake DOM or HTTP-based UI assertions. Waits are explicit and wait for observable readiness.
5. Stop only child servers I started. Never stop a server I do not own, and never kill a process just because it holds a port. Choose another free port.
6. Every run gets its own state file or a verified clean reset.
7. Failures, blocked results and expected engineering failures remain visible in the evidence. Do not swallow or rewrite them, and do not claim a result that was not executed.
8. Do not print environment variables or credentials. Case passwords are synthetic test values only.

## Steps
1. **Validate inputs** per the table. Record each missing item and the chosen behavior.
2. **Read** the task card, any CI/contract file, requirements, case data and existing POM and tests. Do not read instructor, grader or other-workspace material.
3. **Judge the baseline test.** State what a pass proves and what it does not prove (persistence, rejection, preserved state, boundaries). Record this as reasoning.
4. **Map each requirement to observable browser behavior** and to the explicit wait that makes it reliable. Do this for persistence, validation, async settling and any other requirement in scope.
5. **Preflight.** Run the browser preflight, then the baseline suite on the correct app. Record exit code and passed, failed and skipped counts.
6. **Defect run.** Start the defective variant on its own free port with fresh state. Poll readiness with a timeout. Run the unchanged baseline against it with `BASE_URL`. Record the outcome. A pass shows the coverage gap. Record the reason it passes.
7. **Strengthen** the suite with the existing POM, adding POM methods only if needed. Cover every `REQUIRED_CASES` item:
   - each valid boundary accepted, and shown after reload where persistence applies
   - each invalid or non-integer boundary rejected
   - changed valid values persist across an actual browser reload (use at least two distinct configurations)
   - an invalid save after a valid saved baseline leaves the baseline intact after reload
   - Before reading a dependent field after reload, assert the precondition state (for example active mode) so a mismatch is an assertion failure, not a timeout.
8. **Evaluate every variant**, serially: correct, then each defect, each with its own port, state and log, and a distinct JUnit file or log. Record exit code, counts, collected count and the exact failing assertions. The correct app must pass with zero skips.
9. **Review each detecting failure.** Confirm it is an assertion tied to a named requirement ID, and give the expected value, the actual value and the phase (before or after reload). If it is a timeout or setup error, add a direct assertion and re-run. If a variant passes the strengthened suite, the gap is still open. Add the missing assertion.
10. **Cleanup.** Stop only owned children, in a finally-style step. Confirm any server I did not own still answers.
11. **Write evidence and result** (below). State the final status honestly: passed, failed or blocked.

## Automation helpers (code mode)
Steps 1, 5, 8, 10 and 11 are deterministic and have helpers in `automation/` (details and exit codes: `automation/README.md`). Judgment steps 3, 4, 7, 9 and the final accept stay manual.
| Step | Command | How to read the result |
| --- | --- | --- |
| Self-check | `python -m pytest automation/tests -q` | All pass: the gate rejects timeouts, skips and a failing correct run, and accepts a relevant assertion failure. |
| 5 (one server) | `BASE_URL=<url> python automation/guardrails.py --workspace . --junit evidence/guardrails/junit.xml` | Exit equals pytest's. `PASS`, `ASSERTION FAILURE` (a test result) or `INFRASTRUCTURE FAILURE` (blocked, not a result). |
| 1, 8, 10, 11 | `python automation/evaluate_variants.py --workspace .` | Exit 0 / 1 / 2 = passed / failed / blocked. Read `evidence/variant-evaluation.json`: `variants.*.pytest_returncode`, `counts`, `failures[].class`, `verdicts`. |
After the run, review every entry in `review_required` (requirement ID, observed, expected, phase) before accepting `detected`. Treat `failed` and `blocked` as real outcomes; do not rerun to hide them.

## Branches
| Situation | Action |
| --- | --- |
| Correct app fails | No detection credit. Fix the test. If cause is infrastructure, report blocked |
| Defect fails by timeout or hidden element | Not detection. Do step 9 |
| Defect passes strengthened suite | Semantic gap. Add assertion, re-run all variants |
| Port occupied, server not ready, Chrome or driver startup failure | Blocked infrastructure, not a test result. Use another free port. Do not kill the occupant |
| Server not mine and the task says to stop it | Do not stop it. Use my own server on another port and note the deviation |
| Tool call refused by the harness | Use an equivalent tool (for example Python `urllib` for `curl`, async shell mode for `&`) and note it |
| Stale state | New state file for each run |
| Some variant tests pass on a defect | Acceptable only when those cases do not depend on the defective behavior. Say which, and why |
| Variant label undisclosed | Evaluate from test evidence only. Do not look up the label |

## Evidence
- Commands, ports, state paths, exit statuses, pytest summaries and counts per variant.
- Failing assertion messages and the requirement mapping for each. Test and POM diffs. Owned server logs.
- Deviations from the task card and their reason.
- A list of what was not run.

## Completion criteria
- Correct app passes all required cases, executed, with no skips or xfail.
- Each required variant fails on a relevant requirement assertion and not on incidental errors.
- Required cases are present and identical on every variant.
- Owned servers are stopped, others untouched.
- Human judgment remains for whether a defect is a true requirement violation and whether the detecting assertion is the right one.

## Untested branches
These are not exercised by the observed run. Treat them as unverified guidance.
- Variants other than a persistence defect. A boundary defect (for example a valid endpoint wrongly rejected) was not run, so detection of a boundary defect is unproven. The `REQUIRED_CASES` boundaries are the intended coverage.
- Running a Serial-mode or other non-default connection path for persistence.
- Behavior with unknown variant labels, parallel runs and non-loopback servers.
- The ASYNC timing window beyond what explicit waits cover.
- Automated orchestration of the serial evaluation (out of scope here).
