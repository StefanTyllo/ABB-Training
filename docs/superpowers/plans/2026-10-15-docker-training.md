# Docker Training Environment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a Docker package in which both agents and all six training exercises run without host Python, Node, compiler, browser or user-specific paths.

**Architecture:** One locked Linux runtime, with learner and facilitator targets, started through Docker Compose. Agents, application and browsers share the learner container; named volumes preserve work and isolate provider authentication. Keep existing lab and grader semantics, adapting output locations rather than converting the main harness to Codex.

**Tech Stack:** Docker/Compose v2, Linux amd64, Python 3.12, Node 22.23.3, GCC, Chrome for Testing/ChromeDriver, Selenium 4.29.0, pytest 8.3.5, proposed published Codex 0.162.1, Copilot 1.0.97, Playwright 1.64.1, Playwright MCP 0.0.83, pypdf 6.10.0.

**Spec:** [Docker training design](../specs/2026-10-15-docker-training-design.md).

## Global Constraints

- Both coding agents and exercises run inside Docker; host requirements are Docker/Compose, the package and account/network access.
- Support `linux/amd64` first. Validate Windows Docker Desktop/Linux containers and Linux Engine; do not claim ARM compatibility before testing it.
- Preserve six labs, demo/transfer inputs, teaching-stage order, immutable authorities, meaningful engineering FAIL/BLOCKED results, independent grading and historical evidence.
- Keep main `training_ci/run_lab.py` on Copilot; no Codex conversion, global executable impersonation or implicit model substitution. Codex uses `gpt-6.1-sol` / medium for recorded rehearsals.
- Keep the 600-second stage timeout and 900-second T2 grading allowance. Do not hide an early stop or equate agent exit with acceptance.
- Non-root, normal approval controls and actual browser sandboxing. No Docker socket/host home mounts, privileged mode, host networking or automatic unsafe fallback.
- Image-owned dependencies and fixed internal paths; no host cache paths, ordinary runtime package downloads or venv activation.
- Named workspace/run volumes survive normal stop/rebuild. Provider auth volumes are separate; grading gets neither provider secrets nor auth mounts.
- No image ARG/ENV containing credentials; no credentials/auth state in source, exports, PDF attachments, images or ordinary reports.
- Original checkout has user-edited guide/PDF/slides and six student-guide drafts. Preserve those edits and use their current approved versions when implementing documentation.
- Baseline for this plan is main `4ba6e36`; the earlier `b907bb8` experiment and its archives are historical, not container results.
- Plan only in this request. Do not execute the steps below until the user approves implementation.

## Review Focus

1. Windows paths with spaces and a downloaded ZIP without `.git`: Docker-only commands must work; no hidden host Git/Bash/UID assumption. Tested in Tasks 2 and 6.
2. Docker hosts blocking nested agent/browser namespaces: useful BLOCKED diagnostics, never silent sandbox/approval bypass. Gate in Task 1; actual checks in Task 4.
3. Interrupted execution, restart/rebuild and reused workspace names: preserve originals and report occupied ports; stop only owned children. Tasks 2, 3 and 7.
4. Credentials leaking through auth volumes, rendered Compose output, image history or exported evidence: unattended execution mounts only the selected provider credential; grading/export excludes them. Tasks 4, 5 and 6.
5. Teaching artifacts diverging from the executable package: current drafts, handbook, embedded ZIP and commands must agree; intentional starter defects remain. Tasks 3, 6 and 7.

## File structure and responsibilities

