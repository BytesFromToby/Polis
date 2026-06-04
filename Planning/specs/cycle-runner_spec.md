# Cycle Runner Specification

**Version:** v1.2
**Date:** 2026-05-19
**Updated:** 2026-05-23 — Documented full orchestration as implemented in `runner.py`; subsystem detail delegated to their own specs.
**Updated:** 2026-06-02 — Retrofitted `Done when:` acceptance criteria at the orchestration level (runner-owned behavior only; subsystem criteria stay in their own specs). No behavior change.

Sequential initiative model. Factions act one at a time in random order. State updates between turns — later factions see what earlier factions did. Replaces the old batch declaration/resolution model.

---

## Cycle Structure

The conceptual phases below describe the core faction loop. `cycle/runner.py` also orchestrates several subsystems whose detailed rules live in their own specs — the full order as implemented is in "Full Orchestration" below.

| Step | Name | Description |
|---|---|---|
| 0 | Treasury | Income, expenditure, debt interest, tax effects |
| 1 | Initiative | Shuffle factions into random turn order |
| 2 | Action Loop | Factions act sequentially; state updates between turns |
| 3 | Project Ticks | Construction progress, completion checks, defense reset |
| 4 | End of Cycle | Traits, chaos, collapses, cooldowns, counters |

## Full Orchestration (as implemented in `cycle/runner.py`)

Operations run in this order each cycle. Items marked → are detailed in another spec.

**Pre-cycle (Step 0):**
1. Recalculate domain utilization from faction weights
2. Treasury step 0 + tax effects → `treasury_spec.md`
4. External threats → `special-factions_spec.md`
5. Mayor actions (submitted before this cycle) → `mayor_spec.md`

**Action loop (Steps 1–2):** sequential initiative resolution (`cycle/resolution.py`)

**End-of-cycle:**
6. State updates, leadership events, faction collapse check (`cycle/end_of_cycle.py`)
7. Collapse cascades (`events/cascades.py`) — power vacuum + chaos when a floor-≥4 faction falls
8. Active game events → `events_spec.md` (`events/event_system.py`)
9. Project ticks + effects → `projects_spec.md`
10. World chaos upheavals (`events/world.py`); roll new random events → `events_spec.md`; tick power vacuums
11. `world.cycle += 1`; Mayor refill / cooldowns / exemptions / commitments / reputation decay → `mayor_spec.md`
12. Moneylender → `special-factions_spec.md`
13. The Public → `special-factions_spec.md`

> Note: `events/cascades.py` + `events/world.py` (mechanical collapse/chaos reactions) and `events/event_system.py` (the scripted/random event deck) are distinct, complementary systems — both run every cycle.

---

## Step 0 — Treasury

Run `process_treasury_step0()`. Applies in order:
1. Tax income (per-domain, excluding exempt factions)
2. Investment maturity check
3. Debt interest
4. Guard payroll
5. Infrastructure maintenance (`2 × active_project_count`)

Then run `apply_tax_effects()`:
- Public reputation delta from domain tax rates
- Exempted faction +5 Mayor reputation per cycle remaining

**Done when:**
- When `treasury` and `mayor` are provided, the treasury step and tax effects run before the action loop and their results are included in the cycle's results; when either is absent, `run_cycle` skips them and still completes  `[automated]`

---

## Step 1 — Initiative

Shuffle all factions whose `status != "destroyed"` into a random order. Store as the cycle's `initiative_order: List[str]` (faction ids). This order is internal — it is not shown in the public log.

**Done when:**
- Only factions with `status != "destroyed"` are placed in `initiative_order` — a destroyed faction never acts and produces no action result for the cycle  `[automated]`
- `initiative_order` is re-rolled every cycle — no ordering is carried over between `run_cycle` calls (there is no persistent initiative advantage)  `[automated]`

---

## Step 2 — Action Loop

Iterate through `initiative_order`. For each faction:

### 2a — Block Check

Before action selection, scan all factions for an active block targeting this faction:

```
blocker = first faction where faction.active_block_target == current_faction.id
```

If a blocker is found:
- Resolve the block contest: `d20 + floor(blocker.rating)` vs `d20 + floor(current_faction.rating)`
- **Decisive:** current faction's action is cancelled this turn — skip to next faction in order
- **Partial:** current faction's action is downgraded this turn — Harm → Grow, Steal → Grow; other actions unaffected
- **Fail:** current faction acts normally
- Block is consumed regardless of outcome: set `blocker.active_block_target = ""`
- Log block result (see Public Log Rules below)

If multiple factions have active blocks targeting the same faction, only the first one in initiative order fires this cycle. Others remain armed.

If the current faction skips their action (5% base chance from behavior engine), the block does not fire — it stays armed.

### 2b — Behavior Engine

Call `select_faction_action(faction, factions, domains, world, projects)` with **current live state**. The behavior engine sees everything that has already happened this cycle. Returns `FactionPlan`.

Apply any downgrade from a partial block before resolving.

### 2c — Action Resolution

