# Decision: data-models spec ↔ code alignment

**Date:** 2026-05-23
**Status:** Accepted

## Context
First subsystem of the spec-alignment plan. Deep-diffed `data-models_spec.md` (v5) against `engine/models.py`. Every spec entity existed in code and most fields matched; drift was a handful of fields, renamed helpers, and entities the spec hadn't caught up to.

## Decision
**Spec updated to v6 to match code (code was the evolved truth):**
- Added `Faction.floor` (stored confirmed level, distinct from the `floor_rating` property) and `Faction.leadership_need`.
- `ActionResult`: added `margin`; outcome values now include `blocked`/`no_op`; roll fields typed `int`.
- Renamed `Deal.rep_cost_if_broken_by_mayor` → `rep_cost_if_broken`.
- Helper list: `is_leader_absent` → `is_leaderless`; added `get_faction_relationship`, `reset_cycle_state`.
- Delegated special-factions (`ThePublic`, `ThreatEffect`, `ExternalThreat`) and events (`GameEvent`, `EventEffect`, `CascadeSpec`) entity definitions to their own specs rather than duplicating.

**Mayor action-point economy changed (owner decision) — start 1, max 6, +1/cycle:**
- `models.py`: `Mayor.action_points` default `6 → 1`; `refill()` `+2 → +1`.
- `test_mayor.py::test_mayor_refills_each_cycle` updated (0 → 1 after one cycle).
- Spec `action_points` default `0 → 1` with the refill rule noted.

## Rationale
For the field/helper drift, the code is the current truth and the spec had lagged. For the AP economy, the owner specified the intended rule (start 1, +1/turn), which matched neither the old spec (0) nor the old code (start 6, +2/turn).

## Consequences
- `data-models_spec.md` v6 now matches `models.py`. 235 tests green.
- The Mayor starts weaker (1 AP) and accrues slower (+1/cycle) — a deliberate balance change.

## Deferred / follow-up
- **Make the faction leader permanent** (remove `leader: Optional`, `leadership_need`, `is_leaderless`'s None branch). Intended by owner, not yet specced or built — flagged inline in `data-models_spec.md`.
- **`mayor_spec.md`** should document the start-1 / cap-6 / +1-per-cycle AP rule during the mayor alignment pass.