| Files | Responsibility |
|---|---|
| `Dockerfile`, `.dockerignore`, `.gitattributes`, `compose.yaml`, `compose.learner.yaml`, `compose.preview.yaml`, `compose.auth.yaml` | Locked build targets, persistent services, optional loopback-only preview and runtime secret profile |
| `docker/runtime.lock.json`, `docker/requirements.in`, `docker/requirements.lock`, `docker/package.json`, `docker/package-lock.json` | Exact runtime versions, artifact checksums and transitive dependency locks |
| `docker/seccomp.json`, `docker/codex.toml`, `docker/copilot-mcp.json` | Reviewed container namespaces and agent-local configuration templates |
| `docker/abb`, `docker/launcher.py`, `docker/doctor.py`, `docker/auth.py`, `docker/export.py` | Small launcher, factual readiness checks, auth process setup and sanitized exports |
| `training_ci/runtime_paths.py` | Shared output-root selection, retaining existing defaults |
| Existing prepare/server/CI/validation wrappers | Minimal portable output/Git/server-binding changes; no task-answer or grading-criterion changes |
| `training_kit/test_team/support/session_bootstrap.mjs`, `support/README.md`, `support/.env.example` | Missing supplied T1 bootstrap, separate from learner-generated automation |
| `tests/container/test_{image,workspace,portability,agents,browser,ci,package}.py`, `tests/container/smoke.sh`, `tests/container/smoke.ps1` | Behavioral integration checks; credentialed checks explicitly opt in |
| `training_author/build_handbook.py`, `training_author/render_handbook.mjs`, `training_author/build_package.py` | Reproducible PDF/attachment and Docker distribution assembly |
| `README.md`, guide/track/student READMEs, `COPILOT_ACTIONS_GUIDE.md`, workflow YAMLs | One supported container path for learners, facilitators and CI |

## Task 1: Build the locked runtime and prove sandbox feasibility

**Files:** Create `Dockerfile`, `.dockerignore`, `.gitattributes`, `compose.yaml`, `docker/runtime.lock.json`, `docker/requirements.in`, `docker/requirements.lock`, `docker/package.json`, `docker/package-lock.json`, `docker/seccomp.json`, `compose.learner.yaml`, `tests/container/test_image.py`.

**Interfaces:** Consumes the versions/platform in the spec. Produces `learner` and `facilitator` image targets, stable tool paths and a runtime manifest. Development image tags are `abb-training:dev` and `abb-training-facilitator:dev`; grader uses the latter. Install `abb` on PATH and use a keepalive CMD for persistent services, leaving executable overrides available to `docker run IMAGE python ...`. Compose service names are `training`, `facilitator`, `grader`; facilitator/grader are opt-in profiles, not default learner services.

- [ ] Write integration probes `test_real_chrome_sandbox`, `test_codex_sandbox_shell`, `test_pinned_browser_driver_pair` and `test_offline_toolchain`. Assert non-root UID, a real dynamic-field browser interaction, matched binary versions, GCC execution and a working normal Codex sandbox shell without model access. Run probes against the first minimal image and retain the actual initial failures; do not infer browser readiness from version output.
- [ ] Resolve the Python 3.12 slim-bookworm base to an amd64 digest and exact patch; resolve a Chrome for Testing/driver pair and record both download hashes; verify Node 22.23.3 against its published checksum. Resolve a dated Debian package snapshot and record its timestamp plus installed OS package versions, so GCC/browser libraries do not drift through an unpinned apt repository. Write immutable values into the Dockerfile/lock manifest. Generate npm/pip locks inside a disposable container, including transitive integrity/hash data. Never guess digests or silently take another version when a pin is unavailable.
- [ ] Install both real CLIs, required browser OS libraries, sandbox tooling and the pinned runtime. Keep downloads at build time. Implement read-only material/source directories, user-writable temp/cache/home locations and separate learner/facilitator copies. Explicit `.dockerignore` excludes `.git`, `.env*` except examples, `.auth`, work/runs, caches, experiment/validation archives and user exports. Facilitator target includes validation seeds; learner target excludes them and instructor/author checks.
- [ ] Set LF line endings for `docker/abb` and shell scripts in `.gitattributes`; set executable permissions in the image. Configure non-root execution, `init: true`, `shm_size: 1gb` and the minimal reviewed namespace/seccomp profile. Set Chrome paths globally in the image; explicitly enable Chromium sandboxing in Playwright configuration.
- [ ] Build with `docker compose --profile facilitator build training facilitator grader`. Run `docker run --rm --init --network none --security-opt seccomp=docker/seccomp.json --shm-size=1g abb-training-facilitator:dev python -m pytest /opt/abb/repo/tests/container/test_image.py -q`. **Expected:** real offline tools and sandbox probes pass; image contains no host `/tmp/abb-*` paths. Keep this invocation consistent with the image user and Compose security settings.
- [ ] If normal Codex/browser sandboxing is blocked, record host/engine diagnostics and stop this runtime gate before expanding the image. Return the concrete incompatibility for a design decision; do not ship privileged/unsafe fallback defaults.
- [ ] Commit the passing image/locks/feasibility checks: `build: add locked Docker training runtime`.

