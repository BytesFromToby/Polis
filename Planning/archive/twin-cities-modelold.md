# Twin Cities Model
_Last updated: 2026-04-17_

---

## What This Document Is

A description of the Twin Cities city model as currently implemented — its data, structure, and state. Used to guide future updates to the program.

---

## What "Twin Cities" Means Here

Twin Cities is the active city loaded into the simulation. It is a fictional political city modelled loosely on the Minneapolis–St. Paul metro. It is a **single-city simulation** — two cities do not run simultaneously. The name reflects the setting, not a multi-city engine feature.

---

## Current Data Summary

| Element | Count | Notes |
|---------|-------|-------|
| Domains | 15 | Full city coverage |
| Factions | 10 | Spread across 3 domains |
| Named units | 20 | Seeded at startup |
| Generated units | ~4,126 | Pre-sim population fill (anonymous, Level 1) |

---

## Domains (15)

| Domain | Notes |
|--------|-------|
| Traditional Media | Faction home for Star Tribune, WCCO, MPR, City Pages, The Onion |
| Social Media | Special domain — attention system (0–100+), states: baseline / elevated / crisis |
| Political | Faction home for Mayor's Office, City Council DFL, City Council Conservative |
| Street | Faction home for North Minneapolis Community, Southside Alliance |
| Religion | — |
| Bureaucracy | — |
| Finance | — |
| Police | — |
| Underworld | — |
| Legal | — |
| Health | — |
| High Society | — |
| Industry | — |
| Transportation | — |
| University | — |

Each domain has:
- Relationship traits per faction (Friend / Foe / Client / Neutral / Hide)
- A utilization floor (1–5) recalculated each cycle from unit weight sums
- A cap and drift rate (controlling how fast utilization moves)
- A chaos level (0–10)

## City Factions





## Key Files

| File | Purpose |
|------|---------|
| `scr/data/twin_cities.json` | Source of truth for all city data — domains, factions, named units |
| `scr/db/seed.py` | Seeds Twin Cities into the database at startup |
| `scr/loaders.py` | Loads JSON into live engine objects |
| `scr/engine/models.py` | Dataclasses for Unit, Faction, Domain, WorldState |
| `scr/engine/cycle/runner.py` | 13-step cycle orchestrator |

---

## Planned Updates (To Be Filled In)

_Add update goals here as they are identified._

- [ ] Expand faction presence to more domains
- [ ] Implement faction relationship effects in targeting
- [ ] Improve narrative output quality
- [ ] LARP mode: complete player action submission and adjudication
