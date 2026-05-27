# Projects Specification

**Version:** v4
**Date:** 2026-05-19

Projects are persistent city infrastructure — physical things that exist, take time to build, and can be destroyed. They give factions a natural reason to act across domains and create meaningful stakes in the city's physical state.

---

## Overview

A project is a structure with:
- A build cost and build time
- A permanent effect on city baseline stats when complete
- Faction involvement during construction
- Vulnerability to attack and disaster

---

## Project Structure

```python
@dataclass
class Project:
    id: str
    name: str
    domains: List[str]     # domains this project belongs to; factions in any listed domain can build, attack, or receive effects
    build_cost: int        # gold from treasury
    build_time: int        # cycles to complete (fallback if no faction works on it)
    faction_build_actions: int = 4  # successful faction actions required to complete
    cycles_built: int = 0  # fallback cycle counter
    category: str = "standard"       # "standard" | "tax_collection"
    tax_level: int = 0               # 1–5 for tax_collection projects; unlocks that rate tier
    faction_level: bool = False      # True = effects apply only to the faction that built it (initiated_by)
    status: str = "under_construction"  # "under_construction" | "active" | "damaged" | "critical" | "destroyed"
    health: int = 0        # dual purpose: build progress (0→100) during construction; structural health (0→100) when active
    effects: List[ProjectEffect] = field(default_factory=list)
    maintenance_cost: int = 10  # stored per-project; treasury uses flat 2 × active_project_count (see Treasury spec)
    initiated_by: str = "mayor"  # "mayor" | faction_id; doubles as effect owner when faction_level=True
    # cycle-only (not persisted):
    build_actions_this_cycle: int = 0  # counts successful BuildProject actions this cycle; resets each cycle
```

```python
@dataclass
class ProjectEffect:
    target: str       # "domain" | "faction" | "treasury" | "world"
    target_id: str    # id of the entity being affected
    field: str        # what is modified (e.g. "drift", "rating", "gold_per_cycle")
    value: float
    condition: str = "always"  # "always" | "active" | "damaged"
```

---

## Build Process

### Initiation

Projects are initiated by:
- The Mayor (costs action points — see Mayor spec)
- A faction (faction declares a project during declaration phase; must have floor ≥ 3)

Mayor-initiated projects draw from the city treasury. Faction-initiated projects use faction resources (future: faction treasury or health investment).

### Construction Phase

Each cycle a project is under construction:

1. **Faction work:** A faction whose `domain_primary` is in the project's `domains` list may spend its action on `BuildProject`. Roll `d20 + floor(rating)` vs DC 12. On success, `health += 100 / faction_build_actions`. Example: `faction_build_actions = 4` means each successful action adds 25 health.
2. **Sabotage:** Any faction (no domain restriction) may spend its action on `SabotageProject`. See Actions spec for resolution. Under-construction projects start at health 0, giving defense_rating 1 — they are fragile until progress is made.
3. **Completion check:** If `health >= 100` OR `cycles_built >= build_time` (fallback), status → `active`, health reset to 100.

Mayor can accelerate construction by spending treasury: 50 gold = −1 build cycle (once per cycle max).

### Locking Mayor Actions

When the Mayor initiates a project, action points are committed over build time:

| Build time | Action cost |
|---|---|
| 1–2 cycles | 2 action points (paid upfront) |
| 3–5 cycles | 1 action point/cycle during construction |
| 6+ cycles | 1 action point every other cycle during construction |

If the Mayor abandons a project mid-construction: treasury cost is lost, action commitment ends, half-built project is removed from play (ruins — no effect).

---

## Active Projects

When `status == "active"`, the project's effects apply each cycle. Effects are persistent until the project is destroyed.

If `faction_level == True`, effects apply only to the faction whose id matches `initiated_by`. The Mayor cannot commission faction-level projects.

