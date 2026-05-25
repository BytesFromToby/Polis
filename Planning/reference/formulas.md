# Core Formulas (Reference)

The current faction-contest math. Reference doc — definitional, no **Done when:** items.
**Verified against `scr/engine/formulas.py` (v3, units removed), 2026-05-25.**
Subsystem-specific math (treasury interest, entrench decay, health) lives with its own
spec/module, not here.

---

## Rating ceiling
`RATING_MAX = 5.0` — faction rating is clamped to 1.0–5.0.

## Grow increment
Per-cycle rating gain toward the next level: `1 / (2^n + 1)` where `n = floor level`.

| Level | Cycles to next | Increment/cycle |
|-------|----------------|-----------------|
| 1 | 3 | 0.3333 |
| 2 | 5 | 0.2000 |
| 3 | 9 | 0.1111 |
| 4 | 17 | 0.0588 |

## Faction roll
`d20 + floor(rating) + modifier`. Leaderless penalty (−2) is applied by the caller when relevant.

## Contest resolution
Roll attacker vs defender; `margin = attacker_roll − defender_roll`.

| Margin | Outcome |
|--------|---------|
| ≥ 5 | decisive |
| 1–4 | partial |
| ≤ 0 | fail (defender wins ties) |

## Faction weight (for domain utilization)
Weight contributed to a domain by faction level:

| Level | 1 | 2 | 3 | 4 | 5 |
|-------|---|---|---|---|---|
| Weight | 0 | 2 | 4 | 8 | 16 |

## Domain cap resistance
From `utilization / cap`:

| Utilization % | State |
|---------------|-------|
| < 60% | open |
| 60–85% | passive |
| 85–95% | contested |
| ≥ 95% | blocked |

(`cap == 0` → blocked.)
