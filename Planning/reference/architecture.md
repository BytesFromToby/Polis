# System Overview — Polis Engine

**Version:** v4
**Date:** 2026-05-25
**Updated:** 2026-05-25 — Rewritten faction-only. Removed the unit-era 13-step cycle and
invariants, the deleted LARP/multiplayer routes, and `events/faction.py`. Cycle is now
sequential-initiative; `Planning/specs/cycle-runner_spec.md` is authoritative.

---

## What the Simulation Is

Polis models political, social, and economic conflict inside a fictional city.
**Factions** act each cycle — one at a time, in random initiative order — contesting domain
resources and reshaping the balance of power. Each faction has an embedded leader and a
personality (traits). The primary output is a narrative log and full system log per cycle.

The engine is a pure rules engine: no HTTP layer, no database access, no UI. Everything else
wraps around it.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Sim engine | Python (pure, no framework) |
| API | FastAPI + Uvicorn |
| Auth | JWT (`python-jose`) |
| Database | SQLite via SQLAlchemy |
| Frontend | Vue 3 (Options API) + Vite |

---

## Folder Structure

```
polis/
│
├── backend/                    ← Python backend (engine, api, db, tests)
│   ├── engine/                 ← Pure simulation logic
│   │   ├── models.py           ← dataclasses (see Planning/reference/data-models.md)
│   │   ├── formulas.py         ← pure calculations (see Planning/reference/formulas.md)
│   │   ├── logger.py
│   │   ├── actions/            ← faction.py, _helpers.py
│   │   ├── cycle/              ← runner.py, resolution.py, end_of_cycle.py
│   │   ├── events/             ← cascades.py, world.py (mechanical), event_system.py (event deck)
│   │   ├── needs/              ← bands.py, chain.py, drift.py (public-needs_spec — the barley run)
│   │   ├── npc/                ← weights.py, behavior.py, targeting.py
│   │   ├── mayor/              ← actions.py, treasury.py (mayor_spec, treasury_spec)
│   │   ├── llm/                ← audiences, prompt_builder, response_parser, memory, client, crypto
│   │   ├── projects/           ← processing.py (projects_spec)
│   │   └── special/            ← public.py, moneylender.py, external_threats.py (special-factions_spec)
│   │
│   ├── api/
│   │   ├── server.py           ← FastAPI entry; serves frontend/dist at /
│   │   ├── deps.py             ← JWT auth + session dependencies
│   │   └── routes/             ← auth, users, cities, city, sim, state, mayor, llm_profiles
│   │
│   ├── db/                     ← models.py, session.py, seed.py
│   ├── data/                   ← JSON seed data (domains, factions, projects, world_state)
│   ├── loaders.py
│   ├── serializer.py
│   ├── main.py                 ← headless CLI runner
│   └── tests/
│
└── frontend/                   ← Vue 3 + Vite app
```

---

## Component Map

| Module | Owns |
|--------|------|
| `engine/models.py` | Dataclasses: Faction (embedded Leader), Domain, WorldState, plans, results |
| `engine/formulas.py` | Faction-contest math: rating ceiling, grow increment, rolls, contest, faction weight, domain cap resistance |
| `engine/actions/faction.py` | Faction action resolvers (grow, protect, aid, harm, steal, build/sabotage project) |
| `engine/cycle/runner.py` | `run_cycle()` orchestrator — full cycle order (see cycle-runner_spec) |
| `engine/cycle/resolution.py` | Sequential-initiative action loop + Break resolution (0 health → Break, never death) |
| `engine/cycle/end_of_cycle.py` | End-of-cycle state updates, leadership events, Break sweep |
| `engine/events/cascades.py` | Retired no-op (collapse cascades removed — factions are permanent) |
| `engine/events/world.py` | Chaos-driven upheavals (mechanical) |
| `engine/events/event_system.py` | Scripted/random event deck + Public-need gates (events_spec) |
| `engine/needs/` | Public needs: word bands, the harvest chain (pure), drift/shortage/population (public-needs_spec) |
| `engine/npc/{weights,behavior,targeting}.py` | Action weights, selection, and target picking |
| `engine/mayor/{actions,treasury}.py` | Mayor actions + treasury (mayor_spec, treasury_spec) |
| `engine/llm/` | LLM audiences, prompt building, response parsing, memory (llm-system_spec) |
| `engine/projects/processing.py` | Project construction, ticks, effects (projects_spec) |
| `engine/special/` | The Public, moneylender, external threats (special-factions_spec) |
| `engine/logger.py` | SimLogger: narrative + system logs |
| `api/server.py` | FastAPI app entry; serves the built frontend |
| `api/deps.py` | JWT auth, session management |
| `api/routes/` | HTTP endpoint handlers |
| `db/{models,session,seed}.py` | SQLAlchemy tables, connection, startup seeding |
| `loaders.py` / `serializer.py` | JSON → engine objects; engine ↔ snapshot serialization |
| `frontend/` | Vue 3 GM interface |

---

## The Cycle (sequential initiative)

Factions act one at a time in random order; state updates between turns, so later factions
see what earlier ones did. The conceptual phases:

| Step | Name |
|------|------|
| 0 | Treasury — income, expenditure, debt, tax effects |
| 1 | Initiative — shuffle factions into random turn order |
| 2 | Action loop — factions act sequentially (base-project build/sabotage resolve here, on the domain's `BaseProjectStack`) |
| 3 | Project ticks — legacy `tax_collection` construction/effects (base stacks don't tick) |
| 4 | End of cycle — traits, chaos, Break sweep, cooldowns, counters |

**`Planning/specs/cycle-runner_spec.md` is authoritative** for the full per-cycle
orchestration (treasury → external threats → mayor → action loop → Break sweep →
**active-event effects (item 5a)** → **public needs (item 5b)** → projects → world chaos +
new-event rolling → moneylender → the public). `Faction.toiling` and `Faction.withholding` are
cycle-only: set in the action loop (withholding also by an active `withhold` event applied at 5a,
just before needs), consumed by the needs step, reset before `run_cycle` returns.

---

## Module Dependency Rules

```
frontend/  →  api/  →  engine/
                  ↘  db/
```

- `engine/` imports only from stdlib and other `engine/` modules
- `api/` imports from `engine/` and `db/`
- `db/` imports from stdlib and SQLAlchemy only
- `frontend/` talks to `api/` over HTTP only

---

## Key Invariants

1. **Faction-only.** There are no units. Every faction always has an embedded `Leader`.
2. **Rank is clamped 1.0–10.0.** `rating` is the rank; `level` (= `int(rating)`, aliased by the
   `floor_rating` property) is the integer tier. `entrench`/stored `floor` are gone — a faction is
   rank + health. At 0 health a faction **Breaks** (level −1 or leader death); it never dies.
3. **Sequential initiative.** Factions act one at a time in random order; state updates between
   turns. There is no batch declaration/resolution phase.
4. **Domain utilization is recalculated each cycle** as Σ level (each faction contributes its
   `level`) — never carried raw. The old exponential weight table is retired.
5. **Cycle-only fields are never persisted** (e.g. `unstable_stacks`) — reset via
   `Faction.reset_cycle_state()`.
6. **`engine/` never imports from `api/`, `db/`, or `frontend/`.**
7. **The spec is truth.** Where this doc and a spec disagree, the spec wins.
