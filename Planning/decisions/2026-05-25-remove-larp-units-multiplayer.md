# Decision: Remove the LARP + named-units + multiplayer subsystem

**Date:** 2026-05-25
**Status:** Accepted

## Context
The LARP project was spun out into its own separate program. In this build, "factions
are the new units" — the engine dropped units in v3 — but a large LARP/units/multiplayer
layer remained, half-wired and increasingly dead weight: a phase state machine, a
player-action/IM review workflow, named-units CRUD, and a multi-member (gm/im/player)
model, plus matching Vue UI.

## Decision
Removed the whole subsystem, full-stack.

**Backend**
- Deleted routes: `api/routes/phase.py`, `actions.py`, `members.py` (+ unregistered in `server.py`).
- Dropped models: `PlayerAction`, `CityMember`; columns `City.mode`, `SimRun.larp_phase`, `SimRun.phase_advanced_at`.
- Cleaned LARP phase-gating from `sim.py`; `mode` handling + member creation from `city.py`;
  LARP/member/player-action schemas from `schemas.py`; stale unit routes from `state.py`'s docstring.
- DB migration on `city_sim.db`: dropped tables `player_actions` + `city_members`, columns
  `cities.mode` + `sim_runs.larp_phase` + `sim_runs.phase_advanced_at`.

**Frontend**
- `BuilderView.vue`: removed the named-units editor (panel, table, `UnitForm`, add/save/delete, units data).
- `DashboardView.vue`: removed LARP phase UI + `advancePhase`, the Units panel + `CharacterPopout`,
  `isLarp`/phase/unit computeds + helpers, and unit-era sort state. Fixed the factions table to use the
  embedded `f.leader.name` and dropped the unit-era `member_ids` (Members) column.
- `HomeView.vue`: removed LARP mode badges + dropdown options + `unit_count`.
- `api.js`: removed unit + phase methods; `city.load` no longer sends `mode`.
- Deleted components `UnitForm.vue`, `CharacterPopout.vue`.

## Rationale
LARP now lives elsewhere; keeping its scaffolding here was pure liability (a half-broken
publish path, undefined `member_ids`/`leader_id` reads, always-empty unit storage). The
solo GM build relies on `City.owner_id` for ownership — `CityMember` was redundant.

## Consequences
- Backend: **234 tests pass**. Frontend: **`npm run build` succeeds** (47 modules, no errors).
- **Manual UI smoke test passed (2026-05-25)** — Home → load city → Builder → Dashboard (cycle step); nothing broken.
- Audience negotiation (`AudienceModal.vue`) is untouched — its internal `phase` is a local
  state machine, unrelated to LARP cycle phases.
- `unit_id` on the (now-removed) `PlayerAction` is gone; no `unit_id` remains in the schema.
