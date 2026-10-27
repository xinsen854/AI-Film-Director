# Forge Emotion Compatibility Projection Contract

## Authority

- Emotion truth: `state/forge_locked_audit.json`
- Formal HTML: Forge Renderer `scripts/render_emotion_map.py`
- Compatibility projection: `state/audience_emotion_architecture.json`

`state/audience_emotion_architecture.json` is **COMPATIBILITY_PROJECTION_ONLY**. It exists only for downstream AFD modules that still require compact emotion hints. It MUST NOT be used to render formal delivery 05 and MUST NOT compete with Forge AUDIT.

## Required provenance

The compatibility payload must be authored under:

`state/forge_locked_audit.json -> integration.afd.audience_emotion_compat_projection`

and copied deterministically by `compile_forge_handoff.py`.

No AFD module may invent additional emotional semantics, phase boundaries or audience states here.
