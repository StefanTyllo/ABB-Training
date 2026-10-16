
# HW2 Calculate limits and refresh calibration

**Task card.** Review an idealized voltage-divider input against its ADC voltage limit, then regenerate stale nominal calibration from the current inputs. Report the design assessment independently of whether the file generator ran successfully.

**Fresh demonstration entry**
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
python -m json.tool source/circuit.json
python -m json.tool derived/calibration.json
```

**Model contract:** ideal source; upper resistor Rt and lower resistor Rb; nominal capacitor C from divider node to ground; ideal high-impedance ADC. Independent resistor tolerances are +/-t. No ADC loading, sampling transient, leakage, temperature drift, or capacitor tolerance is included. Source values use SI units. These assumptions bound the exercise.

**Allowed changes:** `derived/calibration.json`, `report.json`, and common artifacts. Preserve source/circuit.json and tools/. Use REPORT_CONTRACT.md for report fields and precision.

## Stage 1 Guided operations
Calculate one quantity at a time in the terminal, explaining the equation before running it. Read values from the actual source, even when using a short Python expression.

| Quantity | Required equation |
| --- | --- |
| Nominal gain | Rb / (Rt + Rb) |
| Maximum gain | Rb*(1+t) / (Rt*(1-t) + Rb*(1+t)) |
| Nominal / maximum ADC voltage | Maximum input voltage multiplied by the corresponding gain |
| Equivalent resistance | Rt*Rb / (Rt+Rb) |
| Nominal cutoff | 1 / (2*pi*equivalent resistance*C) |
| Inverse gain | (Rt+Rb) / Rb |
| ADC margin | ADC limit minus maximum ADC voltage |

Explain why upper-resistor minimum and lower-resistor maximum maximize output. Compare the existing coefficient and provenance with current inputs. Then invoke the existing generator:
**Inside the container**:

```bash
python tools/generate_calibration.py --config source/circuit.json \
  --output derived/calibration.json --replace
```
**Demonstration complete:** all eight quantities recorded, voltage limit evaluated, calibration regenerated and checked, report.json written with assumptions and evidence. Now document the observed workflow.


# HW2 Extract calculations and freshness checks

Stay in the existing /workspace/work/hw2-demo container shell for Stages 2–4. If reopening a terminal, repeat this lab's demo entry command without preparation.


## Stage 2 Abstraction focus
All component values, tolerance, maximum input, ADC limit, and file paths are inputs. Equations and model assumptions remain explicit. Do not turn the demo's coefficient into a universal constant.

## Stage 3 Deterministic boundary
| Move into code | Retain as reasoning |
| --- | --- |
| Validate positive finite values, units, and allowed tolerance | Decide whether the ideal circuit model applies to a real design |
| Calculate quantities and intermediate values | Investigate behavior outside the model's scope |
| Compare worst-case voltage with the limit | Select a new design when a limit is exceeded |
| Regenerate calibration and compare source digest | Approve changes to engineering assumptions |

## Stage 4 Required implementation behavior
Create a calculation entry point that accepts a source JSON path and report destination. Give each equation a named function or clearly named intermediate values. Log units, substituted values, calculated results, source revision, and limits. Use the existing calibration generator; do not recreate its file format inconsistently.

Validate freshness using the canonical source digest specified in REPORT_CONTRACT.md. A design-limit failure must remain visible even if nominal calibration was regenerated correctly. The exercise asks for assessment of the supplied design, not redesign to force a pass.

**Required checks:** valid demo; worst-case limit violation; invalid/missing input; changed input invalidates old calibration provenance; regeneration is repeatable for identical input. The source JSON must remain unchanged.

**Fresh transfer entries after Stage 4**
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

The upper resistor changes. Use current inputs for every calculation. Correct transfer behavior produces a design assessment of fail when the worst-case voltage exceeds the stated limit, while recording accurate recalculation and calibration provenance.

**Facilitator check**, from the training root:
**Host terminal — facilitator package only**:

```text
docker compose --profile facilitator run --rm grader python /opt/abb/repo/training_kit/hardware/instructor/check.py --lab hw2 --case demo --workspace /workspace/work/hw2-demo
```

The facilitator's independent checks and assessment sources are supplied separately from the learner materials.

Change case/workspace for transfer. The check validates numerical results and artifact provenance; it does not certify physical hardware. Compare the documented assumptions and engineering explanation as part of assessment.

**Debrief:** which parts of the calculation previously consumed model reasoning despite having a fully specified deterministic answer?
