# Actions Specification

**Version:** v4
**Date:** 2026-05-19
**Supersedes:** v3 (2026-05-17)

Units removed. Simplified action set. Recruit removed. BuildProject and SabotageProject added. Harm restricted to same domain. Project defense system added.

---

## Action Economy

Each faction takes **one action per cycle**. No budget system. No action levels.

Action selection is driven by the faction behavior engine (see `faction-behavior_spec.md`).

---

## Contest Resolution

All contested actions use the same resolution formula:

```
attacker_roll = d20 + floor(attacker.rating)
defender_roll = d20 + floor(defender.rating)
margin = attacker_roll - defender_roll
```

| Margin | Outcome |
|---|---|
| ≥ 5 | Decisive |
| 1–4 | Partial |
| 0 | Tie — defender wins |
| < 0 | Fail |

Leaderless faction penalty: −2 to all rolls.

---

## Action Set

### Grow

**Who:** Faction
**Contested:** No

Rating advances by `grow_increment(floor(rating))` and health increases by `3` (capped at 100).

```
grow_increment(n) = 1 / (2^n + 1)
```

| Floor (N) | Increment |
|---|---|
| 1 | 0.333 |
| 2 | 0.200 |
| 3 | 0.111 |
| 4 | 0.059 |

Rating capped at 5.0. Hard-blocked when `domain.utilization >= domain.cap`.

Floor advance requires `entrench >= 50`. A faction that clears the rating threshold but has low entrenchment stays at its current floor until it consolidates.

**CycleEvent:** Dramatic on floor advance.

---

### Harm

**Who:** Faction
**Target:** Faction in the same domain as the attacker
**Contested:** Yes

On decisive: target loses `0.25` rating and `10` entrench.
On partial: target loses `10` entrench only.
On fail: no effect.

Rating cannot drop below 1.0. Entrench floors at 0.

**CycleEvent:** Dramatic on rating damage.

---

### Block

**Who:** Faction
**Target:** A specific faction — hidden from public log
**Contested:** Yes — fires when target next acts

When a faction takes Block, it sets a standing trap against a chosen target. The public log shows only that the faction has taken a guarded stance — the target is never named until the block fires.

The block persists across cycles until it fires. A faction can hold only one active block at a time; taking a new Block action replaces the existing target silently.

**Timing:** At the start of the target's turn (in any cycle), the block fires before they select their action:

- Decisive: target's action this turn is cancelled
- Partial: target's action downgraded — Harm becomes Grow, Steal becomes Grow; other actions unaffected
- Fail: target acts normally

Block is consumed after firing regardless of outcome. If the target skips their action (5% chance), the block does not fire.

**Public log:**
- When placed: *"[Faction] takes a guarded stance."*
- When fired (any outcome): *"[Blocker] intercepts [Target]..."* — target is now visible

**CycleEvent:** Dramatic on decisive.

---

### Protect

**Who:** Faction
**Contested:** No

Increases entrench by `10` (capped at 100) and health by `5` (capped at 100).
Creates a defensive modifier for this cycle: incoming Harm reduced by one outcome tier (decisive → partial, partial → fail).

**CycleEvent:** Not dramatic.

---

### Steal

**Who:** Faction
**Target:** Faction in the same domain as the attacker
**Contested:** Yes

On decisive: actor +0.20 rating, target −0.20 rating.
On partial: actor +0.10 rating, target −0.10 rating.
On fail: no effect; target alerted (relational trait may shift).

Rating floors at 1.0. Steal cannot push a faction below floor 1.

**CycleEvent:** Dramatic on decisive.

---

### BuildProject

**Who:** Faction whose `domain_primary` is in the project's `domains` list
**Target:** A project with `status == "under_construction"` or `status == "active"`
**Contested:** No — roll d20 + floor(rating) vs DC 12

On success: project `health += 100 / project.faction_build_actions` (construction progress).
On fail: no effect.

**Defense bonus:** Each successful BuildProject on a project this cycle grants it +1 to its defense rating for that cycle, capped at +2 total across all build actions. This makes actively-maintained projects harder to sabotage.

**CycleEvent:** Dramatic on construction completion.

---

### SabotageProject

**Who:** Any faction (no domain restriction)
**Target:** Any project with `status == "under_construction"` or `status == "active"`
**Contested:** Yes — attacker rolls d20 + floor(rating) vs project defense roll

**Project defense rating:**

```
project_defense_rating = max(1, project.health // 20)
```

| Health | Defense Rating |
|---|---|
| 81–100 | 5 |
| 61–80 | 4 |
| 41–60 | 3 |
| 21–40 | 2 |
| 1–20 | 1 |

Plus any BuildProject defense bonus earned this cycle (+1 per success, max +2).

Project rolls: `d20 + project_defense_rating`.

On decisive: project health −25.
On partial: project health −10.
On fail: no effect.

If project health reaches 0: status → `destroyed`, removed from play.

**CycleEvent:** Dramatic on decisive.

---

## Removed Actions

The following actions are removed:

- **Recruit** (v4) — removed; faction health growth handled via Grow and organic events
- Obscure — human player mechanic, not needed for AI factions
- Expose — same
- Support Faction — unit-based pooling mechanic, units are gone
- Seek Leadership — replaced by faction leadership events
- Join / Leave / Kick — unit membership actions, units are gone
