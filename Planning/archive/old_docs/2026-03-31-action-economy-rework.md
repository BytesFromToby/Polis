# Decision: Action Economy Rework — Leveled Budget System

**Date:** 2026-03-31
**Status:** Accepted

---

## Context

The current action economy gives each unit `floor(domain_rating)` action points per cycle. Actions are selected by weighted random choice and allocated proportionally. The `int()` truncation in the proportional calculation floors most action shares to zero — virtually all points go to the single highest-weighted action. Units effectively take one action per cycle regardless of their level. This is broken and misrepresents the design intent.

A rework is needed. The design direction below replaces the current system entirely.

---

## Design Direction (Decided)

### Budget

Each unit's action budget is expressed in Level 1 (L1) units:

| Unit Level | L1 Budget |
|---|---|
| 1 | 1 |
| 2 | 2 |
| 3 | 4 |
| 4 | 8 |
| 5 | 16 |
| N | 2^(N-1) |

A unit's level is `floor(primary domain rating)`.

Higher-level units have exponentially more capacity — a L5 unit can do 16 times what a L1 unit can.

### Action Levels and Cost

Each action is executed at a chosen level. Cost in L1 units:

| Action Level | L1 Cost |
|---|---|
| 1 | 1 |
| 2 | 2 |
| 3 | 4 |
| 4 | 8 |
| 5 | 16 |
| N | 2^(N-1) |

A unit may not execute an action above their own level. A unit may choose to execute an action below their max level to conserve budget for other actions.

### One-Of-Each Rule

A unit may take each named action only once per cycle. They cannot take Harm twice even if budget allows.

### multi domain units
Unit gets action level for each domain to be used in that domain. One-Of-Each applies over all domains.  

for each domain above 1 a unit takes an action per cycle.  they get a health penalty.  
2 domains 5 point health loss
3 = 10
4 = 15

If health is below 50 can only do actions in a max of 2 domains
If health is below 25 can only do actions in a max of 1 domains

### Combinations

A unit spends their full L1 budget across any mix of actions at any levels, subject to:
- No action above their own level
- One of each named action maximum
- Budget cannot be exceeded

**Example — Level 4 unit (8 L1 budget):**
- 1× L4 action (8) — full budget, one action
- 2× L3 actions (4+4) — two actions
- 1× L3 + 2× L2 (4+2+2) — three actions
- 1× L2 + 4× L1 (2+1+1+1+1) — five actions
- Any other combination totaling ≤ 8

---

## Specific Action Rules (Decided)

### Obscure

Obscure is always paired to another action. Its level is at least one below the action it covers.

- Hiding a L4 Harm requires a L3+ Obscure
- Hiding a L3 Block requires a L2+ Obscure
- Total cost = action cost + obscure cost

This means obscuring powerful actions is expensive. A L5 unit burning a L5 action and its L4 Obscure spends 16 + 8 = 24 L1 units — more than a L5 budget. You cannot fully obscure your maximum action unless you are L6+.

### Care

Care heals health in a linear curve, not exponential. The healing amount per level:

| Care Level | HP Healed |
|---|---|
| 1 | 4 |
| 2 | 8 |
| 3 | 12 |
| 4 | 16 |
| N | 4N |

The cost to execute Care still follows the standard level cost table. The effect grows linearly because healing is a support action — it should not scale as aggressively as offensive actions.

### Protect

Protects agains attacks If attacked. stops any attack of equal level or lower.  If attack was 1 level higher, reduce by one. if 2+  attack fully succeed. 



| protect level | Entrench increase |  
|---|---|
| 1 | 4 |
| 2 | 8 |
| 3 | 12 |
| 4 | 16 |
| N | 4N |


## Harm 

This attack action targets a unit/faciion's domain with the intent of lowering it. 

- If level is equal or lower than a target's Protect - nothing happens
- If no Protect action is taken reduce entrench

| protect level | Entrench decrease |  
|---|---|
| 1 | 6 |
| 2 | 12 |
| 3 | 18 |
| 4 | 24 |
| N | 6N |

- If protect action is less than the Attack, use this formula and refer back to the chart 

Harm - protect = 1  then Harm -1 succeeds
Harm - protect > 1 then Harm -1 and a Harm -2 succeeds

- If unit has no entrench, Harm deals rating damage instead:

```
damage = min(0.5, grow_increment(defender_floor) × max(0.1, harm_level - defender_floor + 1))
```

Where `grow_increment(n) = 1 / (2^n + 1)`

