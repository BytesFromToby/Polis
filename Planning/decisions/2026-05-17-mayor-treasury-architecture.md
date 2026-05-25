# Decision: Mayor and Treasury Architecture

**Date:** 2026-05-17
**Status:** Accepted

## Context

Stage 5 begins Phase 2 feature implementation. The Mayor layer (player actions, action pool, reputation) and Treasury (income, expenditure, moneylender) are the first new systems to build. They don't exist in the codebase yet — the engine only processes factions.

## Decision

**Module location:** New `engine/mayor/` package with:
- `engine/mayor/actions.py` — implements all 12 Mayor actions
- `engine/mayor/treasury.py` — income, expenditure, tax effects, moneylender logic

**Data models:** `Mayor` and `Treasury` dataclasses added to `engine/models.py`.

**Cycle integration:**
- Treasury income runs at Step 0 (pre-cycle, before faction actions)
- Treasury expenditure (guard payroll, maintenance) runs at Step 0 also
- Mayor action effects are pre-submitted before `run_cycle` is called; the runner applies them at Step 1 (before faction declaration) for effects that modify faction behavior, and at Step 3.5 (event step) for effects that fire events
- Mayor's action pool refills (+2, cap 6) at Step 9 (end of cycle)

**Mayor action submission:** Mayor actions are passed into `run_cycle` as a `List[MayorAction]`. This keeps the cycle runner pure — it doesn't decide what the Mayor does, just executes what was submitted. In the CLI, the Mayor takes no actions (empty list). In the future UI, the player submits actions before each cycle.

**Reputation:** Stored in `Mayor.reputation` as `Dict[str, int]` keyed by faction_id. Reputation decay runs at Step 9. The Public's support tracks separately in `ThePublic.support` but `Mayor.reputation["the_public"]` mirrors it.

## Rationale

- Keeping Mayor actions as a submitted list (not inline decisions) keeps the cycle runner testable without a player present
- Treasury at Step 0 means income is available for Mayor to spend in the same cycle it arrives
- Single `engine/mayor/` module mirrors the existing `engine/npc/`, `engine/events/` structure
- Models stay in `engine/models.py` — one source of truth for all dataclasses

## Consequences

- `run_cycle` signature changes: adds `mayor` and `treasury` parameters, and optional `mayor_actions` list
- All existing tests still pass (mayor_actions defaults to empty list)
- CLI `main.py` needs to instantiate Mayor and Treasury and pass them to the runner
- Loaders need to load/save Mayor and Treasury state
