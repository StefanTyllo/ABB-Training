# ABB workflow training in Docker

Unpack the learner package into a folder of your choice. Host requirements are Docker Engine or Docker Desktop with Linux containers, Compose v2 or newer, network access for the initial build and approved agent accounts. The supported runtime is **linux/amd64**. Windows Docker Desktop and ARM require separate acceptance evidence; the local validation report records what was actually tested.

**Host terminal** — PowerShell on Windows or a terminal on Linux, in the unpacked package folder:

```text
docker compose build training
docker compose up -d training
docker compose exec training abb doctor --offline
```

The offline doctor launches sandboxed browsers, compiles a disposable program, checks clean preparation and runs the Codex sandbox. Account access is reported separately. Keep the original output when a check returns FAIL or BLOCKED.

**Host terminal** — authenticate each approved provider once, completing its displayed device-code flow:

```text
docker compose exec -it training abb login codex
docker compose exec -it training abb login copilot
```

Accounts, entitlement and organization policy remain required. Run a real harmless tool command through each agent before treating its account as ready. Codex uses `gpt-6.1-sol` with medium reasoning. Login and version output alone do not prove model access.

**Host terminal** — a fresh FW1 example:

```text
docker compose exec training abb prepare fw1 demo
docker compose exec --workdir /workspace/work/fw1-demo training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw1-demo
abb agent codex --workspace /workspace/work/fw1-demo
```

Review normal approval requests. Use the same selected agent/model throughout a lab. The [handbook](docs/ABB_Workflow_Training.pdf), six student guides and three track walkthroughs give the exact demo and transfer entry commands for each exercise. The source materials are image-owned; prepared work belongs to you. The firmware and test starters intentionally contain unfinished or faulty behavior.

`exit` returns to the host. Re-enter an existing workspace with its `docker compose exec --workdir ... training bash` command; **do not prepare it again**. Starting or stopping a shell does not remove work.

**Host terminal** — stop and resume:

```text
docker compose stop training
docker compose up -d training
```

Named work, run, export and separate provider-auth volumes survive normal stop/start and image rebuilds. Preparation refuses an existing workspace. Choose a fresh name for a new attempt.

For several participants on one Docker host, choose distinct Docker project names and repeat `-p` on every command, for example `docker compose -p team-a up -d training`. Keep both terminals and that participant's facilitator grading in the same project.

**Host terminal** — export code and evidence to a fresh filename:

```text
docker compose exec training abb export --output /workspace/export/submission.zip
docker compose cp training:/workspace/export/submission.zip ./submission.zip
```

The export excludes `.env`, `.auth`, provider stores, Git metadata and caches. Inspect the contents before submitting; the exercise asks you to transfer only the specified workflow or reusable code.

## Optional local browser preview

Prepare one T1/T2 workspace first and stop its Terminal A server with Ctrl-C. One workspace can own port 8765 in a service at a time. The optional override publishes only the host loopback address.

**Host terminal — Bash**:

```bash
ABB_PREVIEW_WORKSPACE=t1-demo ABB_PREVIEW_PORT=8765 docker compose -f compose.yaml -f compose.preview.yaml up -d training
```

**Host terminal — PowerShell**:

```powershell
$env:ABB_PREVIEW_WORKSPACE = 't1-demo'
$env:ABB_PREVIEW_PORT = '8765'
docker compose -f compose.yaml -f compose.preview.yaml up -d training
```

Open the local address `http://127.0.0.1:8765` in your host browser. Choose a different host port if occupied. Return to the normal service with this **Host terminal** command:

```text
docker compose -f compose.yaml up -d training
```

## Facilitators

Use the separately named facilitator package for assessment sources, CI workflows and publication tools. Learner archives and the PDF attachment exclude instructor and solved validation sources. The full source tree supports:

**Host terminal**:

```text
docker compose --profile facilitator build facilitator
docker compose --profile facilitator run --rm grader python -m pytest /opt/abb/repo/tests/container -q
```

The grader has no provider-auth mounts or model secrets. The [CI guide](COPILOT_ACTIONS_GUIDE.md) describes separate rehearsals and grading. Live provider acceptance is distinct from deterministic runtime checks; see [Docker validation](docs/validation/docker-training.md).

Dependencies are installed at image build time from the checked-in base digest, Debian snapshot and npm/pip locks. Update pins deliberately, rebuild and repeat the relevant offline and live gates before releasing a new candidate. Current MCP and bootstrap Playwright versions differ as recorded in their lock; both browser paths have their own tests. An offline image can be provided separately with `docker save`/`docker load`; it is never embedded in the PDF.