Resolve the selected action immediately. Update state. Add `CycleEvent` to the cycle log.

**Project action notes:**
- `BuildProject` success: increment `project.build_actions_this_cycle` — the defense bonus is live for the rest of this cycle
- `SabotageProject`: project defense rating includes build bonus accumulated so far this cycle (`min(2, project.build_actions_this_cycle)`)
- `Block` action: set `faction.active_block_target = target_id`; log as guarded stance with no target named

**Done when:**
- A decisive block cancels the target faction's action that turn — no action result is recorded for it  `[automated]`
- A partial block downgrades the target's action that turn — `Harm` → `Grow` and `Steal` → `Grow`; other action types are unaffected  `[automated]`
- A failed block leaves the target's action unchanged  `[automated]`
- A block is consumed after it fires regardless of outcome — the blocker's `active_block_target` is cleared  `[automated]`
- When two factions hold blocks on the same target, only the first in initiative order fires that cycle; the other stays armed  `[automated]`

---

## Step 3 — Project Ticks

For each project:

**Under construction** (`status == "under_construction"`):
- If `health >= 100` OR `cycles_built >= build_time`: `status → "active"`, `health = 100`; log completion as dramatic event
- Else: `cycles_built += 1`

**Active** (`status == "active"`):
- Apply any ongoing `ProjectEffect` entries to their targets

**All projects:**
- Reset `build_actions_this_cycle = 0`

**Done when:**
- After project ticking, every project's `build_actions_this_cycle` is 0  `[automated]`

> Construction-progress and completion transitions (`under_construction → active`) and effect
> application are owned by `projects_spec.md`; the runner only invokes the project tick here.

---

## Step 4 — End of Cycle

Run in this order:

1. **Trait evolution** — evaluate events from this cycle; add, intensify, or decay traits (see faction-behavior_spec)
2. **Domain utilization** — recalculate `domain.utilization` from current faction ratings
3. **Chaos update** — apply chaos deltas from events; clamp to valid range
4. **Power vacuum check** — decrement `cycles_remaining` on active vacuums; resolve or expire
5. **Faction collapse check** — health ≤ 0 or entrench ≤ 0 triggers collapse event
7. **Mayor cooldowns** — decrement all `mayor.cooldowns` values; remove when 0
8. **Mayor exemptions** — decrement all `mayor.exemptions` values; remove when 0
9. **Cycle counter** — `world.cycle += 1`

**Done when:**
- `world.cycle` increases by exactly 1 per `run_cycle` call  `[automated]`
- N successive `run_cycle` calls leave `world.cycle == N` (starting from 0)  `[automated]`
- Domain `utilization` is recalculated from current faction weights each cycle — no stale value carries over  `[automated]`
- `run_cycle` returns a `CycleResult` whose `events` is a list of `CycleEvent` and whose `faction_actions` is a non-negative count that excludes `Skip` actions  `[automated]`

> Subsystem end-of-cycle detail (trait evolution, chaos, collapse, power vacuums, Mayor
> cooldown/exemption/commitment/reputation ticking) is owned by `faction-behavior_spec.md`,
> `events_spec.md`, and `mayor_spec.md`. The runner's contract is that these run, in this order,
> once per cycle.

---

## Block Persistence

Blocks are stored on the faction model as `active_block_target: str = ""`. They persist until fired. A faction holding one active block and taking a second Block action replaces the existing target silently — no log entry for the replacement.

---

## Public Log Rules

The public log (`CycleEvent` narrative) follows these rules for information visibility:

| Event | Public log shows |
|---|---|
| Faction takes Block action | "[Faction] takes a guarded stance." — no target named |
| Block fires, decisive | "[Blocker] intercepts [Target] — their action is neutralized." |
| Block fires, partial | "[Blocker] disrupts [Target] — they are forced to fall back." |
| Block fires, fail | "[Blocker]'s attempt to intercept [Target] fails." |
| Any other action | Standard action narrative |

The target of a placed Block is never in the public log. It only becomes visible when the block fires.

**Done when:**
- A Block action's public-log `CycleEvent` names no target; the blocked faction's identity appears in a public-log entry only when the block fires  `[automated]`

---

## Cycle-Only State

These fields are set during the cycle and reset at end of Step 3 or Step 4. They are not persisted to the database.

| Field | On | When set | Reset |
|---|---|---|---|
| `build_actions_this_cycle` | `Project` | Each successful BuildProject | Step 3 |
| `action_cancelled` | `Faction` | Block decisive fires | Step 4 start |
| `action_downgraded` | `Faction` | Block partial fires | Step 4 start |
| `unstable_stacks` | `Faction` | Cascade events | Step 4 |

---

## Initiative and Information Asymmetry

Acting earlier in initiative order means acting with less information — you cannot see what later factions will do. Acting later means you see what has already happened (ratings changed, projects damaged or built up, blocks placed).

This asymmetry is intentional and emergent. No mechanical adjustment is made to compensate.

The initiative order is re-rolled every cycle. There is no persistent initiative advantage.
