
# FW2 Reproduce and repair a streaming parser

**Task card.** Repair the supplied C parser to satisfy its signed-value and streaming requirements. Preserve its public interface. Demonstrate the failures, explain the repair, and extract a reusable build/reproduction/verification workflow.

**Fresh demonstration entry**
**Host terminal** — in the unpacked package folder; fresh FW2 demonstration:

```text
abb doctor --offline
abb prepare fw2 demo
abb shell --workspace work/fw2-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw2-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

Read `requirements.md` before editing. A packet is `A5 02 sequence low high checksum`; the value is signed 16-bit little-endian and checksum is XOR of the first five bytes. Each CLI argument is one receive chunk in the same stream. The complete contract defines noise, invalid length, checksum failure, and resynchronization. There is no timeout requirement in this fixture.

**Allowed changes:** `fw2/parser.c`, plus common workflow/automation/evidence files. Preserve `parser.h`, `main.c`, and the specification. The compiled `fw2/parser` is a generated artifact.

## Stage 1 Guided operations
**Inside the workspace**:

```bash
gcc -std=c11 -Wall -Wextra -Werror \
  fw2/parser.c fw2/main.c -o fw2/parser
./fw2/parser a5020785ffda
./fw2/parser a50207 85ffda
```
Both invocations describe sequence 7 and value -123. Save their actual outputs. Explain why receive-chunk boundaries must not change the decoded result. Inspect the integer conversion and lifetime of partial parser state before changing code.

Make a focused repair. Rebuild and repeat the same reproductions. Then run a positive value, negative boundary, checksum error, and a valid packet following noise. Derive expected values from the specification, not the current output.

| Decision point | Evidence to explain |
| --- | --- |
| Build passes, behavior fails | Why successful compilation does not establish protocol correctness |
| Whole versus split packet | Whether state survives between feed calls |
| Signed conversion | How the same two bytes represent a negative two's-complement value |
| After repair | Which additional cases protect against a narrow example-specific fix |

**Demonstration complete:** both reproductions produce the specified result; the facilitator's protocol check passes; the participant explains the change. Use the shared documentation prompt.


# FW2 Extract build and replay tooling

Stay in the existing work/fw2-demo workspace shell for Stages 2–4. If reopening a terminal, repeat this lab's demo entry command without preparation.


## Stage 2 Abstraction focus
Parameterize source directory, compiler command, executable path, packet fields, chunk schedule, and evidence destination. Preserve the six-byte packet format, signed range, checksum definition, and streaming semantics as specification invariants.

## Stage 3 Deterministic boundary
| Move into code | Retain as reasoning |
| --- | --- |
| Compile and capture exit status/stdout/stderr | Locate the implementation defect |
| Construct packets from valid fields and split by supplied boundaries | Decide how to repair state handling without unnecessary changes |
| Replay streams and compare actual/expected objects | Resolve any future ambiguous protocol requirement |
| Produce requirement-linked verification records | Explain why the check set is adequate for this task |

## Stage 4 Required implementation behavior
Create readable build, packet construction, stream replay, and comparison functions under `automation/`. Do not put a corrected parser inside the workflow automation. The automation verifies the candidate parser; the agent still performs task-specific repairs.

Represent compilation failure separately from an incorrect decode. A failed compiler command must stop execution of an older executable. Every result must identify the source snapshot or digest, command, input bytes/chunks, expected objects, actual objects, and process result.

**Required checks:** whole/split equivalence; signed minimum and maximum; bad checksum rejected; incomplete tail emits nothing; valid frame after noise recovered; compilation failure cannot reuse a stale executable. Follow the exact resynchronization contract in requirements.md.

**Fresh transfer entries after Stage 4**
After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare fw2 transfer --name fw2-transfer-md
abb shell --workspace work/fw2-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw2-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare fw2 transfer --name fw2-transfer-code
abb shell --workspace work/fw2-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw2-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.

The fresh starters retain the defects. Use this new reproduction after building:
**Inside the workspace**:

```bash
./fw2/parser a502 2a00 f875
```
Expected result: sequence 42, value -2048. Transfer the workflow and helpers, not the repaired `parser.c` or old executable. The new agent must use the process to repair the fresh candidate.

**Facilitator protocol check**, from the training root after a learner build:
**Host terminal — facilitator package only**:

```text
python training_kit/firmware/instructor/smoke.py work/fw2-demo/fw2/parser
```

The facilitator's independent checks and assessment sources are supplied separately from the learner materials.

Use the transfer executable path for a transfer submission. The checker evaluates 50 stream cases plus malformed input. Also review the explanation and automation; a protocol pass alone does not complete the training assessment.
