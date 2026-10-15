# Targeted T1 feedback refinement

This seed copies the application, POM, tests and automation from the measured T1 transfer-code submission. It excludes prior state, evidence and caches. Existing automation documentation describes that earlier submission; new measured results belong under evidence/refinement-*.

Dispatch `.github/workflows/refine-browser-feedback.yml`. It uses Node 22, Python 3.12, Copilot 1.0.97 and runner Chrome. The existing COPILOT secret is mapped to COPILOT_GITHUB_TOKEN only for the agent step. Copilot has 900 seconds; the job has 25 minutes. Independent grading runs in a separate token-free step with existing grading unchanged, plus narrow browser identity/retained-PNG/extra-case checks. The t1-refined artifact contains the resulting workspace and protected-input snapshot.

This is a targeted scripted refinement of known feedback, not a fresh transfer comparison or learner pilot. Syntax and seed inventory were checked locally; the live workflow is the browser/agent verification.
