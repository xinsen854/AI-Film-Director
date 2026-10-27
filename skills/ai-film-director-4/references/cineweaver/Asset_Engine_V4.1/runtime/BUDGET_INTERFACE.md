# BUDGET INTERFACE

Asset Engine exposes reference-cost metadata to SHOT / Seedance compiler.

## Visual/media-reference asset

```yaml
visual_cost_units: 1
seedance_reference_slot_cost: 1
default_reference_role: identity / state / location / prop / crowd
generic_eligible: true / false
```

## Persistent STATE

A persistent state record consumes a media slot only when a dedicated state image/video reference is actively attached and used.

```yaml
visual_cost_units: 0_or_1
seedance_reference_slot_cost: 0_or_1
```

## V-series voice asset

```yaml
asset_family: V
asset_class: TEXT_VOICE_ASSET
media_asset: false
visual_cost_units: 0
seedance_reference_slot_cost: 0
```

V-series is text only. It does not generate or attach image/audio/video files, does not become `@音频`, and does not count toward any Seedance media-reference quantity.

## Generic slot

`generic_eligible` marks an existing visual asset as eligible for a downstream generic slot. It is not a new asset family.

The actual per-Generation-Unit media-reference limit is controlled by the active Seedance/model adapter. Voice text never consumes that limit.
