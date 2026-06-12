# Spec: Public Needs (The Barley Run)

**Version:** v1
**Date:** 2026-06-12
**Proposal:** `../proposals/barley-run.md` (v1 slice of `../proposals/resource-chains.md`)

The Public becomes the material center of the city: a real population that eats, drinks, and
sickens. One production chain — the harvest chain — converts faction strength into the Public's
needs, so a faction's decline propagates into shortage and shortage propagates into pressure.
This spec owns population, the need traits, the word bands, the chain math, and the cycle step
that runs them. The **Toil** action it enables is owned by `actions_spec.md`; behavior weights
by `faction-behavior_spec.md`; event gating keys by `events_spec.md`.

All numeric constants in this spec are provisional — tune by feel (same status as the grow
curve in `../reference/formulas.md`). Tests must reference the constants, not bake in copies.

## Scope
- Does: population + `fed`/`happy` traits on `ThePublic`; band tables; the harvest chain
  (aristocracy → Ovenmen/Winepressers → bread/wine/porridge); consumption and drift; shortage
  and plenty effects (health driver, support deltas, population growth/decline); the cycle step.
- Does NOT: any second chain (fish is the designated extension, not in v1); warehouses,
  stockpiles, trade values, or any persisted goods; pop-gated faction levels; Mayor split
  levers; title/boon mechanics (parked for elections-and-titles).

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

**Drunk** is not stored. Each cycle the chain reports wine's happiness contribution;
`drunk = (wine_happy / demand) >= DRUNK_THRESHOLD` (0.25). Drunk is an *additional*
descriptor, independent of the happy band ("Well fed, drunk, Miserable" is a valid city).

- Input: city data `special_factions.the_public` (gains `population`, `fed`, `happy`).
- Output: band words + drunk/sickly flags exposed to prompt, UI, and event system.

**Done when:**
- `ThePublic` round-trips `population`, `fed`, `happy` through serialization; absent fields
  default to 20000/60/50 (existing saves load)  `[automated]`
- Band lookup returns the table above exactly at the boundaries (20→Starving, 21→Hungry,
  45→Hungry, 46→Fed, 75→Fed, 76→Well fed; same boundaries for happy)  `[automated]`
- `drunk` is true exactly when wine happiness per demand ≥ `DRUNK_THRESHOLD`; `sickly`
  exactly when `health < 40`  `[automated]`

## Feature: The harvest chain

A pure function from live faction state to need supply. Derived every cycle, never persisted
(per `../decisions/2026-03-29-no-persistent-derived-fields.md`).

**Chain definition** lives in `data/chains.json` (one chain in v1):

- **Producers:** every faction with `domain_primary == "aristocracy"` (Eumelidai, Pyrrhidai,
  Skiadai). Each contributes `HARVEST_PER_LEVEL × level` units of raw harvest
  (`HARVEST_PER_LEVEL = 3`).
- **Processors:** `ovenmen` and `winepressers`. Each has capacity
  `CAPACITY_PER_LEVEL × level` units (`CAPACITY_PER_LEVEL = 6`).
- **Split:** if total capacity ≥ raw, processors take raw in proportion to capacity; else
  each processes its full capacity and the remainder is eaten as **porridge**.
- **Toil:** a faction that Toiled this cycle (see `actions_spec.md`) has its contribution —
  harvest for producers, capacity for processors — multiplied by `TOIL_MULT = 1.5`.

**Conversion profiles** (per unit of raw processed):

| Path | fed value | happy value |
|---|---|---|
| Bread (Ovenmen) | 1.0 | 0 |
| Wine (Winepressers) | 0.15 | 0.6 |
| Porridge (unprocessed) | 0.4 | 0 |

**Consumption:** `demand = population / 1000` (float). Targets:
- `fed_target = min(100, 75 × fed_supply / demand)` — supply exactly meeting demand sits at
  the Fed/Well-fed boundary; surplus pushes toward 100.
- `happy_target = clamp(BASE_HAPPY + 75 × happy_supply / demand, 0, 100)`, `BASE_HAPPY = 30`.

- Input: live factions list + `ThePublic.population` (+ this cycle's Toil flags).
- Output: `fed_target`, `happy_target`, `wine_happy`, per-path tonnage for the cycle log.

**Done when:**
- Chain output is computed by a pure function (no state mutation); calling it twice on the
  same state returns identical results  `[automated]`
- Raw harvest equals `Σ HARVEST_PER_LEVEL × level` over aristocracy factions; zero
  aristocracy levels → zero raw → both processors produce nothing regardless of strength
  (*dead estates* fixture)  `[automated]`
- With raw > total capacity, each processor processes exactly its capacity and the remainder
  converts at the porridge rate; with raw ≤ total capacity, the split is proportional to
  capacity and nothing is left over  `[automated]`
- Conservation: bread units + wine units + porridge units = raw harvest, exactly  `[automated]`
- With no processors (*porridge floor* fixture) `fed_supply` degrades to `0.4 × raw` but is
  nonzero whenever raw is nonzero  `[automated]`
- A Toiling producer contributes ×1.5 harvest and a Toiling processor ×1.5 capacity, this
  cycle only  `[automated]`

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

A new end-of-cycle operation, **"Public needs"**, runs in `cycle-runner_spec.md` Full
Orchestration immediately after state updates (item 5) and **before** active/new event
processing (items 6/8) — so this cycle's event rolls see this cycle's bands. The Public's
existing processing (item 11) is unchanged and runs later as before. `Faction.toiling` is
cycle-only state, reset in Step 4 alongside `unstable_stacks`.

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
- The same engineered shortage run with a forced Winepressers+Ovenmen Toil each cycle keeps
  a strictly higher minimum `fed` than the run without Toil (*Toil matters*)  `[automated]`
- After a cycle, the audience system prompt contains the needs line with the current band
  words, e.g. "The people are Well fed, drunk, and Content." (assembly owned by
  `audience_spec.md`; presence proven here)  `[automated]`
- Watching the UI across a shortage: the needs read clearly (band words visible, change is
  noticeable when bands shift)  `[human-required]`

## Open Questions
- None blocking. Constants are provisional by design; first tuning pass happens against the
  dynamics tests.
