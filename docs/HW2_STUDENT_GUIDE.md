# HW2: Calculate the ADC limit and refresh stale calibration

You will calculate an ideal voltage divider’s worst-case output, assess its ADC limit and regenerate calibration without confusing file-generation success with design safety.

## Before you begin

Use the Docker package and complete the [handbook](ABB_Workflow_Training.pdf) readiness checks. The image supplies all language, compiler, browser and agent tools. Record the same selected agent/model throughout.

Host commands run in the unpacked package folder. Commands marked Inside the container run in this exercise's prepared workspace. Preparation is for fresh work; resume by re-entering the existing workspace.

Preserve `source/circuit.json` and supplied tools. You may regenerate `derived/calibration.json` and create the report and learning artifacts. Do not redesign the source to force a pass.

Tell the agent:

> Work with me one operation at a time. Explain its purpose and expected result, then wait for my explanation before continuing. Record actual commands, observations and decisions in evidence/session.md. Do not create reusable automation until Stage 4.

Expected results below describe the supplied examples. Save actual output; if it differs, explain or resolve the difference before proceeding.

## 1. Prepare and read the current inputs

**Do this:** Use the host-side fresh entry below:

**Host terminal** — in the unpacked package folder; fresh HW2 demonstration:

```text
docker compose up -d training
docker compose exec training abb prepare hw2 demo
docker compose exec --workdir /workspace/work/hw2-demo training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/hw2-demo
```

This opens a local container shell; it requires no SSH account or container password. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. `exit` returns to the host. To resume in a new terminal, return to the package folder, run `docker compose up -d training`, and repeat the exact entry command above without preparation. If the directory is wrong, check `pwd` and re-enter the stated workspace. A stopped service is recovered with `docker compose up -d training`; a missing workspace needs its original volume or a deliberately fresh attempt. Normal `docker compose stop training` and `up -d training` preserve work.

**Inside the container**:

```bash
cat REPORT_CONTRACT.md
python -m json.tool source/circuit.json
python -m json.tool derived/calibration.json
```


Record actual values and save the original calibration under `evidence/`.

**You should get:** Demo: board `DIVIDER-ALPHA`, revision `D3`, upper resistor 100000 ohm, lower resistor 10000 ohm, tolerance 0.01, capacitor 1e-7 F, maximum input 30 V and ADC limit 3.3 V. Existing calibration is stale: revision `D2`, inverse gain `10` and a zero digest.

**Why:** Current source inputs and their provenance determine calculations. An existing generated file may describe an older circuit.

## 2. Explain and calculate one quantity at a time

**Do this:** Ask the agent to evaluate each equation in the terminal using values read from `source/circuit.json`. Explain the equation before running it. Save substituted values, units and full-precision results.

| Quantity | Equation | Approximate demo result |
|---|---|---:|
| Nominal gain | `Rb / (Rt + Rb)` | 0.09090909 |
| Worst-case gain | `Rb*(1+t) / (Rt*(1-t) + Rb*(1+t))` | 0.09257562 |
| Nominal ADC voltage | `vin_max_v * nominal_gain` | 2.72727273 V |
| Worst-case ADC voltage | `vin_max_v * worst_case_gain` | 2.77726856 V |
| Equivalent resistance | `Rt*Rb / (Rt+Rb)` | 9090.90909 ohm |
| Nominal cutoff | `1 / (2*pi*r_th_ohm*C)` | 175.07044 Hz |
| Inverse gain | `(Rt+Rb) / Rb` | 11 |
| ADC margin | `adc_max_v - worst_case_adc_v` | 0.52273144 V |

Use the report’s exact key names and retain at least 10 significant digits; this table is rounded for reading.

**You should get:** All eight computed quantities. Explain why the upper resistor at minimum and lower resistor at maximum produce the highest output.

**Why:** Worst-case arithmetic can reveal a limit violation that nominal arithmetic misses.

## 3. Make the engineering assessment

**Do this:** Compare the unrounded worst-case ADC voltage with `adc_max_v`. Record the model assumptions and limits in the report.

**You should get:** The demo is an engineering `pass`: approximately 2.77727 V is below 3.3 V. Equality would also pass; exceeding the limit must produce `fail`.

**Why:** This decision comes from the worst-case model. It is separate from whether a calibration file can be generated. Loading, sampling transients, leakage, temperature drift and capacitor tolerance are outside this model.

## 4. Regenerate and verify calibration

**Do this:** Use the existing generator, then inspect its output:

**Inside the container**:

```bash
python tools/generate_calibration.py --config source/circuit.json --output derived/calibration.json --replace
python -m json.tool derived/calibration.json
```

Compare board/revision, inverse gain and the canonical source digest using `REPORT_CONTRACT.md`. Write `report.json` with all eight calculations, assumptions, `stale_calibration` evidence and the assessment.

**You should get:** Current board `DIVIDER-ALPHA`, revision `D3`, inverse gain `11` and the digest of the current canonical source JSON. Report `changed_files` contains `derived/calibration.json`. Source inputs remain unchanged.

