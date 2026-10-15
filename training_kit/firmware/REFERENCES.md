# Fixture references

These fixtures are original synthetic training material, not vendor protocols or
an actual incident. `requirements.md` is the authoritative exercise specification.
`fw1/expected.json` holds expected device settings. `fw2/parser.h` specifies the
host parser interface. `instructor/smoke.py` holds evaluation vectors and the
isolated reference correction. No third-party source code or hardware manual is
needed. Python's standard library and a local C11 compiler provide the runtime.
