
# HW2 Calculate limits and refresh calibration

**Task card.** Review an idealized voltage-divider input against its ADC voltage limit, then regenerate stale nominal calibration from the current inputs. Report the design assessment independently of whether the file generator ran successfully.

**Prepare from the training root**
```bash
python materials/prepare_lab.py hw2 demo work/hw2-demo
cd work/hw2-demo
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
```bash
python tools/generate_calibration.py --config source/circuit.json \
  --output derived/calibration.json --replace
```
**Demonstration complete:** all eight quantities recorded, voltage limit evaluated, calibration regenerated and checked, report.json written with assumptions and evidence. Now document the observed workflow.


# HW2 Extract calculations and freshness checks

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

**Transfer preparation, from the training root**
```bash
python materials/prepare_lab.py hw2 transfer work/hw2-transfer-md
python materials/prepare_lab.py hw2 transfer work/hw2-transfer-code
```
The upper resistor changes. Use current inputs for every calculation. Correct transfer behavior produces a design assessment of fail when the worst-case voltage exceeds the stated limit, while recording accurate recalculation and calibration provenance.

**Facilitator check**, from the training root:
```bash
python materials/hardware/instructor/check.py \
  --lab hw2 --case demo --workspace work/hw2-demo
```
Change case/workspace for transfer. The check validates numerical results and artifact provenance; it does not certify physical hardware. Compare the documented assumptions and engineering explanation as part of assessment.

**Debrief:** which parts of the calculation previously consumed model reasoning despite having a fully specified deterministic answer?
