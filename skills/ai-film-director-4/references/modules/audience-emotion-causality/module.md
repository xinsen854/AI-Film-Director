# Audience Emotion Causality Handoff Projection

`HANDOFF_PROJECTION_ONLY`

## 职责

本模块不再独立推导观众情绪因果。Forge AUDIT 在理解锁稿时直接生成逐场 AFD handoff，桥接器只落盘到：

`state/audience_causal/<unit>_<scene>.json`

每场至少包含：

```text
scene_id
story_atom_refs
information_refs
must_be_perceptible
must_remain_implicit
must_not_be_revealed
key_reaction_requests
key_listener_or_third_party_response
environmental_pressure_or_release
important_object_or_space_evidence
emotion_capacity_note
```

Scene Direction 只消费这些交接和 Story Authority，不得在此重新发明剧情事实、Reveal 或第二情绪分析。
