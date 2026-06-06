# Personality System Specification

**Version:** v1
**Date:** 2026-05-17

Personality is the core driver of faction behavior. This spec defines how traits are structured, how they influence decisions, and how they evolve over time. The faction-behavior spec defines the weight table; this spec defines the system design.

---

## Overview

Each faction has a list of traits. Traits are not binary flags — they have intensity, and can be general or relational (directed at a specific faction). Personality evolves based on what happens to the faction during play.

No faction has a fixed "goal." Goals emerge from personality. An aggressive faction doesn't decide to attack — it is aggressive, and that trait makes attack the natural choice.

---

## Trait Structure

```python
@dataclass
class FactionTrait:
    trait: str              # see trait list below
    intensity: str          # "slight" | "moderate" | "strong" | "very"
    target_id: Optional[str]  # faction_id if relational; None if general
```

---

## Intensity

| Intensity | Multiplier | Meaning |
|---|---|---|
| `slight` | 0.5 | Tendency, easily overridden |
| `moderate` | 1.0 | Clear personality feature |
| `strong` | 1.5 | Dominant trait, shapes most decisions |
| `very` | 2.0 | Defines the faction — hard to ignore |

Intensity cannot exceed `very`. Traits at `slight` that decay are removed entirely.

---

## General Traits

General traits apply to all decisions. Maximum 6 traits per faction — lowest intensity trait is dropped if exceeded.

| Trait | Character |
|---|---|
| `aggressive` | Seeks to harm, confront, and dominate |
| `defensive` | Protects itself above all else |
| `ambitious` | Grows relentlessly, pushes for more |
| `paranoid` | Sees threats everywhere, over-prepares |
| `opportunistic` | Moves on weakness, takes what's available |
| `expansionary` | Territory and reach above all |
| `conservative` | Maintains what it has, avoids risk |
| `corrupt` | Enriches itself at others' expense |

Each trait's numeric **weight effect** on action selection — plus the two build-focused
traits `industrious` and `destructive` — lives in the canonical weight table in
`faction-behavior_spec.md`. Per the note above, this spec defines the system design and does
not duplicate those numbers.

---

## Relational Traits

Relational traits are directed at a specific faction. They modify behavior only when the targeted faction is a valid option.

| Trait | Trigger |
|---|---|
| `distrusts X` | X is in rivals |
| `angry at X` | X is in rivals |
| `trusts X` | X is the only available rival |
| `allied with X` | X is in rivals |

Weight effects for each relational trait live in the canonical table in `faction-behavior_spec.md`.

Relational traits also influence target selection: `angry at X` and `distrusts X` weight that faction ×3 in target selection.

---

## Caps and Limits

- Maximum 6 traits per faction at any time
- When a 7th trait is added: lowest intensity trait is dropped
- Ties in intensity: most recently added is kept
- `angry at X` relational traits count toward the 6-trait cap

---

## Trait Evolution

Traits shift at end of cycle based on what happened. Callers pass only relevant kwargs.

| Event | Effect |
|---|---|
| Faction was harmed by X | Add/amplify `angry at X` (slight) + `aggressive` (slight) |
| Faction harmed X successfully | Amplify `aggressive` +1 step |
| Faction harmed repeatedly by same X | Force `angry at X` to `strong` |
| Faction grew 3+ cycles in a row | Add/amplify `ambitious` (moderate) |
| Faction protected 3+ cycles in a row | Amplify `defensive` or `paranoid` +1 step |
| Faction health < 20 | Add `defensive` (moderate) if not already present |
| No hostile action for 5+ cycles | Decay `aggressive` and `angry at` traits by 1 step |

**Intensity step order:** slight → moderate → strong → very (bidirectional)

Decay at `slight` = trait removed.

---

## Leader Influence on Personality

Leader traits modify the effective weight of faction traits each cycle.

- Leader trait matches a faction trait: amplify by +0.25 intensity step equivalent
- Leader trait not in faction list: add a weak (+0.25 step) version of that trait's weights
- Leader `status == "weakened"`: all leader influence halved
- Leader `status == "absent"`: leader influence removed entirely

Leader influence is read-only — it does not permanently change faction.traits. It is applied as a modifier at decision time.

---

## Reading Personality

The personality record is the source of truth for:
- What the faction will probably do (behavior engine)
- How the faction responds to the Mayor (future: audience system)
- How the faction reacts to events (future: event system)
- What the narrative says about the faction

Traits are always visible to the player in v1 (full transparency). Limited visibility is a future game mode.
