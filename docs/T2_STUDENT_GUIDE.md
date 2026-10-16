# T2: Prove that a passing test suite can actually detect defects

You will expose a misleading green smoke test, strengthen its assertions and build a repeatable correct-versus-defective application evaluation.

## Before you begin

Follow the [virtual environment setup](../README.md) and complete the [handbook](ABB_Workflow_Training.pdf) readiness checks. Activate `.venv` before running commands. Record the same selected agent/model throughout.

Host commands run in the unpacked package folder. Commands marked Inside the workspace run in this exercise's prepared workspace. Preparation is for fresh work; resume by re-entering the existing workspace.

Extend `pages/settings_page.py`, `tests/test_settings.py` and your learning artifacts. Keep the app, BasePage, fixtures, case and requirements unchanged. Read requirements to establish expected results; do not inspect the server’s fault-switch implementation for answers.

Tell the agent:

> Work with me one operation at a time. Explain its purpose and expected result, then wait for my explanation before continuing. Record actual commands, observations and decisions in evidence/session.md. Do not create reusable automation until Stage 4.

Expected results below describe the supplied examples. Save actual output; if it differs, explain or resolve the difference before proceeding.

## 1. Prepare and run the weak starting suite

**Do this:** Use Terminal A in the workspace as shown below:

**Host terminal** — in the unpacked package folder; fresh T2 demonstration:

```text
abb doctor --offline
abb prepare t2 demo
abb shell --workspace work/t2-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/t2-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

**Inside the workspace — Terminal A**: start only this workspace's server and leave it running.

```bash
python server.py --variant correct --port 8765 --state state.json
```

**Host terminal — Terminal B**, opened separately in the same package folder:

```text
abb shell --workspace work/t2-demo
```

**Inside the workspace — Terminal B**:

```bash
pwd
# Expected: work/t2-demo
```

Run the bootstrap/tests from Terminal B. Both terminals enter the same `training` service and workspace. Stop your Terminal A server with Ctrl-C before changing workspaces; if port 8765 is occupied, identify its owning terminal and stop that server. Keep the evidence and do not stop another participant's process.


In terminal B, repeat the host-side entry command into this same service and workspace:

**Inside the workspace**:

```bash
python -m pytest browser_preflight.py -q
python -m pytest tests -q
```

Read `REQUIREMENTS.md` and the existing smoke test.

**You should get:** Passing browser preflight and one passing smoke test. Its assertion checks only the “Saved” message, not what happens after reload.

**Why:** A green test result proves only what its assertions actually check. A requirement marker is not proof of coverage.

## 2. Challenge the unchanged test with a defect

**Do this:** Stop your server in terminal A with Ctrl-C. Only after it stops, run:

**Inside the workspace**:

```bash
python -c "from pathlib import Path; Path('state.json').unlink(missing_ok=True)"
python server.py --variant no-persist --port 8765 --state state.json
```

In terminal B, rerun the unchanged test:

**Inside the workspace**:

```bash
python -m pytest tests -q
```

Also demonstrate saving valid case values and reloading the browser.

**You should get:** The weak test still passes, while saved values do not survive reload in the defective app.

**Why:** The test misses a real SAVE-01 violation because it never checks persistence. The application must fail for the expected reason, not because the browser cannot start.

## 3. Add assertions that test the actual requirements

**Do this:** Ask the agent to extend the existing Selenium suite and Page Object using observable waits. Include:

- Two distinct valid TCP configurations that retain exact values after actual reload.
- Accepted integer ports `1` and `65535`.
- Rejected `0`, `65536` and non-integer text.
- A valid saved baseline, then an invalid save, followed by reload proving the baseline was not overwritten.

Use the same assertions on every variant; do not branch expected results on the variant name.

**You should get:** Substantive persistence, boundary and invalid-save tests; at least eight executed cases under the CI contract, with names identifying `save_reload`, `port_boundary` and `invalid_save`. No skipped required cases.

**Why:** Requirements determine expectations. Changing expectations to match each implementation would hide the defects.

## 4. Verify detection and correct behavior separately

**Do this:** Run the strengthened suite against the running no-persist app:

**Inside the workspace**:

```bash
python -m pytest tests -q -ra --junitxml=evidence/no-persist.xml
```

Expect relevant persistence assertions to fail. Stop your server, reset only its state as in step 2, then launch:

**Inside the workspace**:

```bash
python server.py --variant correct --port 8765 --state state.json
```

Run the identical strengthened suite:

**Inside the workspace**:

```bash
python -m pytest tests -q -ra --junitxml=evidence/correct.xml
```

**You should get:** No-persist fails because saved values are not restored; the correct app passes all required cases. Preserve both actual results and identify the assertion establishing detection.

**Why:** A suite that fails everything is not an effective detector. Browser crashes, startup errors and unrelated timeouts do not count as detecting the intended defect.

## 5. Document the demonstrated process — finish Stage 1

**Do this:** Ask the agent to reconstruct our actual work as `workflow.md`: goal, inputs, ordered steps, reasons, evidence, decisions, recovery and completion criteria. Review it against `evidence/session.md`.

**You should get:** A procedure supported by our actual observations. Resolve a blocked demonstration with the facilitator before treating it as a successful procedure.

**Why:** The next stages must reuse a demonstrated process, including what went wrong.

## 6. Generalize the instructions — Stage 2

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Replace example-specific details with inputs: test workspace, server command/variant, port, owned state path, current case and evidence destination. Define input sources, validation and missing-input behavior. Keep genuine engineering rules. Save `workflow.md` and an identical `workflow-md-only.md` checkpoint.

**You should get:** Instructions another engineer can follow without the original conversation.

**Why:** A workflow must work with new values rather than repeat the demonstration’s answer.

## 7. Decide what becomes code — Stage 3

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Write `extraction-map.md`: each operation’s purpose, inputs, output, failure condition and owner (code, model or human). Consider automating: start owned servers serially, poll readiness, run the unchanged suite, retain stdout/JUnit, compare expected outcomes and stop only owned child processes. Do not implement yet.

**You should get:** A table of proposed functions with clear contracts and explicit human decisions.

**Why:** Specified, repeatable operations suit code; missing authority and engineering judgment still need people.

## 8. Implement and test — Stage 4

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Implement the agreed helpers under `automation/`. Use readable functions, engineering explanations, actual-result logs and meaningful failure statuses. Test: correct app passing; no-persist failing a save_reload assertion; bad-boundary failing a port_boundary assertion; required skips rejected; occupied port/failed startup reported as infrastructure failure; genuine test exits preserved. Use disposable fixtures under `automation/tests/`. Update `workflow.md` and document exact commands in `automation/README.md`. Keep the Markdown checkpoint and original evidence unchanged.

**You should get:** Working helpers with real passing/failing checks, plus instructions that actually call them. Document guardrails and serial variant-runner commands in the README. In CI these are `automation/guardrails.py --workspace PATH --junit PATH` and `automation/evaluate_variants.py --workspace PATH`. Guardrails inherits caller BASE_URL and preserves pytest status. The variant runner owns separate free ports/state, cleans children in finally, records actual JUnit/log paths and exits successfully only when all expected outcomes occur. A caller may already have opened its console log; use distinct fresh paths for internal logs.

**Why:** Tests show what the code handles; its completion message alone proves nothing.

## 9. Replay twice on fresh inputs

**Do this:** After Stage 4, use a host terminal in the package folder:

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare t2 transfer --name t2-transfer-md
abb shell --workspace work/t2-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/t2-transfer-md
```

