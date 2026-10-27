# FACS Precision Policy

FACS is an **optional high-precision facial-control layer** for performance moments where ordinary observable carriers are too coarse. It is **not a new Owner**, not a second performance engine, and not a required schema. Director Craft remains responsible for the Beat and its readable behavior; FACS may refine only the facial part of that already-supported behavior.

## Provenance split

Keep two claims separate:

1. **Standard FACS / Action Unit vocabulary** — Action Units are a standard facial-movement coding system. Examples used by the upstream source include `AU6` cheek raiser, `AU12` lip-corner puller, `AU4` brow lowerer, `AU1` inner-brow raiser and `AU15` lip-corner depressor.
2. **Model interpretation of AU text** — writing an AU code inside a video prompt is **EMPIRICAL** model behavior, not a documented FACS field, provider parameter, or API parameter. It is **not a guarantee** and is not deterministic.

Do not turn the empirical prompt convention into an AFD global capability claim. The active model adapter decides whether AU-code wording may be emitted.

## Activation

Use FACS only when facial precision materially carries the current Beat, for example:

- a close-up / hero performance where two similar expressions must read differently;
- suppressed, forced, mixed, or uncanny facial behavior;
- dialogue / monologue where facial changes must align with already-established performance beats;
- a known failure where ordinary named emotion or broad facial language is too ambiguous.

**Not every Shot and not every Beat needs FACS.** Medium/wide coverage, low facial readability, simple reactions, or scenes already communicated clearly through body, gaze, business, distance, sound, or timing should remain on the normal Director Craft carriers.

## Evidence boundary — refine, never invent

FACS starts from the current Director Craft Beat and its existing observable / visible carriers. It may make an established facial carrier more precise; it must not create a new emotional truth, hidden motive, relationship fact, Story Authority fact, information reveal, or character state merely because an AU combination looks useful.

If the Beat evidence supports only "suppresses a reaction", do not invent "fear" or "guilt" and reverse-engineer AUs for it. Preserve the ambiguity and use only the minimum observable facial facts actually supported.

## Two prompt styles

When the active adapter permits the heuristic, either form is valid:

- **codes-only** — compact AU cues when the model is already reading them reliably;
- **code + short anatomical description** — e.g. an AU plus the visible muscle movement, used when the code alone is being missed or when human readability matters.

Neither style is universally superior. AU codes are an optional precision signal, not the only representation of the performance.

### Adapter fallback

If the selected model surface does not explicitly allow the FACS prompt heuristic, or AU cues prove unreliable, **fallback to anatomical / observable behavior** already present in Director Craft: brow lowers, cheek tightens, lip corner pulls, eyelids tighten, jaw sets, gaze shifts, breath catches, etc. Do not drop the performance meaning just because the AU notation is unavailable.

## Plan-first sheet workflow

A FACS reference sheet is **optional**. Use it when the character's identity and the target facial states need repeatable visual reference across shots.

Plan first:

1. choose only the facial states actually required by the scene;
2. map them to the smallest useful AU set;
3. if a sheet is needed, generate a small labelled sheet for those states only;
4. verify the labels / muscle action before treating the sheet as reference truth.

Do **not** generate a full 49-AU sheet by default and cherry-pick afterward. The upstream source explicitly treats that as an anti-pattern because label quality and identity consistency degrade as the grid grows. A generated sheet is a draft until its labels are verified.

## Beat density

The upstream Seedance FACS source recommends roughly **3–4 expression states per generation** as an empirical reliability heuristic. AFD records this as a **model-specific heuristic, not a global hard gate, universal hard limit, or global blocker**. If the selected adapter, duration, or production evidence supports another density, use the verified model profile and the current scene need instead.

## Output discipline

- Prefer the smallest AU/anatomical set that makes the intended facial distinction readable.
- Do not expose an exhaustive AU inventory when one or two cues are enough.
- Do not require a character image merely to use AU text; identity reference and facial-control notation are separate concerns.
- Do not claim pixel-identical or deterministic facial execution.
- Final Prompt remains ordinary model-native natural language; FACS is a precision clause inside the performance/microreaction material, not a provider parameter block.
