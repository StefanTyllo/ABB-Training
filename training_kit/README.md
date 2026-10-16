# ABB workflow training materials

Use the [virtual environment README](../README.md), current handbook and your exercise's student guide. Install the documented host tools, run `python setup_env.py --agents`, activate `.venv` and use approved accounts.

**Host terminal**, in the unpacked package folder:

```text
abb doctor --offline
abb doctor --offline
abb prepare fw1 demo
abb shell --workspace work/fw1-demo
```

**Inside the workspace**:

```bash
pwd
# Expected: work/fw1-demo
```

Lab IDs are fw1, fw2, hw1, hw2, t1 and t2. Cases are demo and transfer. Each guide shows its own concrete entry and both fresh transfer paths. Prepared workspaces include the complete current task-card.md. Preparation refuses an existing output; resume by re-entering it without preparation. Clean sources remain image-owned. Provider authentication is separate from entering this shell.

The four teaching stages remain demonstration, Markdown abstraction, extraction decisions, then reusable code. Follow the PDF and student guide for allowed changes and acceptance. Instructor and solved validation sources ship only in the facilitator package. All devices and data are synthetic.
