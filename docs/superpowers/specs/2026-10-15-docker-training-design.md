# Docker training environment design

Status: proposed design for the requested implementation plan; no runtime implementation yet.

## Intent and confirmed scope

Replace host-specific paths and locally installed tools with a reproducible Docker training package. The user confirmed that **both coding agents and exercises run inside Docker**. Cover FW1, FW2, HW1, HW2, T1 and T2, their preparation, four teaching stages, fresh transfers, checks and published setup instructions.

Host prerequisites become Docker Engine/Desktop with Compose v2, Linux-container support, the unpacked training package, and approved agent accounts/network access. Host Python, Node, GCC, Chrome, ChromeDriver, Git and a Bash installation are unnecessary. Agents still require their online services; Docker does not supply accounts or make model inference offline.

This document makes proposed engineering choices explicit. Only the Docker scope and in-container agents are user decisions; other choices below are the planner's recommendations for review.

## Current evidence and source of truth

Planning branch starts at current main `4ba6e36901c2b9d8d03d0a13c2e2bd139d465a51`, not the older Codex experiment baseline. Inspection also included the user's uncommitted `training_author/guide.md` and six `docs/*_STUDENT_GUIDE.md` drafts in the original checkout. Those drafts, the PDF and slides must remain untouched during planning. Integrate their current approved versions before implementation updates documentation; never replace them with an older checkout.

Observed issues:

- Handbook sections 2–4 require host Python/venv, Node, two agent CLIs and browser provisioning. Track walkthroughs repeat `.venv` activation.
- `training_kit/prepare_lab.py` already resolves its own inputs relative to its file; preserve this useful behavior and refusal to overwrite work.
- Browser fixtures already accept `BASE_URL`, `CHROME_BINARY` and `CHROMEDRIVER`. Their defaults assume a shared localhost with the app server.
- `training_ci/run_lab.py` and `grade_all.py` put output under repository-relative `runs/`; six workflows provision overlapping host dependencies.
- T1 promises a facilitator-provided Node bootstrap/MCP setup, but no reusable bootstrap source/package is committed in the current main starter tree.
- No committed handbook build script was found. The PDF embeds a starter ZIP and must be rebuilt consistently with changed instructions/materials.
- Current slide text has no installation/setup terms; verify links/content after the handbook changes rather than rewriting unrelated slides.
- Docker client/server 29.6.2, Linux x86_64, responded on the inspected machine. This does not validate the proposed image.

The prior experiment's 15/15 selected-lab results are historical evidence. Never edit its ZIPs or relabel those executions as container runs.

## Selected architecture and alternatives

Use one versioned Linux runtime built from a single Dockerfile, with learner and facilitator build targets. Compose is the supported entry point on Windows and Linux. A persistent learner service runs the agent, exercise server, Selenium, Playwright MCP and generated code in the **same container**. This preserves localhost semantics and avoids remote-browser file/state/driver coordination.

Alternatives considered: a remote Selenium/Playwright sidecar adds address translation and session handover complexity; a host agent with container-only tests retains host CLI/path dependencies and conflicts with the confirmed scope. Neither is the default.

Default execution is headless, with screenshots/JUnit/logs retained. A host browser preview is optional. Native GUI browser streaming, Kubernetes, production deployment and physical-device access are outside this migration.

### Images, roles and files

- `runtime` base: Python 3.12, Bash, Git, GCC, Node 22, both agent CLIs, Selenium/pytest, pinned Chrome for Testing plus its matching ChromeDriver, Playwright and Playwright MCP.
- `learner` target: clean materials and instructions only. Exclude instructor/author checks, solved validation seeds, experiments, credentials and historical outputs.
- `facilitator` target: runtime plus source, preparation/checking/CI tools and reproducible documentation/package builders. Its independent grading service receives no provider credentials or provider-auth volumes.
- One participant/workspace uses one running learner container; two terminals use `docker compose exec` into that same container. Do not use separate one-off containers for a server and its tests.
- `init: true`, non-root user, writable workspace/temp/cache locations, reviewed namespace/seccomp configuration and 1 GiB private shared memory. Do not mount the Docker socket or host home. No privileged mode, host networking, sandbox-disabling browser arguments or silent agent approval bypass.
- First implementation gate must demonstrate real Chrome sandboxed execution and Codex's normal Linux sandbox on the reference Docker engine. A host restriction must produce a useful BLOCKED result, not an automatic switch to unrestricted flags. If this gate cannot be met, revisit the design with concrete diagnostics before continuing.

