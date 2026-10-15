# ABB workflow training starters

This attachment accompanies ABB_Workflow_Training.pdf. The PDF is the canonical training sequence and contains the guided shared prompts. prompts/ also retains the focused GitHub Copilot CI templates. It is deliberately not copied into six different README files.

Keep this extracted materials directory unchanged. From its parent directory prepare a fresh participant workspace:

    python materials/prepare_lab.py fw1 demo work/fw1-demo

Lab IDs: fw1, fw2, hw1, hw2, t1, t2. Cases: demo, transfer. Output must not already exist. Prepared workspaces include learner inputs, basic tools, the complete task-card.md, and evidence/. They exclude instructor/ directories. hardware workspaces also contain REPORT_CONTRACT.md.

Use the PDF lab card for actual walkthrough, abstraction, extraction, implementation, transfer and grading. The firmware/hardware/test_team README files are technical references. Instructor and author_checks folders validate the starters; they are not generated learner workflows.

All devices and data are synthetic. The local application has deliberately simple state and invented password values and must not be deployed as a real service. See VERIFICATION.md for the measured checks and outstanding live acceptance gates.
