# Special Factions Specification

**Version:** v1
**Date:** 2026-05-17

Special factions exist outside the normal domain power structure. They don't hold territory or grow through the standard action cycle — they exert pressure on everything else and respond to what the city does to them.

---

## Overview

Three special factions:

| Faction | Role | Domain |
|---|---|---|
| The Public | General population — source of mayoral legitimacy | None (city-wide) |
| The Moneylender | Financial power broker | None (economic layer) |
| External Threats | Bandits, rivals, invaders — pure external pressure | None (outside the city) |

Special factions do not participate in the standard declare → block → resolve cycle. They are processed in their own steps and respond to city state rather than acting opportunistically.

---

## The Public

The Public is not a faction in the domain sense. It is the aggregate mood of the city's general population. It has no floor, no rating, no entrench — it has **disposition** and **support**.

### Structure

```python
@dataclass
class ThePublic:
    support: int = 0          # Mayor's legitimacy in public eyes: -50 to +50
    disposition: str = "neutral"  # "content" | "neutral" | "restless" | "angry"
    traits: List[FactionTrait] = field(default_factory=list)
    health: int = 100         # General city wellbeing proxy
```

### Disposition

Disposition is derived from `support` each cycle:

| Support | Disposition |
|---|---|
| +20 to +50 | `content` |
| −19 to +19 | `neutral` |
| −20 to −34 | `restless` |
| −35 to −50 | `angry` |

### What Affects Public Support

Public support is modified by events in the cycle, not by a formula:

| Source | Effect on support |
|---|---|
| Tax rate 0.05 (Low) | +2/cycle |
| Tax rate 0.15 (Elevated) | −2/cycle |
| Tax rate 0.20 (High) | −5/cycle |
| Tax rate 0.25+ (Punishing) | −10/cycle |
| Guard payroll skipped | −5/cycle |
| Mayor: Public Works allocation | +5 (one-time) |
| Mayor: Publicly Endorse popular faction | +5 (one-time) |
| Mayor: Publicly Endorse disliked faction | −5 (one-time) |
| Mayor: Publicly Condemn (target health < 30) | +5 (one-time) |
| Faction collapse in city (any) | −3 (one-time) |
| Active event: disaster or plague | −5/cycle while active |
| Mayor: Turn a Blind Eye | −5 (one-time) |
| Turn a Blind Eye discovered | −10 (one-time) |

Public support also equals Mayor reputation with The Public — tracked as a single value, not separately.

### The Public's Traits

The Public has traits that evolve from disposition and events, the same as any faction. These traits modify how the public responds to the Mayor (see Mayor spec — reputation effects) and may influence event outcomes.

Starting traits: none (disposition = neutral, support = 0).

Trait evolution for The Public:

| Event | Trait effect |
|---|---|
| Disposition reaches `restless` | Add/amplify `distrusts Mayor` (slight) |
| Disposition reaches `angry` | Add/amplify `angry at Mayor` (moderate) |
| Disposition returns to `neutral` | Decay `distrusts Mayor` / `angry at Mayor` by 1 step |
| Disposition reaches `content` | Remove `distrusts` and `angry at` entirely |
| 3+ consecutive cycles of rising support | Add `trusts Mayor` (slight) |

Traits cap at 6 (same rules as faction traits).

### The Public's Role in Faction Politics

When The Public is `content`:
- Factions with `distrusts Mayor` get −5 to Steal actions (public cooperation reduces cover)
- Mayor's decree actions cost 1 fewer action point (public mandate)

When The Public is `restless`:
- No faction effects; Mayor's Broker a Deal DC increases by 2

When The Public is `angry`:
- Factions with `aggressive` trait get +10 to Harm actions (chaos cover)
- Mayor's Condemn actions cost +1 action point (public cynicism)
- Mayor removal countdown starts (see Mayor spec)

### The Public Does Not Act

The Public does not declare actions, block, or resolve. Its influence is passive — through support values, disposition state, and traits that feed into the Mayor removal conditions.

---

## The Moneylender

The Moneylender is a full faction structurally but operates outside domain politics. It interacts primarily through the treasury and leverage mechanics (see Treasury spec).

### Structure

The Moneylender is a `Faction` with:
- `domain: "finance"` (a non-playable domain with no cap or utilization)
- `floor: 3` (fixed — cannot grow or collapse in v1)
- `rating: 3.0` (fixed)
- `health: 100` (cannot be harmed directly in v1)
- Standard `traits` list

Starting traits: `["opportunistic" (moderate), "corrupt" (moderate)]`

