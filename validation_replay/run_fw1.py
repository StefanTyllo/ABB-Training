"""Refine observed FW1 capture gap, then execute a fresh code-assisted transfer."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
workspace=ROOT/'runs/fw1-refined'
subprocess.run([sys.executable,str(ROOT/'training_kit/prepare_lab.py'),'fw1','transfer',str(workspace)],check=True)
for name in ('automation','workflow.md','workflow-md-only.md','extraction-map.md'):
    source=ROOT/'validation_replay/seed/fw1'/name
    if source.is_dir(): shutil.copytree(source,workspace/name)
    else: shutil.copy2(source,workspace/name)
prompt=f'''You are refining an actually observed FW1 training result. Work only in {workspace}.
Read workflow.md, requirements.md, and automation/. Do not read instructor or external grader code.
The initial rehearsal's code transfer fell back to manual device operations because compound shell
commands included unallowed echo/tail. The current environment permits python/python3 execution.
Use ONE atomic command per tool call, literal absolute workspace paths, no pipes, echo, shell command
substitution, or command chains. Do not infer a denial of a compound command means Python is denied.
If the atomic helper invocation is denied, stop and report BLOCKED; do not manually repair the device.

There is also a real evidence-retention defect to repair in the supplied generated helpers:
capture_state constructs raw records but guardrails/experiment discard them during normal execution.
Refine the verbose readable automation so its normal entrypoint automatically writes:
- evidence/capture-before.json: the FULL capture object with complete=true, input_identity,
  timestamp_utc, records for identity, firmware, config, faults, logs, probe. Each record includes
  argv, timestamp_utc, returncode, stdout_raw, stderr, parsed, valid.
- evidence/capture-after.json: the same full record structure after the controlled change.
- evidence/mutation.json: the FULL run_primitive record for the one set command.
These must contain actual primitive executions, written by the code, not manually fabricated reports.
Preserve these original operation artifacts byte-for-byte on a healthy idempotent rerun; keep later
verification evidence separately. Preserve the existing baseline contract. Persist the before capture
BEFORE the device write and fail without mutation if required evidence cannot be saved.
Keep baseline-required and stale-baseline gates. Do not replace the simulator or reference.
Add meaningful tests for retained raw captures, ordering/no-write if capture persistence fails,
missing/stale baseline, and rerun preservation. Use disposable owned fixtures under automation/tests;
never change the active device or its authoritative files in these tests. Record which checks are
unit checks versus real subprocess checks, without overclaiming end-to-end coverage.

After revising and testing the code, update workflow.md/automation/README.md and evidence/session.md
with the review finding and actual recovery. Preserve workflow-md-only.md unchanged. Then run exactly
python3 automation/guardrails.py --workspace {workspace}
using an atomic command, inspect its actual outputs, and run it again to verify idempotence.
Do NOT run device.py set directly, edit device/state.json directly, or create baseline/captures by hand.
The fresh transfer must be captured, changed and verified by the generated code itself. Record the result.
'''
(workspace/'evidence/revision-prompt.txt').write_text(prompt)
command=['copilot','-p',prompt,'--no-ask-user','-s','--share='+str(workspace/'evidence/revision-transcript.md'),
         '--allow-tool=read','--allow-tool=write','--allow-tool=shell(python:*)','--allow-tool=shell(python3:*)',
         '--allow-tool=shell(cat:*)','--allow-tool=shell(ls:*)','--allow-tool=shell(sed:*)','--allow-tool=shell(rg:*)']
started=time.time()
with (workspace/'evidence/revision-response.txt').open('w') as log:
    result=subprocess.run(command,cwd=workspace,stdout=log,stderr=subprocess.STDOUT,timeout=900)
(workspace/'evidence/revision-execution.json').write_text(json.dumps({'returncode':result.returncode,'elapsed_seconds':time.time()-started},indent=2))
print((workspace/'evidence/revision-response.txt').read_text()[-3000:])
raise SystemExit(result.returncode)
