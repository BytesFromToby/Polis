# Decision: API Routes and Server

**Date:** 2026-04-04
**Status:** Accepted

## Context

The auth utilities, session manager, schemas, and DB layer were already in place.
The remaining work was building all route handlers and the FastAPI app entry point.

## Decision

Built the remaining API surface in six files:
- `api/routes/__init__.py` — empty package marker
- `api/routes/users.py` — GET /users/{user_id}
- `api/routes/cities.py` — city template list/get/publish
- `api/routes/city.py` — user city setup and city builder CRUD (pre-sim)
- `api/routes/sim.py` — sim control (start, step, run/n, pause, reset, status)
- `api/routes/state.py` — state reads and GM edits (live sim)
- `api/server.py` — FastAPI app, lifespan startup (DB init + seed), router wiring

`api/schemas.py` extended with request/response models for factions, units, domains,
city create/patch, and GM edit payloads.

`sim/run/{n}` runs cycles synchronously and stops early if `world.sm_state == "crisis"`.
`sim/pause` sets a session flag; it only has effect between cycles during a run (as per spec).
GM edit endpoints reject requests while `session.is_running == True`.

City builder CRUD (pre-sim) operates on the City DB record directly.
Live sim GM edits operate on the in-memory SimSession.

## Rationale

Synchronous cycle execution keeps the implementation simple for the MVP.
No background task infrastructure needed — `run/{n}` blocks until complete.
The `is_running` session flag enforces the GM-edits-blocked-during-run rule
at the HTTP layer without async complexity.

## Consequences

- `sim/pause` cannot interrupt a mid-run HTTP call (client must wait for run/{n} to return).
  This is acceptable for MVP; background task support can be added later.
- `run/{n}` is capped at 100 cycles per call (enforced in the route).
- All cycle results are persisted to DB after each cycle step.