### The Moneylender's Actions

The Moneylender does not use the standard declare → resolve cycle. It acts through treasury mechanics:

| Condition | Moneylender Action |
|---|---|
| Mayor borrows > 0 gold | Interest deducted each cycle (see Treasury spec) |
| Debt > 500 gold | Leverage: +10 to Steal against all factions |
| Debt > 500 gold | Mayor cannot Withhold Resources targeting Moneylender |
| Debt > 500 gold | Demand political concession (tax rate reduction or +2% debt rate) |
| Debt > 800 gold | Adds `angry at Mayor` (moderate) trait |
| Debt not reduced in 5 cycles (> 800) | Backs removal coalition |

### Moneylender Trait Evolution

The Moneylender's traits evolve normally based on what happens to it. The Mayor can improve or worsen the relationship through the standard reputation/action system.

Mayor can target the Moneylender with:
- Meet with Faction (reputation +5, can pair with endorse/condemn)
- Publicly Endorse (reputation +10; other factions: −3)
- Broker a Deal (requires rep ≥ 10 — can reduce existing leverage)

The Moneylender cannot be targeted by Withhold Resources when leverage is active.

---

## External Threats

External Threats represent forces outside the city: bandit gangs, rival cities, political enemies, foreign agents. They have no domain stake and do not compete for territory — they apply pressure.

### Structure

```python
@dataclass
class ExternalThreat:
    id: str
    name: str
    type: str           # "bandits" | "rival_city" | "foreign_agent" | "plague_vector"
    threat_level: int   # 1–5 (scales all effects)
    active: bool = True
    duration: int = 0   # 0 = indefinite; > 0 = cycles remaining
    effects: List[ThreatEffect] = field(default_factory=list)
```

```python
@dataclass
class ThreatEffect:
    target_type: str    # "domain" | "faction" | "world" | "treasury"
    target_id: str
    field: str          # what is affected
    value: float        # delta per cycle
```

### How Threats Work

External Threats are not factions and do not act. Each active threat applies its effects each cycle during Step 8 (alongside world chaos and new events).

Threats can be:
- **Persistent** — remain until Mayor acts to remove them (commission a project, allocate budget, etc.)
- **Timed** — expire after a set number of cycles

### Threat Effects by Type

**Bandits** (threat_level 1–3):
- Chaos +1/cycle in street and underworld domains
- Factions in affected domains: Harm weight +10 (opportunity)
- Treasury: −5 × threat_level gold/cycle (trade disruption)

**Rival City** (threat_level 2–5):
- Dock domain factions: Grow penalty −5/cycle (diverted trade)
- City chaos +1/cycle
- Event: "Trade Ship Seized" added to active events if dock domain chaos ≥ 4

**Foreign Agent** (threat_level 1–4):
- One random faction per cycle: reputation with Mayor −3 (disinformation)
- Mayor information actions cost +1 action point
- Occasionally adds `distrusts X` relational trait between two factions (see Events spec)

**Plague Vector** (threat_level 1–5):
- Health domain factions: health −2 × threat_level/cycle
- The Public health −3/cycle
- World chaos in health domain +1/cycle while active

### Removing Threats

The Mayor does not have a direct "remove threat" action. Threats are removed by:
- **Projects** — City Wall reduces external threat effectiveness; commission guards increases defense
- **Events** — Some events resolve threats naturally
- **Treasury expenditure** — Emergency guard surge (50 gold) reduces all active threat levels by 1 for 1 cycle
- **Scripted resolution** — Some threats are narrative events with defined end conditions

### Starting Threats

A city may begin with 0 or 1 active threats, defined in city data. Most cities start threat-free.

---

## Special Faction Processing Order

Each cycle, special factions are processed in this order (after Step 8 standard chaos):

1. **External Threats** — apply effects; decrement duration; remove expired threats
2. **The Moneylender** — apply interest; check leverage conditions; check removal coalition trigger
3. **The Public** — apply all support modifiers from this cycle's events; derive disposition; evolve traits

This order means External Threat effects are visible when The Public's support is updated.

---

## City Data Format

Special factions are defined in city data alongside normal factions:

```json
{
  "special_factions": {
    "the_public": {
      "support": 0,
      "health": 100,
      "traits": []
    },
    "moneylender": {
      "name": "House Veltris",
      "traits": [
        {"trait": "opportunistic", "intensity": "moderate"},
        {"trait": "corrupt", "intensity": "moderate"}
      ]
    },
    "external_threats": []
  }
}
```
