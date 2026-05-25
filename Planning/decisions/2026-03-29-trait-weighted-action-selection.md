# ADR: Trait-Weighted Action Selection

**Date:** 2026-03-29
**Status:** Accepted

---

## Context

NPCs needed autonomous decision-making. The alternatives considered were:

- **Hand-crafted state machines** — each NPC type has explicit rules (if health < 30 then heal; if enemy in domain then attack). Simple to reason about but inflexible, brittle under novel conditions, and unable to produce emergent faction conflict.
- **Utility scoring systems** — each action scores against the world state and the highest scorer wins. Principled but requires extensive parameter tuning to produce interesting behavior.
- **Probabilistic weighted selection** — each action has a weight derived from the unit's traits; the system samples from the weighted distribution. Produces variable, characterful behavior with minimal tuning, naturally differentiating units with different trait combinations.

The probabilistic approach was chosen because it best supports the goal of emergent conflict: different factions with different trait compositions will naturally develop different behaviors, and adding new traits requires only defining a new weight dict rather than new state machine nodes.

---

## Decision

NPC action selection uses four priority layers, evaluated in order. The first layer that produces a valid action wins.

### Layer 1 — Focus 1 Directed Action

If the unit has a primary focus (`focus_1`) and `focus_1.score > calculate_inertia(unit)`:
- The action is directed toward `focus_1.target_id`.
- The specific action selected is the highest-weight action from TRAIT_WEIGHTS that is applicable to the focus target type.
- Source recorded as `"focus_1"`.

This layer represents a unit actively pursuing a grudge, ambition, or ongoing project. High inertia units require a very intense focus to override their habits.

### Layer 2 — Focus 2 Directed Action

Same as Layer 1, but for `focus_2`. Only reached if `focus_1` is absent or its score does not exceed inertia.
- Source recorded as `"focus_2"`.

### Layer 3 — Trait-Weighted Random

If no focus layer fires:

1. Call `build_trait_weights(unit)` to produce a merged weight dict across all of the unit's traits.
2. Call `apply_tension_modifier(weights, focus_1.score, focus_2.score)` to scale Attack and SpyTargeted weights based on total focus tension.
3. Apply domain relationship boosts from `RELATIONSHIP_ACTION_BOOSTS` for any Foe, Friend, Client, or Hide relationships the unit has.
4. Sample one action from the weighted distribution.
5. Source recorded as `"trait"`.

### Layer 4 — Wildcard Override

After Layer 3 selects an action, there is a 4% chance of discarding that selection and choosing a random action from the full action list (uniform distribution, no weights).
- Source recorded as `"wildcard"`.
- The wildcard fires independently of whether focus layers were available — it can override a focus-driven selection. This represents erratic, unpredictable behavior.

---

## Trait Weight Merging

`build_trait_weights(unit)` operates as follows:

1. For each trait in `unit.traits`, retrieve the weight dict from `TRAIT_WEIGHTS`. If the trait is not in `TRAIT_WEIGHTS`, skip it.
2. Collect all matched trait dicts.
3. For each action in the union of all action names:
   - Sum the weights across all matched dicts (treating missing entries as 0).
   - Divide by the number of matched trait dicts (not the number of traits) to get the average.
4. For any action not covered by any trait dict, use the `DEFAULT_WEIGHTS` value.
5. Apply health-based Rejuvenate boost after merging (not before).

The averaging step prevents a unit with many matching traits from having runaway weights on shared actions. A unit with Expansionary + Ambitious both boosting Grow will have a higher Grow weight than a unit with only one of those traits, but not double.

---

## Gate Enforcement

Certain actions require prerequisites. When the NPC system selects an action that fails its gate check, it redirects to a prerequisite action rather than failing silently.

| Action | Gate | Redirect |
|---|---|---|
| Attack | Target must have been spied (spy gate) | SpyTargeted on same target |
| Entrench | Unit `floor(primary_rating) >= 2` | Grow |
| SeekLeadership | Unit is in a faction with vacancy or LN met | Grow |

Gates are checked after action selection. The redirect action is injected into the NPCPlan and the original action is replaced. Source remains the same as the original selection.

---

## Consequences

### Positive

- **Emergent faction conflict** arises naturally from trait compositions. An Expansionary faction and a Cautious faction occupying the same domain will have opposing behaviors without any script.
- **The tension mechanic** creates escalating behavior: as focus scores accumulate through conflict, the ×1.5 and ×2.0 multipliers on Attack and SpyTargeted push units toward confrontation. Conflict breeds more conflict.
- **Domain relationships create a city-wide behavioral ecology.** Foe relationships cause units in opposing domains to preferentially attack across domain lines. Hide relationships cause units to avoid visibility in certain domains. These behavioral biases emerge from the relationship graph, not from explicit scripts.
- **Adding traits is cheap.** A new trait requires only a new entry in `TRAIT_WEIGHTS`. No state machine changes needed.

### Negative

- **No guarantee of specific behaviors.** A Revengeful unit with high focus will usually attack its target, but the 4% wildcard means it might not. This is by design but can be frustrating to reason about when debugging a specific run.
- **Balance is emergent, not designed.** Trait weight values require playtesting to produce interesting outcomes. Miscalibrated weights (e.g., all traits having high Protect weight) can produce static, non-conflicting simulations.
- **Gate redirects can chain.** If a unit has no valid spy targets and no valid grow target, the gate redirect chain may exhaust all valid actions and fall back to Rejuvenate or a passive action. This edge case should be handled explicitly in the NPC engine rather than failing silently.
