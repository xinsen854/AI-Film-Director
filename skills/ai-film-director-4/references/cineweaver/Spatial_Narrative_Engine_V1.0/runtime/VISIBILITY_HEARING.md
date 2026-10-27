# VISIBILITY / HEARING RELATIONS

## Supported relations
- character sees entity;
- character cannot see entity;
- character hears entity but cannot see it;
- audience can see entity while character cannot;
- entity becomes visible after occluder clears;
- entity remains partially occluded.

## Record
```yaml
viewer:
target:
visual_state: VISIBLE | PARTIAL | OCCLUDED | OFFSCREEN
hearing_state: AUDIBLE | MUFFLED | INAUDIBLE
occluder:
audience_can_see:
character_can_see:
narrative_reason:
```

## Rule
Visibility is a story fact when it affects information, suspense, recognition, deception or action.
Do not micromanage visibility for ordinary background continuity.
