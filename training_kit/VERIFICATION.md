# Author verification record — 14 October 2026

This record distinguishes fixture checks, authenticated agent rehearsals, and classroom acceptance. All exercises use synthetic inputs.

## Fixture and packaging checks

- All twelve prepare_lab.py combinations prepared successfully; overwrite was refused; instructor directories were excluded.
- Firmware: device cases and invalid-input preservation checked; seeded parser defects reproduced; an isolated correction passed 50 stream cases and malformed-input checks. The learner starter remains deliberately broken.
- Hardware: case preparation, provenance, calculation generation, invalid-input preservation, independent acceptance and false-assessment rejection passed.
- Test: all three real HTTP variants, preparation, overwrite refusal, collection and syntax passed. The initial local Chrome launch failed; later hosted real-browser execution supersedes that environment limitation, not the requirement to preflight teaching machines.
- PDF: pages visually reviewed; embedded ZIP extracted and all twelve clean workspace preparations exercised. This attachment contains starters, not the completed agent solutions.

## Authenticated Copilot rehearsal

Repository: StefanTyllo/ABB-Training; branch training/workflow-labs. Ubuntu Actions runner, Node 22, Python 3.12.15, Copilot CLI 1.0.97. The secret COPILOT was mapped to COPILOT_GITHUB_TOKEN only for agent steps. Independent grading ran without that token. Default model identity was not pinned or captured.

Initial run: https://github.com/StefanTyllo/ABB-Training/actions/runs/38592278866
Commit: e36498d5e48667077444be81c6061a6dacd11bd6

Each lab received four scripted stage invocations and separate fresh MD-only/code-assisted transfers. These approximate the handbook process; they are not a facilitated human conversation or a controlled performance experiment.

- FW2: all three submissions passed; actual code helper execution and 50-case independent parser checks verified.
- HW1: demo passed; both transfers correctly blocked on missing revision without changing the export.
- HW2: demo passed; both transfers correctly reported the unsafe idealized divider design. Hardware helper self-tests initially used demo-specific assumptions and were made independent during transfer.
- FW1: initial final-state grades passed, but transcript review found manual fallback after a denied compound command. A fresh code transfer fixed raw capture retention and used the helper for the mutation. Eighteen helper tests, before/after captures and rerun preservation passed: https://github.com/StefanTyllo/ABB-Training/actions/runs/38594335199
- T1: initial real Chrome runs passed. Follow-up retained failure screenshots, captured actual browser identity, added empty-password rejection and invalid-save preservation: https://github.com/StefanTyllo/ABB-Training/actions/runs/38595251454 . Four original XML fixtures omitted from its seed were restored. Complete package passed 13 helper tests, eight browser cases and the independent semantic oracle: https://github.com/StefanTyllo/ABB-Training/actions/runs/38596385772
- T2: demo and MD-only transfer passed. Code transfer's 300-second outer grader limit expired after its direct browser suites passed; the original run remains failed. The unchanged package passed the complete 900-second-limit regrade, including 16 helper self-tests, all 12 correct-app browser tests, relevant assertion failures for both mutants, helper execution and protected-input hashes. Regrade: https://github.com/StefanTyllo/ABB-Training/actions/runs/38597697875

The repository's validation_records directory preserves exact original archives, follow-ups and SHA-256 hashes. Read original failures alongside corrections. A heuristic T2 failure-phase label is explicitly marked for human review; the 65535 Save rejection occurs before reload, despite the demo report's heuristic label.

## Not established

No representative learner pilot was performed. Production hardware, comprehensive adversarial robustness, learning improvements and speed/cost advantages are not established. Local account/browser readiness and the handbook's facilitator pilot remain required before classroom acceptance. A correctly reported engineering failure or blocked input is an accepted lab result.

## 15 October 2026 — Copilot prompt/context delivery update

The active handbook and setup now consistently use GitHub Copilot CLI. Focused
stage/replay templates preserve the full original task card and local contracts;
exact prompt/context snapshots and delivery hashes are retained. Regression checks
cover all six actual cards, four stages and two transfer modes, including hardware
without case.json, source preservation, Copilot isolation and timeout metadata.
The PDF is rebuilt with the current starter files and an exact-content manifest.
These are token-free implementation/material checks, not new authenticated
Copilot outcome measurements. The historical authenticated runs above remain
unchanged. New agent/model performance, authenticated handover and learner
outcomes require their own rehearsals and facilitator review.
