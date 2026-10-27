# Downstream Handoff Contract

Every ACTIVE capability must have at least one named consumer.

Canonical consumer IDs:
- `asset_engine`
- `performance_engine`
- `director_craft_engine`
- `cinekernel`

Examples:
- SUBTEXT → performance_engine + director_craft_engine
- LISTENING_REACTION → performance_engine + director_craft_engine
- REACTION → director_craft_engine
- POWER_SHIFT → director_craft_engine
- INFORMATION → director_craft_engine
- RHYTHM → director_craft_engine
- SPACE → director_craft_engine
- ACTION → director_craft_engine and, when technical execution risk exists, cinekernel
- PHYSICAL_CAUSALITY → cinekernel
- ACTION_TIMING → cinekernel
- VISUAL_STATE_ASSET → asset_engine
- REFERENCE_ROLE_BINDING → asset_engine + cinekernel

If a capability has no explicit consumer, suppress it as `No Downstream Use`.

The handoff contains generic capabilities and control metadata only.
It does not contain scene-type directing methods, shot lists, storyboard design, camera plans, or final prompts.
