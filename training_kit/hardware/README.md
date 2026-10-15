# Hardware technical reference

Use the PDF's HW1/HW2 cards and shared four-stage prompts as the training instructions. Prepare cases using the root `prepare_lab.py` wrapper shown there. It also copies `REPORT_CONTRACT.md` into the participant workspace. Existing output directories are refused.

These synthetic Python 3.12 standard-library fixtures require no EDA software, physical board, network or credentials. The clean fixture masters and instructor references remain outside the participant workspace. Results apply to the supplied evidence and ideal model only.

`REPORT_CONTRACT.md` defines report fields, finding codes, numerical precision, equations and calibration provenance. The PDF defines source authority and allowed changes. The provided `tools/generate_calibration.py` emits nominal calibration; it does not assess the circuit's worst-case voltage limit. Participants build the reusable comparison/calculation workflow after the guided demonstration.

From the training root, the facilitator runs the checker after submission:

```bash
python materials/hardware/instructor/check.py \
  --lab hw1 --case demo --workspace work/hw1-demo
python -m unittest discover -s materials/hardware/tests -v
```

Substitute the actual lab, case and workspace for another submission. A faithful blocked HW1 transfer or failed HW2 design assessment can pass the training checker. The checker validates source preservation, report content, derived data, numerical references and calibration provenance. It does not certify physical hardware or replace review of the explanation, workflow abstraction and code quality.
