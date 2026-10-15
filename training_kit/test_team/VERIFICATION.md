# Test-track verification — 14 October 2026

## Fixture checks

The stdlib HTTP author check passed all three application variants, normal persistence, deliberately missing persistence, the deliberately rejected valid endpoint 65535, invalid 0/65536 and reset behavior. Python compilation, four case preparations, overwrite refusal and initial pytest collection passed. Selenium 4.29.0 and pytest 8.3.5 installed successfully.

The initial author Chrome launch returned SessionNotCreatedException (one setup error and one skipped placeholder). This was recorded as blocked, not passed. Subsequent GitHub-hosted Chrome execution below resolves browser evidence for that environment. Do not disable the browser sandbox to work around a local startup failure.

## Real-browser Copilot rehearsals

Initial six-lab run: https://github.com/StefanTyllo/ABB-Training/actions/runs/38592278866

T1: real Chrome 154.0.8037.97 and independent semantic checks passed for demonstration, MD-only transfer and code-assisted transfer. Generated helpers were actually invoked. A follow-up added retained missing-element screenshots, browser capabilities, empty-password rejection and invalid-save non-overwrite. Its seed initially omitted four helper-test XML files; restoring the exact originals produced a complete package with 13 helper tests and eight browser tests passing, plus independent semantic verification.

T1 refinement: https://github.com/StefanTyllo/ABB-Training/actions/runs/38595251454
Complete T1 package: https://github.com/StefanTyllo/ABB-Training/actions/runs/38596385772

T2: demonstration and MD-only transfer passed independent checks. The code transfer's direct suites recorded 12 correct passes; eight relevant assertion failures for no-persist; three for bad-boundary; no errors or skips. Its helper also passed the correct app. The outer 300-second grader timed out while repeating the three variants through the learner runner, leaving final reports incomplete. The unchanged package passed the complete 900-second-limit regrade, including 16 helper self-tests, all 12 correct-app browser tests, relevant assertion failures for both mutants, helper execution and protected-input hashes. Regrade: https://github.com/StefanTyllo/ABB-Training/actions/runs/38597697875

Actual Copilot invocations and byte-identical transfer helpers were checked. All 16 T2 helper self-tests and referenced fixtures were present. The generated defect phase label is heuristic: the valid 65535 rejection fails at Save before reload. Review the recorded assertion, not the heuristic label alone.

See ../VERIFICATION.md and the repository validation_records archives for provenance. Learners still derive their own tests from REQUIREMENTS.md; these starters do not ship the finished solutions. Run browser_preflight.py on every teaching machine. A facilitated learner pilot and authenticated Codex execution remain unperformed.
