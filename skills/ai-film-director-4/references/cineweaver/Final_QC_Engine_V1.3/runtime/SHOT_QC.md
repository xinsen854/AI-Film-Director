# SHOT QC｜V1.5 Content Quality

Hard checks:
- supplied V4.8-derived EDIT SHOT sections are preserved when applicable;
- **section presence alone is insufficient**: relevant fields contain current-shot concrete facts;
- `FIELD_BOILERPLATE` is ERROR when fields use generic/template filler instead of execution content;
- performance/reaction shots express important emotion through **可观察** behavior rather than a bare label such as `保持克制`;
- camera fields specify current framing/position/behavior/composition when materially relevant;
- spatial fields specify current positions/movement rather than dumping a full map;
- sound fields contain current audible events only;
- continuity fields contain current required facts and exclude future information;
- SH001/GU001/PH01 identifiers are structurally valid;
- PHASE contains no hidden edit;
- true EDIT SHOT boundaries use explicit CUT when packed;
- editorial duration is not mechanically quantized to 15/30 seconds;
- repeated SHs that exactly fill the same model ceiling require distinct dramatic `duration_basis` evidence or trigger `MECHANICAL_DURATION_QUANTIZATION`;
- `MODEL_WINDOW` obeys Seedance adapter;
- `SEEDANCE_PROMPT_STRUCTURE` passes;
- `SUMMARY_COLLAPSE` is absent;
- `GLOBAL_PROMPT_POLLUTION` is absent;
- `REFERENCE_BINDING_FAILURE` is absent.

Invalid boilerplate examples that must be replaced by shot-specific facts:
- `当前动作中只锁定与功能直接相关的视线、停顿、手部状态或许可变化`;
- `按资产库与连续性锁执行`;
- bare `保持克制` without observable eyes/breath/jaw/gaze/body behavior.