## Task 2: Provide the classroom launcher, persistent work and exports

**Files:** Create `docker/abb`, `docker/launcher.py`, `docker/doctor.py`, `docker/export.py`, `tests/container/test_workspace.py`, `tests/container/smoke.sh`, `tests/container/smoke.ps1`; modify `compose.yaml`.

**Interfaces:** Consumes Task 1 image/tool paths. Produces `abb doctor [--offline]`, `abb prepare LAB CASE [--name NAME]`, `abb shell --workspace PATH`, `abb export --output PATH`, plus dispatch hooks for Task 4's `login`/`agent` subcommands. `prepare` defaults to `work/<lab>-<case>`. `doctor` emits `{status, checks, versions, workspace, image}` with PASS/FAIL/BLOCKED and exits 0/1/3 respectively; missing online checks are explicitly untested.

- [ ] Write in-image behavioral tests asserting fresh preparation succeeds, an existing name is refused without changing bytes, and an export includes code/evidence but excludes `.env`, `.auth`, provider state and caches. Include synthetic sentinel secrets, paths with spaces and a package with no `.git`. Add host-native Bash/PowerShell smoke drivers that use only Docker commands to assert restart/rebuild persistence and separate Compose-project volumes, asking the in-image checker to verify bytes. Do not require host Python or mount a Docker socket into a test container. Cleanup is restricted to explicitly disposable `abb-test-*` projects.
- [ ] Run `python -m pytest tests/container/test_workspace.py -q` inside the facilitator image before implementing the commands. **Expected:** missing launcher/subcommands or failed persistence/export assertions, not a claimed pass from an empty test selection.
- [ ] Implement `main(argv: list[str]) -> int` in `launcher.py`, `run_checks(offline: bool) -> dict` in `doctor.py`, and `export_workspace(root: Path, output: Path) -> dict` in `export.py`. Use `subprocess` argv arrays and container paths. Validate workspace names/paths remain under `/workspace/work`; refuse traversal and overwrites. Doctor performs disposable checks, not mutations of a learner's completed task.
- [ ] Use named volumes for `/workspace/work`, `/workspace/runs`, `/workspace/export` and separate provider auth. Add no automatic destructive reset. Export bundles are readable with `docker compose cp training:/workspace/export/learner-work.zip ./learner-work.zip`; normal `down` preserves volumes.
- [ ] Start `docker compose up -d training`; run doctor/prepare from a host path containing spaces; use two `exec` shells in the same service. Stop/start/rebuild and verify the recorded file hashes and export contents. **Expected:** persistence and sanitization tests pass with no host language tools. Docker/host integration tests run separately from the in-image Python checks and use the same named scenarios.
- [ ] Commit: `feat: add persistent container training commands`.

## Task 3: Make exercise and validation paths container-compatible

**Files:** Create `training_ci/runtime_paths.py`, `tests/container/test_portability.py`, `compose.preview.yaml`; modify `training_kit/prepare_lab.py`, `training_kit/test_team/scaffold/server.py`, `training_ci/run_lab.py`, `training_ci/grade_all.py`, `validation_browser/refine.py`, `validation_t1_package/check.py`, `validation_t2_package/check.py`, `validation_replay/run_fw1.py`, `validation_replay/check_fw1.py`.

**Interfaces:** `runs_root() -> Path` returns `ABB_RUNS_DIR` when explicitly set, otherwise the existing repository `runs/`. Compose sets `/workspace/runs`. Existing callers keep their current lab/subdirectory names. Server gains `--host` defaulting to `127.0.0.1`; only the optional preview flow selects `0.0.0.0`.

