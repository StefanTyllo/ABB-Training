# Virtual environment migration validation

The local runtime uses Python 3.11+, an editable `abb-training` installation in
`.venv`, hash-pinned Python requirements and optional locally installed Node tools.
Docker/Compose files and image-specific tests have been retired. Historical
Docker validation records describe earlier releases only.

Run `python setup_env.py`, activate `.venv`, and execute:

```text
python -m pytest tests/runtime -q
python -m unittest discover -s training_ci/tests -v
python -m unittest discover -s training_kit/hardware/tests -v
python training_kit/firmware/instructor/smoke.py
python training_kit/test_team/author_checks/check_server.py
python training_author/check_materials.py
abb doctor --offline
```

The portable suite covers all lab/case preparation, workspace names with spaces,
overwrite protection, export exclusion, local MCP paths, package audience
separation and the embedded handbook attachment. Browser/agent availability is
reported separately from deterministic checks. Run T1/T2 browser preflight with
a local server and a real provider tool call for full workstation acceptance.
Windows PowerShell and WSL need separate virtual environments and acceptance.
