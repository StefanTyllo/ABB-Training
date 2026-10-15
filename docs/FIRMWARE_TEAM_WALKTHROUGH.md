# Firmware team: two exercises from demonstration to reusable code

**Audience:** firmware engineers comfortable with a terminal and basic C/Python. This is a guided workshop, not a completed solution. Follow steps in order and explain your decisions to the coding agent. The facilitator supplies the exercise environment and reviews the evidence.

**Outcomes:** FW1 restores communication using a captured baseline and one justified change. FW2 repairs a streaming parser and verifies its protocol behavior. In both, you first demonstrate the work, extract Markdown, add deterministic helpers, and replay the process on a fresh case.

## Before starting

Use the Docker [handbook](ABB_Workflow_Training.pdf) setup and real readiness checks. Host commands start in the unpacked package folder. Each exercise below supplies its exact container entry, two fresh transfer paths and resume instructions. Use one selected agent/model throughout, and explain each operation before extraction.


---

## FW1 — Capture state before troubleshooting

### 1. Prepare a device case and understand the boundary

Use the host-side entry below:

**Host terminal** — in the unpacked package folder; fresh FW1 demonstration:

```text
docker compose up -d training
docker compose exec training abb prepare fw1 demo
docker compose exec --workdir /workspace/work/fw1-demo training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw1-demo
```

This opens a local container shell; it requires no SSH account or container password. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. `exit` returns to the host. To resume in a new terminal, return to the package folder, run `docker compose up -d training`, and repeat the exact entry command above without preparation. If the directory is wrong, check `pwd` and re-enter the stated workspace. A stopped service is recovered with `docker compose up -d training`; a missing workspace needs its original volume or a deliberately fresh attempt. Normal `docker compose stop training` and `up -d training` preserve work.


- **What and why:** investigate a configuration-induced communication failure without changing the evidence first.
- **How:** read `requirements.md`. Preparation already initializes `device/`; do not initialize it again. Allowed changes are configuration writes through the device tool and your workflow/automation/evidence files. Preserve the simulator, reference file and direct state JSON.
- **Failure and recovery:** if preparation fails, resolve the error or choose a fresh directory. Do not invent state or edit the simulator to make the exercise pass.
- **Code to add later:** validate tool, state and reference paths before capture. Missing inputs should produce an actionable blocked result.
- **Evidence:** the case opens with the supplied state and unchanged authoritative inputs.

### 2. Capture the baseline before any write

Run these individually, retaining complete output, command, time and exit status for each:

**Inside the container**:

```bash
python fw1/device.py --workdir device read --field identity
python fw1/device.py --workdir device read --field firmware
python fw1/device.py --workdir device read --field config
python fw1/device.py --workdir device read --field faults
python fw1/device.py --workdir device logs
python fw1/device.py --workdir device probe
python -m json.tool fw1/expected.json
```

- **What and why:** establish who the device is, its current configuration and whether communication actually works. Several independent observations support a diagnosis.
- **How:** save the raw reads and failed probe under `evidence/` before proceeding. Select the reference entry by the observed identity.
- **Failure and recovery:** a failed required read or failed evidence write means the baseline is incomplete. Restore access or the evidence destination and capture again; do not change configuration yet.
- **Code to add later:** `automation/capture_state.py` invokes every primitive, saves raw results by default and validates completeness. It must not mark partial observations complete.
- **Why the step works:** a persistent baseline makes before/after comparison possible and prevents remembered or inferred values from replacing observations.

### 3. Make one justified change and verify recovery

