# Hardware lab starters

These synthetic, standard-library-only Python 3 fixtures support two manual-first labs. No EDA software, physical board, network, or credentials are required. Results apply only to the stated ideal model and exercise evidence; they do not certify physical hardware.

The starter deliberately contains data and a nominal-calibration emitter, not a reconciliation or circuit-review solution. Keep `instructor/`, `tests/`, and the fixture masters away from learners until review. Both the Markdown-workflow and later code-workflow arms receive identical prepared data and the same low-level calibration tool.

## Prepare a fresh case

Run these commands from the `training_kit` directory. Output directories must not exist, even if empty. Preparation refuses to overwrite participant work.

```bash
python3 hardware/prepare.py --lab hw1 --case demo --output runs/hw1-demo
python3 hardware/prepare.py --lab hw1 --case transfer --output runs/hw1-transfer
python3 hardware/prepare.py --lab hw2 --case demo --output runs/hw2-demo
python3 hardware/prepare.py --lab hw2 --case transfer --output runs/hw2-transfer
```

Start with the demo. The learner executes each inspection, calculation, or edit in the terminal while Codex explains why it is needed. Capture the actions and judgment calls as a workflow, abstract case-specific names and paths, identify deterministic steps, and only then ask Codex to generate verbose automation. Do not begin by asking Codex to solve the whole directory. Use transfer only after the workflow is written.

Each prepared directory is the workspace root for paths in the report. Source files are immutable. Learners may create `report.json`, `workflow.md`, `workflow-md-only.md`, `extraction-map.md`, the session record `evidence/session.md`, and later their own implementation under `automation/`. These are the handbook's canonical handoff paths. HW1 may change only `derived/netlist.json`; HW2 may change only `derived/calibration.json`. Do not edit provided `source/` or `tools/`, the master fixtures, or instructor checks. The instructor tool is an assessment gate after submission, not a learner-side solution command.

## HW1: reconcile a board export against approved evidence

Inspect one file at a time and discuss why its role matters:

```bash
cd runs/hw1-demo
pwd
python3 -m json.tool source/approval.json
cat source/bom.csv
python3 -m json.tool source/schematic.json
python3 -m json.tool derived/netlist.json
```

`source/approval.json` identifies the approved board, revision, and source paths. It is a trust declaration for this synthetic exercise, not proof that a document with missing provenance belongs to that revision. `source/bom.csv` is authoritative for reference designator, component kind, and value. `source/schematic.json` is authoritative for pin-to-net mappings and supplies corroborating values. All source files must agree on the board and revision; conflicting values or missing provenance block reconciliation. The BOM has one component per CSV row and explicit `board_id`, `source_revision`, `ref`, `kind`, and `value` columns. JSON components have `ref`, `kind`, `value`, and `pins`; pin keys are strings.

`derived/netlist.json` is a generated export, never an authority. Compare components by reference designator and pins by pin number, not file order. Parse quantities by dimension: `kOhm` = 1,000 ohms; `nF` = 1e-9 farads; `uF` = 1e-6 farads. In particular, 100 nF and 0.1 uF are equivalent. IC part identifiers are literal strings. You may preserve equivalent notation. Correct demonstrable export discrepancies only after provenance checks pass, then re-read the modified file and compare it with both source documents.

The demo contains a resistor-value discrepancy and an IC pin-mapping discrepancy, plus harmless equivalent capacitor notation. The transfer changes board identity, reference designators, and component order and removes a schematic revision. A missing revision requires a `blocked` report and unchanged netlist. The approval record's expected revision is not permission to fill in an absent source revision. No recovery evidence is included; request an explicitly revisioned approved schematic from the design authority before continuing. Do not invent missing evidence.

## HW2: check a divider and repair stale nominal calibration

```bash
cd runs/hw2-demo
python3 -m json.tool source/circuit.json
python3 -m json.tool derived/calibration.json
python3 tools/generate_calibration.py --help
```

The trusted, immutable `source/circuit.json` uses SI numeric fields: `r_top_ohm`, `r_bottom_ohm`, `resistor_tolerance_fraction`, `c_farad`, `vin_max_v`, and `adc_max_v`, plus `board_id` and `source_revision`. Demo: 100 kOhm / 10 kOhm, independent ±1% resistors, nominal 100 nF from ADC node to ground, 30 V maximum input, and 3.3 V ADC maximum. Transfer substitutes 82 kOhm for the upper resistor. The input source and capacitor are ideal; there is no ADC loading, leakage, parasitic capacitance, sampling transient, resistor temperature drift, or capacitor tolerance in this model.

Execute the arithmetic manually before generating a workflow or code. `python3 -c 'print(10000 / (100000 + 10000))'` is a useful first terminal calculation; explain the circuit assumption before calculating the next quantity. Use input values from the case, not copied demo constants.

Required equations, where `Rt` is the upper resistor, `Rb` the lower resistor, `t` the fractional tolerance, and `C` the shunt capacitor:

