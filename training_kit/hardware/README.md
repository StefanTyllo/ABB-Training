# Hardware technical reference

Use the PDF's HW1/HW2 cards and shared four-stage prompts as the training instructions. Prepare cases using the root `prepare_lab.py` wrapper shown there. It also copies `REPORT_CONTRACT.md` into the participant workspace. Existing output directories are refused.

These synthetic Python 3.12 standard-library fixtures require no EDA software, physical board, network or credentials. The clean fixture masters and instructor references remain outside the participant workspace. Results apply to the supplied evidence and ideal model only.

`REPORT_CONTRACT.md` defines report fields, finding codes, numerical precision, equations and calibration provenance. The PDF defines source authority and allowed changes. The provided `tools/generate_calibration.py` emits nominal calibration; it does not assess the circuit's worst-case voltage limit. Participants build the reusable comparison/calculation workflow after the guided demonstration.


## Container workspaces

Use these commands from the unpacked package folder with `.venv` activated. Provider login is separate; retain the chosen provider/model. Fresh transfers are performed only after Stage 4.


### HW1

**Host terminal** — in the unpacked package folder; fresh HW1 demonstration:

```text
abb doctor --offline
abb prepare hw1 demo
abb shell --workspace work/hw1-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/hw1-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare hw1 transfer --name hw1-transfer-md
abb shell --workspace work/hw1-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/hw1-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare hw1 transfer --name hw1-transfer-code
abb shell --workspace work/hw1-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/hw1-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.

### HW2

**Host terminal** — in the unpacked package folder; fresh HW2 demonstration:

```text
abb doctor --offline
abb prepare hw2 demo
abb shell --workspace work/hw2-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/hw2-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare hw2 transfer --name hw2-transfer-md
abb shell --workspace work/hw2-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/hw2-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare hw2 transfer --name hw2-transfer-code
abb shell --workspace work/hw2-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/hw2-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.

## Facilitator assessment

**Host terminal — facilitator package only**:

```text
python training_kit/hardware/instructor/check.py --lab hw1 --case demo --workspace work/hw1-demo
python training_kit/hardware/instructor/check.py --lab hw2 --case demo --workspace work/hw2-demo
```

Use the actual lab, case and workspace for transfers. A faithful missing-authority BLOCKED or failed design result can be accepted as correct training work.
