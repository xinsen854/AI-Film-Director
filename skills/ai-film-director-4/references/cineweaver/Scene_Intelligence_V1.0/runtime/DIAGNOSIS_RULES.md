# Scene Intelligence V1.0 — Diagnosis Rules

The Scene Diagnosis layer answers **what the scene is**, not how to shoot it.

Every diagnosis uses exactly ten dimensions. Labels are aids, not a closed taxonomy.

---

## SI-01 DRAMATIC_FUNCTION

**Question:** Why does this scene exist in the story?

Identify one primary function and optional secondary functions.

Typical guidance:
- establish
- setup
- reveal
- confrontation
- decision
- reversal
- escalation
- aftermath
- relationship_shift
- emotional_payoff
- information_delivery
- character_exposure
- moral_choice
- separation
- reunion
- commitment
- failure
- sacrifice
- transition

**Evidence allowed:** explicit story event, scene outcome, structural relation to adjacent scenes.

**Invalid overreach:** naming a theme without identifying what changes in the scene.

---

## SI-02 INTERACTION_FORM

**Question:** What is the observable interaction form?

Guidance:
- solo
- two_person_dialogue
- multi_person_dialogue
- ensemble
- confrontation
- negotiation
- observation
- pursuit
- fight
- chase
- ritual
- discovery
- waiting
- caregiving
- parallel_action
- silent_interaction
- montage
- transition
- physical_action

Interaction form is descriptive only. `two_person_dialogue` does not imply shot/reverse-shot.

---

## SI-03 CHARACTER_OBJECTIVES

For each core character identify:
- immediate_objective
- obstacle
- stakes
- hidden_need only when evidence is sufficient
- confidence

Objective must be actionable inside the current scene.

Bad:
- "wants happiness"
- "wants love in life"

Good:
- "wants father to accept the hospital appointment"
- "wants to finish removing the shop sign without help"

If uncertain, mark uncertain rather than inventing motive.

---

## SI-04 EMOTIONAL_MECHANISM

**Question:** By what causal mechanism is emotion generated?

Prefer a causal chain:

```text
trigger
→ internal conflict
→ pressure
→ visible or hidden response
```

A simple emotion word is insufficient when the scene supports a deeper mechanism.

Guidance labels may include:
- restrained_grief
- shame
- emotional_avoidance
- fear_of_dependency
- unresolved_wound
- longing
- betrayal
- guilt
- jealousy
- humiliation
- protective_love
- helplessness
- suppressed_anger
- relief_after_tension
- dread
- anticipation
- absurdity
- comedic_escalation

Custom labels are allowed.

---

## SI-05 RELATIONSHIP_DYNAMIC

**Question:** What is the relationship state at the start and end?

Output:
- start
- end
- delta
- confidence

Only describe change supported by this scene.

A relationship can remain stable. Do not fabricate a shift merely to fill the field.

---

## SI-06 POWER_STATUS_DYNAMIC

Track practical control, not abstract social rank.

Inspect:
- who controls the space,
- who controls the topic,
- who controls the decision,
- who yields,
- who initiates action,
- whether control shifts.

Output:
- start_controller
- shift_points
- end_controller
- direction
- confidence

Do not infer "quiet = powerful" or "loud = weak" as universal truth.

---

## SI-07 SUBTEXT_HIDDEN_TRUTH

**Question:** What is being said on the surface, and what is actually being negotiated, feared, protected, or needed?

Output:
- explicit_layer
- hidden_layer
- confidence

Use only:
- dialogue evidence,
- behavior,
- repeated avoidance,
- scene structure,
- prior established context.

Do not invent childhood trauma, offscreen history, or diagnosis not present in evidence.

If multiple interpretations survive, move them to `ambiguities`.

---

## SI-08 INFORMATION_STATE

Track:
- what each key character knows,
- what the audience knows,
- what the audience expects or mistakenly believes,
- what is revealed in the scene.

Do not force an `audience_misbelief` when none exists.

Information state may change per Beat.

---

## SI-09 SPACE_FUNCTION

**Question:** Is the location merely background, or does it participate in the drama?

Guidance:
- neutral_background
- identity_extension
- power_structure
- memory_container
- emotional_pressure
- obstacle
- concealment
- separation
- intimacy_container
- public_pressure
- symbolic_object_system

Multiple values are allowed only when text supports them.

Do not convert space function into camera instruction.

---

## SI-10 ENERGY_PROFILE

Rate scene-level energy from 0 to 5:

- external_expression
- internal_pressure
- physical_activity
- dialogue_intensity
- reaction_importance
- volatility
- camera_intervention_need

`camera_intervention_need` is diagnostic only: it estimates whether the scene may require stronger visual intervention downstream. It does not prescribe camera behavior.

---

# Scene Core

Always produce `scene_core`.

Question:

> If only one sentence could survive, what meaningful relationship, decision, recognition, or state change actually occurs in this scene?

Rules:
- do not summarize surface plot only,
- do not write camera advice,
- do not write generic theme language,
- prioritize human change or dramatic change.