- **What and why:** test a specific configuration hypothesis with the smallest permitted experiment.
- **How:** compare current baud with the identity-matched reference. Use `python fw1/device.py --help` and the `set` help to construct one `--parameter baud --value` operation. Obtain its numeric value from the reference, not from this document. Then repeat configuration, active faults and probe reads.
- **Failure and recovery:** if identity/reference matching fails, stop and obtain the correct reference. If current configuration differs from the saved baseline, capture a new baseline before writing. If recovery fails, preserve the attempt and reconsider the hypothesis; do not stack unexplained writes.
- **Code to add later:** an experiment helper requires a saved baseline for the same device, checks it against current configuration, applies at most one allowed change, and captures the result. A failed baseline persistence blocks the write.
- **Acceptance and explanation:** one recorded configuration change clears the current fault and produces a successful fresh probe. Historical timeout logs may remain; explain why historical events are different from the active fault register.

### 4. Extract the process into Markdown, then code

Only after the demonstration is complete, ask the agent to reconstruct the actual process as `workflow.md`. Include inputs, reasons, decision branches, evidence, failure handling and acceptance. Review it; replace demo device IDs, baud values and paths with inputs. Save an unchanged `workflow-md-only.md` checkpoint.

Create `extraction-map.md` and implement the agreed deterministic operations under `automation/`:

| Operation | Inputs and output | Problem the code addresses |
| --- | --- | --- |
| Capture state | Tool/state paths → complete raw evidence and manifest | Prose can omit a read or forget to save output |
| Match reference | Observed identity/reference → matched entry or blocked | Demo identities can accidentally be reused |
| Apply experiment | Valid current baseline/one change → before, mutation and after records | A write can occur without a usable baseline |
| Compare recovery | Before/after observations → exact differences and probe result | A completion claim can overlook a remaining active fault |

Use descriptive functions, explicit values and actionable errors. Preserve original evidence on repeat runs; do not overwrite the incident history. Keep diagnosis of unfamiliar faults with the engineer/agent. Update `workflow.md` to call the helpers, and document exact commands/dependencies in `automation/README.md`.

**Checks before replay:** valid capture; missing state directory; failed required read/evidence persistence; unknown identity; missing baseline; stale baseline; successful one-change recovery; rerun preserves prior records. Use independent disposable fixtures for checks that mutate state. Code is useful because it rejects unmet prerequisites and records actual actions; it cannot supply a missing engineering reference.

### 5. Replay on a different device

After Stage 4, use the host-side transfer entries below:

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
docker compose up -d training
docker compose exec training abb prepare fw1 transfer --name fw1-transfer-md
docker compose exec --workdir /workspace/work/fw1-transfer-md training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw1-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
docker compose up -d training
docker compose exec training abb prepare fw1 transfer --name fw1-transfer-code
docker compose exec --workdir /workspace/work/fw1-transfer-code training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw1-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.


Follow the paired replay instructions below. The transfer device identity and required baud differ. Copy no demo `device/`, captured results or finished solution. Each replay must discover the current identity and select its reference.

**Completion:** retain a complete pre-change baseline, identity-matched reference, one mutation record, after-capture and successful fresh probe. If any required input is unavailable, report blocked with the reason. A fixture smoke test alone does not prove the learner captured evidence correctly.

---

## FW2 — Reproduce and repair a streaming parser

### 1. Prepare and read the protocol before editing

Use the host-side entry below:

**Host terminal** — in the unpacked package folder; fresh FW2 demonstration:

```text
docker compose up -d training
docker compose exec training abb prepare fw2 demo
docker compose exec --workdir /workspace/work/fw2-demo training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw2-demo
```

This opens a local container shell; it requires no SSH account or container password. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. `exit` returns to the host. To resume in a new terminal, return to the package folder, run `docker compose up -d training`, and repeat the exact entry command above without preparation. If the directory is wrong, check `pwd` and re-enter the stated workspace. A stopped service is recovered with `docker compose up -d training`; a missing workspace needs its original volume or a deliberately fresh attempt. Normal `docker compose stop training` and `up -d training` preserve work.