**Why:** The generator emits nominal calibration; it does not judge worst-case safety. Provenance links the coefficient to the actual inputs, rather than a timestamp.

## 5. Document the demonstrated process — finish Stage 1

**Do this:** Ask the agent to reconstruct our actual work as `workflow.md`: goal, inputs, ordered steps, reasons, evidence, decisions, recovery and completion criteria. Review it against `evidence/session.md`.

**You should get:** A procedure supported by our actual observations. Resolve a blocked demonstration with the facilitator before treating it as a successful procedure.

**Why:** The next stages must reuse a demonstrated process, including what went wrong.

## 6. Generalize the instructions — Stage 2

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Replace example-specific details with inputs: every component value, tolerance, input/ADC voltage, source path and report/calibration destination. Define input sources, validation and missing-input behavior. Keep genuine engineering rules. Save `workflow.md` and an identical `workflow-md-only.md` checkpoint.

**You should get:** Instructions another engineer can follow without the original conversation.

**Why:** A workflow must work with new values rather than repeat the demonstration’s answer.

## 7. Decide what becomes code — Stage 3

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Write `extraction-map.md`: each operation’s purpose, inputs, output, failure condition and owner (code, model or human). Consider automating: validate finite positive inputs and 0 < tolerance < 1, calculate named intermediate quantities, assess the limit, invoke the supplied generator, check canonical provenance and write the report. Do not implement yet.

**You should get:** A table of proposed functions with clear contracts and explicit human decisions.

**Why:** Specified, repeatable operations suit code; missing authority and engineering judgment still need people.

## 8. Implement and test — Stage 4

Stay in the existing container shell. If reopening a terminal, repeat the demo entry command without preparation.

**Do this:** Implement the agreed helpers under `automation/`. Use readable functions, engineering explanations, actual-result logs and meaningful failure statuses. Test: valid demo; worst-case limit violation; missing/invalid input; changed source invalidating old calibration provenance; identical inputs producing identical regenerated calibration; unchanged source. Use disposable fixtures under `automation/tests/`. Update `workflow.md` and document exact commands in `automation/README.md`. Keep the Markdown checkpoint and original evidence unchanged.

**You should get:** Working helpers with real passing/failing checks, plus instructions that actually call them. A successful calibration subprocess must never erase the separate design-failure status.

**Why:** Tests show what the code handles; its completion message alone proves nothing.

## 9. Replay twice on fresh inputs

**Do this:** After Stage 4, use a host terminal in the package folder:

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
docker compose up -d training
docker compose exec training abb prepare hw2 transfer --name hw2-transfer-md
docker compose exec --workdir /workspace/work/hw2-transfer-md training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/hw2-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
docker compose up -d training
docker compose exec training abb prepare hw2 transfer --name hw2-transfer-code
docker compose exec --workdir /workspace/work/hw2-transfer-code training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/hw2-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.


For **instructions only**, copy `workflow-md-only.md` as `workflow.md`. For **instructions plus code**, copy updated `workflow.md`, reusable `automation/` and documented dependencies. Copy no finished task implementations, demo outputs, reports, evidence or browser session state.

Start a new conversation in each workspace with the same agent/model. Ask it to read `workflow.md`, execute on current inputs and record evidence. Code mode must actually invoke the helpers. The transfer upper resistor is 82000 ohm. Recalculate from its actual inputs: worst-case ADC voltage is approximately 3.31946 V, above 3.3 V, so report engineering `fail` with `adc_limit_exceeded`. Regenerate nominal calibration with inverse gain `9.2` and current provenance while keeping the design failure visible.

**You should get:** Two independent results checked against the same criteria. Record manual fallback and any scripts independently created in instructions-only mode.

**Why:** New inputs expose hard-coded values. The pair shows what the reusable code contributed in these cases.

## 10. Check and submit

**Do this:** Review actual evidence with the facilitator. Use the host-side fresh entry below:

**Host terminal — facilitator package only**:

```text
docker compose --profile facilitator run --rm grader python -m pytest /opt/abb/repo/tests/container -q
```

The facilitator's independent checks and assessment sources are supplied separately from the learner materials.


For each replay use `--case transfer` and its actual workspace. A passing instructor check means the calculations/provenance and reported assessment are correct, including the transfer’s design failure.

Submit both workflow versions, `extraction-map.md`, `automation/` with checks/README, and `evidence/`. Hardware labs also submit `report.json`. Compare correctness, time, interventions and failures. Explain what moved into code and what still requires judgment.

**You should get:** An evidence-backed assessment with untested paths identified. A justified engineering failure or blocked input can be the correct training result.

**Why:** The facilitator assesses both your work and your explanation. One pair of replays is not a statistical benchmark.


Reference: [report contract](../training_kit/hardware/REPORT_CONTRACT.md) and [hardware walkthrough](HARDWARE_TEAM_WALKTHROUGH.md).
