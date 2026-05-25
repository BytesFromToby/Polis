# API Spec — FastAPI Backend

**Status:** Scoping
**Last updated:** 2026-04-03

---

## Purpose

A FastAPI server that wraps the sim engine and exposes it over HTTP. Serves the GM browser interface. Supports multiple users, each running their own city simultaneously. Cities can be started from pre-built templates or built from scratch.

---

## Architecture

```
Browser (GM UI)           Browser (GM UI)
      |                         |
      | HTTP / WebSocket         |
      v                         v
              FastAPI Server
              api/server.py
                    |
          +---------+---------+
          |                   |
    User Session A      User Session B
    (City: Rivers Pt)   (City: Custom)
          |                   |
    Engine Instance     Engine Instance
          |                   |
              SQLite DB
              (single file)
         users / cities / sim_runs
         cycle_snapshots / narrative_log

         data/cities/            ← pre-built templates (JSON, for authoring)
           rivers_point/         ← seeded into DB at server startup
           twin_cities/
```

The server holds one engine instance per active user session in memory. State is written to the SQLite DB after each cycle.

---

## Users & Sessions

Users authenticate via username + password login. The server returns a JWT token which is sent with every subsequent request. The server uses the token to identify the user and route to the correct engine instance and data.

All sim and state endpoints are scoped under `/users/{user_id}/` or derived from the active session.

---

## Endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create a new user account |
| `POST` | `/auth/login` | Login, returns JWT token |
| `POST` | `/auth/logout` | Invalidate session token |

---

### Users

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/users/{user_id}` | Get user info and active city |

---

### City Templates

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/cities` | List all available city templates (pre-built + user published) |
| `GET`  | `/cities/{city_id}` | Get a city template (factions, units, domains) |
| `POST` | `/users/{user_id}/city/publish` | Publish user's current city as a template |

---

### User City Setup

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/{user_id}/city/load` | Start a city from a pre-built template |
| `POST` | `/users/{user_id}/city/new` | Start a blank city to build from scratch |
| `GET`  | `/users/{user_id}/city` | Get the user's current city config |
| `PATCH`| `/users/{user_id}/city` | Edit city-level settings (name, domains) |

---

### City Builder — Factions & Units (pre-sim)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/{user_id}/city/factions` | Add a faction to the city |
| `PATCH`| `/users/{user_id}/city/factions/{id}` | Edit a faction |
| `DELETE`| `/users/{user_id}/city/factions/{id}` | Remove a faction |
| `POST` | `/users/{user_id}/city/units` | Add a named unit |
| `PATCH`| `/users/{user_id}/city/units/{id}` | Edit a unit |
| `DELETE`| `/users/{user_id}/city/units/{id}` | Remove a unit |

---

### Sim Control

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/{user_id}/sim/start` | Initialize and start the sim from current city |
| `POST` | `/users/{user_id}/sim/step` | Run one cycle |
| `POST` | `/users/{user_id}/sim/run/{n}` | Run N cycles uninterrupted (max 100). Auto-stops on Crisis event. GM edits blocked during run. |
| `POST` | `/users/{user_id}/sim/pause` | Pause only applies between cycles during a Run X — not mid-cycle |
| `POST` | `/users/{user_id}/sim/reset` | Reset to starting city (cycle 0) |
| `GET`  | `/users/{user_id}/sim/status` | Current cycle number, running/paused state |

---

### State — Read (live sim)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/{user_id}/state` | Full world state snapshot |
| `GET` | `/users/{user_id}/factions` | All factions |
| `GET` | `/users/{user_id}/factions/{id}` | Single faction |
| `GET` | `/users/{user_id}/units` | All named units |
| `GET` | `/users/{user_id}/units/{id}` | Single unit |
| `GET` | `/users/{user_id}/domains` | All domains |
| `GET` | `/users/{user_id}/logs` | Narrative log (most recent N entries) |
| `GET` | `/users/{user_id}/cycles` | List all saved cycle snapshots |
| `GET` | `/users/{user_id}/cycles/{n}` | Get state snapshot from cycle N |

