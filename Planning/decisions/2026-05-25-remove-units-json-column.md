# Decision: Remove the dead `units_json` city-template field

**Date:** 2026-05-25
**Status:** Accepted

## Context
The sim engine removed units in v3 (factions replaced them — `formulas.py`, `serializer.py`,
`models.py` are all unit-free). But the `City` template table still carried a `units_json`
blob alongside `factions_json`, and it was written `"{}"` at every site (`seed.py`,
`city/new`, `city/load`, the publish fallback). It never stored data.

While removing it, a latent bug surfaced: `cities.py::publish_city`'s live-session branch
called `serialize_state(session.world, session.units, session.factions, session.domains)` —
the old 4-arg unit-era signature — against the current `serialize_state(world, factions,
domains, ...)`, then read `snapshot_data["units"]`, a key the serializer no longer returns.
That branch would raise at runtime; it only "worked" when it fell through to the
no-live-session fallback.

## Decision
- Removed `units_json` from `db/models.py` (`City`), `api/schemas.py` (`CityResponse`,
  with the always-zero `unit_count`), `api/routes/cities.py` (×3), `api/routes/city.py` (×2),
  and `db/seed.py`.
- Corrected the `publish_city` live-session call to `serialize_state(session.world,
  session.factions, session.domains)` and dropped the `snapshot_data["units"]` write.
- Migrated `city_sim.db` with `ALTER TABLE cities DROP COLUMN units_json`.
- Archived dead seed data: `data/units.json`, `data/past_cities/TwinCities/`.

## Rationale
The blob was a dead duplicate of `factions_json` ("factions are the new units"). Single
source of truth: the live units feature (if kept) works through session/snapshot, never the
city-template blob. Removing it also forced the broken publish branch to be corrected.

## Consequences
- 234 tests pass.
- No frontend regression for *loading* template units (the blob was always empty), but
  `BuilderView.vue` and `HomeView.vue` still reference `units_json`/`unit_count` on the
  response and will now read `undefined` — needs a UI spot-check / cleanup.

## Open item (deferred to user)
The **named-units feature is half-removed and untouched here**: `api/routes/state.py` still
exposes units CRUD ("add/edit/remove unit mid-sim"), and `BuilderView`/`DashboardView` have
unit editors, all operating on session/snapshot units rather than the deleted blob. Whether
this is a live LARP "named units" feature to keep or orphaned remains of the removed engine
units is a product decision, not inferable from code. **Do not remove without confirmation.**
