# Decision: Implement Steal, Implement Evolve, Fix unstable_stacks Persistence

**Date:** 2026-04-05
**Status:** Accepted

## Context

Post-restructure review found three spec/code mismatches introduced during the API, DB, and UI additions:

1. **Steal** — Referenced in 13 places across NPC weights and behavior, but no `resolve_steal` existed. The cycle dispatcher routed unit Steal to passive_spy (placeholder) and faction Steal had a stub that rolled but did nothing.
2. **Evolve** — Defined in the actions spec as a faction-only probabilistic trait swap, but no resolver existed and FACTION_TRAIT_WEIGHTS had no entry. Factions could never select it.
3. **unstable_stacks** — `Faction.reset_cycle_state()` zeroed it every cycle, but Attack partial outcomes set it as a cumulative penalty (max 3). Resetting each cycle meant stacks could never meaningfully accumulate.

## Decision

### Steal: Implement with spec
- Added `resolve_steal()` to `engine/actions/unit.py` — contest roll, siphons domain rating from highest rival
  - Decisive: +0.25 actor / -0.25 target
  - Partial: +0.10 / -0.10
  - Fail: actor exposed (target gets spy gate)
- Fixed faction Steal in `cycle/resolution.py` — now siphons entrench from a random rival faction (roll ≥12: 1 entrench, ≥18: 2 entrench)
- Added Steal to `Planning/specs/actions_spec.md`
- All existing weight references (BASE_WEIGHTS, TRAIT_WEIGHTS, FACTION_TRAIT_WEIGHTS, behavior fallbacks) kept as-is

### Evolve: Implement per spec
- Added `resolve_evolve()` to `engine/actions/faction.py`
- Mechanic (from actions_spec.md): No roll. 25% add leader trait, 25% remove non-leader trait, 50% both. Requires leader.
- Added "Evolve" to FACTION_TRAIT_WEIGHTS (Expansionary, Open, Hierarchical, Meritocratic)
- Evolve remains in BASE_WEIGHTS but behavior.py already redirects unit Evolve → Grow
- Wired into `_execute_faction_action` in resolution.py

### unstable_stacks: Persist with decay
- Removed `self.unstable_stacks = 0` from `Faction.reset_cycle_state()`
- Added decay (`unstable_stacks = max(0, unstable_stacks - 1)`) in `end_of_cycle.py` alongside the existing unstable_domains decay
- Already serialized correctly — no serializer changes needed

## Rationale

- Steal was scaffolded in weights and behavior but had no real mechanics. Implementing it (rather than removing) adds a covert resource-extraction action distinct from Harm (which damages) and Expose (which reveals).
- Evolve is fully specced and straightforward to implement. It adds faction personality development.
- unstable_stacks resetting each cycle made the mechanic pointless. Persisting with decay means sustained attacks against a faction create meaningful cumulative pressure.

## Consequences

- Units can now Steal to siphon domain rating without needing a spy gate (but risk exposure on failure)
- Faction Steal siphons entrench from rivals — a softer alternative to Harm
- Factions with leaders can now Evolve, changing their trait composition over time
- unstable_stacks now accumulate across cycles (max 3), making sustained attacks more impactful; stacks decay by 1 per cycle
- Tests may need updates for new Steal and Evolve resolvers
