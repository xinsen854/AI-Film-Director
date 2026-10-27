# Scene Intelligence → Capability Router Handoff

## Contract

**Scene Intelligence identifies:**
- scene type and dramatic function,
- character objectives and conflicts,
- emotional mechanism,
- relationship and power changes,
- subtext,
- information state,
- space function,
- energy profile,
- Beat changes,
- generation risk levels,
- confidence and ambiguity.

**Capability Router decides:**
- which capabilities activate,
- capability priority,
- whether each active capability is HARD, SOFT, or FREE,
- which information is sent to Director Method Library,
- which information is sent to CineKernel.

## Scene Intelligence must not route capabilities

Invalid Scene Intelligence output:
- "activate SUBTEXT"
- "activate PROXEMICS"
- "use FIRST_FRAME_CONTROL"
- "use PHYSICAL_CAUSALITY"

Valid Scene Intelligence output:
- "subtext risk = high"
- "relationship shift = strong"
- "spatial risk = medium"
- "physics risk = high"

## Control-level ownership

Scene Intelligence may describe diagnostic severity.

It does not choose:
- HARD
- SOFT
- FREE

Those values are Capability Router decisions.

## Handoff object

The only handoff is the structured `SCENE_INTELLIGENCE_RESULT`.

No extra shot instructions accompany it.
