# Decision: Permanent Faction Leader

**Date:** 2026-05-24
**Status:** Accepted

## Context

Every faction was always intended to have a leader. The codebase carried leaderless machinery from an earlier design: `leader: Optional[Leader]`, `leadership_need` (an accumulator that ticked up while leaderless), and `is_leaderless()` returning True for both `leader is None` and `leader.status == "absent"`. This was flagged as pending removal in `data-models_spec.md` v6.

## Decision

- `Faction.leader` changed from `Optional[Leader] = None` to required `Leader` (no default). Field moved before `rating` in the dataclass to satisfy Python's required-before-defaulted ordering.
- `Faction.leadership_need` field removed.
- `Faction.is_leaderless()` now only checks `leader.status == "absent"` — a faction can still be effectively leaderless (absent leader), but it always has a leader object.
- Loaders and API routes that constructed factions without a leader now generate a named placeholder leader at creation time.
- `test_leaderless_faction_accumulates_ln` removed (tests the removed field).
- `leadership_need` keys removed from all faction JSON data files.

## Rationale

Leaderless factions added complexity with no payoff in the current design. The leader-replacement loop (`weakened → absent → replaced`) still works unchanged — absent is a valid leader status, not the same as having no leader. Removing the None branch simplifies `is_leaderless()`, serialization, and any code that had to guard against `faction.leader is None`.

## Consequences

- All factions always have a `Leader` object. The absent/weakened/present status cycle is unchanged.
- `leadership_need` is gone. The runner no longer ticks it; the replacement function no longer resets it.
- Serialized state from before this change that carries `leadership_need` is silently ignored on load (the deserializer drops unknown keys).
- Factions created via city builder or live GM routes get a placeholder leader name; a future API change can expose leader naming.
