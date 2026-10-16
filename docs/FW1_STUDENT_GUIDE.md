# FW1: Restore device communication, then make the process reusable

You will diagnose a simulated communication problem, preserve the original state, make one justified change and verify recovery.

## Before you begin

Follow the [virtual environment setup](../README.md) and complete the [handbook](ABB_Workflow_Training.pdf) readiness checks. Activate `.venv` before running commands. Record the same selected agent/model throughout.

Host commands run in the unpacked package folder. Commands marked Inside the workspace run in this exercise's prepared workspace. Preparation is for fresh work; resume by re-entering the existing workspace.

Change device configuration only through the supplied device command. Keep the simulator, `fw1/expected.json` and direct state JSON unchanged. Create your own workflow, evidence and later automation files.

Tell the agent:

> Work with me one operation at a time. Explain its purpose and expected result, then wait for my explanation before continuing. Record actual commands, observations and decisions in evidence/session.md. Do not create reusable automation until Stage 4.

Expected results below describe the supplied examples. Save actual output; if it differs, explain or resolve the difference before proceeding.

## 1. Prepare the faulty device

**Do this:** Use the host-side fresh entry below:

**Host terminal** — in the unpacked package folder; fresh FW1 demonstration:

```text
abb doctor --offline
abb prepare fw1 demo
abb shell --workspace work/fw1-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw1-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

**Inside the workspace**:

```bash
cat requirements.md
```


Start the coding agent here. Preparation already initializes `device/`; do not initialize it again.

**You should get:** A fresh workspace with a simulated device and requirements. There is a communication problem to investigate.

**Why:** A clean starting point makes the before/after evidence meaningful.

## 2. Find out which device you have

**Do this:** Run and inspect these one at a time; save their outputs under `evidence/`:

**Inside the workspace**:

```bash
python fw1/device.py --workdir device read --field identity
python fw1/device.py --workdir device read --field firmware
python fw1/device.py --workdir device read --field config
```

**You should get:** In the supplied demo: device `SIM-017`, firmware `1.4.2`, baud rate `9600`.

**Why:** You need the observed identity to choose the right reference, and the original configuration before you change it.

## 3. Prove and record the problem

**Do this:** Run each operation and retain its complete output:

**Inside the workspace**:

```bash
python fw1/device.py --workdir device read --field faults
python fw1/device.py --workdir device logs
python fw1/device.py --workdir device probe
```

Explain what each result adds to the diagnosis.

**You should get:** `LINK_TIMEOUT`, a historical boot timeout and a probe result with `ok: false` and `status: "timeout"`. The command itself may exit successfully even though communication failed.

**Why:** A successful command invocation and successful engineering behavior are different things. The observations establish the original fault.

## 4. Match the reference and save the baseline

**Do this:** Inspect the reference:

**Inside the workspace**:

```bash
python -m json.tool fw1/expected.json
```

Select its entry using the observed device identity. Ask the agent to save the original identity, firmware, configuration, faults and logs in `evidence/baseline.json`; retain the raw reads and failed probe too. Read the saved baseline back before authorizing a write.

**You should get:** The reference for `SIM-017` requires baud `19200`; observed baud is `9600`. A complete baseline exists on disk before any change. If a required read or evidence write failed, stop.

**Why:** The mismatch supports a specific hypothesis. Persisting the baseline protects the evidence needed to explain the later result.

## 5. Make one supported change

**Do this:** Inspect help, then confirm the target from your reference before running the write:

**Inside the workspace**:

```bash
python fw1/device.py --workdir device set --help
python fw1/device.py --workdir device set --parameter baud --value 19200
```

Save the mutation response. `19200` is the supplied demo’s value, not a universal setting.

**You should get:** A response recording `old: 9600`, `new: 19200`. Only one configuration change has been made.

**Why:** A minimal, justified experiment lets you connect the changed parameter to the observed recovery.

## 6. Verify recovery with fresh observations

**Do this:** Read configuration, faults and probe again, then inspect logs:

**Inside the workspace**:

```bash
python fw1/device.py --workdir device read --field config
python fw1/device.py --workdir device read --field faults
python fw1/device.py --workdir device probe
python fw1/device.py --workdir device logs
```

Save separate after-files; keep the originals.

**You should get:** Baud `19200`, no active faults and a probe with `ok: true`, `status: "reply"`. History still contains the original timeout plus one baud-change entry.

**Why:** Current observations demonstrate recovery. A retained historical timeout is not an active fault.

## 7. Document the demonstrated process — finish Stage 1

**Do this:** Ask the agent to reconstruct our actual work as `workflow.md`: goal, inputs, ordered steps, reasons, evidence, decisions, recovery and completion criteria. Review it against `evidence/session.md`.

**You should get:** A procedure supported by our actual observations. Resolve a blocked demonstration with the facilitator before treating it as a successful procedure.

**Why:** The next stages must reuse a demonstrated process, including what went wrong.

## 8. Generalize the instructions — Stage 2

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Replace example-specific details with inputs: tool/state/reference paths, observed identity and evidence destination; derive required baud from the matching reference. Define input sources, validation and missing-input behavior. Keep genuine engineering rules. Save `workflow.md` and an identical `workflow-md-only.md` checkpoint.

**You should get:** Instructions another engineer can follow without the original conversation.

**Why:** A workflow must work with new values rather than repeat the demonstration’s answer.

## 9. Decide what becomes code — Stage 3

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Write `extraction-map.md`: each operation’s purpose, inputs, output, failure condition and owner (code, model or human). Consider automating: capture state, validate completeness, match reference, require a current same-device baseline before one allowed change, capture after-state and compare recovery. Do not implement yet.

**You should get:** A table of proposed functions with clear contracts and explicit human decisions.

**Why:** Specified, repeatable operations suit code; missing authority and engineering judgment still need people.

## 10. Implement and test — Stage 4

Stay in the existing workspace shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Implement the agreed helpers under `automation/`. Use readable functions, engineering explanations, actual-result logs and meaningful failure statuses. Test: valid capture; missing state; failed required read or evidence save; unknown identity; absent/stale baseline; one-change recovery; repeat execution preserving the original records. Use disposable fixtures under `automation/tests/`. Update `workflow.md` and document exact commands in `automation/README.md`. Keep the Markdown checkpoint and original evidence unchanged.

**You should get:** Working helpers with real passing/failing checks, plus instructions that actually call them. Internal logs should use fresh destinations; do not freeze the append-only session journal as an immutable file.

**Why:** Tests show what the code handles; its completion message alone proves nothing.

## 11. Replay twice on fresh inputs

**Do this:** After Stage 4, use a host terminal in the package folder:

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare fw1 transfer --name fw1-transfer-md
abb shell --workspace work/fw1-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw1-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare fw1 transfer --name fw1-transfer-code
abb shell --workspace work/fw1-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw1-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.


For **instructions only**, copy `workflow-md-only.md` as `workflow.md`. For **instructions plus code**, copy updated `workflow.md`, reusable `automation/` and documented dependencies. Copy no finished task implementations, demo outputs, reports, evidence or browser session state.

Start a new conversation in each workspace with the same agent/model. Ask it to read `workflow.md`, execute on current inputs and record evidence. Code mode must actually invoke the helpers. The supplied transfer starts at `9600` on device `SIM-083`, whose reference requires `38400`. Discover this from current evidence; do not carry over `19200` or the demo’s device state.

**You should get:** Two independent results checked against the same criteria. Record manual fallback and any scripts independently created in instructions-only mode.

**Why:** New inputs expose hard-coded values. The pair shows what the reusable code contributed in these cases.

## 12. Check and submit

**Do this:** Review actual evidence with the facilitator. Check baseline-before-write, identity-matched reference, exactly one recorded change and a fresh successful probe. Use the handbook’s FW1 acceptance criteria.

Submit both workflow versions, `extraction-map.md`, `automation/` with checks/README, and `evidence/`. Compare correctness, time, interventions and failures. Explain what moved into code and what still requires judgment.

**You should get:** An evidence-backed assessment with untested paths identified. A justified engineering failure or blocked input can be the correct training result.

**Why:** The facilitator assesses both your work and your explanation. One pair of replays is not a statistical benchmark.


Reference: [firmware requirements](../training_kit/firmware/requirements.md) and [firmware walkthrough](FIRMWARE_TEAM_WALKTHROUGH.md).
