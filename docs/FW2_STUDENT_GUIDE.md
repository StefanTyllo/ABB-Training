# FW2: Repair a streaming parser and extract repeatable checks

You will reproduce two parser defects, repair the candidate and turn build/replay checks into reusable tools.

## Before you begin

Use the Docker package and complete the [handbook](ABB_Workflow_Training.pdf) readiness checks. The image supplies all language, compiler, browser and agent tools. Record the same selected agent/model throughout.

Host commands run in the unpacked package folder. Commands marked Inside the container run in this exercise's prepared workspace. Preparation is for fresh work; resume by re-entering the existing workspace.

Edit the candidate `fw2/parser.c` and your learning artifacts. Preserve `parser.h`, `main.c` and requirements. Do not copy a repaired parser into the fresh replay workspaces.

Tell the agent:

> Work with me one operation at a time. Explain its purpose and expected result, then wait for my explanation before continuing. Record actual commands, observations and decisions in evidence/session.md. Do not create reusable automation until Stage 4.

Expected results below describe the supplied examples. Save actual output; if it differs, explain or resolve the difference before proceeding.

## 1. Prepare and read the protocol

**Do this:** Use the host-side fresh entry below:

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

**Inside the container**:

```bash
cat requirements.md
```


Read the FW2 section before opening the candidate implementation.

**You should get:** A six-byte packet: `A5 02 sequence low high checksum`. The value is signed 16-bit little-endian; checksum is XOR of the first five bytes. Command arguments are chunks of one stream.

**Why:** The specification supplies expected behavior independently of the faulty code.

## 2. Build the original candidate

**Do this:** Run:

**Inside the container**:

```bash
gcc -std=c11 -Wall -Wextra -Werror fw2/parser.c fw2/main.c -o fw2/parser
```

Record the source version/digest, compiler output and exit status. Continue only if compilation succeeds.

**You should get:** A successful build and a new executable. This does not yet establish correct decoding.

**Why:** You must know which source produced the program you are testing. Never run an old executable after a failed build.

## 3. Reproduce the whole-packet defect

**Do this:** Run and save the actual output:

**Inside the container**:

```bash
./fw2/parser a5020785ffda
```

Compare it with the protocol-derived expectation.

**You should get:** The correct result would be `[{"sequence":7,"value":-123}]`. The supplied faulty parser instead reports value `65413`.

**Why:** The bytes represent a negative signed value. This gives concrete evidence of a signed-conversion defect.

## 4. Reproduce the split-packet defect

**Do this:** Supply exactly the same bytes split between two arguments:

**Inside the container**:

```bash
./fw2/parser a50207 85ffda
```

**You should get:** The correct result is still sequence `7`, value `-123`. The supplied faulty parser instead emits `[]`.

**Why:** Chunk boundaries must not change the meaning of one stream. Losing the partial packet shows that state is not surviving feed calls.

## 5. Repair, rebuild and broaden the checks

**Do this:** Ask the agent to explain how the signed value is reconstructed and how partial state survives calls. Make a focused change only in `fw2/parser.c`. Rebuild and rerun both reproductions. Then check signed limits, positive values, chunk splits, noise, bad length/checksum, recovery to a later valid frame, consecutive packets, embedded `A5`, incomplete tails and malformed CLI input. Save actual outcomes.

**You should get:** Both reproductions now produce sequence `7`, value `-123`. Valid packets decode correctly; invalid frames do not emit values; later valid packets recover according to the contract. Malformed CLI input exits nonzero with stderr and no stdout.

**Why:** Two passing examples are necessary but insufficient. Broader checks show whether the repair preserves the full protocol rules.

## 6. Document the demonstrated process — finish Stage 1

**Do this:** Ask the agent to reconstruct our actual work as `workflow.md`: goal, inputs, ordered steps, reasons, evidence, decisions, recovery and completion criteria. Review it against `evidence/session.md`.

**You should get:** A procedure supported by our actual observations. Resolve a blocked demonstration with the facilitator before treating it as a successful procedure.

**Why:** The next stages must reuse a demonstrated process, including what went wrong.

## 7. Generalize the instructions — Stage 2

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Replace example-specific details with inputs: source/compiler/executable paths, packet fields, chunk schedule and evidence destination; preserve the protocol constants. Define input sources, validation and missing-input behavior. Keep genuine engineering rules. Save `workflow.md` and an identical `workflow-md-only.md` checkpoint.

**You should get:** Instructions another engineer can follow without the original conversation.

**Why:** A workflow must work with new values rather than repeat the demonstration’s answer.

## 8. Decide what becomes code — Stage 3

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Write `extraction-map.md`: each operation’s purpose, inputs, output, failure condition and owner (code, model or human). Consider automating: validate packet inputs, build, construct specification-derived packets, split streams, replay, compare JSON and summarize requirement-linked outcomes. Do not implement yet.

**You should get:** A table of proposed functions with clear contracts and explicit human decisions.

**Why:** Specified, repeatable operations suit code; missing authority and engineering judgment still need people.

## 9. Implement and test — Stage 4

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Implement the agreed helpers under `automation/`. Use readable functions, engineering explanations, actual-result logs and meaningful failure statuses. Test: original defects; valid packets and signed limits; corruption/resynchronization; empty and incomplete input; malformed CLI input; failed compilation proving a stale executable is not run. Use disposable fixtures under `automation/tests/`. Update `workflow.md` and document exact commands in `automation/README.md`. Keep the Markdown checkpoint and original evidence unchanged.

**You should get:** Working helpers with real passing/failing checks, plus instructions that actually call them. Verification helpers must not contain a replacement parser that bypasses the candidate.

**Why:** Tests show what the code handles; its completion message alone proves nothing.

## 10. Replay twice on fresh inputs

**Do this:** After Stage 4, use a host terminal in the package folder:

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


For **instructions only**, copy `workflow-md-only.md` as `workflow.md`. For **instructions plus code**, copy updated `workflow.md`, reusable `automation/` and documented dependencies. Copy no finished task implementations, demo outputs, reports, evidence or browser session state.

Start a new conversation in each workspace with the same agent/model. Ask it to read `workflow.md`, execute on current inputs and record evidence. Code mode must actually invoke the helpers. Repair the new candidate from scratch. After building, `./fw2/parser a502 2a00 f875` must produce sequence `42`, value `-2048`. Copy no finished `parser.c` or executable.

**You should get:** Two independent results checked against the same criteria. Record manual fallback and any scripts independently created in instructions-only mode.

**Why:** New inputs expose hard-coded values. The pair shows what the reusable code contributed in these cases.

## 11. Check and submit

**Do this:** Review actual evidence with the facilitator. From the repository root, the facilitator runs the protocol check on each built executable, for example:

**Host terminal — facilitator package only**:

```text
docker compose --profile facilitator run --rm grader python /opt/abb/repo/training_kit/firmware/instructor/smoke.py /workspace/work/fw2-demo/fw2/parser
```

The facilitator's independent checks and assessment sources are supplied separately from the learner materials.


Use the appropriate transfer executable path for each replay. The independent check covers 50 stream cases plus malformed input.

Submit both workflow versions, `extraction-map.md`, `automation/` with checks/README, and `evidence/`. Compare correctness, time, interventions and failures. Explain what moved into code and what still requires judgment.

**You should get:** An evidence-backed assessment with untested paths identified. A justified engineering failure or blocked input can be the correct training result.

**Why:** The facilitator assesses both your work and your explanation. One pair of replays is not a statistical benchmark.


Reference: [firmware requirements](../training_kit/firmware/requirements.md) and [firmware walkthrough](FIRMWARE_TEAM_WALKTHROUGH.md).