| Harm L | Def Floor | Multiplier | Damage |
|---|---|---|---|
| 1 | 1 | 1.0 | 0.333 |
| 1 | 3 | 0.1 | 0.037 |
| 1 | 5 | 0.1 | 0.015 |
| 3 | 1 | 3.0 | **0.500** (capped) |
| 3 | 3 | 1.0 | 0.111 |
| 3 | 5 | 0.1 | 0.015 |
| 5 | 1 | 5.0 | **0.500** (capped) |
| 5 | 3 | 3.0 | 0.333 |
| 5 | 5 | 1.0 | 0.030 |

- Punching up (harm_level < defender_floor): multiplier floors at 0.1 — always does a small but real hit
- Punching down (harm_level > defender_floor): scales up fast, capped at 0.5
- Rating damage can reduce `int(rating)` below stored floor → floor decreases by 1 per threshold crossed
- Floor minimum is 1 — rating cannot be driven below 1.0

### Expose

2 types Targeted and Domain

Targeted - will expose any action by target unless the obscure level is lower 
    - tie to a PC over an NPC the toe obscureer

Domain - will see the moves in the domain.  but not any that were obscured 

## Block

Block is a targeted action (unit or faction)
block level >= the highest level action done by target:  ALL domain actions blocked. 
Block level = the highest level action done by target - 1:  all domain actions lower by 1 level. (level 1 are blocked)
Block level < the highest level action done by target - 1: no effect

## support Faction
Only Units
Support faction actions increase the effectiveness of a faction they are in. 
support acts as a 1/3 toward a level increase. 

Example:
Faction takes a 5th level action. If 2 other 5 level actions are taken in support, level increases to level 6.  three 4 level supports would count as one 5 toward the increase and and so on.


---

##  NPC actions

-at most 3 actions 
example:
a level 5 has options 
1 level 5
2 l 4s
2 l 3s 1 lv 4

each action option gets weighted. 
the top weighted action take presidence
if second top weighted is within 5, split between the two
if third top weighted is within 8, split between the three 

There is a 5% chance that each one is skipped. 





## Open Design Questions

These must be resolved before implementation begins.

### 1. What is a unit's action level?

Is the level of an action determined by:
- **a) Unit's primary domain level** — a L5 unit always acts at L5 in their primary domain
- **b) The domain relevant to the action** — Harm uses the combat domain rating, Block uses the city_watch domain rating, etc.
- **c) Unit chooses** — the unit selects what level to execute each action at, within their max

Option (c) is most flexible and seems closest to the design intent. Needs confirmation.

### 2. What does action level affect on outcomes?

For each action type, what does executing at a higher level change?

- **Harm** — higher roll, more damage, harder to Block?
- **Block** — can only stop actions at or below its level?
- **Grow** — faster rating gain?
- **Support Faction** — larger health/LN improvement?
- **Seek Leadership** — higher chance of success?
- **Expose** — more information revealed?
- **Obscure** — already defined by pairing rule

Each action needs a defined level effect before implementation.

all answered but faction/leadership

### 3. Block vs. Harm level interaction

If Block can only stop actions at or below its own level, a L3 Block cannot stop a L4 Harm. Does a higher-level action always break through a lower-level Block, or is there a probability involved?

### 4. Unspent budget

What happens to unspent L1 budget at end of cycle? 
- Lost — use it or lose it

### 5. How does NPC action selection change?

The current system uses weighted random choice to select actions, then distributes points proportionally. That model breaks under the new system.

New NPC behavior needs to:
- Determine the unit's L1 budget
- Select a set of actions (respecting one-of-each rule)
- Choose what level to execute each at
- Spend budget optimally or semi-randomly per traits

Does trait weighting still apply? Does a high-weight action get a higher level, more budget, or just higher selection priority?

### 6. Fractional ratings

Unit levels are `floor(domain_rating)`. A unit at rating 3.9 is L3. Does the fractional part have any effect on budget or action execution, or is it only relevant for level-up threshold tracking?

- no affect on actions

### 7. Multi-domain actions

Some actions may logically draw on a different domain than the unit's primary. Does the unit use their primary domain level for budget, or the relevant domain level for that specific action?
- take a health penalty as descripbed above

---

## Consequences (Anticipated)

- High-level units become significantly more powerful — not just marginally better, but capable of doing multiple meaningful actions per cycle
- Low-level units are sharply limited — L1 units can do exactly one L1 action per cycle
- The one-of-each rule forces higher-level units to diversify rather than spam their best action
- Obscure becomes a real strategic cost, not a free buff
- The current NPC behavior engine (`npc.py`) requires a significant rewrite — the weighted proportional allocation model is replaced entirely
- Action outcomes need level-scaled effect values across every action type — larger implementation surface than just the economy change

---

## Implementation Note

This rework touches `npc.py` (action selection), `actions.py` (all action outcomes), and `formulas.py` (any derived calculations). It should not be started until all open design questions are resolved. A spec (`actions_spec.md` update) should follow this decision doc before any code is written.
