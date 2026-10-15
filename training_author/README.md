# Rebuild and verify the handbook

`guide.md` is the source. Each `<!-- PAGE -->` marker is an intentional logical
page so existing handbook page links stay stable. The checked-in PDF includes
the exact current `training_kit/` starter files and generated complete local task cards, including focused Copilot prompts.

On the documented Ubuntu/Bash authoring environment, install DejaVu Sans and
Mono fonts (`fonts-dejavu-core`) and the pinned Python dependencies, then run:

```bash
python -m pip install -r training_author/requirements.txt
python training_author/build_guide.py
python training_author/check_materials.py
```

The builder embeds fonts, retains one page per logical section and writes
`materials-manifest.json` with source/attachment hashes, per-file hashes and page
scales. It excludes caches, authentication state and secret environment files.
The checker verifies every embedded starter byte against source, attachment
integrity, logical page count and the source digest recorded inside the PDF.
Inspect rendered pages after layout/content changes; automated consistency checks
alone do not establish readability. Original historical validation archives are
evidence and are never rebuilt or relabeled by this tool.
