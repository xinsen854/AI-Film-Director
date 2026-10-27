# Scene Intelligence ↔ CineKernel Boundary

Scene Intelligence and CineKernel solve different problems.

## Scene Intelligence says what is true about the scene

Examples:
- performance risk = high
- spatial risk = medium
- subtext is central
- father-to-son power transfer occurs
- physics risk = low
- audience knows more than character B

## CineKernel protects execution reliability

CineKernel may later decide that a routed capability requires:
- a spatial anchor,
- current-shot isolation,
- a local identity lock,
- physical causality,
- dialogue lock,
- prompt density control,
- local repair.

## Forbidden direct leap

Scene Intelligence must not say:

```text
spatial risk = high
therefore add exact 0.3m distance lock
```

It must stop at:

```text
spatial risk = high
```

Router + CineKernel decide whether an exact distance, soft spatial guide, or no extra lock is appropriate.

Likewise, Scene Intelligence must not say:

```text
wrong-opening risk = high
therefore enable first-frame lock
```

It may only report the risk.

## No CineKernel duplication

This package does not copy:
- CineKernel capability registry,
- prompt compilation rules,
- asset engineering rules,
- low-level constraint templates.

CineKernel remains downstream and separately versioned.
