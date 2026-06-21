# Faction Behavior Specification

**Version:** v4.1
**Date:** 2026-06-03
**Updated:** 2026-06-12 — **Toil weights added** (public-needs / barley-run); chain-role gating per `actions_spec.md`.
**Updated:** 2026-06-16 — **Withhold weights added** (resource-chains); base 0, anger-driven (low Mayor standing) per `actions_spec.md`.
**Updated:** 2026-06-16 — **Unrest→crime**: Restless+ public unrest lifts faction `Steal` (public-needs_spec).
**Updated:** 2026-06-17 — **Confidence posture**: low confidence emboldens Harm/Steal, high damps them (public-needs_spec).
**Updated:** 2026-06-21 — **Rally / Agitate weights added**: factions sway the Public's opinion of the Mayor, gated by the faction's standing with the Mayor (see `actions_spec.md`, `../proposals/faction-influence.md`).
**Supersedes:** v3 (2026-05-19)

Demo redesign: **Block removed, Aid added**; entrench-based modifiers gone; aggression targeting now excludes level-1 factions; near-cap logic uses `utilization = Σ level`. Rank is a float 1–10 (`level = int(rank)`). Faction is the sole autonomous agent; behavior driven by personality traits; sequential per-turn with live state.

---

## Overview

The faction behavior engine is called once per faction during the declaration phase. It selects one action and one target for the cycle.

Entry point:

```python
select_faction_action(faction, factions, domains, world, projects) -> FactionPlan
```

The behavior engine is called **per faction per turn** during Step 2 of the cycle, with the **current live state**. It sees ratings, health, entrench, and project status as they stand after all earlier factions have acted this cycle — not a frozen snapshot from cycle start.

---

## Action Selection

### Step 1 — Build Base Weights

Start from default weights:

```python
BASE_WEIGHTS = {
    "Grow":            40,
    "Harm":            20,
    "Aid":             10,
    "Protect":         25,
    "Steal":           20,
    "Toil":            10,
    "Withhold":        0,
    "BuildProject":    15,
    "SabotageProject": 10,
    "Rally":           0,
    "Agitate":         0,
}
```

`Toil` and `Withhold` are only available to factions with a chain role (`data/chains.json`); for
all others their weight is 0 (see `actions_spec.md`). `Withhold` further starts at base weight 0
even *for* chain-role factions — nothing reaches for it by default; it earns weight only from
anger (Step 3). This keeps a strike structurally rare and always legible as a consequence.

`Rally` and `Agitate` (any faction) likewise start at base weight 0 and lift only from the
faction's **standing with the Mayor** (Step 3): a faction the Mayor stands well with reaches for
Rally, a hostile one for Agitate, and the indifferent middle for neither — so swaying public
opinion is always a legible expression of the Mayor↔faction relationship, never default noise.

### Step 2 — Apply Personality Modifiers

For each trait in `faction.traits`, apply modifiers scaled by intensity:

**Intensity multipliers:**

| Intensity | Multiplier |
|---|---|
| slight | 0.5 |
| moderate | 1.0 |
| strong | 1.5 |
| very | 2.0 |

**Trait → action weight modifiers (base, before intensity scaling):**

| Trait | Modifiers |
|---|---|
| `aggressive` | Harm +20, Steal +10 |
| `defensive` | Protect +25, Aid +10, Grow +5 |
| `ambitious` | Grow +25, Steal +15, Harm +5 |
| `paranoid` | Protect +20, Grow −5 |
| `opportunistic` | Steal +20, Grow +15, Harm +10 |
| `expansionary` | Grow +25, Steal +10, Harm +5 |
| `conservative` | Protect +15, Grow +10, Harm −10 |
| `corrupt` | Steal +25, Harm +15, Grow +5 |
| `industrious` | BuildProject +25, Grow +10, Protect +5, Toil +10 |
| `destructive` | SabotageProject +25, Harm +15, Steal +5 |

Relational traits (targeted at a specific faction) apply only when that faction is a valid target:

| Trait | Targeted modifier |
|---|---|
| `distrusts X` | Protect +15 when X is available target |
| `angry at X` | Harm +25, Steal +15 when X is available target |
| `trusts X` | Harm −15, Aid +10 when X is available target |
| `allied with X` | Harm −20, Aid +20 when X is available target |

### Step 3 — Apply State Modifiers

