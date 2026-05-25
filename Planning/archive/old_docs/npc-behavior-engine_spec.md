# NPC Behavior Engine Specification

**Version:** v2
**Date:** 2026-04-01
**Supersedes:** v1 (2026-03-29)
**Decision doc:** `Planning/decisions/2026-03-31-action-economy-rework.md`

Authoritative spec for `npc.py`. Describes how units and factions select actions each cycle.

---

## Overview

The NPC behavior engine is called once per unit and once per faction during the declaration phase (steps 1–2). Plans are locked after declaration; no re-evaluation occurs mid-cycle.

The engine has two main entry points:
- `select_npc_actions(unit, world, factions, domains) -> List[NPCPlan]` — for units; returns up to 3 plans
- `select_faction_action(faction, world, active_supporters) -> FactionPlan` — for factions; returns a single plan

Units take **at most 3 actions per cycle**. Actions are selected by weighted priority, not proportional allocation.

---

## Unit Action Selection

### Step 1 — Build Weights

```
weights = BASE_WEIGHTS.copy()
weights = apply_trait_modifiers(weights, unit.traits)
weights = apply_care_reduction(weights, unit.health)
weights = apply_protect_reduction(weights, unit)
weights = apply_tension_modifier(weights, unit)
weights = apply_relationship_boosts(weights, unit, domains)
```

No changes to weight-building from v1. BASE_WEIGHTS and TRAIT_WEIGHTS are unchanged.

### Step 2 — Action Selection (Top-3 by Weight)

Actions are not allocated proportionally. Instead, the top-weighted eligible actions are selected:

1. **Rank** all eligible actions by final weight (highest first).
2. **First action** (highest weight): always selected.
3. **Second action**: selected if its weight is within 5 of the first action's weight.
4. **Third action**: selected if its weight is within 8 of the first action's weight.
5. **Skip check**: each selected action has a 5% independent chance of being skipped this cycle.

Maximum of 3 actions per unit per cycle.

```
sorted_actions = sorted(weights.items(), key=lambda x: x[1], reverse=True)

selected = []
top_weight = sorted_actions[0][1]

for action, w in sorted_actions:
    if len(selected) == 0:
        selected.append(action)                        # always take highest
    elif len(selected) == 1 and top_weight - w <= 5:
        selected.append(action)                        # within 5 of top
    elif len(selected) == 2 and top_weight - w <= 8:
        selected.append(action)                        # within 8 of top
    else:
        break

# Skip check (5% each, independent)
selected = [a for a in selected if random.random() > 0.05]
```

### Step 3 — Determine Action Level

For each selected action, the level is determined by the unit's floor in the domain relevant to that action (Option B from decision doc).

The unit may choose to execute at any level from 1 up to their floor in that domain. NPC units default to their maximum available level unless budget forces a lower choice.

### Step 4 — Budget Allocation

The unit has a separate L1 budget per domain: `2^(floor - 1)` for each domain they are active in.

For each selected action:
1. Determine the relevant domain.
2. Check budget remaining for that domain.
3. Calculate cost: `2^(action_level - 1)`.
4. If cost exceeds remaining budget: reduce action level until it fits, or drop the action.
5. Deduct cost from domain budget.

One-of-each rule is enforced — no action appears twice even across domains.

### Step 5 — Gate Checks

For each selected action, check its gate. If the gate fails:
- Harm → redirect to Expose (target selection)
- Seek Leadership → redirect to Grow
- Leave → redirect to Grow
- Join → redirect to Grow
- Redirect also gate-checked; if redirect fails → Grow; if Grow invalid → Care

### Step 6 — Focus Modifies Target Selection

Focus does **not** change which actions are selected — it biases who is targeted.

- If `focus_1.score > calculate_inertia(unit)`: weight `focus_1.target_id` 3× in target selection.
- If `focus_2.score > calculate_inertia(unit)`: weight `focus_2.target_id` 2× in target selection.
- Focus_1 dominates. If focus_1 fires, focus_2 bias is not applied.

### Output

One `NPCPlan` per selected action (after gate resolution and budget allocation). Each plan carries:
- `action`: action name
- `level`: level at which the action executes
- `target_id`: selected target (if applicable)
- `source`: `"focus_1"`, `"focus_2"`, `"trait"`, or `"wildcard"`

---

## BASE_WEIGHTS

All actions start from these base weights. Trait modifiers are **added** on top. Decimal tiebreakers determine priority when weights are equal.

```python
BASE_WEIGHTS = {
    "Protect":         10.10,
    "Care":            10.09,
    "Support Faction": 10.08,
    "Obscure":         10.07,
    "Grow":            10.06,
    "Join":            10.055,
    "Leave":           10.054,
    "Block":           10.05,
    "Recruit":         10.045,
    "Kick":            10.044,
    "Evolve":          10.043,
    "Expose":          10.03,
    "Steal":           10.02,
    "Harm":            10.01,
    "Seek Leadership": 10.00,
}
```