Projects require ongoing maintenance (see Treasury spec). The treasury pays a flat `2 × active_project_count` gold per cycle covering all projects collectively. If the treasury cannot cover maintenance, it is silently skipped for that cycle (no per-project damage — maintenance failure cascades via treasury bankruptcy rules instead).

---

## Project Defense

When targeted by `SabotageProject`, the project rolls its own defense:

```
project_defense_rating = max(1, project.health // 20)
project_defense_roll = d20 + project_defense_rating + build_bonus
```

| Health | Defense Rating |
|---|---|
| 81–100 | 5 |
| 61–80 | 4 |
| 41–60 | 3 |
| 21–40 | 2 |
| 1–20 | 1 |

**Build bonus:** Each successful `BuildProject` action on this project this cycle adds +1, capped at +2. Factions choosing to build rather than act offensively are actively defending the project.

A fully healthy project defends like a floor-5 faction. A damaged project spirals — easier to attack, harder to repair.

---

## Project Health

Projects have structural health (0–100).

| Health | Status | Effect |
|---|---|---|
| 100–51 | Intact | Full effects |
| 50–21 | Damaged | Effects halved |
| 20–1 | Critical | Effects at 25%; −5 health/cycle |
| 0 | Destroyed | Removed from play |

Health damage comes from:
- Faction Harm action (targeted at project, not a faction)
- Random events (disasters, fires)
- Neglected maintenance

Health can be repaired: Mayor spends 30 gold + 1 action point → restore 25 health.

---

## Destroying Projects

Factions destroy projects using the `SabotageProject` action (see Actions spec). Any faction can target any project regardless of domain.

- Decisive: project health −25
- Partial: project health −10
- Fail: no effect
- Health 0: status → `destroyed`, removed from play

Why factions destroy projects:
- Remove an opponent's advantage (the wharves help the Quaymen — burn the wharves)
- Create pressure on the Mayor (destroy what the Mayor built)
- Destabilize a rival domain (destroy infrastructure, chaos spills over)
- Deny a rival faction the benefit of their own faction-level project

---

## Example Projects

### Dock Expansion
- **Domains:** `["harbor", "trade"]`
- **Build cost:** 150 gold
- **Build time:** 3 cycles
- **Effect:** domain.cap +10 (harbor); treasury income +15 gold/cycle
- **Faction level:** No

### City Wall Section
- **Domains:** `["military", "aristocracy"]`
- **Build cost:** 200 gold
- **Build time:** 5 cycles
- **Effect:** External threats −5 to attack rolls; garrison effectiveness +10%
- **Faction level:** No

### Public Market
- **Domains:** `["trade", "harbor"]`
- **Build cost:** 80 gold
- **Build time:** 2 cycles
- **Effect:** Public reputation +3/cycle; trade factions Grow +5
- **Faction level:** No

### Temple District Expansion
- **Domains:** `["temples"]`
- **Build cost:** 100 gold
- **Build time:** 3 cycles
- **Effect:** Temples entrench decay −0.02; Public reputation +2/cycle
- **Faction level:** No

### Guild Safehouse
- **Domains:** `["guilds"]`
- **Build cost:** 60 gold
- **Build time:** 2 cycles
- **Effect:** Owner faction: Steal +10 to rolls, Harm −5 to incoming rolls
- **Faction level:** Yes (only the initiating faction benefits)

---

## Starting Projects

A city begins with pre-existing infrastructure. These projects are already `active` with full effects at game start. They have no remaining build time or cost — they simply exist.

Starting projects are defined in city data (JSON). Example starting city:
- 5 Harbor Wharves (5 separate wharf projects at reduced scale each)
- City Walls
- The Agora (main market square)

Starting projects immediately incur maintenance costs and are vulnerable to destruction from cycle 1.

---

## Project Listing

The full list of available projects is defined in a data file (`data/projects.json`). Each entry includes id, name, domain, costs, and effects. The Mayor and factions select from this list when initiating.

Custom projects (edge cases or event-driven) may be injected by the event system with non-standard parameters.
