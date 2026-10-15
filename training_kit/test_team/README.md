# T1/T2 technical reference

Use the PDF handbook for the training sequence and assessment. These files supply a synthetic local device and an existing low-level Selenium scaffold, not extracted workflow automation. No device, account or login is needed. Use invented passwords only.

## Environment and first launch

Commands use Bash in the training root: the directory containing `.venv/`, `materials/`, and `work/`. Complete the handbook's root venv setup first. Python 3.12, Chrome/Chromium, and either a compatible ChromeDriver or working Selenium Manager downloads are required. Keep `materials/` unchanged.

Terminal A, starting at the training root:

```bash
source .venv/bin/activate
python -m pip install -r materials/test_team/scaffold/requirements.txt
python materials/prepare_lab.py t1 demo work/t1-demo
cd work/t1-demo
python server.py --variant correct --port 8765 --state state.json
```

Leave terminal A running. Open terminal B at the training root:

```bash
source .venv/bin/activate
cd work/t1-demo
python -m pytest browser_preflight.py -q
python -m pytest -q
```

The preflight must launch real Chrome and interact with dynamic fields. Expected starter results in a working environment: T1 has one pass and one intentionally skipped learner placeholder; T2 has one weak pass. The skip is unfinished coverage. A browser startup error is a blocked environment, not a detected application defect.

Use `HEADED=1 python -m pytest browser_preflight.py -q` when a desktop display is available. Optional exported variables `CHROME_BINARY=/absolute/chrome` and `CHROMEDRIVER=/absolute/chromedriver` select installed executables; otherwise Selenium Manager discovers/downloads them. Do not disable browser sandboxing to force a launch.

## Next lab or transfer workspace

Stop the running server with Ctrl-C in terminal A **before starting the next lab or transfer**. From a prepared workspace, `cd ../..` returns to the training root. Prepare a fresh output directory with the handbook's command; existing output is refused. These are valid preparation examples, each run from the training root:

```bash
python materials/prepare_lab.py t1 transfer work/t1-transfer-md
python materials/prepare_lab.py t1 transfer work/t1-transfer-code
python materials/prepare_lab.py t2 demo work/t2-demo
python materials/prepare_lab.py t2 transfer work/t2-transfer-md
python materials/prepare_lab.py t2 transfer work/t2-transfer-code
```

For example, after stopping the previous server, terminal A can start T2 from the training root:

```bash
source .venv/bin/activate
cd work/t2-demo
python server.py --variant correct --port 8765 --state state.json
```

In terminal B, return to the training root with `cd ../..`, activate `source .venv/bin/activate`, enter `cd work/t2-demo`, then run the two pytest commands above. For transfer, use its prepared directory in both terminals. Run one workspace at a time on port 8765; never run the shared-state fixture in parallel.

## Product and test contract

`REQUIREMENTS.md` defines the independent expected properties. `case.json` contains inputs, not expected outcomes. T1 demo uses TCP/Password; transfer uses Serial/Password and a different device. Both must cover None and reverse visibility transitions. T2 demo uses TCP/1502; transfer includes valid endpoint 65535.

T1 requires UI-01, UI-02, SAVE-01 and ASYNC-01 assertions: both directions of connection/authentication visibility changes, valid saves, actual browser reload and exact restored active values. No required skips, placeholders or fixed sleeps may remain. T2 additionally requires VAL-01: valid ports 1/65535, invalid 0/65536/non-integer text, invalid-save non-overwrite, and persistence after reload. Improved tests must pass the correct application and fail the faulty application for the relevant requirement violation. Requirement markers alone do not prove coverage.

Editable files: `pages/settings_page.py`, `tests/test_settings.py`, `evidence/session.md`, `workflow.md`, `workflow-md-only.md`, `extraction-map.md`, and supporting `automation/` files. Preserve the server, BasePage, fixture, case data and requirements. Reuse existing helpers. The fixture's HTTP reset is setup only; test assertions and interactions use the actual browser. Each test resets Serial/COM1/None defaults before opening the page. The app has no login.

## Variant and state controls

From the prepared workspace, stop terminal A's server with Ctrl-C before clearing state or selecting a variant:

```bash
python -c "from pathlib import Path; Path('state.json').unlink(missing_ok=True)"
python server.py --variant correct --port 8765 --state state.json
```

Repeat that stop/reset/start sequence with `--variant no-persist` for the T2 demo defect or `--variant bad-boundary` for transfer. Run the unchanged tests in terminal B. `no-persist` acknowledges a valid save but does not persist it; `bad-boundary` rejects valid port 65535. The original weak smoke is expected to pass all variants. The facilitator may withhold the selected variant until evaluation; included source makes this a reproducible classroom exercise, not a tamper-proof benchmark.

For a separate port, start `python server.py --variant correct --port 8766 --state other.json` and run `BASE_URL=http://127.0.0.1:8766 python -m pytest -q` in the matching prepared workspace.

## Verification boundary

From the training root, `python materials/test_team/author_checks/check_server.py` checks real HTTP contracts using stdlib only. It does not verify browser rendering or Selenium waits. See `materials/test_team/VERIFICATION.md` for measured results. The initial author browser could not start; the subsequent GitHub Actions rehearsals used real Chrome successfully. Passing the supplied preflight on each teaching machine remains required. See VERIFICATION.md for run links and the exact scope.
