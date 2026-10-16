# T1: Explore a dynamic form and create meaningful browser tests

You will use Playwright MCP to observe a live form, extend existing Selenium Page Objects and pytest tests, then extract reusable session and execution helpers.

## Before you begin

Follow the [virtual environment setup](../README.md) and complete the [handbook](ABB_Workflow_Training.pdf) readiness checks. Activate `.venv` before running commands. Record the same selected agent/model throughout.

Host commands run in the unpacked package folder. Commands marked Inside the workspace run in this exercise's prepared workspace. Preparation is for fresh work; resume by re-entering the existing workspace.

Extend `pages/settings_page.py`, `tests/test_settings.py` and your learning artifacts; add bootstrap/non-secret configuration as needed. Preserve server, BasePage, fixtures, case and requirements. Use the agent chosen by the facilitator consistently. MCP is for exploration; Selenium remains the test framework.

Tell the agent:

> Work with me one operation at a time. Explain its purpose and expected result, then wait for my explanation before continuing. Record actual commands, observations and decisions in evidence/session.md. Do not create reusable automation until Stage 4.

Expected results below describe the supplied examples. Save actual output; if it differs, explain or resolve the difference before proceeding.

## 1. Prepare the app and verify the real browser

**Do this:** Use Terminal A in the container as shown below:

**Host terminal** — in the unpacked package folder; fresh T1 demonstration:

