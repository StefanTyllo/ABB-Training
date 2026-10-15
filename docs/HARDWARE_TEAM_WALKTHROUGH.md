# Hardware team: two exercises from engineering review to reusable checks

**Audience:** hardware engineers familiar with component units and basic circuit calculations, able to run terminal commands with agent assistance. These exercises use JSON/CSV exports and an idealized circuit, not native drawing extraction or physical board measurements.

**Outcomes:** HW1 reconciles derived board data using approved sources. HW2 calculates a voltage-divider limit and regenerates stale calibration. In each exercise, demonstrate the engineering work first, extract Markdown, supplement repeatable steps with code, then evaluate a fresh case.

## Before starting

Use the [handbook](ABB_Workflow_Training.pdf) for installation, account setup and attachment extraction. The **training root** contains `.venv/`, `materials/` and `work/`. Run preparation/facilitator commands there. Keep `materials/` unchanged and use fresh output directories.

```bash
source .venv/bin/activate
python --version
```

Use Python 3.12, complete the handbook's live agent smoke tests, and record the agent/model and tool versions. Use the same agent/model in demonstration and both replay conditions. Start the agent inside the prepared workspace.

**Guided-work prompt:** “Read the exercise, requirements and report contract. Guide one operation at a time. Before executing, explain the purpose and expected evidence. Wait for my engineering explanation between operations. Record actual commands, inputs, observations and recovery in `evidence/session.md`. Do not create reusable automation before the demonstration is complete.”


**Copilot context and evidence.** Use GitHub Copilot CLI consistently, with a fresh conversation/invocation for each stage after the guided demo. Read the prepared task-card.md and pass only the saved stage inputs needed. Provide the current stage and its named inputs; keep the full card/contract available on demand. Link raw evidence instead of repeating entire transcripts. No automation/ directory exists before Stage 4; early fixtures go under evidence/stage1-fixtures/. Keep original captures immutable and evidence/session.md append-only. In Stage 4, finish required helpers/checks before optional expansion, keep workflow-md-only.md unchanged, and test caller-owned console redirection plus fresh report paths. Helper logs belong in unique run directories; a growing journal or an already-open caller log must not block valid verification. Completed device tasks are verified without a second write.

---

## HW1 — Reconcile a board data package

### 1. Prepare and establish which source owns each fact

From the training root:

```bash
python materials/prepare_lab.py hw1 demo work/hw1-demo
cd work/hw1-demo
python -m json.tool source/approval.json
cat source/bom.csv
python -m json.tool source/schematic.json
python -m json.tool derived/netlist.json
```

- **What and why:** distinguish approved inputs from a generated output that may contain errors.
- **How:** read `REPORT_CONTRACT.md`. Record the board identity, revision and required provenance on each source. Approval declares the expected board/revision; BOM owns component identity/value; schematic owns pin-to-net mapping and corroborates values. The derived netlist is the item being reviewed.
- **Failure and recovery:** missing or conflicting provenance blocks corrections. Obtain an explicitly identified approved source; an expected revision cannot fill a missing source revision.
- **Code to add later:** separate inventory/provenance validation from data comparison. Validate sources before permitting writes.
- **Evidence:** source inventory and field-level provenance support the selected authority. Preserve source files and supplied tools; edit only derived netlist, report and common workflow/automation/evidence files.

### 2. Compare equivalent facts rather than file positions

- **What and why:** identify genuine discrepancies while avoiding false differences from notation or ordering.
- **How:** match components by reference designator and pins by pin number. Convert typed quantities to common units before comparing: kOhm to ohms, nF/uF to farads. Compare IC part numbers literally. Record actual source and derived values before changes.
- **What can go wrong:** array order is mistaken for identity; 100 nF and 0.1 uF are flagged as different; an unknown unit is guessed; a missing component is silently ignored.
- **Supplement Markdown with code:** index components, normalize quantities with explicit dimensions, reject unsupported units and compare complete component/pin sets. Test reordered inputs and missing components.
- **Why it works:** comparisons concern the same physical quantity or connection, independent of serialization order. Equivalent notation is recorded as equivalent, not “corrected” as a fault.

### 3. Correct only supported derived discrepancies

