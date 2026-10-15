# ABB workflow training — retained validation evidence

All records concern synthetic training fixtures, not production ABB systems. Exact Actions artifact ZIP bytes are preserved here before their 14-day hosted retention expires. archive_manifest.json records each ZIP's SHA-256 and byte length. Original failures are retained alongside corrections; never interpret the initial run as wholly green.

## Provenance and results

| Archive | Run | Commit | Result and interpretation |
| --- | --- | --- | --- |
| fw1.zip | 38592278866 | e36498d5e48667077444be81c6061a6dacd11bd6 | Three final-state grades passed, but transcript review found code-transfer manual fallback after a tool denial. Superseded for code execution evidence by fw1-refined. |
| fw2.zip | 38592278866 | e36498d5e48667077444be81c6061a6dacd11bd6 | Demo, MD transfer and code transfer passed; 50 independent stream cases and malformed-input checks. |
| hw1.zip | 38592278866 | e36498d5e48667077444be81c6061a6dacd11bd6 | Demo passed; both transfers correctly blocked on absent revision, leaving netlist unchanged. |
| hw2.zip | 38592278866 | e36498d5e48667077444be81c6061a6dacd11bd6 | Demo passed; both transfers correctly recorded design-limit failure with accurate regeneration/provenance. |
| t1.zip | 38592278866 | e36498d5e48667077444be81c6061a6dacd11bd6 | All three real-browser assessments passed. Review found incomplete browser identity/screenshot retention and missing rejection checks. |
| t2.zip | 38592278866 | e36498d5e48667077444be81c6061a6dacd11bd6 | Demo and MD transfer passed. Code transfer hit the 300-second outer grader limit; original overall run failed. |
| fw1-refined.zip | 38594335199 | 6f4d93da7a36985a954a4de57f7a1cdcefc0de72 | Fresh transfer passed actual code execution, full raw before/after captures, one mutation, preservation on rerun and 18 helper tests. |
| t1-refined.zip | 38595251454 | 8fb42db1bda27a4dadc5f36ce86d90f2f7151bb8 | Browser checks passed; adds real capabilities, retained failure screenshot and invalid-save/password assertions. Four original XML self-test fixtures were omitted from seed. |
| t1-complete-package.zip | 38596385772 | 30edbf3cab41bbed320afe6b22b38482dd356dda | Exact missing XML fixtures restored; 13 helper tests, eight browser cases and independent semantic oracle passed. |
| t2-complete-package.zip | 38597697875 | 026c8b6bc7ee3a0a51fc2631fbd9dc19bfbb557c | The unchanged package passed the complete 900-second-limit regrade, including 16 helper self-tests, all 12 correct-app browser tests, relevant assertion failures for both mutants, helper execution and protected-input hashes. Regrade: https://github.com/StefanTyllo/ABB-Training/actions/runs/38597697875 |

Run URL pattern: https://github.com/StefanTyllo/ABB-Training/actions/runs/ followed by the numeric run ID. Repository access is required.

## Review notes

- Real Copilot CLI version 1.0.97, Node 22 and Python 3.12.15 were used on hosted Ubuntu. Exact model identity was not recorded. No human classroom pilot is claimed.
- Copilot performed four scripted stage invocations and two fresh transfers per lab. Stage/file handoffs are an approximation of the learner's continuous, narrated terminal conversation.
- Hardware transfer checker implementations were reused. Their initial helper unit tests depended on demo inputs; the agent repaired those tests into independent fixtures during transfer. This is not zero-intervention portability. Unexercised stale-report/provenance combinations remain outside the measured claims.
- T1 initial code transfer used unchanged helper implementations. Follow-up browser 154.0.8037.97 and retained PNG were observed. The follow-up package omission was a packaging defect, not grounds to suppress failed self-test evidence.
- T2 direct transfer-code suites before timeout already recorded correct 12/0; no-persist 12/8 relevant assertion failures; bad-boundary 12/3 relevant assertion failures; all zero errors/skips. Helper-correct had 12 passes. Its three automation implementation files were byte-identical to demo and actually invoked by Copilot. The final repeat of variants had not completed when the original outer timeout fired.
- T2's inferred failure-phase field is flagged for review. Demo labels a 65535 rejection after reload although the actual assertion fails at Save before reload. Human interpretation uses assertion evidence.
- Independent graders ran without the Copilot secret. They reject protected-source changes, skips/infrastructure failures, irrelevant mutant failures and missing evidence. Passing the measured paths does not establish general adversarial resistance.

## Reading order

Start with each initial archive's assessment.json and case-specific independent-grader logs. Read stage/replay transcripts when checking actual tool invocation. Follow-up archives contain their fresh evidence directories; T1 refinement has an additional t1-refined/ root. Complete-package archives contain regenerated independent grade reports. Use the PDF for the participant sequence and training acceptance rubric.