| Quantity / report key | Equation |
|---|---|
| `nominal_gain` | `Rb / (Rt + Rb)` |
| `worst_case_gain` | `Rb*(1+t) / (Rt*(1-t) + Rb*(1+t))` |
| `nominal_adc_v` | `vin_max_v * nominal_gain` |
| `worst_case_adc_v` | `vin_max_v * worst_case_gain` |
| `r_th_ohm` | `Rt*Rb / (Rt+Rb)` with ideal voltage source shorted |
| `cutoff_hz` | `1 / (2*pi*r_th_ohm*C)`; nominal only |
| `inverse_gain` | `(Rt+Rb) / Rb`; reconstruct input as `ADC_voltage * inverse_gain` |
| `adc_margin_v` | `adc_max_v - worst_case_adc_v` |

The worst upper output voltage occurs at upper-resistor minimum and lower-resistor maximum. A nominal-only pass is insufficient. Report `pass` only when worst-case voltage does not exceed the ADC maximum; otherwise report `fail`. Do not modify the circuit to force a pass.

The seeded calibration coefficient is stale. Compare it and its source revision/digest to the current config. After the manual review, run the existing low-level emitter:

```bash
python3 tools/generate_calibration.py --config source/circuit.json --output derived/calibration.json --replace
python3 -m json.tool derived/calibration.json
```

This generator emits nominal `inverse_gain` plus provenance only. It does not assess voltage limits or decide pass/fail. Its Python interface is `calibration_from_config(config: dict) -> dict`; its CLI is identical in both workflow arms. `--replace` explicitly authorizes replacing a derived file; omission refuses an existing output. Invalid nonpositive or nonfinite required values fail before replacement. It also refuses output equal to input and symlink output.

`source_sha256` is SHA-256 over the UTF-8 encoding of `json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)`. The digest includes all config fields. This canonicalization ignores JSON whitespace and object-key order, but not changes to numeric representation such as `30` versus `30.0`. Regeneration is deterministic and creates no timestamps. Record a failed transfer circuit honestly even after the nominal coefficient is regenerated.

## Required `report.json` contract

Create this file manually after inspection, then let the later automation produce the same schema. There is no prefilled report in a starter.

| Key | Required value / shape |
|---|---|
| `schema_version` | Integer `1` |
| `lab`, `case` | `hw1` or `hw2`; `demo` or `transfer` |
| `board_id` | Actual source board ID, never hardcoded from demo |
| `status` | Engineering assessment: `pass`, `fail`, or `blocked` |
| `findings` | Array of objects with `code`, nonempty `evidence`, nonempty `explanation`; add `ref` for component findings |
| `changed_files` | Relative derived artifact paths changed; excludes the report, workflow documents, session evidence, and automation implementation |
| `assumptions` | Nonempty array documenting authority/model limits |
| `calculations` | HW2 only: object containing all eight numeric keys from the equations table; retain at least 10 significant digits |

Evidence should point to exact fields or rows, for example `source/schematic.json:components[ref=U1].pins` and the before/after export values. HW1 findings use `value_mismatch`, `pin_mapping_mismatch`, and `equivalent_notation`; blocked transfer uses `missing_source_revision` and explains what authoritative evidence is needed. HW2 uses `stale_calibration` and, when appropriate, `adc_limit_exceeded`. A resolved discrepancy remains in findings so the audit trail explains the changes. HW1 successful reconciliation lists `derived/netlist.json`; blocked reconciliation lists no changed artifacts. HW2 lists `derived/calibration.json` after regeneration. The report's `status` describes the engineering assessment. The instructor check passes when the submission faithfully reports and handles that assessment, including a design `fail` or evidence `blocked` outcome.

## Instructor review and verification

Run from `training_kit` after submission:

```bash
python3 hardware/instructor/check.py --lab hw1 --case demo --workspace runs/hw1-demo
python3 hardware/instructor/check.py --lab hw1 --case transfer --workspace runs/hw1-transfer
python3 hardware/instructor/check.py --lab hw2 --case demo --workspace runs/hw2-demo
python3 hardware/instructor/check.py --lab hw2 --case transfer --workspace runs/hw2-transfer
python3 -m unittest discover -s hardware/tests -v
```

The checker verifies unchanged source bytes, provenance, component sets and values, pin maps, blocked preservation, required report fields, numeric calculations, and regenerated calibration digest. It does not import learner code or the calibration generator to compute expected numeric answers. `instructor/expected.json` supplies independently calculated references; calculated floats accept relative error 1e-8 and absolute error 1e-9. A passing checker is necessary but not sufficient: the instructor also reviews reasoning, evidence quality, workflow extraction, and the later generated code's readability and deterministic boundary. Extra findings need human review.

Expected outcomes: HW1 demo fixes R1 to 4.7 kOhm and U1 pins 2=`SENSE`, 3=`GND`, while C1's equivalent notation is harmless; transfer remains blocked with unchanged derived export. HW2 demo yields inverse gain 11, nominal 2.727272727 V, worst-case 2.777268561 V, and passes. Transfer yields inverse gain 9.2, nominal 3.260869565 V, worst-case 3.319456617 V, and fails the 3.3 V limit by about 19.457 mV. Both coefficients must be regenerated from the current source.
