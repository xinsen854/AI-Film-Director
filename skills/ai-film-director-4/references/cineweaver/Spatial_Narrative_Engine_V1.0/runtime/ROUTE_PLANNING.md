# ROUTE PLANNING

## Purpose
Track routes only when movement through space matters to causality or readability.

For each relevant character / group:
```yaml
route_id:
actor_id:
start_zone:
goal_zone:
planned_zones: []
route_change_trigger:
forced_detour:
controlled_exit:
exposure_changes: []
end_zone:
```

## Rules
- Adjacent route steps must be topologically possible.
- A route may change because of new information, obstacle, blocked exit, threat or tactic shift.
- Do not pre-plan incidental footsteps.
- If route precision does not matter, keep it zone-level.
- If action requires exact distance / height / timing, mark that fact for SHOT Engine instead of over-specifying the whole map.
