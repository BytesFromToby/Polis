# Spec: Food Supply — the production chains

**Version:** v1 (extracted from `public-needs_spec.md` v3, 2026-06-16 restructure)
**Date:** 2026-06-16
**Proposal:** `../proposals/resource-chains.md` (the full resource map)

The production side of the Public's food: a pure function from live faction strength to food
**supply targets**, derived every cycle and never persisted (per
`../decisions/2026-03-29-no-persistent-derived-fields.md`). This spec owns the chain math —
producers, processors, conversion profiles, and the Toil/Withhold contribution modifiers. It
hands its output (`fed_target`, `happy_target`, the per-path tonnage) to `public-state_needs`:
the Public's needs scales drift toward those targets (`public-needs_spec.md` → Drift). The
**Toil**/**Withhold** actions it honors are owned by `actions_spec.md`; event-forced withhold by
`events_spec.md`.

All numeric constants here are provisional — tune by feel (same status as the grow curve in
`../reference/formulas.md`). Tests must reference the constants, not bake in copies.

## Scope
- Does: the three Food sources — the **harvest** chain (aristocracy → Ovenmen/Winepressers →
  bread/wine/porridge), the **fishery** (Netmenders → fish, fed directly), and the **pastoral**
  chain (Eumelidai → meat, fed directly); the `compute_chain` pure function; the Toil (×1.5) and
  Withhold (×0) contribution modifiers; the **Public→production efficiency multiplier** (an input
  scaling food output — defined in `public-needs_spec.md` Feature: The Public→production wire);
  per-chain conservation; demand vs population. `compute_chain` also reports `wine_happy` (the wine
  happiness contribution) so `public-needs` can drive the consumption scale.
- Does NOT: the Public's needs scales, bands, drift, or consequences (those are
  `public-needs_spec.md`); meat processing (butchering, temple sacrifice — meat feeds `fed`
  fresh); wool (a future Goods chain); full per-estate differentiation (the Eumelidai stays a
  *mixed* estate producing both barley and flocks); warehouses, stockpiles, trade values.

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
- **Withhold:** a faction that is withholding this cycle (`faction.withholding` — set by the
  Withhold action or an active event; see `actions_spec.md`, `events_spec.md`) has that same
  contribution multiplied by **0** — it does not appear in this cycle's chain math at all.
  Withhold is checked before Toil; a withholding faction contributes nothing regardless of any
  Toil flag (the two are mutually exclusive actions, but events can force `withholding` onto a
  faction that the engine also flagged `toiling` — Withhold wins).

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

- Input: live factions list + `ThePublic.population` (+ this cycle's Toil and Withhold flags).
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
- A withholding producer contributes 0 harvest and a withholding processor 0 capacity, this
  cycle only; setting `withholding` on a faction that is also `toiling` still yields 0 (Withhold
  wins)  `[automated]`
- *Withhold matters* (the inverted *Toil matters*): a single angry high-level producer that
  withholds drives a strictly **lower** minimum `fed` than the same faction acting normally —
  but source redundancy holds, so one withholder alone never drives the Public to Starving from
  full health (it takes the loss of every Food source, per the redundancy property)  `[automated]`

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
- **Redundancy** — *superseded by the three-source redundancy in Feature: The pastoral chain*
  (once flocks is added, losing fish leaves the city Fed, not Hungry — the resilience gain). The
  two-source property held at the fish slice; the live test (`TestRedundancy`) is the three-source
  version  `[automated]`
- The shipped harvest dynamics (stability, legibility, recoverability, Toil-matters) still pass
  under the re-tuned constants and the added fish source (updated as needed for the two-source
  world)  `[automated]`
- All chain tests reference the named constants (`HARVEST_PER_LEVEL`, `FISH_PER_LEVEL`,
  `FISH_FED_PER_UNIT`), never baked-in literals  `[automated]`

## Feature: The pastoral chain — third Food source (flocks slice)

The Eumelidai ("the well-flocked") raise flocks that feed `fed` directly as fresh **meat** —
the third Food source, completing the three-source redundancy and closing the fish slice's
intentional ~20% lean. Same shape as the fishery: a faction-keyed, processor-less producer.

**Purely additive — barley and fish are unchanged.** The fish slice tuned barley(~50%) +
fish(~30%) to ~80% of demand on purpose, leaving the gap this fills. The three sources now sum
to ≈ demand, so the standard city sits at the top of **Fed** / into **Well-fed**, and the
population treadmill engages (grows while well-fed → demand rises → settles back toward Fed).

**Mixed estate (deliberate interim).** The Eumelidai are an `aristocracy` faction, so they
*still* contribute to the harvest (barley) chain via its `domain: aristocracy` producer **and**
produce flocks via this chain. A great landed house holding both grainfields and herds is
realistic; the clean one-estate-one-food split is deferred to the roster restructure (which
reworks the estates holistically). Rejected for now: making the Eumelidai a flocks-only producer
— it needs a producer-list schema and a multi-constant re-tune, and the estates' sizes
(4/3/2) don't map onto the 50/30/20 source proportions if the biggest estate owns the smallest
source. See the decision log.

The **pastoral** chain in `data/chains.json`:
- **Producer:** `faction_id == "eumelidai"`. Contributes `FLOCKS_PER_LEVEL × level` units of raw
  flocks. **`FLOCKS_PER_LEVEL = 1`** (provisional).
- **No processors.** Flocks feed `fed` directly as fresh meat via the unprocessed path:
  `fed_supply += flocks × MEAT_FED_PER_UNIT`, **`MEAT_FED_PER_UNIT = 1.0`** (meat is protein;
  feeds like fish/bread). No `happy` contribution. Unprocessed `label: "meat"`.
- **Toil:** the Eumelidai are a chain-role faction (producer), so they may Toil; a toiling
  Eumelidai contributes `× TOIL_MULT` flocks that cycle, like any producer.

- Input: live factions (Eumelidai level + toiling flag) + `ThePublic.population`.
- Output: meat units folded into `fed_supply` (the per-path tonnage log gains a `meat` row).

**Done when:**
- The pastoral chain (Netmenders-style: `faction_id` producer, no processors) routes all its raw
  to `fed` at `MEAT_FED_PER_UNIT`: raw flocks = `FLOCKS_PER_LEVEL × eumelidai.level`, and
  `fed_supply` rises by `raw_flocks × MEAT_FED_PER_UNIT`; logs under `units["meat"]`; zero
  Eumelidai level → zero flocks  `[automated]`
- A toiling Eumelidai contributes `× TOIL_MULT` flocks that cycle only; `eumelidai` is in
  `chain_role_faction_ids`  `[automated]`
- Per-chain conservation still holds across all three chains (harvest, fishery, pastoral)  `[automated]`
- Barley and fish output are **unchanged** by this slice — the harvest and fishery chains in
  `data/chains.json` are byte-for-byte the same as the fish slice (additive, no re-tune)  `[automated]`
- **Three-source redundancy** (dynamics, tolerance bands, from a Fed start): all three sources
  running → the standard city sits at **Fed or better** (the fish-slice lean is gone); removing
  the **Netmenders** (fish, ~30%) → the city stays **Fed** (a smaller-source loss is absorbed —
  3-source is more resilient than 2); removing the **aristocracy** producers (barley *and* flocks,
  both produced there) → fed settles in **Hungry**, never Starving within 30 cycles; removing
  **all** food producers (aristocracy + Netmenders) → fed reaches **Starving**  `[automated]`
- The shipped dynamics (stability, legibility, recoverability, Toil-matters) still pass under the
  three-source city  `[automated]`
