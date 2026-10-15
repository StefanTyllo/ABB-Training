"""Independent browser-lab grader; run outside the participant workspace."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def inspect_junit(path, returncode, variant, lab):
    require(path.is_file(), f"Missing JUnit report: {path}")
    cases = ET.parse(path).getroot().findall(".//testcase")
    require(len(cases) >= (4 if lab == "t1" else 8), "Too few executed requirement cases")
    require(not any(c.find("skipped") is not None for c in cases), "Required tests were skipped/xfail")
    require(not any(c.find("error") is not None for c in cases), "Infrastructure/setup/teardown error")
    names = [c.get("name", "") for c in cases]
    required_names = ["save_reload", "connection_visibility", "auth_visibility"] if lab == "t1" else ["save_reload", "port_boundary", "invalid_save"]
    for name in required_names:
        require(any(name in item for item in names), f"Missing named requirement case: {name}")
    failed = [(c.get("name", ""), c.find("failure")) for c in cases if c.find("failure") is not None]
    if variant == "correct":
        require(returncode == 0 and not failed, "Correct application did not pass")
    else:
        require(returncode == 1 and failed, f"Mutant was not detected: {variant}")
        for name, failure in failed:
            summary = failure.get("type", "") + " " + failure.get("message", "")
            require(bool(re.search(r"AssertionError|\bassert\b", summary)), f"Non-assertion failure in {name}: {summary}")
        target = "save_reload" if variant == "no-persist" else "port_boundary"
        require(any(target in name for name, _ in failed), f"Missing relevant {target} assertion failure")
    return {"tests": len(cases), "failures": len(failed), "names": names, "returncode": returncode}


@contextmanager
def server(workspace, evidence, variant):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    state = evidence / (variant + "-state.json")
    state.unlink(missing_ok=True)
    with (evidence / (variant + "-server.log")).open("w") as log:
        process = subprocess.Popen([sys.executable, str(workspace / "server.py"), "--variant", variant,
                                    "--port", str(port), "--state", str(state)], cwd=workspace,
                                   stdout=log, stderr=subprocess.STDOUT)
        url = f"http://127.0.0.1:{port}"
        try:
            deadline = time.monotonic() + 10
            while True:
                require(process.poll() is None, "Owned server exited during startup")
                try:
                    with urllib.request.urlopen(url + "/api/settings", timeout=1) as response:
                        require(response.status == 200, "Server health response was not 200")
                    break
                except OSError:
                    require(time.monotonic() < deadline, "Server readiness timed out")
                    time.sleep(.1)
            yield url
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def run_suite(workspace, evidence, url, variant, lab, helper=False):
    label = variant + ("-helper" if helper else "")
    junit = evidence / (label + ".xml")
    junit.unlink(missing_ok=True)
    command = [sys.executable, "-m", "pytest", "tests", "-q", "-ra", "--junitxml=" + str(junit)]
    if helper:
        command = [sys.executable, str(workspace / "automation" / "guardrails.py"),
                   "--workspace", str(workspace), "--junit", str(junit)]
    environment = {**os.environ, "BASE_URL": url, "PYTEST_ADDOPTS": "", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    with (evidence / (label + ".log")).open("w") as log:
        result = subprocess.run(command, cwd=workspace, env=environment, stdout=log,
                                stderr=subprocess.STDOUT, timeout=180)
    return inspect_junit(junit, result.returncode, variant, lab)


def semantic_t1(workspace, evidence, url):
    """Independent expectations; learner POM drives actual Chrome, not a fake DOM."""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    sys.path.insert(0, str(workspace))
    SettingsPage = importlib.import_module("pages.settings_page").SettingsPage
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    if os.environ.get("CHROME_BINARY"):
        options.binary_location = os.environ["CHROME_BINARY"]
    service = Service(os.environ["CHROMEDRIVER"]) if os.environ.get("CHROMEDRIVER") else Service()
    driver = webdriver.Chrome(service=service, options=options)
    try:
        page = SettingsPage(driver)
        expected_cases = [dict(connection="tcp", host="oracle.example.test", port="1502", password="oracle-demo"),
                          dict(connection="serial", device="COM9", password="oracle-transfer")]
        for expected in expected_cases:
            request = urllib.request.Request(url + "/api/reset", b"{}", {"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=5) as response:
                require(response.status == 200, "Oracle reset failed")
            page.open(url)
            for connection in ("tcp", "serial", "tcp"):
                page.choose_connection(connection)
                for field in ("device", "host", "port"):
                    wanted = (field == "device") == (connection == "serial")
                    require(driver.find_element(By.ID, field).is_displayed() == wanted, "UI-01: " + field)
            for auth in ("password", "none", "password"):
                page.choose_auth(auth)
                require(driver.find_element(By.ID, "password").is_displayed() == (auth == "password"), "UI-02")
            page.choose_connection(expected["connection"])
            for field, value in expected.items():
                if field != "connection":
                    page.fill(field, value)
            require(page.save() == "Saved", "SAVE-01: valid save acknowledgement")
            page.reload()
            for field, value in {**expected, "auth": "password"}.items():
                require(driver.find_element(By.ID, field).get_attribute("value") == value, "SAVE-01 reload: " + field)
            page.choose_auth("none")
            require(page.save() == "Saved", "SAVE-01: None save")
            page.reload()
            require(driver.find_element(By.ID, "auth").get_attribute("value") == "none", "SAVE-01 None reload")
            require(not driver.find_element(By.ID, "password").is_displayed(), "UI-02 None reload")
        return {"status": "passed", "cases": ["tcp-password", "serial-password", "none-reload"],
                "browser": driver.capabilities.get("browserVersion")}
    except Exception:
        driver.save_screenshot(str(evidence / "semantic-failure.png"))
        raise
    finally:
        driver.quit()


def protected_hashes(workspace):
    names = ["server.py", "ui.html", "conftest.py", "pages/base_page.py", "REQUIREMENTS.md", "case.json", "pytest.ini"]
    return {name: hashlib.sha256((workspace / name).read_bytes()).hexdigest() for name in names}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", required=True, choices=("t1", "t2"))
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--mode", choices=("md-only", "code"), default="code")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    evidence = workspace / "evidence" / "ci"
    evidence.mkdir(parents=True, exist_ok=True)
    report = {"lab": args.lab, "mode": args.mode, "workspace": str(workspace), "results": {}}
    status = 1
    try:
        baseline = protected_hashes(workspace)
        test_files = sorted((workspace / "tests").rglob("*.py"))
        require(test_files, "No learner tests found")
        suite_hash = {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in test_files}
        report["suite_sha256"] = suite_hash
        variants = ("correct",) if args.lab == "t1" else ("correct", "no-persist", "bad-boundary")
        names = None
        for variant in variants:
            with server(workspace, evidence, variant) as url:
                result = run_suite(workspace, evidence, url, variant, args.lab)
                report["results"][variant] = result
                if names is None:
                    names = result["names"]
                require(result["names"] == names, "Collected cases changed across variants")
                if variant == "correct":
                    if args.lab == "t1":
                        report["semantic"] = semantic_t1(workspace, evidence, url)
                    if args.mode == "code":
                        helper = run_suite(workspace, evidence, url, variant, args.lab, helper=True)
                        require(helper["names"] == names, "Helper ran a different test selection")
                        report["helper"] = helper
            require(protected_hashes(workspace) == baseline, "Protected application/framework files changed during grading")
            require(all(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest for name, digest in suite_hash.items()), "Tests changed across variants")
        if args.lab == "t2" and args.mode == "code":
            artifact = workspace / "evidence" / "variant-evaluation.json"
            artifact.unlink(missing_ok=True)
            with (evidence / "learner-variant-runner.log").open("w") as log:
                result = subprocess.run([sys.executable, str(workspace / "automation" / "evaluate_variants.py"),
                                         "--workspace", str(workspace)], cwd=workspace,
                                        stdout=log, stderr=subprocess.STDOUT, timeout=600)
            require(result.returncode == 0, "Learner server-owning variant runner failed")
            require(artifact.is_file(), "Missing fresh variant-evaluation.json")
            evaluation = json.loads(artifact.read_text())
            require(evaluation.get("status") == "passed", "Variant runner did not report passed")
            for variant, expected_code in (("correct", 0), ("no-persist", 1), ("bad-boundary", 1)):
                require(evaluation.get("variants", {}).get(variant, {}).get("pytest_returncode") == expected_code,
                        "Incorrect recorded variant outcome: " + variant)
            require(protected_hashes(workspace) == baseline, "Variant runner changed protected files")
            require(all(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest for name, digest in suite_hash.items()), "Variant runner changed tests")
            report["learner_variant_runner"] = evaluation
        report["status"] = "passed"
        status = 0
    except Exception as error:
        report.update(status="failed_or_blocked", error=f"{type(error).__name__}: {error}")
    (evidence / "grade.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
