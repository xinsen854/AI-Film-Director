# Positioning Among Open AI Filmmaking Projects

[Home](../README.md) · [Chinese edition](COMPARISON.zh-CN.md)

The projects below do not all optimize for the same problem. This document distinguishes documented architecture from experimentally measured performance. **It is not a quality ranking.**

| Project | Documented emphasis | Relationship to AFD |
|---|---|---|
| [CineCrew](https://github.com/Ironieser/CineCrew) | FilmDSL, multi-agent script-to-video orchestration, reference assets, visual critique and repair | Shared interest in constraints and continuity; AFD gives more explicit authority to story/emotion audit and screenplay locking. |
| [OpenMontage](https://github.com/jedybrilliant/openmontage) | Agentic media acquisition, generation, editing, composition and a live production board | Stronger emphasis on **executing** media production; AFD is a pre-production decision and evidence layer. |
| [StoryMind](https://github.com/LinHao-city/StoryMind) | Shot planning, provider-backed clips and automated assembly | Targets the storyboard-to-video path; AFD emphasizes emotion, behavior and authority contracts before that path. |
| [Continuity Studio](https://github.com/momorzq-oss/Continuity-Studio) | Local-first workspace for identity, props, locations, state, review and prompts | Potentially complementary production interface; AFD emphasizes the upstream narrative and emotional cause of film decisions. |
| [OpenFilm](https://github.com/openfilm/openfilm) | Editable web-native scenes, timeline, footage, titles and rendering | Video production/animation medium, not a replacement for an emotional story audit. |

## What we think is worth evaluating

The AFD hypothesis is that preserving a consistent causal account of **character disposition → event → affect → choice → performance → audience inference** improves the quality and revisability of downstream directing decisions. That is a hypothesis to test, not a verified benchmark result.

An honest future comparison would provide each system with the **same screenplay**, assets, model constraints, budget and runtime, then independently score:

1. Preservation of story facts and reveal order.
2. Plausibility and specificity of character emotional transitions.
3. Whether behavior and performance are causally motivated, rather than labeled.
4. Audiences' comprehension and emotional response, measured by independent raters.
5. Cross-shot character, space and prop continuity.
6. Rework cost and proportion of deliverables that can be executed by real media tools.

No such controlled evaluation is claimed for this release.

## Current boundary

AFD does **not** currently replace the media generation, TTS, compositing or editing backends supplied by the other projects. Its strength should be judged in the **design and evidence layer**, not by pretending to ship a finished video renderer.
