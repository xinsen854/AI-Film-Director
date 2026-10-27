# Routing Pipeline

```text
VALIDATE INPUT
↓
EXTRACT SIGNALS
↓
BUILD CANDIDATE CAPABILITIES
↓
NECESSITY TEST
↓
DEDUPLICATE
↓
SUPPRESS
↓
PRIORITIZE
↓
HARD / SOFT / FREE
↓
CONFLICT CHECK
↓
DOWNSTREAM ROUTING
↓
ROUTER_RESULT
```

## Input validation
Primary input is `SCENE_INTELLIGENCE_RESULT`.
Do not reopen the screenplay and perform a second scene interpretation pass.

## Candidate generation
Signal-to-capability mapping is guidance, not a mandatory rule table.

## Necessity and suppression
Every candidate must either become ACTIVE with a reason or SUPPRESSED with a reason.

## Output
One Router result only. No shot list, storyboard, camera plan, or final prompt.
