# Decision: Loaders Abstraction

**Date:** 2026-04-03
**Status:** Accepted

## Context

All loading logic — reading JSON files, building engine model objects, generating missing data, and running pre-sim initialization — lives in `main.py`. The CLI can find its data files and hard-code their paths, but the API will need to load state from SQLite snapshots and from city templates stored in the database, not from files on disk.

Before building the API layer, loading must be decoupled from `main.py` so the same engine can be initialized from either source.

## Decision

Extract loading and pre-sim initialization from `main.py` into `scr/loaders.py`.

### What moves to `loaders.py`

- `load_domains_from_json(path)` → `Dict[str, Domain]`
- `load_units_from_json(path)` → `Dict[str, Unit]`
- `load_factions_from_json(path)` → `Dict[str, Faction]`
- `load_world_from_json(path)` → `WorldState`
- `generate_factions_from_domains(domains)` → fallback when factions.json missing
- `ensure_faction_leaders(units, factions, domains)` → generates missing leader units
- `pre_sim_population_fill(units, factions, domains)` → fills background population
- `load_state_from_json(data_dir)` → top-level convenience function that calls all of the above and returns `(world, units, factions, domains)` ready to run

### What stays in `main.py`

- CLI argument parsing
- Logger setup
- The cycle loop
- `print_summary()`

### Future additions (not in this change)

- `load_state_from_db(session, sim_run_id)` — restores a running sim from a SQLite cycle snapshot using `deserialize_state()` from `serializer.py`
- `load_city_template_from_db(session, city_id)` — loads a city template as starting state for a new sim run

## Rationale

`serializer.py` handles encoding/decoding models to plain dicts. `loaders.py` handles the boundary between external sources (JSON files, later SQLite) and live engine objects. Keeping these two concerns separate and out of `main.py` means the API can initialize a sim with a single call and the CLI continues to work unchanged.

## Consequences

- `main.py` becomes a thin CLI wrapper
- The API layer can call `load_state_from_json()` or (later) `load_state_from_db()` without touching file paths
- `ensure_faction_leaders` and `pre_sim_population_fill` are reachable from the API layer, which will need them when starting a new sim run
