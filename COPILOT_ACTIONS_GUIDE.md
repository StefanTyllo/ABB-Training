# CI and Copilot rehearsal

Install Python 3.11+, Git and host GCC, run `python setup_env.py`, then activate
`.venv`. Deterministic checks run locally in the same environment as training:

```text
python -m pytest tests/runtime -q
python -m unittest discover -s training_ci/tests -v
python training_kit/firmware/instructor/smoke.py
python training_kit/test_team/author_checks/check_server.py
```

The current lightweight test workflow installs `.venv` and uses mocked agent
invocations for context interface tests. Its Codex report generation is separate
from deterministic tests and needs the configured account secret. Other active
workflows are defined in `.github/workflows/`; historical validation records do
not establish acceptance of the current runtime.

For a real local Copilot rehearsal, install Node.js 22+ and run
`python setup_env.py --agents`. Provide a private token file named `copilot_token`
in `.auth/secrets/`, or point `ABB_SECRETS_DIR` to a private directory containing
that file. Never commit or upload that directory. The agent imports the token
through stdin into a temporary profile per invocation.

```text
python -m training_runtime.ci --provider copilot -- python training_ci/run_lab.py fw1
python training_ci/grade_all.py fw1
```

Run grading separately without provider token environment variables or access to
secret files. Local virtual environments isolate Python dependencies; independent
OS accounts/filesystem permissions provide isolation for credentials and grading.
Evidence defaults to `runs/`; `ABB_RUNS_DIR` can select a different output location.

Each rehearsal performs all four teaching stages and both transfer conditions.
Record actual provider/model identity, stage transcripts and assessment outcomes.
The 600-second outer stage timeout and engineering acceptance contracts remain.
Do not treat mocked tests, version output or prior runtime records as live
provider or classroom acceptance. See `training_ci/README.md` for context delivery.
