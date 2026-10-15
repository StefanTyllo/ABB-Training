# GitHub Copilot rehearsal and independent assessment

`run_lab.py LAB` prepares three fresh workspaces, runs four teaching stages with
GitHub Copilot CLI, then performs separate Markdown-only and code-assisted fresh
transfers. `grade_all.py LAB` independently assesses the generated work. Keep the
Copilot token scoped to the agent step; graders neither need nor receive it.

## Context delivery

`context_delivery.py` renders templates from `training_kit/prompts/`. Lab identity
is explicit: hardware workspaces do not have case.json. Each stage receives the
card introduction/current section, a reading list and lab-specific invariants.
The complete `task-card.md`, local requirements and CI contract are unmodified
authorities, available on demand. Teaching and acceptance requirements are not
removed to meet a time budget.

Each workspace retains `evidence/<stage>-prompt.txt`, `<stage>-context.md`,
`<stage>-delivery.json`, `<stage>-transcript.md`, `<stage>-response.txt` and
`<stage>-execution.json`. The first three capture what was actually delivered;
delivery metadata records source/prompt/context SHA-256 values and character
counts. `context/current-stage.md` can change between invocations. Preserve the
saved snapshots instead of treating the mutable host directory as baseline data.

## Copilot execution

The pinned CLI receives `--no-auto-update`, `--no-custom-instructions` and disabled
skill retrieval inside a fresh temporary `COPILOT_HOME`. The profile is removed
after each invocation, including timeouts; user-global configuration is untouched.
Built-in remote MCPs are disabled and browser labs explicitly configure reviewed
Playwright MCP 0.0.83. Shell allowances include the supplied Python/C tools plus
Node/npm/npx and Git for the T1 bootstrap/ignore checks. These allowances and the
workspace convention are not a security boundary against arbitrary Python code.

Model and reasoning effort can be supplied via `COPILOT_MODEL` and
`COPILOT_REASONING_EFFORT`; otherwise execution records honestly identify CLI
defaults. Classroom comparisons must record/use the same intended model. The
existing 600-second outer stage limit is unchanged, with no shorter adapter
cutoff. Timeout return 124 and elapsed time are retained as failure metadata.

The manual validation workflow offers all six labs or any single lab for a
focused rerun. Select the lab from actual assessment evidence; no historical
experiment failure group is mislabeled as a new Copilot result. Rerun selection
does not permit omitting grading checks.

## Token-free checks

```bash
python -m unittest discover -s training_ci/tests -v
python -m pip install -r training_author/requirements.txt
python training_author/check_materials.py
```

These verify real card/stage/replay delivery, authority/past-snapshot preservation,
the Copilot command interface and recorded timeout failures, plus exact PDF/source
and starter-attachment consistency. Command execution is stubbed in interface
tests; this is not an authenticated Copilot acceptance run. PR CI also runs the
checks on Python 3.12. Original Copilot results remain in validation_records;
new prompt/runner changes need their own authenticated rehearsal before any claim
of new agent acceptance, facilitator approval or classroom readiness.