- **What and why:** establish a protocol-based expected result before repairing C code.
- **How:** read the FW2 section of `requirements.md`. A packet is `A5 02 sequence low high checksum`: unsigned 8-bit sequence, signed 16-bit little-endian value, XOR of the first five bytes. Each CLI argument is another chunk of the same stream.
- **Failure and recovery:** ambiguous behavior must be resolved from the contract. Do not invent a timeout or discard partial state between chunks.
- **Code to add later:** a packet builder validates fields and derives bytes/checksum from the specification. It does not use the parser's output as the expected result.
- **Boundary:** edit only `fw2/parser.c` plus common artifacts. Preserve `parser.h`, `main.c` and requirements. The executable is generated output.

### 2. Reproduce whole-packet and split-packet failures

**Inside the container**:

```bash
gcc -std=c11 -Wall -Wextra -Werror \
  fw2/parser.c fw2/main.c -o fw2/parser
./fw2/parser a5020785ffda
./fw2/parser a50207 85ffda
```

- **What and why:** separate successful compilation from correct decoding and streaming behavior.
- **How:** run the compiler first; only run the executable if compilation succeeds. Both invocations should produce sequence 7, value -123. Save actual outputs, exit statuses and source snapshot/digest.
- **Failure and recovery:** build failure is an infrastructure/build result; incorrect JSON values are behavioral failure. Never run an older executable after a failed build.
- **Code to add later:** a build-and-replay helper stops on compilation failure and records exactly which source and binary were evaluated.
- **Why this comparison works:** changing only chunk boundaries should leave the decoded objects unchanged. A difference exposes state-handling behavior rather than a different packet.

### 3. Repair the cause and broaden verification

- **What and why:** address signed conversion and partial-state lifetime rather than patching one example.
- **How:** inspect how the two value bytes become a signed number and how parser state survives feed calls. Make a focused repair, rebuild and repeat both reproductions.
- **What can go wrong:** a narrow fix handles -123 but breaks limits or resynchronization. The specification requires discarding only the first candidate byte after invalid length/checksum and rescanning the remaining bytes. `A5` inside a valid packet is ordinary data.
- **Code to add later:** construct/replay independent cases for positive values, signed limits -32768/32767, all relevant splits, bad checksum, invalid length, noise, consecutive packets and incomplete tails. Include a valid frame after corruption, an embedded `A5`, empty input and malformed CLI input.
- **Acceptance and explanation:** whole/split results match; invalid frames emit nothing; later valid frames recover; incomplete tails emit nothing. Tie each assertion to a contract clause. Do not add a corrected parser implementation to the verification helpers.

### 4. Extract build, replay and comparison helpers

After the demonstrated repair passes, write and review `workflow.md`; preserve `workflow-md-only.md`. Parameterize source directory, compiler, executable path, packet fields, chunk schedule and evidence destination. Keep protocol invariants explicit.

| Operation to extract | Failure it makes observable | Evidence to retain |
| --- | --- | --- |
| Compile candidate | Build error or stale binary reuse | Source digest, compiler command, stdout/stderr, exit status |
| Construct and split stream | Invalid field or incorrect chunk schedule | Packet bytes, supplied chunks and specification-derived expected objects |
| Replay and compare | Wrong values, missing/extra packets, process failure | Actual JSON, expected JSON and exact differences |
| Summarize checks | Required case omitted | Requirement-linked case list and individual outcomes |

Implement under `automation/`, with readable functions and independent fixtures under `automation/tests/`. Add a failed-compilation check proving an old executable is not run. Keep parser repair as task-specific work. Update the workflow to invoke the implemented helpers and interpret their results.

**Why code helps:** the same compiler/replay/comparison procedure executes for every case, and a failure identifies its phase and inputs. Human review still explains whether the check set addresses the protocol risks.

### 5. Replay from a fresh faulty parser

Use the host-side entry below:

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
docker compose up -d training
docker compose exec training abb prepare fw2 transfer --name fw2-transfer-md
docker compose exec --workdir /workspace/work/fw2-transfer-md training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw2-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
docker compose up -d training
docker compose exec training abb prepare fw2 transfer --name fw2-transfer-code
docker compose exec --workdir /workspace/work/fw2-transfer-code training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw2-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.


