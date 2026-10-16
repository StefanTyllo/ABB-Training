# Supplied T1 browser support

This bootstrap is infrastructure supplied by the facilitator. It creates no
learner POM, tests or `automation/` directory. Run `python setup_env.py --agents` and activate `.venv` to install dependencies
and Playwright Chromium.

Inside the prepared T1 workspace, with its server running in another
terminal using the same virtual environment:

```bash
node tools/session_bootstrap.mjs --mode no-login --url http://127.0.0.1:8765 --state .auth/state.json --report evidence/bootstrap.json
```

The state belongs only to this workspace. `abb agent` configures local stdio MCP
tools and loads it into a fresh isolated context. No-login state proves fixture
access; it is not authenticated handover and does not authenticate Selenium.
Login mode returns BLOCKED until a reviewed adapter is supplied. Keep `.auth/`
out of Git, exports and transfer copies. Only copy the requested workflow or
learner automation into transfers.
