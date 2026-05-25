# City Sim — /backend

Application code for the simulation engine, API, and database.

## Tech Stack
- Engine: Python 3.13 (pure Python, no framework)
- API: FastAPI + Uvicorn
- Database: SQLite via SQLAlchemy
- Frontend: Vue 3 + Vite (in `../frontend/`)
- Tests: pytest

## Key Directories

| Dir | What |
|-----|------|
| `engine/` | Core simulation — models, formulas, actions, cycle, NPC, events |
| `engine/actions/` | Faction action resolvers |
| `engine/cycle/` | Sequential-initiative cycle runner — resolution, end-of-cycle |
| `engine/npc/` | NPC behavior — weight building, action selection, targeting |
| `engine/events/` | `cascades`/`world` (mechanical collapse + chaos) + `event_system` (event deck) |
| `engine/mayor/` | Mayor actions + treasury (mayor_spec, treasury_spec) |
| `engine/llm/` | LLM audiences, prompts, response parsing, memory (llm-system_spec) |
| `engine/projects/` | Project construction + effects (projects_spec) |
| `engine/special/` | The Public, moneylender, external threats (special-factions_spec) |
| `api/` | FastAPI routes — auth, users, cities, city, sim, state, phase, members, actions, mayor, llm_profiles |
| `db/` | SQLAlchemy models, session, seed data |
| `data/` | JSON starting data (domains, factions, world_state) |
| `tests/` | pytest test suite |
| `logs/` | Simulation run logs |

## Commands

```
# Run tests
py -m pytest tests/ -q

# Start API server
py -m uvicorn api.server:app --reload

# Run sim from CLI
py main.py --cycles 5
```

## Rules
- Follow the **Change rules** in the root `CLAUDE.md` for any change
- Run tests after every change
- Specs live in `../Planning/specs/` — spec is truth for behavior
