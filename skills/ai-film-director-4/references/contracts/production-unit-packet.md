# Production Unit Packet

## 目的

长项目每次只读取当前生产真正需要的事实，避免把几十集/90分钟全部塞进上下文，也避免因为上下文缩短而丢连续性。

每一集或每一个电影生产单元开始前，从磁盘生成：

`state/units/<unit>_PACKET.json`

## 必须包含的内容

### A. 当前任务

```text
unit_id
unit_type: episode / film_segment
unit_story_scope
estimated_runtime
scene_scope
current_story_node
next_mandatory_story_node
```

### B. 项目长期事实引用

```text
project_brief_ref
creative_bible_ref
audience_emotion_architecture_ref
canonical_asset_registry_ref
production_ledger_ref
```

不重复复制整份长期文件，只带当前单元需要的摘取事实。

### B2. 当前生产覆盖

```text
project_target_scope
completed_scope
coverage_percentage
next_resume_point
remaining_scope
```

Packet只带账本当前摘要，不复制整份账本。当前电影单元起点或当前集号必须与 `PRODUCTION_LEDGER.json.next_resume` 一致。

### C. 上一单元继承

```text
previous_unit_id
previous_tail_state_ref
last_completed_event
character_positions_or_scene_exit_state
active_character_states
active_location_states
active_prop_states
relationship_state
character_arc_state
```

### D. 当前人物

对当前会出现的重要人物，只带：

```text
character_id
current_goal
current_tactic_or_defense
current_arc_state
relationship_to_other_active_characters
current_knowledge
current_misunderstanding
physical_state
wardrobe_state
injury_or_ability_effect
```

### E. 信息权限

```text
viewer_knows
viewer_believes
viewer_suspects
viewer_misbeliefs
viewer_hopes
viewer_fears
facts_allowed_to_reveal
facts_only_allowed_as_clues
facts_forbidden_to_reveal
unresolved_foreshadowing_relevant_to_this_unit
```

### F. 情绪位置

```text
macro_emotion_phase
unit_entry_viewer_state
unit_target_peak
unit_exit_viewer_state
fatigue_risk
recovery_or_contrast_plan
next_emotion_phase
```

### G. 当前空间与资产

只带当前可能使用的：

```text
active_locations
location_geometry_refs
active_character_asset_refs
active_prop_asset_refs
available_reference_images
persistent_state_dependencies
```

### H. 生产Profile

```text
aspect_ratio
generation_unit_seconds
reference_upload_cap
supports_multishot
supports_image_reference
supports_video_reference
supports_native_audio
model_max_duration_seconds
model_execution_prompt_max_chars
asset_mode
```

## 生成原则

1. 权威长期事实只引用，不在Packet里重新解释一套。
2. 只带当前生产单元有用的信息。
3. 任何与长期权威文件冲突的Packet内容都应修Packet，而不是让下游“折中”。
4. 完成当前单元后写Tail State；下一单元Packet从Tail State开始继承。
5. Packet不是给用户看的剧情总结，而是生产上下文。
6. 当前单元完成后，先写Tail State，再立即Checkpoint生产账本；下一次Packet从账本下一未完成位置开始，不能重新读取已完成单元作为待生产任务。