- **What and why:** make every correction explainable from approved source evidence.
- **How:** prepare a discrepancy plan with the component/pin, original value, authoritative value and exact source field. Correct demonstrable value and pin-mapping errors in `derived/netlist.json`; re-read and recheck it. Create `report.json` using the contract below.
- **Failure and recovery:** do not choose arbitrarily between conflicting sources. Stop with a blocked report and request the missing authority. Do not edit approved source files to match the export.
- **Code to add later:** validate the complete plan and provenance before applying corrections; retain before/after records and report unresolved discrepancies. Rechecking a corrected demo must find no unresolved issue.
- **Acceptance and explanation:** real value/pin discrepancies are corrected, equivalent notation is recognized, sources are unchanged and each change has evidence. Keep resolved discrepancies in the report so the audit trail remains understandable.

### 4. Extract a reusable checker and verify its failure branches

After the demonstration, ask the agent to reconstruct the actual workflow. Review `workflow.md`, parameterize package/source/output paths and expected identity/revision, then preserve `workflow-md-only.md`. Write `extraction-map.md` before implementing helpers under `automation/`.

| Operation to extract | What can fail | Code response and evidence |
| --- | --- | --- |
| Inventory/provenance gate | Missing file, revision or board mismatch | Block before mutation; identify the exact missing/conflicting source |
| Component/quantity comparison | Wrong value, unknown unit, missing component | Explicit finding with source/derived fields; no guessed conversion |
| Pin comparison | Wrong net or missing pin | Match by component/pin identity and report the difference |
| Optional correction/report | Unsupported correction or incomplete plan | Refuse the write; preserve before/after and all findings when allowed |

Keep authority disputes and future ambiguous drawings with the engineer. Implement readable functions and independent fixtures under `automation/tests/`; do not make helper tests depend on the active demo's component references. Update `workflow.md` and `automation/README.md` with exact entry points and dependencies.

**Required checks:** equivalent 100 nF/0.1 uF; wrong resistor value; wrong pin mapping; reordered components; missing source revision; missing component. Verify blocked checks leave derived data unchanged. These checks show that code enforces the stated comparison rules; it cannot manufacture missing approval evidence.

### 5. Transfer to a package with missing authority

Return to the training root:

```bash
python materials/prepare_lab.py hw1 transfer work/hw1-transfer-md
python materials/prepare_lab.py hw1 transfer work/hw1-transfer-code
```

Follow the paired replay procedure below. This package changes board identity and component references/order and omits a required source revision. No recovery evidence is supplied.

**Correct outcome:** report `blocked`, identify the missing source revision, request an approved explicitly revisioned source and leave the derived netlist unchanged. Do not assume the demo revision or the approval's expected revision belongs to that source.

From the training root, the facilitator checks each submission:

```bash
python materials/hardware/instructor/check.py \
  --lab hw1 --case demo --workspace work/hw1-demo
```

Change case/workspace to `transfer` and the relevant transfer directory. A checker pass for a faithful blocked report means the participant handled the missing evidence correctly; it does not mean the board package was verified.

---

## HW2 — Calculate limits and refresh calibration

### 1. Prepare and state the model assumptions

From the training root:

```bash
python materials/prepare_lab.py hw2 demo work/hw2-demo
cd work/hw2-demo
python -m json.tool source/circuit.json
python -m json.tool derived/calibration.json
```

- **What and why:** calculate from current inputs using an explicitly bounded model.
- **How:** read `REPORT_CONTRACT.md`. The model has an ideal source, upper resistor `Rt`, lower resistor `Rb`, shunt capacitor `C`, ideal high-impedance ADC and independent resistor tolerances `±t`. Source values use SI units. Record maximum input and ADC limit.
- **What can go wrong:** nominal values hide a worst-case violation, stale demo constants are reused, or ideal-model results are presented as physical verification.
- **Code to add later:** validate required finite positive values, units and the contract's tolerance range. Missing/invalid inputs block assessment; do not silently default them.
- **Input rule:** the supplied generator requires `0 < t < 1`; booleans are not numeric inputs. Preserve board identity and source revision in provenance.
- **Boundary:** preserve `source/circuit.json` and supplied tools. Only derived calibration, report and common artifacts are editable. Loading, sampling transients, leakage, temperature drift and capacitor tolerance are outside this model.

### 2. Calculate and explain all eight quantities

Read values from the actual source. Explain each equation before calculating it in the terminal with the agent. Retain units, substitutions and unrounded results.