---

### State — GM Edits (live sim)

| Method | Path | Description |
|--------|------|-------------|
| `PATCH` | `/users/{user_id}/factions/{id}` | Edit faction stats mid-sim |
| `PATCH` | `/users/{user_id}/units/{id}` | Edit unit stats mid-sim |
| `POST` | `/users/{user_id}/factions` | Add a faction mid-sim |
| `DELETE` | `/users/{user_id}/factions/{id}` | Dissolve a faction mid-sim |
| `POST` | `/users/{user_id}/units` | Add a named unit mid-sim |
| `DELETE` | `/users/{user_id}/units/{id}` | Remove a unit mid-sim |
| `POST` | `/users/{user_id}/events/trigger` | Manually fire a named event |

---

## Persistence

**Decision: SQLite via SQLAlchemy**

One SQLite database file for the whole application. Cleaner than thousands of JSON files at scale, handles concurrent writes safely, and allows querying across history.

### Tables (rough schema)

| Table | What it stores |
|-------|----------------|
| `users` | User identity, active city id |
| `cities` | City templates (pre-built and user-created) — factions, units, domains as JSON blobs |
| `sim_runs` | One row per user per city run — start time, current cycle, status, gamemaster, setting, description, details (carried from city template) |
| `cycle_snapshots` | Full world state after each cycle — indexed by run_id + cycle_number |
| `narrative_log` | Narrative events per cycle — indexed by run_id + cycle_number |

### User Fields

| Field | Type | Notes |
|-------|------|-------|
| `user_id` | UUID | Auto-generated on registration |
| `username` | string | Chosen at registration |
| `email` | string | Optional, not shown in UI. Hidden during early testing. |
| `password_hash` | string | Hashed, never stored plain |
| `description` | string | Optional user bio / notes |
| `is_gm` | bool | Default: `true`. Reserved for future role control. |

---

### City Template Fields

| Field | Type | Notes |
|-------|------|-------|
| `city_name` | string | Display name of the city |
| `author` | string | Username of creator, or "official" for pre-builts |
| `description` | string | Short summary shown in the template browser |
| `setting` | string | Default: `"DnD"`. Reserved for future use. |
| `details` | string | Long-form field, unused for now. Reserved for future use. Carried into sim run. |
| `factions` | JSON | Full faction data |
| `units` | JSON | Named starting units |
| `domains` | JSON | Domain definitions |
| `published` | bool | False until user explicitly publishes |

### Key decisions
- City templates (pre-built) are seeded into the `cities` table at server startup, not kept as files
- Current live state is reconstructed from the latest cycle snapshot on server restart
- GM edits mid-sim are applied to memory and written as part of the next cycle snapshot
- Pre-built templates live in `data/cities/` as JSON files for authoring, then loaded into the DB

---

## Real-time Updates

**Decision:** Start with polling (`GET /users/{user_id}/state` on a timer). Add WebSocket push later.

**Frontend framework:** Vue.js (Options API style), served separately from the FastAPI backend.

---

## Engine Changes Required

- [ ] Cycle runner must be steppable (one call = one cycle)
- [ ] World state must serialize to JSON cleanly after each cycle
- [ ] GM edits must apply to in-memory state without a full reload
- [ ] Server must manage one engine instance per user session
- [ ] State must be written to disk after each cycle step

---

## Decisions

| Question | Decision |
|----------|----------|
| User identity | Login with username + password. JWT tokens for sessions. Future-proofed for real auth. |
| Persistence | SQLite via SQLAlchemy |
| Auto-run | Yes — `/sim/run/{n}` with a max of 100 cycles per call (limit is configurable) |
| City publishing | Users can publish their city as a template for others to use |

---

## Out of Scope (for now)
- Users sharing or viewing each other's cities
- Rollback to a previous cycle mid-run