- [ ] Write integration checks preparing all six labs for demo/transfer from a read-only material tree into a writable root with spaces. Assert all twelve original cases/authority files match expected inputs, existing output is refused, missing inputs remain errors and hardware still does not require `case.json`. Exercise validation output relocation with source read-only and fresh run directories.
- [ ] Add tests that default server binding remains loopback, explicit preview binding serves the fixture through a loopback-only host port, occupied ports report failure, and app/variant cleanup never kills a caller-owned server. **Expected before implementation:** relocated outputs/preview path fail where unsupported.
- [ ] Implement shared run-root selection and replace every `ROOT/runs` output/sidecar use in the listed wrappers, including `t1-refined-protected.json`. Keep source/seed resolution relative to the source files. Preserve command interfaces, timeouts, provider choice and grader calculations. Do not edit immutable validation seeds or regenerate their hash manifests.
- [ ] Update preparation to initialize exercise-local Git metadata and ignore rules needed by the existing auth hygiene checks, without requiring an outer Git checkout. Add this before snapshotting protected inputs; do not create reusable learner `automation/` or pre-solve defects.
- [ ] Add explicit server binding and preview override. Default Compose exposes no ports. Preview publishes only `127.0.0.1:<chosen-host-port>:8765`; document exactly one active preview workspace. Keep variants on owned internal ports.
- [ ] Run the portability suite inside the image and the host/Docker preview scenario. **Expected:** twelve preparations, read-only source execution, occupied-port behavior and cleanup pass; starter defects remain demonstrable.
- [ ] Commit: `refactor: make lab execution paths portable in Docker`.

## Task 4: Containerize agent login, MCP and the supplied T1 bootstrap

**Files:** Create `docker/auth.py`, `docker/codex.toml`, `docker/copilot-mcp.json`, `compose.auth.yaml`, `training_kit/test_team/support/session_bootstrap.mjs`, `training_kit/test_team/support/README.md`, `training_kit/test_team/support/.env.example`, `tests/container/test_agents.py`, `tests/container/test_browser.py`; modify launcher/doctor, JS lock files and `training_kit/test_team/prepare.py`.

**Interfaces:** `abb login {codex,copilot}` uses that CLI's documented device login, storing auth only in its own volume. `abb agent {codex,copilot} --workspace PATH` enters the validated workspace and preserves ordinary approvals. Bootstrap CLI: `--mode {no-login,login} --url URL --state PATH --report PATH`; missing reviewed login adapter means BLOCKED, never fabricated auth. MCP uses baked stdio tooling and workspace-local state paths.

- [ ] Write tests for absent credentials, wrong workspace, empty/missing bootstrap parameters, non-secret status reporting, separate auth-volume paths, fresh per-workspace MCP configuration, state export/load, bad URL and useful sanitized element-failure evidence. A login-mode fixture without a configured adapter must be BLOCKED. Test startup cannot silently download Node packages or fall back to a host browser.
- [ ] Run those tests before adding commands/support. **Expected:** missing auth/MCP/bootstrap functionality. Keep real-provider tests explicitly opt-in; offline tests use synthetic sentinels and real local browser tools, not claimed model access.
- [ ] Implement `prepare_agent_process(provider: str, workspace: Path) -> tuple[list[str], dict[str,str]]` in `auth.py`. Construct a provider-scoped environment/config; mount only the selected provider secret in unattended mode, translate its documented format, and remove credentials from tool subprocess environment where supported. Never repurpose or mount the host's home. Keep existing account policy requirements visible.
- [ ] Install the supplied bootstrap in prepared T1 `tools/`, with dependencies already baked. It performs the existing fixture's no-login validation/export, not the learner POM/test solution. Generate agent MCP config from container templates, enable actual browser sandboxing and verify a fresh MCP context can use the state file. Never copy state to transfers or claim state applies to Selenium.
- [ ] Run real Selenium preflight and actual MCP navigation/dynamic-field/state checks against the local fixture. **Expected:** actual tool evidence, real browser capabilities and no extra `automation/` before Stage 4. Preserve FAIL/BLOCKED branches and do not equate no-login state with authenticated handover.
- [ ] With approved accounts, run each agent's harmless tool smoke in a disposable workspace. **Expected:** actual command event, image/workspace identity and CLI version; Codex records `gpt-6.1-sol`/medium. Verify a normal sandbox/approval path inside the container. Missing access is BLOCKED, with no substitute model or bypass flag.
- [ ] Commit: `feat: package agent access and T1 browser support`.

## Task 5: Run CI tools from the same image with independent credential-free grading

**Files:** Create `.github/workflows/build-training-image.yml`; modify all six `.github/workflows/{validate-workflow-labs,copilot-smoke-test,refine-browser-feedback,refine-fw1-replay,check-t1-package,check-t2-package}.yml`, `compose.yaml`; create `tests/container/test_ci.py`.

