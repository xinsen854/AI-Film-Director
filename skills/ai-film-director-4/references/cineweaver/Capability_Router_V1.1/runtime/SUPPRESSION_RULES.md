# Capability Router V1.1 — Suppression Rules

Suppression is a first-class routing output.

## No Signal
Scene Intelligence contains no meaningful signal for this capability.

## Signal Too Weak
The only supporting interpretation is below 0.55 confidence and there is no independent hard project rule.

## Already Covered
Another selected capability already covers the necessary function with less control burden.

## No Downstream Use
No Asset Engine, Performance Engine, Director Craft, or CineKernel consumer needs the capability.

## Over-control Risk
Activating the capability would constrain a variable that should remain free.

## Scene Simplicity
The scene succeeds without a dedicated capability.

## Suppression is not deletion
A suppressed capability may become relevant in another scene or later version.
It remains in the registry but is intentionally inactive here.

## Output
Each suppressed item should contain:

```yaml
- capability: PHYSICAL_CAUSALITY
  reason_code: No Signal
  reason: "No consequential physical chain in this scene."
```
