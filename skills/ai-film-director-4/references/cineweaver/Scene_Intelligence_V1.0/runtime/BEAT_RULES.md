# Scene Intelligence V1.0 — Beat Rules

A Beat is the smallest meaningful unit in which the active dramatic state remains coherent.

## Create a new Beat only when at least one meaningful change occurs

1. **new information** enters the scene
2. an **objective** changes
3. a **tactic failure** occurs
4. a tactic changes
5. **power** or status changes
6. the **relationship** changes
7. a character makes a **decision**
8. the emotional mechanism changes
9. **audience** knowledge, expectation, or misbelief changes
10. action crosses an **irreversible** threshold

## Do not split mechanically

DO NOT:
- create one Beat per dialogue line,
- split line-by-line,
- force a fixed Beat count,
- split on every pause,
- split on every physical action,
- split merely because a new sentence begins.

A pause becomes a Beat boundary only when it marks a meaningful internal or relational change.

## Beat output structure

Each Beat should contain:

```yaml
beat_id: B01
trigger: ""
active_objective: {}
tactic: {}
change:
  type: ""
  description: ""
relationship_effect: null
power_effect: null
information_effect: null
emotional_effect: null
confidence: 0.0
```

## Beat trigger precedence

Prefer the smallest decisive trigger.

Example:
- a character hears new information,
- that information causes a tactic change,
- which produces a power shift.

Do not create three Beats if all three are one continuous dramatic turn.
Create one Beat with the primary trigger and record the downstream effects.

## Beat continuity

A Beat should describe the scene state until the next meaningful change.

If nothing changes, do not manufacture a Beat boundary.

## Irreversible action

An irreversible threshold means the scene cannot simply return to its prior state without consequence.

Examples:
- a secret is spoken,
- a person leaves,
- a weapon is fired,
- a contract is signed,
- help is finally accepted,
- a relationship boundary is crossed.

This is a dramatic criterion, not a camera-cut criterion.
