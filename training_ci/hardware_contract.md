# Generated hardware guardrails: CI contract

This contract is for the code-implementation stage after the guided task, workflow extraction, abstraction, and deterministic-boundary review. It specifies the entry point evaluated by CI; it does not replace those learning stages. Implement the calculations/comparisons yourself using the supplied sources and low-level calibration tool. Do not read, copy, modify, or invoke instructor answers or graders from learner code.

## Entry point and ownership

Create `automation/guardrails.py` runnable with Python 3 and its standard library:

```bash
python automation/guardrails.py --workspace /absolute/path/to/prepared/workspace
```

Resolve every data/output path against `--workspace`, not the current directory. Infer the lab from its source files: HW1 has `source/approval.json`, `source/bom.csv`, and `source/schematic.json`; HW2 has `source/circuit.json`. Reject ambiguous or missing required input. The board ID must come from source data. The fixed synthetic fixture bookkeeping is `SENSE-ALPHA` / `DIVIDER-ALPHA` = `demo`, and `SENSE-BETA` / `DIVIDER-BETA` = `transfer`. This map sets the report's `case` only; never use identity, case, filenames, or cached answers to select engineering results. Calculate and compare actual source values.

Allowed outputs are `report.json`, `evidence/`, learner code/checks under `automation/`, and the lab's single derived artifact: HW1 `derived/netlist.json`, HW2 `derived/calibration.json`. Preserve all source files, supplied tools, and REPORT_CONTRACT.md. No network or external packages are needed. Tests requiring altered inputs must create disposable fixtures under `automation/tests/`; they must not edit the prepared source inputs.

| Engineering assessment | Helper exit code | Meaning |
|---|---:|---|
| `pass` | 0 | Assessment is complete and the task's engineering criteria pass |
| `fail` | 1 | Assessment is complete but the circuit exceeds its stated design limit or another engineering criterion fails |
| `blocked` | 2 | Missing/invalid authority or input prevents assessment |

The external grader returns 0 for a faithful accepted assessment, including expected engineering `fail` and `blocked`. Its default `--mode code` invokes your helper twice, runs the existing independent instructor checker after each invocation, and requires unchanged bytes in `report.json` and the derived artifact on the second invocation. `--mode md-only` checks the already-completed report and derived artifact once using the same instructor checker; it neither requires nor executes a helper and does not impose the code-run idempotence check. Use MD-only mode for the fresh Markdown-only transfer and code mode for the demonstration after stage 4 and fresh code-assisted transfer. Logs under `evidence/` may grow. Do not add timestamps, run counters, transient command output, or changing absolute paths to stable task artifacts.

Retain initial discrepancy findings, evidence, and `changed_files` as a cumulative task audit on repeat runs for the same source inputs. A resolved discrepancy remains documented; `changed_files` records artifacts changed during this task, not only writes in the latest invocation. Preserve evidence of the original values before correction. Validate any reused report against current source identity/revision/content and verify the current derived artifact; do not blindly trust an old `pass` or stale report. If the same task is already correctly reconciled and assessed, preserve its stable report. Start a new report when source inputs change, retaining prior evidence separately.

## Exact task report

Write UTF-8 `report.json` as a JSON object matching the prepared `REPORT_CONTRACT.md`. This task report is distinct from optional operation-event logs.

| Field | Required content |
|---|---|
| `schema_version` | Integer 1 |
| `lab` | `hw1` or `hw2` |
| `case` | `demo` or `transfer`, using fixture bookkeeping above |
| `board_id` | The actual source board ID |
| `status` | Engineering `pass`, `fail`, or `blocked` |
| `findings` | Array of objects containing `code`, nonempty `evidence`, nonempty `explanation`; include `ref` for component findings |
| `changed_files` | Array of relative derived artifact paths changed during the task; no report, logs, code, or workflow files |
| `assumptions` | Nonempty array describing source authority or model limits |
| `calculations` | HW2 only: all eight numeric fields below, retaining at least 10 significant digits |

Finding evidence must identify actual source/export fields and observed before/after values. Informative messages or equivalent-unit notation are findings without being engineering failures. Do not fabricate findings on a clean unrelated input.

## HW1 behavior