| Report key | Equation | What it establishes |
| --- | --- | --- |
| `nominal_gain` | `Rb / (Rt + Rb)` | Nominal input-to-ADC ratio |
| `worst_case_gain` | `Rb*(1+t) / (Rt*(1-t) + Rb*(1+t))` | Maximum output ratio under resistor tolerance |
| `nominal_adc_v` | `vin_max_v * nominal_gain` | Nominal maximum ADC input |
| `worst_case_adc_v` | `vin_max_v * worst_case_gain` | Voltage used for the limit decision |
| `r_th_ohm` | `Rt*Rb / (Rt+Rb)` | Equivalent resistance with ideal voltage source shorted |
| `cutoff_hz` | `1 / (2*pi*r_th_ohm*C)` | Nominal first-order cutoff |
| `inverse_gain` | `(Rt+Rb) / Rb` | Nominal conversion from ADC voltage to input voltage |
| `adc_margin_v` | `adc_max_v - worst_case_adc_v` | Remaining margin; a negative value indicates violation |

- **Why:** upper-resistor minimum and lower-resistor maximum maximize the divider output. A nominal-only pass is insufficient.
- **What can go wrong:** tolerance signs are reversed, units are mixed, or premature rounding changes the limit decision.
- **Supplement Markdown with code:** use named functions/intermediate values for the equations, retain precision, and compare worst-case voltage directly with the ADC limit.
- **Evidence and explanation:** report `pass` only when worst-case voltage is at or below the limit; otherwise `fail`. Show the substituted values so another engineer can verify the reasoning.

### 3. Refresh calibration without hiding the design assessment

- **What and why:** repair a stale derived coefficient while assessing the supplied circuit independently.
- **How:** compare existing coefficient, source revision and digest with current inputs. Save the before state. Invoke the supplied generator:

```bash
python tools/generate_calibration.py --config source/circuit.json \
  --output derived/calibration.json --replace
python -m json.tool derived/calibration.json
```

- **What can go wrong:** successful generation is reported as a safe design, or file timestamps are treated as proof of freshness.
- **Supplement Markdown with code:** compare nominal inverse gain and canonical source digest. Use the supplied emitter; do not recreate a conflicting format. Run regeneration twice for identical input and check identical output.
- **Evidence and explanation:** calibration matches the current source, and the voltage-limit assessment remains visible even when it is `fail`. The generator proves only that nominal calibration was emitted correctly.

The required digest is SHA-256 of UTF-8 `json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)`. Include all fields. Whitespace/key-order changes do not alter this canonical form; numeric representation changes such as `30` versus `30.0` can. Follow the contract exactly.

### 4. Extract calculations, provenance and reporting

After completing the manual review/report, write and review `workflow.md` and preserve `workflow-md-only.md`. Parameterize every component value, tolerance, voltage limit and path; keep equations and assumptions explicit. Write `extraction-map.md`, then implement under `automation/`:

| Operation | Failure addressed | Evidence produced |
| --- | --- | --- |
| Validate current source | Missing/nonfinite/nonpositive input or invalid tolerance | Named input error and blocked result |
| Calculate quantities | Arithmetic/unit mistake or reused demo value | All eight values, substituted inputs and units |
| Assess voltage limit | Nominal-only or generator-only pass | Worst-case value, limit, margin and independent status |
| Refresh/check calibration | Stale coefficient/provenance | Before/after, source revision/digest and repeatability result |

Use readable named equations and independent test fixtures. Verify a valid demo, a worst-case limit violation, invalid/missing input, changed-source digest invalidation and repeatable regeneration. Preserve the source JSON. Update the workflow to invoke the implemented code and interpret its outcomes; engineering model suitability remains a human decision.

**Why code helps:** the same equations and provenance checks run against every current source, reducing manual substitution errors and making stale inputs visible. It does not establish that this ideal circuit model covers a real ADC design.

### 5. Transfer to a changed circuit

From the training root:

```bash
python materials/prepare_lab.py hw2 transfer work/hw2-transfer-md
python materials/prepare_lab.py hw2 transfer work/hw2-transfer-code
```

Use the paired replay procedure. The upper resistor changes; recalculate every quantity from current source data. Do not copy demo calculations or calibration.

**Correct outcome:** accurate calculations show a worst-case ADC voltage exceeding the stated limit, so the engineering assessment is `fail`. Regenerate nominal calibration with current provenance and retain the failed design assessment. Do not redesign the source circuit to force a pass.

