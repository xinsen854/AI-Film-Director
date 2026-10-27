# OUTPUT CONTRACT

Output exactly **one authoritative `ASSET_LIBRARY.md`** for the project.

It may contain:
- quick index;
- A / B character visual identity + `voice_asset_id` link;
- V001... text-only voice assets (`TEXT_VOICE_ASSET`, zero media slots);
- persistent states;
- S locations;
- P key props;
- G creatures / entities / crowds;
- image prompts;
- downstream reference / cost metadata;
- final asset QC.

Do not output a second parallel asset library.
Do not output SHOT design, camera design, Timing, current-shot performance, or any downstream model-execution prompt.

Optional supporting media may include `downstream_metadata.scale_reference` on an existing visual master asset. It is rendered inside the same authoritative ASSET_LIBRARY and indexed with a `SCALE-...` reference ID; it is not a second asset family or parallel registry.
