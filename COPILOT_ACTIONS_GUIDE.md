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

## Stage-focused lab rehearsals

The lab runner still invokes GitHub Copilot CLI 1.0.97 with the existing `COPILOT`
secret passed through the selected runtime token file in its agent container. Independent grading
runs separately without that token. It never invokes a different coding agent.

`training_kit/prompts/` contains common, stage and fresh-transfer instructions.
`training_ci/context_delivery.py` selects the current card section and reading
list without editing the full task card or acceptance contract. Exact prompts,
context snapshots and SHA-256 delivery metadata are saved in each workspace's
evidence directory; context/current-stage.md is host-managed and may change.

Each invocation uses a temporary COPILOT_HOME, --no-custom-instructions and disabled
skill retrieval, so personal instructions/configuration do not enter a rehearsal.
The temporary profile is deleted afterwards; no global settings are changed.
Container rehearsals import the selected runtime token into each temporary profile; stored interactive logins are separate. Classroom guided work keeps normal approvals.
Pinned browser MCP configuration is supplied explicitly for T1/T2; Selenium remains
the test framework. MCP runs from the baked, sandboxed browser tooling. Native Copilot model/effort
can be set through repository variables COPILOT_MODEL/COPILOT_REASONING_EFFORT;
if unset, metadata honestly records CLI defaults rather than a pinned model.

The existing 600-second stage limit is authoritative, with no shorter inner cutoff.
Timeouts retain failure metadata and delivered evidence. Smaller default context
and mandatory-artifact-first prompts do not permit skipping acceptance checks.

Token-free PR checks cover all real card/stage/replay combinations, preservation,
Copilot command isolation, timeout recording and PDF/embedded starter consistency.
Authenticated Copilot rehearsals remain separately dispatchable; passing structural
checks does not establish a new agent acceptance result or a learner pilot.

References: [Copilot programmatic options](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference),
[configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference),
[tool permissions](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools).
