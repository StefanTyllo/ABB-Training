# Measured author verification — 2026-10-14

- PASS: `python author_checks/check_server.py` verified all three real HTTP server variants: normal persistence; acknowledged save without persistence; rejection of valid endpoint 65535. Also verified invalid 0/65536 and fixture reset. This checks backend behavior only.
- PASS: Python compilation; all four prepare combinations; refusal to overwrite existing output; pytest collection (T1: two tests, T2: one test). Selenium 4.29.0 and pytest 8.3.5 were installed successfully for the checks.
- BLOCKED: actual Selenium browser execution. The final launch downloaded Chrome/ChromeDriver but returned `SessionNotCreatedException: Chrome instance exited`. T1 result was **1 setup error, 1 skipped**, not a pass. An earlier attempt failed in Selenium Manager while preparing its temporary directory. No simulated DOM was substituted and no browser sandbox was disabled.
- NOT VERIFIED here: rendered UI behavior, Selenium waits, expected starter passes, or strengthened tests catching both mutants in a real browser. `browser_preflight.py` is supplied for an actual-browser preflight; it is not a completed browser verification claim.

Teaching readiness remains conditional: on the teaching machine run the README browser preflight, baseline starter tests, and requirement-based reload/boundary tests against all three variants. T1's learner placeholder is intentionally skipped until implemented. Learners must still perform the handbook's guided work and derive their own tests; this starter does not ship a finished solution.
