# Polis

A Python simulation engine that models political, social, and economic conflict
inside a fictional ancient-Greek city-state. **Factions** — noble houses, priesthoods,
merchant and banking houses, craftsmen's guilds, generals, and philosophers — act one
at a time each cycle, contesting eight spheres of influence (Aristocracy, Guilds, Trade,
the Professions, Temples, Military, Academy, and the Harbor) and reshaping the balance of
power. Each faction has an embedded leader and a personality that drives its choices. The
result is emergent narrative: alliances, collapses, power vacuums, and the slow tilt toward
greatness or tyranny that no single rule scripts.

A human **Mayor** can intervene — endorsing, condemning, brokering deals, levying
taxes — and can hold a live, **LLM-driven negotiation audience** with any faction,
where the faction's leader bargains in character and the outcome feeds back into the
simulation.

> **Status:** Early alpha — active work-in-progress. The core engine, REST API, and
> browser UI are functional end to end; features are still being added and things may
> change. This repository is published as a demonstration of engineering practice and
> AI-assisted development workflow.

---

## Why this project is interesting

- **Pure rules engine at the core.** `engine/` has no HTTP, no database, no UI — just
  deterministic simulation logic. Everything else wraps around it. This keeps the
  hard part testable and portable.
- **Emergent, not scripted.** Outcomes come from faction traits, contest math, and
  sequential initiative (factions act in random order and react to each other within
  the same cycle), not from hand-authored event chains.
- **LLM negotiation that affects state.** Faction audiences are real multi-turn
  dialogues; the agreed terms are parsed back into structured deals the engine honors.
- **234 automated tests, running in ~1.2s.** The contest math, cycle order, events,
  mayor actions, and LLM parsing are all covered.
- **Built with a disciplined AI-assisted workflow** (see below).

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Simulation engine | Python 3.13 (pure, no framework) |
| API | FastAPI + Uvicorn |
| Auth | JWT (`python-jose`) + bcrypt password hashing |
| Database | SQLite via SQLAlchemy |
| Frontend | Vue 3 (Options API) + Vite |
| Tests | pytest |

---

## Quick start

### Requirements
- Python 3.13+
- Node.js 18+ (only needed to rebuild the frontend)

### 1. Install backend dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the simulation headless (no setup, no UI)
```bash
cd backend
py main.py --cycles 50            # run 50 cycles, print a summary
py main.py --cycles 100 --seed 42 # reproducible run
```
Narrative and system logs are written to `backend/logs/`.

### 3. Run the full app (API + browser UI)
The backend serves the browser UI from `frontend/dist/`, which is build output and is
not checked in — so build it once first:
```bash
cd frontend
npm install
npm run build      # outputs to frontend/dist/
```
Then start the server:
```bash
cd ../backend
py -m uvicorn api.server:app --reload
```
Open **http://localhost:8000**. Create a city, configure factions in the builder,
start the sim, run cycles, and watch the events and faction standings update.

> Working on the frontend? Run `npm run dev` from `frontend/` for a hot-reloading dev
> server instead, and rebuild (`npm run build`) before serving through the backend.
> The API runs fine without a build — you just won't get the UI at `/`.

### 4. Run the tests
```bash
cd backend
py -m pytest tests/ -q
```

---

## Configuration

Copy `.env.example` to `.env` (or export the variables in your shell) to configure
authentication and the optional LLM provider:

| Variable | Purpose | Default |
|----------|---------|---------|
| `POLIS_SECRET` | JWT signing secret — **set this in any real deployment** | `dev-secret-change-me` |
| `LLM_PROVIDER` | `anthropic`, `openai_compat`, or `stub` | `stub` |
| `LLM_API_KEY` | API key for the chosen provider | — |
| `LLM_MODEL` | Model name | — |
| `LLM_BASE_URL` | Base URL (for `openai_compat` — Ollama, LM Studio, etc.) | — |

With no LLM configured, the engine falls back to a **stub client** that returns valid
canned negotiation responses, so the full app runs with zero external dependencies.
LLM provider SDKs (`anthropic`, `openai`) are optional and imported only when used —
install them separately if you want live LLM audiences.

---

## How it works

Each cycle runs in this order:

| Step | What happens |
|------|--------------|
| 0 | **Treasury** — income, expenditure, debt, tax effects |
| 1 | **Initiative** — factions shuffled into random turn order |
| 2 | **Action loop** — factions act one at a time (grow, harm, protect, steal, block, build/sabotage projects); state updates between turns |
| 3 | **Project ticks** — construction, completion, defense reset |
| 4 | **End of cycle** — trait drift, chaos, faction collapse, power-vacuum cascades, cooldowns |

`engine/` imports only the standard library and itself. `api/` wraps it in HTTP;
`db/` persists snapshots; `frontend/` talks to the API over HTTP only. See
[`docs/architecture.md`](docs/architecture.md) for the full system map.

---

## Repository layout

```
backend/      Python backend
  engine/     Pure simulation logic (models, formulas, cycle, npc, events, mayor, llm)
  api/        FastAPI routes, JWT auth, request/response schemas
  db/         SQLAlchemy models, session, startup seeding
  data/       JSON seed data (factions, domains, projects, world state)
  tests/      pytest suite (234 tests)
frontend/     Vue 3 + Vite browser UI
Planning/     Specs, reference docs, and decision records (see below)
docs/         As-built architecture and long-term goals
tools/        Audit and state-validation scripts
```

---

## Development workflow (AI-assisted)

This project is built with **[Plumbline](https://github.com/BytesFromToby/Plumbline)**,
my own structured, spec-driven workflow for AI-assisted coding — a set of skills that
replace ad-hoc prompting with a disciplined pipeline. It's worth a look if you're
interested in *how* to use AI coding tools rigorously:

- **Specs are the source of truth** (`Planning/specs/`). Each feature carries inline
  *Done-when* acceptance criteria tagged `[automated]` or `[human-required]`.
- **Reference docs** (`Planning/reference/`) hold shared truth — the data model and
  the contest formulas — verified against the engine code, so specs cite them instead
  of redefining them.
- **Decision records** (`Planning/decisions/`) capture non-obvious choices: what was
  decided and why.
- The pipeline runs **spec → blueprint → build → inspect**, with every automated
  *Done-when* item backed by a committed test.

The result is a codebase where the intent behind each piece is documented and the
behavior is verified — not just generated.

---

## License

MIT — see [LICENSE](LICENSE).
