# Events Specification

**Version:** v1.1
**Date:** 2026-05-17
**Updated:** 2026-06-12 — **Public-need gates** added to `trigger_conditions` (public-needs / barley-run).

Events are timed pressure sequences injected into the faction system. They are not resource management — they are triggers that cause faction-system effects. A mine disaster doesn't add a mining mechanic; it pressures specific factions for a defined duration.

---

## Overview

An event has:
- A **trigger** — what caused it
- A **target** — which faction, domain, or project is hit
- A **duration** — how many cycles the primary effect lasts
- A **cascade** — secondary effects that fire after the primary expires

Events do not bypass the faction system. They modify conditions (ratings, entrench, health, action weights) and let the faction system respond naturally.

---

## Event Structure

```python
@dataclass
class Event:
    id: str
    name: str
    type: str             # "random" | "scripted" | "mayor_triggered"
    trigger: str          # what caused this event (description/id)
    target_type: str      # "faction" | "domain" | "project" | "world"
    target_id: str        # id of the affected entity
    duration: int         # cycles the primary effect lasts
    cycles_remaining: int = 0  # countdown
    effects: List[EventEffect] = field(default_factory=list)
    cascade: Optional[CascadeSpec] = None
    status: str = "pending"  # "pending" | "active" | "cascading" | "resolved"
```

```python
@dataclass
class EventEffect:
    field: str        # what is modified: "rating" | "health" | "entrench" | "action_weight" | "chaos"
    target_id: str    # entity the field belongs to
    value: float      # delta applied each cycle (negative = penalty)
    label: str        # description for narrative
```

```python
@dataclass
class CascadeSpec:
    delay: int        # cycles after primary expires before cascade fires
    target_id: str
    effects: List[EventEffect]
```

---

## Event Types

### Random Events

The engine rolls for random events each cycle (Step 8 in the cycle runner, alongside world chaos). Probability scales with world chaos level in the relevant domain.

| Chaos level | Base chance of random event |
|---|---|
| 0–2 | 5% |
| 3–5 | 15% |
| 6–8 | 30% |
| 9–10 | 50% |

Random events are drawn from the city's event deck — a curated list of events appropriate to that city's domain makeup. The engine selects a random entry weighted by which factions and domains are currently active.

### Scripted Events

Scripted events are pre-written sequences loaded from city data. They fire at defined conditions or cycle counts. They create a narrative arc — the city has a history that plays out regardless of what the Mayor does (but the Mayor's actions can mitigate or accelerate outcomes).

Scripted events are defined in `data/events.json` per city.

Example conditions for scripted events:
- `cycle >= 10` and `any faction.rating >= 4.0` → power struggle event fires
- `treasury.gold < 100` → financial crisis warning fires
- `faction X collapsed` → succession crisis fires in that domain

### Mayor-Triggered Events

Some Mayor actions produce events as side effects. These are not chosen from the event deck — they are consequences of what the Mayor did.

Examples:
- Mayor condemns a faction publicly → rival factions get a confidence boost event (1 cycle, +5 to all actions in that domain)
- Mayor withhold resources → target faction gets outside pressure event (2 cycles, Grow −10/cycle)
- Mayor turns a blind eye → rival faction gets exposed event if discovered

---

## Event Processing

Events are processed at Step 8 (after end-of-cycle and collapse cascades — see `cycle-runner_spec.md` Full Orchestration). Each active event:

1. Applies its effects for this cycle
2. Decrements `cycles_remaining`
3. If `cycles_remaining == 0` and cascade exists: fire cascade after `cascade.delay` cycles

New events are added to the active events list during Step 8.

---

## Example Events

### The Great Forge Fire
```
trigger: random (high chaos in guilds domain)
target: bronzehands
duration: 2 cycles
effects:
  - bronzehands health: -5/cycle
  - bronzehands entrench: -10 (one-time)
cascade:
  delay: 1
  target: harbor_domain
  effects:
    - all harbor factions Grow: -5/cycle for 2 cycles
```

### Plague Outbreak
```
trigger: scripted (cycle >= 15, public health < 40)
target: professions_domain
duration: 4 cycles
effects:
  - all professions domain factions health: -3/cycle
  - The Public health: -5/cycle
  - world chaos in professions: +2 (one-time)
cascade:
  delay: 0
  target: The Public
  effects:
    - Public reputation with Mayor: -10 (one-time)
```

### Trade Ship Seized
```
trigger: random (external threats active)
target: harbor_domain
duration: 1 cycle
effects:
  - all harbor factions Grow: blocked this cycle
  - treasury income: -20 this cycle
cascade: none
```

### Faction Rivalry Ignites
```
trigger: random (two factions both at rating >= 3.0 in same domain)
target: both factions (applied separately)
duration: 3 cycles
effects:
  - faction A: Harm weight +15/cycle
  - faction B: Harm weight +15/cycle
cascade: none
note: adds distrusts relational trait between A and B at moderate intensity
```

---

## City Event Deck

Each city has a JSON event deck: a list of event templates with their trigger conditions, probability weights, and template effects. The engine instantiates events from these templates when conditions are met.

`data/events.json` format:
```json
[
  {
    "id": "forge_fire",
    "name": "Forge Fire",
    "type": "random",
    "trigger_conditions": {"domain": "guilds", "min_chaos": 4},
    "weight": 3,
    "template": { ... }
  }
]
```

The starting city includes a curated deck of 8–12 events appropriate to its domain mix.

### Public-need gates (public-needs / barley-run, 2026-06-12)

`trigger_conditions` additionally supports gates on the Public's need bands (band tables in
`public-needs_spec.md`). A template is eligible only while every gate it declares holds:

| Key | Meaning |
|---|---|
| `max_fed_band` | Public fed band ≤ this band (e.g. `"Hungry"` → eligible when Hungry or Starving) |
| `min_fed_band` | Public fed band ≥ this band (e.g. `"Well fed"` for boon events) |
| `max_happy_band` / `min_happy_band` | Same, on the happy band |
| `sickly` | `true` → eligible only while Public `health < 40` (the plague gate) |

The needs step runs before new-event rolling each cycle (cycle-runner item 5b), so gates see
the current cycle's bands. Deck additions for v1: a band-gated **Bread Riot**
(`max_fed_band: "Starving"`) and a **Plague Outbreak** gate switching from the old scripted
condition to `sickly: true`.

**Done when:**
- A template with `max_fed_band: "Starving"` is never rolled while the Public's fed band is
  above Starving, and becomes eligible the same cycle the band reaches it  `[automated]`
- Each gate key (`min_/max_fed_band`, `min_/max_happy_band`, `sickly`) is honored
  independently, proven with no-effect sentinel templates injected by the test  `[automated]`

---

## Mayor Response to Events

Events create pressure; the Mayor decides how to respond. The Mayor has no special "respond to event" action — they use their normal action pool (allocate budget, condemn a faction, commission a project to replace destroyed infrastructure, etc.).

Auto-pause triggers (player-configured) can fire when a new event fires, prompting the Mayor to act before the next cycle resolves.
