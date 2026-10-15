# Hardware report and calculation contract

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