**Inside the workspace — Terminal A**:

```bash
python server.py --variant correct --port 8765 --state state.json
```

**Host terminal — Terminal B**:

```text
abb shell --workspace work/t2-transfer-md
```

**Inside the workspace — Terminal B**:

```bash
pwd
# Expected: work/t2-transfer-md
python -m pytest browser_preflight.py -q
```

Run this transfer's tests in Terminal B. Stop this Terminal A server before the next workspace; state from the demonstration is not transferred.

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare t2 transfer --name t2-transfer-code
abb shell --workspace work/t2-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/t2-transfer-code
```

**Inside the workspace — Terminal A**:

```bash
python server.py --variant correct --port 8765 --state state.json
```

**Host terminal — Terminal B**:

```text
abb shell --workspace work/t2-transfer-code
```

**Inside the workspace — Terminal B**:

```bash
pwd
# Expected: work/t2-transfer-code
python -m pytest browser_preflight.py -q
```

Run this transfer's tests in Terminal B. Stop this Terminal A server before the next workspace; state from the demonstration is not transferred.

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.


For **instructions only**, copy `workflow-md-only.md` as `workflow.md`. For **instructions plus code**, copy updated `workflow.md`, reusable `automation/` and documented dependencies. Copy no finished task implementations, demo outputs, reports, evidence or browser session state.

Start a new conversation in each workspace with the same agent/model. Ask it to read `workflow.md`, execute on current inputs and record evidence. Code mode must actually invoke the helpers. Run workspaces one at a time. Current transfer includes valid port `65535`. Evaluate the same new suite against correct, no-persist and bad-boundary, using clean owned state each time. Bad-boundary must fail for rejecting the valid endpoint, while correct passes. Transfer general runners, not finished demo tests or repaired Page Objects.

**You should get:** Two independent results checked against the same criteria. Record manual fallback and any scripts independently created in instructions-only mode.

**Why:** New inputs expose hard-coded values. The pair shows what the reusable code contributed in these cases.

## 10. Check and submit

**Do this:** Review actual evidence with the facilitator. Inspect real browser/JUnit results and the precise assertion detecting each defect. For code mode, review the server-owning runner’s actual correct/no-persist/bad-boundary results and cleanup. A failed process alone is not proof of detection.

Submit both workflow versions, `extraction-map.md`, `automation/` with checks/README, and `evidence/`. Compare correctness, time, interventions and failures. Explain what moved into code and what still requires judgment.

**You should get:** An evidence-backed assessment with untested paths identified. A justified engineering failure or blocked input can be the correct training result.

**Why:** The facilitator assesses both your work and your explanation. One pair of replays is not a statistical benchmark.


Reference: [UI requirements](../training_kit/test_team/REQUIREMENTS.md), [test walkthrough](TEST_TEAM_WALKTHROUGH.md) and [CI execution contract](../training_ci/test_contract.md).
