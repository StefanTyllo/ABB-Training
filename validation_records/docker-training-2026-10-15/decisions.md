# SDD ledger — plan: docs/superpowers/plans/2026-10-15-docker-training.md

Task 1: in progress; base 15d4ad841b876918d4a4afd582de66b191b6787a.
Tasks 2–7: pending runtime feasibility gate.

Pre-flight interfaces:
- 1 → 2/4/5/6/7: stable runtime paths, image targets, locked binaries, sandbox profile; consistent.
- 2 → 3/4/6/7: /workspace work/runs/export and validated CLI workspace paths; consistent.
- 3 → 4/5/6/7: preparation and ABB_RUNS_DIR, loopback server with explicit preview binding; consistent.
- 4 → 5/6/7: scoped provider auth and supplied T1 tools (not automation); consistent.
- 5/6 → 7: same final candidate image, packaged documentation and independent grading; consistent.
Ruling: use author self-review for final review because the user explicitly requested no subagents — honors direct instruction — cost if wrong: no independent reviewer.

Initial host probe: Docker 29.6.2 / Compose 5.3.1, linux/amd64, WSL2 kernel 6.6.114.1. Default seccomp denies unshare with EPERM; Playwright namespace profile permits non-root user/PID namespace creation. This is a precursor only, not browser/Codex acceptance.

Task 1: Ruling: pinned Codex 0.162.1 uses `codex sandbox -- COMMAND` (CLI help verified); update probe accordingly — cost if wrong: probe invocation needs correction.
Task 1: Ruling: extend Playwright seccomp allowlist with mount/umount2/pivot_root for nested bubblewrap namespace operations, preserving non-root outer container without CAP_SYS_ADMIN — cost if wrong: larger syscall surface.
Task 1: Ruling: npm metadata shows MCP 0.0.83 depends on Playwright 1.64.0-alpha-1790635538000, while supplied bootstrap pins 1.64.1; preserve both published dependency trees and disclose versions, rather than override MCP internals — cost if wrong: browser behavior may differ and requires separate real MCP validation.
Baseline note: existing hardware test_starters.py has 5 errors against a read-only source mount because it creates temporary folders beside its source. Final regression checks must run a disposable writable source copy; do not present this as a passing baseline.
Task 1: complete (commits 15d4ad8..b3e24fe, tests: docker run --rm --init --network none --security-opt seccomp=docker/seccomp.json --shm-size=1g abb-training-facilitator:dev python -m pytest /opt/abb/repo/tests/container/test_image.py -q -p no:cacheprovider → 5 passed in 4.65s)
Task 2: complete (commits b3e24fe..35301f0, tests: docker run --rm --init --network none --security-opt seccomp=docker/seccomp.json --shm-size=1g abb-training-facilitator:dev python -m pytest /opt/abb/repo/tests/container/test_workspace.py -q -p no:cacheprovider → 4 passed in 11.20s)
Task 2: host smoke passed from a Docker-copied package with spaces and no .git; restart/rebuild preserved bytes and isolated project volumes.
Task 3: Ruling: copying image read-only modes made prepared copies unwritable; normalize owner-write bits on copied files/directories in common, T1 and hardware preparation before further writes — source bytes and modes stay unchanged — cost if wrong: permissions on learner copies differ from source.
Task 3: complete (commits 35301f0..b9e7191, tests: docker run --rm --init --network none --security-opt seccomp=docker/seccomp.json --shm-size=1g abb-training-facilitator:dev python -m pytest /opt/abb/repo/tests/container/test_portability.py -q -p no:cacheprovider → 15 passed in 9.24s)
Task 4: live provider calls BLOCKED: no approved provider credentials are present in session; continue offline implementation and retain this acceptance gap.
Task 3: host preview passed on loopback port 28765; a second publisher was refused and the original app remained reachable. T1 and T2 existing validation packages both accepted with source read-only and separate ABB_RUNS_DIR roots.
Task 4: offline implementation complete: 9/9 actual auth/bootstrap/MCP/browser tests pass, including sandbox status, dynamic fields, saved-state restoration and symlink rejection. Live provider acceptance remains BLOCKED (no credentials); no model access is claimed.
Task 5: complete (commits 3685682..859742b, tests: docker run --rm --network none abb-training-facilitator:dev python -m pytest /opt/abb/repo/tests/container/test_ci.py -q -p no:cacheprovider → 8 passed in 0.26s)
Task 5: Docker host integration passed: synthetic sentinel present only in rehearsal process, absent from fresh credential-free grader; child exit 7 propagated; image archive saved, hashed and loaded with the same immutable ID.
Task 6: integrated current user handbook + six draft files (input SHA-256 in draft-inputs.json). Original PDF/slides untouched. Current user slide relationships have no PDF page anchors requiring changes.
Task 7 follow-up: test serial rehearsal server restart; pre-bind probe currently lacks SO_REUSEADDR and may mistake TIME_WAIT for an occupied listener. Resolve before freezing candidate.
CI follow-up: direct artifact copying could retain .auth/.env from browser workspaces. New collect_evidence regression failed because collector was absent; route collection through export_workspace sanitizer, preserving failure files and raw grading inputs in the private run volume.
Task 6 follow-up: rerender the PDF starter attachment after runtime-file changes (collect.py and auth config guard), then rebuild distribution manifests.
Task 7 early regression: serial server restart failed with a false occupied-port error while SO_REUSEADDR bind succeeded. Match the HTTPServer reuse policy in the availability probe; keep refusal of a real caller-owned listener.
Image-layer regression RED: docker-save inspection recovered five instructor/author-check files from the learner COPY layer even though final paths were deleted. Fix by copying sanitized materials from a discarded build stage into a fresh runtime-derived stage. Share docker/material_manifest.py with both package and PDF assembly; inspect every final learner layer before acceptance.
Windows target: native Windows Docker CLI 29.8.1 exists, but desktop-linux engine pipe dockerDesktopLinuxEngine is absent. Docker Desktop acceptance is BLOCKED/unverified; active reference engine is Ubuntu 26.04 Linux Engine on WSL2. Do not claim native Windows Docker Desktop or ARM passed.
Baked-seed regression: both T1/T2 package checks failed to create evidence after copytree preserved removed owner-write bits from the source image. Ruling: keep source root-owned and remove only group/other writes (go-w), so learner UID remains unable to edit sources while normal copies retain owner-write permission — consistent with the non-root image contract — cost if wrong: source immutability relies on the required non-root role. Protected source bytes/hashes stay unchanged.
