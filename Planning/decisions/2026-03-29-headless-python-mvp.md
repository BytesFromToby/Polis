# ADR: Headless Python MVP

**Date:** 2026-03-29
**Status:** Accepted

---

## Context

The city simulation has a large design surface: 15 domains, faction dynamics, NPC behavior, a 13-step cycle, cascading events, SM attention mechanics, and more. Before investing in a user interface, save/resume infrastructure, or multiplayer support, the core mechanical loop needed to be validated.

Key questions to answer before adding complexity:
- Do the weight and rating systems create meaningful power dynamics?
- Does trait-weighted action selection produce recognizable faction personalities?
- Does the 13-step cycle produce plausible narrative arcs across many cycles?
- Are there degenerate states (e.g., factions that always win, or cities that always collapse)?

A headless simulation — one that runs autonomously and writes output to files — is the fastest way to generate enough data to answer these questions.

---

## Decision

Version 1 of the city simulation engine is a headless Python program. It runs from the command line. There is no UI, no interactive input during a run, no player-controlled units, and no save/resume capability.

### Configuration

All parameters that would otherwise be set by a GM during play are configured before the run starts via `world_state.json` and the city generation process. This includes:
- Initial domain caps and relationships
- Faction traits and starting ratings
- Unit traits, ratings, and faction memberships
- Chaos thresholds and SM attention starting values
- Number of cycles to simulate

Once the run starts, none of these parameters can be changed from outside the engine.

### Output

Two log files are the primary feedback mechanism:

**`narrative.log`**
- Contains only dramatic events, filtered by `SimLogger.is_dramatic()`.
- Written in human-readable prose via `SimLogger.narrate()`.
- Format: `[Cycle N] <prose description>`
- Intended audience: a GM reading the simulation's story after a run.

**`system.log`**
- Contains every action, every roll, every state change.
- Format: `[Cycle N][Step S][actor_id] action → outcome (delta: X, roll: A vs B)`
- Intended audience: a developer debugging mechanics or a GM analyzing specific decisions.

All dramatic events appear in both logs. Non-dramatic events appear only in `system.log`.

### Standard Library Only

The engine uses no third-party packages. All code runs on a standard Python 3.10+ installation with no `pip install` required. This reduces setup friction and keeps the dependency surface at zero.

> **Superseded in part (2026-06-08):** still true for `engine/` — it imports only the standard
> library. But the project has since grown an API/DB/UI layer (FastAPI, SQLAlchemy, Uvicorn,
> pydantic, etc.) and a test suite, so running the *full app* now needs `pip install -r
> requirements.txt`. The "zero dependencies" property is the **engine's**, not the whole project's.

### Deferred Features

The following features are explicitly out of scope for v1:

| Feature | Reason Deferred |
|---|---|
| Steal action | Resolution mechanic not finalized |
| Contest action | Multi-party resolution not designed |
| Assist action | Cooperative resolution not designed |
| Expose (full) | Partial expose (SpyTargeted) is in scope; full Expose mechanic differs |
| Secession | Faction split mechanic not designed |
| Victory conditions | No win/lose state; simulation runs for a fixed cycle count |
| World Chaos probability table | Table not finalized in constants docs |
| SM surge mechanic | SM cascade behavior not fully specified |
| GM input during run | Requires event loop architecture not present in v1 |
| Player-controlled units | Requires input handling and turn sequencing |
| Save/resume | Requires serialization of mid-cycle state; full-cycle persistence is sufficient for v1 |

Deferred features are not stubbed out — they are simply absent. The code does not contain placeholder functions or TODO markers for deferred mechanics.

---

## Consequences

### Positive

- The mechanical loop can be iterated on rapidly. A full 50-cycle simulation runs in seconds; a developer can test a formula change and observe results immediately.
- The log files provide rich feedback without building any display infrastructure. The narrative log, in particular, produces readable fiction as a side effect of the simulation running.
- No dependency management. Any machine with Python 3.10 can run the simulation.
- The lack of GM input forces the design to be self-sufficient. If the simulation produces boring or degenerate results, the mechanics are at fault — there is no GM intervention to paper over bad design.
- Standard library constraint means the codebase remains portable and auditable.

### Negative

- No GM input means the simulation cannot adapt to produce interesting outcomes. If a faction collapses in cycle 3, the remaining cycles may be imbalanced.
- Fixed cycle count means the simulation does not end when something interesting happens. A victory condition would provide a natural stopping point.
- No save/resume means that if the simulation is interrupted mid-run, progress is lost. The engine writes state to JSON only at the end of each complete cycle.
- The deferred action set (Steal, Contest, Assist, Secession) means v1 simulates a narrower range of conflict than the full design intends. Results from v1 playtesting may not fully reflect the balance properties of the complete system.
