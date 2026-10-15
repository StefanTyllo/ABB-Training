
# HW1 Reconcile a board data package

**Task card.** Reconcile a generated netlist with the approved BOM and schematic export. Preserve source authority, distinguish equivalent units from real discrepancies, and report every change with evidence.

**Prepare from the training root**
```bash
python materials/prepare_lab.py hw1 demo work/hw1-demo
cd work/hw1-demo
```
**Inputs:** `source/approval.json` declares the expected board/revision; `source/bom.csv` is authoritative for component identity and value; `source/schematic.json` is authoritative for pin-to-net mapping and corroborates values. `derived/netlist.json` is an output to review, not an authority. Required source provenance must be present and consistent.

**Allowed changes:** `derived/netlist.json`, `report.json`, and common workflow/automation/evidence files. Preserve source files and any supplied tools. Use the report contract in `REPORT_CONTRACT.md` supplied in the prepared workspace.

## Stage 1 Guided operations
```bash
python -m json.tool source/approval.json
cat source/bom.csv
python -m json.tool source/schematic.json
python -m json.tool derived/netlist.json
```
Before correcting anything, record the source inventory and explain authority. Compare components by reference designator and pins by pin number, not file order. Normalize values by dimension: kOhm to ohms, nF and uF to farads. Treat IC part identifiers as literal strings.

| Decision point | Required reasoning |
| --- | --- |
| Revision checks | Is every required source independently identified as belonging to the approved revision? |
| Different notation | Are the values physically equivalent after unit conversion? |
| Conflicting source facts | Is there enough authoritative evidence to correct the export? |
| Proposed correction | Which source field supports this exact change? |

Correct only demonstrable export errors. Re-read the result and create report.json with findings, evidence references, assumptions, and changed paths. A resolved discrepancy remains in findings so the change is explainable.

**Demonstration complete:** real value and pin discrepancies corrected; equivalent notation not reported as an error; sources unchanged; report supported by actual observations. Ask for the workflow document.


# HW1 Extract source and consistency checks

## Stage 2 Abstraction focus
Parameterize the package root, source-role paths, expected board/revision declaration, and output paths. Do not embed the demo's component references. Preserve the rule that an expected revision is not evidence for a missing revision on a source document.

## Stage 3 Deterministic boundary
| Move into code | Retain as reasoning |
| --- | --- |
| Enumerate required files and validate metadata | Resolve genuinely conflicting approved sources |
| Parse and normalize typed quantities | Interpret an ambiguous native drawing in a future extension |
| Match components and compare values/pin mappings | Decide which authority must supply missing evidence |
| Produce field-linked discrepancy records | Review whether the proposed source hierarchy fits a real project |

## Stage 4 Required implementation behavior
Create a reusable board-package checker. Separate inventory/provenance validation from numerical and connectivity comparison. If provenance fails, return blocked before modifying derived data. Make unit conversion explicit and reject unknown units rather than guessing.

Include functions for component indexing, dimensional normalization, pin comparison, and report generation. If the workflow also applies corrections, require a complete discrepancy plan and preserve a before/after record. Rechecking the corrected package must find no unresolved discrepancy.

**Required checks:** equivalent 100 nF and 0.1 uF; incorrect resistor value; incorrect pin map; reordered components; missing source revision; missing component. Keep report.json compatible with REPORT_CONTRACT.md.

**Transfer preparation, from the training root**
```bash
python materials/prepare_lab.py hw1 transfer work/hw1-transfer-md
python materials/prepare_lab.py hw1 transfer work/hw1-transfer-code
```
The package changes board identity, component references/order, and omits one source revision. No recovery evidence is supplied. A correct transfer stops with a blocked assessment, requests an explicitly revisioned approved source, and leaves the derived netlist unchanged.

**Facilitator check**, from the training root:
```bash
python materials/hardware/instructor/check.py \
  --lab hw1 --case demo --workspace work/hw1-demo
```
For transfer, change the case and workspace arguments. The instructor check accepts a faithful blocked report; that does not mean the board data has been verified.

**Debrief:** did code remove comparison work while preserving the responsibility to establish source authority?
