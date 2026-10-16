# T1/T2 technical reference

The image supplies Selenium, pytest, Node, a matched Chrome/driver pair and sandboxed Playwright/MCP. No browser downloads or host tool paths are needed during exercises. The synthetic app has no login. The supplied T1 `tools/session_bootstrap.mjs` is infrastructure, separate from learner-created `automation/`. See [support instructions](support/README.md).

## Product and test contract

`REQUIREMENTS.md` defines the independent expected properties. `case.json` contains inputs, not expected outcomes. T1 demo uses TCP/Password; transfer uses Serial/Password and a different device. Both must cover None and reverse visibility transitions. T2 demo uses TCP/1502; transfer includes valid endpoint 65535.

T1 requires UI-01, UI-02, SAVE-01 and ASYNC-01 assertions: both directions of connection/authentication visibility changes, valid saves, actual browser reload and exact restored active values. No required skips, placeholders or fixed sleeps may remain. T2 additionally requires VAL-01: valid ports 1/65535, invalid 0/65536/non-integer text, invalid-save non-overwrite, and persistence after reload. Improved tests must pass the correct application and fail the faulty application for the relevant requirement violation. Requirement markers alone do not prove coverage.

Editable files: `pages/settings_page.py`, `tests/test_settings.py`, `evidence/session.md`, `workflow.md`, `workflow-md-only.md`, `extraction-map.md`, and supporting `automation/` files. Preserve the server, BasePage, fixture, case data and requirements. Reuse existing helpers. The fixture's HTTP reset is setup only; test assertions and interactions use the actual browser. Each test resets Serial/COM1/None defaults before opening the page. The app has no login.

## Variant and state controls

From the prepared workspace, stop terminal A's server with Ctrl-C before clearing state or selecting a variant:

**Inside the workspace**:

```bash
python -c "from pathlib import Path; Path('state.json').unlink(missing_ok=True)"
python server.py --variant correct --port 8765 --state state.json
```

Repeat that stop/reset/start sequence with `--variant no-persist` for the T2 demo defect or `--variant bad-boundary` for transfer. Run the unchanged tests in terminal B. `no-persist` acknowledges a valid save but does not persist it; `bad-boundary` rejects valid port 65535. The original weak smoke is expected to pass all variants. The facilitator may withhold the selected variant until evaluation; included source makes this a reproducible classroom exercise, not a tamper-proof benchmark.

For a separate port, start `python server.py --variant correct --port 8766 --state other.json` and run `BASE_URL=http://127.0.0.1:8766 python -m pytest -q` in the matching prepared workspace.

## Verification boundary

The facilitator image provides `python training_kit/test_team/author_checks/check_server.py` through a separate Docker invocation; it checks real HTTP contracts using stdlib only. It does not verify browser rendering or Selenium waits. See `VERIFICATION.md` for measured results. The initial author browser could not start; the subsequent GitHub Actions rehearsals used real Chrome successfully. Passing the supplied preflight on each teaching machine remains required. See VERIFICATION.md for run links and the exact scope.

## Container workspaces

Use these commands from the unpacked package folder with `.venv` activated. Provider login is separate; retain the chosen provider/model. Fresh transfers are performed only after Stage 4.


### T1

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

### T2

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
