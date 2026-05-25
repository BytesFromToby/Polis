# Decision: Project Restructure for API + UI

**Date:** 2026-04-03
**Status:** Accepted

---

## Context

The project is moving from a headless CLI script to a full browser-based application with a FastAPI backend, Vue.js frontend, and SQLite persistence. The current flat file structure under `scr/engine/` was designed for a single-user local runner. It needs to be reorganized before the API layer is built.

## Decision

Adopt the following folder structure:

```
city_sim_Project/
│
├── scr/                        ← Python backend
│   ├── engine/                 ← Pure simulation logic. No HTTP, no DB.
│   │   ├── models.py           (keep — clean, no changes needed)
│   │   ├── formulas.py         (keep — cohesive math)
│   │   ├── logger.py           (keep)
│   │   │
│   │   ├── actions/            (split from actions.py)
│   │   │   ├── __init__.py
│   │   │   ├── unit.py         (grow, protect, care, harm, block, spy)
│   │   │   ├── faction.py      (grow, support, defend, block)
│   │   │   └── membership.py   (join, leave, kick, recruit, seek leadership)
│   │   │
│   │   ├── cycle/              (split from cycle.py — will grow)
│   │   │   ├── __init__.py     (exports run_cycle — no external imports break)
│   │   │   ├── runner.py       (run_cycle orchestrator — thin, calls steps)
│   │   │   ├── declaration.py  (steps 0–2: setup, NPC declare, faction declare)
│   │   │   ├── resolution.py   (steps 3–9: support, block, spy, actions, reset)
│   │   │   └── end_of_cycle.py (steps 10–12: updates, generators, persist)
│   │   │
│   │   ├── events/             (split from events.py)
│   │   │   ├── __init__.py
│   │   │   ├── cascades.py     (cascade system)
│   │   │   ├── faction.py      (collapse, split)
│   │   │   └── world.py        (chaos, power vacuums, SM, retirement, emergence)
│   │   │
│   │   └── npc/                (split from npc.py)
│   │       ├── __init__.py
│   │       ├── weights.py      (BASE_WEIGHTS, TRAIT_WEIGHTS, tables)
│   │       ├── behavior.py     (action selection, build_action_weights)
│   │       └── targeting.py    (target picking, focus management)
│   │
│   ├── api/                    (new)
│   │   ├── server.py           (FastAPI app entry point)
│   │   ├── dependencies.py     (JWT auth, session management)
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── cities.py
│   │       ├── sim.py
│   │       └── state.py
│   │
│   ├── db/                     (new)
│   │   ├── models.py           (SQLAlchemy table definitions)
│   │   ├── session.py          (DB connection and session)
│   │   └── seed.py             (load pre-built cities into DB at startup)
│   │
│   ├── loaders.py              (JSON → engine objects, pulled out of main.py)
│   ├── main.py                 (slim CLI entry point — or retired when API takes over)
│   └── tests/
│
└── frontend/                   ← Vue.js app (separate language, separate concern)
    └── (Vue project)
```

## Key Rules

- `engine/` is pure simulation logic. It must not import from `api/`, `db/`, or anything HTTP/DB related.
- `api/` calls the engine. The engine does not know the API exists.
- `db/` owns all SQLAlchemy models and DB access. Nothing else writes to the DB directly.
- `frontend/` is fully independent. It communicates with the backend only via HTTP.
- The `cycle/__init__.py` re-exports `run_cycle` so all existing callers continue to work without changes.
- Same pattern applies to `actions/__init__.py`, `events/__init__.py`, `npc/__init__.py`.

## Why

- `actions.py`, `events.py`, `npc.py`, and `cycle.py` are all 750–1300 lines and contain clearly separable logical groups. Splitting them now prevents the files from becoming unworkable as the engine grows.
- `cycle.py` in particular will grow as the Crisis system, GM intervention hooks, and API step control are added.
- The API and DB layers need clean separation from the engine to be testable and maintainable independently.
- Frontend is a separate language and toolchain — it does not belong inside `scr/`.
