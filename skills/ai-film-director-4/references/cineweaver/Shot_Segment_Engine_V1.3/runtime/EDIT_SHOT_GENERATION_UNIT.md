# EDIT SHOT / GENERATION UNIT / PRODUCTION BLOCK｜Seedance Adapter

- `SH001 / SH002...` = real editorial shots; duration is narratively free.
- `PH01 / PH02...` = continuous state phases; not cuts; phase-first by default.
- `GU001 / GU002...` = one model invocation.

## Model windows
- Seedance 2.5: max `30s` per GU.
- Seedance 2.0: max `15s` per GU.
- OTHER: read Model Adapter; never guess.

## Packing
- 15S: organize calls up to 15s.
- 30S_BLOCK: under Seedance 2.5 may be one ≤30s GU when safe; under Seedance 2.0 requires multiple ≤15s GUs.
- AUTO: choose by narrative, performance, spatial/control risk and active model capability.

Important micro-performance, dialogue, physics, camera path, reveal/payoff or continuity-risk shots may remain isolated even with unused capacity.

V001/V002 voice assets are text-only: `seedance_reference_slot_cost: 0`; never `@音频`.

**Core:** generation capacity serves film grammar; film grammar never serves generation capacity.