Read `approval.json` for the expected board, approved revision, and approved source list. BOM is authoritative for component identity, kind, and value; the schematic is authoritative for pins and corroborates values. Every source must independently declare the expected board and revision. Missing source revision blocks before modifying the netlist; an approval's expected revision is not evidence for an absent source revision. Conflicting approved facts require resolution by the authority, not a guessed export correction.

Match components by reference designator and pins by pin number, not file order. Parse quantities dimensionally: `kOhm` = 1000 ohms, `Ohm` = ohms, `nF` = 1e-9 F, `uF` = 1e-6 F, `F` = F. Reject unsupported units; IC identifiers remain literal strings. Detect missing/duplicate references and mismatched pin sets. Correct only discrepancies fully supported by valid source evidence, preserving all unrelated data and equivalent notation.

Required seeded-demo finding codes are `value_mismatch`, `pin_mapping_mismatch`, and `equivalent_notation`; after reconciliation the engineering status is `pass`, exit 0, and `changed_files` is `["derived/netlist.json"]`. The seeded transfer is blocked by missing source revision: include `missing_source_revision`, explain which approved source is needed, leave the netlist byte-for-byte unchanged, use `changed_files: []`, status `blocked`, and exit 2. Do not invent recovery evidence. These seeded outcomes are acceptance expectations; derive them from the actual evidence.

## HW2 behavior

Input fields are SI numbers: `r_top_ohm` (Rt), `r_bottom_ohm` (Rb), `resistor_tolerance_fraction` (t), `c_farad` (C), `vin_max_v`, and `adc_max_v`, plus nonempty board/revision. Validate finite positive values and `0 < t < 1`, matching the supplied generator's supported input domain. The model uses an ideal source, unloaded divider, ideal high-impedance ADC, independent resistor tolerances, and nominal capacitor from ADC node to ground; it excludes loading, sampling transients, leakage, temperature drift, and capacitor tolerance.

| Calculation key | Equation |
|---|---|
| `nominal_gain` | `Rb / (Rt + Rb)` |
| `worst_case_gain` | `Rb*(1+t) / (Rt*(1-t) + Rb*(1+t))` |
| `nominal_adc_v` | `vin_max_v * nominal_gain` |
| `worst_case_adc_v` | `vin_max_v * worst_case_gain` |
| `r_th_ohm` | `Rt*Rb / (Rt+Rb)` |
| `cutoff_hz` | `1 / (2*pi*r_th_ohm*C)` |
| `inverse_gain` | `(Rt+Rb) / Rb` |
| `adc_margin_v` | `adc_max_v - worst_case_adc_v` |

The output is highest with upper resistor at minimum and lower resistor at maximum. Compare worst-case ADC voltage to the limit: equality passes; exceeding it fails. Preserve design failure after calibration regeneration; do not redesign sources to force a pass. Include `stale_calibration` for the seeded stale artifact, plus `adc_limit_exceeded` when the source calculation exceeds the limit.

Use the existing generator, preserving its implementation:

```bash
python tools/generate_calibration.py --config source/circuit.json --output derived/calibration.json --replace
```

Invoke this with the workspace as cwd, or pass absolute paths and use the same Python interpreter. Check the process result and verify output content. The output contains schema_version, board_id, source_revision, inverse_gain, and source_sha256. The digest is SHA-256 of UTF-8 `json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)`, including every source field. This low-level tool emits nominal calibration; it does not assess worst-case safety. Both seeded cases require `changed_files: ["derived/calibration.json"]`; demo engineering assessment passes with exit 0, transfer fails the design limit with exit 1.

## External evaluation command

Run from the checkout containing `training_ci/` and `training_kit/` (or `materials/`):

```bash
python training_ci/grade_hardware.py --lab hw1 --workspace work/hw1-demo --mode code
python training_ci/grade_hardware.py --lab hw2 --workspace work/hw2-transfer-md --mode md-only
python training_ci/grade_hardware.py --lab hw2 --workspace work/hw2-transfer-code --mode code
```

The independent instructor checker validates authoritative inputs, exact report fields, component/value/pin agreement or blocked preservation, numerical results, and calibration provenance. Numeric acceptance uses relative tolerance 1e-8 and absolute tolerance 1e-9. The grader saves its commands, real stdout/stderr, return codes, and idempotence hashes to `evidence/grade_hardware.json`. Passing this check is CI evidence for the synthetic task, not physical hardware certification or a substitute for reviewing the learning artifacts.
