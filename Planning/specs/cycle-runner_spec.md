# Cycle Runner Specification

**Version:** v1.3
**Date:** 2026-05-19
**Updated:** 2026-05-23 — Documented full orchestration as implemented in `runner.py`; subsystem detail delegated to their own specs.
**Updated:** 2026-06-02 — Retrofitted `Done when:` acceptance criteria at the orchestration level. No behavior change.
**Updated:** 2026-06-03 (demo-redesign) — **Block removed** (no delayed-fire trap); **faction collapse + power vacuums removed** (factions are permanent); **Break resolution added**. Domain utilization now = Σ level.
**Updated:** 2026-06-12 (public-needs / barley-run) — **Public-needs step added** as orchestration item 5b; `toiling` added to cycle-only state.
**Updated:** 2026-06-16 (Withhold) — active-event **effect application moved before the needs step** (item 5a; new-event rolling stays after); `withholding` added to cycle-only state.

Sequential initiative model. Factions act one at a time in random order. State updates between turns — later factions see what earlier factions did.

---

## Cycle Structure

| Step | Name | Description |
|---|---|---|
| 0 | Treasury | Income, expenditure, debt interest, tax effects |
| 1 | Initiative | Shuffle factions into random turn order |
| 2 | Action Loop | Factions act sequentially; state updates between turns; Breaks resolve inline |
| 3 | Project Ticks | Construction progress, completion checks, defense reset |
| 4 | End of Cycle | Traits, chaos, cooldowns, counters |

## Full Orchestration (as implemented in `cycle/runner.py`)

Operations run in this order each cycle. Items marked → are detailed in another spec.

**Pre-cycle (Step 0):**
1. Recalculate domain utilization as Σ faction level
2. Treasury step 0 + tax effects → `treasury_spec.md`
3. External threats → `special-factions_spec.md`
4. Mayor actions (submitted before this cycle) → `mayor_spec.md`

**Action loop (Steps 1–2):** sequential initiative resolution (`cycle/resolution.py`); a faction reduced to 0 health **Breaks** inline (see Break Resolution).

**End-of-cycle:**
5. State updates + leadership events (`cycle/end_of_cycle.py`)
5a. **Active game event effects** → `events_spec.md` (`events/event_system.py`
    `process_active_events`) — apply the effects of already-active events and decrement their
    timers. Runs **before** the needs step so a `withhold` event asserts `withholding` on its
    target in time for the chain to read it this cycle (added with Withhold, 2026-06-16).
5b. **Public needs** → `public-needs_spec.md` (drift/consequences) + `food-supply_spec.md`
    (the chain math) — derive the food chains from live faction
    state (honoring `toiling` and `withholding` flags), compute targets vs population, drift
    `fed`/`happy`, apply health/support/population effects.
