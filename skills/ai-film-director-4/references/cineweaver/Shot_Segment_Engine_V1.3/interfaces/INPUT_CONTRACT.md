# INPUT CONTRACT

Required upstream evidence may come from:
- locked screenplay,
- Scene Intelligence,
- Capability Router,
- Director Craft Engine,
- asset registry / V-series text Voice Assets,
- optional Spatial Narrative current-shot handoff,
- continuity state,
- `generation_packing_policy: 15S | 30S_BLOCK | AUTO`;
- target model call window/capability.

Priority:
1. user/project hard constraints,
2. locked story/dialogue facts,
3. continuity facts,
4. Director Craft audience-readable intent,
5. generation capacity/risk.

Do not invent unsupported story facts merely to make a shot prettier.


## Spatial Narrative Priority
When an ACTIVE `SPATIAL_NARRATIVE_RESULT` exists, consume only the current-shot handoff. Treat locked route result, reveal stage, must-remain-hidden, landmark requirement and audience/character visibility relation as upstream facts. Camera/composition remain SHOT Engine decisions.


## Scene GEO Lock input

当 ACTIVE `SPATIAL_NARRATIVE_RESULT` 含 meaningful stable topology 时，读取其 `scene_geo_lock`，并在当前 scene 的每个 SH `spatial_blocking` 中保留同一个 `scene_geo_lock_ref + scene_geo_sha256`。SHOT Engine 只能在该几何内设计当前机位/人物站位，不得改写锁定场景几何；同时 GEO Lock 不获得当前机位和人物 blocking 的权威。
