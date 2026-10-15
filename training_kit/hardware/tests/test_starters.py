"""Behavior tests: missing preparation/generation or an unsafe overwrite breaks these."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StartersTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "case"

    def run_command(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)

    def prepare(self, lab, case):
        result = self.run_command(ROOT / "prepare.py", "--lab", lab, "--case", case, "--output", self.out)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_four_cases_and_no_overwrite(self):
        for lab in ("hw1", "hw2"):
            for case in ("demo", "transfer"):
                self.out = Path(self.temp.name) / f"{lab}-{case}"
                self.prepare(lab, case)
                self.assertTrue((self.out / "source").is_dir())
                self.assertFalse((self.out / "instructor").exists())
                marker = self.out / "KEEP"
                marker.write_text("participant work")
                result = self.run_command(ROOT / "prepare.py", "--lab", lab, "--case", case, "--output", self.out)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(marker.read_text(), "participant work")

    def test_hw1_transfer_revision_is_missing(self):
        self.prepare("hw1", "transfer")
        schematic = json.loads((self.out / "source/schematic.json").read_text())
        self.assertIsNone(schematic["source_revision"])
        self.assertEqual(schematic["board_id"], "SENSE-BETA")

    def test_generator_uses_config_and_digest(self):
        for case, expected in (("demo", 11.0), ("transfer", 9.2)):
            self.out = Path(self.temp.name) / case
            self.prepare("hw2", case)
            config = self.out / "source/circuit.json"
            output = self.out / "derived/calibration.json"
            self.assertEqual(json.loads(output.read_text())["inverse_gain"], 10.0)
            command = (self.out / "tools/generate_calibration.py", "--config", config, "--output", output)
            refused = self.run_command(*command)
            self.assertNotEqual(refused.returncode, 0)
            result = self.run_command(*command, "--replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = json.loads(output.read_text())
            self.assertAlmostEqual(actual["inverse_gain"], expected)
            canonical = json.dumps(json.loads(config.read_text()), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            self.assertEqual(actual["source_sha256"], hashlib.sha256(canonical).hexdigest())
            before = output.read_bytes()
            result = self.run_command(*command, "--replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), before)

    def test_generator_rejects_invalid_config_without_overwriting(self):
        self.prepare("hw2", "demo")
        config = self.out / "source/circuit.json"
        value = json.loads(config.read_text())
        value["r_top_ohm"] = -100
        config.write_text(json.dumps(value))
        output = self.out / "derived/calibration.json"
        before = output.read_bytes()
        result = self.run_command(self.out / "tools/generate_calibration.py", "--config", config, "--output", output, "--replace")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), before)

    def test_instructor_accepts_all_correct_outcomes_and_rejects_false_pass(self):
        answers = json.loads((ROOT / "instructor/expected.json").read_text())
        for lab in ("hw1", "hw2"):
            for case in ("demo", "transfer"):
                self.out = Path(self.temp.name) / f"review-{lab}-{case}"
                self.prepare(lab, case)
                expected = answers[f"{lab}/{case}"]
                report = {"schema_version": 1, "lab": lab, "case": case,
                          "board_id": expected["board_id"], "status": expected["status"],
                          "findings": [{"code": code, "evidence": "source field and observed derived value", "explanation": "Synthetic test evidence"} for code in expected["finding_codes"]],
                          "assumptions": ["Synthetic exercise model only"], "changed_files": []}
                if lab == "hw1" and case == "demo":
                    netlist_path = self.out / "derived/netlist.json"
                    netlist = json.loads(netlist_path.read_text())
                    for component in netlist["components"]:
                        if component["ref"] == "R1":
                            component["value"] = "4700 Ohm"
                        if component["ref"] == "U1":
                            component["pins"]["2"] = "SENSE"
                            component["pins"]["3"] = "GND"
                    netlist_path.write_text(json.dumps(netlist))
                    report["changed_files"] = ["derived/netlist.json"]
                elif lab == "hw2":
                    result = self.run_command(self.out / "tools/generate_calibration.py", "--config", self.out / "source/circuit.json", "--output", self.out / "derived/calibration.json", "--replace")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report["changed_files"] = ["derived/calibration.json"]
                    report["calculations"] = expected["calculations"]
                report_path = self.out / "report.json"
                report_path.write_text(json.dumps(report))
                command = (ROOT / "instructor/check.py", "--lab", lab, "--case", case, "--workspace", self.out)
                result = self.run_command(*command)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                report["status"] = "pass" if expected["status"] != "pass" else "fail"
                report_path.write_text(json.dumps(report))
                result = self.run_command(*command)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("report status", result.stdout)


if __name__ == "__main__":
    unittest.main()
