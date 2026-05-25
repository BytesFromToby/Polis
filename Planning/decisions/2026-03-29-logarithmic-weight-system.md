# ADR: Logarithmic Weight System

**Date:** 2026-03-29
**Status:** Accepted

---

## Context

The simulation needs a weight system for two purposes:

1. **Domain utilization** — each unit occupying a domain consumes a weight amount based on its rating level. Domain caps limit how many total weight-points can be present, creating scarcity at the domain level.

2. **Faction capacity** — each faction can hold a limited number of member weight-points based on its own rating floor. When a faction is full, it cannot recruit; it must grow first.

The system needed to create meaningful pressure at high rating levels. A linear weight (weight = level) would allow high-level entities to accumulate without escalating cost. The design goal was that each rating level above baseline should be significantly more expensive than the last, so that a single level-6 unit consumes far more domain space than three level-2 units.

---

## Decision

Use an exponential weight table. The weight for rating level `n` is:

```
WEIGHT_TABLE = {
    1:   0,
    2:   2,
    3:   4,
    4:   8,
    5:  16,
    6:  32,
    7:  64,
    8: 128,
    9: 256,
   10: 512
}
```

Level 1 units have zero weight — they are present but exert no meaningful domain pressure. From level 2 upward, each level doubles the previous weight.

### Discrepancy Note

There are two conflicting sources for this table:

- `02_Constants_and_Scales.txt` (the constants document): defines the table above, where level 3 = 4, level 4 = 8, level 5 = 16.
- `Technical_Spec_v1.txt`: states the formula as `weight(n) = 2^n − 2`, which gives level 3 = 6, level 4 = 14, level 5 = 30. The spec document also contains a comment stating "level 5 = 38," which matches neither source.

**The constants table (`02_Constants_and_Scales.txt`) is authoritative.** The formula `2^n − 2` is not used in the implementation. The values in `Technical_Spec_v1.txt` are incorrect and the comment "level 5 = 38" is also incorrect. These discrepancies should be corrected in `Technical_Spec_v1.txt`.

The runtime implementation uses only the hardcoded `WEIGHT_TABLE` dict in `formulas.py`. No algebraic formula is computed at runtime.

---

## How It Is Used

### Domain Utilization

At the start of each cycle, each domain's `utilization` is recalculated:

```
domain.utilization = sum(
    WEIGHT_TABLE[floor(unit.primary_rating())]
    for unit in units
    if unit.primary_domain() == domain.name
    and not unit.retired
)
```

If `utilization` approaches `cap`, Grow actions that would cause a floor-crossing are gated until the domain has headroom.

### Faction Capacity

Faction capacity is the maximum total weight-points the faction's members can represent:

```
capacity = WEIGHT_TABLE[floor(faction.rating)]
```

This is never stored. It is derived fresh each time it is needed.

When a faction's rating floor increases (e.g., from floor 3 to floor 4), capacity jumps step-wise from 4 to 8. Fractional rating gains within a floor do not change capacity.

---

## Consequences

### Positive

- High-level entities are meaningfully rare. A domain with cap 64 can hold one level-6 unit (weight 32) plus a handful of lower-level units, not dozens of mid-tier entities.
- Domain caps create natural scarcity pressure without explicit hard limits per entity. The pressure is emergent from the weight totals.
- Faction capacity creates natural recruitment friction. A faction must grow to absorb more powerful members.
- Step-wise capacity changes at floor crossings give Grow actions a clear, meaningful payoff threshold.

### Negative

- The doubling is sharp. A level-2 unit (weight 2) and a level-5 unit (weight 16) are not directly comparable; faction composition becomes a significant strategic variable even though NPCs do not reason about it explicitly.
- Level 1 units (weight 0) consume no domain space and no faction capacity. This is intentional — they represent peripheral actors — but means that a faction can technically have unlimited level-1 members without exceeding capacity. The code must enforce a minimum membership count check separately if this becomes a balance issue.
- The discrepancy between `Technical_Spec_v1.txt` and `02_Constants_and_Scales.txt` is a latent documentation error. If the spec document is used as a reference without cross-checking, incorrect values will be implemented.
