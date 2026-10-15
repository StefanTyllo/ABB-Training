"""Check actual raw evidence before and after independent idempotent grading."""
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from training_ci.runtime_paths import runs_root
w=runs_root() / 'fw1-refined'
paths=[w/'evidence'/name for name in ('baseline.json','capture-before.json','capture-after.json','mutation.json')]
saved={p:p.read_bytes() for p in paths}
for moment,baud,ok in [('before',9600,False),('after',38400,True)]:
    capture=json.loads((w/f'evidence/capture-{moment}.json').read_text())
    assert capture['complete'] is True
    assert capture['input_identity']['device_id']=='SIM-083'
    assert capture['timestamp_utc']
    records=capture['records']
    for field in ('identity','firmware','config','faults','logs','probe'):
        r=records[field]
        assert r['returncode']==0 and r['valid'] is True and r['timestamp_utc'] and r['argv']
        assert json.loads(r['stdout_raw'])==r['parsed']
    assert records['config']['parsed']['baud']==baud
    assert records['probe']['parsed']['ok'] is ok
mutation=json.loads((w/'evidence/mutation.json').read_text())
assert mutation['returncode']==0 and mutation['valid'] is True
assert mutation['argv'][-5:]==['set','--parameter','baud','--value','38400']
assert json.loads(mutation['stdout_raw'])=={'parameter':'baud','old':9600,'new':38400}
assert (w/'workflow-md-only.md').read_bytes()==(ROOT/'validation_replay/seed/fw1/workflow-md-only.md').read_bytes()
subprocess.run([sys.executable,str(ROOT/'training_ci/grade_firmware.py'),'--lab','fw1','--workspace',str(w)],check=True)
for path,data in saved.items(): assert path.read_bytes()==data, 'Original evidence overwritten: '+str(path)
for name in ('device.py','expected.json'):
    assert (w/'fw1'/name).read_bytes()==(ROOT/'training_kit/firmware/fw1'/name).read_bytes()
report={'accepted':True,'case':'fresh transfer','checks':['raw before capture','actual mutation record','raw after capture','independent device result','idempotent evidence preservation']}
(w/'assessment.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
