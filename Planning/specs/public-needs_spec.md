# Spec: Public Needs (The Barley Run)

**Version:** v2
**Date:** 2026-06-12
**Updated:** 2026-06-14 — **fish slice**: the Netmenders become a **second Food source**, giving
the city source redundancy (`../proposals/resource-chains.md` → "Food: three sources, by design";
`../proposals/public-model.md`). Producers can now be **faction-keyed** (not only domain-keyed),
and a chain may be **processor-less** (its raw feeds a need directly). Barley is re-tuned down so
each source is partial — see Feature: The fishery.
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
- Does: population + `fed`/`happy` traits on `ThePublic`; band tables; **two Food sources** —
  the harvest chain (aristocracy → Ovenmen/Winepressers → bread/wine/porridge) and the
  **fishery** (Netmenders → fish, fed directly); consumption and drift; shortage and plenty
  effects (health driver, support deltas, population growth/decline); the cycle step.
- Does NOT: a third Food source (flocks/meat — the next extension after fish); fish processing
  (salting via Tanners — fish feeds `fed` *fresh* this slice); the new Public scales
  (piety/unrest/consumption — a later slice); warehouses, stockpiles, trade values, or any
  persisted goods; pop-gated faction levels; Mayor split levers; title/boon mechanics.

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

## Feature: The harvest chain

A pure function from live faction state to need supply. Derived every cycle, never persisted
(per `../decisions/2026-03-29-no-persistent-derived-fields.md`).

**Chain definitions** live in `data/chains.json` (two chains as of the fish slice: `harvest`
and `fishery`). A chain's `producers` may be keyed by **`domain`** (every faction in it) or by
**`faction_id`** (one specific faction); a chain may have **no processors** (its raw feeds a
need directly via the unprocessed path — see the fishery).

The **harvest** chain (barley + wine):

- **Producers:** every faction with `domain_primary == "aristocracy"` (Eumelidai, Pyrrhidai,
  Skiadai). Each contributes `HARVEST_PER_LEVEL × level` units of raw harvest.
  **`HARVEST_PER_LEVEL = 2`** (re-tuned down from 3 in the fish slice so barley is a *partial*
  Food source — see Feature: The fishery for why).
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

## Feature: The fishery — second Food source (fish slice)

A second chain that gives the city **source redundancy**: the Netmenders land fish that feed
`fed` directly. The design goal (`resource-chains.md` → Food: three sources): **one source out →
Hungry at worst, never Starving from full health; two out → Starving.** Fish only matters if
barley alone is *insufficient* — so `HARVEST_PER_LEVEL` is re-tuned down (3 → 2) to make barley
a partial source, and fish supplies the rest. (Flocks/meat, the third source ~20%, is the next
slice; until then the two sources are tuned to roughly meet demand together, leaving a deliberate
flocks-shaped gap.)

The **fishery** chain in `data/chains.json`:
- **Producer:** keyed by `faction_id == "netmenders"` (one faction, not a domain). Contributes
  `FISH_PER_LEVEL × level` units of raw fish. **`FISH_PER_LEVEL = 3`** (provisional).
- **No processors.** Fish is eaten fresh — its raw feeds `fed` directly via the unprocessed path:
  `fed_supply += fish × FISH_FED_PER_UNIT`, **`FISH_FED_PER_UNIT = 1.0`** (fish is protein; feeds
  like bread). No `happy` contribution.
- **Toil:** the Netmenders are a chain-role faction (they are a producer), so they may Toil; a
  toiling Netmenders contributes `× TOIL_MULT` fish that cycle, like any producer.

All Food chains accumulate into one `fed_supply`; `fed_target = min(100, 75 × fed_supply /
demand)` is unchanged. Constants remain provisional — tune against the redundancy test below.

- Input: live factions (Netmenders level + toiling flag) + `ThePublic.population`.
- Output: fish units folded into `fed_supply` (and the per-path tonnage log gains a `fish` row).

**Done when:**
- `compute_chain` sums a `faction_id`-keyed producer over only that one faction (other factions
  in the Netmenders' domain contribute no fish); a `domain`-keyed producer is unchanged  `[automated]`
- The fishery (no processors) routes all its raw to `fed` at `FISH_FED_PER_UNIT`: raw fish =
  `FISH_PER_LEVEL × netmenders.level`, and `fed_supply` rises by `raw_fish × FISH_FED_PER_UNIT`;
  zero Netmenders level → zero fish  `[automated]`
- A toiling Netmenders contributes `× TOIL_MULT` fish that cycle only  `[automated]`
- Conservation holds per chain: each chain's output units sum to its own raw (harvest: bread +
  wine + porridge = harvest raw; fishery: fish = fish raw)  `[automated]`
- **Redundancy** (dynamics, from the balanced two-source standard city, tolerance bands not exact
  values): both sources running → fed band is **Fed** or better; remove the aristocracy estates
  (barley gone) → fed settles in **Hungry** and never reaches Starving within 30 cycles from the
  Fed start; remove the Netmenders (fish gone) → fed settles in **Hungry**, never Starving;
  remove **both** → fed reaches **Starving**  `[automated]`
- The shipped harvest dynamics (stability, legibility, recoverability, Toil-matters) still pass
  under the re-tuned constants and the added fish source (updated as needed for the two-source
  world)  `[automated]`
- All chain tests reference the named constants (`HARVEST_PER_LEVEL`, `FISH_PER_LEVEL`,
  `FISH_FED_PER_UNIT`), never baked-in literals  `[automated]`

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
