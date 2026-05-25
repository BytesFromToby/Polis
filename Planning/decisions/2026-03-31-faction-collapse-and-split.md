# Decision: Faction Collapse and Split

**Date:** 2026-03-31
**Status:** Accepted

---

## Context

Factions can reach health=1, LN=20, zero members, and zero level_1_count and still persist indefinitely. There is no condition under which a faction is removed or transformed. This produces zombie factions that occupy simulation space without contributing to or being affected by the world.

---

## Decision

When a faction's health reaches 1 and a health decay event would reduce it further, the faction collapses. Collapse outcome is determined by the faction's floor rating at time of collapse.

### Trigger

Health decay attempts to reduce a faction below 1. At that point collapse fires instead of further decay.

### Outcome by Level

| Floor Rating | Outcome |
|---|---|
| 2–3 | Dissolve (always) |
| 4–5 | 50% dissolve / 50% split (random) |
| 6+ | Split (always) |

`level = floor(faction.rating)` at time of collapse.

### On Dissolve

- Narrative event fires
- Faction removed from `factions` dict
- All units with this faction in any slot have that slot cleared and shifted down
- Units become unaffiliated — no faction reassignment

### On Split

A faction split produces two factions from one:

**New faction (splinter):**
- ID: `{old_id}_splinter`
- Name: generated (e.g. "The [OldName] Remnant")
- Rating: `floor(old_rating) - 1`, minimum 2
- Health: 80
- Domain: same `domain_primary` as original

**Old faction (demoted):**
- Keeps its name and ID
- Rating drops to `floor(old_rating) - 2`, minimum 2
- Health: 80

**Leader:**
- If a leader exists, they are removed from the faction — not a member or leader of either successor
- `is_leader` set to False, faction slot cleared

**Traits:**
- Original traits divided between the two factions; remainder goes to old faction
- Old faction receives 1 new randomly selected trait
- New faction receives 2 new randomly selected traits

**Unit rebalancing:**
- Sort all named members by primary domain rating (highest first)
- Assign alternately: 1st → leader of new faction, 2nd → leader of old faction, 3rd → new faction, 4th → old faction, repeat
- `level_1_count` split evenly; remainder goes to old faction
- Any level_1_count that exceeds new capacity is discarded

**Faction relationships:**
- New faction and old faction are set as Foe to each other
- Old faction's existing relationships carry over to old faction only
- New faction starts with no relationships except the Foe entry toward old faction

---

## Rationale

- **Health=1 as trigger** keeps the floor behavior consistent — health never goes negative
- **Level-based outcomes** mean small factions die cleanly while powerful factions survive in weakened form, creating narrative continuity
- **Leader ejected on split** is a strong narrative beat — the crisis that broke the faction also ended the leader's tenure
- **Rivals on creation** reflects that splits are hostile events, not amicable divisions
- **New faction ID as `_splinter`** is simple and deterministic for a single split; if multiple splits occur, cycle number can be appended to ensure uniqueness

---

## Consequences

- Zombie factions are eliminated
- High-rated factions become harder to permanently destroy — they fracture and persist
- Split creates two new power centers in the same domain, increasing internal domain competition
- Leaders ejected from splits become unaffiliated high-rated units — prime targets for Seek Leadership elsewhere
