# Scene Intelligence Input Contract

Primary input: `SCENE_INTELLIGENCE_RESULT`.

Capability Router **does not rewrite** Scene Intelligence and does not reopen the screenplay for a second scene-analysis pass.

Router may:
- validate fields,
- read confidence and ambiguities,
- extract routing signals,
- combine signals with locked project hard rules.

Router may not:
- replace the scene core,
- invent new psychology,
- alter Beat Map,
- silently resolve an ambiguity that Scene Intelligence left open.

Optional `PROJECT_CONTEXT` may supply genre/tone/continuity/locked story rules, but it cannot override the scene diagnosis without an explicit project-level hard rule.
