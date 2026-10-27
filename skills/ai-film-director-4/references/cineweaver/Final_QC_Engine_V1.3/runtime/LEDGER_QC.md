# PRODUCTION LEDGER QC

Check:
- `PRODUCTION_LEDGER.json` exists and parses as an object;
- `scope_type` matches the confirmed project format;
- film target runtime or episode target count matches the confirmed Project Brief;
- completed film units / completed episodes are continuous and correspond to real completed storyboard units;
- film `coverage.covered_seconds` and `coverage.gaps` agree with registered completed units;
- episode `coverage.completed_count` agrees with `completed_episodes`;
- `status=COMPLETED` is allowed only when the confirmed full runtime / full episode count is covered with no gap;
- `next_resume` points to the first uncovered film second or next unfinished episode while status is `IN_PROGRESS`;
- Production Ledger stores coverage/checkpoint state only and does not copy full Prompt bodies.

QC may synchronize ledger status/coverage metadata but must not edit creative artifact bodies.
