"""Validate the complete T1 package after restoring omitted original XML fixtures."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import time
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from validation_browser import refine
WORK=refine.WORK
shutil.copytree(ROOT/'validation_t1_package/seed',WORK)
(WORK/'evidence').mkdir()
(ROOT/'runs/t1-refined-protected.json').write_text(json.dumps(refine.hashes()))
with (WORK/'evidence/package-server.log').open('w') as log:
    app=subprocess.Popen([sys.executable,'server.py','--variant','correct','--port','8765','--state','state.json'],cwd=WORK,stdout=log,stderr=log)
    try:
        for _ in range(100):
            if app.poll() is not None:raise RuntimeError('Owned server exited')
            try:
                urllib.request.urlopen('http://127.0.0.1:8765',timeout=1).close();break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('Readiness timeout')
        commands=[
            [sys.executable,'-m','pytest','automation/tests','-q','--junitxml=evidence/automation-self-tests.xml'],
            [sys.executable,'automation/capture_missing_element.py'],
        ]
        for i,command in enumerate(commands):
            result=subprocess.run(command,cwd=WORK,capture_output=True,text=True,timeout=240)
            (WORK/f'evidence/package-command-{i}.log').write_text(result.stdout+'\n'+result.stderr)
            print(result.stdout);print(result.stderr)
            if result.returncode:raise RuntimeError('Package check failed: '+str(command))
    finally:
        app.terminate();app.wait(timeout=10)
refine.verify()
print('Complete T1 package: automation self-tests, real-browser suite, semantic oracle and retained evidence accepted.')
