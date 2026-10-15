# HW1: Check and reconcile a board data package

You will find errors in a derived netlist, justify corrections from approved sources and learn when missing authority requires you to stop.

## Before you begin

Use the Docker package and complete the [handbook](ABB_Workflow_Training.pdf) readiness checks. The image supplies all language, compiler, browser and agent tools. Record the same selected agent/model throughout.

Host commands run in the unpacked package folder. Commands marked Inside the container run in this exercise's prepared workspace. Preparation is for fresh work; resume by re-entering the existing workspace.

Keep `source/` and supplied tools unchanged. Change only supported facts in `derived/netlist.json`, your report and your learning artifacts.

Tell the agent:

> Work with me one operation at a time. Explain its purpose and expected result, then wait for my explanation before continuing. Record actual commands, observations and decisions in evidence/session.md. Do not create reusable automation until Stage 4.

Expected results below describe the supplied examples. Save actual output; if it differs, explain or resolve the difference before proceeding.

## 1. Prepare and identify the approved sources

**Do this:** Use the host-side fresh entry below:

**Host terminal** — in the unpacked package folder; fresh HW1 demonstration:

```text
docker compose up -d training
docker compose exec training abb prepare hw1 demo
docker compose exec --workdir /workspace/work/hw1-demo training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/hw1-demo
```

This opens a local container shell; it requires no SSH account or container password. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. `exit` returns to the host. To resume in a new terminal, return to the package folder, run `docker compose up -d training`, and repeat the exact entry command above without preparation. If the directory is wrong, check `pwd` and re-enter the stated workspace. A stopped service is recovered with `docker compose up -d training`; a missing workspace needs its original volume or a deliberately fresh attempt. Normal `docker compose stop training` and `up -d training` preserve work.

**Inside the container**:

```bash
cat REPORT_CONTRACT.md
python -m json.tool source/approval.json
cat source/bom.csv
python -m json.tool source/schematic.json
python -m json.tool derived/netlist.json
```


Run the inspections one at a time; record which source owns each fact.

**You should get:** The demo board is `SENSE-ALPHA`, approved revision `R7`. BOM and schematic declare that board and revision. BOM supplies component identity/value; schematic supplies pin connections. The netlist is derived output.

**Why:** You need a defensible source of truth before deciding that an export is wrong. Approval’s expected revision cannot fill in a missing revision on a source.

## 2. Compare component values by identity

**Do this:** Match components using reference designators such as `R1`, not their positions in arrays. Compare source and netlist values after explicit unit conversion. Record each observed pair before changing anything.

**You should get:** `R1` is `4.7 kOhm` in the approved source but `10 kOhm` in the netlist: a genuine mismatch. `C1` is `100 nF` versus `0.1 uF`: equivalent quantities, not a defect.

**Why:** Reordering and different unit notation must not create false engineering discrepancies.

## 3. Compare the pin connections

**Do this:** Match each component’s pins by pin number and compare net names with the schematic. Record the exact source and derived fields.

**You should get:** For `U1`, source pin `2` is `SENSE` and pin `3` is `GND`; the netlist has them swapped. Other supported connections agree.

**Why:** Correct values alone do not establish correct connectivity.

## 4. Correct only supported discrepancies

**Do this:** Save a before-copy of the netlist in `evidence/`. Write a discrepancy plan, then correct the R1 value and U1 pin mapping in the derived netlist. Keep equivalent C1 notation and unrelated fields. Re-read and compare again. Write `report.json` using `REPORT_CONTRACT.md`, keeping resolved findings and exact evidence.

**You should get:** No unresolved value/pin discrepancies. Demo report status `pass`, with findings `value_mismatch`, `pin_mapping_mismatch` and `equivalent_notation`; `changed_files` contains only `derived/netlist.json`. Approved sources are unchanged.

**Why:** A correction is justified by approved evidence, not by making files look alike. The report must still explain what was wrong and what changed.

## 5. Document the demonstrated process — finish Stage 1

**Do this:** Ask the agent to reconstruct our actual work as `workflow.md`: goal, inputs, ordered steps, reasons, evidence, decisions, recovery and completion criteria. Review it against `evidence/session.md`.

**You should get:** A procedure supported by our actual observations. Resolve a blocked demonstration with the facilitator before treating it as a successful procedure.

