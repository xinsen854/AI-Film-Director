# SPACE TOPOLOGY

## Purpose
Represent the **narratively useful topology** of a location.

Prefer:
- zones;
- adjacency;
- entrances / exits;
- vertical relationships;
- bottlenecks;
- occluders;
- landmark anchors;
- visibility / hearing edges.

Do not convert every scene into a metric 3D simulation.

## Zone record
```yaml
zone_id:
name:
narrative_function:
adjacent_to: []
access_state:
vertical_relation:
major_occluders: []
landmarks: []
```

## Stable geography authority
Scene geometry must come from ASSET_LIBRARY location facts.
Spatial Narrative may select and use geography; it may not silently redraw the location.


## Scene GEO Lock

当 Spatial Narrative 为 `ACTIVE` 且确实建立了稳定空间拓扑时，先从 ASSET_LIBRARY 的当前 S 场景资产生成 `scene_geo_lock`。锁定内容只包括：`stable_geography / functional_zones / landmark_anchors / entrances_exits`。`locked_geometry` 必须是这些字段的原样 Canonical Snapshot，并由 `geo_sha256` 绑定。

Scene GEO 是**纯场景几何**：不得包含人物、人物路线、当前姿势、当前镜头站位、表演、当前机位、`camera_side` 或镜头构图。它不锁定机位，也不禁止合法越轴；这些仍由 SHOT 的 `axis_and_gaze / spatial_blocking` 和既有越轴规则负责。

同一 scene 的每个 SH 只携带 `scene_geo_lock_ref + scene_geo_sha256`，不需要复制一整份地图。这样保证所有镜头引用同一个场景几何权威，同时避免把 Hell Grind 的“每镜重复 GEO 文本”机械照搬成 Prompt 膨胀。

生成锁：

```bash
python scripts/scene_geo_lock.py --asset-library assets/ASSET_LIBRARY.json --scene-id SC01 --location-asset-id S001
```

若场景没有 meaningful spatial topology、Spatial Narrative 被 SUPPRESSED，或只是简单单镜空间，不强制生成 GEO Lock。
