# Docker training verification — 15 October 2026

The Docker implementation and offline distribution are ready for review. **Classroom release acceptance remains incomplete:** live provider rehearsals, FW1 live refinement and the native Windows Docker Desktop check have not passed. No live model result is inferred from deterministic checks.

## Candidate and provenance

Implementation source: `569f5bb43863ef9666b3959aa127337fb71fae67`, branch `plan/docker-training`.

Final facilitator image: `sha256:b96aab6ccbab5bc53e7cbde383d0207070dde5d21172914f594f55e0fec16a84`.

Final learner image: `sha256:5e49aaf714eccd6bf2aefd5cfd0132486919834dd6ef066b9107debd1d41c5ce`.

The structured manifest and retained logs are in `validation_records/docker-training-2026-10-15/` in the implementation checkout. The manifest records lock hashes, engine identity, browser capabilities, previous regression image identity and publication hashes. This report is included in both distribution archives; raw facilitator evidence is retained separately in the checkout. Evidence/report files are excluded from the image context to avoid a self-referencing image identity. The final record commit adds evidence and ignores generated distribution output; it does not change executable training inputs.

Reference host: Ubuntu 26.04 on WSL2, Linux x86_64 kernel 6.6.114.1, Docker Engine 29.6.2, Compose 5.3.1. This verifies a Linux Engine on WSL2, not native Docker Desktop acceptance. ARM was not tested.

## Results

| Check | Outcome | Evidence |
|---|---|---|
| Final offline container suite | 59 passed | `release-suite.log`, exit 0 |
| Hardware starter checks | 5 passed on disposable writable copy | `release-starters.log` |
| HTTP server contracts | correct, no-persist and bad-boundary passed | `release-starters.log` |
| Firmware instructor smoke | FW1 demo/transfer; starter defects retained; 50 corrected protocol cases passed | `release-firmware.log` |
| T1 retained complete package | Accepted; 13 automation self-tests, actual Chrome tests, timeout evidence | `final-t1.log`, exit 0 |
| T2 retained complete package | Accepted; 16 automation self-tests, actual Chrome, both mutants and protected-input checks | `final-t2.log`, exit 0 |
| Learner archive without Git metadata | Built and exercised from a path containing spaces | `standalone-build.log`, `guide-commands.log` |
| Documented exercise entry commands | All 18 demo/MD/code entries; T1/T2 separate terminal processes; resume/export passed | `guide-commands.log`, exit 0 |
| Persistence and isolation | Stop/start/rebuild retained work; two projects isolated synthetic auth and work | `final-persistence.log`, exit 0 |
| Learner image layers | No facilitator/assessment source in any final layer | `release-layers.log` |
| CI boundary | Child exit 7 preserved; synthetic credential scoped to rehearsal; fresh grader had none; saved image loaded with same ID | `task-5-host.log` and container suite |
| PDF and distribution | 43 pages; all page contact sheets visually inspected; exactly one current starter attachment; reproducibility/allowlist checks passed | `final-handbook.log`, package tests |
| Live Codex and Copilot account smoke | BLOCKED: approved credentials unavailable | No provider call made |
| Six-lab live rehearsal, 18 submissions | NOT RUN; target remains 18/18 | No accepted count or model identity claimed |
| FW1 provider refinement and live aborted-agent cleanup | NOT RUN; account gate remains incomplete | Offline process/server cleanup is tested separately |
| Native Windows Docker Desktop | BLOCKED: desktop-linux engine pipe absent | `windows-native-version.log` |
| Classroom learner pilot | NOT RUN | Remains a release check |

T1/T2 and the 58-test pre-review suite ran on frozen source `157a41c81eb1b78b6c4baef202124b1b29cee563`, facilitator image `sha256:0000e8bfa7cfe253e16985bbc264df7feeccfb6bbf7df703a9d65ab6a7771138`. The final source differs only in the shared CI build workflow and its regression test: it now gates image export on credential-free offline acceptance. Runtime, browser wrappers, seeds, graders and training materials are byte-identical across those two revisions. The final image passed the full 59-test suite; the actual T1/T2 logs retain their original image provenance. No live rehearsal is reused or claimed.

