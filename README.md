# ABB workflow training

Run the training tools in a local Python virtual environment. Install Python 3.11+
(with pip and venv) and Git. FW2 also needs GCC: on Windows, use WSL with GCC for
that lab. Browser labs need Chrome/Chromium; Selenium Manager finds/downloads a
matching driver when `CHROME_BINARY` and `CHROMEDRIVER` are unset. Initial setup
and automatic browser/driver downloads need network access.

From the repository or unpacked learner package folder:

**Windows PowerShell**:

```powershell
py -3 setup_env.py
. .\.venv\Scripts\Activate.ps1
abb doctor --offline
```

**Linux / macOS / WSL — Bash**:

```bash
python3 setup_env.py
source .venv/bin/activate
abb doctor --offline
```

On Debian/Ubuntu, install `python3-venv`, `python3-pip`, `git` and `gcc` through
your system package manager if missing. Use a separate `.venv` for Windows and
WSL; virtual environments cannot be shared across operating systems or moved.
To recreate one, remove only `.venv` and rerun setup; your prepared work persists.
If PowerShell activation is restricted, invoke `.\.venv\Scripts\abb.exe` directly.

## Coding agents and browser tools

Install Node.js 22+ with npm, then run `python setup_env.py --agents`. This installs
the pinned Codex, Copilot and Playwright tools locally under
`training_runtime/node_modules` and downloads Playwright Chromium. Linux may
also need browser system libraries (`node training_runtime/node_modules/playwright/cli.js install-deps chromium`).
These are host tools; a Python virtual environment isolates Python packages.

```text
abb login codex
abb login copilot
abb prepare fw1 demo
abb agent codex --workspace work/fw1-demo
```

Complete the displayed login flow with your approved account. Credentials stay
in the ignored `.auth/` directory. Normal provider approvals apply. Run a real
harmless tool command to verify account/model access; login alone is insufficient.
The offline doctor checks installed Python packages, host tools, compilation and
clean preparation. Missing optional tools are BLOCKED; accounts and browser
execution remain separately UNTESTED until exercised.

## Prepare, resume and export

With `.venv` activated, run commands from the package folder:

```text
abb prepare fw1 demo
abb shell --workspace work/fw1-demo
```

The second command opens a shell in your prepared workspace. Run `pwd` (PowerShell:
`Get-Location`) to verify its location. `exit` returns to the package folder.
Reopen existing work with the same `abb shell` command; preparation refuses an
existing name. Use `--name another-attempt` for fresh work. All six labs are
available: `fw1`, `fw2`, `hw1`, `hw2`, `t1`, `t2`, with `demo` or `transfer` cases.
Keep the same agent/model throughout each lab and transfer comparison.

Work lives in `work/`, CI evidence in `runs/`, and exports in `export/`. For several
participants, use a separate checkout/package folder per participant. The
[handbook](docs/ABB_Workflow_Training.pdf), student guides and team walkthroughs
provide exercise instructions. Source starters intentionally contain unfinished
or faulty behavior; edit prepared copies.

```text
abb export --output export/submission.zip
```

Exports omit authentication state, `.env`, Git metadata and caches. Inspect code
and evidence before submitting. Starting or stopping a shell preserves your work.

## Browser labs

In Terminal A, activate `.venv`, enter the prepared T1/T2 workspace with `abb shell`
and run `python server.py`. In Terminal B, activate the same environment and enter
the same workspace, then run:

```text
python -m pytest browser_preflight.py -q
python -m pytest -q
```

Open `http://127.0.0.1:8765` for a local preview. Stop your server with Ctrl-C before
switching workspaces; one server owns port 8765 at a time. Optional environment
variables `CHROME_BINARY` and `CHROMEDRIVER` select explicit local executables.

## Facilitators

Use the facilitator package for assessment and publication sources. Learner
archives and the PDF attachment omit instructor and solved validation sources.
After setup and activation:

```text
python -m pytest tests/runtime -q
python -m unittest discover -s training_ci/tests -v
python training_author/check_materials.py
```

See [publication instructions](training_author/README.md), the
[CI guide](COPILOT_ACTIONS_GUIDE.md) and [local validation](docs/validation/virtual-environment.md).
Dependencies are pinned in `requirements.lock` and `training_runtime/package-lock.json`.
Rerun setup after updates and verify relevant labs before release. Historical
validation records describe earlier runtimes and remain unchanged.
