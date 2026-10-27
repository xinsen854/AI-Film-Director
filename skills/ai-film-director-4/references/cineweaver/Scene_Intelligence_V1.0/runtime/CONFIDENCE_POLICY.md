# Scene Intelligence V1.0 — Confidence & Ambiguity Policy

Scene Intelligence must distinguish evidence from interpretation.

## Confidence scale

### 0.90–1.00
Directly stated or supported by multiple independent textual/behavioral signals.

Safe to use as a strong Scene Intelligence conclusion.

### 0.75–0.89
Strong inference with substantial support.

Useful for downstream routing, but still recognized as inference.

### 0.55–0.74
Plausible interpretation with meaningful competing explanations.

Do not silently promote to fact.
Preserve the competing interpretation in `ambiguities`.

### Below 0.55
Too unstable to use as a routing fact.

Keep as ambiguity or omit.

---

# Evidence Types

## EXPLICIT
The text directly states the fact.

Example:
A character says, "I decided last month."

## BEHAVIORAL
Actions or reactions strongly support the inference.

Example:
A father repeatedly refuses help, then finally allows his son to take over a task.

## STRUCTURAL
Meaning is supported by the scene's position, setup/payoff, repeated motif, or before/after contrast.

## INFERRED
A reasonable dramatic interpretation not directly stated.

INFERRED evidence must never be presented as EXPLICIT.

---

# Ambiguity Policy

Use `ambiguities` whenever more than one interpretation remains credible.

```yaml
ambiguities:
  - issue: "primary motive for refusing help"
    candidates:
      - interpretation: "fear of dependency"
        confidence: 0.86
      - interpretation: "fear of illness itself"
        confidence: 0.48
```

Rules:
- Do not force a unique answer merely to complete the schema.
- Do not invent unseen history to resolve ambiguity.
- Do not use a candidate below 0.55 as a stable routing fact.
- When two candidates are both >= 0.55, keep both.
- When later scene evidence resolves the ambiguity, update the result rather than pretending the earlier uncertainty never existed.

---

# Overall confidence

`confidence_overall` reflects confidence in the scene-level diagnosis as a whole.

It is not the average of every numeric field.

Lower it when:
- the scene is fragmentary,
- context is missing,
- several central motives remain ambiguous,
- character identity or chronology is unclear.

High confidence does not mean all subfields are equally certain.
