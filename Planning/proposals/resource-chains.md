# Proposal: Resource Chains & Population

**Date:** 2026-06-10 · **Second pass:** 2026-06-12
**Status:** PROPOSAL — incubating. The v1 slice (the barley run) was promoted, **built, and
shipped 2026-06-12** — see `../archive/barley-run.md` (decision record) and
`../specs/public-needs_spec.md` (as-built spec). This doc now holds everything *beyond* v1:
the full resource map, agreed in design discussion 2026-06-12. The first-pass brainstorm is
preserved raw at the bottom.

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

## Piety — the one candidate fourth need

If a fourth Public need is ever added it is **piety** and nothing else. Temples produce it
(sacrifices); low piety gates ominous events (omens, plague *interpretation*, festival
cancellations); it plugs into the stance layer (a disaster in an impious city *means*
something). Resist any fifth.

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

- Adopt piety as the fourth need, or keep Temples on happy only?
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
