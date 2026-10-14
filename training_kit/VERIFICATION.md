# Author verification record

Date: 2026-10-14. Host Python 3.12; GCC available. This record concerns the supplied fixtures and document, not measured agent performance.

Passed:
- Uniform prepare_lab.py: all twelve lab/case combinations prepare successfully; existing output is refused; instructor directories are excluded.
- Firmware: demo and transfer device behavior; invalid parameter/value preservation; seeded parser defects reproduced; isolated corrected source passes 50 stream cases and malformed-input checks. Learner source remains deliberately broken.
- Hardware: five unittest methods covering four case preparations, overwrite refusal, calibration generation/provenance, invalid-input preservation, independent acceptance and false-assessment rejection.
- Test team: three HTTP contract variants; case preparation; overwrite refusal; pytest collection; Python/JavaScript syntax. See test_team/VERIFICATION.md for details.

Not passed or not performed:
- Real Selenium browser startup failed in the author environment with SessionNotCreatedException (Chrome exited). Browser behavior and improved learner-suite mutation detection are NOT verified here. Run the supplied browser_preflight.py and the PDF facilitator rehearsal on training machines before delivery.
- No authenticated Codex or Copilot request was executed. The author environment had neither CLI authenticated. Official setup instructions were verified against documentation; participants must pass the real smoke tests.
- No GitHub Actions run was executed. Account entitlements, organization policy, repository access, and live CI readiness remain local acceptance gates.
- No representative learner pilot or formal classroom acceptance was performed.

Do not describe these fixtures as classroom-accepted until the PDF readiness/rehearsal gates have actual recorded evidence. A correctly reported engineering fail or blocked result may be an accepted training outcome.
