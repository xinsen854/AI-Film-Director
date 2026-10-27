# SHOT HANDOFF

Spatial Narrative outputs a **current-shot handoff**. SHOT / SEGMENT Engine must not load the entire spatial plan into one video Prompt.

```yaml
shot_handoff:
  shot_id:
  current_zone:
  route_phase:
  must_be_visible: []
  may_be_latent: []
  must_remain_hidden: []
  occlusion_logic: []
  visibility_relations: []
  landmark_requirement: []
  threat_state: []
  reveal_stage_changes: []
  spatial_continuity_must_preserve: []
```

## Authority
SHOT Engine may choose camera / composition / blocking that satisfies the handoff.
It may not change:
- locked route result;
- must-remain-hidden fact;
- reveal stage;
- required landmark presence;
- audience/character visibility relation.

This is **current-shot handoff** only.
