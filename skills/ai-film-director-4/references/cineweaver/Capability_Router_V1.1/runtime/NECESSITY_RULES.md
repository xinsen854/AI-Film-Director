# Capability Router V1.1 — Necessity Rules

Every candidate capability must pass all six questions.

1. **Scene Signal** — Is the source signal actually present in `SCENE_INTELLIGENCE_RESULT`?
2. **Scene success** — Would losing this capability materially weaken or break scene success?
3. **Dedicated capability** — Does the problem require a dedicated capability, or can existing scene intelligence pass through without special handling?
4. **already covered** — Is another active capability already covering the same function?
5. **Control burden** — Would activation add unnecessary control burden or reduce useful creative freedom?
6. **Downstream** — Does at least one downstream system explicitly consume the capability?

If any essential step fails, prefer SUPPRESSED.

## Evidence basis
Use:
- Scene Intelligence fields
- confidence
- ambiguities
- project hard rules

Do not reopen the screenplay and perform a second interpretation pass.

## Coverage rule
When two capabilities solve substantially the same problem:
- retain the narrower or more scene-relevant one,
- suppress the redundant one,
- record `Already Covered` as reason.

## Necessity result
An ACTIVE capability must record:
- trigger,
- necessity reason,
- whether another capability covers part of its function,
- evidence confidence,
- downstream consumers.
