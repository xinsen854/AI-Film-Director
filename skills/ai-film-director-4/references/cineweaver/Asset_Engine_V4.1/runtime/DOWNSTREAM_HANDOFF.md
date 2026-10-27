# DOWNSTREAM HANDOFF

SHOT / Seedance compiler may read:

## Visual assets
- asset_id / name / asset_family / asset_class;
- image_file / image_status;
- default_reference_role;
- visual_cost_units;
- seedance_reference_slot_cost;
- generic_eligible;
- execution_anchor_summary;
- state lineage;
- location stable geography / functional zones / landmarks;
- prop structure / scale / state / hand-contact relevance;
- creature/crowd definition and group-count range.

## Voice text assets
- `voice_asset_id` link from A/B character;
- V-series `voice_profile` text fields;
- `media_asset:false`;
- `seedance_reference_slot_cost:0`.

V-series may only be compiled as natural-language sound/voice description inside final Prompt【声音】. It must never be converted to `@图片`, `@视频`, or `@音频` in this version.

Downstream must not ask Asset Engine to pre-decide current SHOT camera, current SHOT blocking/expression/timing, or final video prompt.

## Optional supporting scale reference

若某视觉主资产存在 `downstream_metadata.scale_reference`，下游可读取：`reference_id / subject_asset_ids / relative_scale / image_file / image_status / inherits / excludes / use_scope / dependencies`。只有真实媒体已存在且当前 GU 确实需要该跨主体比例时，才把它绑定成当前媒体职责 `scale`；`PROMPT_ONLY` 不得伪造 `@图片N`。比例参考不改变 A/B/G/S/P/V 资产家族，也不获得故事、身份或场景构图权威。
