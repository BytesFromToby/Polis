# ADR: Multi-Point Action Economy

**Date:** 2026-03-29
**Status:** Accepted

---

## Context

Two conflicting designs existed in the planning documents:

- `02_Constants_and_Scales.txt` and `04_Traits.txt` define a **multi-point action economy**: units receive `floor(domain_rating)` action points per domain per cycle and can spend them across multiple actions at varying levels. A Street-4 unit could take four level-1 actions or one level-4 action or any combination that sums to 4.

- The generated `actions_spec.md` (new planning doc) collapsed this to **1 action per cycle** per unit and per faction, with no explanation.

The actual codebase (`cycle.py`, `npc.py`) currently implements the 1-action-per-cycle model.

---

## Decision

**Keep the multi-point action economy** as defined in `02_Constants_and_Scales.txt` and `04_Traits.txt`.

### Unit action points
```
action_points = floor(domain_rating)   per domain, per cycle
```
Each action costs points equal to the level at which it is taken. Multiple actions per cycle are allowed as long as total cost ≤ available points.

### Faction action points
```
action_points = floor(faction.rating / 2)   per cycle
```

### NPC allocation
Points are distributed proportionally across eligible actions based on weighted action selection (see `npc-behavior-engine_spec.md`). Actions receiving 0 allocated points do not fire.

---

## Rationale

The multi-point economy is core to the design intent:

- It creates meaningful differentiation between high-rated and low-rated actors. A Street-7 unit with 7 points can pursue multiple goals simultaneously; a Street-2 unit with 2 points is forced to focus.
- The base weight system (with decimal tiebreakers) only makes sense in a multi-point context. Proportional allocation across 15 actions has no meaning if only 1 action fires per cycle.
- Trait modifiers shifting action weights have emergent effects across the whole point pool, not just one slot.
- The 1-action model was a simplification that removed strategic depth without a documented reason.

---

## Consequences

- The codebase (`cycle.py`, `npc.py`, `actions.py`) needs to be updated to implement the point economy. This is a non-trivial change to the cycle runner and NPC engine.
- `actions_spec.md` is updated to reflect the correct point costs per action.
- `npc-behavior-engine_spec.md` needs to reflect proportional allocation rather than single-action selection.
- The `NPCPlan` type may need to become a list of plans per unit rather than a single plan.
