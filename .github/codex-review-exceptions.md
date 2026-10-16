# Codex review exceptions

Suppress a finding only when it matches the file and issue described below.
Continue reporting other problems in the same file or platform.
Add new exceptions here after the repository owner accepts them.

## FP-001: Linux x64 Codex optional package in the lockfile

- File: `training_runtime/package-lock.json`
- Finding to skip: `[P1] Restore the Linux x64 Codex package in the lockfile`.
- Scope: The missing `@openai/codex-linux-x64` optional-package entry in this
  lockfile. The original review cited lines 246–247; match the issue and file,
  since line numbers may change.
- Reason: The repository owner explicitly classified this finding as a false
  positive. This is an accepted review exception, not a claim that Linux x64
  installation has been verified.
- Boundary: Continue reporting unrelated dependency, installation, runtime,
  platform-support, and lockfile problems.
