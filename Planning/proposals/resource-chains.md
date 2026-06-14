# Proposal: Resource Chains & Population

**Date:** 2026-06-10 · **Second pass:** 2026-06-12
**Status:** PROPOSAL — incubating. The v1 slice (the barley run) was promoted, **built, and
shipped 2026-06-12** — see `../archive/barley-run.md` (decision record) and
`../specs/public-needs_spec.md` (as-built spec). This doc now holds everything *beyond* v1:
the full resource map, agreed in design discussion 2026-06-12. The first-pass brainstorm is
preserved raw at the bottom. **Per-faction detail** (every faction's resource job) lives in the
companion `faction-resource-map.md`.

## Problem (unchanged)

Faction health and rank matter only politically; the city has no body to wound. v1 fixed this
for one chain. This proposal maps the rest — every resource must answer: *who produces it,
who processes it, which sink does it land in?*

**Still binding:** this is not a goods simulation. No inventories, no per-good markets, no
trade values. Everything is derived per cycle from faction state (public-needs_spec proved
the pattern).

---

## The three sinks

v1 landed everything on Public needs. The rest of the map should not — sinks, not new gauges:

| Sink | What lands there | Examples |
|---|---|---|
| **Public needs** | fed · happy · health (+ piety, candidate below) | bread, wine, fish, meat |
| **Treasury** | export income — goods become gold | oil, textiles, silver |
| **Capability pools** | what the city can *do* — scales existing math, no new gauges | military strength, build speed, fleet |

Capability pools are how weapons and stone matter without a "weapons gauge": Bronzehands
output scales Military effectiveness; building supplies scale project build speed. Derived
per cycle, same as everything else.

## Food: three sources, by design

Redundancy is the design, not flavor. **Barley, fish, flocks** — so one interruption hurts
and two can destroy:

- **One source out → Hungry at worst, never Starving from full health** (source-level
  porridge-floor philosophy).
- **Two out → Starving within a few cycles.** Destruction requires coordinated anger (two
  factions the Mayor alienated) or anger + catastrophe — always a story, never an accident.
- **Three out → unsurvivable without imports** (the Trade valve, below).

Rough proportions to hit those targets: barley ~50%, fish ~30%, flocks ~20%. These become
dynamics-suite fixtures, like *Toil matters*.

**Differentiate the estates** (data-only change): the Eumelidai are "the well-flocked" —
herds → meat (via Temples' sacrifice or the Tanners' butchering); Pyrrhidai + Skiadai grow
the grain. Each named estate becomes individually load-bearing for a *specific* food: an
angry Eumelidai is a meat crisis.

**Sacrificial meat:** Greeks ate meat at temple sacrifices — so **Temples are a Food
processor** (flocks → sacrifice → meat + happy, + piety if adopted). A temple feud becomes
materially scary.

**Fish:** Netmenders, the designated first extension — second producer, zero new mechanics.

## Withhold — the supply-interruption primitive

Toil's evil twin, and the leverage mechanic. **No warehouses needed**: Toil is a cycle-only
flag at ×1.5; Withhold is the same flag at **×0**. The grain was never stored, so refusing to
deliver it needs no tracking — the faction simply doesn't appear in this cycle's chain math.

- **The leverage already exists:** withholding → shortage → the Public goes Hungry → support
  drains from the *Mayor*. They hold the Mayor's standing hostage. No new machinery.
- **It's their action for the cycle** — same opportunity cost as Toil; they stand still
  politically while squeezing.
- **Rare structurally, not by tuning: base weight 0.** Nothing reaches for it by default.
  Weight comes only from anger (low Mayor reputation, `angry at mayor` traits, fresh
  grievances). Every Withhold is legible as a consequence.
- **Loud:** the log names them ("The Winepressers seal their cellars against the Prytanis").
  Counterplay: Condemn, a rival's Harm, or an audience — the deal that ends a strike is a
  committed action (the existing machinery *is* the settlement).
- **One face of a general primitive:** the flag doesn't care why the contribution is zero —
  faction anger, a deal, **or an event setting it for its duration**. A great storm closes
  the sea → the Netmenders are force-withheld for 3 cycles. This is the material thing
  disasters break (`crisis-and-stance.md` hook), and it's one mechanism for all three causes.
- Implementation seam: the event-effect applier must learn one field (`withholding`); shares
  a slice with the deferred Public-fields applier extension.
- Balance fixture when built: how much pain can *one* angry level-4 producer inflict — the
  inverted *Toil matters* test.

## The rest of the map (era-grounded)

- **Grain import — the era-defining mechanic.** Greek cities could not feed themselves;
  Athens lived on Black Sea grain. Imported grain = a Food source that costs treasury gold,
  flows through Trade (Saltroad carry it, Outland Houses source it, Harborwardens gate it),
  and dies in a blockade. The emergency valve for the three-sources math, the answer to
  "Mayor relief levers," and the best crisis fuel in the design — all one mechanic.
- **Oil** — the most Greek good: food (fed) + lamps/gymnasium (health/happy) + premier
  **export** (treasury). Aristocracy groves → Oil-pressers. Splittable output, same
  "split is the gameplay" pattern as bread/wine.
- **The amphora dependency** — oil and wine *exports* need jars: **Kerameis as a multiplier
  on export income.** Weak potters = the oil sits in the press-house. A humble faction
  becomes invisibly load-bearing for the treasury.
- **Building supplies** — wood + stone **merged into one capability pool** (decided
  2026-06-12; the distinction earns nothing). Stonewrights + Carpenters feed it; it scales
  base-project build speed. Post-disaster rebuilding being slow because "the city is short
  of building supplies" is legible for free. Timber import (Greece was deforested) can ride
  the grain-import mechanic later.
- **Metal** — Bronzehands → contested **tools/weapons split** (Ovenmen/Winepressers pattern):
  tools = chain-wide efficiency multiplier, slowly consumed; weapons = military capability.
- **Ships** — timber → Keelwrights → fleet capability (Oarsworn strength + carrying capacity
  for imports).
- **Textiles** — wool (aristocracy flocks) → Weavers → modest happy + export. **"Clothed" is
  NOT a need** — Greek climate doesn't sell it and every need multiplies bookkeeping. Luxury
  tier (Perfumers, Adorners) → aristocratic happy + export, later.
- **Silver** — Laurion: a mine asset → Silverbench mints → treasury income. Gives the money
  world a production root.

## Public state model (settled 2026-06-14)

The Public's state is **seven tracked scales in three layers.** Not balancing them yet — they
exist as the model. A scale earns a stored slot only if it has a **distinct driver**, a **distinct
consequence**, and **benefits from memory** — and the sharpest filter: *both extremes must do
something, and ideally neither extreme is purely "good."* (Derived descriptors that fail this stay
derived.)

**Layer 1 — Needs (inputs; driven by suppliers; memory/drift):**
- **fed** (food chain) · **happy** (joy: festivals, games, wine) · **health** (driven by fed +
  plague + low consumption) — all shipped in `public-needs_spec.md`.
- **piety** — **adopted.** *Belief is the mechanic; the gods are not.* The engine models whether
  the **people feel the city is in good standing with the heavens**, never whether prayers work —
  every material outcome stays materially caused; belief is the *lens* on it, with real political
  teeth. Temples produce piety (rites/festivals) and **interpret** crises (a plague reads as
  "divine punishment / the Mayor angered the gods" → blame, or "a trial we'll endure" → rallying,
  depending on piety + which temple has the people's ear). Historical anchor: the Athenian plague
  of 430 BC — belief was the decisive political force without the gods being real.
  - *Extremes (neither purely good):* **high** → resilient, the Mayor has religious legitimacy,
    *but* zealotry — temples grow powerful enough to challenge him, scapegoating the impious.
    **low** → brittle, anxious, doom-reading, *but* free of priestly power (cynical, unbound).

**Layer 2 — Standing axes (the political/output layer):**
- **confidence** = the existing `support` (mayor reputation with The Public; −50..+50). *Already
  tracked.* Drives the removal spiral + audience leverage; it is also one of unrest's inputs.
  Distinct from unrest (approval ≠ propensity to riot).
- **unrest** — **promoted** from the too-narrow `disposition` (which only read off support). The
  real scale is the **aggregate of pressure** — hunger + impiety + low confidence + drunken
  volatility — with **memory**, because the City Guard mechanic requires it: the Guard *suppresses
  unrest while the cause festers* (stored value pushed down temporarily). Boils over → riots/crime.
  Structurally it sits **on top of** the needs (output), not beside them (input).

**Layer 3 — The balance-axis (interior optimum — tune to the middle, don't maximize):**
- **consumption** (alcohol) — **adopted.** Driven by wine supply (vine estate → Winepressers /
  Dionysos). Bad at *both* ends, which is what earns it: **low** → more shock-sensitive *and*
  **less healthy** (clean water was a real threat; watered wine was the safe daily drink → too
  little drives health down via bad water). **high** → less work done *and* the City Watch is less
  effective. Two bonuses it delivers: it makes **wine a double-edged good** (joy + safe-drink +
  sloth-if-overdone) and it **differentiates the joy sources** (Dionysos drives joy *through*
  consumption; theater/games drive joy *sober*).

**Derived descriptors (never stored as their own levers):** `disposition` (read off unrest/
confidence), `drunk` (read off consumption — and *feeds* unrest as volatility).

**Design notes carried with the model:**
- **Watch the feedback loop:** if misery drives drinking *and* high drinking cuts output, that's a
  doom spiral (drink → less work → less food → more misery → drink). First cut: consumption tracks
  wine supply only; add drink-to-cope later *with a governor*.
- **Consumption → output is the first Public→production wire.** Today the Public's scales reach
  *outward* (support, events); "high consumption → less work" reaches *back into production*,
  closing the loop. Model it as a single **global efficiency multiplier**, not a per-faction
  tangle, to keep it legible — and balance it carefully (two-way loops are where it gets subtle).
- **The "buy time vs. fix the cause" spine:** festivals (Dionysos), games-event, and the City
  Guard are all *symptom* levers (soothe/suppress now); the real fixes (feed them, raise piety
  honestly, prepare for the disaster) are the hard road. Many ways to mask pressure, few to solve
  it, bills compound.

Per-faction temple/academy layout that produces and interprets piety: see
`faction-resource-map.md` → Roster Decisions (temples 4; academy dissolved).

## What is deliberately NOT a resource

- **The Academy produces advantage, not goods.** Stargazers → navigation (trade/fleet
  multiplier), Sophists/Goldentongues → persuasion (audience/assembly effects), the Grove →
  the stance layer's interpreters. Forcing them into chains flattens the one domain whose
  power should be invisible. The Quillsworn are the economy's *measurement* (tax
  efficiency), not part of it.
- **Warehouses / inventories / trade values** — still rejected; Withhold delivers the
  hoarding fantasy without stock.

## Tuning doctrine: easy mode first

Build the self-balancing city, measure where the balance sits, *then* tighten. The shipped
dynamics suite is the regression net; the strings are all named constants:

| Knob | Current | Tightening effect |
|---|---|---|
| Parity target | 75 | Lower → the same economy feels permanently lean |
| Pop growth | ±2% | Faster → the treadmill outruns yesterday's factions sooner |
| Drift step | 10 | Smaller → shocks land harder, mistakes punish faster |
| Prosocial Toil weight | +25 | Lower → the city stops rescuing itself; the Mayor buys rescues |
| Source proportions | 50/30/20 | How much one Withhold or storm hurts |

Every tightening pass reruns the suite — "tougher" must never silently become "death-spirals
from nothing." Difficulty settings, eventually, are constant presets.

## Sequencing (one new sink or mechanic per slice, never two)

1. **Fish** (Netmenders) — proves the second producer. Zero new mechanics.
2. **Withhold + flocks/estate differentiation** — proves the interruption primitive +
   source redundancy (the storm event rides along).
3. **Grain import** — proves Trade as a sink-crossing valve + the blockade crisis hook.
4. **Oil + amphorae** — proves the treasury sink + the export multiplier.
5. **Building supplies + metal** — proves capability pools.
6. **Piety + sacrifices** — the fourth need, if adopted; pairs with crisis-and-stance.

## Open questions

- ~~Adopt piety as the fourth need?~~ → **resolved: yes, as belief** (see Public state model above).
- Estate differentiation: data-only (chains.json) or does it deserve per-faction `produces`
  fields on Faction?
- Does Withhold cost the withholder anything beyond the forgone action (e.g. Public anger at
  the named faction)? v1 answer: no — visibility + Mayor counterplay is enough; revisit if
  it's spammed.
- Import pricing: flat gold per supply unit, or scaled by scarcity? (Flat first.)

---

## First-pass brainstorm (2026-06-10 — kept raw)

- Population
  - 10-50k ? a lot in the surrounding area.
  - Each faction has a pop requirement per level (Workers)
  - Pop consumes resources, food, clothing, ?Housing?
  - Pop has an attitude about the mayor. -> mayor advancment

- Food chain
  - Raw - Fish, grain, meat
  - fishing -> proccesor -> storage -> consuming
    - Fish -> ?salted? fish
  - Barley -> bread
    - Beer(Meed?)
  - ?Sheep -> butcher

- Goods
  - Olives -> Olive Oil
  - Iron ore -> Iron
    - Weapons
    - Tools (Increases efficencey of all factions, slowly consumed)
  - Wood
  - Spices (Mostly imported, Adds happiness)
  - Stone
  - Warehouses — caps the amount of every resources (superseded: Withhold replaces hoarding
    without stock; warehouses remain rejected)

- Clothing
  - Wool -> clothing
  - ?High end?

- Traders
  - wildcard producers and users. Takes access and producess what is lacking.
  - not always producing what is needed
  - need a trade value per resource (example 1 olive oil = 20 fish) (superseded: imports cost
    flat gold; no per-good exchange rates)

- What do Acedemics and — *(answered in "What is deliberately NOT a resource": they produce
  advantage, not goods)*
