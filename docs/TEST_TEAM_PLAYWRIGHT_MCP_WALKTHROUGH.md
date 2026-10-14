# Test team: from live WebUI exploration to a repeatable workflow

Use this walkthrough with [T1 and T2 in the training PDF](ABB_Workflow_Training.pdf#page=17). It explains the purpose of each step and how adding small pieces of code makes a Markdown workflow more reliable.

**Goal:** let Copilot CLI inspect a dynamic form through Playwright MCP, extend the existing Selenium Page Objects and pytest tests, then repeat the process on a fresh case.

**Two environments:** the supplied local app has no login. An authenticated exercise needs a facilitator-provided test URL, account, login selectors and a signal that proves login succeeded. Use the local app to practice exploration and tests; record the login part as untested until it runs against an authenticated target. The existing local graders cover the synthetic app.

## 1. Agree what success means

- **What and why:** establish expected behavior before inspecting the application, so an existing bug does not become the expected result.
- **How:** read `REQUIREMENTS.md`, `case.json`, Page Objects, fixture and tests. Identify existing helpers and allowed changes.
- **What can go wrong:** the AI copies current behavior or a passing smoke test as proof of correctness.
- **Supplement Markdown with code:** later add a preflight that checks required files and case keys; keep business expectations in tests.
- **Evidence and explanation:** each required behavior maps to a concrete assertion. Input checks prevent incomplete runs; assertions establish the product behavior.

## 2. Start the app and prove the browser works

From the training root, with the training venv active:

```bash
python materials/prepare_lab.py t1 demo work/t1-demo
cd work/t1-demo
python server.py --variant correct --port 8765 --state state.json
```

Leave the server running. In a second terminal, activate the same venv and enter the same workspace:

```bash
python -m pytest browser_preflight.py -q
python -m pytest -q
```

- **What and why:** separate environment problems from application defects.
- **What can go wrong:** the port is occupied, the browser cannot start, or the wrong workspace is served. The starter's skipped placeholder is unfinished work.
- **Supplement Markdown with code:** after demonstrating the steps, extract a readiness helper that checks the target and browser and reports `BLOCKED` when setup fails. Only stop processes owned by the exercise.
- **Evidence and explanation:** retain the URL, browser identity and actual results. A real browser interaction proves more than an HTTP response or an agent's completion message.

## 3. Prepare local credentials when login is required

- **What and why:** keep credentials outside instructions and committed code while making login repeatable.
- **How:** the operator creates `.env` locally with `TEST_BASE_URL`, `TEST_USERNAME` and `TEST_PASSWORD`. Commit only an `.env.example` containing empty credential values. Add the following to the workspace's `.gitignore` before creating secrets:

```gitignore
.env
.env.*
!.env.example
.auth/
```

```bash
git check-ignore .env .auth/storage-state.json
git ls-files -- .env .auth
```

- **What can go wrong:** an ignored file was already tracked, credentials appear in logs, or an agent reads `.env`. Git ignore controls tracking, not access.
- **Supplement Markdown with code:** make the login helper validate required values and report missing variable names without printing values. Restrict local access and exclude credentials and session state from evidence archives.
- **Evidence and explanation:** ignore checks identify both secret paths and the tracked-file check returns no entries. The operator confirms this without displaying secrets. Skip credential creation for the no-login fixture.

## 4. Bootstrap login with local JavaScript

- **What and why:** perform the known login sequence deterministically before asking AI to explore unfamiliar UI.
- **How:** first demonstrate a facilitator-reviewed Node.js script. It loads `.env`, opens the target with Playwright, fills approved login fields, submits and waits for the agreed authenticated signal. It saves `context.storageState()` to `.auth/storage-state.json` and closes its browser. No-login mode opens the local form without credentials.
- **What can go wrong:** selectors change, credentials are rejected, MFA needs operator input, or login redirects back to the sign-in page.
- **Supplement Markdown with code:** use condition-based waits, a bounded timeout and explicit failure handling. Stop and request the appropriate operator action when authentication cannot complete.
- **Evidence and explanation:** record successful access to the protected form, without tokens or passwords. A saved file alone does not prove login. The helper worked because it verified an authenticated outcome after submitting credentials.

## 5. Hand the session to Copilot CLI

- **What and why:** give Copilot browser access to the prepared application state.
- **How:** start Copilot without the login environment variables. Use `/mcp add` to configure local Playwright MCP with command `npx` and arguments `-y`, a reviewed pinned `@playwright/mcp` version, `--isolated`, and `--storage-state=<absolute-path>`. Replace the path with the actual state file. Record installed versions. Ask MCP to open the target and verify the protected form.
- **What can go wrong:** a relative path points elsewhere, authentication expires, or the app relies on sessionStorage that saved storage state does not restore.
- **Supplement Markdown with code:** validate the state path and target; rerun bootstrap for expired state. Rehearse an attached-browser approach if the application requires it.
- **Evidence and explanation:** the MCP browser reaches the intended form. Saved state initializes a new browser context; starting Copilot by itself does not transfer an open browser or its login.

## 6. Explore one dynamic transition at a time

- **What and why:** discover fields that static HTML alone cannot expose.
- **How:** use MCP to switch Serial → TCP → Serial and None → Password → None. Inspect after each change settles. Record a small table:

| Action | Expected behavior | Observed behavior | Readiness signal | Candidate Selenium locator |
| --- | --- | --- | --- | --- |
| Select TCP | Host/Port visible; Device hidden | Fill after execution | Both visibility conditions hold | Fill after inspecting DOM |

- **What can go wrong:** the AI observes a transitional state, misses the reverse transition, or treats an MCP snapshot reference as a reusable locator.
- **Supplement Markdown with code:** implement demonstrated interactions and condition-based waits in the existing Page Object. Check locator uniqueness in relevant states.
- **Evidence and explanation:** both directions match the requirements. Waiting for observable conditions handles asynchronous changes without depending on a guessed delay.

## 7. Extend Page Objects and meaningful tests

- **What and why:** turn exploration into maintainable Selenium/pytest coverage.
- **How:** extend `pages/settings_page.py` and `tests/test_settings.py`. Save current-case values, wait, reload and assert exact restored active values. Reject an empty password and an invalid port; verify the previous valid configuration survives each rejected save. Run pytest.
- **What can go wrong:** tests only assert a “Saved” message, contain demo-only values, retain placeholders or silently skip required behavior.
- **Supplement Markdown with code:** reuse Page Object methods and fixture data; put behavioral assertions in tests. External Selenium tests need their own reviewed authentication fixture; Playwright state does not automatically authenticate Selenium.
- **Evidence and explanation:** all required tests execute, and reload assertions establish persistence. Successful clicks alone cannot establish that values were stored correctly.

## 8. Extract the Markdown workflow, then add code

- **What and why:** preserve the process that actually worked and remove repeated manual reconstruction.
- **How:** after completing the demonstration, ask Copilot to write `workflow.md`: inputs, ordered steps, decisions, evidence, failure handling and acceptance. Review it, replace demo-specific values with inputs, then preserve `workflow-md-only.md` unchanged.
- **What can go wrong:** prose omits a recovery step or the agent follows an instruction inconsistently on the next case.
- **Supplement Markdown with code:** create `extraction-map.md`, then implement the fully specified operations under `automation/`. Update `workflow.md` to invoke those helpers and interpret their results.
- **Evidence and explanation:** exercise a valid path and its failure branch for each helper. Code improves repeatability by checking preconditions and producing explicit outcomes; engineering judgment still determines expected behavior and useful assertions.

| Markdown instruction | Code to extract after demonstration | Failure made observable |
| --- | --- | --- |
| Prepare the session | Login/no-login bootstrap | Missing inputs, rejected login, unavailable target |
| Wait for the form | Page Object readiness conditions | Required field never becomes ready |
| Execute and retain evidence | Pytest runner and sanitized artifact collector | Startup error, failed assertion, missing artifacts |
| Compare application variants | Serial evaluation runner | Correct app fails, defect survives, irrelevant failure |

## 9. Use T2 to challenge a green result

- **What and why:** establish whether tests detect a requirement violation.
- **How:** follow T2's stop/reset/start procedure. Run the same improved suite against `correct` and `no-persist`. Cover valid ports 1/65535 and invalid 0/65536/non-integer values. In transfer, also evaluate `bad-boundary`.
- **What can go wrong:** the suite fails because of infrastructure, or fails both correct and defective apps.
- **Supplement Markdown with code:** evaluate variants serially, isolate/reset state and retain assertion details. Reject required skips and distinguish startup errors from behavioral failures.
- **Evidence and explanation:** the correct app passes; the defective app fails the relevant assertion. This supports defect detection because the changed behavior, rather than an unrelated crash, explains the failure.

## 10. Replay on a fresh case and explain the result

- **What and why:** check whether the workflow transfers beyond the original demonstration.
- **How:** prepare separate T1 transfer workspaces. MD-only receives the reviewed Markdown; code-assisted receives the updated Markdown and reusable helpers/dependencies. Both start from clean Page Objects/tests and use the same agent/model. Supply credentials locally and create fresh sessions. Copy no completed demo solutions or authentication state.
- **What can go wrong:** hidden demo constants, missing dependencies or copied outputs make a replay appear successful.
- **Supplement Markdown with code:** validate fresh inputs and record the actual case, commands, test counts, outcomes and interventions. Correct any exposed assumptions, then repeat the affected check.
- **Evidence and explanation:** exact current-case values survive reload, both transitions work, and failures have useful evidence. This demonstrates reuse on the cases exercised; one replay does not establish a general success-rate improvement.

## Record why it worked

Finish `evidence/session.md` with this short record, completed from actual runs:

```text
Goal and requirement:
Action and command/tool used:
Expected and observed result:
What failed and the evidence:
Code added to address the repeated failure:
Verification after the change:
Why the evidence supports the outcome:
Remaining untested paths:
```

For example, **if observed**: “The immediate field lookup failed during the asynchronous transition. We added a wait for Host/Port visibility and Device invisibility. Both switch directions then passed, including the fresh case. The evidence supports the readiness fix; it does not prove every timing condition is covered.”

**Status:** this document describes the exercise and evidence to collect. It is not a record of a completed login/MCP rehearsal. Use “worked” only after recording the corresponding execution evidence.

## Setup references

- [Playwright MCP: configuration and session state](https://github.com/microsoft/playwright-mcp)
- [Adding MCP servers to Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)
- [Existing test-team scaffold and requirements](../training_kit/test_team/README.md)
