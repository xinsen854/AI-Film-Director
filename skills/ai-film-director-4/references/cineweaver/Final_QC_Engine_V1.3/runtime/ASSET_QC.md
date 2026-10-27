# ASSET QC｜V1.5

- visual/media assets must exist and have valid roles when referenced;
- A/S/P/G visual IDs use three digits;
- persistent state uses ST three-digit form when newly created;
- V-series voice IDs use `V001...` and `asset_class: TEXT_VOICE_ASSET`;
- V-series must have `media_asset:false`, `visual_cost_units:0`, `seedance_reference_slot_cost:0`;
- `VOICE_MEDIA_LEAK` is ERROR: V-series may not own image/audio/video files, appear as @图片/@视频/@音频, or consume media-reference slots;
- specific regional accent/dialect still requires evidence.

## GENERATE mode hard gate
When `asset_image_mode=GENERATE` / **GENERATE 模式**:
- every REQUIRED visual asset used by the final production plan must have a real successfully generated media file;
- `PROMPT_ONLY`, `FAILED`, `MISSING`, or placeholder status is not equivalent to generated;
- actual `assets/` delivery contains only files that exist and succeeded;
- any required generated visual asset missing triggers `GENERATE_ASSET_INCOMPLETE` (ERROR/BLOCKER as appropriate) and the project cannot be declared full PASS.