```text
abb doctor --offline
abb prepare t1 demo
abb shell --workspace work/t1-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/t1-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

**Inside the workspace — Terminal A**: start only this workspace's server and leave it running.

```bash
python server.py --variant correct --port 8765 --state state.json
```

**Host terminal — Terminal B**, opened separately in the same package folder:

```text
abb shell --workspace work/t1-demo
```

**Inside the workspace — Terminal B**:

```bash
pwd
# Expected: work/t1-demo
```

Run the bootstrap/tests from Terminal B. Both terminals enter the same `training` service and workspace. Stop your Terminal A server with Ctrl-C before changing workspaces; if port 8765 is occupied, identify its owning terminal and stop that server. Keep the evidence and do not stop another participant's process.


Leave it running. In terminal B, repeat the exact host-side Terminal B entry above into the same service and workspace:

**Inside the workspace**:

```bash
python -m pytest browser_preflight.py -q
python -m pytest -q
```

Read `REQUIREMENTS.md`, `case.json`, existing Page Objects and tests.

**You should get:** Passing browser preflight; the starter suite has one passing smoke test and one skipped placeholder. The form starts at Serial / COM1 / None. Browser startup failure is blocked setup; the skip is unfinished coverage.

**Why:** The browser must work before you interpret UI failures. The requirements define expected behavior independently of what you happen to observe.

## 2. Prepare the session using the reviewed bootstrap

**Do this:** Before creating local secrets/state, add `.env`, `.env.*` and `.auth/` to the workspace’s `.gitignore`, with `!.env.example` as the exception. Check:

**Inside the workspace**:

```bash
git check-ignore .env .auth/state.json
git ls-files -- .env .auth
```

The image supplies `tools/session_bootstrap.mjs`; this infrastructure creates no learner `automation/` solution.

**Inside the workspace — Terminal B**:

```bash
node tools/session_bootstrap.mjs --mode no-login --url http://127.0.0.1:8765 --state .auth/state.json --report evidence/bootstrap.json
```

It validates the fixture, saves workspace-local state and closes its browser. Login mode without a reviewed adapter returns BLOCKED.

For an authorized external login target, the operator instead supplies local `.env` values `TEST_BASE_URL`, `TEST_USERNAME`, `TEST_PASSWORD`, reviewed selectors and an authenticated readiness signal. Keep credentials/state out of prompts, logs, screenshots and submissions; share only an empty `.env.example`.

**You should get:** Ignore check identifies both paths; tracked-file check has no entries. The local bootstrap opens the form and writes session state. Missing script/dependencies are a setup issue to resolve with the facilitator. The local app has no login, so this does not prove authentication.

**Why:** A predictable session setup is reusable code. Successful state-file creation alone does not establish that the intended authenticated page is accessible.

## 3. Verify session handover to MCP

**Do this:** After the state exists, start your selected agent through `abb agent` in this workspace. The launcher creates workspace-specific stdio MCP configuration using the baked browser, sandbox and `.auth/state.json`. It removes provider tokens from tool environments where supported. Ask its actual MCP tools to navigate to the target and inspect the form. Save sanitized tool observations.

**You should get:** MCP reaches the intended form using the exported state. A fresh browser context without the state argument does not prove handover. Record whether the target was no-login or authenticated; unresolved external login paths remain unverified/blocked.

**Why:** Saved storage state initializes a new browser context; it does not transfer an open tab. SessionStorage-dependent targets may need a separately reviewed attached-browser approach.

## 4. Explore both directions of each transition

**Do this:** Using MCP, switch Serial → TCP → Serial and None → Password → None. Wait for observable readiness each time. Inspect snapshots and DOM attributes, and record action, expected behavior, actual fields, readiness signal and a stable proposed Selenium locator.

**You should get:** TCP shows Host/Port and hides Device; Serial reverses this. Password shows and requires a password; None hides it. Transitions settle asynchronously. Verify locator uniqueness in relevant states.

**Why:** Looking at the initial page misses dynamic behavior. MCP snapshot references are temporary exploration aids, not permanent Selenium locators.

## 5. Extend the existing Page Object and assertions

**Do this:** Ask the agent to extend existing interactions with `choose_auth(value)` and `reload()`, keeping observable waits in Page Objects and requirement assertions in tests. Test both connection modes and both authentication states. Use `case.json` values, save, wait, reload and assert exact active values. Reject an empty password and invalid port; after each rejected save reload and prove the last valid configuration survived. Use only invented form passwords.

**You should get:** Assertions cover UI-01, UI-02, SAVE-01 and ASYNC-01, including both directions and actual persistence. Include at least four executed cases, with names identifying `connection_visibility`, `auth_visibility` and `save_reload`; parameterize save/reload for Serial and TCP. No fixed sleeps or placeholder skips remain. The form’s None/Password selector is device configuration, not application login.

**Why:** Clicking through a form proves less than repeatable assertions. A “Saved” message alone does not prove that data survives reload.

## 6. Run and inspect the completed suite

**Do this:** Run the actual framework and save its output:

**Inside the workspace**:

```bash
python -m pytest tests -q -ra --junitxml=evidence/t1-demo.xml
```

Retain sanitized failure evidence, including an intentional missing-element screenshot/error context from a disposable diagnostic check. Keep that intentional diagnostic separate from the passing acceptance suite.

**You should get:** Real Chrome executes substantive tests with no required skips or errors. Both Serial and TCP save/reload cases pass. Failure evidence explains the failed element/action without exposing secrets.

**Why:** MCP exploration and Selenium test execution are separate checks. Useful failure evidence makes later reuse easier to diagnose.

## 7. Document the demonstrated process — finish Stage 1

**Do this:** Ask the agent to reconstruct our actual work as `workflow.md`: goal, inputs, ordered steps, reasons, evidence, decisions, recovery and completion criteria. Review it against `evidence/session.md`.

**You should get:** A procedure supported by our actual observations. Resolve a blocked demonstration with the facilitator before treating it as a successful procedure.

**Why:** The next stages must reuse a demonstrated process, including what went wrong.

## 8. Generalize the instructions — Stage 2

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Replace example-specific details with inputs: target URL, case path, login/no-login mode, approved selectors/readiness signal and evidence destination; supply secrets locally rather than embedding them. Define input sources, validation and missing-input behavior. Keep genuine engineering rules. Save `workflow.md` and an identical `workflow-md-only.md` checkpoint.

**You should get:** Instructions another engineer can follow without the original conversation.

**Why:** A workflow must work with new values rather than repeat the demonstration’s answer.

## 9. Decide what becomes code — Stage 3

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Write `extraction-map.md`: each operation’s purpose, inputs, output, failure condition and owner (code, model or human). Consider automating: validate bootstrap inputs, establish and export a session, validate handover prerequisites, run existing pytest and collect sanitized execution/failure evidence. Do not implement yet.

**You should get:** A table of proposed functions with clear contracts and explicit human decisions.

**Why:** Specified, repeatable operations suit code; missing authority and engineering judgment still need people.

## 10. Implement and test — Stage 4

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Implement the agreed helpers under `automation/`. Use readable functions, engineering explanations, actual-result logs and meaningful failure statuses. Test: no-login bootstrap and actual MCP handover; wrong/unreachable URL; missing credentials in login mode; rejected/expired authentication on an authorized target; meaningful element-failure evidence; real pytest results with no required skips. Use disposable fixtures under `automation/tests/`. Update `workflow.md` and document exact commands in `automation/README.md`. Keep the Markdown checkpoint and original evidence unchanged.

**You should get:** Working helpers with real passing/failing checks, plus instructions that actually call them. Keep stdout capture under the caller’s control; put helper-internal logs in fresh, separately named files. Never overwrite the original observations.

**Why:** Tests show what the code handles; its completion message alone proves nothing.

## 11. Replay twice on fresh inputs

**Do this:** After Stage 4, use a host terminal in the package folder:

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare t1 transfer --name t1-transfer-md
abb shell --workspace work/t1-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/t1-transfer-md
```

