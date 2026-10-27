# SPATIAL NARRATIVE QC

Run only for scenes where Spatial Narrative Engine is ACTIVE.

Check hard spatial/narrative facts:
- route does not jump between non-adjacent zones without a valid transition;
- must-remain-hidden entity is not made READABLE/EMPHASIZED/PAYOFF early;
- PAYOFF that requires prior presence has prior OFFSCREEN/LATENT/PARTIAL/READABLE existence evidence;
- audience/character visibility relations do not contradict the SHOT;
- required landmark is available/visible when it carries orientation or payoff;
- SHOT does not change a locked reveal stage;
- spatial plan does not contradict ASSET_LIBRARY stable geography;
- when `scene_geo_lock` exists, perform a semantic consistency check: every topology statement and SH spatial-blocking statement must remain compatible with `scene_geo_lock.locked_geometry`. The `geo_sha256` / Hash check proves that every shot points to the same authoritative geometry snapshot; it does **not** prove that free-form spatial prose is semantically true, so this QC pass must catch semantic contradictions.

This GEO semantic check protects only stable scene geography. It must not freeze shot-level character positions, legal axis transitions, camera side, shot size, or camera aesthetics. Do not judge whether a different camera angle would be more cinematic.
