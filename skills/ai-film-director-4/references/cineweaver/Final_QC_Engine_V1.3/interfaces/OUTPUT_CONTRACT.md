# OUTPUT CONTRACT

Output exactly one QC artifact:
`FINAL_QC.md`

Return:
- project_result: PASS | FAIL
- per-shot qc_status: WAIT | PASS | FAIL
- issue ledger
- retest_required

Do not duplicate final video Prompt body.

Allowed metadata synchronization:
- QC state
- blocker reason
- next action
- prompt length metadata
- stale flags

No creative-text auto rewrite.
