
# FW1 Capture state before troubleshooting

**Task card.** Restore communication with the simulated device. Explain the cause using observations collected before the change, make one justified configuration change, and verify recovery. Do not repair the simulator's implementation.

**Prepare from the training root**
```bash
python materials/prepare_lab.py fw1 demo work/fw1-demo
cd work/fw1-demo
```
Read `requirements.md`. Start the agent here and use the Stage 1 start prompt. The state is already initialized under `device/`. Reinitialization is unnecessary and refuses existing state.

**Allowed changes:** device configuration through `fw1/device.py set`, plus the common workflow, automation, and evidence files. Do not edit `device/state.json`, the simulator, or `fw1/expected.json` directly.

## Stage 1 Guided operations
Run these one at a time, explaining the question each answers:
```bash
python fw1/device.py --workdir device read --field identity
python fw1/device.py --workdir device read --field firmware
python fw1/device.py --workdir device read --field config
python fw1/device.py --workdir device read --field faults
python fw1/device.py --workdir device logs
python fw1/device.py --workdir device probe
python -m json.tool fw1/expected.json
```

| Decision point | Explanation the participant must supply |
| --- | --- |
| Before any write | Which observations constitute the baseline, and where will they be saved? |
| After the probe | What supports a configuration hypothesis rather than a software repair? |
| Before changing baud | Which expected entry belongs to the observed device identity? |
| After the change | Which current observations demonstrate recovery? |

Use the tool's help to construct a single `set --parameter baud --value` operation from the observed reference. Save pre-change evidence before executing it. Then repeat configuration, faults, and probe. Historical logs may retain the old incident; explain why that differs from an active fault.

**Demonstration complete:** identity-matched reference used; baseline retained; one recorded configuration change; current fault cleared and probe successful. Now use the shared documentation prompt, then continue on the next page.


# FW1 Extract the reusable operations

## Stage 2 Abstraction focus
Inputs are the device tool path, state-directory path, expected-configuration path, and evidence destination. Resolve the expected settings from the observed identity. Do not carry the demo device ID or baud value into the reusable workflow.

## Stage 3 Deterministic boundary
| Move into code | Retain as reasoning |
| --- | --- |
| Capture identity, firmware, configuration, faults, logs, and probe output | Decide which evidence supports the fault hypothesis |
| Validate required observations and identity/reference match | Decide whether an unfamiliar fault warrants a different investigation |
| Compare before/after values and probe status | Explain why the observed change demonstrates recovery |

## Stage 4 Required implementation behavior
Create `automation/capture_state.py` and a controlled experiment entry point with documented arguments. Capture must invoke the low-level tool and retain complete raw outputs, commands, exit status, timestamps and input identity by default. Save the before-capture before any mutation; failed evidence persistence blocks the write. It must fail if any required read fails; a partial capture cannot become a baseline marked complete.

The experiment operation must require a valid baseline for the same device and compare the current configuration with that baseline before writing. If they differ, return blocked and request a new capture. It must apply at most one allowed parameter change, then capture and compare again. Preserve original before/after and mutation records on repeat runs. This is enforcement inside the learner's entry point; direct simulator access remains available in this teaching fixture.

**Journal check:** append a legitimate session entry, rerun read-only verification and confirm original captures and old journal entries remain intact. Do not freeze the whole growing journal hash.

**Required checks:** valid capture; missing/nonexistent state directory produces blocked; unknown identity cannot select a reference; experiment without a baseline is rejected; stale baseline is rejected; correct change restores the probe. Use disposable prepared cases for checks that mutate state.

**Transfer preparation, from the training root**
```bash
python materials/prepare_lab.py fw1 transfer work/fw1-transfer-md
python materials/prepare_lab.py fw1 transfer work/fw1-transfer-code
```
Use the shared replay procedure. The transfer has a different identity and required baud. The learner's code must discover both from current evidence. Do not copy `device/` from the demo.

**Assessment:** the facilitator checks actual before/after records, the device-matched reference, and a fresh successful probe. Automated starter smoke tests validate the fixture, not the learner's reasoning or baseline capture.

**Debrief:** which terminal operations stopped requiring the model to reconstruct commands? Which diagnosis decisions still depended on engineering interpretation?
