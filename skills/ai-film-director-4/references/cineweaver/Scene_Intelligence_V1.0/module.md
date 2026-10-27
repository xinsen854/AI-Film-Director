---
name: scene-intelligence
description: >
  Scene Intelligence V1.0 — understand what a dramatic scene actually is before
  capability routing or shot design. Produces Scene Diagnosis + Beat Map +
  generation risk + confidence/ambiguities, and hands the result to Capability Router.
version: "1.0"
status: "runtime"
---

# Scene Intelligence V1.0 — Runtime

## Role

Understand the current scene before directing it.

Produce:
1. **Scene Diagnosis**
2. **Beat Map**
3. **Generation Risk Profile**
4. **confidence**
5. **ambiguities**

Then hand off one structured result to **Capability Router**.

Do not design shots.

---

# Runtime Pipeline

1. Parse only the current scene or scene-like unit.
2. Produce the approved 10-dimension Scene Diagnosis.
3. Detect meaningful Beat Map changes.
4. Build a generation risk profile.
5. Attach confidence to high-level inference.
6. Preserve competing interpretations in ambiguities.
7. Deliver `SCENE_INTELLIGENCE_RESULT` to Capability Router.

---

# Prime Rules

## Evidence before inference
Use explicit text, behavior, scene structure, and only then inference.

## Low confidence is not routing fact
If an interpretation is weak or has a credible competitor, keep it in ambiguities rather than presenting it as certain.

## Beat is change-driven
A Beat requires meaningful change in information, objective, tactic, power, relationship, decision, emotional mechanism, audience cognition, or irreversible action state.

Do not split Beat Map line-by-line by dialogue.

## Risk identification is not constraint creation
Scene Intelligence may say:
- performance risk = high
- spatial risk = medium

It must not itself activate locks or prescribe generation constraints.

## Scene Intelligence never designs shots
The following are explicitly outside this layer:
- focal length
- FOV
- camera position
- composition
- lighting plan
- shot count
- shot/reverse-shot plan
- final video prompt
- model parameter
- fixed style reference

Do not say:
- use 85mm
- use 35mm
- slow push-in
- hard cut to
- camera should...

Those belong downstream.

---

# Level 1 — Scene Diagnosis

Always diagnose exactly these ten dimensions:

1. DRAMATIC_FUNCTION
2. INTERACTION_FORM
3. CHARACTER_OBJECTIVES
4. EMOTIONAL_MECHANISM
5. RELATIONSHIP_DYNAMIC
6. POWER_STATUS_DYNAMIC
7. SUBTEXT_HIDDEN_TRUTH
8. INFORMATION_STATE
9. SPACE_FUNCTION
10. ENERGY_PROFILE

Use `runtime/DIAGNOSIS_RULES.md` when detailed interpretation rules are needed.

---

# Level 2 — Beat Map

Use `runtime/BEAT_RULES.md` when the scene contains more than a trivial single beat or when Beat boundaries are ambiguous.

Beat count is not fixed.

---

# Confidence / Ambiguity

Use `runtime/CONFIDENCE_POLICY.md` when:
- hidden motive is inferred,
- multiple interpretations are plausible,
- audience knowledge differs from character knowledge,
- relationship or power dynamics are not explicit.

---

# Selective Loading

HOT:
- this `SKILL.md`

WARM:
- `runtime/DIAGNOSIS_RULES.md`
- `runtime/BEAT_RULES.md`
- `runtime/CONFIDENCE_POLICY.md`
- `runtime/BOUNDARY_RULES.md`
- `schema/SCENE_INTELLIGENCE_RESULT.yaml`
- `schema/ENUM_GUIDANCE.yaml`
- `interfaces/ROUTER_HANDOFF.md`
- `interfaces/CINEKERNEL_BOUNDARY.md`

COLD:
- tests
- documentation

Do not load all support files by default.

---

# Output

Return one `SCENE_INTELLIGENCE_RESULT`.

The output describes:
- what the scene is,
- what changes inside it,
- what is uncertain,
- what is likely to fail during generation.

It does not prescribe how to shoot it.
