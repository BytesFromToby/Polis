# Backlog
**Last updated:** 2026-03-31

All 25 original items from the 2026-03-29 audit have been resolved.
Items below are new work identified from playtesting and design review.

---

## Priority Key

- **[Critical]** — Engine produces wrong results without this
- **[Major]** — Significant behavioral gap; needed for valid simulation
- **[Minor]** — Small improvement; low behavioral impact

---

## engine

### ~~1. [Major] Kick can target and remove the faction leader~~ ✓ Done 2026-03-31

**Problem:** `resolve_kick` in `actions.py` has no protection for the leader. When a faction starts with only their leader as a member, the leader fills or exceeds capacity (e.g. a rating-5 leader in a rating-5 faction = 100% utilization), and the kick auto-trigger removes them. This is the primary cause of early leadership collapse in runs with hand-crafted starting data.

**Fix:** In `resolve_kick`, skip the leader when selecting a kick target. If no non-leader members exist, do not kick.

---

### ~~2. [Major] No faction failure / collapse mechanic~~ ✓ Done 2026-03-31

**Problem:** Factions can reach health=1, LN=20, 0 members, and 0 level_1_count and still persist indefinitely. There is no condition under which a faction is removed from the simulation.

**Proposed mechanic:** A faction should collapse (be removed) when it meets all of:
- Health ends actions at 1 health

level = rating - fix when documenting

On collapse:
- naravtive event fires
- if level 2,3 - faction disolves - 
- if level 4-5 50% faction disolves 50% faction splits
- if level 6+  faction splits.

On Disolve
faction removed from `factions` dict, any units still referencing it via faction slots are cleaned up. Units are not associated with any faction. 

On Split
- create new faction, new name, one Rating below old faction at floor and 80 health same domain
- old faction keeps it's name,  drops 2 levels below old faction at floor and 80 health
- kick out leader if there is one - make not a leader and not member of either faction
- Traits - old traits are divide between them, remander going to Old. The small olf faction gets 1 new trait.  the new faction gets 2 new traits.
- rebalance the named units between the two new factions.
    start with the highest level make leader of new group
    2nd leader of old group
    repeat until all are assigned
    fill remander with 1s. any extra 1s are removed.

**Needs:** Decision doc before implementation.

---

### 3. [Minor] Faction relationships are defined but unused

**Problem:** `FactionRelationship` is stored on every faction and loaded from JSON, but `get_faction_relationship()` is never called anywhere in the engine. Faction-to-faction relationships have no effect on behavior.

**Note:** Split factions should automatically be set as rivals (Foe) with each other on creation.

**Needs:** Design pass on where faction relationships should influence behavior (target selection, action weights, etc.) before implementing.

**
---

### 4. [Major] Action point distribution floors to zero for most actions

**Problem:** `select_npc_actions()` uses `int(action_points * share)` to allocate points. With 15 actions and base weights all around 10, most shares are below 1.0 and floor to zero. The remainder dumps entirely onto the top action. In practice, most units end up with one active action regardless of their rating — defeating the purpose of the multi-point economy.

**Example:** A rating-6 unit (6 points) with Care at 30/215 total weight gets `int(6 × 0.14)` = `int(0.84)` = 0 points. All 6 remainder points go to the highest-weight action.

**Fix options:**
- Use `round()` instead of `int()` — shares ≥ 0.5 become 1 point, producing 2–4 active actions for typical units
- Distribute one point at a time to the highest-share action until points are exhausted

**Needs:** Decision on rounding approach before implementing.

---