Use the paired replay procedure. Transfer no repaired `parser.c` or executable. After building in each new workspace, use this reproduction:

**Inside the container**:

```bash
./fw2/parser a502 2a00 f875
```

Expected: sequence 42, value -2048. The new conversation must use the transferred process to repair the fresh candidate.

From the training root, the facilitator independently checks each built submission, changing the executable path as needed:

**Host terminal — facilitator package only**:

```text
docker compose --profile facilitator run --rm grader python /opt/abb/repo/training_kit/firmware/instructor/smoke.py /workspace/work/fw2-demo/fw2/parser
```

The facilitator's independent checks and assessment sources are supplied separately from the learner materials.


**Completion:** protocol checks pass, including the supplied 50-case/malformed-input evaluation; the explanation accounts for the repair; helper checks and actual replay evidence are retained. Compilation alone or one example alone is insufficient.

---

## Paired replay and submission for both exercises

Complete both demonstrations and code extraction stages. The facilitator selects at least one exercise for paired replay; both are preferable when time permits.

1. **MD-only:** copy `workflow-md-only.md` as `workflow.md` into its fresh workspace. Copy no `automation/` or demo outputs.
2. **MD plus code:** copy updated `workflow.md`, reusable `automation/` and documented dependencies into the other workspace. Copy no repaired inputs or finished solutions.
3. Start a new conversation in each with the same agent/model. Explicitly ask it to read `workflow.md` and current requirements, execute on current inputs, and retain evidence. Record any new scripts the MD-only agent independently writes.
4. Compare acceptance results, actual helper invocation, elapsed time, interventions, failures and recovery. Manual fallback must be recorded; it does not establish that the helper worked.

For **each lab**, submit `workflow-md-only.md`, `workflow.md`, `extraction-map.md`, `automation/` including checks/README, and `evidence/session.md` plus actual run artifacts. Learner automation uses exit 0 for pass, 1 for engineering failure and 2 for blocked inputs/infrastructure; preserve native tool statuses separately.

The facilitator applies the handbook rubric: at least 8/10, no zero in any category and every mandatory lab condition satisfied. Review demonstration evidence, reusable workflow, deterministic boundary, code quality and feedback/transfer. Detailed prose or a green tool exit alone does not earn acceptance.

Conclude from recorded evidence: **goal → action → observed failure → code added → rerun result → explanation → remaining untested paths**. For example, a stale-baseline rejection supports the claim that this helper prevented that unsafe write; it does not prove every possible direct write is prevented. One paired replay is evidence about the cases exercised, not a general performance claim.

## Final adequacy and completeness review

- **Documentation review, 14 October 2026:** adequate for a facilitated workshop at the stated level. Each exercise explains the engineering aim, operations, failure/recovery, code extraction and evidence-based conclusion; shared submission/replay rules complete the sequence.
- **Checks performed:** all six firmware workspace preparation commands ran successfully; code fences passed shell syntax/Markdown parsing and referenced local sources were checked. The FW1 reads/baseline path and FW2 build/reproductions were exercised. The supplied firmware smoke check passed, covering both FW1 cases and its parser reference checks. The starter parser's observed wrong signed value/missing split output are intentional exercise failures, not a repaired learner submission.
- **Level:** a concise guide for engineers who can run commands and read basic C/Python. Protocol facts, paths, mutation boundaries, failure branches and completion criteria are explicit; implementing the helpers remains learner work.
- **Coverage:** both lab demonstrations, Markdown abstraction, deterministic extraction, helper failure checks, fresh-case replay and evidence review are included.
- **Required local gate:** run the actual agent workflow and inspect learner artifacts. This document is instructions, not a claim of a completed classroom rehearsal.
- **Review against:** [firmware exercise contracts](../training_kit/firmware/requirements.md), the independent checks supplied in the facilitator package and the handbook's shared method/rubric. Resolve any discrepancy using those contracts before proceeding.