**Inside the workspace — Terminal A**:

```bash
python server.py --variant correct --port 8765 --state state.json
```

**Host terminal — Terminal B**:

```text
abb shell --workspace work/t1-transfer-md
```

**Inside the workspace — Terminal B**:

```bash
pwd
# Expected: work/t1-transfer-md
python -m pytest browser_preflight.py -q
```

Run this transfer's tests in Terminal B. Stop this Terminal A server before the next workspace; state from the demonstration is not transferred.

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare t1 transfer --name t1-transfer-code
abb shell --workspace work/t1-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/t1-transfer-code
```

**Inside the workspace — Terminal A**:

```bash
python server.py --variant correct --port 8765 --state state.json
```

**Host terminal — Terminal B**:

```text
abb shell --workspace work/t1-transfer-code
```

**Inside the workspace — Terminal B**:

```bash
pwd
# Expected: work/t1-transfer-code
python -m pytest browser_preflight.py -q
```

Run this transfer's tests in Terminal B. Stop this Terminal A server before the next workspace; state from the demonstration is not transferred.

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.


For **instructions only**, copy `workflow-md-only.md` as `workflow.md`. For **instructions plus code**, copy updated `workflow.md`, reusable `automation/` and documented dependencies. Copy no finished task implementations, demo outputs, reports, evidence or browser session state.

Start a new conversation in each workspace with the same agent/model. Ask it to read `workflow.md`, execute on current inputs and record evidence. Code mode must actually invoke the helpers. Run only one workspace on port 8765 at a time; stop your own previous server before starting the next. Bootstrap a fresh session in each. Transfer includes Serial / COM9; read all current values from case.json. Write current-case tests/Page Object extensions afresh; copy neither demo tests nor auth state. External Selenium authentication needs its own reviewed fixture; Playwright state does not automatically authenticate Selenium.

**You should get:** Two independent results checked against the same criteria. Record manual fallback and any scripts independently created in instructions-only mode.

**Why:** New inputs expose hard-coded values. The pair shows what the reusable code contributed in these cases.

## 12. Check and submit

**Do this:** Review actual evidence with the facilitator. Review actual MCP observations, handover evidence, all required UI assertions and real pytest/JUnit results. Separate local no-login success from any untested external authentication path; local checks do not validate an external target.

Submit both workflow versions, `extraction-map.md`, `automation/` with checks/README, and `evidence/`. Compare correctness, time, interventions and failures. Explain what moved into code and what still requires judgment.

**You should get:** An evidence-backed assessment with untested paths identified. A justified engineering failure or blocked input can be the correct training result.

**Why:** The facilitator assesses both your work and your explanation. One pair of replays is not a statistical benchmark.


Reference: [UI requirements](../training_kit/test_team/REQUIREMENTS.md), [test walkthrough](TEST_TEAM_WALKTHROUGH.md) and the handbook’s T1 bootstrap/handover instructions.
