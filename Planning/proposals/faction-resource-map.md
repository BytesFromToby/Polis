# Proposal: Faction → Resource Map

**Date:** 2026-06-14
**Status:** PROPOSAL — incubating. The per-domain tables below are the **first pass** (all 41
factions). The **Roster Decisions** section directly under this is the resolved design intent
from the 2026-06-14 cut-test discussion — **design intent only, nothing built yet.** All seven
domains are now settled (the Public's scale model + the piety decision live in
`public-model.md`). Companions: `resource-chains.md` and `public-model.md`.

## Purpose

Run the cut-test across the whole roster: give each faction a resource job, then the overlaps
(merge candidates) and blanks (set-dressing) reveal themselves. Edit freely — the **Notes**
column is yours.

**Sinks** (from `resource-chains.md`): FOOD (fed) · JOY (happy) · HEALTH · PIETY ·
**$** (treasury/export) · MIL (security) · BUILD · FLEET · KNOW (knowledge/efficiency/sensor).

Ratings shown are current starting `rating` in `data/factions.json`.

---

## Roster Decisions — 2026-06-14 (design intent, NOT built)

Resolved in discussion. Net: **41 → 28 factions, 9 → 7 domains** (trade and academy deleted;
`civic` is the faction-less treasury domain). No data/code touched yet.

**Resulting domains:** aristocracy (4) · guilds (9) · Port (4) · military (3) · professions (4) ·
temples (4) · civic (0, faction-less) — academy and trade dissolved.

### Aristocracy — 3 → 4 (one add)
- **Split Skiadai into two estates** to complete the Mediterranean triad (grain / wine / oil +
  herds): a **vine estate** (grapes → Winepressers; keep the Skiadai "shadowed" name) and a new
  **olive estate** (olives → Oil-pressers, the export spine).
- The olive estate is the **stronger** of the two (it feeds the most important chain on the
  board); the vine estate is modest. Differentiation is data-only in `chains.json`.
- Estates: Eumelidai (flocks → meat + wool) · Pyrrhidai (grain) · vine estate (grapes) · olive
  estate (olives).

### Guilds — 10 → 9 (one merge)
- **Stonewrights + Carpenters → "the Builders"** — one faction making **building supplies**
  (BUILD), derived **directly from strength, no raw chain** (capability pools go direct; reserve
  chains for FOOD + flagship goods).
- **Keelwrights kept, distinct** — ships → FLEET, also direct-from-strength (no input). It is the
  **gatekeeper on fleet recovery**: no shipwrights → no replacing a smashed fleet even with gold.
  (Justified because ships are *destroyable assets with a rebuild loop*; building supplies are a
  flow, which is why that one merged.)

### Military — 4 → 3 (cut + restructure), framed by who they face
- **City Guard** (inward) — the day-to-day lever on the Public: suppresses **anger / crime**.
  *Costed suppression, not a free anger-eraser* — treats the **symptom (unrest), not the cause
  (hunger)**, so leaning on it while the city starves buys time and the bill comes due bigger.
  Ties to the existing **20g/cycle guard payroll** (skip payroll → Guard weakens). Double-edged:
  heavy-handed guarding costs support.
- **Army** (outward, land) — the threat-absorber. Idle day-to-day, critical on events.
- **Fleet** (outward, sea) — protects the import lifeline (Oarsworn). Idle day-to-day, critical
  on events.
- Collapses Shieldsworn / Free Spears / Companions into Guard + Army. The **mercenary
  gold-for-force** lever survives as a *hire-mercenaries property on the Army*, not a faction.
- **Army/Fleet "insurance" only works with telegraphing** → pairs with the oracle (Bright Order):
  foresight makes standing forces an investable bet, not a blind tax.
- *(Parking lot, later: a strong Army/Guard becomes a coup risk to the Mayor.)*

### Harbor + Trade → **"Port"** — 9 → 4 (domain deleted + cuts)
- **Trade domain eliminated.** Harbor renamed **Port** = the whole maritime-commerce bloc and the
  city's economic center of gravity. Domain count 9 → 8 (Agora base-project folds into the Port
  stack; domain relationships rewire).
- **Netmenders** — unchanged (fish → FOOD, the designated next slice).
- **Dockhands** (merged Quaymen + Harborwardens) — **the pipe**: capacity + **customs income** +
  the **import gate**. A multiplier / chokepoint, not a producer; neglect throttles imports and
  export revenue.