Dynamic adjustments:
- **Care:** If `unit.health > 75`, Care weight `−= (health − 75)`. Floor: 0.01.
- **Protect:** If primary domain `entrench > 0.85`, Protect weight `−= 1 per 0.01 above 0.85`. Floor: 0.01.
- **Seek Leadership:** If unit is in a leaderless faction, +11 to Seek Leadership weight.

---

## TRAIT_WEIGHTS

Additive modifiers applied on top of BASE_WEIGHTS.

### Unit Traits

| Trait | Action modifiers |
|---|---|
| `Revengeful` | Harm +20, Steal +10, Block +5 |
| `Cautious` | Protect +20, Obscure +15, Care +5, Grow +3 |
| `Expansionary` | Grow +20, Steal +10, Harm +5, Expose +5 |
| `Satisfied` | Support Faction +20, Care +15, Protect +10, Grow +3 |
| `Callous` | Steal +20, Block +15, Expose +5, Harm +5 |
| `Opportunistic` | Grow +15, Expose +10, Steal +10, Block +5 |
| `Loyal` | Support Faction +20, Protect +15, Grow +10, Care +5 |
| `Ambitious` | Seek Leadership +20, Grow +15, Expose +10, Harm +5 |
| `Loner` | Grow +20, Protect +15, Obscure +10, Leave +5 |
| `Joiner` | Join +20, Support Faction +15, Recruit +10, Care +5 |
| `Resilient` | Care +20, Protect +15, Grow +10, Obscure +5 |
| `Fragile` | Obscure +20, Protect +15, Care +10, Leave +5 |
| `Connected` | Join +20, Recruit +15, Support Faction +10, Expose +5 |
| `Paranoid` | Obscure +20, Protect +15, Expose +10, Care +5 |

### SM-Specific Unit Traits

| Trait | Action modifiers |
|---|---|
| `Named` | Expose +20, Grow +15, Harm +10, Block +5 |
| `Anonymous` | Obscure +20, Expose +15, Steal +10, Block +5 |

Multiple traits stack. All modifiers apply simultaneously.

---

## `build_action_weights(unit) -> Dict[str, float]`

```
1. weights = BASE_WEIGHTS.copy()

2. For each trait in unit.traits:
       weights[action] += TRAIT_WEIGHTS[trait][action]

3. Apply Care health reduction:
       if unit.health > 75:
           weights["Care"] -= (unit.health - 75)
           weights["Care"] = max(0.01, weights["Care"])

4. Apply Protect entrench reduction:
       if primary domain entrench > 0.85:
           weights["Protect"] -= (entrench - 0.85) / 0.01
           weights["Protect"] = max(0.01, weights["Protect"])

5. Apply Seek Leadership leaderless boost:
       if unit is in a leaderless faction:
           weights["Seek Leadership"] += 11

6. Apply tension modifier

7. Apply domain relationship boosts

8. Return weights
```

---

## `apply_tension_modifier(weights, focus_1, focus_2) -> Dict[str, float]`

Tension = `(focus_1.score if focus_1 else 0) + (focus_2.score if focus_2 else 0)`

| Tension | Effect |
|---|---|
| 0 – 4 | No change |
| 5 – 7 | Primary trait weights × 1.5; other weights × 0.7 |
| 8 – 10 | Primary trait weights × 2.0; other weights × 0.4 |

Primary trait weights = actions whose merged weight is above the mean of all action weights. Returns a new dict; original not mutated.

---

## Domain Cap Pressure

### `_apply_domain_cap_pressure(weights, unit, domains)`

Applied after all other weight modifiers (traits, tension, relationship boosts). Uses the unit's primary domain utilization.

| Condition | Effect |
|---|---|
| `utilization / cap < 90%` | No change |
| `utilization / cap >= 90%` | Grow `-3` per point over 90% (floor 0); Steal `+2` per 3 dropped from Grow |

**Example:** Domain at 95% cap → 5 points over → Grow -15, Steal +10.

Grow weight cannot go below 0. Steal gain is based on actual points dropped (not the theoretical maximum).

---

## Domain Relationship Boost System

### `RELATIONSHIP_ACTION_BOOSTS`

| Relationship | Boosted Actions |
|---|---|
| `Foe` | Harm ×1.8, Expose ×1.5 |
| `Client` | Support Faction ×1.8, Protect ×1.5 |
| `Friend` | Recruit ×1.5, Join ×1.5, Support Faction ×1.3 |
| `Hide` | Obscure ×1.8, Expose ×1.5 |
| `Neutral` | No boost |

Boosts stack multiplicatively for multiple Foe relationships.

