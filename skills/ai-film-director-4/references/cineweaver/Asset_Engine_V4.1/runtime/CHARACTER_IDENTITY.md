# CHARACTER IDENTITY

A / B character assets define reusable long-term identity, not one-shot acting.

Record:
- story identity / role;
- reuse range;
- silhouette / body relation;
- hair;
- base wardrobe;
- main colors;
- stable distinguishing marks;
- current persistent state reference;
- image file + status;
- image prompt + fixed exclusions;
- `execution_anchor_summary`;
- `voice_asset_id` linking to a separate `V001...` text-only voice record.

## execution_anchor_summary

```yaml
execution_anchor_summary:
  identity:
  silhouette:
  wardrobe:
  persistent_state:
  distinguishing_marks:
  performance_identity:
```

`performance_identity` means stable behavioral identity useful across shots, such as restrained, economical, physically restless, formal, blunt. It must not encode a temporary current-shot expression.

Do not bake into the master identity board:
- current-shot facial expression;
- current-shot gesture;
- current-shot camera angle;
- current-shot lighting design;
- current-shot emotional beat.