**Interfaces:** Host Actions runner performs checkout, Docker build/run and artifact upload. A reusable build job builds once, exports a content-verified image artifact and image ID, and matrix jobs load that artifact; avoid rebuilding/downloading tools independently in six lab jobs. Actual training/validation code runs in the image. Rehearsal and grader use the same immutable image ID and `/workspace/runs`; grader receives no model secret/auth mount and may use `--network none` while retaining container loopback for local app tests.

- [ ] Write checks for workflow path filters including Docker/lock/runtime changes, all six lab matrix entries, preserved timeouts, artifact paths, and exact failure exit propagation. Add an actual Docker test with a synthetic auth sentinel visible to the rehearsal process and absent from a separately created grader process/container.
- [ ] Verify the current workflows fail the image/secret-separation contract, then replace host setup-node/setup-python/pip/npm/browser installation steps with builds and image invocations. Do not move Docker inside the learner container or mount its socket.
- [ ] Preserve the real Copilot invocation in the main harness. Keep smoke/refinement triggers distinct from full rehearsals; no automatic Codex provider migration. Rehearsal ends before independent grading starts. Always retain logs/assessment on failure, then report the correct failed job status.
- [ ] Execute the deterministic CI configuration/image checks without provider secrets; perform a token-scoped smoke only when credentials are available. **Expected:** no auth data in grader environment/files, successful artifact extraction, and deliberate child exit 7 reaches the host as 7 rather than success. Image history/build logs/exports must not contain the synthetic sentinel.
- [ ] Commit: `ci: execute training and grading in the locked image`.

## Task 6: Rewrite prerequisites and assemble the executable training package

**Files:** Create `README.md`, `training_author/build_handbook.py`, `training_author/render_handbook.mjs`, `training_author/build_package.py`, `tests/container/test_package.py`; modify `training_author/guide.md`, `training_kit/README.md`, `training_kit/{firmware,hardware,test_team}/README.md`, `docs/{FIRMWARE,HARDWARE,TEST}_TEAM_WALKTHROUGH.md`, all six `docs/*_STUDENT_GUIDE.md`, `COPILOT_ACTIONS_GUIDE.md`; regenerate `docs/ABB_Workflow_Training.pdf`. Update Docker locks for documentation dependencies. Review current slide links without changing unrelated slide content.

**Interfaces:** `build_handbook.py --source PATH --output PATH --materials PATH` creates the PDF and embedded starter ZIP using baked Chromium/pypdf. `build_package.py --source PATH --output PATH --audience {learner,facilitator}` emits `abb-training-<revision>.zip` or `abb-training-facilitator-<revision>.zip` plus SHA-256/file/version manifest. The learner archive installs `compose.learner.yaml` as its default `compose.yaml`; only the facilitator archive carries full reference/checking sources. Source comes from the integrated current documentation, not stale copies or another chat's private workspace.

- [ ] Integrate the user's current approved handbook/student-guide drafts into the implementation branch without replacing or committing unrelated PDF/slide edits. Record which source revision/drafts the publication builds. Require the six student guides to be included before package assembly.
- [ ] Write package tests asserting the distribution includes Compose/Dockerfile/runtime locks, sanitized starter materials, current handbook and manifest; excludes credentials/solutions/old work from learner artifacts; includes assessment sources only in the facilitator archive; and its PDF has exactly one `ABB_Workflow_Training_Starters.zip` attachment. Preparing all twelve cases from the extracted attachment must work inside the image. Assert no learner setup instructs host venv/pip/npm/browser-path provisioning.
- [ ] Run those checks on the old documentation/package. **Expected:** missing Docker distribution/builders and obsolete setup fail. Do not regard an intentionally skipped learner test as a package-build pass/fail signal.
- [ ] Rewrite sections 2–4 and affected guide references with Docker-only host commands: obtain/unpack package, build or load approved image, start training, device login, offline/online readiness, case preparation, same-container two-terminal use, export, stop/resume. Keep exercise-relative commands and four-stage teaching content; describe supplied T1 support separately from extraction work.
- [ ] Implement PDF rendering from Markdown with explicit `<!-- PAGE -->` boundaries and table support, then attach the freshly assembled starters with pypdf. Pin renderer libraries in the image. Implement distribution assembly from an explicit audience-specific file allowlist and safe output paths. Reuse the learner material allowlist for its Docker context and PDF attachment, so neither exposes instructor/solved validation sources. Build the learner archive independently to prove absent facilitator files do not break its selected Docker target. No Docker image or auth material inside the PDF ZIP; optional offline image tar is a separate artifact produced with Docker.
- [ ] Execute the package tests, extract and exercise the attachment, visually inspect all regenerated PDF pages, and check slide page links. Test the actual package from Windows Docker Desktop in a folder with spaces and from Linux Engine with no host Python/Node/Chrome. **Expected:** published commands reproduce runtime behavior; work survives restart and sanitized export works.
- [ ] Record unsupported/unverified targets, runtime rebuild/update policy and artifact hashes. Do not push images or publish releases as part of this local packaging task without authorization.
- [ ] Commit: `docs: replace host setup with the Docker training package`.

