# V-SERIES VOICE TEXT / DIALOGUE

## Stable voice identity
Speaking characters may link to `V001 / V002...` from ASSET_LIBRARY.
V-series can describe: perceived age, timbre, pitch tendency, texture, resonance, vocal weight, pace, rhythm, breath pattern, articulation, diction clarity, evidence-backed accent/regional quality, speech habit, sentence shape, emotional leakage, pressure behavior, and prohibitions.

V-series is **TEXT_VOICE_ASSET**:
- no image/audio/video file;
- no `@图片/@视频/@音频`;
- zero Seedance reference-slot cost.

## Current SH/GU delivery
Current line execution may specify tone, speed shift, pause/breath, interruption, suppression, leakage point, lip-sync/verbatim requirement, stress and volume.

Stable identity and current delivery are separate. Current performance may vary without contradicting the stable V-series voice identity.

## Final GU dialogue binding
- SH locked dialogue remains the truth source for `speaker + verbatim + order`.
- GU Phase must not replace structured dialogue with a flattened string.
- When the speaking character has a linked V-series asset, the final GU dialogue entry must carry the same `voice_profile_id`, and the current GU must declare that ID in `voice_text_assets`.
- If no V-series asset exists, keep `speaker + verbatim`; do not invent one.