### Paths and persistence

| Container path | Contract |
|---|---|
| `/opt/abb/materials` | Baked, read-only clean starter materials; `/workspace/materials` points here |
| `/opt/abb/repo` | Facilitator source/checks only; read-only runtime source |
| `/opt/abb/runtime` | Launcher, preflight and supplied runtime configuration |
| `/opt/abb/browser` | Image-owned matched Chrome and ChromeDriver |
| `/opt/abb/node` | Pinned Node runtime and locked JS tooling |
| `/workspace/work` | Named volume containing participant work and evidence |
| `/workspace/runs` | Named volume containing rehearsal outputs and assessments |
| `/workspace/export` | Sanitized export bundles; copied out using Docker CLI |
| `/home/learner` | Container-owned home; provider auth stored in separate named auth volumes |

Use named volumes by default to avoid Windows bind-path differences and Linux host UID mismatches. `down` and rebuild preserve work; deletion requires a separate explicit reset command. Export a sanitized ZIP using the launcher, then `docker compose cp` it to the host. Exclude `.env`, `.auth`, agent auth/config caches and unrelated data. An optional advanced bind-mount override may be documented after the default path works; it is not a prerequisite.

Git is inside the image. Preparation initializes an exercise-local Git repository and ignore rules for `.env` and `.auth`, including when the distribution was downloaded as a ZIP without `.git`. Preserve source inputs before the first agent stage. Runtime configuration never depends on the original user's home or `/tmp/abb-*` trees.

### Locked dependencies and platform

Initial supported image is `linux/amd64`, matching the current machine and hosted CI. Do not promise native ARM support; document that as a separate validation target, with emulation unverified until tested.

Preserve Python's 3.12 series, Selenium 4.29.0, pytest 8.3.5, and Copilot CLI 1.0.97. Proposed Node is 22.23.3. Published npm metadata inspected on 2026-10-15 reports Codex 0.162.1, MCP 0.0.83 and Playwright 1.64.1; use these as the proposed container pins. This replaces the experiment's host-specific alpha Codex binary and intentionally aligns the supplied bootstrap with MCP's Playwright dependency; rerun baselines and disclose that change.

Task 1 records the exact Python/base image digest, browser/driver version and checksums, Node archive checksum, package-lock integrity, and Python transitive dependency hashes in checked-in lock files. Pin a dated Debian package snapshot and record OS package versions so compiler/browser-library installation is reproducible too. Resolve browser/driver as a pair from Chrome for Testing metadata, never from whatever the host happens to have. No `latest`, `npx -y` downloads, pip installs or browser downloads during ordinary exercises. Initial image build may access package sources; model calls need their service network. Offline deterministic preflight/checks run after image build.

Use image-owned `CHROME_BINARY`/`CHROMEDRIVER`, inherited by Selenium and graders. Configure Playwright/MCP with that executable and `chromiumSandbox: true`; do not assume non-root alone enables Playwright's browser sandbox.

### Learner command contract

From the unpacked package, these are proposed commands implemented by the plan:

```text
docker compose build training
docker compose up -d training
docker compose exec training abb doctor
docker compose exec -it training abb login codex
docker compose exec -it training abb login copilot
docker compose exec training abb prepare fw1 demo
docker compose exec -it training abb agent codex --workspace work/fw1-demo
docker compose exec -it training bash
```

The in-container shell starts at `/workspace`; existing `python materials/prepare_lab.py ... work/...` and exercise-relative commands continue to work. No activation step or host binary paths. Second terminals enter the same service. `abb prepare` prints the actual working directory and refuses an existing output. `abb agent` validates the selected workspace and records CLI/model/effort without printing secrets. Keep `gpt-6.1-sol` / medium as the Codex rehearsal setting; unavailable model access is BLOCKED, not substituted.

`abb doctor` writes JSON plus a short readable report. It checks versions, writeability, compilation, clean preparation and actual Selenium/Playwright startup; optional provider checks require an actual harmless tool call. Missing credentials do not fail an explicitly offline tool-only check, and tool readiness must not be presented as account readiness. It must distinguish intentional starter defects/skips from infrastructure failure.

### Container entry instructions in every exercise

Each FW1, FW2, HW1, HW2, T1 and T2 lab card, student guide and track walkthrough must show its own container-entry instructions. A link to the general prerequisites is not sufficient. Label command blocks **Host terminal** or **Inside the container**, give the exact exercise directory, and show `pwd` with the expected directory before exercise commands. Entering the container means opening its local shell through Docker Compose; no SSH server, container username/password or agent-account login is required for that shell. Explain agent authentication separately, and repeat it only when the selected provider is not already authenticated.

