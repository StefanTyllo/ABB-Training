# Test team: two exercises from live exploration to effective tests

**Audience:** test engineers comfortable with pytest, Page Objects and basic browser locators. Use the coding agent to guide unfamiliar commands; the facilitator prepares access and reviews the assertions.

**Outcomes:** T1 uses Copilot CLI and Playwright MCP to explore a dynamic form and extend the existing Selenium/pytest framework. T2 challenges a passing suite with defects and extracts repeatable effectiveness evaluation. Both exercises follow demonstration → Markdown abstraction → deterministic helpers → fresh-case replay.

## Before starting

Use the [handbook](ABB_Workflow_Training.pdf#page=17) for installation, agent smoke tests and PDF attachment extraction. The **training root** contains `.venv/`, `materials/` and `work/`; preparation commands start there. Keep `materials/` unchanged. Activate the venv in each terminal:

```bash
source .venv/bin/activate
python -m pip install -r materials/test_team/scaffold/requirements.txt
```

Use Python 3.12, Chrome/Chromium and a compatible driver or working Selenium Manager. For MCP/login work, the facilitator installs reviewed pinned Playwright MCP and Node.js Playwright dependencies and verifies Copilot access. Record versions and agent/model; use the same agent/model in demonstration and both replay conditions.

**Two targets:** the supplied app has no login. It supports repeatable local form/testing exercises. An authenticated extension needs an authorized test URL/account, reviewed login selectors, an authenticated readiness signal and independent product requirements. The local graders do not validate that external target. Do not add login to the protected local fixture or invent a passing login result.

The local form's None/Password selector represents simulated device configuration, not application login. Use invented passwords there; keep real login credentials in the separate local bootstrap configuration.

**Guided-work prompt:** “Read the task, requirements, fixture and Page Objects. Guide one action at a time. Explain its purpose, expected evidence and allowed changes. Wait for my reasoning between actions. Record actual commands/tool calls, observations and recovery in `evidence/session.md`. Build reusable helpers only after demonstrating the process.”


**Copilot context and evidence.** Use GitHub Copilot CLI consistently, with a fresh conversation/invocation for each stage after the guided demo. Read the prepared task-card.md and pass only the saved stage inputs needed. Provide the current stage and its named inputs; keep the full card/contract available on demand. Link raw evidence instead of repeating entire transcripts. No automation/ directory exists before Stage 4; early fixtures go under evidence/stage1-fixtures/. Keep original captures immutable and evidence/session.md append-only. In Stage 4, finish required helpers/checks before optional expansion, keep workflow-md-only.md unchanged, and test caller-owned console redirection plus fresh report paths. Helper logs belong in unique run directories; a growing journal or an already-open caller log must not block valid verification. Completed device tasks are verified without a second write.

---

## T1 — Explore the form and extend Page Objects

### 1. Prepare and establish the test oracle

From the training root:

```bash
python materials/prepare_lab.py t1 demo work/t1-demo
cd work/t1-demo
python server.py --variant correct --port 8765 --state state.json
```

Leave terminal A running. In terminal B, activate the venv and enter the same workspace:

```bash
python -m pytest browser_preflight.py -q
python -m pytest -q
```

- **What and why:** verify real browser access and understand expected behavior before interpreting the UI.
- **How:** read `REQUIREMENTS.md`, `case.json`, `BasePage`, `SettingsPage`, fixture and tests. The starter has one smoke pass and one skipped placeholder; the skip is unfinished work. Each test resets the synthetic app to Serial/COM1/None.
- **Failure and recovery:** browser startup, wrong URL or occupied port is blocked setup. Resolve the actual cause; stop only the server you own. HTTP-only access is insufficient.
- **Code to add later:** readiness and test-execution helpers should distinguish startup errors from UI assertion failures.
- **Boundary:** extend `pages/settings_page.py`, `tests/test_settings.py` and common artifacts; add bootstrap/non-secret configuration as needed. Preserve the server, BasePage, fixture, case data and requirements. The requirements, not current app output, determine expected behavior.

### 2. Prepare credentials and demonstrate the login bootstrap

- **What and why:** perform a known login sequence with local code, then let the agent explore the unfamiliar authenticated UI.
- **How:** for an authenticated target, the operator fills a local `.env` with `TEST_BASE_URL`, `TEST_USERNAME` and `TEST_PASSWORD`. Commit only an `.env.example` with empty credential values. Add these rules to the workspace's `.gitignore` before creating secrets:

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

The ignore check should identify both paths; the tracked-file check should return no entries. Git ignore controls tracking, not agent/local access. Restrict access and exclude credentials/state from prompts, logs, screenshots and evidence archives. Do not display `.env` to the agent.

- **How the bootstrap works:** demonstrate a facilitator-reviewed **Node.js** script that loads `.env`, validates inputs, uses Playwright to log in, waits for the agreed authenticated signal, saves `context.storageState()` under `.auth/`, then closes its browser. The script runs locally; do not serve credentials in browser JavaScript. No-login fixture mode opens the local form and exports session state without credentials.
- **Failure and recovery:** missing values, rejected login, changed selectors or MFA must produce a clear blocked result/operator action. A written state file does not prove authentication.
- **Code to extract later:** parameterized bootstrap with explicit readiness waits, bounded timeouts and sanitized failures. Prove protected-form access; mark login untested when using only the local fixture.
- **Why it works when verified:** the helper checks the authenticated outcome after login rather than assuming submission succeeded.

### 3. Hand state to Playwright MCP and verify access

- **What and why:** make the prepared session available to Copilot's browser tools.
- **How:** start Copilot without the login environment variables. Use `/mcp add`, local server command `npx`, and arguments `-y`, the reviewed pinned `@playwright/mcp` package version, `--isolated`, and `--storage-state=<absolute-path>`. Replace the path with the real state file. Ask MCP to open the target and verify the expected form before exploration.
- **Failure and recovery:** a wrong path, expired state or sessionStorage-dependent app may return to login. Validate the path and rerun bootstrap for expiry. If saved storage state cannot carry this app's session, rehearse an attached-browser method before class.
- **Code to add later:** validate the state file and target; record an authenticated/no-login readiness outcome without exposing state contents.
- **Evidence and explanation:** the MCP browser reaches the intended form. Storage state initializes a new context; starting Copilot alone does not hand over an existing browser tab.

### 4. Explore transitions and record locator evidence

- **What and why:** discover fields and dependencies that appear only after interaction.
- **How:** use MCP to switch Serial → TCP → Serial and None → Password → None. Wait for each change, inspect snapshots and DOM attributes as needed, and record this table from actual observations:

| Action | Requirement | Observed fields/state | Readiness signal | Candidate Selenium locator |
| --- | --- | --- | --- | --- |
| Select TCP | Host/Port visible; Device hidden | Fill after execution | Both visibility conditions hold | Fill after DOM inspection |

- **What can go wrong:** inspecting mid-transition, missing the reverse direction or copying temporary snapshot references into tests.
- **Supplement Markdown with code:** express demonstrated interactions and condition-based waits in the existing Page Object. Prefer stable IDs/test attributes or scoped semantic selectors supported by the framework; verify uniqueness across relevant states.
- **Evidence and explanation:** both directions match requirements after asynchronous settling. Observable readiness handles variable timing without fixed sleeps. MCP references help exploration; committed Selenium locators must be independently valid.

### 5. Extend the existing tests and prove persistence

- **What and why:** convert observed interactions into maintainable assertions of product behavior.
- **How:** use `case.json` values, save, wait, reload and assert exact restored active connection/authentication values, including password when active. Reject an empty password and an invalid port; after each rejected save, reload and verify the last valid configuration survived. Run pytest and inspect failures.
- **What can go wrong:** asserting only “Saved,” using demo constants, swallowing failures or removing the placeholder without substantive coverage.
- **Supplement Markdown with code:** reuse existing Page Object helpers; put readiness in Page Objects and behavioral assertions in tests. External Selenium tests need their own reviewed authentication fixture; Playwright state does not automatically authenticate Selenium.
- **Acceptance and explanation:** UI-01/UI-02 cover both visibility directions, SAVE-01 verifies exact persistence/non-overwrite, and ASYNC-01 uses observable waits. No required skips or fixed sleeps remain. Reload assertions establish persistence; successful clicks alone do not.

### 6. Extract the workflow and reusable session/evidence code

After completing the demonstration, reconstruct actual operations in `workflow.md`: inputs, steps, reasoning, branches, evidence, failure handling and acceptance. Review/parameterize it and save unchanged `workflow-md-only.md`. Write `extraction-map.md`, then implement under `automation/`:

| Operation | Problem code addresses | Required result |
| --- | --- | --- |
| Bootstrap and handover preflight | Repeated login/configuration mistakes | Verified form access or sanitized blocked result |
| Page Object actions/waits | Repeated timing and locator mistakes | Observable state established before proceeding |
| Test runner/evidence collection | Missing results or misleading completion claims | Actual browser identity/URL, collected/skipped counts, statuses and artifacts |

Keep unfamiliar UI interpretation, expected behavior and assertion quality with the engineer/agent. Document exact helper commands/dependencies in `automation/README.md`; update `workflow.md` to invoke them. Use independent helper fixtures, not current-case assumptions. Retain an intentional missing-element screenshot and error context under `evidence/`, sanitized for secrets.

**Required helper checks:** successful interaction/handover; wrong URL; missing credentials in login mode; rejected/expired authentication when using a login target; missing element with useful evidence; browser startup failure; required skip rejection. Mark unexercised login branches blocked. No-login practice does not complete authentication validation.

### 7. Prepare fresh T1 replays

Stop terminal A with Ctrl-C. Return to the training root:

```bash
python materials/prepare_lab.py t1 transfer work/t1-transfer-md
python materials/prepare_lab.py t1 transfer work/t1-transfer-code
```

Use the paired replay procedure below. Start each workspace's `correct` server with the same server command from step 1, one at a time. Transfer targets Serial/Password with a different device value; test both reverse transitions too. Supply local credentials where needed and bootstrap fresh sessions. Copy no finished Page Objects, demo tests or authentication state.

**Completion:** actual Selenium/pytest execution, no required skips, both visibility directions, exact current-case save/reload values, reuse of the framework and retained evidence. The new MCP/login route needs live rehearsal; previous Selenium CI results do not validate that route.

---

## T2 — Test whether the suite detects defects

### 1. Prepare the weak suite and explain its limited claim

Stop the previous server before starting T2. From the training root:

```bash
python materials/prepare_lab.py t2 demo work/t2-demo
cd work/t2-demo
python server.py --variant correct --port 8765 --state state.json
```

In terminal B, activate the venv, enter the same workspace and run:

```bash
python -m pytest browser_preflight.py -q
python -m pytest -q
```

- **What and why:** show that a passing smoke test can leave a requirement untested.
- **How:** read its assertion and map SAVE-01, VAL-01 and ASYNC-01 to observable behavior. Demonstrate a valid save and reload on the correct app.
- **What can go wrong:** treating green status or requirement markers as proof of semantic coverage.
- **Code to add later:** collect test names/counts and assertion results, but have the engineer explain what each assertion establishes.
- **Boundary:** use the same editable Page Object/test files and common artifacts as T1. Preserve independent requirements and the application; do not diagnose by inspecting the server's fault-switch implementation.

### 2. Show the weak test surviving a real defect

Stop terminal A with Ctrl-C. With that server stopped, run in the same workspace:

```bash
python -c "from pathlib import Path; Path('state.json').unlink(missing_ok=True)"
python server.py --variant no-persist --port 8765 --state state.json
```

Run the unchanged weak suite in terminal B.

- **What and why:** demonstrate a gap between a passing test and required persistence. This variant acknowledges saving without retaining the configuration.
- **Failure and recovery:** if startup or browser access fails, fix infrastructure before evaluating test effectiveness. A crash or unrelated timeout is not defect detection.
- **Code to extract later:** a serial variant runner manages its own child server and clean state, waits for readiness and records startup/test phases separately.
- **Evidence and explanation:** the weak suite passes on the faulty app because it does not establish saved values after reload. Record the actual assertion and outcome, not just the exit code.

### 3. Strengthen assertions and confirm both sides

Add coverage in the existing framework for all of these:

- Valid TCP ports **1 and 65535**.
- Invalid **0, 65536 and non-integer text**.
- Nonempty Host/Serial Device and nonempty password in Password mode, as required by the product contract.
- Exact saved active values after an actual browser reload.
- Invalid save preserves the last valid saved configuration after reload.
- Condition-based waits for asynchronous fields/save completion.

Run the strengthened suite on `no-persist`. Then stop/reset/restart `correct` using the same procedure and run the **unchanged strengthened suite** there.

- **What and why:** prove the tests distinguish correct and defective behavior rather than merely causing a failure.
- **What can go wrong:** correct app also fails, or a persistence defect is “detected” by an unrelated timeout.
- **Supplement Markdown with code:** use exact-value reload assertions, reusable Page Object actions and fixture inputs. Preserve assertion details and expected/actual values.
- **Acceptance and explanation:** correct app passes; `no-persist` fails a persistence assertion linked to SAVE-01. Review why the specific failure demonstrates the requirement violation.

### 4. Extract serial effectiveness evaluation

After the demonstration, write/review `workflow.md` and preserve `workflow-md-only.md`. Parameterize workspace, server command/variant, port, state path, case path and evidence destination. Write `extraction-map.md`, then implement an evaluation runner under `automation/`.

| Operation | Failure handling | Evidence |
| --- | --- | --- |
| Start owned server and wait | Occupied port/startup error → blocked | Command, URL, startup outcome and logs |
| Run collected tests | Preserve native failures and reject required skips | Test files/digests, case, counts, exit status and assertion details |
| Evaluate correct then defective app | Correct-app failure prevents a successful detection score | Results linked to the same suite and relevant requirement |
| Clean up | Stop only its child process in `finally` | Owned-process shutdown and isolated/reset state |

Use separate state files or clean resets and evaluate sequentially. Never kill an unrelated process occupying the port. Keep judgment of assertion relevance with the engineer. Document commands/dependencies, use independent helper fixtures and update the workflow to invoke the runner.

**Required checks:** correct app passes; known persistence defect detected; required skip rejected; occupied port/failed startup reported as infrastructure failure; assertion failures retained in final results; child cleanup occurs on failure. Code improves repeatability by controlling setup and retaining evidence; it cannot decide whether an arbitrary failing assertion is meaningful.

### 5. Transfer and detect a boundary defect

Stop the previous server. From the training root:

```bash
python materials/prepare_lab.py t2 transfer work/t2-transfer-md
python materials/prepare_lab.py t2 transfer work/t2-transfer-code
```

Use paired replay. Start each fresh workspace with `correct` and current `case.json`; it includes valid port 65535. The facilitator then stops/resets/restarts that workspace with `--variant bad-boundary`. Run the same improved suite. Keep the chosen variant undisclosed until evaluation where feasible; the fixture is a reproducible exercise, not a tamper-proof benchmark.

**Completion:** correct app passes; the boundary variant fails because it incorrectly rejects valid 65535. This defect occurs at Save, so inspect the relevant assertion instead of trusting a generic “after reload” failure label. Retain the full required-case coverage from step 3 and relevant failure evidence. Transfer reusable runners, not completed demo tests.

---

## Paired replay and submission for both exercises

Complete both demonstrations and code extraction stages. The facilitator selects at least one exercise for paired replay; use both if time permits.

1. **MD-only:** copy `workflow-md-only.md` as `workflow.md` into the clean workspace, without `automation/` or completed outputs.
2. **MD plus code:** copy updated `workflow.md`, reusable `automation/` and documented dependencies. Both start with supplied Page Objects/tests; no finished demo tests, app state, reports or authentication files are transferred.
3. Start a new conversation in each with the same agent/model. Ask it explicitly to read `workflow.md`, use current inputs and record execution/recovery. Record scripts an MD-only agent independently creates.
4. Run one workspace/server at a time on port 8765. Compare acceptance criteria, actual helper invocation, errors, elapsed time and interventions. Manual fallback is not evidence that the helper passed.

For **each lab**, submit both workflows, `extraction-map.md`, `automation/` with checks/README, edited Page Objects/tests and sanitized session/results/failure artifacts. Learner automation reports exit 0 for pass, 1 for engineering failure and 2 for blocked setup; preserve native pytest statuses separately. A relevant expected failure on a defective app is evidence the evaluation must interpret, not silently discard.

Use the handbook rubric: at least 8/10, no zero in any category, all mandatory criteria satisfied and actual real-browser execution. Review demonstration evidence, reusable workflow, deterministic boundary, code quality and feedback/transfer. Missing browser execution or fabricated results prevent acceptance regardless of score.

Finish with **goal → action → observed failure → code remediation → rerun result → why that evidence supports the outcome → untested paths**. For example, if observed: “An immediate lookup failed during the transition; a wait for Host/Port visibility and Device invisibility passed in both directions and on the fresh case.” This supports that readiness fix, not universal timing coverage. One paired replay does not establish a general advantage over Markdown alone.

## Final adequacy and completeness review

- **Documentation review, 14 October 2026:** adequate as a facilitated guide for the stated pytest/POM audience. Both exercises explain the purpose, operations, failure/recovery, code remediation and evidence required to explain success. The login extension has explicit facilitator inputs rather than assumed access.
- **Checks performed:** all six test-track workspace preparations ran; shell syntax, Markdown parsing and local source links were checked. Supplied HTTP contract checks passed for `correct`, `no-persist` and `bad-boundary`. This review environment lacks pytest, Selenium and Chrome, so real-browser, MCP and authenticated handover were not executed. Those gates remain required before delivery; HTTP checks do not substitute for them.
- **Level:** step-by-step guidance for a test engineer with pytest/POM experience. Setup paths, session handover, all required behaviors, failure classifications and evidence are explicit; implementing the login adapter and helpers remains workshop work.
- **Coverage:** T1 and T2 each include demonstration, Markdown abstraction, deterministic code extraction, helper failure checks, transfer and acceptance. Credentials/handover are an explicit extension to the no-login fixture.
- **Required local gate:** rehearse MCP access and the actual login adapter where authentication is required; inspect real Selenium runs and defect assertions. This document is not evidence of a completed login/classroom run.
- **Review against:** [test-team reference](../training_kit/test_team/README.md), [product requirements](../training_kit/test_team/REQUIREMENTS.md), [Playwright MCP session guidance](https://github.com/microsoft/playwright-mcp), [Copilot MCP setup](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers) and the handbook's method/rubric.
