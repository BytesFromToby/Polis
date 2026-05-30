# Polis — Rule the Unrulable

> A simulation of political conflict inside an ancient-Greek city-state — where rival
> factions scheme on their own, and you bargain with their leaders through a live LLM.

![Polis — the game view](docs/InPlayScreenshots/Maininterface.png)

**Polis** models the struggle for influence inside a single Greek *polis*. Eight spheres of
influence — Aristocracy, Temples, the Harbor, the Academy and more — are contested by **41
factions** (noble houses, priesthoods, merchant and banking houses, guilds, generals,
orators), each with an embedded leader and a personality that drives its choices. Factions
act one at a time each cycle and react to each other within it, so the story is emergent:
alliances, collapses, power vacuums, and the slow tilt toward greatness or tyranny that no
single rule scripts.

You play the **Prytanis** — the city's presiding official (the `Mayor` role in the engine).
You can't command the factions; you *work* them — endorse and condemn, levy taxes, broker
deals, spend coin and favor — and you can hold live, **LLM-driven negotiation audiences**
with any faction leader, who bargains in character. Agreed terms are parsed into structured
deals that feed back into the simulation, and the faction remembers how the conversation went.

> **Status:** Playable alpha, published as a demonstration of engineering practice and a
> disciplined AI-assisted workflow (see [Development workflow](#development-workflow-ai-assisted)).

---

## Why it's interesting

- **Emergent, not scripted.** Outcomes come from faction traits, contest math, and sequential
  initiative — not hand-authored event chains.
- **LLM negotiation that changes state.** Audiences are real multi-turn dialogues; the leader
  speaks from their faction's identity and personality, you confirm or reject the result, and
  the agreed terms become live deals that either side can keep or break.
- **A pure rules engine at the core.** `engine/` is deterministic simulation logic that imports
  only the standard library — testable, portable, and wrapped (not entangled) by the API and UI.
- **268 automated tests, ~1s.** Contest math, cycle order, events, mayor actions, and LLM
  parsing are all covered.
- **Built with my own [Plumbline](https://github.com/BytesFromToby/Plumbline)** — a spec-driven
  AI coding workflow I designed and dogfood here. Every feature has a spec, a blueprint, and
  committed tests.

![A negotiation audience — the leader bargains in character and the agreed terms parse into a structured deal](docs/InPlayScreenshots/Audience.png)

---

## Quick start

**Requirements:** Python 3.13+, and Node.js 18+ (only to rebuild the frontend).

```bash
pip install -r requirements.txt
```

**Run it headless** (no setup, no UI — fastest way to see the sim move):
```bash
cd backend
py main.py --cycles 50            # run 50 cycles, print a summary
py main.py --cycles 100 --seed 42 # reproducible run
```
Narrative and system logs land in `backend/logs/`.

**Run the full app** (API + browser UI). The backend serves the UI from `frontend/dist/`,
which is build output and not checked in — so build it once:
```bash
cd frontend && npm install && npm run build
cd ../backend && py -m uvicorn api.server:app --reload
```
Open **http://localhost:8000**, click **New Game**, name yourself and your city, and **Start**.
Run cycles and watch the standings, events, and treasury move; click a faction to hold an
audience. (A city builder for custom domains/factions lives under the same UI.)

> Working on the frontend? `npm run dev` in `frontend/` gives a hot-reloading dev server;
> rebuild before serving through the backend. The API runs fine without a build — you just
> won't get the UI at `/`.

**Run the tests:**
```bash
cd backend && py -m pytest tests/ -q
```

---

## Live LLM audiences (optional)

The game runs with **zero external dependencies**: with no provider configured it falls back
to a **stub client** that returns valid canned negotiation responses. To enable real audiences,
copy `.env.example` to `.env` (or export the variables) and set a provider:

| Variable | Purpose | Default |
|----------|---------|---------|
| `POLIS_SECRET` | JWT signing secret — **set this in any real deployment** | `dev-secret-change-me` |
| `LLM_PROVIDER` | `anthropic`, `openai_compat`, or `stub` | `stub` |
| `LLM_API_KEY` | API key for the chosen provider | — |
| `LLM_MODEL` | Model name | — |
| `LLM_BASE_URL` | Base URL for `openai_compat` (Ollama, LM Studio, …) | — |

Provider SDKs (`anthropic`, `openai`) are optional and imported only when used.

---

## How a cycle runs

| Step | What happens |
|------|--------------|
| 0 | **Treasury** — income, expenditure, debt, tax effects |
| 1 | **Initiative** — factions shuffled into a random turn order |
| 2 | **Action loop** — factions act one at a time (grow, harm, protect, steal, block, build/sabotage projects); state updates between turns |
| 3 | **Project ticks** — construction, completion, defense reset |
| 4 | **End of cycle** — trait drift, chaos, faction collapse, power-vacuum cascades, cooldowns |

`engine/` imports only the standard library and itself; `api/` wraps it in HTTP, `db/`
persists snapshots, and `frontend/` talks to the API over HTTP only. See
[`docs/architecture.md`](docs/architecture.md) for the full system map.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Simulation engine | Python 3.13 (pure, no framework) |
| API | FastAPI + Uvicorn |
| Auth | JWT (`python-jose`) + bcrypt |
| Database | SQLite via SQLAlchemy |
| Frontend | Vue 3 (Options API) + Vite |
| Tests | pytest |

---

## Development workflow (AI-assisted)

Polis is built with **[Plumbline](https://github.com/BytesFromToby/Plumbline)**, my structured,
spec-driven workflow for AI-assisted coding — a set of skills that replace ad-hoc prompting with
a disciplined pipeline. It's the part of this repo most worth a look if you care about *how* to
use AI coding tools rigorously:

- **Specs are the source of truth** (`Planning/specs/`). Each feature carries inline *Done-when*
  acceptance criteria tagged `[automated]` or `[human-required]`.
- **Reference docs** (`Planning/reference/`) hold shared truth — the data model, the contest
  formulas, the world's theming — verified against the code, so specs cite rather than redefine.
- **Decision records** (`Planning/decisions/`) capture non-obvious choices and why.
- The pipeline runs **spec → blueprint → build → inspect**, with every automated *Done-when*
  item backed by a committed test and signed off against the running software.

The result is a codebase where the intent behind each piece is documented and the behavior is
verified — not just generated.

---

## Repository layout

```
backend/      Python backend
  engine/     Pure simulation logic (models, formulas, cycle, npc, events, mayor, llm)
  api/        FastAPI routes, JWT auth, request/response schemas
  db/         SQLAlchemy models, session, startup seeding
  data/       JSON seed data (domains, factions, projects, world state)
  tests/      pytest suite
frontend/     Vue 3 + Vite browser UI
Planning/     Specs, reference docs, decision records (the Plumbline tier)
docs/         As-built architecture, long-term goals, design system
```

---

## License

MIT — see [LICENSE](LICENSE).
