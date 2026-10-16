# Main integration verification — 16 October 2026

Merged remote main a8f2f95 (Copilot focused context, complete local task cards and
material verification) into the Docker implementation e5626cd without dropping
either change. The candidate tree/image and test results are in the manifest.

Resolution preserves dynamic one-lab/all-lab dispatch, native model/effort
variables, exact delivered context evidence, unchanged 600-second stage timeout,
normal classroom approvals, Docker-only execution, credential-free grading and
sanitized learner materials. Runtime secret login is imported into each ephemeral
Copilot profile; browser MCP uses the baked sandboxed tooling without npx downloads.
The context/material workflow now uses the reusable locked Docker image. Its
build gates both the original container suite and upstream context/material checks.

The merged guide supplies all six exact task cards. The 44-page PDF and its clean
Docker attachment were regenerated, hash-verified and visually checked across all
pages. The former host renderer entry point now delegates to the locked renderer;
manifest format 2 records flowing pages, normal font size and sanitized package
hashes. Historical records remain unchanged. No new live-agent or native Windows
acceptance is claimed; the older T1/T2 reference runs retain their exact provenance.

Validation: 67 tests passed (59 container + 8 context), including 12 complete-card
preparations and all 36 card/stage/replay combinations. Current published materials
checker passed. RED evidence demonstrates stale cards, runtime-download MCP and
missing scoped-profile authentication integration were detected before resolution.
No subagents, force push, history rewrite or primary-checkout changes were used.
