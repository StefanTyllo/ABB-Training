# Focused GitHub Copilot rehearsal prompts

These templates drive the scripted GitHub Copilot CLI rehearsal. In class use
the handbook's interactive shared prompts and pause for the participant's
engineering explanation; the 600-second CI budget is not a classroom deadline.

The runner combines common.md, one stage/replay template and a current-stage
card with a focused reading list and lab clarification. The complete original
task card and local requirements/CI contract retain authority. Stage 4 may need
earlier card sections, especially T1's bootstrap/handover requirements.

Use short rationales and links to raw evidence. No automation/ directory exists
before Stage 4; early one-off fixtures belong under evidence/stage1-fixtures/.
Original captures stay immutable, the session journal may append, and temporary
host context is not a capture to freeze. Caller console output and helper-owned
run logs have different owners. Required artifacts and checks precede optional
expansion; a fresh transfer never copies completed demo task outputs.

The host renderer is training_ci/context_delivery.py in the repository. It saves
the exact delivered prompt, context and SHA-256 metadata for every invocation.
The runner owns context/current-stage.md; learners must not edit it. This prompt
library contains no completed learner solution and changes no acceptance rules.
