# Instructor-only evaluation notes

FW1 starts with a configuration mismatch, not broken simulator code. Before/after
evidence capture, documented reasoning, abstraction, and verbose automation must
be authored by learners. Automated smoke checks cannot grade those teaching goals.
Review their transcript and artifacts separately; reject demo-specific constants
in an allegedly reusable workflow. Transfer expects SIM-083 and baud 38400.

FW2 seeds unsigned decoding (`-123` becomes `65413`) and resetting partial state
at every feed call (split input disappears). `smoke.py` changes only those two
lines in a temporary source copy and compiles both versions with warnings as errors.
It checks 50 stream cases plus malformed CLI input: signed extrema, zero, embedded
A5, every byte split, one-byte chunks, empty feeds, adjacent frames, noise, invalid
length/checksum, overlapping sync, and incomplete tail. The corrected reference is
only an oracle check; it is not a learner workflow or extraction solution.

Run `python3 instructor/smoke.py` from `firmware` to validate the kit itself.
Run `python3 instructor/smoke.py ./fw2/parser` to grade a learner build. Exit 0
means protocol cases passed, not that explanation, generalization, or automation
quality passed. All temporary smoke files live under this folder and are removed.