For a fresh FW1 demonstration, the proposed instructions are:

**Host terminal, in the unpacked package directory:**
```text
docker compose up -d training
docker compose exec training abb prepare fw1 demo
docker compose exec --workdir /workspace/work/fw1-demo training bash
```

**Inside the container:**
```bash
pwd
# Expected: /workspace/work/fw1-demo
```

Every guide substitutes its own concrete path, rather than leaving `<lab>` placeholders:

| Exercise | Demonstration directory |
|---|---|
| FW1 | `/workspace/work/fw1-demo` |
| FW2 | `/workspace/work/fw2-demo` |
| HW1 | `/workspace/work/hw1-demo` |
| HW2 | `/workspace/work/hw2-demo` |
| T1 | `/workspace/work/t1-demo` |
| T2 | `/workspace/work/t2-demo` |

Each exercise's fresh transfer instructions prepare **two separate** workspaces using `abb prepare LAB transfer --name LAB-transfer-md` and `--name LAB-transfer-code`, then give the full host-side `docker compose exec --workdir /workspace/work/LAB-transfer-md training bash` or code-workspace equivalent with the real lab ID filled in. Keep copied Markdown versus supplied automation rules unchanged.

For T1/T2, Terminal A enters the chosen workspace and runs its server; Terminal B repeats the same host-side container-entry command into the same service and directory before running bootstrap/tests. Do not run the server/test commands on the host or in different one-off containers. Show how to keep/stop the owned server and serialize workspaces using port 8765.

Each guide also states: `exit` returns to the host without deleting work; reopening a terminal requires repeating the package-directory/container-entry steps; resume an existing workspace without running preparation again; normal `docker compose stop training`/`up -d training` preserves work. Stages 2–4 state whether to stay in the existing shell or repeat its entry command. Include learner-readable recovery for a stopped/missing container and a wrong working directory.

### Browser lifecycle and T1 support

Keep the default app binding at `127.0.0.1` inside the container. Add an explicit `--host` server option, preserving its default, solely for optional preview. A separate Compose preview override publishes `127.0.0.1:8765:8765` and starts the chosen app with `--host 0.0.0.0`. Default exercises expose no ports. Test alternate host ports and collisions; variants remain internal and only owned children are stopped.

Provide the missing facilitator bootstrap under `test_team/support/`, copied into a prepared T1 workspace's `tools/`. It is supplied infrastructure, not learner-generated `automation/`, and does not solve the POM/tests. Lock its Node dependencies in the image. Its no-login mode validates the fixture and exports state under that workspace's `.auth/`; login mode without a reviewed fixture/adapter returns BLOCKED. Generate workspace-scoped stdio MCP configuration for either agent using the baked MCP entry point; no host browser or user plugin configuration is inherited. Verify actual MCP navigation/state loading in the container. Saved state initializes a fresh context; it does not prove authenticated handover or authenticate Selenium.

### Credentials and CI

Support interactive device-code login inside Docker with isolated persistent provider-auth volumes, plus an optional runtime secret-file profile for unattended execution. Do not copy the earlier user's credential file into the package/image. Interactive provider stores are co-resident in a participant-owned container; separate volumes provide persistence and grader separation, not an access-control boundary between CLI processes. Secret-file wrappers translate only documented provider formats for the pinned CLI; mount only the selected provider's secret. No credentials in Dockerfile ARG/ENV, image layers, source, exports, reports or grading containers. Existing `.gitignore` protections remain.

Preserve the main harness's Copilot provider and independent grading semantics. Add only the path configuration needed for Docker: shared `runs_root()` with `ABB_RUNS_DIR` defaulting to the existing `ROOT/runs` behavior. Do not convert it to Codex or rename the real Copilot CLI. Interactive Codex exercises run in the same runtime; rerunning the earlier Codex experiment uses an explicitly separate, container-compatible external adapter if requested, not a covert replacement in the classroom harness.

All six existing workflows use the same built image by digest/image ID for their tool execution. A shared build job exports a verified image artifact for matrix jobs, avoiding six independent builds. Build without credentials, run the rehearsal in its auth-scoped process/container, stop it, then grade in a new credential-free container with the same run volume and image. Preserve matrix cases, 600-second stage limits, 900-second T2 grading allowance, exit propagation, artifact retention and assessment criteria. Deterministic image checks run without model credentials; paid/live agent rehearsals remain separately triggered and recorded.

