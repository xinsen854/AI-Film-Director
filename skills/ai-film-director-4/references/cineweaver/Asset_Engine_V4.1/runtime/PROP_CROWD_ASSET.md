# PROP / CREATURE / CROWD ASSETS

## P key prop

Record only props whose structure/state matters to story or generation stability:
- story function;
- structure;
- material;
- scale relation;
- normal function;
- prohibited impossible function;
- activation conditions / limits;
- damage / exhausted state;
- `hand_contact_relevance`;
- `state_sensitive`;
- `scale_anchor`;
- image file/status;
- image prompt.

Default reference role: `prop`.

## G creature / entity

Record:
- body / anatomy;
- material;
- movement identity;
- ability boundaries;
- persistent morphology state;
- scale anchors.

Default reference role: `identity`.

## G crowd / extra group

A crowd may be one reusable group asset rather than dozens of separate people.
Record:
- `group_count_range`;
- age / wardrobe range where supported;
- faction / social role;
- formation / density tendencies;
- activity range;
- `lead_member_policy` for any recurring close-up individuals.

Default reference role: `crowd`.