| Condition | Effect |
|---|---|
| `faction.health < 30` | Protect +20, Grow +15, Harm −10 |
| Public `fed` band ≤ Hungry AND faction has a chain role | Toil +25 (the prosocial branch — a desperate city's producers work, or steal, per personality) |
| Public `unrest` band ≥ Restless | Steal += `UNREST_CRIME_WEIGHT` (default 15), scaled up one step at Agitated and again at Boiling — civic disorder is cover for theft (public-needs_spec Unrest). `public` absent → no effect |
| Public `confidence` band (off `support`, public-needs_spec) | **Hostile/Suspicious** → Harm += `CONFIDENCE_EMBOLDEN_WEIGHT` (default 10), Steal += same (a distrusted Mayor can't shield rivals); **Favorable/Beloved** → Harm −= `CONFIDENCE_COOP_WEIGHT` (default 10), Steal −= same (public backing raises the cost of open aggression); Neutral → no change. `public` absent → no effect |
| Faction has a chain role AND the Mayor's standing with it is low (`mayor.get_reputation(faction.id) <= WITHHOLD_ANGER_THRESHOLD`, default −20) | Withhold += `WITHHOLD_ANGER_WEIGHT` (default 40) — a strike is a deliberate, anger-driven act; the angrier signal is the only thing that lifts Withhold off its base of 0. The strength of the anger scales with how far below threshold (one step per −10 below it, so a deeply hostile faction reaches for it harder). `mayor` absent (headless without a player) → no Withhold weight, Withhold stays at 0 |
| Mayor's standing with the faction is high (`mayor.get_reputation(faction.id) >= RALLY_THRESHOLD`, default +20) | Rally += `RALLY_WEIGHT` (default 30), scaled up one step per +10 above threshold (a devoted faction rallies harder). `mayor` absent → no Rally weight (stays 0) |
| Mayor's standing with the faction is low (`mayor.get_reputation(faction.id) <= AGITATE_THRESHOLD`, default −20) | Agitate += `AGITATE_WEIGHT` (default 30), scaled up one step per −10 below threshold — mirrors the Withhold anger gate. `mayor` absent → no Agitate weight (stays 0). A faction in the indifferent middle band (between the two thresholds) reaches for neither |
| `domain.utilization >= domain.cap * 0.9` (utilization = Σ level) | Grow −20, Steal +15 |
| An allied faction is at `health < 50` (Friend / `allied with`) | Aid +25 |
| Project under construction in faction's domain | BuildProject +20 |
| Faction owns a damaged/critical project | BuildProject +30 |
| Rival faction owns a project in faction's domain | SabotageProject +20 |
| Faction has `faction_level` project active | Protect +10 (protect their investment) |

### Step 4 — Select Action

Sample from weighted distribution. 5% chance faction takes no action this cycle (skip).

### Step 5 — Select Target

Target selection for contested aggression (Harm, Steal). **Eligible targets are same-domain and not level 1.**

1. If a relational trait (`angry at`) targets a specific *eligible* faction — weight that faction ×3
2. Foe domain relationship — weight eligible factions in Foe domains ×2
3. Weakest eligible rival in the domain (lowest rank) — baseline
4. Random eligible faction — fallback

If no eligible target exists (e.g. every domain rival is level 1), the aggression is dropped and the engine re-selects (typically Grow or Protect).

**Aid target selection** (allies only — `Friend` or `allied with X`; may be cross-domain):
1. Allied faction with the lowest health — baseline (shore up the most endangered ally)
2. Random allied faction — fallback

If the faction has no ally, Aid is not selected.

Protect and Grow require no target. **Rally and Agitate** likewise require no target — they act on
the Mayor's public standing directly (`mayor.reputation["the_public"]`); see `actions_spec.md`.

**BuildProject target selection:**
1. Prefer projects under construction in faction's domain (highest build progress — closest to completion)
2. Fallback: any active project in faction's domain that has taken damage this cycle

**SabotageProject target selection:**
1. Projects owned (`initiated_by`) by a faction with a hostile relationship — weight ×2
2. Projects in a Foe domain (domain relationship = "foe") — weight ×2
3. Highest-health active project in any domain (most impactful to damage)
4. Random eligible project — fallback

Note: weights 1 and 2 stack if both conditions apply (project owned by hostile faction AND in a Foe domain).
### Output

Returns `FactionPlan` with selected action, target, and domain.

---

## Trait Evolution

At end of cycle, traits may shift based on what happened:

| Event | Trait effect |
|---|---|
| Faction was Harmed | `aggressive` intensity +1 step toward target, or add `angry at X` |
| Faction successfully Harmed target | `aggressive` intensity +1 step (general) |
| Faction Harmed repeatedly by same faction | Add `angry at X` (strong) |
| Faction Grew 3+ cycles in a row | `ambitious` intensity +1 step |
| Faction Protected 3+ cycles in a row | `defensive` or `paranoid` intensity +1 step |
| Faction reached health < 20 | Add `defensive` (moderate) |
| No hostile action for 5+ cycles | Aggressive traits decay 1 intensity step |

Intensity cannot exceed `very`. Traits at `slight` that decay are removed.
Maximum 6 traits per faction at any time — lowest intensity trait dropped if exceeded.

---

## Leader Influence

Leader traits modify faction behavior:

- Each leader trait that matches a faction trait amplifies it by +0.25 intensity step
- Leader traits not in faction list add a weak (+0.25) version of that trait's weights
- Leader `status == "weakened"`: all modifier weights halved
- Leader `status == "absent"`: leader influence removed entirely
