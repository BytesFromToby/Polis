# Decision: Rename faction.health to faction.entrench

**Date:** 2026-04-01
**Status:** Accepted

## Context

Factions had a `health` field (int, 1–100) that tracked organizational stability — decaying when leaderless, recovering when led, damaged by attacks. The name `health` was borrowed from units, where it represents the biological condition of a person and drives retirement chance. Factions do not retire; the same retirement logic does not apply. The field was semantically misnamed from the start, and spec docs acknowledged the confusion with a note: "Called 'entrench' in some old docs."

Separately, the growth rework (2026-04-01) requires a minimum entrench gate before a unit or faction can level up. Using `health` for this gate on factions while using `entrench` for units would require two separate checks for the same concept.

## Decision

Rename `faction.health` to `faction.entrench` throughout the codebase and data files. All logic, values, and ranges remain identical — this is a pure rename.

## Rationale

- Factions don't retire, so `health` carries the wrong connotation
- `entrench` correctly describes organizational stability and resistance to disruption
- Unifies the level-up gate concept: both units and factions now use `entrench >= 50` as the floor change condition
- Removes the confusing dual-name situation noted in the spec

## Consequences

- `models.py`: `Faction.health` → `Faction.entrench`
- `actions.py`, `cycle.py`, `events.py`, `npc.py`, `main.py`: all references updated
- `_faction_health_state()` → `_faction_entrench_state()`; `FactionHealthDecay` → `FactionEntrenchDecay`
- `data/factions.json` and `data/past_cities/TwinCities/factions.json`: field renamed
- `Planning/specs/data-models_spec.md`: Faction table updated
- Unit `health` is unchanged
