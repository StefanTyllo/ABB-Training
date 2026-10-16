# Rebuild and verify the handbook

`guide.md` is the source. PAGE markers begin logical sections; long sections flow
onto additional A4 pages. Use section titles when referring to the handbook.

From the repository folder, run `python setup_env.py --agents`, activate `.venv`,
then build to a fresh output path:

```text
python training_author/build_guide.py --sync-cards --output export/rebuilt-handbook.pdf
```

Review the rendered PDF, then replace `docs/ABB_Workflow_Training.pdf` and copy the
sibling `materials-manifest.json` into `training_author/`. The builder uses local
Playwright Chromium (or `CHROME_BINARY`) and attaches the sanitized learner
starter package. Instructor/assessment sources and authentication are excluded.
The metadata records guide/starter hashes, page counts and layout policy.

```text
python training_author/check_materials.py
python -m pytest tests/runtime -q
```

Build separate learner/facilitator distributions to a directory outside the repo:

```text
python training_author/build_package.py --source . --output ../abb-releases --audience learner
python training_author/build_package.py --source . --output ../abb-releases --audience facilitator
```

Historical validation archives remain unchanged.
