# Events Specification

**Version:** v1.1
**Date:** 2026-05-17
**Updated:** 2026-06-12 — **Public-need gates** added to `trigger_conditions` (public-needs / barley-run).
**Updated:** 2026-06-16 — **`withhold` effect field** added (force a faction's chain output to 0 for a duration); active-event effect application moved before the needs step. See `actions_spec.md`, `public-needs_spec.md`.

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
    field: str        # what is modified: "rating" | "health" | "entrench" | "action_weight" | "chaos" | "withhold"
    target_id: str    # entity the field belongs to
    value: float      # delta applied each cycle (negative = penalty)
    label: str        # description for narrative
```

The `withhold` field is the disaster face of the supply-interruption primitive
(`actions_spec.md`, `public-needs_spec.md`): while the event is active it sets
`faction.withholding = True` on its target each cycle (the `value` is ignored), forcing that
faction's chain contribution to 0 for the event's `duration`. A great storm that closes the sea
force-withholds the Netmenders; the same `withholding` flag a striking faction sets on itself, an
event sets on its victim — one mechanism, three causes (anger, deal, disaster).

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

**Active-event effect application runs immediately before the Public-needs step (item 5b); new
events are still *rolled* after the needs step.** This split (added with Withhold, 2026-06-16)
lets a `withhold` event force its target's chain contribution to 0 *this* cycle: the needs step
reads `withholding` flags that active events have just asserted, and the end-of-cycle reset
clears them — so an active storm re-asserts the flag each cycle for its duration, and the city
recovers the cycle after it expires. New-event *rolling* stays after needs so its band gates see
this cycle's freshly-drifted `fed`/`happy` (see Public-need gates below). Effects other than
`withhold` (health/rating/drift/chaos) are unaffected by the move — the needs step does not read
those fields. See `cycle-runner_spec.md` Full Orchestration.

Each active event:

1. Applies its effects for this cycle
2. Decrements `cycles_remaining`
3. If `cycles_remaining == 0` and cascade exists: fire cascade after `cascade.delay` cycles

New events are added to the active events list during the post-needs roll.

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

### The Great Storm
```
trigger: random (port domain)
target: netmenders
duration: 3 cycles
effects:
  - netmenders: withhold (forced — sets withholding each active cycle)
cascade: none
note: the sea closes; the nets stay ashore. For its duration the fishery contributes 0 fed.
      Source redundancy (barley + flocks remain) keeps the city never-Starving from one storm
      alone — it is the loss of every Food source together that Starves it (public-needs_spec
      redundancy property). The material thing a disaster breaks (crisis-and-stance.md hook).
```

### The Mob Marches  (flagship — unrest)
```
trigger: random, gated min_unrest_band: "Boiling"
target: a domain (its chaos) + The Public
duration: 1 cycle
effects:
  - world chaos in the target domain: +2 (the riot spreads disorder)
  - The Public health: −5 (injuries in the streets)
  - factions Steal in the chaos (behavior already lifts Steal at high unrest — no event effect)
cascade: none
note: open riot at the boiling point. Effects reuse existing fields (chaos) + the new
      public-targeted effect (health). The City Guard is the standing counter — it presses unrest
      down before this gate is reached; when unrest still hits Boiling, the riot lands. Heavier
      flagships (Insurrection, the direct removal bid) are deferred — this is the in-slice teeth.
```

### The Ignored Omen  (flagship — piety)
```
trigger: random, gated max_piety_band: "Lax"  (eligible while Godless or Lax)
target: The Public
duration: 1 cycle
effects:
  - piety −5 (the godless city shrugs off a portent; the slide compounds)
  - support −3 (a crisis-blame penalty; the needs step's piety modifier makes it bite harder)
cascade: none
note: the low-belief city dismisses a warning; impiety begets impiety. A teaching event — it makes
      the godless band visible and nudges the player to tend piety before a real disaster lands.
```

### The Wells Sicken  (flagship — consumption, low)
```
trigger: random, gated max_consumption_band: "Dry"
target: The Public
duration: 2 cycles
effects:
  - The Public health −4/cycle (too little wine → raw water → waterborne illness)
cascade: none
note: abstinence causing illness is period-true — weak wine meant people drank dangerous water.
      Surprises players who treat "less drinking" as strictly good. The dry end of the U.
```

### The Drunken Riot  (flagship — consumption, high)
```
trigger: random, gated min_consumption_band: "Sodden" AND min_unrest_band: "Restless"
target: a domain (its chaos) + The Public
duration: 1 cycle
effects:
  - world chaos in the target domain +2 (a festival tips to violence)
  - The Public health −3 (the Watch too sodden to hold it)
cascade: none
note: the consumption+unrest combo — a wasted, violent night. The sodden end of the U; needs both
      a drunk city AND simmering unrest, so it only fires when the city is already on edge.
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
| `max_piety_band` / `min_piety_band` | Same, on the piety band (Godless…Zealous) — added 2026-06-16 |
| `max_unrest_band` / `min_unrest_band` | Same, on the unrest band (Placid…Boiling) — added 2026-06-16 |
| `max_consumption_band` / `min_consumption_band` | Same, on the consumption band (Dry…Sodden) — added 2026-06-16 |
| `sickly` | `true` → eligible only while Public `health < 40` (the plague gate) |

The needs step runs before new-event rolling each cycle (cycle-runner item 5b), so gates see
the current cycle's bands. Deck additions for v1: a band-gated **Bread Riot**
(`max_fed_band: "Starving"`) and a **Plague Outbreak** gate switching from the old scripted
condition to `sickly: true`.

**Done when (Withhold events, 2026-06-16):**
- An active `withhold`-effect event sets `withholding = True` on its target faction each cycle it
  is active, driving that faction's chain contribution to 0; the same cycle the event resolves,
  the target's contribution returns to normal (the flag is no longer re-asserted)  `[automated]`
- A force-withhold of one Food source leaves the Public never Starving from full health
  (redundancy holds); force-withholding **all** Food sources at once drives it to Starving — the
  same redundancy property removal proves, now via the `withholding` flag  `[automated]`
- Active-event effect application is ordered before the needs step while new-event rolling stays
  after it: a `withhold` storm is felt the same cycle, and band-gated rolls still see this
  cycle's bands (both proven in one ordering test)  `[automated]`

**Done when:**
- A template with `max_fed_band: "Starving"` is never rolled while the Public's fed band is
  above Starving, and becomes eligible the same cycle the band reaches it  `[automated]`
- Each gate key (`min_/max_fed_band`, `min_/max_happy_band`, `sickly`) is honored
  independently, proven with no-effect sentinel templates injected by the test  `[automated]`

**Done when (piety/unrest gates + flagships, 2026-06-16):**
- `min_/max_piety_band` and `min_/max_unrest_band` gate templates exactly at their band
  boundaries, proven with sentinel templates (a `min_unrest_band: "Boiling"` template is eligible
  only at Boiling)  `[automated]`
- Event effects can target **`the_public`** (fields `piety`/`unrest`/`support`/`fed`/`happy`/
  `health`), clamped to range — the capability events previously lacked  `[automated]`
- The Mob Marches raises the target domain's chaos and lowers Public `health` when it fires  `[automated]`
- The Ignored Omen lowers `piety` and `support` when it fires while the piety band is Lax or
  Godless, and is never eligible at Observant+  `[automated]`
- `min_/max_consumption_band` gate templates at their band boundaries (sentinel-proven)  `[automated]`
- The Wells Sicken is eligible only at Dry and drains Public health; The Drunken Riot needs both
  Sodden consumption AND Restless+ unrest, and raises chaos + lowers Public health when it fires  `[automated]`

---

## Mayor Response to Events

Events create pressure; the Mayor decides how to respond. The Mayor has no special "respond to event" action — they use their normal action pool (allocate budget, condemn a faction, commission a project to replace destroyed infrastructure, etc.).

Auto-pause triggers (player-configured) can fire when a new event fires, prompting the Mayor to act before the next cycle resolves.
