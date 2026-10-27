---
name: cineweaver-final-qc
version: "1.3"
description: >
  Final production QC gate. Validates story coverage, V4.8-derived EDIT SHOT content quality,
  Seedance Generation Units, Current-GU isolation, explicit media binding, text-only V-series voice assets,
  asset generation completeness, model windows, continuity and Production Ledger consistency without re-directing.
---

# CineWeaver Final QC Engine V1.3｜Execution Quality Gate

## Role
QC validates production correctness, not artistic conformity. It may report a minimal owner-layer fix, but must not rewrite screenplay, dialogue, shot design, asset appearance, or final Prompt body.

## Hard checks
1. locked story/dialogue coverage;
2. required V4.8-derived EDIT SHOT sections **and their concrete content quality**;
3. SH/GU/PH structure and continuity;
4. Seedance Prompt fixed structure;
5. execution-fact coverage / no summary collapse;
6. `CURRENT_GU_ONLY` / no global prompt pollution;
7. explicit active-media reference roles;
8. V-series text-only voice rule;
9. GENERATE-mode required visual asset completeness;
10. active model duration window;
11. continuity / spatial narrative / Production Ledger consistency.
12. analysis-artifact isolation: non-diegetic emotion-map/diagnostic/module/renderer/delivery metadata must not appear as story content without locked-screenplay evidence.

## Prompt / shot hard failures
- `SEEDANCE_PROMPT_STRUCTURE`;
- `SUMMARY_COLLAPSE`;
- `FIELD_BOILERPLATE`;
- `GLOBAL_PROMPT_POLLUTION`;
- `REFERENCE_BINDING_FAILURE`;
- `VOICE_MEDIA_LEAK`;
- `GENERATE_ASSET_INCOMPLETE`;
- `MODEL_WINDOW`;
- locked dialogue mismatch;
- stale shorthand / internal schema leakage;
- `ANALYSIS_ARTIFACT_LEAK`: analysis/delivery metadata became SH/GU/Prompt story content without locked-screenplay evidence.

## Seedance model windows
- Seedance 2.5: GU ≤30s;
- Seedance 2.0: GU ≤15s;
- OTHER: unknown adapter limit blocks execution until supplied.

## Prompt length
No fixed character maximum or minimum. A 30s detailed prompt may exceed 5000 Chinese characters. QC judges execution-fact coverage, not raw length.

## Timing
Default PHASE-first. Dense full-second timeline is not required. Critical time anchors are allowed only when timing materially affects execution; unrelated copied time anchors are `GLOBAL_PROMPT_POLLUTION`.

## Result
- BLOCKER/ERROR => project FAIL
- WARNING/INFO only => project PASS
- no issues => PASS


## Sequence variety warning｜Monotony Audit
Whole-sequence Final QC additionally reads the explicit framing + camera-move column across SHs. If **three consecutive** SHs explicitly share the **same shot size AND the same camera move**, emit `MONOTONY_AUDIT` as a **WARNING**, not a blocker.

This warning must not invent data from free prose. If shot size or camera move is not explicitly structured, do not infer it. Repetition can be deliberate; QC reports the pattern and leaves the director free to keep it when it serves the scene. Never rewrite shot design automatically merely to satisfy variety.