- **Trading faction** (merged Amphora + Saltroad + Outland) — all sea trade: **export ($)** +
  **import (the grain lifeline)**. The most-courted faction; sits mid-chain (Dockhands gate →
  Trading → Fleet escort), so not omnipotent.
- **Storehouse Ring** — the **resilience knob**: sets how deep the granary/drift buffer runs
  (reuses the shipped public-needs drift mechanic — no inventory state). **Relationship-conditional**:
  *buffers* you if courted (releases stock in famine), *hoards* if alienated (the Withhold villain).
- **Cut: Stallmongers** (last-mile distribution assumed). **Cut: Silverbench** (see professions).
- Keep merchant-vs-labor class friction at the **faction level** (Storehouse Ring speculators vs
  Dockhands laborers as rivals), since it's no longer a domain-vs-domain split.

### Professions — 6 → 4 (two cuts)
- **Cut Adorners** — redundant luxury export *and* orphaned input (no silver/gems producer once
  Silverbench is gone). **Keep Perfumers** as the olive chain's luxury terminus.
- **Cut Garland-Chasers → games become an EVENT** (faction teams compete for prizes → Public joy
  spike + faction-standing shuffle + **Mayor sponsorship = bread & circuses**, a distract-from-hunger
  lever). *Rich version waits on the event-applier reaching faction rep — a known follow-up; the
  joy-spike version works today.*
- **Keep Quillsworn** — the **sensor**: public revenue + records (play **blind** without it).
  Absorbs Silverbench's bookkeeping/money-changing.
- **Silverbench cut**: its adversarial-creditor mechanic already lives in the (dormant) special
  **Moneylender**; bookkeeping → Quillsworn; money-changing → assumed. *Later, if finance revives,
  prefer a **political** creditor (negotiable, plays the faction web) over the faceless external timer.*
- Professions lands at: Asklepiads (HEALTH, sole healer) · Players (JOY, steady) · Quillsworn
  (money + records + sensor) · Perfumers ($ luxury export). Joy now has three *profiles*: Players
  (steady) · Raving Choir (risky) · games-event (periodic).

### Temples — 5 → 4 (PIETY adopted; belief is the mechanic, the gods are not)

**Piety is adopted as a Public need** (see `public-model.md`). Belief is
the system; the gods never reach into physics — temples *produce* piety (rites/festivals) and
*interpret* crises. Every effect below is re-grounded as human/morale/interpretation, not a divine
buff. Each god maps to a distinct, now-live scale:

| Faction (god) | Re-grounded mechanic | Touches |
|---|---|---|
| **Greenmantle** (Demeter) | Harvest cult organizes the planting calendar + farmer morale → a *human* multiplier on food yield | FOOD + piety |
| **Bright Order** (Apollo, **+ absorbed Stargazers**) | The oracle **and** the heaven-readers: foresight (the SENSOR that telegraphs events → makes Army/Fleet investable) + practical sky-knowledge (navigation→FLEET, planting calendar→FOOD timing) | sensor + FLEET/FOOD-mult + piety |
| **Raving Choir** (Dionysos) | The cathartic **unrest-release valve** — festivals bleed off tension now, but drive **consumption** up and risk chaos (double-edged) | unrest + consumption + happy + piety |
| **Tidesworn** (Poseidon) | Keeps sailors *willing to sail*; **frames sea-disasters** (impiety-blame vs fatalism), tied to the Port/grain lifeline | piety + sea-disaster interpretation |

- **Stargazers merged into Bright Order** — the oracle and the astronomers both "read the heavens";
  the merge kills the sensor-duplication *and* absorbs academy's only present-value faction.
- **Hearthwardens (Hestia) — CUT.** Vaguest faction on the board; its only candidate mechanic
  (non-coercive unrest-damping) overlaps the City Guard. *Optional revival only if a belief-based
  unrest damper distinct from coercion is wanted — the hearth calms without the truncheon.*

### Academy — DELETED as a domain (like trade → Port)

No domain-worthy core remains once the sensor moves to Apollo. Dissolved:
- **Stargazers** → absorbed into Bright Order (above).
- **Grove** (stance interpreters) → **parked**; returns with the stance layer, likely as a
  stance-layer *function*, not a domain faction.
