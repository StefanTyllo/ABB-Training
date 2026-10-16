# Test summary

- **Tested commit:** `b0550ce43c5f5009c236a90f2c011426f6c17ab9`
- **Run:** [GitHub Actions run](https://github.com/StefanTyllo/ABB-Training/actions/runs/38907824162)
- **Overall outcome:** All seven checks passed.

| Check | Exit code | Outcome | Logged tests / coverage |
|---|---:|---|---|
| hardware-starters | 0 | Passed | 5 tests |
| firmware-replay | 0 | Passed | 11 tests |
| context-delivery | 0 | Passed | 8 tests |
| portability | 0 | Passed | 16 tests |
| t2-automation | 0 | Passed | 16 tests |
| firmware-smoke | 0 | Passed | FW1 demo/transfer; FW2 seeded failures and 50 corrected cases |
| http-server | 0 | Passed | Contracts: correct, no-persist, bad-boundary |

**Failure details:** No check-level assertion failures or infrastructure errors were reported. The firmware-replay `FAIL` messages and context-delivery timeout metadata occurred within passing negative-path tests. No corrective action is indicated.