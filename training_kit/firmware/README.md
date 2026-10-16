# Firmware technical reference

Use the PDF's FW1/FW2 cards and shared four-stage prompts as the training instructions. Prepare cases with the root `prepare_lab.py` wrapper shown there; do not initialize another device inside a prepared case.

These synthetic fixtures require Python 3.12 and, for FW2, GCC with C11 support. No physical board, serial adapter, external Python package or network is required. `requirements.md` is the behavioral contract. `fw1/device.py --help` describes low-level device access. `fw2/parser.c` intentionally contains defects; the public header and CLI are supplied adapters.

The clean firmware directory is reference material. Work only in a prepared participant directory. Instructor checks and corrected reference logic are excluded by preparation. They are an assessment tool, not the learner's workflow automation.


## Container workspaces

Use these commands from the unpacked package folder with `.venv` activated. Provider login is separate; retain the chosen provider/model. Fresh transfers are performed only after Stage 4.


### FW1

**Host terminal** — in the unpacked package folder; fresh FW1 demonstration:

```text
abb doctor --offline
abb prepare fw1 demo
abb shell --workspace work/fw1-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw1-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare fw1 transfer --name fw1-transfer-md
abb shell --workspace work/fw1-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw1-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare fw1 transfer --name fw1-transfer-code
abb shell --workspace work/fw1-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw1-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.

### FW2

**Host terminal** — in the unpacked package folder; fresh FW2 demonstration:

```text
abb doctor --offline
abb prepare fw2 demo
abb shell --workspace work/fw2-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw2-demo
```

This opens a local shell with the active virtual environment. Agent authentication is separate. If your chosen provider is not already authenticated, use its `abb login` command from the setup instructions. Keep the same agent/model throughout the exercise.

Stages 1–4 stay in this shell. To resume, return to the package folder, activate `.venv`, and repeat the exact workspace entry command without preparation. Check `pwd` before continuing. Shell exit preserves your files; choose a fresh name for another attempt.

After Stage 4, stop any owned app server and use two fresh transfer workspaces. Prepare each once. Copy only the workflow or reusable automation specified by the exercise, keeping the demonstration evidence in its original workspace.

**Host terminal** — fresh instructions-only transfer:

```text
abb doctor --offline
abb prepare fw2 transfer --name fw2-transfer-md
abb shell --workspace work/fw2-transfer-md
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw2-transfer-md
```

**Host terminal** — fresh instructions-plus-code transfer:

```text
abb doctor --offline
abb prepare fw2 transfer --name fw2-transfer-code
abb shell --workspace work/fw2-transfer-code
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw2-transfer-code
```

To resume either transfer, repeat its host-side entry command without `abb prepare`. Do not overwrite an existing workspace.

## Facilitator assessment

**Host terminal — facilitator package only**:

```text
python training_kit/firmware/instructor/smoke.py work/fw2-demo/fw2/parser
```

Use each submission's actual executable path. The check exercises 50 stream cases plus malformed input and should fail on the untouched starter.
