"""Deliver one teaching stage without changing the complete task authority."""
from pathlib import Path
import hashlib
import json
import re

TEMPLATES = Path(__file__).resolve().parents[1] / "training_kit/prompts"
LABS = ("fw1", "fw2", "hw1", "hw2", "t1", "t2")
STAGES = ("stage1", "stage2", "stage3", "stage4", "replay-md", "replay-code")
READING = {
    "stage1": "Read CI_CONTRACT.md, the local requirements/report contract, case.json when supplied, and the candidate/adapter interfaces.",
    "stage2": "Read CI_CONTRACT.md, evidence/session.md and workflow.md. Consult requirements to resolve missing invariants.",
    "stage3": "Read CI_CONTRACT.md and workflow.md. Consult recorded evidence when an input/output boundary is unclear.",
    "stage4": "Read CI_CONTRACT.md, local requirements/report contract, extraction-map.md and workflow.md. Read needed implementations; do not reread whole terminal transcripts by default.",
    "replay-md": "Read CI_CONTRACT.md, local requirements/report contract, current case inputs and workflow.md.",
    "replay-code": "Read CI_CONTRACT.md, local requirements/report contract, current case inputs, workflow.md and automation/README.md.",
}


def stage_card(card, stage):
    """Keep the shared card introduction and the selected stage, including its tail."""
    headings = list(re.finditer(r"^## Stage ([1-4])\b[^\n]*", card, re.M))
    for index, heading in enumerate(headings):
        if heading.group(1) == stage[-1]:
            end = headings[index + 1].start() if index + 1 < len(headings) else len(card)
            return card[:headings[0].start()] + "\n" + card[heading.start():end]
    raise ValueError(f"Task card is missing Stage {stage[-1]}")


def prepare_context(workspace, lab, stage):
    """Save exact delivered prompt/context and return prompt plus audit metadata.

    Lab identity comes from the caller, not an assumed case.json: hardware has
    source/ and derived/ instead. All local contracts and the full original card
    retain authority. context/ changes between stages; its evidence snapshots do not.
    """
    if lab not in LABS or stage not in STAGES:
        raise ValueError("Unknown lab or teaching stage")
    workspace = Path(workspace)
    original = (workspace / "task-card.md").read_bytes()
    card = original.decode("utf-8")
    selected = stage_card(card, stage) if stage.startswith("stage") else (
        "Execute the supplied workflow on the current case. The full task-card.md "
        "and local contracts remain available; preserve all transfer and acceptance rules.\n"
    )
    note = json.loads((TEMPLATES / "lab-notes.json").read_text())[lab]
    if lab.startswith("t"):
        note += (" The correct server on port 8765 is caller-owned: leave it running. "
                 "Use distinct free ports/state files for owned variants; stop only your "
                 "children and inherit BASE_URL for externally owned servers.")
    context = (f"# Current stage: {lab.upper()} / {stage}\n\n{READING[stage]}\n\n"
               f"{selected}\n\n## Execution clarification\n{note}\n")
    prompt = ((TEMPLATES / "common.md").read_text() + "\n## Current deliverable\n" +
              (TEMPLATES / f"{stage}.md").read_text() + "\n")
    digest = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()
    metadata = {
        "lab": lab, "stage": stage, "condition": workspace.name,
        "full_card_characters": len(card), "current_card_characters": len(context),
        "prompt_characters": len(prompt),
        "task_card_sha256": hashlib.sha256(original).hexdigest(),
        "context_sha256": digest(context), "prompt_sha256": digest(prompt),
        "authority": "unchanged full task-card.md and local contracts",
    }
    (workspace / "context").mkdir(exist_ok=True)
    evidence = workspace / "evidence"
    evidence.mkdir(exist_ok=True)
    (workspace / "context/current-stage.md").write_text(context)
    (evidence / f"{stage}-context.md").write_text(context)
    (evidence / f"{stage}-prompt.txt").write_text(prompt)
    (evidence / f"{stage}-delivery.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return prompt, metadata
