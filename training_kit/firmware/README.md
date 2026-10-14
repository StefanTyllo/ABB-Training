# Firmware workshop starters

These are synthetic host-only fixtures. Requirements: Python 3.9+ and GCC with
C11 support. No board, serial adapter, pip packages, or network are required.
Run commands from this `firmware` directory. `fw1` is a working low-level
simulator; `fw2` deliberately contains two defects for learners to diagnose.

## Teaching sequence

1. Walk through one incident manually with Codex; ask it to explain **why**
   each observation, command, proposed change, and validation is useful.
2. Record the workflow actually followed, including the evidence and decisions.
3. Abstract incident-specific IDs, values, paths, and packet boundaries into inputs.
4. Identify deterministic steps and separate them from judgments requiring review.
5. Ask Codex to generate verbose automation from that documented workflow,
   explaining actions and retaining evidence. Exercise it on the transfer case.

Do not begin by asking for an end-to-end solution. No diagnostic workflow,
before-change capture, or remediation automation is supplied in the starter.
Learners build those only after the manual walkthrough. The instructor folder
contains evaluation answers; omit it from learner handouts until evaluation.
This is a teaching boundary, not an access-control mechanism.

## FW1: communication incident

```bash
python3 fw1/device.py --workdir runs/demo init --case demo
python3 fw1/device.py --workdir runs/demo read --field identity
python3 fw1/device.py --workdir runs/demo read --field firmware
python3 fw1/device.py --workdir runs/demo read --field config
python3 fw1/device.py --workdir runs/demo read --field faults
python3 fw1/device.py --workdir runs/demo logs
python3 fw1/device.py --workdir runs/demo probe
cat fw1/expected.json
```

Compare observations to the reference. Capture evidence before changing anything;
the learner decides how to save it. The only mutation primitive is `set`:
`python3 fw1/device.py --workdir runs/demo set --parameter baud --value 19200`.
Use it after justifying the change, then independently verify the result.
Transfer setup: `python3 fw1/device.py --workdir runs/transfer init --case transfer`.
Apply your extracted workflow to that workdir without embedding demo constants.
Initialization refuses existing state: use a new workdir for a repeat exercise.

## FW2: host parser incident

```bash
gcc -std=c11 -Wall -Wextra -Werror fw2/parser.c fw2/main.c -o fw2/parser
./fw2/parser a5020785ffda
./fw2/parser a50207 85ffda
./fw2/parser a502 2a00 f875
```

The first two invocations represent identical bytes in different receive chunks.
The last is the transfer fixture (sequence 42, value -2048). Compare with
`requirements.md`, explain the failures, and make a minimal repair. Preserve
failing evidence, explain the fix, and retest independently before generalizing
the build/reproduction/regression workflow into verbose automation.

## Instructor checks

```bash
python3 instructor/smoke.py
python3 instructor/smoke.py ./fw2/parser
```

The first checks FW1 and proves the FW2 grader rejects seeded defects and accepts
an isolated corrected reference. It leaves learner sources unchanged. The second
grades a supplied executable, emits JSON failures, and exits nonzero on failure;
it is expected to fail against the untouched starter. See `instructor/README.md`.
