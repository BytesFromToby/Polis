# Proposal: Faction → Resource Map

**Date:** 2026-06-14
**Status:** PROPOSAL — incubating, first-pass mapping for editing. Companion to
`resource-chains.md` (the sinks framework + mechanics) — this doc is the per-faction detail:
*every one of the 41 factions gets a mechanical job.* Nothing here is built or locked.

## Purpose

Run the cut-test across the whole roster: give each faction a resource job, then the overlaps
(merge candidates) and blanks (set-dressing) reveal themselves. Edit freely — the **Notes**
column is yours.

**Sinks** (from `resource-chains.md`): FOOD (fed) · JOY (happy) · HEALTH · PIETY ·
**$** (treasury/export) · MIL (security) · BUILD · FLEET · KNOW (knowledge/efficiency/sensor).

Ratings shown are current starting `rating` in `data/factions.json`.

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
- Lock the three estates' raws (aristocracy is the root of everything agricultural)?
- Adopt PIETY as a sink, or keep Temples on JOY/HEALTH only? (mirrors `resource-chains.md` OQ)
- Resolve each overlap cluster: distinct flavor, or merge?
- Capability pools (MIL / BUILD / FLEET / KNOW) — confirm they scale existing math rather than
  becoming new gauges (per `resource-chains.md`).
- Estate/faction differentiation: data-only (`chains.json`) vs a `produces` field on `Faction`.
