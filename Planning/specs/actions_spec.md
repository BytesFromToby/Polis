# Actions Specification

**Version:** v5.1
**Date:** 2026-06-03
**Updated:** 2026-06-12 — **Toil added** (public-needs / barley-run); see `public-needs_spec.md`.
**Supersedes:** v4 (2026-05-19)

Demo redesign. Rank is now a float **1.0–10.0** (`level = int(rank)`); `entrench` removed. Health is a **breaking-point buffer**, not a death meter — factions are permanent. **Block removed. Aid added** (cooperation). Harm damages health; Protect is an immediate heal. See `../proposals/demo-redesign.md` and `../reference/formulas.md`.

---

## Action Economy

Each faction takes **one action per cycle**. No budget system, no action levels. Action selection is driven by the faction behavior engine (see `faction-behavior_spec.md`).

---

## Contest Resolution

Contested actions (Harm, Steal) use the same formula:

```
attacker_roll = d20 + floor(attacker.rating)     # floor(rating) = level, 1–10
defender_roll = d20 + floor(defender.rating)
margin = attacker_roll - defender_roll
```

| Margin | Outcome |
|---|---|
| ≥ 5 | Decisive |
| 1–4 | Partial |
| 0 | Tie — defender wins |
| < 0 | Fail |

Leaderless faction penalty: −2 to all rolls. (Open "roll dial": whether to feed raw `rank` instead of `floor(rating)` — deferred; see `formulas.md`.)

---

## Action Set

Six faction actions: **Grow · Protect · Aid · Harm · Steal · Toil**. Project actions (BuildProject / SabotageProject) are retained pending the projects rework — see the bottom of this spec.

### Grow

**Who:** Faction · **Contested:** No

Adds `1 / (level + 1)` to `rank` (`level = int(rank)`). When the new rank crosses an integer, `level` rises by 1 — the **level-up beat** (Dramatic event). Growth decelerates with level (low levels rise fast); see `formulas.md`.

- Rank capped at **10.0**.
- Hard-blocked when `domain.utilization >= domain.cap` (no rank gain that cycle).

**Done when:**
- A successful Grow increases `rank` by `1/(level+1)` for the actor's current level  `[automated]`
- When a Grow pushes `rank` across an integer, `level` increases by exactly 1 and a Dramatic level-up event is recorded  `[automated]`
- Grow produces no rank gain when `domain.utilization >= domain.cap`  `[automated]`
- `rank` never exceeds 10.0  `[automated]`

### Protect

**Who:** Faction · **Contested:** No

Immediately restores the actor's `health` by **50** (capped at 100). No lingering or round-long modifier.

**Done when:**
- Protect raises the actor's `health` by 50, capped at 100  `[automated]`

### Aid

**Who:** Faction · **Target:** an allied faction (`relationship == "Friend"` or an `allied with X` trait) · **Contested:** No

Restores the **target ally's** `health` by **25** (capped at 100). Allowed **across domains** (alliances may span domains).

**Done when:**
- Aid raises the target ally's `health` by 25, capped at 100  `[automated]`
- Aid's only valid targets are Friend / `allied with` factions, and it may target an ally in a different domain  `[automated]`

### Harm

**Who:** Faction · **Target:** a faction in the **same domain**, **not level 1** · **Contested:** Yes

Damages the target faction's `health`:

- Decisive: −30 health
- Partial: −15 health
- Fail: no effect

Health floors at 0. When health reaches 0 the faction **Breaks** (resolution in `cycle-runner_spec.md` — 75% level −1 / 25% leader death; health resets to 75).

**Done when:**
- Harm decisive reduces target `health` by 30; partial by 15; fail leaves it unchanged  `[automated]`
- Target `health` never drops below 0  `[automated]`
- Harm cannot select a level-1 faction as its target  `[automated]`
- Harm targets only factions in the attacker's own domain  `[automated]`

### Steal

**Who:** Faction · **Target:** a faction in the **same domain**, **not level 1** · **Contested:** Yes

Transfers rank from target to actor — **half the attacker's grow increment**: `0.5 / (attacker_level + 1)`.

- Decisive: transfer the full amount
- Partial: transfer half the amount
- Fail: no effect

Actor `rank` gains the amount (capped 10.0); target `rank` loses it (floored at **1.0**).

**Done when:**
- Steal decisive transfers `0.5/(attacker_level+1)` rank from target to actor; partial transfers half that  `[automated]`
- Target `rank` never drops below 1.0 and actor `rank` never exceeds 10.0  `[automated]`
- Steal cannot select a level-1 faction as its target  `[automated]`
- Steal targets only factions in the attacker's own domain  `[automated]`

### Toil

**Who:** Faction with a role in a supply chain (`data/chains.json` — v1: the three aristocracy
estates, the Ovenmen, the Winepressers) · **Contested:** No

The faction works its trade instead of maneuvering. Sets the cycle-only flag
`faction.toiling = True`; the Public-needs step multiplies that faction's chain contribution
(harvest for producers, capacity for processors) by `TOIL_MULT = 1.5` this cycle (see
`public-needs_spec.md`). No rank, health, or project effect — the opportunity cost *is* the
effect: a toiling faction stands still politically.

Toil is a valid `committed_action` deal term (see `audience_spec.md`) — the only way deals
touch supply.

**Done when:**
- A resolved Toil sets `toiling` on the actor and produces no rank or health change  `[automated]`
- Factions with no chain role never select or resolve Toil  `[automated]`
- `committed_action == "Toil"` forces Toil selection for the committed cycles, same as the
  existing committed-action machinery  `[automated]`

---

## Project Actions

*Base projects use the stack model (`projects_spec.md` v6): one `BaseProjectStack` per domain
with a unified `progress` (0–100) on the **top** instance. Both actions resolve against the
**top** of the addressed domain's stack — the only attackable/buildable instance. See
`projects_spec.md` for the authoritative mechanics.*

### BuildProject
**Who:** Faction whose `domain_primary` is the stack's domain · **Target:** the domain's stack top (building) · **Contested:** No — roll `d20 + floor(rating)` vs DC 12. On success `progress += build_step%` (default 25); reaching 100 sets `completed`. Domain-gated. Each successful build this cycle grants +1 defense (max +2).

### SabotageProject
**Who:** Any faction (no domain gate) · **Target:** the domain's stack **top** — including a **building** top (a build site is now attackable, reversing v5) · **Contested:** Yes — attacker vs `d20 + stack_defense_rating (+ build bonus)`, `stack_defense_rating = max(1, int(progress) // 20)`. Decisive −25, partial −10, fail none, applied to `progress`. `progress` floors at 0; `count` drops (destroying the top, revealing a pristine one below) **only** when a hit lands while `progress` is already 0.

---

## Removed Actions

- **Block** (v5) — removed. The hidden delayed-fire trap added cross-cycle timing complexity for little demo value; faction conflict is now Grow / Protect / Aid / Harm / Steal.
- **Recruit** (v4) — faction health growth handled via Protect / Aid and organic events.
- **Obscure / Expose** — human-player mechanics, not needed for AI factions.
- **Support Faction / Seek Leadership / Join / Leave / Kick** — unit-based mechanics; units are gone.