## Documentation and deliverable

Rewrite handbook sections 2–4 around obtaining/building/loading the Docker package, starting the service, account login, real readiness checks, preparing a case, using two terminals, exporting work and stopping/resuming. Remove venv/host-pip/compiler/browser-install instructions from the learner path. Update all three track walkthroughs, six current student guides, technical READMEs, CI guide and T1 facilitator instructions together.

Add reproducible handbook and package builders to the facilitator target. Render the Markdown with explicit page breaks using baked Chromium, attach a freshly built starter ZIP using pypdf, and verify all twelve lab/case preparations from that attachment. The learner distribution ZIP contains a sanitized Docker build context, locked runtime files, learner-only Compose configuration, current PDF/instructions and release manifest. A separately named facilitator ZIP includes assessment/reference sources and the full Compose profiles. Learners must not receive solved validation seeds or instructor sources through a build context or PDF attachment after excluding them from the image; both learner artifacts use the same clean material allowlist. A facilitator may also supply images via `docker save`/`docker load`; publishing images/releases is a separate authorized action. Do not put a large Docker image or any auth state inside the PDF attachment.

Current support slides contain no setup text according to inspection. Review their links and reference them unchanged unless revised handbook pagination invalidates them. Preserve the user's binary edits; no speculative slide rewrite is required.

## Acceptance and rollout

1. A clean supported machine with Docker and the package, but no host language/browser tools, can build/start and complete offline readiness checks.
2. Both agents execute a real harmless command inside the selected container workspace after their respective login. Default Codex uses the requested model/effort and ordinary approval controls.
3. All twelve clean preparations work; starter defects and source-authority rules are unchanged. Supplied T1 support never creates `automation/` before Stage 4.
4. Real Selenium and Playwright MCP use the baked browser; dynamic fields, saved-state boundaries, occupied ports, cleanup and meaningful failures are exercised.
5. Stopping/restarting/rebuilding preserves work. Two isolated participant projects do not share ports, state or credentials. Exports contain current code/evidence and no auth material.
6. Container checks for firmware, hardware and existing replay/T1/T2 packages pass under Python 3.12. Existing validation seeds stay historical and protected hashes are not silently regenerated to permit edits.
7. Before declaring migration complete, run all six current main rehearsal labs with the unchanged provider and independently assess all 18 submissions in the container. Record expected engineering FAIL/BLOCKED outcomes separately; agent exit alone is not acceptance. A missing account/model is explicitly BLOCKED.
8. Every lab and transfer has independently usable, explicitly labeled host/container entry, expected-directory, second-terminal and resume instructions; a learner need not infer these from another lab. Updated PDF, attachment, package manifest, Markdown instructions and actual CLI behavior agree. Verify a representative Windows Docker Desktop path with spaces and Linux Engine path; unsupported ARM/host policies are stated rather than claimed tested.

Roll out runtime feasibility first, then the shared image/launcher, then portability changes, T1 support, CI, synchronized documentation/release packaging, and final live verification of the frozen image. Old experiment records remain intact. This is a plan for review, not a claim that container execution has passed.

## Official references consulted

- [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/): service-specific runtime files, not image credentials.
- [Docker process lifecycle](https://docs.docker.com/engine/containers/multi-service_container/): init/reaping and owned child processes.
- [Playwright Docker](https://playwright.dev/docs/docker): non-root user and reviewed namespace/seccomp requirements; browser/package version distinctions.
- [Debian snapshots](https://snapshot.debian.org/): immutable dated package repositories for reproducible OS dependencies.
- [Playwright browser launch](https://playwright.dev/docs/api/class-browsertype#browser-type-launch-option-chromium-sandbox): explicitly enable Chromium sandboxing.
- [Chrome for Testing](https://developer.chrome.com/docs/automation-and-testing/chrome-for-testing): versioned matched browser/driver artifacts.
- [Codex authentication](https://developers.openai.com/codex/auth/): supported login mechanisms; verify pinned CLI in-container.
- [Codex sandbox](https://learn.chatgpt.com/docs/agent-approvals-security): Linux namespace/seccomp needs can conflict with Docker restrictions.
- [Copilot authentication](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli).
- npm registry metadata for @openai/codex, @github/copilot, @playwright/mcp and playwright, checked without credentials on 2026-10-15.
