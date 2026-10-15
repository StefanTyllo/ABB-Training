"""Token-free regression checks for context delivery and the real Copilot interface."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))
import run_lab
from context_delivery import prepare_context


class ContextDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def workspace(self, lab, condition="demo"):
        workspace = self.root / lab / condition
        workspace.mkdir(parents=True)
        (workspace / "evidence").mkdir()
        (workspace / "task-card.md").write_text(run_lab.card(lab))
        # Hardware deliberately has source/ and derived/, not case.json.
        if not lab.startswith("hw"):
            (workspace / "case.json").write_text(json.dumps({"lab": lab}))
        return workspace

    def test_every_real_card_and_transfer_keeps_original_authority(self):
        for lab in run_lab.LABS:
            for stage in ("stage1", "stage2", "stage3", "stage4", "replay-md", "replay-code"):
                with self.subTest(lab=lab, stage=stage):
                    condition = "transfer-" + stage.split("-")[1] if stage.startswith("replay-") else stage
                    workspace = self.workspace(lab, condition)
                    original = (workspace / "task-card.md").read_bytes()
                    prompt, meta = prepare_context(workspace, lab, stage)
                    context = (workspace / "context/current-stage.md").read_text()
                    self.assertEqual((workspace / "task-card.md").read_bytes(), original)
                    self.assertEqual(meta["task_card_sha256"], hashlib.sha256(original).hexdigest())
                    self.assertEqual(meta["context_sha256"], hashlib.sha256(context.encode()).hexdigest())
                    self.assertEqual((workspace / "evidence" / f"{stage}-prompt.txt").read_text(), prompt)
                    self.assertEqual((workspace / "evidence" / f"{stage}-context.md").read_text(), context)
                    self.assertIn("CI_CONTRACT.md", prompt)
                    self.assertFalse((workspace / "automation").exists())
                    if stage.startswith("stage"):
                        self.assertIn(f"## Stage {stage[-1]}", context)
                        for other in "1234":
                            if other != stage[-1]:
                                self.assertNotIn(f"## Stage {other}", context)

    def test_all_prepared_cases_include_the_complete_current_card(self):
        for lab in run_lab.LABS:
            for case in ("demo", "transfer"):
                with self.subTest(lab=lab, case=case):
                    workspace = self.root / "prepared" / lab / case
                    subprocess.run([sys.executable, str(CI.parent / "training_kit/prepare_lab.py"),
                                    lab, case, str(workspace)], check=True, capture_output=True)
                    self.assertEqual((workspace / "task-card.md").read_text(), run_lab.card(lab))
                    self.assertFalse((workspace / "automation").exists())

    def test_next_stage_preserves_previous_delivered_context(self):
        workspace = self.workspace("fw1")
        prepare_context(workspace, "fw1", "stage1")
        previous = (workspace / "evidence/stage1-context.md").read_bytes()
        prepare_context(workspace, "fw1", "stage4")
        self.assertEqual((workspace / "evidence/stage1-context.md").read_bytes(), previous)
        self.assertNotEqual((workspace / "context/current-stage.md").read_bytes(), previous)

    def test_incomplete_card_is_rejected_before_writing_delivery(self):
        workspace = self.workspace("fw2")
        (workspace / "task-card.md").write_text("# Incomplete task\n## Stage 1\nOnly first stage\n")
        with self.assertRaisesRegex(ValueError, "Stage 4"):
            prepare_context(workspace, "fw2", "stage4")
        self.assertFalse((workspace / "context").exists())

    def test_invalid_lab_or_stage_cannot_select_another_file(self):
        workspace = self.workspace("fw1")
        for lab, stage in [("../other", "stage1"), ("fw1", "../common")]:
            with self.assertRaises(ValueError):
                prepare_context(workspace, lab, stage)
        self.assertFalse((workspace / "context").exists())

    def test_copilot_call_is_isolated_and_browser_tools_are_explicit(self):
        workspace = self.workspace("t1")
        with patch.object(run_lab.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as call:
            run_lab.agent(workspace, "stage1", "t1")
        args, kwargs = call.call_args
        command = args[0]
        self.assertEqual(command[0], "copilot")
        self.assertIn("--no-custom-instructions", command)
        self.assertIn("--no-auto-update", command)
        self.assertIn("--disable-builtin-mcps", command)
        self.assertIn("--allow-tool=playwright", command)
        config = json.loads(command[command.index("--additional-mcp-config") + 1])
        self.assertIn("@playwright/mcp@0.0.83", config["mcpServers"]["playwright"]["args"])
        self.assertEqual(kwargs["timeout"], 600)
        self.assertNotEqual(kwargs["env"].get("COPILOT_HOME"), str(Path.home() / ".copilot"))
        self.assertFalse(Path(kwargs["env"]["COPILOT_HOME"]).exists())
        self.assertEqual(kwargs["cwd"], workspace)
        meta = json.loads((workspace / "evidence/stage1-execution.json").read_text())
        self.assertEqual(meta["returncode"], 0)

    def test_timeout_is_retained_as_failure_metadata(self):
        workspace = self.workspace("fw1")
        with patch.object(run_lab.subprocess, "run", side_effect=subprocess.TimeoutExpired("copilot", 600)):
            with self.assertRaisesRegex(RuntimeError, "stage1"):
                run_lab.agent(workspace, "stage1", "fw1")
        meta = json.loads((workspace / "evidence/stage1-execution.json").read_text())
        self.assertTrue(meta["timed_out"])
        self.assertEqual(meta["returncode"], 124)
        self.assertTrue((workspace / "evidence/stage1-context.md").exists())


if __name__ == "__main__":
    unittest.main()
