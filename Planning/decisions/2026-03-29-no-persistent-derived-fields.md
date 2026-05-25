# ADR: No Persistent Derived Fields

**Date:** 2026-03-29
**Status:** Accepted

---

## Context

During data model design, several fields were identified that could either be stored in JSON or computed at runtime from other stored data. Storing a derived field is convenient for callers but introduces a class of bug: the stored value goes stale when the authoritative source changes, and any code that forgets to update it will read incorrect data.

Three fields were identified as clearly derivable:

- **`capacity`** (on Faction): the maximum member weight the faction can hold
- **`active_supporters`** (cycle-local): the list of units currently supporting a faction this cycle
- **`inertia`** (on Unit): how much focus score is required to override a unit's default behavior

All three are fully deterministic from data that is already stored and updated correctly. None of them represent decisions or history that would be lost if not persisted.

---

## Decision

None of these three fields are stored in JSON or in any persistent model field. They are computed fresh at the point of use each cycle.

### `capacity`

Derived from the faction's current rating:

```python
capacity = get_faction_capacity(floor(faction.rating))
# which returns: WEIGHT_TABLE[floor(faction.rating)]
```

Capacity changes only when `floor(faction.rating)` changes. The faction's rating is stored and updated correctly. There is no scenario where capacity needs to be known independently of the current rating.

The `Faction` dataclass does not define a `capacity` field. `models.py` includes a docstring comment on the `Faction` class explicitly noting that capacity is derived and must not be added as a stored field.

### `active_supporters`

`active_supporters` is a plain Python `list[str]` (unit IDs) created as a local variable inside `run_cycle()` at the start of each cycle. It does not exist before the cycle begins and does not persist after the cycle ends.

Lifecycle:
1. Created as `active_supporters = []` at the start of `run_cycle()`.
2. Populated during step 3 (SupportFaction resolution) and can also be populated by steps 5–6 if a unit's block or spy action involves a faction they belong to.
3. Read during step 8 to compute `faction_effective_power()` for faction actions.
4. Cleared (or simply goes out of scope) at the end of step 9.
5. No step after 9 reads `active_supporters`.

Because it is cycle-local, it cannot be stored — each cycle's supporter set is different, and the field has no meaning outside of the cycle it was built in.

### `inertia`

Derived per-unit per-cycle from stored fields:

```python
inertia = grit + (floor(primary_rating) * 0.5) + entrench_to_bonus(entrench)
```

All three component fields (`grit`, the unit's domain ratings, `entrench`) are stored and updated each cycle. Inertia is used only in the NPC decision engine to determine whether a focus score is strong enough to override the trait-weighted random selection. It is computed at the time of the check and discarded.

The `Unit` dataclass does not define an `inertia` field. The `calculate_inertia(unit)` function in `formulas.py` is the single source of truth for this computation.

---

## Consequences

### Positive

- The data mutation surface is smaller. Fewer fields to update means fewer places where stale data can silently persist.
- Derived values are always consistent with their authoritative sources. There is no code path that can produce a stale capacity or inertia.
- JSON files are leaner. `units.json` and `factions.json` do not grow with redundant fields.
- The rule is simple enough to enforce in review: if a field can be computed from other stored fields, it must not be stored.

### Negative

- Callers cannot cache these values. Any code that needs capacity or inertia must call the derivation function. If this is called in a tight loop, it adds computational cost.
- New contributors must know to call `get_faction_capacity()` and `calculate_inertia()` rather than reading a field. The docstring convention in `models.py` must be maintained to communicate this.
- If the derivation formula changes (e.g., the weight table is revised), all call sites produce new values automatically on the next cycle — which is usually correct, but means there is no migration period where old stored values and new formulas can coexist.

### Enforcement

- `models.py`: `Faction` and `Unit` dataclasses include docstring lines marking each derived field and identifying the function to call instead.
- `formulas.py`: `get_faction_capacity()`, `calculate_inertia()`, and `faction_effective_power()` are the canonical derivation functions. No other module should reimplement this logic inline.
- Code review policy: any PR that adds `capacity`, `inertia`, or `active_supporters` as a persistent field should be rejected.