The standalone learner build and exercise command checks used a restricted host executable path exposing Docker only. Python, Node, GCC and browsers ran inside the image. This tests the Docker-only host route on the reference Linux environment; it does not substitute for Windows PowerShell execution. Occupied-port refusal, caller-owned server preservation, namespace sandboxing, browser failure evidence, dynamic fields, saved-state restoration and copied-file permissions were exercised with actual processes.

## Runtime and assessment integrity

Pinned runtime: Python 3.12.15, Node 22.23.3, Codex CLI 0.162.1, Copilot CLI 1.0.97, Chrome/ChromeDriver 155.0.8059.79, Selenium 4.29.0, pytest 8.3.5, Playwright 1.64.1 and Playwright MCP 0.0.83. MCP's published dependency is Playwright `1.64.0-alpha-1790635538000`; both browser paths were exercised separately. Complete package/OS versions and hashes are retained in the manifest and lock files. Runtime acquisition is pinned by base digest, Debian snapshot, download hashes, pip hashes and npm integrity.

Browsers run with namespace and seccomp sandboxing as the non-root learner. Normal Codex workspace-write approval settings remain enabled. Offline Codex process/sandbox checks do not establish model entitlement. No host credential directory, Docker socket, privileged mode or approval bypass is required. Export and CI collection remove environment files, provider/browser state, caches and Git metadata; synthetic leak tests also inspect learner image layers.

The main rehearsal remains Copilot with its existing 600-second limit and independent 900-second T2 grading limit. Protected browser/firmware seeds, fixtures and grading authorities are unchanged. Expected engineering FAIL/BLOCKED reports remain meaningful. Historical host-based results, including the older Codex 15/15 experiment and prior Copilot run, remain historical and are not Docker acceptance. CLI, browser wrapper and Python versions differ from historical runs, so their outcomes cannot establish equivalence without the pending live baseline.

## Decisions and final review

The implementation was reviewed by its author against the plan, source diff, credential boundaries, default commands, evidence handling and publication contents. No subagents or independent reviewer were used, following the user's instruction. The review found and corrected lower-layer assessment leakage, unwritable copied seed files, stale PDF attachments, unsanitized CI collection, empty collection handling, unsafe configuration symlinks, misleading readiness diagnostics, TIME_WAIT port refusal and the missing CI offline gate. RED and GREEN evidence is retained where applicable. An independent review remains a practical limitation of this review method.

Recorded implementation rulings:

1. Use the pinned CLI's verified `codex sandbox -- COMMAND` syntax; its help does not support the planned extra `linux` argument. Cost: the probe is specific to the pinned CLI contract.
2. Add `mount`, `umount2` and `pivot_root` to the reviewed Playwright namespace profile for normal Codex bubblewrap operation. Cost: additional permitted system calls; the non-root outer container and other restrictions still apply.
3. Preserve MCP's published alpha Playwright dependency separately from stable 1.64.1. Cost: two wrapper versions require separate actual browser verification.
4. Normalize owner-write permissions on prepared copies. Keep image materials root-owned and remove group/other writes, allowing ordinary copy operations to produce writable learner files. Cost: source immutability relies on the specified non-root role; source bytes and protected hashes remain unchanged.
5. Use author self-review because subagents were explicitly prohibited. Cost: no independent reviewer.
6. Retain reference-package results on their exact frozen image after the final CI-only change, with unchanged runtime/grader/seed inputs and a fresh full suite on the final image. Cost: those reference executions are not executions of the final image ID itself; their provenance is explicit above.

The learner distribution omits assessment sources and all repository history. The facilitator distribution contains independent graders. Original user PDF/PPTX files in the primary checkout were preserved; the updated handbook PDF was generated in this isolated worktree. The current supplied slide deck contained no PDF page anchors requiring edits, so no changed slide deck is shipped.

## Remaining release gates

Provide approved accounts and run both real-provider smoke checks with actual model identity recorded, then freeze the candidate and perform the six-lab live rehearsal plus fresh credential-free grading. Run the FW1 refinement sequence separately and preserve actual evidence, including failures. Complete live interruption cleanup, native Windows Docker Desktop/PowerShell acceptance and a representative learner pilot. Reassess affected results if runtime or training sources change. Registry publication, PR/merge and learner-volume deletion remain separate actions.
