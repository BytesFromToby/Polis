# Decision: Spec & architecture-doc hygiene after speccheck

**Date:** 2026-05-23
**Status:** Accepted

## Context
A speccheck pass on the evolved project found: a duplicate/stale cycle-runner spec (a "v2" batch model superseded by a later sequential-initiative spec), inconsistent spec filenames, and architecture docs that predated the mayor/llm/projects/special subsystems and still described the removed unit era.

## Decision
- **Deleted** `Planning/specs/cycle-runner_spec.md` (old batch model). The sequential-initiative spec is now the only cycle spec.
- **Standardized** spec filenames to the CLAUDE.md convention `feature-name_spec.md` (hyphenated feature): renamed `cycle_runner_spec` → `cycle-runner_spec`, `llm_system_spec` → `llm-system_spec`, `llm_profiles_spec` → `llm-profiles_spec`. Updated live references in `engine/cycle/runner.py` and `audience_spec.md`.
- **Updated `cycle-runner_spec.md`** with a "Full Orchestration" section reflecting what `runner.py` actually runs, delegating subsystem detail to the treasury/mayor/projects/special/events specs.
- **Refreshed** `Planning/architecture/system-overview.md` and `scr/CLAUDE.md` to list the mayor/llm/projects/special subsystems, `event_system`, and current API routes; marked the unit-era 13-step cycle and invariants as superseded pending a full rewrite.

## Rationale
Spec is truth and the docs are the map; both had drifted from the code. Consistent filenames prevent the kind of hidden duplicate that the two cycle specs had become.

## Consequences
- 14 specs, all conforming to the naming convention; the misleading duplicate is gone.
- Architecture docs now reflect the evolved subsystems. The old unit-based cycle/invariant text is flagged, not yet rewritten — a full invariant rewrite is deferred.
- Changelog references to the old filenames are left as historical record (append-only).
- **Not done:** the old event modules (`events/cascades.py`, `events/world.py`) were NOT removed. Reading them showed they are live, mechanical collapse/chaos systems — distinct from, not redundant with, `event_system.py` (the event deck). See open item below.

## Open item (deferred to user)
Removing the "old event system" was approved on the premise it duplicated `event_system.py`; the code shows it does not. The only genuinely dead code found is two uncalled functions — `events/faction.py::apply_faction_entrench_decay` and `events/world.py::tick_power_vacuums` — which are safe to delete in a separate cleanup.
