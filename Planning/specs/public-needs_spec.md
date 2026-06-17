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
- Does: population + `fed`/`happy`/**`piety`**/**`unrest`** scales on `ThePublic`; band tables;
  consumption and **drift** toward targets (`fed`/`happy` from `food-supply_spec.md`, `piety` from
  the temple driver here, `unrest` from the pressure aggregate here); shortage/plenty and
  piety/unrest consequences (health driver, support deltas, population, crisis-blame modifier,
  crime/riot gating); the **City Guard** unrest damper; the cycle step that runs the needs update.
- Does NOT: the Food production chains (`food-supply_spec.md`); **consumption** (the alcohol
  balance-axis — the next scale slice); the two Public→production wires (health-output,
  consumption-output); the richer extreme-event deck beyond the flagship few (Witch-Hunt,
  Oracle's Demand, Insurrection — later); warehouses; pop-gated faction levels.

## Feature: Public needs state

`ThePublic` (see `special-factions_spec.md`) gains three persisted fields:

| Field | Type | Range | Start (city data) | Meaning |
|---|---|---|---|---|
| `population` | `int` | ≥ 1000 | 20000 | City population; real state with memory |
| `fed` | `int` | 0–100 | 60 | How well the people eat |
| `happy` | `int` | 0–100 | 50 | The people's mood |
| `piety` | `int` | 0–100 | 50 | Belief the city stands well with the heavens (Feature: Piety) |
| `unrest` | `int` | 0–100 | 10 | Aggregate civic pressure; **low is good** (Feature: Unrest) |
| `consumption` | `int` | 0–100 | 45 | Alcohol consumption; **mid is good** — both ends bite (Feature: Consumption) |

`health` (0–100) already exists and is unchanged structurally — this spec gives it a driver.
`piety`, `unrest`, `consumption` are new persisted scales (round-trip + default like `fed`/`happy`).

**Word bands** — defined once, used by the audience prompt, the UI, and event gating
(precedent: `ThePublic.derive_disposition()`):

| Value | `fed` band | `happy` band | `piety` band | `unrest` band (low good) | `consumption` band (mid good) |
|---|---|---|---|---|---|
| 0–20 | Starving | Miserable | Godless | Placid | Dry |
| 21–40 | Hungry | Sullen | Lax | Quiet | Sober |
| 41–60 | Fed | Content | Observant | Restless | Tempered |
| 61–80 | Well fed* | Festive* | Devout | Agitated | Tipsy |
| 81–100 | Well fed | Festive | Zealous | Boiling | Sodden |

\* `fed`/`happy` keep their existing 4-band tables (boundaries 20/45/75); the 5-row grid above
shows piety/unrest/consumption's 5 bands aligned to the 20% increments of `public-model.md`.
`fed`/`happy` band boundaries are unchanged (still Starving ≤20, Hungry ≤45, Fed ≤75, Well fed).

Health has no band table; one threshold: `health < 40` → the people are **sickly**
(descriptor + event gate). Piety bands gate events and modulate crisis blame; unrest bands gate
crime/riot and feed faction behavior.

**Drunk** is now a *derived descriptor of the consumption band* (Feature: Consumption): the city
is `drunk` exactly while consumption is **Tipsy or Sodden**. It remains independent of the happy
band ("Well fed, drunk, Miserable" is still a valid city) and is cached on `ThePublic.drunk` for
the UI/prompt and read by unrest. (Before the consumption slice, `drunk` was an ad-hoc threshold
on wine; consumption subsumes it — wine now drives the consumption *scale*, and drunk reads off it.)

- Input: city data `special_factions.the_public` (gains `population`, `fed`, `happy`).
- Output: band words + drunk/sickly flags exposed to prompt, UI, and event system.

**Done when:**
- `ThePublic` round-trips `population`, `fed`, `happy`, `piety`, `unrest`, `consumption` through
  serialization; absent fields default to 20000/60/50/50/10/45 (existing saves load)  `[automated]`
- Band lookup returns the table above exactly at the boundaries (20→Starving, 21→Hungry,
  45→Hungry, 46→Fed, 75→Fed, 76→Well fed; same boundaries for happy)  `[automated]`
- Piety band lookup at the 20/40/60/80 boundaries returns Godless/Lax/Observant/Devout/Zealous;
  unrest band lookup returns Placid/Quiet/Restless/Agitated/Boiling; consumption band lookup
  returns Dry/Sober/Tempered/Tipsy/Sodden — all at the same boundaries  `[automated]`
- `drunk` is true exactly when wine happiness per demand ≥ `DRUNK_THRESHOLD`; `sickly`
  exactly when `health < 40`  `[automated]`

## The Food production chains → `food-supply_spec.md`

The harvest (barley/wine), fishery (fish), and pastoral (meat) chains — the `compute_chain`
pure function that turns faction strength into `fed_target`/`happy_target` — were extracted to
**`food-supply_spec.md`** in the 2026-06-16 restructure. This spec consumes those targets: the
needs scales below **drift** toward them each cycle.

## Feature: Drift, shortage, and plenty

This feature covers `fed`/`happy` (the food needs). `piety`, `consumption`, and `unrest` drift by
their own rules (Features: Piety, Consumption, Unrest) within the **same needs step**, in this
order: the food chain computes targets **already scaled by the production-wire efficiency**
(read from the Public's start-of-cycle health/consumption bands) → drift `fed`/`happy` → apply
health/support/population consequences (support penalties scaled by the **piety** crisis-blame
modifier; plus the Dry bad-water health drain) → drift `piety` (+ zealot tax) → drift `consumption`
and set `drunk` → compute `unrest_target`, drift/ease `unrest`, then the City Guard suppression.
(`piety` and `consumption` must settle before `unrest` reads impiety and `drunk`.)

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

## Feature: Piety — the belief need

Belief is the mechanic; the gods are not (`../proposals/public-model.md`). The engine models
whether the **people feel the city stands well with the heavens** — never whether prayers work.
Piety is a need like `fed`/`happy`: temples *produce* it, it drifts, and it has political teeth at
both ends.

**Driver — the temple supply** (mirrors the food chain shape, but lives here, not in
`food-supply_spec.md`, because it produces a Public scale, not food):
- Every faction with `domain_primary == "temples"` contributes `PIETY_PER_LEVEL × level` units of
  piety supply. **`PIETY_PER_LEVEL = 4`** (provisional — tuned so the standard temple roster holds
  piety near Observant at rest).
- `piety_target = clamp(100 × piety_supply / (demand × PIETY_PARITY), 0, 100)`, where
  `demand = population / 1000` and **`PIETY_PARITY = 1.0`** (supply meeting parity-demand sits at
  the top of Observant). Toil/Withhold apply to temple factions here exactly as to food producers
  (a Toiling temple ×1.5 piety supply; a withholding/struck temple ×0 — a priestly strike).

**Bands & both-ends-bite:**
- **Godless (0–20):** crises read as the Mayor's impiety → blame. **Lax (20–40):** unease.
  **Observant (40–60):** stable. **Devout (60–80):** crises reframe as trials the city endures.
  **Zealous (80–100):** the temples are over-mighty and **defy the Mayor** — `support` −1/cycle
  while zealous (high piety is *not* purely good).

**Consequences this slice:**
1. **Crisis-blame modifier:** piety scales the **negative `support` deltas the needs step itself
   applies** (the shortage/health penalties — Starving −5, Hungry −2, Miserable −2, etc.). A
   godless city blames the impious Mayor for the heavens' displeasure; a devout one endures.
   Factor by band: Godless ×`PIETY_BLAME_MAX` (1.5), Lax ×1.25, Observant ×1.0, Devout ×0.75,
   Zealous ×0.75. **Positive** support deltas are unscaled. (Self-contained in the needs step — no
   event-support machinery needed; the flagship events lean on band *gating*, not support effects.)
2. **Feeds unrest:** low piety (Godless/Lax) is a pressure term in the unrest aggregate (below).
3. **Zealot tax:** the −1 `support`/cycle at Zealous, above.

**Drift:** `piety` moves toward `piety_target` by at most `DRIFT_STEP` each cycle (same granary
logic as fed/happy).

**Done when:**
- `piety_supply` sums `PIETY_PER_LEVEL × level` over temple-domain factions only; zero temple
  levels → `piety_target` 0; a Toiling temple contributes ×`TOIL_MULT`, a withholding temple 0  `[automated]`
- `piety` drifts toward `piety_target` by exactly `DRIFT_STEP` when far, lands without overshoot
  when within `DRIFT_STEP`  `[automated]`
- The crisis-blame modifier scales the needs step's **negative** support deltas by the piety-band
  factor (a Starving Godless city loses 1.5× the support a Starving Observant city does; positive
  deltas unscaled)  `[automated]`
- While `piety` is Zealous, `support` decreases by 1/cycle from the zealot tax; at Observant it
  does not  `[automated]`

## Feature: Unrest — the pressure aggregate

Unrest sits **on top of** the needs (`../proposals/public-model.md`): it is the aggregate of
civic pressure, with **memory** — it climbs while causes fester and the City Guard can press it
down without fixing the cause. **Low is good.**

**Driver — the pressure target.** Each cycle compute `unrest_pressure` (0–100) as the sum of
band-keyed pressure terms (provisional weights, all importable constants):

| Source | Condition | Pressure |
|---|---|---|
| Hunger | fed Starving / Hungry | `UNREST_HUNGER` (30) / half (15) |
| Impiety | piety Godless / Lax | `UNREST_IMPIETY` (20) / half (10) |
| Low confidence | `support < 0` | `UNREST_CONFIDENCE × (-support)/50` (max 20) |
| Drunkenness | `drunk` true | `UNREST_DRUNK` (10) |

`unrest_target = clamp(unrest_pressure, 0, 100)`.

**Memory (asymmetric drift):** unrest rises toward a higher target at up to `DRIFT_STEP` (10), but
when the target is *lower* than current unrest it eases by only **`UNREST_EASE` (4)/cycle** — the
cause clears faster than the mood. (So a fed, pious, confident city still takes several cycles to
go from Boiling to Placid.)

**The City Guard lever (costed symptom suppression).** If the `city-guard` faction is present and
the guard payroll was met this cycle (`treasury_spec.md` — skipped payroll → no suppression),
unrest is pressed down by `GUARD_SUPPRESS × city_guard.level` (**`GUARD_SUPPRESS = 3`**) *after*
drift — treating the symptom, not `unrest_target`. **Heavy-handedness costs support:** if that
suppression actually removes ≥ `GUARD_HEAVY_THRESHOLD` (15) of unrest in a cycle, `support`
−`GUARD_HEAVY_SUPPORT` (2) that cycle. So a strong Guard buys calm but a resentful populace.

**Bands & consequences:**
- **Placid (0–20)/Quiet (20–40):** calm. **Restless (40–60):** crime — faction `Steal` weight up
  (`faction-behavior_spec.md`). **Agitated (60–80):** riots loom (event gate). **Boiling
  (80–100):** open riot / revolt events (event gate; the flagship riot below).

**Done when:**
- `unrest_target` equals the summed pressure terms for a constructed state (Starving + Godless +
  `support = −50` + drunk yields `UNREST_HUNGER + UNREST_IMPIETY + 20 + UNREST_DRUNK`, clamped)  `[automated]`
- Asymmetric drift: unrest rises by `DRIFT_STEP` toward a higher target but falls by only
  `UNREST_EASE` toward a lower one  `[automated]`
- With `city-guard` present and payroll met, post-drift unrest is reduced by
  `GUARD_SUPPRESS × level`; with payroll unmet (or no guard) it is not  `[automated]`
- A suppression removing ≥ `GUARD_HEAVY_THRESHOLD` unrest applies the `−GUARD_HEAVY_SUPPORT`
  support cost; a light suppression does not  `[automated]`
- Restless+ unrest raises faction `Steal` weight (proven in `faction-behavior` tests); an
  Agitated/Boiling-gated sentinel event becomes eligible exactly at those bands  `[automated]`

## Feature: Consumption — the alcohol balance-axis

Consumption is the city's drinking, and the model's one **U-shaped** scale: **both ends bite, the
middle is the sweet spot** (`../proposals/public-model.md`). It subsumes the old ad-hoc `drunk`
flag — wine now drives a *scale*, and `drunk` reads off its band.

**Driver — wine supply only (first cut, deliberately).** The food chain reports wine's happiness
contribution (`wine_happy`, see `food-supply_spec.md`); `consumption_target = clamp(100 ×
wine_happy / (demand × CONSUMPTION_PARITY), 0, 100)`, **`CONSUMPTION_PARITY`** tuned so the
standard city sits in **Tempered**. Consumption drifts toward target by `DRIFT_STEP`.
- **No misery→drink feedback this slice.** The doom-loop the proposal warns of (unhappiness raises
  drinking *and* drinking cuts output → spiral) is avoided by tracking wine supply *only*. A
  drink-to-cope term is deferred behind a governor.

**Bands & both-ends-bite:**
- **Dry (0–20):** too little wine → people drink raw water. Bad-water health drain
  (`CONSUMPTION_DRY_HEALTH = −2`/cycle) + the *Wells Sicken* event. (Abstinence causing illness is
  period-true — clean water was the real danger.)
- **Sober (20–40):** fine, a touch brittle. **Tempered (40–60):** the sweet spot.
- **Tipsy (60–80):** work slows — the production wire (below); `drunk` true → feeds unrest.
- **Sodden (80–100):** work largely stops — a heavier production hit; `drunk`; the *Drunken Riot*
  event becomes possible (the consumption+unrest combo).

**Drift:** `consumption` moves toward `consumption_target` by at most `DRIFT_STEP`; then
`public.drunk = consumption_band in (Tipsy, Sodden)`.

**Done when:**
- `consumption_target` tracks `wine_happy` per demand (more wine → higher target; zero wine → 0);
  consumption drifts toward it by `DRIFT_STEP` with no overshoot near it  `[automated]`
- `public.drunk` is true exactly when the consumption band is Tipsy or Sodden (and the old
  wine-threshold `drunk` computation is gone — consumption is the single source)  `[automated]`
- A Dry city loses `CONSUMPTION_DRY_HEALTH` health/cycle (bad water); Tempered does not  `[automated]`

## Feature: The Public→production wire

The first **two-way** loops: the Public's state reaches back into production as one **global
efficiency multiplier** the food chain applies to its output (`food-supply_spec.md`). Read from the
Public's **current** bands (start-of-cycle, before this cycle's drift — the chain runs first):

`efficiency = 1.0 + health_bonus − consumption_penalty`, clamped to `[EFF_MIN, EFF_MAX]` (e.g.
`[0.5, 1.25]`):
- **Health (output↑):** Robust (`health` 61–80) → `+HEALTH_OUTPUT` (0.05); Thriving (81–100) →
  `+2×HEALTH_OUTPUT` — a hale workforce produces more (the user-approved wire).
- **Consumption (output↓):** Tipsy → `−CONSUMPTION_OUTPUT` (0.10); Sodden → `−2×CONSUMPTION_OUTPUT`
  — a drunk city does less work.

Applied to the food chain's supply (the measurable production this slice; extending the multiplier
to other production is future). Magnitudes are provisional and **deliberately small** so the shipped
three-source redundancy and dynamics properties still hold — the wire nudges, it does not dominate.

**Done when:**
- `compute_chain` scales food output by the efficiency multiplier: a Thriving city produces
  strictly more, a Sodden city strictly less, than the same factions at a neutral
  (Healthy/Tempered) Public; a Healthy+Tempered Public yields exactly the un-wired output (×1.0)  `[automated]`
- The efficiency multiplier is clamped to `[EFF_MIN, EFF_MAX]`  `[automated]`
- The shipped three-source redundancy and dynamics (stability, legibility, recoverability,
  Toil-matters) still pass with the wire live (re-tuned/adjusted only as the anticipated coupling
  requires, same discipline as the fish/flocks repairs)  `[automated]`

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