- **Goldentongues** (assembly orators) → **parked**; returns with elections, placed with
  **governance/the assembly**, not a revived academy.
- **Sophists** → **cut outright** (thinnest; no home the others don't cover).
- Principle: future-system factions return **placed by function**, not by reviving a soft-power domain.

### Principles affirmed this pass
- **Capability pools (MIL / BUILD / FLEET) derive directly from faction strength** — no raw
  chains. Raw→process chains are reserved for FOOD and flagship export goods.
- **The "buy time vs. fix the cause" spine:** City Guard (suppress unrest), games (distract from
  hunger), Toil/Withhold (delay). Many ways to mask pressure, few to solve it, bills compound.
- **Don't keep factions alive on future promises** — the roster tracks built mechanics, not the roadmap.
- **Events are the catch-all for "fun things"** and will carry more over time (games are the first
  faction-cut handed to the event layer).

---

## Aristocracy — the land (raw producers)
Differentiate the three estates so each owns a specific raw (data-only change in `chains.json`).

| Faction | r | Role | Produces | Sink | Notes |
|---|---|---|---|---|---|
| Eumelidai | 4 | "the well-flocked," herds | flocks → meat + wool | FOOD + raw for Tanners/Weavers |  |
| Pyrrhidai | 3 | fire-blooded, ambitious | grain (barley) | FOOD (raw for Ovenmen) |  |
| Skiadai | 2 | the shadowed | vines + olives | raw for Winepressers + Oil-pressers |  |

---

## Guilds — the processors (richest domain, 10 deep)

| Faction | r | Converts | Into | Sink | Notes |
|---|---|---|---|---|---|
| Ovenmen | 2 | barley | bread | FOOD |  |
| Winepressers | 2 | grapes | wine | JOY |  |
| Oil-pressers | 4 | olives | oil | FOOD + HEALTH + **$ export** |  |
| Bronzehands | 3 | metal | tools (efficiency) + weapons | KNOW-mult + MIL |  |
| Stonewrights | 3 | stone | building supplies | BUILD |  |
| Carpenters | 2 | timber | building supplies + furniture | BUILD |  |
| Keelwrights | 2 | timber | ships | FLEET |  |
| Kerameis | 2 | clay | amphorae → multiplier on oil/wine export | $ (gatekeeper) |  |
| Tanners | 2 | hides (flocks) | leather + butchered meat | $ + FOOD |  |
| Weavers | 2 | wool (flocks) | cloth | JOY + $ |  |

---

## Harbor — the food-import-trade gateway

| Faction | r | Role | Contribution | Sink | Notes |
|---|---|---|---|---|---|
| Netmenders | 2 | fishing crews | fish (designated next slice) | FOOD |  |
| Quaymen | 3 | dockhands | throughput multiplier on all import/export | gates $ + imports |  |
| Harborwardens | 4 | port authority, customs | customs income + the import gate | $ + gatekeeper |  |
| Saltroad Houses | 3 | shipowners/freight | carrying capacity for imports (grain!) | FLEET-logistics |  |

---

## Trade — money, imports, and the villain

| Faction | r | Role | Contribution | Sink | Notes |
|---|---|---|---|---|---|
| Amphora Houses | 4 | wholesale merchants | move goods out | **$ export** |  |
| Silverbench | 4 | money-changers/lenders | credit, the moneylender | $ (finance) |  |
| Stallmongers | 2 | agora retailers | distribution — get goods to the Public | goods → JOY/access |  |
| Storehouse Ring | 3 | "corner the market" | the Hoard/Withhold faction — withhold supply for leverage | leverage |  |
| Outland Houses | 2 | metic merchants | source imports (spices → joy, grain) | imports |  |

---

## Temples — piety, food-blessing, the oracle

| Faction | r | God | Contribution | Sink | Notes |
|---|---|---|---|---|---|
| Greenmantle | 2 | Demeter, harvest | multiplier on aristocracy food yield | FOOD-multiplier |  |
| Tidesworn | 3 | Poseidon | calms the sea → fewer fishing/shipping disasters | shock-absorber (sea) |  |
| Bright Order | 4 | Apollo, oracle | the sensor — event/disaster foresight | PIETY + KNOW-sensor |  |
| Raving Choir | 2 | Dionysos | festivals/ecstasy | JOY (+ chaos risk) |  |
| Hearthwardens | 3 | Hestia | civic cohesion, the home fires | HEALTH/stability |  |

---

## Military — security + protecting the grain lifeline

| Faction | r | Role | Contribution | Sink | Notes |
|---|---|---|---|---|---|
| Shieldsworn | 4 | citizen phalanx | core land defense, absorbs raids | MIL |  |
| Companions | 3 | sworn veterans | elite offense / threat removal | MIL (offense) |  |
| Free Spears | 2 | sellswords | paid flexible force | MIL (costs $) |  |
| Oarsworn | 3 | war fleet | protects shipping/imports from raids | FLEET (military) |  |

---

## Professions — services

| Faction | r | Role | Contribution | Sink | Notes |
|---|---|---|---|---|---|
| Asklepiads | 3 | physicians | the only healers — plague lever | HEALTH (sole lever) |  |
| Quillsworn | 3 | clerks/tax-farmers | tax efficiency + accurate records | $-mult + KNOW-sensor |  |
| Players | 2 | actors/poets | theater | JOY |  |
| Garland-Chasers | 2 | athletes | the games, civic pride | JOY/morale |  |
| Perfumers | 2 | scented oils | oil → perfume | $ export (downstream of oil) |  |
| Adorners | 2 | jewelers | silver/gems → jewelry | $ luxury export |  |

---

## Academy — advantage, not goods (per the `resource-chains.md` call)

| Faction | r | Role | Contribution | Sink | Notes |
|---|---|---|---|---|---|
| Goldentongues | 3 | assembly orators | sway the assembly → ties to elections | political capability |  |
| Stargazers | 2 | astronomers/math | navigation + planting calendar | FLEET/FOOD-mult + sensor |  |
| Grove | 3 | philosophers | stance-layer interpreters, legitimacy | KNOW |  |
| Sophists | 2 | rhetoric-for-hire | persuasion training | audience advantage |  |

---

## Synthesis

**Most load-bearing** (cut these and the city feels it): the guild processors, Asklepiads
(sole health), Greenmantle (food multiplier), Bright Order (oracle sensor), Storehouse Ring
(withhold villain), the three estates as raw.

**Prettiest cross-domain chains** (the "factions matter to each other" win):
- **Flocks** (Eumelidai) → Tanners *and* Weavers *and* Temple sacrifice — one raw, three
  processors, three sinks.
- **Olives** (Skiadai) → Oil-pressers → oil → Perfumers + export, needing Kerameis jars +
  Amphora Houses + Quaymen + a ship — a chain crossing four domains.
- **Grain lifeline**: import (Outland) → ship (Saltroad) → guarded by Oarsworn → gated by
  Harborwardens. Cut any link, the city starves.

**Overlap / merge-or-differentiate candidates:**
- Three JOY sources: Players · Garland-Chasers · Raving Choir.
- Two luxury exporters: Perfumers · Adorners (saved only by distinct inputs — oil vs gems).
- Three academy persuaders: Sophists · Goldentongues · Grove.

**The honest blank:** Academy has no *resource* by design — material weight only via
multipliers (Stargazers) and sensors (Grove / Bright Order), never a chain.

## Open decisions

> The per-domain tables above are the **first pass**; the resolved structure is in **Roster
> Decisions**. What remains open:

**Resolved this pass** (see Roster Decisions; recorded, not built):
- ~~Adopt PIETY?~~ → **yes**, as belief (gods = interpretation, not magic). Public state model in
  `resource-chains.md`.
- ~~Temples & academy layout~~ → temples 5→4 (Stargazers merged into Apollo; Hestia cut);
  academy deleted (Grove/Goldentongues parked by function; Sophists cut).
- ~~Lock the estate raws~~ → grain/wine/oil + flocks (Skiadai split).
- ~~Overlap clusters~~ → luxury (cut Adorners), JOY (Garland-Chasers → event), building supplies
  (Builders merge), naval (Keelwrights gatekeeper).
- ~~Capability pools scale existing math~~ → confirmed: MIL/BUILD/FLEET derive direct from
  strength, no new gauges.

**Still to settle (non-blocking):**
- Estate/faction differentiation: data-only (`chains.json`) vs a `produces` field on `Faction`.
- City Guard: exact unrest-suppression curve + the support cost of heavy-handedness.
- Storehouse Ring: how relationship maps to buffer-vs-hoard (threshold? continuous?).
- Whether finance, when revived, returns as the political creditor or stays the external timer.
