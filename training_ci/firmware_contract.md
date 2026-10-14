# Firmware CI contract

The runner creates one workspace per case with `training_kit/prepare_lab.py`.
`case.json` contains `lab` (`fw1` or `fw2`) and `case` (`demo` or `transfer`).
Use only that workspace's paths and inputs; do not hard-code the demo identity,
baud, packet sequence, absolute paths, or receive-chunk boundaries.

Follow the training method: manually walk through the demo with Copilot CLI
explaining why; document the observed workflow in `workflow.md`; abstract incident
specifics; identify deterministic steps; then generate verbose automation.
Stage 1 is the manual walkthrough: do not create reusable automation yet.
Keep explanatory comments and useful action/result output in that automation.
An independent reviewer evaluates the explanation and workflow quality; runtime
checks alone do not establish those qualities or prove when evidence was captured.

## Common automation entry point

Create `automation/guardrails.py`, runnable as:

```bash
python3 automation/guardrails.py --workspace /absolute/path/to/workspace
```

It must return 0 after successful completion and verification, and nonzero on
failure. Resolve all input/output paths from `--workspace`, not the caller's cwd.
Do not require interactive input. It must work after Copilot completes the task
in either the demo or a separately prepared transfer workspace, and be idempotent:
a repeat invocation preserves
the original baseline and does not perform an additional device write or change
the repaired parser sources. The runner copies only `automation/` and
`workflow.md` from the demo into a freshly prepared transfer workspace. All helper
code required by automation must therefore live under `automation/`. Copilot
performs the transfer task before the grader runs; copying helpers does not
replace that fresh investigation and repair.

After Copilot completes the task, the independent grader invokes automation,
validates the completed result using trusted
checks, invokes it again, and validates preservation and results. The grader
does not fix or patch starter sources. Do not modify grader/instructor files.

## FW1

Inputs are `fw1/device.py`, `fw1/expected.json`, `case.json`, and
`device/state.json`. Leave the simulator, expected settings, and case metadata
unchanged. Use device CLI primitives for mutations, not direct state-file edits.
Before the first mutation, write `evidence/baseline.json` containing these keys,
each holding the unmodified JSON output of the corresponding primitive:

| Key | Primitive |
| --- | --- |
| `identity` | `read --field identity` |
| `firmware` | `read --field firmware` |
| `config` | `read --field config` |
| `faults` | `read --field faults` |
| `logs` | `logs` |

All calls use `--workdir <workspace>/device`. Baseline must show original baud
9600, LINK_TIMEOUT, and the original boot log, with matching device identity and
firmware. Never overwrite or reformat an existing baseline. Missing baseline on
an already repaired device is an error: do not fabricate historic evidence.
Use the case and expected settings to derive the target baud. Final config must
match the target, faults must be empty, and probe must succeed. The original boot
log remains, followed by exactly one intended `9600 -> target` change. Running
automation again must preserve state and baseline byte-for-byte.
The grader runs the helper after Copilot has completed the device task, including
capturing the baseline and applying any justified change.

## FW2

Inputs are `fw2/parser.c`, `fw2/parser.h`, `fw2/main.c`, `case.json`, and
`requirements.md`. Repair the parser implementation and use the documented public
API/CLI. Copilot performs a fresh repair in each case. The reusable helper only
builds the candidate, replays protocol cases, compares results, and reports
verification; it must not apply the repair or carry a corrected parser in its
helpers. Preserve `main.c`, `parser.h`,
and case metadata. Do not replace the CLI with hard-coded fixture responses.
An executable supplied by automation is not trusted: the grader rebuilds
`parser.c` with the trusted original CLI/header and runs the instructor's external
50-case stream grader plus malformed input checks. Repeat automation must leave
parser source bytes unchanged. FW2 does not require FW1's baseline JSON.

## Independent evaluation

From the repository root:

```bash
python3 training_ci/grade_firmware.py --lab fw1 --workspace /path/to/fw1-demo
python3 training_ci/grade_firmware.py --lab fw2 --workspace /path/to/fw2-demo
python3 training_ci/grade_firmware.py --lab fw1 --workspace /path/to/fw1-transfer --mode md-only
```

Repeat for each transfer workspace after copying the two common artifacts and
having Copilot complete the fresh task.
The grader prints a JSON result to stdout, a terminal summary to stderr, and saves
`evidence/grade_firmware.json`; it exits 0 on pass and 1 on failed checks.
`--mode code` is the default and invokes/requires automation as described above.
`--mode md-only` requires `workflow.md` and grades the existing baseline/device
state or parser with the same independent result checks, but neither requires nor
invokes automation. The runner uses fresh, separate MD-only and code transfer
workspaces. Learners must not access grader/instructor sources; the runner records
protected-file hashes independently.
