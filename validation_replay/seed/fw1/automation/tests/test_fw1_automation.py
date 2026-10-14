"""Checks for the FW1 automation, run against disposable workspaces.

Each test builds a throwaway workspace in a temp dir (copy of fw1/device.py and
expected.json plus ``init --case transfer``), so the demo evidence and state are
never touched.  Run: python3 -m unittest discover -v automation/tests
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTOMATION = HERE.parent
DEMO = AUTOMATION.parent
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(AUTOMATION))
import capture_state as cs  # noqa: E402
import experiment as ex  # noqa: E402


def make_workspace(case="transfer", expected=None):
    """Create a disposable prepared workspace; returns its Path."""
    root = Path(tempfile.mkdtemp(prefix="fw1-check-"))
    (root / "fw1").mkdir()
    shutil.copy(DEMO / "fw1" / "device.py", root / "fw1" / "device.py")
    shutil.copy(expected or DEMO / "fw1" / "expected.json", root / "fw1" / "expected.json")
    (root / "case.json").write_text(json.dumps({"lab": "fw1", "case": case}))
    subprocess.run([sys.executable, str(root / "fw1" / "device.py"), "--workdir",
                    str(root / "device"), "init", "--case", case], check=True, capture_output=True)
    (root / "evidence").mkdir()
    return root


def run_cli(script, root, *extra):
    """Run an automation script; returns CompletedProcess."""
    return subprocess.run([sys.executable, str(AUTOMATION / script), "--workspace", str(root), *extra],
                          capture_output=True, text=True)


def device(root, *args):
    """Call the low-level tool directly and return parsed JSON."""
    out = subprocess.run([sys.executable, str(root / "fw1" / "device.py"), "--workdir",
                          str(root / "device"), *args], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


class Fw1AutomationChecks(unittest.TestCase):
    def setUp(self):
        self.dirs = []

    def tearDown(self):
        for d in self.dirs:
            shutil.rmtree(d, ignore_errors=True)

    def workspace(self, **kw):
        root = make_workspace(**kw)
        self.dirs.append(root)
        return root

    def test_valid_capture_saves_complete_baseline(self):
        root = self.workspace()
        res = run_cli("capture_state.py", root, "--save-baseline")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        baseline = json.loads((root / "evidence" / "baseline.json").read_text())
        self.assertEqual(set(baseline), {"identity", "firmware", "config", "faults", "logs"})
        self.assertEqual(baseline["config"]["baud"], 9600)
        self.assertIn("LINK_TIMEOUT", baseline["faults"])

    def test_missing_state_directory_is_blocked(self):
        root = self.workspace()
        shutil.rmtree(root / "device")
        for script in ("capture_state.py", "experiment.py", "guardrails.py"):
            res = run_cli(script, root)
            self.assertEqual(res.returncode, 2, f"{script}: {res.stdout}")
            self.assertIn("BLOCKED", res.stdout)

    def test_nonexistent_workspace_is_blocked(self):
        res = run_cli("guardrails.py", HERE / "does-not-exist")
        self.assertEqual(res.returncode, 2)

    def test_failed_read_prevents_baseline(self):
        root = self.workspace()
        paths = cs.resolve_paths(root)["paths"]
        capture = cs.capture_state(paths)
        capture["complete"], capture["failed_reads"] = False, ["logs"]
        result = cs.write_baseline(paths, capture)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse((root / "evidence" / "baseline.json").exists())

    def test_unknown_identity_cannot_select_reference(self):
        root = self.workspace(expected=FIXTURES / "expected_unknown_identity.json")
        paths = cs.resolve_paths(root)["paths"]
        result = cs.select_reference(paths["reference"], {"device_id": "SIM-083"}, {"version": "1.4.2"})
        self.assertEqual(result["status"], "BLOCKED")
        before = (root / "device" / "state.json").read_bytes()
        res = run_cli("guardrails.py", root)
        self.assertNotEqual(res.returncode, 0, res.stdout)
        self.assertEqual(before, (root / "device" / "state.json").read_bytes())

    def test_experiment_without_baseline_is_rejected(self):
        root = self.workspace()
        res = run_cli("experiment.py", root)
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertIn("baseline", res.stdout)
        self.assertEqual(device(root, "read", "--field", "config"), {"baud": 9600})

    def test_stale_baseline_is_rejected(self):
        root = self.workspace()
        run_cli("capture_state.py", root, "--save-baseline")
        device(root, "set", "--parameter", "baud", "--value", "4800")  # drift after baseline
        res = run_cli("experiment.py", root)
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertIn("stale baseline", res.stdout)
        self.assertEqual(device(root, "read", "--field", "config"), {"baud": 4800})

    def test_correct_change_restores_probe_and_rerun_is_idempotent(self):
        root = self.workspace()
        run_cli("capture_state.py", root, "--save-baseline")
        self.assertFalse(device(root, "probe")["ok"])
        res = run_cli("experiment.py", root)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertTrue(device(root, "probe")["ok"])
        self.assertEqual(device(root, "read", "--field", "faults"), [])
        logs = device(root, "logs")
        self.assertEqual(logs, ["boot: link timeout", "baud changed: 9600 -> 38400"])
        state_file, baseline = root / "device" / "state.json", root / "evidence" / "baseline.json"
        snapshot = (state_file.read_bytes(), baseline.read_bytes())
        res = run_cli("guardrails.py", root)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(snapshot, (state_file.read_bytes(), baseline.read_bytes()))

    def test_target_comes_from_reference_not_hardcoded(self):
        root = self.workspace(expected=FIXTURES / "expected_altered_baud.json")
        res = run_cli("guardrails.py", root)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(device(root, "read", "--field", "config"), {"baud": 57600})

    def test_guardrails_refuses_to_fabricate_baseline_on_repaired_device(self):
        root = self.workspace()
        device(root, "set", "--parameter", "baud", "--value", "38400")
        res = run_cli("guardrails.py", root)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertFalse((root / "evidence" / "baseline.json").exists())

    def test_failed_verification_is_reported_as_fail(self):
        baseline = {"identity": {"device_id": "X"}, "firmware": {"version": "1"},
                    "config": {"baud": 9600}, "faults": ["LINK_TIMEOUT"], "logs": ["boot: link timeout"]}
        after = dict(baseline, probe={"ok": False, "status": "timeout"})
        verdict = ex.compare_before_after(baseline, after, 38400)
        self.assertEqual(verdict["status"], "FAIL")
        self.assertFalse(next(c for c in verdict["checks"] if c["name"] == "probe_ok")["pass"])


if __name__ == "__main__":
    unittest.main()