**Why:** The next stages must reuse a demonstrated process, including what went wrong.

## 6. Generalize the instructions — Stage 2

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Replace example-specific details with inputs: package/source/report paths and approved board/revision read from the current package. Define input sources, validation and missing-input behavior. Keep genuine engineering rules. Save `workflow.md` and an identical `workflow-md-only.md` checkpoint.

**You should get:** Instructions another engineer can follow without the original conversation.

**Why:** A workflow must work with new values rather than repeat the demonstration’s answer.

## 7. Decide what becomes code — Stage 3

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Write `extraction-map.md`: each operation’s purpose, inputs, output, failure condition and owner (code, model or human). Consider automating: inventory and provenance validation, component indexing, dimensional unit conversion, pin comparison, optional supported corrections and report generation. Do not implement yet.

**You should get:** A table of proposed functions with clear contracts and explicit human decisions.

**Why:** Specified, repeatable operations suit code; missing authority and engineering judgment still need people.

## 8. Implement and test — Stage 4

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Implement the agreed helpers under `automation/`. Use readable functions, engineering explanations, actual-result logs and meaningful failure statuses. Test: 100 nF equals 0.1 uF; wrong resistor value; wrong pin map; reordered components; missing revision; missing component; blocked checks preserving derived data. Use disposable fixtures under `automation/tests/`. Update `workflow.md` and document exact commands in `automation/README.md`. Keep the Markdown checkpoint and original evidence unchanged.

**You should get:** Working helpers with real passing/failing checks, plus instructions that actually call them. Reject unknown units and conflicting source facts instead of guessing.

**Why:** Tests show what the code handles; its completion message alone proves nothing.

## 9. Replay twice on fresh inputs

**Do this:** After Stage 4, use a host terminal in the package folder:

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
docker compose up -d training
docker compose exec training abb prepare hw1 transfer --name hw1-transfer-md
docker compose exec --workdir /workspace/work/hw1-transfer-md training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/hw1-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
docker compose up -d training
docker compose exec training abb prepare hw1 transfer --name hw1-transfer-code
docker compose exec --workdir /workspace/work/hw1-transfer-code training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/hw1-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.


For **instructions only**, copy `workflow-md-only.md` as `workflow.md`. For **instructions plus code**, copy updated `workflow.md`, reusable `automation/` and documented dependencies. Copy no finished task implementations, demo outputs, reports, evidence or browser session state.

Start a new conversation in each workspace with the same agent/model. Ask it to read `workflow.md`, execute on current inputs and record evidence. Code mode must actually invoke the helpers. The transfer deliberately omits a required source revision. Expect status `blocked`, finding `missing_source_revision`, a request for the explicitly revisioned approved source and `changed_files: []`. Leave the netlist byte-for-byte unchanged. Do not infer the missing revision from approval or the demo.

**You should get:** Two independent results checked against the same criteria. Record manual fallback and any scripts independently created in instructions-only mode.

**Why:** New inputs expose hard-coded values. The pair shows what the reusable code contributed in these cases.

## 10. Check and submit

**Do this:** Review actual evidence with the facilitator. Use the host-side fresh entry below:

**Host terminal — facilitator package only**:

```text
docker compose --profile facilitator run --rm grader python /opt/abb/repo/training_kit/hardware/instructor/check.py --lab hw1 --case demo --workspace /workspace/work/hw1-demo
```

The facilitator's independent checks and assessment sources are supplied separately from the learner materials.


For each replay use `--case transfer` and its actual workspace. A passing instructor check can accept the correctly blocked transfer; it does not certify that board data.

Submit both workflow versions, `extraction-map.md`, `automation/` with checks/README, and `evidence/`. Hardware labs also submit `report.json`. Compare correctness, time, interventions and failures. Explain what moved into code and what still requires judgment.

**You should get:** An evidence-backed assessment with untested paths identified. A justified engineering failure or blocked input can be the correct training result.

**Why:** The facilitator assesses both your work and your explanation. One pair of replays is not a statistical benchmark.


Reference: [report contract](../training_kit/hardware/REPORT_CONTRACT.md) and [hardware walkthrough](HARDWARE_TEAM_WALKTHROUGH.md).
