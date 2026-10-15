"""Targeted scripted T1 refinement, not a fresh MD/code comparison."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from training_ci.runtime_paths import runs_root
WORK = runs_root() / "t1-refined"
PROTECTED = ("server.py", "ui.html", "conftest.py", "case.json", "REQUIREMENTS.md", "pytest.ini", "requirements.txt", "browser_preflight.py", "pages/base_page.py")


def hashes():
    return {p: hashlib.sha256((WORK / p).read_bytes()).hexdigest() for p in PROTECTED}


def prepare():
    shutil.copytree(ROOT / "validation_browser" / "seed", WORK)
    (WORK / "evidence").mkdir()
    (runs_root() / "t1-refined-protected.json").write_text(json.dumps(hashes()))


def agent():
    prompt = (ROOT / "validation_browser" / "prompt.md").read_text()
    (WORK / "evidence" / "refinement-prompt.md").write_text(prompt)
    with (WORK / "evidence" / "server.log").open("w") as log:
        app = subprocess.Popen([sys.executable, "server.py", "--variant", "correct", "--port", "8765", "--state", "state.json"], cwd=WORK, stdout=log, stderr=log)
        try:
            for _ in range(100):
                if app.poll() is not None:
                    raise RuntimeError("Owned server exited")
                try:
                    urllib.request.urlopen("http://127.0.0.1:8765", timeout=1).close()
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError("Server not ready")
            command = ["copilot", "-p", prompt, "--no-ask-user", "-s", "--share=" + str(WORK / "evidence" / "refinement-transcript.md"), "--allow-tool=read", "--allow-tool=write"]
            command += ["--allow-tool=shell(" + tool + ":*)" for tool in ("python", "python3", "cat", "ls", "pwd", "sed", "head", "rg")]
            with (WORK / "evidence" / "refinement-response.txt").open("w") as output:
                result = subprocess.run(command, cwd=WORK, stdout=output, stderr=subprocess.STDOUT, timeout=900)
            (WORK / "evidence" / "refinement-execution.json").write_text(json.dumps({"returncode": result.returncode, "method": "targeted scripted refinement"}))
            if result.returncode:
                raise RuntimeError("Copilot refinement failed")
        finally:
            app.terminate()
            try:
                app.wait(timeout=10)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait()


def verify():
    expected = json.loads((runs_root() / "t1-refined-protected.json").read_text())
    if hashes() != expected:
        raise RuntimeError("Protected application/framework changed")
    result = subprocess.run([sys.executable, str(ROOT / "training_ci" / "grade_test.py"), "--lab", "t1", "--workspace", str(WORK), "--mode", "code"], cwd=ROOT)
    if result.returncode:
        raise RuntimeError("Existing independent grading failed")
    if hashes() != expected:
        raise RuntimeError("Protected inputs changed during grading")
    grade = json.loads((WORK / "evidence" / "ci" / "grade.json").read_text())
    summary = json.loads((WORK / "evidence" / "ci" / "correct-helper-summary.json").read_text())
    browser = summary.get("browser")
    if not browser or grade["semantic"]["browser"] not in json.dumps(browser):
        raise RuntimeError("Helper did not record matching actual browser identity")
    names = grade["results"]["correct"]["names"]
    for required in ("empty_password", "invalid_save"):
        if not any(required in name for name in names):
            raise RuntimeError("Missing executed refinement case: " + required)
    screenshots = [p for p in (WORK / "evidence").rglob("*.png") if p.stat().st_size > 100 and p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")]
    if not screenshots:
        raise RuntimeError("No retained real PNG failure evidence")
    (WORK / "evidence" / "refinement-assessment.json").write_text(json.dumps({"status": "passed", "method": "targeted scripted refinement; not a fresh MD/code comparison", "browser": browser, "screenshots": [str(p.relative_to(WORK)) for p in screenshots]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "agent", "verify"))
    action = parser.parse_args().action
    {"prepare": prepare, "agent": agent, "verify": verify}[action]()