## Task 7: Verify complete exercises and retained regression packages in Docker

**Files:** Add integration scenarios to `tests/container/test_image.py`, `test_portability.py`, `test_browser.py`; create `docs/validation/docker-training.md` and a structured runtime/result manifest under a new validation-record directory. Do not modify historical archives/seeds.

**Interfaces:** Consumes Tasks 1–6, including the final documentation/runtime dependencies. Freeze one candidate image ID before full live rehearsals. Produces separately labeled deterministic checks, real-provider rehearsal results, image digest/lock/source hashes and per-submission assessment evidence.

- [ ] Run inside the facilitator image: `python training_kit/hardware/tests/test_starters.py`, the firmware instructor smoke using the documented disposable compiled parser path, `python training_kit/test_team/author_checks/check_server.py`, `python validation_t1_package/check.py`, and `python validation_t2_package/check.py`. Give each conflicting `t1-refined` check a fresh run root. **Expected:** genuine checks pass under Python 3.12; known starter behavior remains intentional, not repaired packaging.
- [ ] Run the existing FW1 refinement/check sequence separately with its required provider access, retain its actual raw evidence and then call `validation_replay/check_fw1.py`. Label this credentialed sequence distinctly from offline checks.
- [ ] Rehearse all six current main labs, one fresh container/run-root per matrix entry, then run independent grading in new credential-free containers. **Expected target:** 18/18 accepted with unchanged authorities; expected engineering FAIL/BLOCKED outcomes are still reported accurately. If any fail, preserve the failure, diagnose the Docker migration, and do not rewrite graders or candidate solutions to manufacture acceptance.
- [ ] Record image ID, complete version manifest, source hashes, actual provider/model identity, timings, all exits and browser capabilities. Compare with historical results as a runtime migration, disclosing changed CLI/Playwright versions and previous Python differences. Do not relabel the older Codex 15/15 as container verification.
- [ ] Verify browser timeout/occupied-port cleanup, aborted agent execution, service restart/rebuild and two isolated participant projects. **Expected:** no orphaned owned servers, shared state or lost original evidence. A full model-account block leaves this acceptance gate explicitly incomplete.
- [ ] Commit: `test: record Docker training verification`.

## Final verification and handoff

- [ ] Self-check the plan/spec coverage and implementation diff; run the focused deterministic/container/package checks on the final tree, reusing completed live rehearsals only when no new runtime or source change invalidates them. Runtime image changes after the Task 7 candidate freeze require the relevant checks and fresh live baseline before claiming that image verified.
- [ ] Run one fresh whole-change review. Verify default commands, credential boundaries, raw failed/success evidence, protected inputs and documentation consistency. Keep historical validation archives immutable.
- [ ] Provide the current image/lock manifest, local distribution ZIP/PDF and validation report. Clearly separate verified targets from account/host-policy/ARM/authentication limitations.
- [ ] Keep the implementation branch for review. Registry publication, PR/merge and deletion of learner volumes are separate decisions.

## Planning check completed

The brainstorming skill's fresh builder check returned **“nothing important left.”** The plan was then self-reviewed for source coverage, interfaces, failure cases and scope. No images were built, dependencies installed or exercises changed while preparing it. Docker client/server availability was inspected only. The sandbox feasibility gate and live accounts are implementation checks, not assumptions that have passed.

Recommended execution: **native**, with one final fresh review. The image, launcher, auth, paths, CI and publication share contracts, so sequential implementation is simpler than parallel changes to those interfaces. Review the proposed design/plan before implementation.
