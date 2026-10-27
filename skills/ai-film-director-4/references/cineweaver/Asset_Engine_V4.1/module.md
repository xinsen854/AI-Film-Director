---
name: asset-engine
version: "4.1"
description: >
  Unified film asset extraction and maintenance engine. Produces one authoritative
  ASSET_LIBRARY.md containing reusable visual identities, persistent states,
  locations, props, creatures/crowds, image prompts, separate V-series text Voice Assets, and downstream
  reference metadata for SHOT / SEGMENT Engine.
---

# Asset Engine V4.1｜Text Voice Asset Edition

## Role

Read approved project / screenplay facts and maintain **one authoritative `ASSET_LIBRARY.md`**.

Asset Engine creates only reusable production facts:
- A / B character visual identity;
- V-series text-only Voice Asset linked from each speaking character;
- persistent visual state lineage;
- S location identity + stable geography;
- P key props;
- G creatures / entities / crowds / extra groups;
- image-generation prompts and reference metadata.

It does **not** design SHOTs, coverage, camera, current-shot blocking, current-shot micro-expression, Timing, or final video prompts.

## Character prompt execution contract

人物视觉资产在进入 `IMAGE PROMPT POLICY` 前必须读取并服从 `references/contracts/asset-prompt-contract.md`。该合同是人物基础资产板的执行权威：大型3/4面部身份近景、正面颈部以下至脚部且故意不显示头部、背面完整身体参考、中性灰背景与平坦照明。Asset Engine 不得用自身概括替代或弱化该合同。

## Core Principle

# Asset only what must stay stable or be reused.

Do not create an asset merely because a single SHOT could mention it.

## Canonical Asset Families

- `A` — core character
- `B` — recurring secondary character
- `G` — creature / entity / crowd / extra group
- `S` — location
- `P` — key prop
- `STATE` — persistent state inheriting a master asset
- `V001...` — text-only stable voice identity

V-series is a separate numbered **TEXT_VOICE_ASSET** family. It never carries an image/audio/video file and never consumes Seedance reference slots.

## Pipeline

```text
PROJECT CREATIVE BIBLE
+ LOCKED / INTEGRATED SCREENPLAY
+ EXISTING ASSET_LIBRARY (if any)
↓
ASSET NECESSITY GATE
↓
IDENTITY / STATE / LOCATION / PROP / CROWD EXTRACTION
↓
V-SERIES TEXT VOICE ASSET
↓
IMAGE PROMPT POLICY
↓
REFERENCE / BUDGET METADATA
↓
ONE ASSET_LIBRARY.md
```

## V-series Voice Asset

Voice assets are separate from visual media:
- IDs use `V001`, `V002`...;
- linked from the character through `voice_asset_id`;
- `asset_class: TEXT_VOICE_ASSET`;
- `media_asset: false`;
- `visual_cost_units: 0`;
- `seedance_reference_slot_cost: 0`;
- no image file, no audio file, no video file;
- current version never compiles V-series into `@图片`, `@视频`, or `@音频`;
- stable voice identity is injected as text inside final Prompt【声音】.

Voice text may describe timbre, pitch tendency, texture, resonance, vocal weight, pace, rhythm, breath, articulation, speech habits, emotional leakage, pressure behavior and evidence-backed accent quality. Specific regional accent/dialect still requires evidence.

## Persistent State

Persistent state follows:

`MASTER → STATE`

Create STATE only when a visible condition persists or is repeatedly reused.

Do not assetize:
- single-shot expression;
- temporary pose;
- one breath change;
- current Beat reaction;
- one-line emotional delivery.

## Budget Metadata

Visual assets normally expose:
- `visual_cost_units: 1`
- `default_reference_role`
- `generic_eligible`

V-series Voice Asset exposes:
- `asset_class: TEXT_VOICE_ASSET`
- `media_asset: false`
- `visual_cost_units: 0`
- `seedance_reference_slot_cost: 0`

`generic_eligible` is a downstream budget role, **not a new asset family**.

## Project Style

Asset image prompts inherit project-approved style. Legacy colored-pencil face treatment is conditional only when the project explicitly requires it; Asset Engine must not impose it globally.

## Output

Exactly one user-facing production asset file:

`ASSET_LIBRARY.md`
