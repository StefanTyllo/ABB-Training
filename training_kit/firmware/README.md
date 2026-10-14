# Firmware technical reference

Use the PDF's FW1/FW2 cards and shared four-stage prompts as the training instructions. Prepare cases with the root `prepare_lab.py` wrapper shown there; do not initialize another device inside a prepared case.

These synthetic fixtures require Python 3.12 and, for FW2, GCC with C11 support. No physical board, serial adapter, external Python package or network is required. `requirements.md` is the behavioral contract. `fw1/device.py --help` describes low-level device access. `fw2/parser.c` intentionally contains defects; the public header and CLI are supplied adapters.

The clean firmware directory is reference material. Work only in a prepared participant directory. Instructor checks and corrected reference logic are excluded by preparation. They are an assessment tool, not the learner's workflow automation.

From the training root, the facilitator runs:

```bash
python materials/firmware/instructor/smoke.py
python materials/firmware/instructor/smoke.py work/fw2-demo/fw2/parser
```

The first validates the fixtures and an isolated corrected reference without changing the starter. The second grades the participant executable and is expected to fail on the untouched parser. Use the transfer executable path when assessing transfer. See `instructor/README.md` for evaluation details.