### `RELATIONSHIP_TARGET_DOMAIN_WEIGHTS`

| Relationship | Target domain weight multiplier |
|---|---|
| `Foe` | ×3.0 |
| `Client` | ×2.0 |
| `Friend` | ×1.5 |
| `Hide` | ×0.3 |
| `Neutral` | ×1.0 |

---

## Target Selection Helpers

### `_pick_expose_target(unit, world, domains) -> str | None`

Priority order:
1. Anonymous units in domains where unit has a Foe relationship
2. Any unit in Foe domains
3. Any unit in the same domain as the acting unit
4. Any non-retired unit

Returns None → action redirects to Grow.

### `_pick_harm_target(unit, world) -> str | None`

Requirements:
- Target must be in `unit.spy_gates`
- Target must not be retired
- Target must not be Anonymous (unless explicitly identified)

Priority order:
1. `focus_1.target_id` if it meets requirements
2. `focus_2.target_id` if it meets requirements
3. Any valid target in Foe domains
4. Any valid target

Returns None → action redirects to Expose.

---

## Faction Action Selection

Factions take **one action per cycle**. This action counts as one of three toward the Support Faction level-pooling mechanic.

### FACTION_TRAIT_WEIGHTS

| Faction Trait | Weights |
|---|---|
| `Defensive` | Defend (50), Grow (30), Steal (20) |
| `Expansionary` | Grow (60), Expose (25), Defend (15), Evolve (10) |
| `Open` | Grow (40), Defend (30), Steal (30), Evolve (15) |
| `Insular` | Defend (50), Block (30), Grow (20) |
| `Hierarchical` | Defend (40), Grow (35), Expose (25), Evolve (10) |
| `Meritocratic` | Grow (50), Expose (30), Defend (20), Evolve (15) |
| `Corrupt` | Harm (40), Grow (30), Expose (30) |
| `Ideological` | Defend (40), Grow (35), Block (25) |

Default (no matching trait): Grow (40), Defend (35), Steal (25). Values are subject to tuning.

### `select_faction_action(faction, world, active_supporters) -> FactionPlan`

1. Build faction weight dict from FACTION_TRAIT_WEIGHTS.
2. **Defensive auto-Protect:** If `"Defensive"` in `faction.traits` and a threat exists in `faction.domain_primary`, force-select Protect regardless of weights.
3. **High LN Grow boost:** If `faction.leadership_need > 1.5`, add +20 to Grow weight.
4. **Low entrench Grow boost:** If `faction.entrench < 40`, add +15 to Grow weight.
5. Sample from weighted distribution.
6. **Skip check:** 5% chance the faction takes no action this cycle.
7. Return `FactionPlan` with the selected action and level = `faction.floor`.

---

## Focus Mechanics

### `update_focus_scores(unit) -> Unit`

Called during end-of-cycle updates.

**Base decay:**
- `focus_1.score -= 0.5`
- `focus_2.score -= 1.0`

**Revengeful:** decay halved:
- `focus_1.score -= 0.25`
- `focus_2.score -= 0.50`

**Satisfied:** decay increased +0.5:
- `focus_1.score -= 1.0`
- `focus_2.score -= 1.5`

**Depletion:** If score <= 0, set focus slot to None.

**Swap check:** After decay, call `focus_swap_chance()`. If it passes, focus_2 becomes focus_1 and vice versa.

### `add_focus(unit, target_id, score, slot) -> Unit`

- If `slot == 1`:
  - If `focus_1` is None: set `focus_1`
  - If `focus_1` exists and new `score > focus_1.score`: push current to focus_2, set new focus_1
  - If `focus_1` exists and new `score <= focus_1.score`: set focus_2
- If `slot == 2`: set or replace focus_2 directly

---

## Summary: Full NPC Selection Flow

```
unit needs action plans for cycle
  → build_action_weights(unit)
      → BASE_WEIGHTS + trait modifiers + Care/Protect/Leaderless reductions
      → apply_tension_modifier (if focus active and above inertia)
      → apply_relationship_boosts

  → select top actions by weight threshold:
      → 1st: always take highest-weight eligible action
      → 2nd: take if within 5 of 1st
      → 3rd: take if within 8 of 1st
      → skip check: 5% chance each selected action is skipped
      → max 3 actions total

  → for each selected action:
      → determine relevant domain and available level (floor of that domain)
      → calculate L1 cost at chosen level; reduce level if budget exceeded
      → gate check:
          → pass: proceed to target selection
          → fail: redirect (Harm→Expose, others→Grow, Grow→Care)
      → target selection:
          → focus_1.score > inertia? → 3× bias toward focus_1.target
          → elif focus_2.score > inertia? → 2× bias toward focus_2.target
          → else: trait/relationship-biased target selection

  → return List[NPCPlan], one per selected action (max 3)
```