6. *(none — active-event effect application moved up to 5a)*
7. Project ticks + effects → `projects_spec.md`
8. World chaos upheavals (`events/world.py`); **roll new** random events → `events_spec.md`
    (the *roll* stays after the needs step so band gates see this cycle's freshly-drifted bands)
9. `world.cycle += 1`; Mayor refill / cooldowns / exemptions / commitments / reputation decay → `mayor_spec.md`
10. Moneylender → `special-factions_spec.md`
11. The Public → `special-factions_spec.md`

> Note: `events/world.py` (chaos upheavals) and `events/event_system.py` (the scripted/random event deck) are distinct, complementary systems — both run every cycle.

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

Shuffle **all factions** into a random order (factions are permanent — none are ever removed). Store as the cycle's `initiative_order: List[str]` (faction ids). Internal — not shown in the public log.

**Done when:**
- Every faction is placed in `initiative_order` each cycle  `[automated]`
- `initiative_order` is re-rolled every cycle — no ordering is carried over between `run_cycle` calls (no persistent initiative advantage)  `[automated]`

---

## Step 2 — Action Loop

Iterate through `initiative_order`. For each faction:

### 2a — Behavior Engine

Call `select_faction_action(faction, factions, domains, world, projects)` with **current live state** — the engine sees everything that has already happened this cycle. Returns `FactionPlan`. (5% base chance the faction skips its turn.)

### 2b — Action Resolution

Resolve the selected action immediately. Update state. Add a `CycleEvent` to the cycle log.

**Project action notes:**
- `BuildProject` success: increment `project.build_actions_this_cycle` — the defense bonus is live for the rest of this cycle
- `SabotageProject`: project defense rating includes the build bonus accumulated so far this cycle (`min(2, project.build_actions_this_cycle)`)

If an action reduces a faction's `health` to 0, that faction **Breaks** this turn before the loop continues (see Break Resolution).

**Done when:**
- Each faction resolves exactly one action per turn (or skips); effects are applied to live state before the next faction acts  `[automated]`
- An action that brings a faction's `health` to 0 triggers a Break that same turn  `[automated]`

---

## Break Resolution

A faction **never dies.** When an action (normally Harm) brings a faction's `health` to 0, it Breaks immediately:

1. Roll the consequence:
   - **75% → level −1.** `rank` drops to `(level − 1).0` — the bottom of the lower tier; in-progress fraction lost. **If the faction is already level 1, this branch is a reprieve — no rank change.**
   - **25% → leader death.** The current leader is replaced by an auto-generated leader (new name, fresh traits, empty `personality_notes`); the new leader's `status = "present"` (full strength). *(A `weakened` window was considered but dropped: the leadership flow escalates `weakened`→`absent`→replace, which would turn the recovery window into a leadership crisis — see Deviations_faction-actions-redesign_2026-06-05.md §2.)*
2. `health` resets to **75**.
3. Log a Dramatic Break event (a level drop, or a leadership fall).

Level-1 factions cannot be *targeted* by Harm or Steal (see `actions_spec.md`), so a Break at level 1 only arises from non-aggression sources (e.g. events).

**Done when:**
- A faction whose `health` reaches 0 has `health` reset to 75 the same cycle and is never removed from play  `[automated]`
- On a Break exactly one consequence applies; with a forced roll, the level-drop branch sets `rank = (level−1).0` and the leader-death branch installs a new `present` (full-strength) leader  `[automated]`
- A level-1 faction that Breaks keeps `level == 1` (the level-drop branch is a no-op)  `[automated]`
- Over many forced Breaks the split approximates 75% level-drop / 25% leader-death  `[automated]`

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

> Construction-progress/completion transitions and effect application are owned by `projects_spec.md`; the runner only invokes the project tick here.

---

## Step 4 — End of Cycle

Run in this order:

1. **Trait evolution** — add, intensify, or decay traits from this cycle's events (see faction-behavior_spec)
2. **Domain utilization** — recalculate `domain.utilization` as **Σ faction level**
3. **Chaos update** — apply chaos deltas from events; clamp to valid range
4. **Mayor cooldowns** — decrement all `mayor.cooldowns`; remove at 0
5. **Mayor exemptions** — decrement all `mayor.exemptions`; remove at 0
6. **Cycle counter** — `world.cycle += 1`

**Done when:**
- `world.cycle` increases by exactly 1 per `run_cycle` call  `[automated]`
- N successive `run_cycle` calls leave `world.cycle == N` (starting from 0)  `[automated]`
- Domain `utilization` is recalculated as Σ faction level each cycle — no stale value carries over  `[automated]`
- `run_cycle` returns a `CycleResult` whose `events` is a list of `CycleEvent` and whose `faction_actions` is a non-negative count that excludes `Skip` actions  `[automated]`

> Subsystem end-of-cycle detail (trait evolution, chaos, Mayor cooldown/exemption/commitment/reputation ticking) is owned by `faction-behavior_spec.md`, `events_spec.md`, and `mayor_spec.md`. The runner's contract is that these run, in this order, once per cycle.

---

## Public Log Rules

The public log (`CycleEvent` narrative) shows:

| Event | Public log shows |
|---|---|
| Faction Breaks — level drop | "[Faction] is thrown into disarray and loses ground." |
| Faction Breaks — leader death | "[Leader] of [Faction] falls; [New Leader] takes command." |
| Level-up | "[Faction] rises in influence." |
| Any other action | Standard action narrative |

---

## Cycle-Only State

Set during the cycle and reset at end of Step 3 or Step 4. Not persisted.

| Field | On | When set | Reset |
|---|---|---|---|
| `build_actions_this_cycle` | `Project` | Each successful BuildProject | Step 3 |
| `unstable_stacks` | `Faction` | Cascade events | Step 4 |
| `toiling` | `Faction` | Toil resolution (Step 2) | Step 4 (after the Public-needs step consumes it) |
| `withholding` | `Faction` | Withhold resolution (Step 2) **or** an active `withhold` event (Step 5a) | Step 4 (after the Public-needs step consumes it; an active event re-asserts it next cycle for its duration) |

---

## Initiative and Information Asymmetry

Acting earlier in initiative order means acting with less information — you cannot see what later factions will do. Acting later means you see what has already happened (ranks changed, projects damaged or built up, factions Broken).

This asymmetry is intentional and emergent. No mechanical adjustment compensates for it. The initiative order is re-rolled every cycle; there is no persistent initiative advantage.
