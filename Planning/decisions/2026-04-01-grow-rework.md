# Decision: Grow Rework — 2^n+1 Curve and Entrench Gate

**Date:** 2026-04-01
**Status:** Accepted

## Context

The old grow system used two separate increment tables: a hand-tuned dict for units (doubling timers up to level 4, then irregular) and a quadratic formula for factions (`1 / floor²`). The curves were inconsistent with each other and didn't align with the action power scaling (which uses `2^(n-1)`). High-level growth was either too fast or too slow depending on which entity type.

Additionally, level-ups resolved instantly mid-action, meaning a unit could cross a floor boundary during a Grow action with no entrenchment requirement — the level just applied immediately.

## Decision

### 1. Unified grow increment formula

Both units and factions use the same formula:

```
cycles to next level = 2^n + 1
increment per Grow   = 1 / (2^n + 1)
```

Where `n` is the current floor level.

| Level | Cycles | Increment |
|-------|--------|-----------|
| 1 | 3 | 0.3333 |
| 2 | 5 | 0.2000 |
| 3 | 9 | 0.1111 |
| 4 | 17 | 0.0588 |
| 5 | 33 | 0.0303 |
| 6 | 65 | 0.0154 |
| 7 | 129 | 0.0078 |
| 8 | 257 | 0.0039 |
| 9 | 513 | 0.0020 |

### 2. Floor stored separately from rating

`rating` is still a float that accumulates freely via Grow. A new `floor` field (int) tracks the last confirmed level. These can diverge: `int(rating)` may exceed `floor` when the rating crosses a threshold but the level-up has not yet been applied.

### 3. Entrench gate on level-up

At end of cycle, for each unit domain and each faction:
- If `int(rating) > floor` AND `entrench >= 50` → level up: `floor += 1`, entrench reset to 25%
- If `int(rating) > floor` AND `entrench < 50` → pending, no level up yet

This makes entrenchment a prerequisite for advancement, not a consequence of it.

## Rationale

- Single formula for both entity types — simpler and consistent
- Aligns with action power scaling (same exponential base)
- The entrench gate gives defensive play a direct reward: units that have built entrench advance faster than those that haven't
- End-of-cycle resolution prevents mid-action state surprises and gives players/observers a clear moment when levels change

## Consequences

- `formulas.py`: `UNIT_GROW_INCREMENTS` dict and `faction_grow_increment()` replaced by `grow_increment(floor_level)`
- `models.py`: `DomainRating` and `Faction` gain a `floor: int` field
- `actions.py`: Grow resolvers no longer trigger level-up; they only increment rating
- `cycle.py`: End-of-step-7 block added to process floor level-ups with entrench check
- `main.py`: Load functions initialize `floor` from `int(rating)`
- Trait modifiers (Expansionary +20%, Satisfied ×0.77) preserved on unit Grow
- Faction Expansionary +11% preserved on faction Grow
