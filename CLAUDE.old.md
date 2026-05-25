# Identity

City_Sim - Python simulation engine featuring complex autonomous agent
behavior, dynamic faction influence modeling, and emergent narrative
generation

## Tech Stack
- Frontend: Vue.js (Options API), browser-based
- Backend: Python, FastAPI
- Database: SQLite via SQLAlchemy

## Workspaces
- `/Planning` — Specs, architecture, decisions
- `/scr` — Application code (engine, API, tests)
- `/docs` — Changelog, long-term goals
- `/tools` — Audit, validation scripts (run `py tools/audit.py` for engine snapshot)
- `/frontend` — Vue 3 + Vite browser UI

## Routing
| Task | Go to | Skills |
|------|-------|--------|
| Spec a feature | `/Planning/specs/` | — |
| Write code | `/scr/` | `updateprocess` |
| Run / test sim | `/scr/` | `postrunlog` |
| Audit engine | `/tools/` | — |
| Improve project | anywhere | `improve` |
| Check spec drift | `/Planning/specs/` | `speccheck` |
| Write docs | `/docs/` | — |
| Build frontend | `/frontend/` | — |

## Naming conventions
- Specs: `feature-name_spec.md`
- Components: PascalCase
- Tests: `test_*.py` (pytest)
- Decision records: `YYYY-MM-DD-decision-title.md`

## Skills

Workspace-level skills (in `workplaceskills/`): `updateprocess`, `speccheck`, `improve` — see root CLAUDE.md.

| Skill | Path | Use when |
|-------|------|----------|
| `postrunlog` | `skillsforprogram/postrunlog/skill.md` | After a sim run |

## Rules
- Write in plain, clear language
- Ask clarifying questions before making assumptions
- When unsure, say so
- Before making ANY code, data, or structure change — follow `updateprocess`
