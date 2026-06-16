# Spec: Public Needs — the Public's state and scales

**Version:** v4
**Date:** 2026-06-12
**Updated:** 2026-06-14 — **fish slice** and **flocks slice**: the city gains a second and third
Food source (the chain math now lives in `food-supply_spec.md`).
**Updated:** 2026-06-16 — **restructure**: the three Food production chains (harvest/fishery/
pastoral + `compute_chain`) were extracted into **`food-supply_spec.md`**. This spec keeps the
Public's *state* — the needs scales, word bands, drift toward the chain's targets, shortage/plenty
consequences, and the cycle step. Retitled off "The Barley Run." (Piety/unrest scales: pending.)
**Proposal:** `../proposals/public-model.md` (the Public's full state model & scales);
`../proposals/resource-chains.md` (production, owned by `food-supply_spec.md`)

The Public is the material center of the city: a real population that eats, drinks, and sickens.
The production chains (`food-supply_spec.md`) convert faction strength into supply **targets**;
this spec owns the Public's needs scales that **drift** toward those targets, so a faction's
decline propagates into shortage and shortage into pressure. It owns population, the need scales,
the word bands, and the cycle step that runs them. The **Toil**/**Withhold** actions are owned by
`actions_spec.md`; behavior weights by `faction-behavior_spec.md`; event gating keys by
`events_spec.md`; the chain math by `food-supply_spec.md`.

All numeric constants in this spec are provisional — tune by feel (same status as the grow
curve in `../reference/formulas.md`). Tests must reference the constants, not bake in copies.

## Scope
- Does: population + `fed`/`happy` scales on `ThePublic`; band tables; consumption and **drift**
  toward the supply targets that `food-supply_spec.md` computes; shortage and plenty consequences
  (health driver, support deltas, population growth/decline); the cycle step that runs the needs
  update.
- Does NOT: the Food production chains themselves (harvest/fishery/pastoral, `compute_chain` —
  now `food-supply_spec.md`); the new Public scales (piety/unrest/consumption — a later slice);
  warehouses, stockpiles, trade values; pop-gated faction levels; Mayor split levers.

## Feature: Public needs state

`ThePublic` (see `special-factions_spec.md`) gains three persisted fields:

| Field | Type | Range | Start (city data) | Meaning |
|---|---|---|---|---|
| `population` | `int` | ≥ 1000 | 20000 | City population; real state with memory |
| `fed` | `int` | 0–100 | 60 | How well the people eat |
| `happy` | `int` | 0–100 | 50 | The people's mood |

`health` (0–100) already exists and is unchanged structurally — this spec gives it a driver.

**Word bands** — defined once, used by the audience prompt, the UI, and event gating
(precedent: `ThePublic.derive_disposition()`):

| Value | `fed` band | `happy` band |
|---|---|---|
| 0–20 | Starving | Miserable |
| 21–45 | Hungry | Sullen |
| 46–75 | Fed | Content |
| 76–100 | Well fed | Festive |

Health has no band table; one threshold: `health < 40` → the people are **sickly**
(descriptor + event gate).

**Drunk** is not an axis. Each cycle the chain reports wine's happiness contribution;
`drunk = (wine_happy / demand) >= DRUNK_THRESHOLD` (0.25). Drunk is an *additional*
descriptor, independent of the happy band ("Well fed, drunk, Miserable" is a valid city).
*(As built: cached on `ThePublic.drunk` purely so the UI/serializer can display it between
cycles — recomputed and overwritten by every needs step; never drifted, never a driver.)*

- Input: city data `special_factions.the_public` (gains `population`, `fed`, `happy`).
- Output: band words + drunk/sickly flags exposed to prompt, UI, and event system.

**Done when:**
- `ThePublic` round-trips `population`, `fed`, `happy` through serialization; absent fields
  default to 20000/60/50 (existing saves load)  `[automated]`
- Band lookup returns the table above exactly at the boundaries (20→Starving, 21→Hungry,
  45→Hungry, 46→Fed, 75→Fed, 76→Well fed; same boundaries for happy)  `[automated]`
- `drunk` is true exactly when wine happiness per demand ≥ `DRUNK_THRESHOLD`; `sickly`
  exactly when `health < 40`  `[automated]`

## The Food production chains → `food-supply_spec.md`

The harvest (barley/wine), fishery (fish), and pastoral (meat) chains — the `compute_chain`
pure function that turns faction strength into `fed_target`/`happy_target` — were extracted to
**`food-supply_spec.md`** in the 2026-06-16 restructure. This spec consumes those targets: the
needs scales below **drift** toward them each cycle.

## Feature: Drift, shortage, and plenty

Each cycle (see Cycle integration) after targets are computed:

1. **Drift:** `fed` and `happy` each move toward their target by at most `DRIFT_STEP = 10`
   (the drift is the granary — one bad cycle dents, only sustained shortage starves).
2. **Health driver** (applied to existing `health`, clamped 0–100):
   Starving → −4/cycle · Hungry → −2/cycle · Well fed → +2/cycle.
3. **Support deltas** (rows added to the table in `special-factions_spec.md`):
   Starving → −5/cycle · Hungry → −2/cycle · Well fed → +2/cycle · Festive → +2/cycle ·
   Miserable → −2/cycle.
4. **Population:** Well fed AND `health ≥ 70` → `population` +2%/cycle (rounded);
   Starving OR `health < 30` → −2%/cycle; otherwise unchanged. Floor at 1000.

- Input: current traits + this cycle's targets.
- Output: updated `fed`, `happy`, `health`, `support` deltas, `population`.

**Done when:**
- A trait 30 points below target rises by exactly `DRIFT_STEP`; one ≤ `DRIFT_STEP` away
  lands exactly on target (no overshoot)  `[automated]`
- Health and support deltas match the band tables above for each fed/happy band  `[automated]`
- Population grows 2% when Well fed and `health ≥ 70`, shrinks 2% when Starving or
  `health < 30`, never drops below 1000, and demand scales with it next cycle (a fed city of
  20k that jumps to 40k with unchanged factions sees `fed_target` halve)  `[automated]`
- *Drunk city* fixture: strong Winepressers + weak Ovenmen (e.g. ratings swapped to 4.0/1.0)
  yields, within 10 cycles, `happy` above and `fed` below their values in the balanced
  baseline city  `[automated]`

## Feature: Cycle integration

A end-of-cycle operation, **"Public needs"** (item 5b), runs in `cycle-runner_spec.md` Full
Orchestration immediately after **active-event effects** (item 5a, which may assert `withholding`)
and **before new-event rolling** — so this cycle's event rolls see this cycle's bands. The
Public's existing processing (item 11) is unchanged and runs later as before. `Faction.toiling`
and `Faction.withholding` are cycle-only state, reset at end of cycle.

Band exposure for events: the needs step publishes the current band words + flags; event
templates gate on them via `trigger_conditions` keys (`max_fed_band`, `min_fed_band`,
`max_happy_band`, `min_happy_band`, `sickly: true`) — key semantics owned by
`events_spec.md`.

**Done when:**
- In a full `run_cycle`, the needs step runs after the action loop and before new-event
  rolling: a cycle that starves the city can unlock a Starving-gated event *that same
  cycle*  `[automated]`
- Sentinel events (no-effect templates, one per fed band, injected by the test) become
  eligible exactly when the Public's fed band matches their gate  `[automated]`
- `Faction.toiling` is always false for every faction after `run_cycle` returns  `[automated]`
- A 60-cycle headless run of the standard city with no Mayor input keeps the fed band at
  Hungry or better for at least 50 of 60 cycles (*stability*)  `[automated]`
- Setting all aristocracy ratings to half their start values produces a fed band at least
  one step lower within 5 cycles of the change (*legibility*); restoring them returns fed
  to the original band within 15 cycles (*recoverability*)  `[automated]`
- The same engineered shortage run with the aristocracy estates under committed Toil keeps a
  strictly higher minimum `fed` than with committed Protect (*Toil matters*). (Two findings
  from build, 2026-06-12: producers, not processors, are the lever in a harvest shortage —
  both processors toiling together merely re-balances an unchanged split; and the control must
  be committed too, because uncommitted hungry estates Toil voluntarily via the prosocial
  shortage weight, by design.)  `[automated]`
- After a cycle, the audience system prompt contains the needs line with the current band
  words, e.g. "The people are Well fed, drunk, and Content." (assembly owned by
  `audience_spec.md`; presence proven here)  `[automated]`
- Watching the UI across a shortage: the needs read clearly (band words visible, change is
  noticeable when bands shift)  `[human-required]`

## Open Questions
- None blocking. Constants are provisional by design; the tuning pass happens against the
  redundancy + dynamics tests.
- Intentional, not a gap: after the fish slice the standard city runs slightly lean (barley +
  fish ≈ demand, with a deliberate ~20% flocks-shaped hole). The flocks/meat source closes it
  in the next slice; until then "Fed, not Well-fed" at rest is expected.