Facilitator command, from the training root:

```bash
python materials/hardware/instructor/check.py \
  --lab hw2 --case demo --workspace work/hw2-demo
```

Change case/workspace for each transfer. A checker pass can accept a correctly assessed design failure. It verifies report arithmetic/provenance, not physical hardware safety.

---

## Report contract for both exercises

Create `report.json` after the demonstration; later automation must produce the same schema. Use each workspace's `REPORT_CONTRACT.md` as authority.

| Field | Required content |
| --- | --- |
| `schema_version`, `lab`, `case`, `board_id` | Version 1; current lab/case and actual source identity |
| `status` | Engineering `pass`, `fail` or `blocked` |
| `findings` | Objects with `code`, nonempty `evidence` and `explanation`; component findings also carry `ref` |
| `changed_files` | Only derived artifacts actually changed; exclude report, workflow, evidence and automation |
| `assumptions` | Nonempty authority/model limitations |
| `calculations` | HW2: all eight numeric keys, retaining at least 10 significant digits |

HW1 findings include `value_mismatch`, `pin_mapping_mismatch`, `equivalent_notation`, or `missing_source_revision` as applicable. HW2 includes `stale_calibration` and, when applicable, `adc_limit_exceeded`. Cite exact fields/rows and before/after values. Successful HW1 lists `derived/netlist.json`; blocked HW1 lists no changed artifacts; regenerated HW2 lists `derived/calibration.json`.

## Paired replay, evidence and final review

After both exercises, the facilitator selects at least one for paired replay; use both if time permits.

1. **MD-only:** copy `workflow-md-only.md` as `workflow.md` into its clean workspace. Copy no automation or completed outputs.
2. **MD plus code:** copy updated `workflow.md`, reusable `automation/` and documented dependencies. Copy no corrected board data, calibration, reports or demo evidence.
3. Start a new conversation in each with the same agent/model. Explicitly ask it to read the workflow and current contract, execute on current inputs and retain evidence. Record any new scripts the MD-only agent creates independently.
4. Compare engineering outcome, source preservation, missing-input handling, actual helper calls, elapsed time, interventions and recovery. Do not call manual fallback a successful helper execution.

For **each lab**, submit both workflow versions, `extraction-map.md`, `automation/` with checks/README, `report.json`, and actual session/verification evidence. Learner automation returns 0 for engineering pass, 1 for engineering fail, 2 for blocked; record the instructor check's separate training decision.

Apply the handbook rubric: at least 8/10, no zero in any category and all mandatory conditions met. Review demonstration evidence, reusable workflow, deterministic boundary, code quality and feedback/transfer. A faithful blocked or failed engineering assessment can earn training credit.

Explain results as **goal → action → observed problem → code remediation → verification → why the evidence supports the outcome → untested limits**. “The provenance gate blocked the incomplete transfer and preserved the netlist” explains a successful workflow outcome without claiming the board itself passed. One paired replay does not prove a general advantage of code over Markdown.

### Adequacy and completeness review

- **Documentation review, 14 October 2026:** adequate for a facilitated workshop at the stated level. Source authority, all eight equations, report fields, code remediation, transfer outcomes and explanations are covered without supplying the finished learner implementation.
- **Checks performed:** all six hardware preparation commands ran; shell syntax, Markdown parsing and local source links were checked. Five supplied hardware tests passed. Current demo/transfer calculations confirmed the expected pass/fail distinction; repeated calibration generation and canonical digests were verified. The transfer's missing schematic revision was confirmed. These are starter/command checks, not acceptance of an uncreated learner report.
- **Level:** concise engineering instructions with explicit source roles, equations and output contract. Participants need terminal assistance and circuit fundamentals; finished comparison/calculation implementations remain learner work.
- **Coverage:** both demonstrations, abstraction, code extraction, required positive/failure checks, transfer, report schema and evidence-based explanations are included.
- **Required local gate:** inspect actual reports, unchanged sources and helper/replay results; complete a representative learner pilot. These instructions do not claim physical validation or a completed classroom rehearsal.
- **Review against:** [hardware report contract](../training_kit/hardware/REPORT_CONTRACT.md), [hardware technical reference](../training_kit/hardware/README.md) and the handbook's shared method/rubric.
