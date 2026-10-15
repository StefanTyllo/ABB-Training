# Container CI, rehearsal and independent grading

All six workflows call `build-training-image.yml`. It builds the locked facilitator target without credentials, records the immutable image ID, and uploads the image archive plus SHA-256 checksum once per workflow run. Matrix jobs verify and load that artifact. The runner performs checkout, Docker operations and artifact upload; application, agent, compiler and browser commands run in the image.

`validate-workflow-labs.yml` retains all six labs, four teaching stages, two fresh transfers, 600-second stage timeouts and a separate 900-second T2 grading allowance. The main harness remains Copilot with its scoped tool allowances. Codex interactive rehearsals request `gpt-6.1-sol` / medium and have separate account acceptance.

The repository secret is **COPILOT**. The selected rehearsal container receives one runtime token file in `/run/secrets/copilot_token`; the CLI imports it through standard input. Its host directory is private, and its file is readable inside the non-root container without assuming the runner's UID. The wrapper removes provider tokens from the child environment. A fresh grader container uses the same immutable image and run volume with `--network none`, no token file and no provider-auth mounts. Authentication state remains outside source and retained artifacts.

Rehearsal ends before grading starts. A failed rehearsal still runs independent grading and artifact collection. Failed child exits reach the job; a successful agent response is not an acceptance result. The four remaining validation/refinement workflows retain their distinct purposes, triggers, timeouts and measured evidence. Authentication smoke still verifies a response with tools disabled; it is not the real tool smoke required by release acceptance.

## Local deterministic checks

**Host terminal**, from the facilitator package:

```text
docker compose --profile facilitator build facilitator
docker compose --profile facilitator run --rm grader python -m pytest /opt/abb/repo/tests/container -q
```

These checks do not verify a paid model account. Live rehearsal needs approved Copilot entitlement, token scope and organization policy. Never replace the provider, impersonate its executable, substitute a model, or suppress a failed/blocked result to get a green job.

## Unattended provider access

Use `compose.auth.yaml` only in the facilitator package. It defines separate `codex-auth` and `copilot-auth` services; each mounts only its own provider secret and auth volume. The selected file contains one plain token line: a Codex API key or a supported Copilot token. Device login through the learner service is the normal interactive route.

On Linux, keep the host secret in a private directory and make the selected file readable by the container user; Compose bind-backed secrets do not remap the host file's UID. A private parent directory with mode 700 and a file with mode 444 supports different host/container UIDs. On Windows, apply equivalent access restrictions. Do not store secret files in the build context.

**Host terminal** — after setting the selected secret-file path through `ABB_COPILOT_SECRET_FILE`:

```text
docker compose -f compose.yaml -f compose.auth.yaml --profile auth run --rm copilot-auth python /opt/abb/runtime/ci.py --provider copilot -- python /opt/abb/repo/training_ci/run_lab.py fw1
docker compose --profile facilitator run --rm grader python /opt/abb/repo/training_ci/grade_all.py fw1
```

Use a fresh run volume/project for a new attempt. Normal commands preserve run evidence and refuse existing work; deleting prior results is a separate explicit operator decision. The grader receives neither provider state nor the runtime secret.

Artifact collection uses the same sanitizer as learner exports, excluding authentication state, provider stores and caches while retaining failed evidence. Inspect the job's assessment JSON/Markdown, grader logs, raw stage transcripts, generated workflows/code and browser evidence. Artifacts remain for 14 days. Record actual provider/model identity and meaningful engineering outcomes. Prior host-based Actions results and the older Codex experiment remain historical; they are not container acceptance.

## Rebuilding and publishing

Change dependency pins and hashes deliberately, rebuild, rerun offline checks and then repeat the affected live baselines. Freeze an image ID before a release rehearsal. A later runtime or source change invalidates the corresponding acceptance evidence. Image registry publication and release publication require their own authorization.
