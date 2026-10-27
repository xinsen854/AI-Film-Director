---
name: spatial-narrative-engine
version: "1.0"
description: >
  Conditional spatial storytelling planner for CineWeaver. Builds scene topology,
  routes, visibility/hearing relations, landmark memory, threat geography and
  reveal/foreshadow progression before SHOT design.
---

# Spatial Narrative Engine V1.0｜空间叙事引擎

## Role

Turn already-approved scene meaning, reusable assets and space facts into a **spatial narrative plan** that SHOT / SEGMENT Engine can execute.

It answers:
- where important characters / objects / landmarks are in the scene topology;
- how routes evolve across Beats;
- who can see or hear whom;
- what is occluded and by what;
- when an existing entity should remain latent, become readable, be emphasized, or pay off;
- how landmarks and motifs support spatial memory and narrative progression.

## Default State

Spatial Narrative Engine is **SUPPRESSED by default**.

Activate only when spatial planning or reveal progression materially affects:
- plot causality;
- audience information;
- character information;
- continuity;
- chase / escape / search / infiltration / ambush logic;
- complex multi-zone blocking;
- delayed reveal / foreshadow payoff / motif progression.

Ordinary static dialogue does not activate this engine.

## Inputs

- locked screenplay / integrated director facts;
- Scene Intelligence result;
- Capability Router result;
- Director Craft result;
- ASSET_LIBRARY.md, especially S-location geography, landmarks, P/G/A/B identities and persistent states;
- continuity state.

## Outputs

When ACTIVE:
- `SPATIAL_NARRATIVE_RESULT` internal structured handoff;
- conditional authority file `SPATIAL_NARRATIVE_PLAN.md`.

When SUPPRESSED:
- no empty plan file;
- only an internal suppression reason may be recorded.

## Hard Boundary

Spatial Narrative Engine:
- **does not create assets**;
- does not rewrite story, Beat, dialogue or Director Craft intent;
- does not decide final SHOT count;
- does not choose final lens / camera / composition;
- **does not generate final video prompt**;
- does not invent symbolic meaning unsupported by upstream story/director facts.

## Core Modules

1. Activation Policy
2. Space Topology
3. Route Planning
4. Visibility / Hearing
5. Landmark Memory / Threat Geography
6. Reveal Ledger
7. Motif Progression
8. Current-shot Handoff

## Topology First, Coordinates Only When Needed

Default to zones, adjacency, route, visibility, occlusion and relative depth.
Do not require metric 3D coordinates unless plot execution actually depends on distance, height or precise path geometry.

## Reveal Stages

Use only:
- OFFSCREEN
- LATENT
- PARTIAL
- READABLE
- EMPHASIZED
- PAYOFF

An entity can exist in the story world while remaining OFFSCREEN, LATENT or PARTIAL.
Do not force every entity through every stage.

## Current-shot Isolation

SHOT / SEGMENT Engine must receive only a **current-shot handoff**, never the full topology/reveal ledger inside a Seedance Prompt.


## Scene GEO Lock

对具有真实稳定空间拓扑的 ACTIVE 场景，Spatial Narrative 必须先从当前 S 场景资产生成 `AFD_SCENE_GEO_LOCK_V1`，再进行 route/reveal/visibility 设计。锁只包含场景稳定几何，不包含人物或机位。若 ASSET_LIBRARY 的稳定几何改变，旧 `geo_sha256` 立即失效，必须重新生成空间计划；简单或 SUPPRESSED 场景不强制启用。
