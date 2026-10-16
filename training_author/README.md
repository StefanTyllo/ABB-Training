# Rebuild and verify the handbook

`guide.md` is the source. PAGE markers begin logical sections; long sections flow
onto additional A4 pages at the normal font size. The Docker edition therefore
records actual PDF pages rather than preserving the previous host edition's page
numbers. Use section titles when referring to the current handbook.

Run publication tools inside the locked facilitator image. No host Python, fonts,
compiler or browser installation is required. From the repository folder:

```text
docker compose --profile facilitator build facilitator
docker compose --profile facilitator run --rm grader python /opt/abb/repo/training_author/build_guide.py --output /workspace/export/rebuilt-handbook.pdf
```

Choose a fresh output name. Copy the PDF from the export volume after reviewing
it, and copy the sibling `materials-manifest.json` into `training_author/`.
For edits to lab sections, use `--sync-cards` in a writable author checkout before
building so the six `training_kit/task_cards/` files match the guide. Never edit
image-owned source; rebuild the image from the updated checkout.

The builder uses the baked sandboxed Playwright browser and attaches the same
sanitized Docker learner starter context used by the learner distribution. It
omits instructor/assessment sources and authentication state. The manifest and
PDF metadata record guide and starter hashes; the manifest also records actual
pages, logical sections, layout policy and every packaged source hash.

After replacing the reviewed PDF and manifest, rebuild the facilitator image and
run `python /opt/abb/repo/training_author/check_materials.py` inside its grader.
That checker verifies all attachment bytes and complete current task cards.
Inspect rendered pages after layout/content changes; consistency checks alone
do not establish readability. Historical validation archives remain unchanged.
